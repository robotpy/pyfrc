"""
    The primary purpose of these tests is to run through your code
    and make sure that it doesn't crash. If you actually want to test
    your code, you need to write your own custom tests to tease out
    the edge cases.
    
    To use these, add the following to a python file in your tests directory::
    
        from pyfrc.tests import *
    
"""

import math
import pytest

from .. import config

_gsms = config.config_obj["pyfrc"]["game_specific_messages"]


@pytest.mark.parametrize("gamedata", _gsms if _gsms else [""])
def test_autonomous(control, fake_time, robot, gamedata):
    """Runs autonomous mode by itself"""

    # run autonomous mode for 15 seconds
    control.game_specific_message = gamedata
    control.set_autonomous(enabled=True)
    control.run_test(lambda tm: tm < 15)

    # make sure autonomous mode ran for 15 seconds
    assert int(fake_time.get()) == 15


@pytest.mark.filterwarnings("ignore")
def test_disabled(control, fake_time, robot):
    """Runs disabled mode by itself"""

    # run disabled mode for 5 seconds
    control.set_autonomous(enabled=False)
    control.run_test(lambda tm: tm < 5)

    # make sure disabled mode ran for 5 seconds
    assert int(fake_time.get()) == 5


@pytest.mark.filterwarnings("ignore")
def test_operator_control(control, fake_time, robot):
    """Runs operator control mode by itself"""

    # run operator mode for 15 seconds
    control.set_operator_control(enabled=True)
    control.run_test(lambda tm: tm < 15)

    # make sure operator mode ran for 15 seconds
    assert int(fake_time.get()) == 15


@pytest.mark.filterwarnings("ignore")
def test_practice(control, fake_time, robot):
    """Runs through the entire span of a practice match"""

    class TestController:
        def __init__(self):
            self.mode = None

            self.disabled = 0
            self.autonomous = 0
            self.teleop = 0

        def on_step(self, tm):
            """
            Called on each simulation step. This runs through each mode,
            and asserts that the robot didn't spend too much time in any
            particular mode.

            If you get an assertion error here, it can mean a lot of
            different things, but typically it means you called Timer.delay()
            somewhere with a parameter greater than a few milliseconds..
            which is almost always a bad idea, and your robot will ignore
            your input for a few seconds.

            :param tm: The current robot time
            """

            mode = control.get_mode()
            if mode == self.mode:
                return

            if mode == "autonomous":
                self.autonomous += 1
                assert int(math.floor(fake_time.get())) == 5

            elif mode == "teleop":
                self.teleop += 1
                assert int(math.floor(fake_time.get())) == 21

            elif mode == "disabled":
                self.disabled += 1

                if self.disabled == 1:
                    # Time must be pretty close to zero at this point.
                    # If it's not, you called Timer.delay() somewhere you
                    # shouldn't have before the test started... you can
                    # try getting rid of the delay by only doing it when
                    # RobotBase.isSimulation() returns False
                    assert int(math.floor(fake_time.get())) == 0
                else:
                    assert int(math.floor(fake_time.get())) == 20
            else:
                assert False, "Internal error!"

            self.mode = mode

    if _gsms:
        control.game_specific_message = _gsms[0]

    control.set_practice_match()
    tc = control.run_test(TestController)

    assert int(math.floor(fake_time.get())) == 36

    # If an error occurs here, for some reason a mode got called too many times
    assert tc.disabled == 2
    assert tc.autonomous == 1
    assert tc.teleop == 1
