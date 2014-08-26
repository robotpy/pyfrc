'''
    Based on input from various drive motors, this simulates
    moving the robot in various ways.
    
    Each of these functions returns a tuple of (speed, yaw)
    indicating the robot's current desired speed/direction
    based on what type of drive_train is being used. Where
    heading is an angle, Yaw is % of circle in one time
    deviation.
    
    These are really simple approximations, and get the job
    done for now. If you have better ways of doing the
    calculations, please submit fixes!
'''

    
def two_motor_drivetrain(tm_diff, l_motor, r_motor, robot_circumference=8):
    '''
        Two center-mounted motors 
    '''
    
    # TODO: do something with tm_diff
    
    jag1 = -l_motor.Get()
    jag2 = r_motor.Get()

    # speed obtained by adding together motor speeds
    speed = (jag1 + jag2) / 6
    yaw = (jag1 / robot_circumference) - (jag2/robot_circumference) 
    
    return speed, yaw
            

# TODO: 4 wheel


#def mechanum_drivetrain(tm_diff, ll_motor, lr_motor, rl_motor, rr_motor,
#                        robot_circumference=8):
#    '''
#        A 4-wheel mechanum drivetrain
#    '''
#    pass

# TODO: swerve drive, etc
