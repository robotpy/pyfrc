pyfrc - RobotPy development library helper
==========================================

[![Build Status](https://travis-ci.org/robotpy/pyfrc.svg)](https://travis-ci.org/robotpy/pyfrc)

pyfrc is a python 3 library designed to make developing code for RobotPy (the
Python interpreter for the FIRST Robotics Competition) easier.

This library contains a few primary parts:

* A built-in uploader that will upload your robot code to the robot
* An implementation of wpilib that allows you to run robot code on your
  computer without a cRio

  This is a library designed to emulate parts of WPILib so you can more easily
  do unit testing of your robot code on any platform that supports python3,
  without having to have a cRio around for testing. 

    NOTE: This is not a complete implementation of WPILib. Add more things
    as needed, and submit patches! :) 
    
* Integration with the py.test testing tool to allow you to easily write unit
  tests for your robot code.
* A robot simulator tool which allows you to run your code in (vaguely) real
  time and get simple feedback via a tk-based UI
  
Documentation
=============

For usage, detailed installation information, and other notes, please see
our documentation at http://pyfrc.readthedocs.org/en/latest/

Quick Install + Demo
====================

If you have python3 and pip installed, then do:

    pip3 install pyfrc

Once this is done, you can run a quick demo by running:

    cd samples/physics/src/
    python3 robot.py sim


Contributing new changes
========================

pyfrc is intended to be a project that all members of the FIRST community can
quickly and easily contribute to. If you find a bug, or have an idea that you
think others can use:

1. [Fork this git repository](https://github.com/robotpy/robotpy/fork) to your github account
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push -u origin my-new-feature`)
5. Create new Pull Request on github


Authors
=======

Dustin Spicuzza (dustin@virtualroadside.com)

pyfrc is originally derived from (and supercedes) fake_wpilib, which was
developed with contributions from Sam Rosenblum and Team 2423. 
