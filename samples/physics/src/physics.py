#
# Implements a limited physics model of the robot
#
# The idea here is you provide a simulation object that overrides specific
# pieces of WPILib, and modifies motors/sensors accordingly depending on the
# state of the simulation. An example of this would be measuring a motor
# moving for a set period of time, and then changing a limit switch to turn 
# on after that period of time. This can help you do more complex simulations
# of your robot code without too much extra effort.
#
# This is a bit limited so far...
#
# NOTE: THIS API IS ALPHA AND WILL MOST LIKELY CHANGE!
#       ... if you have better ideas on how to implement, submit a patch!
#

from pyfrc import wpilib


class PhysicsEngine(object):
    '''
        Simulates a motor moving something that strikes two limit switches,
        one on each end of the track. 
       
        TODO: a better way to implement this is have something track all of
        the input values, and have that in a data structure, while also
        providing the override capability.
       
        Obviously, this is not particularly realistic, but it's good enough
        to illustrate the point
    '''
    
    
    def __init__(self):
        
        self.jag_value = None
        
        self.position = 0
        self.last_tm = None
        
        
    def update_sim(self, tm):
        '''Called when the simulation parameters need to be updated'''
        
        last_tm = self.last_tm
        self.last_tm = tm
        
        if last_tm is None:
            return
        
        time_diff = tm - last_tm
        
        if self.jag_value is None:
            return
        
        # update position
        self.position += self.jag_value * time_diff * 3
        
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
            wpilib.AnalogModule._channels[0].voltage = self.position
        except:
            pass
        
        # always reset variables in case the input values aren't updated
        # by the robot
        self.jag_value = None
    
    def sim_Jaguar_Set(self, obj, fn, value):
        
        if obj.channel == 1:
            self.jag_value = value
        
        fn(value)

