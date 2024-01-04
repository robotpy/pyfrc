import os
from os.path import abspath
import inspect
import pathlib
import sys
import typing

import wpilib

import pytest

from ..util import yesno

from ..test_support import pytest_plugin

# TODO: setting the plugins so that the end user can invoke pytest directly
# could be a useful thing. Will have to consider that later.


class _TryAgain(Exception):
    pass


#
# main test class
#
class PyFrcTest:
    """
    Executes unit tests on the robot code using a special pytest plugin
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

    def run(
        self,
        main_file: pathlib.Path,
        project_path: pathlib.Path,
        robot_class: typing.Type[wpilib.RobotBase],
        builtin: bool,
        coverage_mode: bool,
        pytest_args: typing.List[str],
    ):
        try:
            return self._run_test(
                main_file,
                project_path,
                robot_class,
                builtin,
                coverage_mode,
                pytest_args,
            )
        except _TryAgain:
            return self._run_test(
                main_file,
                project_path,
                robot_class,
                builtin,
                coverage_mode,
                pytest_args,
            )

    def _run_test(
        self,
        main_file: pathlib.Path,
        project_path: pathlib.Path,
        robot_class: typing.Type[wpilib.RobotBase],
        builtin: bool,
        coverage_mode: bool,
        pytest_args: typing.List[str],
    ):
        # find test directory, change current directory so pytest can find the tests
        # -> assume that tests reside in tests or ../tests

        curdir = pathlib.Path.cwd().absolute()

        self.try_dirs = [
            (project_path / "tests").absolute(),
            (project_path / ".." / "tests").absolute(),
        ]

        for d in self.try_dirs:
            if d.exists():
                test_directory = d
                os.chdir(test_directory)
                break
        else:
            if not builtin:
                print("ERROR: Cannot run robot tests, as test directory was not found!")
                retv = self._no_tests(main_file, project_path)
                return 1

            from ..tests import basic

            pytest_args.insert(0, abspath(inspect.getfile(basic)))

        try:
            retv = pytest.main(
                pytest_args,
                plugins=[pytest_plugin.PyFrcPlugin(robot_class, main_file)],
            )
        finally:
            os.chdir(curdir)

        # requires pytest 2.8.x
        if retv == 5:
            print()
            print("ERROR: a tests directory was found, but no tests were defined")
            retv = self._no_tests(main_file, project_path, retv)

        return retv

    def _no_tests(
        self, main_file: pathlib.Path, project_path: pathlib.Path, r: int = 1
    ):
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
                add_tests.run(main_file, project_path)

                raise _TryAgain()

        return r
