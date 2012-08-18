#!/usr/bin/env python

import sys
from time import clock

from .TAppEncTop import TAppEncTop

CLOCKS_PER_SEC = 1

NV_VERSION = "8.0" # Current software version

__GNUC__ = 4
__GNUC_MINOR__ = 2
__GNUC_PATCHLEVEL__ = 1

NVM_COMPILEDBY = "[GCC %d.%d.%d]" % (__GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__)
NVM_ONOS = "[Mac OS X]"
NVM_BITS = "[%d bit] " % 64 # used for checking 64-bit O/S


def TAppEncoder(argv):
    cTAppEncTop = TAppEncTop()

    # print information
    sys.stdout.write("\n")
    sys.stdout.write("HM software: Encoder Version [%s]" % NV_VERSION)
    sys.stdout.write(NVM_ONOS)
    sys.stdout.write(NVM_COMPILEDBY)
    sys.stdout.write(NVM_BITS)
    sys.stdout.write("\n")

    # create application encoder class
    cTAppEncTop.create()

    # parse configuration
    if not cTAppEncTop.parseCfg(argv):
        cTAppEncTop.destroy()
        return False

    # starting time
    lBefore = clock()

    # call encoding function
    cTAppEncTop.encode()

    # ending time
    dResult = (clock()-lBefore) / CLOCKS_PER_SEC
    print("\n Total Time: %12.3f sec.\n" % dResult)

    # destroy application encoder class
    cTAppEncTop.destroy()

    return True
