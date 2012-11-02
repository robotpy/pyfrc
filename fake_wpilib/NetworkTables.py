# Copyright (c) FIRST 2011. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in $(WIND_BASE)/WPILib.
# 
# Ported to Python by Peter Johnson, Team 294
#
import threading
import struct
import logging
import weakref
import select
import socket
import atexit

# Interface constants
kSTRING             = 0
kBEGIN_STRING       = 0xFF
kEND_STRING         = 0
kINT                = 1
kDOUBLE             = 2
kTABLE              = 3
kTABLE_ASSIGNMENT   = kTABLE
kBOOLEAN_FALSE      = 4
kBOOLEAN_TRUE       = 5
kASSIGNMENT         = 6
kEMPTY              = 7
kDATA               = 8
kOLD_DATA           = 9
kTRANSACTION        = 10
kREMOVAL            = 11
kTABLE_REQUEST      = 12
kID                 = (1 << 7)
kTABLE_ID           = (1 << 6)
kCONFIRMATION       = (1 << 5)
kCONFIRMATION_MAX   = (kCONFIRMATION - 1)
kPING               = kCONFIRMATION
kDENIAL             = (1 << 4)

kTypes_NONE = -1
kTypes_STRING = kSTRING
kTypes_INT = kINT
kTypes_DOUBLE = kDOUBLE
kTypes_BOOLEAN = kBOOLEAN_TRUE
kTypes_TABLE = kTABLE

class Buffer:
    formatDouble = struct.Struct(">d")
    formatInt = struct.Struct(">I")

    def __init__(self, capacity):
        self.buffer = bytearray(capacity)
        self.size = 0

    def WriteString(self, entry):
        entry = entry.encode()
        length = len(entry)
        if length >= kBEGIN_STRING:
            self.WriteByte(kBEGIN_STRING)
            self.WriteBytes(length, entry)
            self.WriteByte(kEND_STRING)
        else:
            self.WriteByte(length)
            self.WriteBytes(length, entry)

    def WriteDouble(self, entry):
        self.formatDouble.pack_into(self.buffer, self.size, entry)
        self.size += self.formatDouble.size

    def WriteInt(self, entry):
        self.formatInt.pack_into(self.buffer, self.size, entry)
        self.size += self.formatInt.size

    def WriteId(self, id):
        self.WriteVariableSize(kID, id)

    def WriteTableId(self, id):
        self.WriteVariableSize(kTABLE_ID, id)

    def WriteBytes(self, length, entries):
        self.buffer[self.size:self.size+length] = entries
        self.size += length

    def WriteByte(self, entry):
        self.buffer[self.size] = entry
        self.size += 1

    def Flush(self, socket):
        socket.sendall(self.buffer[0:self.size])
        self.Clear()

    def Clear(self):
        self.size = 0

    def WriteVariableSize(self, tag, id):
        if id < (tag - 4):
            self.WriteByte(tag | id)
        else:
            fullTag = (tag | (tag - 1)) ^ 3
            if id < (1 << 8):
                self.WriteByte(fullTag)
                self.WriteByte(id)
            elif id < (1 << 16):
                self.WriteByte(fullTag | 1)
                self.WriteByte(id >> 8)
                self.WriteByte(id)
            elif id < (1 << 24):
                self.WriteByte(fullTag | 2)
                self.WriteByte(id >> 16)
                self.WriteByte(id >> 8)
                self.WriteByte(id)
            else:
                self.WriteByte(fullTag | 3)
                self.WriteByte(id >> 24)
                self.WriteByte(id >> 16)
                self.WriteByte(id >> 8)
                self.WriteByte(id)

