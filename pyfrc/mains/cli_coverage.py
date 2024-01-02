import argparse
from os.path import dirname
import pathlib
import subprocess
import sys
import typing


class PyFrcCoverage:
    """
    Wraps other commands by running them via the coverage module.

    Requires the coverage module to be installed.
    """

    def __init__(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--parallel-mode", action="store_true", help="Run coverage in parallel mode"
        )
        parser.add_argument(
            "args", nargs=argparse.REMAINDER, help="Arguments to pass to robot.py"
        )

    def run(
        self,
        main_file: pathlib.Path,
        project_path: pathlib.Path,
        parallel_mode: bool,
        args: typing.List[str],
    ):
        try:
            import coverage
        except ImportError:
            print(
                "Error importing coverage module for code coverage testing, did you install it?\n"
                + "You can download it at https://pypi.python.org/pypi/coverage\n",
                file=sys.stderr,
            )
            return 1

        if len(args) == 0:
            print("ERROR: Coverage command requires arguments to run other commands")
            return 1

        option_args = args
        if option_args[0] == "test":
            option_args.insert(1, "--coverage-mode")

        # construct the arguments to run coverage
        args = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--source",
            str(project_path),
        ]
        if parallel_mode:
            args.append("--parallel-mode")

        args += ["-m", "robotpy", "--main", main_file]
        args += option_args

        print("+", *args, file=sys.stderr)
        retval = subprocess.call(args)
        if retval != 0:
            return retval

        if parallel_mode:
            subprocess.call([sys.executable, "-m", "coverage", "combine"])

        args = [sys.executable, "-m", "coverage", "report", "-m"]

        return subprocess.call(args)
