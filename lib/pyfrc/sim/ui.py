'''
    Note: http://bugs.python.org/issue11077 seems to indicate that tk is 
    supposed to be thread-safe, but everyone else on the net insists that
    it isn't. Be safe, don't call into the GUI from another thread.  
'''

try:
    import tkinter as tk
except ImportError:
    print("pyfrc robot simulation requires python tkinter support to be installed")
    raise
    
import queue
from hal_impl.data import hal_data

from .. import __version__

from .field.field import RobotField

from .ui_widgets import CheckButtonWrapper, PanelIndicator, Tooltip, ValueWidget


class SimUI(object):
    
    def __init__(self, manager, fake_time, field_size, px_per_ft):
        '''
            initializes all default values and creates 
            a board, waits for run() to be called
            to start the board
            
            manager - sim manager class instance
        '''
        
        self.manager = manager
        self.fake_time = fake_time
        
        self.root = tk.Tk()
        self.root.wm_title("PyFRC Robot Simulator v%s" % __version__)
        
        # setup mode switch
        frame = tk.Frame(self.root)
        frame.pack(side=tk.TOP, anchor=tk.W)
               
        self._setup_widgets(frame, field_size, px_per_ft)
       
        self.root.resizable(width=0, height=0)
        
        
        self.mode_start_tm = 0
        self.text_id = None
        
        # Set up idle_add
        self.queue = queue.Queue()
        
        # connect to the controller
        self.manager.on_mode_change(lambda mode: self.idle_add(self.on_robot_mode_change, mode))
        self.on_robot_mode_change(self.manager.get_mode())
        
        self.timer_fired()
        
        
    def _setup_widgets(self, frame, field_size, px_per_ft):
        
        top = tk.Frame(frame)
        top.grid(column=0, row=0)
                
        bottom = tk.Frame(frame)
        bottom.grid(column=0, row=1)
        
        self.field = RobotField(frame, self.manager, field_size, px_per_ft)
        self.field.grid(column=1, row=0, rowspan=2)
        
        # status bar
        self.status = tk.Label(frame, bd=1, relief=tk.SUNKEN, anchor=tk.E)
        self.status.grid(column=0, row=2, columnspan=2, sticky=tk.W+tk.E)
        
        # analog
        slot = tk.LabelFrame(top, text='Analog')
        self.analog = []
        
        for i in range(1, 9):
            label = tk.Label(slot, text=str(i-1))
            label.grid(column=0, row=i)
            
            vw = ValueWidget(slot, clickable=True, minval=-10.0, maxval=10.0)
            vw.grid(column=1, row=i)
            
            self.analog.append(vw)
        
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # digital
        slot = tk.LabelFrame(top, text='Digital')
        
        label = tk.Label(slot, text='PWM')
        label.grid(column=0, columnspan=4, row=0)
        self.pwm = []
        
        for i in range(len(hal_data['pwm'])):
            
            c = i // 10
            
            label = tk.Label(slot, text=str(i))
            label.grid(column=0+2*c, row=1 + i % 10)
            
            vw = ValueWidget(slot)
            vw.grid(column=1+2*c, row=1 + i % 10)
            self.pwm.append(vw)
            
        label = tk.Label(slot, text='Digital I/O')
        label.grid(column=4, columnspan=6, row=0)
        self.dio = []
        
        for i in range(len(hal_data['dio'])):
            
            c = i // 9
            
            label = tk.Label(slot, text=str(i))
            label.grid(column=4+c*2, row=1 + i % 9)
            
            pi = PanelIndicator(slot, clickable=True)
            pi.grid(column=5+c*2, row=1 + i % 9)
            self.dio.append(pi)
            
        label = tk.Label(slot, text='Relay')
        label.grid(column=10, columnspan=2, row=0, padx=5)
        self.relays = []
        
        for i in range(len(hal_data['relay'])):
            label = tk.Label(slot, text=str(i))
            label.grid(column=10, row=1 + i, sticky=tk.E)
            
            pi = PanelIndicator(slot)
            pi.grid(column=11, row=1 + i)
            self.relays.append(pi)
            
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
        csfm = tk.Frame(top)
            
        # solenoid
        slot = tk.LabelFrame(csfm, text='Solenoid')
        self.solenoids = []
        
        for i in range(len(hal_data['solenoid'])):
            label = tk.Label(slot, text=str(i))
            
            c = int(i/2)*2
            r = i%2
            
            label.grid(column=0+c, row=r)
            
            pi = PanelIndicator(slot)
            pi.grid(column=1+c, row=r)
            
            self.solenoids.append(pi)
        
        slot.pack(side=tk.TOP, fill=tk.BOTH, padx=5)
        
        # CAN
        self.can_slot = tk.LabelFrame(csfm, text='CAN')
        self.can_slot.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=5)
        self.can = {}
        
        csfm.pack(side=tk.LEFT, fill=tk.Y)
        
        # joysticks
        slot = tk.LabelFrame(bottom, text='Joysticks')
        
        self.joysticks = []
        
        for i in range(4):
        
            axes = []
            buttons = []
            
            col = 1 + i*3
        
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
                buttons.append((ck, var))
                
                if j == 1:
                    Tooltip.create(ck, 'Trigger')
                elif j == 2:
                    Tooltip.create(ck, 'Top')
                
            self.joysticks.append((axes, buttons))
            
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
            
        ctrl_frame = tk.Frame(bottom)
        
        # timing control
        timing_control = tk.LabelFrame(ctrl_frame, text='Time')
        
        #self.
        
        def _set_realtime():
            if realtime_mode.get() == 0:
                step_button.pack_forget()
                step_entry.pack_forget()
                self.on_pause(False)
            else:
                step_button.pack(fill=tk.X)
                step_entry.pack()
                self.on_pause(True)
                
        
        realtime_mode = tk.IntVar()
        
        button = tk.Radiobutton(timing_control, text='Run', variable=realtime_mode,
                                value=0, command=_set_realtime)
        button.pack(fill=tk.X)
        
        button = tk.Radiobutton(timing_control, text='Pause', variable=realtime_mode,
                                value=1, command=_set_realtime)
        button.pack(fill=tk.X)
        
        step_button = tk.Button(timing_control, text='Step', command=self.on_step_time)
        self.step_entry = tk.StringVar()
        self.step_entry.set("0.025")
        step_entry = tk.Entry(timing_control, width=6, textvariable=self.step_entry)
        
        Tooltip.create(step_button, 'Click this to increment time by the step value')
        Tooltip.create(step_entry, 'Time to step (in seconds)')
        realtime_mode.set(0)
        
        timing_control.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # simulation control
        sim = tk.LabelFrame(ctrl_frame, text='Robot')
        self.state_buttons = []
                
        self.mode = tk.IntVar()
        
        def _set_mode():
            self.manager.set_mode(self.mode.get())
        
        button = tk.Radiobutton(sim, text='Disabled', variable=self.mode, \
                                value=self.manager.MODE_DISABLED, command=_set_mode)
        button.pack(fill=tk.X)
        self.state_buttons.append(button)
        
        button = tk.Radiobutton(sim, text='Autonomous', variable=self.mode, \
                                value=self.manager.MODE_AUTONOMOUS, command=_set_mode)
        button.pack(fill=tk.X)
        self.state_buttons.append(button)
        
        button = tk.Radiobutton(sim, text='Teleoperated', variable=self.mode, \
                                value=self.manager.MODE_OPERATOR_CONTROL, command=_set_mode)
        button.pack(fill=tk.X)
        self.state_buttons.append(button)
        
        button = tk.Radiobutton(sim, text='Test', variable=self.mode, \
                                value=self.manager.MODE_TEST, command=_set_mode)
        button.pack(fill=tk.X)
        self.state_buttons.append(button)
        
        self.robot_dead = tk.Label(sim, text='Robot died!', fg='red')
        
        sim.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y)
     
    def _add_CAN(self, canId, device):
        
        row = len(self.can)
        
        lbl = tk.Label(self.can_slot, text=str(canId))
        lbl.grid(column=0, row=row)
        
        motor = ValueWidget(self.can_slot, default=0.0)
        motor.grid(column=1, row=row)
        
        fl = CheckButtonWrapper(self.can_slot, text='F')
        fl.grid(column=2, row=row)
        
        rl = CheckButtonWrapper(self.can_slot, text='R')
        rl.grid(column=3, row=row)
        
        self._set_tooltip(motor, device)
        Tooltip.create(fl, 'Forward limit switch')
        Tooltip.create(rl, 'Reverse limit switch')
        
        self.can[canId] = (motor, fl, rl)
        
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
        
            
        # TODO: support multiple slots?
        
        # analog module
        for i, (ain, aout) in enumerate(zip(hal_data['analog_in'],
                                            hal_data['analog_out'])):
            
            aio = self.analog[i]
            
            if ain['initialized']:
                aio.set_disabled(False)
                ain['voltage'] = aio.get_value()
            elif aout['initialized']:
                aio.set_value(aout['voltage'])
            else:
                aio.set_disabled()
        
        # digital module
        for i, ch in enumerate(hal_data['dio']):
            dio = self.dio[i]
            if not ch['initialized']:
                dio.set_disabled()
            else:
                self._set_tooltip(dio, ch)
                
                # determine which one changed, and set the appropriate one
                ret = dio.sync_value(ch['value'])
                if ret is not None:
                    ch['value'] = ret
        
        for i, ch in enumerate(hal_data['pwm']):
            pwm = self.pwm[i]
            if not ch['initialized']:
                pwm.set_disabled()
            else:
                self._set_tooltip(pwm, ch)
                
                # determine which one changed, and set the appropriate one
                pwm.set_value(ch['value'])
                
        for i, ch in enumerate(hal_data['relay']):
            relay = self.relays[i]
            if not ch['initialized']:
                relay.set_disabled()
            else:
                #self._set_tooltip(relay, ch)
                
                if ch['fwd']:
                    relay.set_on()
                elif ch['rev']:
                    relay.set_back()
                else:
                    relay.set_off()
        
        # solenoid
        for i, ch in enumerate(hal_data['solenoid']):
            sol = self.solenoids[i]
            if not ch['initialized']:
                sol.set_disabled()
            else:
                self._set_tooltip(sol, ch)
                # determine which one changed, and set the appropriate one
                sol.set_value(ch['value'])
        
        # CAN
        
        # detect new devices
        if len(self.can) != len(hal_data['CAN']):
            existing = list(self.can.keys())
            for k in sorted(hal_data['CAN'].keys()):
                if k in existing:
                    continue
                self._add_CAN(k, hal_data['CAN'][k])
                
        for k, (motor, fl, rl) in self.can.items():
            can = hal_data['CAN'][k]
            
            motor.set_value(can['value'])
            
            ret = fl.sync_value(not can['limit_switch_closed_for'])
            if ret is not None:
                can['limit_switch_closed_for'] = not ret
                
            ret = rl.sync_value(not can['limit_switch_closed_rev'])
            if ret is not None:
                can['limit_switch_closed_rev'] = not ret 
        
        
        # joystick/driver station
        #sticks = _core.DriverStation.GetInstance().sticks
        #stick_buttons = _core.DriverStation.GetInstance().stick_buttons
        
        for i, (axes, buttons) in enumerate(self.joysticks):
            joy = hal_data['joysticks'][i]
            jaxes = joy['axes']
            for j, ax in enumerate(axes):
                jaxes[j] = ax.get_value() 
        
            jbuttons = joy['buttons']
            for j, (ck, var) in enumerate(buttons):
                jbuttons[j+1]  = True if var.get() else False
                
        self.field.update_widgets()
        
        tm = self.fake_time.get()
        mode_tm = tm - self.mode_start_tm
        
        self.status.config(text="Time: %.03f mode, %.03f total" % (mode_tm, tm))
            
    
        
    def _set_tooltip(self, widget, obj):
        return
        
        # TODO: Fix this
        if not hasattr(widget, 'has_tooltip'):
            
            if hasattr(obj, 'label'):
                tooltip = obj.label
            else:
                # only show the parent object, otherwise the tip is confusing
                while hasattr(obj, '_parent'):
                    obj = obj._parent
                    
                tooltip = obj.__class__.__name__.strip('_')
                    
            Tooltip.create(widget, tooltip)
            
    def on_robot_mode_change(self, mode):
        self.mode.set(mode)
        
        self.mode_start_tm = self.fake_time.get()
        
        # this is not strictly true... a robot can actually receive joystick
        # commands from the driver station in disabled mode. However, most 
        # people aren't going to use that functionality... 
        controls_disabled = False if mode == self.manager.MODE_OPERATOR_CONTROL else True 
        state = tk.DISABLED if controls_disabled else tk.NORMAL
        
        for axes, buttons in self.joysticks:
            for axis in axes:
                axis.set_disabled(disabled=controls_disabled)
            for ck, var in buttons:
                ck.config(state=state)
        
        if not self.manager.is_alive():
            for button in self.state_buttons:
                button.config(state=tk.DISABLED)
                
            self.robot_dead.pack()
            
    #
    # Time related callbacks
    #
            
    def on_pause(self, pause):
        if pause:
            self.fake_time.pause()
        else:
            self.fake_time.resume()

    def on_step_time(self):
        val = self.step_entry.get()
        try:
            tm = float(self.step_entry.get())
        except ValueError:
            tk.messagebox.showerror("Invalid step time", "'%s' is not a valid number" % val)
            return
            
        if tm > 0:
            self.fake_time.resume(tm)
        
        