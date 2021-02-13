"""
    The 'vision simulator' provides objects that assist in modeling inputs
    from a camera processing system.
"""

import collections
import math

inf = float("inf")
twopi = math.pi * 2.0


def _in_angle_interval(x, a, b):
    return (x - a) % twopi <= (b - a) % twopi


class VisionSimTarget:
    """
    Target object that you pass the to the constructor of :class:`.VisionSim`
    """

    def __init__(self, x, y, view_angle_start, view_angle_end):
        """
        :param x: Target x position
        :param y: Target y position

        :param view_angle_start:
        :param view_angle_end: clockwise from start angle

        View angle is defined in degrees from 0 to 360, with 0 = east,
        increasing clockwise. So, if the robot could only see
        the target from the south east side, you would use a view angle
        of start=0, end=90.
        """
        self.x = x
        self.y = y

        self.view_angle_start = math.radians(view_angle_start)
        self.view_angle_end = math.radians(view_angle_end)

    def compute(self, now, x, y, angle):

        # incoming angle must be normalized to -180,180 (done in VisionSim)

        # note: the position tracking of the robot has Y incrementing
        # positively downwards, presumably because it's convenient for
        # drawing stuff. Not what I had expected.

        # compute target distance
        dx = self.x - x
        dy = self.y - y

        distance = math.hypot(dx, dy)

        # at the right distance?
        if distance < self.view_dst_start or distance > self.view_dst_end:
            return

        # determine the absolute angle of the target relative to the robot
        target_angle = math.atan2(dy, dx)

        # in the view range?
        if not _in_angle_interval(
            target_angle + math.pi, self.view_angle_start, self.view_angle_end
        ):
            return

        # is the robot facing the target?
        a = angle - self.fov2
        b = angle + self.fov2

        if _in_angle_interval(target_angle + math.pi, a + math.pi, b + math.pi):
            offset = math.degrees(
                (((target_angle - angle) + math.pi) % (math.pi * 2)) - math.pi
            )
            return (1, now, offset, distance)


class VisionSim:
    """
    This helper object is designed to help you simulate input from a
    vision system. The algorithm is a very simple approximation and
    has some weaknesses, but it should be a good start and general
    enough to work for many different usages.

    There are a few assumptions that this makes:

    - Your camera code sends new data at a constant frequency
    - The data from the camera lags behind at a fixed latency
    - If the camera is too close, the target cannot be seen
    - If the camera is too far, the target cannot be seen
    - You can only 'see' the target when the 'front' of the robot is
      around particular angles to the target
    - The camera is in the center of your robot (this simplifies some
      things, maybe fix this in the future...)

    To use this, create an instance in your physics simulator::

        targets = [
            VisionSim.Target(...)
        ]


    Then call the :meth:`compute` method from your ``update_sim`` method
    whenever your camera processing is enabled::

        # in physics engine update_sim()
        x, y, angle = self.physics_controller.get_position()

        if self.camera_enabled:
            data = self.vision_sim.compute(now, x, y, angle)
            if data is not None:
                self.nt.putNumberArray('/camera/target', data[0])
        else:
            self.vision_sim.dont_compute()

    .. note:: There is a working example in the examples repository
              you can use to try this functionality out
    """

    Target = VisionSimTarget

    def __init__(
        self,
        targets,
        camera_fov,
        view_dst_start,
        view_dst_end,
        data_frequency=15,
        data_lag=0.050,
        physics_controller=None,
    ):
        """
        There are a lot of constructor parameters:

        :param targets:          List of target positions (x, y) on field in feet
        :param view_angle_start: Center angle that the robot can 'see' the target from (in degrees)
        :param camera_fov:       Field of view of camera (in degrees)
        :param view_dst_start:   If the robot is closer than this, the target cannot be seen
        :param view_dst_end:     If the robot is farther than this, the target cannot be seen
        :param data_frequency:   How often the camera transmits new coordinates
        :param data_lag:         How long it takes for the camera data to be processed
                                 and make it to the robot
        :param physics_controller: If set, will draw target information in UI
        """

        fov2 = math.radians(camera_fov / 2.0)

        self.distance = 0
        self.update_period = 1.0 / data_frequency
        self.data_lag = data_lag

        self.last_compute_time = -10
        self.send_queue = collections.deque()

        self.targets = targets

        assert view_dst_start < view_dst_end
        assert self.data_lag > 0.001

        # objects = []
        # if physics_controller:
        #     objects = physics_controller.config_obj["pyfrc"]["field"]["objects"]

        for target in targets:
            target.camera_fov = camera_fov
            target.view_dst_start = view_dst_start
            target.view_dst_end = view_dst_end
            target.fov2 = fov2

            # objects.append(
            #     {"color": "red", "rect": [target.x - 0.1, target.y - 0.1, 0.4, 0.4]}
            # )

    def dont_compute(self):
        """
        Call this when vision processing should be disabled
        """
        self.send_queue.clear()

    def get_immediate_distance(self):
        """
        Use this data to feed to a sensor that is mostly instantaneous
        (such as an ultrasonic sensor).

        .. note:: You must call :meth:`compute` first.
        """
        return self.distance

    def compute(self, now, x, y, angle):
        """
        Call this when vision processing should be enabled

        :param now:   The value passed to ``update_sim``
        :param x:     Returned from physics_controller.get_position
        :param y:     Returned from physics_controller.get_position
        :param angle: Returned from physics_controller.get_position

        :returns: None or list of tuples of (found=0 or 1, capture_time, offset_degrees, distance).
                  The tuples are ordered by absolute offset from the
                  target. If a list is returned, it is guaranteed to have at
                  least one element in it.

                  Note: If your vision targeting doesn't have the ability
                  to focus on multiple targets, then you should ignore
                  the other elements.
        """

        # Normalize angle to [-180,180]
        output = []
        angle = ((angle + math.pi) % (math.pi * 2)) - math.pi

        for target in self.targets:
            proposed = target.compute(now, x, y, angle)
            if proposed:
                output.append(proposed)

        if not output:
            output.append((0, now, inf, 0))
            self.distance = None
        else:
            # order by absolute offset
            output.sort(key=lambda i: abs(i[2]))
            self.distance = output[-1][3]

        # Only store stuff every once in awhile
        if now - self.last_compute_time > self.update_period:

            self.last_compute_time = now
            self.send_queue.appendleft(output)

        # simulate latency by delaying camera output
        if self.send_queue:
            output = self.send_queue[-1]
            if now - output[0][1] > self.data_lag:
                return self.send_queue.pop()
