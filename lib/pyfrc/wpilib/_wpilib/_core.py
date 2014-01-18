'''
    This is not a complete implementation of WPILib. Add more things
    as needed, and submit patches! :) 
'''

import math
import threading

from ._fake_time import GetClock
from . import internal

#################################################
#
# WPILib Functionality
#
#################################################


def IsAutonomous():
    return internal.on_IsAutonomous(GetClock())

def IsEnabled():
    return internal.on_IsEnabled()
    
def IsDisabled():
    return not internal.on_IsEnabled()
    
def IsOperatorControl():
    return internal.on_IsOperatorControl(GetClock())

def IsTest():
    return True

def IsNewDataAvailable():
    return internal.on_IsNewDataAvailable()

def IsSystemActive():
    return internal.on_IsSystemActive()
    
def GetWatchdog():
    return Watchdog.GetInstance()

def _StartCompetition(self):
    from .._wpilib import SmartDashboard
    SmartDashboard.init()
    self._sr_competition_started = True

    
class SpeedController(object):

    def __init__(self):
        pass
    
    def Get(self):
        raise NotImplementedError()
    
    def Set(self, value, syncGroup=0):
        raise NotImplementedError()
        
    def Disable(self):
        raise NotImplementedError()
    
    
class Accelerometer(object):

    def __init__(self, channel):
        AnalogModule._add_channel(channel, self)
        self.value = 0
        
    def GetAcceleration(self):
        return self.value
        
    def SetSensitivity(self, sensitivity):
        pass
        
    def SetZero(self, zero):
        pass


class AnalogModule(object):

    _channels = [None]*8
    
    @staticmethod
    def _reset():
        AnalogModule._channels = [None]*8
    
    @staticmethod
    def _add_channel(channel, item):
        if AnalogModule._channels[channel-1] is not None:
            raise RuntimeError( "Error inserting %s, %s already at channel %s" % 
                               (item, AnalogModule._channels[channel-1], channel ))
        AnalogModule._channels[channel-1] = item
    
    @staticmethod
    def _print_components():
        '''Useful for ensuring you set your robot up the way you thought...'''
        print("AnalogModule:")
        
        for i,o in enumerate(AnalogModule._channels):
            if o is not None:
                print( "  %2d: %s" % (i+1,o) )
        

class AnalogChannel(object):

    kAccumulatorModuleNumber = 1
    kAccumulatorNumChannels = 2
    kAccumulatorChannels = [1, 2]
    
    _instances = [None]*8
    
    @staticmethod
    def _reset():
        AnalogChannel._instances = [None]*8
    
    def __init__(self, channel):
        AnalogModule._add_channel(channel, self)
        self.value = 0
        self.voltage = 0
        
    def GetValue(self):
        return self.value
        
    def GetAverageValue(self):
        return self.average_value
        
    def GetVoltage(self):
        return self.voltage
        
    def GetAverageVoltage(self):
        return self.average_voltage
        
    # TODO: Implement a sensible implementation for this


class CAN(object):

    _devices = {}
    
    @staticmethod
    def _reset():
        CAN._devices = {}

    @staticmethod
    def _add_can(deviceNumber, device):
        if deviceNumber in CAN._devices:
            raise RuntimeError( "Error inserting %s, %s already at %s" % 
                                (device, CAN._devices[deviceNumber], deviceNumber))
                                
        CAN._devices[deviceNumber] = device
        
    @staticmethod
    def _print_components():
        '''Useful for ensuring you set your robot up the way you thought...'''
        print("CAN:")
        
        for i,o in CAN._devices.items():
            print( "  %2d: %s" % (i,o) )
    
