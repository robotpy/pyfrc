"""
The primary purpose of these tests is to run through your code
and make sure that it doesn't crash. If you actually want to test
your code, you need to write your own custom tests to tease out
the edge cases.

To use these, add the following to a python file in your tests directory::

    from pyfrc.tests import *

"""

import pytest
import typing

if typing.TYPE_CHECKING:
    from pyfrc.test_support.controller import TestController


def test_autonomous(control: "TestController"):
    """Runs autonomous mode by itself"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)

        # Run enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=True, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)


@pytest.mark.filterwarnings("ignore")
def test_disabled(control: "TestController", robot):
    """Runs disabled mode by itself"""

    with control.run_robot():
        # Run disabled + autonomous for a short period
        control.step_timing(seconds=5, autonomous=True, enabled=False)

        # Run disabled + !autonomous for a short period
        control.step_timing(seconds=5, autonomous=False, enabled=False)


@pytest.mark.filterwarnings("ignore")
def test_operator_control(control: "TestController"):
    """Runs operator control mode by itself"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)

        # Run enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=False, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)


@pytest.mark.filterwarnings("ignore")
def test_practice(control: "TestController"):
    """Runs through the entire span of a practice match"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)

        # Run autonomous + enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=True, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)

        # Run teleop + enabled for 2 minutes
        control.step_timing(seconds=120, autonomous=False, enabled=True)
