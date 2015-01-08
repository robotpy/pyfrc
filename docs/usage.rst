Usage
=====

As of 2015, pyfrc integrates into RobotPy WPILib. Once pyfrc is installed,
you can directly run your robot.py file and use the pyfrc files from there.
Use the --help command to discover the various features installed::

	Windows:   py robot.py --help
	
	Linux/OSX: python3 robot.py --help

SmartDashboard/NetworkTables support
------------------------------------

The pyfrc simulator will automatically enable SmartDashboard/Networktables
support. When running unit tests, NetworkTables will be switched to test
mode and will not be able to communicate externally.


Deploying code to the robot
---------------------------

This command will first run any unit tests on your robot code, and if they
pass then it will upload the robot code to the cRio. Running the tests is
really important, so you can catch errors in your code before you run it 
on the robot.

.. code-block:: sh

    Windows:   py robot.py deploy
    
    Linux/OSX: python3 robot.py deploy
    
A really useful option is ``--nc``, which will cause the deploy command to show
your program's console output, by launching a netconsole listener.

.. code-block:: sh

    Windows:   py robot.py deploy --nc
    
    Linux/OSX: python3 robot.py deploy --nc

Of course, maybe you really need to upload the code, and don't care about the
tests. That's OK, you can still upload code to the robot:

.. code-block:: sh

    Windows: py robot.py deploy --skip-tests

    Linux/OSX: python3 robot.py deploy --skip-tests

.. note:: When the code is uploaded to the robot, the following steps occur:

		  * The directory containing ``robot.py`` is recursively copied to the
		    the directory ``/home/lvuser/py``
		  * The files ``robotCommand`` and ``robotDebugCommand`` are created
		  * ``/usr/local/frc/bin/frcKillRobot.sh -t -r`` is called, which
		    causes any existing robot code to be killed, and the new code is
		    launched
		    
		  These steps are compatible with what C++/Java does when deployed by
		  eclipse, so you should be able to seamlessly switch between python
		  and other FRC languages! 

Running an interactive robot simulation
---------------------------------------

The simple robot simulation available in pyfrc will let you interact with your
robot via a simple UI that shows the status of all your motors and sensors,
and lets you give it input too. There is also a field simulator that will show
the position of your robot on a simulated field.

.. code-block:: sh

    Windows:   py robot.py sim
    
    Linux/OSX: python3 robot.py sim

For more details, see :doc:`simulator`

Running unit tests
------------------

.. code-block:: sh

    Windows:   py robot.py test
    
    Linux/OSX: python3 robot.py test

For more details, see :doc:`testing`
