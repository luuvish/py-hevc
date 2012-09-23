# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComPattern.py
    HM 8.0 Python Implementation
"""

from ... import pointer

from ... import cvar

from .TypeDef import (VER_IDX, HOR_IDX, DC_IDX, MODE_INTRA)

from .TComRom import (
    MAX_CU_SIZE, MAX_NUM_SPU_W,
    g_auiZscanToRaster, g_auiRasterToZscan,
    g_auiRasterToPelX, g_auiRasterToPelY
)


# neighbouring pixel access class for one component
class TComPatternParam(object):

    def __init__(self):
        self.m_iOffsetLeft     = 0
        self.m_iOffsetRight    = 0
        self.m_iOffsetAbove    = 0
        self.m_iOffsetBottom   = 0
        self.m_piPatternOrigin = None

        self.m_iROIWidth      = 0
        self.m_iROIHeight     = 0
        self.m_iPatternStride = 0

    def getPatternOrigin(self):
        return pointer(self.m_piPatternOrigin)

    def getROIOrigin(self):
        return pointer(self.m_piPatternOrigin) + \
            self.m_iPatternStride * self.m_iOffsetAbove + self.m_iOffsetLeft

    def setPatternParamPel(self, piTexture, iRoiWidth, iRoiHeight, iStride,
                           iOffsetLeft, iOffsetRight, iOffsetAbove, iOffsetBottom):
        self.m_piPatternOrigin = pointer(piTexture, type='short *')
        self.m_iROIWidth       = iRoiWidth
        self.m_iROIHeight      = iRoiHeight
        self.m_iPatternStride  = iStride
        self.m_iOffsetLeft     = iOffsetLeft
        self.m_iOffsetAbove    = iOffsetAbove
        self.m_iOffsetRight    = iOffsetRight
        self.m_iOffsetBottom   = iOffsetBottom

    def setPatternParamCU(self, pcCU, iComp, iRoiWidth, iRoiHeight,
                          iOffsetLeft, iOffsetRight, iOffsetAbove, iOffsetBottom,
                          uiPartDepth, uiAbsPartIdx):
        self.m_iOffsetLeft   = iOffsetLeft
        self.m_iOffsetRight  = iOffsetRight
        self.m_iOffsetAbove  = iOffsetAbove
        self.m_iOffsetBottom = iOffsetBottom

        self.m_iROIWidth  = iRoiWidth
        self.m_iROIHeight = iRoiHeight

        uiAbsZorderIdx = pcCU.getZorderIdxInCU() + uiAbsPartIdx

        if iComp == 0:
            self.m_iPatternStride = pcCU.getPic().getStride()
            self.m_piPatternOrigin = pointer(pcCU.getPic().getPicYuvRec().getLumaAddr(pcCU.getAddr(), uiAbsZorderIdx), type='short *') - \
                self.m_iOffsetAbove * self.m_iPatternStride - self.m_iOffsetLeft
        else:
            self.m_iPatternStride = pcCU.getPic().getCStride()
            if iComp == 1:
                self.m_piPatternOrigin = pointer(pcCU.getPic().getPicYuvRec().getCbAddr(pcCU.getAddr(), uiAbsZorderIdx), type='short *') - \
                    self.m_iOffsetAbove * self.m_iPatternStride - self.m_iOffsetLeft
            else:
                self.m_piPatternOrigin = pointer(pcCU.getPic().getPicYuvRec().getCrAddr(pcCU.getAddr(), uiAbsZorderIdx), type='short *') - \
                    self.m_iOffsetAbove * self.m_iPatternStride - self.m_iOffsetLeft


# neighbouring pixel access class for all components
class TComPattern(object):

    m_aucIntraFilter = (
        10, #  4x4
         7, #  8x8
         1, # 16x16
         0, # 32x32
        10, # 64x64
    )

    def __init__(self):
        self.m_cPatternY  = TComPatternParam()
        self.m_cPatternCb = TComPatternParam()
        self.m_cPatternCr = TComPatternParam()

    def getROIY(self):
        return self.m_cPatternY.getROIOrigin()
    def getROIYWidth(self):
        return self.m_cPatternY.m_iROIWidth
    def getROIYHeight(self):
        return self.m_cPatternY.m_iROIHeight
    def getPatternLStride(self):
        return self.m_cPatternY.m_iPatternStride

    def getAdiOrgBuf(self, iCuWidth, iCuHeight, piAdiBuf):
        return pointer(piAdiBuf, type='int *')
    def getAdiCbBuf(self, iCuWidth, iCuHeight, piAdiBuf):
        return pointer(piAdiBuf, type='int *')
    def getAdiCrBuf(self, iCuWidth, iCuHeight, piAdiBuf):
        return pointer(piAdiBuf, type='int *') + (iCuWidth*2+1) * (iCuHeight*2+1)

    def getPredictorPtr(self, uiDirMode, log2BlkSize, piAdiBuf):
        assert(log2BlkSize >= 2 and log2BlkSize < 7)

        diff = min(abs(uiDirMode - HOR_IDX), abs(uiDirMode - VER_IDX))
        ucFiltIdx = 1 if diff > TComPattern.m_aucIntraFilter[log2BlkSize-2] else 0
        if uiDirMode == DC_IDX:
            ucFiltIdx = 0 # no smoothing for DC or LM chroma

        assert(ucFiltIdx <= 1)

        width = 1 << log2BlkSize
        height = 1 << log2BlkSize

        piSrc = self.getAdiOrgBuf(width, height, piAdiBuf)

        if ucFiltIdx:
            piSrc += (2*width+1) * (2*height+1)

        return pointer(piSrc, type='int *')

    def initPattern(self, *args):
        if len(args) == 10:
            (piY, piCb, piCr, iRoiWidth, iRoiHeight, iStride,
             iOffsetLeft, iOffsetRight, iOffsetAbove, iOffsetBottom) = args

            self.m_cPatternY.setPatternParamPel(piY, iRoiWidth, iRoiHeight, iStride,
                iOffsetLeft, iOffsetRight, iOffsetAbove, iOffsetBottom)
            self.m_cPatternCb.setPatternParamPel(piCb, iRoiWidth>>1, iRoiHeight>>1, iStride>>1,
                iOffsetLeft>>1, iOffsetRight>>1, iOffsetAbove>>1, iOffsetBottom>>1)
            self.m_cPatternCr.setPatternParamPel(piCr, iRoiWidth>>1, iRoiHeight>>1, iStride>>1,
                iOffsetLeft>>1, iOffsetRight>>1, iOffsetAbove>>1, iOffsetBottom>>1)

        elif len(args) == 3:
            pcCU, uiPartDepth, uiAbsPartIdx = args

            uiOffsetLeft  = 0
            uiOffsetRight = 0
            uiOffsetAbove = 0

            pcPic = pcCU.getPic()
            uiWidth = pcCU.getWidth(0) >> uiPartDepth
            uiHeight = pcCU.getHeight(0) >> uiPartDepth

            uiAbsZorderIdx = pcCU.getZorderIdxInCU() + uiAbsPartIdx
            uiCurrPicPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsZorderIdx]]
            uiCurrPicPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsZorderIdx]]

            if uiCurrPicPelX != 0:
                uiOffsetLeft = 1

            if uiCurrPicPelY != 0:
                uiNumPartInWidth = uiWidth / pcPic.getMinCUWidth()
                uiOffsetAbove = 1

                if uiCurrPicPelX + uiWidth < pcCU.getSlice().getSPS().getPicWidthInLumaSamples():
                    if (g_auiZscanToRaster[uiAbsZorderIdx] + uiNumPartInWidth) % pcPic.getNumPartInWidth(): # Not CU boundary
                        if g_auiRasterToZscan[g_auiZscanToRaster[uiAbsZorderIdx] - pcPic.getNumPartInWidth() + uiNumPartInWidth] < uiAbsZorderIdx:
                            uiOffsetRight = 1
                    else: # if it is CU boundary
                        if g_auiZscanToRaster[uiAbsZorderIdx] < pcPic.getNumPartInWidth() and uiCurrPicPelX+uiWidth < pcPic.getPicYuvRec().getWidth(): # first line
                            uiOffsetRight = 1

            self.m_cPatternY.setPatternParamCU(pcCU, 0, uiWidth, uiHeight,
                uiOffsetLeft, uiOffsetRight, uiOffsetAbove, 0, uiPartDepth, uiAbsPartIdx)
            self.m_cPatternCb.setPatternParamCU(pcCU, 1, uiWidth>>1, uiHeight>>1,
                uiOffsetLeft, uiOffsetRight, uiOffsetAbove, 0, uiPartDepth, uiAbsPartIdx)
            self.m_cPatternCr.setPatternParamCU(pcCU, 2, uiWidth>>1, uiHeight>>1,
                uiOffsetLeft, uiOffsetRight, uiOffsetAbove, 0, uiPartDepth, uiAbsPartIdx)

    def initAdiPattern(self, pcCU, uiZorderIdxInPart, uiPartDepth, piAdiBuf,
                       iOrgBufStride, iOrgBufHeight, bAbove, bLeft, bLMmode=False):
        uiCuWidth = pcCU.getWidth(0) >> uiPartDepth
        uiCuHeight = pcCU.getHeight(0) >> uiPartDepth
        uiCuWidth2 = uiCuWidth << 1
        uiCuHeight2 = uiCuHeight << 1
        iPicStride = pcCU.getPic().getStride()
        iTotalUnits = 0
        bNeighborFlags = pointer((4 * MAX_NUM_SPU_W + 1) * [False])
        iNumIntraNeighbor = 0

        uiPartIdxLT = uiPartIdxRT = uiPartIdxLB = 0
        uiPartIdxLT, uiPartIdxRT = pcCU.deriveLeftRightTopIdxAdi(uiPartIdxLT, uiPartIdxRT, uiZorderIdxInPart, uiPartDepth)
        uiPartIdxLB = pcCU.deriveLeftBottomIdxAdi(uiPartIdxLB, uiZorderIdxInPart, uiPartDepth)

        iUnitSize = cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth
        iNumUnitsInCu = uiCuWidth / iUnitSize
        iTotalUnits = (iNumUnitsInCu << 2) + 1

        bNeighborFlags[iNumUnitsInCu*2] = self.isAboveLeftAvailable(pcCU, uiPartIdxLT)
        iNumIntraNeighbor += bNeighborFlags[iNumUnitsInCu*2]
        iNumIntraNeighbor += self.isAboveAvailable     (pcCU, uiPartIdxLT, uiPartIdxRT, bNeighborFlags + (iNumUnitsInCu*2+1))
        iNumIntraNeighbor += self.isAboveRightAvailable(pcCU, uiPartIdxLT, uiPartIdxRT, bNeighborFlags + (iNumUnitsInCu*3+1))
        iNumIntraNeighbor += self.isLeftAvailable      (pcCU, uiPartIdxLT, uiPartIdxLB, bNeighborFlags + (iNumUnitsInCu*2-1))
        iNumIntraNeighbor += self.isBelowLeftAvailable (pcCU, uiPartIdxLT, uiPartIdxLB, bNeighborFlags + (iNumUnitsInCu  -1))

        bAbove = True
        bLeft = True

        uiWidth = uiCuWidth2 + 1
        uiHeight = uiCuHeight2 + 1

        if (uiWidth<<2) > iOrgBufStride or (uiHeight<<2) > iOrgBufHeight:
            return bAbove, bLeft

        piRoiOrigin = pointer(pcCU.getPic().getPicYuvRec().getLumaAddr(
            pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiZorderIdxInPart), type='short *')
        piAdiTemp = pointer(piAdiBuf, type='int *')

        self.fillReferenceSamples(pcCU, piRoiOrigin, piAdiTemp,
            bNeighborFlags, iNumIntraNeighbor, iUnitSize, iNumUnitsInCu, iTotalUnits,
            uiCuWidth, uiCuHeight, uiWidth, uiHeight, iPicStride, bLMmode)

        # generate filtered intra prediction samples
        iBufSize = uiCuHeight2 + uiCuWidth2 + 1 # left and left above border + above and above right border + top left corner = length of 3. filter buffer

        uiWH = uiWidth * uiHeight               # number of elements in one buffer

        piFilteredBuf1 = pointer(piAdiBuf, type='int *') + uiWH  # 1. filter buffer
        piFilteredBuf2 = pointer(piFilteredBuf1)         + uiWH  # 2. filter buffer
        piFilterBuf    = pointer(piFilteredBuf2)         + uiWH  # buffer for 2. filtering (sequential)
        piFilteredBufN = pointer(piFilterBuf)         + iBufSize # buffer for 1. filtering (sequential)

        l = 0
        # left border from bottom to top
        for i in xrange(uiCuHeight2):
            piFilterBuf[l] = piAdiTemp[uiWidth * (uiCuHeight2 - i)]
            l += 1
        # top left corner
        piFilterBuf[l] = piAdiTemp[0]
        l += 1
        # above border from left to right
        for i in xrange(uiCuWidth2):
            piFilterBuf[l] = piAdiTemp[1 + i]
            l += 1

        # 1. filtering with [1 2 1]
        piFilteredBufN[0] = piFilterBuf[0]
        piFilteredBufN[iBufSize-1] = piFilterBuf[iBufSize-1]
        for i in xrange(1, iBufSize-1):
            piFilteredBufN[i] = (piFilterBuf[i-1] + 2*piFilterBuf[i] + piFilterBuf[i+1] + 2) >> 2

        # fill 1. filter buffer with filtered values
        l = 0
        for i in xrange(uiCuHeight2):
            piFilteredBuf1[uiWidth * (uiCuHeight2-i)] = piFilteredBufN[l]
            l += 1
        piFilteredBuf1[0] = piFilteredBufN[l]
        l += 1
        for i in xrange(uiCuWidth2):
            piFilteredBuf1[1+i] = piFilteredBufN[l]
            l += 1

        return bAbove, bLeft

    def initAdiPatternChroma(self, pcCU, uiZorderIdxInPart, uiPartDepth, piAdiBuf,
                             iOrgBufStride, iOrgBufHeight, bAbove, bLeft):
        uiCuWidth = pcCU.getWidth(0) >> uiPartDepth
        uiCuHeight = pcCU.getHeight(0) >> uiPartDepth
        iPicStride = pcCU.getPic().getCStride()

        iTotalUnits = 0
        bNeighborFlags = pointer((4 * MAX_NUM_SPU_W + 1) * [False])
        iNumIntraNeighbor = 0

        uiPartIdxLT = uiPartIdxRT = uiPartIdxLB = 0
        uiPartIdxLT, uiPartIdxRT = pcCU.deriveLeftRightTopIdxAdi(uiPartIdxLT, uiPartIdxRT, uiZorderIdxInPart, uiPartDepth)
        uiPartIdxLB = pcCU.deriveLeftBottomIdxAdi(uiPartIdxLB, uiZorderIdxInPart, uiPartDepth)

        iUnitSize = (cvar.g_uiMaxCUWidth >> cvar.g_uiMaxCUDepth) >> 1 # for chroma
        iNumUnitsInCu = (uiCuWidth / iUnitSize) >> 1 # for chroma
        iTotalUnits = (iNumUnitsInCu << 2) + 1

        bNeighborFlags[iNumUnitsInCu*2] = self.isAboveLeftAvailable(pcCU, uiPartIdxLT)
        iNumIntraNeighbor += bNeighborFlags[iNumUnitsInCu*2]
        iNumIntraNeighbor += self.isAboveAvailable     (pcCU, uiPartIdxLT, uiPartIdxRT, bNeighborFlags+(iNumUnitsInCu*2+1))
        iNumIntraNeighbor += self.isAboveRightAvailable(pcCU, uiPartIdxLT, uiPartIdxRT, bNeighborFlags+(iNumUnitsInCu*3+1))
        iNumIntraNeighbor += self.isLeftAvailable      (pcCU, uiPartIdxLT, uiPartIdxLB, bNeighborFlags+(iNumUnitsInCu*2-1))
        iNumIntraNeighbor += self.isBelowLeftAvailable (pcCU, uiPartIdxLT, uiPartIdxLB, bNeighborFlags+(iNumUnitsInCu  -1))

        bAbove = True
        bLeft = True

        uiCuWidth = uiCuWidth >> 1 # for chroma
        uiCuHeight = uiCuHeight >> 1 # for chroma

        uiWidth = uiCuWidth * 2 + 1
        uiHeight = uiCuHeight * 2 + 1

        if 4*uiWidth > iOrgBufStride or 4*uiHeight > iOrgBufHeight:
            return bAbove, bLeft

        # get Cb pattern
        piRoiOrigin = pointer(pcCU.getPic().getPicYuvRec().getCbAddr(
            pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiZorderIdxInPart), type='short *')
        piAdiTemp = pointer(piAdiBuf, type='int *')

        self.fillReferenceSamples(pcCU, piRoiOrigin, piAdiTemp,
            bNeighborFlags, iNumIntraNeighbor, iUnitSize, iNumUnitsInCu, iTotalUnits,
            uiCuWidth, uiCuHeight, uiWidth, uiHeight, iPicStride)

        # get Cr pattern
        piRoiOrigin = pointer(pcCU.getPic().getPicYuvRec().getCrAddr(
            pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiZorderIdxInPart), type='short *')
        piAdiTemp = pointer(piAdiBuf, type='int *') + uiWidth * uiHeight

        self.fillReferenceSamples(pcCU, piRoiOrigin, piAdiTemp,
            bNeighborFlags, iNumIntraNeighbor, iUnitSize, iNumUnitsInCu, iTotalUnits,
            uiCuWidth, uiCuHeight, uiWidth, uiHeight, iPicStride)

        return bAbove, bLeft

    def fillReferenceSamples(self, pcCU, piRoiOrigin, piAdiTemp,
                             bNeighborFlags, iNumIntraNeighbor,
                             iUnitSize, iNumUnitsInCu, iTotalUnits,
                             uiCuWidth, uiCuHeight, uiWidth, uiHeight, iPicStride,
                             bLMmode=False):
        piRoiOrigin    = pointer(piRoiOrigin,    type='short *')
        piAdiTemp      = pointer(piAdiTemp,      type='int *'  )
        bNeighborFlags = pointer(bNeighborFlags, type='bool *' )

        iDCValue = 1 << (cvar.g_uiBitDepth + cvar.g_uiBitIncrement - 1)

        if iNumIntraNeighbor == 0:
            # Fill border with DC value
            for i in xrange(uiWidth):
                piAdiTemp[i] = iDCValue
            for i in xrange(uiHeight):
                piAdiTemp[i*uiWidth] = iDCValue
        elif iNumIntraNeighbor == iTotalUnits:
            # Fill top-left border with rec. samples
            piRoiTemp = piRoiOrigin - iPicStride - 1
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')
            piAdiTemp[0] = piRoiTemp[0]

            # Fill left border with rec. samples
            piRoiTemp = piRoiOrigin - 1

            if bLMmode:
                piRoiTemp -= 1 # move to the second left column
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')

            for i in xrange(uiCuHeight):
                piAdiTemp[(1+i)*uiWidth] = piRoiTemp[0]
                piRoiTemp += iPicStride

            # Fill below left border with rec. samples
            for i in xrange(uiCuHeight):
                piAdiTemp[(1+uiCuHeight+i)*uiWidth] = piRoiTemp[0]
                piRoiTemp += iPicStride

            # Fill top border with rec. samples
            piRoiTemp = piRoiOrigin - iPicStride
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')
            for i in xrange(uiCuWidth):
                piAdiTemp[1+i] = piRoiTemp[i]

            # Fill top right border with rec. samples
            piRoiTemp = piRoiOrigin - iPicStride + uiCuWidth
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')
            for i in xrange(uiCuWidth):
                piAdiTemp[1+uiCuWidth+i] = piRoiTemp[i]
        else: # reference samples are partially available
            iNumUnits2 = iNumUnitsInCu << 1
            iTotalSamples = iTotalUnits * iUnitSize
            piAdiLine = pointer((5 * MAX_CU_SIZE) * [0])
            piAdiLineTemp = None
            pbNeighborFlags = None

            # Initialize
            for i in xrange(iTotalSamples):
                piAdiLine[i] = iDCValue

            # Fill top-left sample
            piRoiTemp = piRoiOrigin - iPicStride - 1
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')
            piAdiLineTemp = piAdiLine + iNumUnits2 * iUnitSize
            pbNeighborFlags = bNeighborFlags + iNumUnits2
            if pbNeighborFlags[0]:
                piAdiLineTemp[0] = piRoiTemp[0]
                for i in xrange(1, iUnitSize):
                    piAdiLineTemp[i] = piAdiLineTemp[0]

            # Fill left & below-left samples
            piRoiTemp += iPicStride
            if bLMmode:
                piRoiTemp -= 1 # move the second left column
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')
            piAdiLineTemp -= 1
            pbNeighborFlags -= 1
            for j in xrange(iNumUnits2):
                if pbNeighborFlags[0]:
                    for i in xrange(iUnitSize):
                        piAdiLineTemp[-i] = piRoiTemp[i * iPicStride]
                piRoiTemp += iUnitSize * iPicStride
                piAdiLineTemp -= iUnitSize
                pbNeighborFlags -= 1

            # Fill above & above-right samples
            piRoiTemp = piRoiOrigin - iPicStride
            piRoiTemp = pointer(piRoiTemp.cast(), type='short *')
            piAdiLineTemp = piAdiLine + (iNumUnits2+1) * iUnitSize
            pbNeighborFlags = bNeighborFlags + iNumUnits2 + 1
            for j in xrange(iNumUnits2):
                if pbNeighborFlags[0]:
                    for i in xrange(iUnitSize):
                        piAdiLineTemp[i] = piRoiTemp[i]
                piRoiTemp += iUnitSize
                piAdiLineTemp += iUnitSize
                pbNeighborFlags += 1

            # Pad reference samples when necessary
            iCurr = 0
            iNext = 1
            piRef = 0
            piAdiLineTemp = pointer(piAdiLine)
            while iCurr < iTotalUnits:
                if not bNeighborFlags[iCurr]:
                    if iCurr == 0:
                        while iNext < iTotalUnits and not bNeighborFlags[iNext]:
                            iNext += 1
                        piRef = piAdiLine[iNext * iUnitSize]
                        # Pad unavailable samples with new value
                        while iCurr < iNext:
                            for i in xrange(iUnitSize):
                                piAdiLineTemp[i] = piRef
                            piAdiLineTemp += iUnitSize
                            iCurr += 1
                    else:
                        piRef = piAdiLine[iCurr * iUnitSize - 1]
                        for i in xrange(iUnitSize):
                            piAdiLineTemp[i] = piRef
                        piAdiLineTemp += iUnitSize
                        iCurr += 1
                else:
                    piAdiLineTemp += iUnitSize
                    iCurr += 1
      
            # Copy processed samples
            piAdiLineTemp = piAdiLine + uiHeight + iUnitSize - 2
            for i in xrange(uiWidth):
                piAdiTemp[i] = piAdiLineTemp[i]
            piAdiLineTemp = piAdiLine + uiHeight - 1
            for i in xrange(1, uiHeight):
                piAdiTemp[i*uiWidth] = piAdiLineTemp[-i]

    def isAboveLeftAvailable(self, pcCU, uiPartIdxLT):
        bAboveLeftFlag = False
        uiPartAboveLeft = 0
        pcCUAboveLeft, uiPartAboveLeft = pcCU.getPUAboveLeft(uiPartAboveLeft, uiPartIdxLT, True, False)
        if pcCU.getSlice().getPPS().getConstrainedIntraPred():
            bAboveLeftFlag = pcCUAboveLeft and pcCUAboveLeft.getPredictionMode(uiPartAboveLeft) == MODE_INTRA
        else:
            bAboveLeftFlag = True if pcCUAboveLeft else False
        return bAboveLeftFlag

    def isAboveAvailable(self, pcCU, uiPartIdxLT, uiPartIdxRT, bValidFlags):
        uiRasterPartBegin = g_auiZscanToRaster[uiPartIdxLT]
        uiRasterPartEnd = g_auiZscanToRaster[uiPartIdxRT] + 1
        uiIdxStep = 1
        pbValidFlags = pointer(bValidFlags, type='bool *')
        iNumIntra = 0

        for uiRasterPart in xrange(uiRasterPartBegin, uiRasterPartEnd, uiIdxStep):
            uiPartAbove = 0
            pcCUAbove, uiPartAbove = pcCU.getPUAbove(uiPartAbove, g_auiRasterToZscan[uiRasterPart], True, False)
            if pcCU.getSlice().getPPS().getConstrainedIntraPred():
                if pcCUAbove and pcCUAbove.getPredictionMode(uiPartAbove) == MODE_INTRA:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            else:
                if pcCUAbove:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            pbValidFlags += 1

        return iNumIntra

    def isLeftAvailable(self, pcCU, uiPartIdxLT, uiPartIdxLB, bValidFlags):
        uiRasterPartBegin = g_auiZscanToRaster[uiPartIdxLT]
        uiRasterPartEnd = g_auiZscanToRaster[uiPartIdxLB] + 1
        uiIdxStep = pcCU.getPic().getNumPartInWidth()
        pbValidFlags = pointer(bValidFlags, type='bool *')
        iNumIntra = 0

        for uiRasterPart in xrange(uiRasterPartBegin, uiRasterPartEnd, uiIdxStep):
            uiPartLeft = 0
            pcCULeft, uiPartLeft = pcCU.getPULeft(uiPartLeft, g_auiRasterToZscan[uiRasterPart], True, False)
            if pcCU.getSlice().getPPS().getConstrainedIntraPred():
                if pcCULeft and pcCULeft.getPredictionMode(uiPartAbove) == MODE_INTRA:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            else:
                if pcCULeft:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            pbValidFlags -= 1 # opposite direction

        return iNumIntra

    def isAboveRightAvailable(self, pcCU, uiPartIdxLT, uiPartIdxRT, bValidFlags):
        uiNumUnitsInPU = g_auiZscanToRaster[uiPartIdxRT] - g_auiZscanToRaster[uiPartIdxLT] + 1
        uiPuWidth = uiNumUnitsInPU * pcCU.getPic().getMinCUWidth()
        pbValidFlags = pointer(bValidFlags, type='bool *')
        iNumIntra = 0

        for uiOffset in xrange(1, uiNumUnitsInPU+1):
            uiPartAboveRight = 0
            pcCUAboveRight, uiPartAboveRight = pcCU.getPUAboveRightAdi(uiPartAboveRight, uiPuWidth, uiPartIdxRT, uiOffset, True, False)
            if pcCU.getSlice().getPPS().getConstrainedIntraPred():
                if pcCUAboveRight and pcCUAboveRight.getPredictionMode(uiPartAboveRight) == MODE_INTRA:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            else:
                if pcCUAboveRight:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            pbValidFlags += 1

        return iNumIntra

    def isBelowLeftAvailable(self, pcCU, uiPartIdxLT, uiPartIdxLB, bValidFlags):
        uiNumUnitsInPU = (g_auiZscanToRaster[uiPartIdxLB] - g_auiZscanToRaster[uiPartIdxLT]) / \
                         pcCU.getPic().getNumPartInWidth() + 1
        uiPuHeight = uiNumUnitsInPU * pcCU.getPic().getMinCUHeight()
        pbValidFlags = pointer(bValidFlags, type='bool *')
        iNumIntra = 0

        for uiOffset in xrange(1, uiNumUnitsInPU+1):
            uiPartBelowLeft = 0
            pcCUBelowLeft, uiPartBelowLeft = pcCU.getPUBelowLeftAdi(uiPartBelowLeft, uiPuHeight, uiPartIdxLB, uiOffset, True, False)
            if pcCU.getSlice().getPPS().getConstrainedIntraPred():
                if pcCUBelowLeft and pcCUBelowLeft.getPredictionMode(uiPartBelowLeft) == MODE_INTRA:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            else:
                if pcCUBelowLeft:
                    iNumIntra += 1
                    pbValidFlags[0] = True
                else:
                    pbValidFlags[0] = False
            pbValidFlags -= 1 # opposite direction

        return iNumIntra
