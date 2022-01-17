"""
    .. versionadded:: 2018.4.0

    .. note:: The equations used in our :class:`TankModel` is derived from
              `Noah Gleason and Eli Barnett's motor characterization whitepaper
              <https://www.chiefdelphi.com/media/papers/3402>`_. It is
              recommended that users of this model read the paper so they can
              more fully understand how this works.
              
              In the interest of making progress, this API may receive
              backwards-incompatible changes before the start of the 2019
              FRC season.
"""

import math
import typing

from wpimath.geometry import Transform2d

from .motor_cfgs import MotorModelConfig
from .units import units, Helpers

import logging

logger = logging.getLogger("pyfrc.physics")

# default parameters for a kitbot
_bumper_length = 3.25 * units.inch

_kitbot_wheelbase = 21.0 * units.inch
_kitbot_width = _kitbot_wheelbase + _bumper_length * 2
_kitbot_length = 30.0 * units.inch + _bumper_length * 2

_inertia_units = (units.foot ** 2) * units.pound
_bm_units = units.foot * units.pound


class MotorModel:
    """
    Motor model used by the :class:`TankModel`. You should not need to create
    this object if you're using the :class:`TankModel` class.
    """

    @units.wraps(None, (None, None, "tm_kv", "tm_ka", "volts"))
    def __init__(
        self,
        motor_config: MotorModelConfig,
        kv: units.tm_kv,
        ka: units.tm_ka,
        vintercept: units.volts,
    ):
        """
        :param motor_config: The specification data for your motor
        :param kv: Computed ``kv`` for your robot
        :param ka: Computed ``ka`` for your robot
        :param vintercept: The minimum voltage required to generate enough
                           torque to overcome steady-state friction (see the
                           paper for more details)
        """

        #: Current computed acceleration (in ft/s^2)
        self.acceleration = 0

        #: Current computed velocity (in ft/s)
        self.velocity = 0

        #: Current computed position (in ft)
        self.position = 0

        self._nominalVoltage = units.volts.m_from(
            motor_config.nominalVoltage,
            strict=False,
            name="motor_config.nominalVoltage",
        )
        self._vintercept = vintercept
        self._kv = kv
        self._ka = ka

    def compute(self, motor_pct: float, tm_diff: float) -> float:
        """
        :param motor_pct: Percentage of power for motor in range [1..-1]
        :param tm_diff:   Time elapsed since this function was last called

        :returns: velocity
        """

        appliedVoltage = self._nominalVoltage * motor_pct
        appliedVoltage = math.copysign(
            max(abs(appliedVoltage) - self._vintercept, 0), appliedVoltage
        )

        # Heun's method (taken from Ether's drivetrain calculator)
        # -> yn+1 = yn + (h/2) (f(xn, yn) + f(xn + h, yn +  h f(xn, yn)))
        a0 = self.acceleration
        v0 = self.velocity

        # initial estimate for next velocity/acceleration
        v1 = v0 + a0 * tm_diff
        a1 = (appliedVoltage - self._kv * v1) / self._ka

        # corrected trapezoidal estimate
        v1 = v0 + (a0 + a1) * 0.5 * tm_diff
        a1 = (appliedVoltage - self._kv * v1) / self._ka
        self.position += (v0 + v1) * 0.5 * tm_diff

        self.velocity = v1
        self.acceleration = a1

        return self.velocity


