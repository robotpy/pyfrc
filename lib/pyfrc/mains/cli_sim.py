import inspect
import json
from os.path import abspath, dirname, exists, join

from ..test_support import pyfrc_fake_hooks

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
        
        # Load these late so tk isn't loaded each time we run a test
        from .. import sim
        
        # load the pyfrc region of the config json file
        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)
        config_file = join(robot_path, 'sim', "config.json")

        if exists(config_file):
            with open(config_file, 'r') as fp:
                config_obj = json.load(fp)["pyfrc"]
        else:
            config_obj = {}
        
        fake_time = sim.FakeRealTime()
        hal_impl.functions.hooks = pyfrc_fake_hooks.PyFrcFakeHooks(fake_time)
        hal_impl.functions.reset_hal()

        robot_controller = sim.RobotController(robot_class, static_options.get("physics_class", None), fake_time, config_obj.get("robot", {}))

        sim_manager = sim.SimManager()
        sim_manager.add_robot(robot_controller)

        robot_controller.run()
        robot_controller.wait_for_robotinit()

        ui = sim.SimUI(sim_manager, fake_time, config_obj)
        ui.run()
    
        return 0
