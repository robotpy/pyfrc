import inspect
import os
from os.path import abspath, dirname, exists, join

builtin_tests = """'''
    This test module imports tests that come with pyfrc, and can be used
    to test basic functionality of just about any robot.
'''

from pyfrc.tests import *
"""


class PyFrcAddTests:
    def __init__(self, parser=None):
        pass

    def run(self, options, robot_class, **static_options):

        print("tests are not yet implemented for RobotPy 2020")
        return 1

        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)

        try_dirs = [
            abspath(join(robot_path, "tests")),
            abspath(join(robot_path, "..", "tests")),
        ]

        test_directory = try_dirs[0]

        for d in try_dirs:
            if exists(d):
                test_directory = d
                break
        else:
            os.makedirs(test_directory)

        print("Tests directory is %s" % test_directory)
        print()
        builtin_tests_file = join(test_directory, "pyfrc_test.py")
        if exists(builtin_tests_file):
            print("- pyfrc_test.py already exists")
        else:
            with open(builtin_tests_file, "w") as fp:
                fp.write(builtin_tests)
            print("- builtin tests created at", builtin_tests_file)

        print()
        print("Robot tests can be ran via 'python3 robot.py test'")
