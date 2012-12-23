import logging
import time
import threading
import sys
from .NetworkTables import NetworkTable
from .core import DriverStation, PIDSource, PIDOutput

class Scheduler:
    @staticmethod
    def GetInstance():
        """Returns the {@link Scheduler}, creating it if one does not exist.
        @return the {@link Scheduler}"""
        try:
            return Scheduler._instance
        except AttributeError:
            Scheduler._instance = Scheduler._inner()
            return Scheduler._instance

    class _inner:
        def __init__(self):
            self.tableLock = threading.RLock()
            self.table = None
            self.subsystems = set()
            self.buttonsLock = threading.RLock()
            self.buttons = []
            self.additionsLock = threading.RLock()
            self.additions = []
            self.commands = []
            self.commandSet = set()
            self.adding = False

        def __del__(self):
            self.additionsLock.acquire()
            self.buttonsLock.acquire()
            self.tableLock.acquire()

        def AddCommand(self, command):
            with self.additionsLock:
                self.additions.append(command)

        def AddButton(self, button):
            with self.buttonsLock:
                self.buttons.append(button)

        def ProcessCommandAddition(self, command):
            if command is None:
                return

            # Check to make sure no adding during adding
            if self.adding:
                logging.error("IncompatibleState: Can not start command from cancel method")
                return

            # Only add if not already in
            if command not in self.commandSet:
                # Check that the requirements can be had
                for lock in command.GetRequirements():
                    if (lock.GetCurrentCommand() is not None and
                            not lock.GetCurrentCommand().IsInterruptible()):
                        return

                # Give it the requirements
                self.adding = True
                for lock in command.GetRequirements():
                    if lock.GetCurrentCommand() is not None:
                        lock.GetCurrentCommand().Cancel()
                        self.Remove(lock.GetCurrentCommand())
                    lock.SetCurrentCommand(command)
                self.adding = False

                self.commands.append(command)
                self.commandSet.add(command)

                command.StartRunning()

        def Run(self):
            """Runs a single iteration of the loop.  This method should be
            called often in order to have a functioning {@link Command} system.
            The loop has five stages:

            <ol>
            <li> Poll the Buttons </li>
            <li> Execute/Remove the Commands </li>
            <li> Send values to SmartDashboard </li>
            <li> Add Commands </li>
            <li> Add Defaults </li>
            </ol>"""
            # Get button input (going backwards preserves button priority)
            with self.buttonsLock:
                for button in reversed(self.buttons):
                    button.Execute()

            # Loop through the commands
            for command in self.commands:
                if not command.Run():
                    self.Remove(command)

            # Send the value over the table
            if self.table is not None:
                with self.tableLock:
                    count = 0
                    self.table.BeginTransaction()
                    for command in self.commands:
                        count += 1
                        self.table[str(count)] = command.GetTable()
                    self.table["count"] = count
                    self.table.EndTransaction()

            # Add the new things
            with self.additionsLock:
                for command in self.additions:
                    self.ProcessCommandAddition(command)
                self.additions.clear()

            # Add in the defaults
            for lock in self.subsystems:
                if lock.GetCurrentCommand() is None:
                    self.ProcessCommandAddition(lock.GetDefaultCommand())
                lock.ConfirmCommand()

        def RegisterSubsystem(self, subsystem):
            """Registers a {@link Subsystem} to this {@link Scheduler}, so
            that the {@link Scheduler} might know if a default {@link Command}
            needs to be run.  All {@link Subsystem Subsystems} should call this.
            @param system the system"""
            if subsystem is None:
                logging.error("NullParameter: subsystem")
                return
            self.subsystems.add(subsystem)

        def Remove(self, command):
            """Removes the {@link Command} from the {@link Scheduler}.
            @param command the command to remove"""
            if command is None:
                logging.error("NullParameter: command")
                return

            if command not in self.commandSet:
                return

            try:
                self.commands.remove(command)
            except ValueError:
                pass
            self.commandSet.remove(command)

            for lock in command.GetRequirements():
                lock.SetCurrentCommand(None)

            command.Removed()

        #
        # SmartDashboardNamedData interface
        #
        def GetName(self):
            return "Scheduler"

        def GetType(self):
            return "Scheduler"

        def GetTable(self):
            if self.table is None:
                self.table = NetworkTable()
                self.table["count"] = 0
            return self.table

