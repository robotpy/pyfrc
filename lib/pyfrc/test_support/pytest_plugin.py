
import pytest

import hal_impl
from . import fake_time, pyfrc_fake_hooks

from .controller import TestController


class PyFrcPlugin(object):

    def __init__(self, robot_class, robot_file, robot_path):
        self.robot_class = robot_class
        
        self._robot_file = robot_file
        self._robot_path = robot_path
        
        # Setup fake time
        self._fake_time = fake_time.FakeTime()
        
        # Setup control instance
        self._control = None
        
        # Setup the hal hooks so we can control time
        hal_impl.functions.hooks = pyfrc_fake_hooks.PyFrcFakeHooks(self._fake_time)
        hal_impl.functions.reset_hal()
    
    def pytest_runtest_setup(self):
    
        import networktables
        networktables.NetworkTable.setTestMode()
        
        self._fake_time.reset()
        hal_impl.functions.reset_hal()
        
        self._test_controller = TestController(self._fake_time)
        
        self._robot = self.robot_class()
        
        # patch the robot
    
    def pytest_runtest_teardown(self):
        self._robot = None
        
        import wpilib._impl.utils
        wpilib._impl.utils.reset_wpilib()
        
        import networktables
        networktables.NetworkTable._staticProvider = None
    
    #
    # Fixtures
    #
    # Each one of these can be arguments to your test, and the result of the
    # corresponding function will be passed to your test as that argument.
    #
    
    @pytest.fixture()
    def control(self):
        '''
            A fixture that provides control over the robot
            
            :rtype: :class:`.TestController`
        '''
        return self._test_controller
    
    @pytest.fixture()
    def fake_time(self):
        '''
            A fixture that gives you control over the time your robot is using
            
            :rtype:   :class:`.FakeTime`
        '''
        return self._fake_time
    
    @pytest.fixture()
    def hal_data(self):
        '''
            Provides access to a dict with all the device data about the robot
        '''
        return hal_impl.data.hal_data
    
    @pytest.fixture()
    def robot(self):
        '''Your robot instance'''
        return self._robot
    
    @pytest.fixture()
    def robot_file(self):
        '''The absolute filename your robot code is started from'''
        return self._robot_file
    
    @pytest.fixture()
    def robot_path(self):
        '''The absolute directory that your robot code is located at'''
        return self._robot_path
    
    @pytest.fixture()
    def wpilib(self):
        '''The wpilib module. Provided for backwards compatibility'''
        import wpilib
        return wpilib
