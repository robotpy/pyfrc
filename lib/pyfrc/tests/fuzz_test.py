'''
    The purpose of the fuzz 'test' is not exactly to 'do' anything, but
    rather it mashes the buttons and switches in various completely
    random ways to try and find any possible control situations and 
    such that would probably never *normally* come up, but.. well, 
    given a bit of bad luck, could totally happen. 
    
    Keep in mind that the results will totally different every time
    you run this, so if you find an error, fix it -- but don't expect
    that you'll be able to duplicate it with this test. Instead, you
    should design a specific test that can trigger the bug, to ensure
    that you actually fixed it.
'''

import pyfrc.config
import pytest
import random
import math
        
def fuzz_bool():
                    
    if random.randrange(0,2,1) == 0:
        return False
    else:
        return True
        
    
    
def fuzz_all(hal_data):

    # fuzz the eio switches    
    for dio in hal_data['dio']:
    
        # inputs only
        if not dio['is_input'] or not dio['initialized'] :
            continue
            
        # activate at random times
        dio['value'] = fuzz_bool()

            
    # fuzz the joysticks
    for stick in hal_data['joysticks']:
        if stick['has_source']:
            # axes 
            for axes in stick['axes']:
                if fuzz_bool():
                    axes = random.uniform(-1,1)
                    
            # buttons
            for button in stick['buttons']:
                    self._fuzz_bool(tm, j, self.ds.stick_buttons[i], stick[1])

                
    # fuzz analog channels
    for analog in hal_data['analog_in']:
        if analog['has_source'] and fuzz_bool():
            analog['voltage'] = analog[ 'avg_voltage']= random.uniform(0.0,5.0)
            analog['value'] = analog['value'] = (analog['voltage']/5.0) * analog['offset']

def test_fuzz(hal_data, control, fake_time, robot):
    '''
        Runs through a whole game randomly setting components
    '''
    class TestController:
    
        def __init__(self):
            self.mode = None
            
            self.disabled = 0
            self.autonomous = 0
            self.teleop = 0
            
            
        def on_step(self, tm):
            '''
                Called on each simulation step. This runs through each mode,
                and asserts that the robot didn't spend too much time in any
                particular mode.This also calls fuzz_all and fuzzes all data
            
                :param tm: The current robot time
            '''
            
            fuzz_all(hal_data)
            mode = control.get_mode()
            if mode == self.mode:
                return
            
            if mode == 'autonomous':
                self.autonomous += 1
                assert int(math.floor(fake_time.get())) == 5
                
            elif mode == 'teleop':
                self.teleop += 1
                assert int(math.floor(fake_time.get())) == 21
            
            elif mode == 'disabled':
                self.disabled += 1
                
                if self.disabled == 1:
                    assert int(math.floor(fake_time.get())) == 0
                else:
                    assert int(math.floor(fake_time.get())) == 20
            else:
                assert False, "Internal error!"
            
            self.mode = mode
    
    control.set_practice_match()
    tc = control.run_test(TestController)
    
    assert int(math.floor(fake_time.get())) == 36
    
    # If an error occurs here, for some reason a mode got called too many times
    assert tc.disabled == 2
    assert tc.autonomous == 1
    assert tc.teleop == 1


     

