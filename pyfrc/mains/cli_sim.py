from os.path import abspath, dirname
import argparse
import inspect
import logging

logger = logging.getLogger("pyfrc.sim")


class PyFrcSim:
    """
    Runs the robot using WPILib's GUI HAL Simulator
    """

    def __init__(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--gui",
            default=False,
            action="store_true",
            help="Use the WPIlib simulation gui",
        )

    def run(self, options, robot_class, **static_options):

        if options.gui:
            try:
                import halsim_gui
            except ImportError:
                print("robotpy-halsim-gui is not installed!")
                exit(1)
            else:
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
