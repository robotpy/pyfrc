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


Uploading code to the robot
---------------------------

This command will first run any unit tests on your robot code, and if they
pass then it will upload the robot code to the cRio. Running the tests is
really important, so you can catch errors in your code before you run it 
on the robot.

.. code-block:: sh

    Windows:   py robot.py upload
    
    Linux/OSX: python3 robot.py upload

Of course, maybe you really need to upload the code, and don't care about the
tests. That's OK, you can still upload code to the robot:

.. code-block:: sh

    Windows: py robot.py upload --skip-tests

    Linux/OSX: python3 robot.py upload --skip-tests

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
