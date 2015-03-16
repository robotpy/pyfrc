'''
    Based on input from various drive motors, these helper functions
    simulate moving the robot in various ways. Many thanks to
    `Ether <http://www.chiefdelphi.com/forums/member.php?u=34863>`_
    for assistance with the motion equations.
      
    When specifying the robot speed to the below functions, the following
    may help you determine the approximate speed of your robot:
    
    * Slow: 4ft/s
    * Typical: 5 to 7ft/s
    * Fast: 8 to 12ft/s
        
    Obviously, to get the best simulation results, you should try to
    estimate the speed of your robot accurately.
'''

    
def two_motor_drivetrain(l_motor, r_motor, x_wheelbase=2, speed=5):
    '''
        Two center-mounted motors with a simple drivetrain. The 
        motion equations are as follows::
    
            FWD = (L+R)/2
            RCW = (L-R)/W
        
        * L is forward speed of the left wheel(s), all in sync
        * R is forward speed of the right wheel(s), all in sync
        * W is wheelbase in feet
        
        If you called "SetInvertedMotor" on any of your motors in RobotDrive,
        then you will need to multiply that motor's value by -1.
        
        .. note:: WPILib RobotDrive assumes that to make the robot go forward,
                  the left motor must be set to -1, and the right to +1 
        
        :param l_motor:    Left motor value (-1 to 1); -1 is forward
        :param r_motor:    Right motor value (-1 to 1); 1 is forward
        :param x_wheelbase: The distance in feet between right and left wheels.
        :param speed:      Speed of robot in feet per second (see above)
        
        :returns: speed of robot (ft/s), clockwise rotation of robot (radians/s)
    '''
    
    l = -l_motor * speed
    r = r_motor * speed

    # Motion equations
    fwd = (l + r) * 0.5
    rcw = (l - r) / float(x_wheelbase)
        
    return fwd, rcw


def four_motor_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, x_wheelbase=2, speed=5):
    '''
        Four motors, each side chained together. The motion equations are
        as follows::
    
            FWD = (L+R)/2
            RCW = (L-R)/W
        
        * L is forward speed of the left wheel(s), all in sync
        * R is forward speed of the right wheel(s), all in sync
        * W is wheelbase in feet
        
        If you called "SetInvertedMotor" on any of your motors in RobotDrive,
        then you will need to multiply that motor's value by -1.
        
        .. note:: WPILib RobotDrive assumes that to make the robot go forward,
                  the left motors must be set to -1, and the right to +1
        
        :param lr_motor:   Left rear motor value (-1 to 1); -1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); 1 is forward
        :param lf_motor:   Left front motor value (-1 to 1); -1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); 1 is forward
        :param x_wheelbase: The distance in feet between right and left wheels.
        :param speed:      Speed of robot in feet per second (see above)
        
        :returns: speed of robot (ft/s), clockwise rotation of robot (radians/s)
    '''
    
    l = -(lf_motor + lr_motor) * 0.5 * speed
    r = (rf_motor + rr_motor) * 0.5 * speed
    
    # Motion equations
    fwd = (l + r) * 0.5
    rcw = (l - r) / float(x_wheelbase)
        
    return fwd, rcw


def mecanum_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, x_wheelbase=2, y_wheelbase=3, speed=5):
    '''
        Four motors, each with a mechanum wheel attached to it.
        
        If you called "SetInvertedMotor" on any of your motors in RobotDrive,
        then you will need to multiply that motor's value by -1.
        
        .. note:: WPILib RobotDrive assumes that to make the robot go forward,
                  all motors are set to +1
        
        :param lr_motor:   Left rear motor value (-1 to 1); 1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); 1 is forward
        :param lf_motor:   Left front motor value (-1 to 1); 1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); 1 is forward
        :param x_wheelbase: The distance in feet between right and left wheels.
        :param y_wheelbase: The distance in feet between forward and rear wheels.
        :param speed:      Speed of robot in feet per second (see above)
        
        :returns: Speed of robot in x (ft/s), Speed of robot in y (ft/s), 
                  clockwise rotation of robot (radians/s)
    '''

    #
    # From http://www.chiefdelphi.com/media/papers/download/2722 pp7-9
    # [F] [omega](r) = [V]
    #
    # F is
    # .25  .25  .25 .25
    # -.25 .25 -.25 .25
    # -.25k -.25k .25k .25k
    #
    # omega is
    # [lf lr rr rf]

    # Calculate speed of each wheel
    lr = lr_motor * speed
    rr = rr_motor * speed
    lf = lf_motor * speed
    rf = rf_motor * speed

    # Calculate K
    k = abs(x_wheelbase/2) + abs(y_wheelbase/2)

    # Calculate resulting motion
    Vy = .25 * (lf + lr + rr + rf)
    Vx = .25 * (lf + -lr + rr + -rf)
    Vw = (.25/k) * (lf + lr + -rr + -rf)
    
    return Vx, Vy, Vw
    
    

# TODO: swerve drive, etc
