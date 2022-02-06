import gc
import pathlib
import typing

import pytest
import weakref


import hal.simulation
import networktables
import wpilib
from wpilib.simulation import DriverStationSim, pauseTiming, restartTiming

from .controller import TestController
from ..physics.core import PhysicsInterface


class PyFrcPlugin:
    """
    Pytest plugin. Each documented member function name can be an argument
    to your test functions, and the data that these functions return will
    be passed to your test function.
    """

    def __init__(self, robot_class: type[wpilib.RobotBase], robot_file: pathlib.Path):

        self._robot_file = robot_file
        self._robot_class = robot_class
        self._robot: typing.Optional[wpilib.RobotBase] = None

        self._started = False

        # attach physics
        physics = PhysicsInterface._create_and_attach(
            self._robot_class,
            self._robot_file.parent,
        )
        if physics:
            physics.log_init_errors = False
        else:
            self._robot_class._simulationInit = lambda *a: None
            self._robot_class._simulationPeriodic = lambda *a: None

    def pytest_runtest_setup(self):
        # This function needs to do the same things that RobotBase.main does
        # plus some extra things needed for testing

        networktables.NetworkTables.startLocal()

        pauseTiming()
        restartTiming()

        wpilib.DriverStation.silenceJoystickConnectionWarning(True)
        DriverStationSim.setAutonomous(False)
        DriverStationSim.setEnabled(False)
        DriverStationSim.notifyNewData()

        self._robot = self._robot_class()

        self._started = True

    def pytest_runtest_teardown(self, nextitem):

        started = self._started
        self._started = False

        del self._robot

        # Ensure all objects are destroyed so that HAL handles are released
        gc.collect()

        # If the unit test never started, then the rest may hang. Bail
        # out now instead, and choose to have more errors later.
        if not started:
            return

        # Reset the HAL handles
        hal.simulation.resetGlobalHandles()

        # Reset the HAL data
        hal.simulation.resetAllData()

        # goal: all robot state should be reset via hal.shutdown, which can be
        # called multiple times (even though it's not documented)
        # hal.shutdown()
        # .. in practice, hal.shutdown doesn't do anything

        # shutdown networktables
        networktables.NetworkTables.stopLocal()

        # TODO: reset simulation objects

    #
    # Fixtures
    #
    # Each one of these can be arguments to your test, and the result of the
    # corresponding function will be passed to your test as that argument.
    #

    @pytest.fixture(scope="function")
    def control(self, reraise) -> TestController:
        """
        A pytest fixture that provides control over the robot
        """
        return TestController(reraise, self._robot)

    @pytest.fixture(scope="function")
    def robot(self) -> wpilib.RobotBase:
        """
        Your robot instance
        """
        return weakref.proxy(self._robot)

    @pytest.fixture()
    def robot_file(self) -> pathlib.Path:
        """The absolute filename your robot code is started from"""
        return self._robot_file

    @pytest.fixture()
    def robot_path(self) -> pathlib.Path:
        """The absolute directory that your robot code is located at"""
        return self._robot_file.parent
