
import pytest
from pyfrc.physics import drivetrains

@pytest.mark.parametrize("l_motor,r_motor,output", [
    ( 0,  0, ( 0,  0)), # stationary
    (-1,  1, ( 1,  0)), # forward
    ( 1, -1, (-1,  0)), # backwards
    ( 1,  1, ( 0, -1)), # rotate left
    (-1, -1, ( 0,  1)), # rotate right
])
def test_two_motor_drivetrain(l_motor, r_motor, output):
    result = drivetrains.two_motor_drivetrain(l_motor, r_motor, speed=1)
    assert abs(result[0] - output[0]) < 0.001
    assert abs(result[1] - output[1]) < 0.001
    

@pytest.mark.parametrize("lr_motor,rr_motor,lf_motor,rf_motor,output", [
    ( 0,  0,  0,  0, ( 0,  0)), # stationary
    (-1,  1, -1,  1, ( 1,  0)), # forward
    ( 1, -1,  1, -1, (-1,  0)), # backwards
    ( 1,  1,  1,  1, ( 0, -1)), # rotate left
    (-1, -1, -1, -1, ( 0,  1)), # rotate right
])    
def test_four_motor_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, output):
    result = drivetrains.four_motor_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, speed=1)
    assert abs(result[0] - output[0]) < 0.001
    assert abs(result[1] - output[1]) < 0.001

@pytest.mark.parametrize("lr_motor,rr_motor,lf_motor,rf_motor,output", [
    ( 0,  0,  0,  0, ( 0,  0,  0)), # stationary
    ( 1,  1,  1,  1, ( 0,  1,  0)), # forward
    (-1, -1, -1, -1, ( 0, -1,  0)), # backwards
    ( 1, -1, -1,  1, (-1,  0,  0)), # strafe left
    (-1,  1,  1, -1, ( 1,  0,  0)), # strafe right
    (-1,  1, -1,  1, ( 0,  0, -1)), # rotate left
    ( 1, -1,  1, -1, ( 0,  0,  1)), # rotate right
])    
def test_mecanum_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, output):
    result = drivetrains.mecanum_drivetrain(lr_motor, rr_motor, lf_motor, rf_motor, speed=1, x_wheelbase=1, y_wheelbase=1)
    assert abs(result[0] - output[0]) < 0.001
    assert abs(result[1] - output[1]) < 0.001
    assert abs(result[2] - output[2]) < 0.001
