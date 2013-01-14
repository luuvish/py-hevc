#!/usr/bin/env bash

svn checkout https://hevc.hhi.fraunhofer.de/svn/svn_HEVCSoftware/tags/HM-9.1/ ../hm-9.1
cd ../hm-9.1
patch -p0 < ../swig/swig-hm-9.1.diff
cd ./build/linux
make
cd ../../../swig

python setup.py build_ext --inplace
