# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComPicSym.py
    HM 8.0 Python Implementation
"""

import sys

from ... import SAOParam
from ... import TComSlice
from ... import TComDataCU
from ... import TComSampleAdaptiveOffset


class TComTile(object):

    def __init__(self):
        self.m_uiTileWidth = 0
        self.m_uiTileHeight = 0
        self.m_uiRightEdgePosInCU = 0
        self.m_uiBottomEdgePosInCU = 0
        self.m_uiFirstCUAddr = 0

    def setTileWidth(self, i):
        self.m_uiTileWidth = i
    def getTileWidth(self, i):
        return self.m_uiTileWidth
    def setTileHeight(self, i):
        self.m_uiTileHeight = i
    def getTileHeight(self, i):
        return self.m_uiTileHeight
    def setRightEdgePosInCU(self, i):
        self.m_uiRightEdgePosInCU = i
    def getRightEdgePosInCU(self, i):
        return self.m_uiRightEdgePosInCU
    def setBottomEdgePosInCU(self, i):
        self.m_uiBottomEdgePosInCU = i
    def getBottomEdgePosInCU(self, i):
        return self.m_uiBottomEdgePosInCU
    def setFirstCUAddr(self, i):
        self.m_uiFirstCUAddr = i
    def getFirstCUAddr(self):
        return self.m_uiFirstCUAddr


class TComPicSym(object):

    def __init__(self):
        self.m_uiWidthInCU = 0
        self.m_uiHeightInCU = 0

        self.m_uiMaxCUWidth = 0
        self.m_uiMaxCUHeight = 0
        self.m_uiMinCUWidth = 0
        self.m_uiMinCUHeight = 0

        self.m_uhTotalDepth = 0
        self.m_uiNumPartitions = 0
        self.m_uiNumPartInWidth = 0
        self.m_uiNumPartInHeight = 0
        self.m_uiNumCUsInFrame = 0

        self.m_apcTComSlice = None
        self.m_uiNumAllocatedSlice = 0
        self.m_apcTComDataCU = None

        self.m_iTileBoundaryIndependenceIdr = 0
        self.m_iNumColumnsMinus1 = 0
        self.m_iNumRowsMinus1 = 0
        self.m_apcTComTile = None
        self.m_puiCUOrderMap = None
        self.m_puiTileIdxMap = None
        self.m_puiInverseCUOrderMap = None

        self.m_saoParam = None

    def create(self, iPicWidth, iPicHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth):
        self.m_uhTotalDepth = uiMaxDepth
        self.m_uiNumPartitions = 1 << (self.m_uhTotalDepth<<1)

        self.m_uiMaxCUWidth = uiMaxWidth
        self.m_uiMaxCUHeight = uiMaxHeight

        self.m_uiMinCUWidth = uiMaxWidth >> self.m_uhTotalDepth
        self.m_uiMinCUHeight = uiMaxHeight >> self.m_uhTotalDepth

        self.m_uiNumPartInWidth = self.m_uiMaxCUWidth / self.m_uiMinCUWidth
        self.m_uiNumPartInHeight = self.m_uiMaxCUHeight / self.m_uiMinCUHeight

        self.m_uiWidthInCU = iPicWidth/self.m_uiMaxCUWidth+1 if iPicWidth % self.m_uiMaxCUWidth else iPicWidth/self.m_uiMaxCUWidth
        self.m_uiHeightInCU = iPicHeight/self.m_uiMaxCUHeight+1 if iPicHeight % self.m_uiMaxCUHeight else iPicHeight/self.m_uiMaxCUHeight

        self.m_uiNumCUsInFrame = self.m_uiWidthInCU * self.m_uiHeightInCU
        self.m_apcTComDataCU = self.m_uiNumCUsInFrame * [None]

        if self.m_uiNumAllocatedSlice > 0:
            for i in xrange(self.m_uiNumAllocatedSlice):
                del self.m_apcTComSlice[i]
            del self.m_apcTComSlice
        self.m_apcTComSlice = (self.m_uiNumCUsInFrame * self.m_uiNumPartitions) * [None]
        self.m_apcTComSlice[0] = TComSlice()
        for i in xrange(self.m_uiNumCUsInFrame):
            self.m_apcTComDataCU[i] = TComDataCU()
            self.m_apcTComDataCU[i].create(
                self.m_uiNumPartitions, self.m_uiMaxCUWidth, self.m_uiMaxCUHeight,
                False, self.m_uiMaxCUWidth >> self.m_uhTotalDepth, True)

        self.m_puiCUOrderMap = (self.m_uiNumCUsInFrame+1) * [0]
        self.m_puiTileIdxMap = self.m_uiNumCUsInFrame * [0]
        self.m_puiInverseCUOrderMap = (self.m_uiNumCUsInFrame+1) * [0]

        for i in xrange(self.m_uiNumCUsInFrame):
            self.m_puiCUOrderMap[i] = i
            self.m_puiInverseCUOrderMap[i] = i
        self.m_saoParam = None

    def destroy(self):
        if self.m_uiNumAllocatedSlice > 0:
            for i in xrange(self.m_uiNumAllocatedSlice):
                del self.m_apcTComSlice[i]
            del self.m_apcTComSlice
        self.m_apcTComSlice = None

        for i in xrange(self.m_uiNumCUsInFrame):
            self.m_apcTComDataCU[i].destroy()
            del self.m_apcTComDataCU[i]
            self.m_apcTComDataCU[i] = None
        del self.m_apcTComDataCU
        self.m_apcTComDataCU = None

        for i in xrange((self.m_iNumColumnsMinus1+1)*(self.m_iNumRowsMinus1+1)):
            del self.m_apcTComTile[i]
        del self.m_apcTComTile
        self.m_apcTComTile = None

        del self.m_puiCUOrderMap
        self.m_puiCUOrderMap = None

        del self.m_puiTileIdxMap
        self.m_puiTileIdxMap = None

        del self.m_puiInverseCUOrderMap
        self.m_puiInverseCUOrderMap = None

        if self.m_saoParam:
            TComSampleAdaptiveOffset.freeSaoParam(self.m_saoParam)
            del self.m_saoParam
            self.m_saoParam = None

    def getSlice(self, i):
        return self.m_apcTComSlice[i]
    def getFrameWidthInCU(self):
        return self.m_uiWidthInCU
    def getFrameHeightInCU(self):
        return self.m_uiHeightInCU
    def getMinCUWidth(self):
        return self.m_uiMinCUWidth
    def getMinCUHeight(self):
        return self.m_uiMinCUHeight
    def getNumberOfCUsInFrame(self):
        return self.m_uiNumCUsInFrame
    def getCU(self, uiCUAddr):
        return self.m_apcTComDataCU[uiCUAddr]

    def setSlice(self, p, i):
        self.m_apcTComSlice[i] = p
    def getNumAllocatedSlice(self):
        return self.m_uiNumAllocatedSlice

    def allocateNewSlice(self):
        self.m_apcTComSlice[self.m_uiNumAllocatedSlice] = TComSlice()
        self.m_uiNumAllocatedSlice += 1
        if self.m_uiNumAllocatedSlice >= 2:
            self.m_apcTComSlice[self.m_uiNumAllocatedSlice-1].copySliceInfo(self.m_apcTComSlice[self.m_uiNumAllocatedSlice-2])
            self.m_apcTComSlice[self.m_uiNumAllocatedSlice-1].initSlice()
            self.m_apcTComSlice[self.m_uiNumAllocatedSlice-1].initTiles()

    def clearSliceBuffer(self):
        for i in xrange(self.m_uiNumAllocatedSlice):
            del self.m_apcTComSlice[i]
        self.m_uiNumAllocatedSlice = 1

    def getNumPartition(self):
        return self.m_uiNumPartitions
    def getNumPartInWidth(self):
        return self.m_uiNumPartInWidth
    def getNumPartInHeight(self):
        return self.m_uiNumPartInHeight

    def setNumColumnsMinus1(self, i):
        self.m_iNumColumnsMinus1 = i
    def getNumColumnsMinus1(self):
        return self.m_iNumColumnsMinus1
    def setNumRowsMinus1(self, i):
        self.m_iNumRowsMinus1 = i
    def getNumRowsMinus1(self):
        return self.m_iNumRowsMinus1

    def getNumTiles(self):
        return (self.m_iNumRowsMinus1+1)*(self.m_iNumColumnsMinus1+1)
    def getTComTile(self, tileIdx):
        return self.m_apcTComTile[tileIdx]

    def setCUOrderMap(self, encCUOrder, cuAddr):
        self.m_puiCUOrderMap[encCUOrder] = cuAddr
    def getCUOrderMap(self, encCUOrder):
        return self.m_puiCUOrderMap[self.m_uiNumCUsInFrame if encCUOrder >= self.m_uiNumCUsInFrame else encCUOrder]
    def getTileIdxMap(self, i):
        return self.m_puiTileIdxMap[i]
    def setInverseCUOrderMap(self, cuAddr, encCUOrder):
        self.m_puiInverseCUOrderMap[cuAddr] = encCUOrder
    def getInverseCUOrderMap(self, cuAddr):
        return self.m_puiInverseCUOrderMap[self.m_uiNumCUsInFrame if cuAddr >= self.m_uiNumCUsInFrame else cuAddr]
    def getPicSCUEncOrder(self, SCUAddr):
        return self.getInverseCUOrderMap(SCUAddr/self.m_uiNumPartitions) * \
            self.m_uiNumPartitions + SCUAddr % self.m_uiNumPartitions
    def getPicSCUAddr(self, SCUEncOrder):
        return self.getCUOrderMap(SCUEncOrder/self.m_uiNumPartitions) * \
            self.m_uiNumPartitions + SCUEncOrder % self.m_uiNumPartitions

    def xCreateTComTileArray(self):
        self.m_apcTComTile = ((self.m_iNumColumnsMinus1+1)*(self.m_iNumRowsMinus1+1)) * [None]
        for i in xrange((self.m_iNumColumnsMinus1+1)*(self.m_iNumRowsMinus1+1)):
            self.m_apcTComTile[i] = TComTile()

    def xInitTiles(self):
        #initialize each tile of the current picture
        for uiRowIdx in xrange(self.m_iNumRowsMinus1+1):
            for uiColumnIdx in xrange(self.m_iNumColumnsMinus1+1):
                uiTileIdx = uiRowIdx * (self.m_iNumColumnsMinus1+1) + uiColumnIdx

                #initialize the RightEdgePosInCU for each tile
                uiRightEdgePosInCU = 0
                for i in xrange(uiColumnIdx+1):
                    uiRightEdgePosInCU += self.getTComTile(uiRowIdx * (self.m_iNumColumnsMinus1+1) + 1).getTileWidth()
                self.getTComTile(uiTileIdx).setRightEdgePosInCU(uiRightEdgePosInCU-1)

                #initialize the BottomEdgePosInCU for each tile
                uiBottomEdgePosInCU = 0
                for i in xrange(uiRowIdx+1):
                    uiBottomEdgePosInCU += self.getTComTile(i * (self.m_iNumColumnsMinus1+1) + uiColumnIdx).getTileHeight()
                self.getTComTile(uiTileIdx).setBottomEdgePosInCU(uiBottomEdgePosInCU-1)

                #initialize the FirstCUAddr for each tile
                self.getTComTile(uiTileIdx).setFirstCUAddr(
                    (self.getTComTile(uiTileIdx).getBottomEdgePosInCU() - self.getTComTile(uiTileIdx).getTileHeight() + 1) * self.m_uiWidthInCU +
                    (self.getTComTile(uiTileIdx).getRightEdgePosInCU() - self.getTComTile(uiTileIdx).getTileWidth() + 1))

        #initialize the TileIdxMap
        for i in xrange(self.m_uiNumCUsInFrame):
            for j in xrange(self.m_iNumColumnsMinus1+1):
                if i % self.m_uiWidthInCU <= self.getTComTile(j).getRightEdgePosInCU():
                    uiColumnIdx = j
                    j = self.m_iNumColumnsMinus1+1
            for j in xrange(self.m_iNumRowsMinus1+1):
                if i / self.m_uiWidthInCU <= self.getTComTile(j*(self.m_iNumColumnsMinus1+1)).getBottomEdgePosInCU():
                    uiRowIdx = j
                    j = self.m_iNumRowsMinus1+1
            self.m_puiTileIdxMap[i] = uiRowIdx * (self.m_iNumColumnsMinus1+1) + uiColumnIdx

    def xCalculateNxtCUAddr(self, uiCurrCUAddr):
        #get the tile index for the current LCU
        uiTileIdx = self.getTileIdxMap(uiCurrCUAddr)

        #get the raster scan address for the next LCU
        if uiCurrCUAddr % self.m_uiWidthInCU == self.getTComTile(uiTileIdx).getRightEdgePosInCU() and \
           uiCurrCUAddr / self.m_uiWidthInCU == self.getTComTile(uiTileIdx).getBottomEdgePosInCU():
            #the current LCU is the last LCU of the tile
            if uiTileIdx == (self.m_iNumColumnsMinus1+1)*(self.m_iNumRowsMinus1+1)-1:
                uiNxtCUAddr = self.m_uiNumCUsInFrame
            else:
                uiNxtCUAddr = self.getTComTile(uiTileIdx+1).getFirstCUAddr()
        else:
            #the current LCU is not the last LCU of the tile
            if uiCurrCUAddr % self.m_uiWidthInCU == self.getTComTile(uiTileIdx).getRightEdgePosInCU():
                #the current LCU is on the rightmost edge of the tile
                uiNxtCUAddr = uiCurrCUAddr + self.m_uiWidthInCU - self.getTComTile(uiTileIdx).getTileWidth() + 1
            else:
                uiNxtCUAddr = uiCurrCUAddr + 1

        return uiNxtCUAddr

    def allocSaoParam(self, sao):
        self.m_saoParam = SAOParam()
        sao.allocSaoParam(self.m_saoParam)
    def getSaoParam(self):
        return self.m_saoParam
