import os
from os.path import abspath, dirname
import argparse
import inspect
import logging
from pkg_resources import iter_entry_points

try:
    from importlib.metadata import metadata
except ImportError:
    from importlib_metadata import metadata

logger = logging.getLogger("pyfrc.sim")


class PyFrcSim:
    """
    Runs the robot using WPILib's GUI HAL Simulator
    """

    def __init__(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--nogui",
            default=False,
            action="store_true",
            help="Don't use the WPIlib simulation gui",
        )

        self.simexts = {}

        for entry_point in iter_entry_points(group="robotpysimext", name=None):
            if entry_point.module_name == "halsim_gui":
                continue
            try:
                sim_ext_module = entry_point.load()
            except ImportError:
                print(f"WARNING: Error detected in {entry_point}")
                continue

            self.simexts[entry_point.name] = sim_ext_module

            parser.add_argument(
                f"--{entry_point.name}",
                default=False,
                action="store_true",
                help=metadata(entry_point.dist.project_name)["summary"],
            )

    def run(self, options, robot_class, **static_options):

        if not options.nogui:
            try:
                import halsim_gui
            except ImportError:
                print("robotpy-halsim-gui is not installed!")
                exit(1)
            else:
                halsim_gui.loadExtension()

        # Some extensions (gui) changes the current directory
        cwd = os.getcwd()

        for name, module in self.simexts.items():
            if getattr(options, name.replace("-", "_"), False):
                try:
                    module.loadExtension()
                except:
                    print(f"Error loading {name}!")
                    raise

        os.chdir(cwd)

        # initialize physics, attach to the user robot class
        from ..physics.core import PhysicsInterface, PhysicsInitException

        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)

        try:
            physics = PhysicsInterface._create(robot_path)
            if physics:

                # We create a robot class so we can pass the robot object to
                # physics._simulationInit
                class PhysicsRobot(robot_class):
                    def _simulationInit(self):
                        physics._simulationInit(self)

                    _simulationPeriodic = physics._simulationPeriodic

                # The user doesn't need to know that we didn't create their class directly..
                PhysicsRobot.__name__ = robot_class.__name__
                PhysicsRobot.__module__ = robot_class.__module__
                PhysicsRobot.__qualname__ = robot_class.__qualname__

                robot_class = PhysicsRobot

            # run the robot
            return robot_class.main(robot_class)

        except PhysicsInitException:
            return False
