#!/usr/bin/env python

from ...Lib.TLibCommon.CommonDef import *
from ...Lib.TLibCommon.TComBitstream import TComBitstream

class NALUnit:

    def __init__(self, nalUnitType, nalRefFlag, temporalId=0):
        self.m_nalUnitType = nalUnitType
        self.m_nalRefFlag = nalRefFlag
        self.m_temporalId = temporalId

    def isSlice(self):
        return self.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLANT or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE_CRANT or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE_CRA or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE_TLA or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE_TFD or \
               self.m_nalUnitType == NAL_UNIT_CODED_SLICE

class NALUnitEBSP(NALUnit):
    m_nalUnitData

    def __init__(self, nalu):
        pass
