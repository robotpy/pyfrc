import logging
from .NetworkTables import NetworkTable
import time
from .core import PIDController, Gyro

class SmartDashboardData:
    def GetType(self):
        raise NotImplementedError
    def GetTable(self):
        raise NotImplementedError

class SmartDashboardNamedData(SmartDashboardData):
    def GetName(self):
        raise NotImplementedError

class SmartDashboard:
    """The {@link SmartDashboard} class is the bridge between robot programs
    and the SmartDashboard on the laptop.

    When a value is put into the SmartDashboard here, it pops up on the
    SmartDashboard on the laptop.  Users can put values into and get values
    from the SmartDashboard."""
    @staticmethod
    def GetInstance():
        try:
            return SmartDashboard._instance
        except AttributeError:
            SmartDashboard._instance = SmartDashboard._inner()
            return SmartDashboard._instance

    class _inner:
        def __init__(self):
            self.table = NetworkTable.GetTable("SmartDashboard")
            self.tablesToData = {}

        def __setitem__(self, keyName, value):
            if hasattr(value, "GetType") and hasattr(value, "GetTable"):
                # Assumed to be SmartDashboardData
                self.PutData(keyName, value)
            else:
                self.table[keyName] = value

        def __getitem__(self, keyName):
            v = self.table[keyName]
            if isinstance(v, NetworkTable):
                data = self.tablesToData.get(v)
                if data is None:
                    logging.error("SmartDashboardMissingKey: %s", keyName)
                return data
            else:
                return v

        def PutData(self, keyName=None, value=None):
            """Maps the specified key to the specified value in this table.
            The key can not be None.
            The value can be retrieved by calling the get method with a key
            that is equal to the original key.
            @param keyName the key
            @param value the value"""
            if keyName is None and hasattr(value, "GetName"):
                keyName = value.GetName()
            if keyName is None:
                logging.error("NullParameter: keyName")
                return
            if value is None:
                logging.error("NullParameter: value")
                return
            t = NetworkTable()
            t.PutString("~TYPE~", value.GetType())
            t.PutSubTable("Data", value.GetTable())
            self.table[keyName] = t
            self.tablesToData[t] = value

        def GetData(self, keyName):
            """Returns the value at the specified key.
            @param keyName the key
            @return the value"""
            if keyName is None:
                logging.error("NullParameter: keyName")
                return None
            subtable = self.table.GetSubTable(keyName)
            data = self.tablesToData.get(subtable)
            if data is None:
                logging.error("SmartDashboardMissingKey: %s", keyName)
            return data

        def PutBoolean(self, keyName, value):
            """Maps the specified key to the specified value in this table.
            The key can not be NULL.
            The value can be retrieved by calling the get method with a key
            that is equal to the original key.
            @param keyName the key
            @param value the value"""
            self.table.PutBoolean(keyName, value)

        def GetBoolean(self, keyName):
            """Returns the value at the specified key.
            @param keyName the key
            @return the value"""
            return self.table.GetBoolean(keyName)

        def PutInt(self, keyName, value):
            """Maps the specified key to the specified value in this table.
            The keyName can not be None.
            The value can be retrieved by calling the get method with a key
            that is equal to the original key.
            @param keyName the key
            @param value the value"""
            self.table.PutInt(keyName, value)

        def GetInt(self, keyName):
            """Returns the value at the specified key.
            @param keyName the key
            @return the value"""
            return self.table.GetInt(keyName)

        def PutDouble(self, keyName, value):
            """Maps the specified key to the specified value in this table.
            The key can not be None.
            The value can be retrieved by calling the get method with a key
            that is equal to the original key.
            @param keyName the key
            @param value the value"""
            self.table.PutDouble(keyName, value)

        def GetDouble(self, keyName):
            """Returns the value at the specified key.
            @param keyName the key
            @return the value"""
            return self.table.GetDouble(keyName)

        def PutString(self, keyName, value):
            """Maps the specified key to the specified value in this table.
            Neither the key nor the value can be None.
            The value can be retrieved by calling the get method with a key
            that is equal to the original key.
            @param keyName the key
            @param value the value"""
            self.table.PutString(keyName, value)

        def GetString(self, keyName):
            """Returns the value at the specified key.
            @param keyName the key
            @return the value"""
            return self.table.GetString(keyName)

