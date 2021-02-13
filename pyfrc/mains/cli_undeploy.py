import argparse
import inspect

from os.path import abspath, dirname, join

from robotpy_installer import sshcontroller

from ..util import print_err, yesno


class PyFrcUndeploy:
    """
    Removes current robot code from a RoboRIO
    """

    def __init__(self, parser: argparse.ArgumentParser):

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

        config.mode = "undeploy"

        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)
        cfg_filename = join(robot_path, ".deploy_cfg")

        if not yesno(
            "This will stop your robot code and delete it from the RoboRIO. Continue?"
        ):
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

                # first, turn off the running program
                ssh.exec_cmd("/usr/local/frc/bin/frcKillRobot.sh -t")

                # delete the code
                ssh.exec_cmd("rm -rf /home/lvuser/py")

                # for good measure, delete the start command too
                ssh.exec_cmd(
                    "rm -f /home/lvuser/robotDebugCommand /home/lvuser/robotCommand"
                )

        except sshcontroller.SshExecError as e:
            print_err("ERROR:", str(e))
            return 1

        print("SUCCESS: Files have been successfully wiped!")

        return 0
