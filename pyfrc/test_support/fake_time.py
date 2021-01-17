import threading
import weakref


class TestRanTooLong(BaseException):
    """
    This is thrown when the time limit has expired

    This exception inherits from BaseException, so if you want to catch
    it you must explicitly specify it, as a blanket except statement
    will not catch this exception.'

    Generally, only internal pyfrc code needs to catch this
    """

    pass


class TestEnded(BaseException):
    """
    This is thrown when the controller has been signaled to end the test

    This exception inherits from BaseException, so if you want to catch
    it you must explicitly specify it, as a blanket except statement
    will not catch this exception.'

    Generally, only internal pyfrc code needs to catch this
    """

    pass


class TestFroze(BaseException):
    """
    This happens when an infinite loop of some kind in one of your
    non-robot threads is detected.
    """

    pass


class FakeTime:
    """
    Keeps track of time for robot code being tested, and makes sure the
    DriverStation is notified that new packets are coming in.

    .. note:: Do not create this object, your testing code can use this
              object to control time via the ``fake_time`` fixture
    """

    def __init__(self):
        # Note: when iterating this list, make copies or you'll run into errors
        self._child_threads = weakref.WeakKeyDictionary()
        self._children_free_run = False
        self._children_not_running = threading.Event()
        self._freeze_detect_threshold = 250
        self.lock = threading.RLock()

    def initialize(self):
        """
        Initializes fake time
        """

        self.reset()

        # Setup driver station hooks
        import wpilib

        assert not hasattr(wpilib.DriverStation, "instance"), (
            "You must not initialize the driver station before your robot "
            + "code executes. Perhaps you have a global somewhere? Globals are "
            + "generally evil and should be avoided!"
        )

        # The DS thread causes too many problems, disable it by getting
        # rid of the thread function
        wpilib.DriverStation._run = lambda _: None

        self._ds = wpilib.DriverStation.getInstance()

        # This is used to make DriverStation.waitForData() work
        self.ds_cond = _DSCondition(self)
        self._ds.waitForDataCond = self.ds_cond

        self.thread_id = threading.current_thread().ident
        return self.ds_cond

    def __time_test__(self):
        if self.time_limit is not None and self.time_limit <= self.time:
            raise TestRanTooLong()

    def _wake_children(self, timestep):
        # Subtract the timestep from the last requested times of the threads.
        # Wake them up if the requested time is in the past, and they haven't
        # already been stopped.
        waiting_on = []
        with self.lock:
            child_threads = list(self._child_threads.items())
        for thread, thread_info in child_threads:
            thread_info["time"] -= timestep
            if thread_info["time"] <= 0 and thread.is_alive():
                self._children_not_running.clear()
                thread_info["event"].set()  # Wake it up
                waiting_on.append(thread)

        # Wait for everything we woke up to sleep again.
        # Check that we did wake something up.
        if waiting_on:
            i = 0
            while not self._children_not_running.wait(0.020):
                i += 1
                if i == self._freeze_detect_threshold:
                    raise TestFroze("Waiting on %s" % waiting_on)

                # if this timed out, check to see if that particular
                # child died...
                for thread in waiting_on:
                    if thread.is_alive():
                        break  # out of the for loop, at least one child is active
                else:
                    break  # out of the while loop, everyone is dead

    def children_stopped(self):
        with self.lock:
            keys = list(self._child_threads.keys())
        for thread in keys:
            if thread.is_alive():
                return False
        return True

    def teardown(self):
        self._children_free_run = True  # Stop any threads being blocked
        self._children_not_running.set()  # Main thread needs to be running
        with self.lock:
            thread_infos = list(self._child_threads.values())
        for thread_info in thread_infos:
            thread_info["event"].set()

    def reset(self):
        """
        Resets the fake time to zero, and sets the time limit to default
        """
        self.time = 0
        self.time_limit = 500
        self.in_increment = False

        # Drop references to any child threads
        self._child_threads = weakref.WeakKeyDictionary()
        self._children_not_running.set()
        self._children_free_run = False

        self.next_ds_time = 0.020

    def get(self):
        """
        :returns: The current time for the robot
        """
        return self.time

    def increment_time_by(self, time):
        """
        Increments time by some number of seconds

        :param time: Number of seconds to increment time by
        :type time: float
        """
        # If it is a thread calling us, we intercept the call and insert
        # a blocking call to a threading.Event.wait() to force it to sleep
        # in the "real world", otherwise it keeps looping indeterminately.
        # Store the requested time, and at each DS step wake up those that
        # should have fired in the previous timestep.
        current_thread = threading.current_thread()
        if current_thread.ident != self.thread_id:
            with self.lock:
                child_info = self._child_threads.get(current_thread)
                if child_info is None:
                    child_info = {"event": threading.Event(), "time": time}
                    self._child_threads[current_thread] = child_info

            if time > 0 and not self._children_free_run:
                # Daughter thread needs to fire in the next DS time step,
                # so make it wait
                child_info["event"].clear()
                child_info["time"] = time
                # Check to see if the other threads have finished
                running = False
                with self.lock:
                    child_threads = list(self._child_threads.values())
                for v in child_threads:
                    if v["event"].is_set():
                        running = True
                if not running:
                    self._children_not_running.set()
                child_info["event"].wait()
            # We don't need to do anything else for children
            return

        if time < 0:
            time = 0

        with self.lock:
            if self.in_increment:
                raise ValueError(
                    "increment_time_by is not reentrant (did you call timer.delay?)"
                )

            next_ds = self.next_ds_time - self.time

        # When we wake up the TimerTasks, we can't do it while we have the lock
        # because some tasks need to get the time themselves
        # eg feeding motor watchdogs

        # This is terrible, but it works
        while time > 0:

            # Short wait, just get it done and exit
            if time < next_ds:
                with self.lock:
                    self.time += time
                    self.__time_test__()
                self._wake_children(time)
                break

            with self.lock:
                self.time += next_ds

                if current_thread.ident == self.thread_id:
                    self.ds_cond.on_step(self.time)

                # TODO: document this

                with self.ds_cond:
                    self.ds_cond.notify_all()
                    self._ds._getData()

                time -= next_ds

                next_ds = 0.020
                self.next_ds_time += next_ds

                self.__time_test__()
            self._wake_children(next_ds)

    def increment_new_packet(self):
        """
        Increment time enough to where the new DriverStation packet
        comes in
        """
        with self.lock:
            next_ds_time = self.next_ds_time
            time = self.time

        self.increment_time_by(next_ds_time - time)

    def set_time_limit(self, time_limit):
        """
        Sets the amount of time that a robot will run. When time is
        incremented past this time, a TestRanTooLong is thrown.

        The default time limit is 500 seconds

        :param time_limit: Number of seconds
        :type time_limit: float
        """
        self.time_limit = time_limit

    def _ds_time_offset(self):
        with self.lock:
            return self.next_ds_time - self.time


