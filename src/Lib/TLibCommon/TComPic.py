# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComPic.py
    HM 8.0 Python Implementation
"""

import sys

from ... import cvar

from ... import TComPicSym
from ... import TComPicYuv
from ... import NDBFBlockInfo

from .TComRom import (g_auiZscanToRaster, g_auiRasterToPelX, g_auiRasterToPelY)


class TComPic(object):

    def __init__(self):
        self.m_uiTLayer = 0
        self.m_bUsedByCurr = False
        self.m_bIsLongTerm = False
        self.m_bIsUsedAsLongTerm = False
        self.m_apcPicSym = None

        self.m_apcPicYuv = [None, None]

        self.m_pcPicYuvPred = None
        self.m_pcPicYuvResi = None
        self.m_bReconstructed = False
        self.m_bNeededForOutput = False
        self.m_uiCurrSliceIdx = 0
        self.m_pSliceSUMap = None
        self.m_pbValidSlice = None
        self.m_sliceGranularityForNDBFilter = 0
        self.m_bIndependentSliceBoundaryForNDBFilter = False
        self.m_bIndependentTileBoundaryForNDBFilter = False
        self.m_pNDBFilterYuvTmp = None
        self.m_bCheckLTMSB = False
        self.m_vSliceCUDataLink = []

        self.m_SEIs = None
        self.m_uiCurrDepSliceIdx = 0

    def create(self, iWidth, iHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth, bIsVirtual=False):
        self.m_apcPicSym = TComPicSym()
        self.m_apcPicSym.create(iWidth, iHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth)
        if not bIsVirtual:
            self.m_apcPicYuv[0] = TComPicYuv()
            self.m_apcPicYuv[0].create(iWidth, iHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth)
        self.m_apcPicYuv[1] = TComPicYuv()
        self.m_apcPicYuv[1].create(iWidth, iHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth)

        # there are no SEI messages associated with this picture initially
        self.m_SEIs = None
        self.m_bUsedByCurr = False

    def destroy(self):
        if self.m_apcPicSym:
            self.m_apcPicSym.destroy()
            del self.m_apcPicSym
            self.m_apcPicSym = None

        if self.m_apcPicYuv[0]:
            self.m_apcPicYuv[0].destroy()
            del self.m_apcPicYuv[0]
            self.m_apcPicYuv[0] = None

        if self.m_apcPicYuv[1]:
            self.m_apcPicYuv[1].destroy()
            del self.m_apcPicYuv[1]
            self.m_apcPicYuv[1] = None

        if self.m_SEIs:
            del self.m_SEIs

    def getTLayer(self):
        return self.m_uiTLayer
    def setTLayer(self, uiTLayer):
        self.m_uiTLayer = uiTLayer

    def getUsedByCurr(self):
        return self.m_bUsedByCurr
    def setUsedByCurr(self, bUsed):
        self.m_bUsedByCurr = bUsed
    def getIsLongTerm(self):
        return self.m_bIsLongTerm
    def setIsLongTerm(self, lt):
        self.m_bIsLongTerm = lt
    def getIsUsedAsLongTerm(self):
        return self.m_bIsUsedAsLongTerm
    def setIsUsedAsLongTerm(self, lt):
        self.m_bIsUsedAsLongTerm = lt
    def setCheckLTMSBPresent(self, b):
        self.m_bCheckLTMSB = b
    def getCheckLTMSBPresent(self):
        return self.m_bCheckLTMSB

    def getPicSym(self):
        return self.m_apcPicSym
    def getSlice(self, i):
        return self.m_apcPicSym.getSlice(i)
    def getPOC(self):
        return self.m_apcPicSym.getSlice(self.m_uiCurrSliceIdx).getPOC()
    def getCU(self, uiCUAddr):
        return self.m_apcPicSym.getCU(uiCUAddr)

    def getPicYuvOrg(self):
        return self.m_apcPicYuv[0]
    def getPicYuvRec(self):
        return self.m_apcPicYuv[1]

    def getPicYuvPred(self):
        return self.m_pcPicYuvPred
    def getPicYuvResi(self):
        return self.m_pcPicYuvResi
    def setPicYuvPred(self, pcPicYuv):
        self.m_pcPicYuvPred = pcPicYuv
    def setPicYuvResi(self, pcPicYuv):
        self.m_pcPicYuvResi = pcPicYuv

    def getNumCUsInFrame(self):
        return self.m_apcPicSym.getNumberOfCUsInFrame()
    def getNumPartInWidth(self):
        return self.m_apcPicSym.getNumPartInWidth()
    def getNumPartInHeight(self):
        return self.m_apcPicSym.getNumPartInHeight()
    def getNumPartInCU(self):
        return self.m_apcPicSym.getNumPartition()
    def getFrameWidthInCU(self):
        return self.m_apcPicSym.getFrameWidthInCU()
    def getFrameHeightInCU(self):
        return self.m_apcPicSym.getFrameHeightInCU()
    def getMinCUWidth(self):
        return self.m_apcPicSym.getMinCUWidth()
    def getMinCUHeight(self):
        return self.m_apcPicSym.getMinCUHeight()

    def getParPelX(self, uhPartIdx):
        return self.getParPelX(uhPartIdx)
    def getParPelY(self, uhPartIdx):
        return self.getParPelY(uhPartIdx)

    def getStride(self):
        return self.m_apcPicYuv[1].getStride()
    def getCStride(self):
        return self.m_apcPicYuv[1].getCStride()

    def setReconMask(self, b):
        self.m_bReconstructed = b
    def getReconMask(self):
        return self.m_bReconstructed
    def setOutputMask(self, b):
        self.m_bNeededForOutput = b
    def getOutputMask(self):
        return self.m_bNeededForOutput

    def compressMotion(self):
        pPicSym = self.getPicSym()
        for uiCUAddr in xrange(pPicSym.getFrameHeightInCU()*pPicSym.getFrameWidthInCU()):
            pcCU = pPicSym.getCU(uiCUAddr)
            pcCU.compressMV()

    def getCurrSliceIdx(self):
        return self.m_uiCurrSliceIdx
    def setCurrSliceIdx(self, i):
        self.m_uiCurrSliceIdx = i
    def getNumAllocatedSlice(self):
        return self.m_apcPicSym.getNumAllocatedSlice()
    def allocateNewSlice(self):
        self.m_apcPicSym.allocateNewSlice()
    def clearSliceBuffer(self):
        self.m_apcPicSym.clearSliceBuffer()

    def createNonDBFilterInfo(self, sliceStartAddress, sliceGranularityDepth,
                              LFCrossSliceBoundary,
                              numTiles=1, bNDBFilterCrossTileBoundary=True):
        maxNumSUInLCU = self.getNumPartInCU()
        numLCUInPic = self.getNumCUsInFrame()
        picWidth = self.getSlice(0).getSPS().getPicWidthInLumaSamples()
        picHeight = self.getSlice(0).getSPS().getPicHeightInLumaSamples()
        numLCUsInPicWidth = self.getFrameWidthInCU()
        numLCUsInPicHeight = self.getFrameHeightInCU()
        maxNumSUInLCUWidth = self.getNumPartInWidth()
        maxNumSUInLCUHeight = self.getNumPartInHeight()
        numSlices = len(sliceStartAddress) - 1
        self.m_bIndependentSliceBoundaryForNDBFilter = False
        if numSlices > 1:
            for s in xrange(numSlices):
                if LFCrossSliceBoundary[s] == False:
                    self.m_bIndependentSliceBoundaryForNDBFilter = True
        self.m_sliceGranularityForNDBFilter = sliceGranularityDepth
        self.m_bIndependentTileBoundaryForNDBFilter = \
            False if bNDBFilterCrossTileBoundary else \
            True if numTiles > 1 else False

        self.m_pbValidSlice = numSlices * [True]
        self.m_pSliceSUMap = (maxNumSUInLCU*numLCUInPic) * [-1]

        for CUAddr in xrange(numLCUInPic):
            pcCU = self.getCU(CUAddr)
            pcCU.setSliceSUMap(self.m_pSliceSUMap + CUAddr*maxNumSUInLCU)
            pcCU.getNDBFilterBlocks().clear()
        self.m_vSliceCUDataLink.clear()
        self.m_vSliceCUDataLink.resize(numSlices)

        for s in xrange(numSlices):
            #1st step: decide the real start address
            startAddr = sliceStartAddress[s]
            endAddr = sliceStartAddress[s+1] - 1

            startLCU = startAddr / maxNumSUInLCU
            firstCUInStartLCU = startAddr % maxNumSUInLCU

            endLCU = endAddr / maxNumSUInLCU
            lastCUInEndLCU = endAddr % maxNumSUInLCU

            uiAddr = self.m_apcPicSym.getCUOrderMap(startLCU)

            LCUX = self.getCU(uiAddr).getCUPelX()
            LCUY = self.getCU(uiAddr).getCUPelY()
            LPelX = LCUX + g_auiRasterToPelX[g_auiZscanToRaster[firstCUInStartLCU]]
            TPelY = LCUY + g_auiRasterToPelY[g_auiZscanToRaster[firstCUInStartLCU]]
            currSU = firstCUInStartLCU

            bMoveToNextLCU = False
            bSliceInOneLCU = startLCU == endLCU

            while not (LPelX < picWidth) or not (TPelY < picHeight):
                currSU += 1

                if bSliceInOneLCU:
                    if currSU > lastCUInEndLCU:
                        self.m_pbValidSlice[s] = False
                        break

                if currSU >= maxNumSUInLCU:
                    bMoveToNextLCU = True
                    break

                LPelX = LCUX + g_auiRasterToPelX[g_auiZscanToRaster[currSU]]
                TPelY = LCUY + g_auiRasterToPelY[g_auiZscanToRaster[currSU]]

            if not self.m_pbValidSlice[s]:
                continue

            if currSU != firstCUInStartLCU:
                if not bMoveToNextLCU:
                    firstCUInStartLCU = currSU
                else:
                    startLCU += 1
                    firstCUInStartLCU = 0
                    assert(startLCU < self.getNumCUsInFrame())
                assert(startLCU*maxNumSUInLCU + firstCUInStartLCU < endAddr)

            #2nd step: assign NonDBFilterInfo to each processing block
            for i in xrange(startLCU, endLCU+1):
                startSU = firstCUInStartLCU if i == startLCU else 0
                endSU = lastCUInEndLCU if i == endLCU else maxNumSUInLCU-1

                uiAddr = self.m_apcPicSym.getCUOrderMap(i)
                iTileID = self.m_apcPicSym.getTileIdxMap(uiAddr)

                pcCU = self.getCU(uiAddr)
                self.m_vSliceCUDataLink[s].push_back(pcCU)

                self.createNonDBFilterInfoLCU(iTileID, s, pcCU, startSU, endSU,
                    self.m_sliceGranularityForNDBFilter, picWidth, picHeight)

        #step 3: border availability
        for s in xrange(numSlices):
            if not self.m_pbValidSlice[s]:
                continue

            for i in xrange(self.m_vSliceCUDataLink[s].size()):
                pcCU = self.m_vSliceCUDataLink[s][i]
                uiAddr = pcCU.getAddr()

                if not pcCU.getPic():
                    continue
                iTileID = self.m_apcPicSym.getTileIdxMap(uiAddr)
                bTopTileBoundary = False
                bDownTileBoundary = False
                bLeftTileBoundary = False
                bRightTileBoundary = False

                if self.m_bIndependentTileBoundaryForNDBFilter:
                    #left
                    if uiAddr % numLCUsInPicWidth != 0:
                        bLeftTileBoundary = True if self.m_apcPicSym.getTileIdxMap(uiAddr-1) != iTileID else False
                    #right
                    if uiAddr % numLCUsInPicWidth != numLCUsInPicWidth-1:
                        bRightTileBoundary = True if self.m_apcPicSym.getTileIdxMap(uiAddr+1) != iTileID else False
                    #top
                    if uiAddr >= numLCUsInPicWidth:
                        bTopTileBoundary = True if self.m_apcPicSym.getTileIdxMap(uiAddr-numLCUsInPicWidth) != iTileID else False
                    #down
                    if uiAddr + numLCUsInPicWidth < numLCUInPic:
                        bDownTileBoundary = True if self.m_apcPicSym.getTileIdxMap(uiAddr+numLCUsInPicWidth) != iTileID else False

                pcCU.setNDBFilterBlockBorderAvailability(
                    numLCUsInPicWidth, numLCUsInPicHeight,
                    maxNumSUInLCUWidth, maxNumSUInLCUHeight,
                    picWidth, picHeight, LFCrossSliceBoundary,
                    bTopTileBoundary, bDownTileBoundary,
                    bLeftTileBoundary, bRightTileBoundary,
                    self.m_bIndependentTileBoundaryForNDBFilter)

        if self.m_bIndependentSliceBoundaryForNDBFilter or self.m_bIndependentTileBoundaryForNDBFilter:
            self.m_pNDBFilterYuvTmp = TComPicYuv()
            self.m_pNDBFilterYuvTmp.create(
                picWidth, picHeight,
                cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth)

    def createNonDBFilterInfoLCU(self, tileID, sliceID, pcCU,
                                 startSU, endSU, sliceGranularityDepth,
                                 picWidth, picHeight):
        LCUX = pcCU.getCUPelX()
        LCUY = pcCU.getCUPelY()
        pCUSliceMap = pcCU.getSliceSUMap()
        maxNumSUInLCU = self.getNumPartInCU()
        maxNumSUInSGU = maxNumSUInLCU >> (sliceGranularityDepth << 1)
        maxNumSUInLCUWidth = self.getNumPartInWidth()

        #get the number of valid NBFilterBLock
        currSU = startSU
        while currSU <= endSU:
            LPelX = LCUX + g_auiRasterToPelX[g_auiZscanToRaster[currSU]]
            TPelY = LCUY + g_auiRasterToPelY[g_auiZscanToRaster[currSU]]

            while not (LPelX < picWidth) or not (TPelY < picHeight):
                currSU += maxNumSUInSGU
                if currSU >= maxNumSUInLCU or currSU > endSU:
                    break
                LPelX = LCUX + g_auiRasterToPelX[g_auiZscanToRaster[currSU]]
                TPelY = LCUY + g_auiRasterToPelY[g_auiZscanToRaster[currSU]]

            if currSU >= maxNumSUInLCU or currSU > endSU:
                break

            NDBFBlock = NDBFBlockInfo()

            NDBFBlock.tileID  = tileID
            NDBFBlock.sliceID = sliceID
            NDBFBlock.posY    = TPelY
            NDBFBlock.posX    = LPelX
            NDBFBlock.startSU = currSU

            uiLastValidSU = currSU
            for uiIdx in xrange(currSU, currSU+maxNumSUInSGU):
                if uiIdx > endSU:
                    break
                uiLPelX_su = LCUX + g_auiRasterToPelX[g_auiZscanToRaster[uiIdx]]
                uiTPelY_su = LCUY + g_auiRasterToPelY[g_auiZscanToRaster[uiIdx]]
                if not (uiLPelX_su < picWidth) or not (uiTPelY_su < picHeight):
                    continue
                pCUSliceMap[uiIdx] = sliceID
                uiLastValidSU = uiIdx
            NDBFBlock.endSU = uiLastValidSU

            rTLSU = g_auiZscanToRaster[NDBFBlock.startSU]
            rBRSU = g_auiZscanToRaster[NDBFBlock.endSU]
            NDBFBlock.widthSU = (rBRSU % maxNumSUInLCUWidth) - (rTLSU % maxNumSUInLCUWidth) + 1
            NDBFBlock.heightSU = (rBRSU / maxNumSUInLCUWidth) - (rTLSU / maxNumSUInLCUWidth) + 1
            NDBFBlock.width = NDBFBlock.widthSU * self.getMinCUWidth()
            NDBFBlock.height = NDBFBlock.heightSU * self.getMinCUHeight()

            pcCU.getNDBFilterBlocks().push_back(NDBFBlock)

            currSU += maxNumSUInSGU

    def destroyNonDBFilterInfo(self):
        if self.m_pbValidSlice != None:
            del self.m_pbValidSlice
            self.m_pbValidSlice = None

        if self.m_pSliceSUMap != None:
            del self.m_pSliceSUMap
            self.m_pSliceSUMap = None

        for CUAddr in xrange(self.getNumCUsInFrame()):
            pcCU = self.getCU(CUAddr)
            pcCU.getNDBFilterBlocks().clear()

        if self.m_bIndependentSliceBoundaryForNDBFilter or self.m_bIndependentTileBoundaryForNDBFilter:
            self.m_pNDBFilterYuvTmp.destroy()
            del self.m_pNDBFilterYuvTmp
            self.m_pNDBFilterYuvTmp = None

    def getValidSlice(self, sliceID):
        return self.m_pbValidSlice[sliceID]
    def getIndependentSliceBoundaryForNDBFilter(self):
        return self.m_bIndependentSliceBoundaryForNDBFilter
    def getIndependentTileBoundaryForNDBFilter(self):
        return self.m_bIndependentTileBoundaryForNDBFilter
    def getYuvPicBufferForIndependentBoundaryProcessing(self):
        return self.m_pNDBFilterYuvTmp
    def getOneSliceCUDataForNDBFilter(self, sliceID):
        return self.m_vSliceCUDataLink[sliceID]

    def setSEIs(self, seis):
        self.m_SEIs = seis
    def getSEIs(self):
        return self.m_SEIs

    def getCurrDepSliceIdx(self):
        return self.m_uiCurrDepSliceIdx
    def setCurrDepSliceIdx(self, i):
        self.m_uiCurrDepSliceIdx = i
