# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecEntropy.py
    HM 8.0 Python Implementation
"""

import sys

from ... import pointer
from ... import trace

from ... import TComMv
from ... import ArrayTComMvField, ArrayUChar

from ..TLibCommon.TypeDef import (
    SIZE_2Nx2N, SIZE_NxN, MODE_INTER, MODE_INTRA,
    TEXT_LUMA, TEXT_CHROMA_U, TEXT_CHROMA_V,
    REF_PIC_LIST_0, REF_PIC_LIST_1, AM_EXPL
)

from ..TLibCommon.CommonDef import (NOT_VALID, MRG_MAX_NUM_CANDS)

from ..TLibCommon.TComRom import (g_auiPUOffset, g_aucConvertToBit)


class TDecEntropy(object):

    def __init__(self):
        self.m_pcEntropyDecoderIf = None
        self.m_pcPrediction = None
        self.m_uiBakAbsPartIdx = 0
        self.m_uiBakChromaOffset = 0
        self.m_bakAbsPartIdxCU = 0

    def init(self, p):
        self.m_pcPrediction = p

    def decodePUWise(self, pcCU, uiAbsPartIdx, uiDepth, pcSubCU):
        ePartSize = pcCU.getPartitionSize(uiAbsPartIdx)
        uiNumPU = 1 if ePartSize == SIZE_2Nx2N else 4 if ePartSize == SIZE_NxN else 2
        uiPUOffset = (g_auiPUOffset[ePartSize] <<
                      ((pcCU.getSlice().getSPS().getMaxCUDepth() - uiDepth) << 1)) >> 4

        cMvFieldNeighbours = ArrayTComMvField(MRG_MAX_NUM_CANDS<<1) # double length for mv of both lists
        uhInterDirNeighbours = ArrayUChar(MRG_MAX_NUM_CANDS)

        for ui in xrange(MRG_MAX_NUM_CANDS):
            uhInterDirNeighbours[ui] = 0
        numValidMergeCand = 0
        isMerged = False

        pcSubCU.copyInterPredInfoFrom(pcCU, uiAbsPartIdx, REF_PIC_LIST_0)
        pcSubCU.copyInterPredInfoFrom(pcCU, uiAbsPartIdx, REF_PIC_LIST_1)
        uiSubPartIdx = uiAbsPartIdx
        for uiPartIdx in xrange(uiNumPU):
            self.decodeMergeFlag(pcCU, uiSubPartIdx, uiDepth, uiPartIdx)
            if pcCU.getMergeFlag(uiSubPartIdx):
                self.decodeMergeIndex(pcCU, uiPartIdx, uiSubPartIdx, ePartSize,
                                      uhInterDirNeighbours.cast(), cMvFieldNeighbours.cast(), uiDepth)
                uiMergeIndex = pcCU.getMergeIndex(uiSubPartIdx)
                if pcCU.getSlice().getPPS().getLog2ParallelMergeLevelMinus2() and \
                   ePartSize != SIZE_2Nx2N and pcSubCU.getWidth(0) <= 8:
                    pcSubCU.setPartSizeSubParts(SIZE_2Nx2N, 0, uiDepth)
                    if not isMerged:
                        numValidMergeCand = pcSubCU.getInterMergeCandidates(0, 0, uiDepth,
                            cMvFieldNeighbours.cast(), uhInterDirNeighbours.cast(), numValidMergeCand)
                        isMerged = True
                    pcSubCU.setPartSizeSubParts(ePartSize, 0, uiDepth)
                else:
                    uiMergeIndex = pcCU.getMergeIndex(uiSubPartIdx)
                    numValidMergeCand = pcSubCU.getInterMergeCandidates(uiSubPartIdx-uiAbsPartIdx, uiPartIdx, uiDepth,
                        cMvFieldNeighbours.cast(), uhInterDirNeighbours.cast(), numValidMergeCand, uiMergeIndex)
                pcCU.setInterDirSubParts(uhInterDirNeighbours[uiMergeIndex], uiSubPartIdx, uiPartIdx, uiDepth)

                cTmpMv = TComMv(0, 0)
                for uiRefListIdx in xrange(2):
                    if pcCU.getSlice().getNumRefIdx(uiRefListIdx) > 0:
                        pcCU.setMVPIdxSubParts(0, uiRefListIdx, uiSubPartIdx, uiPartIdx, uiDepth)
                        pcCU.setMVPNumSubParts(0, uiRefListIdx, uiSubPartIdx, uiPartIdx, uiDepth)
                        pcCU.getCUMvField(uiRefListIdx).setAllMvd(cTmpMv, ePartSize, uiSubPartIdx, uiDepth, uiPartIdx)
                        pcCU.getCUMvField(uiRefListIdx).setAllMvField(
                            cMvFieldNeighbours[2*uiMergeIndex+uiRefListIdx], ePartSize, uiSubPartIdx, uiDepth, uiPartIdx)
            else:
                self.decodeInterDirPU(pcCU, uiSubPartIdx, uiDepth, uiPartIdx)
                for uiRefListIdx in xrange(2):
                    if pcCU.getSlice().getNumRefIdx(uiRefListIdx) > 0:
                        self.decodeRefFrmIdxPU(pcCU, uiSubPartIdx, uiDepth, uiPartIdx, uiRefListIdx)
                        self.decodeMvdPU(pcCU, uiSubPartIdx, uiDepth, uiPartIdx, uiRefListIdx)
                        self.decodeMVPIdxPU(pcSubCU, uiSubPartIdx-uiAbsPartIdx, uiDepth, uiPartIdx, uiRefListIdx)
            if pcCU.getInterDir(uiSubPartIdx) == 3 and pcSubCU.isBipredRestriction(uiPartIdx):
                pcCU.getCUMvField(REF_PIC_LIST_1).setAllMv(TComMv(0, 0), ePartSize, uiSubPartIdx, uiDepth, uiPartIdx)
                pcCU.getCUMvField(REF_PIC_LIST_1).setAllRefIdx(-1, ePartSize, uiSubPartIdx, uiDepth, uiPartIdx)
                pcCU.setInterDirSubParts(1, uiSubPartIdx, uiPartIdx, uiDepth)
            uiSubPartIdx += uiPUOffset

    def decodeInterDirPU(self, pcCU, uiAbsPartIdx, uiDepth, uiPartIdx):
        uiInterDir = 0

        if pcCU.getSlice().isInterP():
            uiInterDir = 1
        else:
            uiInterDir = self.m_pcEntropyDecoderIf.parseInterDir(pcCU, uiInterDir, uiAbsPartIdx, uiDepth)

        pcCU.setInterDirSubParts(uiInterDir, uiAbsPartIdx, uiPartIdx, uiDepth)

    def decodeRefFrmIdxPU(self, pcCU, uiAbsPartIdx, uiDepth, uiPartIdx, eRefList):
        iRefFrmIdx = 0
        iParseRefFrmIdx = pcCU.getInterDir(uiAbsPartIdx) & (1 << eRefList)

        if pcCU.getSlice().getNumRefIdx(eRefList) > 1 and iParseRefFrmIdx:
            iRefFrmIdx = self.m_pcEntropyDecoderIf.parseRefFrmIdx(pcCU, iRefFrmIdx, uiAbsPartIdx, uiDepth, eRefList)
        elif not iParseRefFrmIdx:
            iRefFrmIdx = NOT_VALID
        else:
            iRefFrmIdx = 0

        ePartSize = pcCU.getPartitionSize(uiAbsPartIdx)
        pcCU.getCUMvField(eRefList).setAllRefIdx(iRefFrmIdx, ePartSize, uiAbsPartIdx, uiDepth, uiPartIdx)

    def decodeMvdPU(self, pcCU, uiAbsPartIdx, uiDepth, uiPartIdx, eRefList):
        if pcCU.getInterDir(uiAbsPartIdx) & (1 << eRefList):
            self.m_pcEntropyDecoderIf.parseMvd(pcCU, uiAbsPartIdx, uiPartIdx, uiDepth, eRefList)

    def decodeMVPIdxPU(self, pcSubCU, uiPartAddr, uiDepth, uiPartIdx, eRefList):
        iMVPIdx = -1

        cZeroMv = TComMv(0, 0)
        cMv = cZeroMv
        iRefIdx = -1

        pcSubCUMvField = pcSubCU.getCUMvField(eRefList)
        pAMVPInfo = pcSubCUMvField.getAMVPInfo()

        iRefIdx = pcSubCUMvField.getRefIdx(uiPartAddr)
        cMv = cZeroMv

        if (pcSubCU.getInterDir(uiPartAddr) & (1 << eRefList)) and pcSubCU.getAMVPMode(uiPartAddr) == AM_EXPL:
            iMVPIdx = self.m_pcEntropyDecoderIf.parseMVPIdx(iMVPIdx)
        pcSubCU.fillMvpCand(uiPartIdx, uiPartAddr, eRefList, iRefIdx, pAMVPInfo)
        pcSubCU.setMVPNumSubParts(pAMVPInfo.iN, eRefList, uiPartAddr, uiPartIdx, uiDepth)
        pcSubCU.setMVPIdxSubParts(iMVPIdx, eRefList, uiPartAddr, uiPartIdx, uiDepth)
        if iRefIdx >= 0:
            cMv = self.m_pcPrediction.getMvPredAMVP(pcSubCU, uiPartIdx, uiPartAddr, eRefList, iRefIdx)
            cMv = cMv + pcSubCUMvField.getMvd(uiPartAddr)

        ePartSize = pcSubCU.getPartitionSize(uiPartAddr)
        pcSubCU.getCUMvField(eRefList).setAllMv(cMv, ePartSize, uiPartAddr, 0, uiPartIdx)

    def setEntropyDecoder(self, p):
        self.m_pcEntropyDecoderIf = p
    def setBitstream(self, p):
        self.m_pcEntropyDecoderIf.setBitstream(p)
    def resetEntropy(self, p):
        self.m_pcEntropyDecoderIf.resetEntropy(p)
    def decodeVPS(self, pcVPS):
        self.m_pcEntropyDecoderIf.parseVPS(pcVPS)
    def decodeSPS(self, pcSPS):
        self.m_pcEntropyDecoderIf.parseSPS(pcSPS)
    def decodePPS(self, pcPPS, parameterSet):
        self.m_pcEntropyDecoderIf.parsePPS(pcPPS)
    def decodeSEI(self, seis):
        self.m_pcEntropyDecoderIf.parseSEI(seis)
    def decodeSliceHeader(self, rpcSlice, parameterSetManager):
        self.m_pcEntropyDecoderIf.parseSliceHeader(rpcSlice, parameterSetManager)
    def decodeTerminatingBit(self, ruiIsLast):
        ruiIsLast = self.m_pcEntropyDecoderIf.parseTerminatingBit(ruiIsLast)
        return ruiIsLast
    def getEntropyDecoder(self):
        return self.m_pcEntropyDecoderIf

    def updateContextTables(self, eSliceType, iQp):
        self.m_pcEntropyDecoderIf.updateContextTables(eSliceType, iQp)
    def decodeFlush(self):
        self.m_pcEntropyDecoderIf.decodeFlush()

    def decodeSplitFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parseSplitFlag(pcCU, uiAbsPartIdx, uiDepth)
    def decodeSkipFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parseSkipFlag(pcCU, uiAbsPartIdx, uiDepth)
    def decodeCUTransquantBypassFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parseCUTransquantBypassFlag(pcCU, uiAbsPartIdx, uiDepth)
    def decodeMergeFlag(self, pcCU, uiAbsPartIdx, uiDepth, uiPUIdx):
        self.m_pcEntropyDecoderIf.parseMergeFlag(pcCU, uiAbsPartIdx, uiDepth, uiPUIdx)
    def decodeMergeIndex(self, pcCU, uiPartIdx, uiAbsPartIdx,
                         eCUMode, puhInterDirNeighbours, pcMvFieldNeighbours, uiDepth):
        uiMergeIndex = 0
        uiMergeIndex = self.m_pcEntropyDecoderIf.parseMergeIndex(pcCU, uiMergeIndex, uiAbsPartIdx, uiDepth)
        pcCU.setMergeIndexSubParts(uiMergeIndex, uiAbsPartIdx, uiPartIdx, uiDepth)
    def decodePredMode(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parsePredMode(pcCU, uiAbsPartIdx, uiDepth)
    def decodePartSize(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parsePartSize(pcCU, uiAbsPartIdx, uiDepth)
    def decodeIPCMInfo(self, pcCU, uiAbsPartIdx, uiDepth):
        if not pcCU.getSlice().getSPS().getUsePCM() or \
           pcCU.getWidth(uiAbsPartIdx) > (1 << pcCU.getSlice().getSPS().getPCMLog2MaxSize()) or \
           pcCU.getWidth(uiAbsPartIdx) < (1 << pcCU.getSlice().getSPS().getPCMLog2MinSize()):
            return
        self.m_pcEntropyDecoderIf.parseIPCMInfo(pcCU, uiAbsPartIdx, uiDepth)
    def decodePredInfo(self, pcCU, uiAbsPartIdx, uiDepth, pcSubCU):
        if pcCU.isIntra(uiAbsPartIdx):
            self.decodeIntraDirModeLuma(pcCU, uiAbsPartIdx, uiDepth)
            self.decodeIntraDirModeChroma(pcCU, uiAbsPartIdx, uiDepth)
        else:
            self.decodePUWise(pcCU, uiAbsPartIdx, uiDepth, pcSubCU)
    def decodeIntraDirModeLuma(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parseIntraDirLumaAng(pcCU, uiAbsPartIdx, uiDepth)
    def decodeIntraDirModeChroma(self, pcCU, uiAbsPartIdx, uiDepth):
        self.m_pcEntropyDecoderIf.parseIntraDirChroma(pcCU, uiAbsPartIdx, uiDepth)
    def decodeQP(self, pcCU, uiAbsPartIdx):
        if pcCU.getSlice().getPPS().getUseDQP():
            self.m_pcEntropyDecoderIf.parseDeltaQP(pcCU, uiAbsPartIdx, pcCU.getDepth(uiAbsPartIdx))

    def decodeCoeff(self, pcCU, uiAbsPartIdx, uiDepth, uiWidth, uiHeight, bCodeDQP):
        uiMinCoeffSize = pcCU.getPic().getMinCUWidth() * pcCU.getPic().getMinCUHeight()
        uiLumaOffset = uiMinCoeffSize * uiAbsPartIdx
        uiChromaOffset = uiLumaOffset >> 2

        if not pcCU.isIntra(uiAbsPartIdx):
            uiQtRootCbf = 1
            if not (pcCU.getPartitionSize(uiAbsPartIdx) == SIZE_2Nx2N and pcCU.getMergeFlag(uiAbsPartIdx)):
                uiQtRootCbf = self.m_pcEntropyDecoderIf.parseQtRootCbf(pcCU, uiAbsPartIdx, uiDepth, uiQtRootCbf)
            if not uiQtRootCbf:
                pcCU.setCbfSubParts(0, 0, 0, uiAbsPartIdx, uiDepth)
                pcCU.setTrIdxSubParts(0, uiAbsPartIdx, uiDepth)
                return bCodeDQP
        bCodeDQP = self._xDecodeTransform(pcCU, uiLumaOffset, uiChromaOffset,
                                          uiAbsPartIdx, uiAbsPartIdx, uiDepth, uiWidth, uiHeight,
                                          0, 0, bCodeDQP)
        return bCodeDQP

    def _xDecodeTransform(self, pcCU, offsetLuma, offsetChroma,
                          uiAbsPartIdx, absTUPartIdx, uiDepth, uiWidth, uiHeight,
                          uiTrIdx, uiInnerQuadIdx, bCodeDQP):
        uiSubdiv = 0
        uiLog2TrafoSize = g_aucConvertToBit[pcCU.getSlice().getSPS().getMaxCUWidth()] + 2 - uiDepth

        if uiTrIdx == 0:
            self.m_bakAbsPartIdxCU = uiAbsPartIdx
        if uiLog2TrafoSize == 2:
            partNum = pcCU.getPic().getNumPartInCU() >> ((uiDepth-1) << 1)
            if uiAbsPartIdx % partNum == 0:
                self.m_uiBakAbsPartIdx = uiAbsPartIdx
                self.m_uiBakChromaOffset = offsetChroma
        if pcCU.getPredictionMode(uiAbsPartIdx) == MODE_INTRA and \
           pcCU.getPartitionSize(uiAbsPartIdx) == SIZE_NxN and \
           uiDepth == pcCU.getDepth(uiAbsPartIdx):
            uiSubdiv = 1
        elif pcCU.getSlice().getSPS().getQuadtreeTUMaxDepthInter() == 1 and \
             pcCU.getPredictionMode(uiAbsPartIdx) == MODE_INTER and \
             pcCU.getPartitionSize(uiAbsPartIdx) != SIZE_2Nx2N and \
             uiDepth == pcCU.getDepth(uiAbsPartIdx):
            uiSubdiv = uiLog2TrafoSize > pcCU.getQuadtreeTULog2MinSizeInCU(uiAbsPartIdx)
        elif uiLog2TrafoSize > pcCU.getSlice().getSPS().getQuadtreeTULog2MaxSize():
            uiSubdiv = 1
        elif uiLog2TrafoSize == pcCU.getSlice().getSPS().getQuadtreeTULog2MinSize():
            uiSubdiv = 0
        elif uiLog2TrafoSize == pcCU.getQuadtreeTULog2MinSizeInCU(uiAbsPartIdx):
            uiSubdiv = 0
        else:
            assert(uiLog2TrafoSize > pcCU.getQuadtreeTULog2MinSizeInCU(uiAbsPartIdx))
            uiSubdiv = self.m_pcEntropyDecoderIf.parseTransformSubdivFlag(uiSubdiv, 5-uiLog2TrafoSize)

        uiTrDepth = uiDepth - pcCU.getDepth(uiAbsPartIdx)
        bFirstCbfOfCU = uiTrDepth == 0
        if bFirstCbfOfCU:
            pcCU.setCbfSubParts(0, TEXT_CHROMA_U, uiAbsPartIdx, uiDepth)
            pcCU.setCbfSubParts(0, TEXT_CHROMA_V, uiAbsPartIdx, uiDepth)
        if bFirstCbfOfCU or uiLog2TrafoSize > 2:
            if bFirstCbfOfCU or pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_U, uiTrDepth-1):
                self.m_pcEntropyDecoderIf.parseQtCbf(pcCU, uiAbsPartIdx, TEXT_CHROMA_U, uiTrDepth, uiDepth)
            if bFirstCbfOfCU or pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_V, uiTrDepth-1):
                self.m_pcEntropyDecoderIf.parseQtCbf(pcCU, uiAbsPartIdx, TEXT_CHROMA_V, uiTrDepth, uiDepth)
        else:
            pcCU.setCbfSubParts(pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_U, uiTrDepth-1) << uiTrDepth, TEXT_CHROMA_U, uiAbsPartIdx, uiDepth)
            pcCU.setCbfSubParts(pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_V, uiTrDepth-1) << uiTrDepth, TEXT_CHROMA_V, uiAbsPartIdx, uiDepth)

        if uiSubdiv:
            uiWidth >>= 1
            uiHeight >>= 1
            size = uiWidth * uiHeight
            uiTrIdx += 1
            uiDepth += 1
            uiQPartNum = pcCU.getPic().getNumPartInCU() >> (uiDepth << 1)
            uiStartAbsPartIdx = uiAbsPartIdx
            uiLumaTrMode = 0
            uiChromaTrMode = 0
            uiLumaTrMode, uiChromaTrMode = \
                pcCU.convertTransIdx(uiStartAbsPartIdx, uiTrDepth+1, uiLumaTrMode, uiChromaTrMode)
            uiYCbf = 0
            uiUCbf = 0
            uiVCbf = 0

            for i in xrange(4):
                nsAddr = uiAbsPartIdx
                bCodeDQP = self._xDecodeTransform(pcCU, offsetLuma, offsetChroma, uiAbsPartIdx, nsAddr,
                    uiDepth, uiWidth, uiHeight, uiTrIdx, i, bCodeDQP)
                uiYCbf |= pcCU.getCbf(uiAbsPartIdx, TEXT_LUMA, uiLumaTrMode)
                uiUCbf |= pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_U, uiChromaTrMode)
                uiVCbf |= pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_V, uiChromaTrMode)
                uiAbsPartIdx += uiQPartNum
                offsetLuma += size
                offsetChroma += (size >> 2)

            uiLumaTrMode, uiChromaTrMode = \
                pcCU.convertTransIdx(uiStartAbsPartIdx, uiTrDepth, uiLumaTrMode, uiChromaTrMode)
            for ui in xrange(4 * uiQPartNum):
                cbfY = pointer(pcCU.getCbf(TEXT_LUMA), type='uchar *')
                cbfU = pointer(pcCU.getCbf(TEXT_CHROMA_U), type='uchar *')
                cbfV = pointer(pcCU.getCbf(TEXT_CHROMA_V), type='uchar *')
                cbfY[uiStartAbsPartIdx + ui] |= uiYCbf << uiLumaTrMode
                cbfU[uiStartAbsPartIdx + ui] |= uiUCbf << uiChromaTrMode
                cbfV[uiStartAbsPartIdx + ui] |= uiVCbf << uiChromaTrMode
        else:
            assert(uiDepth >= pcCU.getDepth(uiAbsPartIdx))
            pcCU.setTrIdxSubParts(uiTrDepth, uiAbsPartIdx, uiDepth)

            if trace.use_trace:
                trace.DTRACE_CABAC_VL(trace.g_nSymbolCounter)
                trace.g_nSymbolCounter += 1
                trace.DTRACE_CABAC_T("\tTrIdx: abspart=")
                trace.DTRACE_CABAC_V(uiAbsPartIdx)
                trace.DTRACE_CABAC_T("\tdepth=")
                trace.DTRACE_CABAC_V(uiDepth)
                trace.DTRACE_CABAC_T("\ttrdepth=")
                trace.DTRACE_CABAC_V(uiTrDepth)
                trace.DTRACE_CABAC_T("\n")

            uiLumaTrMode = 0
            uiChromaTrMode = 0
            uiLumaTrMode, uiChromaTrMode = \
                pcCU.convertTransIdx(uiAbsPartIdx, uiTrDepth, uiLumaTrMode, uiChromaTrMode)
            pcCU.setCbfSubParts(0, TEXT_LUMA, uiAbsPartIdx, uiDepth)
            if pcCU.getPredictionMode(uiAbsPartIdx) != MODE_INTRA and \
               uiDepth == pcCU.getDepth(uiAbsPartIdx) and \
               not pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_U, 0) and \
               not pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_V, 0):
                pcCU.setCbfSubParts(1 << uiLumaTrMode, TEXT_LUMA, uiAbsPartIdx, uiDepth)
            else:
                self.m_pcEntropyDecoderIf.parseQtCbf(pcCU, uiAbsPartIdx, TEXT_LUMA, uiLumaTrMode, uiDepth)

            # transform_unit begin
            cbfY = pcCU.getCbf(uiAbsPartIdx, TEXT_LUMA, uiTrIdx)
            cbfU = pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_U, uiTrIdx)
            cbfV = pcCU.getCbf(uiAbsPartIdx, TEXT_CHROMA_V, uiTrIdx)
            if uiLog2TrafoSize == 2:
                partNum = pcCU.getPic().getNumPartInCU() >> ((uiDepth-1) << 1)
                if (uiAbsPartIdx % partNum) == (partNum - 1):
                    cbfU = pcCU.getCbf(self.m_uiBakAbsPartIdx, TEXT_CHROMA_U, uiTrIdx)
                    cbfV = pcCU.getCbf(self.m_uiBakAbsPartIdx, TEXT_CHROMA_V, uiTrIdx)
            if cbfY or cbfU or cbfV:
                # dQP: only for LCU
                if pcCU.getSlice().getPPS().getUseDQP():
                    if bCodeDQP:
                        self.decodeQP(pcCU, self.m_bakAbsPartIdxCU)
                        bCodeDQP = False
            if cbfY:
                trWidth = uiWidth
                trHeight = uiHeight
                self.m_pcEntropyDecoderIf.parseCoeffNxN(pcCU,
                    pointer(pcCU.getCoeffY(), base=offsetLuma, type='int *').cast(),
                    uiAbsPartIdx, trWidth, trHeight, uiDepth, TEXT_LUMA)
            if uiLog2TrafoSize > 2:
                trWidth = uiWidth >> 1
                trHeight = uiHeight >> 1
                if cbfU:
                    self.m_pcEntropyDecoderIf.parseCoeffNxN(pcCU,
                        pointer(pcCU.getCoeffCb(), base=offsetChroma, type='int *').cast(),
                        uiAbsPartIdx, trWidth, trHeight, uiDepth, TEXT_CHROMA_U)
                if cbfV:
                    self.m_pcEntropyDecoderIf.parseCoeffNxN(pcCU,
                        pointer(pcCU.getCoeffCr(), base=offsetChroma, type='int *').cast(),
                        uiAbsPartIdx, trWidth, trHeight, uiDepth, TEXT_CHROMA_V)
            else:
                partNum = pcCU.getPic().getNumPartInCU() >> ((uiDepth-1) << 1)
                if (uiAbsPartIdx % partNum) == (partNum - 1):
                    trWidth = uiWidth
                    trHeight = uiHeight
                    if cbfU:
                        self.m_pcEntropyDecoderIf.parseCoeffNxN(pcCU,
                            pointer(pcCU.getCoeffCb(), base=self.m_uiBakChromaOffset, type='int *').cast(),
                            self.m_uiBakAbsPartIdx, trWidth, trHeight, uiDepth, TEXT_CHROMA_U)
                    if cbfV:
                        self.m_pcEntropyDecoderIf.parseCoeffNxN(pcCU,
                            pointer(pcCU.getCoeffCr(), base=self.m_uiBakChromaOffset, type='int *').cast(),
                            self.m_uiBakAbsPartIdx, trWidth, trHeight, uiDepth, TEXT_CHROMA_V)
            # transform_unit end

        return bCodeDQP