class _DSCondition(threading.Condition):
    """
    Condition variable replacement to allow fake time to be used to hook
    into the DriverStation packets.
    """

    def __init__(self, fake_time_inst, lock=None):
        super().__init__(lock)

        self.thread_id = threading.current_thread().ident
        self.fake_time_inst = fake_time_inst
        self._on_step = lambda tm: True

    def on_step(self, tm):

        retval = self._on_step(tm)
        if not retval:
            raise TestEnded()

    def wait(self, timeout=None):

        in_main = threading.current_thread().ident == self.thread_id

        # easy case: infinite timeout
        if timeout is None:

            # If on main thread, increment until the next packet time
            if in_main:
                self.fake_time_inst.increment_new_packet()
            else:
                # Not on main thread? wait for notify
                # -> TODO: this could never return if a notify doesn't occur
                super().wait()

            return True

        else:
            # harder case: some timeout
            # -> because this is the DS condition variable, we know when it will
            #    be notified. Determine if that time is before or after the next
            #    ds time
            ds_offset = self.fake_time_inst._ds_time_offset()

            # either way, increment by the time difference
            self.fake_time_inst.increment_time_by(ds_offset)

            # if before, return False indicating timeout
            # if after, return True indicating successful notification
            return timeout > ds_offset

        if timeout is not None:
            raise NotImplementedError("Didn't implement timeout support yet")

        # If we're on the robot's main thread, when this is called we just
        # need to increment the time, no wait required. If we're not on the
        # main thread, then we need to wait for a notification..

    # Copied from Python 3.6 source code, Python license
    # -> have to fork it because need to use our own time definition
    def wait_for(self, predicate, timeout=None):
        """Wait until a condition evaluates to True.

        predicate should be a callable which result will be interpreted as a
        boolean value.  A timeout may be provided giving the maximum time to
        wait.

        """
        endtime = None
        waittime = timeout
        result = predicate()
        while not result:
            if waittime is not None:
                if endtime is None:
                    endtime = self.fake_time_inst.get() + waittime
                else:
                    waittime = endtime - self.fake_time_inst.get()
                    if waittime <= 0:
                        break
            self.wait(waittime)
            result = predicate()
        return result