class CANJaguar(SpeedController):

    # ControlMode
    kPercentVbus = 1
    kCurrent = 2
    kSpeed = 3
    kPosition = 4
    kVoltage = 5
    
    # Limits
    kForwardLimit = 1
    kReverseLimit = 2
    
    # PositionReference
    kPosRef_QuadEncoder = 0
    kPosRef_Potentiometer = 1
    kPosRef_None = 0xFF
    
    # SpeedReference
    kSpeedRef_Encoder = 0
    kSpeedRef_InvEncoder = 2
    kSpeedRef_QuadEncoder = 3
    kSpeedRef_None = 0xFF
    
    # NeutralMode
    kNeutralMode_Brake = 1
    kNeutralMode_Coast = 2
    
    # LimitMode
    kLimitMode_SwitchInputsOnly = 0
    kLimitMode_SoftPositionLimits = 1
    
    def __init__(self, deviceNumber, controlMode=kPercentVbus):
        SpeedController.__init__(self)
        CAN._add_can(deviceNumber, self)
        self.control_mode = controlMode
        self.forward_ok = True              # forward limit switch
        self.reverse_ok = True              # reverse limit switch
        self.position = 0
        self.speed = 0
        self.value = 0
    
    def ChangeControlMode(self, mode):
        self.control_mode = mode
    
    def ConfigEncoderCodesPerRev(self, codes):
        pass
        
    def ConfigFaultTime(self, faultTime):
        pass
        
    def ConfigMaxOutputVoltage(self, voltage):
        pass
    
    def ConfigNeutralMode(self, mode):
        pass
    
    def ConfigPotentiometerTurns(self, turns):
        pass
        
    def ConfigSoftPositiionLimits(self, forward, reverse):
        pass
        
    def DisableControl(self):
        pass
        
    def DisableSoftPositionLimits(self):
        pass
        
    def EnableControl(self, encoder_position=0):
        pass
        
    def Get(self):
        return self.value
        
    def GetControlMode(self):
        return self.control_mode
        
    def GetFirmwareVersion(self):
        return 0
        
    def GetForwardLimitOK(self):
        return self.forward_ok
        
    def GetOutputCurrent(self):
        return 0.0
        
    def GetOutputVoltage(self):
        return 0.0
        
    def GetP(self):
        return self.p
        
    def GetI(self):
        return self.i
        
    def GetD(self):
        return self.d
        
    def GetReverseLimitOK(self):
        return self.reverse_ok
        
    def GetPosition(self):
        if hasattr(self, 'position_reference'):
            return self.position
        else:
            raise RuntimeError("No position reference set")
        
    def GetSpeedReference(self):
        return self.speed_reference
        
    def GetSpeed(self):
        if hasattr(self, 'speed_reference'):
            return self.speed
        else:
            raise RuntimeError("No speed reference set")
        
    def Set(self, value, syncGroup=0):
        self.value = value
        
    def SetPID(self, p, i, d):
        self.p = p
        self.i = i
        self.d = d
        
    def SetPositionReference(self, positionReference):
        self.position_reference = positionReference
        
    def SetSpeedReference(self, speedReference):
        self.speed_reference = speedReference
        
    def SetVoltageRampRate(self, rampRate):
        pass
        
    @staticmethod
    def UpdateSyncGroup(group):
        pass
    
class Compressor(object):
    
    def __init__(self, pressureSwitchChannel, compressorRelayChannel):
        DigitalModule._add_io( pressureSwitchChannel, self )
        DigitalModule._add_relay( compressorRelayChannel, self )
        self.enabled = False
        self.value = 0
        
    def Enabled(self):
        return self.enabled
    
    def Start(self):
        self.enabled = True
        
    def Stop(self):
        self.enabled = False
        
    def GetPressureSwitchValue(self):
        return self.value

        
class DigitalModule(object):

    _io = [None] * 16
    _pwm = [None] * 10
    _relays = [None] * 8
    
    @staticmethod
    def _reset():
        DigitalModule._io = [None]*16
        DigitalModule._pwm = [None]*10
        DigitalModule._relays = [None]*8
    
    @staticmethod
    def _add_io(channel, item):
        if DigitalModule._io[channel-1] is not None:
            raise RuntimeError( "Error inserting %s, %s already at channel %s" % 
                               (item, DigitalModule._io[channel-1], channel ))
        DigitalModule._io[channel-1] = item
        
    @staticmethod
    def _add_pwm(channel, item):
        if DigitalModule._pwm[channel-1] is not None:
            raise RuntimeError( "Error inserting %s, %s already at channel %s" % 
                               (item, DigitalModule._pwm[channel-1], channel ))
        DigitalModule._pwm[channel-1] = item
        
    @staticmethod
    def _add_relay(channel, item):
        if DigitalModule._relays[channel-1] is not None:
            raise RuntimeError( "Error inserting %s, %s already at channel %s" % 
                               (item, DigitalModule._relays[channel-1], channel ))
        DigitalModule._relays[channel-1] = item
    
    @staticmethod
    def _print_components():
        '''Useful for ensuring you set your robot up the way you thought...'''
        print("DigitalModule:")
        
        print( "  IO:")
        for i,o in enumerate(DigitalModule._io):
            if o is not None:
                print( "    %2d: %s" % (i+1,o) )
                
        print( "  PWM:")
        for i,o in enumerate(DigitalModule._pwm):
            if o is not None:
                print( "    %2d: %s" % (i+1,o) )
        
        print( "  Relay:")
        for i,o in enumerate(DigitalModule._relays):
            if o is not None:
                print( "    %2d: %s" % (i+1,o) )
    
