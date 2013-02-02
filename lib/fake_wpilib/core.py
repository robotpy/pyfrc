from _wpilib import *

class RobotBase:
    def __init__(self):
        self.ds = DriverStation.GetInstance()
        self.watchdog = GetWatchdog()

    def IsSystemActive(self):
        return IsSystemActive()

    def GetWatchdog(self):
        return GetWatchdog()

    def IsEnabled(self):
        return IsEnabled()

    def IsDisabled(self):
        return IsDisabled()

    def IsAutonomous(self):
        return IsAutonomous()

    def IsOperatorControl(self):
        return IsOperatorControl()

    def IsTest(self):
        return IsTest()

    def IsNewDataAvailable(self):
        return IsNewDataAvailable()

class SimpleRobot(RobotBase):
    """The SimpleRobot class is intended to be subclassed by a user creating
    a robot program. Overridden Autonomous() and OperatorControl() methods
    are called at the appropriate time as the match proceeds. In the
    current implementation, the Autonomous code will run to completion
    before the OperatorControl code could start."""

    def __init__(self):
        super().__init__()
        self.watchdog.SetEnabled(False)

    def RobotInit(self):
        """Robot-wide initialization code should go here.
        Programmers should override this method for default Robot-wide
        initialization which will be called each time the robot enters
        the disabled state."""
        print("Default RobotInit() method... Overload me!")

    def Disabled(self):
        """Disabled should go here.
        Programmers should override this method to run code that should run
        while the field is disabled."""
        print("Default Disabled() method... Overload me!")

    def Autonomous(self):
        """Autonomous should go here.
        Programmers should override this method to run code that should run
        while the field is in the autonomous period. This will be called
        once each time the robot enters the autonomous state."""
        print("Default Autonomous() method... Overload me!")

    def OperatorControl(self):
        """Operator control (tele-operated) code should go here.
        Programmers should override this method to run code that should run
        while the field is in the Operator Control (tele-operated) period.
        This is called once each time the robot enters the teleop state."""
        print("Default OperatorControl() method... Overload me!")

    def Test(self):
        """Test program should go here. Programmers should override this
        method to run code that executes while the robot is in test mode.
        This will be called once whenever the robot enters test mode."""
        print("Default Test() method... Overload me!")

    def StartCompetition(self):
        """Start a competition.
        This code needs to track the order of the field starting to ensure
        that everything happens in the right order. Repeatedly run the correct
        method, either Autonomous or OperatorControl or Test when the robot is
        enabled. After running the correct method, wait for some state to
        change, either the other mode starts or the robot is disabled. Then go
        back and wait for the robot to be enabled again."""
        lw = LiveWindow.GetInstance()

        SmartDashboard.init()
        NetworkTable.GetTable("LiveWindow").GetSubTable("~STATUS~").PutBoolean("LW Enabled", False)

        if callable(getattr(self, "RobotMain", None)):
            self.RobotMain()
            return

        lw.SetEnabled(False)
        self.RobotInit()
        while True:
            if self.IsDisabled():
                self.ds.InDisabled(True)
                self.Disabled()
                self.ds.InDisabled(False)
                while self.IsDisabled():
                    self.ds.WaitForData()
            elif self.IsAutonomous():
                self.ds.InAutonomous(True)
                self.Autonomous()
                self.ds.InAutonomous(False)
                while self.IsAutonomous() and self.IsEnabled():
                    self.ds.WaitForData()
            elif self.IsTest():
                lw.SetEnabled(True)
                self.ds.InTest(True)
                self.Test()
                self.ds.InTest(False)
                while self.IsTest() and self.IsEnabled():
                    self.ds.WaitForData()
                lw.SetEnabled(False)
            else:
                self.ds.InOperatorControl(True)
                self.OperatorControl()
                self.ds.InOperatorControl(False)
                while self.IsOperatorControl() and self.IsEnabled():
                    self.ds.WaitForData()