class Command:
    """The Command class is at the very core of the entire command framework.
    Every command can be started with a call to {@link Command#Start()}.
    Once a command is started it will call {@link Command#Initialize()}, and
    then will repeatedly call {@link Command#Execute()} until the
    {@link Command#IsFinished()} returns True.  Once it does,
    {@link Command#End()} will be called.

    However, if at any point while it is running {@link Command#Cancel()} is
    called, then the command will be stopped and {@link Command#Interrupted()}
    will be called.

    If a command uses a {@link Subsystem}, then it should specify that it does
    so by calling the {@link Command#Requires()} method in its constructor.
    Note that a Command may have multiple requirements, and
    {@link Command#Requires()} should be called for each one.

    If a command is running and a new command with shared requirements is
    started, then one of two things will happen.  If the active command is
    interruptible, then {@link Command#Cancel()} will be called and the
    command will be removed to make way for the new one.  If the active
    command is not interruptible, the other one will not even be started,
    and the active one will continue functioning.

    @see CommandGroup
    @see Subsystem"""
    kName = "name"
    kRunning = "running"
    kIsParented = "isParented"

    def __init__(self, name=None, timeout=None):
        """Creates a new command with the given name and timeout.
        @param name the name of the command
        @param timeout the time (in seconds) before this command "times out"
        @see Command#isTimedOut()"""
        if timeout is None and not isinstance(name, str):
            timeout = name
            name = None

        # default timeout and name
        if timeout is not None and timeout < 0.0:
            logging.error("ParameterOutOfRange: timeout < 0.0")
        if name is None:
            name = self.__class__.__name__

        self.name = name            # The name of this command
        self.startTime = None       # The time since this command was init'ed
        # The time (in seconds) before this command "times out" (or None if no
        # timeout)
        self.timeout = timeout
        self.initialized = False    # has this command been initialized?
        self.requirements = set()   # The requirements
        self.running = False        # command is running?
        self.interruptible = True   # command is interruptible?
        self.canceled = False       # command has been canceled?
        self.locked = False         # command has been locked?
        # command should run when the robot is disabled?
        self.runWhenDisabled = False
        self.parent = None          # The {@link CommandGroup} this is in
        self.table = None

    def SetTimeout(self, timeout):
        """Sets the timeout of this command.
        @param timeout the timeout (in seconds)
        @see Command#isTimedOut()"""
        if timeout < 0.0:
            logging.error("ParameterOutOfRange: timeout < 0.0")
        else:
            self.timeout = timeout

    def TimeSinceInitialized(self):
        """Returns the time since this command was initialized (in seconds).
        This function will work even if there is no specified timeout.
        @return the time since this command was initialized (in seconds)."""
        if self.startTime is None:
            return 0.0
        else:
            return time.clock() - self.startTime

    def Requires(self, subsystem):
        """This method specifies that the given {@link Subsystem} is used by
        this command.  This method is crucial to the functioning of the
        Command System in general.

        Note that the recommended way to call this method is in the constructor.

        @param subsystem the {@link Subsystem} required
        @see Subsystem"""
        if not self.AssertUnlocked("Can not add new requirement to command"):
            return

        if subsystem is not None:
            self.requirements.add(subsystem)
        else:
            logging.error("NullParameter: subsystem")

    def Removed(self):
        """Called when the command has been removed.
        This will call {@link Command#interrupted()} or
        {@link Command#end()}."""
        if self.initialized:
            if self.IsCanceled():
                self.Interrupted()
                self._Interrupted()
            else:
                self.End()
                self._End()
        self.initialized = False
        self.canceled = False
        self.running = False
        if self.table is not None:
            self.table[kRunning] = False

    def Start(self):
        """Starts up the command.  Gets the command ready to start.
        Note that the command will eventually start, however it will not
        necessarily do so immediately, and may in fact be canceled before
        initialize is even called."""
        self.LockChanges()
        if self.parent is not None:
            logging.error("CommandIllegalUse: Can not start a command that is part of a command group")

        Scheduler.GetInstance().AddCommand(self)

    def Run(self):
        """The run method is used internally to actually run the commands.
        @return whether or not the command should stay within the
        {@link Scheduler}."""
        if (not self.runWhenDisabled and self.parent is None and
                DriverStation.GetInstance().IsDisabled()):
            self.Cancel()

        if self.IsCanceled():
            return False

        if not self.initialized:
            self.initialized = True
            self.StartTiming()
            self._Initialize()
            self.Initialize()
        self._Execute()
        self.Execute()
        return not self.IsFinished()

    def _Initialize(self):
        pass

    def _Interrupted(self):
        pass

    def _Execute(self):
        pass

    def _End(self):
        pass

    def Initialize(self):
        """The initialize method is called the first time this Command is run
        after being started."""
        pass

    def Execute(self):
        """The execute method is called repeatedly until this Command either
        finishes or is canceled."""
        pass

    def IsFinished(self):
        """Returns whether this command is finished.
        If it is, then the command will be removed
        and {@link Command#end() end()} will be called.

        It may be useful for a team to reference the
        {@link Command#isTimedOut()} method for time-sensitive commands.
        @return whether this command is finished.
        @see Command#isTimedOut()"""
        raise NotImplementedError

    def End(self):
        """Called when the command ended peacefully.  This is where you may want
        to wrap up loose ends, like shutting off a motor that was being used
        in the command."""
        pass

    def Interrupted(self):
        """Called when the command ends because somebody called
        {@link Command#cancel()} or another command shared the same
        requirements as this one, and booted it out.

        This is where you may want to wrap up loose ends, like shutting off a
        motor that was being used in the command.

        Generally, it is useful to simply call the {@link Command#end()} method
        within this method."""
        pass

    def StartTiming(self):
        """Called to indicate that the timer should start.
        This is called right before {@link Command#initialize()} is, inside the
        {@link Command#run()} method."""
        self.startTime = time.clock()

    def IsTimedOut(self):
        """Returns whether or not the {@link Command#timeSinceInitialized()}
        method returns a number which is greater than or equal to the timeout
        for the command.
        If there is no timeout, this will always return false.
        @return whether the time has expired"""
        return (self.timeout is not None and
                self.TimeSinceInitialized() >= self.timeout)

    def GetRequirements(self):
        """Returns the requirements (as an std::set of {@link Subsystem}
        pointers) of this command
        @return the requirements (as an set of {@link Subsystem}) of this
        command"""
        return self.requirements

    def LockChanges(self):
        """Prevents further changes from being made"""
        self.locked = True

    def AssertUnlocked(self, message):
        """If changes are locked, then this will generate a CommandIllegalUse
        error.
        @param message the message to report on error (it is appended by a
        default message)
        @return true if assert passed, false if assert failed"""
        if self.locked:
            logging.error("CommandIllegalUse: %s after being started or being added to a command group", message)
            return False
        return True

    def SetParent(self, parent):
        """Sets the parent of this command.  No actual change is made to the
        group.
        @param parent the parent"""
        if parent is None:
            logging.error("NullParameter: parent")
        elif self.parent is not None and self.parent is not parent:
            logging.error("CommandIllegalUse: Can not give command to multiple command groups")
        else:
            self.LockChanges()
            self.parent = parent
            if self.table is not None:
                self.table[kIsParented] = True

    def StartRunning(self):
        """This is used internally to mark that the command has been started.
        The lifecycle of a command is:

        startRunning() is called.
        run() is called (multiple times potentially)
        removed() is called

        It is very important that startRunning and removed be called in order
        or some assumptions of the code will be broken."""
        self.running = True
        self.startTime = None
        if self.table is not None:
            self.table[kRunning] = True

    def IsRunning(self):
        """Returns whether or not the command is running.
        This may return true even if the command has just been canceled, as it
        may not have yet called {@link Command#interrupted()}.
        @return whether or not the command is running"""
        return self.running

    def Cancel(self):
        """This will cancel the current command.
        This will cancel the current command eventually.  It can be called
        multiple times.  And it can be called when the command is not running.
        If the command is running though, then the command will be marked as
        canceled and eventually removed.
        A command can not be canceled if it is a part of a command group, you
        must cancel the command group instead."""
        if self.parent is not None:
            logging.error("CommandIllegalUse: Can not cancel a command that is part of a command group")

        self._Cancel()

    def _Cancel(self):
        """This works like cancel(), except that it doesn't throw an exception
        if it is a part of a command group.  Should only be called by the
        parent command group."""
        if self.IsRunning():
            self.canceled = True

    def IsCanceled(self):
        """Returns whether or not this has been canceled.
        @return whether or not this has been canceled"""
        return self.canceled

    def IsInterruptible(self):
        """Returns whether or not this command can be interrupted.
        @return whether or not this command can be interrupted"""
        return self.interruptible

    def SetInterruptible(self, interruptible):
        """Sets whether or not this command can be interrupted.
        @param interruptible whether or not this command can be interrupted"""
        self.interruptible = interruptible

    def DoesRequire(self, system):
        """Checks if the command requires the given {@link Subsystem}.
        @param system the system
        @return whether or not the subsystem is required (False if given
        None)"""
        return system in self.requirements

    def GetGroup(self):
        """Returns the {@link CommandGroup} that this command is a part of.
        Will return null if this {@link Command} is not in a group.
        @return the {@link CommandGroup} that this command is a part of
        (or None if not in group)"""
        return self.parent

    def SetRunWhenDisabled(self, run):
        """Sets whether or not this {@link Command} should run when the robot
        is disabled.

        By default a command will not run when the robot is disabled, and will
        in fact be canceled.
        @param run whether or not this command should run when the robot is
        disabled"""
        self.runWhenDisabled = run

    def WillRunWhenDisabled(self):
        """Returns whether or not this {@link Command} will run when the robot
        is disabled, or if it will cancel itself.
        @return whether or not this {@link Command} will run when the robot is
        disabled, or if it will cancel itself"""
        return self.runWhenDisabled

    #
    # SmartDashboardNamedData interface
    #
    def GetName(self):
        return self.name

    def GetType(self):
        return "Command"

    def GetTable(self):
        if self.table is None:
            self.table = NetworkTable()
            self.table[self.kName] = self.GetName()
            self.table[self.kRunning] = self.IsRunning()
            self.table[self.kIsParented] = self.parent is not None
            self.table.AddChangeListener(self.kRunning, self)
        return self.table

    #
    # NetworkTableChangeListener interface
    #
    def ValueChanged(self, table, name, type):
        if table.GetBoolean(self.kRunning):
            self.Start()
        else:
            self.Cancel()

    def ValueConfirmed(self, table, name, type):
        pass

