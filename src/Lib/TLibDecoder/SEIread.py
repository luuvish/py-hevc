# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/SEIread.py
    HM 8.0 Python Implementation
"""

from ..TLibCommon.SEI import SEI, SEIuserDataUnregistered, SEIpictureDigest


def parseSEIuserDataUnregistered(bs, sei, payloadSize):
    assert(payloadSize >= 16)
    for i in xrange(16):
        sei.uuid_iso_iec_11578[i] = bs.read(8)

    sei.userDataLength = payloadSize - 16
    if sei.userDataLength == 0:
        sei.userData = None
        return

    sei.userData = sei.userDataLength * [0]
    for i in xrange(sei.userDataLength):
        sei.userData[i] = bs.read(8)

def parseSEIpictureDigest(bs, sei, payloadSize):
    numChar = 0

    sei.method = bs.read(8)
    if SEIpictureDigest.MD5 == sei.method:
        numChar = 16
    elif SEIpictureDigest.CRC == sei.method:
        numChar = 2
    elif SEIpictureDigest.CHECKSUM == sei.method:
        numChar = 4

    for yuvIdx in xrange(3):
        for i in xrange(numChar):
            sei.digest[yuvIdx][i] = bs.read(8)

def parseSEImessage(bs, seis):
    payloadType = 0
    byte = 0xff
    while byte == 0xff:
        byte = bs.read(8)
        payloadType += byte

    payloadSize = 0
    byte = 0xff
    while byte == 0xff:
        byte = bs.read(8)
        payloadSize += byte

    if payloadType == SEI.USER_DATA_UNREGISTERED:
        seis.user_data_unregistered = SEIuserDataUnregistered()
        parseSEIuserDataUnregistered(bs, seis.user_data_unregistered, payloadSize)
    elif payloadType == SEI.PICTURE_DIGEST:
        seis.picture_digest = SEIpictureDigest()
        parseSEIpictureDigest(bs, seis.picture_digest, payloadSize)
    else:
        assert(not "Unhandled SEI message")
