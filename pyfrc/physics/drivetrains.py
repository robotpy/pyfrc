"""
    .. warning:: These drivetrain models are not particularly realistic, and
                 if you are using a tank drive style drivetrain you should use
                 the :class:`.TankModel` instead.

    Based on input from various drive motors, these helper functions
    simulate moving the robot in various ways. Many thanks to
    `Ether <http://www.chiefdelphi.com/forums/member.php?u=34863>`_
    for assistance with the motion equations.
      
    When specifying the robot speed to the below functions, the following
    may help you determine the approximate speed of your robot:
    
    * Slow: 4ft/s
    * Typical: 5 to 7ft/s
    * Fast: 8 to 12ft/s
        
    Obviously, to get the best simulation results, you should try to
    estimate the speed of your robot accurately.
    
    Here's an example usage of the drivetrains::
    
        import hal.simulation
        from pyfrc.physics import drivetrains
    
        class PhysicsEngine:
            
            def __init__(self, physics_controller):
                self.physics_controller = physics_controller
                self.drivetrain = drivetrains.TwoMotorDrivetrain(deadzone=drivetrains.linear_deadzone(0.2))
                
                self.l_motor = hal.simulation.PWMSim(1)
                self.r_motor = hal.simulation.PWMSim(2)
                
            def update_sim(self, now, tm_diff):
                l_motor = self.l_motor.getSpeed()
                r_motor = self.r_motor.getSpeed()

                speeds = self.drivetrain.calculate(l_motor, r_motor)
                self.physics_controller.drive(speeds, tm_diff)
                
                # optional: compute encoder
                # l_encoder = self.drivetrain.wheelSpeeds.left * tm_diff
    
    .. versionchanged:: 2020.1.0

       The input speeds and output rotation angles were changed to reflect
       the current WPILib drivetrain/field objects. Wheelbases and default
       speeds all require units.
"""
import math
import typing

from .units import units, Helpers

from wpimath.geometry import Translation2d

from wpimath.kinematics import (
    ChassisSpeeds,
    DifferentialDriveKinematics,
    DifferentialDriveWheelSpeeds,
    MecanumDriveKinematics,
    MecanumDriveWheelSpeeds,
)

DeadzoneCallable = typing.Callable[[float], float]


def linear_deadzone(deadzone: float) -> DeadzoneCallable:
    """
    Real motors won't actually move unless you give them some minimum amount
    of input. This computes an output speed for a motor and causes it to
    'not move' if the input isn't high enough. Additionally, the output is
    adjusted linearly to compensate.

    Example: For a deadzone of 0.2:

    * Input of 0.0 will result in 0.0
    * Input of 0.2 will result in 0.0
    * Input of 0.3 will result in ~0.12
    * Input of 1.0 will result in 1.0

    This returns a function that computes the deadzone. You should pass the
    returned function to one of the drivetrain simulation functions as the
    ``deadzone`` parameter.

    :param motor_input: The motor input (between -1 and 1)
    :param deadzone: Minimum input required for the motor to move (between 0 and 1)
    """
    assert 0.0 < deadzone < 1.0
    scale_param = 1.0 - deadzone

    def _linear_deadzone(motor_input):
        abs_motor_input = abs(motor_input)
        if abs_motor_input < deadzone:
            return 0.0
        else:
            return math.copysign(
                (abs_motor_input - deadzone) / scale_param, motor_input
            )

    return _linear_deadzone


class TwoMotorDrivetrain:
    """
    Two center-mounted motors with a simple drivetrain. The
    motion equations are as follows::

        FWD = (L+R)/2
        RCCW = (R-L)/W

    * L is forward speed of the left wheel(s), all in sync
    * R is forward speed of the right wheel(s), all in sync
    * W is wheelbase in feet

    .. note:: :class:`wpilib.drive.DifferentialDrive` assumes that to make
              the robot go forward, the left motor output is 1, and the
              right motor output is -1

    .. versionadded:: 2018.2.0
    """

    #: Wheel speeds you can use for encoder calculations (updated by calculate)
    wheelSpeeds: DifferentialDriveWheelSpeeds

    def __init__(
        self,
        x_wheelbase: units.Quantity = 2 * units.feet,
        speed: units.Quantity = 5 * units.fps,
        deadzone: typing.Optional[DeadzoneCallable] = None,
    ):
        """
        :param x_wheelbase: The distance between right and left wheels.
        :param speed:       Speed of robot (see above)
        :param deadzone:    A function that adjusts the output of the motor (see :func:`linear_deadzone`)
        """
        trackwidth = units.meters.m_from(x_wheelbase, name="x_wheelbase")
        self.kinematics = DifferentialDriveKinematics(trackwidth)
        self.speed = units.mps.m_from(speed, name="speed")
        self.wheelSpeeds = DifferentialDriveWheelSpeeds()
        self.deadzone = deadzone

    def calculate(self, l_motor: float, r_motor: float) -> ChassisSpeeds:
        """
        Given motor values, computes resulting chassis speeds of robot

        :param l_motor:    Left motor value (-1 to 1); 1 is forward
        :param r_motor:    Right motor value (-1 to 1); -1 is forward

        :returns: ChassisSpeeds that can be passed to 'drive'

        .. versionadded:: 2020.1.0
        """
        if self.deadzone:
            l_motor = self.deadzone(l_motor)
            r_motor = self.deadzone(r_motor)

        l = l_motor * self.speed
        r = -r_motor * self.speed

        self.wheelSpeeds.left = l
        self.wheelSpeeds.right = r

        return self.kinematics.toChassisSpeeds(self.wheelSpeeds)