class CommandGroupEntry:
    kSequence_InSequence = 1
    kSequence_BranchPeer = 2
    kSequence_BranchChild = 3

    def __init__(self, command=None, state=kSequence_InSequence, timeout=None):
        self.command = command
        self.state = state
        self.timeout = timeout

    def IsTimedOut(self):
        if self.timeout is None:
            return False
        time = self.command.TimeSinceInitialized()
        if time is None or time == 0.0:
            return False
        return time >= self.timeout

class CommandGroup(Command):
    """A {@link CommandGroup} is a list of commands which are executed in
    sequence.

    Commands in a {@link CommandGroup} are added using the
    {@link CommandGroup#AddSequential()} method and are called sequentially.
    {@link CommandGroup CommandGroups} are themselves {@link Command Commands}
    and can be given to other {@link CommandGroup CommandGroups}.

    {@link CommandGroup CommandGroups} will carry all of the requirements of
    their {@link Command subcommands}.  Additional requirements can be
    specified by calling {@link CommandGroup#Requires()} normally in the
    constructor.

    CommandGroups can also execute commands in parallel, simply by adding them
    using {@link CommandGroup#AddParallel()}.

    @see Command
    @see Subsystem"""
    def __init__(self, name=None):
        """Creates a new {@link CommandGroup CommandGroup} with the given name.
        @param name the name for this command group"""
        super().__init__(name=name)
        self.commands = []  # The commands in this group (stored in entries)
        self.children = []  # The active children in this group (in entries)
        self.currentCommandIndex = None # The current command

    def AddSequential(self, command, timeout=None):
        """Adds a new {@link Command Command} to the group with an optional
        timeout.  The {@link Command Command} will be started after all the
        previously added commands.

        Once the {@link Command Command} is started, it will be run until it
        finishes or the time expires, whichever is sooner.  Note that the
        given {@link Command Command} will have no knowledge that it is on a
        timer.

        Note that any requirements the given {@link Command Command} has will
        be added to the group.  For this reason, a {@link Command Command's}
        requirements can not be changed after being added to a group.

        It is recommended that this method be called in the constructor.

        @param command The {@link Command Command} to be added
        @param timeout The timeout (in seconds)"""
        if command is None:
            logging.error("NullParameter: command")
            return
        if not self.AssertUnlocked("Cannot add new command to command group"):
            return
        if timeout is not None and timeout < 0.0:
            logging.error("ParameterOutOfRange: timeout < 0.0")
            return

        command.SetParent(self)

        self.commands.append(CommandGroupEntry(command,
                CommandGroupEntry.kSequence_InSequence, timeout))
        # Iterate through command.GetRequirements() and call Requires() on
        # each required subsystem
        for subsys in command.GetRequirements():
            self.Requires(subsys)

    def AddParallel(self, command, timeout=None):
        """Adds a new child {@link Command} to the group with an optionl
        timeout.  The {@link Command} will be started after all the previously
        added {@link Command Commands}.

        Once the {@link Command Command} is started, it will run until it
        finishes, is interrupted, or the time expires, whichever is sooner.
        Note that the given {@link Command Command} will have no knowledge
        that it is on a timer.

        Instead of waiting for the child to finish, a {@link CommandGroup}
        will have it run at the same time as the subsequent {@link Command
        Commands}.  The child will run until either it finishes, the timeout
        expires, a new child with conflicting requirements is started, or the
        main sequence runs a {@link Command} with conflicting requirements.
        In the latter two cases, the child will be canceled even if it says it
        can't be interrupted.

        Note that any requirements the given {@link Command Command} has will
        be added to the group.  For this reason, a {@link Command Command's}
        requirements can not be changed after being added to a group.

        It is recommended that this method be called in the constructor.

        @param command The command to be added
        @param timeout The timeout (in seconds)"""
        if command is None:
            logging.error("NullParameter: command")
            return
        if not self.AssertUnlocked("Cannot add new command to command group"):
            return
        if timeout is not None and timeout < 0.0:
            logging.error("ParameterOutOfRange: timeout < 0.0")
            return

        command.SetParent(self)

        self.commands.append(CommandGroupEntry(command,
                CommandGroupEntry.kSequence_BranchChild, timeout))
        # Iterate through command.GetRequirements() and call Requires() on
        # each required subsystem
        for subsys in command.GetRequirements():
            self.Requires(subsys)

    def _Initialize(self):
        self.currentCommandIndex = None

    def _Execute(self):
        entry = None
        cmd = None
        firstRun = False

        if self.currentCommandIndex is None:
            firstRun = True
            self.currentCommandIndex = 0

        while self.currentCommandIndex < len(self.commands):
            if cmd is not None:
                if entry.IsTimedOut():
                    cmd._Cancel()

                if cmd.Run():
                    break
                else:
                    cmd.Removed()
                    self.currentCommandIndex += 1
                    firstRun = True
                    cmd = None
                    continue

            entry = self.commands[self.currentCommandIndex]
            cmd = None

            if entry.state == CommandGroupEntry.kSequence_InSequence:
                cmd = entry.command
                if firstRun:
                    cmd.StartRunning()
                    self.CancelConflicts(cmd)
                    firstRun = False
            elif entry.state == CommandGroupEntry.kSequence_BranchPeer:
                self.currentCommandIndex += 1
                entry.command.Start()
            elif entry.state == CommandGroupEntry.kSequence_BranchChild:
                self.currentCommandIndex += 1
                self.CancelConflicts(entry.command)
                entry.command.StartRunning()
                self.children.append(entry)

        # Run Children
        iter = 0
        while iter < len(self.children):
            entry = self.children[iter]
            child = entry.command
            if entry.IsTimedOut():
                child._Cancel()

            if not child.Run():
                child.Removed()
                del self.children[iter]
            else:
                iter += 1

    def _End(self):
        # Theoretically, we don't have to check this, but we do if teams
        # override the IsFinished method
        if (self.currentCommandIndex is not None and
                self.currentCommandIndex < len(self.commands)):
            cmd = self.commands[self.currentCommandIndex].command
            cmd._Cancel()
            cmd.Removed()

        for child in self.children:
            cmd = child.command
            cmd._Cancel()
            cmd.Removed()
        self.children = []

    def _Interrupted(self):
        self._End()

    def _Cancel(self):
        pass

    def IsFinished(self):
        return (self.currentCommandIndex >= len(self.commands) and
                not self.children)

    def IsInterruptible(self):
        if not super().IsInterruptible():
            return False

        if (self.currentCommandIndex is not None and
                self.currentCommandIndex < len(self.commands)):
            cmd = self.commands[self.currentCommandIndex].command
            if not cmd.IsInterruptible():
                return False

        for child in self.children:
            if not child.command.IsInterruptible():
                return False

        return True

    def CancelConflicts(self, command):
        childIter = 0
        while childIter < len(self.children):
            child = self.children[childIter].command
            erased = False

            for reqt in command.GetRequirements():
                if child.DoesRequire(reqt):
                    child._Cancel()
                    child.Removed()
                    del self.children[childIter]
                    erased = True
                    break
            if not erased:
                childIter += 1

    def GetSize(self):
        return len(self.children)

    def __len__(self):
        return len(self.children)

