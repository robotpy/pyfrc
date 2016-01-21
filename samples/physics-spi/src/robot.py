#!/usr/bin/env python3

import wpilib

class MyRobot(wpilib.SampleRobot):
    '''Main robot class'''
    
    def robotInit(self):
        '''Robot-wide initialization code should go here'''
        
        self.lstick = wpilib.Joystick(0)
        self.rstick = wpilib.Joystick(1)
        
        self.l_motor = wpilib.Jaguar(1)
        self.r_motor = wpilib.Jaguar(2)
        
        # Position gets automatically updated as robot moves
        self.gyro = wpilib.ADXRS450_Gyro()
        
        self.robot_drive = wpilib.RobotDrive(self.l_motor, self.r_motor)
        
        self.motor = wpilib.Jaguar(4)
        
        self.limit1 = wpilib.DigitalInput(1)
        self.limit2 = wpilib.DigitalInput(2)
        
        self.position = wpilib.AnalogInput(2)
        
    def disabled(self):
        '''Called when the robot is disabled'''
        while self.isDisabled():
            wpilib.Timer.delay(0.01)

    def autonomous(self):
        '''Called when autonomous mode is enabled'''
        
        timer = wpilib.Timer()
        timer.start()
        
        while self.isAutonomous() and self.isEnabled():
            
            if timer.get() < 2.0:
                self.robot_drive.arcadeDrive(-1.0, -.3)
            else:
                self.robot_drive.arcadeDrive(0, 0)
            
            wpilib.Timer.delay(0.01)

    def operatorControl(self):
        '''Called when operation control mode is enabled'''
        
        timer = wpilib.Timer()
        timer.start()

        while self.isOperatorControl() and self.isEnabled():
            
            if timer.hasPeriodPassed(1.0):
                print("Gyro:", self.gyro.getAngle())
                
                # This is where the data ends up..
                #from hal_impl.data import hal_data
                #print(hal_data['robot'])
            
            self.robot_drive.arcadeDrive(self.lstick)

            # Move a motor with a Joystick
            y = self.rstick.getY()
            
            # stop movement backwards when 1 is on
            if self.limit1.get():
                y = max(0, y)
                
            # stop movement forwards when 2 is on
            if self.limit2.get():
                y = min(0, y)
                
            self.motor.set(y)

            wpilib.Timer.delay(0.04)

if __name__ == '__main__':
    
    wpilib.run(MyRobot,
               physics_enabled=True)

