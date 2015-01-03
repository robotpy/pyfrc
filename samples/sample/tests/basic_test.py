#
# This is a py.test based testing system. Anything you can do with
# py.test, you can do with this too. There are a few magic parameters
# provided as fixtures that will allow your tests to access the robot
# code and stuff
#
#    control - the wpilib.internal module
#    fake_time - the FAKETIME object that controls time
#    robot - This is whatever is returned from the run function in robot.py
#    robot_file - The filename of robot.py
#    robot_path - The directory name that robot.py is located in
#    wpilib - This is the wpilib module
#


#
# Each of these functions is an individual test run by py.test. Global
# wpilib state is cleaned up between each test run, and a new robot
# object is created each time
#

def test_autonomous(control, fake_time, robot):
    
    # run autonomous mode for 10 seconds
    control.set_autonomous(enabled=True)
    control.on_step = lambda tm: tm < 10
    
    robot.robotInit()
    robot.autonomous()
    
    # make sure autonomous mode ran for 10 seconds
    assert int(fake_time.get()) == 10


def test_disabled(control, fake_time, robot):
    
    # run disabled mode for 5 seconds
    control.set_autonomous(enabled=False)
    control.on_step = lambda tm: tm < 5
    
    robot.robotInit()
    robot.disabled()
    
    # make sure disabled mode ran for 5 seconds
    assert int(fake_time.get()) == 5


def test_operator_control(control, robot, hal_data):
    
    class TestController:
        '''This object is only used for this test'''
    
        loop_count = 0
        
        stick_prev = 0
        
        def on_step(self, tm):
            '''
                Continue operator control for 1000 control loops
                
                The idea is to change the joystick/other inputs, and see if the 
                robot motors/etc respond the way that we expect. 
                
                Keep in mind that when you set a value, the robot code does not
                see the value until after this function returns. So, when you
                use assert to check a motor value, you have to check to see that
                it matches the previous value that you set on the inputs, not the
                current value.
            '''
            self.loop_count += 1
            #print(self.loop_count)
            #print("STEP", tm)
            #print("MOO", hal_data['joysticks'][1]['axes'][1])
            
            # motor value is equal to the previous value of the stick
            assert abs(hal_data['pwm'][8]['value'] - self.stick_prev) < 0.1
            
            # set the stick value based on time
            self.stick_prev = (tm % 2.0) - 1.0
            hal_data['joysticks'][1]['axes'][1] = self.stick_prev
            #print("Set", hal_data['joysticks'][1]['axes'][1])
            return not self.loop_count == 1000
    
    control.set_operator_control(enabled=True)
    control.on_step = TestController
    
    robot.robotInit()
    robot.operatorControl()
    
    # do something like assert the motor == stick value