class Subsystem:
    def __init__(self, name):
        """Creates a subsystem with the given name
        @param name the name of the subsystem"""
        self.table = None
        self.currentCommand = None
        self._defaultCommand = None
        self.name = name
        Scheduler.GetInstance().RegisterSubsystem(self)

    def SetDefaultCommand(self, command):
        """Sets the default command.  If this is not called or is called with
        None, then there will be no default command for the subsystem.

        <b>WARNING:</b> This should <b>NOT</b> be called in a constructor if
        the subsystem is a singleton.

        @param command the default command (or null if there should be none)"""
        if command is None:
            self._defaultCommand = None
        else:
            if self not in command.GetRequirements():
                logging.error("CommandIllegalUse: A default command must require the subsystem")
                return

            self._defaultCommand = command

        if self.table is not None:
            if self._defaultCommand is not None:
                self.table["hasDefault"] = True
                self.table["default"] = self._defaultCommand.GetTable()
            else:
                self.table["hasDefault"] = False

    def GetDefaultCommand(self):
        """Returns the default command (or null if there is none).
        @return the default command"""
        return self._defaultCommand

    defaultCommand = property(GetDefaultCommand, SetDefaultCommand)

    def SetCurrentCommand(self, command):
        """Sets the current command
        @param command the new current command"""
        self.currentCommand = command

    def GetCurrentCommand(self):
        """Returns the command which currently claims this subsystem.
        @return the command which currently claims this subsystem"""
        return self.currentCommand

    def ConfirmCommand(self):
        """Call this to alert Subsystem that the current command is actually
        the command.  Sometimes, the {@link Subsystem} is told that it has no
        command while the {@link Scheduler} is going through the loop, only to
        be soon after given a new one.  This will avoid that situation."""
        if self.table is not None:
            if self.currentCommand is not None:
                self.table["hasCommand"] = True
                self.table["command"] = self.currentCommand.GetTable()
            else:
                self.table["hasCommand"] = False

    #
    # SmartDashboardNamedData interface
    #
    def GetName(self):
        return "Subsystem"

    def GetType(self):
        return "Subsystem"

    def GetTable(self):
        if self.table is None:
            self.table = NetworkTable()
            self.table["count"] = 0
        return self.table

