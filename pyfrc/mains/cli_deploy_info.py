import argparse
import inspect

import pathlib
import json

from robotpy_installer import sshcontroller

from ..util import print_err


class PyFrcDeployInfo:
    """
    Displays information about code deployed to robot
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

        config.mode = "deploy-info"

        robot_file = pathlib.Path(inspect.getfile(robot_class))
        cfg_filename = robot_file.parent / ".deploy_cfg"

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

                result = ssh.exec_cmd(
                    "cat /home/lvuser/py/deploy.json", get_output=True
                )
                if not result.stdout:
                    print("{}")
                else:
                    data = json.loads(result.stdout)
                    print(json.dumps(data, indent=2, sort_keys=True))

        except sshcontroller.SshExecError as e:
            print_err("ERROR:", str(e))
            return 1

        return 0
