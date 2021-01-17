import pytest

import hal_impl
from . import fake_time, pyfrc_fake_hooks

from .controller import TestController


class ThreadStillRunningError(Exception):
    pass


class PyFrcPlugin:
    """
    Pytest plugin. Each documented member function name can be an argument
    to your test functions, and the data that these functions return will
    be passed to your test function.
    """

    def __init__(self, robot_class, robot_file, robot_path):
        self.robot_class = robot_class

        self._robot_file = robot_file
        self._robot_path = robot_path

        # Setup fake time
        self._fake_time = fake_time.FakeTime()

        # Setup control instance
        self._control = None

        self._started = False

        # Setup the hal hooks so we can control time
        # -> The hook doesn't have any state, so we initialize it only once
        hal_impl.functions.hooks = pyfrc_fake_hooks.PyFrcFakeHooks(self._fake_time)

    def pytest_runtest_setup(self):
        # This function needs to do the same things that RobotBase.main does,
        # plus some extra things needed for testing

        #
        # Initialization order is important, because there are a bunch
        # of inter-related things happening here.
        #
        # - Initialize networktables first since it has no dependencies
        # - Initialize the fake time, because the HAL uses it
        #   - This initializes the driver station, but it doesn't need HAL yet
        # - Reset HAL data
        # - Initialize RobotBase
        #

        import networktables

        if hasattr(networktables, "NetworkTables"):
            if hasattr(networktables.NetworkTables, "setTestMode"):
                networktables.NetworkTables.setTestMode()
            else:
                networktables.NetworkTables.startTestMode()
        else:
            networktables.NetworkTable.setTestMode()

        self._fake_time.initialize()
        self._test_controller = TestController(self._fake_time)

        hal_impl.functions.reset_hal()

        import wpilib

        hwcfg = getattr(wpilib.RobotBase, "initializeHardwareConfiguration", None)
        if hwcfg:
            hwcfg()

        self._test_controller._robot = self.robot_class()

        # TODO: Remove after 2016
        getattr(self._test_controller._robot, "prestart", lambda: True)()

        assert hasattr(
            self._test_controller._robot, "_RobotBase__initialized"
        ), "If your robot class has an __init__ function, it must call super().__init__()!"

        self._started = True

    def pytest_runtest_teardown(self, nextitem):

        started = self._started
        self._started = False

        # Let any child threads run in realtime to allow cancelling if it
        # has been implemented.
        self._fake_time.teardown()
        self._test_controller = None

        # If the unit test never started, then the rest may hang. Bail
        # out now instead, and choose to have more errors later.
        if not started:
            return

        import wpilib._impl.utils

        wpilib._impl.utils.reset_wpilib()

        import networktables

        if hasattr(networktables, "NetworkTables"):
            networktables.NetworkTables.shutdown()
        else:
            networktables.NetworkTable._staticProvider.close()
            networktables.NetworkTable._staticProvider = None

        if not self._fake_time.children_stopped():
            raise ThreadStillRunningError(
                "Make sure spawning class has free() "
                "method to stop thread and is registered with "
                "Resource.add_global_resource()."
            )

    #
    # Fixtures
    #
    # Each one of these can be arguments to your test, and the result of the
    # corresponding function will be passed to your test as that argument.
    #

    @pytest.fixture()
    def control(self):
        """
        A fixture that provides control over the robot

        :rtype: :class:`.TestController`
        """
        return self._test_controller

    @pytest.fixture()
    def fake_time(self):
        """
        A fixture that gives you control over the time your robot is using

        :rtype:   :class:`.FakeTime`
        """
        return self._fake_time

    @pytest.fixture()
    def hal_data(self):
        """
        Provides access to a dict with all the device data about the robot

        .. seealso:: For a listing of what the dict contains and some documentation, see
                     https://github.com/robotpy/robotpy-wpilib/blob/master/hal-sim/hal_impl/data.py
        """
        return hal_impl.data.hal_data

    @pytest.fixture()
    def robot(self):
        """Your robot instance"""
        return self._test_controller._robot

    @pytest.fixture()
    def robot_file(self):
        """The absolute filename your robot code is started from"""
        return self._robot_file

    @pytest.fixture()
    def robot_path(self):
        """The absolute directory that your robot code is located at"""
        return self._robot_path

    @pytest.fixture()
    def wpilib(self):
        """The :mod:`wpilib` module. Provided for backwards compatibility"""
        import wpilib

        return wpilib

    #
    # Internal use only because newer versions of pytest
    # don't allow calling fixtures directly
    #

    def get_control(self):
        return self._test_controller

    def get_fake_time(self):
        return self._fake_time

    def get_robot(self):
        return self._test_controller._robot
