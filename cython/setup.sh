#!/usr/bin/env bash

svn checkout https://hevc.hhi.fraunhofer.de/svn/svn_HEVCSoftware/tags/HM-9.2/ ../hm-9.2
cd ../hm-9.2
#patch -p0 < ../cython/cython-hm-9.1.diff
cd ./build/linux
make
cd ../../../cython

python setup.py build_ext --inplace
