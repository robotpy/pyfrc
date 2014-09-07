Installation
============

Via pip on Linux/OSX
--------------------

The easiest installation is by using pip. On a linux/OSX system that has pip
installed, just run the following command:

	$ pip3 install pyfrc

Via pip on Windows
------------------

On Windows, I recommend using pip-Win to install packages. Download it from:

	https://sites.google.com/site/pydatalog/python/pip-for-windows
	
Once you've downloaded it, run it to install pip, and run the following
command in its window:

	pip install pyfrc

Non-pip installation
--------------------

First, make sure that you have python 3 installed. pyfrc does not support
python 2.

You must have the following python packages installed:

* py.test (http://pytest.org/)

Once you have those installed, you can just install pyfrc the same way 
you would install most other python programs:

	$ python3 setup.py install
	
code coverage support
---------------------

If you wish to run code coverage testing, then you must install the following
package:

* coverage (https://pypi.python.org/pypi/coverage)

On linux, you can execute the following command:

    pip3 install coverage 

It requires a compiler to install from source, so if you're on Windows you
probably just want to download the binary from pypi and install that, instead
of trying to install from pip.