class DigitalInput(object):

    def __init__(self, channel):
        DigitalModule._add_io( channel, self )
        self._value = 0
        self.channel = channel
    
    def Get(self):
        return self.value
        
    def GetChannel(self):
        return self.channel
        
    # testing use only, not present on the robot
        
    @property
    def value(self):
        return self._value
        
    @value.setter
    def value(self, value):
        if value:
            self._value = 1
        else:
            self._value = 0
     
     
class DigitalOutput(object):
    
    def __init__(self, channel):
        DigitalModule._add_io( channel, self )
        self._value = 0
        self.channel = channel

    def Get(self):
        return self.value
       
    def Set(self, value):
        self.value = value
        
    # testing use only, not present on the robot
        
    @property
    def value(self):
        return self._value
        
    @value.setter
    def value(self, value):
        if value:
            self._value = 1
        else:
            self._value = 0

class DriverStation(object):
    
    kBatteryModuleNumber = 1
    kBatteryChannel = 8
    kJoystickPorts = 4
    kJoystickAxes = 6
    
    # Alliance
    kRed = 0
    kBlue = 1
    kInvalid = 2
    
    @staticmethod
    def _reset():
        if hasattr(DriverStation, '_instance'):
            delattr(DriverStation, '_instance')
        
    @staticmethod
    def GetInstance():
        try:
            return DriverStation._instance
        except AttributeError:
            DriverStation._instance = DriverStation._DriverStation()
            return DriverStation._instance
    
    class _DriverStation:
        def __init__(self):
    
            # when running multiple threads, be sure to grab this
            # lock before modifying any of the DS internal state
            self.lock = threading.RLock()
        
            AnalogModule._add_channel(DriverStation.kBatteryChannel, self)
        
            # TODO: Need to sync this with the enhanced I/O
            self.digital_in = [ False, False, False, False, False, False, False, False ]
            self.fms_attached = False
            self.enhanced_io = DriverStationEnhancedIO._inner()
            self.alliance = DriverStation.kInvalid
            
            self.new_control_data = False
            
            # arrays of [port][axis/button]
            self.sticks = []
            self.stick_buttons = []
            
            for i in range(0, DriverStation.kJoystickPorts):
                axes = [ 0.0 ] * DriverStation.kJoystickAxes
                buttons = [ False ] * 16
                
                self.sticks.append(axes)
                self.stick_buttons.append(buttons)
        
        def GetAlliance(self):
            with self.lock:
                return self.alliance
        
        def GetDigitalIn(self, number):
            with self.lock:
                return self.digital_in[number-1]
            
        def GetEnhancedIO(self):
            return self.enhanced_io
        
        def GetStickAxis(self, stick, axis):
            with self.lock:
                return self.sticks[stick-1][axis]
            
        def GetStickButtons(self, stick):
            with self.lock:
                buttons = 0
                for i, button in enumerate(self.stick_buttons[stick-1]):
                    if button:
                        buttons |= (1 << i)
        
            return buttons
        
        def IsFMSAttached(self):
            with self.lock:
                return self.fms_attached 
            
        def IsNewControlData(self):
            with self.lock:
                new_data = self.new_control_data
                self.new_control_data = False
            return new_data
        
        def SetDigitalOut(self, number, value):
            pass
        
