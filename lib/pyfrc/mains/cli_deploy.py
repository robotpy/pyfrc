import inspect
import os
import sys
import re

import shutil
import tempfile
import threading

from os.path import abspath, basename, dirname, exists, join, splitext
from pathlib import PurePosixPath

from ..util import print_err, yesno

import wpilib

import logging

logger = logging.getLogger("deploy")


def relpath(path):
    """Path helper, gives you a path relative to this file"""
    return os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
    )


class PyFrcDeploy:
    """
        Uploads your robot code to the robot and executes it immediately
    """

    def __init__(self, parser):
        """ :type parser: argparse.ArgumentParser """
        parser.add_argument(
            "--builtin",
            default=False,
            action="store_true",
            help="Use pyfrc's builtin tests if no tests are specified",
        )

        parser.add_argument(
            "--skip-tests",
            action="store_true",
            default=False,
            help="If specified, don't run tests before uploading code to robot (DANGEROUS)",
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help="If specified, runs the code in debug mode (which only currently enables verbose logging)",
        )

        parser.add_argument(
            "--nonstandard",
            action="store_true",
            default=False,
            help="When specified, allows you to deploy code in a file that isn't called robot.py",
        )

        parser.add_argument(
            "--nc",
            "--netconsole",
            action="store_true",
            default=False,
            help="Attach netconsole listener and show robot stdout (requires DS to be connected)",
        )

        parser.add_argument(
            "--nc-ds",
            "--netconsole-ds",
            action="store_true",
            default=False,
            help="Attach netconsole listener and show robot stdout (fakes a DS connection)",
        )

        parser.add_argument(
            "--in-place",
            action="store_true",
            default=False,
            help="Overwrite currently deployed code, don't delete anything, and don't restart running robot code.",
        )

        parser.add_argument(
            "-n",
            "--no-version-check",
            action="store_true",
            default=False,
            help="If specified, don't verify that your local wpilib install matches the version on the robot (not recommended)",
        )

        parser.add_argument(
            "--robot", default=None, help="Set hostname or IP address of robot"
        )

        parser.add_argument(
            "--no-resolve",
            action="store_true",
            default=False,
            help="If specified, don't do a DNS lookup, allow ssh et al to do it instead",
        )

    def run(self, options, robot_class, **static_options):

        try:
            from robotpy_installer import installer
        except ImportError:
            raise ImportError(
                "You must have the robotpy-installer package installed to deploy code!"
            )

        from .. import config

        config.mode = "upload"

        # run the test suite before uploading
        if not options.skip_tests:
            from .cli_test import PyFrcTest

            tester = PyFrcTest()

            retval = tester.run_test(
                [], robot_class, options.builtin, ignore_missing_test=True
            )
            if retval != 0:
                print_err("ERROR: Your robot tests failed, aborting upload.")
                if not sys.stdin.isatty():
                    print_err("- Use --skip-tests if you want to upload anyways")
                    return retval

                print()
                if not yesno("- Upload anyways?"):
                    return retval

                if not yesno("- Are you sure? Your robot code may crash!"):
                    return retval

                print()
                print("WARNING: Uploading code against my better judgement...")

        # upload all files in the robot.py source directory
        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)
        robot_filename = basename(robot_file)
        cfg_filename = join(robot_path, ".deploy_cfg")

        if not options.nonstandard and robot_filename != "robot.py":
            print_err(
                "ERROR: Your robot code must be in a file called robot.py (launched from %s)!"
                % robot_filename
            )
            print_err()
            print_err(
                "If you really want to do this, then specify the --nonstandard argument"
            )
            return 1

        # This probably should be configurable... oh well

        deploy_dir = PurePosixPath("/home/lvuser")
        py_deploy_subdir = "py"
        py_new_deploy_subdir = "py_new"
        py_deploy_dir = deploy_dir / py_deploy_subdir

        # note below: deployed_cmd appears that it only can be a single line

        # In 2015, there were stdout/stderr issues. In 2016, they seem to
        # have been fixed, but need to use -u for it to really work properly

        if options.debug:
            compileall_flags = ""
            deployed_cmd = (
                "env LD_LIBRARY_PATH=/usr/local/frc/lib/ /usr/local/bin/python3 -u %s/%s -v run"
                % (py_deploy_dir, robot_filename)
            )
            deployed_cmd_fname = "robotDebugCommand"
            extra_cmd = "touch /tmp/frcdebug; chown lvuser:ni /tmp/frcdebug"
            bash_cmd = "/bin/bash -cex"
        else:
            compileall_flags = "-O"
            deployed_cmd = (
                "env LD_LIBRARY_PATH=/usr/local/frc/lib/ /usr/local/bin/python3 -u -O %s/%s run"
                % (py_deploy_dir, robot_filename)
            )
            deployed_cmd_fname = "robotCommand"
            extra_cmd = ""
            bash_cmd = "/bin/bash -ce"

        if options.in_place:
            replace_cmd = "true"
            py_new_deploy_subdir = py_deploy_subdir
        else:
            replace_cmd = (
                "[ -d %(py_deploy_dir)s ] && rm -rf %(py_deploy_dir)s; mv %(py_new_deploy_dir)s %(py_deploy_dir)s"
            )

        py_new_deploy_dir = deploy_dir / py_new_deploy_subdir
        replace_cmd %= {
            "py_deploy_dir": py_deploy_dir,
            "py_new_deploy_dir": py_new_deploy_dir,
        }

        check_version = (
            '/usr/local/bin/python3 -c "exec(open(\\"$SITEPACKAGES/wpilib/version.py\\", \\"r\\").read(), globals()); print(\\"WPILib version on robot is \\" + __version__);exit(0) if __version__ == \\"%s\\" else exit(89)"'
            % wpilib.__version__
        )
        if options.no_version_check:
            check_version = ""

        check_startup_dlls = (
            '(if [ "$(grep ^StartupDLLs /etc/natinst/share/ni-rt.ini)" != "" ]; then exit 91; fi)'
        )

        # This is a nasty bit of code now...
        sshcmd = inspect.cleandoc(
            """
            %(bash_cmd)s '[ -x /usr/local/bin/python3 ] || exit 87
            SITEPACKAGES=$(/usr/local/bin/python3 -c "import site; print(site.getsitepackages()[0])")
            [ -f $SITEPACKAGES/wpilib/version.py ] || exit 88
            %(check_version)s
            echo "%(deployed_cmd)s" > %(deploy_dir)s/%(deployed_cmd_fname)s
            %(extra_cmd)s
            %(check_startup_dlls)s
            '
        """
        )

        sshcmd %= locals()

        sshcmd = re.sub("\n+", ";", sshcmd)

        nc_thread = None

        try:
            controller = installer.ssh_from_cfg(
                cfg_filename,
                username="lvuser",
                password="",
                hostname=options.robot,
                allow_mitm=True,
                no_resolve=options.no_resolve,
            )

            try:
                # Housekeeping first
                logger.debug("SSH: %s", sshcmd)
                controller.ssh(sshcmd)
            except installer.SshExecError as e:
                doret = True
                if e.retval == 87:
                    print_err(
                        "ERROR: python3 was not found on the roboRIO: have you installed robotpy?"
                    )
                elif e.retval == 88:
                    print_err(
                        "ERROR: WPILib was not found on the roboRIO: have you installed robotpy?"
                    )
                elif e.retval == 89:
                    print_err("ERROR: expected WPILib version %s" % wpilib.__version__)
                    print_err()
                    print_err("You should either:")
                    print_err(
                        "- If the robot version is older, upgrade the RobotPy on your robot"
                    )
                    print_err("- Otherwise, upgrade pyfrc on your computer")
                    print_err()
                    print_err(
                        "Alternatively, you can specify --no-version-check to skip this check"
                    )
                elif e.retval == 90:
                    print_err("ERROR: error running compileall")
                elif e.retval == 91:
                    # Not an error; ssh in as admin and fix the startup dlls (Saves 24M of RAM)
                    # -> https://github.com/wpilibsuite/EclipsePlugins/pull/154
                    logger.info("Fixing StartupDLLs to save RAM...")
                    controller.username = "admin"
                    controller.ssh(
                        'sed -i -e "s/^StartupDLLs/;StartupDLLs/" /etc/natinst/share/ni-rt.ini'
                    )

                    controller.username = "lvuser"
                    doret = False
                else:
                    print_err("ERROR: %s" % e)

                if doret:
                    return 1

            # Copy the files over, copy to a temporary directory first
            # -> this is inefficient, but it's easier in sftp
            tmp_dir = tempfile.mkdtemp()
            try:
                py_tmp_dir = join(tmp_dir, py_new_deploy_subdir)
                self._copy_to_tmpdir(py_tmp_dir, robot_path)
                controller.sftp(py_tmp_dir, deploy_dir, mkdir=not options.in_place)
            finally:
                shutil.rmtree(tmp_dir)

            # start the netconsole listener now if requested, *before* we
            # actually start the robot code, so we can see all messages
            if options.nc or options.nc_ds:
                from netconsole import run

                nc_event = threading.Event()
                nc_thread = threading.Thread(
                    target=run,
                    args=(controller.hostname,),
                    kwargs=dict(connect_event=nc_event, fakeds=options.nc_ds),
                    daemon=True,
                )
                nc_thread.start()
                nc_event.wait(5)
                logger.info("Netconsole is listening...")

            if not options.in_place:
                # Restart the robot code and we're done!
                sshcmd = (
                    "%(bash_cmd)s '"
                    + "%(replace_cmd)s;"
                    + "/usr/local/bin/python3 %(compileall_flags)s -m compileall -q -r 5 /home/lvuser/py;"
                    + ". /etc/profile.d/natinst-path.sh; "
                    + "chown -R lvuser:ni %(py_deploy_dir)s; "
                    + "sync; "
                    + "/usr/local/frc/bin/frcKillRobot.sh -t -r || true"
                    + "'"
                )

                sshcmd %= {
                    "bash_cmd": bash_cmd,
                    "compileall_flags": compileall_flags,
                    "py_deploy_dir": py_deploy_dir,
                    "replace_cmd": replace_cmd,
                }

                logger.debug("SSH: %s", sshcmd)
                controller.ssh(sshcmd)

        except installer.Error as e:
            print_err("ERROR: %s" % e)
            return 1
        else:
            print("\nSUCCESS: Deploy was successful!")

        if nc_thread is not None:
            nc_thread.join()

        return 0

    def _copy_to_tmpdir(self, tmp_dir, robot_path):

        upload_files = []

        for root, dirs, files in os.walk(robot_path):
            prefix = root[len(robot_path) + 1 :]
            os.mkdir(join(tmp_dir, prefix))

            # skip .svn, .git, .hg, etc directories
            for d in dirs[:]:
                if d.startswith(".") or d == "__pycache__":
                    dirs.remove(d)

            # skip .pyc files
            for filename in files:

                r, ext = splitext(filename)
                if ext == "pyc" or r.startswith("."):
                    continue

                shutil.copy(join(root, filename), join(tmp_dir, prefix, filename))

        return upload_files
