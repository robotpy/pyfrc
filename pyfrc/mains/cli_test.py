import logging
import os
from os.path import abspath
import inspect
import pathlib
import sys
import typing

import wpilib

import tomli
import pytest

from ..util import yesno

from ..test_support import pytest_plugin

# TODO: setting the plugins so that the end user can invoke pytest directly
# could be a useful thing. Will have to consider that later.

logger = logging.getLogger("test")


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
            isolation_group = parser.add_mutually_exclusive_group()
            isolation_group.add_argument(
                "--isolated",
                default=None,
                dest="isolated",
                action="store_true",
                help="Run each test in a separate robot process (default). Set `tool.robotpy.pyfrc.isolated` in your pyproject.toml to control the default",
            )
            isolation_group.add_argument(
                "--no-isolation",
                dest="isolated",
                action="store_false",
                help="Disable isolated test mode and run tests in-process",
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
            parser.add_argument(
                "-j",
                "--jobs",
                type=int,
                default=-1,
                help="Maximum isolated robot processes (default: max CPUs - 1)",
            )
            parser.add_argument(
                "--init-timeout",
                type=float,
                default=2.0,
                help="Seconds to wait for robot to start (can be set in `tool.robotpy.pyfrc.init_timeout` also)",
            )

    def run(
        self,
        main_file: pathlib.Path,
        project_path: pathlib.Path,
        robot_class: typing.Type[wpilib.RobotBase],
        builtin: bool,
        isolated: typing.Optional[bool],
        coverage_mode: bool,
        verbose: bool,
        pytest_args: typing.List[str],
        jobs: int,
        init_timeout: float,
    ):
        if isolated is None:
            pyproject_path = project_path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as fp:
                    d = tomli.load(fp)

                try:
                    v = d["tool"]["robotpy"]["pyfrc"]["isolated"]
                except KeyError:
                    pass
                else:
                    if not isinstance(v, bool):
                        raise ValueError(
                            f"tool.robotpy.pyfrc.isolated must be a boolean value (got {v})"
                        )

                    isolated = v

                try:
                    v = d["tool"]["robotpy"]["pyfrc"]["init_timeout"]
                except KeyError:
                    pass
                else:
                    if not isinstance(v, (int, float)):
                        raise ValueError(
                            f"tool.robotpy.pyfrc.init_timeout must be a number (got {v})"
                        )
                    elif not (v > 0):
                        raise ValueError(
                            f"tool.robotpy.pyfrc.init_timeout must be a positive number (got {v})"
                        )

                    init_timeout = float(v)

        if isolated is None:
            isolated = True

        try:
            return self._run_test(
                main_file,
                project_path,
                robot_class,
                builtin,
                isolated,
                coverage_mode,
                verbose,
                pytest_args,
                jobs,
                init_timeout,
            )
        except _TryAgain:
            return self._run_test(
                main_file,
                project_path,
                robot_class,
                builtin,
                isolated,
                coverage_mode,
                verbose,
                pytest_args,
                jobs,
                init_timeout,
            )

    def _run_test(
        self,
        main_file: pathlib.Path,
        project_path: pathlib.Path,
        robot_class: typing.Type[wpilib.RobotBase],
        builtin: bool,
        isolated: bool,
        coverage_mode: bool,
        verbose: bool,
        pytest_args: typing.List[str],
        jobs: int,
        init_timeout: float,
    ):
        # find test directory, change current directory so pytest can find the tests
        # -> assume that tests reside in tests or ../tests

        curdir = pathlib.Path.cwd().absolute()

        self.try_dirs = [
            ((project_path / "tests").absolute(), False),
            ((project_path / ".." / "tests").absolute(), True),
        ]

        for d, chdir in self.try_dirs:
            if d.exists():
                builtin = False
                if chdir:
                    os.chdir(d)
                break
        else:
            if not builtin:
                print("ERROR: Cannot run robot tests, as test directory was not found!")
                retv = self._no_tests(main_file, project_path)
                return 1

            from ..tests import basic

            pytest_args.insert(0, abspath(inspect.getfile(basic)))

        try:
            if isolated:
                from ..test_support import pytest_isolated_tests_plugin

                retv = pytest.main(
                    pytest_args,
                    plugins=[
                        pytest_isolated_tests_plugin.IsolatedTestsPlugin(
                            robot_class, main_file, builtin, verbose, jobs, init_timeout
                        )
                    ],
                )
            else:
                retv = pytest.main(
                    pytest_args,
                    plugins=[
                        pytest_plugin.PyFrcPlugin(
                            robot_class, main_file, False, init_timeout
                        )
                    ],
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
        for d, _ in self.try_dirs:
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
