from os.path import abspath, dirname, join

import halsim_gui
import inspect
import logging

logger = logging.getLogger("pyfrc.sim")


class PyFrcSim:
    """
        Runs the robot using WPILib's GUI HAL Simulator
    """

    def __init__(self, parser):
        pass

    def run(self, options, robot_class, **static_options):
        halsim_gui.loadExtension()

        # initialize physics, attach to the user robot class
        from ..physics.core import PhysicsInterface, PhysicsInitException

        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)

        try:
            physics = PhysicsInterface._create(robot_path)
            if physics:
                robot_class._simulationInit = physics._simulationInit
                robot_class._simulationPeriodic = physics._simulationPeriodic

            # run the robot
            return robot_class.main(robot_class)

        except PhysicsInitException:
            return False
