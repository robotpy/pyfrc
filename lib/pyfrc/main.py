
import inspect
import os
import sys

from .version import __version__
from distutils.version import StrictVersion


def run(min_version=None):
    '''
        This function gets run from your robot code something like this:
        
            if __name__ == '__main__':
                retval = wpilib.run()
                exit(retval)
            
        This syntax ensures that the code will never run on the cRio, as the
        robot code is not the main code module.
        
        This will parse command line arguments, and allow the user to perform
        a number of different actions on the robot code.
        
        :param min_version:    Specify the minimum version of pyfrc required
                               to run tests
    '''
    
    if min_version is not None:
        pyfrc_version = StrictVersion(__version__)
        min_version = StrictVersion(min_version)
        
        if pyfrc_version < min_version:
            print("ERROR: robot code requires pyfrc %s or later (currently running %s)" % (min_version, pyfrc_version))
            return 1
    
    if len(sys.argv) == 1:
        print("Usage: %s upload|test ...", file=sys.stderr)
        return 1
    
    try:
        frame = inspect.currentframe()
        if frame is None:
            print("Your python interpreter does not seem to support 'currentframe'. Please use a different python interpreter", file=sys.stderr)
            return 4
        
        frame = frame.f_back
        
        if 'run' not in frame.f_globals:
            print('Your robot code does not seem to have a "run" function. It must have a run function!', file=sys.stderr)
            return 3
        
        run_fn = frame.f_globals['run']
        file_location = os.path.abspath(frame.f_code.co_filename)
        
    finally:
        del frame
    
    arg1 = sys.argv[1]
    del sys.argv[1]
    
    if arg1 == 'upload':
        from .cli import cli_upload
        cli_upload.run(run_fn, file_location)
        
    elif arg1 == 'test':
        from .cli import cli_test
        cli_test.run(run_fn, file_location)
        
    elif arg1 == 'sim':
        from .cli import cli_sim
        cli_sim.run(run_fn, file_location)

    elif arg1 == 'netsim':
        from .cli import cli_sim
        cli_sim.run(run_fn, file_location, True)
