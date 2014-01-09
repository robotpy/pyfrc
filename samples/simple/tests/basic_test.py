#
# This is a py.test based testing system. Anything you can do with
# py.test, you can do with this too. There are a few magic parameters
# provided as fixtures that will allow your tests to access the robot
# code and stuff
#
#    robot - This is whatever is returned from the run function in robot.py
#    wpilib - This is the wpilib.internal module
#

class TestController(object):
    
    loop_count = 0
    
    def IsOperatorControl(self, tm):
        '''Continue operator control for 1000 control loops'''
        self.loop_count += 1
        return not self.loop_count == 1000

#
# Each of these functions is an individual test run by py.test. Global
# wpilib state is cleaned up between each test run, and a new robot
# object is created each time
#

def test_autonomous(robot, wpilib):
    
    wpilib.enabled = True
    robot.Autonomous()


def test_disabled(robot):
    robot.Disabled()


def test_operator_control(robot, wpilib):
    
    wpilib.set_test_controller(TestController)
    wpilib.enabled = True
    
    robot.OperatorControl()
    
    # do something like assert the motor == stick value

