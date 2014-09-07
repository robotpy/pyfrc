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

from pyfrc import wpilib
from pyfrc.physics import drivetrains


class PhysicsEngine(object):
    '''
        Simulates a motor moving something that strikes two limit switches,
        one on each end of the track. Obviously, this is not particularly
        realistic, but it's good enough to illustrate the point
       
        TODO: a better way to implement this is have something track all of
        the input values, and have that in a data structure, while also
        providing the override capability.
    '''
    
    #: Width of robot, specified in feet
    ROBOT_WIDTH = 2
    ROBOT_HEIGHT = 3
    
    ROBOT_STARTING_X = 18.5
    ROBOT_STARTING_Y = 12
    
    # In degrees, 0 is east, 90 is south
    STARTING_ANGLE = 180
    
    
    def __init__(self, physics_controller):
        '''
            :param physics_controller: `pyfrc.physics.core.Physics` object
                                       to communicate simulation effects to
        '''
        
        self.physics_controller = physics_controller
        
        self.jag_value = None
        
        self.position = 0
        self.last_tm = None
            
    def update_sim(self, now, tm_diff):
        '''
            Called when the simulation parameters for the program need to be
            updated. This is mostly when wpilib.Wait is called.
            
            :param now: The current time as a float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
        '''
        
        # Simulate the drivetrain
        l_motor = wpilib.DigitalModule._pwm[0].Get()
        r_motor = wpilib.DigitalModule._pwm[1].Get()
        
        speed, rotation = drivetrains.two_motor_drivetrain(l_motor, r_motor)
        self.physics_controller.drive(speed, rotation, tm_diff)
        
        
        if self.jag_value is None:
            return
        
        # update position (use tm_diff so the rate is constant)
        self.position += self.jag_value * tm_diff * 3
        
        # update limit switches based on position
        if self.position <= 0:
            switch1 = True
            switch2 = False
            
        elif self.position > 10:
            switch1 = False
            switch2 = True
            
        else:
            switch1 = False
            switch2 = False 
        
        # set values here
        try:
            wpilib.DigitalModule._io[0].value = switch1
        except:
            pass
        
        try:
            wpilib.DigitalModule._io[1].value = switch2
        except:
            pass
        
        try:
            wpilib.AnalogModule._channels[1].voltage = self.position
        except:
            pass
        
        # always reset variables in case the input values aren't updated
        # by the robot
        self.jag_value = None
    
    def sim_Jaguar_Set(self, obj, fn, value):
        '''
            Called when Jaguar.Set() is called. This function should
            call fn() with the passed in value.
            
            :param obj:   Jaguar object
            :param fn:    Wrapped Jaguar.Set function
            :param value: Value passed to Jaguar.Set
        '''
        
        if obj.channel == 4:
            self.jag_value = value
        
        fn(value)