class DriverStationEnhancedIO(object):
    
    kUnknown = 1
    kInputFloating = 2 
    kInputPullUp = 3
    kInputPullDown = 4
    kOutput = 5
    kPWM = 6
    kAnalogComparator = 7
    
    _kInputTypes = [kInputFloating, kInputPullUp, kInputPullDown]

    class _inner:

        # don't call this directly
        def __init__(self):
            self.digital = [ False, False, False, False, 
                             False, False, False, False,
                             False, False, False, False,
                             False, False, False, False ]
                            
            self.digital_config = [ None, None, None, None,
                                    None, None, None, None,
                                    None, None, None, None,
                                    None, None, None, None ]
            
        def GetDigital(self, channel):
            if self.digital_config[channel-1] not in DriverStationEnhancedIO._kInputTypes:
                raise RuntimeError( "Digital channel not configured as input, configured as %s" % self.digital_config[channel-1] )
            return self.digital[channel-1]
            
        def GetDigitalConfig(self, channel):
            config = self.digital_config[channel-1]
            if config is None:
                return DriverStationEnhancedIO.kUnknown
            return config
            
        def SetDigitalConfig(self, channel, config):
            if self.digital_config[channel-1] is not None:
                raise RuntimeError( "Configured digital channel twice!" )
            self.digital_config[channel-1] = config
        
        def SetDigitalOutput(self, channel, value):
            if self.digital_config[channel-1] != DriverStationEnhancedIO.kOutput:
                raise RuntimeError( "Digital channel not configured as output, configured as %s" % self.digital_config[channel-1] )
            self.digital[channel-1] = bool(value)
            
    
        def _print_components(self):
            '''Debugging use only'''
            print( "DriverStationEnhancedIO:" )
            for i,o in enumerate(self.digital_config):
                if o is not None:
                    od = {
                        DriverStationEnhancedIO.kUnknown: "kUnknown",
                        DriverStationEnhancedIO.kInputFloating: "kInputFloating",
                        DriverStationEnhancedIO.kInputPullUp: "kInputPullUp",
                        DriverStationEnhancedIO.kInputPullDown: "kInputPullDown",
                        DriverStationEnhancedIO.kOutput: "kOutput"
                    }
                    
                    print( "  %2d: %s" % (i+1, od[o]))
        
class Encoder(object):

    # encoding_type
    k1X = 1
    k2X = 2
    k4X = 3

    # pid_source
    kDistance = 1
    kRate = 2

    def __init__(self, port1, port2, reverseDirection=False, encoding_type=k1X ):
        DigitalModule._add_io( port1, self )
        DigitalModule._add_io( port2, self )
        self.value = None
        self.pid_mode = Encoder.kDistance
        self.rate = 0 # TODO: calculate this
        
    def Get(self):
        return self.value
        
    def GetRate(self):
        # TODO: calculate this
        return self.rate
        
    def GetPeriod(self):
        return self.period
        
    def PIDGet(self):
        if self.pid_mode == Encoder.kDistance:
            return self.value
        else:
            return self.rate
            
    def Reset(self):
        self.value = 0
    
    def SetDistancePerPulse(self, distance):
        pass
        
    def SetPIDSourceParameter(self, pid_source):
        self.pid_mode = pid_source
        
    def Start(self):
        self.value = 0
        
    def Stop(self):
        pass


class GenericHID(object):
    kLeftHand = 0
    kRightHand = 1
    
        
class Gyro(object):
    
    kSamplesPerSecond = 50.0
    kCalibrationSampleTime = 5.0
    kDefaultVoltsPerDegreePerSecond = 0.007
    
    def __init__(self, channel):
        AnalogModule._add_channel(channel, self)
        self.value = 0
        
    def GetAngle(self):
        return self.value
    
    def Reset(self):
        self.value = 0
    
    def SetSensitivity(self, voltsPerDegreePerSecond):
        pass
        
        
class Jaguar(SpeedController):

    def __init__(self, channel):
        SpeedController.__init__(self)
        DigitalModule._add_pwm( channel, self )
        self.value = 0
        
    def Get(self):
        return self.value
        
    def Set(self, value, syncGroup=0):
        self.value = value
        
        
