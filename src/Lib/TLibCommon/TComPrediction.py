# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComPrediction.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = False
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import TComYuv
    from swig.hevc import ArrayInt
else:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
#   from . import TComRom as cvar
    from .TComYuv import TComYuv
    from swig.hevc import ArrayInt

from .pointer import pointer

from .TComWeightPrediction import TComWeightPrediction
from .TComInterpolationFilter import TComInterpolationFilter

from .TypeDef import (
    PLANAR_IDX, VER_IDX, HOR_IDX, DC_IDX,
    B_SLICE, P_SLICE,
    REF_PIC_LIST_0, REF_PIC_LIST_1, REF_PIC_LIST_X,
    AM_NONE, AM_EXPL
)

from .CommonDef import Clip

from .TComRom import (MAX_CU_DEPTH, MAX_CU_SIZE, g_aucConvertToBit)

NTAPS_LUMA = 8
NTAPS_CHROMA = 4


class TComPrediction(TComWeightPrediction):

    def __init__(self):
        super(TComPrediction, self).__init__()

        self.m_piYuvExt = None
        self.m_iYuvExtStride = 0
        self.m_iYuvExtHeight = 0

        self.m_acYuvPred = (TComYuv(), TComYuv())
        self.m_cYuvPredTemp = TComYuv()
        self.m_filteredBlock = ((TComYuv(), TComYuv(), TComYuv(), TComYuv()),
                                (TComYuv(), TComYuv(), TComYuv(), TComYuv()),
                                (TComYuv(), TComYuv(), TComYuv(), TComYuv()),
                                (TComYuv(), TComYuv(), TComYuv(), TComYuv()))
        self.m_filteredBlockTmp = (TComYuv(), TComYuv(), TComYuv(), TComYuv())

        self.m_if = TComInterpolationFilter()

    #   self.m_pLumaRecBuffer = None
    #   self.m_iLumaRecStride = 0
    #   self.m_uiaShift = []

    def __del__(self):
        if self.m_piYuvExt:
            del self.m_piYuvExt

        self.m_acYuvPred[0].destroy()
        self.m_acYuvPred[1].destroy()

        self.m_cYuvPredTemp.destroy()

    #   if self.m_pLumaRecBuffer:
    #       del self.m_pLumaRecBuffer

        for i in xrange(4):
            for j in xrange(4):
                self.m_filteredBlock[i][j].destroy()
            self.m_filteredBlockTmp[i].destroy()

    def initTempBuff(self):
        if self.m_piYuvExt == None:
            extWidth = cvar.g_uiMaxCUWidth + 16
            extHeight = cvar.g_uiMaxCUHeight + 1
            for i in xrange(4):
                self.m_filteredBlockTmp[i].create(extWidth, extHeight+7)
                for j in xrange(4):
                    self.m_filteredBlock[i][j].create(extWidth, extHeight)
            self.m_iYuvExtHeight = (cvar.g_uiMaxCUHeight + 2) << 4
            self.m_iYuvExtStride = (cvar.g_uiMaxCUWidth + 8) << 4
            self.m_piYuvExt = ArrayInt(self.m_iYuvExtStride * self.m_iYuvExtHeight)

            self.m_acYuvPred[0].create(cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight)
            self.m_acYuvPred[1].create(cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight)

            self.m_cYuvPredTemp.create(cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight)

    #   if self.m_iLumaRecStride != (cvar.g_uiMaxCUWidth >> 1) + 1:
    #       self.m_iLumaRecStride = (cvar.g_uiMaxCUWidth >> 1) + 1
    #       if not self.m_pLumaRecBuffer:
    #           self.m_pLumaRecBuffer = (self.m_iLumaRecStride * self.m_iLumaRecStride) * [0]
    #
    #   shift = cvar.g_uiBitDepth + cvar.g_uiBitIncrement + 4
    #
    #   for i in xrange(32, 64):
    #       self.m_uiaShift[i-32] = ((1 << shift) + i/2) / i

    def motionCompensation(self, pcCU, pcYuvPred, eRefPicList=REF_PIC_LIST_X, iPartIdx=-1):
        iWidth = 0
        iHeight = 0
        uiPartAddr = 0

        if iPartIdx >= 0:
            uiPartAddr, iWidth, iHeight = pcCU.getPartIndexAndSize(iPartIdx, uiPartAddr, iWidth, iHeight)
            if eRefPicList != REF_PIC_LIST_X:
                if pcCU.getSlice().getPPS().getUseWP():
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx, True)
                else:
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx)
                if pcCU.getSlice().getPPS().getUseWP():
                    self._xWeightedPredictionUni(pcCU, pcYuvPred, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx)
            else:
                if self._xCheckIdenticalMotion(pcCU, uiPartAddr):
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, REF_PIC_LIST_0, pcYuvPred, iPartIdx)
                else:
                    self._xPredInterBi(pcCU, uiPartAddr, iWidth, iHeight, pcYuvPred, iPartIdx)
            return

        for iPartIdx in xrange(pcCU.getNumPartInter()):
            uiPartAddr, iWidth, iHeight = pcCU.getPartIndexAndSize(iPartIdx, uiPartAddr, iWidth, iHeight)
            if eRefPicList != REF_PIC_LIST_X:
                if pcCU.getSlice().getPPS().getUseWP():
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx, True)
                else:
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx)
                self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx)
                if pcCU.getSlice().getPPS().getUseWP():
                    self._xWeightedPredictionUni(pcCU, pcYuvPred, uiPartAddr, iWidth, iHeight, eRefPicList, pcYuvPred, iPartIdx)
            else:
                if self._xCheckIdenticalMotion(pcCU, uiPartAddr):
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, REF_PIC_LIST_0, pcYuvPred, iPartIdx)
                else:
                    self._xPredInterBi(pcCU, uiPartAddr, iWidth, iHeight, pcYuvPred, iPartIdx)

    def getMvPredAMVP(self, pcCU, uiPartIdx, uiPartAddr, eRefPicList, iRefIdx):
        rcMvPred = None
        pcAMVPInfo = pcCU.getCUMvField(eRefPicList).getAMVPInfo()
        acMvCand = pointer(pcAMVPInfo.m_acMvCand, type='TComMv *')

        if pcCU.getAMVPMode(uiPartAddr) == AM_NONE or \
           (pcAMVPInfo.iN <= 1 and pcCU.getAMVPMode(uiPartAddr) == AM_EXPL):
            rcMvPred = acMvCand[0]

            pcCU.setMVPIdxSubParts(0, eRefPicList, uiPartAddr, uiPartIdx, pcCU.getDepth(uiPartAddr))
            pcCU.setMVPNumSubParts(pcAMVPInfo.iN, eRefPicList, uiPartAddr, uiPartIdx, pcCU.getDepth(uiPartAddr))
            return rcMvPred

        assert(pcCU.getMVPIdx(eRefPicList, uiPartAddr) >= 0)
        rcMvPred = acMvCand[pcCU.getMVPIdx(eRefPicList, uiPartAddr)]
        return rcMvPred

    def predIntraLumaAng(self, pcTComPattern, uiDirMode, piPred, uiStride, iWidth, iHeight, pcCU, bAbove, bLeft):
        pDst = pointer(piPred, type='short *')

        assert(ord(cvar.g_aucConvertToBit[iWidth]) >= 0) # 4x4
        assert(ord(cvar.g_aucConvertToBit[iWidth]) <= 5) # 128x128
        assert(iWidth == iHeight)

        ptrSrc = pcTComPattern.getPredictorPtr(uiDirMode, ord(cvar.g_aucConvertToBit[iWidth])+2, self.m_piYuvExt.cast())
        ptrSrc = pointer(ptrSrc, type='int *')

        # get starting pixel in block
        sw = 2 * iWidth + 1

        # Create the prediction
        if uiDirMode == PLANAR_IDX:
            self._xPredIntraPlanar(ptrSrc+sw+1, sw, pDst, uiStride, iWidth, iHeight)
        else:
            self._xPredIntraAng(ptrSrc+sw+1, sw, pDst, uiStride, iWidth, iHeight, uiDirMode, bAbove, bLeft, True)

            if uiDirMode == DC_IDX and bAbove and bLeft:
                self._xDCPredFiltering(ptrSrc+sw+1, sw, pDst, uiStride, iWidth, iHeight)

    def predIntraChromaAng(self, pcTComPattern, piSrc, uiDirMode, piPred, uiStride, iWidth, iHeight, pcCU, bAbove, bLeft):
        pDst = pointer(piPred, type='short *')
        ptrSrc = pointer(piSrc, type='int *')

        # get starting pixel in block
        sw = 2 * iWidth + 1

        if uiDirMode == PLANAR_IDX:
            self._xPredIntraPlanar(ptrSrc+sw+1, sw, pDst, uiStride, iWidth, iHeight)
        else:
            # Create the prediction
            self._xPredIntraAng(ptrSrc+sw+1, sw, pDst, uiStride, iWidth, iHeight, uiDirMode, bAbove, bLeft, False)

    def getPredicBuf(self):
        return self.m_piYuvExt.cast()
    def getPredicBufWidth(self):
        return self.m_iYuvExtStride
    def getPredicBufHeight(self):
        return self.m_iYuvExtHeight

    def _xCheckIdenticalMotion(self, pcCU, PartAddr):
        if pcCU.getSlice().isInterB() and not pcCU.getSlice().getPPS().getWPBiPred():
            if pcCU.getCUMvField(REF_PIC_LIST_0).getRefIdx(PartAddr) >= 0 and \
               pcCU.getCUMvField(REF_PIC_LIST_1).getRefIdx(PartAddr) >= 0:
                RefPOCL0 = pcCU.getSlice().getRefPic(REF_PIC_LIST_0, pcCU.getCUMvField(REF_PIC_LIST_0).getRefIdx(PartAddr)).getPOC()
                RefPOCL1 = pcCU.getSlice().getRefPic(REF_PIC_LIST_1, pcCU.getCUMvField(REF_PIC_LIST_1).getRefIdx(PartAddr)).getPOC()
                if RefPOCL0 == RefPOCL1 and \
                   pcCU.getCUMvField(REF_PIC_LIST_0).getMv(PartAddr) == pcCU.getCUMvField(REF_PIC_LIST_1).getMv(PartAddr):
                    return True
        return False

    def _xDCPredFiltering(self, piSrc, iSrcStride, rpDst, iDstStride, iWidth, iHeight):
        piSrc = pointer(piSrc, bias=-(iSrcStride+1), type='int *')

        # boundary pixels processing
        rpDst[0] = (piSrc[-iSrcStride] + piSrc[-1] + 2 * rpDst[0] + 2) >> 2

        for x in xrange(1, iWidth):
            rpDst[x] = (piSrc[x - iSrcStride] + 3 * rpDst[x] + 2) >> 2

        iDstStride2 = iDstStride
        iSrcStride2 = iSrcStride-1
        for y in xrange(1, iHeight):
            rpDst[iDstStride2] = (piSrc[iSrcStride2] + 3 * rpDst[iDstStride2] + 2) >> 2
            iDstStride2 += iDstStride
            iSrcStride2 += iSrcStride

    def _predIntraGetPredValDC(self, piSrc, iSrcStride, iWidth, iHeight, bAbove, bLeft):
        piSrc = pointer(piSrc, bias=-(iSrcStride+1), type='int *')
        iSum = 0
        pDcVal = 0

        if bAbove:
            for iInd in xrange(iWidth):
                iSum += piSrc[iInd - iSrcStride]
        if bLeft:
            for iInd in xrange(iHeight):
                iSum += piSrc[iInd * iSrcStride - 1]

        if bAbove and bLeft:
            pDcVal = (iSum + iWidth) / (iWidth + iHeight)
        elif bAbove:
            pDcVal = (iSum + iWidth/2) / iWidth
        elif bLeft:
            pDcVal = (iSum + iHeight/2) / iHeight
        else:
            pDcVal = piSrc[-1] # Default DC value already calculated and placed in the prediction array if no neighbors are available

        return pDcVal

    def _xPredIntraAng(self, piSrc, srcStride, rpDst, dstStride, width, height,
                       dirMode, blkAboveAvailable, blkLeftAvailable, bFilter):
        blkSize = width
        piSrc = pointer(piSrc, bias=-(srcStride+1), type='int *')

        # Map the mode index to main prediction direction and angle
        assert(dirMode > 0) #no planar
        modeDC = dirMode < 2
        modeHor = not modeDC and (dirMode < 18)
        modeVer = not modeDC and not modeHor
        intraPredAngle = (dirMode-VER_IDX) if modeVer else -(dirMode-HOR_IDX) if modeHor else 0
        absAng = abs(intraPredAngle)
        signAng = -1 if intraPredAngle < 0 else 1

        # Set bitshifts and scale the angle parameter to block size
        angTable = (0, 2, 5, 9, 13, 17, 21, 26, 32)
        invAngTable = (0, 4096, 1638, 910, 630, 482, 390, 315, 256) # (256 * 32) / Angle
        invAngle = invAngTable[absAng]
        absAng = angTable[absAng]
        intraPredAngle = signAng * absAng

        # Do the DC prediction
        if modeDC:
            dcval = self._predIntraGetPredValDC(piSrc, srcStride, width, height, blkAboveAvailable, blkLeftAvailable)

            for k in xrange(blkSize):
                for l in xrange(blkSize):
                    rpDst[k * dstStride + l] = dcval
        # Do angular predictions
        else:
            refMain = None
            refSize = None
            refAbove = (2 * MAX_CU_SIZE + 1) * [0]
            refLeft = (2 * MAX_CU_SIZE + 1) * [0]

            # Initialise the Main and Left reference array.
            if intraPredAngle < 0:
                for k in xrange(blkSize+1):
                    refAbove[k + blkSize - 1] = piSrc[k - srcStride - 1]
                for k in xrange(blkSize+1):
                    refLeft[k + blkSize - 1] = piSrc[(k-1) * srcStride - 1]
                refMain = pointer(refAbove if modeVer else refLeft, base=(blkSize-1))
                refSide = pointer(refLeft if modeVer else refAbove, base=(blkSize-1))

                # Extend the Main reference to the left.
                invAngleSum = 128 # rounding for (shift by 8)
                for k in xrange(-1, blkSize * intraPredAngle >> 5, -1):
                    invAngleSum += invAngle
                    refMain[k] = refSide[invAngleSum >> 8]
            else:
                for k in xrange(2*blkSize+1):
                    refAbove[k] = piSrc[k - srcStride - 1]
                for k in xrange(2*blkSize+1):
                    refLeft[k] = piSrc[(k-1) * srcStride - 1]
                refMain = pointer(refAbove if modeVer else refLeft)
                refSide = pointer(refLeft if modeVer else refAbove)

            if intraPredAngle == 0:
                for k in xrange(blkSize):
                    for l in xrange(blkSize):
                        rpDst[k * dstStride + l] = refMain[l + 1]

                if bFilter:
                    for k in xrange(blkSize):
                        rpDst[k * dstStride] = Clip(rpDst[k*dstStride] + ((refSide[k+1] - refSide[0]) >> 1))
            else:
                deltaPos = 0
                deltaInt = 0
                deltaFract = 0
                refMainIndex = 0

                for k in xrange(blkSize):
                    deltaPos += intraPredAngle
                    deltaInt = deltaPos >> 5
                    deltaFract = deltaPos & (32 - 1)

                    if deltaFract:
                        # Do linear filtering
                        for l in xrange(blkSize):
                            refMainIndex = l + deltaInt + 1
                            rpDst[k * dstStride + l] = \
                                ((32-deltaFract)*refMain[refMainIndex] +
                                 deltaFract * refMain[refMainIndex+1] + 16) >> 5
                    else:
                        # Just copy the integer samples
                        for l in xrange(blkSize):
                            rpDst[k * dstStride + l] = refMain[l + deltaInt + 1]

            # Flip the block if this is the horizontal mode
            if modeHor:
                for k in xrange(blkSize-1):
                    for l in xrange(k+1, blkSize):
                        rpDst[k * dstStride + l], rpDst[l * dstStride + k] = \
                            rpDst[l * dstStride + k], rpDst[k * dstStride + l]

    def _xPredIntraPlanar(self, piSrc, srcStride, rpDst, dstStride, width, height):
        assert(width == height)
        piSrc = pointer(piSrc, bias=-(srcStride+1), type='int *')

        leftColumn = MAX_CU_SIZE * [0]
        topRow = MAX_CU_SIZE * [0]
        bottomRow = MAX_CU_SIZE * [0]
        rightColumn = MAX_CU_SIZE * [0]
        blkSize = width
        offset2D = width
        shift1D = g_aucConvertToBit[width] + 2
        shift2D = shift1D + 1

        # Get left and above reference column and row
        for k in xrange(blkSize+1):
            topRow[k] = piSrc[k - srcStride]
            leftColumn[k] = piSrc[k * srcStride - 1]

        # Prepare intermediate variables used in interpolation
        bottomLeft = leftColumn[blkSize]
        topRight = topRow[blkSize]
        for k in xrange(blkSize):
            bottomRow[k] = bottomLeft - topRow[k]
            rightColumn[k] = topRight - leftColumn[k]
            topRow[k] <<= shift1D
            leftColumn[k] <<= shift1D

        # Generate prediction signal
        for k in xrange(blkSize):
            horPred = leftColumn[k] + offset2D
            for l in xrange(blkSize):
                horPred += rightColumn[k]
                topRow[l] += bottomRow[l]
                rpDst[k * dstStride + l] = (horPred + topRow[l]) >> shift2D

    def _xPredInterUni(self, pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, rpcYuvPred, iPartIdx, bi=False):
        iRefIdx = pcCU.getCUMvField(eRefPicList).getRefIdx(uiPartAddr)
        assert(iRefIdx >= 0)
        cMv = pcCU.getCUMvField(eRefPicList).getMv(uiPartAddr)
        pcCU.clipMv(cMv)
        self._xPredInterLumaBlk(
            pcCU, pcCU.getSlice().getRefPic(eRefPicList, iRefIdx).getPicYuvRec(),
            uiPartAddr, cMv, iWidth, iHeight, rpcYuvPred, bi)
        self._xPredInterChromaBlk(
            pcCU, pcCU.getSlice().getRefPic(eRefPicList, iRefIdx).getPicYuvRec(),
            uiPartAddr, cMv, iWidth, iHeight, rpcYuvPred, bi)

    def _xPredInterBi(self, pcCU, uiPartAddr, iWidth, iHeight, rpcYuvPred, iPartIdx):
        pcMbYuv = None
        iRefIdx = [-1, -1]

        for iRefList in xrange(2):
            eRefPicList = REF_PIC_LIST_1 if iRefList else REF_PIC_LIST_0
            iRefIdx[iRefList] = pcCU.getCUMvField(eRefPicList).getRefIdx(uiPartAddr)

            if iRefIdx[iRefList] < 0:
                continue

            assert(iRefIdx[iRefList] < pcCU.getSlice().getNumRefIdx(eRefPicList))

            pcMbYuv = self.m_acYuvPred[iRefList]
            if pcCU.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiPartAddr) >= 0 and \
               pcCU.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiPartAddr) >= 0:
                self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcMbYuv, iPartIdx, True)
            else:
                if (pcCU.getSlice().getPPS().getUseWP() and pcCU.getSlice().getSliceType() == P_SLICE) or \
                   (pcCU.getSlice().getPPS().getWPBiPred() and pcCU.getSlice().getSliceType() == B_SLICE):
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcMbYuv, iPartIdx, True)
                else:
                    self._xPredInterUni(pcCU, uiPartAddr, iWidth, iHeight, eRefPicList, pcMbYuv, iPartIdx)

        if pcCU.getSlice().getPPS().getWPBiPred() and pcCU.getSlice().getSliceType() == B_SLICE:
            self._xWeightedPredictionBi(pcCU, self.m_acYuvPred[0], self.m_acYuvPred[1],
                iRefIdx[0], iRefIdx[1], uiPartAddr, iWidth, iHeight, rpcYuvPred)
        elif pcCU.getSlice().getPPS().getUseWP() and pcCU.getSlice().getSliceType() == P_SLICE:
            self._xWeightedPredictionUni(pcCU, self.m_acYuvPred[0],
                uiPartAddr, iWidth, iHeight, REF_PIC_LIST_0, rpcYuvPred, iPartIdx)
        else:
            self._xWeightedAverage(pcCU, self.m_acYuvPred[0], self.m_acYuvPred[1],
                iRefIdx[0], iRefIdx[1], uiPartAddr, iWidth, iHeight, rpcYuvPred)

    def _xPredInterLumaBlk(self, cu, refPic, partAddr, mv, width, height, dstPic, bi):
        refStride = refPic.getStride()
        refOffset = (mv.getHor() >> 2) + (mv.getVer() >> 2) * refStride
        ref = pointer(refPic.getLumaAddr(cu.getAddr(), cu.getZorderIdxInCU() + partAddr), base=refOffset, type='short *')

        dstStride = dstPic.getStride()
        dst = pointer(dstPic.getLumaAddr(partAddr), type='short *')

        xFrac = mv.getHor() & 0x3
        yFrac = mv.getVer() & 0x3

        if yFrac == 0:
            self.m_if.filterHorLuma(ref, refStride, dst, dstStride, width, height, xFrac, not bi)
        elif xFrac == 0:
            self.m_if.filterVerLuma(ref, refStride, dst, dstStride, width, height, yFrac, True, not bi)
        else:
            tmpStride = self.m_filteredBlockTmp[0].getStride()
            tmp = pointer(self.m_filteredBlockTmp[0].getLumaAddr(), type='short *')

            filterSize = NTAPS_LUMA
            halfFilterSize = filterSize >> 1

            self.m_if.filterHorLuma(ref - (halfFilterSize-1)*refStride, refStride, tmp, tmpStride, width, height+filterSize-1, xFrac, False)
            self.m_if.filterVerLuma(tmp + (halfFilterSize-1)*tmpStride, tmpStride, dst, dstStride, width, height, yFrac, False, not bi)

    def _xPredInterChromaBlk(self, cu, refPic, partAddr, mv, width, height, dstPic, bi):
        refStride = refPic.getCStride()
        dstStride = dstPic.getCStride()

        refOffset = (mv.getHor() >> 3) + (mv.getVer() >> 3) * refStride

        refCb = pointer(refPic.getCbAddr(cu.getAddr(), cu.getZorderIdxInCU() + partAddr), base=refOffset, type='short *')
        refCr = pointer(refPic.getCrAddr(cu.getAddr(), cu.getZorderIdxInCU() + partAddr), base=refOffset, type='short *')

        dstCb = pointer(dstPic.getCbAddr(partAddr), type='short *')
        dstCr = pointer(dstPic.getCrAddr(partAddr), type='short *')

        xFrac = mv.getHor() & 0x7
        yFrac = mv.getVer() & 0x7
        cxWidth = width >> 1
        cxHeight = height >> 1

        extStride = self.m_filteredBlockTmp[0].getStride()
        extY = pointer(self.m_filteredBlockTmp[0].getLumaAddr(), type='short *')

        filterSize = NTAPS_CHROMA
        halfFilterSize = filterSize >> 1

        if yFrac == 0:
            self.m_if.filterHorChroma(refCb, refStride, dstCb, dstStride, cxWidth, cxHeight, xFrac, not bi)
            self.m_if.filterHorChroma(refCr, refStride, dstCr, dstStride, cxWidth, cxHeight, xFrac, not bi)
        elif xFrac == 0:
            self.m_if.filterVerChroma(refCb, refStride, dstCb, dstStride, cxWidth, cxHeight, yFrac, True, not bi)
            self.m_if.filterVerChroma(refCr, refStride, dstCr, dstStride, cxWidth, cxHeight, yFrac, True, not bi)
        else:
            self.m_if.filterHorChroma(refCb - (halfFilterSize-1)*refStride, refStride, extY, extStride, cxWidth, cxHeight+filterSize-1, xFrac, False)
            self.m_if.filterVerChroma(extY + (halfFilterSize-1)*extStride, extStride, dstCb, dstStride, cxWidth, cxHeight, yFrac, False, not bi)

            self.m_if.filterHorChroma(refCr - (halfFilterSize-1)*refStride, refStride, extY, extStride, cxWidth, cxHeight+filterSize-1, xFrac, False)
            self.m_if.filterVerChroma(extY + (halfFilterSize-1)*extStride, extStride, dstCr, dstStride, cxWidth, cxHeight, yFrac, False, not bi)

    def _xWeightedAverage(self, pcCU, pcYuvSrc0, pcYuvSrc1, iRefIdx0, iRefIdx1, uiPartIdx, iWidth, iHeight, rpcYuvDst):
        if iRefIdx0 >= 0 and iRefIdx1 >= 0:
            rpcYuvDst.addAvg(pcYuvSrc0, pcYuvSrc1, uiPartIdx, iWidth, iHeight)
        elif iRefIdx0 >= 0 and iRefIdx1 < 0:
            pcYuvSrc0.copyPartToPartYuv(rpcYuvDst, uiPartIdx, iWidth, iHeight)
        elif iRefIdx0 < 0 and iRefIdx1 >= 0:
            pcYuvSrc1.copyPartToPartYuv(rpcYuvDst, uiPartIdx, iWidth, iHeight)
