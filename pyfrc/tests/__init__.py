"""
    These generic test modules can be applied to :class:`wpilib.iterativerobot.IterativeRobot`
    and :class:`wpilib.samplerobot.SampleRobot` based robots.
"""

# import basic tests
from .basic import test_autonomous, test_disabled, test_operator_control, test_practice

# Other test types
from .fuzz_test import test_fuzz
