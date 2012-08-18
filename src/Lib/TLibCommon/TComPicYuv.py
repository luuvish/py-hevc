#!/usr/bin/env python

from .TComRom import g_uiBitIncrement,
                     g_uiBitDepth,
                     g_uiMaxCUWidth,
                     g_uiMaxCUHeight,
                     g_auiZscanToRaster


class TComPicYuv:

    def __init__(self):
        self.m_apiPicBufY = []
        self.m_apiPicBufU = []
        self.m_apiPicBufV = []

        self.m_piPicOrgY = []
        self.m_piPicOrgU = []
        self.m_piPicOrgV = []

        self.m_bIsBorderExtended = False

    def create(self, iPicWidth, iPicHeight, uiMaxCUWidth, uiMaxCUHeight, uiMaxCUDepth):
        self.m_iPicWidth = iPicWidth
        self.m_iPicHeight = iPicHeight

        self.m_iCuWidth = uiMaxCUWidth
        self.m_iCuHeight = uiMaxCUHeight

        numCuInWidth = self.m_iPicWidth / self.m_iCuWidth + (self.m_iPicWidth % self.m_iCuWidth != 0)
        numCuInHeight = self.m_iPicHeight / self.m_iCuHeight + (self.m_iPicHeight % self.m_iCuHeight != 0)

        self.m_iLumaMarginX = g_uiMaxCUWidth + 16
        self.m_iLumaMarginY = g_uiMaxCUHeight + 16

        self.m_iChromaMarginX = self.m_iLumaMarginX >> 1
        self.m_iChromaMarginY = self.m_iLumaMarginY >> 1

        self.m_apiPicBufY = [] # array('h') (self.m_iPicWidth + (self.m_iLumaMarginX << 1)) * (self.m_iPicHeight + (self.m_iLumaMarginY << 1))
        self.m_apiPicBufU = [] # array('h') (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1)) * ((self.m_iPicHeight >> 1) + (self.m_iChromaMarginY << 1))
        self.m_apiPicBufV = [] # array('h') (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1)) * ((self.m_iPicHeight >> 1) + (self.m_iChromaMarginY << 1))

        self.m_piPicOrgY = self.m_iLumaMarginY * self.getStride() + self.m_iLumaMarginX
        self.m_piPicOrgU = self.m_iChromaMarginY * self.getCStride() + self.m_iChromaMarginX
        self.m_piPicOrgV = self.m_iChromaMarginY * self.getCStride() + self.m_iChromaMarginX

        self.m_bIsBorderExtended = False

        self.m_cuOffsetY = [] # array('l') (numCuInWidth * numCuInHeight)
        self.m_cuOffsetC = [] # array('l') (numCuInWidth * numCuInHeight)
        for cuRow in range(0, numCuInHeight):
            for cuCol in range(0, numCuInWidth):
                self.m_cuOffsetY[cuRow * numCuInWidth + cuCol] = self.getStride() * cuRow * self.m_iCuHeight + cuCol * self.m_iCuWidth
                self.m_cuOffsetC[cuRow * numCuInWidth + cuCol] = self.getCStride() * cuRow * (self.m_iCuHeight / 2) + cuCol * (self.m_iCuWidth / 2)

        self.m_buOffsetY = [] # array('l') (1 << (2 * uiMaxCUDepth))
        self.m_buOffsetC = [] # array('l') (1 << (2 * uiMaxCUDepth))
        for buRow in range(0, 1 << uiMaxCUDepth):
            for buCol in range(0, 1 << uiMaxCUDepth):
                self.m_buOffsetY[(buRow << uiMaxCUDepth) + buCol] = self.getStride() * buRow * (uiMaxCUHeight >> uiMaxCUDepth) + buCol * (uiMaxCUWidth >> uiMaxCUDepth)
                self.m_buOffsetC[(buRow << uiMaxCUDepth) + buCol] = self.getCStride() * buRow * (uiMaxCUHeight / 2 >> uiMaxCUDepth) + buCol * (uiMaxCUWidth / 2 >> uiMaxCUDepth)

    def destroy(self):
        self.m_piPicOrgY = 0
        self.m_piPicOrgU = 0
        self.m_piPicOrgV = 0

        self.m_apiPicBufY = []
        self.m_apiPicBufU = []
        self.m_apiPicBufV = []

        self.m_cuOffsetY = []
        self.m_cuOffsetC = []
        self.m_buOffsetY = []
        self.m_buOffsetC = []

    def createLuma(self, iPicWidth, iPicHeight, uiMaxCUWidth, uiMaxCUHeight, uiMaxCUDepth):
        self.m_iPicWidth = iPicWidth
        self.m_iPicHeight = iPicHeight

        self.m_iCuWidth = uiMaxCUWidth
        self.m_iCuHeight = uiMaxCUHeight

        numCuInWidth = self.m_iPicWidth / self.m_iCuWidth + (self.m_iPicWidth % self.m_iCuWidth != 0)
        numCuInHeight = self.m_iPicHeight / self.m_iCuHeight + (self.m_iPicHeight % self.m_iCuHeight != 0)

        self.m_iLumaMarginX = g_uiMaxCUWidth + 16
        self.m_iLumaMarginY = g_uiMaxCUHeight + 16

        self.m_apiPicBufY = [] # array('h') (self.m_iPicWidth + (self.m_iLumaMarginX << 1)) * (self.m_iPicHeight + (self.m_iLumaMarginY << 1))
        self.m_piPicOrgY = self.m_iLumaMarginY * self.getStride() + self.m_iLumaMarginX

        self.m_cuOffsetY = [] # array('l') (numCuInWidth * numCuInHeight)
        self.m_cuOffsetC = []
        for cuRow in range(0, numCuInHeight):
            for cuCol in range(0, numCuInWidth):
                self.m_cuOffsetY[cuRow * numCuInWidth + cuCol] = self.getStride() * cuRow * self.m_iCuHeight + cuCol * self.m_iCuWidth

        self.m_buOffsetY = [] # array('l') (1 << (2 * uiMaxCUDepth))
        self.m_buOffsetC = []
        for buRow in range(0, 1 << uiMaxCUDepth):
            for buCol in range(0, 1 << uiMaxCUDepth):
                self.m_buOffsetY[(buRow << uiMaxCUDepth) + buCol] = self.getStride() * buRow * (uiMaxCUHeight >> uiMaxCUDepth) + buCol * (uiMaxCUWidth >> uiMaxCUDepth)

    def destroyLuma(self):
        self.m_piPicOrgY = 0

        self.m_apiPicBufY = []

        self.m_cuOffsetY = []
        self.m_buOffsetY = []

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
        apiY = self.getBufY()
        piY = self.getLumaAddr()
        iMin = (1 << g_uiBitDepth) - 1
        iMax = 0

        for y in range(0, self.m_iPicHeight):
            for x in range(0, self.m_iPicWidth):
                if apiY[piY + x] < iMin:
                    iMin = apiY[piY + x]
                if apiY[piY + x] > iMax:
                    iMax = apiY[piY + x]
            piY += self.getStride()

        pMin = iMin
        pMax = iMax
        return pMin, pMax

    def getBufY(self):
        return self.m_apiPicBufY
    def getBufU(self):
        return self.m_apiPicBufU
    def getBufV(self):
        return self.m_apiPicBufV

    def getLumaAddr(self):
        return self.m_piPicOrgY
    def getCbAddr(self):
        return self.m_piPicOrgU
    def getCrAddr(self):
        return self.m_piPicOrgV

    def getLumaAddr(self, iCuAddr):
        return self.m_piPicOrgY + self.m_cuOffsetY[iCuAddr]
    def getCrAddr(self, iCuAddr):
        return self.m_piPicOrgU + self.m_cuOffsetC[iCuAddr]
    def getCrAddr(self, iCuAddr):
        return self.m_piPicOrgV + self.m_cuOffsetC[iCuAddr]
    def getLumaAddr(self, iCuAddr, uiAbsZorderIdx):
        return self.m_piPicOrgY + self.m_cuOffsetY[iCuAddr] + self.m_buOffsetY[g_auiZscanToRaster[uiAbsZorderIdx]]
    def getCrAddr(self, iCuAddr, uiAbsZorderIdx):
        return self.m_piPicOrgU + self.m_cuOffsetC[iCuAddr] + self.m_buOffsetC[g_auiZscanToRaster[uiAbsZorderIdx]]
    def getCrAddr(self, iCuAddr, uiAbsZorderIdx):
        return self.m_piPicOrgV + self.m_cuOffsetC[iCuAddr] + self.m_buOffsetC[g_auiZscanToRaster[uiAbsZorderIdx]]

    def copyToPic(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        dst, src = pcPicYuvDst.getBufY(), self.m_apiPicBufY
        for i in range(0, self.m_iPicWidth + (self.m_iLumaMarginX << 1) * (self.m_iPicHeight + (self.m_iLumaMarginY << 1))):
            dst[i] = src[i]
        dst, src = pcPicYuvDst.getBufU(), self.m_apiPicBufU
        for i in range(0, (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1) * ((self.m_iPicHeight >> 1) + (self.m_iChromaMarginY << 1))):
            dst[i] = src[i]
        dst, src = pcPicYuvDst.getBufV(), self.m_apiPicBufV
        for i in range(0, (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1) * ((self.m_iPicHeight >> 1) + (self.m_iChromaMarginY << 1))):
            dst[i] = src[i]

    def copyToPicLuma(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        dst, src = pcPicYuvDst.getBufY(), self.m_apiPicBufY
        for i in range(0, self.m_iPicWidth + (self.m_iLumaMarginX << 1) * (self.m_iPicHeight + (self.m_iLumaMarginY << 1))):
            dst[i] = src[i]

    def copyToPicCb(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        dst, src = pcPicYuvDst.getBufU(), self.m_apiPicBufU
        for i in range(0, (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1) * ((self.m_iPicHeight >> 1) + (self.m_iChromaMarginY << 1))):
            dst[i] = src[i]

    def copyToPicCr(self, pcPicYuvDst):
        assert(self.m_iPicWidth == pcPicYuvDst.getWidth())
        assert(self.m_iPicHeight == pcPicYuvDst.getHeight())

        dst, src = pcPicYuvDst.getBufV(), self.m_apiPicBufV
        for i in range(0, (self.m_iPicWidth >> 1) + (self.m_iChromaMarginX << 1) * ((self.m_iPicHeight >> 1) + (self.m_iChromaMarginY << 1))):
            dst[i] = src[i]

    def extendPicBorder(self):
        if self.m_bIsBorderExtended:
            return

        self.xExtendPicCompBorder(self.getBufY(), self.getLumaAddr(), self.getStride(), self.getWidth(), self.getHeight(), self.m_iLumaMarginX, self.m_iLumaMarginY)
        self.xExtendPicCompBorder(self.getBufU(), self.getCbAddr(), self.getCStride(), self.getWidth() >> 1, self.getHeight() >> 1, self.m_iChromaMarginX, self.m_iChromaMarginY)
        self.xExtendPicCompBorder(self.getBufV(), self.getCrAddr(), self.getCStride(), self.getWidth() >> 1, self.getHeight() >> 1, self.m_iChromaMarginX, self.m_iChromaMarginY)

        self.m_bIsBorderExtended = True

    def xExtendPicCompBorder(self, apiTxt, piTxt, iStride, iWidth, iHeight, iMarginX, iMarginY):
        api = apiTxt
        pi = piTxt
        for y in range(0, iHeight):
            for x in range(0, iMarginX):
                api[pi - iMarginX + x] = api[pi + 0]
                api[pi + iWidth + x] = api[pi + iWidth - 1]
            pi += iStride

        pi -= iStride + iMarginX
        for y in range(0, iMarginY):
            for x in range(0, iWidth + (iMarginX << 1)):
                api[pi + (y + 1) * iStride + x] = api[pi + x]

        pi -= (iHeight - 1) * iStride
        for y in range(0, iMarginY):
            for x in range(0, iWidth + (iMarginX << 1)):
                api[pi - (y + 1) * iStride + x] = api[pi + x]

    def dump(self, pFileName, bAdd=False):
        if not bAdd:
            pFile = open(pFileName, "wb")
        else:
            pFile = open(pFileName, "ab+")

        shift = g_uiBitIncrement
        offset = 1 << (shift - 1) if shift > 0 else 0

        apiY = self.getBufY()
        apiU = self.getBufU()
        apiV = self.getBufV()
        piY = self.getLumaAddr()
        piCb = self.getCbAddr()
        piCr = self.getCrAddr()

        iMax = (1 << g_uiBitDepth) - 1

        Clip3 = lambda min, max, i: min if i < min else max if i > max else i

        for y in range(0, self.m_iPicHeight):
            for x in range(0, self.m_iPicWidth):
                uc = Clip3(0, iMax, (apiY[piY + x] + offset) >> shift)
                pFile.write(uc)
            piY += self.getStride()

        for y in range(0, self.m_iPicHeight >> 1):
            for x in range(0, self.m_iPicWidth >> 1):
                uc = Clip3(0, iMax, (apiU[piCb + x] + offset) >> shift)
                pFile.write(uc)
            piCb += self.getCStride()

        for y in range(0, self.m_iPicHeight >> 1):
            for x in range(0, self.m_iPicWidth >> 1):
                uc = Clip3(0, iMax, (apiV[piCr + x] + offset) >> shift)
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
