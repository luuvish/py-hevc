#!/usr/bin/env python

import sys
sys.path.insert(0, '..')

from time import clock
from swig.hevc import ArrayUChar
from src.Lib.TLibCommon.array import array

start = clock()

a = 1000 * [0]

for i in xrange(1000):
	for j in xrange(100):
		a[0:i] = a[i-1:-1:-1]

print "a[0:i] time = %d" % (clock() - start)

start = clock()

b = 1000 * [0]

for i in xrange(1000):
	for j in xrange(100):
		for k in xrange(i):
			b[k] = b[i-k]

print "* a[i] time = %d" % (clock() - start)