class Joystick(GenericHID):
    
    kDefaultXAxis = 1
    kDefaultYAxis = 2
    kDefaultZAxis = 3
    kDefaultTwistAxis = 4
    kDefaultThrottleAxis = 3
    
    kXAxis = 0
    kYAxis = 1
    kZAxis = 2
    kTwistAxis = 3
    kThrottleAxis = 4
    kNumAxisTypes = 5
    
    kDefaultTriggerButton = 1
    kDefaultTopButton = 2
    
    kTriggerButton = 0
    kTopButton = 1
    kNumButtonTypes = 2
    
    def __init__(self, port):
        self.port = port
        self._ds = DriverStation.GetInstance()
        
        self.axes = [Joystick.kDefaultXAxis, 
                     Joystick.kDefaultYAxis, 
                     Joystick.kDefaultZAxis, 
                     Joystick.kDefaultTwistAxis, 
                     Joystick.kDefaultThrottleAxis]
                     
        # TODO
        #self.buttons = [Joystick.kDefaultTriggerButton,
        #                Joystick.kDefaultTopButton]
        
    def GetAxis(self, axis_type):
        return self.GetRawAxis(self.axes[axis_type])
        
    def GetAxisChannel(self, axis_type):
        return self.axes[axis_type]
        
    def GetButton(self, button_type):
        if button_type == Joystick.kTriggerButton:
            return self.GetTrigger()
        elif button_type == Joystick.kTopButton:
            return self.GetTop()
            
        raise RuntimeError('Invalid button type specified')
    
    def GetDirectionDegrees(self):
        return (180.0/math.acos(-1.0)) * self.GetDirectionRadians()
    
    def GetDirectionRadians(self):
        return math.atan2(self.x, -self.y)
        
    def GetMagnitude(self):
        return math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))
        
    def GetRawAxis(self, axis):
        return self._ds.GetStickAxis(self.port, axis)
        
    def GetRawButton(self, number):
        return self._get_button(number)
        
    def GetThrottle(self):
        return self.GetRawAxis(self.axes[Joystick.kThrottleAxis])
        
    def GetTop(self):
        return self.GetRawButton(Joystick.kTopButton)
        
    def GetTrigger(self):
        return self.GetRawButton(Joystick.kTriggerButton)
        
    def GetTwist(self):
        return self.GetRawAxis(self.axes[Joystick.kTwistAxis])
        
    def GetX(self):
        return self.GetRawAxis(self.axes[Joystick.kXAxis])
        
    def GetY(self):
        return self.GetRawAxis(self.axes[Joystick.kYAxis])
        
    def GetZ(self):
        return self.GetRawAxis(self.axes[Joystick.kZAxis])
        
    def SetAxisChannel(self, axis_type, channel):
        self.axes[axis_type] = channel
    
    def _limit(self, value):
        return min(max(float(value), -1.0), 1.0)
    
    # internal API
    def _set_x(self, value):
        with self._ds.lock:
            self._ds.sticks[self.port-1][self.axes[Joystick.kXAxis]] = self._limit(value)
        
    def _set_y(self, value):
        with self._ds.lock:
            self._ds.sticks[self.port-1][self.axes[Joystick.kYAxis]] = self._limit(value)
            
    def _set_z(self, value):
        with self._ds.lock:
            self._ds.sticks[self.port-1][self.axes[Joystick.kZAxis]] = self._limit(value)
            
    def _set_twist(self, value):
        with self._ds.lock:
            self._ds.sticks[self.port-1][self.axes[Joystick.kTwistAxis]] = self._limit(value)
            
    def _set_throttle(self, value):
        with self._ds.lock:
            self._ds.sticks[self.port-1][self.axes[Joystick.kThrottleAxis]] = self._limit(value)
            
    def _get_button(self, number):
        with self._ds.lock:
            return self._ds.stick_buttons[self.port-1]
        
    def _set_button(self, number, value):
        with self._ds.lock:
            self._ds.stick_buttons[self.port-1] = bool(value) 
    
    # internal properties to make testing easier
    # -> DO NOT USE THESE FROM ROBOT CODE
    x = property(GetX, _set_x)
    y = property(GetY, _set_y)
    z = property(GetZ, _set_z)
    twist = property(GetTwist, _set_twist)
    throttle = property(GetThrottle, _set_throttle)
    
    
class KinectStick(Joystick):
    pass
    
    
