import os
import pathlib
import sys

builtin_tests = """'''
    This test module imports tests that come with pyfrc, and can be used
    to test basic functionality of just about any robot.
'''

from pyfrc.tests import *
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

        print()
        print("Robot tests can be ran via 'python3 -m robotpy test'")
