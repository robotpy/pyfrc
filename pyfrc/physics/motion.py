import hal
import typing


class LinearMotion:
    """
    Helper for simulating motion involving a encoder directly coupled to
    a motor.

    Here's an example that shows a linear motion of 6ft at 2 ft/s with a
    360-count-per-ft encoder, coupled to a PWM motor on port 0 and the
    first encoder object::

        import hal.simulation
        from pyfrc.physics import motion

        class PhysicsEngine:

            def __init__(self, physics_controller):
                self.motion = pyfrc.physics.motion.LinearMotion('Motion', 2, 360, 6)
                self.motor = hal.simulation.PWMSim(0)
                self.encoder = hal.simulation

            def update_sim(self, now, tm_diff):
                motor_value = self.motor.getValue()
                count = self.motion.compute(motor_value, tm_diff)
                self.encoder.setCount(count)

    .. versionadded:: 2018.3.0
    """

    #: Current computed position of motion, in feet
    position_ft = 0

    #: Current computed position of motion (encoder ticks)
    position_ticks = 0

    def __init__(
        self,
        name: str,
        motor_ft_per_sec: float,
        ticks_per_feet: int,
        max_position: typing.Optional[float] = None,
        min_position: typing.Optional[float] = 0,
    ):
        """
        :param name: Name of motion, shown in simulation UI
        :param motor_ft_per_sec: Motor travel in feet per second (or whatever units you want)
        :param ticks_per_feet: Number of encoder ticks per feet
        :param max_position: Maximum position that this motion travels to
        :param min_position: Minimum position that this motion travels to
        """
        self.name = name
        self.motor_ft_per_sec = motor_ft_per_sec
        self.ticks_per_feet = ticks_per_feet
        self.min_position = min_position
        self.max_position = max_position

        self.device = hal.SimDevice(self.name)
        self.position = self.device.createDouble("position", True, 0.0)

    def compute(self, motor_val, tm_diff):
        self.position_ft += motor_val * tm_diff * self.motor_ft_per_sec

        if self.max_position is not None:
            self.position_ft = min(
                max(self.position_ft, self.min_position), self.max_position
            )

        self.position_ticks = int(self.position_ft * self.ticks_per_feet)

        # This causes a label to be rendered in the UI
        self.position.set(self.position_ft)
        return self.position_ticks
