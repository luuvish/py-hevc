# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecBinCoderCABAC.py
    HM 9.1 Python Implementation
"""

from ..TLibCommon.TComCABACTables import sm_aucLPSTable, sm_aucRenormTable


class TDecBinCABAC(object):

    def __init__(self):
        self.m_pcTComBitstream = None
        self.m_uiRange         = 0
        self.m_uiValue         = 0
        self.m_bitsNeeded      = 0

    def init(self, pcTComBitstream):
        self.m_pcTComBitstream = pcTComBitstream
    def uninit(self):
        self.m_pcTComBitstream = None

    def start(self):
        assert(self.m_pcTComBitstream.getNumBitsUntilByteAligned() == 0)
        self.m_uiRange = 510
        self.m_bitsNeeded = -8
        self.m_uiValue = self.m_pcTComBitstream.readByte() << 8
        self.m_uiValue |= self.m_pcTComBitstream.readByte()

    def finish(self):
        pass

    def flush(self):
        while self.m_pcTComBitstream.getNumBitsLeft() > 0 and \
              self.m_pcTComBitstream.getNumBitsUntilByteAligned() != 0:
            uiBits = 0
            uiBits = self.m_pcTComBitstream.read(1, uiBits)
        self.start()

    def decodeBin(self, ruiBin, rcCtxModel):
        uiLPS = sm_aucLPSTable[rcCtxModel.getState()][(self.m_uiRange>>6)-4]
        self.m_uiRange -= uiLPS
        scaledRange = self.m_uiRange << 7

        if self.m_uiValue < scaledRange:
            # MPS path
            ruiBin = rcCtxModel.getMps()
            rcCtxModel.updateMPS()

            if scaledRange >= (256<<7):
                return ruiBin

            self.m_uiRange = scaledRange >> 6
            self.m_uiValue += self.m_uiValue

            self.m_bitsNeeded += 1
            if self.m_bitsNeeded == 0:
                self.m_bitsNeeded = -8
                self.m_uiValue += self.m_pcTComBitstream.readByte()
        else:
            # LPS path
            numBits = sm_aucRenormTable[uiLPS >> 3]
            self.m_uiValue = (self.m_uiValue - scaledRange) << numBits
            self.m_uiRange = uiLPS << numBits
            ruiBin = 1 - rcCtxModel.getMps()
            rcCtxModel.updateLPS()

            self.m_bitsNeeded += numBits

            if self.m_bitsNeeded >= 0:
                self.m_uiValue += self.m_pcTComBitstream.readByte() << self.m_bitsNeeded
                self.m_bitsNeeded -= 8

        return ruiBin

    def decodeBinEP(self, ruiBin):
        self.m_uiValue += self.m_uiValue

        self.m_bitsNeeded += 1
        if self.m_bitsNeeded >= 0:
            self.m_bitsNeeded = -8
            self.m_uiValue += self.m_pcTComBitstream.readByte()

        ruiBin = 0
        scaledRange = self.m_uiRange << 7
        if self.m_uiValue >= scaledRange:
            ruiBin = 1
            self.m_uiValue -= scaledRange

        return ruiBin

    def decodeBinsEP(self, ruiBin, numBins):
        bins = 0

        while numBins > 8:
            self.m_uiValue = (self.m_uiValue<<8) + \
                (self.m_pcTComBitstream.readByte() << (8+self.m_bitsNeeded))

            scaledRange = self.m_uiRange << 15
            for i in xrange(8):
                bins += bins
                scaledRange >>= 1
                if self.m_uiValue >= scaledRange:
                    bins += 1
                    self.m_uiValue -= scaledRange
            numBins -= 8

        self.m_bitsNeeded += numBins
        self.m_uiValue <<= numBins

        if self.m_bitsNeeded >= 0:
            self.m_uiValue += self.m_pcTComBitstream.readByte() << self.m_bitsNeeded
            self.m_bitsNeeded -= 8

        scaledRange = self.m_uiRange << (numBins+7)
        for i in xrange(numBins):
            bins += bins
            scaledRange >>= 1
            if self.m_uiValue >= scaledRange:
                bins += 1
                self.m_uiValue -= scaledRange

        ruiBin = bins
        return ruiBin

    def decodeBinTrm(self, ruiBin):
        self.m_uiRange -= 2
        scaledRange = self.m_uiRange << 7
        if self.m_uiValue >= scaledRange:
            ruiBin = 1
        else:
            ruiBin = 0
            if scaledRange < (256<<7):
                self.m_uiRange = scaledRange >> 6
                self.m_uiValue += self.m_uiValue

                self.m_bitsNeeded += 1
                if self.m_bitsNeeded == 0:
                    self.m_bitsNeeded = -8
                    self.m_uiValue += self.m_pcTComBitstream.readByte()

        return ruiBin

    def resetBac(self):
        self.m_uiRange = 510
        self.m_bitsNeeded = -8
        self.m_uiValue = self.m_pcTComBitstream.read(16)

    def decodePCMAlignBits(self):
        iNum = self.m_pcTComBitstream.getNumBitsUntilByteAligned()

        uiBit = 0
        uiBit = self.m_pcTComBitstream.read(iNum, uiBit)

    def xReadPCMCode(self, uiLength, ruiCode):
        assert(uiLength > 0)
        ruiCode = self.m_pcTComBitstream.read(uiLength, ruiCode)
        return ruiCode

    def copyState(self, pcTDecBinIf):
        pcTDecBinCABAC = pcTDecBinIf.getTDecBinCABAC()
        self.m_uiRange = pcTDecBinCABAC.m_uiRange
        self.m_uiValue = pcTDecBinCABAC.m_uiValue
        self.m_bitsNeeded = pcTDecBinCABAC.m_bitsNeeded

    def getTDecBinCABAC(self):
        return self
