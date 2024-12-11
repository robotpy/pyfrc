import os
import pathlib
import sys

builtin_tests = """'''
    This test module imports tests that come with pyfrc, and can be used
    to test basic functionality of just about any robot.
'''

from pyfrc.tests import *
"""

conftest = """'''
    This file registesr the PyFrcPlugin so it can be found during
    distributed tests with pytest-xdist
'''

import sys
import pathlib
from pyfrc.test_support.pytest_plugin import PyFrcPlugin

# Add the location of robot.py to our path
parentdir = pathlib.Path(__file__).parent.parent
sys.path.append(str(parentdir))
import robot

def pytest_configure(config):
    if config.pluginmanager.has_plugin("pyfrc_plugin"):
        # Avoid double registration
        return
    robot_class = robot.MyRobot
    robot_file = parentdir/'robot.py'
    plugin = PyFrcPlugin(robot_class, robot_file)
    config.pluginmanager.register(plugin, "pyfrc_plugin")
"""


class PyFrcAddTests:
    """
    Adds default pyfrc tests to your robot project directory
    """

    def __init__(self, parser=None):
        pass

    def run(self, main_file: pathlib.Path, project_path: pathlib.Path):
        if not main_file.exists():
            print(
                f"ERROR: is this a robot project? {main_file} does not exist",
                file=sys.stderr,
            )
            return 1

        try_dirs = [project_path / "tests", project_path / ".." / "tests"]

        test_directory = try_dirs[0]

        for d in try_dirs:
            if d.exists():
                test_directory = d
                break
        else:
            test_directory.mkdir(parents=True)

        print(f"Tests directory is {test_directory}")
        print()
        builtin_tests_file = test_directory / "pyfrc_test.py"
        if builtin_tests_file.exists():
            print("- pyfrc_test.py already exists")
        else:
            with open(builtin_tests_file, "w") as fp:
                fp.write(builtin_tests)
            print("- builtin tests created at", builtin_tests_file)

        conftest_file = test_directory / "conftest.py"
        if conftest_file.exists():
            print("- conftest.py already exists")
        else:
            with open(conftest_file, "w") as fp:
                fp.write(conftest)
            print("- conftest created at", conftest_file)

        print()
        print("Robot tests can be ran via 'robotpy test'")