class Reader:
    def __init__(self, connection, inputStream):
        self.connection = connection
        self.inputStream = inputStream
        # The last read value (-2 if nothing has been read)
        self.lastByte = -2

    def Read(self):
        try:
            rlist = select.select([self.inputStream], [], [])[0]
            if self.inputStream in rlist:
                try:
                    data = self.inputStream.recv(1)
                    if data:
                        self.lastByte = data[0]
                        if self.lastByte != kPING:
                            logging.debug("I:%02X", self.lastByte)
                        return self.lastByte
                except socket.error as err:
                    # TODO: Should we ignore ECONNRESET errors?
                    logging.error("NetworkTablesReadError: %s, errno=%s",
                        self.connection, err.errno)
        except select.error as err:
            if not self.connection.IsConnected():
                # The error came from us closing the socket
                return 0
            logging.error("NetworkTablesReadError: %s, errno=%s",
                self.connection, err)

        self.connection.Close()
        return 0

    def Check(self, useLastValue):
        return self.lastByte if useLastValue else self.Read()

    def ReadString(self):
        self.Read()
        if self.lastByte == kBEGIN_STRING:
            rd = []
            while self.Read() != kEND_STRING:
                rd.append(self.lastByte)
            buffer = "".join(chr(x) for x in rd)
        else:
            length = self.lastByte
            buffer = "".join(chr(self.Read()) for x in range(length))
        return buffer

    def ReadId(self, useLastValue):
        return self.ReadVariableSize(useLastValue, kID)

    def ReadTableId(self, useLastValue):
        return self.ReadVariableSize(useLastValue, kTABLE_ID)

    def ReadVariableSize(self, useLastValue, tag):
        value = self.Check(useLastValue)
        value ^= tag
        if value < (tag - 4):
            return value
        else:
            bytes = (value & 3) + 1
            id = 0
            for i in range(bytes):
                id = (id << 8) | self.Read()
            return id

    def ReadInt(self):
        raw = bytes(self.Read() for x in range(Buffer.formatInt.size))
        return Buffer.formatInt.unpack(raw)[0]

    def ReadDouble(self):
        raw = bytes(self.Read() for x in range(Buffer.formatDouble.size))
        return Buffer.formatDouble.unpack(raw)[0]

    def ReadConfirmations(self, useLastValue):
        return self.Check(useLastValue) ^ kCONFIRMATION

    def ReadDenials(self, useLastValue):
        return self.Check(useLastValue) ^ kDENIAL

    def ReadEntry(self, useLastValue):
        type = self.Check(useLastValue)
        if type == kBOOLEAN_FALSE:
            return BooleanEntry(False)
        elif type == kBOOLEAN_TRUE:
            return BooleanEntry(True)
        elif type == kINT:
            return IntegerEntry(self.ReadInt())
        elif type == kDOUBLE:
            return DoubleEntry(self.ReadDouble())
        elif type == kSTRING:
            return StringEntry(self.ReadString())
        else:
            return None

class Data:
    def Encode(self, buffer):
        raise NotImplementedError

    def IsEntry(self):
        return False
    def IsOldData(self):
        return False
    def IsTransaction(self):
        return False

class Confirmation(Data):
    def __init__(self, count):
        super().__init__()
        self.count = count

    def Encode(self, buffer):
        for i in range(self.count, 0, -(kCONFIRMATION - 1)):
            buffer.WriteByte(kCONFIRMATION | min(kCONFIRMATION - 1, i))

    @staticmethod
    def Combine(a, b):
        a.count = a.count + b.count
        return a

class Denial(Data):
    def __init__(self, count):
        super().__init__()
        self.count = count

    def Encode(self, buffer):
        for i in range(self.count, 0, -(kDENIAL - 1)):
            buffer.WriteByte(kDENIAL | min(kDENIAL - 1, i))

    @staticmethod
    def Combine(a, b):
        a.count = a.count + b.count
        return a

class Key(Data):
    _staticLock = threading.RLock()
    _idsMap = weakref.WeakValueDictionary()
    _currentId = 0

    def __init__(self, table, keyName):
        super().__init__()
        self.table = table
        self.name = keyName
        self.entry = None
        self.id = Key._AllocateId()
        Key._idsMap[self.id] = self

    def GetTable(self):
        return self.table

    def GetType(self):
        if self.entry is None:
            return kTypes_NONE
        return self.entry.GetType()

    def Encode(self, buffer):
        buffer.WriteByte(kASSIGNMENT)
        self.table.EncodeName(buffer)
        buffer.WriteString(self.name)
        buffer.WriteId(self.id)

    def GetEntry(self):
        return self.entry

    def SetEntry(self, entry):
        self.entry = entry
        self.entry.SetKey(self)

    def HasEntry(self):
        return self.entry is not None

    def GetName(self):
        return self.name

    def GetId(self):
        return self.id

    def EncodeName(self, buffer):
        buffer.WriteId(self.id)

    @staticmethod
    def GetKey(id):
        return Key._idsMap.get(id)

    @staticmethod
    def _AllocateId():
        with Key._staticLock:
            Key._currentId += 1
            return Key._currentId

class OldData(Data):
    def __init__(self):
        super().__init__()
        self.entry = entry

    def IsOldData(self):
        return True

    def GetEntry(self):
        return self.entry

    def Encode(self, buffer):
        buffer.WriteByte(kOLD_DATA)
        self.entry.Encode(buffer)

class TableAssignment(Data):
    def __init__(self, table, alteriorId):
        super().__init__()
        self.table = table
        self.alteriorId = alteriorId

    def Encode(self, buffer):
        buffer.WriteByte(kTABLE_ASSIGNMENT)
        buffer.WriteTableId(self.alteriorId)
        self.table.EncodeName(buffer)

class TransactionStart(Data):
    def IsTransaction(self):
        return True

    def Encode(self, buffer):
        buffer.WriteByte(kTRANSACTION)

class TransactionEnd(Data):
    def IsTransaction(self):
        return True

    def Encode(self, buffer):
        buffer.WriteByte(kTRANSACTION)

class Entry(Data):
    def __init__(self):
        super().__init__()
        self.key = None
        self.source = None

    def SetKey(self, key):
        self.key = key

    def GetKey(self):
        return self.key

    def SetSource(self, source):
        self.source = source

    def GetSource(self):
        return self.source

    def IsEntry(self):
        return True

    def GetType(self):
        raise NotImplementedError

    def GetId(self):
        return self.key.GetId()

    def Encode(self, buffer):
        self.key.EncodeName(buffer)

    def GetInt(self):
        raise TypeError

    def GetDouble(self):
        raise TypeError

    def GetBoolean(self):
        raise TypeError

    def GetString(self):
        raise TypeError

    def GetTable(self):
        raise TypeError

