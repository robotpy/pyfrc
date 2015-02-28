Robot Simulator
===============

The pyfrc robot simulator allows very simplistic simulation of your code
in real time and displays the results in a (ugly) user interface. To run
the simulator, run your robot.py with the following arguments:

.. code-block:: sh

    Windows:   py robot.py sim
    
    Linux/OSX: python3 robot.py sim

As there is interest, I will add more features to the simulator. Please feel
free to improve it and submit pull requests!

A new feature as of version 2014.7.0 is the addition of showing the robot's
simulated motion on a miniature field in the UI. This feature is really useful
for early testing of autonomous movements.

.. note:: For this to work, you must implement a physics module (it's a lot 
   easier than it sounds!). Helper functions are provided to calculate robot
   position for common drivetrain types (see below for details). There are
   samples provided in pyfrc for each supported drivetrain type.

..  Adding custom tooltips to motors/sensors (doesn't work in 2015!)
	
	If you move the mouse over the motors/sensors in the simulator user interface,
	you will notice that tooltips are shown which show which type of object is
	using the slot. pyfrc will now read the 'label' attribute from each object,
	and if present it will display that as the tooltip instead. For example::
	
	    motor = wpilib.Jaguar(1)
	    motor.label = 'whatzit motor'
	
	This does not affect operation on the robot, as RobotPy will just ignore
	the extra attribute.

.. _smartdashboard:

Communicating with SmartDashboard
---------------------------------

If you have `pynetworktables <https://github.com/robotpy/pynetworktables>`_
installed, the simulator can be used to communicate with the SmartDashboard or
other NetworkTables clients. As of 2015, nothing special is required, just
run it the way that you would normally run the simulator.

.. code-block:: sh

    Windows: py robot.py sim
    
    Linux/OSX: python3 robot.py sim

For this to work, you need to tell SmartDashboard to connect to the IP address
that your simulator is listening on (typically this is 127.0.0.1). Using
the original SmartDashboard, you need to launch the jar using the following
command:

.. code-block:: sh

  $ javac -jar SmartDashboard.jar ip 127.0.0.1

If you are using the SFX dashboard, there is a configuration option that you 
can tweak to get it to connect to a different IP. You can also launch it from
the command line using the following command:

.. code-block:: sh

  $ javac -jar sfx.jar 127.0.0.1


Robot 'physics model'
---------------------

.. automodule:: pyfrc.physics.core
   :members:

Drivetrain support
------------------

.. automodule:: pyfrc.physics.drivetrains
   :members:
