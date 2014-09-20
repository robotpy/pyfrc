
#
# Requires matplotlib
#

import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler

from matplotlib.animation import Animation

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import tkinter as Tk


from ..wpilib._wpilib import _core, _fake_time

class UiGraph(object):
    
    # This just has to be a separate window I think
    
    # need to put everything into a json dictionary, for preparation for HTML
    # -> best way to do this is probably define a giant structure, and
    #    just do all operations on that structure?
    
    # define a queue for robots to put their stuff on, and we only redraw it periodically

    # change geometry after hide/show
    # axis has 
    
    # queue: use numpy.roll
    
    def _get_values(self):
        
        with _core._WPILibObject._sim_lock:
        
            for i, ch in enumerate(_core.AnalogModule._channels):
                pass
            
            for i, ch in enumerate(_core.DigitalModule._io):
                pass
                
            for i, ch in enumerate(_core.DigitalModule._pwm):
                if ch is not None:
                    ch.value
                
            for i, ch in enumerate(_core.DigitalModule._relays):
                pass
                
            for i, ch in enumerate(_core.Solenoid._channels):
                pass
                
            for k, (motor, fl, rl) in self.can.items():
                pass
                
            # skip joysticks for now
            
            #
            #sticks = _core.DriverStation.GetInstance().sticks
            #stick_buttons = _core.DriverStation.GetInstance().stick_buttons
            #
            
        # the y axis is fake_time
        # the x axis is whatever the thing is    
        
        pass

    def __init__(self, root):
        
        
        
        self.window = Tk.Toplevel(root)
        self.window.wm_title("Graph")

        # Three subplots sharing both x/y axes
        #f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=True)
        #ax1.plot(x, y)
        #ax1.set_title('Sharing both axes')
        #ax2.scatter(x, y)
        #ax3.scatter(x, 2 * y ** 2 - 1, color='r')
        # Fine-tune figure; make subplots close to each other and hide x ticks for
        # all but bottom plot.
        #f.subplots_adjust(hspace=0)
        #plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)

        # This must be the data    
        f = Figure(figsize=(5,4), dpi=100)
        a = f.add_subplot(111)
        
        t = arange(0.0,3.0,0.01)
        s = sin(2*pi*t)
        
        a.plot(t,s)
    
        # This is the stuffs.
    
        # a tk.DrawingArea
        canvas = FigureCanvasTkAgg(f, master=self.window)
        canvas.show()
        canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        
        toolbar = NavigationToolbar2TkAgg( canvas, self.window )
        toolbar.update()
        canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        def on_key_event(event):
            print('you pressed %s'%event.key)
            key_press_handler(event, canvas, toolbar)
    
        canvas.mpl_connect('key_press_event', on_key_event)