class FourMotorDrivetrain:
    """
    Four motors, each side chained together. The motion equations are
    as follows::

        FWD = (L+R)/2
        RCCW = (R-L)/W

    * L is forward speed of the left wheel(s), all in sync
    * R is forward speed of the right wheel(s), all in sync
    * W is wheelbase in feet

    .. note:: :class:`wpilib.drive.DifferentialDrive` assumes that to make
              the robot go forward, the left motors must be set to 1, and
              the right to -1

    .. versionadded:: 2018.2.0
    """

    #: Wheel speeds you can use for encoder calculations (updated by calculate)
    wheelSpeeds: DifferentialDriveWheelSpeeds

    def __init__(
        self,
        x_wheelbase: units.Quantity = 2 * units.feet,
        speed: units.Quantity = 5 * units.fps,
        deadzone: typing.Optional[DeadzoneCallable] = None,
    ):
        """
        :param x_wheelbase: The distance between right and left wheels.
        :param speed:       Speed of robot (see above)
        :param deadzone:    A function that adjusts the output of the motor (see :func:`linear_deadzone`)
        """
        trackwidth = units.meters.m_from(x_wheelbase, name="x_wheelbase")
        self.kinematics = DifferentialDriveKinematics(trackwidth)
        self.speed = units.mps.m_from(speed, name="speed")
        self.wheelSpeeds = DifferentialDriveWheelSpeeds()
        self.deadzone = deadzone

    def calculate(
        self, lf_motor: float, lr_motor: float, rf_motor: float, rr_motor: float
    ) -> ChassisSpeeds:
        """
        Given motor values, computes resulting chassis speeds of robot

        :param lf_motor:   Left front motor value (-1 to 1); 1 is forward
        :param lr_motor:   Left rear motor value (-1 to 1); 1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); -1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); -1 is forward

        :returns: ChassisSpeeds that can be passed to 'drive'

        .. versionadded:: 2020.1.0
        """

        if self.deadzone:
            lf_motor = self.deadzone(lf_motor)
            lr_motor = self.deadzone(lr_motor)
            rf_motor = self.deadzone(rf_motor)
            rr_motor = self.deadzone(rr_motor)

        l = (lf_motor + lr_motor) * 0.5 * self.speed
        r = -(rf_motor + rr_motor) * 0.5 * self.speed

        self.wheelSpeeds.left = l
        self.wheelSpeeds.right = r

        return self.kinematics.toChassisSpeeds(self.wheelSpeeds)


class MecanumDrivetrain:
    """
    Four motors, each with a mecanum wheel attached to it.

    .. note:: :class:`wpilib.drive.MecanumDrive` assumes that to make
              the robot go forward, the left motor outputs are 1, and the
              right motor outputs are -1

    .. versionadded:: 2018.2.0
    """

    #: Use this to compute encoder data after calculate is called
    wheelSpeeds: MecanumDriveWheelSpeeds

    def __init__(
        self,
        x_wheelbase: units.Quantity = 2 * units.feet,
        y_wheelbase: units.Quantity = 3 * units.feet,
        speed: units.Quantity = 5 * units.fps,
        deadzone: typing.Optional[DeadzoneCallable] = None,
    ):
        """
        :param x_wheelbase: The distance between right and left wheels.
        :param y_wheelbase: The distance between forward and rear wheels.
        :param speed:       Speed of robot (see above)
        :param deadzone:    A function that adjusts the output of the motor (see :func:`linear_deadzone`)
        """
        x2 = units.meters.m_from(x_wheelbase, name="x_wheelbase") / 2.0
        y2 = units.meters.m_from(y_wheelbase, name="y_wheelbase") / 2.0

        self.kinematics = MecanumDriveKinematics(
            Translation2d(x2, y2),
            Translation2d(x2, -y2),
            Translation2d(-x2, y2),
            Translation2d(-x2, -y2),
        )

        self.speed = units.mps.m_from(speed, name="speed")
        self.deadzone = deadzone

        self.wheelSpeeds = MecanumDriveWheelSpeeds()

    def calculate(
        self,
        lf_motor: float,
        lr_motor: float,
        rf_motor: float,
        rr_motor: float,
    ) -> ChassisSpeeds:
        """
        :param lf_motor:   Left front motor value (-1 to 1); 1 is forward
        :param lr_motor:   Left rear motor value (-1 to 1); 1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); -1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); -1 is forward

        :returns: ChassisSpeeds that can be passed to 'drive'

        .. versionadded:: 2020.1.0
        """

        if self.deadzone:
            lf_motor = self.deadzone(lf_motor)
            lr_motor = self.deadzone(lr_motor)
            rf_motor = self.deadzone(rf_motor)
            rr_motor = self.deadzone(rr_motor)

        # Calculate speed of each wheel
        lr = lr_motor * self.speed
        rr = -rr_motor * self.speed
        lf = lf_motor * self.speed
        rf = -rf_motor * self.speed

        self.wheelSpeeds.frontLeft = lf
        self.wheelSpeeds.rearLeft = lr
        self.wheelSpeeds.frontRight = rf
        self.wheelSpeeds.rearRight = rr

        return self.kinematics.toChassisSpeeds(self.wheelSpeeds)


