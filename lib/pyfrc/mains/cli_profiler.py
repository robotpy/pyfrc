
import subprocess
import sys


def run(run_fn, file_location):

    try:
        import cProfile
    except ImportError:
        print("Error importing cProfile module for profiling, your python interpreter may not support profiling\n", file=sys.stderr)
        return 1

    # construct the arguments to run the profiler
    args = [sys.executable, '-m', 'cProfile', '-s', 'tottime', file_location] + sys.argv[1:]
    
    return subprocess.call(args)
    