class RobotDrive(object):

    kFrontLeftMotor = 0
    kFrontRightMotor = 1
    kRearLeftMotor = 2
    kRearRightMotor = 3 
    
    kMaxNumberOfMotors = 4
    
    def __init__(self, lr_motor, rr_motor, lf_motor=None, rf_motor=None):
        self.lr_motor = lr_motor    # left rear
        self.rr_motor = rr_motor    # right rear
        self.lf_motor = lf_motor    # left front
        self.rf_motor = rf_motor    # right front
        
        self.maxOutput = 1.0
        self.inverted = [1,1,1,1]
        
    def ArcadeDrive(self, *args, **kwargs):
        
        # parse the arguments first
        # -> TODO: There has to be a better way to do this
        squaredInputs = False
        
        if len(kwargs) == 1:
            args.append(kwargs['squaredInputs'])
        elif len(kwargs) != 0:
            raise ValueError('RobotDrive.ArcadeDrive takes exactly one named argument')
        
        if len(args) == 1:
            
            # ArcadeDrive(GenericHID, squaredInputs)
            if not isinstance(args[0], GenericHID):
                raise TypeError("Invalid parameter 1 (expected GenericHID, got %s)", args[0])
            
            moveValue = args[0].GetY()
            rotateValue = args[0].GetX()
            
        elif len(args) == 2:
            
            # ArcadeDrive(GenericHID, squaredInputs)
            if isinstance(args[0], GenericHID) and isinstance(args[1], bool):
                moveValue = args[0].GetY()
                rotateValue = args[0].GetX()
                squaredInputs = args[1]
                
            # ArcadeDrive(moveValue, rotateValue, squaredInputs)
            elif isinstance(args[0], (float, int)) and isinstance(args[1], (float, int)):
                moveValue, rotateValue = args
                
            else:
                raise TypeError("Invalid parameters for RobotDrive.ArcadeDrive()")
                
        elif len(args) == 3:
            
            # ArcadeDrive(moveValue, rotateValue, squaredInputs)
            if not isinstance(args[0], float):
                raise TypeError("Invalid parameter 1: expected float, got %s" % type(args[0]))
            
            if not isinstance(args[1], float):
                raise TypeError("Invalid parameter 2: expected float, got %s" % type(args[1]))
            
            if not isinstance(args[2], bool):
                raise TypeError("Invalid parameter 3: expected float, got %s" % type(args[2]))
            
            moveValue, rotateValue, squaredInputs = args
            
        else:
            raise TypeError("Invalid arguments")
        
        
        # Actually do the function now
        
        moveValue = self._Limit(moveValue)
        rotateValue = self._Limit(rotateValue)
        
        if squaredInputs:
        
            if moveValue >= 0.0:
                moveValue = moveValue*moveValue
            else:
                moveValue = -(moveValue*moveValue)
                
            if rotateValue >= 0.0:
                rotateValue = rotateValue*rotateValue
            else:
                rotateValue = -(rotateValue*rotateValue)
                
        if moveValue > 0.0:
            if rotateValue > 0.0:
                leftMotorOutput = moveValue - rotateValue
                rightMotorOutput = max(moveValue, rotateValue)
            else:
                leftMotorOutput = max(moveValue, -rotateValue)
                rightMotorOutput = moveValue + rotateValue
        else:
            if rotateValue > 0.0:
                leftMotorOutput = -max(-moveValue, rotateValue)
                rightMotorOutput = moveValue + rotateValue
            else:
                leftMotorOutput = moveValue - rotateValue
                rightMotorOutput = -max(-moveValue, -rotateValue)
        
        self._SetLeftRightMotorOutputs(leftMotorOutput, rightMotorOutput)
        
    def MecanumDrive_Cartesian(self, x, y, rotation, gyroAngle=0.0):
        
        xIn = float(x)
        yIn = float(y)
        # Negate y for the joystick.
        yIn = -yIn;
        # Compenstate for gyro angle.
        xIn, yIn = self._RotateVector(xIn, yIn, gyroAngle);
    
        wheelSpeeds = [None]*self.kMaxNumberOfMotors
        wheelSpeeds[RobotDrive.kFrontLeftMotor] = xIn + yIn + rotation
        wheelSpeeds[RobotDrive.kFrontRightMotor] = -xIn + yIn - rotation
        wheelSpeeds[RobotDrive.kRearLeftMotor] = -xIn + yIn + rotation
        wheelSpeeds[RobotDrive.kRearRightMotor] = xIn + yIn - rotation
    
        self._Normalize(wheelSpeeds)
    
        syncGroup = 0x80
    
        self.lf_motor.Set(wheelSpeeds[RobotDrive.kFrontLeftMotor] * self.inverted[RobotDrive.kFrontLeftMotor] * self.maxOutput, syncGroup)
        self.rf_motor.Set(wheelSpeeds[RobotDrive.kFrontRightMotor] * self.inverted[RobotDrive.kFrontRightMotor] * self.maxOutput, syncGroup)
        self.lr_motor.Set(wheelSpeeds[RobotDrive.kRearLeftMotor] * self.inverted[RobotDrive.kRearLeftMotor] * self.maxOutput, syncGroup)
        self.rr_motor.Set(wheelSpeeds[RobotDrive.kRearRightMotor] * self.inverted[RobotDrive.kRearRightMotor] * self.maxOutput, syncGroup)
        
        
    def MecanumDrive_Polar(self, magnitude, direction, rotation):
        
        # Normalized for full power along the Cartesian axes.
        magnitude = self._Limit(magnitude) * math.sqrt(2.0)
        # The rollers are at 45 degree angles.
        dirInRad = (direction + 45.0) * 3.14159 / 180.0
        cosD = math.cos(dirInRad)
        sinD = math.sin(dirInRad)
    
        wheelSpeeds = [None]*RobotDrive.kMaxNumberOfMotors
        wheelSpeeds[RobotDrive.kFrontLeftMotor] = sinD * magnitude + rotation
        wheelSpeeds[RobotDrive.kFrontRightMotor] = cosD * magnitude - rotation
        wheelSpeeds[RobotDrive.kRearLeftMotor] = cosD * magnitude + rotation
        wheelSpeeds[RobotDrive.kRearRightMotor] = sinD * magnitude - rotation
    
        self._Normalize(wheelSpeeds)
    
        syncGroup = 0x80
    
        self.lf_motor.Set(wheelSpeeds[RobotDrive.kFrontLeftMotor] * self.inverted[RobotDrive.kFrontLeftMotor] * self.maxOutput, syncGroup)
        self.rf_motor.Set(wheelSpeeds[RobotDrive.kFrontRightMotor] * self.inverted[RobotDrive.kFrontRightMotor] * self.maxOutput, syncGroup)
        self.lr_motor.Set(wheelSpeeds[RobotDrive.kRearLeftMotor] * self.inverted[RobotDrive.kRearLeftMotor] * self.maxOutput, syncGroup)
        self.rr_motor.Set(wheelSpeeds[RobotDrive.kRearRightMotor] * self.inverted[RobotDrive.kRearRightMotor] * self.maxOutput, syncGroup)
        
    
    def HolonomicDrive(self, magnitude, direction, rotation):
        return self.MecanumDrive_Polar(magnitude, direction, rotation)
        
    def SetInvertedMotor(self, motorType, isInverted):
        if motorType < 0 or motorType > len(self.inverted):
            raise ValueError("Invalid motor number")
            
        self.inverted[motorType] = -1 if isInverted else 1
        
    def SetSafetyEnabled(self, enabled):
        pass
        
    #
    # WPILib Internal functions
    #
    
    def _Limit(self, num):
        if num > 1.0:
            return 1.0
        elif num < -1.0:
            return -1.0
        return num
    
    def _Normalize(self, wheelSpeeds):
        maxMagnitude = abs(wheelSpeeds[0])
        
        for speed in wheelSpeeds:
            temp = abs(speed)
            if maxMagnitude < temp:
                maxMagnitude = temp
                
        if maxMagnitude > 1.0:
            for i in range(0, len(wheelSpeeds)):
                wheelSpeeds[i] = wheelSpeeds[i] / maxMagnitude
                
    def _RotateVector(self, x, y, angle):
        x = float(x)
        y = float(y)
        angle = float(angle)
        cosA = math.cos(angle * (3.14159 / 180.0))
        sinA = math.sin(angle * (3.14159 / 180.0))
        xOut = x * cosA - y * sinA
        yOut = x * sinA + y * cosA

        return xOut, yOut
        
    def _SetLeftRightMotorOutputs(self, leftOutput, rightOutput):
        if self.lf_motor is not None:
            self.lf_motor.Set(self._Limit(leftOutput) * self.inverted[RobotDrive.kFrontLeftMotor] * self.maxOutput)
        self.lr_motor.Set(self._Limit(leftOutput) * self.inverted[RobotDrive.kRearLeftMotor] * self.maxOutput)
        
        if self.rf_motor is not None:
            self.rf_motor.Set(-self._Limit(rightOutput) * self.inverted[RobotDrive.kFrontRightMotor] * self.maxOutput)
        self.rr_motor.Set(-self._Limit(rightOutput) * self.inverted[RobotDrive.kRearRightMotor] * self.maxOutput)


