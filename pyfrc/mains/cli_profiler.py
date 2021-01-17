import argparse
import inspect
from os.path import abspath
import subprocess
import sys


class PyFrcProfiler:
    """
    Wraps other commands by running them via the built in cProfile module.
    Use this to profile your program and figure out where you're spending
    a lot of time (note that cProfile only profiles the main thread)
    """

    def __init__(self, parser):
        parser.add_argument(
            "-o", "--outfile", default=None, help="Save stats to <outfile>"
        )
        parser.add_argument(
            "args", nargs=argparse.REMAINDER, help="Arguments to pass to robot.py"
        )

    def run(self, options, robot_class, **static_options):

        print("profiling is not yet implemented for RobotPy 2020")
        return 1

        from .. import config

        config.mode = "profiler"

        try:
            import cProfile
        except ImportError:
            print(
                "Error importing cProfile module for profiling, your python interpreter may not support profiling\n",
                file=sys.stderr,
            )
            return 1

        if len(options.args) == 0:
            print("ERROR: Profiler command requires arguments to run other commands")
            return 1

        file_location = abspath(inspect.getfile(robot_class))

        if options.outfile:
            profile_args = ["-o", options.outfile]
        else:
            profile_args = ["-s", "tottime"]

        # construct the arguments to run the profiler
        args = (
            [sys.executable, "-m", "cProfile"]
            + profile_args
            + [file_location]
            + options.args
        )

        return subprocess.call(args)
