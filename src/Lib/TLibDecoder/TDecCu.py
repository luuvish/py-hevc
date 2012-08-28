# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecCu.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import MODE_INTRA, MODE_INTER
    from swig.hevc import TEXT_LUMA, TEXT_CHROMA, TEXT_CHROMA_U, TEXT_CHROMA_V
    from swig.hevc import MRG_MAX_NUM_CANDS, DM_CHROMA_IDX, REG_DCT
    from swig.hevc import SIZE_2Nx2N
    from swig.hevc import REF_PIC_LIST_0, REF_PIC_LIST_1

    from swig.hevc import TComYuv
    from swig.hevc import TComDataCU
    from swig.hevc import TComMv

    from swig.hevc import initZscanToRaster, initRasterToZscan
    from swig.hevc import initRasterToPelXY, initMotionReferIdx

    from swig.hevc import ArrayChar, ArrayUChar, ArrayUInt, ArrayInt, ArrayPel
    from swig.hevc import ArrayTComYuv, ArrayTComDataCU, ArrayTComMvField
    from swig.hevc import TCoeffAdd


Clip = lambda x: min(cvar.g_uiIBDI_MAX, max(0, x))

g_auiZscanToRaster = ArrayUInt.frompointer(cvar.g_auiZscanToRaster)
g_auiRasterToPelX = ArrayUInt.frompointer(cvar.g_auiRasterToPelX)
g_auiRasterToPelY = ArrayUInt.frompointer(cvar.g_auiRasterToPelY)
g_eTTable = ArrayInt.frompointer(cvar.g_eTTable)


