#
# See the documentation for more details on how this works
#
# The idea here is you provide a simulation object that overrides specific
# pieces of WPILib, and modifies motors/sensors accordingly depending on the
# state of the simulation. An example of this would be measuring a motor
# moving for a set period of time, and then changing a limit switch to turn 
# on after that period of time. This can help you do more complex simulations
# of your robot code without too much extra effort.
#
# NOTE: THIS API IS ALPHA AND WILL MOST LIKELY CHANGE!
#       ... if you have better ideas on how to implement, submit a patch!
#

from robotpy_ext.physics import drivetrains, core


class MyPhysics(core.PhysicsEngine):
    '''
        Simulates a motor moving something that strikes two limit switches,
        one on each end of the track. Obviously, this is not particularly
        realistic, but it's good enough to illustrate the point
    '''

    def update_physics(self, hal_data, robot_enabled, dt):
        '''
            Called when the simulation parameters for the program need to be
            updated.
            
            :param dt: (delta time) The amount of time that has passed since the last
                            time that this function was called
        '''
        
        # Simulate the drivetrain

        # Don't move if robot is disabled
        if not robot_enabled:
            return

        # Handle basic drivetrain
        l_motor = hal_data['pwm'][1]['value']
        r_motor = hal_data['pwm'][2]['value']
        self.state["drivetrain"] = drivetrains.two_motor_drivetrain(self.state["drivetrain"], dt, l_motor, r_motor)

        # integrate lift position
        self.state["lift"] += hal_data['pwm'][4]['value'] * dt * 3
        
        # update limit switches based on position
        if self.state["lift"] <= 0:
            switch1 = True
            switch2 = False
        elif self.state["lift"] > 10:
            switch1 = False
            switch2 = True
        else:
            switch1 = False
            switch2 = False 
        
        # set switch values
        hal_data['dio'][1]['value'] = switch1
        hal_data['dio'][2]['value'] = switch2
        # set potentiometer value
        hal_data['analog_in'][2]['voltage'] = self.state["lift"]
