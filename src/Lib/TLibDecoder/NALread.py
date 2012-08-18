#!/usr/bin/env python

from ...Lib.TLibCommon.CommonDef import *
from ...Lib.TLibCommon.NAL import NALUnit
from ...Lib.TLibCommon.TComBitstream import TComBitstream

class InputNALUnit(NALUnit):

    def __init__(self):
        super(InputNALUnit, self).__init__(self)
        self.m_Bitstream = 0

def read(nalu, nalUnitBuf):

    def convertPayloadToRBSP(nalUnitBuf, pcBitstream):
        zeroCount = 0
        it_read = 0
        it_write = 0

        for it_read < len(nalUnitBuf):
            if zeroCount == 2 and nalUnitBuf[it_read] == 0x03:
                it_read += 1
                zeroCount = 0
            zeroCount = zeroCount + 1 if nalUnitBuf[it_read] == 0x00 else 0
            nalUnitBuf[it_write] = nalUnitBuf[it_read]
            it_read += 1
            it_write += 1

        nalUnitBuf.resize(it_write)

    pcBitstream = TComBitstream(None)
    convertPayloadToRBSP(nalUnitBuf, pcBitstream)

    nalu.m_Bitstream = TComBitstream(nalUnitBuf)
    bs = nalu.m_Bitstream

    forbidden_zero_bit = bs.read(1)
    assert(forbidden_zero_bit == 0)

    nalu.m_nalRefFlag = bs.read(1) != 0
    nalu.m_nalUnitType = bs.read(6)

    nalu.m_temporalId = bs.read(3)
    reserved_one_5bits = bs.read(5)
    assert(reserved_one_5bits == 1)
    if nalu.m_temporalId:
        assert(nalu.m_nalUnitType != NAL_UNIT_CODED_SLICE_CRA and
               nalu.m_nalUnitType != NAL_UNIT_CODED_SLICE_CRANT and
               nalu.m_nalUnitType != NAL_UNIT_CODED_SLICE_BLA and
               nalu.m_nalUnitType != NAL_UNIT_CODED_SLICE_BLANT and
               nalu.m_nalUnitType != NAL_UNIT_CODED_SLICE_IDR)
