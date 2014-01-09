
import sys

#
# Test function
#

def run(run_fn, file_location):
    
    # setup path correctly so things are importable
    # -> remove sys.path? no... 
    
    # something something
    
        # how to find tests:
    # - once we find the robot source code, we look for a test directory
    #   ... ooh, can we hook into py.test to do the introspection for us instead? That would be sweet, and
    #       provide a lot of debugging capability that we wouldn't otherwise have
    #   ... if setup is via pip, we can bring in py.test automatically
    #       -> need to test that on windows
    
    #   ... or perhaps this is a py.test plugin? then we automatically become a fixture and stuff. 
    
    # how does this access other modules?
    # -> setup python path to point at robot directory in setup

    
    
    try:
        import pytest
    except ImportError as e:
        print("Error importing py.test module, is it installed? Error was: %s" % e, file=sys.stderr)
        return 1
        
    pytest.main()
    
    # need to reset wpilib internal state inbetween each test?
    
    # need to setup robot/wpilib fixtures
    
    #
