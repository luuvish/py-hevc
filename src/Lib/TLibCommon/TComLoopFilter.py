# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComLoopFilter.py
    HM 8.0 Python Implementation
"""

import sys

from ... import pointer
from ... import cvar
from ... import Char

from .TypeDef import LFCUParam
from .TypeDef import (
    SIZE_2Nx2N, SIZE_2NxN, SIZE_Nx2N, SIZE_NxN,
    SIZE_2NxnU, SIZE_2NxnD, SIZE_nLx2N, SIZE_nRx2N, SIZE_NONE,
    TEXT_LUMA, REF_PIC_LIST_0, REF_PIC_LIST_1
)

from .CommonDef import (MIN_QP, MAX_QP, Clip, Clip3)

from .TComRom import (
    g_auiZscanToRaster, g_auiRasterToZscan,
    g_auiRasterToPelX, g_auiRasterToPelY,
    g_aucChromaScale
)

DEBLOCK_SMALLEST_BLOCK = 8

EDGE_VER = 0
EDGE_HOR = 1
QpUV = lambda iQpY: g_aucChromaScale[max(min(iQpY, MAX_QP), MIN_QP)]

DEFAULT_INTRA_TC_OFFSET = 2

tctable_8x8 = (
   0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  1,  1,  1,  1,  1,  1,
   1,  1,  1,  2,  2,  2,  2,  3,
   3,  3,  3,  4,  4,  4,  5,  5,
   6,  6,  7,  8,  9, 10, 11, 13,
  14, 16, 18, 20, 22, 24
)

betatable_8x8 = (
   0,  0,  0,  0,  0,  0,  0,  0,
   0,  0,  0,  0,  0,  0,  0,  0,
   6,  7,  8,  9, 10, 11, 12, 13,
  14, 15, 16, 17, 18, 20, 22, 24,
  26, 28, 30, 32, 34, 36, 38, 40,
  42, 44, 46, 48, 50, 52, 54, 56,
  58, 60, 62, 64
)


class TComLoopFilter(object):

    def __init__(self):
        self.m_uiDisableDeblockingFilterIdc = 0
        self.m_betaOffsetDiv2 = 0
        self.m_tcOffsetDiv2 = 0

        self.m_uiNumPartitions = 0
        self.m_aapucBS = 2 * [None]
        self.m_aapbEdgeFilter = [[None, None, None] for x in xrange(2)]
        self.m_stLFCUParam = LFCUParam()

        self.m_bLFCrossTileBoundary = True

    def create(self, uiMaxCUDepth):
        self.destroy()
        self.m_uiNumPartitions = 1 << (uiMaxCUDepth << 1)
        for uiDir in xrange(2):
            self.m_aapucBS[uiDir] = self.m_uiNumPartitions * [0]
            for uiPlane in xrange(3):
                self.m_aapbEdgeFilter[uiDir][uiPlane] = self.m_uiNumPartitions * [False]

    def destroy(self):
        for uiDir in xrange(2):
            if self.m_aapucBS:
                p = self.m_aapucBS[uiDir]
                del p
                self.m_aapucBS[uiDir] = None
            for uiPlane in xrange(3):
                if self.m_aapbEdgeFilter[uiDir][uiPlane]:
                    p = self.m_aapbEdgeFilter[uiDir][uiPlane]
                    del p
                    self.m_aapbEdgeFilter[uiDir][uiPlane] = None

    def setCfg(self, DeblockingFilterControlPresent, uiDisableDblkIdc,
               iBetaOffset_div2, iTcOffset_div2, bLFCrossTileBoundary):
        self.m_bLFCrossTileBoundary = bLFCrossTileBoundary

        if DeblockingFilterControlPresent:
            self.m_uiDisableDeblockingFilterIdc = uiDisableDblkIdc
            self.m_betaOffsetDiv2 = iBetaOffset_div2
            self.m_tcOffsetDiv2 = iTcOffset_div2
        else: # use default values
            self.m_uiDisableDeblockingFilterIdc = 0
            self.m_betaOffsetDiv2 = 0
            self.m_tcOffsetDiv2 = 0

    def loopFilterPic(self, pcPic):
        if self.m_uiDisableDeblockingFilterIdc == 1:
            return

        # Horizontal filtering
        for uiCUAddr in xrange(pcPic.getNumCUsInFrame()):
            pcCU = pcPic.getCU(uiCUAddr)

            for uiPart in xrange(self.m_uiNumPartitions):
                self.m_aapucBS[EDGE_VER][uiPart] = 0
            for iPlane in xrange(3):
                for uiPart in xrange(self.m_uiNumPartitions):
                    self.m_aapbEdgeFilter[EDGE_VER][iPlane][uiPart] = False

            # CU-based deblocking
            self._xDeblockCU(pcCU, 0, 0, EDGE_VER)

        # Vertical filtering
        for uiCUAddr in xrange(pcPic.getNumCUsInFrame()):
            pcCU = pcPic.getCU(uiCUAddr)

            for uiPart in xrange(self.m_uiNumPartitions):
                self.m_aapucBS[EDGE_HOR][uiPart] = 0
            for iPlane in xrange(3):
                for uiPart in xrange(self.m_uiNumPartitions):
                    self.m_aapbEdgeFilter[EDGE_HOR][iPlane][uiPart] = False

            # CU-based deblocking
            self._xDeblockCU(pcCU, 0, 0, EDGE_HOR)

    def _xDeblockCU(self, pcCU, uiAbsZorderIdx, uiDepth, Edge):
        if not pcCU.getPic() or pcCU.getPartitionSize(uiAbsZorderIdx) == SIZE_NONE:
            return
        pcPic = pcCU.getPic()
        uiCurNumParts = pcPic.getNumPartInCU() >> (uiDepth << 1)
        uiQNumParts = uiCurNumParts >> 2

        if pcCU.getDepth(uiAbsZorderIdx) > uiDepth:
            for uiPartIdx in xrange(4):
                uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsZorderIdx]]
                uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsZorderIdx]]
                if uiLPelX < pcCU.getSlice().getSPS().getPicWidthInLumaSamples() and \
                   uiTPelY < pcCU.getSlice().getSPS().getPicHeightInLumaSamples():
                    self._xDeblockCU(pcCU, uiAbsZorderIdx, uiDepth+1, Edge)
                uiAbsZorderIdx += uiQNumParts
            return

        self._xSetLoopfilterParam(pcCU, uiAbsZorderIdx)

        self._xSetEdgefilterTU(pcCU, uiAbsZorderIdx, uiAbsZorderIdx, uiDepth)
        self._xSetEdgefilterPU(pcCU, uiAbsZorderIdx)

        iDir = Edge
        for uiPartIdx in xrange(uiAbsZorderIdx, uiAbsZorderIdx+uiCurNumParts):
            uiBSCheck = 0
            if (cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth) == 4:
                uiBSCheck = (iDir == EDGE_VER and (uiPartIdx % 2) == 0) or \
                            (iDir == EDGE_HOR and (uiPartIdx-((uiPartIdx>>2)<<2))/2 == 0)
            else:
                uiBSCheck = 1

            if self.m_aapbEdgeFilter[iDir][0][uiPartIdx] and uiBSCheck:
                self._xGetBoundaryStrengthSingle(pcCU, uiAbsZorderIdx, iDir, uiPartIdx)

        uiPelsInPart = cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth
        PartIdxIncr = DEBLOCK_SMALLEST_BLOCK / uiPelsInPart \
                      if DEBLOCK_SMALLEST_BLOCK / uiPelsInPart else 1

        uiSizeInPU = pcPic.getNumPartInWidth() >> uiDepth

        for iEdge in xrange(0, uiSizeInPU, PartIdxIncr):
            self._xEdgeFilterLuma(pcCU, uiAbsZorderIdx, uiDepth, iDir, iEdge)
            if uiPelsInPart > DEBLOCK_SMALLEST_BLOCK or \
               (iEdge % ((DEBLOCK_SMALLEST_BLOCK<<1) / uiPelsInPart)) == 0:
                self._xEdgeFilterChroma(pcCU, uiAbsZorderIdx, uiDepth, iDir, iEdge)

    def _xSetLoopfilterParam(self, pcCU, uiAbsZorderIdx):
        uiX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsZorderIdx]]
        uiY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsZorderIdx]]

        pcTempCU = None
        uiTempPartIdx = 0

        self.m_stLFCUParam.bInternalEdge = False if self.m_uiDisableDeblockingFilterIdc else True

        if uiX == 0 or self.m_uiDisableDeblockingFilterIdc == 1:
            self.m_stLFCUParam.bLeftEdge = False
        else:
            self.m_stLFCUParam.bLeftEdge = True
        if self.m_stLFCUParam.bLeftEdge:
            pcTempCU, uiTempPartIdx = pcCU.getPULeft(
                uiTempPartIdx, uiAbsZorderIdx,
                not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                False, not self.m_bLFCrossTileBoundary)
            if pcTempCU:
                self.m_stLFCUParam.bLeftEdge = True
            else:
                self.m_stLFCUParam.bLeftEdge = False

        if uiY == 0 or self.m_uiDisableDeblockingFilterIdc == 1:
            self.m_stLFCUParam.bTopEdge = False
        else:
            self.m_stLFCUParam.bTopEdge = True
        if self.m_stLFCUParam.bTopEdge:
            pcTempCU, uiTempPartIdx = pcCU.getPUAbove(
                uiTempPartIdx, uiAbsZorderIdx,
                not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                False, False, False, not self.m_bLFCrossTileBoundary)
            if pcTempCU:
                self.m_stLFCUParam.bTopEdge = True
            else:
                self.m_stLFCUParam.bTopEdge = False

    def _xSetEdgefilterTU(self, pcCU, absTUPartIdx, uiAbsZorderIdx, uiDepth):
        if pcCU.getTransformIdx(uiAbsZorderIdx) + pcCU.getDepth(uiAbsZorderIdx) > uiDepth:
            uiCurNumParts = pcCU.getPic().getNumPartInCU() >> (uiDepth << 1)
            uiQNumParts = uiCurNumParts >> 2
            for uiPartIdx in xrange(4):
                nsAddr = uiAbsZorderIdx
                self._xSetEdgefilterTU(pcCU, nsAddr, uiAbsZorderIdx, uiDepth+1)
                uiAbsZorderIdx += uiQNumParts
            return

        trWidth = pcCU.getWidth(uiAbsZorderIdx) >> pcCU.getTransformIdx(uiAbsZorderIdx)
        trHeight = pcCU.getHeight(uiAbsZorderIdx) >> pcCU.getTransformIdx(uiAbsZorderIdx)

        uiWidthInBaseUnits = trWidth / (cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth)
        uiHeightInBaseUnits = trHeight / (cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth)

        self._xSetEdgefilterMultiple(pcCU, absTUPartIdx, uiDepth, EDGE_VER, 0,
                                     self.m_stLFCUParam.bInternalEdge,
                                     uiWidthInBaseUnits, uiHeightInBaseUnits)
        self._xSetEdgefilterMultiple(pcCU, absTUPartIdx, uiDepth, EDGE_HOR, 0,
                                     self.m_stLFCUParam.bInternalEdge,
                                     uiWidthInBaseUnits, uiHeightInBaseUnits)

    def _xSetEdgefilterPU(self, pcCU, uiAbsZorderIdx):
        uiDepth = pcCU.getDepth(uiAbsZorderIdx)
        uiWidthInBaseUnits = pcCU.getPic().getNumPartInWidth() >> uiDepth
        uiHeightInBaseUnits = pcCU.getPic().getNumPartInHeight() >> uiDepth
        uiHWidthInBaseUnits = uiWidthInBaseUnits >> 1
        uiHHeightInBaseUnits = uiHeightInBaseUnits >> 1
        uiQWidthInBaseUnits = uiWidthInBaseUnits >> 2
        uiQHeightInBaseUnits = uiHeightInBaseUnits >> 2

        self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_VER,
                                     0, self.m_stLFCUParam.bLeftEdge)
        self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_HOR,
                                     0, self.m_stLFCUParam.bTopEdge)

        uiPartSize = pcCU.getPartitionSize(uiAbsZorderIdx)
        if uiPartSize == SIZE_2Nx2N:
            pass
        elif uiPartSize == SIZE_2NxN:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_HOR,
                                         uiHHeightInBaseUnits, self.m_stLFCUParam.bInternalEdge)
        elif uiPartSize == SIZE_Nx2N:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_VER,
                                         uiHWidthInBaseUnits, self.m_stLFCUParam.bInternalEdge)
        elif uiPartSize == SIZE_NxN:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_VER,
                                         uiHWidthInBaseUnits, self.m_stLFCUParam.bInternalEdge)
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_HOR,
                                         uiHHeightInBaseUnits, self.m_stLFCUParam.bInternalEdge)
        elif uiPartSize == SIZE_2NxnU:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_HOR,
                                         uiQHeightInBaseUnits, self.m_stLFCUParam.bInternalEdge)
        elif uiPartSize == SIZE_2NxnD:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_HOR,
                                         uiHeightInBaseUnits - uiQHeightInBaseUnits, self.m_stLFCUParam.bInternalEdge)
        elif uiPartSize == SIZE_nLx2N:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_VER,
                                         uiQWidthInBaseUnits, self.m_stLFCUParam.bInternalEdge)
        elif uiPartSize == SIZE_nRx2N:
            self._xSetEdgefilterMultiple(pcCU, uiAbsZorderIdx, uiDepth, EDGE_VER,
                                         uiWidthInBaseUnits - uiQWidthInBaseUnits, self.m_stLFCUParam.bInternalEdge)

    def _xGetBoundaryStrengthSingle(self, pcCU, uiAbsZorderIdx, iDir, uiAbsPartIdx):
        pcSlice = pcCU.getSlice()

        uiPartQ = uiAbsPartIdx
        pcCUQ = pcCU

        uiPartP = 0
        pcCUP = None
        uiBs = 0

        #-- Calculate Block Index
        if iDir == EDGE_VER:
            pcCUP, uiPartP = pcCUQ.getPULeft(
                uiPartP, uiPartQ,
                not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                False, not self.m_bLFCrossTileBoundary)
        else: # (iDir == EDGE_HOR)
            pcCUP, uiPartP = pcCUQ.getPUAbove(
                uiPartP, uiPartQ,
                not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                False, False, False, not self.m_bLFCrossTileBoundary)
  
        #-- Set BS for Intra MB : BS = 4 or 3
        if pcCUP.isIntra(uiPartP) or pcCUQ.isIntra(uiPartQ):
            uiBs = 2
  
        #-- Set BS for not Intra MB : BS = 2 or 1 or 0
        if not pcCUP.isIntra(uiPartP) and not pcCUQ.isIntra(uiPartQ):
            nsPartQ = uiPartQ
            nsPartP = uiPartP

            if self.m_aapucBS[iDir][uiAbsPartIdx] and \
               (pcCUQ.getCbf(nsPartQ, TEXT_LUMA, pcCUQ.getTransformIdx(nsPartQ)) != 0 or
                pcCUP.getCbf(nsPartP, TEXT_LUMA, pcCUP.getTransformIdx(nsPartP)) != 0):
                uiBs = 1
            else:
                if iDir == EDGE_HOR:
                    pcCUP, uiPartP = pcCUQ.getPUAbove(
                        uiPartP, uiPartQ,
                        not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                        False, True, False, not self.m_bLFCrossTileBoundary)
                if pcSlice.isInterB():
                    iRefIdx = pcCUP.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiPartP)
                    piRefP0 = None if iRefIdx < 0 else pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx).getPOC() # Swig Fix
                    iRefIdx = pcCUP.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiPartP)
                    piRefP1 = None if iRefIdx < 0 else pcSlice.getRefPic(REF_PIC_LIST_1, iRefIdx).getPOC() # Swig Fix
                    iRefIdx = pcCUQ.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiPartQ)
                    piRefQ0 = None if iRefIdx < 0 else pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx).getPOC() # Swig Fix
                    iRefIdx = pcCUQ.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiPartQ)
                    piRefQ1 = None if iRefIdx < 0 else pcSlice.getRefPic(REF_PIC_LIST_1, iRefIdx).getPOC() # Swig Fix

                    pcMvP0 = pcCUP.getCUMvField(REF_PIC_LIST_0).getMv(uiPartP)
                    pcMvP1 = pcCUP.getCUMvField(REF_PIC_LIST_1).getMv(uiPartP)
                    pcMvQ0 = pcCUQ.getCUMvField(REF_PIC_LIST_0).getMv(uiPartQ)
                    pcMvQ1 = pcCUQ.getCUMvField(REF_PIC_LIST_1).getMv(uiPartQ)

                    if (piRefP0 == piRefQ0 and piRefP1 == piRefQ1) or \
                       (piRefP0 == piRefQ1 and piRefP1 == piRefQ0):
                        uiBs = 0
                        if piRefP0 != piRefP1: # Different L0 & L1
                            if piRefP0 == piRefQ0:
                                pcMvP0 = pcMvP0 - pcMvQ0 #pcMvP0 -= pcMvQ0 # Swig Fix
                                pcMvP1 = pcMvP1 - pcMvQ1 #pcMvP1 -= pcMvQ1 # Swig Fix
                                uiBs = 1 if pcMvP0.getAbsHor() >= 4 or pcMvP0.getAbsVer() >= 4 or \
                                            pcMvP1.getAbsHor() >= 4 or pcMvP1.getAbsVer() >= 4 else 0
                            else:
                                pcMvP0 = pcMvP0 - pcMvQ1 #pcMvP0 -= pcMvQ1 # Swig Fix
                                pcMvP1 = pcMvP1 - pcMvQ0 #pcMvP1 -= pcMvQ0 # Swig Fix
                                uiBs = 1 if pcMvP0.getAbsHor() >= 4 or pcMvP0.getAbsVer() >= 4 or \
                                            pcMvP1.getAbsHor() >= 4 or pcMvP1.getAbsVer() >= 4 else 0
                        else: # Same L0 & L1
                            pcMvSub0 = pcMvP0 - pcMvQ0
                            pcMvSub1 = pcMvP1 - pcMvQ1
                            pcMvP0 = pcMvP0 - pcMvQ1 #pcMvP0 -= pcMvQ1 # Swig Fix
                            pcMvP1 = pcMvP1 - pcMvQ0 #pcMvP1 -= pcMvQ0 # Swig Fix
                            uiBs = 1 if (pcMvP0.getAbsHor() >= 4 or pcMvP0.getAbsVer() >= 4 or
                                         pcMvP1.getAbsHor() >= 4 or pcMvP1.getAbsVer() >= 4) and \
                                        (pcMvSub0.getAbsHor() >= 4 or pcMvSub0.getAbsVer() >= 4 or
                                         pcMvSub1.getAbsHor() >= 4 or pcMvSub1.getAbsVer() >= 4) else 0
                    else: # for all different Ref_Idx
                        uiBs = 1
                else: # pcSlice->isInterP()
                    iRefIdx = pcCUP.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiPartP)
                    piRefP0 = None if iRefIdx < 0 else pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx).getPOC() # Swig Fix
                    iRefIdx = pcCUQ.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiPartQ)
                    piRefQ0 = None if iRefIdx < 0 else pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx).getPOC() # Swig Fix

                    pcMvP0 = pcCUP.getCUMvField(REF_PIC_LIST_0).getMv(uiPartP)
                    pcMvQ0 = pcCUQ.getCUMvField(REF_PIC_LIST_0).getMv(uiPartQ)
                    
                    pcMvP0 = pcMvP0 - pcMvQ0 #pcMvP0 -= pcMvQ0 # Swig Fix
                    uiBs = 1 if (piRefP0 != piRefQ0) or \
                                (pcMvP0.getAbsHor() >= 4 or pcMvP0.getAbsVer() >= 4) else 0

        self.m_aapucBS[iDir][uiAbsPartIdx] = uiBs

    def _xCalcBsIdx(self, pcCU, uiAbsZorderIdx, iDir, iEdgeIdx, iBaseUnitIdx):
        pcPic = pcCU.getPic()
        uiLCUWidthInBaseUnits = pcPic.getNumPartInWidth()
        if iDir == 0:
            return g_auiRasterToZscan[g_auiZscanToRaster[uiAbsZorderIdx] +
                iBaseUnitIdx * uiLCUWidthInBaseUnits + iEdgeIdx]
        else:
            return g_auiRasterToZscan[g_auiZscanToRaster[uiAbsZorderIdx] +
                iEdgeIdx * uiLCUWidthInBaseUnits + iBaseUnitIdx]

    def _xSetEdgefilterMultiple(self, pcCU, uiScanIdx, uiDepth, iDir, iEdgeIdx, bValue,
                                uiWidthInBaseUnits=0, uiHeightInBaseUnits=0, nonSquare=False):
        if uiWidthInBaseUnits == 0:
            uiWidthInBaseUnits = pcCU.getPic().getNumPartInWidth() >> uiDepth
        if uiHeightInBaseUnits == 0:
            uiHeightInBaseUnits = pcCU.getPic().getNumPartInHeight() >> uiDepth
        uiNumElem = uiHeightInBaseUnits if iDir == 0 else uiWidthInBaseUnits
        assert(uiNumElem > 0)
        assert(uiWidthInBaseUnits > 0)
        assert(uiHeightInBaseUnits > 0)
        for ui in xrange(uiNumElem):
            uiBsIdx = self._xCalcBsIdx(pcCU, uiScanIdx, iDir, iEdgeIdx, ui)
            self.m_aapbEdgeFilter[iDir][0][uiBsIdx] = bValue
            self.m_aapbEdgeFilter[iDir][1][uiBsIdx] = bValue
            self.m_aapbEdgeFilter[iDir][2][uiBsIdx] = bValue
            if iEdgeIdx == 0:
                self.m_aapucBS[iDir][uiBsIdx] = 1 if bValue else 0

    def _xEdgeFilterLuma(self, pcCU, uiAbsZorderIdx, uiDepth, iDir, iEdge):
        pcPicYuvRec = pcCU.getPic().getPicYuvRec()
        piSrc = pcPicYuvRec.getLumaAddr(pcCU.getAddr(), uiAbsZorderIdx)
        piTmpSrc = pointer(piSrc, type='short *')

        iStride = pcPicYuvRec.getStride()
        iQP = 0
        iQP_P = 0
        iQP_Q = 0
        uiNumParts = pcCU.getPic().getNumPartInWidth() >> uiDepth

        uiPelsInPart = cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth
        uiBsAbsIdx = 0
        uiBs = 0
        iOffset = 0
        iSrcStep = 0

        bPCMFilter = pcCU.getSlice().getSPS().getUsePCM() and \
                     pcCU.getSlice().getSPS().getPCMFilterDisableFlag()
        bPartPNoFilter = False
        bPartQNoFilter = False
        uiPartPIdx = 0
        uiPartQIdx = 0
        pcCUP = pcCU
        pcCUQ = pcCU

        if iDir == EDGE_VER:
            iOffset = 1
            iSrcStep = iStride
            piTmpSrc += iEdge * uiPelsInPart
        else: # (iDir == EDGE_HOR)
            iOffset = iStride
            iSrcStep = 1
            piTmpSrc += iEdge * uiPelsInPart * iStride

        for iIdx in xrange(uiNumParts):
            uiBsAbsIdx = self._xCalcBsIdx(pcCU, uiAbsZorderIdx, iDir, iEdge, iIdx)
            uiBs = self.m_aapucBS[iDir][uiBsAbsIdx]
            if uiBs:
                iQP_Q = Char(pcCU.getQP(uiBsAbsIdx))
                uiPartQIdx = uiBsAbsIdx
                # Derive neighboring PU index
                if iDir == EDGE_VER:
                    pcCUP, uiPartPIdx = pcCUQ.getPULeft(
                        uiPartPIdx, uiPartQIdx,
                        not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                        False, not self.m_bLFCrossTileBoundary)
                else: # (iDir == EDGE_HOR)
                    pcCUP, uiPartPIdx = pcCUQ.getPUAbove(
                        uiPartPIdx, uiPartQIdx,
                        not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                        False, False, False, not self.m_bLFCrossTileBoundary)

                iQP_P = Char(pcCUP.getQP(uiPartPIdx))
                iQP = (iQP_P + iQP_Q + 1) >> 1
                iBitdepthScale = 1 << (cvar.g_uiBitIncrement + cvar.g_uiBitDepth - 8)

                iIndexTC = Clip3(0, MAX_QP+DEFAULT_INTRA_TC_OFFSET,
                                 iQP+DEFAULT_INTRA_TC_OFFSET*(uiBs-1) + (self.m_tcOffsetDiv2<<1))
                iIndexB = Clip3(0, MAX_QP, iQP + (self.m_betaOffsetDiv2<<1))

                iTc = tctable_8x8[iIndexTC] * iBitdepthScale
                iBeta = betatable_8x8[iIndexB] * iBitdepthScale
                iSideThreshold = (iBeta + (iBeta >> 1)) >> 3
                iThrCut = iTc * 10

                uiBlocksInPart = uiPelsInPart / 4 if uiPelsInPart / 4 else 1
                for iBlkIdx in xrange(uiBlocksInPart):
                    dp0 = self._xCalcDP(piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + 0), iOffset)
                    dq0 = self._xCalcDQ(piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + 0), iOffset)
                    dp3 = self._xCalcDP(piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + 3), iOffset)
                    dq3 = self._xCalcDQ(piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + 3), iOffset)
                    d0 = dp0 + dq0
                    d3 = dp3 + dq3

                    dp = dp0 + dp3
                    dq = dq0 + dq3
                    d = d0 + d3

                    if bPCMFilter:
                        # Check if each of PUs is I_PCM
                        bPartPNoFilter = pcCUP.getIPCMFlag(uiPartPIdx)
                        bPartQNoFilter = pcCUQ.getIPCMFlag(uiPartQIdx)
                    # check if each of PUs is lossless coded
                    bPartPNoFilter = bPartPNoFilter or pcCUP.isLosslessCoded(uiPartPIdx)
                    bPartQNoFilter = bPartQNoFilter or pcCUQ.isLosslessCoded(uiPartQIdx)
                    if d < iBeta:
                        bFilterP = dp < iSideThreshold
                        bFilterQ = dq < iSideThreshold

                        sw = self._xUseStrongFiltering(iOffset, 2*d0, iBeta, iTc, piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + 0)) and \
                             self._xUseStrongFiltering(iOffset, 2*d3, iBeta, iTc, piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + 3))

                        for i in xrange(DEBLOCK_SMALLEST_BLOCK/2):
                            self._xPelFilterLuma(
                                piTmpSrc + iSrcStep * (iIdx * uiPelsInPart + iBlkIdx * 4 + i),
                                iOffset, d, iBeta, iTc, sw, bPartPNoFilter, bPartQNoFilter, iThrCut, bFilterP, bFilterQ)
               
    def _xEdgeFilterChroma(self, pcCU, uiAbsZorderIdx, uiDepth, iDir, iEdge):
        pcPicYuvRec = pcCU.getPic().getPicYuvRec()
        iStride = pcPicYuvRec.getCStride()
        piSrcCb = pcPicYuvRec.getCbAddr(pcCU.getAddr(), uiAbsZorderIdx)
        piSrcCr = pcPicYuvRec.getCrAddr(pcCU.getAddr(), uiAbsZorderIdx)
        iQP = 0
        iQP_P = 0
        iQP_Q = 0

        uiPelsInPartChroma = cvar.g_uiMaxCUWidth >> (cvar.g_uiMaxCUDepth+1)

        iOffset = 0
        iSrcStep = 0

        uiLCUWidthInBaseUnits = pcCU.getPic().getNumPartInWidth()

        bPCMFilter = pcCU.getSlice().getSPS().getUsePCM() and \
                     pcCU.getSlice().getSPS().getPCMFilterDisableFlag()
        bPartPNoFilter = False
        bPartQNoFilter = False
        uiPartPIdx = 0
        uiPartQIdx = 0
        pcCUP = pcCU
        pcCUQ = pcCU

        # Vertical Position
        uiEdgeNumInLCUVert = g_auiZscanToRaster[uiAbsZorderIdx] % uiLCUWidthInBaseUnits + iEdge
        uiEdgeNumInLCUHor = g_auiZscanToRaster[uiAbsZorderIdx] / uiLCUWidthInBaseUnits + iEdge

        if (uiPelsInPartChroma < DEBLOCK_SMALLEST_BLOCK) and \
           (((uiEdgeNumInLCUVert % (DEBLOCK_SMALLEST_BLOCK / uiPelsInPartChroma)) and iDir == 0) or
            ((uiEdgeNumInLCUHor % (DEBLOCK_SMALLEST_BLOCK / uiPelsInPartChroma)) and iDir)):
            return

        uiNumParts = pcCU.getPic().getNumPartInWidth() >> uiDepth

        uiBsAbsIdx = 0
        ucBs = 0

        piTmpSrcCb = pointer(piSrcCb, type='short *')
        piTmpSrcCr = pointer(piSrcCr, type='short *')

        if iDir == EDGE_VER:
            iOffset = 1
            iSrcStep = iStride
            piTmpSrcCb += iEdge * uiPelsInPartChroma
            piTmpSrcCr += iEdge * uiPelsInPartChroma
        else: # (iDir == EDGE_HOR)
            iOffset = iStride
            iSrcStep = 1
            piTmpSrcCb += iEdge * iStride * uiPelsInPartChroma
            piTmpSrcCr += iEdge * iStride * uiPelsInPartChroma

        for iIdx in xrange(uiNumParts):
            ucBs = 0

            uiBsAbsIdx = self._xCalcBsIdx(pcCU, uiAbsZorderIdx, iDir, iEdge, iIdx)
            ucBs = self.m_aapucBS[iDir][uiBsAbsIdx]

            if ucBs > 1:
                iQP_Q = Char(pcCU.getQP(uiBsAbsIdx))
                uiPartQIdx = uiBsAbsIdx
                # Derive neighboring PU index
                if iDir == EDGE_VER:
                    pcCUP, uiPartPIdx = pcCUQ.getPULeft(
                        uiPartPIdx, uiPartQIdx,
                        not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                        False, not self.m_bLFCrossTileBoundary)
                else: # (iDir == EDGE_HOR)
                    pcCUP, uiPartPIdx = pcCUQ.getPUAbove(
                        uiPartPIdx, uiPartQIdx,
                        not pcCU.getSlice().getLFCrossSliceBoundaryFlag(),
                        False, False, False, not self.m_bLFCrossTileBoundary)

                iQP_P = Char(pcCUP.getQP(uiPartPIdx))
                iQP = QpUV((iQP_P + iQP_Q + 1) >> 1)
                iBitdepthScale = 1 << (cvar.g_uiBitIncrement + cvar.g_uiBitDepth - 8)

                iIndexTC = Clip3(0, MAX_QP+DEFAULT_INTRA_TC_OFFSET,
                                 iQP+DEFAULT_INTRA_TC_OFFSET*(ucBs-1) + (self.m_tcOffsetDiv2<<1))
                iTc = tctable_8x8[iIndexTC] * iBitdepthScale

                if bPCMFilter:
                    # Check if each of PUs is IPCM
                    bPartPNoFilter = pcCUP.getIPCMFlag(uiPartPIdx)
                    bPartQNoFilter = pcCUQ.getIPCMFlag(uiPartQIdx)
                
                # check if each of PUs is lossless coded
                bPartPNoFilter = bPartPNoFilter or pcCUP.isLosslessCoded(uiPartPIdx)
                bPartQNoFilter = bPartQNoFilter or pcCUQ.isLosslessCoded(uiPartQIdx)
                for uiStep in xrange(uiPelsInPartChroma):
                    self._xPelFilterChroma(
                        piTmpSrcCb + iSrcStep * (uiStep + iIdx * uiPelsInPartChroma),
                        iOffset, iTc, bPartPNoFilter, bPartQNoFilter)
                    self._xPelFilterChroma(
                        piTmpSrcCr + iSrcStep * (uiStep + iIdx * uiPelsInPartChroma),
                        iOffset, iTc, bPartPNoFilter, bPartQNoFilter)

    def _xPelFilterLuma(self, piSrc, iOffset, d, beta, tc, sw,
                        bPartPNoFilter, bPartQNoFilter, iThrCut, bFilterSecondP, bFilterSecondQ):
        piSrc = pointer(piSrc, bias=-iOffset*4, type='short *')

        m4 = piSrc[+iOffset*0]
        m3 = piSrc[-iOffset*1]
        m5 = piSrc[+iOffset*1]
        m2 = piSrc[-iOffset*2]
        m6 = piSrc[+iOffset*2]
        m1 = piSrc[-iOffset*3]
        m7 = piSrc[+iOffset*3]
        m0 = piSrc[-iOffset*4]

        if sw:
            piSrc[-iOffset*1] = Clip3(m3-2*tc, m3+2*tc, (m1+2*m2+2*m3+2*m4+m5+4) >> 3)
            piSrc[+iOffset*0] = Clip3(m4-2*tc, m4+2*tc, (m2+2*m3+2*m4+2*m5+m6+4) >> 3)
            piSrc[-iOffset*2] = Clip3(m2-2*tc, m2+2*tc, (m1+m2+m3+m4+2) >> 2)
            piSrc[+iOffset*1] = Clip3(m5-2*tc, m5+2*tc, (m3+m4+m5+m6+2) >> 2)
            piSrc[-iOffset*3] = Clip3(m1-2*tc, m1+2*tc, (2*m0+3*m1+m2+m3+m4+4) >> 3)
            piSrc[+iOffset*2] = Clip3(m6-2*tc, m6+2*tc, (m3+m4+m5+3*m6+2*m7+4) >> 3)
        else:
            # Weak filter
            delta = (9*(m4-m3) - 3*(m5-m2) + 8) >> 4

            if abs(delta) < iThrCut:
                delta = Clip3(-tc, tc, delta)
                piSrc[-iOffset*1] = Clip(m3+delta)
                piSrc[+iOffset*0] = Clip(m4-delta)

                tc2 = tc >> 1
                if bFilterSecondP:
                    delta1 = Clip3(-tc2, tc2, (((m1+m3+1)>>1) - m2 + delta) >> 1)
                    piSrc[-iOffset*2] = Clip(m2+delta1)
                if bFilterSecondQ:
                    delta2 = Clip3(-tc2, tc2, (((m6+m4+1)>>1) - m5 - delta) >> 1)
                    piSrc[+iOffset*1] = Clip(m5+delta2)

        if bPartPNoFilter:
            piSrc[-iOffset*1] = m3
            piSrc[-iOffset*2] = m2
            piSrc[-iOffset*3] = m1
        if bPartQNoFilter:
            piSrc[+iOffset*0] = m4
            piSrc[+iOffset*1] = m5
            piSrc[+iOffset*2] = m6

    def _xPelFilterChroma(self, piSrc, iOffset, tc, bPartPNoFilter, bPartQNoFilter):
        piSrc = pointer(piSrc, bias=-iOffset*2, type='short *')

        m4 = piSrc[+iOffset*0]
        m3 = piSrc[-iOffset*1]
        m5 = piSrc[+iOffset*1]
        m2 = piSrc[-iOffset*2]

        delta = Clip3(-tc, tc, (((m4-m3)<<2) + m2 - m5 + 4) >> 3)
        piSrc[-iOffset*1] = Clip(m3+delta)
        piSrc[+iOffset*0] = Clip(m4-delta)

        if bPartPNoFilter:
            piSrc[-iOffset*1] = m3
        if bPartQNoFilter:
            piSrc[+iOffset*0] = m4

    def _xUseStrongFiltering(self, offset, d, beta, tc, piSrc):
        piSrc = pointer(piSrc, bias=-offset*4, type='short *')

        m4 = piSrc[+offset*0]
        m3 = piSrc[-offset*1]
        m7 = piSrc[+offset*3]
        m0 = piSrc[-offset*4]

        d_strong = abs(m0-m3) + abs(m7-m4)

        return d_strong < (beta>>3) and d < (beta>>2) and abs(m3-m4) < ((tc*5+1)>>1)

    def _xCalcDP(self, piSrc, iOffset):
        piSrc = pointer(piSrc, bias=-iOffset*3, type='short *')

        return abs(piSrc[-iOffset*3] - 2*piSrc[-iOffset*2] + piSrc[-iOffset*1])

    def _xCalcDQ(self, piSrc, iOffset):
        piSrc = pointer(piSrc, type='short *')

        return abs(piSrc[+iOffset*0] - 2*piSrc[+iOffset*1] + piSrc[+iOffset*2])
