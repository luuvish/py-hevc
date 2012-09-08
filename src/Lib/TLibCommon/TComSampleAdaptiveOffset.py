# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComSampleAdaptiveOffet.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import ArrayInt, ArrayPel

# TypeDef.h
SAO_EO_LEN = 4
SAO_BO_LEN = 4
SAO_MAX_BO_CLASSES = 32
SAO_EO_0 = 0 
SAO_EO_1 = 1
SAO_EO_2 = 2
SAO_EO_3 = 3
SAO_BO = 4
MAX_NUM_SAO_TYPE = 5
# CommonDef.h
MAX_INT = 2147483647
MAX_DOUBLE = 1.7e+308
# TComRom.h

# TComDataCU.h
SGU_L = 0
SGU_R = 1
SGU_T = 2
SGU_B = 3
SGU_TL = 4
SGU_TR = 5
SGU_BL = 6
SGU_BR = 7
# NUM_SGU_BORDER

# TComSampleAdaptiveOffset.h
SAO_MAX_DEPTH = 4
SAO_BO_BITS = 5
LUMA_GROUP_NUM = 1 << SAO_BO_BITS
MAX_NUM_SAO_OFFSETS = 4
MAX_NUM_SAO_CLASS = 33

xSign = lambda x: (x >> 31) | ((-x) >> 31)

logf = lambda x: x


