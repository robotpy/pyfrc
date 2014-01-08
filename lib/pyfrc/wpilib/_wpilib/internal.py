
import os


#################################################
#
# Core engine that controls the robot code
#
#################################################    

# as a shortcut, you can assign to this variable to enable/disable the
# robot instead of overriding on_IsAutonomous
enabled = False
    
# assign functions to the on_* variables below in the test program to be 
# called when something happens in the robot code. The return value will 
# be given to the robot code.

# The 'tm' argument returns the value of GetClock(), which is the time
# that has been elapsed

on_IsAutonomous         = lambda tm: False
on_IsOperatorControl    = lambda tm: False
on_IsEnabled            = lambda: enabled

on_IsSystemActive       = lambda: True
on_IsNewDataAvailable   = lambda: True


#################################################
#
# Fake WPILib specific code
#
#################################################  

def initialize_fake_wpilib():
    
    import fake_wpilib as wpilib
    from ._core import _StartCompetition
    
    wpilib.IterativeRobot.StartCompetition = _StartCompetition
    wpilib.SimpleRobot.StartCompetition = _StartCompetition

def initialize_robot():
    '''
        Call this function first to import the robot code and
        start it up
    '''

    import robot
    return robot.run()
    
    
def load_module(calling_file, relative_module_to_load):
    '''
        Utility function to be used to load a module that isn't in your python
        path. Can be useful if you're creating multiple testing robot programs
        and you don't want to copy modules from your main code to test them
        individually. 
    
        This should be called like so:
        
            module = load_module( __file__, '/../../relative/path/to/module.py' )
    
    '''
    
    import imp
 
    module_filename = os.path.normpath( os.path.join(os.path.dirname(os.path.abspath(calling_file)),relative_module_to_load))
    module_name = os.path.basename( os.path.splitext(module_filename)[0] )
    return imp.load_source( module_name, module_filename )
    
    
def print_components():
    '''
        Debugging function, prints out the components currently on the robot
    '''
    
    from . import AnalogModule, CAN, DigitalModule, DriverStation 
    
    AnalogModule._print_components()
    CAN._print_components()
    DigitalModule._print_components()
    DriverStation.GetInstance().GetEnhancedIO()._print_components()
    
