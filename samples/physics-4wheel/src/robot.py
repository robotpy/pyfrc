
try:
    import wpilib
except ImportError:
    from pyfrc import wpilib


class MyRobot(wpilib.SimpleRobot):
    '''Main robot class'''
    
    def __init__(self):
        '''Constructor'''
        super().__init__()
        
        self.lstick = wpilib.Joystick(1)
        self.rstick = wpilib.Joystick(2)
        
        self.lr_motor = wpilib.Jaguar(1)
        self.rr_motor = wpilib.Jaguar(2)
        self.lf_motor = wpilib.Jaguar(3)
        self.rf_motor = wpilib.Jaguar(4)
        
        self.robot_drive = wpilib.RobotDrive(self.lr_motor, self.rr_motor,
                                             self.lf_motor, self.rf_motor)
        
        # Position gets automatically updated as robot moves
        self.gyro = wpilib.Gyro(1)
         
    def Disabled(self):
        '''Called when the robot is disabled'''
        while self.IsDisabled():
            wpilib.Wait(0.01)

    def Autonomous(self):
        '''Called when autonomous mode is enabled'''
        
        timer = wpilib.Timer()
        timer.Start()
        
        self.GetWatchdog().SetEnabled(False)
        while self.IsAutonomous() and self.IsEnabled():
            
            if timer.Get() < 2.0:
                self.robot_drive.ArcadeDrive(-1.0, -.3)
            else:
                self.robot_drive.ArcadeDrive(0, 0)
            
            wpilib.Wait(0.01)

    def OperatorControl(self):
        '''Called when operation control mode is enabled'''
        
        dog = self.GetWatchdog()
        dog.SetEnabled(True)
        dog.SetExpiration(0.25)

        while self.IsOperatorControl() and self.IsEnabled():
            dog.Feed()
            
            self.robot_drive.TankDrive(self.lstick, self.rstick)

            wpilib.Wait(0.04)


def run():
    '''Called by RobotPy when the robot initializes'''
    
    robot = MyRobot()
    robot.StartCompetition()
    
    return robot


if __name__ == '__main__':
    
    wpilib.require_version('2014.7.2')
    
    import physics
    wpilib.internal.physics_controller.setup(physics)
    
    wpilib.run()

