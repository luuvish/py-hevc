# -*- coding: utf-8 -*-
"""
    module : src/App/TAppEncoder/TAppEncoder.py
    HM 10.0 Python Implementation
"""

import sys

from ... import clock, CLOCKS_PER_SEC
from ... import TAppEncTop

from ...Lib.TLibCommon.CommonDef import (
    NV_VERSION,
    NVM_COMPILEDBY,
    NVM_ONOS,
    NVM_BITS
)


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
    try:
        if not cTAppEncTop.parseCfg(argv):
            cTAppEncTop.destroy()
            return False
    except error:
        sys.stderr.write("Error parsing option \"%r\" with argument \"%r\"\n." % (error, error))
        return False

    # starting time
    lBefore = clock()

    # call encoding function
    cTAppEncTop.encode()

    # ending time
    dResult = (clock()-lBefore) / CLOCKS_PER_SEC
    sys.stdout.write("\n Total Time: %12.3f sec.\n" % dResult)

    # destroy application encoder class
    cTAppEncTop.destroy()

    return True
