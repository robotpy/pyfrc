'''
    These generic test modules can be applied to a
    :class:`wpilib.SimpleRobot` based robot. To use these, add the
    following to a python file in your tests directory::
    
        from pyfrc.tests.simple import *
'''

# import common test types
from ..docstring_test import test_docstrings

# simple-specific test types
from ..fuzz_test import test_simple_fuzz as test_fuzz

from .basic import (
    test_autonomous,
    test_disabled,
    test_operator_control,
    test_practice
)