class TComSampleAdaptiveOffset(object):

    m_uiMaxDepth = SAO_MAX_DEPTH

    m_aiNumCulPartsLevel = (
          1, # level 0
          5, # level 1
         21, # level 2
         85, # level 3
        341, # level 4
    )

    m_auiEoTable = (
        1, # 0    
        2, # 1   
        0, # 2
        3, # 3
        4, # 4
        0, # 5  
        0, # 6  
        0, # 7 
        0
    )

    m_iNumClass = (
        SAO_EO_LEN,
        SAO_EO_LEN,
        SAO_EO_LEN,
        SAO_EO_LEN,
        SAO_BO_LEN
    )

    def __init__(self):
        self.m_pcPic = None

        self.m_iOffsetBo = None
        self.m_iOffsetEo = LUMA_GROUP_NUM * [0]

        self.m_iPicWidth = 0
        self.m_iPicHeight = 0
        self.m_uiMaxSplitLevel = 0
        self.m_uiMaxCUWidth = 0
        self.m_uiMaxCUHeight = 0
        self.m_iNumCuInWidth = 0
        self.m_iNumCuInHeight = 0
        self.m_iNumTotalParts = 0

        self.m_eSliceType = 0
        self.m_iPicNalReferenceIdc = 0

        self.m_uiSaoBitIncrease = 0
        self.m_uiQP = 0

        self.m_pClipTable = None
        self.m_pClipTableBase = None
        self.m_lumaTableBo = None
        self.m_iUpBuff1 = None
        self.m_iUpBuff2 = None
        self.m_iUpBufft = None
    #   self.ipSwap = None
        self.m_bUseNIF = False
        self.m_uiNumSlicesInPic = 0
        self.m_iSGDepth = 0
        self.m_pcYuvTmp = None

        self.m_pTmpU1 = None
        self.m_pTmpU2 = None
        self.m_pTmpL1 = None
        self.m_pTmpL2 = None
        self.m_iLcuPartIdx = None
        self.m_maxNumOffsetPerPic = 0
        self.m_saoLcuBoundary = False

    def create(self, uiSourceWidth, uiSourceHeight,
               uiMaxCUWidth, uiMaxCUHeight, uiMaxCUDepth):
        self.m_iPicWidth = uiSourceWidth
        self.m_iPicHeight = uiSourceHeight

        self.m_uiMaxCUWidth = uiMaxCUWidth
        self.m_uiMaxCUHeight = uiMaxCUHeight

        self.m_iNumCuInWidth = self.m_iPicWidth / self.m_uiMaxCUWidth
        self.m_iNumCuInWidth += 1 if self.m_iPicWidth % self.m_uiMaxCUWidth else 0

        self.m_iNumCuInHeight = self.m_iPicHeight / self.m_uiMaxCUHeight
        self.m_iNumCuInHeight += 1 if self.m_iPicHeight % self.m_uiMaxCUHeight else 0

        iMaxSplitLevelHeight = logf(float(self.m_iNumCuInHeight)/logf(2.0))
        iMaxSplitLevelWidth = logf(float(self.m_iNumCuInWidth)/logf(2.0))

        self.m_uiMaxSplitLevel = iMaxSplitLevelHeight if iMaxSplitLevelHeight < iMaxSplitLevelWidth else iMaxSplitLevelWidth
        self.m_uiMaxSplitLevel = self.m_uiMaxSplitLevel if self.m_uiMaxSplitLevel < self.m_uiMaxDepth else self.m_uiMaxDepth
        # various structures are overloaded to store per component data.
        # m_iNumTotalParts must allow for sufficient storage in any allocated arrays
        self.m_iNumTotalParts = max(3, self.m_aiNumCulPartsLevel[self.m_uiMaxSplitLevel])

        uiInternalBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        uiPixelRange = 1 << uiInternalBitDepth
        uiBoRangeShift = uiInternalBitDepth - SAO_BO_BITS

        self.m_lumaTableBo = ArrayPel(uiPixelRange)
        for k2 in xrange(uiPixelRange):
            self.m_lumaTableBo[k2] = 1 + (k2 >> uiBoRangeShift)
        self.m_iUpBuff1 = ArrayInt(self.m_iPicWidth+2)
        self.m_iUpBuff2 = ArrayInt(self.m_iPicWidth+2)
        self.m_iUpBufft = ArrayInt(self.m_iPicWidth+2)

        uiMaxY = cvar.g_uiIBDI_MAX
        uiMinY = 0

        iCRangeExt = uiMaxY >> 1

        self.m_pClipTableBase = ArrayPel(uiMaxY + 2 * iCRangeExt)
        self.m_iOffsetBo = ArrayInt(uiMaxY + 2 * iCRangeExt)

        for i in xrange(uiMinY+iCRangeExt):
            self.m_pClipTableBase[i] = uiMinY

        for i in xrange(uiMinY+iCRangeExt, uiMaxY+iCRangeExt):
            self.m_pClipTableBase[i] = i - iCRangeExt

        for i in xrange(uiMaxY+iCRangeExt, uiMaxY+2*iCRangeExt):
            self.m_pClipTableBase[i] = uiMaxY

        self.m_pClipTable = self.m_pClipTableBase[iCRangeExt]

        self.m_iLcuPartIdx = ArrayInt(self.m_iNumCuInHeight*self.m_iNumCuInWidth)
        self.m_pTmpL1 = ArrayPel(self.m_uiMaxCUHeight+1)
        self.m_pTmpL2 = ArrayPel(self.m_uiMaxCUHeight+1)
        self.m_pTmpU1 = ArrayPel(self.m_iPicWidth)
        self.m_pTmpU2 = ArrayPel(self.m_iPicWidth)

    def destroy(self):
        if self.m_pClipTableBase:
            del self.m_pClipTableBase
            self.m_pClipTableBase = None
        if self.m_iOffsetBo:
            del self.m_iOffsetBo
            self.m_iOffsetBo = None
        if self.m_lumaTableBo:
            del self.m_lumaTableBo
            self.m_lumaTableBo = None

        if self.m_iUpBuff1:
            del self.m_iUpBuff1
            self.m_iUpBuff1 = None
        if self.m_iUpBuff2:
            del self.m_iUpBuff2
            self.m_iUpBuff2 = None
        if self.m_iUpBufft:
            del self.m_iUpBufft
            self.m_iUpBufft = None
        if self.m_pTmpL1:
            del self.m_pTmpL1
            self.m_pTmpL1 = None
        if self.m_pTmpL2:
            del self.m_pTmpL2
            self.m_pTmpL2 = None
        if self.m_pTmpU1:
            del self.m_pTmpU1
            self.m_pTmpU1 = None
        if self.m_pTmpU2:
            del self.m_pTmpU2
            self.m_pTmpU2 = None
        if self.m_iLcuPartIdx:
            del self.m_iLcuPartIdx
            self.m_iLcuPartIdx = None

    def convertLevelRowCol2Idx(level, row, col):
        idx = 0
        if level == 0:
            idx = 0
        elif level == 1:
            idx = 1 + row*2 + col
        elif level == 2:
            idx = 5 + row*4 + col
        elif level == 3:
            idx = 21 + row*8 + col
        else: # (level == 4)
            idx = 85 + row*16 + col
        return idx

    def initSAOParam(self, pcSaoParam, iPartLevel, iPartRow, iPartCol,
                     iParentPartIdx, StartCUX, EndCUX, StartCUY, EndCUY, iYCbCr):
        iPartIdx = self.convertLevelRowCol2Idx(iPartLevel, iPartRow, iPartCol)

        pSaoPart = pcSaoParam.psSaoPart[iYCbCr][iPartIdx]

        pSaoPart.PartIdx = iPartIdx
        pSaoPart.PartLevel = iPartLevel
        pSaoPart.PartRow = iPartRow
        pSaoPart.PartCol = iPartCol

        pSaoPart.StartCUX = StartCUX
        pSaoPart.EndCUX = EndCUX
        pSaoPart.StartCUY = StartCUY
        pSaoPart.EndCUY = EndCUY

        pSaoPart.UpPartIdx = iParentPartIdx
        pSaoPart.iBestType = -1
        pSaoPart.iLength = 0

        pSaoPart.subTypeIdx = 0

        for j in xrange(MAX_NUM_SAO_OFFSETS):
            pSaoPart.iOffset[j] = 0

        if pSaoPart.PartLevel != self.m_uiMaxSplitLevel:
            DownLevel = iPartLevel + 1
            DownRowStart = iPartRow << 1
            DownColStart = iPartCol << 1

            NumCUWidth = EndCUX - StartCUX + 1
            NumCUHeight = EndCUY - StartCUY + 1
            NumCULeft = NumCUWidth >> 1
            NumCURight = NumCUHeight >> 1

            DownStartCUX = StartCUX
            DownEndCUX = DownStartCUX + NumCULeft - 1
            DownStartCUY = StartCUY
            DownEndCUY = DownStartCUY + NumCUTop - 1
            iDownRowIdx = DownRowStart
            iDownColIdx = DownColStart

            pSaoPart.DownPartsIdx[0] = self.convertLevelRowCol2Idx(DownLevel, iDownRowIdx, iDownColIdx)

            self.initSAOParam(pcSaoParam,
                DownLevel, iDownRowIdx, iDownColIdx, iPartIdx,
                DownStartCUX, DownEndCUX, DownStartCUY, DownEndCUY, iYCbCr)

            DownStartCUX = StartCUX + NumCULeft
            DownEndCUX = EndCUX
            DownStartCUY = StartCUY
            DownEndCUY = DownStartCUY + NumCUTop - 1
            iDownRowIdx = DownRowStart
            iDownColIdx = DownColStart + 1

            pSaoPart.DownPartsIdx[1] = self.convertLevelRowCol2Idx(DownLevel, iDownRowIdx, iDownColIdx)

            self.initSAOParam(pcSaoParam,
                DownLevel, iDownRowIdx, iDownColIdx, iPartIdx,
                DownStartCUX, DownEndCUX, DownStartCUY, DownEndCUY, iYCbCr)

            DownStartCUX = StartCUX
            DownEndCUX = DownStartCUX + NumCULeft - 1
            DownStartCUY = StartCUY + NumCUTop
            DownEndCUY = EndCUY
            iDownRowIdx = DownRowStart + 1
            iDownColIdx = DownColStart

            pSaoPart.DownPartsIdx[2] = self.convertLevelRowCol2Idx(DownLevel, iDownRowIdx, iDownColIdx)

            self.initSAOParam(pcSaoParam,
                DownLevel, iDownRowIdx, iDownColIdx, iPartIdx,
                DownStartCUX, DownEndCUX, DownStartCUY, DownEndCUY, iYCbCr)

            DownStartCUX = StartCUX + NumCULeft
            DownEndCUX = EndCUX
            DownStartCUY = StartCUY + NumCUTop
            DownEndCUY = EndCUY
            iDownRowIdx = DownRowStart + 1
            iDownColIdx = DownColStart + 1

            pSaoPart.DownPartsIdx[3] = self.convertLevelRowCol2Idx(DownLevel, iDownRowIdx, iDownColIdx)

            self.initSAOParam(pcSaoParam,
                DownLevel, iDownRowIdx, iDownColIdx, iPartIdx,
                DownStartCUX, DownEndCUX, DownStartCUY, DownEndCUY, iYCbCr)
        else:
            pSaoPart.DownPartsIdx[0] = -1
            pSaoPart.DownPartsIdx[1] = -1
            pSaoPart.DownPartsIdx[2] = -1
            pSaoPart.DownPartsIdx[3] = -1

    def allocSaoParam(self, pcSaoParam):
        pcSaoParam.iMaxSplitLevel = self.m_uiMaxSplitLevel
        pcSaoParam.psSaoPart[0] = ArraySAOQTPart(self.m_aiNumCulPartsLevel[pcSaoParam.iMaxSplitLevel])
        self.initSAOParam(pcSaoParam, 0, 0, 0, -1, 0, self.m_iNumCuInWidth-1, 0, self.m_iNumCuInHeight-1, 0)
        pcSaoParam.psSaoPart[1] = ArraySAOQTPart(self.m_aiNumCulPartsLevel[pcSaoParam.iMaxSplitLevel])
        pcSaoParam.psSaoPart[2] = ArraySAOQTPart(self.m_aiNumCulPartsLevel[pcSaoParam.iMaxSplitLevel])
        self.initSAOParam(pcSaoParam, 0, 0, 0, -1, 0, self.m_iNumCuInWidth-1, 0, self.m_iNumCuInHeight-1, 1)
        self.initSAOParam(pcSaoParam, 0, 0, 0, -1, 0, self.m_iNumCuInWidth-1, 0, self.m_iNumCuInHeight-1, 2)
        for j in xrange(MAX_NUM_SAO_TYPE):
            pcSaoParam.iNumClass[j] = self.m_iNumClass[j]
        pcSaoParam.numCuInWidth = self.m_iNumCuInWidth
        pcSaoParam.numCuInHeight = self.m_iNumCuInHeight
        pcSaoParam.saoLcuParam[0] = ArraySaoLcuParam(self.m_iNumCuInHeight*self.m_iNumCuInWidth)
        pcSaoParam.saoLcuParam[1] = ArraySaoLcuParam(self.m_iNumCuInHeight*self.m_iNumCuInWidth)
        pcSaoParam.saoLcuParam[2] = ArraySaoLcuParam(self.m_iNumCuInHeight*self.m_iNumCuInWidth)

    def resetSAOParam(self, pcSaoParam):
        iNumComponent = 3
        for c in xrange(iNumComponent):
            if c < 2:
                pcSaoParam.bsSaoFlag[c] = 0
            for i in xrange(self.m_aiNumCulPartsLevel[self.m_uiMaxSplitLevel]):
                pcSaoParam.psSaoPart[c][i].iBestType = -1
                pcSaoParam.psSaoPart[c][i].iLength = 0
                pcSaoParam.psSaoPart[c][i].bSplit = False
                pcSaoParam.psSaoPart[c][i].bProcessed = False
                pcSaoParam.psSaoPart[c][i].dMinCost = MAX_DOUBLE
                pcSaoParam.psSaoPart[c][i].iMinDist = MAX_INT
                pcSaoParam.psSaoPart[c][i].iMinRate = MAX_INT
                pcSaoParam.psSaoPart[c][i].subTypeIdx = 0
                for j in xrange(MAX_NUM_SAO_OFFSETS):
                    pcSaoParam.psSaoPart[c][i].iOffset[j] = 0
                    pcSaoParam.psSaoPart[c][i].iOffset[j] = 0
                    pcSaoParam.psSaoPart[c][i].iOffset[j] = 0
            pcSaoParam.oneUnitFlag[0] = 0
            pcSaoParam.oneUnitFlag[1] = 0
            pcSaoParam.oneUnitFlag[2] = 0
            self.resetLcuPart(pcSaoParam.salLcuParam[0])
            self.resetLcuPart(pcSaoParam.salLcuParam[1])
            self.resetLcuPart(pcSaoParam.salLcuParam[2])

    @staticmethod
    def freeSaoParam(pcSaoParam):
        del psSaoPart.psSaoPart[0]
        del psSaoPart.psSaoPart[1]
        del psSaoPart.psSaoPart[2]
        psSaoPart.psSaoPart[0] = 0
        psSaoPart.psSaoPart[1] = 0
        psSaoPart.psSaoPart[2] = 0
        if pcSaoParam.saoLcuParam[0]:
            del pcSaoParam.saoLcuParam[0]
            pcSaoParam.saoLcuParam[0] = None
        if pcSaoParam.saoLcuParam[1]:
            del pcSaoParam.saoLcuParam[1]
            pcSaoParam.saoLcuParam[1] = None
        if pcSaoParam.saoLcuParam[2]:
            del pcSaoParam.saoLcuParam[2]
            pcSaoParam.saoLcuParam[2] = None

    def SAOProcess(self, pcPic, pcSaoParam):
        if pcSaoParam.bSaoFlag[0] or pcSaoParam.bSaoFlag[1]:
            self.m_uiSaoBitIncrease = cvar.g_uiBitDepth + cvar.g_uiBitIncrement - \
                min(cvar.g_uiBitDepth + cvar.g_uiBitIncrement, 10)

            if self.m_bUseNIF:
                self.m_pcPic.getPicYuvRec().copyToPic(self.m_pcYuvTmp)
            if self.m_saoLcuBasedOptimization:
                pcSaoParam.oneUnitFlag[0] = 0
                pcSaoParam.oneUnitFlag[1] = 0
                pcSaoParam.oneUnitFlag[2] = 0
            iY = 0
            if pcSaoParam.bSaoFlag[0]:
                self.processSaoUnitAll(pcSaoParam.salLcuParam[iY], pcSaoParam.oneUnitFlag[iY], iY)
            if pcSaoParam.bSaoFlag[1]:
                self.processSaoUnitAll(pcSaoParam.salLcuParam[1], pcSaoParam.oneUnitFlag[1], 1) #Cb
                self.processSaoUnitAll(pcSaoParam.salLcuParam[2], pcSaoParam.oneUnitFlag[2], 2) #Cr
            self.m_pcPic = None

    def processSaoCu(self, iAddr, iSaoType, iYCbCr):
        if not self.m_bUseNIF:
            self.processSaoCuOrg(iAddr, iSaoType, iYCbCr)
        else:
            isChroma = 1 if iYCbCr else 0
            stride = self.m_pcPic.getCStride() if iYCbCr else self.m_pcPic.getStride()
            pPicRest = self.getPicYuvAddr(self.m_pcPic.getPicYuvRec(), iYCbCr)
            pPicDec = self.getPicYuvAddr(self.m_pcYuvTmp, iYCbCr)

            vFilterBlocks = self.m_pcPic.getCU(iAddr).getNDBFilterBlocks()

            # variables
            for i in xrange(vFilterBlocks.size()):
                xPos = vFilterBlocks[i].posX >> isChroma
                yPos = vFilterBlocks[i].posY >> isChroma
                width = vFilterBlocks[i].width >> isChroma
                height = vFilterBlocks[i].height >> isChroma
                pbBorderAvail = vFilterBlocks[i].isBorderAvailable

                posOffset = yPos * stride + xPos

                self.processSaoBlock(pPicDec+posOffset, pPicRest+posOffset,
                    stride, iSaoType, xPos, yPos, width, height, pbBorderAvail)

    def getPicYuvAddr(self, pcPicYuv, iYCbCr, iAddr=0):
        if iYCbCr == 0:
            return pcPicYuv.getLumaAddr(iAddr)
        elif iYCbCr == 1:
            return pcPicYuv.getCbAddr(iAddr)
        elif iYCbCr == 2:
            return pcPicYuv.getCrAddr(iAddr)
        else:
            return None

    def processSaoCuOrg(self, iAddr, iPartIdx, iYCbCr):
        pTmpCu = self.m_pcPic.getCU(iAddr)
        iLcuWidth = self.m_uiMaxCUWidth
        iLcuHeight = self.m_uiMaxCUHeight
        uiLPelX = pTmpCu.getCUPelX()
        uiTPelY = pTmpCu.getCUPelY()
        iIsChroma = 1 if iYCbCr else 0

        iPicWidthTmp = self.m_iPicWidth >> iIsChroma
        iPicHeightTmp = self.m_iPicHeight >> iIsChroma
        iLcuWidth = iLcuWidth >> iIsChroma
        iLcuHeight = iLcuHeight >> iIsChroma
        uiLPelX = uiLPelX >> iIsChroma
        uiTPelY = uiTPelY >> iIsChroma
        uiRPelX = uiLPelX + iLcuWidth
        uiBPelY = uiTPelY + iLcuHeight
        uiRPelX = iPicWidthTmp if uiRPelX > iPicWidthTmp else uiRPelX
        uiBPelY = iPicHeightTmp if uiBPelY > iPicHeightTmp else uiBPelY
        iLcuWidth = uiRPelX - uiLPelX
        iLcuHeight = uiBPelY - uiTPelY

        if not pTmpCu.getPic():
            return
        if iYCbCr == 0:
            pRec = self.m_pcPic.getPicYuvRec().getLumaAddr(iAddr)
            iStride = self.m_pcPic.getStride()
        elif iYCbCr == 1:
            pRec = self.m_pcPic.getPicYuvRec().getCbAddr(iAddr)
            iStride = self.m_pcPic.getCStride()
        else:
            pRec = self.m_pcPic.getPicYuvRec().getCrAddr(iAddr)
            iStride = self.m_pcPic.getCStride()

        iCuHeightTmp = self.m_uiMaxCUHeight >> iIsChroma
        iShift = (self.m_uiMaxCUWidth >> iIsChroma) - 1
        for i in xrange(iCuHeightTmp+1):
            self.m_pTmpL2[i] = pDec[iShift]
            pRec += iStride
        pRec -= iStride * (iCuHeightTmp+1)

        pTmpL = self.m_pTmpL1
        pTmpU = self.m_pTmpU1[uiLPelX]

        if iSaoType == SAO_EO_0: # dir: -
            iStartX = 1 if uiLPelX == 0 else 0
            iEndX = iLcuWidth-1 if uiRPelX == iPicWidthTmp else iLcuWidth
            for y in xrange(iLcuHeight):
                iSignLeft = xSign(pDec[iStartX] - pTmpL[y])
                for x in xrange(iStartX, iEndX):
                    iSignRight = xSign(pDec[x] - pRec[x+1])
                    uiEdgeType = iSignRight + iSignLeft + 2
                    iSignLeft = -iSignRight

                    pRec[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[uiEdgeType]]
                pRec += iStride
        elif iSaoType == SAO_EO_1: # dir: |
            iStartY = 1 if uiTPelY == 0 else 0
            iEndY = iLcuHeight-1 if uiBPelY == iPicHeightTmp else iLcuHeight
            if uiTPelY == 0:
                pRec += iStride
            for x in xrange(iLcuWidth):
                self.m_iUpBuff1[x] = xSign(pRec[x] - pTmpU[x])
            for y in xrange(iStartY, iEndY):
                for x in xrange(iLcuWidth):
                    iSignDown = xSign(pDec[x] - pRec[x+stride])
                    uiEdgeType = iSignDown + self.m_iUpBuff1[x] + 2
                    self.m_iUpBuff1[x] = -iSignDown

                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[uiEdgeType]]
                pRec += iStride
        elif iSaoType == SAO_EO_2: # dir: 135
            iStartX = 1 if uiLPelX == 0 else 0
            iEndX = iLcuWidth-1 if uiRPelX == iPicWidthTmp else iLcuWidth

            iStartY = 1 if uiTPelY == 0 else 0
            iEndY = iLcuHeight-1 if uiBPelY == iPicHeightTmp else iLcuHeight

            if uiTPelY == 0:
                pRec += iStride

            for x in xrange(iStartX, iEndX):
                self.m_iUpBuff1[x] = xSign(pRec[x] - pTmpU[x-1])
            for y in xrange(iStartY, iEndY):
                iSignDown2 = xSign(pRec[iStride+iStartX] - pTmpL[y])
                for x in xrange(iStartX, iEndX):
                    iSignDown1 = xSign(pRec[x] - pRec[x+iStride+1])
                    uiEdgeType = iSignDown1 + self.m_iUpBuff1[x] + 2
                    self.m_iUpBufft[x+1] = -iSignDown1
                    pRec[x] = self.m_pClipTable[pRec[x] + self.m_iOffsetEo[uiEdgeType]]
                self.m_iUpBufft[iStartX] = iSignDown2

                self.m_iUpBuff2, self.m_iUpBuff1 = self.m_iUpBuff1, self.m_iUpBuff2

                pRec += iStride
        elif iSaoType == SAO_EO_3: # dir: 45
            iStartX = 1 if uiLPelX == 0 else 0
            iEndX = iLcuWidth-1 if uiRPelX == iPicWidthTmp else iLcuWidth

            iStartY = 1 if uiTPelY == 0 else 0
            iEndY = iLcuHeight-1 if uiBPelY == iPicHeightTmp else iLcuHeight

            if iStartY == 1:
                pRec += iStride

            for x in xrange(iStartX-1, iEndX):
                self.m_iUpBuff1[x] = xSign(pRec[x] - pTmpU[x+1])
            for y in xrange(iStartY, iEndY):
                x = iStartX
                iSignDown1 = xSign(pRec[x] - pTmpL[y+1])
                uiEdgeType = iSignDown1 + self.m_iUpBuff1[x] + 2
                self.m_iUpBuff1[x-1] = -iSignDown1
                pRec[x] = self.m_pClipTable[pRec[x] + self.m_iOffsetEo[uiEdgeType]]
                for x in xrange(iStartX+1, iEndX):
                    iSignDown1 = xSign(pDec[x] - pRec[x+iStride-1])
                    uiEdgeType = iSignDown1 + self.m_iUpBuff1[x] + 2
                    self.m_iUpBuff1[x-1] = -iSignDown1
                    pRec[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[uiEdgeType]]
                self.m_iUpBuff1[iEndX-1] = xSign(pRec[iEndX-1 + iStride] - pRec[iEndX])

                pRec += iStride
        elif iSaoType == SAO_BO:
            for y in xrange(iLcuHeight):
                for x in xrange(iLcuWidth):
                    pRec[x] = self.m_iOffsetBo[pRec[x]]
                pRec += iStride

        self.m_pTmpL2, self.m_pTmpL1 = self.m_pTmpL1, self.m_pTmpL2

    def createPicSaoInfo(self, pcPic, numSlicesInPic=1):
        self.m_pcPic = pcPic
        self.m_uiNumSlicesInPic = numSlicesInPic
        self.m_iSGDepth = 0
        self.m_bUseNIF = pcPic.getIndependentSliceBoundaryForNDBFilter() or \
                         pcPic.getIndependentTileBoundaryForNDBFilter()
        if self.m_bUseNIF:
            self.m_pcYuvTmp = pcPic.getYuvPicBufferForIndependentBoundaryProcessing()

    def destroyPicSaoInfo(self):
        pass

    def processSaoBlock(self, pDec, pRest, stride, iSaoType, xPos, yPos, width, height, pbBorderAvail):
        # variables
        if saoType == SAO_EO_0: # dir: -
            startX = 0 if pbBorderAvail[SGU_L] else 1
            endX = width if pbBorderAvail[SGU_R] else width-1
            for y in xrange(height):
                signLeft = xSign(pDec[startX] - pDec[startX-1])
                for x in xrange(startX, endX):
                    signRight = xSign(pDec[x] - pDec[x+1])
                    edgeType = signRight + signLeft + 2
                    signLeft = -signRight

                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
                pDec += stride
                pRest += stride
        elif saoType == SAO_EO_1: # dir: |
            startY = 0 if pbBorderAvail[SGU_T] else 1
            endY = height if pbBorderAvail[SGU_B] else height-1
            if not pbBorderAvail[SGU_T]:
                pDec += stride
                pRest += stride
            for x in xrange(width):
                self.m_iUpBuff1[x] = xSign(pDec[x] - pDec[x-stride])
            for y in xrange(startY, endY):
                for x in xrange(width):
                    signDown = xSign(pDec[x] - pDec[x+stride])
                    edgeType = signDown + self.m_iUpBuff1[x] + 2
                    self.m_iUpBuff1[x] = -signDown

                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
                pDec += stride
                pRest += stride
        elif saoType == SAO_EO_2: # dir: 135
            posShift = stride + 1
            startX = 0 if pbBorderAvail[SGU_L] else 1
            endX = width if pbBorderAvail[SGU_R] else width-1

            #prepare 2nd line upper sign
            pDec += stride
            for x in xrange(startX, endX+1):
                self.m_iUpBuff1[x] = xSign(pDec[x] - pDec[x - posShift])

            #1st line
            pDec -= stride
            if pbBorderAvail[SGU_TL]:
                x = 0
                edgeType = xSign(pDec[x] - pDec[x-posShift]) - self.m_iUpBuff1[x+1] + 2
                pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
            if pbBorderAvail[SGU_T]:
                for x in xrange(1, endX):
                    edgeType = xSign(pDec[x] - pDec[x-posShift]) - self.m_iUpBuff1[x+1] + 2
                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
            pDec += stride
            pRest += stride

            #middle lines
            for y in xrange(1, height-1):
                for x in xrange(startX, endX):
                    signDown1 = xSign(pDec[x] - pDec[x+posShift])
                    edgeType = signDown1 + self.m_iUpBuff1[x] + 2
                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]

                    self.m_iUpBufft[x+1] = -signDown1
                self.m_iUpBufft[startX] = xSign(pDec[stride+startX] - pDec[startX-1])

                self.m_iUpBuff2, self.m_iUpBuff1 = self.m_iUpBuff1, self.m_iUpBuff2

                pDec += stride
                pRest += stride

            #last line
            if pbBorderAvail[SGU_B]:
                for x in xrange(startX, width-1):
                    edgeType = xSign(pDec[x] - pDec[x+posShift]) + self.m_iUpBuff1[x] + 2
                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
            if pbBorderAvail[SGU_BR]:
                x = width - 1
                edgeType = xSign(pDec[x] - pDec[x+posShift]) + self.m_iUpBuff1[x] + 2
                pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
        elif saoType == SAO_EO_3: # dir: 45
            posShift = stride - 1
            startX = 0 if pbBorderAvail[SGU_L] else 1
            endX = width if pbBorderAvail[SGU_R] else width-1

            #prepare 2nd line upper sign
            pDec += stride
            for x in xrange(startX-1, endX):
                self.m_iUpBuff1[x] = xSign(pDec[x] - pDec[x - posShift])

            #first line
            pDec -= stride
            if pbBorderAvail[SGU_T]:
                for x in xrange(startX, width-1):
                    edgeType = xSign(pDec[x] - pDec[x-posShift]) - self.m_iUpBuff1[x-1] + 2
                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
            if pbBorderAvail[SGU_TR]:
                x = width-1
                edgeType = xSign(pDec[x] - pDec[x-posShift]) - self.m_iUpBuff1[x-1] + 2
                pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
            pDec += stride
            pRest += stride

            #middle lines
            for y in xrange(1, height-1):
                for x in xrange(startX, endX):
                    signDown1 = xSign(pDec[x] - pDec[x+posShift])
                    edgeType = signDown1 + self.m_iUpBuff1[x] + 2

                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
                    self.m_iUpBuff1[x-1] = -signDown1
                self.m_iUpBuff1[endX-1] = xSign(pDec[endX-1 + stride] - pDec[endX])

                pDec += stride
                pRest += stride

            #last line
            if pbBorderAvail[SGU_BL]:
                x = 0
                edgeType = xSign(pDec[x] - pDec[x+posShift]) + self.m_iUpBuff1[x] + 2
                pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
            if pbBorderAvail[SGU_B]:
                for x in xrange(1, endX):
                    edgeType = xSign(pDec[x] - pDec[x+posShift]) + self.m_iUpBuff1[x] + 2
                    pRest[x] = self.m_pClipTable[pDec[x] + self.m_iOffsetEo[edgeType]]
        elif saoType == SAO_BO:
            for y in xrange(height):
                for x in xrange(width):
                    pRest[x] = self.m_iOffsetBo[pDec[x]]
                pRest += stride
                pDec += stride

    def resetLcuPart(self, saoLcuParam):
        for i in xrange(self.m_iNumCuInWidth * self.m_iNumCuInHeight):
            saoLcuParam[i].mergeUpFlag = 1
            saoLcuParam[i].mergeLeftFlag = 0
            saoLcuParam[i].partIdx = 0
            saoLcuParam[i].typeIdx = -1
            for j in xrange(MAX_NUM_SAO_OFFSETS):
                saoLcuParam[i].offset[j] = 0
            saoLcuParam[i].subTypeIdx = 0

    def convertQT2SaoUnit(self, saoParam, partIdx, yCbCr):
        saoPart = saoParam.psSaoPart[yCbCr][partIdx]
        if not saoPart.bSplit:
            self.convertOnePart2SaoUnit(saoParam, partIdx, yCbCr)
            return

        if saoPart.PartLevel < self.m_uiMaxSplitLevel:
            self.convertQT2SaoUnit(saoParam, saoPart.DownPartsIdx[0], yCbCr)
            self.convertQT2SaoUnit(saoParam, saoPart.DownPartsIdx[1], yCbCr)
            self.convertQT2SaoUnit(saoParam, saoPart.DownPartsIdx[2], yCbCr)
            self.convertQT2SaoUnit(saoParam, saoPart.DownPartsIdx[3], yCbCr)

    def convertOnePart2SaoUnit(self, saoParam, partIdx, yCbCr):
        frameWidthInCU = self.m_pcPic.getFrameWidthInCU()
        saoQTPart = saoParam.psSaoPart[yCbCr]
        saoLcuParam = saoParam.saoLcuParam[yCbCr]

        for idxY in xrange(saoQTPart[partIdx].StartCUY, saoQTPart[partIdx].EndCUY+1):
            for idxX in xrange(saoQTPart[partIdx].StartCUX, saoQTPart[partIdx].EndCUX+1):
                addr = idxY * frameWidthInCU + idxX
                saoLcuParam[addr].partIdxTmp = partIdx
                saoLcuParam[addr].typeIdx = saoQTPart[partIdx].iBestType
                salLcuParam[addr].subTypeIdx = saoQTPart[partIdx].subTypeIdx
                if saoLcuParam[addr].typeIdx != -1:
                    salLcuParam[addr].length = saoQTPart[partIdx].iLength
                    for j in xrange(MAX_NUM_SAO_OFFSETS):
                        salLcuParam[addr].offset[j] = saoQTPart[partIdx].iOffset[j]
                else:
                    salLcuParam[addr].length = 0
                    saoLcuParam[addr].subTypeIdx = saoQTPart[partIdx].subTypeIdx
                    for j in xrange(MAX_NUM_SAO_OFFSETS):
                        saoLcuParam[addr].offset[j] = 0

    def processSaoUnitAll(self, salLcuParam, oneUnitFlag, yCbCr):
        if yCbCr == 0:
            pRec = self.m_pcPic.getPicYuvRec().getLumaAddr()
            picWidthTmp = self.m_iPicWidth
        elif yCbCr == 1:
            pRec = self.m_pcPic.getPicYuvRec().getCbAddr()
            picWidthTmp = self.m_iPicWidth >> 1
        else:
            pRec = self.m_pcPic.getPicYuvRec().getCrAddr()
            picWidthTmp = self.m_iPicWidth >> 1

        for i in xrange(picWidthTmp):
            self.m_pTmpU1[i] = pRec[i]

        ppLumaTable = None
        offset = (LUMA_GROUP_NUM+1) * [0]
        frameWidthInCU = self.m_pcPic.getFrameWidthInCU()
        frameHeightInCU = self.m_pcPic.getFrameHeightInCU()
        isChroma = 0 if yCbCr == 0 else 1

        offset[0] = 0
        for idxY in xrange(frameHeightInCU):
            addr = idxY * frameWidthInCU
            if yCbCr == 0:
                pRec = self.m_pcPic.getPicYuvRec().getLumaAddr(addr)
                stride = self.m_pcPic.getStride()
                picWidthTmp = self.m_iPicWidth
            elif yCbCr == 1:
                pRec = self.m_pcPic.getPicYuvRec().getCbAddr(addr)
                stride = self.m_pcPic.getCStride()
                picWidthTmp = self.m_iPicWidth >> 1
            else:
                pRec = self.m_pcPic.getPicYuvRec().getCrAddr(addr)
                stride = self.m_pcPic.getCStride()
                picWidthTmp = self.m_iPicWidth >> 1

            for i in xrange((self.m_uiMaxCUHeight>>isChroma)+1):
                self.m_pTmpL1[i] = pRec[0]
                pRec += stride
            pRec -= (stride<<1)

            for i in xrange(picWidthTmp):
                self.m_pTmpU2[i] = pRec[i]

            for idxX in xrange(frameWidthInCU):
                addr = idxY * frameWidthInCU + idxX

                if oneUnitFlag:
                    typeIdx = salLcuParam[0].typeIdx
                    mergeLeftFlag = 0 if addr == 0 else 1
                else:
                    typeIdx = salLcuParam[addr].typeIdx
                    mergeLeftFlag = salLcuParam[addr].mergeLeftFlag
                if typeIdx >= 0:
                    if not mergeLeftFlag:
                        if typeIdx == SAO_BO:
                            for i in xrange(SAO_MAX_BO_CLASSES+1):
                                offset[i] = 0
                            for i in xrange(saoLcuParam[addr].length):
                                offset[(salLcuParam[addr].subTypeIdx+i) % SAO_MAX_BO_CLASSES + 1] = \
                                    saoLcuParam[addr].offset[i] << self.m_uiSaoBitIncrease

                            ppLumaTable = self.m_lumaTableBo

                            for i in xrange(1 << (cvar.g_uiBitIncrement+8)):
                                self.m_iOffsetBo[i] = self.m_pClipTable[i + offset[ppLumaTable[i]]]
                        if typeIdx == SAO_EO_0 or typeIdx == SAO_EO_1 or typeIdx == SAO_EO_2 or typeIdx == SAO_EO_3:
                            for i in xrange(salLcuParam[addr].length):
                                offset[i+1] = salLcuParam[addr].offset[i] << self.m_uiSaoBitIncrease
                            for edgeType in xrange(6):
                                self.m_iOffsetEo[edgeType] = offset[self.m_auiEoTable[edgeType]]
                    self.processSaoCu(addr, typeIdx, yCbCr)
                else:
                    if idxX != (frameWidthInCU-1):
                        if yCbCr == 0:
                            pRec = self.m_pcPic.getPicYuvRec().getLumaAddr(addr)
                            stride = self.m_pcPic.getStride()
                        elif yCbCr == 1:
                            pRec = self.m_pcPic.getPicYuvRec().getCbAddr(addr)
                            stride = self.m_pcPic.getCStride()
                        else:
                            pRec = self.m_pcPic.getPicYuvRec().getCrAddr(addr)
                            stride = self.m_pcPic.getCStride()
                        widthShift = self.m_uiMaxCUWidth >> isChroma
                        for i in xrange((self.m_uiMaxCUWidth>>isChroma)+1):
                            self.m_pTmpL1[i] = pRec[widthShift-1]
                            pRec += stride
            self.m_pTmpU2, self.m_pTmpU1 = self.m_pTmpU1, self.m_pTmpU2

    def setSaoLcuBoundary(self, bVal):
        self.m_saoLcuBoundary = bVal
    def getSaoLcuBoundary(self):
        return self.m_saoLcuBoundary

    def setSaoLcuBasedOptimization(self, bVal):
        self.m_saoLcuBasedOptimization = bVal
    def getSaoLcuBasedOptimization(self):
        return self.m_saoLcuBasedOptimization

    def resetSaoUnit(self, saoUnit):
        saoUnit.partIdx = 0
        saoUnit.partIdxTmp = 0
        saoUnit.mergeLeftFlag = 0
        saoUnit.mergeUpFlag = 0
        saoUnit.typeIdx = -1
        saoUnit.length = 0
        saoUnit.subTypeIdx = 0

        for i in xrange(4):
            saoUnit.offset[i] = 0

    def copySaoUnit(self, saoUnitDst, saoUnitSrc):
        saoUnitDst.mergeLeftFlag = saoUnitSrc.mergeLeftFlag
        saoUnitDst.mergeUpFlag = saoUnitSrc.mergeUpFlag
        saoUnitDst.typeIdx = saoUnitSrc.typeIdx
        saoUnitDst.length = saoUnitSrc.length

        saoUnitDst.subTypeIdx = saoUnitSrc.subTypeIdx
        for i in xrange(4):
            saoUnitDst.offset[i] = saoUnitSrc.offset[i]
