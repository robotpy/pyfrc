#
# See the notes for the other physics sample
#


from pyfrc.physics import drivetrains


class PhysicsEngine(object):
    '''
       Simulates a 4-wheel mecanum robot using Tank Drive joystick control 
    '''
    
    def __init__(self, physics_controller):
        '''
            :param physics_controller: `pyfrc.physics.core.Physics` object
                                       to communicate simulation effects to
        '''
        
        self.physics_controller = physics_controller
        self.physics_controller.add_analog_gyro_channel(1)
        
            
    def update_sim(self, hal_data, now, tm_diff):
        '''
            Called when the simulation parameters for the program need to be
            updated.
            
            :param now: The current time as a float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
        '''
        
        # Simulate the drivetrain
        # -> Remember, in the constructor we inverted the left motors, so
        #    invert the motor values here too!
        lr_motor = -hal_data['pwm'][1]['value']
        rr_motor = hal_data['pwm'][2]['value']
        lf_motor = -hal_data['pwm'][3]['value']
        rf_motor = hal_data['pwm'][4]['value']
        
        vx, vy, vw = drivetrains.mecanum_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor)
        self.physics_controller.vector_drive(vx, vy, vw, tm_diff)

