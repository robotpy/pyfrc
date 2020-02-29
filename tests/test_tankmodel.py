# import pytest
from pyfrc.physics import tankmodel, motor_cfgs
from pyfrc.physics.units import units
import math


def test_tankdrive_get_distance():
    """Test TankModel.get_distance() by driving in a quarter circle.
    If the turn angle is 90deg, then x should equal y. get_distance() runs in little steps,
    so multiple calls should be equivalent to a single call"""

    # just use the default robot
    tank = tankmodel.TankModel.theory(
        motor_cfgs.MOTOR_CFG_CIM,
        robot_mass=90 * units.lbs,
        gearing=10.71,
        nmotors=2,
        x_wheelbase=2.0 * units.feet,
        wheel_diameter=6 * units.inch,
    )
    # slight turn to the right
    l_motor = 1.0
    r_motor = -0.9

    # get the motors up to speed, so that subsequent calls produce the same result
    tank.calculate(l_motor, r_motor, 2.0)

    # figure out how much time is needed to turn 90 degrees
    angle = 0.0
    angle_target = -math.pi / 2.0  # 90 degrees
    total_time = 0.0
    tstep = 0.01

    while angle < angle_target:
        result = tank.calculate(l_motor, r_motor, tstep)
        angle += result.rotation().radians()
        total_time += tstep

    # print('time needed', total_time)

    # OK, now do it in a single call. x should equal y
    result = tank.calculate(l_motor, r_motor, total_time)
    # print(result[0], result[1], degrees(result[2]), result[0]/result[1])
    assert math.isclose(
        result.rotation().radians(), angle_target, abs_tol=2.0
    ), "Single call should produce a 90deg turn"
    assert math.isclose(
        result.translation().x, result.translation().y, rel_tol=0.01
    ), "For 90deg turn, x and y should be the same"
    return