class BooleanEntry(Entry):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def GetType(self):
        return kTypes_BOOLEAN

    def Encode(self, buffer):
        super().Encode(buffer)
        buffer.WriteByte(kBOOLEAN_TRUE if self.value else
                kBOOLEAN_FALSE)

    def GetBoolean(self):
        return self.value

class IntegerEntry(Entry):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def GetType(self):
        return kTypes_INT

    def Encode(self, buffer):
        super().Encode(buffer)
        buffer.WriteByte(kINT)
        buffer.WriteInt(self.value)

    def GetInt(self):
        return self.value

class DoubleEntry(Entry):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def GetType(self):
        return kTypes_DOUBLE

    def Encode(self, buffer):
        super().Encode(buffer)
        buffer.WriteByte(kDOUBLE)
        buffer.WriteDouble(self.value)

    def GetDouble(self):
        return self.value

class StringEntry(Entry):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def GetType(self):
        return kTypes_STRING

    def Encode(self, buffer):
        super().Encode(buffer)
        buffer.WriteByte(kSTRING)
        buffer.WriteString(self.value)

    def GetString(self):
        return self.value

class TableEntry(Entry):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def GetType(self):
        return kTypes_TABLE

    def Encode(self, buffer):
        super().Encode(buffer)
        self.value.EncodeName(buffer)

    def GetTable(self):
        return self.value

class NetworkQueue:
    class Elem:
        def __init__(self, data):
            self.data = data

    def __init__(self):
        self.dataLock = threading.RLock()
        self.dataQueue = []
        self.latestDataHash = {}
        self.inTransaction = False

    def Offer(self, value):
        with self.dataLock:
            if isinstance(value, TransactionStart):
                self.inTransaction = True
                self.dataQueue.append(NetworkQueue.Elem(value))
            elif isinstance(value, TransactionEnd):
                self.inTransaction = False
                self.dataQueue.append(NetworkQueue.Elem(value))
            elif value.IsEntry():
                if self.inTransaction:
                    self.dataQueue.append(NetworkQueue.Elem(value))
                elif value.GetId() in self.latestDataHash:
                    # Replace the old value for this key with a new one
                    self.latestDataHash[value.GetId()].data = value
                else:
                    # Add a new entry to the queue
                    elem = NetworkQueue.Elem(value)
                    self.dataQueue.append(elem)
                    self.latestDataHash[value.GetId()] = elem
            else:
                # TODO: Combine Confirmations
                # TODO: Combine Denials
                self.dataQueue.append(NetworkQueue.Elem(value))

    def IsEmpty(self):
        with self.dataLock:
            return not self.dataQueue

    def ContainsKey(self, key):
        with self.dataLock:
            return key in self.latestDataHash

    def __contains__(self, key):
        return self.ContainsKey(key)

    def Poll(self):
        with self.dataLock:
            if not self.dataQueue:
                return None
            data = self.dataQueue.pop(0).data
            if data.IsEntry():
                del self.latestDataHash[data.GetId()]
            return data

    def Clear(self):
        with self.dataLock:
            self.dataQueue.clear()
            self.latestDataHash.clear()

    def Peek(self):
        with self.dataLock:
            if not self.dataQueue:
                return None
            return self.dataQueue[0].data

    def GetQueue(self):
        return self.dataQueue

class NetworkTableAdditionListener:
    def FieldAdded(self, table, name, type):
        raise NotImplementedError

class NetworkTableChangeListener:
    def ValueChanged(self, table, name, type):
        raise NotImplementedError
    def ValueConfirmed(self, table, name, type):
        raise NotImplementedError

class NetworkTableConnectionListener:
    def Connected(self, table):
        raise NotImplementedError
    def Disconnected(self, table):
        raise NotImplementedError

