
import os
import sys

from os.path import abspath, dirname, exists, join

import pytest

from hal_impl import data, functions

# TODO: setting the plugins so that the end user can invoke py.test directly
# could be a useful thing. Will have to consider that later.

class PyFrcPlugin(object):

    def __init__(self, robot_class):
        self.robot_class = robot_class

    
    def pytest_runtest_setup(self):
        wpilib.internal.initialize_test()
    
    #
    # Fixtures
    #
    # Each one of these can be arguments to your test, and the result of the
    # corresponding function will be passed to your test as that argument.
    #
    
    @pytest.fixture()
    def control(self):
        pass
    
    @pytest.fixture()
    def fake_time(self):
        pass
    
    @pytest.fixture()
    def robot(self):
        myrobot = self.run_fn()
        
        # validate robot + results
        
        if myrobot is None:
            pytest.fail("ERROR: the run() function in robot.py MUST return an instance of your robot class")
        
        if not isinstance(myrobot, wpilib.SimpleRobot) and not isinstance(myrobot, wpilib.IterativeRobot):
            pytest.fail("ERROR: the object returned from the run function MUST return an instance of a robot class that inherits from wpilib.SimpleRobot or wpilib.IterativeRobot")

        # if they forget to do this, it's an annoying problem to diagnose on the cRio... 
        if not hasattr(myrobot, 'watchdog') or not myrobot.watchdog:
            pytest.fail("ERROR: class '%s' must call super().__init__() in its constructor" % (myrobot.__class__.__name__))
            
        if not myrobot._sr_competition_started:
            pytest.fail("ERROR: Your run() function must call StartCompetition() on your robot class")
                
        return myrobot
    
    @pytest.fixture
    def robot_file(self):
        return self.file_location
    
    @pytest.fixture()
    def robot_path(self):
        return dirname(self.file_location)
    
    @pytest.fixture()
    def wpilib(self):
        return wpilib

#
# main test class
#
class PyFrcTest(object):
    
    def __init__(self, parser):
        parser.add_argument('--ignore_mising_test', default=False, 
                            action = 'store_true', 
                            help= 'ignore failure if tests are missing')
    
    def run(self, options, robot_class):
    
        # find test directory, change current directory so py.test can find the tests
        # -> assume that tests reside in tests or ../tests
        
        test_directory = None
        root = abspath(os.getcwd())
        
        try_dirs = [join(root, 'tests'), abspath(join(root, '..', 'tests'))]
        
        for d in try_dirs:
            if exists(d):
                test_directory = d
                break
        
        if test_directory is None:
            print("Cannot run robot tests, as test directory was not found. Looked for tests at:")
            for d in try_dirs:
                print('- %s' % d)
            return 0 if ignore_missing_test else 1
        
        os.chdir(test_directory)
        
        return pytest.main(sys.argv[1:], plugins=[PyFrcPlugin(robot_class)])

