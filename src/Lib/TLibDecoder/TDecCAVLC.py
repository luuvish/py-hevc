# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecCAVLC.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import TComMv
    from swig.hevc import ArrayTComMvField, ArrayUChar, ArrayUInt
    from swig.hevc import TCoeffAdd

from .TDecEntropy import TDecEntropy

# TypeDef.h
SIZE_2Nx2N = 0
SIZE_NxN = 3
MODE_INTER = 0
MODE_INTRA = 1
TEXT_LUMA = 0
TEXT_CHROMA_U = 2
TEXT_CHROMA_V = 3
REF_PIC_LIST_0 = 0
REF_PIC_LIST_1 = 1
AM_EXPL = 1
# CommonDef.h
NOT_VALID = -1
MRG_MAX_NUM_CANDS = 5
# TComRom.h
g_auiPUOffset = ArrayUInt.frompointer(cvar.g_auiPUOffset)


def copySaoOneLcuParam(dst, src):
    dst.partIdx = src.partIdx
    dst.typeIdx = src.typeIdx
    if dst.typeIdx != -1:
        dst.subTypeIdx = src.subTypeIdx
        dst.length = src.length
        for i in xrange(dst.length):
            dst.offset[i] = src.offset[i]
    else:
        dst.length = 0
        for i in xrange(SAO_BO_LEN):
            dst.offset[i] = 0

