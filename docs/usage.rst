Usage
=====

This sections gives you an overview of the various commands that you can
execute on your robot code once pyfrc is installed.

Running pyfrc commands
----------------------

As of 2015, pyfrc integrates into RobotPy WPILib. When you want to execute
the pyfrc commands listed in this documentation, you just run your ``robot.py``
directly, and pass it command line arguments to tell it what to do. Typically
you will execute the code via a command prompt or Terminal, but tools
like IDLE, pydev, and pycharm all support executing your code from within
the IDE window.

Windows
~~~~~~~

On Windows, you will typically execute your robot code by opening up the
command prompt (cmd), changing directories to where your robot code is,
and then running this::

  py robot.py

Linux/OSX
~~~~~~~~~

On Linux/OSX, you will typically execute your robot code by opening up the
Terminal program, changing directories to where your robot code is, and
then running this::

  python3 robot.py

Command discovery
~~~~~~~~~~~~~~~~~

Once you know how to execute your code, you can execute various commands by
passing ``robot.py`` command line options. To discover the various features
that are installed, you can use the use the ``--help`` command::

	Windows:   py robot.py --help
	
	Linux/OSX: python3 robot.py --help


Deploying code to the robot
---------------------------

pyfrc makes it easy to deploy code to your robot!

.. code-block:: sh

    Windows:   py robot.py deploy
    
    Linux/OSX: python3 robot.py deploy

For more details and troubleshooting steps, see :doc:`deploy`.


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

SmartDashboard/NetworkTables support
------------------------------------

The pyfrc simulator will automatically enable SmartDashboard/Networktables
support. When running unit tests, NetworkTables will be switched to test
mode and will not be able to communicate externally.