class Relay(object):
    
    # Value
    kOff = 0
    kOn = 1
    kForward = 2
    kReverse = 3
    
    # Direction
    kBothDirections = 0
    kForwardOnly = 1
    kReverseOnly = 2
    
    def __init__(self, channel, direction=kBothDirections):
        DigitalModule._add_relay( channel, self )
        self.on = False
        self.forward = False
        self.value = Relay.kOff
        
    def Set(self, value):
        
        self.value = value
        
        if value == Relay.kOff or value == Relay.kReverse:
            self.forward = False
            self.on = False
            
        elif value == Relay.kOn or value == Relay.kForward:
            self.forward = True
            self.on = True
            
        else:
            raise RuntimeError( 'Invalid value %s passed to Relay.Set' % str(value) )
            
            
class Servo(object):

    kMaxServoAngle = 170.0
    kMinServoAngle = 0.0

    def __init__(self, channel):
        DigitalModule._add_pwm( channel, self )
        self.value = None
        
    def Get(self):
        return self.value
    
    def GetAngle(self):
        return self.value * self.__GetServoAngleRange() + Servo.kMinServoAngle
    
    def GetMaxAngle(self):
        return Servo.kMaxAngle
        
    def GetMinAngle(self):
        return Servo.kMinAngle
    
    def Set(self, value):
        self.value = value
        
    def SetAngle(self, degrees):
        if degrees < Servo.kMinServoAngle:
            degrees = Servo.kMinServoAngle
        elif degrees > Servo.kMaxServoAngle:
            degrees = Servo.kMaxServoAngle
            
        self.Set( (degrees - Servo.kMinServoAngle) / self.__GetServoAngleRange() )
    
    def __GetServoAngleRange(self):
        return Servo.kMaxServoAngle - Servo.kMinServoAngle
        
        
