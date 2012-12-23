import threading
import logging
from .NetworkTables import NetworkTable

__all__ = ["Preferences"]

class Preferences:
    """The preferences class provides a relatively simple way to save important
    values to the cRIO to access the next time the cRIO is booted.

    This class loads and saves from a file inside the cRIO.  The user can not
    access the file directly, but may modify values at specific fields which
    will then be saved to the file when {@link Preferences#Save() Save()} is
    called.

    This class is thread safe.

    This will also interact with {@link NetworkTable} by creating a table
    called "Preferences" with all the key-value pairs.  To save using
    {@link NetworkTable}, simply set the boolean at position "~S A V E~" to
    True.  Also, if the value of any variable is " in the {@link NetworkTable},
    then that represents non-existence in the {@link Preferences} table"""
    # The Preferences table name
    kTableName = "Preferences"
    # The value of the save field
    kSaveField = "~S A V E~"
    # The file to save to
    kFileName = "/c/wpilib-preferences.ini"
    # The characters to put between a field and value
    kValuePrefix = "=\""
    # The characters to put after the value
    kValueSuffix = "\""

    @staticmethod
    def GetInstance():
        """Get the one and only {@link Preferences} object
        @return The {@link Preferences}"""
        try:
            return Preferences._instance
        except AttributeError:
            Preferences._instance = Preferences._inner()
            return Preferences._instance

    class _inner:
        def __init__(self):
            # The semaphore for accessing the file
            self.fileLock = threading.RLock()
            # The semaphore for beginning reads and writes to the file
            self.fileOpStarted = threading.Event()
            # The semaphore for reading from the table
            self.tableLock = threading.RLock()
            # The actual values (String->String)
            self.values = {}
            # The keys in the order they were read from the file
            self.keylist = []
            # The comments that were in the file sorted by which key they
            # appeared over (String->Comment)
            self.comments = {}
            # The comment at the end of the file
            self.endComment = ""
            # Whether any settings have been changed
            self.changed = False

            readTask = threading.Thread(name="PreferencesReadTask",
                    target=self.ReadTaskRun)
            readTask.start()
            self.fileOpStarted.wait()

            table = NetworkTable.GetTable(Preferences.kTableName)
            table[Preferences.kSaveField] = False
            table.AddChangeListenerAny(self)

        def __del__(self):
            self.tableLock.acquire()
            self.fileLock.acquire()

        def GetKeys(self):
            """Returns a vector of all the keys
            @return a vector of the keys"""
            return self.keylist

        def keys(self):
            return self.keylist

        def GetString(self, key, default=""):
            """Returns the string at the given key.  If this table does not
            have a value for that position, then the given default will be
            returned.
            @param key the key
            @param default the value to return if none exists in the table
            @return either the value in the table, or the default"""
            value = self.Get(key)
            return default if value is None else value

        def GetInt(self, key, default=0):
            """Returns the int at the given key.  If this table does not have
            a value for that position, then the given default value will be
            returned.
            @param key the key
            @param default the value to return if none exists in the table
            @return either the value in the table, or the default"""
            value = self.Get(key)
            if value is None:
                return default

            return int(value)

        def GetDouble(self, key, default=0.0):
            """Returns the double at the given key.  If this table does not
            have a value for that position, then the given default value will
            be returned.
            @param key the key
            @param default the value to return if none exists in the table
            @return either the value in the table, or the default"""
            value = self.Get(key)
            if value is None:
                return default

            return float(value)

        def GetFloat(self, key, default=0.0):
            """Returns the float at the given key.  If this table does not
            have a value for that position, then the given default value will
            be returned.
            @param key the key
            @param default the value to return if none exists in the table
            @return either the value in the table, or the default"""
            value = self.Get(key)
            if value is None:
                return default

            return float(value)

        def GetBoolean(self, key, default=False):
            """Returns the boolean at the given key.  If this table does not
            have a value for that position, then the given default value will
            be returned.
            @param key the key
            @param default the value to return if none exists in the table
            @return either the value in the table, or the default"""
            value = self.Get(key)
            if value is None:
                return default

            if value in ("True", "true", "yes", "on", "1"):
                return True
            elif value in ("False", "false", "no", "off", "0"):
                return False

            logging.error("ParameterOutOfRange: invalid Boolean value \"%s\"",
                    value)
            return False

        def GetLong(self, key, default=0):
            """Returns the long (INT64) at the given key.  If this table does
            not have a value for that position, then the given default value
            will be returned.
            @param key the key
            @param default the value to return if none exists in the table
            @return either the value in the table, or the default"""
            return self.GetInt(key, default)

        def PutString(self, key, value):
            """Puts the given string into the preferences table.

            The value may not have quotation marks, nor may the key
            have any whitespace nor an equals sign

            This will <b>NOT</b> save the value to memory between power cycles,
            to do that you must call {@link Preferences#Save() Save()} (which
            must be used with care).
            at some point after calling this.
            @param key the key
            @param value the value"""
            if value is None:
                logging.error("NullParameter: value")
                return
            if '"' in value:
                logging.error("ParameterOutOfRange: value contains illegal characters")
                return
            self.Put(key, value)

        def PutInt(self, key, value):
            """Puts the given int into the preferences table.

            The key may not have any whitespace nor an equals sign

            This will <b>NOT</b> save the value to memory between power cycles,
            to do that you must call {@link Preferences#Save() Save()} (which
            must be used with care)
            at some point after calling this.
            @param key the key
            @param value the value"""
            self.Put(key, str(value))

        def PutDouble(self, key, value):
            """Puts the given double into the preferences table.

            The key may not have any whitespace nor an equals sign

            This will <b>NOT</b> save the value to memory between power cycles,
            to do that you must call {@link Preferences#Save() Save()} (which
            must be used with care)
            at some point after calling this.
            @param key the key
            @param value the value"""
            self.Put(key, str(value))

        def PutFloat(self, key, value):
            """Puts the given float into the preferences table.

            The key may not have any whitespace nor an equals sign

            This will <b>NOT</b> save the value to memory between power cycles,
            to do that you must call {@link Preferences#Save() Save()} (which
            must be used with care)
            at some point after calling this.
            @param key the key
            @param value the value"""
            self.Put(key, str(value))

        def PutBoolean(self, key, value):
            """Puts the given boolean into the preferences table.

            The key may not have any whitespace nor an equals sign

            This will <b>NOT</b> save the value to memory between power cycles,
            to do that you must call {@link Preferences#Save() Save()} (which must be used with care)
            at some point after calling this.
            @param key the key
            @param value the value"""
            self.Put(key, "true" if value else "false")

        def PutLong(self, key, value):
            """Puts the given long (INT64) into the preferences table.

            The key may not have any whitespace nor an equals sign

            This will <b>NOT</b> save the value to memory between power cycles,
            to do that you must call {@link Preferences#Save() Save()} (which
            must be used with care)
            at some point after calling this.</p>
            @param key the key
            @param value the value"""
            self.Put(key, str(value))

        def Save(self):
            """Saves the preferences to a file on the cRIO.

            This should <b>NOT</b> be called often.
            Too many writes can damage the cRIO's flash memory.
            While it is ok to save once or twice a match, this should never
            be called every run of {@link IterativeRobot#TeleopPeriodic()}, etc.

            The actual writing of the file is done in a separate thread.
            However, any call to a get or put method will wait until the table
            is fully saved before continuing."""
            if not self.changed:
                return
            with self.fileLock:
                self.fileOpStarted.clear()
                writeTask = threading.Thread(name="PreferencesWriteTask",
                        target=self.WriteTaskRun)
                writeTask.start()
                self.fileOpStarted.wait()

        def ContainsKey(self, key):
            """Returns whether or not there is a key with the given name.
            @param key the key
            @return if there is a value at the given key"""
            with self.tableLock:
                return key in self.values

        def __contains__(self, key):
            return self.ContainsKey(key)

        def Remove(self, key):
            """Remove a preference
            @param key the key"""
            with self.tableLock:
                if key in self.values:
                    del self.values[key]
                    self.keylist.remove(key)
                self.changed = True

        def __delitem__(self, key):
            with self.tableLock:
                del self.values[key]
                self.keylist.remove(key)
                self.changed = True

        def Get(self, key, default=None):
            """Returns the value at the given key.
            @param key the key
            @return the value (or empty if none exists)"""
            if key is None:
                logging.error("NullParameter: key")
                return None
            with self.tableLock:
                return self.values.get(key, default)

        def get(self, key, default=None):
            return self.Get(key, default)

        def __getitem__(self, key):
            with self.tableLock:
                return self.values[key]

        def Put(self, key, value):
            """Puts the given value into the given key position
            @param key the key
            @param value the value"""
            if key is None:
                logging.error("NullParameter: key")
                return

            for p in "=\n\r \t\"":
                if p in key:
                    logging.error("ParameterOutOfRange: key contains illegal characters")
                    return

            with self.tableLock:
                if key not in self.values:
                    self.keylist.append(key)
                self.values[key] = str(value)
                self.changed = True

            table = NetworkTable.GetTable(Preferences.kTableName)
            table[key] = value

        def __setitem__(self, key, value):
            self.Put(key, value)

        def ReadTaskRun(self):
            """The internal method to read from a file.
            This will be called in its own thread when the preferences
            singleton is first created."""
            with self.tableLock:
                self.fileOpStarted.set()

                comment = ""
                try:
                    with open(Preferences.kFileName) as f:
                        in_section = False
                        in_value = False
                        value_done = False

                        for line in f:
                            line = line.strip()

                            if not line:
                                comment += '\n'
                            elif line[0] == ';':
                                comment += line
                                comment += '\n'
                            elif line[0] == '[':
                                # throw it away
                                if ']' not in line:
                                    in_section = True
                            elif in_section:
                                # in multi-line section header
                                if ']' in line:
                                    in_section = False
                            elif in_value:
                                # in multi-line value
                                l, sep, r = line.partition('"')
                                value += l
                                if sep:
                                    in_value = False
                                    value_done = True
                            else:
                                name, equal, value = line.partition('=')
                                if not equal:
                                    continue
                                name = name.strip()
                                value = value.strip()
                                if value[0] == '"':
                                    l, sep, r = value[1:].partition('"')
                                    if sep:
                                        value = l
                                        value_done = True
                                    else:
                                        value = l
                                        in_value = True

                            if not value_done:
                                continue
                            value_done = False

                            if name and value:
                                self.keylist.append(name)
                                self.values[name] = value
                                table = NetworkTable.GetTable(Preferences.kTableName)
                                table[name] = value

                                if comment:
                                    self.comments[name] = comment
                                    comment = ""

                except IOError:
                    logging.error("NoAvailableResources: Failed to open preferences file.")

                self.endComment = comment

        def WriteTaskRun(self):
            """Internal method that actually writes the table to a file.
            This is called in its own thread when {@link Preferences#Save()
            Save()} is called."""
            with self.tableLock:
                self.fileOpStarted.set()

                with open(Preferences.kFileName, "w") as f:
                    print("[Preferences]", file=f)
                    for key in self.keylist:
                        value = self.values[key]
                        comment = self.comments.get(key, "")

                        if comment:
                            print(comment, end='', file=f)

                        print(key, Preferences.kValuePrefix, value,
                                Preferences.kValueSuffix, sep='', file=f)

                    if self.endComment:
                        print(self.endComment, file=f)

                table = NetworkTable.GetTable(Preferences.kTableName)
                table[Preferences.kSaveField] = False

                self.changed = False

        #
        # NetworkTableChangeListener interface
        #
        def ValueChanged(self, table, name, type):
            if name == Preferences.kSaveField:
                if table.GetBoolean(Preferences.kSaveField):
                    self.Save()
                return

            with self.tableLock:
                key = name
                for p in "=\n\r \t\"":
                    if p in key:
                        # The key is bogus... ignore it
                        return

                if '"' in table.GetString(key):
                    table[key] = '"'
                    if key in self.values:
                        del self.values[key]
                        self.keylist.remove(key)
                else:
                    if key not in self.values:
                        self.keylist.append(key)
                    self.values[key] = table.GetString(key)
                self.changed = True

        def ValueConfirmed(self, table, name, type):
            pass
