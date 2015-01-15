Deploy robot code
=================

.. warning::
   
   If you used pyfrc 2015.0.x and uploaded code to your robot there was a
   critical bug that may prevent your robot from running robot programs.
   To fix this, please upgrade pyfrc to the latest version, and run the
   following command::
             
       Windows:    py -m pyfrc.robotpy.fixbug
             
       Linux/OSX:  python3 -m pyfrc.robotpy.fixbug
             
   Alternatively, you can ssh in as admin, and execute
   ``rm /var/local/natinst/log/FRC_UserProgram.log``.  

This command will first run any unit tests on your robot code, and if they
pass then it will upload the robot code to the cRio. Running the tests is
really important, so you can catch errors in your code before you run it 
on the robot.

.. code-block:: sh

    Windows:   py robot.py deploy
    
    Linux/OSX: python3 robot.py deploy
 
Note that when you run this command like that, you won't get any feedback from the robot whether your code actually worked or not. If you want to see the feedback from your robot, a really useful option is ``--nc``. This will cause the deploy command to show your program's console output, by launching a netconsole listener.

.. code-block:: sh

    Windows:   py robot.py deploy --nc
    
    Linux/OSX: python3 robot.py deploy --nc

Of course, maybe you really need to upload the code, and don't care about the
tests. That's OK, you can still upload code to the robot:

.. code-block:: sh

    Windows: py robot.py deploy --skip-tests

    Linux/OSX: python3 robot.py deploy --skip-tests

Troubleshooting
---------------

1. Make sure you have the latest version of pyfrc! Older versions **won't** work.
2. Read any error messages that pyfrc might give you. They might be useful. :)

Problem: pyfrc cannot connect to the robot, or appears to hang
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Can you ping your robot from the machine that you're deploying code from? If not, pyfrc isn't going to be able to connect to the robot either.
2. Try to ssh into your robot, using `PuTTY <http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html>`_ or the ``ssh`` command on Linux/OSX. The username to use is ``lvuser``, and the password is an empty string. If this doesn't work, pyfrc won't be able to copy files to your robot
3. If all of that works, it might just be that you typed the wrong hostname to connect to. There's a file called ``.deploy_cfg`` next to your ``robot.py`` that pyfrc created. Delete it, and try again.


Problem: I deploy successfully, but the driver station still shows 'No Robot Code'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Did you use the ``--nc`` option to the deploy command? Your code may have crashed, and the output should be visible on netconsole.
2. If you can't see any useful output there, then ssh into the robot and run ``ps -Af | grep python3``. If nothing shows up, it means your python code crashed and you'll need to debug it. Try running it manually on the robot using this command:: 
    
    python3 /home/lvuser/py/robot.py run

    

Internal details
----------------

When the code is uploaded to the robot, the following steps occur:

* SSH/sftp operations are performed as the 'lvuser' user (this is REALLY important!)
* The directory containing ``robot.py`` is recursively copied to the
the directory ``/home/lvuser/py``
* The files ``robotCommand`` and ``robotDebugCommand`` are created
* ``/usr/local/frc/bin/frcKillRobot.sh -t -r`` is called, which
causes any existing robot code to be killed, and the new code is
launched

These steps are compatible with what C++/Java does when deployed by eclipse,
so you should be able to seamlessly switch between python and other FRC
languages!