class PrintCommand(Command):
    def __init__(self, message):
        super().__init__("Print \"%s\"" % message)
        self.message = message

    def Initialize(self):
        print(self.message)

    def IsFinished(self):
        return True

class StartCommand(Command):
    def __init__(self, commandToStart):
        super().__init__("StartCommand")
        self.commandToFork = commandToStart

    def Initialize(self):
        self.commandToFork.Start()

    def IsFinished(self):
        return True

class WaitCommand(Command):
    def __init__(self, name=None, timeout=None):
        if timeout is None and not isinstance(name, str):
            timeout = name
            name = None

        if name is None:
            name = "Wait(%f)" % timeout

        super().__init__(name, timeout)

    def IsFinished(self):
        return self.IsTimedOut()

class WaitForChildren(Command):
    def __init__(self, name=None, timeout=None):
        if timeout is None and not isinstance(name, str):
            timeout = name
            name = None

        if name is None:
            name = "WaitForChildren"

        super().__init__(name, timeout)

    def IsFinished(self):
        return self.GetGroup() is None or self.GetGroup().GetSize() == 0

class WaitUntilCommand(Command):
    """A {@link WaitCommand} will wait until a certain match time before
    finishing.  This will wait until the game clock reaches some value, then
    continue to the next command.
    @see CommandGroup"""

    def __init__(self, name=None, time=None):
        if timeout is None and not isinstance(name, str):
            time = name
            name = None

        if name is None:
            name = "WaitUntilCommand"

        super().__init__(name, time)
        self.time = time

    def IsFinished(self):
        """Check if we've reached the actual finish time."""
        return DriverStation.GetInstance().GetMatchTime() >= self.time

