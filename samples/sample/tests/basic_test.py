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
    control.run_test(lambda tm: tm < 15)
    
    # make sure autonomous mode ran for 15 seconds
    assert int(fake_time.get()) == 15


def test_disabled(control, fake_time, robot):
    
    # run disabled mode for 5 seconds
    control.set_autonomous(enabled=False)
    control.run_test(lambda tm: tm < 5)
    
    # make sure disabled mode ran for 5 seconds
    assert int(fake_time.get()) == 5


def test_operator_control(control, robot, hal_data):
    
    class TestController:
        '''This object is only used for this test'''
    
        step_count = 0
        
        # Use two values because we're never quite sure when the value will
        # be changed by the robot... there's probably a better way to do this
        expected_value = 0
        
        def on_step(self, tm):
            '''
                Continue operator control for 1000 simulation steps. Each step
                represents roughly 20ms of fake time.
                
                The idea is to change the joystick/other inputs, and see if the 
                robot motors/etc respond the way that we expect. 
                
                Keep in mind that when you set a value, the robot code does not
                see the value until after this function returns AND the driver
                station delivers a new packet. Therefore when you use assert to
                check a motor value, you have to check to see that it matches
                the previous value that you set on the inputs, not the current
                value.
                
                :param tm: The current robot time in seconds
            '''
            self.step_count += 1
            
            pwm_val = hal_data['pwm'][8]['value']
            if pwm_val is not None:
                
                # motor value is equal to the previous value of the stick
                # -> Note that the PWM value isn't exact, because it was converted to
                #    a raw PWM value and then back to -1 to 1
                assert abs(pwm_val - self.expected_value) < 0.1
                
                # We do this so that we only check the value when it changes
                hal_data['pwm'][8]['value'] = None
            
                # set the stick value based on time
                
                self.expected_value = (tm % 2.0) - 1.0
                print("Set value", self.expected_value)
                hal_data['joysticks'][1]['axes'][1] = self.expected_value
            
            return not self.step_count == 1000
    
    # Initialize
    hal_data['pwm'][8]['value'] = None
    
    control.set_operator_control(enabled=True)
    control.run_test(TestController)