def four_motor_swerve_drivetrain(
    lr_motor: float,
    rr_motor: float,
    lf_motor: float,
    rf_motor: float,
    lr_angle: float,
    rr_angle: float,
    lf_angle: float,
    rf_angle: float,
    x_wheelbase=2,
    y_wheelbase=2,
    speed=5,
    deadzone=None,
) -> ChassisSpeeds:
    """
    Four motors that can be rotated in any direction

    If any motors are inverted, then you will need to multiply that motor's
    value by -1.

    :param lr_motor:   Left rear motor value (-1 to 1); 1 is forward
    :param rr_motor:   Right rear motor value (-1 to 1); 1 is forward
    :param lf_motor:   Left front motor value (-1 to 1); 1 is forward
    :param rf_motor:   Right front motor value (-1 to 1); 1 is forward

    :param lr_angle:   Left rear motor angle in degrees (0 to 360 measured clockwise from forward position)
    :param rr_angle:   Right rear motor angle in degrees (0 to 360 measured clockwise from forward position)
    :param lf_angle:   Left front motor angle in degrees (0 to 360 measured clockwise from forward position)
    :param rf_angle:   Right front motor angle in degrees (0 to 360 measured clockwise from forward position)

    :param x_wheelbase: The distance in feet between right and left wheels.
    :param y_wheelbase: The distance in feet between forward and rear wheels.
    :param speed:       Speed of robot in feet per second (see above)
    :param deadzone:    A function that adjusts the output of the motor (see :func:`linear_deadzone`)

    :returns: ChassisSpeeds that can be passed to 'drive'

    .. versionchanged:: 2020.1.0

       The output rotation angle was changed from CW to CCW to reflect the
       current WPILib drivetrain/field objects
    """

    if deadzone:
        lf_motor = deadzone(lf_motor)
        lr_motor = deadzone(lr_motor)
        rf_motor = deadzone(rf_motor)
        rr_motor = deadzone(rr_motor)

    # Calculate speed of each wheel
    lr = lr_motor * speed
    rr = rr_motor * speed
    lf = lf_motor * speed
    rf = rf_motor * speed

    # Calculate angle in radians
    lr_rad = math.radians(lr_angle)
    rr_rad = math.radians(rr_angle)
    lf_rad = math.radians(lf_angle)
    rf_rad = math.radians(rf_angle)

    # Calculate wheelbase radius
    wheelbase_radius = math.hypot(x_wheelbase / 2.0, y_wheelbase / 2.0)

    # Calculates the Vx and Vy components
    # Sin an Cos inverted because forward is 0 on swerve wheels
    Vx = (
        (math.sin(lr_rad) * lr)
        + (math.sin(rr_rad) * rr)
        + (math.sin(lf_rad) * lf)
        + (math.sin(rf_rad) * rf)
    )
    Vy = (
        (math.cos(lr_rad) * lr)
        + (math.cos(rr_rad) * rr)
        + (math.cos(lf_rad) * lf)
        + (math.cos(rf_rad) * rf)
    )

    # Adjusts the angle corresponding to a diameter that is perpendicular to the radius (add or subtract 45deg)
    lr_rad = (lr_rad + (math.pi / 4)) % (2 * math.pi)
    rr_rad = (rr_rad - (math.pi / 4)) % (2 * math.pi)
    lf_rad = (lf_rad - (math.pi / 4)) % (2 * math.pi)
    rf_rad = (rf_rad + (math.pi / 4)) % (2 * math.pi)

    # Finds the rotational velocity by finding the torque and adding them up
    Vw = wheelbase_radius * (
        (math.cos(lr_rad) * -lr)
        + (math.cos(rr_rad) * rr)
        + (math.cos(lf_rad) * -lf)
        + (math.cos(rf_rad) * rf)
    )

    Vx *= 0.25
    Vy *= 0.25
    Vw *= 0.25

    return ChassisSpeeds.fromFeet(Vx, Vy, Vw)
