'''
    The primary purpose of these tests is to run through your code
    and make sure that it doesn't crash. If you actually want to test
    your code, you need to write your own custom tests to tease out
    the edge cases
'''

import math


def test_autonomous(control, fake_time, robot):
    '''Runs autonomous mode by itself'''
    
    # run autonomous mode for 10 seconds
    control.set_autonomous(enabled=True)
    control.on_step = lambda tm: tm < 10
    
    robot.robotInit()
    robot.autonomous()
    
    # make sure autonomous mode ran for 10 seconds
    assert int(fake_time.get()) == 10


def test_disabled(control, fake_time, robot):
    '''Runs disabled mode by itself'''
    
    # run disabled mode for 5 seconds
    control.set_operator_control(enabled=False)
    control.on_step = lambda tm: tm < 5
    
    robot.robotInit()
    robot.disabled()
    
    # make sure disabled mode ran for 5 seconds
    assert int(fake_time.get()) == 5


def test_operator_control(control, fake_time, robot):
    '''Runs operator control mode by itself'''
    
    # run operator mode for 120 seconds
    control.set_operator_control(enabled=True)
    control.on_step = lambda tm: tm < 120
    
    robot.robotInit()
    robot.operatorControl()
    
    # make sure operator mode ran for 10 seconds
    assert int(fake_time.get()) == 120


def test_practice(control, fake_time, robot):
    '''Runs through the entire span of a practice match'''
    
    control.setup_practice_match()
    
    robot.robotInit()
    
    robot.disabled()
    assert int(math.floor(fake_time.get())) == 5
    
    # transition to autonomous
    robot.autonomous()
    assert int(math.floor(fake_time.get())) == 15
    
    # transition to disabled for 1 second
    robot.disabled()
    assert int(math.floor(fake_time.get())) == 16
    
    # transition to operator control
    robot.operatorControl()
    assert int(math.floor(fake_time.get())) == 136
    
    # That's it! Easy enough. 
