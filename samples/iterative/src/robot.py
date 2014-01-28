
try:
    import wpilib
except ImportError:
    from pyfrc import wpilib


class MyRobot(wpilib.IterativeRobot):
    '''Main robot class'''
    
    def __init__(self):
        '''Constructor'''
        super().__init__()
        
        self.lstick = wpilib.Joystick(1)
        self.motor = wpilib.CANJaguar(8)

    def AutonomousInit(self):
        '''Called only at the beginning of autonomous mode'''
        self.GetWatchdog().SetEnabled(False)

    def AutonomousPeriodic(self):
        '''Called every 20ms in autonomous mode'''
        pass

    def DisabledInit(self):
        '''Called only at the beginning of disabled mode'''
        pass
    
    def DisabledPeriodic(self):
        '''Called every 20ms in disabled mode'''
        pass

    def TeleopInit(self):
        '''Called only at the beginning of teleoperated mode'''
        dog = self.GetWatchdog()
        dog.SetEnabled(True)
        dog.SetExpiration(0.25)

    def TeleopPeriodic(self):
        '''Called every 20ms in teleoperated mode'''

        self.GetWatchdog().Feed()

        # Move a motor with a Joystick
        self.motor.Set(self.lstick.GetY())


def run():
    '''Called by RobotPy when the robot initializes'''
    
    robot = MyRobot()
    robot.StartCompetition()
    
    return robot


if __name__ == '__main__':
    wpilib.run()

