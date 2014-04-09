'''
    This imports all of the generic test modules that can be applied to a
    SimpleRobot-based robot. The idea is you should be able to do something
    like the following:
    
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
