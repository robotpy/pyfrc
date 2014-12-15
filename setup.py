#!/usr/bin/env python

from os.path import join, dirname
from distutils.core import setup

setup_dir = dirname(__file__)

packages = [
    'pyfrc',
    'pyfrc.mains',
    'pyfrc.tests',
    'pyfrc.support',
]

def get_version():
    g = {}
    with open(join(dirname(__file__), 'lib', 'pyfrc', 'version.py'), 'r') as fp:
        exec(fp.read(), g)
    return g['__version__']

with open(join(setup_dir, 'requirements.txt')) as requirements_file:
    install_requires = requirements_file.readlines()

with open(join(dirname(__file__), 'README.md'), 'r') as readme_file:
    long_description = readme_file.read()

setup(name='pyfrc',
      version=get_version(),
      description='Development tools library for python interpreter used for the FIRST Robotics Competition',
      long_description=long_description,
      author='Dustin Spicuzza, Sam Rosenblum',
      author_email='robotpy@googlegroups.com',
      url='https://github.com/robotpy/pyfrc',
      license='Apache 2.0',
      packages=packages,
      package_dir={'': 'lib'},
      install_requires=install_requires,
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development'
        ],
      entry_points={'robotpy': [ 'test = pyfrc.mains.pyfrc_test:PyFrcTest']
                    }
)