class Solenoid(object):
    
    def __init__(self, channel):
        self.value = False
        
    def Get(self):
        return self.value
        
    def Set(self, value):
        self.value = value

        
class Ultrasonic(object):

    @staticmethod
    def SetAutomaticMode( mode ):
        pass

    def __init__(self, pingChannel, echoChannel):
        DigitalModule._add_io( pingChannel, self )
        DigitalModule._add_io( echoChannel, self )
        self.distance = 0
        self.enabled = True
        self.range_valid = True
        
    def GetRangeInches(self):
        return self.distance
        
    def GetRangeMM(self):
        return self.GetRangeInches() * 25.4
        
    def IsEnabled(self):
        return self.enabled
        
    def IsRangeValid(self):
        return self.enabled and self.range_valid
        
    def Ping(self):
        pass
        
    def SetEnabled(self, enable):
        self.enabled = enable
    
    
class Victor(SpeedController):
    
    def __init__(self, channel):
        SpeedController.__init__(self)
        DigitalModule._add_pwm( channel, self )
        self.value = 0
        
    def Get(self):
        return self.value
        
    def Set(self, value):
        self.value = value
    
    
class Watchdog(object):
    
    kDefaultWatchdogExpiration = 0.5
    
    @staticmethod
    def _reset():
        if hasattr(Watchdog, '_instance'):
            delattr(Watchdog, '_instance')
    
    @staticmethod
    def GetInstance():
        try:
            return Watchdog._instance
        except AttributeError:
            Watchdog._instance = Watchdog._inner()
            return Watchdog._instance
    
    class _inner:
    
        def __init__(self):
            self.enabled = False
            self.expiration = Watchdog.kDefaultWatchdogExpiration
        
        def Feed(self):
            return self.enabled
        
        def GetEnabled(self):
            return self.enabled
        
        def GetExpiration(self):
            raise self.expiration
            
        def GetTimer(self):
            raise NotImplementedError()
            
        def IsAlive(self):
            return True
            
        def IsSystemActive(self):
            return True
            
        def Kill(self):
            raise NotImplementedError()
            
        def SetEnabled(self, enable):
            self.enabled = bool(enable)
            
        def SetExpiration(self, period):
            self.expiration = float(period)
        
