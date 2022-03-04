import os
from os.path import abspath
import inspect
import pathlib
import sys


import pytest

from ..util import yesno

from ..test_support import pytest_plugin

# TODO: setting the plugins so that the end user can invoke py.test directly
# could be a useful thing. Will have to consider that later.


class _TryAgain(Exception):
    pass


#
# main test class
#
class PyFrcTest:
    """
    Executes unit tests on the robot code using a special py.test plugin
    """

    def __init__(self, parser=None):
        if parser:
            parser.add_argument(
                "--builtin",
                default=False,
                action="store_true",
                help="Use pyfrc's builtin tests if no tests are specified",
            )
            parser.add_argument(
                "--coverage-mode",
                default=False,
                action="store_true",
                help="This flag is passed when trying to determine coverage",
            )
            parser.add_argument(
                "pytest_args",
                nargs="*",
                help="To pass args to pytest, specify --<space>, then the args",
            )

    def run(self, options, robot_class, **static_options):
        # wrapper around run_test that sets the appropriate mode

        from .. import config

        config.mode = "test"
        config.coverage_mode = options.coverage_mode

        return self.run_test(
            options.pytest_args, robot_class, options.builtin, **static_options
        )

    def run_test(self, *a, **k):
        try:
            return self._run_test(*a, **k)
        except _TryAgain:
            return self._run_test(*a, **k)

    def _run_test(self, pytest_args, robot_class, use_builtin, **static_options):

        # find test directory, change current directory so py.test can find the tests
        # -> assume that tests reside in tests or ../tests

        curdir = pathlib.Path.cwd().absolute()

        self.robot_class = robot_class
        robot_file = pathlib.Path(inspect.getfile(robot_class)).absolute()

        if robot_file.name == "cProfile.py":
            # so, the module for the robot class is __main__, and __main__ is
            # cProfile so try to find it
            robot_file = curdir / "robot.py"

            if not robot_file.exists():
                print(
                    "ERROR: Cannot run profiling from a directory that does not contain robot.py"
                )
                return 1

        self.try_dirs = [
            (robot_file.parent / "tests").absolute(),
            (robot_file.parent / ".." / "tests").absolute(),
        ]

        for d in self.try_dirs:
            if d.exists():
                test_directory = d
                os.chdir(test_directory)
                break
        else:
            if not use_builtin:
                print("ERROR: Cannot run robot tests, as test directory was not found!")
                retv = self._no_tests()
                return 1

            from ..tests import basic

            pytest_args.insert(0, abspath(inspect.getfile(basic)))

        try:
            retv = pytest.main(
                pytest_args,
                plugins=[pytest_plugin.PyFrcPlugin(robot_class, robot_file)],
            )
        finally:
            os.chdir(curdir)

        # requires pytest 2.8.x
        if retv == 5:
            print()
            print("ERROR: a tests directory was found, but no tests were defined")
            retv = self._no_tests(retv)

        return retv

    def _no_tests(self, r=1):
        print()
        print("Looked for tests at:")
        for d in self.try_dirs:
            print("-", d)
        print()
        print(
            "If you don't want to write your own tests, pyfrc comes with generic tests"
        )
        print("that can test basic functionality of most robots. You can run them by")
        print("specifying the --builtin option.")
        print()

        if not sys.stdin.isatty():
            print(
                "Alternatively, to create a tests directory with the builtin tests, you can run:"
            )
            print()
            print("    python3 robot.py add-tests")
            print()
        else:
            if yesno("Create a tests directory with builtin tests now?"):
                from .cli_add_tests import PyFrcAddTests

                add_tests = PyFrcAddTests()
                add_tests.run(None, self.robot_class)

                raise _TryAgain()

        return r
