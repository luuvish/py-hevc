#!/usr/bin/env python

import sys
sys.path.insert(0, '..')
from time import clock

from swig.hevc import cvar
from swig.hevc import TAppEncTop

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


config_dir = '../../h265/binary'
stream_dir = '../../h265/binary'
output_dir = '.'
encode_opt = ('-c', config_dir+'/h265enc.cfg',
              '--SourceWidth=1920', '--SourceHeight=1080',
              '--IntraPeriod=32', '--GOPSize=8', '--FramesToBeEncoded=600', '--FrameRate=60',
              '--SEIpictureDigest=1',
              '--InputFile=%s' % (stream_dir+'/phantom.yuv'),
              '--BitstreamFile=%s' % (output_dir+'/phantom.265'))

TAppEncoder(['TAppEncoder'] + list(encode_opt))
