import argparse
import contextlib
import inspect
import os
import sys
import re

import shutil
import tempfile
import threading

from os.path import abspath, basename, dirname, join, splitext
from pathlib import PurePosixPath

from robotpy_installer import sshcontroller

from ..util import print_err, yesno

import wpilib

import logging

logger = logging.getLogger("deploy")


def relpath(path):
    """Path helper, gives you a path relative to this file"""
    return os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
    )


@contextlib.contextmanager
def wrap_ssh_error(msg: str):
    try:
        yield
    except sshcontroller.SshExecError as e:
        raise sshcontroller.SshExecError(f"{msg}: {str(e)}", e.retval) from e


class PyFrcDeploy:
    """
    Uploads your robot code to the robot and executes it immediately
    """

    def __init__(self, parser: argparse.ArgumentParser):
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
            "--large",
            action="store_true",
            default=False,
            help="If specified, allow uploading large files (> 250k) to the RoboRIO",
        )

        robot_args = parser.add_mutually_exclusive_group()

        robot_args.add_argument(
            "--robot", default=None, help="Set hostname or IP address of robot"
        )

        robot_args.add_argument(
            "--team", default=None, type=int, help="Set team number to deploy robot for"
        )

        parser.add_argument(
            "--no-resolve",
            action="store_true",
            default=False,
            help="If specified, don't do a DNS lookup, allow ssh et al to do it instead",
        )

    def run(self, options, robot_class, **static_options):

        from .. import config

        config.mode = "upload"

        # run the test suite before uploading
        # TODO: disabled for 2020
        if False and not options.skip_tests:
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

        if not options.large and not self._check_large_files(robot_path):
            return 1

        hostname_or_team = options.robot
        if not hostname_or_team and options.team:
            hostname_or_team = options.team

        try:
            with sshcontroller.ssh_from_cfg(
                cfg_filename,
                username="lvuser",
                password="",
                hostname=hostname_or_team,
                no_resolve=options.no_resolve,
            ) as ssh:

                if not self._check_requirements(ssh, options.no_version_check):
                    return 1

                if not self._do_deploy(ssh, options, robot_filename, robot_path):
                    return 1

        except sshcontroller.SshExecError as e:
            print_err("ERROR:", str(e))
            return 1

        print("\nSUCCESS: Deploy was successful!")
        return 0

    def _check_large_files(self, robot_path):

        large_sz = 250000

        large_files = []
        for fname in self._copy_to_tmpdir(None, robot_path, dry_run=True):
            st = os.stat(fname)
            if st.st_size > large_sz:
                large_files.append((fname, st.st_size))

        if large_files:
            print_err(f"ERROR: large files found (larger than {large_sz} bytes)")
            for fname, sz in sorted(large_files):
                print_err(f"- {fname} ({sz} bytes)")

            if not yesno("Upload anyways?"):
                return False

        return True

    def _check_requirements(
        self, ssh: sshcontroller.SshController, no_wpilib_version_check: bool
    ) -> bool:

        # does python exist
        with wrap_ssh_error("checking if python exists"):
            if ssh.exec_cmd("[ -x /usr/local/bin/python3 ]").returncode != 0:
                print_err(
                    "ERROR: python3 was not found on the roboRIO: have you installed robotpy?"
                )
                print_err()
                print_err(
                    f"See {sys.executable} -m robotpy-installer install-python --help"
                )
                return False

        # does wpilib exist and does the version match
        with wrap_ssh_error("checking for wpilib version"):
            py = ";".join(
                [
                    "import os.path, site",
                    "version = 'unknown'",
                    "v = site.getsitepackages()[0] + '/wpilib/version.py'",
                    "exec(open(v).read(), globals()) if os.path.exists(v) else False",
                    "print(version)",
                ]
            )

            result = ssh.exec_cmd(
                f'/usr/local/bin/python3 -c "{py}"', check=True, get_output=True
            )
            assert result.stdout is not None

            wpilib_version = result.stdout.strip()
            if wpilib_version == "unknown":
                print_err(
                    "WPILib was not found on the roboRIO: have you installed it on the RoboRIO?"
                )
                return False

            print("RoboRIO has WPILib version", wpilib_version)

            if not no_wpilib_version_check and wpilib_version != wpilib.__version__:
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
                return False

        # See if there's any roboRIO settings we need to adjust
        with wrap_ssh_error("checking on-robot settings"):
            result = ssh.exec_cmd(
                "grep ^StartupDLLs /etc/natinst/share/ni-rt.ini",
                get_output=True,
            )
            assert result.stdout is not None
            fix_startupdlls = result.stdout.strip() != ""

            result = ssh.exec_cmd(
                'grep \\"exec /usr/local/frc/bin/frcRunRobot.sh',
                get_output=True,
            )
            assert result.stdout is not None
            fix_runrobot = result.stdout.strip() != ""

        if fix_runrobot or fix_startupdlls:
            with wrap_ssh_error("Applying patches to roborio"):
                self._apply_admin_fixes(ssh, fix_startupdlls, fix_runrobot)

        return True

    def _apply_admin_fixes(
        self,
        lvuser_ssh: sshcontroller.SshController,
        fix_startupdlls: bool,
        fix_runrobot: bool,
    ):
        # requires admin-level access to fix, so create a new ssh controller
        ssh = sshcontroller.SshController(lvuser_ssh.hostname, "admin", "")
        with ssh:
            if fix_startupdlls:
                # Frees up memory on the RIO
                ssh.exec_cmd(
                    'sed -i -e "s/^StartupDLLs/;StartupDLLs/" /etc/natinst/share/ni-rt.ini'
                )
            if fix_runrobot:
                # GradleRIO does this, so we do too
                ssh.exec_cmd(
                    "sed -i -e 's/\\\"exec /\\\"/' /usr/local/frc/bin/frcRunRobot.sh"
                )

    def _do_deploy(
        self,
        ssh: sshcontroller.SshController,
        options,
        robot_filename: str,
        robot_path: str,
    ) -> bool:
        # This probably should be configurable... oh well

        deploy_dir = PurePosixPath("/home/lvuser")
        py_deploy_subdir = "py"
        py_new_deploy_subdir = "py_new"
        py_deploy_dir = deploy_dir / py_deploy_subdir

        # note below: deployed_cmd appears that it only can be a single line

        # In 2015, there were stdout/stderr issues. In 2016+, they seem to
        # have been fixed, but need to use -u for it to really work properly

        if options.debug:
            compileall_flags = ""
            deployed_cmd = (
                "env LD_LIBRARY_PATH=/usr/local/frc/lib/ /usr/local/bin/python3 -u %s/%s -v run"
                % (py_deploy_dir, robot_filename)
            )
            deployed_cmd_fname = "robotDebugCommand"
            bash_cmd = "/bin/bash -cex"
        else:
            compileall_flags = "-O"
            deployed_cmd = (
                "env LD_LIBRARY_PATH=/usr/local/frc/lib/ /usr/local/bin/python3 -u -O %s/%s run"
                % (py_deploy_dir, robot_filename)
            )
            deployed_cmd_fname = "robotCommand"
            bash_cmd = "/bin/bash -ce"

        if options.in_place:
            replace_cmd = "true"
            py_new_deploy_subdir = py_deploy_subdir
        else:
            replace_cmd = (
                "rm -rf %(py_deploy_dir)s; mv %(py_new_deploy_dir)s %(py_deploy_dir)s"
            )

        py_new_deploy_dir = deploy_dir / py_new_deploy_subdir
        replace_cmd %= {
            "py_deploy_dir": py_deploy_dir,
            "py_new_deploy_dir": py_new_deploy_dir,
        }

        with wrap_ssh_error("configuring command"):
            ssh.exec_cmd(
                f'echo "{deployed_cmd}" > {deploy_dir}/{deployed_cmd_fname}', check=True
            )

        if options.debug:
            with wrap_ssh_error("touching frcDebug"):
                ssh.exec_cmd("touch /tmp/frcdebug", check=True)

        with wrap_ssh_error("removing stale deploy directory"):
            ssh.exec_cmd(f"rm -rf {py_new_deploy_dir}", check=True)

        # Copy the files over, copy to a temporary directory first
        # -> this is inefficient, but it's easier in sftp
        tmp_dir = tempfile.mkdtemp()
        try:
            py_tmp_dir = join(tmp_dir, py_new_deploy_subdir)
            self._copy_to_tmpdir(py_tmp_dir, robot_path)
            ssh.sftp(py_tmp_dir, deploy_dir, mkdir=not options.in_place)
        finally:
            shutil.rmtree(tmp_dir)

        # start the netconsole listener now if requested, *before* we
        # actually start the robot code, so we can see all messages
        nc_thread = None
        if options.nc or options.nc_ds:
            nc_thread = self._start_nc(ssh, options)

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

            with wrap_ssh_error("starting robot code"):
                ssh.exec_cmd(sshcmd, check=True, print_output=True)

        if nc_thread is not None:
            nc_thread.join()

        return True

    def _start_nc(self, ssh, options):
        from netconsole import run

        nc_event = threading.Event()
        nc_thread = threading.Thread(
            target=run,
            args=(ssh.hostname,),
            kwargs=dict(connect_event=nc_event, fakeds=options.nc_ds),
            daemon=True,
        )
        nc_thread.start()
        nc_event.wait(5)
        logger.info("Netconsole is listening...")
        return nc_thread

    def _copy_to_tmpdir(self, tmp_dir, robot_path, dry_run=False):

        upload_files = []
        ignore_exts = {"pyc", "whl", "ipk", "zip", "gz"}

        for root, dirs, files in os.walk(robot_path):
            prefix = root[len(robot_path) + 1 :]
            if not dry_run:
                os.mkdir(join(tmp_dir, prefix))

            # skip .svn, .git, .hg, etc directories
            for d in dirs[:]:
                if d.startswith(".") or d in ("__pycache__", "venv"):
                    dirs.remove(d)

            # skip .pyc files
            for filename in files:

                r, ext = splitext(filename)
                if ext in ignore_exts or r.startswith("."):
                    continue

                fname = join(root, filename)
                upload_files.append(fname)

                if not dry_run:
                    shutil.copy(fname, join(tmp_dir, prefix, filename))

        return upload_files
