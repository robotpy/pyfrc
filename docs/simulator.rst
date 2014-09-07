robot simulator
===============

The pyfrc robot simulator allows very simplistic simulation of your code
in real time and displays the results in a (ugly) user interface. To run
the simulator, run your robot.py with the following arguments:

    $ python3 robot.py sim
    
If you wish to run so that your simulator can connect to the SmartDashboard,
if you have pynetworktables installed you can run the following:

    $ python3 robot.py netsim

Or you can use this instead:

    $ python3 robot.py sim --enable-pynetworktables

As there is interest, I will add more features to the simulator. Please feel
free to improve it and submit pull requests!

Adding custom tooltips to motors/sensors
----------------------------------------

If you move the mouse over the motors/sensors in the simulator user interface,
you will notice that tooltips are shown which show which type of object is
using the slot. pyfrc will now read the 'label' attribute from each object,
and if present it will display that as the tooltip instead. For example:

    motor = wpilib.Jaguar(1)
    motor.label = 'whatzit motor'

This does not affect operation on the robot, as RobotPy will just ignore
the extra attribute.


Robot 'physics model'
---------------------

pyfrc now supports a simplistic custom physics model implementations for
simulation and testing support. It can be as simple or complex as you want
to make it. Hopefully in the future we will be adding helper functions to
make this a lot easier to do.

The idea here is you provide a simulation object that overrides specific
pieces of WPILib, and modifies motors/sensors accordingly depending on the
state of the simulation. An example of this would be measuring a motor
moving for a set period of time, and then changing a limit switch to turn 
on after that period of time. This can help you do more complex simulations
of your robot code without too much extra effort.

By default, pyfrc doesn't modify any of your inputs/outputs without being
told to do so by your code or the simulation GUI. 

See samples/physics for more details. The API has changed a bit as of 
pyfrc 2014.7.0

