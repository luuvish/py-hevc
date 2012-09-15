# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComYuv.py
    HM 8.0 Python Implementation
"""

import sys

from ... import pointer
from ... import cvar

from .CommonDef import Clip
from .TComRom import (g_auiZscanToRaster, g_auiRasterToPelX, g_auiRasterToPelY)

IF_INTERNAL_PREC = 14
IF_INTERNAL_OFFS = 1 << (IF_INTERNAL_PREC-1)


class TComYuv(object):

    def __init__(self):
        self.m_apiBufY = None
        self.m_apiBufU = None
        self.m_apiBufV = None

        self.m_iWidth = 0
        self.m_iHeight = 0
        self.m_iCWidth = 0
        self.m_iCHeight = 0

    def create(self, iWidth, iHeight):
        self.m_apiBufY = pointer((iWidth*iHeight   ) * [0], type='short *')
        self.m_apiBufU = pointer((iWidth*iHeight>>2) * [0], type='short *')
        self.m_apiBufV = pointer((iWidth*iHeight>>2) * [0], type='short *')

        self.m_iWidth = iWidth
        self.m_iHeight = iHeight
        self.m_iCWidth = iWidth >> 1
        self.m_iCHeight = iHeight >> 1

    def destroy(self):
        del self.m_apiBufY
        self.m_apiBufY = None
        del self.m_apiBufU
        self.m_apiBufU = None
        del self.m_apiBufV
        self.m_apiBufV = None

    def clear(self):
        for i in xrange(self.m_iWidth * self.m_iHeight):
            self.m_apiBufY[i] = 0
        for i in xrange(self.m_iCWidth * self.m_iCHeight):
            self.m_apiBufU[i] = 0
            self.m_apiBufV[i] = 0

    def copyToPicYuv(self, pcPicYuvDst, iCuAddr, uiAbsZorderIdx, uiPartDepth=0, uiPartIdx=0):
        self.copyToPicLuma(pcPicYuvDst, iCuAddr, uiAbsZorderIdx, uiPartDepth, uiPartIdx)
        self.copyToPicChroma(pcPicYuvDst, iCuAddr, uiAbsZorderIdx, uiPartDepth, uiPartIdx)

    def copyToPicLuma(self, pcPicYuvDst, iCuAddr, uiAbsZorderIdx, uiPartDepth=0, uiPartIdx=0):
        iWidth = self.m_iWidth >> uiPartDepth
        iHeight = self.m_iHeight >> uiPartDepth

        pSrc = pointer(self.getLumaAddr(uiPartIdx, iWidth), type='short *')
        pDst = pointer(pcPicYuvDst.getLumaAddr(iCuAddr, uiAbsZorderIdx), type='short *')

        iSrcStride = self.getStride()
        iDstStride = pcPicYuvDst.getStride()
        for y in xrange(iHeight):
            for x in xrange(iWidth): pDst[x] = pSrc[x]
            #pDst[0:iWidth] = pSrc[0:iWidth]
            pDst += iDstStride
            pSrc += iSrcStride

    def copyToPicChroma(self, pcPicYuvDst, iCuAddr, uiAbsZorderIdx, uiPartDepth=0, uiPartIdx=0):
        iWidth = self.m_iCWidth >> uiPartDepth
        iHeight = self.m_iCHeight >> uiPartDepth

        pSrcU = pointer(self.getCbAddr(uiPartIdx, iWidth), type='short *')
        pSrcV = pointer(self.getCrAddr(uiPartIdx, iWidth), type='short *')
        pDstU = pointer(pcPicYuvDst.getCbAddr(iCuAddr, uiAbsZorderIdx), type='short *')
        pDstV = pointer(pcPicYuvDst.getCrAddr(iCuAddr, uiAbsZorderIdx), type='short *')

        iSrcStride = self.getCStride()
        iDstStride = pcPicYuvDst.getCStride()
        for y in xrange(iHeight):
            for x in xrange(iWidth): pDstU[x] = pSrcU[x]
            for x in xrange(iWidth): pDstV[x] = pSrcV[x]
            #pDstU[0:iWidth] = pSrcU[0:iWidth]
            #pDstV[0:iWidth] = pSrcV[0:iWidth]
            pSrcU += iSrcStride
            pSrcV += iSrcStride
            pDstU += iDstStride
            pDstV += iDstStride

    def copyFromPicYuv(self, pcPicYuvSrc, iCuAddr, uiAbsZorderIdx):
        self.copyFromPicLuma(pcPicYuvSrc, iCuAddr, uiAbsZorderIdx)
        self.copyFromPicChroma(pcPicYuvSrc, iCuAddr, uiAbsZorderIdx)

    def copyFromPicLuma(self, pcPicYuvSrc, iCuAddr, uiAbsZorderIdx):
        pDst = pointer(self.m_apiBufY, type='short *')
        pSrc = pointer(pcPicYuvSrc.getLumaAddr(iCuAddr, uiAbsZorderIdx), type='short *')

        iDstStride = self.getStride()
        iSrcStride = pcPicYuvSrc.getStride()
        for y in xrange(self.m_iHeight):
            for x in xrange(self.m_iWidth): pDst[x] = pSrc[x]
            #pDst[0:self.m_iWidth] = pSrc[0:self.m_iWidth]
        pDst += iDstStride
        pSrc += iSrcStride

    def copyFromPicChroma(self, pcPicYuvSrc, iCuAddr, uiAbsZorderIdx):
        pDstU = pointer(self.m_apiBufU, type='short *')
        pDstV = pointer(self.m_apiBufV, type='short *')
        pSrcU = pointer(pcPicYuvSrc.getCbAddr(iCuAddr, uiAbsZorderIdx), type='short *')
        pSrcV = pointer(pcPicYuvSrc.getCrAddr(iCuAddr, uiAbsZorderIdx), type='short *')

        iDstStride = self.getCStride()
        iSrcStride = pcPicYuvSrc.getCStride()
        for y in xrange(self.m_iCHeight):
            for x in xrange(self.m_iCWidth): pDstU[x] = pSrcU[x]
            for x in xrange(self.m_iCWidth): pDstV[x] = pSrcV[x]
            #pDstU[0:self.m_iCWidth] = pSrcU[0:self.m_iCWidth]
            #pDstV[0:self.m_iCWidth] = pSrcV[0:self.m_iCWidth]
        pSrcU += iSrcStride
        pSrcV += iSrcStride
        pDstU += iDstStride
        pDstV += iDstStride

    def copyToPartYuv(self, pcYuvDst, uiDstPartIdx):
        self.copyToPartLuma(pcYuvDst, uiDstPartIdx)
        self.copyToPartChroma(pcYuvDst, uiDstPartIdx)

    def copyToPartLuma(self, pcYuvDst, uiDstPartIdx):
        pSrc = pointer(self.m_apiBufY, type='short *')
        pDst = pointer(pcYuvDst.getLumaAddr(uiDstPartIdx), type='short *')

        iSrcStride = self.getStride()
        iDstStride = pcYuvDst.getStride()
        for y in xrange(self.m_iHeight):
            for x in xrange(self.m_iWidth): pDst[x] = pSrc[x]
            #pDst[0:self.m_iWidth] = pSrc[0:self.m_iWidth]
        pDst += iDstStride
        pSrc += iSrcStride

    def copyToPartChroma(self, pcYuvDst, uiDstPartIdx):
        pSrcU = pointer(self.m_apiBufU, type='short *')
        pSrcV = pointer(self.m_apiBufV, type='short *')
        pDstU = pointer(pcYuvDst.getCbAddr(uiDstPartIdx), type='short *')
        pDstV = pointer(pcYuvDst.getCrAddr(uiDstPartIdx), type='short *')

        iSrcStride = self.getCStride()
        iDstStride = pcYuvDst.getCStride()
        for y in xrange(self.m_iCHeight):
            for x in xrange(self.m_iCWidth): pDstU[x] = pSrcU[x]
            for x in xrange(self.m_iCWidth): pDstV[x] = pSrcV[x]
            #pDstU[0:self.m_iCWidth] = pSrcU[0:self.m_iCWidth]
            #pDstV[0:self.m_iCWidth] = pSrcV[0:self.m_iCWidth]
        pSrcU += iSrcStride
        pSrcV += iSrcStride
        pDstU += iDstStride
        pDstV += iDstStride

    def copyPartToYuv(self, pcYuvDst, uiSrcPartIdx):
        self.copyPartToLuma(pcYuvDst, uiSrcPartIdx)
        self.copyPartToChroma(pcYuvDst, uiSrcPartIdx)

    def copyPartToLuma(self, pcYuvDst, uiSrcPartIdx):
        pSrc = pointer(self.getLumaAddr(uiSrcPartIdx), type='short *')
        pDst = pointer(pcYuvDst.getLumaAddr(0), type='short *')

        iSrcStride = self.getStride()
        iDstStride = pcYuvDst.getStride()

        uiHeight = pcYuvDst.getHeight()
        uiWidth = pcYuvDst.getWidth()

        for y in xrange(uiHeight):
            for x in xrange(uiWidth): pDst[x] = pSrc[x]
            #pDst[0:uiWidth] = pSrc[0:uiWidth]
            pDst += iDstStride
            pSrc += iSrcStride

    def copyPartToChroma(self, pcYuvDst, uiSrcPartIdx):
        pSrcU = pointer(self.getCbAddr(uiSrcPartIdx), type='short *')
        pSrcV = pointer(self.getCrAddr(uiSrcPartIdx), type='short *')
        pDstU = pointer(pcYuvDst.getCbAddr(0), type='short *')
        pDstV = pointer(pcYuvDst.getCrAddr(0), type='short *')

        iSrcStride = self.getCStride()
        iDstStride = pcYuvDst.getCStride()

        uiCHeight = pcYuvDst.getCHeight()
        uiCWidth = pcYuvDst.getCWidth()

        for y in xrange(uiCHeight):
            for x in xrange(uiCWidth): pDstU[x] = pSrcU[x]
            for x in xrange(uiCWidth): pDstV[x] = pSrcV[x]
            #pDstU[0:uiCWidth] = pSrcU[0:uiCWidth]
            #pDstV[0:uiCWidth] = pSrcV[0:uiCWidth]
            pSrcU += iSrcStride
            pSrcV += iSrcStride
            pDstU += iDstStride
            pDstV += iDstStride

    def copyPartToPartYuv(self, pcYuvDst, uiPartIdx, iWidth, iHeight):
        self.copyPartToPartLuma(pcYuvDst, uiPartIdx, iWidth, iHeight)
        self.copyPartToPartChroma(pcYuvDst, uiPartIdx, iWidth>>1, iHeight>>1)

    def copyPartToPartLuma(self, pcYuvDst, uiPartIdx, iWidth, iHeight):
        pSrc = pointer(self.getLumaAddr(uiPartIdx), type='short *')
        pDst = pointer(pcYuvDst.getLumaAddr(uiPartIdx), type='short *')
        if pSrc == pDst:
            #th not a good idea
            #th best would be to fix the caller 
            return

        iSrcStride = self.getStride()
        iDstStride = pcYuvDst.getStride()
        for y in xrange(iHeight):
            for x in xrange(iWidth): pDst[x] = pSrc[x]
            #pDst[0:iWidth] = pSrc[0:iWidth]
            pSrc += iSrcStride
            pDst += iDstStride

    def copyPartToPartChroma(self, pcYuvDst, uiPartIdx, iWidth, iHeight, chromaId=None):
        if chromaId == 0:
            pSrcU = pointer(self.getCbAddr(uiPartIdx), type='short *')
            pDstU = pointer(pcYuvDst.getCbAddr(uiPartIdx), type='short *')
            if pSrcU == pDstU:
                return
            iSrcStride = self.getCStride()
            iDstStride = pcYuvDst.getCStride()
            for y in xrange(iHeight):
                for x in xrange(iWidth): pDstU[x] = pSrcU[x]
                #pDstU[0:iWidth] = pSrcU[0:iWidth]
            pSrcU += iSrcStride
            pDstU += iDstStride
            return
        elif chromaId == 1:
            pSrcV = pointer(self.getCrAddr(uiPartIdx), type='short *')
            pDstV = pointer(pcYuvDst.getCrAddr(uiPartIdx), type='short *')
            if pSrcU == pDstU:
                return
            iSrcStride = self.getCStride()
            iDstStride = pcYuvDst.getCStride()
            for y in xrange(iHeight):
                for x in xrange(iWidth): pDstV[x] = pSrcV[x]
                #pDstV[0:iWidth] = pSrcV[0:iWidth]
            pSrcV += iSrcStride
            pDstV += iDstStride
            return

        pSrcU = pointer(self.getCbAddr(uiPartIdx), type='short *')
        pSrcV = pointer(self.getCrAddr(uiPartIdx), type='short *')
        pDstU = pointer(pcYuvDst.getCbAddr(uiPartIdx), type='short *')
        pDstV = pointer(pcYuvDst.getCrAddr(uiPartIdx), type='short *')
        if pSrcU == pDstU and pSrcV == pDstV:
            #th not a good idea
            #th best would be to fix the caller 
            return

        iSrcStride = self.getCStride()
        iDstStride = pcYuvDst.getCStride()
        for y in xrange(iHeight):
            for x in xrange(iWidth): pDstU[x] = pSrcU[x]
            for x in xrange(iWidth): pDstV[x] = pSrcV[x]
            #pDstU[0:iWidth] = pSrcU[0:iWidth]
            #pDstV[0:iWidth] = pSrcV[0:iWidth]
            pSrcU += iSrcStride
            pSrcV += iSrcStride
            pDstU += iDstStride
            pDstV += iDstStride

    def addClip(self, pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize):
        self.addClipLuma(pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize)
        self.addClipChroma(pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize>>1)

    def addClipLuma(self, pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize):
        pSrc0 = pointer(pcYuvSrc0.getLumaAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrc1 = pointer(pcYuvSrc1.getLumaAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pDst = pointer(self.getLumaAddr(uiTrUnitIdx, uiPartSize), type='short *')

        iSrc0Stride = pcYuvSrc0.getStride()
        iSrc1Stride = pcYuvSrc1.getStride()
        iDstStride = self.getStride()
        for y in xrange(uiPartSize):
            for x in xrange(uiPartSize):
                pDst[x] = Clip(pSrc0[x] + pSrc1[x])
            pSrc0 += iSrc0Stride
            pSrc1 += iSrc1Stride
            pDst += iDstStride

    def addClipChroma(self, pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize):
        pSrcU0 = pointer(pcYuvSrc0.getCbAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrcU1 = pointer(pcYuvSrc1.getCbAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrcV0 = pointer(pcYuvSrc0.getCrAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrcV1 = pointer(pcYuvSrc1.getCrAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pDstU = pointer(self.getCbAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pDstV = pointer(self.getCrAddr(uiTrUnitIdx, uiPartSize), type='short *')

        iSrc0Stride = pcYuvSrc0.getCStride()
        iSrc1Stride = pcYuvSrc1.getCStride()
        iDstStride = self.getCStride()
        for y in xrange(uiPartSize):
            for x in xrange(uiPartSize):
                pDstU[x] = Clip(pSrcU0[x] + pSrcU1[x])
                pDstV[x] = Clip(pSrcV0[x] + pSrcV1[x])
            pSrcU0 += iSrc0Stride
            pSrcU1 += iSrc1Stride
            pSrcV0 += iSrc0Stride
            pSrcV1 += iSrc1Stride
            pDstU += iDstStride
            pDstV += iDstStride

    def subtract(self, pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize):
        self.subtractLuma(pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize)
        self.subtractChroma(pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize>>1)

    def subtractLuma(self, pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize):
        pSrc0 = pointer(pcYuvSrc0.getLumaAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrc1 = pointer(pcYuvSrc1.getLumaAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pDst = pointer(self.getLumaAddr(uiTrUnitIdx, uiPartSize), type='short *')

        iSrc0Stride = pcYuvSrc0.getStride()
        iSrc1Stride = pcYuvSrc1.getStride()
        iDstStride = self.getStride()
        for y in xrange(uiPartSize):
            for x in xrange(uiPartSize):
                pDst[x] = pSrc0[x] - pSrc1[x]
            pSrc0 += iSrc0Stride
            pSrc1 += iSrc1Stride
            pDst += iDstStride

    def subtractChroma(self, pcYuvSrc0, pcYuvSrc1, uiTrUnitIdx, uiPartSize):
        pSrcU0 = pointer(pcYuvSrc0.getCbAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrcU1 = pointer(pcYuvSrc1.getCbAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrcV0 = pointer(pcYuvSrc0.getCrAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pSrcV1 = pointer(pcYuvSrc1.getCrAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pDstU = pointer(self.getCbAddr(uiTrUnitIdx, uiPartSize), type='short *')
        pDstV = pointer(self.getCrAddr(uiTrUnitIdx, uiPartSize), type='short *')

        iSrc0Stride = pcYuvSrc0.getCStride()
        iSrc1Stride = pcYuvSrc1.getCStride()
        iDstStride = self.getCStride()
        for y in xrange(uiPartSize):
            for x in xrange(uiPartSize):
                pDstU[x] = pSrcU0[x] - pSrcU1[x]
                pDstV[x] = pSrcV0[x] - pSrcV1[x]
            pSrcU0 += iSrc0Stride
            pSrcU1 += iSrc1Stride
            pSrcV0 += iSrc0Stride
            pSrcV1 += iSrc1Stride
            pDstU += iDstStride
            pDstV += iDstStride

    def addAvg(self, pcYuvSrc0, pcYuvSrc1, iPartUnitIdx, iWidth, iHeight):
        pSrcY0 = pointer(pcYuvSrc0.getLumaAddr(iPartUnitIdx), type='short *')
        pSrcU0 = pointer(pcYuvSrc0.getCbAddr(iPartUnitIdx), type='short *')
        pSrcV0 = pointer(pcYuvSrc0.getCrAddr(iPartUnitIdx), type='short *')

        pSrcY1 = pointer(pcYuvSrc1.getLumaAddr(iPartUnitIdx), type='short *')
        pSrcU1 = pointer(pcYuvSrc1.getCbAddr(iPartUnitIdx), type='short *')
        pSrcV1 = pointer(pcYuvSrc1.getCrAddr(iPartUnitIdx), type='short *')

        pDstY = pointer(self.getLumaAddr(iPartUnitIdx), type='short *')
        pDstU = pointer(self.getCbAddr(iPartUnitIdx), type='short *')
        pDstV = pointer(self.getCrAddr(iPartUnitIdx), type='short *')

        iSrc0Stride = pcYuvSrc0.getStride()
        iSrc1Stride = pcYuvSrc1.getStride()
        iDstStride = self.getStride()
        shiftNum = IF_INTERNAL_PREC + 1 - (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)
        offset = (1 << (shiftNum-1)) + 2 * IF_INTERNAL_OFFS

        for y in xrange(iHeight):
            for x in xrange(0, iWidth, 4):
                pDstY[x+0] = Clip((pSrcY0[x+0] + pSrcY1[x+0] + offset) >> shiftNum)
                pDstY[x+1] = Clip((pSrcY0[x+1] + pSrcY1[x+1] + offset) >> shiftNum)
                pDstY[x+2] = Clip((pSrcY0[x+2] + pSrcY1[x+2] + offset) >> shiftNum)
                pDstY[x+3] = Clip((pSrcY0[x+3] + pSrcY1[x+3] + offset) >> shiftNum)
            pSrcY0 += iSrc0Stride
            pSrcY1 += iSrc1Stride
            pDstY += iDstStride

        iSrc0Stride = pcYuvSrc0.getCStride()
        iSrc1Stride = pcYuvSrc1.getCStride()
        iDstStride = self.getCStride()

        iWidth >>= 1
        iHeight >>= 1

        for y in xrange(iHeight):
            for x in xrange(iWidth-1, -1, -2):
                # note: chroma min width is 2
                pDstU[x-0] = Clip((pSrcU0[x-0] + pSrcU1[x-0] + offset) >> shiftNum)
                pDstV[x-0] = Clip((pSrcV0[x-0] + pSrcV1[x-0] + offset) >> shiftNum)
                pDstU[x-1] = Clip((pSrcU0[x-1] + pSrcU1[x-1] + offset) >> shiftNum)
                pDstV[x-1] = Clip((pSrcV0[x-1] + pSrcV1[x-1] + offset) >> shiftNum)
            pSrcU0 += iSrc0Stride
            pSrcU1 += iSrc1Stride
            pSrcV0 += iSrc0Stride
            pSrcV1 += iSrc1Stride
            pDstU += iDstStride
            pDstV += iDstStride

    def removeHighFreq(self, pcYuvSrc, uiPartIdx, iWidth, iHeight):
        pSrc = pointer(pcYuvSrc.getLumaAddr(uiPartIdx), type='short *')
        pSrcU = pointer(pcYuvSrc.getCbAddr(uiPartIdx), type='short *')
        pSrcV = pointer(pcYuvSrc.getCrAddr(uiPartIdx), type='short *')

        pDst = pointer(self.getLumaAddr(uiPartIdx), type='short *')
        pDstU = pointer(self.getCbAddr(uiPartIdx), type='short *')
        pDstV = pointer(self.getCrAddr(uiPartIdx), type='short *')

        iSrcStride = pcYuvSrc.getStride()
        iDstStride = self.getStride()

        for y in xrange(iHeight):
            for x in xrange(iWidth):
                pDst[x] = (pDst[x]<<1) - pSrc[x]
            pSrc += iSrcStride
            pDst += iDstStride

        iSrcStride = pcYuvSrc.getCStride()
        iDstStride = self.getCStride()

        uiHeight >>= 1
        uiWidth >>= 1

        for y in xrange(iHeight):
            for x in xrange(iWidth):
                pDstU[x] = (pDstU[x]<<1) - pSrcU[x]
                pDstV[x] = (pDstV[x]<<1) - pSrcV[x]
            pSrcU += iSrcStride
            pSrcV += iSrcStride
            pDstU += iDstStride
            pDstV += iDstStride

    def getLumaAddr(self, iPartUnitIdx=None, iBlkSize=None):
        if iPartUnitIdx is None and iBlkSize is None:
            return pointer(self.m_apiBufY, type='short *')
        elif iBlkSize is None:
            return pointer(self.m_apiBufY, type='short *') + self.getAddrOffset(iPartUnitIdx, self.m_iWidth)
        else:
            return pointer(self.m_apiBufY, type='short *') + self.getAddrOffset(iPartUnitIdx, iBlkSize, self.m_iWidth)

    def getCbAddr(self, iPartUnitIdx=None, iBlkSize=None):
        if iPartUnitIdx is None and iBlkSize is None:
            return pointer(self.m_apiBufU, type='short *')
        elif iBlkSize is None:
            return pointer(self.m_apiBufU, type='short *') + (self.getAddrOffset(iPartUnitIdx, self.m_iCWidth) >> 1)
        else:
            return pointer(self.m_apiBufU, type='short *') + self.getAddrOffset(iPartUnitIdx, iBlkSize, self.m_iCWidth)

    def getCrAddr(self, iPartUnitIdx=None, iBlkSize=None):
        if iPartUnitIdx is None and iBlkSize is None:
            return pointer(self.m_apiBufV, type='short *')
        elif iBlkSize is None:
            return pointer(self.m_apiBufV, type='short *') + (self.getAddrOffset(iPartUnitIdx, self.m_iCWidth) >> 1)
        else:
            return pointer(self.m_apiBufV, type='short *') + self.getAddrOffset(iPartUnitIdx, iBlkSize, self.m_iCWidth)

    def getStride(self):
        return self.m_iWidth
    def getCStride(self):
        return self.m_iCWidth
    def getHeight(self):
        return self.m_iHeight
    def getWidth(self):
        return self.m_iWidth
    def getCHeight(self):
        return self.m_iCHeight
    def getCWidth(self):
        return self.m_iCWidth

    @staticmethod
    def getAddrOffset(*args):
        if len(args) == 2:
            uiPartUnitIdx, width = args

            blkX = g_auiRasterToPelX[g_auiZscanToRaster[uiPartUnitIdx]]
            blkY = g_auiRasterToPelY[g_auiZscanToRaster[uiPartUnitIdx]]

            return blkX + blkY * width
        elif len(args) == 3:
            iTransUnitIdx, iBlkSize, width = args

            blkX = (iTransUnitIdx * iBlkSize) &  (width - 1)
            blkY = (iTransUnitIdx * iBlkSize) & ~(width - 1)

            return blkX + blkY * iBlkSize
        else:
            return 0