class NetworkTable:
    # Links names to tables
    _tableMap = {}
    _currentId = 1
    _initialized = False
    _staticMemberMutex = threading.RLock()

    def __init__(self):
        super().__init__()
        self.dataLock = threading.RLock()# The lock for data
        self.data = {}                  # The actual data
        self.connections = set()        # The connections this table has
        # The lock for listener modification
        self.listenerLock = threading.RLock()
        # Set of NetworkingListeners who register for everything
        self.listenToAllListeners = weakref.WeakSet()
        self.listeners = {}             # Links names to NetworkingListeners
        self.additionListeners = weakref.WeakSet()  # Set of addition listeners
        self.connectionListeners = weakref.WeakSet()# Set of connection listeners
        self.id = NetworkTable._GrabId()# The id of this table
        # The queue of the current transaction
        self.transaction = NetworkQueue()
        # The number of times begin transaction has been called without a
        # matching end transaction
        self.transactionCount = 0
        # A list of values which need to be signaled
        self.hasChanged = NetworkQueue()
        # A list of values which have been added
        self.hasAdded = NetworkQueue()

    def __del__(self):
        if not hasattr(self, "hasAdded"):
            return
        with self.listenerLock:
            self.connectionListeners.clear()
            self.additionListeners.clear()
            self.listeners.clear()
            self.listenToAllListeners.clear()
        with self.dataLock:
            self.connections.clear()
            self.data.clear()

    @staticmethod
    def Initialize():
        """Opens up the connection stream.  Note that this method will be
        called automatically when {@link NetworkTable.GetTable()} is called.
        This will only have an effect the first time this is called."""
        if not NetworkTable._initialized:
            NetworkTable._initialized = True
            ConnectionManager.GetInstance()

    @staticmethod
    def GetTable(name):
        """Returns the table with the given name.  The table will
        automatically be connected by clients asking for the same table."""
        NetworkTable.Initialize()
        with NetworkTable._staticMemberMutex:
            try:
                return NetworkTable._tableMap[name]
            except KeyError:
                table = NetworkTable()
                NetworkTable._tableMap[name] = table
                return table

    def GetKeys(self):
        with self.dataLock:
            return [x.GetName() for x in self.data.values() if x.HasEntry()]

    def keys(self):
        return self.GetKeys()

    def BeginTransaction(self):
        """Begins a transaction.  Note that you must call EndTransaction()
        afterwards."""
        with self.dataLock:
            self.transactionCount += 1

    def EndTransaction(self):
        with self.dataLock:
            if self.transactionCount == 0:
                raise ValueError("EndTransaction() called too many times")
            self.transactionCount -= 1
            if self.transactionCount == 0:
                self.ProcessTransaction(True, self.transaction)

    def AddChangeListener(self, keyName, listener):
        """Adds a NetworkTableChangeListener to listen to the specified element.
        @param keyName the key to listen to
        @param listener the listener
        @see NetworkTableChangeListener"""
        with self.listenerLock:
            listenersForKey = \
                    self.listeners.setdefault(keyName, weakref.WeakSet())
            listenersForKey.add(listener)

    def AddChangeListenerAny(self, listener):
        """Adds a NetworkTableChangeListener to listen to any element changed
        in the table
        @param listener the listener"""
        with self.listenerLock:
            self.listenToAllListeners.add(listener)

    def RemoveChangeListener(self, keyName, listener):
        """Removes the given NetworkTableChangeListener from the specified
        element.
        @param keyName the key to no longer listen to.
        @param listener the listener to remove
        @see NetworkTableChangeListener"""
        with self.listenerLock:
            try:
                self.listeners[keyName].discard(listener)
            except KeyError:
                pass

    def RemoveChangeListenerAny(self, listener):
        """Removes the given NetworkTableChangeListener for any element in the
        table.
        @param listener the listener to remove
        @see NetworkTableChangeListener"""
        with self.listenerLock:
            self.listenToAllListeners.discard(listener)

    def AddAdditionListener(self, listener):
        """Adds the NetworkTableAdditionListener to the table.
        @param listener the listener to add
        @see NetworkTableAdditionListener"""
        with self.listenerLock:
            self.additionListeners.add(listener)

    def RemoveAdditionListener(self, listener):
        """Removes the given NetworkTableAdditionListener from the set of
        listeners.
        @param listener the listener to remove
        @see NetworkTableAdditionListener"""
        with self.listenerLock:
            self.additionListeners.discard(listener)

    def AddConnectionListener(self, listener, immediateNotify):
        """Adds a NetworkTableConnectionListener to this table.
        @param listener the listener to add
        @param immediateNotify whether to tell the listener of the current
               connection status
        @see NetworkTableConnectionListener"""
        with self.listenerLock:
            self.connectionListeners.add(listener)

    def RemoveConnectionListener(self, listener):
        """Removes the given NetworkTableConnectionListener from the table.
        @param listener the listener to remove
        @see NetworkTableConnectionListener"""
        with self.listenerLock:
            self.connectionListeners.discard(listener)

    def IsConnected(self):
        """Returns whether or not this table is connected to the robot."""
        with self.dataLock:
            return bool(self.connections)

    def ContainsKey(self, keyName):
        with self.dataLock:
            val = self.data.get(keyName)
            return val is not None and val.HasEntry()

    def __contains__(self, keyName):
        return self.ContainsKey(keyName)

    def GetEntry(self, keyName):
        """Internally used to get at the underlying Entry
        @param keyName the name of the key
        @return the entry at that position (or null if no entry)"""
        with self.dataLock:
            val = self.data.get(keyName)
            if val is None:
                return None
            return val.GetEntry()

    def __getitem__(self, keyName):
        """Returns the value at the specified key.
        @param keyName the key
        @return the value"""
        entry = self.GetEntry(keyName)
        if entry is None:
            raise KeyError
        t = entry.GetType()
        if t == kTypes_INT:
            return entry.GetInt()
        elif t == kTypes_BOOLEAN:
            return entry.GetBoolean()
        elif t == kTypes_DOUBLE:
            return entry.GetDouble()
        elif t == kTypes_STRING:
            return entry.GetString()
        elif t == kTypes_TABLE:
            return entry.GetTable()
        else:
            return None

    def GetInt(self, keyName):
        """Returns the value at the specified key.
        @param keyName the key
        @return the value"""
        entry = self.GetEntry(keyName)
        if entry is None:
            return 0
        if entry.GetType() == kTypes_INT:
            return entry.GetInt()
        else:
            raise TypeError

    def GetBoolean(self, keyName):
        """Returns the value at the specified key.
        @param keyName the key
        @return the value"""
        entry = self.GetEntry(keyName)
        if entry is None:
            return False
        if entry.GetType() == kTypes_BOOLEAN:
            return entry.GetBoolean()
        else:
            raise TypeError

    def GetDouble(self, keyName):
        """Returns the value at the specified key.
        @param keyName the key
        @return the value"""
        entry = self.GetEntry(keyName)
        if entry is None:
            return 0.0
        if entry.GetType() == kTypes_DOUBLE:
            return entry.GetDouble()
        else:
            raise TypeError

    def GetString(self, keyName):
        """Returns the value at the specified key.
        @param keyName the key
        @return the value"""
        entry = self.GetEntry(keyName)
        if entry is None:
            return ""
        if entry.GetType() == kTypes_STRING:
            return entry.GetString()
        else:
            raise TypeError

    def GetSubTable(self, keyName):
        """Returns the value at the specified key.
        @param keyName the key
        @return the value"""
        entry = self.GetEntry(keyName)
        if entry is None:
            return None
        if entry.GetType() == kTypes_TABLE:
            return entry.GetTable()
        else:
            raise TypeError

    def PutInt(self, keyName, value):
        """Maps the specified key to the specified value in this table.
        Neither the key nor the value can be null.
        The value can be retrieved by calling the get method with a key that
        is equal to the original key.
        @param keyName the key
        @param value the value"""
        self._Put(keyName, IntegerEntry(value))

    def PutBoolean(self, keyName, value):
        """Maps the specified key to the specified value in this table.
        Neither the key nor the value can be null.
        The value can be retrieved by calling the get method with a key that
        is equal to the original key.
        @param keyName the key
        @param value the value"""
        self._Put(keyName, BooleanEntry(value))

    def PutDouble(self, keyName, value):
        """Maps the specified key to the specified value in this table.
        Neither the key nor the value can be null.
        The value can be retrieved by calling the get method with a key that
        is equal to the original key.
        @param keyName the key
        @param value the value"""
        self._Put(keyName, DoubleEntry(value))

    def PutString(self, keyName, value):
        """Maps the specified key to the specified value in this table.
        Neither the key nor the value can be null.
        The value can be retrieved by calling the get method with a key that
        is equal to the original key.
        @param keyName the key
        @param value the value"""
        if value is None:
            raise ValueError
        self._Put(keyName, StringEntry(value))

    def PutSubTable(self, keyName, value):
        """Maps the specified key to the specified value in this table.
        Neither the key nor the value can be null.
        The value can be retrieved by calling the get method with a key that
        is equal to the original key.
        @param keyName the key
        @param value the value"""
        if value is None:
            raise ValueError
        self._Put(keyName, TableEntry(value))

    def __setitem__(self, keyName, value):
        """Maps the specified key to the specified value in this table.
        Neither the key nor the value can be null.
        The value can be retrieved by calling the get method with a key that
        is equal to the original key.
        @param keyName the key
        @param value the value"""
        if isinstance(value, NetworkTable):
            self._Put(keyName, TableEntry(value))
        elif isinstance(value, str):
            self._Put(keyName, StringEntry(value))
        elif isinstance(value, float):
            self._Put(keyName, DoubleEntry(value))
        elif isinstance(value, bool):
            self._Put(keyName, BooleanEntry(value))
        elif isinstance(value, int):
            self._Put(keyName, IntegerEntry(value))
        else:
            raise ValueError

    @staticmethod
    def _GrabId():
        with NetworkTable._staticMemberMutex:
            curId = NetworkTable._currentId
            NetworkTable._currentId += 1
            return curId

    def ProcessTransaction(self, confirmed, transaction):
        if transaction.IsEmpty():
            return

        source = transaction.Peek().GetSource()

        with self.dataLock:
            for conn in self.connections:
                if conn is not source:
                    conn.OfferTransaction(transaction)

            while not transaction.IsEmpty():
                entry = transaction.Poll()
                oldEntry = entry.GetKey().SetEntry(entry)
                if oldEntry is None:
                    self.hasAdded.Offer(entry)
                else:   # TODO: Filter unchanged values
                    self.hasChanged.Offer(entry)
            while not self.hasAdded.IsEmpty():
                entry = self.hasAdded.Poll()
                self.AlertListeners(True, confirmed, entry.GetKey().GetName(),
                        entry)
            while not self.hasChanged.IsEmpty():
                entry = self.hasChanged.Poll()
                self.AlertListeners(True, confirmed, entry.GetKey().GetName(),
                        entry)

    def AddConnection(self, connection):
        with self.dataLock:
            if connection not in self.connections:
                self.connections.add(connection)
                for it in self.data.values():
                    connection.Offer(it)
                    if it.HasEntry():
                        connection.Offer(it.GetEntry())
                if len(self.connections) == 1:
                    with NetworkTable._staticMemberMutex:
                        NetworkTable._tableMap[self.id] = self
                    for it in self.connectionListeners:
                        it.Connected(self)

    def RemoveConnection(self, connection):
        with self.dataLock:
            self.connections.discard(connection)

            if not self.connections:
                with NetworkTable._staticMemberMutex:
                    NetworkTable._tableMap.pop(self.id, None)
                for it in self.connectionListeners:
                    it.Disconnected(self)

    def GetKey(self, keyName):
        """Returns the key that the name maps to.  This should
        never fail, if their is no key for that name, then one should be made.
        @param keyName the name
        @return the key"""
        with self.dataLock:
            try:
                return self.data[keyName]
            except KeyError:
                # Key not found.  Create a new one.
                newval = Key(self, keyName)
                self.data[keyName] = newval
                if self.connections:
                    for it in self.connections:
                        it.Offer(newval)
                return newval

    def _Put(self, keyName, value):
        with self.dataLock:
            key = self.GetKey(keyName)
            value.SetKey(key)

            if self.transactionCount == 0:
                self.Got(True, key, value)
            else:
                self.transaction.Offer(value)

    def Send(self, entry):
        with self.dataLock:
            for it in self.connections:
                if it is not entry.GetSource():
                    it.Offer(entry)

    def Got(self, confirmed, key, value):
        """This method should be called by children when they want to add a
        new value.  It will notify listeners of the value
        @param confirmed whether or not this value was confirmed or received
        @param key the key
        @param value the value"""
        with self.dataLock:
            old = key.SetEntry(value)
        # TODO: return if value didn't change

        self.Send(key.GetEntry())
        self.AlertListeners(old is None, confirmed, key.GetName(),
                key.GetEntry())

    def AlertListeners(self, isNew, confirmed, keyName, value):
        with self.listenerLock:
            if isNew:
                for it in self.additionListeners:
                    it.FieldAdded(self, keyName, value.GetType())

            for it in self.listeners.get(keyName, []):
                if confirmed:
                    it.ValueConfirmed(self, keyName, value.GetType())
                else:
                    it.ValueChanged(self, keyName, value.GetType())

            for it in self.listenToAllListeners:
                if confirmed:
                    it.ValueConfirmed(self, keyName, value.GetType())
                else:
                    it.ValueChanged(self, keyName, value.GetType())

    def EncodeName(self, buffer):
        buffer.WriteTableId(self.id)

    def GetId(self):
        return self.id

