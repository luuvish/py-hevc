# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecCu.py
    HM 9.2 Python Implementation
"""

import sys

from ... import pointer
from ... import Trace

from ... import TComDataCU, ArrayTComDataCU
from ... import ArrayTComMvField, ArrayUChar
from ... import TComMv, ArrayTComYuv

from ... import cvar
from ... import initZscanToRaster
from ... import initRasterToZscan
from ... import initRasterToPelXY

use_trace = False

from ..TLibCommon.TypeDef import (
    DM_CHROMA_IDX, REG_DCT,
    SIZE_2Nx2N, MODE_INTER, MODE_INTRA,
    TEXT_LUMA, TEXT_CHROMA, TEXT_CHROMA_U, TEXT_CHROMA_V,
    REF_PIC_LIST_0, REF_PIC_LIST_1
)

from ..TLibCommon.CommonDef import (ClipY, ClipC, MRG_MAX_NUM_CANDS)

from ..TLibCommon.TComRom import (
    g_auiZscanToRaster, g_auiRasterToPelX, g_auiRasterToPelY,
    g_aucConvertToBit, g_eTTable
)


class TDecCu(object):

    def __init__(self):
        self.m_uiMaxDepth       = False
        self.m_ppcYuvResi       = None
        self.m_ppcYuvReco       = None
        self.m_ppcCU            = None

        self.m_pcTrQuant        = None
        self.m_pcPrediction     = None
        self.m_pcEntropyDecoder = None

        self.m_bDecoderDQP      = False

    def init(self, pcEntropyDecoder, pcTrQuant, pcPrediction):
        self.m_pcEntropyDecoder = pcEntropyDecoder
        self.m_pcTrQuant = pcTrQuant
        self.m_pcPrediction = pcPrediction

    def create(self, uiMaxDepth, uiMaxWidth, uiMaxHeight):
        self.m_uiMaxDepth = uiMaxDepth + 1

        self.m_ppcYuvResi = ArrayTComYuv(self.m_uiMaxDepth-1)
        self.m_ppcYuvReco = ArrayTComYuv(self.m_uiMaxDepth-1)
        self.m_ppcCU = ArrayTComDataCU(self.m_uiMaxDepth-1)

        uiNumPartitions = 0
        for ui in xrange(self.m_uiMaxDepth-1):
            uiNumPartitions = 1 << ((self.m_uiMaxDepth - ui - 1) << 1)
            uiWidth = uiMaxWidth >> ui
            uiHeight = uiMaxHeight >> ui

            self.m_ppcYuvResi[ui].create(uiWidth, uiHeight)
            self.m_ppcYuvReco[ui].create(uiWidth, uiHeight)
            self.m_ppcCU[ui].create(uiNumPartitions, uiWidth, uiHeight, True,
                                    uiMaxWidth >> (self.m_uiMaxDepth-1))

        self.m_bDecoderDQP = False

        # initialize partition order.
        piTmp = g_auiZscanToRaster
        initZscanToRaster(self.m_uiMaxDepth, 1, 0, piTmp)
        initRasterToZscan(uiMaxWidth, uiMaxHeight, self.m_uiMaxDepth)

        # initialize conversion matrix from partition index to pel
        initRasterToPelXY(uiMaxWidth, uiMaxHeight, self.m_uiMaxDepth)

    def destroy(self):
        for ui in xrange(self.m_uiMaxDepth-1):
            self.m_ppcYuvResi[ui].destroy()
            #del self.m_ppcYuvResi[ui]
            #self.m_ppcYuvResi[ui] = None
            self.m_ppcYuvReco[ui].destroy()
            #del self.m_ppcYuvReco[ui]
            #self.m_ppcYuvReco[ui] = None
            self.m_ppcCU[ui].destroy()
            #del self.m_ppcCU[ui]
            #self.m_ppcCU[ui] = None

        del self.m_ppcYuvResi
        self.m_ppcYuvResi = None
        del self.m_ppcYuvReco
        self.m_ppcYuvReco = None
        del self.m_ppcCU
        self.m_ppcCU = None

    def decodeCU(self, pcCU, ruiIsLast):
        if pcCU.getSlice().getPPS().getUseDQP():
            self.setdQPFlag(True)

        # start from the top level CU
        ruiIsLast = self.xDecodeCU(pcCU, 0, 0, ruiIsLast)
        return ruiIsLast

    #@Trace.trace(enable=use_trace, init=Trace.initCU, after=lambda self, pcCU: Trace.dumpCU(pcCU))
    def decompressCU(self, pcCU):
        self.xDecompressCU(pcCU, 0, 0)

    def xDecodeCU(self, pcCU, uiAbsPartIdx, uiDepth, ruiIsLast):
        pcPic = pcCU.getPic()
        uiCurNumParts = pcPic.getNumPartInCU() >> (uiDepth<<1)
        uiQNumParts = uiCurNumParts >> 2

        bBoundary = False
        uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]]
        uiRPelX = uiLPelX + (cvar.g_uiMaxCUWidth>>uiDepth) - 1
        uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]]
        uiBPelY = uiTPelY + (cvar.g_uiMaxCUHeight>>uiDepth) - 1

        pcSlice = pcCU.getPic().getSlice(pcCU.getPic().getCurrSliceIdx())
        bStartInCU = (pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts) > pcSlice.getSliceSegmentCurStartCUAddr() and \
                     (pcCU.getSCUAddr() + uiAbsPartIdx) < pcSlice.getSliceSegmentCurStartCUAddr()
        if not bStartInCU and \
           uiRPelX < pcSlice.getSPS().getPicWidthInLumaSamples() and \
           uiBPelY < pcSlice.getSPS().getPicHeightInLumaSamples():
            self.m_pcEntropyDecoder.decodeSplitFlag(pcCU, uiAbsPartIdx, uiDepth)
        else:
            bBoundary = True

        if ((uiDepth < pcCU.getDepth(uiAbsPartIdx)) and \
            (uiDepth < cvar.g_uiMaxCUDepth - cvar.g_uiAddCUDepth)) or \
           bBoundary:
            uiIdx = uiAbsPartIdx
            if (cvar.g_uiMaxCUWidth >> uiDepth) == pcCU.getSlice().getPPS().getMinCuDQPSize() and \
               pcCU.getSlice().getPPS().getUseDQP():
                self.setdQPFlag(True)
                pcCU.setQPSubParts(pcCU.getRefQP(uiAbsPartIdx), uiAbsPartIdx, uiDepth) # set QP to default QP

            for uiPartUnitIdx in xrange(4):
                uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiIdx]]
                uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiIdx]]

                bSubInSlice = pcCU.getSCUAddr() + uiIdx + uiQNumParts > pcSlice.getSliceSegmentCurStartCUAddr()
                if bSubInSlice:
                    if not ruiIsLast and \
                       uiLPelX < pcCU.getSlice().getSPS().getPicWidthInLumaSamples() and \
                       uiTPelY < pcCU.getSlice().getSPS().getPicHeightInLumaSamples():
                        ruiIsLast = self.xDecodeCU(pcCU, uiIdx, uiDepth+1, ruiIsLast)
                    else:
                        pcCU.setOutsideCUPart(uiIdx, uiDepth+1)

                uiIdx += uiQNumParts
            if (cvar.g_uiMaxCUWidth >> uiDepth) == pcCU.getSlice().getPPS().getMinCuDQPSize() and \
               pcCU.getSlice().getPPS().getUseDQP():
                if self.getdQPFlag():
                    uiQPSrcPartIdx = 0;
                    if pcPic.getCU(pcCU.getAddr()).getSliceSegmentStartCU(uiAbsPartIdx) != \
                       pcSlice.getSliceSegmentCurStartCUAddr():
                        uiQPSrcPartIdx = pcSlice.getSliceSegmentCurStartCUAddr() % pcPic.getNumPartInCU()
                    else:
                        uiQPSrcPartIdx = uiAbsPartIdx
                    pcCU.setQPSubParts(pcCU.getRefQP(uiQPSrcPartIdx), uiAbsPartIdx, uiDepth) # set QP to default QP
            return ruiIsLast

        if (cvar.g_uiMaxCUWidth >> uiDepth) >= pcCU.getSlice().getPPS().getMinCuDQPSize() and \
           pcCU.getSlice().getPPS().getUseDQP():
            self.setdQPFlag(True)
            pcCU.setQPSubParts(pcCU.getRefQP(uiAbsPartIdx), uiAbsPartIdx, uiDepth) # set QP to default QP

        if pcCU.getSlice().getPPS().getTransquantBypassEnableFlag():
            self.m_pcEntropyDecoder.decodeCUTransquantBypassFlag(pcCU, uiAbsPartIdx, uiDepth)

        # decode CU mode and the partition size
        if not pcCU.getSlice().isIntra():
            self.m_pcEntropyDecoder.decodeSkipFlag(pcCU, uiAbsPartIdx, uiDepth)

        if pcCU.isSkipped(uiAbsPartIdx):
            self.m_ppcCU[uiDepth].copyInterPredInfoFrom(pcCU, uiAbsPartIdx, REF_PIC_LIST_0)
            self.m_ppcCU[uiDepth].copyInterPredInfoFrom(pcCU, uiAbsPartIdx, REF_PIC_LIST_1)
            cMvFieldNeighbours = ArrayTComMvField(MRG_MAX_NUM_CANDS<<1) # double length for mv of both lists
            uhInterDirNeighbours = ArrayUChar(MRG_MAX_NUM_CANDS)
            numValidMergeCand = 0
            for ui in xrange(self.m_ppcCU[uiDepth].getSlice().getMaxNumMergeCand()):
                uhInterDirNeighbours[ui] = 0
            self.m_pcEntropyDecoder.decodeMergeIndex(pcCU, 0, uiAbsPartIdx, uiDepth)
            uiMergeIndex = pcCU.getMergeIndex(uiAbsPartIdx)
            numValidMergeCand = self.m_ppcCU[uiDepth].getInterMergeCandidates(
                0, 0, cMvFieldNeighbours.cast(), uhInterDirNeighbours.cast(), numValidMergeCand, uiMergeIndex)
            pcCU.setInterDirSubParts(uhInterDirNeighbours[uiMergeIndex], uiAbsPartIdx, 0, uiDepth)

            cTmpMv = TComMv(0, 0)
            for uiRefListIdx in xrange(2):
                if pcCU.getSlice().getNumRefIdx(uiRefListIdx) > 0:
                    pcCU.setMVPIdxSubParts(0, uiRefListIdx, uiAbsPartIdx, 0, uiDepth)
                    pcCU.setMVPNumSubParts(0, uiRefListIdx, uiAbsPartIdx, 0, uiDepth)
                    pcCU.getCUMvField(uiRefListIdx).setAllMvd(cTmpMv, SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
                    pcCU.getCUMvField(uiRefListIdx).setAllMvField(cMvFieldNeighbours[2*uiMergeIndex+uiRefListIdx], SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
            ruiIsLast = self.xFinishDecodeCU(pcCU, uiAbsPartIdx, uiDepth, ruiIsLast)
            return ruiIsLast

        self.m_pcEntropyDecoder.decodePredMode(pcCU, uiAbsPartIdx, uiDepth)
        self.m_pcEntropyDecoder.decodePartSize(pcCU, uiAbsPartIdx, uiDepth)

        if pcCU.isIntra(uiAbsPartIdx) and pcCU.getPartitionSize(uiAbsPartIdx) == SIZE_2Nx2N:
            self.m_pcEntropyDecoder.decodeIPCMInfo(pcCU, uiAbsPartIdx, uiDepth)

            if pcCU.getIPCMFlag(uiAbsPartIdx):
                ruiIsLast = self.xFinishDecodeCU(pcCU, uiAbsPartIdx, uiDepth, ruiIsLast)
                return ruiIsLast

        uiCurrWidth = pcCU.getWidth(uiAbsPartIdx)
        uiCurrHeight = pcCU.getHeight(uiAbsPartIdx)

        # prediction mode ( Intra : direction mode, Inter : Mv, reference idx )
        self.m_pcEntropyDecoder.decodePredInfo(pcCU, uiAbsPartIdx, uiDepth, self.m_ppcCU[uiDepth])

        # Coefficient decoding
        bCodeDQP = self.getdQPFlag()
        self.m_pcEntropyDecoder.decodeCoeff(pcCU, uiAbsPartIdx, uiDepth, uiCurrWidth, uiCurrHeight, bCodeDQP)
        self.setdQPFlag(bCodeDQP)
        ruiIsLast = self.xFinishDecodeCU(pcCU, uiAbsPartIdx, uiDepth, ruiIsLast)
        return ruiIsLast

    def xFinishDecodeCU(self, pcCU, uiAbsPartIdx, uiDepth, ruiIsLast):
        if pcCU.getSlice().getPPS().getUseDQP():
            pcCU.setQPSubParts(
                pcCU.getRefQP(uiAbsPartIdx) if self.getdQPFlag() else pcCU.getCodedQP(),
                uiAbsPartIdx, uiDepth) # set QP

        ruiIsLast = self.xDecodeSliceEnd(pcCU, uiAbsPartIdx, uiDepth)
        return ruiIsLast

    def xDecodeSliceEnd(self, pcCU, uiAbsPartIdx, uiDepth):
        uiIsLast = 0
        pcPic = pcCU.getPic()
        pcSlice = pcPic.getSlice(pcPic.getCurrSliceIdx())
        uiCurNumParts = pcPic.getNumPartInCU() >> (uiDepth<<1)
        uiWidth = pcSlice.getSPS().getPicWidthInLumaSamples()
        uiHeight = pcSlice.getSPS().getPicHeightInLumaSamples()
        uiGranularityWidth = cvar.g_uiMaxCUWidth
        uiPosX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]]
        uiPosY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]]

        if ((uiPosX + pcCU.getWidth(uiAbsPartIdx)) % uiGranularityWidth == 0 or
            (uiPosX + pcCU.getWidth(uiAbsPartIdx)) == uiWidth) and \
           ((uiPosY + pcCU.getHeight(uiAbsPartIdx)) % uiGranularityWidth == 0 or
            (uiPosY + pcCU.getHeight(uiAbsPartIdx)) == uiHeight):
            uiIsLast = self.m_pcEntropyDecoder.decodeTerminatingBit(uiIsLast)
        else:
            uiIsLast = 0

        if uiIsLast:
            if pcSlice.isNextSliceSegment() and not pcSlice.isNextSlice():
                pcSlice.setSliceSegmentCurEndCUAddr(pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts)
            else:
                pcSlice.setSliceCurEndCUAddr(pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts)
                pcSlice.setSliceSegmentCurEndCUAddr(pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts)

        return uiIsLast > 0

    def xDecompressCU(self, pcCU, uiAbsPartIdx, uiDepth):
        pcPic = pcCU.getPic()

        bBoundary = False
        uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]]
        uiRPelX = uiLPelX + (cvar.g_uiMaxCUWidth>>uiDepth) - 1
        uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]]
        uiBPelY = uiTPelY + (cvar.g_uiMaxCUHeight>>uiDepth) - 1

        uiCurNumParts = pcPic.getNumPartInCU() >> (uiDepth<<1)
        pcSlice = pcCU.getPic().getSlice(pcCU.getPic().getCurrSliceIdx())
        bStartInCU = (pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts) > pcSlice.getSliceSegmentCurStartCUAddr() and \
                     (pcCU.getSCUAddr() + uiAbsPartIdx) < pcSlice.getSliceSegmentCurStartCUAddr()
        if bStartInCU or \
           uiRPelX >= pcSlice.getSPS().getPicWidthInLumaSamples() or \
           uiBPelY >= pcSlice.getSPS().getPicHeightInLumaSamples():
            bBoundary = True

        if (uiDepth < pcCU.getDepth(uiAbsPartIdx) and
            uiDepth < cvar.g_uiMaxCUDepth - cvar.g_uiAddCUDepth) or \
           bBoundary:
            uiNextDepth = uiDepth + 1
            uiQNumParts = pcCU.getTotalNumPart() >> (uiNextDepth<<1)
            uiIdx = uiAbsPartIdx
            for uiPartIdx in xrange(4):
                uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiIdx]]
                uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiIdx]]

                binSlice = pcCU.getSCUAddr() + uiIdx + uiQNumParts > pcSlice.getSliceSegmentCurStartCUAddr() and \
                           pcCU.getSCUAddr() + uiIdx < pcSlice.getSliceSegmentCurEndCUAddr()
                if binSlice and \
                   uiLPelX < pcSlice.getSPS().getPicWidthInLumaSamples() and \
                   uiTPelY < pcSlice.getSPS().getPicHeightInLumaSamples():
                    self.xDecompressCU(pcCU, uiIdx, uiNextDepth)

                uiIdx += uiQNumParts
            return

        # Residual reconstruction
        self.m_ppcYuvResi[uiDepth].clear()

        self.m_ppcCU[uiDepth].copySubCU(pcCU, uiAbsPartIdx, uiDepth)

        predMode = self.m_ppcCU[uiDepth].getPredictionMode(0)
        if predMode == MODE_INTER:
            self.xReconInter(self.m_ppcCU[uiDepth], uiDepth)
        elif predMode == MODE_INTRA:
            self.xReconIntraQT(self.m_ppcCU[uiDepth], uiDepth)
        else:
            assert(False)
        if self.m_ppcCU[uiDepth].isLosslessCoded(0) and \
           self.m_ppcCU[uiDepth].getIPCMFlag(0) == False:
            self.xFillPCMBuffer(self.m_ppcCU[uiDepth], uiDepth)

        self.xCopyToPic(self.m_ppcCU[uiDepth], pcPic, uiAbsPartIdx, uiDepth)

    def xReconInter(self, pcCU, uiDepth):
        # inter prediction
        self.m_pcPrediction.motionCompensation(pcCU, self.m_ppcYuvReco[uiDepth])

        # inter recon
        self.xDecodeInterTexture(pcCU, 0, uiDepth)

        # clip for only non-zero cbp case
        if pcCU.getCbf(0, TEXT_LUMA) or pcCU.getCbf(0, TEXT_CHROMA_U) or pcCU.getCbf(0, TEXT_CHROMA_V):
            self.m_ppcYuvReco[uiDepth].addClip(
                self.m_ppcYuvReco[uiDepth], self.m_ppcYuvResi[uiDepth],
                0, pcCU.getWidth(0))
        else:
            self.m_ppcYuvReco[uiDepth].copyPartToPartYuv(
                self.m_ppcYuvReco[uiDepth], 0,
                pcCU.getWidth(0), pcCU.getHeight(0))

    def xReconIntraQT(self, pcCU, uiDepth):
        uiInitTrDepth = 0 if pcCU.getPartitionSize(0) == SIZE_2Nx2N else 1
        uiNumPart = pcCU.getNumPartInter()
        uiNumQPart = pcCU.getTotalNumPart() >> 2

        if pcCU.getIPCMFlag(0):
            self.xReconPCM(pcCU, uiDepth)
            return

        for uiPU in xrange(uiNumPart):
            self.xIntraLumaRecQT(pcCU, uiInitTrDepth, uiPU * uiNumQPart,
                self.m_ppcYuvReco[uiDepth], self.m_ppcYuvReco[uiDepth], self.m_ppcYuvResi[uiDepth])

        for uiPU in xrange(uiNumPart):
            self.xIntraChromaRecQT(pcCU, uiInitTrDepth, uiPU * uiNumQPart,
                self.m_ppcYuvReco[uiDepth], self.m_ppcYuvReco[uiDepth], self.m_ppcYuvResi[uiDepth])

    def xIntraRecLumaBlk(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiWidth = pcCU.getWidth(0) >> uiTrDepth
        uiHeight = pcCU.getHeight(0) >> uiTrDepth
        uiStride = pcRecoYuv.getStride()
        piReco = pcRecoYuv.getLumaAddr(uiAbsPartIdx)
        piPred = pcPredYuv.getLumaAddr(uiAbsPartIdx)
        piResi = pcResiYuv.getLumaAddr(uiAbsPartIdx)
        piPred = pointer(piPred, type='short *')
        piResi = pointer(piResi, type='short *')
        piReco = pointer(piReco, type='short *')

        uiNumCoeffInc = (pcCU.getSlice().getSPS().getMaxCUWidth() *
                         pcCU.getSlice().getSPS().getMaxCUHeight()) >> \
                        (pcCU.getSlice().getSPS().getMaxCUDepth() << 1)
        pcCoeff = pointer(pcCU.getCoeffY(), base=(uiNumCoeffInc*uiAbsPartIdx), type='int *')

        uiLumaPredMode = pcCU.getLumaIntraDir(uiAbsPartIdx)

        uiZOrder = pcCU.getZorderIdxInCU() + uiAbsPartIdx
        piRecIPred = pcCU.getPic().getPicYuvRec().getLumaAddr(pcCU.getAddr(), uiZOrder)
        piRecIPred = pointer(piRecIPred, type='short *')
        uiRecIPredStride = pcCU.getPic().getPicYuvRec().getStride()
        useTransformSkip = pcCU.getTransformSkip(uiAbsPartIdx, TEXT_LUMA)

        #===== init availability pattern =====
        bAboveAvail = False
        bLeftAvail = False
        pcCU.getPattern().initPattern(pcCU, uiTrDepth, uiAbsPartIdx)
        bAboveAvail, bLeftAvail = \
            pcCU.getPattern().initAdiPattern(pcCU, uiAbsPartIdx, uiTrDepth,
                                             self.m_pcPrediction.getPredicBuf(),
                                             self.m_pcPrediction.getPredicBufWidth(),
                                             self.m_pcPrediction.getPredicBufHeight(),
                                             bAboveAvail, bLeftAvail)

        #===== get prediction signal =====
        self.m_pcPrediction.predIntraLumaAng(pcCU.getPattern(), uiLumaPredMode,
                                             piPred.cast(), uiStride, uiWidth, uiHeight,
                                             bAboveAvail, bLeftAvail)

        #===== inverse transform =====
        self.m_pcTrQuant.setQPforQuant(pcCU.getQP(0), TEXT_LUMA, pcCU.getSlice().getSPS().getQpBDOffsetY(), 0)

        scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[TEXT_LUMA]
        assert(scalingListType < 6)
        self.m_pcTrQuant.invtransformNxN(
            pcCU.getCUTransquantBypass(uiAbsPartIdx), TEXT_LUMA,
            pcCU.getLumaIntraDir(uiAbsPartIdx), piResi.cast(),
            uiStride, pcCoeff.cast(), uiWidth, uiHeight,
            scalingListType, useTransformSkip)

        #===== reconstruction =====
        for uiY in xrange(uiHeight):
            for uiX in xrange(uiWidth):
                piReco[uiX] = ClipY(piPred[uiX] + piResi[uiX])
                piRecIPred[uiX] = piReco[uiX]
            piPred += uiStride
            piResi += uiStride
            piReco += uiStride
            piRecIPred += uiRecIPredStride

    def xIntraRecChromaBlk(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, uiChromaId):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiLog2TrSize = g_aucConvertToBit[pcCU.getSlice().getSPS().getMaxCUWidth() >> uiFullDepth] + 2

        if uiLog2TrSize == 2:
            assert(uiTrDepth > 0)
            uiTrDepth -= 1
            uiQPDiv = pcCU.getPic().getNumPartInCU() >> ((pcCU.getDepth(0)+uiTrDepth) << 1)
            bFirstQ = (uiAbsPartIdx % uiQPDiv) == 0
            if not bFirstQ:
                return

        eText = TEXT_CHROMA_V if uiChromaId > 0 else TEXT_CHROMA_U
        uiWidth = pcCU.getWidth(0) >> (uiTrDepth+1)
        uiHeight = pcCU.getHeight(0) >> (uiTrDepth+1)
        uiStride = pcRecoYuv.getCStride()
        piReco = pcRecoYuv.getCrAddr(uiAbsPartIdx) if uiChromaId > 0 else pcRecoYuv.getCbAddr(uiAbsPartIdx)
        piPred = pcPredYuv.getCrAddr(uiAbsPartIdx) if uiChromaId > 0 else pcPredYuv.getCbAddr(uiAbsPartIdx)
        piResi = pcResiYuv.getCrAddr(uiAbsPartIdx) if uiChromaId > 0 else pcResiYuv.getCbAddr(uiAbsPartIdx)
        piPred = pointer(piPred, type='short *')
        piResi = pointer(piResi, type='short *')
        piReco = pointer(piReco, type='short *')

        uiNumCoeffInc = ((pcCU.getSlice().getSPS().getMaxCUWidth() *
                          pcCU.getSlice().getSPS().getMaxCUHeight()) >> \
                         (pcCU.getSlice().getSPS().getMaxCUDepth() << 1)) >> 2
        pcCoeff = pointer(pcCU.getCoeffCr() if uiChromaId > 0 else pcCU.getCoeffCb(),
                          base=(uiNumCoeffInc*uiAbsPartIdx), type='int *')

        uiChromaPredMode = pcCU.getChromaIntraDir(0)

        uiZOrder = pcCU.getZorderIdxInCU() + uiAbsPartIdx
        piRecIPred = \
            pcCU.getPic().getPicYuvRec().getCrAddr(pcCU.getAddr(), uiZOrder) if uiChromaId > 0 else \
            pcCU.getPic().getPicYuvRec().getCbAddr(pcCU.getAddr(), uiZOrder)
        piRecIPred = pointer(piRecIPred, type='short *')
        uiRecIPredStride = pcCU.getPic().getPicYuvRec().getCStride()
        useTransformSkipChroma = pcCU.getTransformSkip(uiAbsPartIdx, eText)

        #===== init availability pattern =====
        bAboveAvail = False
        bLeftAvail = False
        pcCU.getPattern().initPattern(pcCU, uiTrDepth, uiAbsPartIdx)
        bAboveAvail, bLeftAvail = \
            pcCU.getPattern().initAdiPatternChroma(pcCU, uiAbsPartIdx, uiTrDepth,
                                                   self.m_pcPrediction.getPredicBuf(),
                                                   self.m_pcPrediction.getPredicBufWidth(),
                                                   self.m_pcPrediction.getPredicBufHeight(),
                                                   bAboveAvail, bLeftAvail)
        pPatChroma = \
            pcCU.getPattern().getAdiCrBuf(uiWidth, uiHeight, self.m_pcPrediction.getPredicBuf()) if uiChromaId > 0 else \
            pcCU.getPattern().getAdiCbBuf(uiWidth, uiHeight, self.m_pcPrediction.getPredicBuf())

        #===== get prediction signal =====
        if uiChromaPredMode == DM_CHROMA_IDX:
            uiChromaPredMode = pcCU.getLumaIntraDir(0)
        self.m_pcPrediction.predIntraChromaAng(pPatChroma, uiChromaPredMode,
                                               piPred.cast(), uiStride, uiWidth, uiHeight,
                                               bAboveAvail, bLeftAvail)

        #===== inverse transform =====
        curChromaQpOffset = 0
        if eText == TEXT_CHROMA_U:
            curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCbQpOffset() + \
                                pcCU.getSlice().getSliceQpDeltaCb()
        else:
            curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCrQpOffset() + \
                                pcCU.getSlice().getSliceQpDeltaCr()
        self.m_pcTrQuant.setQPforQuant(pcCU.getQP(0), eText, pcCU.getSlice().getSPS().getQpBDOffsetC(), curChromaQpOffset)

        scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[eText]
        assert(scalingListType < 6)
        self.m_pcTrQuant.invtransformNxN(
            pcCU.getCUTransquantBypass(uiAbsPartIdx), eText,
            REG_DCT, piResi.cast(),
            uiStride, pcCoeff.cast(), uiWidth, uiHeight,
            scalingListType, useTransformSkipChroma)

        #===== reconstruction =====
        for uiY in xrange(uiHeight):
            for uiX in xrange(uiWidth):
                piReco[uiX] = ClipC(piPred[uiX] + piResi[uiX])
                piRecIPred[uiX] = piReco[uiX]
            piPred += uiStride
            piResi += uiStride
            piReco += uiStride
            piRecIPred += uiRecIPredStride

    def xReconPCM(self, pcCU, uiDepth):
        # Luma
        uiWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uiHeight = cvar.g_uiMaxCUHeight >> uiDepth

        piPcmY = pointer(pcCU.getPCMSampleY(), type='short *')
        piRecoY = pointer(self.m_ppcYuvReco[uiDepth].getLumaAddr(0, uiWidth), type='short *')

        uiStride = self.m_ppcYuvResi[uiDepth].getStride()

        self.xDecodePCMTexture(pcCU, 0, piPcmY, piRecoY, uiStride, uiWidth, uiHeight, TEXT_LUMA)

        # Cb and Cr
        uiCWidth = uiWidth >> 1
        uiCHeight = uiHeight >> 1

        piPcmCb = pointer(pcCU.getPCMSampleCb(), type='short *')
        piPcmCr = pointer(pcCU.getPCMSampleCr(), type='short *')
        pRecoCb = pointer(self.m_ppcYuvReco[uiDepth].getCbAddr(), type='short *')
        pRecoCr = pointer(self.m_ppcYuvReco[uiDepth].getCrAddr(), type='short *')

        uiCStride = self.m_ppcYuvReco[uiDepth].getCStride()

        self.xDecodePCMTexture(pcCU, 0, piPcmCb, pRecoCb, uiCStride, uiCWidth, uiCHeight, TEXT_CHROMA_U)
        self.xDecodePCMTexture(pcCU, 0, piPcmCr, pRecoCr, uiCStride, uiCWidth, uiCHeight, TEXT_CHROMA_V)

    def xDecodeInterTexture(self, pcCU, uiAbsPartIdx, uiDepth):
        uiWidth = pcCU.getWidth(uiAbsPartIdx)
        uiHeight = pcCU.getHeight(uiAbsPartIdx)
        trMode = pcCU.getTransformIdx(uiAbsPartIdx)

        # Y
        piCoeff = pcCU.getCoeffY()
        pResi = self.m_ppcYuvResi[uiDepth].getLumaAddr()

        self.m_pcTrQuant.setQPforQuant(
            pcCU.getQP(uiAbsPartIdx), TEXT_LUMA,
            pcCU.getSlice().getSPS().getQpBDOffsetY(), 0)

        self.m_pcTrQuant.invRecurTransformNxN(
            pcCU, 0, TEXT_LUMA, pResi,
            0, self.m_ppcYuvResi[uiDepth].getStride(),
            uiWidth, uiHeight, trMode, 0, piCoeff)

        # Cb and Cr
        curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCbQpOffset() + pcCU.getSlice().getSliceQpDeltaCb()
        self.m_pcTrQuant.setQPforQuant(
            pcCU.getQP(uiAbsPartIdx), TEXT_CHROMA,
            pcCU.getSlice().getSPS().getQpBDOffsetC(), curChromaQpOffset)

        uiWidth >>= 1
        uiHeight >>= 1
        piCoeff = pcCU.getCoeffCb()
        pResi = self.m_ppcYuvResi[uiDepth].getCbAddr()
        self.m_pcTrQuant.invRecurTransformNxN(
            pcCU, 0, TEXT_CHROMA_U, pResi,
            0, self.m_ppcYuvResi[uiDepth].getCStride(),
            uiWidth, uiHeight, trMode, 0, piCoeff)

        curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCrQpOffset() + pcCU.getSlice().getSliceQpDeltaCr()
        self.m_pcTrQuant.setQPforQuant(
            pcCU.getQP(uiAbsPartIdx), TEXT_CHROMA,
            pcCU.getSlice().getSPS().getQpBDOffsetC(), curChromaQpOffset)

        piCoeff = pcCU.getCoeffCr()
        pResi = self.m_ppcYuvResi[uiDepth].getCrAddr()
        self.m_pcTrQuant.invRecurTransformNxN(
            pcCU, 0, TEXT_CHROMA_V, pResi,
            0, self.m_ppcYuvResi[uiDepth].getCStride(),
            uiWidth, uiHeight, trMode, 0, piCoeff)

    def xDecodePCMTexture(self, pcCU, uiPartIdx, piPCM, piReco, uiStride, uiWidth, uiHeight, ttText):
        piPicReco = None
        uiPicStride = uiPcmLeftShiftBit = 0

        if ttText == TEXT_LUMA:
            uiPicStride = pcCU.getPic().getPicYuvRec().getStride()
            piPicReco = pcCU.getPic().getPicYuvRec().getLumaAddr(pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiPartIdx)
            uiPcmLeftShiftBit = cvar.g_bitDepthY - pcCU.getSlice().getSPS().getPCMBitDepthLuma()
        else:
            uiPicStride = pcCU.getPic().getPicYuvRec().getCStride()

            if ttText == TEXT_CHROMA_U:
                piPicReco = pcCU.getPic().getPicYuvRec().getCbAddr(pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiPartIdx)
            else:
                piPicReco = pcCU.getPic().getPicYuvRec().getCrAddr(pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiPartIdx)
            uiPcmLeftShiftBit = cvar.g_bitDepthC - pcCU.getSlice().getSPS().getPCMBitDepthChroma()

        piPicReco = pointer(piPicReco, type='short *')
        for uiY in xrange(uiHeight):
            for uiX in xrange(uiWidth):
                piReco[uiX] = piPCM[uiX] << uiPcmLeftShiftBit
                piPicReco[uiX] = piReco[uiX]
            piPCM += uiWidth
            piReco += uiStride
            piPicReco += uiPicStride

    def xCopyToPic(self, pcCU, pcPic, uiZorderIdx, uiDepth):
        uiCUAddr = pcCU.getAddr()
        self.m_ppcYuvReco[uiDepth].copyToPicYuv(pcPic.getPicYuvRec(), uiCUAddr, uiZorderIdx)

    def xIntraLumaRecQT(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiTrMode = pcCU.getTransformIdx(uiAbsPartIdx)
        if uiTrMode == uiTrDepth:
            self.xIntraRecLumaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv)
        else:
            uiNumQPart = pcCU.getPic().getNumPartInCU() >> ((uiFullDepth+1) << 1)
            for uiPart in xrange(4):
                self.xIntraLumaRecQT(pcCU, uiTrDepth+1, uiAbsPartIdx+uiPart*uiNumQPart, pcRecoYuv, pcPredYuv, pcResiYuv)

    def xIntraChromaRecQT(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiTrMode = pcCU.getTransformIdx(uiAbsPartIdx)
        if uiTrMode == uiTrDepth:
            self.xIntraRecChromaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, 0)
            self.xIntraRecChromaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, 1)
        else:
            uiNumQPart = pcCU.getPic().getNumPartInCU() >> ((uiFullDepth+1) << 1)
            for uiPart in xrange(4):
                self.xIntraChromaRecQT(pcCU, uiTrDepth+1, uiAbsPartIdx+uiPart*uiNumQPart, pcRecoYuv, pcPredYuv, pcResiYuv)

    def getdQPFlag(self):
        return self.m_bDecoderDQP

    def setdQPFlag(self, b):
        self.m_bDecoderDQP = b

    def xFillPCMBuffer(self, pcCU, uiDepth):
        # Luma
        uiWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uiHeight = cvar.g_uiMaxCUHeight >> uiDepth

        piPcmY = pointer(pcCU.getPCMSampleY(), type='short *')
        piRecoY = pointer(self.m_ppcYuvReco[uiDepth].getLumaAddr(0, uiWidth), type='short *')

        uiStride = self.m_ppcYuvReco[uiDepth].getStride()

        for uiY in xrange(uiHeight):
            for uiX in xrange(uiWidth):
                piPcmY[uiX] = piRecoY[uiX]
            piPcmY += uiWidth
            piRecoY += uiStride

        # Cb and Cr
        uiWidthC = uiWidth >> 1
        uiHeightC = uiHeight >> 1

        piPcmCb = pointer(pcCU.getPCMSampleCb(), type='short *')
        piPcmCr = pointer(pcCU.getPCMSampleCr(), type='short *')
        piRecoCb = pointer(self.m_ppcYuvReco[uiDepth].getCbAddr(), type='short *')
        piRecoCr = pointer(self.m_ppcYuvReco[uiDepth].getCrAddr(), type='short *')

        uiStrideC = self.m_ppcYuvReco[uiDepth].getCStride()

        for uiY in xrange(uiHeightC):
            for uiX in xrange(uiWidthC):
                piPcmCb[uiX] = piRecoCb[uiX]
                piPcmCr[uiX] = piRecoCr[uiX]
            piPcmCb += uiWidthC
            piPcmCr += uiWidthC
            piRecoCb += uiStrideC
            piRecoCr += uiStrideC