class TDecCu(object):

    def __init__(self):
        self.m_uiMaxDepth = False
        self.m_ppcYuvResi = None
        self.m_ppcYuvReco = None
        self.m_ppcCU = None

        self.m_pcTrQuant = None
        self.m_pcPrediction = None
        self.m_pcEntropyDecoder = None

        self.m_bDecoderDQP = False

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
        for ui in range(self.m_uiMaxDepth-1):
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
        initZscanToRaster(self.m_uiMaxDepth, 1, 0, piTmp.cast())
        initRasterToZscan(uiMaxWidth, uiMaxHeight, self.m_uiMaxDepth)

        # initialize conversion matrix from partition index to pel
        initRasterToPelXY(uiMaxWidth, uiMaxHeight, self.m_uiMaxDepth)
        initMotionReferIdx(uiMaxWidth, uiMaxHeight, self.m_uiMaxDepth)

    def destroy(self):
        for ui in range(self.m_uiMaxDepth-1):
            self.m_ppcYuvResi[ui].destroy()
            self.m_ppcYuvReco[ui].destroy()
            self.m_ppcCU[ui].destroy()

        del self.m_ppcYuvResi
        self.m_ppcYuvResi = None
        del self.m_ppcYuvReco
        self.m_ppcYuvReco = None
        del self.m_ppcCU
        self.m_ppcCU = None

    def decodeCU(self, pcCU, ruiIsLast):
        if pcCU.getSlice().getPPS().getUseDQP():
            self._setdQPFlag(True)

        pcCU.setNumSucIPCM(0)

        # start from the top level CU
        ruiIsLast = self._xDecodeCU(pcCU, 0, 0, ruiIsLast)
        return ruiIsLast

    def decompressCU(self, pcCU):
        self._xDecompressCU(pcCU, pcCU, 0, 0)

    def _xDecodeCU(self, pcCU, uiAbsPartIdx, uiDepth, ruiIsLast):
        pcPic = pcCU.getPic()
        uiCurNumParts = pcPic.getNumPartInCU() >> (uiDepth<<1)
        uiQNumParts = uiCurNumParts >> 2

        bBoundary = False
        uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]]
        uiRPelX = uiLPelX + (cvar.g_uiMaxCUWidth>>uiDepth) - 1
        uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]]
        uiBPelY = uiTPelY + (cvar.g_uiMaxCUHeight>>uiDepth) - 1

        pcSlice = pcCU.getPic().getSlice(pcCU.getPic().getCurrSliceIdx())
        bStartInCU = (pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts) > pcSlice.getDependentSliceCurStartCUAddr() and \
                     (pcCU.getSCUAddr() + uiAbsPartIdx) < pcSlice.getDependentSliceCurStartCUAddr()
        if not bStartInCU and \
           uiRPelX < pcSlice.getSPS().getPicWidthInLumaSamples() and \
           uiBPelY < pcSlice.getSPS().getPicHeightInLumaSamples():
            if pcCU.getNumSucIPCM() == 0:
                self.m_pcEntropyDecoder.decodeSplitFlag(pcCU, uiAbsPartIdx, uiDepth)
            else:
                pcCU.setDepthSubParts(uiDepth, uiAbsPartIdx)
        else:
            bBoundary = True

        if ((uiDepth < pcCU.getDepth(uiAbsPartIdx)) and \
            (uiDepth < cvar.g_uiMaxCUDepth - cvar.g_uiAddCUDepth)) or \
           bBoundary:
            uiIdx = uiAbsPartIdx
            if (cvar.g_uiMaxCUWidth >> uiDepth) == pcCU.getSlice().getPPS().getMinCuDQPSize() and \
               pcCU.getSlice().getPPS().getUseDQP():
                self._setdQPFlag(True)
                pcCU.setQPSubParts(pcCU.getRefQP(uiAbsPartIdx), uiAbsPartIdx, uiDepth) # set QP to default QP

            for uiPartUnitIdx in range(4):
                uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiIdx]]
                uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiIdx]]

                bSubInSlice = pcCU.getSCUAddr() + uiIdx + uiQNumParts > pcSlice.getDependentSliceCurStartCUAddr()
                if bSubInSlice:
                    if uiLPelX < pcCU.getSlice().getSPS().getPicWidthInLumaSamples() and \
                       uiTPelY < pcCU.getSlice().getSPS().getPicHeightInLumaSamples():
                        ruiIsLast = self._xDecodeCU(pcCU, uiIdx, uiDepth+1, ruiIsLast)
                    else:
                        pcCU.setOutsideCUPart(uiIdx, uiDepth+1)
                if ruiIsLast:
                    break

                uiIdx += uiQNumParts
            if (cvar.g_uiMaxCUWidth >> uiDepth) == pcCU.getSlice().getPPS().getMinCuDQPSize() and \
               pcCU.getSlice().getPPS().getUseDQP():
                if self._getdQPFlag():
                    uiQPSrcPartIdx = 0;
                    if pcPic.getCU(pcCU.getAddr()).getDependentSliceStartCU(uiAbsPartIdx) != \
                       pcSlice.getDependentSliceCurStartCUAddr():
                        uiQPSrcPartIdx = pcSlice.getDependentSliceCurStartCUAddr() % pcPic.getNumPartInCU()
                    else:
                        uiQPSrcPartIdx = uiAbsPartIdx
                    pcCU.setQPSubParts(pcCU.getRefQP(uiQPSrcPartIdx), uiAbsPartIdx, uiDepth) # set QP to default QP
            return ruiIsLast

        if (cvar.g_uiMaxCUWidth >> uiDepth) >= pcCU.getSlice().getPPS().getMinCuDQPSize() and \
           pcCU.getSlice().getPPS().getUseDQP():
            self._setdQPFlag(True)
            pcCU.setQPSubParts(pcCU.getRefQP(uiAbsPartIdx), uiAbsPartIdx, uiDepth) # set QP to default QP

        if pcCU.getSlice().getPPS().getTransquantBypassEnableFlag() and \
           pcCU.getNumSucIPCM() == 0:
            self.m_pcEntropyDecoder.decodeCUTransquantBypassFlag(pcCU, uiAbsPartIdx, uiDepth)

        # decode CU mode and the partition size
        if not pcCU.getSlice().isIntra() and pcCU.getNumSucIPCM() == 0:
            self.m_pcEntropyDecoder.decodeSkipFlag(pcCU, uiAbsPartIdx, uiDepth)

        if pcCU.isSkipped(uiAbsPartIdx):
            self.m_ppcCU[uiDepth].copyInterPredInfoFrom(pcCU, uiAbsPartIdx, REF_PIC_LIST_0)
            self.m_ppcCU[uiDepth].copyInterPredInfoFrom(pcCU, uiAbsPartIdx, REF_PIC_LIST_1)
            cMvFieldNeighbours = ArrayTComMvField(MRG_MAX_NUM_CANDS<<1) # double length for mv of both lists
            uhInterDirNeighbours = ArrayUChar(MRG_MAX_NUM_CANDS)
            numValidMergeCand = 0
            for ui in range(MRG_MAX_NUM_CANDS):
                uhInterDirNeighbours[ui] = 0
            self.m_pcEntropyDecoder.decodeMergeIndex(pcCU, 0, uiAbsPartIdx, SIZE_2Nx2N,
                uhInterDirNeighbours.cast(), cMvFieldNeighbours.cast(), uiDepth)
            uiMergeIndex = pcCU.getMergeIndex(uiAbsPartIdx)
            self.m_ppcCU[uiDepth].getInterMergeCandidates(0, 0, uiDepth,
                cMvFieldNeighbours.cast(), uhInterDirNeighbours.cast(), numValidMergeCand, uiMergeIndex)
            pcCU.setInterDirSubParts(uhInterDirNeighbours[uiMergeIndex], uiAbsPartIdx, 0, uiDepth)

            cTmpMv = TComMv(0, 0)
            for uiRefListIdx in range(2):
                if pcCU.getSlice().getNumRefIdx(uiRefListIdx) > 0:
                    pcCU.setMVPIdxSubParts(0, uiRefListIdx, uiAbsPartIdx, 0, uiDepth)
                    pcCU.setMVPNumSubParts(0, uiRefListIdx, uiAbsPartIdx, 0, uiDepth)
                    pcCU.getCUMvField(uiRefListIdx).setAllMvd(cTmpMv, SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
                    pcCU.getCUMvField(uiRefListIdx).setAllMvField(cMvFieldNeighbours[2*uiMergeIndex+uiRefListIdx], SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
            ruiIsLast = self._xFinishDecodeCU(pcCU, uiAbsPartIdx, uiDepth, ruiIsLast)
            return ruiIsLast

        if pcCU.getNumSucIPCM() == 0:
            self.m_pcEntropyDecoder.decodePredMode(pcCU, uiAbsPartIdx, uiDepth)
            self.m_pcEntropyDecoder.decodePartSize(pcCU, uiAbsPartIdx, uiDepth)
        else:
            pcCU.setPredModeSubParts(MODE_INTRA, uiAbsPartIdx, uiDepth)
            pcCU.setPartSizeSubParts(SIZE_2Nx2N, uiAbsPartIdx, uiDepth)
            pcCU.setSizeSubParts(cvar.g_uiMaxCUWidth>>uiDepth, cvar.g_uiMaxCUHeight>>uiDepth, uiAbsPartIdx, uiDepth)
            pcCU.setTrIdxSubParts(0, uiAbsPartIdx, uiDepth)

        if pcCU.isIntra(uiAbsPartIdx) and pcCU.getPartitionSize(uiAbsPartIdx) == SIZE_2Nx2N:
            self.m_pcEntropyDecoder.decodeIPCMInfo(pcCU, uiAbsPartIdx, uiDepth)

            if pcCU.getIPCMFlag(uiAbsPartIdx):
                ruiIsLast = self._xFinishDecodeCU(pcCU, uiAbsPartIdx, uiDepth, ruiIsLast)
                return ruiIsLast

        uiCurrWidth = pcCU.getWidth(uiAbsPartIdx)
        uiCurrHeight = pcCU.getHeight(uiAbsPartIdx)

        # prediction mode ( Intra : direction mode, Inter : Mv, reference idx )
        self.m_pcEntropyDecoder.decodePredInfo(pcCU, uiAbsPartIdx, uiDepth, self.m_ppcCU[uiDepth])

        # Coefficient decoding
        bCodeDQP = self._getdQPFlag()
        self.m_pcEntropyDecoder.decodeCoeff(pcCU, uiAbsPartIdx, uiDepth, uiCurrWidth, uiCurrHeight, bCodeDQP)
        self._setdQPFlag(bCodeDQP)
        ruiIsLast = self._xFinishDecodeCU(pcCU, uiAbsPartIdx, uiDepth, ruiIsLast)
        return ruiIsLast

    def _xFinishDecodeCU(self, pcCU, uiAbsPartIdx, uiDepth, ruiIsLast):
        if pcCU.getSlice().getPPS().getUseDQP():
            pcCU.setQPSubParts(
                pcCU.getRefQP(uiAbsPartIdx) if self._getdQPFlag() else pcCU.getCodedQP(),
                uiAbsPartIdx, uiDepth) # set QP
        if pcCU.getNumSucIPCM() > 0:
            ruiIsLast = 0
            return ruiIsLast

        ruiIsLast = self._xDecodeSliceEnd(pcCU, uiAbsPartIdx, uiDepth)
        return ruiIsLast

    def _xDecodeSliceEnd(self, pcCU, uiAbsPartIdx, uiDepth):
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
            self.m_pcEntropyDecoder.decodeTerminatingBit(uiIsLast)
        else:
            uiIsLast = 0

        if uiIsLast:
            if pcSlice.isNextDependentSlice() and not pcSlice.isNextSlice():
                pcSlice.setDependentSliceCurEndCUAddr(pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts)
            else:
                pcSlice.setSliceCurEndCUAddr(pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts)
                pcSlice.setDependentSliceCurEndCUAddr(pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts)

        return uiIsLast > 0

    def _xDecompressCU(self, pcCU, pcCUCur, uiAbsPartIdx, uiDepth):
        pcPic = pcCU.getPic()

        bBoundary = False
        uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiAbsPartIdx]]
        uiRPelX = uiLPelX + (cvar.g_uiMaxCUWidth>>uiDepth) - 1
        uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiAbsPartIdx]]
        uiBPelY = uiTPelY + (cvar.g_uiMaxCUHeight>>uiDepth) - 1

        uiCurNumParts = pcPic.getNumPartInCU() >> (uiDepth<<1)
        pcSlice = pcCU.getPic().getSlice(pcCU.getPic().getCurrSliceIdx())
        bStartInCU = (pcCU.getSCUAddr() + uiAbsPartIdx + uiCurNumParts) > pcSlice.getDependentSliceCurStartCUAddr() and \
                     (pcCU.getSCUAddr() + uiAbsPartIdx) < pcSlice.getDependentSliceCurStartCUAddr()
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
            for uiPartIdx in range(4):
                uiLPelX = pcCU.getCUPelX() + g_auiRasterToPelX[g_auiZscanToRaster[uiIdx]]
                uiTPelY = pcCU.getCUPelY() + g_auiRasterToPelY[g_auiZscanToRaster[uiIdx]]

                binSlice = pcCU.getSCUAddr() + uiIdx + uiQNumParts > pcSlice.getDependentSliceCurStartCUAddr() and \
                           pcCU.getSCUAddr() + uiIdx < pcSlice.getDependentSliceCurEndCUAddr() # SliceCurStartCUAddr() ???
                if binSlice and \
                   uiLPelX < pcSlice.getSPS().getPicWidthInLumaSamples() and \
                   uiTPelY < pcSlice.getSPS().getPicHeightInLumaSamples():
                    self._xDecompressCU(pcCU, self.m_ppcCU[uiNextDepth], uiIdx, uiNextDepth)

                uiIdx += uiQNumParts
            return

        # Residual reconstruction
        self.m_ppcYuvResi[uiDepth].clear()

        self.m_ppcCU[uiDepth].copySubCU(pcCU, uiAbsPartIdx, uiDepth)

        predMode = self.m_ppcCU[uiDepth].getPredictionMode(0)
        if predMode == MODE_INTER:
            self._xReconInter(self.m_ppcCU[uiDepth], uiAbsPartIdx, uiDepth)
        elif predMode == MODE_INTRA:
            self._xReconIntraQT(self.m_ppcCU[uiDepth], uiAbsPartIdx, uiDepth)
        else:
            assert(False)
        if self.m_ppcCU[uiDepth].isLosslessCoded(0) and \
           self.m_ppcCU[uiDepth].getIPCMFlag(0) == False:
            self._xFillPCMBuffer(self.m_ppcCU[uiDepth], uiAbsPartIdx, uiDepth)

        self._xCopyToPic(self.m_ppcCU[uiDepth], pcPic, uiAbsPartIdx, uiDepth)

    def _xReconInter(self, pcCU, uiAbsPartIdx, uiDepth):
        # inter prediction
        self.m_pcPrediction.motionCompensation(pcCU, self.m_ppcYuvReco[uiDepth])

        # inter recon
        self._xDecodeInterTexture(pcCU, 0, uiDepth)

        # clip for only non-zero cbp case
        if pcCU.getCbf(0, TEXT_LUMA) or pcCU.getCbf(0, TEXT_CHROMA_U) or pcCU.getCbf(0, TEXT_CHROMA_V):
            self.m_ppcYuvReco[uiDepth].addClip(
                self.m_ppcYuvReco[uiDepth], self.m_ppcYuvResi[uiDepth],
                0, pcCU.getWidth(0))
        else:
            self.m_ppcYuvReco[uiDepth].copyPartToPartYuv(
                self.m_ppcYuvReco[uiDepth], 0,
                pcCU.getWidth(0), pcCU.getHeight(0))

    def _xReconIntraQT(self, pcCU, uiAbsPartIdx, uiDepth):
        uiInitTrDepth = 0 if pcCU.getPartitionSize(0) == SIZE_2Nx2N else 1
        uiNumPart = pcCU.getNumPartInter()
        uiNumQPart = pcCU.getTotalNumPart() >> 2

        if pcCU.getIPCMFlag(0):
            self._xReconPCM(pcCU, uiAbsPartIdx, uiDepth)
            return

        for uiPU in range(uiNumPart):
            self._xIntraLumaRecQT(pcCU, uiInitTrDepth, uiPU * uiNumQPart,
                self.m_ppcYuvReco[uiDepth], self.m_ppcYuvReco[uiDepth], self.m_ppcYuvResi[uiDepth])

        for uiPU in range(uiNumPart):
            self._xIntraChromaRecQT(pcCU, uiInitTrDepth, uiPU * uiNumQPart,
                self.m_ppcYuvReco[uiDepth], self.m_ppcYuvReco[uiDepth], self.m_ppcYuvResi[uiDepth])

    def _xIntraRecLumaBlk(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiWidth = pcCU.getWidth(0) >> uiTrDepth
        uiHeight = pcCU.getHeight(0) >> uiTrDepth
        uiStride = pcRecoYuv.getStride()
        piReco = pcRecoYuv.getLumaAddr(uiAbsPartIdx)
        piPred = pcPredYuv.getLumaAddr(uiAbsPartIdx)
        piResi = pcResiYuv.getLumaAddr(uiAbsPartIdx)

        uiNumCoeffInc = (pcCU.getSlice().getSPS().getMaxCUWidth() *
                         pcCU.getSlice().getSPS().getMaxCUHeight()) >> \
                        (pcCU.getSlice().getSPS().getMaxCUDepth() << 1)
        pcCoeff = TCoeffAdd(pcCU.getCoeffY(), uiNumCoeffInc * uiAbsPartIdx)

        uiLumaPredMode = pcCU.getLumaIntraDir(uiAbsPartIdx)

        uiZOrder = pcCU.getZorderIdxInCU() + uiAbsPartIdx
        piRecIPred = pcCU.getPic().getPicYuvRec().getLumaAddr(pcCU.getAddr(), uiZOrder)
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
                                             piPred, uiStride, uiWidth, uiHeight,
                                             pcCU, bAboveAvail, bLeftAvail)

        #===== inverse transform =====
        self.m_pcTrQuant.setQPforQuant(ord(pcCU.getQP(0)), TEXT_LUMA, pcCU.getSlice().getSPS().getQpBDOffsetY(), 0)

        scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[TEXT_LUMA]
        assert(scalingListType < 6)
        self.m_pcTrQuant.invtransformNxN(
            pcCU.getCUTransquantBypass(uiAbsPartIdx), TEXT_LUMA,
            pcCU.getLumaIntraDir(uiAbsPartIdx), piResi,
            uiStride, pcCoeff, uiWidth, uiHeight,
            scalingListType, useTransformSkip)

        #===== reconstruction =====
        pPred = ArrayPel.frompointer(piPred); uiPred = 0
        pResi = ArrayPel.frompointer(piResi); uiResi = 0
        pReco = ArrayPel.frompointer(piReco); uiReco = 0
        pRecIPred = ArrayPel.frompointer(piRecIPred); uiRecIPred = 0
        for uiY in range(uiHeight):
            for uiX in range(uiWidth):
                pReco[uiReco+uiX] = Clip(pPred[uiPred+uiX] + pResi[uiResi+uiX])
                pRecIPred[uiRecIPred+uiX] = pReco[uiReco+uiX]
            uiPred += uiStride
            uiResi += uiStride
            uiReco += uiStride
            uiRecIPred += uiRecIPredStride

    def _xIntraRecChromaBlk(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, uiChromaId):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiLog2TrSize = ord(cvar.g_aucConvertToBit[pcCU.getSlice().getSPS().getMaxCUWidth() >> uiFullDepth]) + 2

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

        uiNumCoeffInc = ((pcCU.getSlice().getSPS().getMaxCUWidth() *
                          pcCU.getSlice().getSPS().getMaxCUHeight()) >> \
                         (pcCU.getSlice().getSPS().getMaxCUDepth() << 1)) >> 2
        pcCoeff = TCoeffAdd((pcCU.getCoeffCr() if uiChromaId > 0 else pcCU.getCoeffCb()), uiNumCoeffInc * uiAbsPartIdx)

        uiChromaPredMode = pcCU.getChromaIntraDir(0)

        uiZOrder = pcCU.getZorderIdxInCU() + uiAbsPartIdx
        piRecIPred = \
            pcCU.getPic().getPicYuvRec().getCrAddr(pcCU.getAddr(), uiZOrder) if uiChromaId > 0 else \
            pcCU.getPic().getPicYuvRec().getCbAddr(pcCU.getAddr(), uiZOrder)
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
        self.m_pcPrediction.predIntraChromaAng(pcCU.getPattern(), pPatChroma, uiChromaPredMode,
                                               piPred, uiStride, uiWidth, uiHeight,
                                               pcCU, bAboveAvail, bLeftAvail)

        #===== inverse transform =====
        curChromaQpOffset = 0
        if eText == TEXT_CHROMA_U:
            curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCbQpOffset() + \
                                pcCU.getSlice().getSliceQpDeltaCb()
        else:
            curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCrQpOffset() + \
                                pcCU.getSlice().getSliceQpDeltaCr()
        self.m_pcTrQuant.setQPforQuant(ord(pcCU.getQP(0)), eText, pcCU.getSlice().getSPS().getQpBDOffsetC(), curChromaQpOffset)

        scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[eText]
        assert(scalingListType < 6)
        self.m_pcTrQuant.invtransformNxN(
            pcCU.getCUTransquantBypass(uiAbsPartIdx), eText,
            REG_DCT, piResi,
            uiStride, pcCoeff, uiWidth, uiHeight,
            scalingListType, useTransformSkipChroma)

        #===== reconstruction =====
        pPred = ArrayPel.frompointer(piPred); uiPred = 0
        pResi = ArrayPel.frompointer(piResi); uiResi = 0
        pReco = ArrayPel.frompointer(piReco); uiReco = 0
        pRecIPred = ArrayPel.frompointer(piRecIPred); uiRecIPred = 0
        for uiY in range(uiHeight):
            for uiX in range(uiWidth):
                pReco[uiReco+uiX] = Clip(pPred[uiPred+uiX] + pResi[uiResi+uiX])
                pRecIPred[uiRecIPred+uiX] = pReco[uiReco+uiX]
            uiPred += uiStride
            uiResi += uiStride
            uiReco += uiStride
            uiRecIPred += uiRecIPredStride

    def _xIntraRecQT(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiTrMode = pcCU.getTransformIdx(uiAbsPartIdx)
        if uiTrMode == uiTrDepth:
            self._xIntraRecLumaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv)
            self._xIntraRecChromaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, 0)
            self._xIntraRecChromaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, 1)
        else:
            uiNumQPart = pcCU.getPic().getNumPartInCU() >> ((uiFullDepth+1) << 1)
            for uiPart in range(4):
                self._xIntraRecQT(pcCU, uiTrDepth+1, uiAbsPartIdx+uiPart*uiNumQPart, pcRecoYuv, pcPredYuv, pcResiYuv)

    def _xReconPCM(self, pcCU, uiAbsPartIdx, uiDepth):
        # Luma
        uiWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uiHeight = cvar.g_uiMaxCUHeight >> uiDepth

        piPcmY = pcCU.getPCMSampleY()
        piRecoY = self.m_ppcYuvReco[uiDepth].getLumaAddr(0, uiWidth)

        uiStride = self.m_ppcYuvResi[uiDepth].getStride()

        self._xDecodePCMTexture(pcCU, 0, piPcmY, piRecoY, uiStride, uiWidth, uiHeight, TEXT_LUMA)

        # Cb and Cr
        uiCWidth = uiWidth >> 1
        uiCHeight = uiHeight >> 1

        piPcmCb = pcCU.getPCMSampleCb()
        piPcmCr = pcCU.getPCMSampleCr()
        pRecoCb = self.m_ppcYuvReco[uiDepth].getCbAddr()
        pRecoCr = self.m_ppcYuvReco[uiDepth].getCrAddr()

        uiCStride = self.m_ppcYuvReco[uiDepth].getCStride()

        self._xDecodePCMTexture(pcCU, 0, piPcmCb, pRecoCb, uiCStride, uiCWidth, uiCHeight, TEXT_CHROMA_U)
        self._xDecodePCMTexture(pcCU, 0, piPcmCr, pRecoCr, uiCStride, uiCWidth, uiCHeight, TEXT_CHROMA_V)

    def _xDecodeInterTexture(self, pcCU, uiAbsPartIdx, uiDepth):
        uiWidth = pcCU.getWidth(uiAbsPartIdx)
        uiHeight = pcCU.getHeight(uiAbsPartIdx)
        uiLumaTrMode = uiChromaTrMode = 0

        pcCU.convertTransIdx(uiAbsPartIdx, pcCU.getTransformIdx(uiAbsPartIdx), uiLumaTrMode, uiChromaTrMode)

        # Y
        piCoeff = pcCU.getCoeffY()
        pResi = self.m_ppcYuvResi[uiDepth].getLumaAddr()

        self.m_pcTrQuant.setQPforQuant(
            ord(pcCU.getQP(uiAbsPartIdx)), TEXT_LUMA,
            pcCU.getSlice().getSPS().getQpBDOffsetY(), 0)
        self.m_pcTrQuant.invRecurTransformNxN(
            pcCU, 0, TEXT_LUMA, pResi,
            0, self.m_ppcYuvResi[uiDepth].getStride(),
            uiWidth, uiHeight, uiLumaTrMode, 0, piCoeff)

        # Cb and Cr
        curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCbQpOffset() + pcCU.getSlice().getSliceQpDeltaCb()
        self.m_pcTrQuant.setQPforQuant(
            ord(pcCU.getQP(uiAbsPartIdx)), TEXT_CHROMA,
            pcCU.getSlice().getSPS().getQpBDOffsetC(), curChromaQpOffset)

        uiWidth >>= 1
        uiHeight >>= 1
        piCoeff = pcCU.getCoeffCb()
        pResi = self.m_ppcYuvResi[uiDepth].getCbAddr()
        self.m_pcTrQuant.invRecurTransformNxN(
            pcCU, 0, TEXT_CHROMA_U, pResi,
            0, self.m_ppcYuvResi[uiDepth].getCStride(),
            uiWidth, uiHeight, uiChromaTrMode, 0, piCoeff)

        curChromaQpOffset = pcCU.getSlice().getPPS().getChromaCrQpOffset() + pcCU.getSlice().getSliceQpDeltaCr()
        self.m_pcTrQuant.setQPforQuant(
            ord(pcCU.getQP(uiAbsPartIdx)), TEXT_CHROMA,
            pcCU.getSlice().getSPS().getQpBDOffsetC(), curChromaQpOffset)

        piCoeff = pcCU.getCoeffCr()
        pResi = self.m_ppcYuvResi[uiDepth].getCrAddr()
        self.m_pcTrQuant.invRecurTransformNxN(
            pcCU, 0, TEXT_CHROMA_V, pResi,
            0, self.m_ppcYuvResi[uiDepth].getCStride(),
            uiWidth, uiHeight, uiChromaTrMode, 0, piCoeff)

    def _xDecodePCMTexture(self, pcCU, uiPartIdx, piPCM, piReco, uiStride, uiWidth, uiHeight, ttText):
        piPicReco = None
        uiPicStride = uiPcmLeftShiftBit = 0

        if ttText == TEXT_LUMA:
            uiPicStride = pcCU.getPic().getPicYuvRec().getStride()
            piPicReco = pcCU.getPic().getPicYuvRec().getLumaAddr(pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiPartIdx)
            uiPcmLeftShiftBit = cvar.g_uiBitDepth + cvar.g_uiBitIncrement - pcCU.getSlice().getSPS().getPCMBitDepthLuma()
        else:
            uiPicStride = pcCU.getPic().getPicYuvRec().getCStride()

            if ttText == TEXT_CHROMA_U:
                piPicReco = pcCU.getPic().getPicYuvRec().getCbAddr(pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiPartIdx)
            else:
                piPicReco = pcCU.getPic().getPicYuvRec().getCrAddr(pcCU.getAddr(), pcCU.getZorderIdxInCU() + uiPartIdx)
            uiPcmLeftShiftBit = cvar.g_uiBitDepth + cvar.g_uiBitIncrement - pcCU.getSlice().getSPS().getPCMBitDepthChroma()

        pPCM = ArrayPel.frompointer(piPCM); uiPCM = 0
        pReco = ArrayPel.frompointer(piReco); uiReco = 0
        pPicReco = ArrayPel.frompointer(piPicReco); uiPicReco = 0
        for uiY in range(uiHeight):
            for uiX in range(uiWidth):
                pReco[uiReco+uiX] = pPCM[uiPCM+uiX] << uiPcmLeftShiftBit
                pPicReco[uiPicReco+uiX] = pReco[uiReco+uiX]
            uiPCM += uiWidth
            uiReco += uiStride
            uiPicReco += uiPicStride

    def _xCopyToPic(self, pcCU, pcPic, uiZorderIdx, uiDepth):
        uiCUAddr = pcCU.getAddr()
        self.m_ppcYuvReco[uiDepth].copyToPicYuv(pcPic.getPicYuvRec(), uiCUAddr, uiZorderIdx)

    def _xIntraLumaRecQT(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiTrMode = pcCU.getTransformIdx(uiAbsPartIdx)
        if uiTrMode == uiTrDepth:
            self._xIntraRecLumaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv)
        else:
            uiNumQPart = pcCU.getPic().getNumPartInCU() >> ((uiFullDepth+1) << 1)
            for uiPart in range(4):
                self._xIntraLumaRecQT(pcCU, uiTrDepth+1, uiAbsPartIdx+uiPart*uiNumQPart, pcRecoYuv, pcPredYuv, pcResiYuv)

    def _xIntraChromaRecQT(self, pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv):
        uiFullDepth = pcCU.getDepth(0) + uiTrDepth
        uiTrMode = pcCU.getTransformIdx(uiAbsPartIdx)
        if uiTrMode == uiTrDepth:
            self._xIntraRecChromaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, 0)
            self._xIntraRecChromaBlk(pcCU, uiTrDepth, uiAbsPartIdx, pcRecoYuv, pcPredYuv, pcResiYuv, 1)
        else:
            uiNumQPart = pcCU.getPic().getNumPartInCU() >> ((uiFullDepth+1) << 1)
            for uiPart in range(4):
                self._xIntraChromaRecQT(pcCU, uiTrDepth+1, uiAbsPartIdx+uiPart*uiNumQPart, pcRecoYuv, pcPredYuv, pcResiYuv)

    def _getdQPFlag(self):
        return self.m_bDecoderDQP

    def _setdQPFlag(self, b):
        self.m_bDecoderDQP = b

    def _xFillPCMBuffer(self, pcCU, uiAbsPartIdx, uiDepth):
        # Luma
        uiWidth = cvar.g_uiMaxCUWidth >> uiDepth
        uiHeight = cvar.g_uiMaxCUHeight >> uiDepth

        piPcmY = pcCU.getPCMSampleY()
        piRecoY = self.m_ppcYuvReco[uiDepth].getLumaAddr(0, uiWidth)

        uiStride = self.m_ppcYuvReco[uiDepth].getStride()

        pPcmY = ArrayPel.frompointer(piPcmY); uiPcmY = 0
        pRecoY = ArrayPel.frompointer(piRecoY); uiRecoY = 0
        for uiY in range(uiHeight):
            for uiX in range(uiWidth):
                pPcmY[uiPcmY+uiX] = pRecoY[uiRecoY+uiX]
            uiPcmY += uiWidth
            uiRecoY += uiStride

        # Cb and Cr
        uiWidthC = uiWidth >> 1
        uiHeightC = uiHeight >> 1

        piPcmCb = pcCU.getPCMSampleCb()
        piPcmCr = pcCU.getPCMSampleCr()
        piRecoCb = self.m_ppcYuvReco[uiDepth].getCbAddr()
        piRecoCr = self.m_ppcYuvReco[uiDepth].getCrAddr()

        uiStrideC = self.m_ppcYuvReco[uiDepth].getCStride()

        pPcmCb = ArrayPel.frompointer(piPcmCb); uiPcmCb = 0
        pPcmCr = ArrayPel.frompointer(piPcmCr); uiPcmCr = 0
        pRecoCb = ArrayPel.frompointer(piRecoCb); uiRecoCb = 0
        pRecoCr = ArrayPel.frompointer(piRecoCr); uiRecoCr = 0
        for uiY in range(uiHeightC):
            for uiX in range(uiWidthC):
                pPcmCb[uiPcmCb+uiX] = pRecoCb[uiRecoCb+uiX]
                pPcmCr[uiPcmCr+uiX] = pRecoCr[uiRecoCr+uiX]
            uiPcmCb += uiWidthC
            uiPcmCr += uiWidthC
            uiRecoCb += uiStrideC
            uiRecoCr += uiStrideC
