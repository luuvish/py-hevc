#!/usr/bin/env bash

svn checkout https://hevc.hhi.fraunhofer.de/svn/svn_HEVCSoftware/tags/HM-10.0/ ../hm-10.0
cd ../hm-10.0
patch -p0 < ../swig/swig-hm-10.0.diff
cd ./build/linux
make
cd ../../../swig

python setup.py build_ext --inplace
