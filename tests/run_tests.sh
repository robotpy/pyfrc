#!/bin/bash

set -e
cd `dirname $0`

#
# Runs tests on pyfrc components
#

PYTHONPATH="../lib" py.test $@
#PYTHONPATH="../lib" python3 -m coverage run --source pyfrc -m pytest $@
#python3 -m coverage report -m

#
# Runs included tests on all samples 
#

pushd ../samples

for dir in `ls`; do
	if [ -d "$dir" ]; then
		pushd $dir/src
		python3 robot.py coverage test
		popd
	fi
done