class PIDCommand(Command, PIDOutput, PIDSource):
    def __init__(self, *args, **kwargs):
        name = kwargs.get("name")
        p = kwargs.get("p")
        i = kwargs.get("i")
        d = kwargs.get("d")
        period = kwargs.get("period")
        if name is None and args and isinstance(args[0], str):
            name = args.pop(0)
        if len(args) > 0:
            p = args.pop(0)
            i = args.pop(0)
            d = args.pop(0)
        if period is None and args:
            period = args.pop(0)

        Command.__init__(self, name)
        PIDOutput.__init__(self)
        PIDSource.__init__(self)

        self.max = sys.float_info.max   # The max setpoint value
        self.min = sys.float_info.min   # The min setpoint value
        # The internal PIDController
        from SmartDashboard import SendablePIDController
        self.controller = SendablePIDController(p, i, d, self, self, period)

    def _Initialize(self):
        self.controller.Enable()

    def _End(self):
        self.controller.Disable()

    def _Interrupted(self):
        self._End()

    def SetSetpointRelative(self, deltaSetpoint):
        self.SetSetpoint(self.GetSetpoint() + deltaSetpoint)

    #
    # PIDOutput interface
    #
    def PIDWrite(self, output):
        self.UsePIDOutput(output)

    #
    # PIDSource interface
    #
    def PIDGet(self):
        return self.ReturnPIDInput()

    def GetPIDController(self):
        return self.controller

    def SetSetpoint(self, setpoint):
        self.controller.SetSetpoint(setpoint)

    def GetSetpoint(self):
        return self.controller.GetSetpoint()

    def GetPosition(self):
        return self.ReturnPIDInput()

    def SetSetpointRange(self, a, b):
        if a <= b:
            self.min = a
            self.max = b
        else:
            self.min = b
            self.max = a

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "PIDCommand"

    def GetControllerTable(self):
        return self.controller.GetTable()

