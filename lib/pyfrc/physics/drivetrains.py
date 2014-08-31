'''
    Based on input from various drive motors, this simulates
    moving the robot in various ways.
                
    Thanks to Ether (http://www.chiefdelphi.com/forums/member.php?u=34863)
    for assistance with the motion equations.
    
    2/4/6 wheel robot, simple drivetrain:
    
        FWD = (L+R)/2
        RCW = (L-R)/W
        
    L is forward speed of the left wheel(s), all in sync
    R is forward speed of the right wheel(s), all in sync
    W is wheelbase in feet
    
    When specifying the robot speed to the below functions, the following
    may help you determine the approximate speed of your robot:
    
        Slow: 4ft/s
        Typical: 5 to 7ft/s
        Fast: 8 to 12ft/s
        
    Obviously, to get the best simulation results, you should try to
    estimate the speed of your robot accurately.
'''

    
def two_motor_drivetrain(l_motor, r_motor, wheelbase=2, speed=5):
    '''
        Two center-mounted motors (see above for equations)
        
        :param l_motor:    Left motor value (-1 to 1); -1 is forward
        :param r_motor:    Right motor value (-1 to 1); 1 is forward
        :param speed:      Speed of robot in feet per second (see above)
        :param wheelbase:  Distance between wheels, in feet
        
        :returns: speed of robot (ft/s), rotation of robot (radians/s)
    '''
    
    l = -l_motor.Get() * speed
    r = r_motor.Get() * speed

    # Motion equations
    fwd = (l + r) * 0.5
    rcw = (l - r) / float(wheelbase)
        
    return fwd, rcw


def four_motor_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, wheelbase=2, speed=5):
    '''
        Four motors, each side chained together (see above for equations)
        
        :param lr_motor:   Left rear motor value (-1 to 1); -1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); 1 is forward
        :param lf_motor:   Left front motor value (-1 to 1); -1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); 1 is forward
        :param speed:      Speed of robot in feet per second (see above)
        :param wheelbase:  Distance between wheels, in feet
        
        :returns: speed of robot (ft/s), rotation of robot (radians/s)
    '''
    
    l = -(lf_motor.Get() + lr_motor.Get()) * 0.5 * speed
    r = (rf_motor.Get() + rr_motor.Get()) * 0.5 * speed
    
    # Motion equations
    fwd = (l + r) * 0.5
    rcw = (l - r) / float(wheelbase)
        
    return fwd, rcw




#def mechanum_drivetrain(tm_diff, ll_motor, lr_motor, rl_motor, rr_motor,
#                        robot_circumference=8):
#    '''
#        A 4-wheel mechanum drivetrain
#    '''
#    pass

# TODO: swerve drive, etc
