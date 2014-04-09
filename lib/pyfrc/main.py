
import inspect
import os
import sys

from .version import __version__
from distutils.version import StrictVersion

def require_version(min_version=None):
    '''
        You should *always* call this
         
        :param min_version:    Specify the minimum version of pyfrc required
                               to run tests.
        :return:               True if the version requirement is met, False otherwise
    '''
    if min_version is not None:
        pyfrc_version = StrictVersion(__version__)
        min_version = StrictVersion(min_version)
        
        if pyfrc_version < min_version:
            print("ERROR: robot code requires pyfrc %s or later (currently running %s)" % (min_version, pyfrc_version))
            return False
        
    return True

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
    
    usage_args = 'netsim|sim|test|upload ...'
    
    if not require_version(min_version):
        exit(2)
    
    if len(sys.argv) == 1:
        print("Usage: %s coverage|%s" % (sys.argv[0], usage_args), file=sys.stderr)
        exit(1)
    
    try:
        frame = inspect.currentframe()
        if frame is None:
            print("Your python interpreter does not seem to support 'currentframe'. Please use a different python interpreter", file=sys.stderr)
            exit(3)
        
        frame = frame.f_back
        
        if 'run' not in frame.f_globals:
            print('Your robot code does not seem to have a "run" function. It must have a run function!', file=sys.stderr)
            exit(4)
        
        run_fn = frame.f_globals['run']
        file_location = os.path.abspath(frame.f_code.co_filename)
        
    finally:
        del frame
    
    from . import config
    
    arg1 = sys.argv[1]
    del sys.argv[1]
    
    config.mode = arg1
    
    if arg1 == '--coverage-passthru':
        
        # Set this so randomized unit tests can be skipped
        
        config.coverage_mode = True
        
        if len(sys.argv) == 1:
            print("Usage: %s coverage %s" % (sys.argv[0], usage_args), file=sys.stderr)
            exit(1)
        
        arg1 = sys.argv[1]
        del sys.argv[1]
        
    
    if arg1 == 'upload':
        from .cli import cli_upload
        retval = cli_upload.run(run_fn, file_location)
        
    elif arg1 == 'test':
        from .cli import cli_test
        retval = cli_test.run(run_fn, file_location)
        
    elif arg1 == 'coverage':
        from .cli import cli_coverage
        retval = cli_coverage.run(run_fn, file_location)
        
    elif arg1 == 'profiler':
        from .cli import cli_profiler
        retval = cli_profiler.run(run_fn, file_location)
        
    elif arg1 == 'sim':
        from .cli import cli_sim
        retval = cli_sim.run(run_fn, file_location)

    elif arg1 == 'netsim':
        from .cli import cli_sim
        retval = cli_sim.run(run_fn, file_location, True)
        
    else:
        print("ERROR: Invalid argument '%s'" % arg1, file=sys.stderr)
        retval = 5
    
    exit(retval)
