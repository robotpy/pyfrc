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
from hal import TalonSRXConst as tsrxc

from .. import __version__

from .field.field import RobotField

from .ui_widgets import CheckButtonWrapper, PanelIndicator, Tooltip, ValueWidget

import logging
logger = logging.getLogger(__name__)


class SimUI(object):
    
    def __init__(self, manager, fake_time, config_obj):
        '''
            initializes all default values and creates 
            a board, waits for run() to be called
            to start the board
            
            manager - sim manager class instance
        '''
        
        self.manager = manager
        self.fake_time = fake_time
        self.config_obj = config_obj
        
        # Set up idle_add
        self.queue = queue.Queue()
        
        self.root = tk.Tk()
        self.root.wm_title("PyFRC Robot Simulator v%s" % __version__)
        
        # setup mode switch
        frame = tk.Frame(self.root)
        frame.pack(side=tk.TOP, anchor=tk.W)
               
        self._setup_widgets(frame)
       
        self.root.resizable(width=0, height=0)
        
        
        self.mode_start_tm = 0
        self.text_id = None
        
        # connect to the controller
        self.manager.on_mode_change(lambda mode: self.idle_add(self.on_robot_mode_change, mode))
        self.on_robot_mode_change(self.manager.get_mode())
        
        # create pygame joystick if supported
        try:
            from .pygame_joysticks import UsbJoysticks
        except ImportError:
            logger.warn('pygame not detected, real joystick support not loaded')
            self.usb_joysticks = None
        else:
            self.usb_joysticks = UsbJoysticks(self)
            logger.info('pygame was detected, real joystick support loaded!')
              
        try:
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.attributes('-topmost', False)
        except Exception:
            pass
        
        self.timer_fired()      
        
    def _setup_widgets(self, frame):
        
        top = tk.Frame(frame)
        top.grid(column=0, row=0)
                
        bottom = tk.Frame(frame)
        bottom.grid(column=0, row=1)
        
        self.field = RobotField(frame, self.manager, self.config_obj)
        self.field.grid(column=1, row=0, rowspan=2)
        
        # status bar
        self.status = tk.Label(frame, bd=1, relief=tk.SUNKEN, anchor=tk.E)
        self.status.grid(column=0, row=2, columnspan=2, sticky=tk.W+tk.E)
        
        # analog
        slot = tk.LabelFrame(top, text='Analog')
        self.analog = []
        
        for i in range(len(hal_data['analog_in'])):
            if hal_data['analog_in'][i]['initialized'] or hal_data['analog_out'][i]['initialized']:
                label = tk.Label(slot, text=str(i))
                label.grid(column=0, row=i+1)
                
                vw = ValueWidget(slot, clickable=True, minval=-10.0, maxval=10.0)
                vw.grid(column=1, row=i+1)
                self.set_tooltip(vw, 'analog', i)
            else:
                vw = None
            
            self.analog.append(vw)
        
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # digital
        slot = tk.LabelFrame(top, text='Digital')
        
        label = tk.Label(slot, text='PWM')
        label.grid(column=0, columnspan=4, row=0)
        self.pwm = []
        
        for i in range(len(hal_data['pwm'])):
            if hal_data['pwm'][i]['initialized']:
                c = i // 10
                
                label = tk.Label(slot, text=str(i))
                label.grid(column=0+2*c, row=1 + i % 10)
                
                vw = ValueWidget(slot)
                vw.grid(column=1+2*c, row=1 + i % 10)
                self.set_tooltip(vw, 'pwm', i)
            else:
                vw = None
            self.pwm.append(vw)
            
        label = tk.Label(slot, text='Digital I/O')
        label.grid(column=4, columnspan=6, row=0)
        self.dio = []
        
        for i in range(len(hal_data['dio'])):
            
            if hal_data['dio'][i]['initialized']:
            
                c = i // 9
                
                label = tk.Label(slot, text=str(i))
                label.grid(column=4+c*2, row=1 + i % 9)
                
                pi = PanelIndicator(slot, clickable=True)
                pi.grid(column=5+c*2, row=1 + i % 9)
                self.set_tooltip(pi, 'dio', i)
            else:
                pi = None
            
            self.dio.append(pi)
            
        label = tk.Label(slot, text='Relay')
        label.grid(column=10, columnspan=2, row=0, padx=5)
        self.relays = []
        
        for i in range(len(hal_data['relay'])):
            if hal_data['relay'][i]['initialized']:
                label = tk.Label(slot, text=str(i))
                label.grid(column=10, row=1 + i, sticky=tk.E)
                
                pi = PanelIndicator(slot)
                pi.grid(column=11, row=1 + i)
                self.set_tooltip(pi, 'relay', i)
            else:
                pi = None
                
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
            self.set_tooltip(pi, 'solenoid', i)
            
            self.solenoids.append(pi)
        
        slot.pack(side=tk.TOP, fill=tk.BOTH, padx=5)
        
        # CAN
        self.can_slot = tk.LabelFrame(csfm, text='CAN')
        self.can_slot.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=5)
        self.can_mode_map = {
                        tsrxc.kMode_CurrentCloseLoop: 'PercentVbus',
                        tsrxc.kMode_DutyCycle:'PercentVbus',
                        tsrxc.kMode_NoDrive:'Disabled',
                        tsrxc.kMode_PositionCloseLoop:'Position',
                        tsrxc.kMode_SlaveFollower:'Follower',
                        tsrxc.kMode_VelocityCloseLoop:'Speed',
                        tsrxc.kMode_VoltCompen:'Voltage'
                     }
        self.can = {}
        
        # detect new devices
        for k in sorted(hal_data['CAN'].keys()):
            self._add_CAN(k, hal_data['CAN'][k])
        
        
        csfm.pack(side=tk.LEFT, fill=tk.Y)
        
        # joysticks
        slot = tk.LabelFrame(bottom, text='Joysticks')
        
        self.joysticks = []
        
        for i in range(4):
        
            axes = []
            buttons = []
            
            col = 1 + i*3
            row = 0
        
            label = tk.Label(slot, text='Stick %s' % i)
            label.grid(column=col, columnspan=3, row=row)
            row += 1
            
            # TODO: make this configurable
            
            for j, t in enumerate(['X', 'Y', 'Z', 'T', '4', '5']):
                label = tk.Label(slot, text=t)
                label.grid(column=col, row=row)
                
                vw = ValueWidget(slot, clickable=True, default=0.0)
                vw.grid(column=col+1, row=row, columnspan=2)
                self.set_joy_tooltip(vw, i, 'axes', t)
                
                axes.append(vw)
                row += 1
                
            # POV: this needs improvement
            label = tk.Label(slot, text='POV')
            label.grid(column=col, row=row) 
            pov = ValueWidget(slot, clickable=True, default=-1, minval=-1, maxval=360, step=45, round_to_step=True)
            pov.grid(column=col+1, row=row, columnspan=2)
            row += 1
            
            for j in range(1, 11):
                var = tk.IntVar()
                ck = tk.Checkbutton(slot, text=str(j), variable=var)
                ck.grid(column=col+1+(1-j%2), row=row + int((j - 1) / 2))
                self.set_joy_tooltip(ck, i, 'buttons', j)
                
                buttons.append((ck, var))
                
            self.joysticks.append((axes, buttons, [pov]))
            
        
        slot.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
            
        ctrl_frame = tk.Frame(bottom)
        
        # timing control
        timing_control = tk.LabelFrame(ctrl_frame, text='Time')
        
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
        
        #
        # Set up a combo box that allows you to select an autonomous
        # mode in the simulator
        #
        
        try:
            from tkinter.ttk import Combobox
        except:
            pass
        else:
            auton = tk.LabelFrame(ctrl_frame, text='Autonomous')
            
            self.autobox = Combobox(auton, state='readonly')
            self.autobox.bind('<<ComboboxSelected>>', self.on_auton_selected)
            self.autobox['width'] = 12
            self.autobox.pack(fill=tk.X)
            
            Tooltip.create(self.autobox, "Use robotpy_ext.autonomous.AutonomousModeSelector to use this selection box")
            
            from networktables.util import ChooserControl
            self.auton_ctrl = ChooserControl('Autonomous Mode',
                                              lambda v: self.idle_add(self.on_auton_choices, v),
                                              lambda v: self.idle_add(self.on_auton_selection, v))
            
            auton.pack(side=tk.TOP)
        
        ctrl_frame.pack(side=tk.LEFT, fill=tk.Y)
     
    def _add_CAN(self, canId, device):
        
        row = len(self.can)*2
        
        lbl = tk.Label(self.can_slot, text=str(canId))
        lbl.grid(column=0, row=row)
        
        motor = ValueWidget(self.can_slot, default=0.0)
        motor.grid(column=1, row=row)
        self.set_tooltip(motor, 'CAN', canId)
        
        fl = CheckButtonWrapper(self.can_slot, text='F')
        fl.grid(column=2, row=row)
        
        rl = CheckButtonWrapper(self.can_slot, text='R')
        rl.grid(column=3, row=row)
        
        Tooltip.create(fl, 'Forward limit switch')
        Tooltip.create(rl, 'Reverse limit switch')
        
        mode_lbl_txt = tk.StringVar(value = self.can_mode_map[device['mode_select']])
        mode_label = tk.Label(self.can_slot, textvariable=mode_lbl_txt)
        mode_label.grid(column=4, row=row)
        
        labels = tk.Frame(self.can_slot)
        labels.grid(column=0, row=row+1, columnspan=6)
        
        enc_value = tk.StringVar(value='E: 0')
        enc_label = tk.Label(labels, textvariable=enc_value)
        enc_label.pack(side=tk.LEFT)
        
        analog_value = tk.StringVar(value='A: 0')
        analog_label = tk.Label(labels, textvariable=analog_value)
        analog_label.pack(side=tk.LEFT)
        
        pwm_value = tk.StringVar(value='P: 0')
        pwm_label = tk.Label(labels, textvariable=pwm_value)
        pwm_label.pack(side=tk.LEFT)
        
        Tooltip.create(enc_label, "Encoder Input")
        Tooltip.create(analog_label, "Analog Input")
        Tooltip.create(pwm_label, "PWM Input")
        
        self.can[canId] = (motor, fl, rl, mode_lbl_txt, enc_value, analog_value, pwm_value)
        
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
        
        #joystick stuff
        if self.usb_joysticks is not None:
            self.usb_joysticks.update()
        
        # analog module
        for i, (ain, aout) in enumerate(zip(hal_data['analog_in'],
                                            hal_data['analog_out'])):
            
            aio = self.analog[i]
            if aio is not None:
                if ain['initialized']:
                    aio.set_disabled(False)
                    ain['voltage'] = aio.get_value()
                elif aout['initialized']:
                    aio.set_value(aout['voltage'])
        
        # digital module
        for i, ch in enumerate(hal_data['dio']):
            dio = self.dio[i]
            if dio is not None:
                if not ch['initialized']:
                    dio.set_disabled()
                else:
                    # determine which one changed, and set the appropriate one
                    ret = dio.sync_value(ch['value'])
                    if ret is not None:
                        ch['value'] = ret
        
        for i, ch in enumerate(hal_data['pwm']):
            pwm = self.pwm[i]
            if pwm is not None:
                pwm.set_value(ch['value'])
                
        for i, ch in enumerate(hal_data['relay']):
            relay = self.relays[i]
            if relay is not None:
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
                sol.set_value(ch['value'])
        
        # CAN        
        for k, (motor, fl, rl, mode_lbl_txt, enc_txt, analog_txt, pwm_txt) in self.can.items():
            can = hal_data['CAN'][k]
            mode = can['mode_select']
            mode_lbl_txt.set(self.can_mode_map[mode])
            #change how output works based on control mode
            if   mode == tsrxc.kMode_DutyCycle :  
                #based on the fact that the vbus has 1023 steps
                motor.set_value(can['value']/1023)
                
            elif mode == tsrxc.kMode_VoltCompen:
                #assume voltage is 12 divide by muliplier in cantalon code (256)
                motor.set_value(can['value']/12/256)
                
            elif mode == tsrxc.kMode_SlaveFollower:
                #follow the value of the motor value is equal too
                motor.set_value(self.can[can['value']][0].get_value())
            #
            # currently other control modes are not correctly implemented
            #
            else:
                motor.set_value(can['value'])
                
            enc_txt.set('E: %s' % can['enc_position'])
            analog_txt.set('A: %s' % can['analog_in_position'])
            pwm_txt.set('P: %s' % can['pulse_width_position'])
            
            ret = fl.sync_value(can['limit_switch_closed_for'])
            if ret is not None:
                can['limit_switch_closed_for'] = ret
                
            ret = rl.sync_value(can['limit_switch_closed_rev'])
            if ret is not None:
                can['limit_switch_closed_rev'] = ret 
        
        
        # joystick/driver station
        #sticks = _core.DriverStation.GetInstance().sticks
        #stick_buttons = _core.DriverStation.GetInstance().stick_buttons
        
        for i, (axes, buttons, povs) in enumerate(self.joysticks):
            joy = hal_data['joysticks'][i]
            jaxes = joy['axes']
            for j, ax in enumerate(axes):
                jaxes[j] = ax.get_value()
        
            jbuttons = joy['buttons']
            for j, (ck, var) in enumerate(buttons):
                jbuttons[j+1]  = True if var.get() else False
                
            jpovs = joy['povs']
            for j, pov in enumerate(povs):
                jpovs[j] = int(pov.get_value())
                
        self.field.update_widgets()
        
        tm = self.fake_time.get()
        mode_tm = tm - self.mode_start_tm
        
        self.status.config(text="Time: %.03f mode, %.03f total" % (mode_tm, tm))
            
    
        
    def set_tooltip(self, widget, cat, idx):
        
        tooltip = self.config_obj['pyfrc'][cat].get(str(idx))
        if tooltip is not None:
            Tooltip.create(widget, tooltip)
            
    def set_joy_tooltip(self, widget, idx, typ, idx2):
        tooltip = self.config_obj['pyfrc']['joysticks'][str(idx)][typ].get(str(idx2))
        if tooltip is not None:
            Tooltip.create(widget, tooltip)
            
    def on_auton_choices(self, choices):
        self.autobox['values'] = choices[:]
    
    def on_auton_selection(self, selection):
        self.autobox.set(selection)
        
    def on_auton_selected(self, e):
        self.auton_ctrl.setSelected(self.autobox.get())
            
    def on_robot_mode_change(self, mode):
        self.mode.set(mode)
        
        self.mode_start_tm = self.fake_time.get()
        
        # this is not strictly true... a robot can actually receive joystick
        # commands from the driver station in disabled mode. However, most 
        # people aren't going to use that functionality... 
        controls_disabled = False if mode == self.manager.MODE_OPERATOR_CONTROL else True 
        state = tk.DISABLED if controls_disabled else tk.NORMAL
        
        for axes, buttons, povs in self.joysticks:
            for axis in axes:
                axis.set_disabled(disabled=controls_disabled)
            for ck, var in buttons:
                ck.config(state=state)
            for pov in povs:
                pov.set_disabled(disabled=controls_disabled)
        
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
        
        