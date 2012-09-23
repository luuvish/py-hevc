# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComDataCU.py
    HM 8.0 Python Implementation
"""

from ... import pointer

from ... import VectorNDBFBlockInfo

from ... import TComMv
from ... import TComMvField, TComCUMvField, ArrayTComCUMvField

from ... import cvar

from .TComPattern import TComPattern

from .TypeDef import (
    MRG_MAX_NUM_CANDS_SIGNALED, AMVP_DECIMATION_FACTOR,
    SIZE_2Nx2N, SIZE_2NxN, SIZE_Nx2N, SIZE_NxN,
    SIZE_2NxnU, SIZE_2NxnD, SIZE_nLx2N, SIZE_nRx2N, SIZE_NONE,
    MODE_INTER, MODE_INTRA, MODE_NONE,
    PLANAR_IDX, VER_IDX, HOR_IDX, DC_IDX, NUM_CHROMA_MODE, DM_CHROMA_IDX,
    TEXT_LUMA, TEXT_CHROMA_U, TEXT_CHROMA_V,
    REF_PIC_LIST_0, REF_PIC_LIST_1,
    MD_LEFT, MD_ABOVE, MD_ABOVE_RIGHT, MD_BELOW_LEFT, MD_ABOVE_LEFT,
    AM_NONE, SCAN_ZIGZAG
)

from .CommonDef import (
    MAX_UINT, MAX_DOUBLE, NOT_VALID,
    Clip3,
    AMVP_MAX_NUM_CANDS,
    MRG_MAX_NUM_CANDS
)

from .TComRom import (
    g_auiZscanToRaster, g_auiRasterToZscan,
    g_auiRasterToPelX, g_auiRasterToPelY, g_motionRefer,
    g_aucConvertTxtTypeToIdx, g_aucConvertToBit
)


# Non-deblocking filter processing block border tag
#enum NDBFBlockBorderTag
SGU_L          = 0
SGU_R          = 1
SGU_T          = 2
SGU_B          = 3
SGU_TL         = 4
SGU_TR         = 5
SGU_BL         = 6
SGU_BR         = 7
NUM_SGU_BORDER = 8

# Non-deblocking filter processing block information
class NDBFBlockInfo(object):

    def __init__(self):
        self.tileID    = 0
        self.sliceID   = 0
        self.startSU   = 0
        self.endSU     = 0
        self.widthSU   = 0
        self.heightSU  = 0
        self.posX      = 0
        self.posY      = 0
        self.width     = 0
        self.height    = 0
        self.isBorderAvailable = NUM_SGU_BORDER * [False]
        self.allBordersAvailable = False

    def copyFrom(self, src):
        self.tileID   = src.tileID
        self.sliceID  = src.sliceID
        self.startSU  = src.startSU
        self.endSU    = src.endSU
        self.widthSU  = src.widthSU
        self.heightSU = src.heightSU
        self.posX     = src.posX
        self.posY     = src.posY
        self.width    = src.width
        self.height   = src.height
        self.isBorderAvailable[:] = src.isBorderAvailable[:]
        self.allBordersAvailable = src.allBordersAvailable

        return self


class TComDataCU(object):

    m_pcGlbArlCoeffY = None
    m_pcGlbArlCoeffCb = None
    m_pcGlbArlCoeffCr = None

    def __init__(self):
        self.m_pcPic = None
        self.m_pcSlice = None
        self.m_pcPattern = None

        self.m_uiCUAddr = 0
        self.m_uiAbsIdxInLCU = 0
        self.m_uiCUPelX = 0
        self.m_uiCUPelY = 0
        self.m_uiNumPartition = 0
        self.m_puhWidth = None
        self.m_puhHeight = None
        self.m_puhDepth = None
        self.m_unitSize = 0

        self.m_skipFlag = None
        self.m_pePartSize = None
        self.m_pePredMode = None
        self.m_CUTransquantBypass = None
        self.m_phQP = None
        self.m_puhTrIdx = None
        self.m_puhTransformSkip = [None for i in xrange(3)]
        self.m_puhCbf = [None for i in xrange(3)]
        self.m_acCUMvField = ArrayTComCUMvField(2)
        self.m_pcTrCoeffY = None
        self.m_pcTrCoeffCb = None
        self.m_pcTrCoeffCr = None
        self.m_pcArlCoeffY = None
        self.m_pcArlCoeffCb = None
        self.m_pcArlCoeffCr = None
        self.m_ArlCoeffIsAliasedAllocation = False

        self.m_pcIPCMSampleY = None
        self.m_pcIPCMSampleCb = None
        self.m_pcIPCMSampleCr = None

        self.m_piSliceSUMap = None
        self.m_vNDFBlock = VectorNDBFBlockInfo

        self.m_pcCUAboveLeft = None
        self.m_pcCUAboveRight = None
        self.m_pcCUAbove = None
        self.m_pcCULeft = None
        self.m_apcCUColocated = [None, None]
        self.m_cMvFieldA = TComMvField()
        self.m_cMvFieldB = TComMvField()
        self.m_cMvFieldC = TComMvField()
        self.m_cMvPred = TComMv()

        self.m_pbMergeFlag = None
        self.m_puhMergeIndex = None
        self.m_bIsMergeAMP = False
        self.m_puhLumaIntraDir = None
        self.m_puhChromaIntraDir = None
        self.m_puhInterDir = None
        self.m_apiMVPIdx = [None, None]
        self.m_apiMVPNum = [None, None]
        self.m_lcuAlfEnabled = 3 * [False]
        self.m_pbIPCMFlag = None

        self.m_numSucIPCM = 0
        self.m_lastCUSucIPCMFlag = False

        self.m_bDecSubCu = False
        self.m_dTotalCost = 0.0
        self.m_uiTotalDistortion = 0
        self.m_uiTotalBits = 0
        self.m_uiTotalBins = 0
        self.m_uiSliceStartCU = None
        self.m_uiDependentSliceStartCU = None
        self.m_codedQP = 0

    def create(self, uiNumPartition, uiWidth, uiHeight, bDecSubCu, unitSize, bGlobalRMARLBuffer=False):
        self.m_bDecSubCu = bDecSubCu

        self.m_pcPic = None
        self.m_pcSlice = None
        self.m_uiNumPartition = uiNumPartition
        self.m_unitSize = unitSize

        if not bDecSubCu:
            self.m_phQP                = uiNumPartition * [0]
            self.m_puhDepth            = uiNumPartition * [0]
            self.m_puhWidth            = uiNumPartition * [0]
            self.m_puhHeight           = uiNumPartition * [0]

            self.m_skipFlag            = uiNumPartition * [False]

            self.m_pePartSize          = uiNumPartition * [SIZE_NONE]
            self.m_pePredMode          = uiNumPartition * [0]
            self.m_CUTransquantBypass  = uiNumPartition * [False]
            self.m_pbMergeFlag         = uiNumPartition * [False]
            self.m_puhMergeIndex       = uiNumPartition * [0]
            self.m_puhLumaIntraDir     = uiNumPartition * [0]
            self.m_puhChromaIntraDir   = uiNumPartition * [0]
            self.m_puhInterDir         = uiNumPartition * [0]

            self.m_puhTrIdx            = uiNumPartition * [0]
            self.m_puhTransformSkip[0] = uiNumPartition * [0]
            self.m_puhTransformSkip[1] = uiNumPartition * [0]
            self.m_puhTransformSkip[2] = uiNumPartition * [0]

            self.m_puhCbf[0]           = uiNumPartition * [0]
            self.m_puhCbf[1]           = uiNumPartition * [0]
            self.m_puhCbf[2]           = uiNumPartition * [0]

            self.m_apiMVPIdx[0]        = uiNumPartition * [255]
            self.m_apiMVPIdx[1]        = uiNumPartition * [255]
            self.m_apiMVPNum[0]        = uiNumPartition * [0]
            self.m_apiMVPNum[1]        = uiNumPartition * [0]

            self.m_pcTrCoeffY          = (uiWidth*uiHeight  ) * [0]
            self.m_pcTrCoeffCb         = (uiWidth*uiHeight/4) * [0]
            self.m_pcTrCoeffCr         = (uiWidth*uiHeight/4) * [0]

            if bGlobalRMARLBuffer:
                if TComDataCU.m_pcGlbArlCoeffY == None:
                    TComDataCU.m_pcGlbArlCoeffY  = (uiWidth*uiHeight  ) * [0]
                    TComDataCU.m_pcGlbArlCoeffCb = (uiWidth*uiHeight/4) * [0]
                    TComDataCU.m_pcGlbArlCoeffCr = (uiWidth*uiHeight/4) * [0]
                self.m_pcArlCoeffY  = TComDataCU.m_pcGlbArlCoeffY
                self.m_pcArlCoeffCb = TComDataCU.m_pcGlbArlCoeffCb
                self.m_pcArlCoeffCr = TComDataCU.m_pcGlbArlCoeffCr
                self.m_ArlCoeffIsAliasedAllocation = True
            else:
                self.m_pcArlCoeffY  = (uiWidth*uiHeight  ) * [0]
                self.m_pcArlCoeffCb = (uiWidth*uiHeight/4) * [0]
                self.m_pcArlCoeffCr = (uiWidth*uiHeight/4) * [0]

            self.m_pbIPCMFlag     = uiNumPartition * [False]
            self.m_pcIPCMSampleY  = (uiWidth*uiHeight  ) * [0]
            self.m_pcIPCMSampleCb = (uiWidth*uiHeight/4) * [0]
            self.m_pcIPCMSampleCr = (uiWidth*uiHeight/4) * [0]

            self.m_acCUMvField[0].create(uiNumPartition)
            self.m_acCUMvField[1].create(uiNumPartition)
        else:
            self.m_acCUMvField[0].setNumPartition(uiNumPartition)
            self.m_acCUMvField[1].setNumPartition(uiNumPartition)

        self.m_uiSliceStartCU          = uiNumPartition * [0]
        self.m_uiDependentSliceStartCU = uiNumPartition * [0]

        # create pattern memory
        self.m_pcPattern = TComPattern()

        # create motion vector fields
        self.m_pcCUAboveLeft  = None
        self.m_pcCUAboveRight = None
        self.m_pcCUAbove      = None
        self.m_pcCULeft       = None

        self.m_apcCUColocated[0] = None
        self.m_apcCUColocated[1] = None

    def destroy(self):
        self.m_pcPic = None
        self.m_pcSlice = None

        if self.m_pcPattern:
            del self.m_pcPattern
            self.m_pcPattern = None

        # encoder-side buffer free
        if not self.m_bDecSubCu:
            if self.m_phQP:
                del self.m_phQP
                self.m_phQP = None
            if self.m_puhDepth:
                del self.m_puhDepth
                self.m_puhDepth = None
            if self.m_puhWidth:
                del self.m_puhWidth
                self.m_puhWidth = None
            if self.m_puhHeight:
                del self.m_puhHeight
                self.m_puhHeight = None

            if self.m_pePartSize:
                del self.m_pePartSize
                self.m_pePartSize = None
            if self.m_pePredMode:
                del self.m_pePredMode
                self.m_pePredMode = None
            if self.m_CUTransquantBypass:
                del self.m_CUTransquantBypass
                self.m_CUTransquantBypass = None
            if self.m_puhCbf[0]:
                del self.m_puhCbf[0]
                self.m_puhCbf[0] = None
            if self.m_puhCbf[1]:
                del self.m_puhCbf[1]
                self.m_puhCbf[1] = None
            if self.m_puhCbf[2]:
                del self.m_puhCbf[2]
                self.m_puhCbf[2] = None
            if self.m_puhInterDir:
                del self.m_puhInterDir
                self.m_puhInterDir = None
            if self.m_pbMergeFlag:
                del self.m_pbMergeFlag
                self.m_pbMergeFlag = None
            if self.m_puhMergeIndex:
                del self.m_puhMergeIndex
                self.m_puhMergeIndex = None
            if self.m_puhLumaIntraDir:
                del self.m_puhLumaIntraDir
                self.m_puhLumaIntraDir = None
            if self.m_puhChromaIntraDir:
                del self.m_puhChromaIntraDir
                self.m_puhChromaIntraDir = None
            if self.m_puhTrIdx:
                del self.m_puhTrIdx
                self.m_puhTrIdx = None
            if self.m_puhTransformSkip[0]:
                del self.m_puhTransformSkip[0]
                self.m_puhTransformSkip[0] = None
            if self.m_puhTransformSkip[1]:
                del self.m_puhTransformSkip[1]
                self.m_puhTransformSkip[1] = None
            if self.m_puhTransformSkip[2]:
                del self.m_puhTransformSkip[2]
                self.m_puhTransformSkip[2] = None
            if self.m_pcTrCoeffY:
                del self.m_pcTrCoeffY
                self.m_pcTrCoeffY = None
            if self.m_pcTrCoeffCb:
                del self.m_pcTrCoeffCb
                self.m_pcTrCoeffCb = None
            if self.m_pcTrCoeffCr:
                del self.m_pcTrCoeffCr
                self.m_pcTrCoeffCr = None
            if not self.m_ArlCoeffIsAliasedAllocation:
                del self.m_pcArlCoeffY
                self.m_pcArlCoeffY = None
                del self.m_pcArlCoeffCb
                self.m_pcArlCoeffCb = None
                del self.m_pcArlCoeffCr
                self.m_pcArlCoeffCr = None
            if self.m_pbIPCMFlag:
                del self.m_pbIPCMFlag
                self.m_pbIPCMFlag = None
            if self.m_pcIPCMSampleY:
                del self.m_pcIPCMSampleY
                self.m_pcIPCMSampleY = None
            if self.m_pcIPCMSampleCb:
                del self.m_pcIPCMSampleCb
                self.m_pcIPCMSampleCb = None
            if self.m_pcIPCMSampleCr:
                del self.m_pcIPCMSampleCr
                self.m_pcIPCMSampleCr = None
            if self.m_apiMVPIdx[0]:
                del self.m_apiMVPIdx[0]
                self.m_apiMVPIdx[0] = None
            if self.m_apiMVPIdx[1]:
                del self.m_apiMVPIdx[1]
                self.m_apiMVPIdx[1] = None
            if self.m_apiMVPNum[0]:
                del self.m_apiMVPNum[0]
                self.m_apiMVPNum[0] = None
            if self.m_apiMVPNum[1]:
                del self.m_apiMVPNum[1]
                self.m_apiMVPNum[1] = None

            self.m_acCUMvField[0].destroy()
            self.m_acCUMvField[1].destroy()

        self.m_pcCUAboveLeft = None
        self.m_pcCUAboveRight = None
        self.m_pcCUAbove = None
        self.m_pcCULeft = None

        self.m_apcCUColocated[0] = None
        self.m_apcCUColocated[1] = None

        if self.m_uiSliceStartCU:
            del self.m_uiSliceStartCU
            self.m_uiSliceStartCU = None
        if self.m_uiDependentSliceStartCU:
            del self.m_uiDependentSliceStartCU
            self.m_uiDependentSliceStartCU = None

    def initCU(self, pcPic, uiCUAddr):
        self.m_pcPic    = pcPic
        self.m_pcSlice  = pcPic.getSlice(pcPic.getCurrSliceIdx())
        self.m_uiCUAddr = iCUAddr
        self.m_uiCUPelX = (iCUAddr % pcPic.getFrameWidthInCU()) * cvar.g_uiMaxCUWidth
        self.m_uiCUPelY = (iCUAddr / pcPic.getFrameWidthInCU()) * cvar.g_uiMaxCUHeight
        self.m_uiAbsIdxInLCU     = 0
        self.m_dTotalCost        = MAX_DOUBLE
        self.m_uiTotalDistortion = 0
        self.m_uiTotalBits       = 0
        self.m_uiTotalBins       = 0
        self.m_uiNumPartition    = pcPic.getNumPartInCU()
        self.m_numSucIPCM        = 0
        self.m_lastCUSucIPCMFlag = False

        for i in xrange(pcPic.getNumPartInCU()):
            if pcPic.getPicSym().getInverseCUOrderMap(iCUAddr) * pcPic.getNumPartInCU() + i >= \
               self.getSlice().getSliceCurStartCUAddr():
                self.m_uiSliceStartCU[i] = self.getSlice().getSliceCurStartCUAddr()
            else:
                self.m_uiSliceStartCU[i] = pcPic.getCU(self.getAddr()).m_uiSliceStartCU[i]
        for i in xrange(pcPic.getNumPartInCU()):
            if pcPic.getPicSym().getInverseCUOrderMap(iCUAddr) * pcPic.getNumPartInCU() + i >= \
               self.getSlice().getDependentSliceCurStartCUAddr():
                self.m_uiDependentSliceStartCU[i] = self.getSlice().getDependentSliceCurStartCUAddr()
            else:
                self.m_uiDependentSliceStartCU[i] = pcPic.getCU(self.getAddr()).m_uiDependentSliceStartCU[i]

        partStartIdx = self.getSlice().getDependentSliceCurStartCUAddr() - \
            pcPic.getPicSym().getInverseCUOrderMap(iCUAddr) * pcPic.getNumPartInCU()

        numElements = min(partStartIdx, self.m_uiNumPartition)
        for ui in xrange(numElements):
            pcFrom = pcPic.getCU(self.getAddr())
            self.m_skipFlag[ui]            = pcFrom.getSkipFlag(ui)
            self.m_pePartSize[ui]          = pcFrom.getPartitionSize(ui)
            self.m_pePredMode[ui]          = pcFrom.getPredictionMode(ui)
            self.m_CUTransquantBypass[ui]  = pcFrom.getCUTransquantBypass(ui)
            self.m_puhDepth[ui]            = pcFrom.getDepth(ui)
            self.m_puhWidth[ui]            = pcFrom.getWidth(ui)
            self.m_puhHeight[ui]           = pcFrom.getHeight(ui)
            self.m_puhTrIdx[ui]            = pcFrom.getTransformIdx(ui)
            self.m_puhTransformSkip[0][ui] = pcFrom.getTransformSkip(ui, TEXT_LUMA)
            self.m_puhTransformSkip[1][ui] = pcFrom.getTransformSkip(ui, TEXT_CHROMA_U)
            self.m_puhTransformSkip[2][ui] = pcFrom.getTransformSkip(ui, TEXT_CHROMA_V)
            self.m_apiMVPIdx[0][ui]        = pcFrom.m_apiMVPIdx[0][ui]
            self.m_apiMVPIdx[1][ui]        = pcFrom.m_apiMVPIdx[1][ui]
            self.m_apiMVPNum[0][ui]        = pcFrom.m_apiMVPNum[0][ui]
            self.m_apiMVPNum[1][ui]        = pcFrom.m_apiMVPNum[1][ui]
            self.m_phQP[ui]                = pcFrom.m_phQP[ui]
            self.m_lcuAlfEnabled[0]        = pcFrom.m_lcuAlfEnabled[0]
            self.m_lcuAlfEnabled[1]        = pcFrom.m_lcuAlfEnabled[1]
            self.m_lcuAlfEnabled[2]        = pcFrom.m_lcuAlfEnabled[2]
            self.m_pbMergeFlag[ui]         = pcFrom.m_pbMergeFlag[ui]
            self.m_puhMergeIndex[ui]       = pcFrom.m_puhMergeIndex[ui]
            self.m_puhLumaIntraDir[ui]     = pcFrom.m_puhLumaIntraDir[ui]
            self.m_puhChromaIntraDir[ui]   = pcFrom.m_puhChromaIntraDir[ui]
            self.m_puhInterDir[ui]         = pcFrom.m_puhInterDir[ui]
            self.m_puhCbf[0][ui]           = pcFrom.m_puhCbf[0][ui]
            self.m_puhCbf[1][ui]           = pcFrom.m_puhCbf[1][ui]
            self.m_puhCbf[2][ui]           = pcFrom.m_puhCbf[2][ui]
            self.m_pbIPCMFlag[ui]          = pcFrom.m_pbIPCMFlag[ui]

        firstElement = max(partStartIdx, 0)
        numElements = self.m_uiNumPartition - firstElement

        if numElements > 0:
            for ui in xrange(firstElement, firstElement+numElements):
                self.m_skipFlag[ui]            = False

                self.m_pePartSize[ui]          = SIZE_NONE
                self.m_pePredMode[ui]          = MODE_NONE
                self.m_CUTransquantBypass[ui]  = False
                self.m_puhDepth[ui]            = 0
                self.m_puhTrIdx[ui]            = 0
                self.m_puhTransformSkip[0][ui] = 0
                self.m_puhTransformSkip[1][ui] = 0
                self.m_puhTransformSkip[2][ui] = 0
                self.m_puhWidth[ui]            = cvar.g_uiMaxCUWidth
                self.m_puhHeight[ui]           = cvar.g_uiMaxCUHeight
                self.m_apiMVPIdx[0][ui]        = 255
                self.m_apiMVPIdx[1][ui]        = 255
                self.m_apiMVPNum[0][ui]        = 255
                self.m_apiMVPNum[1][ui]        = 255
                self.m_phQP[ui]                = self.getSlice().getSliceQp()
                self.m_lcuAlfEnabled[0]        = False
                self.m_lcuAlfEnabled[1]        = False
                self.m_lcuAlfEnabled[2]        = False
                self.m_pbMergeFlag[ui]         = False
                self.m_puhMergeIndex[ui]       = 0
                self.m_puhLumaIntraDir[ui]     = DC_IDX
                self.m_puhChromaIntraDir[ui]   = 0
                self.m_puhInterDir[ui]         = 0
                self.m_puhCbf[0][ui]           = 0
                self.m_puhCbf[1][ui]           = 0
                self.m_puhCbf[2][ui]           = 0
                self.m_pbIPCMFlag[ui]          = False

        uiTmp = cvar.g_uiMaxCUWidth * cvar.g_uiMaxCUHeight
        if 0 >= partStartIdx:
            self.m_acCUMvField[0].clearMvField()
            self.m_acCUMvField[1].clearMvField()
            for ui in xrange(uiTmp):
                self.m_pcTrCoeffY[ui]    = 0
                self.m_pcArlCoeffY[ui]   = 0
                self.m_pcIPCMSampleY[ui] = 0
            uiTmp >>= 2
            for ui in xrange(uiTmp):
                self.m_pcTrCoeffCb[ui]    = 0
                self.m_pcTrCoeffCr[ui]    = 0
                self.m_pcArlCoeffCb[ui]   = 0
                self.m_pcArlCoeffCr[ui]   = 0
                self.m_pcIPCMSampleCb[ui] = 0
                self.m_pcIPCMSampleCr[ui] = 0
        else:
            pcFrom = pcPic.getCU(self.getAddr())
            self.m_acCUMvField[0].copyFrom(pcFrom.m_acCUMvField[0], self.m_uiNumPartition, 0)
            self.m_acCUMvField[1].copyFrom(pcFrom.m_acCUMvField[1], self.m_uiNumPartition, 0)
            for i in xrange(uiTmp):
                self.m_pcTrCoeffY[i]    = pcFrom.m_pcTrCoeffY[i]
                self.m_pcArlCoeffY[i]   = pcFrom.m_pcArlCoeffY[i]
                self.m_pcIPCMSampleY[i] = pcFrom.m_pcIPCMSampleY[i]
            for i in xrange(uiTmp>>2):
                self.m_pcTrCoeffCb[i]    = pcFrom.m_pcTrCoeffCb[i]
                self.m_pcTrCoeffCr[i]    = pcFrom.m_pcTrCoeffCr[i]
                self.m_pcArlCoeffCb[i]   = pcFrom.m_pcArlCoeffCb[i]
                self.m_pcArlCoeffCr[i]   = pcFrom.m_pcArlCoeffCr[i]
                self.m_pcIPCMSampleCb[i] = pcFrom.m_pcIPCMSampleCb[i]
                self.m_pcIPCMSampleCr[i] = pcFrom.m_pcIPCMSampleCr[i]

        # Setting neighbor CU
        self.m_pcCULeft = None
        self.m_pcCUAbove = None
        self.m_pcCUAboveLeft = None
        self.m_pcCUAboveRight = None

        self.m_apcCUColocated[0] = None
        self.m_apcCUColocated[1] = None

        uiWidthInCU = pcPic.getFrameWidthInCU()
        if self.m_uiCUAddr % uiWidthInCU:
            self.m_pcCULeft = pcPic.getCU(self.m_uiCUAddr - 1)

        if self.m_uiCUAddr / uiWidthInCU:
            self.m_pcCUAbove = pcPic.getCU(self.m_uiCUAddr - uiWidthInCU)

        if self.m_pcCULeft and self.m_pcCUAbove:
            self.m_pcCUAboveLeft = pcPic.getCU(self.m_uiCUAddr - uiWidthInCU - 1)

        if self.m_pcCUAbove and (self.m_uiCUAddr % uiWidthInCU) < (uiWidthInCU-1):
            self.m_pcCUAboveRight = pcPic.getCU(self.m_uiCUAddr - uiWidthInCU + 1)

        if self.getSlice().getNumRefIdx(REF_PIC_LIST_0) > 0:
            self.m_apcCUColocated[0] = self.getSlice().getRefPic(REF_PIC_LIST_0, 0).getCU(self.m_uiCUAddr)

        if self.getSlice().getNumRefIdx(REF_PIC_LIST_1) > 0:
            self.m_apcCUColocated[1] = self.getSlice().getRefPic(REF_PIC_LIST_1, 1).getCU(self.m_uiCUAddr)

    def initEstData(self, uiDepth, qp):
        self.m_dTotalCost        = MAX_DOUBLE
        self.m_uiTotalDistortion = 0
        self.m_uiTotalBits       = 0
        self.m_uiTotalBins       = 0

        uhWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uhHeight = cvar.g_uiMaxCUHeight >> uiDepth
        self.m_lcuAlfEnabled[0] = False
        self.m_lcuAlfEnabled[1] = False
        self.m_lcuAlfEnabled[2] = False

        for ui in xrange(self.m_uiNumPartition):
            if self.getPic().getPicSym().getInverseCUOrderMap(self.getAddr()) * \
               self.m_pcPic.getNumPartInCU() + self.m_uiAbsIdxInLCU + ui >= \
               self.getSlice().getDependentSliceCurStartCUAddr():
                self.m_apiMVPIdx[0][ui]        = 255
                self.m_apiMVPIdx[1][ui]        = 255
                self.m_apiMVPNum[0][ui]        = 255
                self.m_apiMVPNum[1][ui]        = 255
                self.m_puhDepth[ui]            = uiDepth
                self.m_puhWidth[ui]            = uiWidth
                self.m_puhHeight[ui]           = uiHeight
                self.m_puhTrIdx[ui]            = 0
                self.m_puhTransformSkip[0][ui] = 0
                self.m_puhTransformSkip[1][ui] = 0
                self.m_puhTransformSkip[2][ui] = 0
                self.m_skipFlag[ui]            = False
                self.m_pePartSize[ui]          = SIZE_NONE
                self.m_pePredMode[ui]          = MODE_NONE
                self.m_CUTransquantBypass[ui]  = False
                self.m_pbIPCMFlag[ui]          = 0
                self.m_phQP[ui]                = qp
                self.m_pbMergeFlag[ui]         = 0
                self.m_puhMergeIndex[ui]       = 0
                self.m_puhLumaIntraDir[ui]     = DC_IDX
                self.m_puhChromaIntraDir[ui]   = 0
                self.m_puhInterDir[ui]         = 0
                self.m_puhCbf[0][ui]           = 0
                self.m_puhCbf[1][ui]           = 0
                self.m_puhCbf[2][ui]           = 0

        uiTmp = uhWidth * uhHeight

        if self.getPic().getPicSym().getInverseCUOrderMap(self.getAddr()) * \
           self.m_pcPic.getNumPartInCU() + self.m_uiAbsIdxInLCU >= \
           self.getSlice().getDependentSliceCurStartCUAddr():
            self.m_acCUMvField[0].clearMvField()
            self.m_acCUMvField[1].clearMvField()
            uiTmp = uhWidth * uhHeight

            for ui in xrange(uiTmp):
                self.m_pcTrCoeffY[ui]    = 0
                self.m_pcArlCoeffY[ui]   = 0
                self.m_pcIPCMSampleY[ui] = 0

            uiTmp >>= 2
            for ui in xrange(uiTmp):
                self.m_pcTrCoeffCb[ui]    = 0
                self.m_pcTrCoeffCr[ui]    = 0
                self.m_pcArlCoeffCb[ui]   = 0
                self.m_pcArlCoeffCr[ui]   = 0
                self.m_pcIPCMSampleCb[ui] = 0
                self.m_pcIPCMSampleCr[ui] = 0

    def initSubCU(self, pcCU, uiPartUnitIdx, uiDepth, qp):
        assert(uiPartUnitIdx < 4)

        uiPartOffset = (pcCU.getTotalNumPart() >> 2) * uiPartUnitIdx

        self.m_pcPic         = pcCU.getPic()
        self.m_pcSlice       = self.m_pcPic.getSlice(self.m_pcPic.getCurrSliceIdx())
        self.m_uiCUAddr      = pcCU.getAddr()
        self.m_uiAbsIdxInLCU = pcCU.getZorderIdxInCU() + uiPartOffset

        self.m_uiCUPelY      = pcCU.getCUPelX() + (cvar.g_uiMaxCUWidth>>uiDepth) * (uiPartUnitIdx&1)
        self.m_uiCUPelY      = pcCU.getCUPelY() + (cvar.g_uiMaxCUHeight>>uiDepth) * (uiPartUnitIdx>>1)

        self.m_dTotalCost        = MAX_DOUBLE
        self.m_uiTotalDistortion = 0
        self.m_uiTotalBits       = 0
        self.m_uiTotalBins       = 0
        self.m_uiNumPartition    = pcCU.getTotalNumPart() >> 2

        self.m_numSucIPCM        = 0
        self.m_lastCUSucIPCMFlag = False

        self.m_lcuAlfEnabled[0]  = pcCU.m_lcuAlfEnabled[0]
        self.m_lcuAlfEnabled[1]  = pcCU.m_lcuAlfEnabled[1]
        self.m_lcuAlfEnabled[2]  = pcCU.m_lcuAlfEnabled[2]

        uhWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uhHeight = cvar.g_uiMaxCUHeight >> uiDepth

        for ui in xrange(self.m_uiNumPartition):
            self.m_pbMergeFlag[ui]         = 0
            self.m_puhMergeIndex[ui]       = 0
            self.m_puhLumaIntraDir[ui]     = DC_IDX
            self.m_puhChromaIntraDir[ui]   = 0
            self.m_puhInterDir[ui]         = 0
            self.m_puhTrIdx[ui]            = 0
            self.m_puhTransformSkip[0][ui] = 0
            self.m_puhTransformSkip[1][ui] = 0
            self.m_puhTransformSkip[2][ui] = 0
            self.m_puhCbf[0][ui]           = 0
            self.m_puhCbf[1][ui]           = 0
            self.m_puhCbf[2][ui]           = 0
            self.m_puhDepth[ui]            = uiDepth

            self.m_puhWidth[ui]            = uhWidth
            self.m_puhHeight[ui]           = uhHeight
            self.m_pbIPCMFlag[ui]          = 0

        for ui in xrange(self.m_uiNumPartition):
            self.m_skipFlag[ui]           = False
            self.m_pePartSize[ui]         = SIZE_NONE
            self.m_pePredMode[ui]         = MODE_NONE
            self.m_CUTransquantBypass[ui] = False
            self.m_apiMVPIdx[0][ui]       = 255
            self.m_apiMVPIdx[1][ui]       = 255
            self.m_apiMVPNum[0][ui]       = 255
            self.m_apiMVPNum[1][ui]       = 255
            if self.m_pcPic.getPicSym().getInverseCUOrderMap(self.getAddr()) * \
               self.m_pcPic.getNumPartInCU() + self.m_uiAbsIdxInLCU + ui < \
               self.getSlice().getDependentSliceCurStartCUAddr():
                self.m_apiMVPIdx[0][ui]        = pcCU.m_apiMVPIdx[0][uiPartOffset+ui]
                self.m_apiMVPIdx[1][ui]        = pcCU.m_apiMVPIdx[1][uiPartOffset+ui]
                self.m_apiMVPNum[0][ui]        = pcCU.m_apiMVPNum[0][uiPartOffset+ui]
                self.m_apiMVPNum[1][ui]        = pcCU.m_apiMVPNum[1][uiPartOffset+ui]
                self.m_puhDepth[ui]            = pcCU.getDepth(uiPartOffset+ui)
                self.m_puhWidth[ui]            = pcCU.getWidth(uiPartOffset+ui)
                self.m_puhHeight[ui]           = pcCU.getHeight(uiPartOffset+ui)
                self.m_puhTrIdx[ui]            = pcCU.getTransformIdx(uiPartOffset+ui)
                self.m_puhTransformSkip[0][ui] = pcCU.getTransformSkip(uiPartOffset+ui, TEXT_LUMA)
                self.m_puhTransformSkip[1][ui] = pcCU.getTransformSkip(uiPartOffset+ui, TEXT_CHROMA_U)
                self.m_puhTransformSkip[2][ui] = pcCU.getTransformSkip(uiPartOffset+ui, TEXT_CHROMA_V)
                self.m_skipFlag[ui]            = pcCU.getSkipFlag(uiPartOffset+ui)
                self.m_pePartSize[ui]          = pcCU.getPartitionSize(uiPartOffset+ui)
                self.m_pePredMode[ui]          = pcCU.getPredictionMode(uiPartOffset+ui)
                self.m_CUTransquantBypass[ui]  = pcCU.getCUTransquantBypass(uiPartOffset+ui)
                self.m_pbIPCMFlag[ui]          = pcCU.m_pbIPCMFlag[uiPartOffset+ui]
                self.m_phQP[ui]                = pcCU.m_phQP[uiPartOffset+ui]
                self.m_pbMergeFlag[ui]         = pcCU.m_pbMergeFlag[uiPartOffset+ui]
                self.m_puhMergeIndex[ui]       = pcCU.m_puhMergeIndex[uiPartOffset+ui]
                self.m_puhLumaIntraDir[ui]     = pcCU.m_puhLumaIntraDir[uiPartOffset+ui]
                self.m_puhChromaIntraDir[ui]   = pcCU.m_puhChromaIntraDir[uiPartOffset+ui]
                self.m_puhInterDir[ui]         = pcCU.m_puhInterDir[uiPartOffset+ui]
                self.m_puhCbf[0][ui]           = pcCU.m_puhCbf[0][uiPartOffset+ui]
                self.m_puhCbf[1][ui]           = pcCU.m_puhCbf[1][uiPartOffset+ui]
                self.m_puhCbf[2][ui]           = pcCU.m_puhCbf[2][uiPartOffset+ui]
        uiTmp = uhWidth * uhHeight
        for ui in xrange(uiTmp):
            self.m_pcTrCoeffY[ui]    = 0
            self.m_pcArlCoeffY[ui]   = 0
            self.m_pcIPCMSampleY[ui] = 0
        uiTmp >>= 2
        for ui in xrange(uiTmp):
            self.m_pcTrCoeffCb[ui]    = 0
            self.m_pcTrCoeffCr[ui]    = 0
            self.m_pcArlCoeffCb[ui]   = 0
            self.m_pcArlCoeffCr[ui]   = 0
            self.m_pcIPCMSampleCb[ui] = 0
            self.m_pcIPCMSampleCr[ui] = 0
        self.m_acCUMvField[0].clearMvField()
        self.m_acCUMvField[1].clearMvField()

        if self.m_pcPic.getPicSym().getInverseCUOrderMap(self.getAddr()) * \
           self.m_pcPic.getNumPartInCU() + self.m_uiAbsIdxInLCU < \
           self.getSlice().getDependentSliceCurStartCUAddr():
            # Part of this CU contains data from an older slice. Now copy in that data.
            uiMaxCuWidth = pcCU.getSlice().getSPS().getMaxCUWdith()
            uiMaxCuHeight = pcCU.getSlice().getSPS().getMaxCUHeight()
            bigCU = self.getPic().getCU(self.getAddr())
            minui = uiPartOffset
            minui = -minui
            pcCU.m_acCUMvField[0].copyTo(self.m_acCUMvField[0], minui, uiPartOffset, self.m_uiNumPartition)
            pcCU.m_acCUMvField[1].copyTo(self.m_acCUMvField[1], minui, uiPartOffset, self.m_uiNumPartition)
            uiCoffOffset = uiMaxCuWidth * uiMaxCuHeight * self.m_uiAbsIdxInLCU / \
                           pcCU.getPic().getNumPartInCU()
            uiTmp = uhWidth * uhHeight
            for i in xrange(uiTmp):
                self.m_pcTrCoeffY[i]    = bigCU.m_pcTrCoeffY[uiCoffOffset+i]
                self.m_pcArlCoeffY[i]   = bigCU.m_pcArlCoeffY[uiCoffOffset+i]
                self.m_pcIPCMSampleY[i] = bigCU.m_pcIPCMSampleY[uiCoffOffset+i]
            uiTmp >>= 2
            uiCoffOffset >>= 2
            for i in xrange(uiTmp):
                self.m_pcTrCoeffCb[i]    = bigCU.m_pcTrCoeffCb[uiCoffOffset+i]
                self.m_pcTrCoeffCr[i]    = bigCU.m_pcTrCoeffCr[uiCoffOffset+i]
                self.m_pcArlCoeffCb[i]   = bigCU.m_pcArlCoeffCb[uiCoffOffset+i]
                self.m_pcArlCoeffCr[i]   = bigCU.m_pcArlCoeffCr[uiCoffOffset+i]
                self.m_pcIPCMSampleCb[i] = bigCU.m_pcIPCMSampleCb[uiCoffOffset+i]
                self.m_pcIPCMSampleCr[i] = bigCU.m_pcIPCMSampleCr[uiCoffOffset+i]

        self.m_pcCULeft       = pcCU.getCULeft()
        self.m_pcCUAbove      = pcCU.getCUAbove()
        self.m_pcCUAboveLeft  = pcCU.getCUAboveLeft()
        self.m_pcCUAboveRight = pcCU.getCUAboveRight()

        self.m_apcCUColocated[0] = pcCU.getCUColocated(REF_PIC_LIST_0)
        self.m_apcCUColocated[1] = pcCU.getCUColocated(REF_PIC_LIST_1)
        for ui in xrange(self.m_uiNumPartition):
            self.m_uiSliceStartCU[ui]          = pcCU.m_uiSliceStartCU[uiPartOffset+ui]
            self.m_uiDependentSliceStartCU[ui] = pcCU.m_uiDependentSliceStartCU[uiPartOffset+ui]

    def setOutsideCUPart(self, uiAbsPartIdx, uiDepth):
        uiNumPartition = self.m_uiNumPartition >> (uiDepth << 1)
        uhWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uhHeight = cvar.g_uiMaxCUHeight >> uiDepth

        for ui in xrange(uiNumPartition):
            self.m_puhDepth[uiAbsPartIdx+ui]  = uiDepth
            self.m_puhWidth[uiAbsPartIdx+ui]  = uhWidth
            self.m_puhHeight[uiAbsPartIdx+ui] = uhHeight

    def copySubCU(self, pcCU, uiAbsPartIdx, uiDepth):
        uiPart = uiAbsPartIdx

        self.m_pcPic         = pcCU.getPic()
        self.m_pcSlice       = pcCU.getSlice()
        self.m_uiCUAddr      = pcCU.getAddr()
        self.m_uiAbsIdxInLCU = uiAbsPartIdx

        self.m_uiCUPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]]
        self.m_uiCUPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]]

        uiWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uiHeight = cvar.g_uiMaxCUHeight >> uiDepth

        self.m_skipFlag            = pointer(pcCU.getSkipFlag(), type='bool *') + uiPart

        self.m_phQP                = pointer(pcCU.getQP(), type='uchar *')                + uiPart
        self.m_pePartSize          = pointer(pcCU.getPartitionSize(), type='uchar *')     + uiPart
        self.m_pePredMode          = pointer(pcCU.getPredictionMode(), type='uchar *')    + uiPart
        self.m_CUTransquantBypass  = pointer(pcCU.getCUTransquantBypass(), type='bool *') + uiPart

        self.m_pbMergeFlag         = pointer(pcCU.getMergeFlag(), type='bool *')   + uiPart
        self.m_puhMergeIndex       = pointer(pcCU.getMergeIndex(), type='uchar *') + uiPart

        self.m_puhLumaIntraDir     = pointer(pcCU.getLumaIntraDir(), type='uchar *')   + uiPart
        self.m_puhChromaIntraDir   = pointer(pcCU.getChromaIntraDir(), type='uchar *') + uiPart
        self.m_puhInterDir         = pointer(pcCU.getInterDir(), type='uchar *')       + uiPart
        self.m_puhTrIdx            = pointer(pcCU.getTransformIdx(), type='uchar *')   + uiPart
        self.m_puhTransformSkip[0] = pointer(pcCU.getTransformSkip(TEXT_LUMA), type='uchar *')     + uiPart
        self.m_puhTransformSkip[1] = pointer(pcCU.getTransformSkip(TEXT_CHROMA_U), type='uchar *') + uiPart
        self.m_puhTransformSkip[2] = pointer(pcCU.getTransformSkip(TEXT_CHROMA_V), type='uchar *') + uiPart

        self.m_puhCbf[0]           = pointer(pcCU.getCbf(TEXT_LUMA), type='uchar *')     + uiPart
        self.m_puhCbf[1]           = pointer(pcCU.getCbf(TEXT_CHROMA_U), type='uchar *') + uiPart
        self.m_puhCbf[2]           = pointer(pcCU.getCbf(TEXT_CHROMA_V), type='uchar *') + uiPart

        self.m_puhDepth            = pointer(pcCU.getDepth(), type='uchar *')  + uiPart
        self.m_puhWidth            = pointer(pcCU.getWidth(), type='uchar *')  + uiPart
        self.m_puhHeight           = pointer(pcCU.getHeight(), type='uchar *') + uiPart

        self.m_apiMVPIdx[0]        = pointer(pcCU.getMVPIdx(REF_PIC_LIST_0), type='uchar *') + uiPart
        self.m_apiMVPIdx[1]        = pointer(pcCU.getMVPIdx(REF_PIC_LIST_1), type='uchar *') + uiPart
        self.m_apiMVPNum[0]        = pointer(pcCU.getMVPNum(REF_PIC_LIST_0), type='uchar *') + uiPart
        self.m_apiMVPNum[1]        = pointer(pcCU.getMVPNum(REF_PIC_LIST_1), type='uchar *') + uiPart

        self.m_pbIPCMFlag          = pointer(pcCU.getIPCMFlag(), type='bool *') + uiPart

        self.m_pcCUAboveLeft       = pcCU.getCUAboveLeft()
        self.m_pcCUAboveRight      = pcCU.getCUAboveRight()
        self.m_pcCUAbove           = pcCU.getCUAbove()
        self.m_pcCULeft            = pcCU.getCULeft()

        self.m_apcCUColocated[0]   = pcCU.getCUColocated(REF_PIC_LIST_0)
        self.m_apcCUColocated[1]   = pcCU.getCUColocated(REF_PIC_LIST_1)

        uiTmp = uiWidth * uiHeight
        uiMaxCuWidth = pcCU.getSlice().getSPS().getMaxCUWidth()
        uiMaxCuHeight = pcCU.getSlice().getSPS().getMaxCUHeight()

        uiCoffOffset = uiMaxCuWidth * uiMaxCuHeight * uiAbsPartIdx / \
                       pcCU.getPic().getNumPartInCU()

        self.m_pcTrCoeffY    = pointer(pcCU.getCoeffY(), type='int *')       + uiCoffOffset
        self.m_pcArlCoeffY   = pointer(pcCU.getArlCoeffY(), type='int *')    + uiCoffOffset
        self.m_pcIPCMSampleY = pointer(pcCU.getPCMSampleY(), type='short *') + uiCoffOffset

        uiTmp >>= 2
        uiCoffOffset >>= 2
        self.m_pcTrCoeffCb    = pointer(pcCU.getCoeffCb(), type='int *')       + uiCoffOffset
        self.m_pcTrCoeffCr    = pointer(pcCU.getCoeffCr(), type='int *')       + uiCoffOffset
        self.m_pcArlCoeffCb   = pointer(pcCU.getArlCoeffCb(), type='int *')    + uiCoffOffset
        self.m_pcArlCoeffCr   = pointer(pcCU.getArlCoeffCr(), type='int *')    + uiCoffOffset
        self.m_pcIPCMSampleCb = pointer(pcCU.getPCMSampleCb(), type='short *') + uiCoffOffset
        self.m_pcIPCMSampleCr = pointer(pcCU.getPCMSampleCr(), type='short *') + uiCoffOffset

        self.m_acCUMvField[0].linkToWithOffset(pcCU.getCUMvField(REF_PIC_LIST_0), uiPart)
        self.m_acCUMvField[1].linkToWithOffset(pcCU.getCUMvField(REF_PIC_LIST_1), uiPart)
        for ui in xrange(self.m_uiNumPartition):
            self.m_uiSliceStartCU[ui]          = pcCU.getSliceStartCU(uiPart+ui)
            self.m_uiDependentSliceStartCU[ui] = pcCU.getDependentSliceStartCU(uiPart+ui)

    def copyInterPredInfoFrom(self, pcCU, uiAbsPartIdx, eRefPicList):
        self.m_pcPic              = pcCU.getPic()
        self.m_pcSlice            = pcCU.getSlice()
        self.m_uiCUAddr           = pcCU.getAddr()
        self.m_uiAbsIdxInLCU      = uiAbsPartIdx

        iRastPartIdx              = g_auiZscanToRaster[uiAbsPartIdx]
        self.m_uiCUPelX           = pcCU.getCUPelX() + self.m_pcPic.getMinCUWidth()  * (iRastPartIdx % self.m_pcPic.getNumPartInWidth())
        self.m_uiCUPelY           = pcCU.getCUPelY() + self.m_pcPic.getMinCUHeight() * (iRastPartIdx / self.m_pcPic.getNumPartInWidth())

        self.m_pcCUAboveLeft      = pcCU.getCUAboveLeft()
        self.m_pcCUAboveRight     = pcCU.getCUAboveRight()
        self.m_pcCUAbove          = pcCU.getCUAbove()
        self.m_pcCULeft           = pcCU.getCULeft()

        self.m_apcCUColocated[0]  = pcCU.getCUColocated(REF_PIC_LIST_0)
        self.m_apcCUColocated[1]  = pcCU.getCUColocated(REF_PIC_LIST_1)

        self.m_skipFlag           = pointer(pcCU.getSkipFlag(), type='bool *')           + uiAbsPartIdx

        self.m_pePartSize         = pointer(pcCU.getPartitionSize(), type='uchar *')     + uiAbsPartIdx
        self.m_pePredMode         = pointer(pcCU.getPredictionMode(), type='uchar *')    + uiAbsPartIdx
        self.m_CUTransquantBypass = pointer(pcCU.getCUTransquantBypass(), type='bool *') + uiAbsPartIdx
        self.m_puhInterDir        = pointer(pcCU.getInterDir(), type='uchar *')          + uiAbsPartIdx

        self.m_puhDepth           = pointer(pcCU.getDepth(), type='uchar *')             + uiAbsPartIdx
        self.m_puhWidth           = pointer(pcCU.getWidth(), type='uchar *')             + uiAbsPartIdx
        self.m_puhHeight          = pointer(pcCU.getHeight(), type='uchar *')            + uiAbsPartIdx

        self.m_pbMergeFlag        = pointer(pcCU.getMergeFlag(), type='bool *')          + uiAbsPartIdx
        self.m_puhMergeIndex      = pointer(pcCU.getMergeIndex(), type='uchar *')        + uiAbsPartIdx

        self.m_apiMVPIdx[eRefPicList] = pointer(pcCU.getMVPIdx(eRefPicList), type='uchar *') + uiAbsPartIdx
        self.m_apiMVPNum[eRefPicList] = pointer(pcCU.getMVPNum(eRefPicList), type='uchar *') + uiAbsPartIdx

        self.m_acCUMvField[eRefPicList].linkToWithOffset(pcCU.getCUMvField(eRefPicList), uiAbsPartIdx)

        for ui in xrange(self.m_uiNumPartition):
            self.m_uiSliceStartCU[ui]          = pcCU.getSliceStartCU(uiAbsPartIdx+ui)
            self.m_uiDependentSliceStartCU[ui] = pcCU.getDependentSliceStartCU(uiAbsPartIdx+ui)

    def copyPartFrom(self, pcCU, uiPartUnitIdx, uiDepth):
        assert(uiPartUnitIdx < 4)

        self.m_dTotalCost        += pcCU.getTotalCost()
        self.m_uiTotalDistortion += pcCU.getTotalDistortion()
        self.m_uiTotalBits       += pcCU.getTotalBits()

        uiOffset = pcCU.getTotalNumPart() * uiPartUnitIdx

        uiNumPartition = pcCU.getTotalNumPart()

        for ui in xrange(uiNumPartition):
            self.m_skipFlag           [uiOffset+ui] = pcCU.getSkipFlag(ui)
            self.m_phQP               [uiOffset+ui] = pcCU.getQP(ui)
            self.m_pePartSize         [uiOffset+ui] = pcCU.getPartitionSize(ui)
            self.m_pePredMode         [uiOffset+ui] = pcCU.getPredictionMode(ui)
            self.m_CUTransquantBypass [uiOffset+ui] = pcCU.getCUTransquantBypass(ui)
            self.m_lcuAlfEnabled[0] = pcCU.m_lcuAlfEnabled[0]
            self.m_lcuAlfEnabled[1] = pcCU.m_lcuAlfEnabled[1]
            self.m_lcuAlfEnabled[2] = pcCU.m_lcuAlfEnabled[2]
            self.m_pbMergeFlag        [uiOffset+ui] = pcCU.getMergeFlag(ui)
            self.m_puhMergeIndex      [uiOffset+ui] = pcCU.getMergeIndex(ui)
            self.m_puhLumaIntraDir    [uiOffset+ui] = pcCU.getLumaIntraDir(ui)
            self.m_puhChromaIntraDir  [uiOffset+ui] = pcCU.getChromaIntraDir(ui)
            self.m_puhInterDir        [uiOffset+ui] = pcCU.getInterDir(ui)
            self.m_puhTrIdx           [uiOffset+ui] = pcCU.getTransformIdx(ui)
            self.m_puhTransformSkip[0][uiOffset+ui] = pcCU.getTransformSkip(TEXT_LUMA    , ui)
            self.m_puhTransformSkip[1][uiOffset+ui] = pcCU.getTransformSkip(TEXT_CHROMA_U, ui)
            self.m_puhTransformSkip[2][uiOffset+ui] = pcCU.getTransformSkip(TEXT_CHROMA_V, ui)

            self.m_puhCbf[0]          [uiOffset+ui] = pcCU.getCbf(TEXT_LUMA    , ui)
            self.m_puhCbf[1]          [uiOffset+ui] = pcCU.getCbf(TEXT_CHROMA_U, ui)
            self.m_puhCbf[2]          [uiOffset+ui] = pcCU.getCbf(TEXT_CHROMA_V, ui)

            self.m_puhDepth           [uiOffset+ui] = pcCU.getDepth(ui)
            self.m_puhWidth           [uiOffset+ui] = pcCU.getWidth(ui)
            self.m_puhHeight          [uiOffset+ui] = pcCU.getHeight(ui)

            self.m_apiMVPIdx[0]       [uiOffset+ui] = pcCU.getMVPIdx(REF_PIC_LIST_0, ui)
            self.m_apiMVPIdx[1]       [uiOffset+ui] = pcCU.getMVPIdx(REF_PIC_LIST_1, ui)
            self.m_apiMVPNum[0]       [uiOffset+ui] = pcCU.getMVPNum(REF_PIC_LIST_0, ui)
            self.m_apiMVPNum[1]       [uiOffset+ui] = pcCU.getMVPNum(REF_PIC_LIST_1, ui)

            self.m_pbIPCMFlag         [uiOffset+ui] = pcCU.getIPCMFlag(ui)

        self.m_pcCUAboveLeft  = pcCU.getCUAboveLeft()
        self.m_pcCUAboveRight = pcCU.getCUAboveRight()
        self.m_pcCUAbove      = pcCU.getCUAbove()
        self.m_pcCULeft       = pcCU.getCULeft()

        self.m_apcCUColocated[0] = pcCU.getCUColocated(REF_PIC_LIST_0)
        self.m_apcCUColocated[1] = pcCU.getCUColocated(REF_PIC_LIST_1)

        self.m_acCUMvField[0].copyFrom(pcCU.getCUMvField(REF_PIC_LIST_0), pcCU.getTotalNumPart(), uiOffset)
        self.m_acCUMvField[1].copyFrom(pcCU.getCUMvField(REF_PIC_LIST_1), pcCU.getTotalNumPart(), uiOffset)

        uiTmp = cvar.g_uiMaxCUWidth * cvar.g_uiMaxCUHeight >> (uiDepth<<1)
        uiTmp2 = uiPartUnitIdx * uiTmp
        for ui in xrange(uiTmp):
            self.m_pcTrCoeffY   [uiTmp2+ui] = pcCU.getCoeffY() + ui
            self.m_pcArlCoeffY  [uiTmp2+ui] = pcCU.getArlCoeffY() + ui
            self.m_pcIPCMSampleY[uiTmp2+ui] = pcCU.getPCMSampleY() + ui

        uiTmp >>= 2
        uiTmp2 >>= 2
        for ui in xrange(uiTmp):
            self.m_pcTrCoeffCb   [uiTmp2+ui] = pcCU.getCoeffCb()[ui]
            self.m_pcTrCoeffCr   [uiTmp2+ui] = pcCU.getCoeffCr()[ui]
            self.m_pcArlCoeffCb  [uiTmp2+ui] = pcCU.getArlCoeffCb()[ui]
            self.m_pcArlCoeffCr  [uiTmp2+ui] = pcCU.getArlCoeffCr()[ui]
            self.m_pcIPCMSampleCb[uiTmp2+ui] = pcCU.getPCMSampleCb()[ui]
            self.m_pcIPCMSampleCr[uiTmp2+ui] = pcCU.getPCMSampleCr()[ui]
        self.m_uiTotalBins += pcCU.getTotalBins()

        for ui in xrange(uiNumPartition):
            self.m_uiSliceStartCU         [uiOffset+ui] = pcCU.m_uiSliceStartCU[ui]
            self.m_uiDependentSliceStartCU[uiOffset+ui] = pcCU.m_uiDependentSliceStartCU[ui]

    def copyToPic(self, uiDepth, uiPartIdx=None, uiPartDepth=None):
        if uiPartIdx == None and uiPartDepth == None:
            rpcCU = self.m_pcPic.getCU(self.m_uiCUAddr)

            rpcCU.m_dTotalCost        = self.m_dTotalCost
            rpcCU.m_uiTotalDistortion = self.m_uiTotalDistortion
            rpcCU.m_uiTotalBits       = self.m_uiTotalBits

            for ui in xrange(self.m_uiNumPartition):
                rpcCU.getSkipFlag()          [self.m_uiAbsIdxInLCU+ui] = self.m_skipFlag[ui]

                rpcCU.getQP()                [self.m_uiAbsIdxInLCU+ui] = self.m_phQP[ui]

                rpcCU.getPartitionSize()     [self.m_uiAbsIdxInLCU+ui] = self.m_pePartSize[ui]
                rpcCU.getPredictionMode()    [self.m_uiAbsIdxInLCU+ui] = self.m_pePredMode[ui]
                rpcCU.getCUTransquantBypass()[self.m_uiAbsIdxInLCU+ui] = self.m_CUTransquantBypass[ui]
                rpcCU.m_lcuAlfEnabled[0] = self.m_lcuAlfEnabled[0]
                rpcCU.m_lcuAlfEnabled[1] = self.m_lcuAlfEnabled[1]
                rpcCU.m_lcuAlfEnabled[2] = self.m_lcuAlfEnabled[2]
                rpcCU.getMergeFlag()         [self.m_uiAbsIdxInLCU+ui] = self.m_pbMergeFlag[ui]
                rpcCU.getMergeIndex()        [self.m_uiAbsIdxInLCU+ui] = self.m_puhMergeIndex[ui]
                rpcCU.getLumaIntraDir()      [self.m_uiAbsIdxInLCU+ui] = self.m_puhLumaIntraDir[ui]
                rpcCU.getChromaIntraDir()    [self.m_uiAbsIdxInLCU+ui] = self.m_puhChromaIntraDir[ui]
                rpcCU.getInterDir()          [self.m_uiAbsIdxInLCU+ui] = self.m_puhInterDir[ui]
                rpcCU.getTransformIdx()      [self.m_uiAbsIdxInLCU+ui] = self.m_puhTrIdx[ui]

                rpcCU.getTransformSkip(TEXT_LUMA)    [self.m_uiAbsIdxInLCU+ui] = self.m_puhTransformSkip[0][ui]
                rpcCU.getTransformSkip(TEXT_CHROMA_U)[self.m_uiAbsIdxInLCU+ui] = self.m_puhTransformSkip[1][ui]
                rpcCU.getTransformSkip(TEXT_CHROMA_V)[self.m_uiAbsIdxInLCU+ui] = self.m_puhTransformSkip[2][ui]

                rpcCU.getDepth() [self.m_uiAbsIdxInLCU+ui] = self.m_puhDepth[ui]
                rpcCU.getWidth() [self.m_uiAbsIdxInLCU+ui] = self.m_puhWidth[ui]
                rpcCU.getHeight()[self.m_uiAbsIdxInLCU+ui] = self.m_puhHeight[ui]

                rpcCU.getMVPIdx(REF_PIC_LIST_0)[self.m_uiAbsIdxInLCU+ui] = self.m_apiMVPIdx[0][ui]
                rpcCU.getMVPIdx(REF_PIC_LIST_1)[self.m_uiAbsIdxInLCU+ui] = self.m_apiMVPIdx[1][ui]
                rpcCU.getMVPNum(REF_PIC_LIST_0)[self.m_uiAbsIdxInLCU+ui] = self.m_apiMVPNum[0][ui]
                rpcCU.getMVPNum(REF_PIC_LIST_1)[self.m_uiAbsIdxInLCU+ui] = self.m_apiMVPNum[1][ui]

                rpcCU.getIPCMFlag()[self.m_uiAbsIdxInLCU+ui] = self.m_pbIPCMFlag[ui]

            self.m_acCUMvField[0].copyTo(rpcCU.getCUMvField(REF_PIC_LIST_0), self.m_uiAbsIdxInLCU)
            self.m_acCUMvField[1].copyTo(rpcCU.getCUMvField(REF_PIC_LIST_1), self.m_uiAbsIdxInLCU)

            uiTmp = cvar.g_uiMaxCUWidth * cvar.g_uiMaxCUHeight >> (uiDepth<<1)
            uiTmp2 = self.m_uiAbsIdxInLCU * self.m_pcPic.getMinCUWidth() * self.m_pcPic.getMinCUHeight()
            for ui in xrange(uiTmp):
                rpcCU.getCoeffY()    [uiTmp2+ui] = self.m_pcTrCoeffY[ui]
                rpcCU.getArlCoeffY() [uiTmp2+ui] = self.m_pcArlCoeffY[ui]
                rpcCU.getPCMSampleY()[uiTmp2+ui] = self.m_pcIPCMSampleY[ui]

            uiTmp >>= 2
            uiTmp2 >>=2
            for ui in xrange(uiTmp):
                rpcCU.getCoeffCb()    [uiTmp2+ui] = self.m_pcTrCoeffCb[ui]
                rpcCU.getCoeffCr()    [uiTmp2+ui] = self.m_pcTrCoeffCr[ui]
                rpcCU.getArlCoeffCb() [uiTmp2+ui] = self.m_pcArlCoeffCb[ui]
                rpcCU.getArlCoeffCr() [uiTmp2+ui] = self.m_pcArlCoeffCr[ui]
                rpcCU.getPCMSampleCb()[uiTmp2+ui] = self.m_pcIPCMSampleCb[ui]
                rpcCU.getPCMSampleCr()[uiTmp2+ui] = self.m_pcIPCMSampleCr[ui]

            rpcCU.m_uiTotalBins += self.m_uiTotalBins

            for ui in xrange(self.m_uiNumPartition):
                rpcCU.m_uiSliceStartCU         [self.m_uiAbsIdxInLCU+ui] = self.m_uiSliceStartCU[ui]
                rpcCU.m_uiDependentSliceStartCU[self.m_uiAbsIdxInLCU+ui] = self.m_uiDependentSliceStartCU[ui]
        elif uiPartIdx != None and uiPartDepth != None:
            rpcCU = self.m_pcPic.getCU(self.m_uiCUAddr)
            uiQNumPart = self.m_uiNumPartition >> (uiPartDepth<<1)

            uiPartStart = uipartIdx * uiQNumPart
            uiPartOffset = self.m_uiAbsIdxInLCU * uiPartStart

            rpcCU.m_dTotalCost        = self.m_dTotalCost
            rpcCU.m_uiTotalDistortion = self.m_uiTotalDistortion
            rpcCU.m_uiTotalBits       = self.m_uiTotalBits

            for ui in xrange(uiQNumPart):
                rpcCU.getSkipFlag()          [uiPartOffset+ui] = self.m_skipFlag[ui]

                rpcCU.getQP()                [uiPartOffset+ui] = self.m_phQP[ui]

                rpcCU.getPartitionSize()     [uiPartOffset+ui] = self.m_pePartSize[ui]
                rpcCU.getPredictionMode()    [uiPartOffset+ui] = self.m_pePredMode[ui]
                rpcCU.getCUTransquantBypass()[uiPartOffset+ui] = self.m_CUTransquantBypass[ui]
                rpcCU.m_lcuAlfEnabled[0] = self.m_lcuAlfEnabled[0]
                rpcCU.m_lcuAlfEnabled[1] = self.m_lcuAlfEnabled[1]
                rpcCU.m_lcuAlfEnabled[2] = self.m_lcuAlfEnabled[2]
                rpcCU.getMergeFlag()         [uiPartOffset+ui] = self.m_pbMergeFlag[ui]
                rpcCU.getMergeIndex()        [uiPartOffset+ui] = self.m_puhMergeIndex[ui]
                rpcCU.getLumaIntraDir()      [uiPartOffset+ui] = self.m_puhLumaIntraDir[ui]
                rpcCU.getChromaIntraDir()    [uiPartOffset+ui] = self.m_puhChromaIntraDir[ui]
                rpcCU.getInterDir()          [uiPartOffset+ui] = self.m_puhInterDir[ui]
                rpcCU.getTransformIdx()      [uiPartOffset+ui] = self.m_puhTrIdx[ui]

                rpcCU.getTransformSkip(TEXT_LUMA    )[uiPartOffset+ui] = self.m_puhTransformSkip[0][ui]
                rpcCU.getTransformSkip(TEXT_CHROMA_U)[uiPartOffset+ui] = self.m_puhTransformSkip[1][ui]
                rpcCU.getTransformSkip(TEXT_CHROMA_V)[uiPartOffset+ui] = self.m_puhTransformSkip[2][ui]

                rpcCU.getDepth() [uiPartOffset+ui] = self.m_puhDepth[ui]
                rpcCU.getWidth() [uiPartOffset+ui] = self.m_puhWidth[ui]
                rpcCU.getHeight()[uiPartOffset+ui] = self.m_puhHeight[ui]

                rpcCU.getMVPIdx(REF_PIC_LIST_0)[uiPartOffset+ui] = self.m_apiMVPIdx[0][ui]
                rpcCU.getMVPIdx(REF_PIC_LIST_1)[uiPartOffset+ui] = self.m_apiMVPIdx[1][ui]
                rpcCU.getMVPNum(REF_PIC_LIST_0)[uiPartOffset+ui] = self.m_apiMVPNum[0][ui]
                rpcCU.getMVPNum(REF_PIC_LIST_1)[uiPartOffset+ui] = self.m_apiMVPNum[1][ui]

                rpcCU.getIPCMFlag()[uiPartOffset+ui] = self.m_pbIPCMFlag[ui]

            self.m_acCUMvField[0].copyTo(rpcCU.getCUMvField(REF_PIC_LIST_0), self.m_uiAbsIdxInLCU, uiPartStart, uiQNumPart)
            self.m_acCUMvField[1].copyTo(rpcCU.getCUMvField(REF_PIC_LIST_1), self.m_uiAbsIdxInLCU, uiPartStart, uiQNumPart)

            uiTmp = cvar.g_uiMaxCUWidth * cvar.g_uiMaxCUHeight >> ((uiDepth+uiPartDepth)<<1)
            uiTmp2 = uiPartOffset * self.m_pcPic.getMinCUWidth() * self.m_pcPic.getMinCUHeight()
            for ui in xrange(uiTmp):
                rpcCU.getCoeffY()    [uiTmp2+ui] = self.m_pcTrCoeffY[ui]
                rpcCU.getArlCoeffY() [uiTmp2+ui] = self.m_pcArlCoeffY[ui]
                rpcCU.getPCMSampleY()[uiTmp2+ui] = self.m_pcIPCMSampleY[ui]

            uiTmp >>= 2
            uiTmp2 >>=2
            for ui in xrange(uiTmp):
                rpcCU.getCoeffCb()    [uiTmp2+ui] = self.m_pcTrCoeffCb[ui]
                rpcCU.getCoeffCr()    [uiTmp2+ui] = self.m_pcTrCoeffCr[ui]
                rpcCU.getArlCoeffCb() [uiTmp2+ui] = self.m_pcArlCoeffCb[ui]
                rpcCU.getArlCoeffCr() [uiTmp2+ui] = self.m_pcArlCoeffCr[ui]
                rpcCU.getPCMSampleCb()[uiTmp2+ui] = self.m_pcIPCMSampleCb[ui]
                rpcCU.getPCMSampleCr()[uiTmp2+ui] = self.m_pcIPCMSampleCr[ui]

            rpcCU.m_uiTotalBins += self.m_uiTotalBins

            for ui in xrange(uiQNumPart):
                rpcCU.m_uiSliceStartCU         [uiPartOffset+ui] = self.m_uiSliceStartCU[ui]
                rpcCU.m_uiDependentSliceStartCU[uiPartOffset+ui] = self.m_uiDependentSliceStartCU[ui]

    def getPic(self):
        return self.m_pcPic
    def getSlice(self):
        return self.m_pcSlice
    def getAddr(self):
        return self.m_uiCUAddr
    def getZorderIdxInCU(self):
        return self.m_uiAbsIdxInLCU
    def getSCUAddr(self):
        return self.getPic().getPicSym().getInverseCUOrderMap(self.m_uiCUAddr) * \
               (1 << (self.m_pcSlice.getSPS().getMaxCUDepth()<<1)) + self.m_uiAbsIdxInLCU
    def getCUPelX(self):
        return self.m_uiCUPelX
    def getCUPelY(self):
        return self.m_uiCUPelY
    def getPattern(self):
        return self.m_pcPattern

    def getDepth(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhDepth
        else:
            return self.m_puhDepth[uiIdx]
    def setDepth(self, uiIdx, uh):
        self.m_puhDepth[uiIdx] = uh
    def setDepthSubParts(self, uiDepth, uiAbsPartIdx):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        for ui in xrange(uiCurrPartNumb):
            self.m_puhDepth[uiAbsPartIdx+ui] = uiDepth

    def getPartitionSize(self, uiIdx=None):
        if uiIdx == None:
            return self.m_pePartSize
        else:
            return self.m_pePartSize[uiIdx]
    def setPartitionSize(self, uiIdx, uh):
        self.m_pePartSize[uiIdx] = uh
    def setPartSizeSubParts(self, eMode, uiAbsPartIdx, uiDepth):
        for ui in xrange(self.m_pcPic.getNumPartInCU() >> (2*uiDepth)):
            self.m_pePartSize[uiAbsPartIdx+ui] = eMode

    def getCUTransquantBypass(self, uiIdx=None):
        if uiIdx == None:
            return self.m_CUTransquantBypass
        else:
            return self.m_CUTransquantBypass[uiIdx]
    def setCUTransquantBypassSubParts(self, flag, uiAbsPartIdx, uiDepth):
        for ui in xrange(self.m_pcPic.getNumPartInCU() >> (2*uiDepth)):
            self.m_CUTransquantBypass[uiAbsPartIdx+ui] = flag

    def getSkipFlag(self, idx=None):
        if idx == None:
            return self.m_skipFlag
        else:
            return self.m_skipFlag[idx]
    def setSkipFlag(self, idx, skip):
        self.m_skipFlag[idx] = skip
    def setSkipFlagSubParts(self, skip, absPartIdx, depth):
        for ui in xrange(self.m_pcPic.getNumPartInCU() >> (2*uiDepth)):
            self.m_skipFlag[absPartIdx+ui] = skip

    def getPredictionMode(self, uiIdx=None):
        if uiIdx == None:
            return self.m_pePredMode
        else:
            return self.m_pePredMode[uiIdx]
    def setPredictionMode(self, uiIdx, uh):
        self.m_pePredMode[uiIdx] = uh
    def setPredModeSubParts(self, eMode, uiAbsPartIdx, uiDepth):
        for ui in xrange(self.m_pcPic.getNumPartInCU() >> (2*uiDepth)):
            self.m_pePredMode[uiAbsPartIdx+ui] = eMode

    def getWidth(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhWidth
        else:
            return self.m_puhWidth[uiIdx]
    def setWidth(self, uiIdx, uh):
        self.m_puhWidth[uiIdx] = uh

    def getHeight(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhHeight
        else:
            return self.m_puhHeight[uiIdx]
    def setHeight(self, uiIdx, uh):
        self.m_puhHeight[uiIdx] = uh

    def setSizeSubParts(self, uiWidth, uiHeight, uiAbsPartIdx, uiDepth):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)

        for ui in xrange(uiCurrPartNumb):
            self.m_puhWidth[uiAbsPartIdx+ui] = uiWidth
            self.m_puhHeight[uiAbsPartIdx+ui] = uiHeight

    def getQP(self, uiIdx=None):
        if uiIdx == None:
            return self.m_phQP
        else:
            return self.m_phQP[uiIdx]
    def setQP(self, uiIdx, value):
        self.m_phQP[uiIdx] = value
    def setQPSubParts(self, qp, uiAbsPartIdx, uiDepth):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        pcSlice = self.getPic().getSlice(self.getPic().getCurrSliceIdx())

        for uiSCUIdx in xrange(uiAbsPartIdx, uiAbsPartIdx+uiCurrPartNumb):
            if self.m_pcPic.getCU(self.getAddr().getDependentSliceStartCU(uiSCUIdx + self.getZorderIdxInCU())) == pcSlice.getDependentSliceCurStartCUAddr():
                self.m_phQP[uiSCUIdx] = qp
    def setQPSubCUs(self, qp, pcCU, absPartIdx, depth, foundNonZeroCbf):
        currPartNumb = self.m_pcPic.getNumPartInCU() >> (depth << 1)
        currPartNumQ = currPartNumb >> 2

        if not foundNonZeroCbf:
            if pcCU.getDepth(absPartIdx) > depth:
                for partUnitIdx in xrange(4):
                    pcCU.setQPSubCUs(qp, pcCU, absPartIdx + partUnitIdx * currPartNumQ,
                                     depth+1, foundNonZeroCbf)
            else:
                if pcCU.getCbf(absPartIdx, TEXT_LUMA) or pcCU.getCbf(absPartIdx, TEXT_CHROMA_U) or pcCU.getCbf(absPartIdx, TEXT_CHROMA_V):
                    foundNonZeroCbf = True
                else:
                    self.setQPSubParts(qp, absPartIdx, depth)

        return foundNonZeroCbf

    def setCodedQP(self, qp):
        self.m_codedQP = qp
    def getCodedQP(self):
        return self.m_codedQP

    def getTransformIdx(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhTrIdx
        else:
            return self.m_puhTrIdx[uiIdx]
    def setTrIdxSubParts(self, uiTrIdx, uiAbsPartIdx, uiDepth):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        for ui in xrange(uiCurrPartNumb):
            self.m_puhTrIdx[uiAbsPartIdx+ui] = uiTrIdx

    def getTransformSkip(self, *args):
        if len(args) == 1:
            eType, = args
            self.m_puhTransformSkip[g_aucConvertTxtTypeToIdx[eType]]
        elif len(args) == 2:
            uiIdx, eType = args
            self.m_puhTransformSkip[g_aucConvertTxtTypeToIdx[eType]][uiIdx]
    def setTransformSkipSubParts(self, *args):
        if len(args) == 4:
            useTransformSkip, eType, uiAbsPartIdx, uiDepth = args
            uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)

            for ui in xrange(uiCurrPartNumb):
                self.m_puhTransformSkip[g_aucConvertTxtTypeToIdx[eType]][uiAbsPartIdx+ui] = useTransformSkip
        elif len(args) == 5:
            useTransformSkipY, useTransformSkipU, useTransformSkipV, uiAbsPartIdx, uiDepth = args
            uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)

            for ui in xrange(uiCurrPartNumb):
                self.m_puhTransformSkip[0][uiAbsPartIdx+ui] = useTransformSkipY
                self.m_puhTransformSkip[1][uiAbsPartIdx+ui] = useTransformSkipU
                self.m_puhTransformSkip[2][uiAbsPartIdx+ui] = useTransformSkipV

    def getCUMvField(self, e):
        return self.m_acCUMvField[e]

    def getCoeffY(self):
        return self.m_pcTrCoeffY
    def getCoeffCb(self):
        return self.m_pcTrCoeffCb
    def getCoeffCr(self):
        return self.m_pcTrCoeffCr
    def getArlCoeffY(self):
        return self.m_pcArlCoeffY
    def getArlCoeffCb(self):
        return self.m_pcArlCoeffCb
    def getArlCoeffCr(self):
        return self.m_pcArlCoeffCr

    def getPCMSampleY(self):
        return self.m_pcIPCMSampleY
    def getPCMSampleCb(self):
        return self.m_pcIPCMSampleCb
    def getPCMSampleCr(self):
        return self.m_pcIPCMSampleCr

    def getCbf(self, *args):
        if len(args) == 2:
            uiIdx, eType = args
            return self.m_puhCbf[g_aucConvertTxtTypeToIdx[eType]][uiIdx]
        elif len(args) == 1:
            eType, = args
            return self.m_puhCbf[g_aucConvertTxtTypeToIdx[eType]]
        elif len(args) == 3:
            uiIdx, eType, uiTrDepth = args
            return (self.getCbf(uiIdx, eType) >> uiTrDepth) & 0x1
    def setCbf(self, uiIdx, eType, uh):
        self.m_puhCbf[g_aucConvertTxtTypeToIdx[eType]][uiIdx] = uh
    def clearCbf(self, uiIdx, eType, uiNumParts):
        for ui in xrange(uiNumParts):
            self.m_puhCbf[g_aucConvertTxtTypeToIdx[eType]][uiIdx+ui] = 0
    def getQtRootCbf(self, uiIdx):
        return self.getCbf(uiIdx, TEXT_LUMA, 0) or \
               self.getCbf(uiIdx, TEXT_CHROMA_U, 0) or \
               self.getCbf(uiIdx, TEXT_CHROMA_V, 0)

    def setCbfSubParts(self, *args):
        if len(args) == 5:
            uiCbfY, uiCbfU, uiCbfV, uiAbsPartIdx, uiDepth = args
            uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
            for ui in xrange(uiCurrPartNumb):
                self.m_puhCbf[0][uiAbsPartIdx+ui] = uiCbfY
                self.m_puhCbf[1][uiAbsPartIdx+ui] = uiCbfU
                self.m_puhCbf[2][uiAbsPartIdx+ui] = uiCbfV
        elif len(args) == 4:
            uiCbf, eTType, uiAbsPartIdx, uiDepth = args
            uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
            for ui in xrange(uiCurrPartNumb):
                self.m_puhCbf[g_aucConvertTxtTypeToIdx[eTType]][uiAbsPartIdx+ui] = uiCbf

        #   uiCbf, eTType, uiAbsPartIdx, uiPartIdx, uiDepth = args
        #   self.setSubPart(uiCbf, self.m_puhCbf[g_aucConvertTxtTypeToIdx[eTType]],
        #                   uiAbsPartIdx, uiDepth, uiPartIdx)

    def getMergeFlag(self, uiIdx=None):
        if uiIdx == None:
            return self.m_pbMergeFlag
        else:
            return self.m_pbMergeFlag[uiIdx]
    def setMergeFlag(self, uiIdx, b):
        self.m_pbMergeFlag[uiIdx] = b
    def setMergeFlagSubParts(self, bMergeFlag, uiAbsPartIdx, uiPartIdx, uiDepth):
        self.setSubPart(bMergeFlag, self.m_pbMergeFlag, uiAbsPartIdx, uiDepth, uiPartIdx)

    def getMergeIndex(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhMergeIndex
        else:
            return self.m_puhMergeIndex[uiIdx]
    def setMergeIndex(self, uiIdx, uiMergeIndex):
        self.m_puhMergeIndex[uiIdx] = uiMergeIndex
    def setMergeIndexSubParts(self, uiMergeIndex, uiAbsPartIdx, uiPartIdx, uiDepth):
        self.setSubPart(uiMergeIndex, self.m_puhMergeIndex, uiAbsPartIdx, uiDepth, uiPartIdx)

    def setMergeAMP(self, b):
        self.m_bIsMergeAMP = b
    def getMergeAMP(self):
        return self.m_bIsMergeAMP

    def getLumaIntraDir(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhLumaIntraDir
        else:
            return self.m_puhLumaIntraDir[uiIdx]
    def setLumaIntraDir(self, uiIdx, uh):
        self.m_puhLumaIntraDir[uiIdx] = uh
    def setLumaIntraDirSubParts(self, uiDir, uiAbsPartIdx, uiDepth):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        for ui in xrange(uiCurrPartNumb):
            self.m_puhLumaIntraDir[uiAbsPartIdx+ui] = uiDir

    def getChromaIntraDir(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhChromaIntraDir
        else:
            return self.m_puhChromaIntraDir[uiIdx]
    def setChromaIntraDir(self, uiIdx, uh):
        self.m_puhChromaIntraDir[uiIdx] = uh
    def setChromaIntraDirSubParts(self, uiDir, uiAbsPartIdx, uiDepth):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        for ui in xrange(uiCurrPartNumb):
            self.m_puhChromaIntraDir[uiAbsPartIdx+ui] = uiDir

    def getInterDir(self, uiIdx=None):
        if uiIdx == None:
            return self.m_puhInterDir
        else:
            return self.m_puhInterDir[uiIdx]
    def setInterDir(self, uiIdx, uh):
        self.m_puhInterDir[uiIdx] = uh
    def setInterDirSubParts(self, uiDir, uiAbsPartIdx, uiPartIdx, uiDepth):
        self.setSubPart(uiDir, self.m_puhInterDir, uiAbsPartIdx, uiDepth, uiPartIdx)

    def getAlfLCUEnabled(self, compIdx):
        return self.m_lcuAlfEnabled[compIdx]
    def setAlfLCUEnabled(self, b, compIdx):
        self.m_lcuAlfEnabled[compIdx] = b
    def getIPCMFlag(self, uiIdx=None):
        if uiIdx == None:
            return self.m_pbIPCMFlag
        else:
            return self.m_pbIPCMFlag[uiIdx]
    def setIPCMFlag(self, uiIdx, b):
        self.m_pbIPCMFlag[uiIdx] = b
    def setIPCMFlagSubParts(self, bIpcmFlag, uiAbsPartIdx, uiDepth):
        uiCurrPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        for ui in xrange(uiCurrPartNumb):
            self.m_pbIPCMFlag[uiAbsPartIdx+ui] = bIpcmFlag

    def getNumSucIPCM(self, num=None):
        if num == None:
            return self.m_numSucIPCM
        else:
            return self.m_numSucIPCM[num]
    def getLastCUSucIPCMFlag(self):
        return self.m_lastCUSucIPCMFlag
    def setLastCUSucIPCMFlag(self, flg):
        self.m_lastCUSucIPCMFlag = flg

    def setSubPart(self, uiParameter, puhBaseLCU, uiCUAddr, uiCUDepth, uiPUIdx):
        uiCurrPartNumQ = (self.m_pcPic.getNumPartInCU() >> (2 * uiCUDepth)) >> 2
        uiPartSize = self.m_pePartSize[uiCUAddr]
        if uiPartSize == SIZE_2Nx2N:
            for ui in xrange(4 * uiCurrPartNumQ):
                puhBaseLCU[uiCUAddr+ui] = uiParameter
        elif uiPartSize == SIZE_2NxN:
            for ui in xrange(2 * uiCurrPartNumQ):
                puhBaseLCU[uiCUAddr+ui] = uiParameter
        elif uiPartSize == SIZE_Nx2N:
            for ui in xrange(uiCurrPartNumQ):
                puhBaseLCU[uiCUAddr                 +ui] = uiParameter
                puhBaseLCU[uiCUAddr+2*uiCurrPartNumQ+ui] = uiParameter
        elif uiPartSize == SIZE_NxN:
            for ui in xrange(uiCurrPartNumQ):
                puhBaseLCU[uiCUAddr+ui] = uiParameter
        elif uiPartSize == SIZE_2NxnU:
            if uiPUIdx == 0:
                for ui in xrange(uiCurrPartNumQ>>1):
                    puhBaseLCU[uiCUAddr               +ui] = uiParameter
                    puhBaseLCU[uiCUAddr+uiCurrPartNumQ+ui] = uiParameter
            elif uiPUIdx == 1:
                for ui in xrange(uiCurrPartNumQ>>1):
                    puhBaseLCU[uiCUAddr               +ui] = uiParameter
                    puhBaseLCU[uiCUAddr+uiCurrPartNumQ+ui] = uiParameter
            else:
                assert(False)
        elif uiPartSize == SIZE_2NxnD:
            if uiPUIdx == 0:
                for ui in xrange((uiCurrPartNumQ<<1) + (uiCurrPartNumQ>>1)):
                    puhBaseLCU[uiCUAddr                                   +ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ>>1):
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)+uiCurrPartNumQ+ui] = uiParameter
            elif uiPUIdx == 1:
                for ui in xrange(uiCurrPartNumQ>>1):
                    puhBaseLCU[uiCUAddr               +ui] = uiParameter
                    puhBaseLCU[uiCUAddr+uiCurrPartNumQ+ui] = uiParameter
            else:
                assert(False)
        elif uiPartSize == SIZE_nLx2N:
            if uiPUIdx == 0:
                for ui in xrange(uiCurrPartNumQ>>2):
                    puhBaseLCU[uiCUAddr                                        +ui] = uiParameter
                    puhBaseLCU[uiCUAddr                    +(uiCurrPartNumQ>>1)+ui] = uiParameter
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)                    +ui] = uiParameter
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)+(uiCurrPartNumQ>>1)+ui] = uiParameter
            elif uiPUIdx == 1:
                for ui in xrange(uiCurrPartNumQ>>2):
                    puhBaseLCU[uiCUAddr                                        +ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ + (uiCurrPartNumQ>>2)):
                    puhBaseLCU[uiCUAddr                    +(uiCurrPartNumQ>>1)+ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ>>2):
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)                    +ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ + (uiCurrPartNumQ>>2)):
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)+(uiCurrPartNumQ>>1)+ui] = uiParameter
            else:
                assert(False)
        elif uiPartSize == SIZE_nRx2N:
            if uiPUIdx == 0:
                for ui in xrange(uiCurrPartNumQ + (uiCurrPartNumQ>>2)):
                    puhBaseLCU[uiCUAddr                                                       +ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ>>2):
                    puhBaseLCU[uiCUAddr+                    uiCurrPartNumQ+(uiCurrPartNumQ>>1)+ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ + (uiCurrPartNumQ>>2)):
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)                                   +ui] = uiParameter
                for ui in xrange(uiCurrPartNumQ>>2):
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)+uiCurrPartNumQ+(uiCurrPartNumQ>>1)+ui] = uiParameter
            elif uiPUIdx == 1:
                for ui in xrange(uiCurrPartNumQ>>2):
                    puhBaseLCU[uiCUAddr                                        +ui] = uiParameter
                    puhBaseLCU[uiCUAddr                    +(uiCurrPartNumQ>>1)+ui] = uiParameter
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)                    +ui] = uiParameter
                    puhBaseLCU[uiCUAddr+(uiCurrPartNumQ<<1)+(uiCurrPartNumQ>>1)+ui] = uiParameter
            else:
                assert(False)
        else:
            assert(False)

    def getSUSliceID(self, uiIdx):
        return self.m_piSliceSUMap[uiIdx]
    def getSliceSUMap(self):
        return self.m_piSliceSUMap
    def setSliceSUMap(self, pi):
        self.m_piSliceSUMap = pi

    def getNDBFilterBlocks(self):
        return self.m_vNDFBlock
    def setNDBFilterBlockBorderAvailability(self,
                numLCUInPicWidth, numLCUInPicHeight, numSUInLCUWidth, numSUInLCUHeight,
                picWidth, picHeight, LFCrossSliceBoundary,
                bTopTileBoundary, bDownTileBoundary, bLeftTileBoundary, bRightTileBoundary,
                bIndependentTileBoundaryEnabled):
        numSUInLCU = numSUInLCUWidth * numSUInLCUHeight
        pSliceIDMapLCU = self.m_piSliceSUMap
        onlyOneSliceInPic = LFCrossSliceBoundary.size() == 1
        uiLPelX = uiTPelY = 0
        width = height = 0
        bPicRBoundary = bPicBBoundary = bPicTBoundary = bPicLBoundary = 0
        bLCURBoundary = bLCUBBoundary = bLCUTBoundary = bLCULBoundary = False
        pbAvailBorder = None
        pbAvail = None
        rTLSU = rBRSU = widthSU = heightSU = 0
        zRefSU = 0
        pRefID = None
        pRefMapLCU = None
        rTRefSU = rBRefSU = rLRefSU = rRRefSU = 0
        pRRefMapLCU = None
        pLRefMapLCU = None
        pTRefMapLCU = None
        pBRefMapLCU = None
        sliceID = 0
        numSGU = self.m_vNDFBlock.size()

        for i in xrange(numSGU):
            rSGU = self.m_vNDFBlock[i]

            sliceID  = rSGU.sliceID
            uiLPelX  = rSGU.posX
            uiTPelY  = rSGU.posY
            width    = rSGU.width
            height   = rSGU.height
            rTLSU    = g_auiZscanToRaster[rSGU.startSU]
            rBRSU    = g_auiZscanToRaster[rSGU.endSU]
            widthSU  = rSGU.widthSU
            heightSU = rSGU.heightSU

            pbAvailBorder = rSGU.isBorderAvailable

            bPicTBoundary = True if uiTPelY == 0 else False
            bPicLBoundary = True if uiLPelX == 0 else False
            bPicRBoundary = True if not (uiLPelX + width < picWidth) else False
            bPicBBoundary = True if not (uiTPelY + height < picHeight) else False

            bLCULBoundary = True if rTLSU % numSUInLCUWidth == 0 else False
            bLCURBoundary = True if (rTLSU + widthSU) % numSUInLCUWidth == 0 else False
            bLCUTBoundary = True if rTLSU / numSUInLCUWidth == 0 else False
            bLCUBBoundary = True if rBRSU / numSUInLCUWidth == numSUInLCUHeight-1 else False

            # SGU_L
            pbAvail = pbAvailBorder[SGU_L]
            if bPicLBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                # bLCULBoundary = (rTLSU % uiNumSUInLCUWidth == 0)?(true):(false);
                if bLCULBoundary:
                    rLRefSU = rTLSU + numSUInLCUWidth - 1
                    zRefSU = g_auiRasterToZscan[rLRefSU]
                    pRefMapLCU = pLRefMapLCU = pSliceIDMapLCU - numSUInLCU
                else:
                    zRefSU = g_auiRasterToZscan[rTLSU - 1]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_R
            pbAvail = pbAvailBorder[SGU_R]
            if bPicRBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                # bLCURBoundary = ( (rTLSU+ uiWidthSU) % uiNumSUInLCUWidth == 0)?(true):(false);
                if bLCURBoundary:
                    rRRefSU = rTLSU + widthSU - numSUInLCUWidth
                    zRefSU = g_auiRasterToZscan[rRRefSU]
                    pRefMapLCU = pRRefMapLCU = pSliceIDMapLCU - numSUInLCU
                else:
                    zRefSU = g_auiRasterToZscan[rTLSU + widthSU]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_T
            pbAvail = pbAvailBorder[SGU_T]
            if bPicTBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                # bLCUTBoundary = ( (UInt)(rTLSU / uiNumSUInLCUWidth)== 0)?(true):(false);
                if bLCUTBoundary:
                    rTRefSU = numSUInLCU - (numSUInLCUWidth - rTLSU)
                    zRefSU = g_auiRasterToZscan[rTRefSU]
                    pRefMapLCU = pTRefMapLCU = pSliceIDMapLCU - (numLCUInPicWidth*numSUInLCU)
                else:
                    zRefSU = g_auiRasterToZscan[rTLSU - numSUInLCUWidth]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_B
            pbAvail = pbAvailBorder[SGU_B]
            if bPicBBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                # bLCUBBoundary = ( (UInt)(rBRSU / uiNumSUInLCUWidth) == (uiNumSUInLCUHeight-1) )?(true):(false);
                if bLCUBBoundary:
                    rBRefSU = rTLSU % numSUInLCUWidth
                    zRefSU = g_auiRasterToZscan[rBRefSU]
                    pRefMapLCU = pBRefMapLCU = pSliceIDMapLCU + (numLCUInPicWidth*numSUInLCU)
                else:
                    zRefSU = g_auiRasterToZscan[rTLSU + heightSU*numSUInLCUWidth]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_TL
            pbAvail = pbAvailBorder[SGU_TL]
            if bPicTBoundary or bPicLBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                if bLCUTBoundary and bLCULBoundary:
                    zRefSU = numSUInLCU - 1
                    pRefMapLCU = pSliceIDMapLCU - (numLCUInPicWidth+1)*numSUInLCU
                elif bLCUTBoundary:
                    zRefSU = g_auiRasterToZscan[rTRefSU - 1]
                    pRefMapLCU = pTRefMapLCU
                elif bLCULBoundary:
                    zRefSU = g_auiRasterToZscan[rLRefSU - numSUInLCUWidth]
                    pRefMapLCU = pLRefMapLCU
                else: #inside LCU
                    zRefSU = g_auiRasterToZscan[rTLSU - numSUInLCUWidth - 1]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_TR
            pbAvail = pbAvailBorder[SGU_TR]
            if bPicTBoundary or bPicRBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                if bLCUTBoundary and bLCURBoundary:
                    zRefSU = g_auiRasterToZscan[numSUInLCU - numSUInLCUWidth]
                    pRefMapLCU = pSliceIDMapLCU - (numLCUInPicWidth-1)*numSUInLCU
                elif bLCUTBoundary:
                    zRefSU = g_auiRasterToZscan[rTRefSU + widthSU]
                    pRefMapLCU = pTRefMapLCU
                elif bLCURBoundary:
                    zRefSU = g_auiRasterToZscan[rRRefSU - numSUInLCUWidth]
                    pRefMapLCU = pRRefMapLCU
                else: #inside LCU
                    zRefSU = g_auiRasterToZscan[rTLSU - numSUInLCUWidth + widthSU]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_BL
            pbAvail = pbAvailBorder[SGU_BL]
            if bPicBBoundary or bPicLBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                if bLCUBBoundary and bLCULBoundary:
                    zRefSU = g_auiRasterToZscan[numSUInLCUWidth - 1]
                    pRefMapLCU = pSliceIDMapLCU + (numLCUInPicWidth-1)*numSUInLCU
                elif bLCUBBoundary:
                    zRefSU = g_auiRasterToZscan[rBRefSU - 1]
                    pRefMapLCU = pBRefMapLCU
                elif bLCULBoundary:
                    zRefSU = g_auiRasterToZscan[rLRefSU + heightSU*numSUInLCUWidth]
                    pRefMapLCU = pLRefMapLCU
                else: #inside LCU
                    zRefSU = g_auiRasterToZscan[rTLSU + heightSU*numSUInLCUWidth - 1]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            # SGU_BR
            pbAvail = pbAvailBorder[SGU_BR]
            if bPicBBoundary or bPicRBoundary:
                pbAvail[0] = False
            elif onlyOneSliceInPic:
                pbAvail[0] = True
            else:
                if bLCUBBoundary and bLCURBoundary:
                    zRefSU = 0
                    pRefMapLCU = pSliceIDMapLCU + (numLCUInPicWidth+1)*numSUInLCU
                elif bLCUBBoundary:
                    zRefSU = g_auiRasterToZscan[rBRefSU + widthSU]
                    pRefMapLCU = pBRefMapLCU
                elif bLCURBoundary:
                    zRefSU = g_auiRasterToZscan[rRRefSU + heightSU*numSUInLCUWidth]
                    pRefMapLCU = pRRefMapLCU
                else: #inside LCU
                    zRefSU = g_auiRasterToZscan[rTLSU + heightSU*numSUInLCUWidth + widthSU]
                    pRefMapLCU = pSliceIDMapLCU
                pRefID = pRefMapLCU + zRefSU
                pbAvail[0] = True if pRefID[0] == sliceID else \
                             LFCrossSliceBoundary[pRefID[0]] if pRefID[0] > sliceID else LFCrossSliceBoundary[sliceID]

            if bIndependentTileBoundaryEnabled:
                # left LCU boundary
                if not bPicLBoundary and bLCULBoundary:
                    if bLeftTileBoundary:
                        pbAvailBorder[SGU_L ] = False
                        pbAvailBorder[SGU_TL] = False
                        pbAvailBorder[SGU_BL] = False
                # right LCU boundary
                if not bPicRBoundary and bLCURBoundary:
                    if bRightTileBoundary:
                        pbAvailBorder[SGU_R ] = False
                        pbAvailBorder[SGU_TR] = False
                        pbAvailBorder[SGU_BR] = False
                # top LCU boundary
                if not bPicTBoundary and bLCUTBoundary:
                    if bTopTileBoundary:
                        pbAvailBorder[SGU_T ] = False
                        pbAvailBorder[SGU_TL] = False
                        pbAvailBorder[SGU_TR] = False
                # down LCU boundary
                if not bPicBBoundary and bLCUBBoundary:
                    if bDownTileBoundary:
                        pbAvailBorder[SGU_B ] = False
                        pbAvailBorder[SGU_BL] = False
                        pbAvailBorder[SGU_BR] = False
            rSGU.allBordersAvailable = True
            for b in xrange(NUM_SGU_BORDER):
                if pbAvailBorder[b] == False:
                    rSGU.allBordersAvailable = False
                    break

    def getPartIndexAndSize(self, uiPartIdx, ruiPartAddr, riWidth, riHeight):
        if self.m_pePartSize[0] == SIZE_2NxN:
            riWidth = self.getWidth(0)
            riHeight = self.getHeight(0) >> 1
            ruiPartAddr = 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_Nx2N:
            riWidth = self.getWidth(0) >> 1
            riHeight = self.getHeight(0)
            ruiPartAddr = 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 2
        elif self.m_pePartSize[0] == SIZE_NxN:
            riWidth = self.getWidth(0) >> 1
            riHeight = self.getHeight(0) >> 1
            ruiPartAddr = (self.m_uiNumPartition >> 2) * uiPartIdx
        elif self.m_pePartSize[0] == SIZE_2NxnU:
            riWidth = self.getWidth(0)
            riHeight = self.getHeight(0) >> 2 if uiPartIdx == 0 else (self.getHeight(0)>>2) + (self.getHeight(0)>>1)
            ruiPartAddr = 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 3
        elif self.m_pePartSize[0] == SIZE_2NxnD:
            riWidth = self.getWidth(0)
            riHeight = (self.getHeight(0)>>2) + (self.getHeight(0)>>1) if uiPartIdx == 0 else self.getHeight(0) >> 2
            ruiPartAddr = 0 if uiPartIdx == 0 else (self.m_uiNumPartition>>1) + (self.m_uiNumPartition>>3)
        elif self.m_pePartSize[0] == SIZE_nLx2N:
            riWidth = self.getWidth(0) >> 2 if uiPartIdx == 0 else (self.getWidth(0)>>2) + (self.getWidth(0)>>1)
            riHeight = self.getHeight(0)
            ruiPartAddr = 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 4
        elif self.m_pePartSize[0] == SIZE_nRx2N:
            riWidth = (self.getWidth(0)>>2) + (self.getWidth(0)>>1) if uiPartIdx == 0 else self.getWidth(0) >> 2
            riHeight = self.getHeight(0)
            ruiPartAddr = 0 if uiPartIdx == 0 else (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>4)
        else:
            assert(self.m_pePartSize[0] == SIZE_2Nx2N)
            riWidth = self.getWidth(0)
            riHeight = self.getHeight(0)
            ruiPartAddr = 0

        return ruiPartAddr, riWidth, riHeight

    def getNumPartInter(self):
        iNumPart = 0

        if self.m_pePartSize[0] == SIZE_2Nx2N:
            iNumPart = 1
        elif self.m_pePartSize[0] == SIZE_2NxN:
            iNumPart = 2
        elif self.m_pePartSize[0] == SIZE_Nx2N:
            iNumPart = 2
        elif self.m_pePartSize[0] == SIZE_NxN:
            iNumPart = 4
        elif self.m_pePartSize[0] == SIZE_2NxnU:
            iNumPart = 2
        elif self.m_pePartSize[0] == SIZE_2NxnD:
            iNumPart = 2
        elif self.m_pePartSize[0] == SIZE_nLx2N:
            iNumPart = 2
        elif self.m_pePartSize[0] == SIZE_nRx2N:
            iNumPart = 2
        else:
            assert(False)

        return iNumPart

    def getMvField(self, pcCU, uiAbsPartIdx, eRefPicList, rcMvField):
        if pcCU == None: # OUT OF BOUNDARY
            cZeroMv = TComMv()
            rcMvField.setMvField(cZeroMv, NOT_VALID)
            return rcMvField

        pcCUMvField = pcCU.getCUMvField(eRefPicList)
        rcMvField.setMvField(pcCUMvField.getMv(uiAbsPartIdx), pcCUMvField.getRefIdx(uiAbsPartIdx))
        return rcMvField

    def isDiffMER(self, xN, yN, xP, yP):
        plevel = self.getSlice().getPPS().getLog2ParallelMergeLevelMinus2() + 2
        if (xN >> plevel) != (xP >> plevel):
            return True
        if (yN >> plevel) != (yP >> plevel):
            return True
        return False

    def getPartPosition(self, partIdx, xP, yP, nPSW, nPSH):
        col = self.m_uiCUPelX
        row = self.m_uiCUPelY

        if self.m_pePartSize[0] == SIZE_2NxN:
            nPSW = self.getWidth(0)
            nPSH = self.getHeight(0) >> 1
            xP = col
            yP = row if partIdx == 0 else row + nPSH
        elif self.m_pePartSize[0] == SIZE_Nx2N:
            nPSW = self.getWidth(0) >> 1
            nPSH = self.getHeight(0)
            xP = col if partIdx == 0 else col + nPSW
            yP = row
        elif self.m_pePartSize[0] == SIZE_NxN:
            nPSW = self.getWidth(0) >> 1
            nPSH = self.getHeight(0) >> 1
            xP = col + (partIdx & 0x1) * nPSW
            yP = row + (partIdx >> 1) * nPSH
        elif self.m_pePartSize[0] == SIZE_2NxnU:
            nPSW = self.getWidth(0)
            nPSH = self.getHeight(0) >> 2 if partIdx == 0 else (self.getHeight(0)>>2) + (self.getHeight(0)>>1)
            xP = col
            yP = row if partIdx == 0 else row + self.getHeight(0) - nPSH
        elif self.m_pePartSize[0] == SIZE_2NxnD:
            nPSW = self.getWidth(0)
            nPSH = (self.getHeight(0)>>2) + (self.getHeight(0)>>1) if partIdx == 0 else self.getHeight(0) >> 2
            xP = col
            yP = row if partIdx == 0 else row + self.getHeight(0) - nPSH
        elif self.m_pePartSize[0] == SIZE_nLx2N:
            nPSW = self.getWidth(0) >> 2 if partIdx == 0 else (self.getHeight(0)>>2) + (self.getHeight(0)>>1)
            nPSH = self.getHeight(0)
            xP = col if partIdx == 0 else col + self.getWidth(0) - nPSW
            yP = row
        elif self.m_pePartSize[0] == SIZE_nRx2N:
            nPSW = (self.getWidth(0)>>2) + (self.getWidth(0)>>1) if partIdx == 0 else self.getHeight(0) >> 2
            nPSH = self.getHeight(0)
            xP = col if partIdx == 0 else col + self.getWidth(0) - nPSW
            yP = row
        else:
            assert(self.m_pePartSize[0] == SIZE_2Nx2N)
            nPSW = self.getWidth(0)
            nPSH = self.getHeight(0)
            xP = col
            yP = row

        return xP, yP, nPSW, nPSH

    def getAMVPMode(self, uiIdx):
        return self.m_pcSlice.getSPS().getAMVPMode(self.m_puhDepth[uiIdx])

    def fillMvpCand(self, uiPartIdx, uiPartAddr, eRefPicList, iRefIdx, pInfo):
        eCUMode = self.getPartitionSize(0)

        pInfo.iN = 0
        if iRefIdx < 0:
            return

        #-- Get Spatial MV
        uiPartIdxLT = uiPartIdxRT = uiPartIdxLB = 0
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        uiPartIdxLT, uiPartIdxRT = self.deriveLeftRightTopIdx(eCUMode, uiPartIdx, uiPartIdxLT, uiPartIdxRT)
        uiPartIdxLB = self.deriveLeftBottomIdx(eCUMode, uiPartIdx, uiPartIdxLB)

        idx = 0
        tmpCU, idx = self.getPUBelowLeft(idx, uiPartIdxLB, True, False)
        bAddedSmvp = (tmpCU != None) and (tmpCU.getPredictionMode(idx) != MODE_INTRA)

        if not bAddedSmvp:
            tmpCU, idx = self.getPULeft(idx, uiPartIdxLB, True, False)
            bAddedSmvp = (tmpCU != None) and (tmpCU.getPredictionMode(idx) != MODE_INTRA)

        # Left predictor search
        bAdded = self.xAddMVPCand(pInfo, eRefPicList, iRefIdx, uiPartIdxLB, MD_BELOW_LEFT)
        if not bAdded:
            bAdded = self.xAddMVPCand(pInfo, eRefPicList, iRefIdx, uiPartIdxLB, MD_LEFT)

        if not bAdded:
            bAdded = self.xAddMVPCandOrder(pInfo, eRefPicList, iRefIdx, uiPartIdxLB, MD_BELOW_LEFT)
            if not bAdded:
                bAdded = self.xAddMVPCandOrder(pInfo, eRefPicList, iRefIdx, uiPartIdxLB, MD_LEFT)

        # Above predictor search
        bAdded = self.xAddMVPCand(pInfo, eRefPicList, iRefIdx, uiPartIdxRT, MD_ABOVE_RIGHT)
        if not bAdded:
            bAdded = self.xAddMVPCand(pInfo, eRefPicList, iRefIdx, uiPartIdxRT, MD_ABOVE)

        if not bAdded:
            bAdded = self.xAddMVPCand(pInfo, eRefPicList, iRefIdx, uiPartIdxLT, MD_ABOVE_LEFT)
        bAdded = bAddedSmvp
        if pInfo.iN == 2:
            bAdded = True

        if not bAdded:
            bAdded = self.xAddMVPCandOrder(pInfo, eRefPicList, iRefIdx, uiPartIdxRT, MD_ABOVE_RIGHT)
            if not bAdded:
                bAdded = self.xAddMVPCandOrder(pInfo, eRefPicList, iRefIdx, uiPartIdxRT, MD_ABOVE)

            if not bAdded:
                bAdded = self.xAddMVPCandOrder(pInfo, eRefPicList, iRefIdx, uiPartIdxLT, MD_ABOVE_LEFT)

        if self.getAMVPMode(uiPartAddr) == AM_NONE: #Should be optimized later for special cases
            assert(pInfo.iN > 0)
            pInfo.iN = 1
            return

        if pInfo.iN == 2:
            acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
            if acMvCand[0] == acMvCand[1]:
                pInfo.iN = 1

        if self.getSlice().getEnableTMVPFlag():
            # Get Temporal Motion Predictor
            iRefIdx_Col = iRefIdx
            cColMv = TComMv()
            uiPartIdxRB = 0
            uiLCUIdx = self.getAddr()

            uiPartIdxRB = self.deriveRightBottomIdx(eCUMode, uiPartIdx, uiPartIdxRB)
            uiAbsPartAddr = self.m_uiAbsIdxInLCU + uiPartAddr

            #---- co-located RightBottom Temporal Predictor (H) ---
            uiAbsPartIdx = g_auiZscanToRaster[uiPartIdxRB]
            if self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelX() + g_auiRasterToPelX[uiAbsPartIdx] + self.m_pcPic.getMinCUWidth() >= \
               self.m_pcSlice.getSPS().getPicWidthInLumaSamples(): # image boundary check
                uiLCUIdx = -1
            elif self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelY() + g_auiRasterToPelY[uiAbsPartIdx] + self.m_pcPic.getMinCUHeight() >= \
               self.m_pcSlice.getSPS().getPicHeightInLumaSamples():
                uiLCUIdx = -1
            else:
                if (uiAbsPartIdx % uiNumPartInCUWidth < uiNumPartInCUWidth - 1 and # is not at the last column of LCU
                    uiAbsPartIdx / uiNumPartInCUWidth < self.m_pcPic.getNumPartInHeight() - 1): # is not at the last row of LCU
                    uiAbsPartAddr = g_auiRasterToZscan[uiAbsPartIdx + uiNumPartInCUWidth + 1]
                    uiLCUIdx = self.getAddr()
                elif uiAbsPartIdx % uiNumPartInCUWidth < uiNumPartInCUWidth - 1: # is not at the last column of LCU But is last row of LCU
                    uiAbsPartAddr = g_auiRasterToZscan[(uiAbsPartIdx + uiNumPartInCUWidth + 1) % self.m_pcPic.getNumPartInCU()]
                    uiLCUIdx = -1
                elif uiAbsPartIdx / uiNumPartInCUWidth < self.m_pcPic.getNumPartInHeight() - 1: # is not at the last row of LCU But is last column of LCU
                    uiAbsPartAddr = g_auiRasterToZscan[uiAbsPartIdx + 1]
                    uiLCUIdx = self.getAddr() + 1
                else: #is the right bottom corner of LCU
                    uiAbsPartAddr = 0
                    uiLCUIdx = -1
            ret = 0
            if uiLCUIdx >= 0:
                ret, cColMv, iRefIdx_Col = self.xGetColMVP(eRefPicList, uiLCUIdx, uiAbsPartAddr, cColMv, iRefIdx_Col)
            if uiLCUIdx >= 0 and ret:
                acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
                acMvCand[pInfo.iN].set(cColMv.getHor(), cColMv.getVer())
                pInfo.iN += 1
            else:
                uiPartIdxCenter = 0
                uiCurLCUIdx = self.getAddr()
                uiPartIdxCenter = self.xDeriveCenterIdx(eCUMode, uiPartIdx, uiPartIdxCenter)
                ret, cColMv, iRefIdx_Col = self.xGetColMVP(eRefPicList, uiCurLCUIdx, uiPartIdxCenter, cColMv, iRefIdx_Col)
                if ret:
                    acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
                    acMvCand[pInfo.iN].set(cColMv.getHor(), cColMv.getVer())
                    pInfo.iN += 1
            #---- co-located RightBottom Temporal Predictor ---

        if pInfo.iN > AMVP_MAX_NUM_CANDS:
            pInfo.iN = AMVP_MAX_NUM_CANDS
        while pInfo.iN < AMVP_MAX_NUM_CANDS:
            acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
            acMvCand[pInfo.iN].set(0, 0)
            pInfo.iN += 1

    def setMVPIdx(self, eRefPicList, uiIdx, iMVPIdx):
        self.m_apiMVPIdx[eRefPicList][uiIdx] = iMVPIdx
    def getMVPIdx(self, eRefPicList, uiIdx=None):
        if uiIdx == None:
            return self.m_apiMVPIdx[eRefPicList]
        else:
            return self.m_apiMVPIdx[eRefPicList][uiIdx]
    def setMVPIdxSubParts(self, iMVPIdx, eRefPicList, uiAbsPartIdx, uiPartIdx, uiDepth):
        self.setSubPart(iMVPIdx, self.m_apiMVPIdx[eRefPicList], uiAbsPartIdx, uiDepth, uiPartIdx)

    def setMVPNum(self, eRefPicList, uiIdx, iMVPNum):
        self.m_apiMVPNum[eRefPicList][uiIdx] = iMVPNum
    def getMVPNum(self, eRefPicList, uiIdx=None):
        if uiIdx == None:
            return self.m_apiMVPNum[eRefPicList]
        else:
            return self.m_apiMVPNum[eRefPicList][uiIdx]
    def setMVPNumSubParts(self, iMVPNum, eRefPicList, uiAbsPartIdx, uiPartIdx, uiDepth):
        self.setSubPart(iMVPNum, self.m_apiMVPNum[eRefPicList], uiAbsPartIdx, uiDepth, uiPartIdx)

    def clipMv(self, rcMv):
        iMvShift = 2
        iOffset = 8
        iHorMax = (self.m_pcSlice.getSPS().getPicWidthInLumaSamples() + iOffset - self.m_uiCUPelX - 1) << iMvShift
        iHorMin = (-cvar.g_uiMaxCUWidth - iOffset - self.m_uiCUPelX + 1) << iMvShift

        iVerMax = (self.m_pcSlice.getSPS().getPicHeightInLumaSamples() + iOffset - self.m_uiCUPelY - 1) << iMvShift
        iVerMin = (-cvar.g_uiMaxCUHeight - iOffset - self.m_uiCUPelY + 1) << iMvShift

        rcMv.setHor(min(iHorMax, max(iHorMin, rcMv.getHor())))
        rcMv.setVer(min(iVerMax, max(iVerMin, rcMv.getVer())))
        return rcMv

    def getMvPredLeft(self, rcMvPred):
        rcMvPred = self.m_cMvFieldA.getMv()
        return rcMvPred
    def getMvPredAbove(self, rcMvPred):
        rcMvPred = self.m_cMvFieldB.getMv()
        return rcMvPred
    def getMvPredAboveRight(self, rcMvPred):
        rcMvPred = self.m_cMvFieldC.getMv()
        return rcMvPred

    def compressMV(self):
        scaleFactor = 4 * AMVP_DECIMATION_FACTOR / self.m_unitSize
        if scaleFactor > 0:
            self.m_acCUMvField[0].compress(self.m_pePredMode.cast(), scaleFactor)
            self.m_acCUMvField[1].compress(self.m_pePredMode.cast(), scaleFactor)

    def getCULeft(self):
        return self.m_pcCULeft
    def getCUAbove(self):
        return self.m_pcCUAbove
    def getCUAboveLeft(self):
        return self.m_pcCUAboveLeft
    def getCUAboveRight(self):
        return self.m_pcCUAboveRight
    def getCUColocated(self, eRefPicList):
        return self.m_apcCUColocated[eRefPicList]

    def getPULeft(self, uiLPartUnitIdx, uiCurrPartUnitIdx,
                  bEnforceSliceRestriction=True,
                  bEnforceDependentSliceRestriction=True,
                  bEnforceTileRestriction=True):
        uiAbsPartIdx = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdx = g_auiZscanToRaster[self.m_uiAbsIdxInLCU]
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if not RasterAddress.isZeroCol(uiAbsPartIdx, uiNumPartInCUWidth):
            uiLPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx-1]
            if RasterAddress.isEqualCol(uiAbsPartIdx, uiAbsZorderCUIdx, uiNumPartInCUWidth):
                return self.m_pcPic.getCU(self.getAddr()), uiLPartUnitIdx
            else:
                uiLPartUnitIdx -= self.m_uiAbsIdxInLCU
                return self, uiLPartUnitIdx

        uiLPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx + uiNumPartInCUWidth - 1]

        if (bEnforceSliceRestriction and
            (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
             self.m_pcCULeft.getSCUAddr() + uiLPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx))) or \
           (bEnforceDependentSliceRestriction and
            (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
             self.m_pcCULeft.getSCUAddr() + uiLPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx))) or \
           (bEnforceTileRestriction and
            (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
            return None, uiLPartUnitIdx
        return self.m_pcCULeft, uiLPartUnitIdx

    def getPUAbove(self, uiAPartUnitIdx, uiCurrPartUnitIdx,
                   bEnforceSliceRestriction=True,
                   bEnforceDependentSliceRestriction=True,
                   MotionDataCompression=False,
                   plannarAtLCUBoundary=False,
                   bEnforceTileRestriction=True):
        uiAbsPartIdx = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdx = g_auiZscanToRaster[self.m_uiAbsIdxInLCU]
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if not RasterAddress.isZeroRow(uiAbsPartIdx, uiNumPartInCUWidth):
            uiAPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx - uiNumPartInCUWidth]
            if RasterAddress.isEqualRow(uiAbsPartIdx, uiAbsZorderCUIdx, uiNumPartInCUWidth):
                return self.m_pcPic.getCU(self.getAddr()), uiAPartUnitIdx
            else:
                uiAPartUnitIdx -= self.m_uiAbsIdxInLCU
                return self, uiAPartUnitIdx

        if plannarAtLCUBoundary:
            return None, uiAPartUnitIdx

        uiAPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx + self.m_pcPic.getNumPartInCU() - uiNumPartInCUWidth]
        if MotionDataCompression:
            uiAPartUnitIdx = g_motionRefer[uiAPartUnitIdx]

        if (bEnforceSliceRestriction and
            (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
             self.m_pcCUAbove.getSCUAddr() + uiAPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx))) or \
           (bEnforceDependentSliceRestriction and
            (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
             self.m_pcCUAbove.getSCUAddr() + uiAPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx))) or \
           (bEnforceTileRestriction and
            (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
            return None, uiAPartUnitIdx
        return self.m_pcCUAbove, uiAPartUnitIdx

    def getPUAboveLeft(self, uiALPartUnitIdx, uiCurrPartUnitIdx,
                       bEnforceSliceRestriction=True,
                       bEnforceDependentSliceRestriction=True,
                       MotionDataCompression=False):
        uiAbsPartIdx = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdx = g_auiZscanToRaster[self.m_uiAbsIdxInLCU]
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if not RasterAddress.isZeroCol(uiAbsPartIdx, uiNumPartInCUWidth):
            if not RasterAddress.isZeroRow(uiAbsPartIdx, uiNumPartInCUWidth):
                uiALPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx - uiNumPartInCUWidth - 1]
                if RasterAddress.isEqualRowOrCol(uiAbsPartIdx, uiAbsZorderCUIdx, uiNumPartInCUWidth):
                    return self.m_pcPic.getCU(self.getAddr()), uiALPartUnitIdx
                else:
                    uiALPartUnitIdx -= self.m_uiAbsIdxInLCU
                    return self, uiALPartUnitIdx

            uiALPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx + self.m_pcPic.getNumPartInCU() - uiNumPartInCUWidth - 1]
            if MotionDataCompression:
                uiALPartUnitIdx = g_motionRefer[uiALPartUnitIdx]

            if (bEnforceSliceRestriction and
                (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
                 self.m_pcCUAbove.getSCUAddr() + uiALPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
               (bEnforceDependentSliceRestriction and
                (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
                 self.m_pcCUAbove.getSCUAddr() + uiALPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
                return None, uiALPartUnitIdx
            return self.m_pcCUAbove, uiALPartUnitIdx

        if not RasterAddress.isZeroRow(uiAbsPartIdx, uiNumPartInCUWidth):
            uiALPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdx - 1]
            if (bEnforceSliceRestriction and
                (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
                 self.m_pcCULeft.getSCUAddr() + uiALPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
               (bEnforceDependentSliceRestriction and
                (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
                 self.m_pcCULeft.getSCUAddr() + uiALPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
                return None, uiALPartUnitIdx
            return self.m_pcCULeft, uiALPartUnitIdx

        uiALPartUnitIdx = g_auiRasterToZscan[self.m_pcPic.getNumPartInCU() - 1]
        if MotionDataCompression:
            uiALPartUnitIdx = g_motionRefer[uiALPartUnitIdx]
        if (bEnforceSliceRestriction and
            (self.m_pcCUAboveLeft == None or self.m_pcCUAboveLeft.getSlice() == None or
             self.m_pcCUAboveLeft.getSCUAddr() + uiALPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAboveLeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
           (bEnforceDependentSliceRestriction and
            (self.m_pcCUAboveLeft == None or self.m_pcCUAboveLeft.getSlice() == None or
             self.m_pcCUAboveLeft.getSCUAddr() + uiALPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAboveLeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
            return None, uiALPartUnitIdx
        return self.m_pcCUAboveLeft, uiALPartUnitIdx

    def getPUAboveRight(self, uiARPartUnitIdx, uiCurrPartUnitIdx,
                        bEnforceSliceRestriction=True,
                        bEnforceDependentSliceRestriction=True,
                        MotionDataCompression=False):
        uiAbsPartIdxRT = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdx = g_auiZscanToRaster[self.m_uiAbsIdxInLCU] + self.m_puhWidth[0] / self.m_pcPic.getMinCUWidth() - 1
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelX() + g_auiRasterToPelX[uiAbsPartIdxRT] + self.m_pcPic.getMinCUWidth() >= \
           self.m_pcSlice.getSPS().getPicWidthInLumaSamples():
            uiARPartUnitIdx = MAX_UINT
            return None, uiARPartUnitIdx

        if RasterAddress.lessThanCol(uiAbsPartIdxRT, uiNumPartInCUWidth-1, uiNumPartInCUWidth):
            if not RasterAddress.isZeroRow(uiAbsPartIdxRT, uiNumPartInCUWidth):
                if uiCurrPartUnitIdx > g_auiRasterToZscan[uiAbsPartIdxRT - uiNumPartInCUWidth + 1]:
                    uiARPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxRT - uiNumPartInCUWidth + 1]
                    if RasterAddress.isEqualRowOrCol(uiAbsPartIdxRT, uiAbsZorderCUIdx, uiNumPartInCUWidth):
                        return self.m_pcPic.getCU(self.getAddr()), uiARPartUnitIdx
                    else:
                        uiARPartUnitIdx -= self.m_uiAbsIdxInLCU
                        return self, uiARPartUnitIdx
                uiARPartUnitIdx = MAX_UINT
                return None, uiARPartUnitIdx

            uiARPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxRT + self.m_pcPic.getNumPartInCU() - uiNumPartInCUWidth + 1]
            if MotionDataCompression:
                uiARPartUnitIdx = g_motionRefer[uiARPartUnitIdx]

            if (bEnforceSliceRestriction and
                (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
                 self.m_pcCUAbove.getSCUAddr() + uiARPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
               (bEnforceDependentSliceRestriction and
                (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
                 self.m_pcCUAbove.getSCUAddr() + uiARPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
                return None, uiARPartUnitIdx
            return self.m_pcCUAbove, uiARPartUnitIdx

        if not RasterAddress.isZeroRow(uiAbsPartIdxRT, uiNumPartInCUWidth):
            uiARPartUnitIdx = MAX_UINT
            return None, uiARPartUnitIdx

        uiARPartUnitIdx = g_auiRasterToZscan[self.m_pcPic.getNumPartInCU() - uiNumPartInCUWidth]
        if MotionDataCompression:
            uiARPartUnitIdx = g_motionRefer[uiARPartUnitIdx]
        if (bEnforceSliceRestriction and
            (self.m_pcCUAboveRight == None or self.m_pcCUAboveRight.getSlice() == None or
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.m_pcCUAboveRight.getAddr()) >
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.getAddr()) or
             self.m_pcCUAboveRight.getSCUAddr() + uiARPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAboveRight.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
           (bEnforceDependentSliceRestriction and
            (self.m_pcCUAboveRight == None or self.m_pcCUAboveRight.getSlice() == None or
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.m_pcCUAboveRight.getAddr()) >
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.getAddr()) or
             self.m_pcCUAboveRight.getSCUAddr() + uiARPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAboveRight.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
            return None, uiARPartUnitIdx
        return self.m_pcCUAboveRight, uiARPartUnitIdx

    def getPUBelowLeft(self, uiBLPartUnitIdx, uiCurrPartUnitIdx,
                       bEnforceSliceRestriction=True,
                       bEnforceDependentSliceRestriction=True):
        uiAbsPartIdxLB = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdxLB = g_auiZscanToRaster[self.m_uiAbsIdxInLCU] + \
            (self.m_puhHeight[0] / self.m_pcPic.getMinCUHeight() - 1) * self.m_pcPic.getNumPartInWidth()
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelY() + g_auiRasterToPelY[uiAbsPartIdxLB] + self.m_pcPic.getMinCUHeight() >= \
           self.m_pcSlice.getSPS().getPicHeightInLumaSamples():
            uiBLPartUnitIdx = MAX_UINT
            return None, uiBLPartUnitIdx

        if RasterAddress.lessThanRow(uiAbsPartIdxLB, self.m_pcPic.getNumPartInHeight() - 1, uiNumPartInCUWidth):
            if not RasterAddress.isZeroCol(uiAbsPartIdxLB, uiNumPartInCUWidth):
                if uiCurrPartUnitIdx > g_auiRasterToZscan[uiAbsPartIdxLB + uiNumPartInCUWidth - 1]:
                    uiBLPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxLB + uiNumPartInCUWidth - 1]
                    if RasterAddress.isEqualRowOrCol(uiAbsPartIdxLB, uiAbsZorderCUIdxLB, uiNumPartInCUWidth):
                        return self.m_pcPic.getCU(self.getAddr()), uiBLPartUnitIdx
                    else:
                        uiBLPartUnitIdx -= self.m_uiAbsIdxInLCU
                        return self, uiBLPartUnitIdx
                uiBLPartUnitIdx = MAX_UINT
                return None, uiBLPartUnitIdx

            uiBLPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxLB + uiNumPartInCUWidth * 2 - 1]
            if (bEnforceSliceRestriction and
                (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
                 self.m_pcCULeft.getSCUAddr() + uiBLPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
               (bEnforceDependentSliceRestriction and
                (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
                 self.m_pcCULeft.getSCUAddr() + uiBLPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
                return None, uiBLPartUnitIdx
            return self.m_pcCULeft, uiBLPartUnitIdx

        uiBLPartUnitIdx = MAX_UINT
        return None, uiBLPartUnitIdx

    def getPUBelowLeftAdi(self, uiBLPartUnitIdx, uiPuHeight, uiCurrPartUnitIdx,
                          uiPartUnitOffset=1,
                          bEnforceSliceRestriction=True,
                          bEnforceDependentSliceRestriction=True):
        uiAbsPartIdxLB = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdxLB = g_auiZscanToRaster[self.m_uiAbsIdxInLCU] + \
            (self.m_puhHeight[0] / self.m_pcPic.getMinCUHeight() - 1) * self.m_pcPic.getNumPartInWidth()
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelY() + g_auiRasterToPelY[uiAbsPartIdxLB] + \
           self.m_pcPic.getPicSym().getMinCUHeight() * uiPartUnitOffset >= \
           self.m_pcSlice.getSPS().getPicHeightInLumaSamples():
            uiBLPartUnitIdx = MAX_UINT
            return None, uiBLPartUnitIdx

        if RasterAddress.lessThanRow(uiAbsPartIdxLB, self.m_pcPic.getNumPartInHeight() - uiPartUnitOffset, uiNumPartInCUWidth):
            if not RasterAddress.isZeroCol(uiAbsPartIdxLB, uiNumPartInCUWidth):
                if uiCurrPartUnitIdx > g_auiRasterToZscan[uiAbsPartIdxLB + uiPartUnitOffset * uiNumPartInCUWidth - 1]:
                    uiBLPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxLB + uiPartUnitOffset * uiNumPartInCUWidth - 1]
                    if RasterAddress.isEqualRowOrCol(uiAbsPartIdxLB, uiAbsZorderCUIdxLB, uiNumPartInCUWidth):
                        return self.m_pcPic.getCU(self.getAddr()), uiBLPartUnitIdx
                    else:
                        uiBLPartUnitIdx -= self.m_uiAbsIdxInLCU
                        return self, uiBLPartUnitIdx
                uiBLPartUnitIdx = MAX_UINT
                return None, uiBLPartUnitIdx

            uiBLPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxLB + (1+uiPartUnitOffset) * uiNumPartInCUWidth - 1]
            if (bEnforceSliceRestriction and
                (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
                 self.m_pcCULeft.getSCUAddr() + uiBLPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
               (bEnforceDependentSliceRestriction and
                (self.m_pcCULeft == None or self.m_pcCULeft.getSlice() == None or
                 self.m_pcCULeft.getSCUAddr() + uiBLPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCULeft.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
                return None, uiBLPartUnitIdx
            return self.m_pcCULeft, uiBLPartUnitIdx

        uiBLPartUnitIdx = MAX_UINT
        return None, uiBLPartUnitIdx

    def getPUAboveRightAdi(self, uiARPartUnitIdx, uiPuWidth, uiCurrPartUnitIdx,
                           uiPartUnitOffset=1,
                           bEnforceSliceRestriction=True,
                           bEnforceDependentSliceRestriction=True):
        uiAbsPartIdxRT = g_auiZscanToRaster[uiCurrPartUnitIdx]
        uiAbsZorderCUIdx = g_auiZscanToRaster[self.m_uiAbsIdxInLCU] + self.m_puhWidth[0] / self.m_pcPic.getMinCUWidth() - 1
        uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

        if self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelX() + g_auiRasterToPelX[uiAbsPartIdxRT] + \
           self.m_pcPic.getPicSym().getMinCUHeight() * uiPartUnitOffset >= \
           self.m_pcSlice.getSPS().getPicWidthInLumaSamples():
            uiARPartUnitIdx = MAX_UINT
            return None, uiARPartUnitIdx

        if RasterAddress.lessThanCol(uiAbsPartIdxRT, uiNumPartInCUWidth - uiPartUnitOffset, uiNumPartInCUWidth):
            if not RasterAddress.isZeroRow(uiAbsPartIdxRT, uiNumPartInCUWidth):
                if uiCurrPartUnitIdx > g_auiRasterToZscan[uiAbsPartIdxRT - uiNumPartInCUWidth + uiPartUnitOffset]:
                    uiARPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxRT - uiNumPartInCUWidth + uiPartUnitOffset]
                    if RasterAddress.isEqualRowOrCol(uiAbsPartIdxRT, uiAbsZorderCUIdx, uiNumPartInCUWidth):
                        return self.m_pcPic.getCU(self.getAddr()), uiARPartUnitIdx
                    else:
                        uiARPartUnitIdx -= self.m_uiAbsIdxInLCU
                        return self, uiARPartUnitIdx
                uiARPartUnitIdx = MAX_UINT
                return None, uiARPartUnitIdx

            uiARPartUnitIdx = g_auiRasterToZscan[uiAbsPartIdxRT + self.m_pcPic.getNumPartInCU() - uiNumPartInCUWidth + uiPartUnitOffset]
            if (bEnforceSliceRestriction and
                (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
                 self.m_pcCUAbove.getSCUAddr() + uiARPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
               (bEnforceDependentSliceRestriction and
                (self.m_pcCUAbove == None or self.m_pcCUAbove.getSlice() == None or
                 self.m_pcCUAbove.getSCUAddr() + uiARPartUnitIdx <
                 self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
                 self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAbove.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
                return None, uiARPartUnitIdx
            return self.m_pcCUAbove, uiARPartUnitIdx

        if not RasterAddress.isZeroRow(uiAbsPartIdxRT, uiNumPartInCUWidth):
            uiARPartUnitIdx = MAX_UINT
            return None, uiARPartUnitIdx

        uiARPartUnitIdx = g_auiRasterToZscan[self.m_pcPic.getNumPartInCU() - uiNumPartInCUWidth + uiPartUnitOffset - 1]
        if (bEnforceSliceRestriction and
            (self.m_pcCUAboveRight == None or self.m_pcCUAboveRight.getSlice() == None or
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.m_pcCUAboveRight.getAddr()) >
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.getAddr()) or
             self.m_pcCUAboveRight.getSCUAddr() + uiARPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getSliceStartCU(uiCurrPartUnitIdx) or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAboveRight.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))) or \
           (bEnforceDependentSliceRestriction and
            (self.m_pcCUAboveRight == None or self.m_pcCUAboveRight.getSlice() == None or
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.m_pcCUAboveRight.getAddr()) >
             self.m_pcPic.getPicSym().getInverseCUOrderMap(self.getAddr()) or
             self.m_pcCUAboveRight.getSCUAddr() + uiARPartUnitIdx <
             self.m_pcPic.getCU(self.getAddr()).getDependentSliceStartCU(uiCurrPartUnitIdx) or
             self.m_pcPic.getPicSym().getTileIdxMap(self.m_pcCUAboveRight.getAddr()) != self.m_pcPic.getPicSym().getTileIdxMap(self.getAddr()))):
            return None, uiARPartUnitIdx
        return self.m_pcCUAboveRight, uiARPartUnitIdx

    def getQpMinCuLeft(self, uiLPartUnitIdx, uiCurrAbsIdxInLCU,
                       bEnforceSliceRestriction=True,
                       bEnforceDependentSliceRestriction=True):
        numPartInCUWidth = self.m_pcPic.getNumPartInWidth()
        absZorderQpMinCUIdx = (uiCurrAbsIdxInLCU >> ((cvar.g_uiMaxCUDepth - self.getSlice().getPPS().getMaxCuDQPDepth()) << 1)) << \
                              ((cvar.g_uiMaxCUDepth - self.getSlice().getPPS().getMaxCuDQPDepth()) << 1)
        absRorderQpMinCUIdx = g_auiZscanToRaster[absZorderQpMinCUIdx]

        # check for left LCU boundary
        if RasterAddress.isZeroCol(absRorderQpMinCUIdx, numPartInCUWidth):
            return None, uiLPartUnitIdx

        # get index of left-CU relative to top-left corner of current quantization group
        uiLPartUnitIdx = g_auiRasterToZscan[absRorderQpMinCUIdx - 1]

        # return pointer to current LCU
        return self.m_pcPic.getCU(self.getAddr()), uiLPartUnitIdx

    def getQpMinCuAbove(self, aPartUnitIdx, currAbsIdxInLCU,
                        enforceSliceRestriction=True,
                        enforceDependentSliceRestriction=True):
        numPartInCUWidth = self.m_pcPic.getNumPartInWidth()
        absZorderQpMinCUIdx = (currAbsIdxInLCU >> ((cvar.g_uiMaxCUDepth - self.getSlice().getPPS().getMaxCuDQPDepth()) << 1)) << \
                              ((cvar.g_uiMaxCUDepth - self.getSlice().getPPS().getMaxCuDQPDepth()) << 1)
        absRorderQpMinCUIdx = g_auiZscanToRaster[absZorderQpMinCUIdx]

        # check for top LCU boundary
        if RasterAddress.isZeroRow(absRorderQpMinCUIdx, numPartInCUWidth):
            return None, aPartUnitIdx

        # get index of top-CU relative to top-left corner of current quantization group
        aPartUnitIdx = g_auiRasterToZscan[absRorderQpMinCUIdx - numPartInCUWidth]

        # return pointer to current LCU
        return self.m_pcPic.getCU(self.getAddr()), aPartUnitIdx

    def getRefQP(self, uiCurrAbsIdxInLCU):
        lPartIdx = 0
        aPartIdx = 0
        cULeft, lPartIdx = self.getQpMinCuLeft(lPartIdx, self.m_uiAbsIdxInLCU + uiCurrAbsIdxInLCU)
        cUAbove, aPartIdx = self.getQpMinCuAbove(aPartIdx, self.m_uiAbsIdxInLCU + uiCurrAbsIdxInLCU)
        return ((cULeft.getQP(lPartIdx) if cULeft else self.getLastCodedQP(uiCurrAbsIdxInLCU)) +
                (cUAbove.getQP(aPartIdx) if cUAbove else self.getLastCodedQP(uiCurrAbsIdxInLCU)) + 1) >> 1

    def getLastValidPartIdx(self, iAbsPartIdx):
        iLastValidPartIdx = iAbsPartIdx - 1
        while iLastValidPartIdx >= 0 and \
              self.getPredictionMode(iLastValidPartIdx) == MODE_NONE:
            uiDepth = self.getDepth(iLastValidPartIdx)
            iLastValidPartIdx -= self.m_uiNumPartition >> (uiDepth << 1)
        return iLastValidPartIdx

    def getLastCodedQP(self, uiAbsPartIdx):
        uiQUPartIdxMask = ~((1 << ((cvar.g_uiMaxCUDepth - self.getSlice().getPPS().getMaxCuDQPDepth()) << 1)) - 1)
        iLastValidPartIdx = self.getLastValidPartIdx(uiAbsPartIdx & uiQUPartIdxMask)
        if uiAbsPartIdx < self.m_uiNumPartition and \
           (self.getSCUAddr() + iLastValidPartIdx < self.getSliceStartCU(self.m_uiAbsIdxInLCU + iAbsPartIdx) or
            self.getSCUAddr() + iLastValidPartIdx < self.getDependentSliceStartCU(self.m_uiAbsIdxInLCU + iAbsPartIdx)):
            return self.getSlice().getSliceQp()
        elif iLastValidPartIdx >= 0:
            return self.getQP(iLastValidPartIdx)
        else:
            if self.getZorderIdxInCU() > 0:
                return self.getPic().getCU(self.getAddr()).getLastCodedQP(self.getZorderIdxInCU())
            elif self.getPic().getPicSym().getInverseCUOrderMap(self.getAddr()) > 0 and \
                 self.getPic().getPicSym().getTileIdxMap(self.getAddr()) == \
                 self.getPic().getPicSym().getTileIdxMap(self.getPic().getPicSym().getCUOrderMap(self.getPic().getPicSym().getInverseCUOrderMap(self.getAddr())-1)) and \
                 not (self.getSlice().getPPS().getTilesOrEntropyCodingSyncIdc() == 2 and self.getAddr() % self.getPic().getFrameWidthInCU() == 0):
                return self.getPic().getCU(self.getPic().getPicSym().getCUOrderMap(self.getPic().getPicSym().getInverseCUOrderMap(self.getAddr())-1)).getLastCodedQP(self.getPic().getNumPartInCU())
            else:
                return self.getSlice().getSliceQp()

    def isLosslessCoded(self, absPartIdx):
        return self.getSlice().getPPS().getTransquantBypassEnableFlag() and \
               self.getCUTransquantBypass(absPartIdx)

    def getAllowedChromaDir(self, uiAbsPartIdx, uiModeList):
        uiModeList[0] = PLANAR_IDX
        uiModeList[1] = VER_IDX
        uiModeList[2] = HOR_IDX
        uiModeList[3] = DC_IDX
        uiModeList[4] = DM_CHROMA_IDX

        uiLumaMode = self.getLumaIntraDir(uiAbsPartIdx)

        for i in xrange(NUM_CHROMA_MODE-1):
            if uiLumaMode == uiModeList[i]:
                uiModeList[i] = 34 # VER+8 mode
                break

    def getIntraDirLumaPredictor(self, uiAbsPartIdx, uiIntraDirPred, piMode=None):
        uiTempPartIdx = 0

        bDepSliceRestriction = not self.m_pcSlice.getPPS().getDependentSlicesEnabledFlag()
        pcTempCU, uiTempPartIdx = self.getPULeft(uiTempPartIdx, self.m_uiAbsIdxInLCU + uiAbsPartIdx, True, bDepSliceRestriction)

        iLeftIntraDir = (pcTempCU.getLumaIntraDir(uiTempPartIdx) if pcTempCU.isIntra(uiTempPartIdx) else DC_IDX) \
                        if pcTempCU else DC_IDX

        # Get intra direction of above PU
        pcTempCU, uiTempPartIdx = self.getPUAbove(uiTempPartIdx, self.m_uiAbsIdxInLCU + uiAbsPartIdx, True, bDepSliceRestriction, False, True)

        iAboveIntraDir = (pcTempCU.getLumaIntraDir(uiTempPartIdx) if pcTempCU.isIntra(uiTempPartIdx) else DC_IDX) \
                         if pcTempCU else DC_IDX

        uiPredNum = 3
        if iLeftIntraDir == iAboveIntraDir:
            if piMode:
                piMode[0] = 1

            if iLeftIntraDir > 1: # angular modes
                uiIntraDirPred[0] = iLeftIntraDir
                uiIntraDirPred[1] = ((iLeftIntraDir + 29) % 32) + 2
                uiIntraDirPred[2] = ((iLeftIntraDir - 1) % 32) + 2
            else: # non-angular
                uiIntraDirPred[0] = PLANAR_IDX
                uiIntraDirPred[1] = DC_IDX
                uiIntraDirPred[2] = VER_IDX
        else:
            if piMode:
                piMode[0] = 2
            uiIntraDirPred[0] = iLeftIntraDir
            uiIntraDirPred[1] = iAboveIntraDir

            if iLeftIntraDir and iAboveIntraDir: #both modes are non-planar
                uiIntraDirPred[2] = PLANAR_IDX
            else:
                uiIntraDirPred[2] = VER_IDX if iLeftIntraDir+iAboveIntraDir < 2 else DC_IDX

        return uiPredNum

    def getCtxSplitFlag(self, uiAbsPartIdx, uiDepth):
        uiTempPartIdx = 0

        # Get left split flag
        bDepSliceRestriction = not self.m_pcSlice.getPPS().getDependentSlicesEnabledFlag()
        pcTempCU, uiTempPartIdx = self.getPULeft(uiTempPartIdx, self.m_uiAbsIdxInLCU + uiAbsPartIdx, True, bDepSliceRestriction)
        uiCtx = (1 if pcTempCU.getDepth(uiTempPartIdx) > uiDepth else 0) if pcTempCU else 0

        # Get above split flag
        pcTempCU, uiTempPartIdx = self.getPUAbove(uiTempPartIdx, self.m_uiAbsIdxInLCU + uiAbsPartIdx, True, bDepSliceRestriction)
        uiCtx += (1 if pcTempCU.getDepth(uiTempPartIdx) > uiDepth else 0) if pcTempCU else 0

        return uiCtx

    def getCtxQtCbf(self, uiAbsPartIdx, eType, uiTrDepth):
        if eType:
            return uiTrDepth
        else:
            uiCtx = 1 if uiTrDepth == 0 else 0
            return uiCtx

    def getQuadtreeTULog2MinSizeInCU(self, absPartIdx):
        log2CbSize = g_aucConvertToBit[self.getWidth(absPartIdx)] + 2
        partSize = self.getPartitionSize(absPartIdx)
        quadtreeTUMaxDepth = self.m_pcSlice.getSPS().getQuadtreeTUMaxDepthIntra() \
                             if self.getPredictionMode(absPartIdx) == MODE_INTRA else \
                             self.m_pcSlice.getSPS().getQuadtreeTUMaxDepthInter()
        intraSplitFlag = 1 if (self.getPredictionMode(absPartIdx) == MODE_INTRA and partSize == SIZE_NxN) else 0
        interSplitFlag = 1 if quadtreeTUMaxDepth == 1 and self.getPredictionMode(absPartIdx) == MODE_INTER and partSize != SIZE_2Nx2N else 0

        log2MinTUSizeInCU = 0
        if log2CbSize < self.m_pcSlice.getSPS().getQuadtreeTULog2MinSize() + quadtreeTUMaxDepth - 1 + interSplitFlag + intraSplitFlag:
            # when fully making use of signaled TUMaxDepth + inter/intraSplitFlag, resulting luma TB size is < QuadtreeTULog2MinSize
            log2MinTUSizeInCU = self.m_pcSlice.getSPS().getQuadtreeTULog2MinSize()
        else:
            # when fully making use of signaled TUMaxDepth + inter/intraSplitFlag, resulting luma TB size is still >= QuadtreeTULog2MinSize
            log2MinTUSizeInCU = log2CbSize - (quadtreeTUMaxDepth - 1 + interSplitFlag + intraSplitFlag) # stop when trafoDepth == hierarchy_depth = splitFlag
            if log2MinTUSizeInCU > self.m_pcSlice.getSPS().getQuadtreeTULog2MaxSize():
                # when fully making use of signaled TUMaxDepth + inter/intraSplitFlag, resulting luma TB size is still > QuadtreeTULog2MaxSize
                log2MinTUSizeInCU = self.m_pcSlice.getSPS().getQuadtreeTULog2MaxSize()
        return log2MinTUSizeInCU

    def getCtxSkipFlag(self, uiAbsPartIdx):
        uiTempPartIdx = 0

        # Get BCBP of left PU
        bDepSliceRestriction = not self.m_pcSlice.getPPS().getDependentSlicesEnabledFlag()
        pcTempCU, uiTempPartIdx = self.getPULeft(uiTempPartIdx, self.m_uiAbsIdxInLCU + uiAbsPartIdx, True, bDepSliceRestriction)
        uiCtx = pcTempCU.isSkipped(uiTempPartIdx) if pcTempCU else 0

        # Get BCBP of above PU
        pcTempCU, uiTempPartIdx = self.getPUAbove(uiTempPartIdx, self.m_uiAbsIdxInLCU + uiAbsPartIdx, True, bDepSliceRestriction)
        uiCtx += pcTempCU.isSkipped(uiTempPartIdx) if pcTempCU else 0

        return uiCtx

    def getCtxInterDir(self, uiAbsPartIdx):
        return self.getDepth(uiAbsPartIdx)

    def isFirstAbsZorderIdxInDepth(self, uiAbsPartIdx, uiDepth):
        uiPartNumb = self.m_pcPic.getNumPartInCU() >> (uiDepth << 1)
        return (self.m_uiAbsIdxInLCU + uiAbsPartIdx) % uiPartNumb == 0

    def deriveLeftRightTopIdxGeneral(self, eCUMode, uiAbsPartIdx, uiPartIdx, ruiPartIdxLT, ruiPartIdxRT):
        ruiPartIdxLT = self.m_uiAbsIdxInLCU + uiAbsPartIdx
        uiPuWidth = 0

        if self.m_pePartSize[uiAbsPartIdx] == SIZE_2Nx2N:
            uiPuWidth = self.m_puhWidth[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_2NxN:
            uiPuWidth = self.m_puhWidth[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_Nx2N:
            uiPuWidth = self.m_puhWidth[uiAbsPartIdx] >> 1
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_NxN:
            uiPuWidth = self.m_puhWidth[uiAbsPartIdx] >> 1
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_2NxnU:
            uiPuWidth = self.m_puhWidth[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_2NxnD:
            uiPuWidth = self.m_puhWidth[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_nLx2N:
            if uiPartIdx == 0:
                uiPuWidth = self.m_puhWidth[uiAbsPartIdx] >> 2
            elif uiPartIdx == 1:
                uiPuWidth = (self.m_puhWidth[uiAbsPartIdx]>>1) + (self.m_puhWidth[uiAbsPartIdx]>>2)
            else:
                assert(False)
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_nRx2N:
            if uiPartIdx == 0:
                uiPuWidth = (self.m_puhWidth[uiAbsPartIdx]>>1) + (self.m_puhWidth[uiAbsPartIdx]>>2)
            elif uiPartIdx == 1:
                uiPuWidth = self.m_puhWidth[uiAbsPartIdx] >> 2
            else:
                assert(False)
        else:
            assert(False)

        ruiPartIdxRT = g_auiRasterToZscan[g_auiZscanToRaster[ruiPartIdxLT] + uiPuWidth / self.m_pcPic.getMinCUWidth() - 1]
        return ruiPartIdxLT, ruiPartIdxRT

    def deriveLeftBottomIdxGeneral(self, eCUMode, uiAbsPartIdx, uiPartIdx, ruiPartIdxLB):
        uiPUHeight = 0

        if self.m_pePartSize[uiAbsPartIdx] == SIZE_2Nx2N:
            uiPUHeight = self.m_puhHeight[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_2NxN:
            uiPUHeight = self.m_puhHeight[uiAbsPartIdx] >> 1
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_Nx2N:
            uiPUHeight = self.m_puhHeight[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_NxN:
            uiPUHeight = self.m_puhHeight[uiAbsPartIdx] >> 1
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_2NxnU:
            if uiPartIdx == 0:
                uiPUHeight = self.m_puhHeight[uiAbsPartIdx] >> 2
            elif uiPartIdx == 1:
                uiPUHeight = (self.m_puhHeight[uiAbsPartIdx]>>1) + (self.m_puhHeight[uiAbsPartIdx]>>2)
            else:
                assert(False)
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_2NxnD:
            if uiPartIdx == 0:
                uiPUHeight = (self.m_puhHeight[uiAbsPartIdx]>>1) + (self.m_puhHeight[uiAbsPartIdx]>>2)
            elif uiPartIdx == 1:
                uiPUHeight = self.m_puhHeight[uiAbsPartIdx] >> 2
            else:
                assert(False)
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_nLx2N:
            uiPUHeight = self.m_puhHeight[uiAbsPartIdx]
        elif self.m_pePartSize[uiAbsPartIdx] == SIZE_nRx2N:
            uiPUHeight = self.m_puhHeight[uiAbsPartIdx]
        else:
            assert(False)

        ruiPartIdxLB = g_auiRasterToZscan[g_auiZscanToRaster[self.m_uiAbsIdxInLCU + uiAbsPartIdx] + (uiPUHeight/self.m_pcPic.getMinCUHeight()-1) * self.m_pcPic.getNumPartInWidth()]
        return ruiPartIdxLB

    def deriveLeftRightTopIdx(self, eCUMode, uiPartIdx, ruiPartIdxLT, ruiPartIdxRT):
        ruiPartIdxLT = self.m_uiAbsIdxInLCU
        ruiPartIdxRT = g_auiRasterToZscan[g_auiZscanToRaster[ruiPartIdxLT] + self.m_puhWidth[0] / self.m_pcPic.getMinCUWidth() - 1]

        if self.m_pePartSize[0] == SIZE_2Nx2N or self.m_pePartSize[0] == SIZE_2NxN:
            ruiPartIdxLT += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 1
            ruiPartIdxRT += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_Nx2N:
            ruiPartIdxLT += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 2
            ruiPartIdxRT -= 0 if uiPartIdx == 1 else self.m_uiNumPartition >> 2
        elif self.m_pePartSize[0] == SIZE_NxN:
            ruiPartIdxLT += (self.m_uiNumPartition >> 2) * uiPartIdx
            ruiPartIdxRT += (self.m_uiNumPartition >> 2) * (uiPartIdx - 1)
        elif self.m_pePartSize[0] == SIZE_2NxnU:
            ruiPartIdxLT += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 3
            ruiPartIdxRT += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 3
        elif self.m_pePartSize[0] == SIZE_2NxnD:
            ruiPartIdxLT += 0 if uiPartIdx == 0 else (self.m_uiNumPartition>>1) + (self.m_uiNumPartition>>3)
            ruiPartIdxRT += 0 if uiPartIdx == 0 else (self.m_uiNumPartition>>1) + (self.m_uiNumPartition>>3)
        elif self.m_pePartSize[0] == SIZE_nLx2N:
            ruiPartIdxLT += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 4
            ruiPartIdxRT -= 0 if uiPartIdx == 1 else (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>4)
        elif self.m_pePartSize[0] == SIZE_nRx2N:
            ruiPartIdxLT += 0 if uiPartIdx == 0 else (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>4)
            ruiPartIdxRT -= 0 if uiPartIdx == 1 else self.m_uiNumPartition >> 4
        else:
            assert(False)

        return ruiPartIdxLT, ruiPartIdxRT

    def deriveLeftBottomIdx(self, eCUMode, uiPartIdx, ruiPartIdxLB):
        ruiPartIdxLB = g_auiRasterToZscan[g_auiZscanToRaster[self.m_uiAbsIdxInLCU] + (((self.m_puhHeight[0] / self.m_pcPic.getMinCUHeight()) >> 1) - 1) * self.m_pcPic.getNumPartInWidth()]

        if self.m_pePartSize[0] == SIZE_2Nx2N:
            ruiPartIdxLB += self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_2NxN:
            ruiPartIdxLB += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_Nx2N:
            ruiPartIdxLB += self.m_uiNumPartition >> 1 if uiPartIdx == 0 else (self.m_uiNumPartition >> 2) * 3
        elif self.m_pePartSize[0] == SIZE_NxN:
            ruiPartIdxLB += (self.m_uiNumPartition >> 2) * uiPartIdx
        elif self.m_pePartSize[0] == SIZE_2NxnU:
            ruiPartIdxLB += -(self.m_uiNumPartition >> 3) if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_2NxnD:
            ruiPartIdxLB += (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>3) if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_nLx2N:
            ruiPartIdxLB += self.m_uiNumPartition >> 1 if uiPartIdx == 0 else (self.m_uiNumPartition>>1) + (self.m_uiNumPartition>>4)
        elif self.m_pePartSize[0] == SIZE_nRx2N:
            ruiPartIdxLB += self.m_uiNumPartition >> 1 if uiPartIdx == 0 else (self.m_uiNumPartition>>1) + (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>4)
        else:
            assert(False)

        return ruiPartIdxLB

    def deriveRightBottomIdx(self, eCUMode, uiPartIdx, ruiPartIdxRB):
        ruiPartIdxRB = g_auiRasterToZscan[g_auiZscanToRaster[self.m_uiAbsIdxInLCU] + (((self.m_puhHeight[0] / self.m_pcPic.getMinCUHeight()) >> 1) - 1) * self.m_pcPic.getNumPartInWidth() + self.m_puhWidth[0] / self.m_pcPic.getMinCUWidth() - 1]

        if self.m_pePartSize[0] == SIZE_2Nx2N:
            ruiPartIdxRB += self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_2NxN:
            ruiPartIdxRB += 0 if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_Nx2N:
            ruiPartIdxRB += self.m_uiNumPartition >> 2 if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_NxN:
            ruiPartIdxRB += (self.m_uiNumPartition >> 2) * (uiPartIdx - 1)
        elif self.m_pePartSize[0] == SIZE_2NxnU:
            ruiPartIdxRB += -(self.m_uiNumPartition >> 3) if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_2NxnD:
            ruiPartIdxRB += (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>3) if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_nLx2N:
            ruiPartIdxRB += (self.m_uiNumPartition>>3) + (self.m_uiNumPartition>>4) if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        elif self.m_pePartSize[0] == SIZE_nRx2N:
            ruiPartIdxRB += (self.m_uiNumPartition>>2) + (self.m_uiNumPartition>>3) + (self.m_uiNumPartition>>4) if uiPartIdx == 0 else self.m_uiNumPartition >> 1
        else:
            assert(False)

        return ruiPartIdxRB

    def deriveLeftRightTopIdxAdi(self, ruiPartIdxLT, ruiPartIdxRT, uiPartOffset, uiPartDepth):
        uiNumPartInCUWidth = (self.m_puhWidth[0] / self.m_pcPic.getMinCUWidth()) >> uiPartDepth
        ruiPartIdxLT = self.m_uiAbsIdxInLCU + uiPartOffset
        ruiPartIdxRT = g_auiRasterToZscan[g_auiZscanToRaster[ruiPartIdxLT] + uiNumPartInCUWidth - 1]

        return ruiPartIdxLT, ruiPartIdxRT

    def deriveLeftBottomIdxAdi(self, ruiPartIdxLB, uiPartOffset, uiPartDepth):
        uiMinCuWidth = self.getPic().getMinCUWidth()
        uiWidthInMinCus = (self.getWidth(0) / uiMinCuWidth) >> uiPartDepth
        uiAbsIdx = self.getZorderIdxInCU() + uiPartOffset + (self.m_uiNumPartition >> (uiPartDepth<<1)) - 1
        uiAbsIdx = g_auiZscanToRaster[uiAbsIdx] - (uiWidthInMinCus - 1)
        ruiPartIdxLB = g_auiRasterToZscan[uiAbsIdx]

        return ruiPartIdxLB

    def hasEqualMotion(self, uiAbsPartIdx, pcCandCU, uiCandAbsPartIdx):
        if self.getInterDir(uiAbsPartIdx) != pcCandCU.getInterDir(uiCandAbsPartIdx):
            return False

        for uiRefListIdx in xrange(2):
            if self.getInterDir(uiAbsPartIdx) & (1 << uiRefListIdx):
                if self.getCUMvField(uiRefListIdx).getMv(uiAbsPartIdx) != \
                   pcCandCU.getCUMvField(uiRefListIdx).getMv(uiCandAbsPartIdx) or \
                   self.getCUMvField(uiRefListIdx).getRefIdx(uiAbsPartIdx) != \
                   pcCandCU.getCUMvField(uiRefListIdx).getRefIdx(uiCandAbsPartIdx):
                    return False

        return True

    def getInterMergeCandidates(self, uiAbsPartIdx, uiPUIdx, uiDepth,
                                pcMvFieldNeighbours, puhInterDirNeighbours,
                                numValidMergeCand, mrgCandIdx=-1):
        pcMvFieldNeighbours = pointer(pcMvFieldNeighbours, type='TComMvField *')
        puhInterDirNeighbours = pointer(puhInterDirNeighbours, type='uchar *')

        uiAbsPartAddr = self.m_uiAbsIdxInLCU + uiAbsPartIdx
        uiIdx = 1
        abCandIsInter = MRG_MAX_NUM_CANDS * [False]
        # compute the location of the current PU
        xP = yP = nPSW = nPSH = 0
        xP, yP, nPSW, nPSH = self.getPartPosition(uiPUIdx, xP, yP, nPSW, nPSH)

        iCount = 0

        uiPartIdxLT = uiPartIdxRT = uiPartIdxLB = 0
        cCurPS = self.getPartitionSize(uiAbsPartIdx)
        uiPartIdxLT, uiPartIdxRT = self.deriveLeftRightTopIdxGeneral(cCurPS, uiAbsPartIdx, uiPUIdx, uiPartIdxLT, uiPartIdxRT)
        uiPartIdxLB = self.deriveLeftBottomIdxGeneral(cCurPS, uiAbsPartIdx, uiPUIdx, uiPartIdxLB)

        # left
        uiLeftPartIdx = 0
        pcCULeft, uiLeftPartIdx = self.getPULeft(uiLeftPartIdx, uiPartIdxLB, True, False)
        if pcCULeft:
            if not pcCULeft.isDiffMER(xP-1, yP+nPSH-1, xP, yP):
                pcCULeft = None
        partSize = self.getPartitionSize(uiAbsPartIdx)
        if not (uiPUIdx == 1 and (partSize == SIZE_Nx2N or partSize == SIZE_nLx2N or partSize == SIZE_nRx2N)):
            if pcCULeft and not pcCULeft.isIntra(uiLeftPartIdx):
                abCandIsInter[iCount] = True
                # get Inter Dir
                puhInterDirNeighbours[iCount] = pcCULeft.getInterDir(uiLeftPartIdx)
                # get Mv from Left
                pcCULeft.getMvField(pcCULeft, uiLeftPartIdx, REF_PIC_LIST_0, pcMvFieldNeighbours[iCount<<1])
                if self.getSlice().isInterB():
                    pcCULeft.getMvField(pcCULeft, uiLeftPartIdx, REF_PIC_LIST_1, pcMvFieldNeighbours[(iCount<<1)+1])
                if mrgCandIdx == iCount:
                    return numValidMergeCand
                iCount += 1

        # above
        uiAbovePartIdx = 0
        pcCUAbove, uiAbovePartIdx = self.getPUAbove(uiAbovePartIdx, uiPartIdxRT, True, False, True)
        if pcCUAbove:
            if not pcCUAbove.isDiffMER(xP+nPSW-1, yP-1, xP, yP):
                pcCUAbove = None
        if pcCUAbove and not pcCUAbove.isIntra(uiAbovePartIdx) and \
           not (uiPUIdx == 1 and (cCurPS == SIZE_2NxN or cCurPS == SIZE_2NxnU or cCurPS == SIZE_2NxnD)) and \
           (not pcCULeft or pcCULeft.isIntra(uiLeftPartIdx) or not pcCULeft.hasEqualMotion(uiLeftPartIdx, pcCUAbove, uiAbovePartIdx)):
            abCandIsInter[iCount] = True
            # get Inter Dir
            puhInterDirNeighbours[iCount] = pcCUAbove.getInterDir(uiAbovePartIdx)
            # get Mv From Left
            pcCUAbove.getMvField(pcCUAbove, uiAbovePartIdx, REF_PIC_LIST_0, pcMvFieldNeighbours[iCount<<1])
            if self.getSlice().isInterB():
                pcCUAbove.getMvField(pcCUAbove, uiAbovePartIdx, REF_PIC_LIST_1, pcMvFieldNeighbours[(iCount<<1)+1])
            if mrgCandIdx == iCount:
                return numValidMergeCand
            iCount += 1

        # above right
        uiAboveRightPartIdx = 0
        pcCUAboveRight, uiAboveRightPartIdx = self.getPUAboveRight(uiAboveRightPartIdx, uiPartIdxRT, True, False, True)
        if pcCUAboveRight:
            if not pcCUAboveRight.isDiffMER(xP+nPSW, yP-1, xP, yP):
                pcCUAboveRight = None
        if pcCUAboveRight and not pcCUAboveRight.isIntra(uiAboveRightPartIdx) and \
           (not pcCUAbove or pcCUAbove.isIntra(uiAbovePartIdx) or not pcCUAbove.hasEqualMotion(uiAbovePartIdx, pcCUAboveRight, uiAboveRightPartIdx)):
            abCandIsInter[iCount] = True
            # get Inter Dir
            puhInterDirNeighbours[iCount] = pcCUAboveRight.getInterDir(uiAboveRightPartIdx)
            # get Mv From Left
            pcCUAboveRight.getMvField(pcCUAboveRight, uiAboveRightPartIdx, REF_PIC_LIST_0, pcMvFieldNeighbours[iCount<<1])
            if self.getSlice().isInterB():
                pcCUAboveRight.getMvField(pcCUAboveRight, uiAboveRightPartIdx, REF_PIC_LIST_1, pcMvFieldNeighbours[(iCount<<1)+1])
            if mrgCandIdx == iCount:
                return numValidMergeCand
            iCount += 1

        # left bottom
        uiLeftBottomPartIdx = 0
        pcCULeftBottom, uiLeftBottomPartIdx = self.getPUBelowLeft(uiLeftBottomPartIdx, uiPartIdxLB, True, False)
        if pcCULeftBottom:
            if not pcCULeftBottom.isDiffMER(xP-1, yP+nPSH, xP, yP):
                pcCULeftBottom = None
        if pcCULeftBottom and not pcCULeftBottom.isIntra(uiLeftBottomPartIdx) and \
           (not pcCULeft or pcCULeft.isIntra(uiLeftPartIdx) or not pcCULeft.hasEqualMotion(uiLeftPartIdx, pcCULeftBottom, uiLeftBottomPartIdx)):
            abCandIsInter[iCount] = True
            # get Inter Dir
            puhInterDirNeighbours[iCount] = pcCULeftBottom.getInterDir(uiLeftBottomPartIdx)
            # get Mv From Left
            pcCULeftBottom.getMvField(pcCULeftBottom, uiLeftBottomPartIdx, REF_PIC_LIST_0, pcMvFieldNeighbours[iCount<<1])
            if self.getSlice().isInterB():
                pcCULeftBottom.getMvField(pcCULeftBottom, uiLeftBottomPartIdx, REF_PIC_LIST_1, pcMvFieldNeighbours[(iCount<<1)+1])
            if mrgCandIdx == iCount:
                return numValidMergeCand
            iCount += 1

        # above left
        if iCount < 4:
            uiAboveLeftPartIdx = 0
            pcCUAboveLeft, uiAboveLeftPartIdx = self.getPUAboveLeft(uiAboveLeftPartIdx, uiAbsPartAddr, True, False, True)
            if pcCUAboveLeft:
                if not pcCUAboveLeft.isDiffMER(xP-1, yP-1, xP, yP):
                    pcCUAboveLeft = None
            if pcCUAboveLeft and not pcCUAboveLeft.isIntra(uiAboveLeftPartIdx) and \
               (not pcCULeft or pcCULeft.isIntra(uiLeftPartIdx) or not pcCULeft.hasEqualMotion(uiLeftPartIdx, pcCUAboveLeft, uiAboveLeftPartIdx)) and \
               (not pcCUAbove or pcCUAbove.isIntra(uiAbovePartIdx) or not pcCUAbove.hasEqualMotion(uiAbovePartIdx, pcCUAboveLeft, uiAboveLeftPartIdx)):
                abCandIsInter[iCount] = True
                # get Inter Dir
                puhInterDirNeighbours[iCount] = pcCUAboveLeft.getInterDir(uiAboveLeftPartIdx)
                # get Mv From Left
                pcCUAboveLeft.getMvField(pcCUAboveLeft, uiAboveLeftPartIdx, REF_PIC_LIST_0, pcMvFieldNeighbours[iCount<<1])
                if self.getSlice().isInterB():
                    pcCUAboveLeft.getMvField(pcCUAboveLeft, uiAboveLeftPartIdx, REF_PIC_LIST_1, pcMvFieldNeighbours[(iCount<<1)+1])
                if mrgCandIdx == iCount:
                    return numValidMergeCand
                iCount += 1

        if self.getSlice().getEnableTMVPFlag():
            # MTK colocated-RightBottom
            uiPartIdxRB = 0
            uiLCUIdx = self.getAddr()
            eCUMode = self.getPartitionSize(0)

            uiPartIdxRB = self.deriveRightBottomIdx(eCUMode, uiPUIdx, uiPartIdxRB)

            uiAbsPartIdxTmp = g_auiZscanToRaster[uiPartIdxRB]
            uiNumPartInCUWidth = self.m_pcPic.getNumPartInWidth()

            if self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelX() + g_auiRasterToPelX[uiAbsPartIdxTmp] + self.m_pcPic.getMinCUWidth() >= \
               self.m_pcSlice.getSPS().getPicWidthInLumaSamples(): # image boundary check
                uiLCUIdx = -1
            elif self.m_pcPic.getCU(self.m_uiCUAddr).getCUPelY() + g_auiRasterToPelY[uiAbsPartIdxTmp] + self.m_pcPic.getMinCUHeight() >= \
                 self.m_pcSlice.getSPS().getPicHeightInLumaSamples():
                uiLCUIdx = -1
            else:
                # is not at the last column of LCU
                if uiAbsPartIdxTmp % uiNumPartInCUWidth < uiNumPartInCUWidth - 1 and \
                   uiAbsPartIdxTmp / uiNumPartInCUWidth < self.m_pcPic.getNumPartInHeight() - 1:
                   # is not at the last row of LCU
                    uiAbsPartAddr = g_auiRasterToZscan[uiAbsPartIdxTmp + uiNumPartInCUWidth + 1]
                    uiLCUIdx = self.getAddr()
                elif uiAbsPartIdxTmp % uiNumPartInCUWidth < uiNumPartInCUWidth - 1:
                     # is not at the last column of LCU But is last row of LCU
                    uiAbsPartAddr = g_auiRasterToZscan[(uiAbsPartIdxTmp + uiNumPartInCUWidth + 1) % self.m_pcPic.getNumPartInCU()]
                    uiLCUIdx = -1
                elif uiAbsPartIdxTmp / uiNumPartInCUWidth < self.m_pcPic.getNumPartInHeight() - 1:                    
                     # is not at the last row of LCU But is last column of LCU
                    uiAbsPartAddr = g_auiRasterToZscan[uiAbsPartIdxTmp + 1]
                    uiLCUIdx = self.getAddr() + 1
                else: # is the right bottom corner of LCU
                    uiAbsPartAddr = 0
                    uiLCUIdx = -1
            iRefIdx = 0
            cColMv = TComMv()

            bExistMV = False
            uiPartIdxCenter = 0
            uiCurLCUIdx = self.getAddr()
            uiPartIdxCenter = self.xDeriveCenterIdx(eCUMode, uiPUIdx, uiPartIdxCenter)
            if uiLCUIdx >= 0:
                ret, cColMv, iRefIdx = self.xGetColMVP(REF_PIC_LIST_0, uiLCUIdx, uiAbsPartAddr, cColMv, iRefIdx)
                bExistMV = uiLCUIdx >= 0 and ret
            if bExistMV == False:
                ret, cColMv, iRefIdx = self.xGetColMVP(REF_PIC_LIST_0, uiCurLCUIdx, uiPartIdxCenter, cColMv, iRefIdx)
                bExistMV = ret
            if bExistMV:
                uiArrayAddr = iCount
                abCandIsInter[uiArrayAddr] = True
                pcMvFieldNeighbours[uiArrayAddr<<1].setMvField(cColMv, iRefIdx)

                if self.getSlice().isInterB():
                    iRefIdx = 0
                    if uiLCUIdx >= 0:
                        ret, cColMv, iRefIdx = self.xGetColMVP(REF_PIC_LIST_1, uiLCUIdx, uiAbsPartAddr, cColMv, iRefIdx)
                        bExistMV = uiLCUIdx >= 0 and ret
                    if bExistMV == False:
                        ret, cColMv, iRefIdx = self.xGetColMVP(REF_PIC_LIST_1, uiCurLCUIdx, uiPartIdxCenter, cColMv, iRefIdx)
                        bExistMV = ret
                    if bExistMV:
                        pcMvFieldNeighbours[(uiArrayAddr<<1)+1].setMvField(cColMv, iRefIdx)
                        puhInterDirNeighbours[uiArrayAddr] = 3
                    else:
                        puhInterDirNeighbours[uiArrayAddr] = 1
                else:
                    puhInterDirNeighbours[uiArrayAddr] = 1
                if mrgCandIdx == iCount:
                    return numValidMergeCand
                iCount += 1
            uiIdx += 1

        uiArrayAddr = iCount
        uiCutoff = uiArrayAddr

        if self.getSlice().isInterB():
            uiPriorityList0 = (0, 1, 0, 2, 1, 2, 0, 3, 1, 3, 2, 3)
            uiPriorityList1 = (1, 0, 2, 0, 2, 1, 3, 0, 3, 1, 3, 2)

            for idx in xrange(uiCutoff * (uiCutoff-1)):
                if uiArrayAddr == MRG_MAX_NUM_CANDS:
                    break

                i = uiPriorityList0[idx]
                j = uiPriorityList1[idx]
                if abCandIsInter[i] and puhInterDirNeighbours[i] & 0x1 and \
                   abCandIsInter[j] and puhInterDirNeighbours[j] & 0x2:
                    abCandIsInter[uiArrayAddr] = True
                    puhInterDirNeighbours[uiArrayAddr] = 3

                    # get Mv from cand[i] and cand[j]
                    pcMvFieldNeighbours[uiArrayAddr<<1].setMvField(
                        pcMvFieldNeighbours[i<<1].getMv(), pcMvFieldNeighbours[i<<1].getRefIdx())
                    pcMvFieldNeighbours[(uiArrayAddr<<1)+1].setMvField(
                        pcMvFieldNeighbours[(j<<1)+1].getMv(), pcMvFieldNeighbours[(j<<1)+1].getRefIdx())

                    iRefPOCL0 = self.m_pcSlice.getRefPOC(REF_PIC_LIST_0, pcMvFieldNeighbours[uiArrayAddr<<1].getRefIdx())
                    iRefPOCL1 = self.m_pcSlice.getRefPOC(REF_PIC_LIST_1, pcMvFieldNeighbours[(uiArrayAddr<<1)+1].getRefIdx())
                    if iRefPOCL0 == iRefPOCL1 and \
                       pcMvFieldNeighbours[uiArrayAddr<<1].getMv() == pcMvFieldNeighbours[(uiArrayAddr<<1)+1].getMv():
                        abCandIsInter[uiArrayAddr] = False
                    else:
                        uiArrayAddr += 1

        iNumRefIdx = min(self.m_pcSlice.getNumRefIdx(REF_PIC_LIST_0), self.m_pcSlice.getNumRefIdx(REF_PIC_LIST_1)) \
                     if self.getSlice().isInterB() else self.m_pcSlice.getNumRefIdx(REF_PIC_LIST_0)
        r = 0
        refcnt = 0
        while uiArrayAddr < MRG_MAX_NUM_CANDS:
            abCandIsInter[uiArrayAddr] = True
            puhInterDirNeighbours[uiArrayAddr] = 1
            pcMvFieldNeighbours[uiArrayAddr<<1].setMvField(TComMv(0, 0), r)

            if self.getSlice().isInterB():
                puhInterDirNeighbours[uiArrayAddr] = 3
                pcMvFieldNeighbours[(uiArrayAddr<<1)+1].setMvField(TComMv(0, 0), r)
            uiArrayAddr += 1
            if refcnt == iNumRefIdx-1:
                r = 0
            else:
                r += 1
                refcnt += 1
        if uiArrayAddr > MRG_MAX_NUM_CANDS_SIGNALED:
            uiArrayAddr = MRG_MAX_NUM_CANDS_SIGNALED
        numValidMergeCand = uiArrayAddr

        return numValidMergeCand

    def isIntra(self, uiPartIdx):
        return self.m_pePredMode[uiPartIdx] == MODE_INTRA
    def isSkipped(self, uiPartIdx):
        return self.getSkipFlag(uiPartIdx)

    def isBipredRestriction(self, puIdx):
        width = height = partAddr = 0
        partAddr, width, height = self.getPartIndexAndSize(puIdx, partAddr, width, height)
        if self.getWidth(0) == 8 and (width < 8 or height < 8):
            return True
        return False

    def getIntraSizeIdx(self, uiAbsPartIdx):
        uiShift = self.m_puhTrIdx[uiAbsPartIdx] + 1 \
            if self.m_puhTrIdx[uiAbsPartIdx] == 0 and self.m_pePartSize[uiAbsPartIdx] == SIZE_NxN else \
            self.m_puhTrIdx[uiAbsPartIdx]
        uiShift = 1 if self.m_pePartSize[uiAbsPartIdx] == SIZE_NxN else 0

        uiWidth = self.m_puhWidth[uiAbsPartIdx] >> uiShift
        uiCnt = 0
        while uiWidth:
            uiCnt += 1
            uiWidth >>= 1
        uiCnt -= 2
        return 6 if uiCnt > 6 else uiCnt

    def convertTransIdx(self, uiAbsPartIdx, uiTrIdx, ruiLumaTrMode, ruiChromaTrMode):
        ruiLumaTrMode = uiTrIdx
        ruiChromaTrMode = uiTrIdx
        return ruiLumaTrMode, ruiChromaTrMode

    def getSliceStartCU(self, pos):
        return self.m_uiSliceStartCU[pos - self.m_uiAbsIdxInLCU]
    def getDependentSliceStartCU(self, pos):
        return self.m_uiDependentSliceStartCU[pos - self.m_uiAbsIdxInLCU]
    def getTotalBins(self):
        return self.m_uiTotalBins

    def getTotalCost(self):
        return self.m_dTotalCost
    def getTotalDistortion(self):
        return self.m_uiTotalDistortion
    def getTotalBits(self):
        return self.m_uiTotalBits
    def getTotalNumPart(self):
        return self.m_uiNumPartition

    def getCoefScanIdx(self, uiAbsPartIdx, uiWidth, bIsLuma, bIsIntra):
        uiCTXIdx = uiScanIdx = uiDirMode = 0

        if not bIsIntra:
            uiScanIdx = SCAN_ZIGZAG
            return uiScanIdx

        if uiWidth == 2:
            uiCTXIdx = 6
        elif uiWidth == 4:
            uiCTXIdx = 5
        elif uiWidth == 8:
            uiCTXIdx = 4
        elif uiWidth == 16:
            uiCTXIdx = 3
        elif uiWidth == 32:
            uiCTXIdx = 2
        elif uiWidth == 64:
            uiCTXIdx = 1
        else:
            uiCTXIdx = 0

        if bIsLuma:
            uiDirMode = self.getLumaIntraDir(uiAbsPartIdx)
            uiScanIdx = SCAN_ZIGZAG
            if uiCTXIdx > 3 and uiCTXIdx < 6: # if multiple scans supported for transform size
                uiScanIdx = 1 if abs(uiDirMode - VER_IDX) < 5 else \
                            2 if abs(uiDirMode - HOR_IDX) < 5 else 0
            else:
                uiDirMode = self.getChromaIntraDir(uiAbsPartIdx)
                if uiDirMode == DM_CHROMA_IDX:
                    # get number of partitions in current CU
                    depth = self.getDepth(uiAbsPartIdx)
                    numParts = self.getPic().getNumPartInCU() >> (2 * depth)

                    # get luma mode from upper-left corner of current CU
                    uiDirMode = self.getLumaIntraDir((uiAbsPartIdx/numParts) * numParts)
                uiScanIdx = SCAN_ZIGZAG
                if uiCTXIdx > 4 and uiCTXIdx < 7: #if multiple scans supported for transform size
                    uiScanIdx = 1 if abs(uiDirMode - VER_IDX) < 5 else \
                                2 if abs(uiDirMode - HOR_IDX) < 5 else 0

        return uiScanIdx

    def xCheckDuplicateCand(self, pcMvFieldNeighbours, puhInterDirNeighbours, pbCandIsInter, ruiArrayAddr):
        if self.getSlice().isInterB():
            uiMvFieldNeighIdxCurr = ruiArrayAddr << 1
            iRefIdxL0 = pcMvFieldNeighbours[uiMvFieldNeighIdxCurr  ].getRefIdx()
            iRefIdxL1 = pcMvFieldNeighbours[uiMvFieldNeighIdxCurr+1].getRefIdx()
            MvL0 = pcMvFieldNeighbours[uiMvFieldNeighIdxCurr  ].getMv()
            MvL1 = pcMvFieldNeighbours[uiMvFieldNeighIdxCurr+1].getMv()

            for k in xrange(ruiArrayAddr):
                uiMvFieldNeighIdxComp = k << 1
                if iRefIdxL0 == pcMvFieldNeighbours[uiMvFieldNeighIdxComp  ].getRefIdx() and \
                   iRefIdxL1 == pcMvFieldNeighbours[uiMvFieldNeighIdxComp+1].getRefIdx() and \
                   MvL0 == pcMvFieldNeighbours[uiMvFieldNeighIdxComp  ].getMv() and \
                   MvL1 == pcMvFieldNeighbours[uiMvFieldNeighIdxComp+1].getMv() and \
                   puhInterDirNeighbours[ruiArrayAddr] == puhInterDirNeighbours[k]:
                    pbCandIsInter[ruiArrayAddr] = False
                    break
        else:
            uiMvFieldNeighIdxCurr = ruiArrayAddr << 1
            iRefIdxL0 = pcMvFieldNeighbours[uiMvFieldNeighIdxCurr].getRefIdx()
            MvL0 = pcMvFieldNeighbours[uiMvFieldNeighIdxCurr].getMv()

            for k in xrange(ruiArrayAddr):
                uiMvFieldNeighIdxComp = k << 1
                if iRefIdxL0 == pcMvFieldNeighbours[uiMvFieldNeighIdxComp].getRefIdx() and \
                   MvL0 == pcMvFieldNeighbours[uiMvFieldNeighIdxComp].getMv() and \
                   puhInterDirNeighbours[ruiArrayAddr] == puhInterDirNeighbours[k]:
                    pbCandIsInter[ruiArrayAddr] = False
                    break

        if pbCandIsInter[ruiArrayAddr]:
            ruiArrayAddr += 1
        return ruiArrayAddr

    def xCheckCornerCand(self, pcCorner, uiCornerPUIdx, uiIter, rbValidCand):
        if uiIter == 0:
            if pcCorner and not pcCorner.isIntra(uiCornerPUIdx):
                rbValidCand = True
                if self.getSlice().isInterB():
                    if pcCorner.getInterDir(uiCornerPUIdx) == 1:
                        if pcCorner.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiCornerPUIdx) != 0:
                            rbValidCand = False
                    elif pcCorner.getInterDir(uiCornerPUIdx) == 2:
                        if pcCorner.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiCornerPUIdx) != 0:
                            rbValidCand = False
                    else:
                        if pcCorner.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiCornerPUIdx) != 0 or \
                           pcCorner.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiCornerPUIdx) != 0:
                            rbValidCand = False
                elif pcCorner.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiCornerPUIdx) != 0:
                    rbValidCand = False
        else:
            if pcCorner and not pcCorner.isIntra(uiCornerPUIdx):
                rbValidCand = True
                if self.getSlice().isInterB():
                    if pcCorner.getInterDir(uiCornerPUIdx) == 1:
                        if pcCorner.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiCornerPUIdx) < 0:
                            rbValidCand = False
                    elif pcCorner.getInterDir(uiCornerPUIdx) == 2:
                        if pcCorner.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiCornerPUIdx) < 0:
                            rbValidCand = False
                    else:
                        if pcCorner.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiCornerPUIdx) < 0 or \
                           pcCorner.getCUMvField(REF_PIC_LIST_1).getRefIdx(uiCornerPUIdx) < 0:
                            rbValidCand = False
                elif pcCorner.getCUMvField(REF_PIC_LIST_0).getRefIdx(uiCornerPUIdx) < 0:
                    rbValidCand = False

        return rbValidCand

    def xAddMVPCand(self, pInfo, eRefPicList, iRefIdx, uiPartUnitIdx, eDir):
        pcTmpCU = None
        uiIdx = 0
        if eDir == MD_LEFT:
            pcTmpCU, uiIdx = self.getPULeft(uiIdx, uiPartUnitIdx, True, False)
        elif eDir == MD_ABOVE:
            pcTmpCU, uiIdx = self.getPUAbove(uiIdx, uiPartUnitIdx, True, False, True)
        elif eDir == MD_ABOVE_RIGHT:
            pcTmpCU, uiIdx = self.getPUAboveRight(uiIdx, uiPartUnitIdx, True, False, True)
        elif eDir == MD_BELOW_LEFT:
            pcTmpCU, uiIdx = self.getPUBelowLeft(uiIdx, uiPartUnitIdx, True, False)
        elif eDir == MD_ABOVE_LEFT:
            pcTmpCU, uiIdx = self.getPUAboveLeft(uiIdx, uiPartUnitIdx, True, False, True)

        if pcTmpCU != None and self.m_pcSlice.isEqualRef(eRefPicList, pcTmpCU.getCUMvField(eRefPicList).getRefIdx(uiIdx), iRefIdx):
            cMvPred = pcTmpCU.getCUMvField(eRefPicList).getMv(uiIdx)
            acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
            acMvCand[pInfo.iN].setHor(cMvPred.getHor())
            acMvCand[pInfo.iN].setVer(cMvPred.getVer())
            pInfo.iN += 1
            return True

        if pcTmpCU == None:
            return False

        eRefPicList2nd = REF_PIC_LIST_0
        if eRefPicList == REF_PIC_LIST_0:
            eRefPicList2nd = REF_PIC_LIST_1
        elif eRefPicList == REF_PIC_LIST_1:
            eRefPicList2nd = REF_PIC_LIST_0

        iCurrRefPOC = self.m_pcSlice.getRefPic(eRefPicList, iRefIdx).getPOC()
        iNeibRefPOC = 0

        if pcTmpCU.getCUMvField(eRefPicList2nd).getRefIdx(uiIdx) >= 0:
            iNeibRefPOC = pcTmpCU.getSlice().getRefPOC(eRefPicList2nd, pcTmpCU.getCUMvField(eRefPicList2nd).getRefIdx(uiIdx))
            if iNeibRefPOC == iCurrRefPOC: # Same Reference Frame But Diff List
                cMvPred = pcTmpCU.getCUMvField(eRefPicList2nd).getMv(uiIdx)
                acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
                acMvCand[pInfo.iN].setHor(cMvPred.getHor())
                acMvCand[pInfo.iN].setVer(cMvPred.getVer())
                pInfo.iN += 1
                return True
        return False

    def xAddMVPCandOrder(self, pInfo, eRefPicList, iRefIdx, uiPartUnitIdx, eDir):
        pcTmpCU = None
        uiIdx = 0
        if eDir == MD_LEFT:
            pcTmpCU, uiIdx = self.getPULeft(uiIdx, uiPartUnitIdx, True, False)
        elif eDir == MD_ABOVE:
            pcTmpCU, uiIdx = self.getPUAbove(uiIdx, uiPartUnitIdx, True, False, True)
        elif eDir == MD_ABOVE_RIGHT:
            pcTmpCU, uiIdx = self.getPUAboveRight(uiIdx, uiPartUnitIdx, True, False, True)
        elif eDir == MD_BELOW_LEFT:
            pcTmpCU, uiIdx = self.getPUBelowLeft(uiIdx, uiPartUnitIdx, True, False)
        elif eDir == MD_ABOVE_LEFT:
            pcTmpCU, uiIdx = self.getPUAboveLeft(uiIdx, uiPartUnitIdx, True, False, True)

        if pcTmpCU == None:
            return False

        eRefPicList2nd = REF_PIC_LIST_0
        if eRefPicList == REF_PIC_LIST_0:
            eRefPicList2nd = REF_PIC_LIST_1
        elif eRefPicList == REF_PIC_LIST_1:
            eRefPicList2nd = REF_PIC_LIST_0

        iCurrPOC = self.m_pcSlice.getPOC()
        iCurrRefPOC = self.m_pcSlice.getRefPic(eRefPicList, iRefIdx).getPOC()
        iNeibPOC = iCurrPOC
        iNeibRefPOC = 0

        bIsCurrRefLongTerm = self.m_pcSlice.getRefPic(eRefPicList, iRefIdx).getIsLongTerm()
        bIsNeibRefLongTerm = False
        #---------------  V1 (END) ------------------
        if pcTmpCU.getCUMvField(eRefPicList).getRefIdx(uiIdx) >= 0:
            iNeibRefPOC = pcTmpCU.getSlice().getRefPOC(eRefPicList, pcTmpCU.getCUMvField(eRefPicList).getRefIdx(uiIdx))
            cMvPred = pcTmpCU.getCUMvField(eRefPicList).getMv(uiIdx)
            rcMv = None

            bIsNeibRefLongTerm = pcTmpCU.getSlice().getRefPic(eRefPicList, pcTmpCU.getCUMvField(eRefPicList).getRefIdx(uiIdx)).getIsLongTerm()
            if bIsCurrRefLongTerm or bIsNeibRefLongTerm:
                rcMv = cMvPred
            else:
                iScale = self.xGetDistScaleFactor(iCurrPOC, iCurrRefPOC, iNeibPOC, iNeibRefPOC)
                if iScale == 4096:
                    rcMv = cMvPred
                else:
                    rcMv = cMvPred.scaleMv(iScale)
            acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
            acMvCand[pInfo.iN].setHor(rcMv.getHor())
            acMvCand[pInfo.iN].setVer(rcMv.getVer())
            pInfo.iN += 1
            return True
        #---------------  V2 (END) ------------------
        if pcTmpCU.getCUMvField(eRefPicList2nd).getRefIdx(uiIdx) >= 0:
            iNeibRefPOC = pcTmpCU.getSlice().getRefPOC(eRefPicList2nd, pcTmpCU.getCUMvField(eRefPicList2nd).getRefIdx(uiIdx))
            cMvPred = pcTmpCU.getCUMvField(eRefPicList2nd).getMv(uiIdx)
            rcMv = None

            bIsNeibRefLongTerm = pcTmpCU.getSlice().getRefPic(eRefPicList2nd, pcTmpCU.getCUMvField(eRefPicList2nd).getRefIdx(uiIdx)).getIsLongTerm()
            if bIsCurrRefLongTerm or bIsNeibRefLongTerm:
                rcMv = cMvPred
            else:
                iScale = self.xGetDistScaleFactor(iCurrPOC, iCurrRefPOC, iNeibPOC, iNeibRefPOC)
                if iScale == 4096:
                    rcMv = cMvPred
                else:
                    rcMv = cMvPred.scaleMv(iScale)
            acMvCand = pointer(pInfo.m_acMvCand, type='TComMv *')
            acMvCand[pInfo.iN].setHor(rcMv.getHor())
            acMvCand[pInfo.iN].setVer(rcMv.getVer())
            pInfo.iN += 1
            return True
        #---------------  V3 (END) ------------------
        return False

    def xGetColMVP(self, eRefPicList, uiCUAddr, uiPartUnitIdx, rcMv, riRefIdx):
        uiAbsPartAddr = uiPartUnitIdx

        # use coldir.
        pColPic = self.getSlice().getRefPic(
            self.getSlice().getColDir() if self.getSlice().isInterB() else 0,
            self.getSlice().getColRefIdx())
        pColCU = pColPic.getCU(uiCUAddr)
        if pColCU.getPic() == None or pColCU.getPartitionSize(uiPartUnitIdx) == SIZE_NONE:
            return False, rcMv, riRefIdx
        iCurrPOC = self.m_pcSlice.getPOC()
        iCurrRefPOC = self.m_pcSlice.getRefPic(eRefPicList, riRefIdx).getPOC()
        iColPOC = pColCU.getSlice().getPOC()

        if pColCU.isIntra(uiAbsPartAddr):
            return False, rcMv, riRefIdx
        eColRefPicList = eRefPicList if self.getSlice().getCheckLDC() else \
                         1 - self.getSlice().getColDir()

        iColRefIdx = pColCU.getCUMvField(eColRefPicList).getRefIdx(uiAbsPartAddr)

        if iColRefIdx < 0:
            eColRefPicList = 1 - eColRefPicList
            iColRefIdx = pColCU.getCUMvField(eColRefPicList).getRefIdx(uiAbsPartAddr)

            if iColRefIdx < 0:
                return False, rcMv, riRefIdx

        # Scale the vector.
        iColRefPOC = pColCU.getSlice().getRefPOC(eColRefPicList, iColRefIdx)
        cColMv = pColCU.getCUMvField(eColRefPicList).getMv(uiAbsPartAddr)

        iCurrRefPOC = self.m_pcSlice.getRefPic(eRefPicList, riRefIdx).getPOC()
        bIsCurrRefLongTerm = self.m_pcSlice.getRefPic(eRefPicList, riRefIdx).getIsLongTerm()
        bIsColRefLongTerm = pColCU.getSlice().getRefPic(eColRefPicList, iColRefIdx).getIsUsedAsLongTerm()
        if bIsCurrRefLongTerm or bIsColRefLongTerm:
            rcMv = cColMv
        else:
            iScale = self.xGetDistScaleFactor(iCurrPOC, iCurrRefPOC, iColPOC, iColRefPOC)
            if iScale == 4096:
                rcMv = cColMv
            else:
                rcMv = cColMv.scaleMv(iScale)
        return True, rcMv, riRefIdx

    def xGetMvdBits(self, cMvd):
        return self.xGetComponentBits(cMvd.getHor()) + self.xGetComponentBits(cMvd.getVer())

    def xGetComponentBits(self, iVal):
        uiLength = 1
        uiTemp = (-iVal<<1)+1 if iVal <= 0 else iVal<<1

        assert(uiTemp)

        while 1 != uiTemp:
            uiTemp >>= 1
            uiLength += 2

        return uiLength

    def xGetDistScaleFactor(self, iCurrPOC, iCurrRefPOC, iColPOC, iColRefPOC):
        iDiffPocD = iColPOC - iColRefPOC
        iDiffPocB = iCurrPOC - iCurrRefPOC

        if iDiffPocD == iDiffPocB:
            return 4096
        else:
            iTDB = Clip3(-128, 127, iDiffPocB)
            iTDD = Clip3(-128, 127, iDiffPocD)
            iX = (0x4000 + abs(iTDD/2)) / iTDD
            iScale = Clip3(-4096, 4095, (iTDB * iX +32) >> 6)
            return iScale

    def xDeriveCenterIdx(self, eCUMode, uiPartIdx, ruiPartIdxCenter):
        uiPartAddr = iPartWidth = iPartHeight = 0
        uiPartAddr, iPartWidth, iPartHeight = self.getPartIndexAndSize(uiPartIdx, uiPartAddr, iPartWidth, iPartHeight)

        ruiPartIdxCenter = self.m_uiAbsIdxInLCU + uiPartAddr # partition origin.
        ruiPartIdxCenter = g_auiRasterToZscan[
            g_auiZscanToRaster[ruiPartIdxCenter] +
            iPartHeight / self.m_pcPic.getMinCUHeight() / 2 * self.m_pcPic.getNumPartInWidth() +
            iPartWidth / self.m_pcPic.getMinCUWidth() / 2]
        return ruiPartIdxCenter

    def xGetCenterCol(self, uiPartIdx, eRefPicList, iRefIdx, pcMv):
        eCUMode = self.getPartitionSize(0)

        iCurrPOC = self.m_pcSlice.getPOC()

        # use coldir.
        pColPic = self.getSlice().getRefPic(
            self.getSlice().getColDir() if self.getSlice().isInterB() else 0,
            self.getSlice().getColRefIdx())
        pColCU = pColPic.getCU(self.m_uiCUAddr)

        iColPOC = pColCU.getSlice().getPOC()
        uiPartIdxCenter = 0
        uiPartIdxCenter = self.xDeriveCenterIdx(eCUMode, uiPartIdx, uiPartIdxCenter)

        if pColCU.isIntra(uiPartIdxCenter):
            return False

        # Prefer a vector crossing us.  Prefer shortest.
        eColRefPicList = REF_PIC_LIST_0
        bFirstCrosses = False
        iFirstColDist = -1
        for l in xrange(2):
            bSaveit = False
            iColRefIdx = pColCU.getCUMvField(l).getRefIdx(uiPartIdxCenter)
            if iColRefIdx < 0:
                continue
            iColRefPOC = pColCU.getSlice().getRefPOC(l, iColRefIdx)
            iColDist = abs(iColRefPOC - iColPOC)
            bCrosses = iColRefPOC > iCurrPOC if iColPOC < iCurrPOC else iColRefPOC < iCurrPOC
            if iFirstColDist < 0:
                bSaveit = True
            elif bCrosses and not bFirstCrosses:
                bSaveit = True
            elif bCrosses == bFirstCrosses and l == eRefPicList:
                bSaveit = True

            if bSaveit:
                bFirstCrosses = bCrosses
                iFirstColDist = iColDist
                eColRefPicList = l

        # Scale the vector.
        iColRefPOC = pColCU.getSlice().getRefPOC(eColRefPicList, pColCU.getCUMvField(eColRefPicList).getRefIdx(uiPartIdxCenter))
        cColMv = pColCU.getCUMvField(eColRefPicList).getMv(uiPartIdxCenter)

        iCurrRefPOC = self.m_pcSlice.getRefPic(eRefPicList, iRefIdx).getPOC()
        bIsCurrRefLongTerm = self.m_pcSlice.getRefPic(eRefPicList, iRefIdx).getIsLongTerm()
        bIsColRefLongTerm = pColCU.getSlice().getRefPic(eColRefPicList, pColCU.getCUMvField(eColRefPicList).getRefIdx(uiPartIdxCenter)).getIsUsedAsLongTerm()
        if bIsCurrRefLongTerm or bIsColRefLongTerm:
            pcMv[0] = cColMv
        else:
            iScale = self.xGetDistScaleFactor(iCurrPOC, iCurrRefPOC, iColPOC, iColRefPOC)
            if iScale == 4096:
                pcMv[0] = cColMv
            else:
                pcMv[0] = cColMv.scaleMv(iScale)
        return True

class RasterAddress(object):

    @staticmethod
    def isEqualCol(addrA, addrB, numUnitsPerRow):
        return ((addrA ^ addrB) & (numUnitsPerRow - 1)) == 0

    @staticmethod
    def isEqualRow(addrA, addrB, numUnitsPerRow):
        return ((addrA ^ addrB) & ~(numUnitsPerRow - 1)) == 0

    @staticmethod
    def isEqualRowOrCol(addrA, addrB, numUnitsPerRow):
        return RasterAddress.isEqualCol(addrA, addrB, numUnitsPerRow) or \
               RasterAddress.isEqualRow(addrA, addrB, numUnitsPerRow)

    @staticmethod
    def isZeroCol(addr, numUnitsPerRow):
        return (addr & (numUnitsPerRow - 1)) == 0

    @staticmethod
    def isZeroRow(addr, numUnitsPerRow):
        return (addr & ~(numUnitsPerRow - 1)) == 0

    @staticmethod
    def lessThanCol(addr, val, numUnitsPerRow):
        return (addr & (numUnitsPerRow - 1)) < val

    @staticmethod
    def lessThanRow(addr, val, numUnitsPerRow):
        return addr < val * numUnitsPerRow
