import inspect

from hal_impl import mode_helpers
from hal_impl.data import hal_data

from .fake_time import TestEnded


class _PracticeMatch:

    autonomous_period = 15
    operator_period = 15

    def __init__(self, on_step, controller):
        self._on_step = on_step
        self._controller = controller

    def on_step(self, tm):
        """
        Called when a driver station packet would be delivered
        """

        if tm < 5:
            self._controller.set_autonomous(False)

        elif tm < 5 + self.autonomous_period:
            self._controller.set_autonomous(True)

        elif tm < 5 + self.autonomous_period + 1:
            self._controller.set_operator_control(False)

        elif tm < 5 + self.autonomous_period + 1 + self.operator_period:
            self._controller.set_operator_control(True)

        else:
            return False

        if self._on_step is not None:
            retval = self._on_step(tm)
            if retval is not None:
                return retval

        return True


class TestController:
    """
    This object is used to control the robot during unit tests. You
    do not need to create an instance of this, instead use the
    ``controller`` fixture.

    To set a game specific message for autonomous mode, just
    set the 'game_specific_message' property of this object, and it will
    be setup correctly upon transition into autonomous mode.
    """

    def __init__(self, fake_time_inst):
        self._practice = False
        self._test_running = False
        self._ds_cond = fake_time_inst.ds_cond
        self.game_specific_message = None

    def get_mode(self):
        """Returns the current mode that the robot is in

        :returns: 'autonomous', 'teleop', 'test', or 'disabled'
        """

        ctrl = hal_data["control"]
        if not ctrl["enabled"]:
            return "disabled"
        if ctrl["autonomous"]:
            return "autonomous"
        if ctrl["test"]:
            return "test"

        return "teleop"

    def set_practice_match(self):
        """Call this function to enable a practice match. Must only
        be called before :meth:`run_test` is called.
        """

        assert not self._test_running
        self._practice = True

    def set_autonomous(self, enabled=True):
        """Puts the robot in autonomous mode"""
        mode_helpers.set_mode(
            "auto", enabled, game_specific_message=self.game_specific_message
        )

    def set_operator_control(self, enabled=True):
        """Puts the robot in operator control mode"""
        mode_helpers.set_mode("teleop", enabled)

    def set_test_mode(self, enabled=True):
        """Puts the robot in test mode (the robot mode, not related to unit testing)"""
        mode_helpers.set_mode("test", enabled)

    def run_test(self, controller=None):
        """
        Call this to execute the robot code. Cannot be called more than once
        in a single test.

        If the controller argument is a class, it will be constructed and the
        instance will be returned.

        :param controller: This can either be a function that takes a single
                           argument, or a class that has an 'on_step' function.
                           If it is a class, an instance will be created. Either
                           the function or the on_step function will be called
                           with a single parameter, which is the the current
                           robot time. If None, an error will be signaled unless
                           :meth:`set_practice_match` has been called.
        """

        # Can't call this twice!
        assert not self._test_running

        on_step = None
        retval = None

        if controller is not None:

            if inspect.isclass(controller):
                retval = controller()
                on_step = retval.on_step

            elif callable(controller):
                on_step = controller

            else:
                raise ValueError("Invalid controller parameter")

            info = inspect.getfullargspec(on_step)
            if len(info.args) > 0 and info.args[0] == "self":
                info.args.remove("self")

            if len(info.args) + len(info.kwonlyargs) != 1:
                raise ValueError(
                    "%s must be a function that takes a single argument" % on_step
                )

        # Setup the time hooks
        if self._practice:
            pm = _PracticeMatch(on_step, self)
            on_step = pm.on_step

        if on_step is not None:
            self._ds_cond._on_step = on_step
        else:
            raise ValueError(
                "The controller parameter must not be None OR you must call control.set_practice_match"
            )

        self._test_running = True

        try:
            self._robot.startCompetition()
        except TestEnded:
            pass
        except:
            raise

        return retval
