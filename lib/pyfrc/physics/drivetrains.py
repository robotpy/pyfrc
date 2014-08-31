'''
    Based on input from various drive motors, this simulates
    moving the robot in various ways.
    
    Each of these functions returns a tuple of (distance, yaw)
    indicating the distance the robot traveled during the time
    diff passed in. Where
    heading is an angle, Yaw is % of circle in one time
    deviation.
    
    Distance is specified in feet
    Yaw is specified in % of circle
    
    These are really simple approximations, and get the job
    done for now. If you have better ways of doing the
    calculations, please submit fixes!
    
    Scale approximations:
        Robot size: 20px x 20px -- 2.3ft x 2.3ft
        Robot speed estimates:
            Slow: 4ft/s
            Typical: 5 to 7ft/s
            Fast: 8 to 12ft/s
'''

    
def two_motor_drivetrain(tm_diff, l_motor, r_motor, speed=5, robot_circumference=8):
    '''
        Two center-mounted motors 
        
        :param tm_diff:    Amount of time that has passed since last call
        :param l_motor:    Left motor speed
        :param r_motor:    Right motor speed
        :param speed:      Speed of robot in feet per second (see above)
        :param robot_circumference:
    '''
    
    # TODO: do something with tm_diff
    
    jag1 = -l_motor.Get()
    jag2 = r_motor.Get()

    # speed obtained by adding together motor speeds
    speed = (jag1 + jag2) * 0.5 * tm_diff * speed
    
    # Physics could be better here.. why is circumference here?
    yaw = (jag1 / robot_circumference) - (jag2/robot_circumference) 
    
    return speed, yaw
            

#def four_wheel_drivetrain()... 

#def six_wheel_drivetrain()...


#def mechanum_drivetrain(tm_diff, ll_motor, lr_motor, rl_motor, rr_motor,
#                        robot_circumference=8):
#    '''
#        A 4-wheel mechanum drivetrain
#    '''
#    pass

# TODO: swerve drive, etc
