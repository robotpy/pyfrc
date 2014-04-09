#
# Basic tests for the IterativeRobot framework.
#
# The primary purpose of these tests is to run through your code
# and make sure that it doesn't crash. If you actually want to test
# your code, you need to write your own custom tests to tease out
# the edge cases
#

import math


def test_autonomous(robot, wpilib, fake_time):
    '''Runs autonomous mode by itself'''
    
    # run autonomous mode for 10 seconds
    wpilib.internal.enabled = True
    wpilib.internal.on_IsAutonomous = lambda tm: tm < 10
    
    wpilib.internal.IterativeRobotAutonomous(robot)
    
    # make sure autonomous mode ran for 10 seconds
    assert int(fake_time.Get()) == 10


def test_disabled(robot, fake_time, wpilib):
    '''Runs disabled mode by itself'''
    
    # run disabled mode for 5 seconds
    wpilib.internal.on_IsEnabled = lambda tm: fake_time.Get() > 5.0 
    wpilib.internal.IterativeRobotDisabled(robot, 1000)
    
    # make sure disabled mode ran for 5 seconds
    assert int(fake_time.Get()) == 5


def test_operator_control(robot, fake_time, wpilib):
    '''Runs operator control mode by itself'''
    
    # run operator mode for 120 seconds
    wpilib.internal.enabled = True
    wpilib.internal.on_IsOperatorControl = lambda tm: tm < 120
    
    wpilib.internal.IterativeRobotTeleop(robot)
    
    # make sure operator mode ran for 10 seconds
    assert int(fake_time.Get()) == 120


def test_practice(robot, fake_time, wpilib):
    '''Runs through the entire span of a practice match'''
    
    wpilib.internal.set_test_controller(wpilib.internal.PracticeMatchTestController)
    
    
    wpilib.internal.IterativeRobotDisabled(robot, 10000)
    assert int(math.floor(fake_time.Get())) == 5
    
    # transition to autonomous
    wpilib.internal.IterativeRobotAutonomous(robot)
    assert int(math.floor(fake_time.Get())) == 15
    
    # transition to disabled for 1 second
    wpilib.internal.IterativeRobotDisabled(robot, 10000)
    assert int(math.floor(fake_time.Get())) == 16
    
    # transition to operator control
    wpilib.internal.IterativeRobotTeleop(robot)
    assert int(math.floor(fake_time.Get())) == 136
    
    # That's it! Easy enough. 
