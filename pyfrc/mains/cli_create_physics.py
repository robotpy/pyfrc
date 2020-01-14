import inspect
import json
from os import mkdir
from os.path import abspath, dirname, exists, join

physics_starter = '''
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


class PhysicsEngine:
    """
       Simulates a 4-wheel robot using Tank Drive joystick control
    """

    def __init__(self, physics_controller):
        """
        :param physics_controller: `pyfrc.physics.core.Physics` object
                                   to communicate simulation effects to
        """

        self.physics_controller = physics_controller

        """
        # Change these parameters to fit your robot!
        bumper_width = 3.25 * units.inch

        self.drivetrain = tankmodel.TankModel.theory(
            motor_cfgs.MOTOR_CFG_CIM,           # motor configuration
            110 * units.lbs,                    # robot mass
            10.71,                              # drivetrain gear ratio \omega In/\omega Out
            2,                                  # motors per side
            22 * units.inch,                    # robot wheelbase
            23 * units.inch + bumper_width * 2, # robot width
            32 * units.inch + bumper_width * 2, # robot length
            6 * units.inch,                     # wheel diameter
        )
        """

    def update_sim(self, hal_data, now, tm_diff):
        """
        Called when the simulation parameters for the program need to be
        updated.

        :param now: The current time as a float
        :param tm_diff: The amount of time that has passed since the last
                        time that this function was called
        """

        # Simulate the drivetrain
        """
        lr_motor = hal_data["pwm"][1]["value"]
        rr_motor = hal_data["pwm"][2]["value"]

        # Not needed because front and rear should be in sync
        # lf_motor = hal_data['pwm'][3]['value']
        # rf_motor = hal_data['pwm'][4]['value']

        x, y, angle = self.drivetrain.get_distance(lr_motor, rr_motor, tm_diff)
        self.physics_controller.distance_drive(x, y, angle)
        """
'''

sim_starter = {
    "pyfrc": {
        "robot": {
            "w": 3,
            "h": 2,
            "starting_x": 10,
            "starting_y": 10,
            "starting_angle": 0,
        },
        "pwm": {},
        "can": {},
        "joysticks": {
            "0": {"axes": {}, "buttons": {}},
            "1": {"axes": {}, "buttons": {}},
        },
    }
}


class PyFrcCreatePhysics:
    def __init__(self, parser=None):
        pass

    def run(self, options, robot_class, **static_options):

        print("Robot physics are not yet implemented for RobotPy 2020")
        return 1

        robot_file = abspath(inspect.getfile(robot_class))
        robot_path = dirname(robot_file)
        sim_path = join(robot_path, "sim")

        physics_file = join(robot_path, "physics.py")
        sim_file = join(sim_path, "config.json")
        if exists(physics_file):
            print("- physics.py already exists")
        else:
            with open(physics_file, "w") as fp:
                fp.write(physics_starter)
            print("- physics file created at", physics_file)

        if exists(sim_path):
            if exists(sim_file):
                print("- config.json already exists")
            else:
                with open(sim_file, "w") as f:
                    f.write(json.dumps(sim_starter, indent=4) + "\n")
                print("- sim file created at", sim_file)
        else:
            mkdir(sim_path)
            with open(sim_file, "w") as f:
                f.write(json.dumps(sim_starter, indent=4) + "\n")
            print("- sim file created at", sim_file)
        print()
        print("Robot simulation can be run via 'python3 robot.py sim'")
