import contextlib

import hal
import wpilib

import pytest

from pyfrc.test_support.pytest_plugin import PyFrcPlugin
from pyfrc.tests.basic import test_practice as _test_practice


@contextlib.contextmanager
def get_plugin(cls):

    wpilib.DriverStation._reset()

    plugin = PyFrcPlugin(cls, None, None)
    plugin.pytest_runtest_setup()

    try:
        yield plugin, plugin.get_control()
    finally:
        plugin.pytest_runtest_teardown(None)


class SampleRobotInit(wpilib.SampleRobot):
    def robotInit(self):
        assert False


class SampleAutonomous(wpilib.SampleRobot):
    def autonomous(self):
        assert False


class SampleTeleop(wpilib.SampleRobot):
    def operatorControl(self):
        assert False


class IterativeRobotInit(wpilib.IterativeRobot):
    def robotInit(self):
        assert False


class IterativeAutoInit(wpilib.IterativeRobot):
    def autonomousInit(self):
        assert False


class IterativeAutoPeriodic(wpilib.IterativeRobot):
    def autonomousPeriodic(self):
        assert False


class IterativeTeleopInit(wpilib.IterativeRobot):
    def teleopInit(self):
        assert False


class IterativeTeleopPeriodic(wpilib.IterativeRobot):
    def teleopPeriodic(self):
        assert False


@pytest.mark.parametrize(
    "cls",
    [
        SampleRobotInit,
        SampleAutonomous,
        IterativeRobotInit,
        IterativeAutoInit,
        IterativeAutoPeriodic,
    ],
)
def test_auto_failure(cls):
    """Ensure that failures can be detected in autonomous mode"""
    with get_plugin(cls) as (plugin, control):
        control.set_autonomous(enabled=True)
        with pytest.raises(AssertionError):
            control.run_test(lambda tm: tm < 15)


@pytest.mark.parametrize(
    "cls",
    [
        SampleRobotInit,
        SampleTeleop,
        IterativeRobotInit,
        IterativeTeleopInit,
        IterativeTeleopPeriodic,
    ],
)
def test_teleop_failure(cls):
    """Ensure that failures can be detected in teleop mode"""
    with get_plugin(cls) as (plugin, control):
        control.set_operator_control(enabled=True)
        with pytest.raises(AssertionError):
            control.run_test(lambda tm: tm < 15)


class Iterative(wpilib.IterativeRobot):
    def robotInit(self):
        self.did_robot_init = True

    def disabledInit(self):
        self.did_disabled_init = True

    def disabledPeriodic(self):
        self.did_disabled_periodic = True

    def autonomousInit(self):
        self.did_auto_init = True

    def autonomousPeriodic(self):
        self.did_auto_periodic = True

    def teleopInit(self):
        self.did_teleop_init = True

    def teleopPeriodic(self):
        self.did_teleop_periodic = True


def test_iterative():
    """Ensure that all states of the iterative robot run"""
    with get_plugin(Iterative) as (plugin, control):
        _test_practice(plugin.get_control(), plugin.get_fake_time(), plugin.get_robot())

        robot = plugin.get_robot()
        assert robot.did_robot_init == True
        assert robot.did_disabled_init == True
        assert robot.did_disabled_periodic == True
        assert robot.did_auto_init == True
        assert robot.did_auto_periodic == True
        assert robot.did_teleop_init == True
        assert robot.did_teleop_periodic == True


class Sample(wpilib.SampleRobot):
    def robotInit(self):
        self.did_robot_init = True

    def disabled(self):
        self.did_robot_disabled = True

    def autonomous(self):
        self.did_autonomous = True

    def operatorControl(self):
        self.did_operator = True


def test_sample():
    """Ensure that all states of the sample robot run"""
    with get_plugin(Sample) as (plugin, control):
        _test_practice(plugin.get_control(), plugin.get_fake_time(), plugin.get_robot())

        robot = plugin.get_robot()
        assert robot.did_robot_init == True
        assert robot.did_robot_disabled == True
        assert robot.did_autonomous == True
        assert robot.did_operator == True
