# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComPicYuv.py
    HM 8.0 Python Implementation
"""

import sys

from ... import cvar

from ... import NDBFBlockInfo

from .CommonDef import Clip3

from .TComRom import g_auiZscanToRaster


class TComPicYuv(object):

    def __init__(self):
        self.m_apiPicBufY = None
        self.m_apiPicBufU = None
        self.m_apiPicBufV = None

        self.m_piPicOrgY = None
        self.m_piPicOrgU = None
        self.m_piPicOrgV = None

        self.m_iPicWidth = 0
        self.m_iPicHeight = 0

        self.m_iCuWidth = 0
        self.m_iCuHeight = 0
        self.m_cuOffsetY = None
        self.m_cuOffsetC = None
        self.m_buOffsetY = None
        self.m_buOffsetC = None

        self.m_iLumaMarginX = 0
        self.m_iLumaMarginY = 0
        self.m_iChromaMarginX = 0
        self.m_iChromaMarginY = 0

        self.m_bIsBorderExtended = False

    def create(self, iPicWidth, iPicHeight, uiMaxCUWidth, uiMaxCUHeight, uiMaxCUDepth):
        self.m_iPicWidth = iPicWidth
        self.m_iPicHeight = iPicHeight

        # --> After config finished!
        self.m_iCuWidth = uiMaxCUWidth
        self.m_iCuHeight = uiMaxCUHeight

        numCuInWidth = self.m_iPicWidth / self.m_iCuWidth + (self.m_iPicWidth % self.m_iCuWidth != 0)
        numCuInHeight = self.m_iPicHeight / self.m_iCuHeight + (self.m_iPicHeight % self.m_iCuHeight != 0)

        self.m_iLumaMarginX = cvar.g_uiMaxCUWidth + 16 # for 16-byte alignment
        self.m_iLumaMarginY = cvar.g_uiMaxCUHeight + 16 # margin for 8-tap filter and infinite padding

        self.m_iChromaMarginX = self.m_iLumaMarginX >> 1
        self.m_iChromaMarginY = self.m_iLumaMarginY >> 1

        self.m_apiPicBufY = ArrayPel(( self.m_iPicWidth     + (self.m_iLumaMarginX  <<1)) * ( self.m_iPicHeight     + (self.m_iLumaMarginY  <<1)))
        self.m_apiPicBufU = ArrayPel(((self.m_iPicWidth>>1) + (self.m_iChromaMarginX<<1)) * ((self.m_iPicHeight>>1) + (self.m_iChromaMarginY<<1)))
        self.m_apiPicBufV = ArrayPel(((self.m_iPicWidth>>1) + (self.m_iChromaMarginX<<1)) * ((self.m_iPicHeight>>1) + (self.m_iChromaMarginY<<1)))

        self.m_piPicOrgY = self.m_apiPicBufY + self.m_iLumaMarginY * self.getStride() + self.m_iLumaMarginX
        self.m_piPicOrgU = self.m_apiPicBufU + self.m_iChromaMarginY * self.getCStride() + self.m_iChromaMarginX
        self.m_piPicOrgV = self.m_apiPicBufV + self.m_iChromaMarginY * self.getCStride() + self.m_iChromaMarginX

        self.m_bIsBorderExtended = False

        self.m_cuOffsetY = ArrayInt(numCuInWidth * numCuInHeight)
        self.m_cuOffsetC = ArrayInt(numCuInWidth * numCuInHeight)
        for cuRow in xrange(numCuInHeight):
            for cuCol in xrange(numCuInWidth):
                self.m_cuOffsetY[cuRow * numCuInWidth + cuCol] = self.getStride() * cuRow * self.m_iCuHeight + cuCol * self.m_iCuWidth
                self.m_cuOffsetC[cuRow * numCuInWidth + cuCol] = self.getCStride() * cuRow * (self.m_iCuHeight/2) + cuCol * (self.m_iCuWidth/2)

        self.m_buOffsetY = ArrayInt(1 << (2 * uiMaxCUDepth))
        self.m_buOffsetC = ArrayInt(1 << (2 * uiMaxCUDepth))
        for buRow in xrange(1 << uiMaxCUDepth):
            for buCol in xrange(1 << uiMaxCUDepth):
                self.m_buOffsetY[(buRow << uiMaxCUDepth) + buCol] = self.getStride() * buRow * (uiMaxCUHeight >> uiMaxCUDepth) + buCol * (uiMaxCUWidth >> uiMaxCUDepth)
                self.m_buOffsetC[(buRow << uiMaxCUDepth) + buCol] = self.getCStride() * buRow * (uiMaxCUHeight/2 >> uiMaxCUDepth) + buCol * (uiMaxCUWidth/2 >> uiMaxCUDepth)

    def destroy(self):
        self.m_piPicOrgY = None
        self.m_piPicOrgU = None
        self.m_piPicOrgV = None

        if self.m_apiPicBufY:
            del self.m_apiPicBufY
            self.m_apiPicBufY = None
        if self.m_apiPicBufU:
            del self.m_apiPicBufU
            self.m_apiPicBufU = None
        if self.m_apiPicBufV:
            del self.m_apiPicBufV
            self.m_apiPicBufV = None

        del self.m_cuOffsetY
        del self.m_cuOffsetC
        del self.m_buOffsetY
        del self.m_buOffsetC

    def createLuma(self, iPicWidth, iPicHeight, uiMaxCUWidth, uiMaxCUHeight, uiMaxCUDepth):
        self.m_iPicWidth = iPicWidth
        self.m_iPicHeight = iPicHeight

        # --> After config finished!
        self.m_iCuWidth = uiMaxCUWidth
        self.m_iCuHeight = uiMaxCUHeight

        numCuInWidth = self.m_iPicWidth / self.m_iCuWidth + (self.m_iPicWidth % self.m_iCuWidth != 0)
        numCuInHeight = self.m_iPicHeight / self.m_iCuHeight + (self.m_iPicHeight % self.m_iCuHeight != 0)

        self.m_iLumaMarginX = cvar.g_uiMaxCUWidth + 16 # for 16-byte alignment
        self.m_iLumaMarginY = cvar.g_uiMaxCUHeight + 16 # margin for 8-tap filter and infinite padding

        self.m_apiPicBufY = ArrayPel((self.m_iPicWidth + (self.m_iLumaMarginX<<1)) * (self.m_iPicHeight + (self.m_iLumaMarginY<<1)))
        self.m_piPicOrgY = self.apiPicBufY + self.m_iLumaMarginY * self.getStride() + self.m_iLumaMarginX

        self.m_cuOffsetY = ArrayInt(numCuInWidth * numCuInHeight)
        self.m_cuOffsetC = None
        for cuRow in xrange(numCuInHeight):
            for cuCol in xrange(numCuInWidth):
                self.m_cuOffsetY[cuRow * numCuInWidth + cuCol] = self.getStride() * cuRow * self.m_iCuHeight + cuCol * self.m_iCuWidth

        self.m_buOffsetY = ArrayInt(1 << (2 * uiMaxCUDepth))
        self.m_buOffsetC = None
        for buRow in xrange(1 << uiMaxCUDepth):
            for buCol in xrange(1 << uiMaxCUDepth):
                self.m_buOffsetY[(buRow << uiMaxCUDepth) + buCol] = self.getStride() * buRow * (uiMaxCUHeight >> uiMaxCUDepth) + buCol * (uiMaxCUWidth >> uiMaxCUDepth)

    def destroyLuma(self):
        self.m_piPicOrgY = None

        if self.m_apiPicBufY:
            del self.m_apiPicBufY
            self.m_apiPicBufY = None

        del self.m_cuOffsetY
        del self.m_buOffsetY

    def getWidth(self):
        return self.m_iPicWidth
    def getHeight(self):
        return self.m_iPicHeight

    def getStride(self):
        return self.m_iPicWidth + (self.m_iLumaMarginX << 1)
    def getCStride(self):
        return (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1)

    def getLumaMargin(self):
        return self.m_iLumaMarginX
    def getChromaMargin(self):
        return self.m_iChromaMarginX

    def getLumaMinMax(self, pMin, pMax):
        piY = self.getLumaAddr()
        iMin = (1 << cvar.g_uiBitDepth) - 1
        iMax = 0

        for y in xrange(self.m_iPicHeight):
            for x in xrange(self.m_iPicWidth):
                if piY[x] < iMin:
                    iMin = piY[x]
                if piY[x] > iMax:
                    iMax = piY[x]
            piY += self.getStride()

        pMin[0] = iMin
        pMax[0] = iMax

    def getBufY(self):
        return self.m_apiPicBufY
    def getBufU(self):
        return self.m_apiPicBufU
    def getBufV(self):
        return self.m_apiPicBufV

    def getLumaAddr(self, iCuAddr=None, uiAbsZorderIdx=None):
        if iCuAddr == None and uiAbsZorderIdx == None:
            return self.m_piPicOrgY
        if uiAbsZorderIdx == None:
            return self.m_piPicOrgY + self.m_cuOffsetY[iCuAddr]
        return self.m_piPicOrgY + self.m_cuOffsetY[iCuAddr] + self.m_buOffsetY[g_auiZscanToRaster[uiAbsZorderIdx]]
    def getCrAddr(self, iCuAddr=None, uiAbsZorderIdx=None):
        if iCuAddr == None and uiAbsZorderIdx == None:
            return self.m_piPicOrgU
        if uiAbsZorderIdx == None:
            return self.m_piPicOrgU + self.m_cuOffsetC[iCuAddr]
        return self.m_piPicOrgU + self.m_cuOffsetC[iCuAddr] + self.m_buOffsetC[g_auiZscanToRaster[uiAbsZorderIdx]]
    def getCrAddr(self, iCuAddr=None, uiAbsZorderIdx=None):
        if iCuAddr == None and uiAbsZorderIdx == None:
            return self.m_piPicOrgV
        if uiAbsZorderIdx == None:
            return self.m_piPicOrgV + self.m_cuOffsetC[iCuAddr]
        return self.m_piPicOrgV + self.m_cuOffsetC[iCuAddr] + self.m_buOffsetC[g_auiZscanToRaster[uiAbsZorderIdx]]

    def copyToPic(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        for i in xrange((self.m_iPicWidth + (self.m_iLumaMarginX<<1)) * (self.m_iPicHeight + (self.m_iLumaMarginY<<1))):
            pcPicYuvDst.getBufY()[i] = self.m_apiPicBufY[i]
        for i in xrange(((self.m_iPicWidth>>1) + (self.m_iChromaMarginX<<1)) * ((self.m_iPicHeight>>1) + (self.m_iChromaMarginY<<1))):
            pcPicYuvDst.getBufU()[i] = self.m_apiPicBufU[i]
        for i in xrange(((self.m_iPicWidth>>1) + (self.m_iChromaMarginX<<1)) * ((self.m_iPicHeight>>1) + (self.m_iChromaMarginY<<1))):
            pcPicYuvDst.getBufV()[i] = self.m_apiPicBufV[i]

    def copyToPicLuma(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        for i in xrange((self.m_iPicWidth + (self.m_iLumaMarginX<<1)) * (self.m_iPicHeight + (self.m_iLumaMarginY<<1))):
            pcPicYuvDst.getBufY()[i] = self.m_apiPicBufY[i]

    def copyToPicCb(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        for i in xrange(((self.m_iPicWidth>>1) + (self.m_iChromaMarginX<<1)) * ((self.m_iPicHeight>>1) + (self.m_iChromaMarginY<<1))):
            pcPicYuvDst.getBufU()[i] = self.m_apiPicBufU[i]

    def copyToPicCr(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        for i in xrange(((self.m_iPicWidth>>1) + (self.m_iChromaMarginX<<1)) * ((self.m_iPicHeight>>1) + (self.m_iChromaMarginY<<1))):
            pcPicYuvDst.getBufV()[i] = self.m_apiPicBufV[i]

    def extendPicBorder(self):
        if self.m_bIsBorderExtended:
            return

        self.xExtendPicCompBorder(self.getLumaAddr(), self.getStride(), self.getWidth(), self.getHeight(), self.m_iLumaMarginX, self.m_iLumaMarginY)
        self.xExtendPicCompBorder(self.getCbAddr(), self.getCStride(), self.getWidth() >> 1, self.getHeight() >> 1, self.m_iChromaMarginX, self.m_iChromaMarginY)
        self.xExtendPicCompBorder(self.getCrAddr(), self.getCStride(), self.getWidth() >> 1, self.getHeight() >> 1, self.m_iChromaMarginX, self.m_iChromaMarginY)

        self.m_bIsBorderExtended = True

    def xExtendPicCompBorder(self, piTxt, iStride, iWidth, iHeight, iMarginX, iMarginY):
        pi = piTxt
        for y in xrange(iHeight):
            for x in xrange(iMarginX):
                pi[-iMarginX + x] = pi[0]
                pi[   iWidth + x] = pi[iWidth - 1]
            pi += iStride

        pi -= iStride + iMarginX
        for y in xrange(iMarginY):
            for x in xrange(iWidth + (iMarginX<<1)):
                pi[(y+1) * iStride + x] = pi[x]

        pi -= (iHeight-1) * iStride
        for y in xrange(iMarginY):
            for x in xrange(iWidth + (iMarginX<<1)):
                pi[-(y+1) * iStride + x] = pi[x]

    def dump(self, pFileName, bAdd=False):
        pFile = None
        if not bAdd:
            pFile = open(pFileName, "wb")
        else:
            pFile = open(pFileName, "ab")

        shift = cvar.g_uiBitIncrement
        offset = 1 << (shift-1) if shift > 0 else 0

        piY = self.getLumaAddr()
        piCb = self.getCbAddr()
        piCr = self.getCrAddr()

        iMax = (1 << cvar.g_uiBitDepth) - 1

        for y in xrange(self.m_iPicHeight):
            for x in xrange(self.m_iPicWidth):
                uc = Clip3(0, iMax, (piY[x] + offset) >> shift)
                pFile.write(uc)
            piY += self.getStride()

        for y in xrange(self.m_iPicHeight >> 1):
            for x in xrange(self.m_iPicWidth >> 1):
                uc = Clip3(0, iMax, (piCb[x] + offset) >> shift)
                pFile.write(uc)
            piCb += self.getCStride()

        for y in xrange(self.m_iPicHeight >> 1):
            for x in xrange(self.m_iPicWidth >> 1):
                uc = Clip3(0, iMax, (piCr[x] + offset) >> shift)
                pFile.write(uc)
            piCr += self.getCStride()

        pFile.close()

    def setBorderExtension(self, b):
        self.m_bIsBorderExtended = b


def calcChecksum(pic, digest):
    pass
def calcCRC(pic, digest):
    pass
def calcMD5(pic, digest):
    pass