class TankModel:
    """
    This is a model of a FRC tankdrive-style drivetrain that will provide
    vaguely realistic motion for the simulator.

    This drivetrain model makes a number of assumptions:

    * N motors per side
    * Constant gearing
    * Motors are geared together
    * Wheels do not 'slip' on the ground
    * Each side of the robot moves in unison

    There are two ways to construct this model. You can use the theoretical
    model via :func:`TankModel.theory` and provide robot parameters
    such as gearing, total mass, etc.

    Alternatively, if you measure ``kv``, ``ka``, and ``vintercept`` as
    detailed in the paper mentioned above, you can plug those values in
    directly instead using the :class:`TankModel` constructor instead. For
    more information about measuring your own values, see the paper and
    `this thread on ChiefDelphi <https://www.chiefdelphi.com/forums/showthread.php?t=161539>`_.

    .. note:: You must specify the You can use whatever units you would like to specify the input
              parameter for your robot, RobotPy will convert them all
              to the correct units for computation.

              Output units for velocity and acceleration are in ft/s and
              ft/s^2

    Example usage for a 90lb robot with 2 CIM motors on each side with 6 inch
    wheels::

        from pyfrc.physics import motors, tankmodel
        from pyfrc.physics.units import units

        class PhysicsEngine:

            def __init__(self, physics_controller):
                self.physics_controller = physics_controller

                self.l_motor = hal.simulation.PWMSim(1)
                self.r_motor = hal.simulation.PWMSim(2)

                self.drivetrain = tankmodel.TankModel.theory(motors.MOTOR_CFG_CIM_IMP,
                                                             robot_mass=90 * units.lbs,
                                                             gearing=10.71, nmotors=2,
                                                             x_wheelbase=2.0*feet,
                                                             wheel_diameter=6*units.inch)

            def update_sim(self, now, tm_diff):
                l_motor = self.l_motor.getSpeed()
                r_motor = self.r_motor.getSpeed()

                transform = self.drivetrain.calculate(l_motor, r_motor, tm_diff)
                self.physics_controller.move_robot(transform)

                # optional: compute encoder
                # l_encoder = self.drivetrain.l_position * ENCODER_TICKS_PER_FT
                # r_encoder = self.drivetrain.r_position * ENCODER_TICKS_PER_FT
    """

    @classmethod
    def theory(
        cls,
        motor_config: MotorModelConfig,
        robot_mass: units.Quantity,
        gearing: float,
        nmotors: int = 1,
        x_wheelbase: units.Quantity = _kitbot_wheelbase,
        robot_width: units.Quantity = _kitbot_width,
        robot_length: units.Quantity = _kitbot_length,
        wheel_diameter: units.Quantity = 6 * units.inch,
        vintercept: units.volts = 1.3 * units.volts,
        timestep: int = 5 * units.ms,
    ):
        r"""
        Use this to create the drivetrain model when you haven't measured
        ``kv`` and ``ka`` for your robot.

        :param motor_config:    Specifications for your motor
        :param robot_mass:      Mass of the robot
        :param gearing:         Gear ratio .. so for a 10.74:1 ratio, you would pass 10.74
        :param nmotors:         Number of motors per side
        :param x_wheelbase:     Wheelbase of the robot
        :param robot_width:     Width of the robot
        :param robot_length:    Length of the robot
        :param wheel_diameter:  Diameter of the wheel
        :param vintercept:      The minimum voltage required to generate enough
                                torque to overcome steady-state friction (see the
                                paper for more details)
        :param timestep_ms:     Model computation timestep

        Computation of ``kv`` and ``ka`` are done as follows:

        * :math:`\omega_{free}` is the free speed of the motor
        * :math:`\tau_{stall}` is the stall torque of the motor
        * :math:`n` is the number of drive motors
        * :math:`m_{robot}` is the mass of the robot
        * :math:`d_{wheels}` is the diameter of the robot's wheels
        * :math:`r_{gearing}` is the total gear reduction between the motors and the wheels
        * :math:`V_{max}` is the nominal max voltage of the motor

        .. math::

            velocity_{max} = \frac{\omega_{free} \cdot \pi \cdot d_{wheels} }{r_{gearing}}

            acceleration_{max} = \frac{2 \cdot n \cdot \tau_{stall} \cdot r_{gearing} }{d_{wheels} \cdot m_{robot}}

            k_{v} = \frac{V_{max}}{velocity_{max}}

            k_{a} = \frac{V_{max}}{acceleration_{max}}
        """

        # Check input units
        # -> pint doesn't seem to support default args in check()
        Helpers.ensure_mass(robot_mass)
        Helpers.ensure_length(x_wheelbase)
        Helpers.ensure_length(robot_width)
        Helpers.ensure_length(robot_length)
        Helpers.ensure_length(wheel_diameter)

        max_velocity = (motor_config.freeSpeed * math.pi * wheel_diameter) / gearing
        max_acceleration = (2.0 * nmotors * motor_config.stallTorque * gearing) / (
            wheel_diameter * robot_mass
        )

        Helpers.ensure_velocity(max_velocity)
        Helpers.ensure_acceleration(max_acceleration)

        kv = motor_config.nominalVoltage / max_velocity
        ka = motor_config.nominalVoltage / max_acceleration

        kv = units.tm_kv.from_(kv, name="kv")
        ka = units.tm_ka.from_(ka, name="ka")

        logger.info(
            "Motor config: %d %s motors @ %.2f gearing with %.1f diameter wheels",
            nmotors,
            motor_config.name,
            gearing,
            wheel_diameter.m,
        )

        logger.info(
            "- Theoretical: vmax=%.3f ft/s, amax=%.3f ft/s^2, kv=%.3f, ka=%.3f",
            max_velocity.m_as(units.foot / units.second),
            max_acceleration.m_as(units.foot / units.second ** 2),
            kv.m,
            ka.m,
        )

        return cls(
            motor_config,
            robot_mass,
            x_wheelbase,
            robot_width,
            robot_length,
            kv,
            ka,
            vintercept,
            kv,
            ka,
            vintercept,
            timestep,
        )

    def __init__(
        self,
        motor_config: MotorModelConfig,
        robot_mass: units.Quantity,
        x_wheelbase: units.Quantity,
        robot_width: units.Quantity,
        robot_length: units.Quantity,
        l_kv: units.Quantity,
        l_ka: units.Quantity,
        l_vi: units.volts,
        r_kv: units.Quantity,
        r_ka: units.Quantity,
        r_vi: units.volts,
        timestep: units.Quantity = 5 * units.ms,
    ):
        """
        Use the constructor if you have measured ``kv``, ``ka``, and
        ``Vintercept`` for your robot. Use the :func:`.theory` function
        if you haven't.

        ``Vintercept`` is the minimum voltage required to generate enough
        torque to overcome steady-state friction (see the paper for more
        details).

        The robot width/length is used to compute the moment of inertia of
        the robot. Don't forget about bumpers!

        :param motor_config: Motor specification
        :param robot_mass:   Mass of robot
        :param x_wheelbase:  Wheelbase of the robot
        :param robot_width:  Width of the robot
        :param robot_length: Length of the robot
        :param l_kv:         Left side ``kv``
        :param l_ka:         Left side ``ka``
        :param l_vi:         Left side ``Vintercept``
        :param r_kv:         Right side ``kv``
        :param r_ka:         Right side ``ka``
        :param r_vi:         Right side ``Vintercept``
        :param timestep:     Model computation timestep
        """

        # check input parameters
        Helpers.ensure_mass(robot_mass)
        Helpers.ensure_length(x_wheelbase)
        Helpers.ensure_length(robot_width)
        Helpers.ensure_length(robot_length)
        Helpers.ensure_time(timestep)

        logger.info(
            "Robot base: %.1fx%.1f frame, %.1f wheelbase, %.1f mass",
            robot_width.m,
            robot_length.m,
            x_wheelbase.m,
            robot_mass.m,
        )

        self._lmotor = MotorModel(motor_config, l_kv, l_ka, l_vi)
        self._rmotor = MotorModel(motor_config, r_kv, r_ka, r_vi)

        self.inertia = (1 / 12.0) * robot_mass * (robot_length ** 2 + robot_width ** 2)

        # This is used to compute the rotational velocity
        self._bm = _bm_units.m_from((x_wheelbase / 2.0) * robot_mass)

        self._timestep = units.milliseconds.m_from(timestep, name="timestep") * 100

    @property
    def l_velocity(self):
        """The velocity of the left side (in ft/s)"""
        return self._lmotor.velocity

    @property
    def r_velocity(self):
        """The velocity of the right side (in ft/s)"""
        return self._rmotor.velocity

    @property
    def l_position(self):
        """The linear position of the left side wheel (in feet)"""
        return self._lmotor.position

    @property
    def r_position(self):
        """The linear position of the right side wheel (in feet)"""
        return self._rmotor.position

    @property
    def inertia(self):
        """
        The model computes a moment of inertia for your robot based on the
        given mass and robot width/length. If you wish to use a different
        moment of inertia, set this property after constructing the object

        Units are ``[mass] * [length] ** 2``
        """
        return self._inertia * _inertia_units

    @inertia.setter
    @units.wraps(None, (None, _inertia_units))
    def inertia(self, value):
        self._inertia = value

    def calculate(self, l_motor: float, r_motor: float, tm_diff: float) -> Transform2d:
        """
        Given motor values and the amount of time elapsed since this was last
        called, retrieves the x,y,angle that the robot has moved. Pass these
        values to :meth:`PhysicsInterface.distance_drive`.

        To update your encoders, use the ``l_position`` and ``r_position``
        attributes of this object.

        :param l_motor:    Left motor value (-1 to 1); 1 is forward
        :param r_motor:    Right motor value (-1 to 1); -1 is forward
        :param tm_diff:    Elapsed time since last call to this function

        :returns: transform containing x/y/angle offsets of robot travel

        .. note:: If you are using more than 2 motors, it is assumed that
                  all motors on each side are set to the same speed. Only
                  pass in one of the values from each side

        .. versionadded:: 2020.1.0
        """

        # This isn't quite right, the right way is to use matrix math. However,
        # this is Good Enough for now...
        x = 0
        y = 0
        angle = 0

        # split the time difference into timestep_ms steps
        total_time = int(tm_diff * 100000)
        steps = total_time // self._timestep
        remainder = total_time % self._timestep
        step = self._timestep / 100000.0
        if remainder:
            last_step = remainder / 100000.0
            steps += 1
        else:
            last_step = step

        while steps != 0:
            if steps == 1:
                tm_diff = last_step
            else:
                tm_diff = step

            steps -= 1

            l = self._lmotor.compute(l_motor, tm_diff)
            r = self._rmotor.compute(-r_motor, tm_diff)

            # Tank drive motion equations
            velocity = (l + r) * 0.5

            # Thanks to Tyler Veness for fixing the rotation equation, via conservation
            # of angular momentum equations
            # -> omega = b * m * (l - r) / J
            rotation = self._bm * (r - l) / self._inertia

            distance = velocity * tm_diff
            turn = rotation * tm_diff

            x += distance * math.cos(angle)
            y += distance * math.sin(angle)
            angle += turn

        return Transform2d.fromFeet(x, y, angle)
