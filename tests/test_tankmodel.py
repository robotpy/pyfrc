
# import pytest
from pyfrc.physics import tankmodel, motor_cfgs
from pyfrc.physics.units import units
from math import degrees, radians


def test_tankdrive_get_distance():
    tank = tankmodel.TankModel.theory(motor_cfgs.MOTOR_CFG_CIM,
                                      robot_mass=90*units.lbs,
                                      gearing=10.71,
                                      nmotors=2,
                                      x_wheelbase=2.0*units.feet,
                                      wheel_diameter=6*units.inch)
    l_motor = -1.0
    r_motor = 0.9
    # get the motors up to speed
    tank.get_distance(l_motor, r_motor, 2.0)

    # figure out how long to go to get 90deg
    angle = 0.0
    total_time = 0.0
    tstep = 0.01
    while angle < radians(90.0):
        result = tank.get_distance(l_motor, r_motor, tstep)
        angle += result[2]
        total_time += tstep

    print('time needed', total_time)

    result = tank.get_distance(l_motor, r_motor, total_time)
    print(result[0], result[1], degrees(result[2]), result[0]/result[1])
    assert abs(degrees(result[2]) - 90.0) < 2.0
    assert abs(result[0] / result[1] - 1.0) < 0.01
    return
