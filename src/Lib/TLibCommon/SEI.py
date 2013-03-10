# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/SEI.py
    HM 10.0 Python Implementation
"""


from ... import VectorInt


class SEI(object):

    BUFFERING_PERIOD                     = 0
    PICTURE_TIMING                       = 1
    PAN_SCAN_RECT                        = 2
    FILLER_PAYLOAD                       = 3
    USER_DATA_REGISTERED_ITU_T_T35       = 4
    USER_DATA_UNREGISTERED               = 5
    RECOVERY_POINT                       = 6
    SCENE_INFO                           = 9
    FULL_FRAME_SNAPSHOT                  = 15
    PROGRESSIVE_REFINEMENT_SEGMENT_START = 16
    PROGRESSIVE_REFINEMENT_SEGMENT_END   = 17
    FILM_GRAIN_CHARACTERISTICS           = 19
    POST_FILTER_HINT                     = 22
    TONE_MAPPING_INFO                    = 23
    FRAME_PACKING                        = 45
    DISPLAY_ORIENTATION                  = 47
    SOP_DESCRIPTION                      = 128
    ACTIVE_PARAMETER_SETS                = 129
    DECODING_UNIT_INFO                   = 130
    TEMPORAL_LEVEL0_INDEX                = 131
    DECODED_PICTURE_HASH                 = 132
    SCALABLE_NESTING                     = 133
    REGION_REFRESH_INFO                  = 134

    def payloadType(self):
        pass


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
        self.m_fullRandomAccessFlag = False
        self.m_noParamSetUpdateFlag = False
        self.numSpsIdsMinus1        = 0
        self.activeSeqParamSetId    = VectorInt()

    def payloadType(self):
        return SEI.ACTIVE_PARAMETER_SETS


class SEIBufferingPeriod(SEI):

    def __init__(self):
        self.m_bpSeqParameterSetId             = 0
        self.m_rapCpbParamsPresentFlag         = False
        self.m_cpbDelayOffset                  = 0
        self.m_dpbDelayOffset                  = 0
        self.m_initialCpbRemovalDelay          = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_initialCpbRemovalDelayOffset    = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_initialAltCpbRemovalDelay       = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_initialAltCpbRemovalDelayOffset = [[0 for j in xrange(2)] for x in xrange(MAX_CPB_CNT)]
        self.m_concatenationFlag               = False
        self.m_auCpbRemovalDelayDelta          = 0

    def payloadType(self):
        return SEI.BUFFERING_PERIOD


class SEIPictureTiming(SEI):

    def __init__(self):
        self.m_picStruct                     = 0
        self.m_sourceScanType                = 0
        self.m_duplicateFlag                 = False

        self.m_auCpbRemovalDelay             = 0
        self.m_picDpbOutputDelay             = 0
        self.m_picDpbOutputDuDelay           = 0
        self.m_numDecodingUnitsMinus1        = 0
        self.m_duCommonCpbRemovalDelayFlag   = 0
        self.m_duCommonCpbRemovalDelayMinus1 = 0
        self.m_numNalusInDuMinus1            = None
        self.m_duCpbRemovalDelayMinus1       = None

    def __del__(self):
        if self.m_numNalusInDuMinus1 != None:
            del self.m_numNalusInDuMinus1
        if self.m_duCpbRemovalDelayMinus1 != None:
            del self.m_duCpbRemovalDelayMinus1

    def payloadType(self):
        return SEI.PICTURE_TIMING


class SEIDecodingUnitInfo(SEI):

    def __init__(self):
        self.m_decodingUnitIdx             = 0
        self.m_duSptCpbRemovalDelay        = 0
        self.m_dpbOutputDuDelayPresentFlag = False
        self.m_picSptDpbOutputDuDelay      = 0

    def payloadType(self):
        return SEI.DECODING_UNIT_INFO


class SEIRecoveryPoint(SEI):

    def __init__(self):
        self.m_recoveryPocCnt    = 0
        self.m_exactMatchingFlag = 0
        self.m_brokenLinkFlag    = 0

    def payloadType(self):
        return SEI.RECOVERY_POINT


class SEIFramePacking(SEI):

    def __init__(self):
        self.m_arrangementId              = 0
        self.m_arrangementCancelFlag      = False
        self.m_arrangementType            = 0
        self.m_quincunxSamplingFlag       = False
        self.m_contentInterpretationType  = 0
        self.m_spatialFlippingFlag        = False
        self.m_frame0FlippingFlag         = False
        self.m_fieldViewsFlag             = False
        self.m_currentFrameIsFrame0Flag   = False
        self.m_frame0SelfContainedFlag    = False
        self.m_frame1SelfContainedFlag    = False
        self.m_frame0GridPositionX        = 0
        self.m_frame0GridPositionY        = 0
        self.m_frame1GridPositionX        = 0
        self.m_frame1GridPositionY        = 0
        self.m_arrangementReservedByte    = 0
        self.m_arrangementPersistenceFlag = False
        self.m_upsampledAspectRatio       = False

    def payloadType(self):
        return SEI.FRAME_PACKING


class SEIDisplayOrientation(SEI):

    def __init__(self):
        self.cancelFlag            = True
        self.horFlip               = False
        self.verFlip               = False

        self.anticlockwiseRotation = 0
        self.persistenceFlag       = False
        self.extensionFlag         = False

    def payloadType(self):
        return SEI.DISPLAY_ORIENTATION


class SEITemporalLevel0Index(SEI):

    def __init__(self):
        self.tl0Idx = 0
        self.rapIdx = 0

    def payloadType(self):
        return SEI.TEMPORAL_LEVEL0_INDEX


class SEIGradualDecodingRefreshInfo(SEI):

    def __init__(self):
        self.m_gdrForegroundFlag = False

    def payloadType(self):
        return SEI.REGION_REFRESH_INFO


def getSeisByType(seiList, seiType):
    result = []

    for it in seiList[:]:
        if it.payloadType() == seiType:
            result.append(it)
    return result


def extractSeisByType(seiList, seiType):
    result = []

    for it in seiList[:]:
        if it.payloadType() == seiType:
            result.append(it)
            seiList.remove(it)
    return result


def deleteSEIs(seiList):
    for it in seiList[:]:
        del it
    seiList[:] = []
