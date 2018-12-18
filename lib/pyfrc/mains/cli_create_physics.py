import inspect
from os.path import abspath, dirname, exists, join

physics_starter = """
#
# See the documentation for more details on how this works
#
# Documentation can be found at https://robotpy.readthedocs.io/projects/pyfrc/en/latest/physics.html
#
# The idea here is you provide a simulation object that overrides specific
# pieces of WPILib, and modifies motors/sensors accordingly depending on the
# state of the simulation. An example of this would be measuring a motor
# moving for a set period of time, and then changing a limit switch to turn
# on after that period of time. This can help you do more complex simulations
# of your robot code without too much extra effort.
#
# Examples can be found at https://github.com/robotpy/examples


class PhysicsEngine(object):
    \"\"\"
        Basic physics engine to be combined with the simulator
    \"\"\"

    def __init__(self, physics_controller):
        \"\"\"
            :param physics_controller: `pyfrc.physics.core.PhysicsInterface` object
                                       to communicate simulation effects to
        \"\"\"

        self.physics_controller = physics_controller

    def update_sim(self, hal_data, now, tm_diff):
        \"\"\"
            Called when the simulation parameters for the program need to be
            updated.
            
            :param hal_data: Dictionary representing objects created through wpilib
            :param now: The current time as a float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
        \"\"\"
        pass
"""


class PyFrcCreatePhysics:
    def __init__(self, parser=None):
        pass

    def run(self, options, robot_class, **static_options):
        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)

        physics_file = join(robot_path, "physics.py")
        if exists(physics_file):
            print("- physics.py already exists")
        else:
            with open(physics_file, "w") as fp:
                fp.write(physics_starter)
            print("- physics file created at", physics_file)

        print()
        print("Robot simulation can be run via 'python3 robot.py sim'")
