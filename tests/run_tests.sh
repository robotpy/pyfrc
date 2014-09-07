#!/bin/bash

cd `dirname $0`

#
# Runs tests on pyfrc components
#

PYTHONPATH="../lib" py.test $@ || exit $?

#
# Runs included tests on all samples 
#

pushd ../samples

for dir in `ls`; do
	if [ -d "$dir" ]; then
		pushd $dir/src
		python3 robot.py coverage test || exit $?
		popd
	fi
done

