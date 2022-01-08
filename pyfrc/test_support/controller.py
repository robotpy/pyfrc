import contextlib
import typing
import wpilib
import threading
import pytest

from wpilib.simulation import DriverStationSim, stepTiming


class TestController:
    def __init__(self, reraise, robot: wpilib.RobotBase):
        self._reraise = reraise

        self._thread: typing.Optional[threading.Thread] = None
        self._robot = robot

        self._starting = threading.Condition()
        self._robot_started = False
        self._robot_finished = False

    def _robot_thread(self, robot):

        with self._starting:
            self._robot_started = True
            self._starting.notify_all()

        with self._reraise(catch=True):
            assert robot is not None  # shouldn't happen...

            try:
                robot.startCompetition()
                assert self._robot_finished
            finally:
                # always call endCompetition or python hangs
                robot.endCompetition()
                del robot

    @contextlib.contextmanager
    def run_robot(self):
        """
        Use this in a "with" statement to start your robot code at the
        beginning of the with block, and end your robot code at the end
        of the with block.
        """

        # remove robot reference so it gets cleaned up when gc.collect() is called
        robot = self._robot
        self._robot = None

        self._thread = th = threading.Thread(
            target=self._robot_thread, args=(robot,), daemon=True
        )
        th.start()

        with self._starting:
            assert self._starting.wait_for(lambda: self._robot_started, timeout=0.5)

        try:
            # in this block you should tell the sim to do sim things
            yield
        finally:
            self._robot_finished = True
            robot.endCompetition()

        # the robot thread should exit quickly
        th.join(timeout=1)
        if th.is_alive():
            pytest.fail("robot did not exit within 2 seconds")

        self._robot = None
        self._thread = None

    @property
    def robot_is_alive(self) -> bool:
        """
        True if the robot code is alive
        """
        th = self._thread
        if not th:
            return False

        return th.is_alive()

    def step_timing(self, *, seconds: float, autonomous: bool, enabled: bool) -> float:
        """
        This utility will increment simulated time, while pretending that
        there's a driver station connected and delivering new packets
        every 0.2 seconds.

        :param seconds:    Number of seconds to run (will step in increments of 0.2)
        :param autonomous: Tell the robot that it is in autonomous mode
        :param enabled:    Tell the robot that it is enabled

        :returns: Number of seconds time was incremented
        """

        assert seconds > 0

        DriverStationSim.setDsAttached(True)
        DriverStationSim.setAutonomous(autonomous)
        DriverStationSim.setEnabled(enabled)

        tm = 0.0

        while tm < seconds + 0.01:
            DriverStationSim.notifyNewData()
            stepTiming(0.2)
            assert self.robot_is_alive
            tm += 0.2

        return tm
