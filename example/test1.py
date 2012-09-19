#!/usr/bin/env python

import sys
sys.path.insert(0, '..')

from time import clock
from swig.hevc import ArrayUChar

start = clock()

a = ArrayUChar(1000)

for i in xrange(1000):
	for j in xrange(1000):
		for k in xrange(10):
			a[i], a[j] = a[j], a[k]

print "ArrayUChar time = %d" % (clock() - start)

start = clock()

b = bytearray(1000)

for i in xrange(1000):
	for j in xrange(1000):
		for k in xrange(10):
			b[i], b[j] = b[j], b[k]

print "ByteArray time = %d" % (clock() - start)