class PIDSubsystem(Subsystem, PIDOutput, PIDSource):
    def __init__(self, *args, **kwargs):
        name = kwargs.get("name")
        p = kwargs.get("p")
        i = kwargs.get("i")
        d = kwargs.get("d")
        period = kwargs.get("period")
        if name is None and args and isinstance(args[0], str):
            name = args.pop(0)
        if len(args) > 0:
            p = args.pop(0)
            i = args.pop(0)
            d = args.pop(0)
        if period is None and args:
            period = args.pop(0)

        Subsystem.__init__(self, name)
        PIDOutput.__init__(self)
        PIDSource.__init__(self)

        self.max = sys.float_info.max   # The max setpoint value
        self.min = sys.float_info.min   # The min setpoint value
        # The internal PIDController
        from SmartDashboard import SendablePIDController
        self.controller = SendablePIDController(p, i, d, self, self, period)

    def Enable(self):
        self.controller.Enable()

    def Disable(self):
        self.controller.Disable()

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "PIDSubsystem"

    def GetControllerTable(self):
        return self.controller.GetTable()

    def GetPIDController(self):
        return self.controller

    def SetSetpoint(self, setpoint):
        self.controller.SetSetpoint(setpoint)

    def SetSetpointRelative(self, deltaSetpoint):
        self.SetSetpoint(self.GetSetpoint() + deltaSetpoint)

    def GetSetpoint(self):
        return self.controller.GetSetpoint()

    def GetPosition(self):
        return self.ReturnPIDInput()

    def SetSetpointRange(self, a, b):
        if a <= b:
            self.min = a
            self.max = b
        else:
            self.min = b
            self.max = a

    def PIDWrite(self, output):
        self.UsePIDOutput(output)

    def PIDGet(self):
        return self.ReturnPIDInput()

    def ReturnPIDInput(self):
        raise NotImplementedError

    def UsePIDOutput(self, output):
        raise NotImplementedError