class SendablePIDController(PIDController):
    """A {@link SendablePIDController} is a {@link PIDController} that can be
    sent over to the {@link SmartDashboard} using the
    {@link SmartDashboard#PutData()} method.

    It is useful if you want to test values of a {@link PIDController} without
    having to recompile code between tests.
    Also, consider using {@link Preferences} to save the important values
    between matches.

    @see SmartDashboard"""
    kP = "p"
    kI = "i"
    kD = "d"
    kSetpoint = "setpoint"
    kEnabled = "enabled"

    def __init__(self, p, i, d, source, output, period=0.05):
        """Allocate a PID object with the given constants for P, I, D.
        @param p the proportional coefficient
        @param i the integral coefficient
        @param d the derivative coefficient
        @param source The PIDSource object that is used to get values
        @param output The PIDOutput object that is set to the output value
        @param period the loop time for doing calculations in seconds. This
        particularly effects calculations of the integral and differential
        terms.  The default is 50ms."""
        super().__init__(p, i, d, source, output, period)
        self.table = None

    def SetSetpoint(self, setpoint):
        """Set the setpoint for the PIDController
        @param setpoint the desired setpoint"""
        super().SetSetpoint(setpoint)

        if self.table is not None:
            self.table[self.kSetpoint] = float(setpoint)

    def SetPID(self, p, i, d):
        """Set the PID Controller gain parameters.
        Set the proportional, integral, and differential coefficients.
        @param p Proportional coefficient
        @param i Integral coefficient
        @param d Differential coefficient"""
        super().SetPID(p, i, d)

        if self.table is not None:
            self.table[self.kP] = float(p)
            self.table[self.kI] = float(i)
            self.table[self.kD] = float(d)

    def Enable(self):
        """Begin running the PIDController"""
        super().Enable()

        if self.table is not None:
            self.table[self.kEnabled] = True

    def Disable(self):
        """Stop running the PIDController, this sets the output to zero before
        stopping."""
        super().Disable()

        if self.table is not None:
            self.table[self.kEnabled] = False

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "PIDController"

    def GetTable(self):
        if self.table is None:
            self.table = NetworkTable()

            self.table[self.kP] = self.GetP()
            self.table[self.kI] = self.GetI()
            self.table[self.kD] = self.GetD()
            self.table[self.kSetpoint] = self.GetSetpoint()
            self.table[self.kEnabled] = self.IsEnabled()

            self.table.AddChangeListenerAny(self)
        return self.table

    #
    # NetworkTableChangeListener interface
    #
    def ValueChanged(self, table, name, type):
        if name == self.kP or name == self.kI or name == self.kD:
            super().SetPID(table.GetDouble(self.kP), table.GetDouble(self.kI),
                    table.GetDouble(self.kD))
        elif name == self.kSetpoint:
            super().SetSetpoint(table.GetDouble(self.kSetpoint))
        elif name == self.kEnabled:
            if table.GetBoolean(self.kEnabled):
                super().Enable()
            else:
                super().Disable()

    def ValueConfirmed(self, table, name, type):
        pass

