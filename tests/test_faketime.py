
import pytest

from pyfrc.test_support.fake_time import TestEnded, TestRanTooLong, FakeTime

def test_faketime_1():
    '''Test expiration'''
    
    ft = FakeTime()
    ft._setup()
    ft.set_time_limit(5)
    
    with pytest.raises(TestRanTooLong):
        ft.increment_time_by(10)

def assert_float(f1, f2):
    assert abs(f1 - f2) < 0.001
     
class StepChecker:
        
    def __init__(self):
        self.expected = 0.02
    
    def on_step(self, tm):
        assert_float(tm, self.expected)
        self.expected += 0.02 
        return True
        
def test_faketime_2():
    '''Test calling the step function '''
    
    ft = FakeTime()
    ft._setup()
    ft.set_time_limit(5)
    
    sc = StepChecker()
    ft._ds_cond._on_step = sc.on_step
    
    ft.increment_new_packet()
    ft.increment_new_packet()
    ft.increment_new_packet()
    
    assert_float(ft.get(), 0.06)
    assert_float(sc.expected, 0.06 + 0.02)

def test_faketime_3():
    '''Test calling the step function with varying lengths'''
        
    ft = FakeTime()
    ft._setup()
    ft.set_time_limit(5)
    
    sc = StepChecker()
    ft._ds_cond._on_step = sc.on_step
    
    ft.increment_time_by(0.005)
    ft.increment_time_by(0.01)
    ft.increment_time_by(0.02)
    ft.increment_time_by(0.03)
    ft.increment_time_by(0.04)
    ft.increment_time_by(0.05)
    
    tm = 0.005 + 0.01 + 0.02 + 0.03 + 0.04 + 0.05
    assert_float(ft.get(), tm)
    assert_float(sc.expected, 0.16)



