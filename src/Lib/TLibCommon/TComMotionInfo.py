# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComMotionInfo.py
    HM 8.0 Python Implementation
"""

import sys

from ... import TComMv

from .CommonDef import AMVP_MAX_NUM_CANDS_MEM, NOT_VALID, MODE_INTRA


class AMVPInfo(object):

    def __init__(self):
        self.m_acMvCand = AMVP_MAX_NUM_CANDS_MEM * [TComMv()]
        self.iN = 0


class TComMvField(object):

    def __init__(self):
        self.m_acMv = TComMv()
        self.m_iRefIdx = NOT_VALID

    def setMvField(self, cMv, iRefIdx):
        self.m_acMv = cMv
        self.m_iRefIdx = iRefIdx

    def setRefIdx(self, refIdx):
        self.m_iRefIdx = refIdx

    def getMv(self):
        return self.m_acMv

    def getRefIdx(self):
        return self.m_iRefIdx
    def getHor(self):
        return self.m_acMv.getHor()
    def getVer(self):
        return self.m_acMv.getVer()


class TComCUMvField(object):

    def __init__(self):
        self.m_pcMv = None
        self.m_pcMvd = None
        self.m_piRefIdx = None
        self.m_uiNumPartition = 0
        self.m_cAMVPInfo = AMVPInfo()

    def create(self, uiNumPartition):
        assert(self.m_pcMv == None)
        assert(self.m_pcMvd == None)
        assert(self.m_piRefIdx == None)

        self.m_pcMv = uiNumPartition * [TComMv()]
        self.m_pcMvd = uiNumPartition * [TComMv()]
        self.m_piRefIdx = uiNumPartition * [0]

        self.m_uiNumPartition = uiNumPartition

    def destroy(self):
        assert(self.m_pcMv != None)
        assert(self.m_pcMvd != None)
        assert(self.m_piRefIdx != None)

        del self.m_pcMv
        del self.m_pcMvd
        del self.m_piRefIdx

        self.m_pcMv = None
        self.m_pcMvd = None
        self.m_piRefIdx = None

        self.m_uiNumPartition = 0

    def clearMvField(self):
        for i in xrange(self.m_uiNumPartition):
            self.m_pcMv[i].setZero()
            self.m_pcMvd[i].setZero()
        for i in xrange(self.m_uiNumPartition):
            self.m_piRefIdx[i] = NOT_VALID

    def copyFrom(self, pcCUMvFieldSrc, iNumPartSrc, iPartAddrDst):
        for i in xrange(iNumPartSrc):
            self.m_pcMv[iPartAddrDst+i] = pcCUMvFieldSrc.m_pcMv[i]
            self.m_pcMvd[iPartAddrDst+i] = pcCUMvFieldSrc.m_pcMvd[i]
            self.m_piRefIdx[iPartAddrDst+i] = pcCUMvFieldSrc.m_piRefIdx[i]

    def copyTo(self, pcCUMvFieldDst, iPartAddrDst, uiOffset=None, uiNumPart=None):
        if uiOffset == None and uiNumPart == None:
            return self.copyTo(pcCUMvFieldDst, iPartAddrDst, 0, self.m_uiNumPartition)
        for i in xrange(uiNumPart):
            pcCUMvFieldDst.m_pcMv[uiOffset+iPartAddrDst+i] = self.m_pcMv[uiOffset+i]
            pcCUMvFieldDst.m_pcMvd[uiOffset+iPartAddrDst+i] = self.m_pcMvd[uiOffset+i]
            pcCUMvFieldDst.m_piRefIdx[uiOffset+iPartAddrDst+i] = self.m_piRefIdx[uiOffset+i]

    def getMv(self, iIdx):
        return self.m_pcMv[iIdx]
    def getMvd(self, iIdx):
        return self.m_pcMvd[iIdx]
    def getRefIdx(self, iIdx):
        return self.m_piRefIdx[iIdx]

    def getAMVPInfo(self):
        return self.m_cAMVPInfo

    def setAll(self, p, val, eCUMode, iPartAddr, uiDepth, iPartIdx):
        p += iPartAddr
        numElements = self.m_uiNumPartition >> (2*uiDepth)

        if eCUMode == SIZE_2Nx2N:
            for i in xrange(numElements):
                p[i] = val
        elif eCUMode == SIZE_2NxN:
            numElements >>= 1
            for i in xrange(numElements):
                p[i] = val
        elif eCUMode == SIZE_Nx2N:
            numElements >>= 2
            for i in xrange(numElements):
                p[i] = val
                p[i + 2 * numElements] = val
        elif eCUMode == SIZE_NxN:
            numElements >>= 2
            for i in xrange(numElements):
                p[i] = val
        elif eCUMode == SIZE_2NxnU:
            iCurrPartNumQ = numElements >> 2
            if iPartIdx == 0:
                pT = p
                pT2 = p + iCurrPartNumQ
                for i in xrange(iCurrPartNumQ>>1):
                    pT[i] = val
                    pT2[i] = val
            else:
                pT = p
                for i in xrange(iCurrPartNumQ>>1):
                    pT[i] = val

                pT = p + iCurrPartNumQ
                for i in xrange((iCurrPartNumQ>>1)+(iCurrPartNumQ<<1)):
                    pT[i] = val
        elif eCUMode == SIZE_2NxnD:
            iCurrPartNumQ = numElements >> 2
            if iPartIdx == 0:
                pT = p
                for i in xrange((iCurrPartNumQ>>1)+(iCurrPartNumQ<<1)):
                    pT[i] = val

                pT = p + (numElements - iCurrPartNumQ)
                for i in xrange(iCurrPartNumQ>>1):
                    pT[i] = val
            else:
                pT = p
                pT2 = p + iCurrPartNumQ
                for i in xrange(iCurrPartNumQ>>1):
                    pT[i] = val
                    pT2[i] = val
        elif eCUMode == SIZE_nLx2N:
            iCurrPartNumQ = numElements >> 2
            if iPartIdx == 0:
                pT = p
                pT2 = p + (iCurrPartNumQ<<1)
                pT3 = p + (iCurrPartNumQ>>1)
                pT4 = p + (iCurrPartNumQ<<1) + (iCurrPartNumQ>>1)

                for i in xrange(iCurrPartNumQ>>2):
                    pT[i] = val
                    pT2[i] = val
                    pT3[i] = val
                    pT4[i] = val
            else:
                pT = p
                pT2 = p + (iCurrPartNumQ<<1)
                for i in xrange(iCurrPartNumQ>>2):
                    pT[i] = val
                    pT2[i] = val

                pT = p + (iCurrPartNumQ>>1)
                pT2 = p + (iCurrPartNumQ<<1) + (iCurrPartNumQ>>1)
                for i in xrange((iCurrPartNumQ>>2)+iCurrPartNumQ):
                    pT[i] = val
                    pT2[i] = val
        elif eCUMode == SIZE_nRx2N:
            iCurrPartNumQ = numElements >> 2
            if iPartIdx == 0:
                pT = p
                pT2 = p + (iCurrPartNumQ<<1)
                for i in xrange((iCurrPartNumQ>>2)+iCurrPartNumQ):
                    pT[i] = val
                    pT2[i] = val

                pT = p + iCurrPartNumQ + (iCurrPartNumQ>>1)
                pT2 = p + numElements - iCurrPartNumQ + (iCurrPartNumQ>>1)
                for i in xrange(iCurrPartNumQ>>2):
                    pT[i] = val
                    pT2[i] = val
            else:
                pT = p
                pT2 = p + (iCurrPartNumQ>>1)
                pT3 = p + (iCurrPartNumQ<<1)
                pT2 = p + (iCurrPartNumQ<<1) + (iCurrPartNumQ>>1)
                for i in xrange(iCurrPartNumQ>>2):
                    pT[i] = val
                    pT2[i] = val
                    pT3[i] = val
                    pT4[i] = val
        else:
            assert(False)

    def setAllMv(self, mv, eCUMode, iPartAddr, uiDepth, iPartIdx=0):
        self.setAll(self.m_pcMv, mv, eCUMode, iPartAddr, uiDepth, iPartIdx)
    def setAllMvd(self, mvd, eCUMode, iPartAddr, uiDepth, iPartIdx=0):
        self.setAll(self.m_pcMvd, mvd, eCUMode, iPartAddr, uiDepth, iPartIdx)
    def setAllRefIdx(self, iRefIdx, eCUMode, iPartAddr, uiDepth, iPartIdx=0):
        self.setAll(self.m_piRefIdx, iRefIdx, eCUMode, iPartAddr, uiDepth, iPartIdx)
    def setAllMvField(self, mvField, eCUMode, iPartAddr, uiDepth, iPartIdx=0):
        self.setAllMv(mvField.getMv(), eCUMode, iPartAddr, uiDepth, iPartIdx)
        self.setAllRefIdx(mvField.getRefIdx(), eCUMode, iPartAddr, uiDepth, iPartIdx)

    def setNumPartition(self, iNumPart):
        self.m_uiNumPartition = iNumPart

    def linkToWithOffset(self, src, offset):
        self.m_pcMv = src.m_pcMv + offset
        self.m_pcMvd = src.m_pcMvd + offset
        self.m_piRefIdx = src.m_piRefIdx + offset

    def compress(self, pePredMode, scale):
        N = scale * scale
        assert(N > 0 and N <= self.m_uiNumPartition)

        for uiPartIdx in xrange(0, self.m_uiNumPartition, N):
            cMv = TComMv(0, 0)
            predMode = MODE_INTRA
            iRefIdx = 0

            cMv = self.m_pcMv[uiPartIdx]
            predMode = pePredMode[uiPartIdx]
            iRefIdx = self.m_piRefIdx[uiPartIdx]
            for i in xrange(N):
                self.m_pcMv[uiPartIdx+i] = cMv
                pePredMode[uiPartIdx+i] = predMode
                self.m_piRefIdx[uiPartIdx+i] = iRefIdx
