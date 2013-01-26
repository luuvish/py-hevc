# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/SEI.py
    HM 9.1 Python Implementation
"""


class SEI(object):

    BUFFERING_PERIOD       = 0
    PICTURE_TIMING         = 1
    USER_DATA_UNREGISTERED = 5
    RECOVERY_POINT         = 6
    DISPLAY_ORIENTATION    = 47
    ACTIVE_PARAMETER_SETS  = 130
    TEMPORAL_LEVEL0_INDEX  = 132
    DECODED_PICTURE_HASH   = 133

    def payloadType(self): pass

class SEIuserDataUnregistered(SEI):

    def __init__(self):
        self.uuid_iso_iec_11578 = 16 * [0]
        self.userDataLength     = 0
        self.userData           = None

    def __del__(self):
        if self.userData != None:
            del self.userData

    def payloadType(self):
        return SEI.USER_DATA_UNREGISTERED

class SEIDecodedPictureHash(SEI):

    MD5      = 0
    CRC      = 1
    CHECKSUM = 2
    RESERVED = 3

    def __init__(self):
        self.method = 0
        self.digest = [[0 for j in xrange(16)] for x in xrange(3)]

    def payloadType(self):
        return SEI.DECODED_PICTURE_HASH

class SEIActiveParameterSets(SEI):

    def __init__(self):
        self.activeVPSId            = 0
        self.activeSPSIdPresentFlag = 1
        self.activeSeqParamSetId    = 0

    def payloadType(self):
        return SEI.ACTIVE_PARAMETER_SETS

class SEIBufferingPeriod(SEI):

    def __init__(self):
        self.m_seqParameterSetId               = 0
        self.m_altCpbParamsPresentFlag         = 0
        self.m_initialCpbRemovalDelay          = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_initialCpbRemovalDelayOffset    = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_initialAltCpbRemovalDelay       = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_initialAltCpbRemovalDelayOffset = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_sps                             = None

    def payloadType(self):
        return SEI.BUFFERING_PERIOD

class SEIPictureTiming(SEI):

    def __init__(self):
        self.m_auCpbRemovalDelay             = 0
        self.m_picDpbOutputDelay             = 0
        self.m_numDecodingUnitsMinus1        = 0
        self.m_duCommonCpbRemovalDelayFlag   = 0
        self.m_duCommonCpbRemovalDelayMinus1 = 0
        self.m_numNalusInDuMinus1            = None
        self.m_duCpbRemovalDelayMinus1       = None
        self.m_sps                           = None

    def __del__(self):
        if self.m_numNalusInDuMinus1 != None:
            del self.m_numNalusInDuMinus1
        if self.m_duCpbRemovalDelayMinus1 != None:
            del self.m_duCpbRemovalDelayMinus1

    def payloadType(self):
        return SEI.PICTURE_TIMING

class SEIRecoveryPoint(SEI):

    def __init__(self):
        self.m_recoveryPocCnt    = 0
        self.m_exactMatchingFlag = 0
        self.m_brokenLinkFlag    = 0

    def payloadType(self):
        return SEI.RECOVERY_POINT

class SEIDisplayOrientation(SEI):

    def __init__(self):
        self.cancelFlag            = True
        self.horFlip               = False
        self.verFlip               = False

        self.anticlockwiseRotation = 0
        self.repetitionPeriod      = 1
        self.extensionFlag         = False

    def payloadType(self):
        return SEI.DISPLAY_ORIENTATION

class SEITemporalLevel0Index(SEI):

    def __init__(self):
        self.tl0Idx = 0
        self.rapIdx = 0

    def payloadType(self):
        return SEI.TEMPORAL_LEVEL0_INDEX


class SEImessages(object):

    def __init__(self):
        self.user_data_unregistered = None
        self.active_parameter_sets  = None
        self.picture_digest         = None
        self.buffering_period       = None
        self.picture_timing         = None
        self.m_pSPS                 = None
        self.recovery_point         = None
        self.display_orientation    = None
        self.temporal_level0_index  = None

    def __del__(self):
        if self.user_data_unregistered != None:
            del self.user_data_unregistered
        if self.active_parameter_sets != None:
            del self.active_parameter_sets
        if self.picture_digest != None:
            del self.picture_digest
        if self.buffering_period != None:
            del self.buffering_period
        if self.picture_timing != None:
            del self.picture_timing
        if self.recovery_point != None:
            del self.recovery_point
        if self.display_orientation != None:
            del self.display_orientation
        if self.temporal_level0_index != None:
            del self.temporal_level0_index