class SendableGyro(Gyro):
    """The {@link SendableGyro} class behaves exactly the same as a
    {@link Gyro} except that it also implements {@link SmartDashboardData} so
    that it can be sent over to the {@link SmartDashboard}."""
    # The time (in seconds) between updates to the table
    kDefaultTimeBetweenUpdates = 0.2
    kAngle = "angle"

    def __init__(self, *args):
        super().__init__(*args)
        self.offset = 0.0
        self.period = self.kDefaultTimeBetweenUpdates
        self.table = None
        self.publisher = threading.Thread("SendableGyroPublisher",
                self._PublishTaskRun)
        self.runPublisher = False

    def __del__(self):
        if self.table is not None:
            # Stop the task
            self.runPublisher = False
            self.publisher.join()

    def GetAngle(self):
        return self.offset + super().GetAngle()

    def Reset(self):
        self.offset = 0.0
        super().Reset()

    def SetUpdatePeriod(self, period):
        """Sets the time (in seconds) between updates to the
        {@link SmartDashboard}.  The default is 0.2 seconds.
        @param period the new time between updates"""
        if period <= 0.0:
            logging.error("ParameterOutOfRange: period <= 0.0")
        else:
            self.period = period

    def GetUpdatePeriod(self):
        """Returns the period (in seconds) between updates to the
        {@link SmartDashboard}.  This value is independent of whether or not
        this {@link SendableGyro} is connected to the {@link SmartDashboard}.
        The default value is 0.2 seconds.
        @return the period (in seconds)"""
        return self.period

    def ResetToAngle(self, angle):
        """Reset the gyro.
        Resets the gyro to the given heading. This can be used if there is
        significant drift in the gyro and it needs to be recalibrated after
        it has been running.
        @param angle the angle the gyro should believe it is pointing"""
        self.offset = angle
        super().Reset()

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "Gyro"

    def GetTable(self):
        if self.table is None:
            self.table = NetworkTable()
            self.table[self.kAngle] = int(GetAngle())
            self.table.AddChangeListener(self.kAngle, self)
            self.publisher.start()
        return self.table

    #
    # NetworkTableChangeListener interface
    #
    def ValueChanged(self, table, name, type):
        # Update value from smart dashboard
        self.ResetToAngle(self.table.GetDouble(name))

    def ValueConfirmed(self, table, name, type):
        pass

    def _PublishTaskRun(self):
        self.runPublisher = True
        while self.runPublisher:
            self.table[self.kAngle] = int(GetAngle())
            time.sleep(self.period)

class SendableChooser:
    """The {@link SendableChooser} class is a useful tool for presenting a
    selection of options to the {@link SmartDashboard}.

    For instance, you may wish to be able to select between multiple
    autonomous modes.  You can do this by putting every possible
    {@link Command} you want to run as an autonomous into a
    {@link SendableChooser} and then put it into the {@link SmartDashboard}
    to have a list of options appear on the laptop.  Once autonomous starts,
    simply ask the {@link SendableChooser} what the selected value is.

    @see SmartDashboard"""
    kDefault = "default"
    kCount = "count"
    kSelected = "selected"

    def __init__(self):
        self.defaultChoice = None
        self.choices = {}   # map from names to objects
        self.ids = {}       # map from objects to ids
        self.table = NetworkTable()
        self.count = 0

    def AddObject(self, name, obj):
        """Adds the given object to the list of options.  On the
        {@link SmartDashboard} on the desktop, the object will appear as the
        given name.
        @param name the name of the option
        @param object the option"""
        if name in self.choices:
            id = self.ids[self.choices[name]]
        else:
            id = str(self.count)
            self.count += 1
            self.ids[obj] = id
            self.table[self.kCount] = self.count
        self.choices[name] = obj
        self.table[id] = str(name)

    def AddDefault(self, name, obj):
        """Add the given object to the list of options and marks it as the
        default.  Functionally, this is very close to
        {@link SendableChooser#AddObject()} except that it will use this as
        the default option if none other is explicitly selected.
        @param name the name of the option
        @param object the option"""
        self.defaultChoice = obj
        self.AddObject(name, obj)
        self.table[self.kDefault] = str(name)

    def GetSelected(self):
        """Returns the selected option.  If there is none selected, it will
        return the default.  If there is none selected and no default, then
        it will return {@code None}.
        @return the option selected"""
        if self.kSelected in self.table:
            return self.choices[self.table[self.kSelected]]
        else:
            return self.defaultChoice

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "String Chooser"

    def GetTable(self):
        return self.table
