# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecBinCabac.py
    HM 8.0 Python Implementation
"""

sm_aucLPSTable = (
    (128, 176, 208, 240),
    (128, 167, 197, 227),
    (128, 158, 187, 216),
    (123, 150, 178, 205),
    (116, 142, 169, 195),
    (111, 135, 160, 185),
    (105, 128, 152, 175),
    (100, 122, 144, 166),
    ( 95, 116, 137, 158),
    ( 90, 110, 130, 150),
    ( 85, 104, 123, 142),
    ( 81,  99, 117, 135),
    ( 77,  94, 111, 128),
    ( 73,  89, 105, 122),
    ( 69,  85, 100, 116),
    ( 66,  80,  95, 110),
    ( 62,  76,  90, 104),
    ( 59,  72,  86,  99),
    ( 56,  69,  81,  94),
    ( 53,  65,  77,  89),
    ( 51,  62,  73,  85),
    ( 48,  59,  69,  80),
    ( 46,  56,  66,  76),
    ( 43,  53,  63,  72),
    ( 41,  50,  59,  69),
    ( 39,  48,  56,  65),
    ( 37,  45,  54,  62),
    ( 35,  43,  51,  59),
    ( 33,  41,  48,  56),
    ( 32,  39,  46,  53),
    ( 30,  37,  43,  50),
    ( 29,  35,  41,  48),
    ( 27,  33,  39,  45),
    ( 26,  31,  37,  43),
    ( 24,  30,  35,  41),
    ( 23,  28,  33,  39),
    ( 22,  27,  32,  37),
    ( 21,  26,  30,  35),
    ( 20,  24,  29,  33),
    ( 19,  23,  27,  31),
    ( 18,  22,  26,  30),
    ( 17,  21,  25,  28),
    ( 16,  20,  23,  27),
    ( 15,  19,  22,  25),
    ( 14,  18,  21,  24),
    ( 14,  17,  20,  23),
    ( 13,  16,  19,  22),
    ( 12,  15,  18,  21),
    ( 12,  14,  17,  20),
    ( 11,  14,  16,  19),
    ( 11,  13,  15,  18),
    ( 10,  12,  15,  17),
    ( 10,  12,  14,  16),
    (  9,  11,  13,  15),
    (  9,  11,  12,  14),
    (  8,  10,  12,  14),
    (  8,   9,  11,  13),
    (  7,   9,  11,  12),
    (  7,   9,  10,  12),
    (  7,   8,  10,  11),
    (  6,   8,   9,  11),
    (  6,   7,   9,  10),
    (  6,   7,   8,   9),
    (  2,   2,   2,   2)
)

sm_aucRenormTable = (
    6, 5, 4, 4,
    3, 3, 3, 3,
    2, 2, 2, 2,
    2, 2, 2, 2,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1
)


class TDecBinCabac(object):

    def __init__(self):
        self.m_pcTComBitstream = None
        self.m_uiRange = 0
        self.m_uiValue = 0
        self.m_bitsNeeded = 0

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

    def resetBac(self):
        self.m_uiRange = 510
        self.m_bitsNeeded = -8
        self.m_uiValue = self.m_pcTComBitstream.read(16)

    def copyState(self, pcTDecBinIf):
        pcTDecBinCABAC = pcTDecBinIf.getTDecBinCABAC()
        self.m_uiRange = pcTDecBinCABAC.m_uiRange
        self.m_uiValue = pcTDecBinCABAC.m_uiValue
        self.m_bitsNeeded = pcTDecBinCABAC.m_bitsNeeded

    def getTDecBinCABAC(self):
        return self

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

    def decodeNumSubseqIPCM(self, numSubseqIPCM):
        bit = 0
        numSubseqIPCM = 0

        while True:
            self.m_uiValue += self.m_uiValue
            self.m_bitsNeeded += 1
            if self.m_bitsNeeded >= 0:
                self.m_bitsNeeded = -8
                self.m_uiValue += self.m_pcTComBitstream.readByte()
            bit = (self.m_uiValue & 128) >> 7
            numSubseqIPCM += 1
            if not (bit and numSubseqIPCM < 3):
                break

        if bit and numSubseqIPCM == 3:
            numSubseqIPCM += 1

        numSubseqIPCM -= 1
        return numSubseqIPCM

    def decodePCMAlignBits(self):
        iNum = self.m_pcTComBitstream.getNumBitsUntilByteAligned()

        uiBit = 0
        self.m_pcTComBitstream.read(iNum, uiBit)

    def xReadPCMCode(self, uiLength, ruiCode):
        assert(uiLength > 0)
        ruiCode = self.m_pcTComBitstream.read(uiLength, ruiCode)
        return ruiCode