class TDecCAVLC(TDecEntropy):

    def __init__(self):
        super(TDecCAVLC, self).__init__()

        self.m_pcBitstream = None

    def resetEntropy(self, pcSlice):
        assert(False)
    def setBitstream(self, p):
        self.m_pcBitstream = p

    def parseTransformSubdivFlag(self, ruiSubdivFlag, uiLog2TransformBlockSize):
        return ruiSubdivFlag
    def parseQtCbf(self, pcCU, uiAbsPartIdx, eType, uiTrDepth, uiDepth):
    def parseQtRootCbf(self, pcCU, uiAbsPartIdx, uiDepth, uiQtRootCbf):
        return uiQtRootCbf
    def parseVPS(self, pcVPS):
    def parseSPS(self, pcSPS):
    def parsePPS(self, pcPPS):
        uiCode = 0
        iCode = 0

        uiCode = self._xReadUvlc("pic_parameter_set_id")
        pcPPS.setPPSId(uiCode)
        uiCode = self._xReadUvlc("seq_parameter_set_id")
        pcPPS.setSPSId(uiCode)

        uiCode = self._xReadFlag("sign_data_hiding_flag")
        pcPPS.setSignHideFlag(uiCode)

        uiCode = self._xReadFlag("cabac_init_present_flag")
        pcPPS.setCabacInitPresentFlag(True if uiCode else False)

        uiCode = self._xReadUvlc("num_ref_idx_l0_default_active_minus1")
        pcPPS.setNumRefIdxL0DefaultActive(uiCode+1)
        uiCode = self._xReadUvlc("num_ref_idx_l1_default_active_minus1")
        pcPPS.setNumRefIdxL1DefaultActive(uiCode+1)

        iCode = self._xReadSvlc("pic_init_qp_minus26")
        pcPPS.setPicInitQPMinus26(iCode)
        uiCode = self._xReadFlag("constrained_intra_pred_flag")
        pcPPS.setConstrainedIntraPred(True if uiCode else False)
        uiCode = self._xReadFlag("transform_skip_enabled_flag")
        pcPPS.setUseTransformSkip(True if uiCode else False)

        # alf_param() ?
        uiCode = self._xReadFlag("cu_qp_delta_enabled_flag")
        pcPPS.setUseDQP(True if uiCode else False)
        if pcPPS.getUseDQP():
            uiCode = self._xReadUvlc("diff_cu_qp_delta_depth")
            pcRPS.setMaxCuDQPDepth(uiCode)
        else:
            pcPPS.setMaxCuDQPDepth(0)

        iCode = self._xReadSvlc("cb_qp_offset")
        pcPPS.setChromaCbQpOffset(iCode)
        assert(pcPPS.getChromaCbQpOffset() >= -12)
        assert(pcPPS.getChromaCbQpOffset() <= 12)

        iCode = self._xReadSvlc("cr_qp_offset")
        pcPPS.setChromaCrQpOffset(iCode)
        assert(pcPPS.getChromaCrQpOffset() >= -12)
        assert(pcPPS.getChromaCrQpOffset() <= 12)

        uiCode = self._xReadFlag("slicelevel_chroma_qp_flag")
        pcPPS.setSliceChromaQpFlag(True if uiCode else False)

        uiCode = self._xReadFlag("weighted_pred_flag") # Use of Weighting Prediction (P_SLICE)
        pcPPS.setUseWP(uiCode == 1)
        uiCode = self._xReadFlag("weighted_bipred_flag") # Use of Bi-Directional Weighting Prediction (B_SLICE)
        pcPPS.setWPBiPred(uiCode == 1)
        sys.stdout.write("TDecCavlc::parsePPS():\tm_bUseWeightPred=%d\tm_uiBiPredIdc=%d\n" %
            (pcPPS.getUseWP(), pcPPS.getWPBiPred()))

        uiCode = self._xReadFlag("output_flag_present_flag")
        pcPPS.setOutputFlagPresentFlag(uiCode == 1)

        uiCode = self._xReadFlag("dependent_slices_enabled_flag")
        pcPPS.setDependentSlicesEnabledFlag(uiCode == 1)

        uiCode = self._xReadFlag("transquant_bypass_enable_flag")
        pcPPS.settransquantBypassEnableFlag(True if uiCode else False)

        uiCode = self._xReadCode(2, "tiles_or_entropy_coding_sync_idc")
        pcPPS.setTilesOrEntropyCodingSyncIdx(uiCode)
        if pcPPS.setTilesOrEntropyCodingSyncIdx() == 1:
            uiCode = self._xReadUvlc("num_tile_columns_minus1")
            pcPPS.setNumColumnsMinus1(uiCode)
            uiCode = self._xReadUvlc("num_tile_rows_minus1")
            pcPPS.setNumRowsMinus1(uiCode)
            uiCode = self._xReadFlag("uniform_spacing_flag")
            pcPPS.setUniformSpacingIdr(uiCode)

            if pcPPS.getUniformSpacingIdr() == 0:
                columnWidth = ArrayUInt(pcPPS.getNumColumnsMinus1())
                for i in xrange(pcPPS.getNumColumnsMinus1()):
                    uiCode = self._xReadUvlc("column_width")
                    columnWidth[i] = uiCode
                pcPPS.setColumnWidth(columnWidth)
                del columnWidth

                rowHeight = ArrayUInt(pcPPS.getNumRowsMinus1())
                for i in xrange(pcPPS.getNumRowsMinus1()):
                    uiCode = self._xReadUvlc("row_width")
                    rowHeight[i] = uiCode
                pcPPS.setRowHeight(rowHeight)
                del rowHeight

            if pcPPS.getNumColumnsMinus1() != 0 or pcPPS.getNumRowsMinus1() != 0:
                uiCode = self._xReadFlag("loop_filter_across_tiles_enabled_flag")
                pcPPS.setLFCrossTileBoundaryFlag(True if uiCode == 1 else False)
        elif pcPPS.getTilesOrEntropyCodingSyncIdc() == 3:
            uiCode = self._xReadFlag("cabac_independent_flag")
            pcPPS.setCabacIndependentFlag(True if uiCode == 1 else False)

        uiCode = self._xReadFlag("loop_filter_across_slice_flag")
        pcPPS.setLFCrossSliceBoundaryFlag(True if uiCode else False)

        uiCode = self._xReadFlag("deblocking_filter_control_present_flag")
        pcPPS.setDeblockingFilterControlPresent(True if uiCode else False)
        if pcPPS.getDeblockingFilterControlPresent():
            uiCode = self._xReadFlag("pps_deblocking_filter_flag")
            pcPPS.setLoopFilterOffsetInPPS(True if uiCode == 1 else False)
            if pcPPS.getLoopFilterOffsetInPPS():
                uiCode = self._xReadFlag("disable_deblocking_filter_flag")
                pcPPS.setLoopFilterDisable(1 if uiCode else 0)
                if not pcPPS.getLoopFilterDisable():
                    iCode = self._xReadSvlc("pps_beta_offset_div2")
                    pcPPS.setLoopFilterBetaOffset(iCode)
                    iCode = self._xReadSvlc("pps_tc_offset_div2")
                    pcPPS.setLoopFilterTcOffset(iCode)
        uiCode = self._xReadFlag("pps_scaling_list_data_present_flag")
        pcPPS.setScalingListPresentFlag(True if uiCode == 1 else False)
        if pcPPS.getScalingListPresentFlag():
            self.parseScalingList(pcPPS.getScalingList())
        uiCode = self._xReadUvlc("log2_parallel_merge_level_minus2")
        pcPPS.setLog2ParallelMergeLevelMinus2(uiCode)

        uiCode = self._xReadFlag("slice_header_extension_present_flag")
        pcPPS.setSliceHeaderExtensionPresentFlag(uiCode)

        uiCode = self._xReadFlag("pps_extension_flag")
        if uiCode:
            while self._xMoreRbspData():
                uiCode = self._xReadFlag("pps_extension_flag")

    def parseSEI(self, seis):
        assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
        while True:
            self.parseSEImessage(self.m_pcBitstream, seis)
            # SEI messages are an integer number of bytes, something has failed
            # in the parsing if bitstream not byte-aligned
            assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
            if 0x80 == self.m_pcBitstream.peekBits(8):
                break
        assert(self.m_pcBitstream.getNumBitsLeft() == 8) # rsbp_trailing_bits

    def parseSliceHeader(self, rpcSlice, parameterSetManager):
    def parseTerminatingBit(self, ruiBit):
        return ruiBit

    def parseMVPIdx(self, riMVPIdx):
        return riMVPIdx

    def parseSkipFlag(self, pcCU, uiAbsPartIdx, uiDepth):
    def parseCUTransquantBypassFlag(self, pcCU, uiAbsPartIdx, uiDepth):
    def parseMergeFlag(self, pcCU, uiAbsPartIdx, uiDepth, uiPUIdx):
    def parseMergeIndex(self, pcCU, ruiMergeIndex, uiAbsPartIdx, uiDepth):
        return ruiMergeIndex
    def parseSplitFlag(self, pcCU, uiAbsPartIdx, uiDepth):
    def parsePartSize(self, pcCU, uiAbsPartIdx, uiDepth):
    def parsePredMode(self, pcCU, uiAbsPartIdx, uiDepth):

    def parseIntraDirLumaAng(self, pcCU, uiAbsPartIdx, uiDepth):
    def parseIntraDirChroma(self, pcCU, uiAbsPartIdx, uiDepth):

    def parseInterDir(self, pcCU, ruiInterDir, uiAbsPartIdx, uiDepth):
        return ruiInterDir
    def parseRefFrmIdx(self, pcCU, riRefFrmIdx, uiAbsPartIdx, uiDepth, eRefList):
        return riRefFrmIdx
    def parseMvd(self, pcCU, uiAbsPartIdx, uiPartIdx, uiDepth, eRefList):

    def parseDeltaQP(self, pcCU, uiAbsPartIdx, uiDepth):
    def parseCoeffNxN(self, pcCU, pcCoef, uiAbsPartIdx, uiWidth, uiHeight, uiDepth, eTType):
    def parseTransformSkilFlags(self, pcCU, uiAbsPartIdx, width, height, uiDepth, eTType):

    def parseIPCMInfo(self, pcCU, uiAbsPartIdx, uiDepth):

    def updateContextTables(self, eSliceType, iQp): pass
    def decodeFlush(self): pass

    def xParsePredWeightTable(self, pcSlice):
    def parseScalingList(self, scalingList):
    def xDecodeScalingList(self, scalingList, sizeId, listId):

    def _xMoreRbspData(self):

    def _xReadCode(self, uiLength, ruiCode):
        return ruiCode

    def _xReadUvlc(self, ruiVal):
        return ruiVal

    def _xReadSvlc(self, riVal):
        return riVal

    def _xReadFlag(self, ruiCode):
        return ruiCode

    def _xReadEpExGolomb(self, ruiSymbol, uiCount):
        return ruiSymbol

    def _xReadExGolombLevel(self, ruiSymbol):
        return ruiSymbol

    def _xReadUnaryMaxSymbol(self, ruiSymbol, uiMaxSymbol):
        return ruiSymbol

    def _xReadPCMAlignZero(self):
    def _xGetBit(self):
    def _parseShortTermRefPicSet(self, pcSPS, pcRPS, idx):
        cdoe = 0
        interRPSPred = self._xReadFlag("inter_ref_pic_set_prediction_flag")
        rps.setInterRPSPrediction(interRPSPred)
        if interRPSPred:
            if idx == sps.getRPSList().getNumberOfReferencePictureSets():
                code = self._xReadUvlc("delta_idx_minus1") # delta index of the Reference Picture Set used for prediction minus 1
            else:
                code = 0
            assert(code <= idx-1) # delta_idx_minus1 shall not be larger than idx-1, otherwise we will predict from a negative row position that does not exist. When idx equals 0 there is no legal value and interRPSPred must be zero. See J0185-r2
            rIdx = idx - 1 - code
            assert(0 <= rIdx <= idx-1) # Made assert tighter; if rIdx = idx then prediction is done from itself. rIdx must belong to range 0, idx-1, inclusive, see J0185-r2
            rpsRef = sps.getRPSList().getReferencePictureSet(rIdx)
            k = k0 = k1 = 0
            bit = self._xReadCode(1, "delta_rps_sign") # delta_RPS_sign
            code = self._xReadUvlc("abs_delta_rps_minus1") # absolute delta RPS minus 1
            deltaRPS = (1 - (bit<<1)) * (code + 1) # delta_RPS
            for j in xrange(rpsRef.getNumberOfPictures()):
                bit = self._xReadCode(1, "used_by_curr_pic_flag") #first bit is "1" if Idc is 1
                refIdx = bit
                if refIdx == 0:
                    bit = self._xReadCode(1, "use_delta_flag") #second bit is "1" if Idc is 2, "0" otherwise.
                    refIdc = bit << 1 #second bit is "1" if refIdc is 2, "0" if refIdc = 0.
                if refIdc == 1 or refIdc == 2:
                    deltaPOC = deltaRPS + (rpsRef.getDeltaPOC(j) if j < rpsRef.getNumberOfPictures() else 0)
                    rps.setDeltaPOC(k, deltaPOC)
                    rps.setUsed(k, refIdc == 1)

                    if deltaPOC < 0:
                        k0 += 1
                    else:
                        k1 += 1
                    k += 1
                rps.setRefIdx(j, refIdc)
            rps.setNumRefIdx(rpsRef.getNumberOfPictures() + 1)
            rps.setNumberOfPictures(k)
            rps.setNumberOfNegativePictures(k0)
            rps.setNumberOfPositivePictures(k1)
            rps.sortDeltaPOC()
        else:
            code = self._xReadUvlc("num_negative_pics")
            rps.setNumberOfNegativePictures(code)
            code = self._xReadUvlc("num_positive_pics")
            rps.setNumberOfPositivePictures(code)
            prev = 0
            poc = 0
            for j in xrange(rps.getNumberOfNegativePictures()):
                code = self._xReadUvlc("delta_poc_s0_minus1")
                poc = prev - code - 1
                prev = poc
                rps.setDeltaPOC(j, poc)
                code = self._xReadFlag("used_by_curr_pic_s0_flag")
                rps.setUsed(j, code)
            prev = 0
            for j in xrange(rps.getNumberOfNegativePictures(),
                            rps.getNumberOfNegativePictures()+rps.getNumberOfPositivePictures()):
                code = self._xReadUvlc("delta_poc_s1_minus1")
                poc = prev + code + 1
                prev = poc
                rps.setDeltaPOC(j, poc)
                code = self._xReadFlag("used_by_curr_pic_s1_flag")
                rps.setUsed(j, code)
            rps.setNumberOfPictures(rps.getNumberOfNegativePictures()+rps.getNumberOfPositivePictures())