class Connection:
    kWriteDelay = 0.25
    kTimeout = 1.0

    def __init__(self, socket):
        self.socket = socket
        self.dataLock = threading.RLock()
        self.dataAvailable = threading.Condition(self.dataLock)
        self.watchdogFood = threading.Condition()
        self.tableMap = {}
        self.fieldMap = {}
        self.queue = NetworkQueue()
        self.confirmations = []
        self.transaction = NetworkQueue()
        self.connected = True
        self.inTransaction = False
        self.denyTransaction = False
        self.watchdogActive = False
        self.watchdogFed = False
        self.readTask = threading.Thread(target=self._ReadTaskRun,
                name="NetworkTablesReadTask")
        self.writeTask = threading.Thread(target=self._WriteTaskRun,
                name="NetworkTablesWriteTask")
        self.watchdogTask = threading.Thread(target=self._WatchdogTaskRun,
                name="NetworkTablesWatchdogTask")
        self.transactionStart = TransactionStart()
        self.transactionEnd = TransactionEnd()

    def OfferTransaction(self, transaction):
        with self.dataLock:
            for it in transaction.GetQueue():
                data = it.data
                if data.IsEntry() and data.GetType() == kTABLE:
                    data.GetTable().AddConnection(self)
            self.queue.Offer(self.transactionStart)
            for it in transaction.GetQueue():
                self.queue.Offer(it.data)
            self.queue.Offer(self.transactionEnd)
            self.dataAvailable.notify()

    def Offer(self, data):
        if data is None:
            return
        with self.dataLock:
            if data.IsEntry() and data.GetType() == kTABLE:
                data.GetTable().AddConnection(self)
            self.queue.Offer(data)
            self.dataAvailable.notify()

    def Start(self):
        self.watchdogTask.start()
        self.readTask.start()
        self.writeTask.start()

    def _ReadTaskRun(self):
        input = Reader(self, self.socket)

        value = input.Read()
        while self.connected:
            self._WatchdogFeed()
            self._WatchdogActivate()

            if value >= kID or value == kOLD_DATA:
                oldData = (value == kOLD_DATA)
                id = input.ReadId(not oldData)
                if not self.connected:
                    break

                key = Key.GetKey(self.fieldMap[id])
                if key is None:
                    logging.error("NetworkTablesCorrupt: Unexpected ID")
                    self.Close()
                    return

                logging.debug("Update field \"%s\" value remote=%d local=%d\n",
                        key.GetName(), id, self.fieldMap[id])

                value = input.Read()
                if not self.connected:
                    break

                if (ConnectionManager.GetInstance().IsServer() and
                        self.ConfirmationsContainsKey(key)):
                    if self.inTransaction:
                        self.denyTransaction = True
                    else:
                        self.Offer(Denial(1))
                    if value >= kTABLE_ID:
                        input.ReadTableId(True)
                    else:
                        input.ReadEntry(True)
                elif value >= kTABLE_ID:
                    tableId = input.ReadTableId(True)
                    if not self.connected:
                        break
                    if oldData and key.HasEntry():
                        self.Offer(Denial(1))
                    else:
                        table = self.GetTable(False, tableId)
                        tableEntry = TableEntry(table)
                        tableEntry.SetSource(self)
                        tableEntry.SetKey(key)
                        if self.inTransaction:
                            self.transaction.Offer(tableEntry)
                        else:
                            key.GetTable().Got(False, key, tableEntry)
                            self.Offer(Confirmation(1))
                else:
                    entry = input.ReadEntry(True)
                    if not self.connected:
                        break

                    if entry is None:
                        logging.error("NetworkTablesCorrupt: Unable to parse entry")
                        self.Close()
                        return
                    elif oldData and key.HasEntry():
                        self.Offer(Denial(1))
                    else:
                        entry.SetSource(self)
                        entry.SetKey(key)
                        if self.inTransaction:
                            self.transaction.Offer(entry)
                        else:
                            key.GetTable().Got(False, key, entry)
                            self.Offer(Confirmation(1))
            elif value >= kCONFIRMATION:
                count = input.ReadConfirmations(True)
                if not self.connected:
                    break
                while count > 0:
                    count -= 1
                    if not self.confirmations:
                        logging.error("NetworkTablesCorrupt: Too many confirmations")
                        self.Close()
                        return
                    entry = self.confirmations.pop(0)
                    # TransactionStart
                    if entry is None:
                        if ConnectionManager.GetInstance().IsServer():
                            while (self.confirmations and
                                    self.confirmations[0] is not None):
                                self.confirmations.pop(0)
                        else:
                            while (self.confirmations and
                                    self.confirmations[0] is not None):
                                self.transaction.Offer(self.confirmations.pop(0))

                            if not self.transaction.IsEmpty():
                                self.transaction.Peek().GetKey().GetTable()\
                                        .ProcessTransaction(True, self.transaction)
                    elif not ConnectionManager.GetInstance().IsServer():
                        entry.GetKey().GetTable().Got(True, entry.GetKey(),
                                entry)
            elif value >= kDENIAL:
                if ConnectionManager.GetInstance().IsServer():
                    logging.error("NetworkTablesCorrupt: Server can not be denied")
                    self.Close()
                    return
                count = input.ReadDenials(self.connected)
                if not self.connected:
                    break
                while count > 0:
                    count -= 1
                    if not self.confirmations:
                        logging.error("NetworkTablesCorrupt: Excess denial")
                        self.Close()
                        return
                    elif self.confirmations[0] is None:
                        self.confirmations.pop(0)
                        # Skip the transaction
                        while (self.confirmations and
                                self.confirmations[0] is not None):
                            self.confirmations.pop(0)
                    else:
                            self.confirmations.pop(0)
            elif value == kTABLE_REQUEST:
                if not ConnectionManager.GetInstance().IsServer():
                    logging.error("NetworkTablesCorrupt: Server requesting table")
                    self.Close()
                    return
                name = input.ReadString()
                if not self.connected:
                    break
                id = input.ReadTableId(False)
                if not self.connected:
                    break
                logging.debug("Request table: %s (%d)\n", name, id)

                table = NetworkTable.GetTable(name)
                with self.dataLock:
                    self.Offer(TableAssignment(table, id))
                    table.AddConnection(self)

                self.tableMap[id] = table.GetId()
            elif value == kTABLE_ASSIGNMENT:
                localTableId = input.ReadTableId(False)
                if not self.connected:
                    break
                remoteTableId = input.ReadTableId(False)
                if not self.connected:
                    break
                logging.debug("Table Assignment: local=%d remote=%d\n",
                        localTableId, remoteTableId)
                self.tableMap[remoteTableId] = localTableId
            elif value == kASSIGNMENT:
                tableId = input.ReadTableId(False)
                if not self.connected:
                    break
                table = self.GetTable(False, tableId)
                keyName = input.ReadString()
                if not self.connected:
                    break
                key = table.GetKey(keyName)
                id = input.ReadId(False)
                if not self.connected:
                    break
                logging.debug("Field Assignment: table %d \"%s\" local=%d remote=%d\n",
                        tableId, keyName, key.GetId(), id)
                self.fieldMap[id] = key.GetId()
            elif value == kTRANSACTION:
                logging.debug("Transaction Start")
                self.inTransaction = not self.inTransaction
                # Finishing a transaction
                if not self.inTransaction:
                    if self.denyTransaction:
                        self.Offer(Denial(1))
                    else:
                        if not self.transaction.IsEmpty():
                            self.transaction.Peek().GetKey().GetTable()\
                                    .ProcessTransaction(False, self.transaction)
                        self.Offer(Confirmation(1))
                    self.denyTransaction = False
                logging.debug("Transaction End")
            else:
                logging.error("NetworkTablesCorrupt: Don't know how to interpret marker byte (%02X)", value)
                self.Close()
                return

            value = input.Read()

    def _WriteTaskRun(self):
        buffer = Buffer(2048)
        sentData = True
        while self.connected:
            data = None
            with self.dataLock:
                data = self.queue.Poll()
                # Check if there is no data to send
                if data is None:
                    # Ping if necessary
                    if sentData:
                        sentData = False
                    else:
                        buffer.WriteByte(kPING)
                        buffer.Flush(self.socket)
                    self.dataAvailable.wait(self.kWriteDelay)
                    continue

            # If there is data, send it
            sentData = True

            if data.IsEntry():
                self.confirmations.append(data)
            elif data.IsOldData():
                self.confirmations.append(data.GetEntry())
            elif data.IsTransaction():
                self.confirmations.append(None)

            data.Encode(buffer)
            buffer.Flush(self.socket)

    def IsConnected(self):
        return self.connected

    def Close(self):
        if self.connected:
            self.connected = False
            self.socket.close()
            self._WatchdogFeed()
            for id in self.tableMap.values():
                table = NetworkTable.GetTable(id)
                logging.debug("Removing Table %d (%r)\n", id, table)
                if table is not None:
                    table.RemoveConnection(self)

            ConnectionManager.GetInstance().RemoveConnection(self)

    def GetTable(self, local, id):
        table = None
        if local:
            table = NetworkTable.GetTable(id)
        else:
            localID = self.tableMap.get(id)
            if localID is not None:
                table = NetworkTable.GetTable(localID)
            else:
                pass
                # This should not be needed as long as TABLE_REQUEST is always issued first
                # We don't care about hosting locally anonymous tables from the network
                #table = NetworkTable()
                #self.tableMap[id] = table.GetId()
                #self.Offer(TableAssignment(table, id))
                #table.AddConnection(self)
        if table is None:
            logging.error("NetworkTablesCorrupt: Unexpected ID")
        return table

    def ConfirmationsContainsKey(self, key):
        for it in self.confirmations:
            if it.GetKey() == key:
                return True

        return False

    def _WatchdogTaskRun(self):
        with self.watchdogFood:
            while self.connected:
                self.watchdogFood.wait_for(lambda: self.watchdogActive)
                self.watchdogFed = False
                if not self.watchdogFood.wait_for(lambda: self.watchdogFed,
                        self.kTimeout):
                    logging.error("Timeout: NetworkTables watchdog expired... disconnecting")
                    break
            self.Close()

    def _WatchdogActivate(self):
        with self.watchdogFood:
            if not self.watchdogActive:
                self.watchdogActive = True
                self.watchdogFood.notify()

    def _WatchdogFeed(self):
        with self.watchdogFood:
            self.watchdogActive = False
            self.watchdogFed = True
            self.watchdogFood.notify()

