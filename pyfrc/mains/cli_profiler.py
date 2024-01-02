import argparse
import inspect
from os.path import abspath
import pathlib
import subprocess
import sys
import typing


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
            "args", nargs=argparse.REMAINDER, help="Arguments to pass to robotpy module"
        )

    def run(
        self,
        main_file: pathlib.Path,
        outfile: typing.Optional[str],
        args: typing.List[str],
    ):
        try:
            import cProfile
        except ImportError:
            print(
                "Error importing cProfile module for profiling, your python interpreter may not support profiling\n",
                file=sys.stderr,
            )
            return 1

        if len(args) == 0:
            print("ERROR: Profiler command requires arguments to run other commands")
            return 1

        if outfile:
            profile_args = ["-o", outfile]
        else:
            profile_args = ["-s", "tottime"]

        # construct the arguments to run the profiler
        args = (
            [sys.executable, "-m", "cProfile"]
            + profile_args
            + ["-m", "robotpy", "--main", str(main_file)]
            + args
        )

        print("+", *args, file=sys.stderr)
        return subprocess.call(args)
