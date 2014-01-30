'''
    Note: http://bugs.python.org/issue11077 seems to indicate that tk is 
    supposed to be thread-safe, but everyone else on the net insists that
    it isn't. Be safe, don't call into the GUI from another thread.  
'''

try:
    import tkinter as tk
    import tkinter.ttk as ttk
except ImportError:
    print("pyfrc robot simulation requires python tkinter support to be installed")
    raise
    
import queue

from ..wpilib._wpilib import _core

from .ui_widgets import PanelIndicator, ValueWidget


class SimUI(object):
    
    def __init__(self, manager):
        '''
            initializes all default values and creates 
            a board, waits for run() to be called
            to start the board
            
            manager - sim manager class instance
        '''
        
        self.manager = manager
        
        self.root = tk.Tk()
        self.root.wm_title("pyfrc Robot Simulator")
        
        # setup mode switch
        frame = tk.Frame(self.root)
        frame.pack(side=tk.TOP, anchor=tk.W)
               
        self._setup_widgets(frame)
       
        self.root.resizable(width=0, height=0)
        
        
        
        self.text_id = None
        
        # Set up idle_add
        self.queue = queue.Queue()
        
        # connect to the controller
        self.manager.on_mode_change(lambda mode: self.idle_add(self.on_robot_mode_change, mode))
        
        self.timer_fired()
        
        
    def _setup_widgets(self, frame):
        
        top = tk.Frame(frame)
        top.pack(side=tk.TOP, fill=tk.X)
        
        bottom = tk.Frame(frame)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        
        # analog
        slot = tk.LabelFrame(top, text='Analog')
        self.analog = []
        
        for i in range(1, 9):
            label = tk.Label(slot, text=str(i))
            label.grid(column=0, row=i)
            
            vw = ValueWidget(slot, clickable=True)
            vw.grid(column=1, row=i)
            self.analog.append(vw)
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # digital
        slot = tk.LabelFrame(top, text='Digital')
        
        label = tk.Label(slot, text='PWM')
        label.grid(column=0, columnspan=2, row=0)
        self.pwm = []
        
        for i in range(1, 11):
            label = tk.Label(slot, text=str(i))
            label.grid(column=0, row=i)
            
            vw = ValueWidget(slot)
            vw.grid(column=1, row=i)
            self.pwm.append(vw)
            
        label = tk.Label(slot, text='Digital I/O')
        label.grid(column=2, columnspan=4, row=0)
        self.dio = []
        
        for i in range(1, 8):
            label = tk.Label(slot, text=str(i))
            label.grid(column=2, row=i)
            
            pi = PanelIndicator(slot, clickable=True)
            pi.grid(column=3, row=i)
            self.dio.append(pi)
            
        for i in range(8, 15):
            label = tk.Label(slot, text=str(i))
            label.grid(column=4, row=i-7)
            
            pi = PanelIndicator(slot, clickable=True)
            pi.grid(column=5, row=i-7)
            self.dio.append(pi)
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
        # CAN
        slot = tk.LabelFrame(top, text='CAN')
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
        # solenoid
        slot = tk.LabelFrame(top, text='Solenoid')
        self.solenoids = []
        
        for i in range(1, 9):
            label = tk.Label(slot, text=str(i))
            label.grid(column=0, row=i)
            
            pi = PanelIndicator(slot)
            pi.grid(column=1, row=i)
            
            self.solenoids.append(pi)
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # joysticks
        slot = tk.LabelFrame(bottom, text='Joysticks')
        
        self.joysticks = []
        
        for i in range(1, 5):
        
            axes = []
            buttons = []
            
            col = i*3
        
            label = tk.Label(slot, text='Stick %s' % i)
            label.grid(column=col, columnspan=3, row=0)
            
            for j, t in enumerate(['X', 'Y', 'Z', 'T']):
                label = tk.Label(slot, text=t)
                label.grid(column=col, row=j+1)
                
                vw = ValueWidget(slot, clickable=True, default=0.0)
                vw.grid(column=col+1, row=j+1, columnspan=2)
                
                axes.append(vw)
            
            for j in range(1, 11):
                var = tk.IntVar()
                ck = tk.Checkbutton(slot, text=str(j), variable=var)
                ck.grid(column=col+1+(1-j%2), row=5 + int((j - 1) / 2))
                buttons.append(var)
                
            self.joysticks.append((axes, buttons))
            
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
            
        # simulation control
        sim = tk.LabelFrame(bottom, text='Robot')
        
        button = tk.Button(sim, text='Stop')
        button = tk.Button(sim, text='Step')
        
        self.mode = tk.IntVar()
        
        def _set_mode():
            self.manager.set_mode(self.mode.get())
        
        button = tk.Radiobutton(sim, text='Disabled', variable=self.mode, \
                                value=self.manager.MODE_DISABLED, command=_set_mode)
        button.pack(fill=tk.X)
        button = tk.Radiobutton(sim, text='Autonomous', variable=self.mode, \
                                value=self.manager.MODE_AUTONOMOUS, command=_set_mode)
        button.pack(fill=tk.X)
        button = tk.Radiobutton(sim, text='Teleoperated', variable=self.mode, \
                                value=self.manager.MODE_OPERATOR_CONTROL, command=_set_mode)
        button.pack(fill=tk.X)
        
        
        sim.pack(side=tk.LEFT, fill=tk.Y)
     
    def _add_CAN(self):
        pass   
        
    def idle_add(self, callable, *args):
        '''Call this with a function as the argument, and that function
           will be called on the GUI thread via an event
           
           This function returns immediately
        '''
        self.queue.put((callable, args))
        
    def __process_idle_events(self):
        '''This should never be called directly, it is called via an 
           event, and should always be on the GUI thread'''
        while True:
            try:
                callable, args = self.queue.get(block=False)
            except queue.Empty:
                break
            callable(*args)
        
    def run(self):
        # and launch the thread
        self.root.mainloop()  # This call BLOCKS
         
    def timer_fired(self):
        '''Polling loop for events from other threads'''
        self.__process_idle_events()
        
        # grab the simulation lock, gather all of the
        # wpilib objects, and display them on the screen
        self.update_widgets()
            
        # call next timer_fired (or we'll never call timer_fired again!)
        delay = 100 # milliseconds
        self.root.after(delay, self.timer_fired) # pause, then call timer_fired again
        
    
    def update_widgets(self):
        
        with _core._WPILibObject._sim_lock:
            
            # TODO: support multiple slots?
            
            # analog module
            # -> TODO: voltage and value should be the same?
            
            for i, ch in enumerate(_core.AnalogModule._channels):
                if ch is None:
                    self.analog[i].set_disabled()
                else:
                    ret = self.analog[i].sync_value(ch.value)
                    if ret is not None:
                        ch.value = ret
            
            # digital module
            for i, ch in enumerate(_core.DigitalModule._io):
                if ch is None:
                    self.dio[i].set_disabled()
                else:
                    # determine which one changed, and set the appropriate one
                    ret = self.dio[i].sync_value(ch.value)
                    if ret is not None:
                        ch.value = ret
            
            for i, ch in enumerate(_core.DigitalModule._pwm):
                if ch is None:
                    self.pwm[i].set_disabled()
                else:
                    self.pwm[i].set_value(ch.value)
            
            # solenoid
            for i, ch in enumerate(_core.Solenoid._channels):
                if ch is None:
                    self.solenoids[i].set_disabled()
                else:
                    self.solenoids[i].set_value(ch.value)
            
            # can
            
            # joystick/driver station
            sticks = _core.DriverStation.GetInstance().sticks
            stick_buttons = _core.DriverStation.GetInstance().stick_buttons
            
            for i, (axes, buttons) in enumerate(self.joysticks):
                for j, ax in enumerate(axes):
                    sticks[i][j+1] = ax.get_value() 
            
                for j, button in enumerate(buttons):
                    stick_buttons[i][j] = True if button.get() else False
        
    def on_robot_mode_change(self, mode):
        self.mode.set(mode)
