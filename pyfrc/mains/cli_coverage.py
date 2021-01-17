import argparse
import inspect
from os.path import dirname
import subprocess
import sys


class PyFrcCoverage:
    """
    Wraps other commands by running them via the coverage module. Requires
    the coverage module to be installed.
    """

    def __init__(self, parser):
        parser.add_argument(
            "args", nargs=argparse.REMAINDER, help="Arguments to pass to robot.py"
        )

    def run(self, options, robot_class, **static_options):

        print("tests+coverage are not yet implemented for RobotPy 2020")
        return 1

        try:
            import coverage
        except ImportError:
            print(
                "Error importing coverage module for code coverage testing, did you install it?\n"
                + "You can download it at https://pypi.python.org/pypi/coverage\n",
                file=sys.stderr,
            )
            return 1

        if len(options.args) == 0:
            print("ERROR: Coverage command requires arguments to run other commands")
            return 1

        file_location = inspect.getfile(robot_class)

        option_args = list(options.args)
        if option_args[0] == "test":
            option_args.insert(1, "--coverage-mode")

        # construct the arguments to run coverage
        args = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--source",
            dirname(file_location),
            file_location,
        ] + list(options.args)

        retval = subprocess.call(args)
        if retval != 0:
            return retval

        args = [sys.executable, "-m", "coverage", "report", "-m"]

        return subprocess.call(args)
