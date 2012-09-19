# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/SEI.py
    HM 8.0 Python Implementation
"""

class SEI(object):

    USER_DATA_UNREGISTERED = 5
    PICTURE_DIGEST         = 256


class SEIuserDataUnregistered(SEI):

    def __init__(self):
        self.uuid_iso_iec_11578 = 16 * [0]
        self.userDataLength = 0
        self.userData = None

    def __del__(self):
        if self.userData != None:
            del self.userData

    def payloadType(self):
        return USER_DATA_UNREGISTERED


class SEIpictureDigest(SEI):

    MD5      = 0
    CRC      = 1
    CHECKSUM = 2
    RESERVED = 3

    def __init__(self):
        self.method = 0
        self.digest = [[0 for j in xrange(16)] for x in xrange(3)]

    def payloadType(self):
        return PICTURE_DIGEST


class SEImessages(object):

    def __init__(self):
        self.user_data_unregistered = None
        self.picture_digest = None

    def __del__(self):
        if self.user_data_unregistered != None:
            del self.user_data_unregistered
        if self.picture_digest != None:
            del self.picture_digest
