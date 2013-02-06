'''
    This is a unit test of driving.py. It is designed to test both expected 
    functionality as well as if code is written correctly. If naming
    conventions are not followed this will break the test. If functionality
    is incorrect this test will print out failure
'''

# directory of component to test
robot_path = '../../robot/source/components'
import_robot = False

import fake_wpilib as wpilib


class Test(object):
    
    def __init__(self):
        self.l_motor = wpilib.Jaguar(1)
        self.r_motor = wpilib.Jaguar(2)
        self.drive = wpilib.RobotDrive(self.l_motor, self.r_motor)
        self.tested_driver = Driving(self.drive)
    
    def test_drive(self):
        #test 1, check if speed and rotation set correctly
        speed = 1
        rotation = .5
        leftMotorOutput = speed - rotation
        rightMotorOutput = max(speed, rotation)
        
        self.tested_driver.drive(self.rotation, self.speed)
        
        if self.l_motor.get() != 0 and \
        self.r_motor.get != 0:
            
            print("Motor speeds set before update called")
        
        self.tested_driver.update()
        
        if self.l_motor.get() != leftMotorOutput and \
        self.r_motor.get != rightMotorOutput:
            
            print("Motor speeds not set correctly in Test")
        
    
def run_test():
    import driving
    test = Test()
    