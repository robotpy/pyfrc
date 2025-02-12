import gc
import pathlib

from typing import Type

import pytest
import weakref

import hal
import hal.simulation
import ntcore
import wpilib
import wpilib.shuffleboard
from wpilib.simulation import DriverStationSim, pauseTiming, restartTiming
import wpilib.simulation

# TODO: get rid of special-casing.. maybe should register a HAL shutdown hook or something
try:
    import commands2
except ImportError:
    commands2 = None

from .controller import TestController
from ..physics.core import PhysicsInterface


class PyFrcPlugin:
    """
    Pytest plugin. Each documented member function name can be an argument
    to your test functions, and the data that these functions return will
    be passed to your test function.
    """

    def __init__(
        self,
        robot_class: Type[wpilib.RobotBase],
        robot_file: pathlib.Path,
        isolated: bool,
    ):
        self.isolated = isolated

        # attach physics
        physics, robot_class = PhysicsInterface._create_and_attach(
            robot_class,
            robot_file.parent,
        )

        # Tests need to know when robotInit is called, so override the robot
        # to do that
        class TestRobot(robot_class):
            def robotInit(self):
                try:
                    super().robotInit()
                finally:
                    self.__robotInitialized()

        TestRobot.__name__ = robot_class.__name__
        TestRobot.__module__ = robot_class.__module__
        TestRobot.__qualname__ = robot_class.__qualname__

        self._robot_file = robot_file
        self._robot_class = TestRobot

        self._physics = physics

        if physics:
            physics.log_init_errors = False

    #
    # Fixtures
    #
    # Each one of these can be arguments to your test, and the result of the
    # corresponding function will be passed to your test as that argument.
    #

    @pytest.fixture(scope="function", autouse=True)
    def robot(self):
        """
        Your robot instance

        .. note:: RobotPy/WPILib testing infrastructure is really sensitive
                  to ensuring that things get cleaned up properly. Make sure
                  that you don't store references to your robot or other
                  WPILib objects in a global or static context.
        """

        #
        # This function needs to do the same things that RobotBase.main does
        # plus some extra things needed for testing
        #
        # Previously this was separate from robot fixture, but we need to
        # ensure that the robot cleanup happens deterministically relative to
        # when handle cleanup/etc happens, otherwise unnecessary HAL errors will
        # bubble up to the user
        #

        nt_inst = ntcore.NetworkTableInstance.getDefault()
        nt_inst.startLocal()

        pauseTiming()
        restartTiming()

        wpilib.DriverStation.silenceJoystickConnectionWarning(True)
        DriverStationSim.setAutonomous(False)
        DriverStationSim.setEnabled(False)
        DriverStationSim.notifyNewData()

        robot = self._robot_class()

        # Tests only get a proxy to ensure cleanup is more reliable
        yield weakref.proxy(robot)

        # If running in separate processes, no need to do cleanup
        if self.isolated:
            # .. and funny enough, in isolated mode we *don't* want the
            # robot to be cleaned up, as that can deadlock
            self._saved_robot = robot
            return

        # reset engine to ensure it gets cleaned up too
        # -> might be holding wpilib objects, or the robot
        if self._physics:
            self._physics.engine = None

        # HACK: avoid motor safety deadlock
        wpilib.simulation._simulation._resetMotorSafety()

        del robot

        if commands2 is not None:
            commands2.CommandScheduler.resetInstance()

        # Double-check all objects are destroyed so that HAL handles are released
        gc.collect()

        # shutdown networktables before other kinds of global cleanup
        # -> some reset functions will re-register listeners, so it's important
        #    to do this before so that the listeners are active on the current
        #    NetworkTables instance
        nt_inst.stopLocal()
        nt_inst._reset()

        # Cleanup WPILib globals
        # -> preferences, SmartDashboard, Shuffleboard, LiveWindow, MotorSafety
        wpilib.simulation._simulation._resetWpilibSimulationData()
        wpilib._wpilib._clearSmartDashboardData()
        wpilib.shuffleboard._shuffleboard._clearShuffleboardData()

        # Cancel all periodic callbacks
        hal.simulation.cancelAllSimPeriodicCallbacks()

        # Reset the HAL handles
        hal.simulation.resetGlobalHandles()

        # Reset the HAL data
        hal.simulation.resetAllSimData()

        # Don't call HAL shutdown! This is only used to cleanup HAL extensions,
        # and functions will only be called the first time (unless re-registered)
        # hal.shutdown()

    @pytest.fixture(scope="function")
    def control(self, reraise, robot: wpilib.RobotBase) -> TestController:
        """
        A pytest fixture that provides control over your robot
        """
        return TestController(reraise, robot)

    @pytest.fixture()
    def robot_file(self) -> pathlib.Path:
        """The absolute filename your robot code is started from"""
        return self._robot_file

    @pytest.fixture()
    def robot_path(self) -> pathlib.Path:
        """The absolute directory that your robot code is located at"""
        return self._robot_file.parent
