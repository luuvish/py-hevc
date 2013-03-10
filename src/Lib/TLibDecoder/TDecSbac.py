# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecSbac.py
    HM 10.0 Python Implementation
"""

import sys

from ... import pointer
from ... import Trace

from ... import ArrayUInt, ArrayInt

from ... import cvar

from ... import TComMv
from ... import TComTrQuant

from ..TLibCommon.ContextModel import ContextModel
from ..TLibCommon.ContextModel3DBuffer import ContextModel3DBuffer
from .TDecEntropy import TDecEntropy

from ..TLibCommon.ContextTables import (
    MAX_NUM_CTX_MOD,
    NUM_SPLIT_FLAG_CTX, NUM_SKIP_FLAG_CTX,
    NUM_MERGE_FLAG_EXT_CTX, NUM_MERGE_IDX_EXT_CTX,
    NUM_PART_SIZE_CTX, NUM_CU_AMP_CTX, NUM_PRED_MODE_CTX,
    NUM_ADI_CTX,
    NUM_CHROMA_PRED_CTX, NUM_INTER_DIR_CTX, NUM_MV_RES_CTX,
    NUM_REF_NO_CTX, NUM_TRANS_SUBDIV_FLAG_CTX,
    NUM_QT_CBF_CTX, NUM_QT_ROOT_CBF_CTX, NUM_DELTA_QP_CTX,
    NUM_SIG_CG_FLAG_CTX,
    NUM_SIG_FLAG_CTX, NUM_SIG_FLAG_CTX_LUMA, #NUM_SIG_FLAG_CTX_CHROMA,
    NUM_CTX_LAST_FLAG_XY,
    NUM_ONE_FLAG_CTX, NUM_ONE_FLAG_CTX_LUMA, #NUM_ONE_FLAG_CTX_CHROMA,
    NUM_ABS_FLAG_CTX, NUM_ABS_FLAG_CTX_LUMA, #NUM_ABS_FLAG_CTX_CHROMA,
    NUM_MVP_IDX_CTX,
    NUM_SAO_MERGE_FLAG_CTX, NUM_SAO_TYPE_IDX_CTX,
    NUM_TRANSFORMSKIP_FLAG_CTX, NUM_CU_TRANSQUANT_BYPASS_FLAG_CTX,
    INIT_CU_TRANSQUANT_BYPASS_FLAG,
    INIT_SPLIT_FLAG, INIT_SKIP_FLAG,
    INIT_MERGE_FLAG_EXT, INIT_MERGE_IDX_EXT,
    INIT_PART_SIZE, INIT_CU_AMP_POS, INIT_PRED_MODE,
    INIT_INTRA_PRED_MODE, INIT_CHROMA_PRED_MODE, INIT_INTER_DIR,
    INIT_MVD, INIT_REF_PIC, INIT_DQP,
    INIT_QT_CBF, INIT_QT_ROOT_CBF,
    INIT_LAST, INIT_SIG_CG_FLAG, INIT_SIG_FLAG,
    INIT_ONE_FLAG, INIT_ABS_FLAG, INIT_MVP_IDX,
    INIT_SAO_MERGE_FLAG, INIT_SAO_TYPE_IDX,
    INIT_TRANS_SUBDIV_FLAG, INIT_TRANSFORMSKIP_FLAG
)

from ..TLibCommon.TypeDef import (
    COEF_REMAIN_BIN_REDUCTION, CU_DQP_TU_CMAX, CU_DQP_EG_k,
    SBH_THRESHOLD, C1FLAG_NUMBER, C2FLAG_NUMBER,
    MLS_GRP_NUM, MLS_CG_SIZE, SCAN_SET_SIZE, LOG2_SCAN_SET_SIZE,
    NUM_CHROMA_MODE, DM_CHROMA_IDX
)
from ..TLibCommon.TypeDef import (
    SAO_EO_LEN, SAO_BO_LEN, SAO_BO,
    B_SLICE, P_SLICE,
    SIZE_2Nx2N, SIZE_2NxN, SIZE_Nx2N, SIZE_NxN,
    SIZE_2NxnU, SIZE_2NxnD, SIZE_nLx2N, SIZE_nRx2N,
    MODE_INTER, MODE_INTRA,
    TEXT_LUMA, TEXT_CHROMA, TEXT_NONE,
    REF_PIC_LIST_1, SCAN_VER
)

from ..TLibCommon.CommonDef import (AMVP_MAX_NUM_CANDS, MRG_MAX_NUM_CANDS)

from ..TLibCommon.TComRom import (
    g_auiRasterToPelX, g_auiRasterToPelY, g_auiZscanToRaster,
    g_uiMinInGroup, g_uiGroupIdx, g_aucConvertToBit,
    g_auiSigLastScan, g_sigLastScan8x8, g_sigLastScanCG32x32
)


class TDecSbac(TDecEntropy):

    def __init__(self):
        super(TDecSbac, self).__init__()

        self.m_pcBitstream = None
        self.m_pcTDecBinIf = None

        self.m_uiLastDQpNonZero = 0
        self.m_uiLastQp = 0

        self.m_contextModels = pointer([ContextModel() for i in xrange(MAX_NUM_CTX_MOD)])
        self.m_numContextModels = 0

        numContextModels = [0]
        self.m_cCUSplitFlagSCModel           = ContextModel3DBuffer(1, 1, NUM_SPLIT_FLAG_CTX               , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUSkipFlagSCModel            = ContextModel3DBuffer(1, 1, NUM_SKIP_FLAG_CTX                , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUMergeFlagExtSCModel        = ContextModel3DBuffer(1, 1, NUM_MERGE_FLAG_EXT_CTX           , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUMergeIdxExtSCModel         = ContextModel3DBuffer(1, 1, NUM_MERGE_IDX_EXT_CTX            , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUPartSizeSCModel            = ContextModel3DBuffer(1, 1, NUM_PART_SIZE_CTX                , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUPredModeSCModel            = ContextModel3DBuffer(1, 1, NUM_PRED_MODE_CTX                , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUIntraPredSCModel           = ContextModel3DBuffer(1, 1, NUM_ADI_CTX                      , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUChromaPredSCModel          = ContextModel3DBuffer(1, 1, NUM_CHROMA_PRED_CTX              , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUDeltaQpSCModel             = ContextModel3DBuffer(1, 1, NUM_DELTA_QP_CTX                 , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUInterDirSCModel            = ContextModel3DBuffer(1, 1, NUM_INTER_DIR_CTX                , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCURefPicSCModel              = ContextModel3DBuffer(1, 1, NUM_REF_NO_CTX                   , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUMvdSCModel                 = ContextModel3DBuffer(1, 1, NUM_MV_RES_CTX                   , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUQtCbfSCModel               = ContextModel3DBuffer(1, 2, NUM_QT_CBF_CTX                   , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUTransSubdivFlagSCModel     = ContextModel3DBuffer(1, 1, NUM_TRANS_SUBDIV_FLAG_CTX        , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUQtRootCbfSCModel           = ContextModel3DBuffer(1, 1, NUM_QT_ROOT_CBF_CTX              , self.m_contextModels + numContextModels[0], numContextModels)

        self.m_cCUSigCoeffGroupSCModel       = ContextModel3DBuffer(1, 2, NUM_SIG_CG_FLAG_CTX              , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUSigSCModel                 = ContextModel3DBuffer(1, 1, NUM_SIG_FLAG_CTX                 , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUCtxLastX                   = ContextModel3DBuffer(1, 2, NUM_CTX_LAST_FLAG_XY             , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUCtxLastY                   = ContextModel3DBuffer(1, 2, NUM_CTX_LAST_FLAG_XY             , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUOneSCModel                 = ContextModel3DBuffer(1, 1, NUM_ONE_FLAG_CTX                 , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cCUAbsSCModel                 = ContextModel3DBuffer(1, 1, NUM_ABS_FLAG_CTX                 , self.m_contextModels + numContextModels[0], numContextModels)

        self.m_cMVPIdxSCModel                = ContextModel3DBuffer(1, 1, NUM_MVP_IDX_CTX                  , self.m_contextModels + numContextModels[0], numContextModels)

        self.m_cCUAMPSCModel                 = ContextModel3DBuffer(1, 1, NUM_CU_AMP_CTX                   , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cSaoMergeSCModel              = ContextModel3DBuffer(1, 1, NUM_SAO_MERGE_FLAG_CTX           , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cSaoTypeIdxSCModel            = ContextModel3DBuffer(1, 1, NUM_SAO_TYPE_IDX_CTX             , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_cTransformSkipSCModel         = ContextModel3DBuffer(1, 2, NUM_TRANSFORMSKIP_FLAG_CTX       , self.m_contextModels + numContextModels[0], numContextModels)
        self.m_CUTransquantBypassFlagSCModel = ContextModel3DBuffer(1, 1, NUM_CU_TRANSQUANT_BYPASS_FLAG_CTX, self.m_contextModels + numContextModels[0], numContextModels)

        self.m_numContextModels = numContextModels[0]
        assert(self.m_numContextModels <= MAX_NUM_CTX_MOD)

    def init(self, p):
        self.m_pcTDecBinIf = p
    def uninit(self):
        self.m_pcTDecBinIf = None

    def load(self, pSrc):
        self.xCopyFrom(pSrc)
    def loadContexts(self, pSrc):
        self.xCopyContextsFrom(pSrc)

    def xCopyFrom(self, pSrc):
        self.m_pcTDecBinIf.copyState(pSrc.m_pcTDecBinIf)

        self.m_uiLastQp = pSrc.m_uiLastQp
        self.xCopyContextsFrom(pSrc)

    def xCopyContextsFrom(self, pSrc):
        for x in xrange(self.m_numContextModels):
            self.m_contextModels[x] = pSrc.m_contextModels[x]

    def resetEntropy(self, pcSlice):
        sliceType = pcSlice.getSliceType()
        qp = pcSlice.getSliceQp()

        if pcSlice.getPPS().getCabacInitPresentFlag() and pcSlice.getCabacInitFlag():
            if sliceType == P_SLICE: # change initialization table to B_SLICE initialization
                sliceType = B_SLICE
            elif sliceType == B_SLICE: # change initialization table to P_SLICE initialization
                sliceType = P_SLICE
            else: # should not occur
                assert(False)

        self.m_cCUSplitFlagSCModel.initBuffer          (sliceType, qp, INIT_SPLIT_FLAG)
        self.m_cCUSkipFlagSCModel.initBuffer           (sliceType, qp, INIT_SKIP_FLAG)
        self.m_cCUMergeFlagExtSCModel.initBuffer       (sliceType, qp, INIT_MERGE_FLAG_EXT)
        self.m_cCUMergeIdxExtSCModel.initBuffer        (sliceType, qp, INIT_MERGE_IDX_EXT)
        self.m_cCUPartSizeSCModel.initBuffer           (sliceType, qp, INIT_PART_SIZE)
        self.m_cCUAMPSCModel.initBuffer                (sliceType, qp, INIT_CU_AMP_POS)
        self.m_cCUPredModeSCModel.initBuffer           (sliceType, qp, INIT_PRED_MODE)
        self.m_cCUIntraPredSCModel.initBuffer          (sliceType, qp, INIT_INTRA_PRED_MODE)
        self.m_cCUChromaPredSCModel.initBuffer         (sliceType, qp, INIT_CHROMA_PRED_MODE)
        self.m_cCUInterDirSCModel.initBuffer           (sliceType, qp, INIT_INTER_DIR)
        self.m_cCUMvdSCModel.initBuffer                (sliceType, qp, INIT_MVD)
        self.m_cCURefPicSCModel.initBuffer             (sliceType, qp, INIT_REF_PIC)
        self.m_cCUDeltaQpSCModel.initBuffer            (sliceType, qp, INIT_DQP)
        self.m_cCUQtCbfSCModel.initBuffer              (sliceType, qp, INIT_QT_CBF)
        self.m_cCUQtRootCbfSCModel.initBuffer          (sliceType, qp, INIT_QT_ROOT_CBF)
        self.m_cCUSigCoeffGroupSCModel.initBuffer      (sliceType, qp, INIT_SIG_CG_FLAG)
        self.m_cCUSigSCModel.initBuffer                (sliceType, qp, INIT_SIG_FLAG)
        self.m_cCUCtxLastX.initBuffer                  (sliceType, qp, INIT_LAST)
        self.m_cCUCtxLastY.initBuffer                  (sliceType, qp, INIT_LAST)
        self.m_cCUOneSCModel.initBuffer                (sliceType, qp, INIT_ONE_FLAG)
        self.m_cCUAbsSCModel.initBuffer                (sliceType, qp, INIT_ABS_FLAG)
        self.m_cMVPIdxSCModel.initBuffer               (sliceType, qp, INIT_MVP_IDX)
        self.m_cSaoMergeSCModel.initBuffer             (sliceType, qp, INIT_SAO_MERGE_FLAG)
        self.m_cSaoTypeIdxSCModel.initBuffer           (sliceType, qp, INIT_SAO_TYPE_IDX)

        self.m_cCUTransSubdivFlagSCModel.initBuffer    (sliceType, qp, INIT_TRANS_SUBDIV_FLAG)
        self.m_cTransformSkipSCModel.initBuffer        (sliceType, qp, INIT_TRANSFORMSKIP_FLAG)
        self.m_CUTransquantBypassFlagSCModel.initBuffer(sliceType, qp, INIT_CU_TRANSQUANT_BYPASS_FLAG)
        self.m_uiLastDQpNonZero = 0

        self.m_uiLastQp = qp

        self.m_pcTDecBinIf.start()

    def setBitstream(self, p):
        self.m_pcBitstream = p
        self.m_pcTDecBinIf.init(p)

    def parseVPS(self, pcVPS):
        pass
    def parseSPS(self, pcSPS):
        pass
    def parsePPS(self, pcPPS):
        pass

    def parseSliceHeader(self, rpcSlice, parameterSetManager):
        pass

    def parseTerminatingBit(self, ruiBit):
        ruitBit = self.m_pcTDecBinIf.decodeBinTrm(ruiBit)
        return ruiBit

    def parseMVPIdx(self, riMVPIdx):
        uiSymbol = 0
        uiSymbol = self.xReadUnaryMaxSymbol(
            uiSymbol, self.m_cMVPIdxSCModel.get(0), 1, AMVP_MAX_NUM_CANDS-1)
        riMVPIdx = uiSymbol
        return riMVPIdx

    def parseSaoMaxUvlc(self, val, maxSymbol):
        if maxSymbol == 0:
            val = 0
            return val

        code = 0
        code = self.m_pcTDecBinIf.decodeBinEP(code)
        if code == 0:
            val = 0
            return val

        i = 1
        while True:
            code = self.m_pcTDecBinIf.decodeBinEP(code)
            if code == 0:
                break
            i += 1
            if i == maxSymbol:
                break

        val = i
        return val

    def parseSaoMerge(self, ruiVal):
        uiCode = 0
        uiCode = self.m_pcTDecBinIf.decodeBin(uiCode, self.m_cSaoMergeSCModel.get(0, 0, 0))
        ruiVal = uiCode
        return ruiVal

    def parseSaoTypeIdx(self, ruiVal):
        uiCode = 0
        uiCode = self.m_pcTDecBinIf.decodeBin(uiCode, self.m_cSaoTypeIdxSCModel.get(0, 0, 0))
        if uiCode == 0:
            ruiVal = 0
        else:
            uiCode = self.m_pcTDecBinIf.decodeBinEP(uiCode)
            if uiCode == 0:
                ruiVal = 5
            else:
                ruiVal = 1
        return ruiVal

    def parseSaoUflc(self, uiLength, riVal):
        riVal = self.m_pcTDecBinIf.decodeBinsEP(riVal, uiLength)
        return riVal

    def parseSaoOneLcuInterleaving(self, rx, ry, pSaoParam,
        pcCU, iCUAddrInSlice, iCUAddrUpInSlice, allowMergeLeft, allowMergeUp):

        def copySaoOneLcuParam(psDst, psSrc):
            src_offset = pointer(psSrc.offset, type='int *')
            dst_offset = pointer(psDst.offset, type='int *')

            psDst.partIdx = psSrc.partIdx
            psDst.typeIdx = psSrc.typeIdx
            if psDst.typeIdx != -1:
                psDst.subTypeIdx = psSrc.subTypeIdx
                psDst.length = psSrc.length
                for i in xrange(psDst.length):
                    dst_offset[i] = src_offset[i]
            else:
                psDst.length = 0
                for i in xrange(SAO_BO_LEN):
                    dst_offset[i] = 0

        iAddr = pcCU.getAddr()
        uiSymbol = 0

        bSaoFlag = pointer(pSaoParam.bSaoFlag, type='bool *')
        saoLcuParamG = pointer(pSaoParam.saoLcuParam, type='SaoLcuParam **')
        saoLcuParam = (pointer(saoLcuParamG[0], type='SaoLcuParam *'),
                       pointer(saoLcuParamG[1], type='SaoLcuParam *'),
                       pointer(saoLcuParamG[2], type='SaoLcuParam *'))

        for iCompIdx in xrange(3):
            saoLcuParam[iCompIdx][iAddr].mergeUpFlag   = 0
            saoLcuParam[iCompIdx][iAddr].mergeLeftFlag = 0
            saoLcuParam[iCompIdx][iAddr].subTypeIdx    = 0
            saoLcuParam[iCompIdx][iAddr].typeIdx       = -1
            offset = pointer(saoLcuParam[iCompIdx][iAddr].offset, type='int *')
            offset[0] = 0
            offset[1] = 0
            offset[2] = 0
            offset[3] = 0
        if bSaoFlag[0] or bSaoFlag[1]:
            if rx > 0 and iCUAddrInSlice != 0 and allowMergeLeft:
                uiSymbol = self.parseSaoMerge(uiSymbol)
                saoLcuParam[0][iAddr].mergeLeftFlag = uiSymbol
            if saoLcuParam[0][iAddr].mergeLeftFlag == 0:
                if ry > 0 and iCUAddrInSlice >= 0 and allowMergeUp:
                    uiSymbol = self.parseSaoMerge(uiSymbol)
                    saoLcuParam[0][iAddr].mergeUpFlag = uiSymbol

        for iCompIdx in xrange(3):
            if (iCompIdx == 0 and bSaoFlag[0]) or (iCompIdx > 0 and bSaoFlag[1]):
                if rx > 0 and iCUAddrInSlice != 0 and allowMergeLeft:
                    saoLcuParam[iCompIdx][iAddr].mergeLeftFlag = saoLcuParam[0][iAddr].mergeLeftFlag
                else:
                    saoLcuParam[iCompIdx][iAddr].mergeLeftFlag = 0

                if saoLcuParam[iCompIdx][iAddr].mergeLeftFlag == 0:
                    if ry > 0 and iCUAddrInSlice >= 0 and allowMergeUp:
                        saoLcuParam[iCompIdx][iAddr].mergeUpFlag = saoLcuParam[0][iAddr].mergeUpFlag
                    else:
                        saoLcuParam[iCompIdx][iAddr].mergeUpFlag = 0
                    if not saoLcuParam[iCompIdx][iAddr].mergeUpFlag:
                        saoLcuParam[2][iAddr].typeIdx = saoLcuParam[1][iAddr].typeIdx
                        self.parseSaoOffset(saoLcuParam[iCompIdx][iAddr], iCompIdx)
                    else:
                        copySaoOneLcuParam(saoLcuParam[iCompIdx][iAddr],
                                           saoLcuParam[iCompIdx][iAddr-pSaoParam.numCuInWidth])
                else:
                    copySaoOneLcuParam(saoLcuParam[iCompIdx][iAddr], saoLcuParam[iCompIdx][iAddr-1])
            else:
                saoLcuParam[iCompIdx][iAddr].typeIdx = -1
                saoLcuParam[iCompIdx][iAddr].subTypeIdx = 0

    def parseSaoOffset(self, psSaoLcuParam, compIdx):
        offset = pointer(psSaoLcuParam.offset, type='int *')

        iTypeLength = (
            SAO_EO_LEN,
            SAO_EO_LEN,
            SAO_EO_LEN,
            SAO_EO_LEN,
            SAO_BO_LEN
        )
        uiSymbol = 0

        if compIdx == 2:
            uiSymbol = psSaoLcuParam.typeIdx + 1
        else:
            uiSymbol = self.parseSaoTypeIdx(uiSymbol)

        psSaoLcuParam.typeIdx = uiSymbol - 1
        if uiSymbol:
            psSaoLcuParam.length = iTypeLength[psSaoLcuParam.typeIdx]

            bitDepth = cvar.g_bitDepthC if compIdx else cvar.g_bitDepthY
            offsetTh = 1 << min(bitDepth - 5, 5)

            if psSaoLcuParam.typeIdx == SAO_BO:
                for i in xrange(psSaoLcuParam.length):
                    uiSymbol = self.parseSaoMaxUvlc(uiSymbol, offsetTh-1)
                    offset[i] = uiSymbol
                for i in xrange(psSaoLcuParam.length):
                    if offset[i] != 0:
                        uiSymbol = self.m_pcTDecBinIf.decodeBinEP(uiSymbol)
                        if uiSymbol:
                            offset[i] = - offset[i]
                uiSymbol = self.parseSaoUflc(5, uiSymbol)
                psSaoLcuParam.subTypeIdx = uiSymbol
            elif psSaoLcuParam.typeIdx < 4:
                uiSymbol = self.parseSaoMaxUvlc(uiSymbol, offsetTh-1)
                offset[0] = uiSymbol
                uiSymbol = self.parseSaoMaxUvlc(uiSymbol, offsetTh-1)
                offset[1] = uiSymbol
                uiSymbol = self.parseSaoMaxUvlc(uiSymbol, offsetTh-1)
                offset[2] = -uiSymbol
                uiSymbol = self.parseSaoMaxUvlc(uiSymbol, offsetTh-1)
                offset[3] = -uiSymbol
                if compIdx != 2:
                    uiSymbol = self.parseSaoUflc(2, uiSymbol)
                    psSaoLcuParam.subTypeIdx = uiSymbol
                    psSaoLcuParam.typeIdx += psSaoLcuParam.subTypeIdx
        else:
            psSaoLcuParam.length = 0

    def xReadUnarySymbol(self, ruiSymbol, pcSCModel, iOffset):
        ruiSymbol = self.m_pcTDecBinIf.decodeBin(ruiSymbol, pcSCModel[0])

        if not ruiSymbol:
            return ruiSymbol

        uiSymbol = 0
        uiCont = 0

        while True:
            uiCont = self.m_pcTDecBinIf.decodeBin(uiCont, pcSCModel[iOffset])
            uiSymbol += 1
            if not uiCont:
                break

        ruiSymbol = uiSymbol
        return ruiSymbol

    def xReadUnaryMaxSymbol(self, ruiSymbol, pcSCModel, iOffset, uiMaxSymbol):
        if uiMaxSymbol == 0:
            ruiSymbol = 0
            return ruiSymbol

        ruiSymbol = self.m_pcTDecBinIf.decodeBin(ruiSymbol, pcSCModel[0])

        if ruiSymbol == 0 or uiMaxSymbol == 1:
            return ruiSymbol

        uiSymbol = 0
        uiCont = 0

        while True:
            uiCont = self.m_pcTDecBinIf.decodeBin(uiCont, pcSCModel[iOffset])
            uiSymbol += 1
            if not (uiCont and uiSymbol < uiMaxSymbol-1):
                break

        if uiCont and uiSymbol == uiMaxSymbol-1:
            uiSymbol += 1

        ruiSymbol = uiSymbol
        return ruiSymbol

    def xReadEpExGolomb(self, ruiSymbol, uiCount):
        uiSymbol = 0
        uiBit = 1

        while uiBit:
            uiBit = self.m_pcTDecBinIf.decodeBinEP(uiBit)
            uiSymbol += uiBit << uiCount
            uiCount += 1

        uiCount -= 1
        if uiCount:
            bins = 0
            bins = self.m_pcTDecBinIf.decodeBinsEP(bins, uiCount)
            uiSymbol += bins

        ruiSymbol = uiSymbol
        return ruiSymbol

    def xReadCoefRemainExGolomb(self, rSymbol, rParam):
        prefix = 0
        codeWord = 0

        while True:
            prefix += 1
            codeWord = self.m_pcTDecBinIf.decodeBinEP(codeWord)
            if not codeWord:
                break

        codeWord = 1 - codeWord
        prefix -= codeWord
        codeWord = 0
        if prefix < COEF_REMAIN_BIN_REDUCTION:
            codeWord = self.m_pcTDecBinIf.decodeBinsEP(codeWord, rParam)
            rSymbol = (prefix << rParam) + codeWord
        else:
            codeWord = self.m_pcTDecBinIf.decodeBinsEP(codeWord,
                prefix - COEF_REMAIN_BIN_REDUCTION + rParam)
            rSymbol = (((1 << (prefix - COEF_REMAIN_BIN_REDUCTION)) + 
                        COEF_REMAIN_BIN_REDUCTION - 1) << rParam) + codeWord

        return rSymbol, rParam

    def parseSkipFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        if pcCU.getSlice().isIntra():
            return

        uiCtxSkip = pcCU.getCtxSkipFlag(uiAbsPartIdx)
        uiSymbol = 0
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUSkipFlagSCModel.get(0, 0, uiCtxSkip))

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tSkipFlag')
            Trace.DTRACE_CABAC_T('\tuiCtxSkip: ')
            Trace.DTRACE_CABAC_V(uiCtxSkip)
            Trace.DTRACE_CABAC_T('\tuiSymbol: ')
            Trace.DTRACE_CABAC_V(uiSymbol)
            Trace.DTRACE_CABAC_T('\n')

        if uiSymbol:
            pcCU.setSkipFlagSubParts(True, uiAbsPartIdx, uiDepth)
            pcCU.setPredModeSubParts(MODE_INTER, uiAbsPartIdx, uiDepth)
            pcCU.setPartSizeSubParts(SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
            pcCU.setSizeSubParts(cvar.g_uiMaxCUWidth>>uiDepth, cvar.g_uiMaxCUHeight>>uiDepth, uiAbsPartIdx, uiDepth)
            pcCU.setMergeFlagSubParts(True, uiAbsPartIdx, 0, uiDepth)

    def parseCUTransquantBypassFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        uiSymbol = 0
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_CUTransquantBypassFlagSCModel.get(0, 0, 0))
        pcCU.setCUTransquantBypassSubParts(True if uiSymbol else False, uiAbsPartIdx, uiDepth)

    def parseSplitFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        if uiDepth == cvar.g_uiMaxCUDepth - cvar.g_uiAddCUDepth:
            pcCU.setDepthSubParts(uiDepth, uiAbsPartIdx)
            return

        uiSymbol = 0
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUSplitFlagSCModel.get(0, 0, pcCU.getCtxSplitFlag(uiAbsPartIdx, uiDepth)))
        pcCU.setDepthSubParts(uiDepth + uiSymbol, uiAbsPartIdx)

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tSplitFlag\n')

    def parseMergeFlag(self, pcCU, uiAbsPartIdx, uiDepth, uiPUIdx):
        uiSymbol = 0
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUMergeFlagExtSCModel.get(0)[0])
        pcCU.setMergeFlagSubParts(True if uiSymbol else False, uiAbsPartIdx, uiPUIdx, uiDepth)

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tMergeFlag: ')
            Trace.DTRACE_CABAC_V(uiSymbol)
            Trace.DTRACE_CABAC_T('\tAddress: ')
            Trace.DTRACE_CABAC_V(pcCU.getAddr())
            Trace.DTRACE_CABAC_T('\tuiAbsPartIdx: ')
            Trace.DTRACE_CABAC_V(uiAbsPartIdx)
            Trace.DTRACE_CABAC_T('\n')

    def parseMergeIndex(self, pcCU, ruiMergeIdx):
        uiUnaryIdx = 0
        uiNumCand = pcCU.getSlice().getMaxNumMergeCand()
        if uiNumCand > 1:
            while uiUnaryIdx < uiNumCand-1:
                uiSymbol = 0
                if uiUnaryIdx == 0:
                    uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, self.m_cCUMergeIdxExtSCModel.get(0, 0, 0))
                else:
                    uiSymbol = self.m_pcTDecBinIf.decodeBinEP(uiSymbol)
                if uiSymbol == 0:
                    break
                uiUnaryIdx += 1
        ruiMergeIdx = uiUnaryIdx

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tparseMergeIndex()')
            Trace.DTRACE_CABAC_T('\tuiMRGIdx= ')
            Trace.DTRACE_CABAC_V(ruiMergeIdx)
            Trace.DTRACE_CABAC_T('\n')

        return ruiMergeIdx

    def parsePartSize(self, pcCU, uiAbsPartIdx, uiDepth):
        uiSymbol = uiMode = 0
        eMode = 0

        if pcCU.isIntra(uiAbsPartIdx):
            uiSymbol = 1
            if uiDepth == cvar.g_uiMaxCUDepth - cvar.g_uiAddCUDepth:
                uiSymbol = self.m_pcTDecBinIf.decodeBin(
                    uiSymbol, self.m_cCUPartSizeSCModel.get(0, 0, 0))
            eMode = SIZE_2Nx2N if uiSymbol else SIZE_NxN
            uiTrLevel = 0
            uiWidthInBit = g_aucConvertToBit[pcCU.getWidth(uiAbsPartIdx)] + 2
            uiTrSizeInBit = g_aucConvertToBit[pcCU.getSlice().getSPS().getMaxTrSize()] + 2
            uiTrLevel = uiWidthInBit - uiTrSizeInBit if uiWidthInBit >= uiTrSizeInBit else 0
            if eMode == SIZE_NxN:
                pcCU.setTrIdxSubParts(1 + uiTrLevel, uiAbsPartIdx, uiDepth)
            else:
                pcCU.setTrIdxSubParts(uiTrLevel, uiAbsPartIdx, uiDepth)
        else:
            uiMaxNumBits = 2
            if uiDepth == cvar.g_uiMaxCUDepth - cvar.g_uiAddCUDepth and \
               not ((cvar.g_uiMaxCUWidth >> uiDepth) == 8 and
                    (cvar.g_uiMaxCUHeight >> uiDepth) == 8):
                uiMaxNumBits += 1
            for ui in xrange(uiMaxNumBits):
                uiSymbol = self.m_pcTDecBinIf.decodeBin(
                    uiSymbol, self.m_cCUPartSizeSCModel.get(0, 0, ui))
                if uiSymbol:
                    break
                uiMode += 1
            eMode = uiMode
            if pcCU.getSlice().getSPS().getAMPAcc(uiDepth):
                if eMode == SIZE_2NxN:
                    uiSymbol = self.m_pcTDecBinIf.decodeBin(
                        uiSymbol, self.m_cCUAMPSCModel.get(0, 0, 0))
                    if uiSymbol == 0:
                        uiSymbol = self.m_pcTDecBinIf.decodeBinEP(uiSymbol)
                        eMode = SIZE_2NxnU if uiSymbol == 0 else SIZE_2NxnD
                elif eMode == SIZE_Nx2N:
                    uiSymbol = self.m_pcTDecBinIf.decodeBin(
                        uiSymbol, self.m_cCUAMPSCModel.get(0, 0, 0))
                    if uiSymbol == 0:
                        uiSymbol = self.m_pcTDecBinIf.decodeBinEP(uiSymbol)
                        eMode = SIZE_nLx2N if uiSymbol == 0 else SIZE_nRx2N
        pcCU.setPartSizeSubParts(eMode, uiAbsPartIdx, uiDepth)
        pcCU.setSizeSubParts(cvar.g_uiMaxCUWidth>>uiDepth, cvar.g_uiMaxCUHeight>>uiDepth, uiAbsPartIdx, uiDepth)

    def parsePredMode(self, pcCU, uiAbsPartIdx, uiDepth):
        if pcCU.getSlice().isIntra():
            pcCU.setPredModeSubParts(MODE_INTRA, uiAbsPartIdx, uiDepth)
            return

        uiSymbol = 0
        iPredMode = MODE_INTER
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUPredModeSCModel.get(0, 0, 0))
        iPredMode += uiSymbol
        pcCU.setPredModeSubParts(iPredMode, uiAbsPartIdx, uiDepth)

    def parseIntraDirLumaAng(self, pcCU, absPartIdx, depth):
        mode = pcCU.getPartitionSize(absPartIdx)
        partNum = 4 if mode == SIZE_NxN else 1
        partOffset = (pcCU.getPic().getNumPartInCU() >> (pcCU.getDepth(absPartIdx)<<1)) >> 2
        mpmPred = 4 * [0]
        symbol = 0
        intraPredMode = 0

        if mode == SIZE_NxN:
            depth += 1
        for j in xrange(partNum):
            symbol = self.m_pcTDecBinIf.decodeBin(
                symbol, self.m_cCUIntraPredSCModel.get(0, 0, 0))
            mpmPred[j] = symbol
        for j in xrange(partNum):
            preds = ArrayInt(3)
            for i in xrange(3):
                preds[i] = -1
            predNum = pcCU.getIntraDirLumaPredictor(absPartIdx + partOffset * j, preds.cast())
            if mpmPred[j]:
                symbol = self.m_pcTDecBinIf.decodeBinEP(symbol)
                if symbol:
                    symbol = self.m_pcTDecBinIf.decodeBinEP(symbol)
                    symbol += 1
                intraPredMode = preds[symbol]
            else:
                intraPredMode = 0
                symbol = self.m_pcTDecBinIf.decodeBinsEP(symbol, 5)
                intraPredMode = symbol

                #postponed sorting of MPMs (only in remaining branch)
                if preds[0] > preds[1]:
                    preds[0], preds[1] = preds[1], preds[0]
                if preds[0] > preds[2]:
                    preds[0], preds[2] = preds[2], preds[0]
                if preds[1] > preds[2]:
                    preds[1], preds[2] = preds[2], preds[1]
                for i in xrange(predNum):
                    intraPredMode += (1 if intraPredMode >= preds[i] else 0)
            pcCU.setLumaIntraDirSubParts(intraPredMode, absPartIdx + partOffset * j, depth)

    def parseIntraDirChroma(self, pcCU, uiAbsPartIdx, uiDepth):
        uiSymbol = 0
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUChromaPredSCModel.get(0, 0, 0))

        if uiSymbol == 0:
            uiSymbol = DM_CHROMA_IDX
        else:
            uiIPredMode = 0
            uiIPredMode = self.m_pcTDecBinIf.decodeBinsEP(uiIPredMode, 2)
            uiAllowedChromaDir = ArrayUInt(NUM_CHROMA_MODE)
            pcCU.getAllowedChromaDir(uiAbsPartIdx, uiAllowedChromaDir.cast())
            uiSymbol = uiAllowedChromaDir[uiIPredMode]
        pcCU.setChromIntraDirSubParts(uiSymbol, uiAbsPartIdx, uiDepth)

    def parseInterDir(self, pcCU, ruiInterDir, uiAbsPartIdx):
        uiCtx = pcCU.getCtxInterDir(uiAbsPartIdx)
        pCtx = self.m_cCUInterDirSCModel.get(0)
        uiSymbol = 0
        if pcCU.getPartitionSize(uiAbsPartIdx) == SIZE_2Nx2N or \
           pcCU.getHeight(uiAbsPartIdx) != 8:
            uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, pCtx[uiCtx])

        if uiSymbol:
            uiSymbol = 2
        else:
            uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, pCtx[4])
            assert(uiSymbol == 0 or uiSymbol == 1)

        uiSymbol += 1
        ruiInterDir = uiSymbol
        return ruiInterDir

    def parseRefFrmIdx(self, pcCU, riRefFrmIdx, eRefList):
        uiSymbol = 0
        pCtx = self.m_cCURefPicSCModel.get(0)
        uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, pCtx[0])

        if uiSymbol:
            uiRefNum = pcCU.getSlice().getNumRefIdx(eRefList) - 2
            pCtx += 1
            ui = 0
            while ui < uiRefNum:
                if ui == 0:
                    uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, pCtx[0])
                else:
                    uiSymbol = self.m_pcTDecBinIf.decodeBinEP(uiSymbol)
                if uiSymbol == 0:
                    break
                ui += 1
            uiSymbol = ui + 1
        riRefFrmIdx = uiSymbol
        return riRefFrmIdx

    def parseMvd(self, pcCU, uiAbsPartIdx, uiPartIdx, uiDepth, eRefList):
        uiSymbol = 0
        uiHorAbs = uiHorSign = 0
        uiVerAbs = uiVerSign = 0
        pCtx = self.m_cCUMvdSCModel.get(0)

        if pcCU.getSlice().getMvdL1ZeroFlag() and \
           eRefList == REF_PIC_LIST_1 and pcCU.getInterDir(uiAbsPartIdx) == 3:
            uiHorAbs = 0
            uiVerAbs = 0
        else:
            uiHorAbs = self.m_pcTDecBinIf.decodeBin(uiHorAbs, pCtx[0])
            uiVerAbs = self.m_pcTDecBinIf.decodeBin(uiVerAbs, pCtx[0])

            bHorAbsGr0 = uiHorAbs != 0
            bVerAbsGr0 = uiVerAbs != 0
            pCtx += 1

            if bHorAbsGr0:
                uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, pCtx[0])
                uiHorAbs += uiSymbol

            if bVerAbsGr0:
                uiSymbol = self.m_pcTDecBinIf.decodeBin(uiSymbol, pCtx[0])
                uiVerAbs += uiSymbol

            if bHorAbsGr0:
                if uiHorAbs == 2:
                    uiSymbol = self.xReadEpExGolomb(uiSymbol, 1)
                    uiHorAbs += uiSymbol

                uiHorSign = self.m_pcTDecBinIf.decodeBinEP(uiHorSign)

            if bVerAbsGr0:
                if uiVerAbs == 2:
                    uiSymbol = self.xReadEpExGolomb(uiSymbol, 1)
                    uiVerAbs += uiSymbol

                uiVerSign = self.m_pcTDecBinIf.decodeBinEP(uiVerSign)

        cMv = TComMv(-uiHorAbs if uiHorSign else uiHorAbs,
                     -uiVerAbs if uiVerSign else uiVerAbs)
        pcCU.getCUMvField(eRefList).setAllMvd(
            cMv, pcCU.getPartitionSize(uiAbsPartIdx), uiAbsPartIdx, uiDepth, uiPartIdx)

    def parseTransformSubdivFlag(self, ruiSubdivFlag, uiLog2TransformBlockSize):
        ruiSubdivFlag = self.m_pcTDecBinIf.decodeBin(
            ruiSubdivFlag, self.m_cCUTransSubdivFlagSCModel.get(0, 0, uiLog2TransformBlockSize))

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tparseTransformSubdivFlag()')
            Trace.DTRACE_CABAC_T('\tsymbol=')
            Trace.DTRACE_CABAC_V(ruiSubdivFlag)
            Trace.DTRACE_CABAC_T('\tctx=')
            Trace.DTRACE_CABAC_V(uiLog2TransformBlockSize)
            Trace.DTRACE_CABAC_T('\n')

        return ruiSubdivFlag

    def parseQtCbf(self, pcCU, uiAbsPartIdx, eType, uiTrDepth, uiDepth):
        uiSymbol = 0
        uiCtx = pcCU.getCtxQtCbf(eType, uiTrDepth)
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUQtCbfSCModel.get(0, TEXT_CHROMA if eType else eType, uiCtx))

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tparseQtCbf()')
            Trace.DTRACE_CABAC_T('\tsymbol=')
            Trace.DTRACE_CABAC_V(uiSymbol)
            Trace.DTRACE_CABAC_T('\tctx=')
            Trace.DTRACE_CABAC_V(uiCtx)
            Trace.DTRACE_CABAC_T('\tetype=')
            Trace.DTRACE_CABAC_V(eType)
            Trace.DTRACE_CABAC_T('\tuiAbsPartIdx=')
            Trace.DTRACE_CABAC_V(uiAbsPartIdx)
            Trace.DTRACE_CABAC_T('\n')

        pcCU.setCbfSubParts(uiSymbol<<uiTrDepth, eType, uiAbsPartIdx, uiDepth)

    def parseQtRootCbf(self, uiAbsPartIdx, uiQtRootCbf):
        uiSymbol = 0
        uiCtx = 0
        uiSymbol = self.m_pcTDecBinIf.decodeBin(
            uiSymbol, self.m_cCUQtRootCbfSCModel.get(0, 0, uiCtx))

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tparseQtRootCbf()')
            Trace.DTRACE_CABAC_T('\tsymbol=')
            Trace.DTRACE_CABAC_V(uiSymbol)
            Trace.DTRACE_CABAC_T('\tctx=')
            Trace.DTRACE_CABAC_V(uiCtx)
            Trace.DTRACE_CABAC_T('\tuiAbsPartIdx=')
            Trace.DTRACE_CABAC_V(uiAbsPartIdx)
            Trace.DTRACE_CABAC_T('\n')

        uiQtRootCbf = uiSymbol
        return uiQtRootCbf

    def parseDeltaQp(self, pcCU, uiAbsPartIdx, uiDepth):
        qp = 0
        uiDQp = 0
        iDQp = 0

        uiSymbol = 0

        uiDQp = self.xReadUnaryMaxSymbol(
            uiDQp, self.m_cCUDeltaQpSCModel.get(0, 0, 0), 1, CU_DQP_TU_CMAX)

        if uiDQp >= CU_DQP_TU_CMAX:
            uiSymbol = self.xReadEpExGolomb(uiSymbol, CU_DQP_EG_k)
            uiDQp += uiSymbol

        if uiDQp > 0:
            uiSign = 0
            qpBdOffsetY = pcCU.getSlice().getSPS().getQpBDOffsetY()
            uiSign = self.m_pcTDecBinIf.decodeBinEP(uiSign)
            iDQp = uiDQp
            if uiSign:
                iDQp = -iDQp
            qp = ((pcCU.getRefQP(uiAbsPartIdx) + iDQp + 52 + 2 * qpBdOffsetY) % \
                  (52 + qpBdOffsetY)) - qpBdOffsetY
        else:
            iDQp = 0
            qp = pcCU.getRefQP(uiAbsPartIdx)
        pcCU.setQPSubParts(qp, uiAbsPartIdx, uiDepth)
        pcCU.setCodedQP(qp)

    def parseIPCMInfo(self, pcCU, uiAbsPartIdx, uiDepth):
        uiSymbol = 0
        readPCMSampleFlag = False

        uiSymbol = self.m_pcTDecBinIf.decodeBinTrm(uiSymbol)

        if uiSymbol:
            readPCMSampleFlag = True
            self.m_pcTDecBinIf.decodePCMAlignBits()

        if readPCMSampleFlag == True:
            bIpcmFlag = True

            pcCU.setPartSizeSubParts(SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
            pcCU.setSizeSubParts(cvar.g_uiMaxCUWidth>>uiDepth, cvar.g_uiMaxCUHeight>>uiDepth, uiAbsPartIdx, uiDepth)
            pcCU.setTrIdxSubParts(0, uiAbsPartIdx, uiDepth)
            pcCU.setIPCMFlagSubParts(bIpcmFlag, uiAbsPartIdx, uiDepth)

            uiMinCoeffSize = pcCU.getPic().getMinCUWidth() * pcCU.getPic().getMinCUHeight()
            uiLumaOffset = uiMinCoeffSize * uiAbsPartIdx
            uiChromaOffset = uiLumaOffset >> 2

            piPCMSample = pointer(pcCU.getPCMSampleY(), type='short *') + uiLumaOffset
            uiWidth = pcCU.getWidth(uiAbsPartIdx)
            uiHeight = pcCU.getHeight(uiAbsPartIdx)
            uiSampleBits = pcCU.getSlice().getSPS().getPCMBitDepthLuma()

            for uiY in xrange(uiHeight):
                for uiX in xrange(uiWidth):
                    uiSample = 0
                    uiSample = self.m_pcTDecBinIf.xReadPCMCode(uiSampleBits, uiSample)
                    piPCMSample[uiX] = uiSample
                piPCMSample += uiWidth

            piPCMSample = pointer(pcCU.getPCMSampleCb(), type='short *') + uiChromaOffset
            uiWidth = pcCU.getWidth(uiAbsPartIdx) / 2
            uiHeight = pcCU.getHeight(uiAbsPartIdx) / 2
            uiSampleBits = pcCU.getSlice().getSPS().getPCMBitDepthChroma()

            for uiY in xrange(uiHeight):
                for uiX in xrange(uiWidth):
                    uiSample = 0
                    uiSample = self.m_pcTDecBinIf.xReadPCMCode(uiSampleBits, uiSample)
                    piPCMSample[uiX] = uiSample
                piPCMSample += uiWidth

            piPCMSample = pointer(pcCU.getPCMSampleCr(), type='short *') + uiChromaOffset
            uiWidth = pcCU.getWidth(uiAbsPartIdx) / 2
            uiHeight = pcCU.getHeight(uiAbsPartIdx) / 2
            uiSampleBits = pcCU.getSlice().getSPS().getPCMBitDepthChroma()

            for uiY in xrange(uiHeight):
                for uiX in xrange(uiWidth):
                    uiSample = 0
                    uiSample = self.m_pcTDecBinIf.xReadPCMCode(uiSampleBits, uiSample)
                    piPCMSample[uiX] = uiSample
                piPCMSample += uiWidth

            self.m_pcTDecBinIf.resetBac()

    def parseLastSignificantXY(self, uiPosLastX, uiPosLastY, width, height, eTType, uiScanIdx):
        uiLast = 0
        pCtxX = self.m_cCUCtxLastX.get(0, eTType)
        pCtxY = self.m_cCUCtxLastY.get(0, eTType)

        blkSizeOffsetX = 0 if eTType else g_aucConvertToBit[width] * 3 + ((g_aucConvertToBit[width]+1)>>2)
        blkSizeOffsetY = 0 if eTType else g_aucConvertToBit[height] * 3 + ((g_aucConvertToBit[height]+1)>>2)
        shiftX = g_aucConvertToBit[width] if eTType else (g_aucConvertToBit[width]+3)>>2
        shiftY = g_aucConvertToBit[height] if eTType else (g_aucConvertToBit[height]+3)>>2
        # posX
        uiPosLastX = 0
        while uiPosLastX < g_uiGroupIdx[width-1]:
            uiLast = self.m_pcTDecBinIf.decodeBin(
                uiLast, pCtxX[blkSizeOffsetX + (uiPosLastX>>shiftX)])
            if not uiLast:
                break
            uiPosLastX += 1

        # posY
        uiPosLastY = 0
        while uiPosLastY < g_uiGroupIdx[height-1]:
            uiLast = self.m_pcTDecBinIf.decodeBin(
                uiLast, pCtxY[blkSizeOffsetY + (uiPosLastY>>shiftY)])
            if not uiLast:
                break
            uiPosLastY += 1

        if uiPosLastX > 3:
            uiTemp = 0
            uiCount = (uiPosLastX-2) >> 1
            for i in xrange(uiCount-1, -1, -1):
                uiLast = self.m_pcTDecBinIf.decodeBinEP(uiLast)
                uiTemp += uiLast << i
            uiPosLastX = g_uiMinInGroup[uiPosLastX] + uiTemp
        if uiPosLastY > 3:
            uiTemp = 0
            uiCount = (uiPosLastY-2) >> 1
            for i in xrange(uiCount-1, -1, -1):
                uiLast = self.m_pcTDecBinIf.decodeBinEP(uiLast)
                uiTemp += uiLast << i
            uiPosLastY = g_uiMinInGroup[uiPosLastY] + uiTemp

        if uiScanIdx == SCAN_VER:
            uiPosLastX, uiPosLastY = uiPosLastY, uiPosLastX

        return uiPosLastX, uiPosLastY

    def parseCoeffNxN(self, pcCU, pcCoef, uiAbsPartIdx, uiWidth, uiHeight, uiDepth, eTType):
        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tparseCoeffNxN()\teType=')
            Trace.DTRACE_CABAC_V(eTType)
            Trace.DTRACE_CABAC_T('\twidth=')
            Trace.DTRACE_CABAC_V(uiWidth)
            Trace.DTRACE_CABAC_T('\theight=')
            Trace.DTRACE_CABAC_V(uiHeight)
            Trace.DTRACE_CABAC_T('\tdepth=')
            Trace.DTRACE_CABAC_V(uiDepth)
            Trace.DTRACE_CABAC_T('\tabspartidx=')
            Trace.DTRACE_CABAC_V(uiAbsPartIdx)
            Trace.DTRACE_CABAC_T('\ttoCU-X=')
            Trace.DTRACE_CABAC_V(pcCU.getCUPelX())
            Trace.DTRACE_CABAC_T('\ttoCU-Y=')
            Trace.DTRACE_CABAC_V(pcCU.getCUPelY())
            Trace.DTRACE_CABAC_T('\tCU-addr=')
            Trace.DTRACE_CABAC_V(pcCU.getAddr())
            Trace.DTRACE_CABAC_T('\tinCU-X=')
            Trace.DTRACE_CABAC_V(g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]])
            Trace.DTRACE_CABAC_T('\tinCU-Y=')
            Trace.DTRACE_CABAC_V(g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]])
            Trace.DTRACE_CABAC_T('\tpredmode=')
            Trace.DTRACE_CABAC_V(pcCU.getPredictionMode(uiAbsPartIdx))
            Trace.DTRACE_CABAC_T('\n')

        pcCoef = pointer(pcCoef, type='int *')

        if uiWidth > pcCU.getSlice().getSPS().getMaxTrSize():
            uiWidth = pcCU.getSlice().getSPS().getMaxTrSize()
            uiHeight = pcCU.getSlice().getSPS().getMaxTrSize()
        if pcCU.getSlice().getPPS().getUseTransformSkip():
            self.parseTransformSkipFlags(pcCU, uiAbsPartIdx, uiWidth, uiHeight, uiDepth, eTType)

        eTType = TEXT_LUMA if eTType == TEXT_LUMA else \
                 TEXT_NONE if eTType == TEXT_NONE else TEXT_CHROMA

        #----- parse significance map -----
        uiLog2BlockSize = g_aucConvertToBit[uiWidth] + 2
        uiMaxNumCoeff = uiWidth * uiHeight
        uiMaxNumCoeffM1 = uiMaxNumCoeff - 1
        uiScanIdx = pcCU.getCoefScanIdx(uiAbsPartIdx, uiWidth, eTType==TEXT_LUMA, pcCU.isIntra(uiAbsPartIdx))

        #===== decode last significant =====
        uiPosLastX = uiPosLastY = 0
        uiPosLastX, uiPosLastY = self.parseLastSignificantXY(uiPosLastX, uiPosLastY, uiWidth, uiHeight, eTType, uiScanIdx)
        uiBlkPosLast = uiPosLastX + (uiPosLastY << uiLog2BlockSize)
        pcCoef[uiBlkPosLast] = 1

        #===== decode significance flags =====
        uiScanPosLast = uiBlkPosLast
        scan = g_auiSigLastScan[uiScanIdx][uiLog2BlockSize-1]
        uiScanPosLast = 0
        while uiScanPosLast < uiMaxNumCoeffM1:
            uiBlkPos = scan[uiScanPosLast]
            if uiBlkPosLast == uiBlkPos:
                break
            uiScanPosLast += 1

        baseCoeffGroupCtx = self.m_cCUSigCoeffGroupSCModel.get(0, eTType)
        baseCtx = self.m_cCUSigSCModel.get(0, 0) if eTType == TEXT_LUMA else \
                  self.m_cCUSigSCModel.get(0, 0) + NUM_SIG_FLAG_CTX_LUMA

        iLastScanSet = uiScanPosLast >> LOG2_SCAN_SET_SIZE
        c1 = 1
        uiGoRiceParam = 0

        beValid = False
        if pcCU.getCUTransquantBypass(uiAbsPartIdx):
            beValid = False
        else:
            beValid = pcCU.getSlice().getPPS().getSignHideFlag() > 0
        absSum = 0

        uiSigCoeffGroupFlag = ArrayUInt(MLS_GRP_NUM)
        for i in xrange(MLS_GRP_NUM):
            uiSigCoeffGroupFlag[i] = 0
        uiNumBlkSide = uiWidth >> (MLS_CG_SIZE >> 1)
        scanCG = g_auiSigLastScan[uiScanIdx][uiLog2BlockSize-2-1 if uiLog2BlockSize > 3 else 0]
        if uiLog2BlockSize == 3:
            scanCG = g_sigLastScan8x8[uiScanIdx]
        elif uiLog2BlockSize == 5:
            scanCG = g_sigLastScanCG32x32
        iScanPosSig = uiScanPosLast
        for iSubSet in xrange(iLastScanSet, -1, -1):
            iSubPos = iSubSet << LOG2_SCAN_SET_SIZE
            uiGoRiceParam = 0
            numNonZero = 0

            lastNZPosInCG = -1
            firstNZPosInCG = SCAN_SET_SIZE

            pos = SCAN_SET_SIZE * [0]
            if iScanPosSig == uiScanPosLast:
                lastNZPosInCG = iScanPosSig
                firstNZPosInCG = iScanPosSig
                iScanPosSig -= 1
                pos[numNonZero] = uiBlkPosLast
                numNonZero = 1

            # decode significant_coeffgroup_flag
            iCGBlkPos = scanCG[iSubSet]
            iCGPosY = iCGBlkPos // uiNumBlkSide
            iCGPosX = iCGBlkPos - (iCGPosY * uiNumBlkSide)
            if iSubSet == iLastScanSet or iSubSet == 0:
                uiSigCoeffGroupFlag[iCGBlkPos] = 1
            else:
                uiSigCoeffGroup = 0
                uiCtxSig = TComTrQuant.getSigCoeffGroupCtxInc(
                    uiSigCoeffGroupFlag.cast(), iCGPosX, iCGPosY, uiWidth, uiHeight)
                uiSigCoeffGroup = self.m_pcTDecBinIf.decodeBin(uiSigCoeffGroup, baseCoeffGroupCtx[uiCtxSig])
                uiSigCoeffGroupFlag[iCGBlkPos] = uiSigCoeffGroup

            # decode significant_coeff_flag
            patternSigCtx = TComTrQuant.calcPatternSigCtx(
                uiSigCoeffGroupFlag.cast(), iCGPosX, iCGPosY, uiWidth, uiHeight)
            while iScanPosSig >= iSubPos:
                uiBlkPos = scan[iScanPosSig]
                uiPosY = uiBlkPos >> uiLog2BlockSize
                uiPosX = uiBlkPos - (uiPosY << uiLog2BlockSize)
                uiSig = 0

                if uiSigCoeffGroupFlag[iCGBlkPos]:
                    if iScanPosSig > iSubPos or iSubSet == 0 or numNonZero:
                        uiCtxSig = TComTrQuant.getSigCtxInc(
                            patternSigCtx, uiScanIdx, uiPosX, uiPosY, uiLog2BlockSize, eTType)
                        uiSig = self.m_pcTDecBinIf.decodeBin(uiSig, baseCtx[uiCtxSig])
                    else:
                        uiSig = 1
                pcCoef[uiBlkPos] = uiSig
                if uiSig:
                    pos[numNonZero] = uiBlkPos
                    numNonZero += 1
                    if lastNZPosInCG == -1:
                        lastNZPosInCG = iScanPosSig
                    firstNZPosInCG = iScanPosSig
                iScanPosSig -= 1

            if numNonZero:
                signHidden = lastNZPosInCG - firstNZPosInCG >= SBH_THRESHOLD
                absSum = 0
                uiCtxSet = 2 if iSubSet > 0 and eTType == TEXT_LUMA else 0
                uiBin = 0
                if c1 == 0:
                    uiCtxSet += 1
                c1 = 1
                baseCtxMod = \
                    self.m_cCUOneSCModel.get(0, 0) + 4 * uiCtxSet if eTType == TEXT_LUMA else \
                    self.m_cCUOneSCModel.get(0, 0) + NUM_ONE_FLAG_CTX_LUMA + 4 * uiCtxSet
                absCoeff = SCAN_SET_SIZE * [0]

                for i in xrange(numNonZero):
                    absCoeff[i] = 1
                numC1Flag = min(numNonZero, C1FLAG_NUMBER)
                firstC2FlagIdx = -1

                for idx in xrange(numC1Flag):
                    uiBin = self.m_pcTDecBinIf.decodeBin(uiBin, baseCtxMod[c1])
                    if uiBin == 1:
                        c1 = 0
                        if firstC2FlagIdx == -1:
                            firstC2FlagIdx = idx
                    elif c1 < 3 and c1 > 0:
                        c1 += 1
                    absCoeff[idx] = uiBin + 1

                if c1 == 0:
                    baseCtxMod = \
                        self.m_cCUAbsSCModel.get(0, 0) + uiCtxSet if eTType == TEXT_LUMA else \
                        self.m_cCUAbsSCModel.get(0, 0) + NUM_ABS_FLAG_CTX_LUMA + uiCtxSet
                    if firstC2FlagIdx != -1:
                        uiBin = self.m_pcTDecBinIf.decodeBin(uiBin, baseCtxMod[0])
                        absCoeff[firstC2FlagIdx] = uiBin + 2

                coeffSigns = 0
                if signHidden and beValid:
                    coeffSigns = self.m_pcTDecBinIf.decodeBinsEP(coeffSigns, numNonZero-1)
                    coeffSigns <<= 32 - (numNonZero-1)
                else:
                    coeffSigns = self.m_pcTDecBinIf.decodeBinsEP(coeffSigns, numNonZero)
                    coeffSigns <<= 32 - numNonZero

                iFirstCoeff2 = 1
                if c1 == 0 or numNonZero > C1FLAG_NUMBER:
                    for idx in xrange(numNonZero):
                        baseLevel = (2 + iFirstCoeff2) if idx < C1FLAG_NUMBER else 1

                        if absCoeff[idx] == baseLevel:
                            uiLevel = 0
                            uiLevel, uiGoRiceParam = self.xReadCoefRemainExGolomb(uiLevel, uiGoRiceParam)
                            absCoeff[idx] = uiLevel + baseLevel
                            if absCoeff[idx] > 3 * (1 << uiGoRiceParam):
                                uiGoRiceParam = min(uiGoRiceParam+1, 4)

                        if absCoeff[idx] >= 2:
                            iFirstCoeff2 = 0

                for idx in xrange(numNonZero):
                    blkPos = pos[idx]
                    # Signs applied later.
                    pcCoef[blkPos] = absCoeff[idx]
                    absSum += absCoeff[idx]

                    if idx == numNonZero-1 and signHidden and beValid:
                        # Infer sign of 1st element.
                        if absSum & 0x01:
                            pcCoef[blkPos] = - pcCoef[blkPos]
                    else:
                        sign = -1 if coeffSigns >> 31 else 0
                        pcCoef[blkPos] = (pcCoef[blkPos] ^ sign) - sign
                        coeffSigns <<= 1
                        coeffSigns &= 0xFFFFFFFF

    def parseTransformSkipFlags(self, pcCU, uiAbsPartIdx, width, height, uiDepth, eTType):
        if pcCU.getCUTransquantBypass(uiAbsPartIdx):
            return

        if width != 4 or height != 4:
            return

        useTransformSkip = 0
        useTransformSkip = self.m_pcTDecBinIf.decodeBin(
            useTransformSkip, self.m_cTransformSkipSCModel.get(0, TEXT_CHROMA if eTType else TEXT_LUMA, 0))
        if eTType != TEXT_LUMA:
            uiLog2TrafoSize = g_aucConvertToBit[pcCU.getSlice().getSPS().getMaxCUWidth()] + 2 - uiDepth
            if uiLog2TrafoSize == 2:
                uiDepth -= 1

        if Trace.on:
            Trace.DTRACE_CABAC_VL(Trace.g_nSymbolCounter)
            Trace.g_nSymbolCounter += 1
            Trace.DTRACE_CABAC_T('\tparseTransformSkip()')
            Trace.DTRACE_CABAC_T('\tsymbol=')
            Trace.DTRACE_CABAC_V(useTransformSkip)
            Trace.DTRACE_CABAC_T('\tAddr=')
            Trace.DTRACE_CABAC_V(pcCU.getAddr())
            Trace.DTRACE_CABAC_T('\tetype=')
            Trace.DTRACE_CABAC_V(eTType)
            Trace.DTRACE_CABAC_T('\tuiAbsPartIdx=')
            Trace.DTRACE_CABAC_V(uiAbsPartIdx)
            Trace.DTRACE_CABAC_T('\n')

        pcCU.setTransformSkipSubParts(useTransformSkip, eTType, uiAbsPartIdx, uiDepth)

    def updateContextTables(self, eSliceType, iQp):
        uiBit = 0
        uiBit = self.m_pcTDecBinIf.decodeBinTrm(uiBit)
        self.m_pcTDecBinIf.finish()
        self.m_pcBitstream.readOutTrailingBits()

        self.m_cCUSplitFlagSCModel.initBuffer          (eSliceType, iQp, INIT_SPLIT_FLAG)
        self.m_cCUSkipFlagSCModel.initBuffer           (eSliceType, iQp, INIT_SKIP_FLAG);
        self.m_cCUMergeFlagExtSCModel.initBuffer       (eSliceType, iQp, INIT_MERGE_FLAG_EXT)
        self.m_cCUMergeIdxExtSCModel.initBuffer        (eSliceType, iQp, INIT_MERGE_IDX_EXT)
        self.m_cCUPartSizeSCModel.initBuffer           (eSliceType, iQp, INIT_PART_SIZE)
        self.m_cCUAMPSCModel.initBuffer                (eSliceType, iQp, INIT_CU_AMP_POS)
        self.m_cCUPredModeSCModel.initBuffer           (eSliceType, iQp, INIT_PRED_MODE);
        self.m_cCUIntraPredSCModel.initBuffer          (eSliceType, iQp, INIT_INTRA_PRED_MODE)
        self.m_cCUChromaPredSCModel.initBuffer         (eSliceType, iQp, INIT_CHROMA_PRED_MODE)
        self.m_cCUInterDirSCModel.initBuffer           (eSliceType, iQp, INIT_INTER_DIR)
        self.m_cCUMvdSCModel.initBuffer                (eSliceType, iQp, INIT_MVD)
        self.m_cCURefPicSCModel.initBuffer             (eSliceType, iQp, INIT_REF_PIC)
        self.m_cCUDeltaQpSCModel.initBuffer            (eSliceType, iQp, INIT_DQP)
        self.m_cCUQtCbfSCModel.initBuffer              (eSliceType, iQp, INIT_QT_CBF)
        self.m_cCUQtRootCbfSCModel.initBuffer          (eSliceType, iQp, INIT_QT_ROOT_CBF)
        self.m_cCUSigCoeffGroupSCModel.initBuffer      (eSliceType, iQp, INIT_SIG_CG_FLAG)
        self.m_cCUSigSCModel.initBuffer                (eSliceType, iQp, INIT_SIG_FLAG)
        self.m_cCUCtxLastX.initBuffer                  (eSliceType, iQp, INIT_LAST)
        self.m_cCUCtxLastY.initBuffer                  (eSliceType, iQp, INIT_LAST)
        self.m_cCUOneSCModel.initBuffer                (eSliceType, iQp, INIT_ONE_FLAG)
        self.m_cCUAbsSCModel.initBuffer                (eSliceType, iQp, INIT_ABS_FLAG)
        self.m_cMVPIdxSCModel.initBuffer               (eSliceType, iQp, INIT_MVP_IDX)
        self.m_cSaoMergeSCModel.initBuffer             (eSliceType, iQp, INIT_SAO_MERGE_FLAG)
        self.m_cSaoTypeIdxSCModel.initBuffer           (eSliceType, iQp, INIT_SAO_TYPE_IDX)
        self.m_cCUTransSubdivFlagSCModel.initBuffer    (eSliceType, iQp, INIT_TRANS_SUBDIV_FLAG)
        self.m_cTransformSkipSCModel.initBuffer        (eSliceType, iQp, INIT_TRANSFORMSKIP_FLAG)
        self.m_CUTransquantBypassFlagSCModel.initBuffer(eSliceType, iQp, INIT_CU_TRANSQUANT_BYPASS_FLAG)

        self.m_pcTDecBinIf.start()

    def parseScalingList(self, scalingList):
        pass
