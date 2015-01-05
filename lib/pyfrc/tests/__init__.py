'''
    These generic test modules can be applied to :class:`wpilib.iterativerobot.IterativeRobot`
    and :class:`wpilib.samplerobot.SampleRobot` based robots. To use these, add the
    following to a python file in your tests directory::
    
        from pyfrc.tests import *
'''

# import basic tests
from .basic import (
    test_autonomous,
    test_disabled,
    test_operator_control,
    test_practice
)

# import common test types
from .docstring_test import test_docstrings

# simple-specific test types
from .fuzz_test import test_sample_fuzz as test_fuzz

