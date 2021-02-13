"""
    pyfrc supports simplistic custom physics model implementations for
    simulation and testing support. It can be as simple or complex as you want
    to make it. We will continue to add helper functions (such as the
    :mod:`pyfrc.physics.drivetrains` module) to make this a lot easier
    to do. General purpose physics implementations are welcome also!

    The idea is you provide a :class:`PhysicsEngine` object that interacts with
    the simulated HAL, and modifies motors/sensors accordingly depending on the
    state of the simulation. An example of this would be measuring a motor
    moving for a set period of time, and then changing a limit switch to turn
    on after that period of time. This can help you do more complex simulations
    of your robot code without too much extra effort.

    By default, pyfrc doesn't modify any of your inputs/outputs without being
    told to do so by your code or the simulation GUI.
    
    See the `physics sample <https://github.com/robotpy/examples/tree/master/physics/src>`_
    for more details.

    Enabling physics support
    ------------------------

    You must create a python module called ``physics.py`` next to your
    ``robot.py``. A physics module must have a class called
    :class:`PhysicsEngine` which must have a function called ``update_sim``.
    When initialized, it will be passed an instance of this object.
"""

import imp
import math
from os.path import exists, join
import threading

import wpilib
import wpilib.simulation

from wpimath.kinematics import ChassisSpeeds
from wpimath.geometry import Pose2d, Rotation2d, Transform2d, Translation2d, Twist2d

import logging

logger = logging.getLogger("pyfrc.physics")


class PhysicsInitException(Exception):
    pass


class PhysicsEngine:
    """
    Your physics module must contain a class called ``PhysicsEngine``,
    and it must implement the same functions as this class.

    Alternatively, you can inherit from this object. However, that is
    not required.
    """

    def __init__(self, physics_controller: "PhysicsInterface"):
        """
        The constructor must take the following arguments:

        :param physics_controller: The physics controller interface
        :type  physics_controller: :class:`.PhysicsInterface`
        """
        self.physics_controller = physics_controller

    def update_sim(self, now: float, tm_diff: float):
        """
        Called when the simulation parameters for the program should be
        updated. This is called after robotPeriodic is called.

        :param now: The current time
        :type  now: float
        :param tm_diff: The amount of time that has passed since the last
                        time that this function was called
        :type  tm_diff: float
        """
        pass


class PhysicsInterface:
    """
    An instance of this is passed to the constructor of your
    :class:`PhysicsEngine` object. This instance is used to communicate
    information to the simulation, such as moving the robot on the
    field displayed to the user.
    """

    @classmethod
    def _create(cls, robot_path):

        physics_module_path = join(robot_path, "physics.py")
        if exists(physics_module_path):

            # Load the user's physics module if it exists
            try:
                physics_module = imp.load_source("physics", physics_module_path)
            except:
                logger.exception("Error loading user physics module")
                raise PhysicsInitException()

            if not hasattr(physics_module, "PhysicsEngine"):
                logger.error("User physics module does not have a PhysicsEngine object")
                raise PhysicsInitException()

            logger.info("Physics support successfully enabled")
            return PhysicsInterface(physics_module)

        else:
            logger.warning(
                "Cannot enable physics support, %s not found", physics_module_path
            )

    def __init__(self, physics_module):
        self.last_tm = None
        self.module = physics_module
        self.engine = None
        self.device_gyro_channels = []
        self.field = wpilib.Field2d()
        wpilib.SmartDashboard.putData("Field", self.field)

    def __repr__(self):
        return "Physics"

    def _simulationInit(self):
        # look for a class called PhysicsEngine
        try:
            self.engine = self.module.PhysicsEngine(self)
        except Exception:
            logger.exception("Error creating user's PhysicsEngine object")
            raise PhysicsInitException()

    def _simulationPeriodic(self):
        now = wpilib.Timer.getFPGATimestamp()
        last_tm = self.last_tm

        if last_tm is None:
            self.last_tm = now
        else:

            # When using time, always do it based on a differential! You may
            # not always be called at a constant rate
            tm_diff = now - last_tm

            # Don't run physics calculations more than 100hz
            if tm_diff > 0.010:
                try:
                    self.engine.update_sim(now, tm_diff)
                except Exception as e:
                    raise Exception(
                        "User physics code raised an exception (see above)"
                    ) from e
                self.last_tm = now

    #######################################################
    #
    # Public API
    #
    #######################################################

    def drive(self, speeds: ChassisSpeeds, tm_diff: float) -> Pose2d:
        """Call this from your :func:`PhysicsEngine.update_sim` function.
        Will update the robot's position on the simulation field.

        You can either calculate the chassis speeds yourself, or you
        can use the predefined functions in :mod:`pyfrc.physics.drivetrains`.

        The outputs of the `drivetrains.*` functions should be passed
        to this function.

        :param speeds:   Represents current speed/angle of robot travel
        :param tm_diff:  Amount of time speed was traveled (this is the
                         same value that was passed to update_sim)

        :return: current robot pose

        .. versionchanged:: 2020.1.0
           Input parameter is ChassisSpeeds object
        """

        twist = Twist2d(
            dx=speeds.vx * tm_diff,
            dy=speeds.vy * tm_diff,
            dtheta=speeds.omega * tm_diff,
        )

        pose = self.field.getRobotPose()
        pose = pose.exp(twist)
        self.field.setRobotPose(pose)
        return pose

    def move_robot(self, transform: Transform2d) -> Pose2d:
        """Call this from your :func:`PhysicsEngine.update_sim` function.
        Will update the robot's position on the simulation field.

        This moves the robot some relative distance and angle from
        its current position.

        :param transform: The distance and angle to move the robot

        :return: current robot pose

        .. versionadded:: 2020.1.0
        """

        pose = self.field.getRobotPose()
        pose = pose + transform
        self.field.setRobotPose(pose)
        return pose

    def get_pose(self):
        """
        :returns: current robot pose

        .. versionadded:: 2020.1.0
        """
        return self.field.getRobotPose()

    # def get_offset(self, point: Translation2d):
    #     """
    #         Computes how far away and at what angle a coordinate is
    #         located from the robot.

    #         :returns: distance,angle offset of the given x,y coordinate

    #         .. versionadded:: 2018.1.7

    #         .. versionchanged:: 2020.1.0
    #     """
    #     tr = self.field.getRobotPose().translation()

    #     dx = tr.x_feet - x
    #     dy = tr.y_feet - y

    #     distance = math.hypot(dx, dy)
    #     angle = math.atan2(dy, dx)
    #     return distance, math.degrees(angle)
