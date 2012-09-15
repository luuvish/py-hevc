# -*- coding: utf-8 -*-
"""
    module : src/App/TAppDecoder/TAppDecoder.py
    HM 8.0 Python Implementation
"""

import sys

from ... import clock, CLOCKS_PER_SEC
from ... import cvar
from ... import TAppDecTop

from ...Lib.TLibCommon.CommonDef import (
    NV_VERSION,
    NVM_COMPILEDBY,
    NVM_ONOS,
    NVM_BITS
)


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
