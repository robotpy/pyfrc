import argparse
import contextlib
import inspect
import os
import sys
import re

import shutil
import tempfile
import threading

from os.path import abspath, basename, dirname, exists, join, splitext
from pathlib import PurePosixPath

from robotpy_installer import sshcontroller

from ..util import print_err, yesno

import wpilib

import logging

logger = logging.getLogger("wipe")


class PyFrcUndeploy:
    def run(self, options, robot_class, **static_options):
        from .. import config

        config.mode = "undeploy"

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

                if not self._delete_dir(ssh):
                    return 1

        except sshcontroller.SshExecError as e:
            print_err("ERROR:", str(e))
            return 1

        print("SUCCESS: Files have been successfully wiped!")
        return 0

    def _delete_dir(
        self, ssh: sshcontroller.SshController, robot_path: str, robot_filename: str
    ):
        wipe_dir = PurePosixPath("/home/lvuser")
        py_wipe_subdir = "py"
        py_wipe_dir = wipe_dir / py_wipe_subdir

        sshcmd = "rm -rf %(py_wipe_dir)s"

        logger.debug("SSH: %s", sshcmd)

        with wrap_ssh_error("erasing robot code"):
            ssh.exec_cmd(sshcmd, check=True, print_output=True)


@contextlib.contextmanager
def wrap_ssh_error(msg: str):
    try:
        yield
    except sshcontroller.SshExecError as e:
        raise sshcontroller.SshExecError(f"{msg}: {str(e)}") from e
