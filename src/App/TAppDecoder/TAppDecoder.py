# -*- coding: utf-8 -*-
"""
    module : src/App/TAppDecoder/TAppDecoder.py
    HM 8.0 Python Implementation
"""

import sys
from time import clock

use_swig = False
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import TAppDecTop
else:
    from .TAppDecTop import TAppDecTop
    class CVar(object):
        def __init__(self):
            self.g_md5_mismatch = False
    cvar = CVar()

CLOCKS_PER_SEC = 1

NV_VERSION = "8.0" # Current software version

__GNUC__ = 4
__GNUC_MINOR__ = 2
__GNUC_PATCHLEVEL__ = 1

NVM_COMPILEDBY = "[GCC %d.%d.%d]" % (__GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__)
NVM_ONOS = "[Mac OS X]"
NVM_BITS = "[%d bit] " % 64 # used for checking 64-bit O/S


cvar.g_md5_mismatch = False

def TAppDecoder(argv):
    cTAppDecTop = TAppDecTop()

    # print information
    sys.stdout.write("\n")
    sys.stdout.write("HM software: Decoder Version [%s]" % NV_VERSION)
    sys.stdout.write(NVM_ONOS)
    sys.stdout.write(NVM_COMPILEDBY)
    sys.stdout.write(NVM_BITS)
    sys.stdout.write("\n")

    # create application decoder class
    cTAppDecTop.create()

    # parse configuration
    if not cTAppDecTop.parseCfg(argv):
        cTAppDecTop.destroy()
        return False

    # starting time
    lBefore = clock()

    # call decoding function
    cTAppDecTop.decode()

    if cvar.g_md5_mismatch:
        sys.stdout.write("\n\n***ERROR*** A decoding mismatch occured: signalled md5sum does not match\n")

    # ending time
    dResult = (clock()-lBefore) / CLOCKS_PER_SEC
    sys.stdout.write("\n Total Time: %12.3f sec.\n" % dResult)

    # destroy application decoder class
    cTAppDecTop.destroy()

    return False if cvar.g_md5_mismatch else True