class ConnectionManager:
    kPort = 1735

    @staticmethod
    def GetInstance():
        try:
            return ConnectionManager._instance
        except AttributeError:
            ConnectionManager._instance = ConnectionManager._inner()
            return ConnectionManager._instance

    class _inner:
        def __init__(self):
            self.isServer = True
            self.connections = set()
            self.listener = threading.Thread(target=self.ListenTaskRun,
                    name="NetworkTablesListener")
            self.run = True
            self.connectionLock = threading.RLock()

            self.listener.daemon = True
            self.listener.start()

        def __del__(self):
            if getattr(self, "listener", None) is None:
                return
            self.run = False
            self.listener.join()

        def ListenTaskRun(self):
            # Create the socket.
            listenSocket = socket.socket()

            # Set the TCP socket so that it can be reused if it is in the wait state
            listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to local address.
            listenSocket.bind(("0.0.0.0", ConnectionManager.kPort))

            # Create queue for client connection requests.
            listenSocket.listen(1)

            while self.run:
                # Check for a shutdown once per second
                rlist = select.select([listenSocket], [], [], 1.0)[0]
                if listenSocket in rlist:
                    try:
                        connectedSocket = listenSocket.accept()[0]
                    except socket.error:
                        continue
                    # TODO: Linger option?
                    self.AddConnection(Connection(connectedSocket))

        def IsServer(self):
            return self.isServer

        def AddConnection(self, connection):
            with self.connectionLock:
                if connection in self.connections:
                    logging.error("ResourceAlreadyAllocated: Connection object already exists")
                    return
                self.connections.add(connection)
            connection.Start()

        def RemoveConnection(self, connection):
            with self.connectionLock:
                self.connections.discard(connection)

