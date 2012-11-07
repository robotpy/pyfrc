'''
    Test harness to be used with fake_wpilib. Ideally, this should be
    generic enough to test any robot code you throw at it.
    
    How it works:
    
        This base test program doesn't really have any intelligence, it
        just loads robot code from a specified location and then runs
        code in a separately defined test module. 
        
    Implementing your own tests:
        
        In the 'tests' directory, add your own testname.py file
        
        In the module, there should be two things:
            - a variable called 'robot_path', which has the path of your
            robot code, relative to the directory your tests are located
            - A function called 'run_tests', which takes two arguments:
                - module:   The module for your robot code
                - myrobot:  The robot class returned by your run() function
        
    Running your tests:
    
        test.bat testname
        test.sh testname
        
        .. or some variation thereof. Don't run test.py directly, otherwise
        the pycache will be generated, which we don't want.
        
    TODO:
    
        - Need to make creating tests easier, add a template, base class,
        or something that makes the logic a lot easier. 
        
        - Fake wpilib needs a better way to access the raw objects, instead
        of traversing through the robot module to get at them. 
        
    
'''

from glob import glob
import imp
import os
from optparse import OptionParser
import sys


testdir_path = os.path.dirname(os.path.abspath(__file__))

try:
    import fake_wpilib as wpilib
except ImportError:
    sys.path.append(testdir_path)
    import fake_wpilib as wpilib


def import_robot(robot_path):

    # convert \ to / or whatever, depending on the platform
    robot_path = os.path.abspath(robot_path)
    sys.path.append(robot_path)
    
    # setup the robot code
    import robot

    myrobot = wpilib.initialize_robot()

    return (robot, myrobot)
    
    
def run_test( test_module_name ):
    
    test_module_name = args[0]
    
    if test_module_name not in modules:
        sys.stderr.write("Invalid module name \"%s\"\n" % test_module_name)
        exit(1)
        
    # setup options
    ds = wpilib.DriverStation.GetInstance()
    ds.fms_attached = options.fms_attached

    # import the test module
    test_module = imp.load_source(test_module_name, os.path.join( modules_path, test_module_name + '.py'))
    
    # add the robot directory to the path, so it can load other things
    if not hasattr(test_module, 'robot_path'):
        sys.stderr.write("ERROR: the test module '%s' does not have a 'robot_path' global variable\n" % test_module_name)
        exit(1)
    
    (robot, myrobot) = import_robot(os.path.join(modules_path, test_module.robot_path))
    
    if myrobot is None:
        sys.stderr.write("ERROR: the run() function in robot.py MUST return an instance of your robot class\n")
        exit(1)
       
    if not hasattr(myrobot, '_sr_initialized') or not myrobot._sr_initialized:
        sys.stderr.write("ERROR: Your robot class must inherit from SimpleRobot and you must call SimpleRobot.__init__(self)\n")
        exit(1)
        
    if not myrobot._sr_competition_started:
        sys.stderr.write("ERROR: Your run() function must call StartCompetition() on your robot class\n")
        exit(1)
    
    #
    # Finally, run the tests
    #
    
    test_module.run_tests( robot, myrobot )
    
    print( "Test complete." )
    
    

if __name__ == '__main__':

    parser = OptionParser()
    
    parser.add_option(  '--fms',
                        action='store_true', dest='fms_attached', default=False,
                        help='Pretend that the robot is on the field')
                        
    parser.add_option(  '--import',
                        dest='import_dir', default=None,
                        help='Import robot.py from a test directory without running')
                        
    parser.add_option(  '--test-modules',
                        dest='modules_path', default=None,
                        help='Directory that the test modules can be found in')
                        
    (options, args) = parser.parse_args()
    
    if options.import_dir is not None:
        import_robot(options.import_dir)
        print("Import successful")
        exit(0)
    
    if options.modules_path is None:
        parser.error("don't know where to find the test modules!")
        
    modules_path = os.path.abspath(options.modules_path)
    modules = [ os.path.basename(module[:-3]) for module in glob(os.path.join(modules_path, '*.py')) ]
    
    if len(args) == 1:
        run_test(args[0])
        exit(0)
    
    err = "You must specify a test module to run. Available test modules\nin %s:\n" % modules_path 
    
    for module in sorted(modules):
        err += "  %s\n" % module
        
    parser.error(err)
    
    

