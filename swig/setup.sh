#!/usr/bin/env bash

svn checkout https://hevc.hhi.fraunhofer.de/svn/svn_HEVCSoftware/tags/HM-9.2/ ../hm-9.2
cd ../hm-9.2
patch -p0 < ../swig/swig-hm-9.2.diff
cd ./build/linux
make
cd ../../../swig

python setup.py build_ext --inplace
