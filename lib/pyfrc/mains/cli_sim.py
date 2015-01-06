
from ..test_support import pyfrc_fake_hooks

from .. import sim
#from ..sim.field import elements

import hal_impl.functions

class PyFrcSim:
    """
        Executes the robot code using the low fidelity simulator and shows
        a tk-based GUI to control the simulation 
    """

    def __init__(self, parser):
        pass

    def run(self, options, robot_class, **static_options):
        
        from .. import config
        config.mode = 'sim'
        
        # sim parameters
        #field_size = (25, 54)
        field_size = (1,1)
        px_per_ft = 10
        
        
        fake_time = sim.FakeRealTime()
        hal_impl.functions.hooks = pyfrc_fake_hooks.PyFrcFakeHooks(fake_time)
        hal_impl.functions.reset_hal()
    
        sim_manager = sim.SimManager()
        
        controller = sim.RobotController(robot_class, fake_time)
        #if controller.has_physics():
        #    robot_element = sim.RobotElement(controller, px_per_ft)
        #else:
        #    center = (field_size[0]*px_per_ft/2, field_size[1]*px_per_ft/2)
        #    robot_element = elements.TextElement("Physics not setup", center, 0, '#000', 12)
        
        sim_manager.add_robot(controller)
        
        controller.run()
        
        ui = sim.SimUI(sim_manager, fake_time, field_size, px_per_ft)
        #ui.field.add_moving_element(robot_element)
        ui.run()
    
        # once it has finished, try to shut the robot down
        # -> if it can't, then the user messed up
        if not controller.stop():
            print('Error: could not stop the robot code! Check your code')
    
        return 0