class IterativeRobot(RobotBase):
    """IterativeRobot implements a specific type of Robot Program
    framework, extending the RobotBase class.

    The IterativeRobot class is intended to be subclassed by a user
    creating a robot program.

    This class is intended to implement the "old style" default code, by
    providing the following functions which are called by the main loop,
    StartCompetition(), at the appropriate times:

    RobotInit() -- provide for initialization at robot power-on

    Init() functions -- each of the following functions is called once
    when the appropriate mode is entered:
     - DisabledInit()   -- called only when first disabled
     - AutonomousInit() -- called each and every time autonomous is entered
                           from another mode
     - TeleopInit()     -- called each and every time teleop is entered
                           from another mode
     - TestInit()       -- called each and every time test is entered
                           from another mode

    Periodic() functions -- each of these functions is called iteratively
    at the appropriate periodic rate (aka the "slow loop").  The default
    period of the iterative robot is synced to the driver station control
    packets, giving a periodic frequency of about 50Hz (50 times per
    second).
     - DisabledPeriodic()
     - AutonomousPeriodic()
     - TeleopPeriodic()
     - TestPeriodic()
    """

    def __init__(self):
        super().__init__()
        self._disabledInitialized = False
        self._autonomousInitialized = False
        self._teleopInitialized = False
        self._testInitialized = False
        self._period = 0.0
        self._mainLoopTimer = Timer()
        self.watchdog.SetEnabled(False)

    def SetPeriod(self, period):
        """Set the period for the periodic functions.

        period: The period of the periodic function calls.  0.0 means sync
        to driver station control data.
        """
        if period > 0.0:
            # Not syncing with the DS, so start the timer for the main
            # loop
            self._mainLoopTimer.Reset()
            self._mainLoopTimer.Start()
        else:
            # Syncing with the DS, don't need the timer
            self._mainLoopTimer.Stop()
        self._period = period

    def GetPeriod(self):
        """Get the period for the periodic functions.
        Returns 0.0 if configured to syncronize with DS control data packets.
        Otherwise returns period of the periodic function calls."""
        return self._period

    period = property(GetPeriod, SetPeriod, None,
                      "Period for the periodic functions.")

    def GetLoopsPerSec(self):
        """Get the number of loops per second for the IterativeRobot.
        Returns frequency of the periodic function calls."""
        # If syncing to the driver station, we don't know the rate,
        # so guess something close.
        if self._period <= 0.0:
            return 50.0
        return 1.0 / self._period

    def StartCompetition(self):
        """Provide an alternate "main loop" via StartCompetition().

        This specific StartCompetition() implements "main loop" behavior
        like that of the FRC control system in 2008 and earlier, with a
        primary (slow) loop that is called periodically, and a "fast loop"
        (a.k.a. "spin loop") that is called as fast as possible with no
        delay between calls."""
        lw = LiveWindow.GetInstance()

        # first and one-time initialization
        SmartDashboard.init()
        NetworkTable.GetTable("LiveWindow").GetSubTable("~STATUS~").PutBoolean("LW Enabled", False)
        self.RobotInit()

        # loop forever, calling the appropriate mode-dependent function
        while True:
            # Call the appropriate function depending upon the current
            # robot mode
            if self.IsDisabled():
                # call DisabledInit() if we are now just entering disabled
                # mode from either a different mode or from power-on
                if not self._disabledInitialized:
                    lw.SetEnabled(False)
                    self.DisabledInit()
                    self._disabledInitialized = True
                    # reset the initialization flags for the other modes
                    self._autonomousInitialized = False
                    self._teleopInitialized = False
                    self._testInitialized = False
                if self.NextPeriodReady():
                    FRC_NetworkCommunication_observeUserProgramDisabled()
                    self.DisabledPeriodic()
            elif self.IsAutonomous():
                # call AutonomousInit() if we are now just entering
                # autonomous mode from either a different mode or from
                # power-on
                if not self._autonomousInitialized:
                    lw.SetEnabled(False)
                    self.AutonomousInit()
                    self._autonomousInitialized = True
                    # reset the initialization flags for the other modes
                    self._disabledInitialized = False
                    self._teleopInitialized = False
                    self._testInitialized = False
                if self.NextPeriodReady():
                    FRC_NetworkCommunication_observeUserProgramAutonomous()
                    self.AutonomousPeriodic()
                self.AutonomousContinuous()
            elif self.IsTest():
                # call TestInit() if we are now just entering
                # test mode from either a different mode or from
                # power-on
                if not self._testInitialized:
                    lw.SetEnabled(True)
                    self.TestInit()
                    self._testInitialized = True
                    # reset the initialization flags for the other modes
                    self._disabledInitialized = False
                    self._autonomousInitialized = False
                    self._teleopInitialized = False
                if self.NextPeriodReady():
                    FRC_NetworkCommunication_observeUserProgramTest()
                    self.TestPeriodic()
            else:
                # call TeleopInit() if we are now just entering teleop mode
                # from either a different mode or from power-on
                if not self._teleopInitialized:
                    lw.SetEnabled(False)
                    self.TeleopInit()
                    self._teleopInitialized = True
                    # reset the initialization flags for the other modes
                    self._disabledInitialized = False
                    self._autonomousInitialized = False
                    self._testInitialized = False
                    Scheduler.GetInstance().SetEnabled(True)
                if self.NextPeriodReady():
                    FRC_NetworkCommunication_observeUserProgramTeleop()
                    self.TeleopPeriodic()

            self.ds.WaitForData()

    def NextPeriodReady(self):
        """Determine if the periodic functions should be called.

        If self.period > 0.0, call the periodic function every self.period as
        compared to Timer.Get().  If self.period == 0.0, call the periodic
        functions whenever a packet is received from the Driver Station, or
        about every 20ms.

        TODO: Decide what this should do if it slips more than one cycle.
        """
        if self._period > 0.0:
            return self.mainLoopTimer.HasPeriodPassed(self._period)
        else:
            return self.ds.IsNewControlData()

    def RobotInit(self):
        """Robot-wide initialization code should go here.
        Users should override this method for default Robot-wide
        initialization which will be called when the robot is first powered
        on.  It will be called exactly 1 time."""
        print("Default RobotInit() method... Overload me!")

    def DisabledInit(self):
        """Initialization code for disabled mode should go here.
        Users should override this method for initialization code which will
        be called each time the robot enters disabled mode."""
        print("Default DisabledInit() method... Overload me!")

    def AutonomousInit(self):
        """Initialization code for autonomous mode should go here.
        Users should override this method for initialization code which will
        be called each time the robot enters autonomous mode."""
        print("Default AutonomousInit() method... Overload me!")

    def TeleopInit(self):
        """Initialization code for teleop mode should go here.
        Users should override this method for initialization code which will
        be called each time the robot enters teleop mode."""
        print("Default TeleopInit() method... Overload me!")

    def TestInit(self):
        """Initialization code for test mode should go here.
        Users should override this method for initialization code which will
        be called each time the robot enters test mode."""
        print("Default TestInit() method... Overload me!")

    def DisabledPeriodic(self):
        """Periodic code for disabled mode should go here.
        Users should override this method for code which will be called
        periodically at a regular rate while the robot is in disabled mode."""
        if not hasattr(self.DisabledPeriodic, "run"):
            self.DisabledPeriodic.run = True
            print("Default DisabledPeriodic() method... Overload me!")
        Wait(0.01)

    def AutonomousPeriodic(self):
        """Periodic code for autonomous mode should go here.
        Users should override this method for code which will be called
        periodically at a regular rate while the robot is in autonomous
        mode."""
        if not hasattr(self.AutonomousPeriodic, "run"):
            self.AutonomousPeriodic.run = True
            print("Default AutonomousPeriodic() method... Overload me!")
        Wait(0.01)

    def TeleopPeriodic(self):
        """Periodic code for teleop mode should go here.
        Users should override this method for code which will be called
        periodically at a regular rate while the robot is in teleop mode."""
        if not hasattr(self.TeleopPeriodic, "run"):
            self.TeleopPeriodic.run = True
            print("Default TeleopPeriodic() method... Overload me!")
        Wait(0.01)

    def TestPeriodic(self):
        """Periodic code for test mode should go here.
        Users should override this method for code which will be called
        periodically at a regular rate while the robot is in test mode."""
        if not hasattr(self.TestPeriodic, "run"):
            self.TestPeriodic.run = True
            print("Default TestPeriodic() method... Overload me!")
        Wait(0.01)

