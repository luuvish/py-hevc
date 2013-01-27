# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecCAVLC.py
    HM 9.2 Python Implementation
"""

import sys

from ... import pointer
from ... import Trace

from ... import TComSPS
from ... import ArrayUInt

from ... import cvar

from .SyntaxElementParser import SyntaxElementParser
from .TDecEntropy import TDecEntropy

from ..TLibCommon.TypeDef import (
    MAX_VPS_OP_SETS_PLUS1,
    MAX_VPS_NUH_RESERVED_ZERO_LAYER_ID_PLUS1,
    B_SLICE, P_SLICE, I_SLICE,
    REF_PIC_LIST_0, REF_PIC_LIST_1,
    SCAN_DIAG
)

from ..TLibCommon.CommonDef import (
    MAX_NUM_REF, Clip3, MRG_MAX_NUM_CANDS,
    NAL_UNIT_CODED_SLICE_BLA,
    NAL_UNIT_CODED_SLICE_BLANT,
    NAL_UNIT_CODED_SLICE_BLA_N_LP
)

from ..TLibCommon.TComRom import (
    SCALING_LIST_START_VALUE, MAX_MATRIX_COEF_NUM,
    SCALING_LIST_8x8, SCALING_LIST_SIZE_NUM,
    g_auiSigLastScan, g_sigLastScanCG32x32,
    g_scalingListSize, g_scalingListNum
)


def xTraceVUIHeader(pVUI, pcSPS):
    Trace.g_hTrace.write("----------- vui_parameters -----------\n")

def xTraceSPSHeader(pSPS):
    Trace.g_hTrace.write("=========== Sequence Parameter Set ID: %d ===========\n" % pSPS.getSPSId())

def xTracePPSHeader(pPPS):
    Trace.g_hTrace.write("=========== Picture Parameter Set ID: %d ===========\n" % pPPS.getPPSId())

def xTraceSliceHeader(pSlice):
    Trace.g_hTrace.write("=========== Slice ===========\n")


class TDecCavlc(SyntaxElementParser, TDecEntropy):

    def __init__(self):
        super(TDecCavlc, self).__init__()

    def xReadEpExGolomb(self, ruiSymbol, uiCount):
        uiSymbol = 0
        uiBit = 1

        while uiBit:
            uiBit = self.xReadFlag(uiBit)
            uiSymbol += uiBit << uiCount
            uiCount += 1

        uiCount -= 1
        while uiCount:
            uiCount -= 1
            uiBit = self.xReadFlag(uiBit)
            uiSymbol += uiBit << uiCount

        ruiSymbol = uiSymbol
        return ruiSymbol

    def xReadExGolombLevel(self, ruiSymbol):
        uiSymbol = 0
        uiCount = 0

        while True:
            uiSymbol = self.xReadFlag(uiSymbol)
            uiCount += 1
            if not (uiSymbol and uiCount != 13):
                break

        ruiSymbol = uiCount - 1

        if uiSymbol:
            uiSymbol = self.xReadEpExGolomb(uiSymbol, 0)
            ruiSymbol += uiSymbol + 1

        return ruiSymbol

    def xReadUnaryMaxSymbol(self, ruiSymbol, uiMaxSymbol):
        if uiMaxSymbol == 0:
            ruiSymbol = 0
            return ruiSymbol

        ruiSymbol = self.xReadFlag(ruiSymbol)

        if ruiSymbol == 0 or uiMaxSymbol == 1:
            return ruiSymbol

        uiSymbol = 0
        uiCont = 0

        while True:
            uiCont = self.xReadFlag(uiCont)
            uiSymbol += 1
            if not (uiCont and uiSymbol < uiMaxSymbol-1):
                break

        if uiCont and uiSymbol == uiMaxSymbol-1:
            uiSymbol += 1

        ruiSymbol = uiSymbol
        return ruiSymbol

    def xReadPCMAlignZero(self):
        uiNumberOfBits = self.m_pcBitstream.getNumBitsUntilByteAligned()

        if uiNumberOfBits:
            uiSymbol = 0

            for uiBits in xrange(uiNumberOfBits):
                uiSymbol = self.xReadFlag(uiSymbol)

                if uiSymbol:
                    sys.stdout.write("\nWarning! pcm_align_zero include a non-zero value.\n")

    def xGetBit(self):
        ruiCode = 0
        ruiCode = self.m_pcBitstream.read(1, ruiCode)
        return ruiCode

    def parseShortTermRefPicSet(self, sps, rps, idx):
        code = 0
        interRPSPred = 0
        if idx > 0:
            interRPSPred = self.xReadFlag(interRPSPred, 'inter_ref_pic_set_prediction_flag')
            rps.setInterRPSPrediction(interRPSPred)
        else:
            interRPSPred = 0
            rps.setInterRPSPrediction(0)

        if interRPSPred:
            bit = 0
            if idx == sps.getRPSList().getNumberOfReferencePictureSets():
                code = self.xReadUvlc(code, 'delta_idx_minus1') # delta index of the Reference Picture Set used for prediction minus 1
            else:
                code = 0
            assert(code <= idx-1) # delta_idx_minus1 shall not be larger than idx-1, otherwise we will predict from a negative row position that does not exist. When idx equals 0 there is no legal value and interRPSPred must be zero. See J0185-r2
            rIdx = idx - 1 - code
            assert(0 <= rIdx <= idx-1) # Made assert tighter; if rIdx = idx then prediction is done from itself. rIdx must belong to range 0, idx-1, inclusive, see J0185-r2
            rpsRef = sps.getRPSList().getReferencePictureSet(rIdx)
            k = k0 = k1 = 0
            bit = self.xReadCode(1, bit, 'delta_rps_sign') # delta_RPS_sign
            code = self.xReadUvlc(code, 'abs_delta_rps_minus1') # absolute delta RPS minus 1
            deltaRPS = (1 - 2 * bit) * (code + 1) # delta_RPS
            for j in xrange(rpsRef.getNumberOfPictures()+1):
                bit = self.xReadCode(1, bit, 'used_by_curr_pic_flag') #first bit is "1" if Idc is 1
                refIdc = bit
                if refIdc == 0:
                    bit = self.xReadCode(1, bit, 'use_delta_flag') #second bit is "1" if Idc is 2, "0" otherwise.
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
                rps.setRefIdc(j, refIdc)
            rps.setNumRefIdc(rpsRef.getNumberOfPictures() + 1)
            rps.setNumberOfPictures(k)
            rps.setNumberOfNegativePictures(k0)
            rps.setNumberOfPositivePictures(k1)
            rps.sortDeltaPOC()
        else:
            code = self.xReadUvlc(code, 'num_negative_pics')
            rps.setNumberOfNegativePictures(code)
            code = self.xReadUvlc(code, 'num_positive_pics')
            rps.setNumberOfPositivePictures(code)
            prev = 0
            poc = 0
            for j in xrange(rps.getNumberOfNegativePictures()):
                code = self.xReadUvlc(code, 'delta_poc_s0_minus1')
                poc = prev - code - 1
                prev = poc
                rps.setDeltaPOC(j, poc)
                code = self.xReadFlag(code, 'used_by_curr_pic_s0_flag')
                rps.setUsed(j, code)
            prev = 0
            for j in xrange(rps.getNumberOfNegativePictures(),
                            rps.getNumberOfNegativePictures()+rps.getNumberOfPositivePictures()):
                code = self.xReadUvlc(code, 'delta_poc_s1_minus1')
                poc = prev + code + 1
                prev = poc
                rps.setDeltaPOC(j, poc)
                code = self.xReadFlag(code, 'used_by_curr_pic_s1_flag')
                rps.setUsed(j, code)
            rps.setNumberOfPictures(rps.getNumberOfNegativePictures()+rps.getNumberOfPositivePictures())

    def resetEntropy(self, pcSlice):
        assert(False)
    def setBitstream(self, p):
        self.m_pcBitstream = p
    def parseTransformSubdivFlag(self, ruiSubdivFlag, uiLog2TransformBlockSize):
        assert(False)
    def parseQtCbf(self, pcCU, uiAbsPartIdx, eType, uiTrDepth, uiDepth):
        assert(False)
    def parseQtRootCbf(self, uiAbsPartIdx, uiQtRootCbf):
        assert(False)

    def parseVPS(self, pcVPS):
        uiCode = 0

        uiCode = self.xReadCode(4, uiCode, 'vps_video_parameter_set_id')
        pcVPS.setVPSId(uiCode)
        uiCode = self.xReadCode(2, uiCode, 'vps_reserved_three_2bits')
        assert(uiCode == 3)
        uiCode = self.xReadCode(6, uiCode, 'vps_reserved_zero_6bits')
        assert(uiCode == 0)
        uiCode = self.xReadCode(3, uiCode, 'vps_max_sub_layers_minus1')
        pcVPS.setMaxTLayers(uiCode + 1)
        uiCode = self.xReadFlag(uiCode, 'vps_temporal_id_nesting_flag')
        pcVPS.setTemporalNestingFlag(True if uiCode else False)
        assert(pcVPS.getMaxTLayers() > 1 or pcVPS.getTemporalNestingFlag())
        uiCode = self.xReadCode(16, uiCode, 'vps_reserved_ffff_16bits')
        assert(uiCode == 0xffff)
        self.parsePTL(pcVPS.getPTL(), True, pcVPS.getMaxTLayers()-1)
        self.parseBitratePicRateInfo(pcVPS.getBitratePicrateInfo(), 0, pcVPS.getMaxTLayers()-1)
        subLayerOrderingInfoPresentFlag = 0
        subLayerOrderingInfoPresentFlag = self.xReadFlag(subLayerOrderingInfoPresentFlag, 'vps_sub_layer_ordering_info_present_flag')
        for i in xrange(pcVPS.getMaxTLayers()):
            uiCode = self.xReadUvlc(uiCode, 'vps_max_dec_pic_buffering[i]')
            pcVPS.setMaxDecPicBuffering(uiCode, i)
            uiCode = self.xReadUvlc(uiCode, 'vps_num_reorder_pics[i]')
            pcVPS.setNumReorderPics(uiCode, i)
            uiCode = self.xReadUvlc(uiCode, 'vps_max_latency_increase[i]')
            pcVPS.setMaxLatencyIncrease(uiCode, i)

            if not subLayerOrderingInfoPresentFlag:
                i += 1
                while i < pcVPS.getMaxTLayers():
                    pcVPS.setMaxDecPicBuffering(pcVPS.getMaxDecPicBuffering(0), i)
                    pcVPS.setNumReorderPics(pcVPS.getNumReorderPics(0), i)
                    pcVPS.setMaxLatencyIncrease(pcVPS.getMaxLatencyIncrease(0), i)
                break

        assert(pcVPS.getNumHrdParameters() < MAX_VPS_OP_SETS_PLUS1)
        assert(pcVPS.getMaxNuhReservedZeroLayerId() < MAX_VPS_NUH_RESERVED_ZERO_LAYER_ID_PLUS1)
        uiCode = self.xReadCode(6, uiCode, 'vps_max_nuh_reserved_zero_layer_id')
        pcVPS.setMaxNuhReservedZeroLayerId(uiCode)
        uiCode = self.xReadUvlc(uiCode, 'vps_max_op_sets_minus1')
        pcVPS.setMaxOpSets(uiCode + 1)
        for opsIdx in xrange(1, pcVPS.getMaxOpSets()):
            # Operation point set
            for i in xrange(pcVPS.getMaxNuhReservedZeroLayerId()+1):
                uiCode = self.xReadFlag(uiCode, 'layer_id_included_flag[opsIdx][i]')
                pcVPS.setLayerIdIncludedFlag(True if uiCode == 1 else False, opsIdx, i)

        uiCode = self.xReadUvlc(uiCode, 'vps_num_hrd_parameters')
        pcVPS.setNumHrdParameters(uiCode)

        if pcVPS.getNumHrdParameters() > 0:
            pcVPS.createHrdParamBuffer()
        for i in xrange(pcVPS.getNumHrdParameters()):
            uiCode = self.xReadUvlc(uiCode, 'hrd_op_set_idx')
            pcVPS.setHrdOpSetIdx(uiCode, i)
            if i > 0:
                uiCode = self.xReadFlag(uiCode, 'cprms_present_flag[i]')
                pcVPS.setCprmsPresentFlag(True if uiCode == 1 else False, i)
            self.parseHrdParameters(pcVPS.getHrdParameters(i), pcVPS.getCprmsPresentFlag(i), pcVPS.getMaxTLayers()-1)

        uiCode = self.xReadFlag(uiCode, 'vps_extension_flag')
        if uiCode:
            while self.xMoreRbspData():
                uiCode = self.xReadFlag(uiCode, 'vps_extension_data_flag')

    @Trace.trace(Trace.on, before=lambda self, pcSPS: xTraceSPSHeader(pcSPS))
    def parseSPS(self, pcSPS):
        uiCode = 0

        uiCode = self.xReadCode(4, uiCode, 'sps_video_parameter_set_id')
        pcSPS.setVPSId(uiCode)
        uiCode = self.xReadCode(3, uiCode, 'sps_max_sub_layers_minus1')
        pcSPS.setMaxTLayers(uiCode+1)
        uiCode = self.xReadFlag(uiCode, 'sps_temporal_id_nesting_flag')
        pcSPS.setTemporalIdNestingFlag(True if uiCode > 0 else False)
        self.parsePTL(pcSPS.getPTL(), 1, pcSPS.getMaxTLayers() - 1)
        uiCode = self.xReadUvlc(uiCode, 'sps_seq_parameter_set_id')
        pcSPS.setSPSId(uiCode)
        uiCode = self.xReadUvlc(uiCode, 'chroma_format_idc')
        pcSPS.setChromaFormatIdc(uiCode)
        # in the first version we only support chroma_format_idc equal to 1 (4:2:0), so separate_colour_plane_flag cannot appear in the bitstream
        assert(uiCode == 1)
        if uiCode == 3:
            uiCode = self.xReadFlag(uiCode, 'separate_colour_plane_flag')
            assert(uiCode == 0)

        uiCode = self.xReadUvlc(uiCode, 'pic_width_in_luma_samples')
        pcSPS.setPicWidthInLumaSamples(uiCode)
        uiCode = self.xReadUvlc(uiCode, 'pic_height_in_luma_samples')
        pcSPS.setPicHeightInLumaSamples(uiCode)
        uiCode = self.xReadFlag(uiCode, 'conformance_window_flag')
        if uiCode != 0:
            conf = pcSPS.getConformanceWindow()
            uiCode = self.xReadUvlc(uiCode, 'conf_win_left_offset')
            conf.setWindowLeftOffset(uiCode * TComSPS.getWinUnitX(pcSPS.getChromaFormatIdc()))
            uiCode = self.xReadUvlc(uiCode, 'conf_win_right_offset')
            conf.setWindowRightOffset(uiCode * TComSPS.getWinUnitX(pcSPS.getChromaFormatIdc()))
            uiCode = self.xReadUvlc(uiCode, 'conf_win_top_offset')
            conf.setWindowTopOffset(uiCode * TComSPS.getWinUnitY(pcSPS.getChromaFormatIdc()))
            uiCode = self.xReadUvlc(uiCode, 'conf_win_bottom_offset')
            conf.setWindowBottomOffset(uiCode * TComSPS.getWinUnitY(pcSPS.getChromaFormatIdc()))

        uiCode = self.xReadUvlc(uiCode, 'bit_depth_luma_minus8')
        cvar.g_bitDepthY = 8 + uiCode
        pcSPS.setBitDepthY(cvar.g_bitDepthY)
        pcSPS.setQpBDOffsetY(6*uiCode)

        uiCode = self.xReadUvlc(uiCode, 'bit_depth_chroma_minus8')
        cvar.g_bitDepthC = 8 + uiCode
        pcSPS.setBitDepthC(cvar.g_bitDepthC)
        pcSPS.setQpBDOffsetC(6*uiCode)

        uiCode = self.xReadUvlc(uiCode, 'log2_max_pic_order_cnt_lsb_minus4')
        pcSPS.setBitsForPOC(4+uiCode)

        subLayerOrderingInfoPresentFlag = 0
        subLayerOrderingInfoPresentFlag = self.xReadFlag(subLayerOrderingInfoPresentFlag, 'sps_sub_layer_ordering_info_present_flag')
        for i in xrange(pcSPS.getMaxTLayers()):
            uiCode = self.xReadUvlc(uiCode, 'sps_max_dec_pic_buffering')
            pcSPS.setMaxDecPicBuffering(uiCode, i)
            uiCode = self.xReadUvlc(uiCode, 'sps_num_reorder_pics')
            pcSPS.setNumReorderPics(uiCode, i)
            uiCode = self.xReadUvlc(uiCode, 'sps_max_latency_increase')
            pcSPS.setMaxLatencyIncrease(uiCode, i)

            if not subLayerOrderingInfoPresentFlag:
                i += 1
                while i < pcSPS.getMaxTLayers():
                    pcSPS.setMaxDecPicBuffering(pcSPS.getMaxDecPicBuffering(0), i)
                    pcSPS.setNumReorderPics(pcSPS.getNumReorderPics(0), i)
                    pcSPS.setMaxLatencyIncrease(pcSPS.getMaxLatencyIncrease(0), i)
                    i += 1
                break

        uiCode = self.xReadUvlc(uiCode, 'log2_min_coding_block_size_minus3')
        log2MinCUSize = uiCode + 3
        uiCode = self.xReadUvlc(uiCode, 'log2_diff_max_min_coding_block_size')
        uiMaxCUDepthCorret = uiCode
        pcSPS.setMaxCUWidth(1 << (log2MinCUSize + uiMaxCUDepthCorret))
        cvar.g_uiMaxCUWidth = 1 << (log2MinCUSize + uiMaxCUDepthCorret)
        pcSPS.setMaxCUHeight(1 << (log2MinCUSize + uiMaxCUDepthCorret))
        cvar.g_uiMaxCUHeight = 1 << (log2MinCUSize + uiMaxCUDepthCorret)
        uiCode = self.xReadUvlc(uiCode, 'log2_min_transform_block_size_minus2')
        pcSPS.setQuadtreeTULog2MinSize(uiCode+2)

        uiCode = self.xReadUvlc(uiCode, 'log2_diff_max_min_transform_block_size')
        pcSPS.setQuadtreeTULog2MaxSize(uiCode + pcSPS.getQuadtreeTULog2MinSize())
        pcSPS.setMaxTrSize(1 << (uiCode + pcSPS.getQuadtreeTULog2MinSize()))

        uiCode = self.xReadUvlc(uiCode, 'max_transform_hierarchy_depth_inter')
        pcSPS.setQuadtreeTUMaxDepthInter(uiCode+1)
        uiCode = self.xReadUvlc(uiCode, 'max_transform_hierarchy_depth_intra')
        pcSPS.setQuadtreeTUMaxDepthIntra(uiCode+1)
        cvar.g_uiAddCUDepth = 0
        while (pcSPS.getMaxCUWidth() >> uiMaxCUDepthCorret) > \
              (1 << (pcSPS.getQuadtreeTULog2MinSize() + cvar.g_uiAddCUDepth)):
            cvar.g_uiAddCUDepth += 1
        pcSPS.setMaxCUDepth(uiMaxCUDepthCorret + cvar.g_uiAddCUDepth)
        cvar.g_uiMaxCUDepth = uiMaxCUDepthCorret + cvar.g_uiAddCUDepth
        # BB: these parameters may be removed completly and replaced by the fixed values
        pcSPS.setMinTrDepth(0)
        pcSPS.setMaxTrDepth(1)
        uiCode = self.xReadFlag(uiCode, 'scaling_list_enabled_flag')
        pcSPS.setScalingListFlag(uiCode)
        if pcSPS.getScalingListFlag():
            uiCode = self.xReadFlag(uiCode, 'sps_scaling_list_data_present_flag')
            pcSPS.setScalingListPresentFlag(uiCode)
            if pcSPS.getScalingListPresentFlag():
                self.parseScalingList(pcSPS.getScalingList())
        uiCode = self.xReadFlag(uiCode, 'amp_enabled_flag')
        pcSPS.setUseAMP(uiCode)
        uiCode = self.xReadFlag(uiCode, 'sample_adaptive_offset_enabled_flag')
        pcSPS.setUseSAO(True if uiCode else False)

        uiCode = self.xReadFlag(uiCode, 'pcm_enabled_flag')
        pcSPS.setUsePCM(True if uiCode else False)
        if pcSPS.getUsePCM():
            uiCode = self.xReadCode(4, uiCode, 'pcm_sample_bit_depth_luma_minus1')
            pcSPS.setPCMBitDepthLuma(1 + uiCode)
            uiCode = self.xReadCode(4, uiCode, 'pcm_sample_bit_depth_chroma_minus1')
            pcSPS.setPCMBitDepthChroma(1 + uiCode)
            uiCode = self.xReadUvlc(uiCode, 'log2_min_pcm_luma_coding_block_size_minus3')
            pcSPS.setPCMLog2MinSize(uiCode + 3)
            uiCode = self.xReadUvlc(uiCode, 'log2_diff_max_min_pcm_luma_coding_block_size')
            pcSPS.setPCMLog2MaxSize(uiCode + pcSPS.getPCMLog2MinSize())
            uiCode = self.xReadFlag(uiCode, 'pcm_loop_filter_disable_flag')
            pcSPS.setPCMFilterDisableFlag(True if uiCode else False)

        uiCode = self.xReadUvlc(uiCode, 'num_short_term_ref_pic_sets')
        pcSPS.createRPSList(uiCode)

        rpsList = pcSPS.getRPSList()

        for i in xrange(rpsList.getNumberOfReferencePictureSets()):
            rps = rpsList.getReferencePictureSet(i)
            self.parseShortTermRefPicSet(pcSPS, rps, i)
        uiCode = self.xReadFlag(uiCode, 'long_term_ref_pics_present_flag')
        pcSPS.setLongTermRefsPresent(uiCode)
        if pcSPS.getLongTermRefsPresent():
            uiCode = self.xReadUvlc(uiCode, 'num_long_term_ref_pic_sps')
            pcSPS.setNumLongTermRefPicSPS(uiCode)
            for k in xrange(pcSPS.getNumLongTermRefPicSPS()):
                uiCode = self.xReadCode(pcSPS.getBitsForPOC(), uiCode, 'lt_ref_pic_poc_lsb_sps')
                pcSPS.setLtRefPicPocLsbSps(k, uiCode)
                uiCode = self.xReadFlag(uiCode, 'used_by_curr_pic_lt_sps_flag[i]')
                pcSPS.setUsedByCurrPicLtSPSFlag(k, 1 if uiCode else 0)
        uiCode = self.xReadFlag(uiCode, 'sps_temporal_mvp_enable_flag')
        pcSPS.setTMVPFlagsPresent(uiCode)

        uiCode = self.xReadFlag(uiCode, 'sps_strong_intra_smoothing_enable_flag')
        pcSPS.setUseStrongIntraSmoothing(uiCode)

        uiCode = self.xReadFlag(uiCode, 'vui_parameters_present_flag')
        pcSPS.setVuiParametersPresentFlag(uiCode)

        if pcSPS.getVuiParametersPresentFlag():
            self.parseVUI(pcSPS.getVuiParameters(), pcSPS)

        uiCode = self.xReadFlag(uiCode, 'sps_extension_flag')
        if uiCode:
            while self.xMoreRbspData():
                uiCode = self.xReadFlag(uiCode, 'sps_extension_data_flag')

    @Trace.trace(Trace.on, before=lambda self, pcPPS: xTracePPSHeader(pcPPS))
    def parsePPS(self, pcPPS):
        uiCode = 0
        iCode = 0

        uiCode = self.xReadUvlc(uiCode, 'pic_parameter_set_id')
        pcPPS.setPPSId(uiCode)
        uiCode = self.xReadUvlc(uiCode, 'seq_parameter_set_id')
        pcPPS.setSPSId(uiCode)

        uiCode = self.xReadFlag(uiCode, 'dependent_slice_segments_enabled_flag')
        pcPPS.setDependentSliceSegmentsEnabledFlag(uiCode == 1)
        uiCode = self.xReadFlag(uiCode, 'sign_data_hiding_flag')
        pcPPS.setSignHideFlag(uiCode)

        uiCode = self.xReadFlag(uiCode, 'cabac_init_present_flag')
        pcPPS.setCabacInitPresentFlag(True if uiCode else False)

        uiCode = self.xReadUvlc(uiCode, 'num_ref_idx_l0_default_active_minus1')
        pcPPS.setNumRefIdxL0DefaultActive(uiCode+1)
        uiCode = self.xReadUvlc(uiCode, 'num_ref_idx_l1_default_active_minus1')
        pcPPS.setNumRefIdxL1DefaultActive(uiCode+1)

        iCode = self.xReadSvlc(iCode, 'init_qp_minus26')
        pcPPS.setPicInitQPMinus26(iCode)
        uiCode = self.xReadFlag(uiCode, 'constrained_intra_pred_flag')
        pcPPS.setConstrainedIntraPred(True if uiCode else False)
        uiCode = self.xReadFlag(uiCode, 'transform_skip_enabled_flag')
        pcPPS.setUseTransformSkip(True if uiCode else False)

        uiCode = self.xReadFlag(uiCode, 'cu_qp_delta_enabled_flag')
        pcPPS.setUseDQP(True if uiCode else False)
        if pcPPS.getUseDQP():
            uiCode = self.xReadUvlc(uiCode, 'diff_cu_qp_delta_depth')
            pcPPS.setMaxCuDQPDepth(uiCode)
        else:
            pcPPS.setMaxCuDQPDepth(0)
        iCode = self.xReadSvlc(iCode, 'pps_cb_qp_offset')
        pcPPS.setChromaCbQpOffset(iCode)
        assert(pcPPS.getChromaCbQpOffset() >= -12)
        assert(pcPPS.getChromaCbQpOffset() <= 12)

        iCode = self.xReadSvlc(iCode, 'pps_cr_qp_offset')
        pcPPS.setChromaCrQpOffset(iCode)
        assert(pcPPS.getChromaCrQpOffset() >= -12)
        assert(pcPPS.getChromaCrQpOffset() <= 12)

        uiCode = self.xReadFlag(uiCode, 'pps_slice_chroma_qp_offsets_present_flag')
        pcPPS.setSliceChromaQpFlag(True if uiCode else False)

        uiCode = self.xReadFlag(uiCode, 'weighted_pred_flag') # Use of Weighting Prediction (P_SLICE)
        pcPPS.setUseWP(uiCode == 1)
        uiCode = self.xReadFlag(uiCode, 'weighted_bipred_flag') # Use of Bi-Directional Weighting Prediction (B_SLICE)
        pcPPS.setWPBiPred(uiCode == 1)
        sys.stdout.write("TDecCavlc::parsePPS():\tm_bUseWeightPred=%d\tm_uiBiPredIdc=%d\n" %
            (pcPPS.getUseWP(), pcPPS.getWPBiPred()))

        uiCode = self.xReadFlag(uiCode, 'output_flag_present_flag')
        pcPPS.setOutputFlagPresentFlag(uiCode == 1)

        uiCode = self.xReadFlag(uiCode, 'transquant_bypass_enable_flag')
        pcPPS.setTransquantBypassEnableFlag(True if uiCode else False)
        uiCode = self.xReadFlag(uiCode, 'tiles_enabled_flag')
        pcPPS.setTilesEnabledFlag(uiCode == 1)
        uiCode = self.xReadFlag(uiCode, 'entropy_coding_sync_enabled_flag')
        pcPPS.setEntropyCodingSyncEnabledFlag(uiCode == 1)

        if pcPPS.getTilesEnabledFlag():
            uiCode = self.xReadUvlc(uiCode, 'num_tile_columns_minus1')
            pcPPS.setNumColumnsMinus1(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'num_tile_rows_minus1')
            pcPPS.setNumRowsMinus1(uiCode)
            uiCode = self.xReadFlag(uiCode, 'uniform_spacing_flag')
            pcPPS.setUniformSpacingFlag(uiCode)

            if not pcPPS.getUniformSpacingFlag():
                columnWidth = ArrayUInt(pcPPS.getNumColumnsMinus1())
                for i in xrange(pcPPS.getNumColumnsMinus1()):
                    uiCode = self.xReadUvlc(uiCode, 'column_width_minus1')
                    columnWidth[i] = uiCode+1
                pcPPS.setColumnWidth(columnWidth.cast())
                del columnWidth

                rowHeight = ArrayUInt(pcPPS.getNumRowsMinus1())
                for i in xrange(pcPPS.getNumRowsMinus1()):
                    uiCode = self.xReadUvlc(uiCode, 'row_height_minus1')
                    rowHeight[i] = uiCode+1
                pcPPS.setRowHeight(rowHeight.cast())
                del rowHeight

            if pcPPS.getNumColumnsMinus1() != 0 or pcPPS.getNumRowsMinus1() != 0:
                uiCode = self.xReadFlag(uiCode, 'loop_filter_across_tiles_enabled_flag')
                pcPPS.setLoopFilterAcrossTilesEnabledFlag(True if uiCode else False)
        uiCode = self.xReadFlag(uiCode, 'loop_filter_across_slices_enabled_flag')
        pcPPS.setLoopFilterAcrossSlicesEnabledFlag(True if uiCode else False)
        uiCode = self.xReadFlag(uiCode, 'deblocking_filter_control_present_flag')
        pcPPS.setDeblockingFilterControlPresentFlag(True if uiCode else False)
        if pcPPS.getDeblockingFilterControlPresentFlag():
            uiCode = self.xReadFlag(uiCode, 'deblocking_filter_override_enabled_flag')
            pcPPS.setDeblockingFilterOverrideEnabledFlag(True if uiCode else False)
            uiCode = self.xReadFlag(uiCode, 'pps_disable_deblocking_filter_flag')
            pcPPS.setPicDisableDeblockingFilterFlag(True if uiCode else False)
            if not pcPPS.getPicDisableDeblockingFilterFlag():
                iCode = self.xReadSvlc(iCode, 'pps_beta_offset_div2')
                pcPPS.setDeblockingFilterBetaOffsetDiv2(iCode)
                iCode = self.xReadSvlc(iCode, 'pps_tc_offset_div2')
                pcPPS.setDeblockingFilterTcOffsetDiv2(iCode)
        uiCode = self.xReadFlag(uiCode, 'pps_scaling_list_data_present_flag')
        pcPPS.setScalingListPresentFlag(True if uiCode else False)
        if pcPPS.getScalingListPresentFlag():
            self.parseScalingList(pcPPS.getScalingList())

        uiCode = self.xReadFlag(uiCode, 'lists_modification_present_flag')
        pcPPS.setListsModificationPresentFlag(uiCode)

        uiCode = self.xReadUvlc(uiCode, 'log2_parallel_merge_level_minus2')
        pcPPS.setLog2ParallelMergeLevelMinus2(uiCode)

        uiCode = self.xReadCode(3, uiCode, 'num_extra_slice_header_bits')
        pcPPS.setNumExtraSliceHeaderBits(uiCode)

        uiCode = self.xReadFlag(uiCode, 'slice_segment_header_extension_present_flag')
        pcPPS.setSliceHeaderExtensionPresentFlag(uiCode)

        uiCode = self.xReadFlag(uiCode, 'pps_extension_flag')
        if uiCode:
            while self.xMoreRbspData():
                uiCode = self.xReadFlag(uiCode, 'pps_extension_data_flag')

    @Trace.trace(Trace.on, before=lambda self, pcVUI, pcSPS: xTraceVUIHeader(pcVUI, pcSPS))
    def parseVUI(self, pcVUI, pcSPS):
        uiCode = 0

        uiCode = self.xReadFlag(uiCode, 'aspect_ratio_info_present_flag')
        pcVUI.setAspectRatioInfoPresentFlag(uiCode)
        if pcVUI.getAspectRatioInfoPresentFlag():
            uiCode = self.xReadCode(8, uiCode, 'aspect_ratio_idc')
            pcVUI.setAspectRatioIdc(uiCode)
            if pcVUI.getAspectRatioIdc() == 255:
                uiCode = self.xReadCode(16, uiCode, 'sar_width')
                pcVUI.setSarWidth(uiCode)
                uiCode = self.xReadCode(16, uiCode, 'sar_height')
                pcVUI.setSarHeight(uiCode)

        uiCode = self.xReadFlag(uiCode, 'overscan_info_present_flag')
        pcVUI.setOverscanInfoPresentFlag(uiCode)
        if pcVUI.getOverscanInfoPresentFlag():
            uiCode = self.xReadFlag(uiCode, 'overscan_approriate_flag')
            pcVUI.setOverscanApproriateFlag(uiCode)

        uiCode = self.xReadFlag(uiCode, 'video_signal_type_present_flag')
        pcVUI.setVideoSignalTypePresentFlag(uiCode)
        if pcVUI.getVideoSignalTypePresentFlag():
            uiCode = self.xReadCode(3, uiCode, 'video_format')
            pcVUI.setVideoFormat(uiCode)
            uiCode = self.xReadFlag(uiCode, 'video_full_range_flag')
            pcVUI.setVideoFullRangeFlag(uiCode)
            uiCode = self.xReadFlag(uiCode, 'colour_description_present_flag')
            pcVUI.setColourDescriptionPresentFlag(uiCode)
            if pcVUI.getColourDescriptionPresentFlag():
                uiCode = self.xReadCode(8, uiCode, 'colour_primaries')
                pcVUI.setColourPrimaries(uiCode)
                uiCode = self.xReadCode(8, uiCode, 'transfer_characteristics')
                pcVUI.setTransferCharacteristics(uiCode)
                uiCode = self.xReadCode(8, uiCode, 'matrix_coefficients')
                pcVUI.setMatrixCoefficients(uiCode)

        uiCode = self.xReadFlag(uiCode, 'chroma_loc_info_present_flag')
        pcVUI.setChromaLocInfoPresentFlag(uiCode)
        if pcVUI.getChromaLocInfoPresentFlag():
            uiCode = self.xReadUvlc(uiCode, 'chroma_sample_loc_type_top_field')
            pcVUI.setChromaSampleLocTypeTopField(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'chroma_sample_loc_type_bottom_field')
            pcVUI.setChromaSampleLocTypeBottomField(uiCode)

        uiCode = self.xReadFlag(uiCode, 'neutral_chroma_indication_flag')
        pcVUI.setNeutralChromaIndicationFlag(uiCode)

        uiCode = self.xReadFlag(uiCode, 'field_seq_flag')
        pcVUI.setFieldSeqFlag(uiCode)
        assert(pcVUI.getFieldSeqFlag() == False) # not support yet

        uiCode = self.xReadFlag(uiCode, 'frame_field_info_present_flag')
        pcVUI.setFrameFieldInfoPresentFlag(uiCode)

        uiCode = self.xReadFlag(uiCode, 'default_display_window_flag')
        if uiCode != 0:
            defDisp = pcVUI.getDefaultDisplayWindow()
            uiCode = self.xReadUvlc(uiCode, 'def_disp_win_left_offset')
            defDisp.setWindowLeftOffset(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'def_disp_win_right_offset')
            defDisp.setWindowRightOffset(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'def_disp_win_top_offset')
            defDisp.setWindowTopOffset(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'def_disp_win_bottom_offset')
            defDisp.setWindowBottomOffset(uiCode)

        uiCode = self.xReadFlag(uiCode, 'hrd_parameters_present_flag')
        pcVUI.setHrdParametersPresentFlag(uiCode)
        if pcVUI.getHrdParametersPresentFlag():
            self.parseHrdParameters(pcVUI.getHrdParameters(), 1, pcSPS.getMaxTLayers()-1)
        uiCode = self.xReadFlag(uiCode, 'poc_proportional_to_timing_flag')
        pcVUI.setPocProportionalToTimingFlag(True if uiCode else False)
        if pcVUI.getPocProportionalToTimingFlag() and pcVUI.getHrdParameters().getTimingInfoPresentFlag():
            uiCode = self.xReadUvlc(uiCode, 'num_ticks_poc_diff_one_minus1')
            pcVUI.setNumTicksPocDiffOneMinus1(uiCode)
        uiCode = self.xReadFlag(uiCode, 'bitstream_restriction_flag')
        pcVUI.setBitstreamRestrictionFlag(uiCode)
        if pcVUI.getBitstreamRestrictionFlag():
            uiCode = self.xReadFlag(uiCode, 'tiles_fixed_structure_flag')
            pcVUI.setTilesFixedStructureFlag(uiCode)
            uiCode = self.xReadFlag(uiCode, 'motion_vectors_over_pic_boundaries_flag')
            pcVUI.setMotionVectorsOverPicBoundariesFlag(uiCode)
            uiCode = self.xReadFlag(uiCode, 'restricted_ref_pic_lists_flag')
            pcVUI.setRestrictedRefPicListsFlag(uiCode)
            uiCode = self.xReadCode(8, uiCode, 'min_spatial_segmentation_idc')
            pcVUI.setMinSpatialSegmentationIdc(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'max_bytes_per_pic_denom')
            pcVUI.setMaxBytesPerPicDenom(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'max_bits_per_mincu_denom')
            pcVUI.setMaxBitsPerMinCuDenom(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'log2_max_mv_length_horizontal')
            pcVUI.setLog2MaxMvLengthHorizontal(uiCode)
            uiCode = self.xReadUvlc(uiCode, 'log2_max_mv_length_vertical')
            pcVUI.setLog2MaxMvLengthVertical(uiCode)

    def parseSEI(self, seis):
        pass

    def parsePTL(self, rpcPTL, profilePresentFlag, maxNumSubLayersMinus1):
        uiCode = 0
        if profilePresentFlag:
            self.parseProfileTier(rpcPTL.getGeneralPTL())
        uiCode = self.xReadCode(8, uiCode, 'general_level_idc')
        rpcPTL.getGeneralPTL().setLevelIdc(uiCode)

        for i in xrange(maxNumSubLayersMinus1):
            if profilePresentFlag:
                uiCode = self.xReadFlag(uiCode, 'sub_layer_profile_present_flag[i]')
                rpcPTL.setSubLayerProfilePresentFlag(i, uiCode)
            uiCode = self.xReadFlag(uiCode, 'sub_layer_level_present_flag[i]')
            rpcPTL.setSubLayerLevelPresentFlag(i, uiCode)
            if profilePresentFlag and rpcPTL.getSubLayerProfilePresentFlag(i):
                self.parseProfileTier(rpcPTL.getSubLayerPTL(i))
            if rpcPTL.getSubLayerLevelPresentFlag(i):
                uiCode = self.xReadCode(8, uiCode, 'sub_layer_level_idc[i]')
                rpcPTL.getSubLayerPTL(i).setLevelIdc(uiCode)

    def parseProfileTier(self, ptl):
        uiCode = 0
        uiCode = self.xReadCode(2, uiCode, 'XXX_profile_space[]')
        ptl.setProfileSpace(uiCode)
        uiCode = self.xReadFlag(uiCode, 'XXX_tier_flag[]')
        ptl.setTierFlag(1 if uiCode else 0)
        uiCode = self.xReadCode(5, uiCode, 'XXX_profile_idc[]')
        ptl.setProfileIdc(uiCode)
        for j in xrange(32):
            uiCode = self.xReadFlag(uiCode, 'XXX_profile_compatibility_flag[][j]')
            ptl.setProfileCompatibilityFlag(j, 1 if uiCode else 0)
        uiCode = self.xReadCode(16, uiCode, 'XXX_reserved_zero_16bits[]')
        assert(uiCode == 0)

    def parseBitratePicRateInfo(self, info, tempLevelLow, tempLevelHigh):
        uiCode = 0
        for i in xrange(tempLevelLow, tempLevelHigh+1):
            uiCode = self.xReadFlag(uiCode, 'bit_rate_info_present_flag[i]')
            info.setBitRateInfoPresentFlag(i, True if uiCode else False)
            uiCode = self.xReadFlag(uiCode, 'pic_rate_info_present_flag[i]')
            info.setPicRateInfoPresentFlag(i, True if uiCode else False)
            if info.getBitRateInfoPresentFlag(i):
                uiCode = self.xReadCode(16, uiCode, 'avg_bit_rate[i]')
                info.setAvgBitRate(i, uiCode)
                uiCode = self.xReadCode(16, uiCode, 'max_bit_rate[i]')
                info.setMaxBitRate(i, uiCode)
            if info.getPicRateInfoPresentFlag(i):
                uiCode = self.xReadCode(2, uiCode, 'constant_pic_rate_idc[i]')
                info.setConstantPicRateIdc(i, uiCode)
                uiCode = self.xReadCode(16, uiCode, 'avg_pic_rate[i]')
                info.setAvgPicRate(i, uiCode)

    def parseHrdParameters(self, hrd, commonInfPresentFlag, maxNumSubLayersMinus1):
        uiCode = 0
        if commonInfPresentFlag:
            uiCode = self.xReadFlag(uiCode, 'timing_info_present_flag')
            hrd.setTimingInfoPresentFlag(True if uiCode == 1 else False)
            if hrd.getTimingInfoPresentFlag():
                uiCode = self.xReadCode(32, uiCode, 'num_units_in_tick')
                hrd.setNumUnitsInTick(uiCode)
                uiCode = self.xReadCode(32, uiCode, 'time_scale')
                hrd.setTimeScale(uiCode)
            uiCode = self.xReadFlag(uiCode, 'nal_hrd_parameters_present_flag')
            hrd.setNalHrdParametersPresentFlag(True if uiCode == 1 else False)
            uiCode = self.xReadFlag(uiCode, 'vcl_hrd_parameters_present_flag')
            hrd.setVclHrdParametersPresentFlag(True if uiCode == 1 else False)
            if hrd.getNalHrdParametersPresentFlag() or hrd.getVclHrdParametersPresentFlag():
                uiCode = self.xReadFlag(uiCode, 'sub_pic_cpb_params_present_flag')
                hrd.setSubPicCpbParamsPresentFlag(True if uiCode == 1 else False)
                if hrd.getSubPicCpbParamsPresentFlag():
                    uiCode = self.xReadCode(8, uiCode, 'tick_divisor_minus2')
                    hrd.setTickDivisorMinus2(uiCode)
                    uiCode = self.xReadCode(5, uiCode, 'du_cpb_removal_delay_length_minus1')
                    hrd.setDuCpbRemovalDelayLengthMinus1(uiCode)
                    uiCode = self.xReadFlag(uiCode, 'sub_pic_cpb_params_in_pic_timing_sei_flag')
                    hrd.setSubPicCpbParamsInPicTimingSEIFlag(True if uiCode == 1 else False)
                uiCode = self.xReadCode(4, uiCode, 'bit_rate_scale')
                hrd.setBitRateScale(uiCode)
                uiCode = self.xReadCode(4, uiCode, 'cpb_size_scale')
                hrd.setCpbSizeScale(uiCode)
                if hrd.getSubPicCpbParamsPresentFlag():
                    uiCode = self.xReadCode(4, uiCode, 'cpb_size_du_scale')
                    hrd.setDuCpbSizeScale(uiCode)
                uiCode = self.xReadCode(5, uiCode, 'initial_cpb_removal_delay_length_minus1')
                hrd.setInitialCpbRemovalDelayLengthMinus1(uiCode)
                uiCode = self.xReadCode(5, uiCode, 'au_cpb_removal_delay_length_minus1')
                hrd.setCpbRemovalDelayLengthMinus1(uiCode)
                uiCode = self.xReadCode(5, uiCode, 'dpb_output_delay_length_minus1')
                hrd.setDpbOutputDelayLengthMinus1(uiCode)

            for i in xrange(maxNumSubLayersMinus1):
                uiCode = self.xReadFlag(uiCode, 'fixed_pic_rate_general_flag')
                hrd.setFixedPicRateFlag(i, True if uiCode == 1 else False)
                if not hrd.getFixedPicRateFlag(i):
                    uiCode = self.xReadFlag(uiCode, 'fixed_pic_rate_within_cvs_flag')
                    hrd.setFixedPicRateWithinCvsFlag(i, True if uiCode == 1 else False)
                else:
                    hrd.setFixedPicRateWithinCvsFlag(i, True)
                if hrd.getFixedPicRateWithinCvsFlag(i):
                    uiCode = self.xReadUvlc(uiCode, 'elemental_duration_in_tc_minus1')
                    hrd.setPicDurationInTcMinus1(i, uiCode)
                uiCode = self.xReadFlag(uiCode, 'low_delay_hrd_flag')
                hrd.setLowDelayHrdFlag(i, True if uiCode == 1 else False)
                uiCode = self.xReadUvlc(uiCode, 'cpb_cnt_minus1')
                hrd.setCpbCntMinus1(i, uiCode)
                for nalOrVcl in xrange(2):
                    if (nalOrVcl == 0 and hrd.getNalHrdParametersPresentFlag()) or \
                       (nalOrVcl == 1 and hrd.getVclHrdParametersPresentFlag()):
                        for j in xrange(hrd.getCpbCntMinus1(i) + 1):
                            uiCode = self.xReadUvlc(uiCode, 'bit_size_value_minus1')
                            hrd.setBitRateValueMinus1(i, j, nalOrVcl, uiCode)
                            uiCode = self.xReadUvlc(uiCode, 'cpb_size_value_minus1')
                            hrd.setCpbSizeValueMinus1(i, j, nalOrVcl, uiCode)
                            if hrd.getSubPicCpbParamsPresentFlag():
                                uiCode = self.xReadUvlc(uiCode, 'cpb_size_du_value_minus1')
                                hrd.setDuCpbSizeValueMinus1(i, j, nalOrVcl, uiCode)
                            uiCode = self.xReadFlag(uiCode, 'cbr_flag')
                            hrd.setCbrFlag(i, j, nalOrVcl, True if uiCode == 1 else False)

    @Trace.trace(Trace.on, before=lambda self, pSlice, psm: xTraceSliceHeader(pSlice))
    def parseSliceHeader(self, rpcSlice, parameterSetManager):
        uiCode = 0
        iCode = 0

        firstSliceSegmentInPic = 0
        firstSliceSegmentInPic = self.xReadFlag(firstSliceSegmentInPic, 'first_slice_segment_in_pic_flag')
        if rpcSlice.getRapPicFlag():
            uiCode = self.xReadFlag(uiCode, 'no_output_of_prior_pics_flag') #ignored
        uiCode = self.xReadUvlc(uiCode, 'slice_pic_parameter_set_id')
        rpcSlice.setPPSId(uiCode)
        pps = parameterSetManager.getPrefetchedPPS(uiCode)
        #!KS: need to add error handling code here, if PPS is not available
        assert(pps != None)
        sps = parameterSetManager.getPrefetchedSPS(pps.getSPSId())
        #!KS: need to add error handling code here, if SPS is not available
        assert(sps != None)
        rpcSlice.setSPS(sps)
        rpcSlice.setPPS(pps)
        if pps.getDependentSliceSegmentsEnabledFlag() and not firstSliceSegmentInPic:
            uiCode = self.xReadFlag(uiCode, 'dependent_slice_segment_flag')
            rpcSlice.setDependentSliceSegmentFlag(True if uiCode else False)
        else:
            rpcSlice.setDependentSliceSegmentFlag(False)
        numCTUs = ((sps.getPicWidthInLumaSamples() + sps.getMaxCUWidth() - 1) // sps.getMaxCUWidth()) * \
                  ((sps.getPicHeightInLumaSamples() + sps.getMaxCUHeight() - 1) // sps.getMaxCUHeight())
        maxParts = 1 << (sps.getMaxCUDepth()<<1)
        sliceSegmentAddress = 0
        bitsSliceSegmentAddress = 0
        while numCTUs > (1<<bitsSliceSegmentAddress):
            bitsSliceSegmentAddress += 1

        if not firstSliceSegmentInPic:
            bitsSliceSegmentAddress = 0
            bitsSliceSegmentAddress = self.xReadCode(bitsSliceSegmentAddress, sliceSegmentAddress, 'slice_segment_address')
        #set uiCode to equal slice start address (or dependent slice start address)
        sliceCuAddress = maxParts * sliceSegmentAddress
        rpcSlice.setSliceSegmentCurStartCUAddr(sliceCuAddress)
        rpcSlice.setSliceSegmentCurEndCUAddr(numCTUs * maxParts)

        if rpcSlice.getDependentSliceSegmentFlag():
            rpcSlice.setNextSlice(False)
            rpcSlice.setNextSliceSegment(True)
        else:
            rpcSlice.setNextSlice(True)
            rpcSlice.setNextSliceSegment(False)

            rpcSlice.setSliceCurStartCUAddr(sliceCuAddress)
            rpcSlice.setSliceCurEndCUAddr(numCTUs * maxParts)

        if not rpcSlice.getDependentSliceSegmentFlag():
            for i in xrange(rpcSlice.getPPS().getNumExtraSliceHeaderBits()):
                uiCode = self.xReadFlag(uiCode, 'slice_reserved_undetermined_flag[]') # ignore

            uiCode = self.xReadUvlc(uiCode, 'slice_type')
            rpcSlice.setSliceType(uiCode)
            if pps.getOutputFlagPresentFlag():
                uiCode = self.xReadFlag(uiCode, 'pic_output_flag')
                rpcSlice.setPicOutputFlag(True if uiCode else False)
            else:
                rpcSlice.setPicOutputFlag(True)
            # in the first version chroma_format_idc is equal to one, thus colour_plane_id will not be present
            assert(sps.getChromaFormatIdc() == 1)

            if rpcSlice.getIdrPicFlag():
                rpcSlice.setPOC(0)
                rps = rpcSlice.getLocalRPS()
                rps.setNumberOfNegativePictures(0)
                rps.setNumberOfPositivePictures(0)
                rps.setNumberOfLongtermPictures(0)
                rps.setNumberOfPictures(0)
                rpcSlice.setRPS(rps)
            else:
                uiCode = self.xReadCode(sps.getBitsForPOC(), uiCode, 'pic_order_cnt_lsb')
                iPOClsb = uiCode
                iPrevPOC = rpcSlice.getPrevPOC()
                iMaxPOClsb = 1 << sps.getBitsForPOC()
                iPrevPOClsb = iPrevPOC % iMaxPOClsb
                iPrevPOCmsb = iPrevPOC - iPrevPOClsb
                iPOCmsb = 0
                if iPOClsb < iPrevPOClsb and iPrevPOClsb - iPOClsb >= iMaxPOClsb / 2:
                    iPOCmsb = iPrevPOCmsb + iMaxPOClsb
                elif iPOClsb > iPrevPOClsb and iPOClsb - iPrevPOClsb > iMaxPOClsb / 2:
                    iPOCmsb = iPrevPOCmsb - iMaxPOClsb
                else:
                    iPOCmsb = iPrevPOCmsb
                if rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA or \
                   rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT or \
                   rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA_N_LP:
                    # For BLA picture types, POCmsb is set to 0.
                    iPOCmsb = 0
                rpcSlice.setPOC(iPOCmsb + iPOClsb)

                rps = None
                uiCode = self.xReadFlag(uiCode, 'short_term_ref_pic_set_sps_flag')
                if uiCode == 0: # use short-term reference picture set explicitly signalled in slice header
                    rps = rpcSlice.getLocalRPS()
                    self.parseShortTermRefPicSet(
                        sps, rps, sps.getRPSList().getNumberOfReferencePictureSets())
                    rpcSlice.setRPS(rps)
                else: # use reference to short-term reference picture set in PPS
                    numBits = 0
                    while (1 << numBits) < rpcSlice.getSPS().getRPSList().getNumberOfReferencePictureSets():
                        numBits += 1
                    if numBits > 0:
                        uiCode = self.xReadCode(numBits, uiCode, 'short_term_ref_pic_set_idx')
                    else:
                        uiCode = 0
                    rpcSlice.setRPS(sps.getRPSList().getReferencePictureSet(uiCode))

                    rps = rpcSlice.getRPS()
                if sps.getLongTermRefsPresent():
                    offset = rps.getNumberOfNegativePictures() + rps.getNumberOfPositivePictures()
                    numOfLtrp = 0
                    numLtrpInSPS = 0
                    if rpcSlice.getSPS().getNumLongTermRefPicSPS() > 0:
                        uiCode = self.xReadUvlc(uiCode, 'num_long_term_sps')
                        numLtrpInSPS = uiCode
                        numOfLtrp += numLtrpInSPS
                        rps.setNumberOfLongtermPictures(numOfLtrp)
                    bitsForLtrpInSPS = 1
                    while rpcSlice.getSPS().getNumLongTermRefPicSPS() > (1<<bitsForLtrpInSPS):
                        bitsForLtrpInSPS += 1
                    uiCode = self.xReadUvlc(uiCode, 'num_long_term_pics')
                    rps.setNumberOfLongtermPictures(uiCode)
                    numOfLtrp += uiCode
                    rps.setNumberOfLongtermPictures(numOfLtrp)
                    maxPicOrderCntLSB = 1 << rpcSlice.getSPS().getBitsForPOC()
                    prevLSB = prevDeltaMSB = deltaPocMSBCycleLT = 0
                    j = offset + rps.getNumberOfLongtermPictures() - 1
                    for k in xrange(numOfLtrp):
                        pocLsbLt = 0
                        if k < numLtrpInSPS:
                            uiCode = 0
                            if bitsForLtrpInSPS > 0:
                                uiCode = self.xReadCode(bitsForLtrpInSPS, uiCode, 'lt_idx_sps[i]')
                            usedByCurrFromSPS = rpcSlice.getSPS().getUsedByCurrPicLtSPSFlag(uiCode)

                            pocLsbLt = rpcSlice.getSPS().getLtRefPicPocLsbSps(uiCode)
                            rps.setUsed(j, usedByCurrFromSPS)
                        else:
                            uiCode = self.xReadCode(rpcSlice.getSPS().getBitsForPOC(), uiCode, 'poc_lsb_lt')
                            pocLsbLt = uiCode
                            uiCode = self.xReadFlag(uiCode, 'used_by_curr_pic_lt_flag')
                            rps.setUsed(j, uiCode)
                        uiCode = self.xReadFlag(uiCode, 'delta_poc_msb_present_flag')
                        mSBPresentFlag = True if uiCode else False
                        if mSBPresentFlag:
                            uiCode = self.xReadUvlc(uiCode, 'delta_poc_msb_cycle_lt[i]')
                            deltaFlag = False
                            if j == offset + rps.getNumberOfLongtermPictures() - 1 or \
                               j == offset + (numOfLtrp - numLtrpInSPS) - 1 or \
                               pocLsbLt != prevLSB:
                                deltaFlag = True
                            if deltaFlag:
                                deltaPocMSBCycleLT = uiCode
                            else:
                                deltaPocMSBCycleLT = uiCode + prevDeltaMSB

                            pocLTCurr = rpcSlice.getPOC() - \
                                        deltaPocMSBCycleLT * maxPicOrderCntLSB - \
                                        iPOClsb + pocLsbLt
                            rps.setPOC(j, pocLTCurr)
                            rps.setDeltaPOC(j, - rpcSlice.getPOC() + pocLTCurr)
                            rps.setCheckLTMSBPresent(j, True)
                        else:
                            rps.setPOC(j, pocLsbLt)
                            rps.setDeltaPOC(j, - rpcSlice.getPOC() + pocLsbLt)
                            rps.setCheckLTMSBPresent(j, False)
                        prevLSB = pocLsbLt
                        prevDeltaMSB = deltaPocMSBCycleLT
                        j -= 1
                    offset += rps.getNumberOfLongtermPictures()
                    rps.setNumberOfPictures(offset)
                if rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA or \
                   rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT or \
                   rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA_N_LP:
                    # In the case of BLA picture types, rps data is read from slice header but ignored
                    rps = rpcSlice.getLocalRPS()
                    rps.setNumberOfNegativePictures(0)
                    rps.setNumberOfPositivePictures(0)
                    rps.setNumberOfLongtermPictures(0)
                    rps.setNumberOfPictures(0)
                    rpcSlice.setRPS(rps)
                if rpcSlice.getSPS().getTMVPFlagsPresent():
                    uiCode = self.xReadFlag(uiCode, 'slice_temporal_mvp_enable_flag')
                    rpcSlice.setEnableTMVPFlag(True if uiCode == 1 else False)
            if sps.getUseSAO():
                uiCode = self.xReadFlag(uiCode, 'slice_sao_luma_flag')
                rpcSlice.setSaoEnabledFlag(uiCode)
                uiCode = self.xReadFlag(uiCode, 'slice_sao_chroma_flag')
                rpcSlice.setSaoEnabledFlagChroma(uiCode)

            if rpcSlice.getIdrPicFlag():
                rpcSlice.setEnableTMVPFlag(False)
            if not rpcSlice.isIntra():
                uiCode = self.xReadFlag(uiCode, 'num_ref_idx_active_override_flag')
                if uiCode:
                    uiCode = self.xReadUvlc(uiCode, 'num_ref_idx_l0_active_minus1')
                    rpcSlice.setNumRefIdx(REF_PIC_LIST_0, uiCode+1)
                    if rpcSlice.isInterB():
                        uiCode = self.xReadUvlc(uiCode, 'num_ref_idx_l1_active_minus1')
                        rpcSlice.setNumRefIdx(REF_PIC_LIST_1, uiCode+1)
                    else:
                        rpcSlice.setNumRefIdx(REF_PIC_LIST_1, 0)
                else:
                    rpcSlice.setNumRefIdx(REF_PIC_LIST_0,
                        rpcSlice.getPPS().getNumRefIdxL0DefaultActive())
                    if rpcSlice.isInterB():
                        rpcSlice.setNumRefIdx(REF_PIC_LIST_1,
                            rpcSlice.getPPS().getNumRefIdxL1DefaultActive())
                    else:
                        rpcSlice.setNumRefIdx(REF_PIC_LIST_1, 0)

            refPicListModification = rpcSlice.getRefPicListModification()
            if not rpcSlice.isIntra():
                if not rpcSlice.getPPS().getListsModificationPresentFlag() or \
                   rpcSlice.getNumRpsCurrTempList() <= 1:
                    refPicListModification.setRefPicListModificationFlagL0(0)
                else:
                    uiCode = self.xReadFlag(uiCode, 'ref_pic_list_modification_flag_l0')
                    refPicListModification.setRefPicListModificationFlagL0(1 if uiCode else 0)

                if refPicListModification.getRefPicListModificationFlagL0():
                    uiCode = 0
                    i = 0
                    numRpsCurrTempList0 = rpcSlice.getNumRpsCurrTempList()
                    if numRpsCurrTempList0 > 1:
                        length = 1
                        numRpsCurrTempList0 -= 1
                        while numRpsCurrTempList0 >> 1:
                            numRpsCurrTempList0 >>= 1
                            length += 1
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_0)):
                            uiCode = self.xReadCode(length, uiCode, 'list_entry_l0')
                            refPicListModification.setRefPicSetIdxL0(i, uiCode)
                    else:
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_0)):
                            refPicListModification.setRefPicSetIdxL0(i, 0)
            else:
                refPicListModification.setRefPicListModificationFlagL0(0)
            if rpcSlice.isInterB():
                if not rpcSlice.getPPS().getListsModificationPresentFlag() or \
                   rpcSlice.getNumRpsCurrTempList() <= 1:
                    refPicListModification.setRefPicListModificationFlagL1(0)
                else:
                    uiCode = self.xReadFlag(uiCode, 'ref_pic_list_modification_flag_l1')
                    refPicListModification.setRefPicListModificationFlagL1(1 if uiCode else 0)
                if refPicListModification.getRefPicListModificationFlagL1():
                    uiCode = 0
                    i = 0
                    numRpsCurrTempList1 = rpcSlice.getNumRpsCurrTempList()
                    if numRpsCurrTempList1 > 1:
                        length = 1
                        numRpsCurrTempList1 -= 1
                        while numRpsCurrTempList1 >> 1:
                            numRpsCurrTempList1 >>= 1
                            length += 1
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_1)):
                            uiCode = self.xReadCode(length, uiCode, 'list_entry_l1')
                            refPicListModification.setRefPicSetIdxL1(i, uiCode)
                    else:
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_1)):
                            refPicListModification.setRefPicSetIdxL1(i, 0)
            else:
                refPicListModification.setRefPicListModificationFlagL1(0)
            if rpcSlice.isInterB():
                uiCode = self.xReadFlag(uiCode, 'mvd_l1_zero_flag')
                rpcSlice.setMvdL1ZeroFlag(True if uiCode else False)

            rpcSlice.setCabacInitFlag(False) # default
            if pps.getCabacInitPresentFlag() and not rpcSlice.isIntra():
                uiCode = self.xReadFlag(uiCode, 'cabac_init_flag')
                rpcSlice.setCabacInitFlag(True if uiCode else False)

            if rpcSlice.getEnableTMVPFlag():
                if rpcSlice.getSliceType() == B_SLICE:
                    uiCode = self.xReadFlag(uiCode, 'collocated_from_l0_flag')
                    rpcSlice.setColFromL0Flag(uiCode)
                else:
                    rpcSlice.setColFromL0Flag(1)

                if rpcSlice.getSliceType() != I_SLICE and \
                   (rpcSlice.getColFromL0Flag() == 1 and rpcSlice.getNumRefIdx(REF_PIC_LIST_0) > 1 or
                    rpcSlice.getColFromL0Flag() == 0 and rpcSlice.getNumRefIdx(REF_PIC_LIST_1) > 1):
                    uiCode = self.xReadUvlc(uiCode, 'collocated_ref_idx')
                    rpcSlice.setColRefIdx(uiCode)
                else:
                    rpcSlice.setColRefIdx(0)
            if pps.getUseWP() and rpcSlice.getSliceType() == P_SLICE or \
               pps.getWPBiPred() and rpcSlice.getSliceType() == B_SLICE:
                self.xParsePredWeightTable(rpcSlice)
                rpcSlice.initWpScaling()
            if not rpcSlice.isIntra():
                uiCode = self.xReadUvlc(uiCode, 'five_minus_max_num_merge_cand')
                rpcSlice.setMaxNumMergeCand(MRG_MAX_NUM_CANDS - uiCode)

            iCode = self.xReadSvlc(iCode, 'slice_qp_delta')
            rpcSlice.setSliceQp(26 + pps.getPicInitQPMinus26() + iCode)

            assert(rpcSlice.getSliceQp() >= -sps.getQpBDOffsetY())
            assert(rpcSlice.getSliceQp() <= 51)

            if rpcSlice.getPPS().getSliceChromaQpFlag():
                iCode = self.xReadSvlc(iCode, 'slice_qp_delta_cb')
                rpcSlice.setSliceQpDeltaCb(iCode)
                assert(rpcSlice.getSliceQpDeltaCb() >= -12)
                assert(rpcSlice.getSliceQpDeltaCb() <= 12)
                assert(rpcSlice.getPPS().getChromaCbQpOffset() + rpcSlice.getSliceQpDeltaCb() >= -12)
                assert(rpcSlice.getPPS().getChromaCbQpOffset() + rpcSlice.getSliceQpDeltaCb() <= 12)

                iCode = self.xReadSvlc(iCode, 'slice_qp_delta_cr')
                rpcSlice.setSliceQpDeltaCr(iCode)
                assert(rpcSlice.getSliceQpDeltaCr() >= -12)
                assert(rpcSlice.getSliceQpDeltaCr() <= 12)
                assert(rpcSlice.getPPS().getChromaCrQpOffset() + rpcSlice.getSliceQpDeltaCr() >= -12)
                assert(rpcSlice.getPPS().getChromaCrQpOffset() + rpcSlice.getSliceQpDeltaCr() <= 12)

            if rpcSlice.getPPS().getDeblockingFilterControlPresentFlag():
                if rpcSlice.getPPS().getDeblockingFilterOverrideEnabledFlag():
                    uiCode = self.xReadFlag(uiCode, 'deblocking_filter_override_flag')
                    rpcSlice.setDeblockingFilterOverrideFlag(True if uiCode else False)
                else:
                    rpcSlice.setDeblockingFilterOverrideFlag(0)
                if rpcSlice.getDeblockingFilterOverrideFlag():
                    uiCode = self.xReadFlag(uiCode, 'slice_disable_deblocking_filter_flag')
                    rpcSlice.setDeblockingFilterDisable(1 if uiCode else 0)
                    if not rpcSlice.getDeblockingFilterDisable():
                        iCode = self.xReadSvlc(iCode, 'beta_offset_div2')
                        rpcSlice.setDeblockingFilterBetaOffsetDiv2(iCode)
                        iCode = self.xReadSvlc(iCode, 'tc_offset_div2')
                        rpcSlice.setDeblockingFilterTcOffsetDiv2(iCode)
                else:
                    rpcSlice.setDeblockingFilterDisable(rpcSlice.getPPS().getPicDisableDeblockingFilterFlag())
                    rpcSlice.setDeblockingFilterBetaOffsetDiv2(rpcSlice.getPPS().getDeblockingFilterBetaOffsetDiv2())
                    rpcSlice.setDeblockingFilterTcOffsetDiv2(rpcSlice.getPPS().getDeblockingFilterTcOffsetDiv2())
            else:
                rpcSlice.setDeblockingFilterDisable(False)
                rpcSlice.setDeblockingFilterBetaOffsetDiv2(0)
                rpcSlice.setDeblockingFilterTcOffsetDiv2(0)

            isSAOEnabled = False if not rpcSlice.getSPS().getUseSAO() else \
                           (rpcSlice.getSaoEnabledFlag() or rpcSlice.getSaoEnabledFlagChroma())
            isDBFEnabled = not rpcSlice.getDeblockingFilterDisable()

            if rpcSlice.getPPS().getLoopFilterAcrossSlicesEnabledFlag() and \
               (isSAOEnabled or isDBFEnabled):
                uiCode = self.xReadFlag(uiCode, 'slice_loop_filter_across_slices_enabled_flag')
            else:
                uiCode = 1 if rpcSlice.getPPS().getLoopFilterAcrossSlicesEnabledFlag() else 0
            rpcSlice.setLFCrossSliceBoundaryFlag(True if uiCode == 1 else False)

        if pps.getTilesEnabledFlag() or pps.getEntropyCodingSyncEnabledFlag():
            entryPointOffset = None
            numEntryPointOffsets = offsetLenMinus1 = 0

            numEntryPointOffsets = self.xReadUvlc(numEntryPointOffsets, 'num_entry_point_offsets')
            rpcSlice.setNumEntryPointOffsets(numEntryPointOffsets)
            if numEntryPointOffsets > 0:
                offsetLenMinus1 = self.xReadUvlc(offsetLenMinus1, 'offset_len_minus1')
            entryPointOffset = numEntryPointOffsets * [0]
            for idx in xrange(numEntryPointOffsets):
                uiCode = self.xReadCode(offsetLenMinus1+1, uiCode, 'entry_point_offset')
                entryPointOffset[idx] = uiCode

            if pps.getTilesEnabledFlag():
                rpcSlice.setTileLocationCount(numEntryPointOffsets)

                prevPos = 0
                for idx in xrange(rpcSlice.getTileLocationCount()):
                    rpcSlice.setTileLocation(idx, prevPos + entryPointOffset[idx])
                    prevPos += entryPointOffset[idx]
            elif pps.getEntropyCodingSyncEnabledFlag():
                numSubstreams = rpcSlice.getNumEntryPointOffsets() + 1
                rpcSlice.allocSubstreamSizes(numSubstreams)
                pSubstreamSizes = pointer(rpcSlice.getSubstreamSizes(), type='uint *')
                for idx in xrange(numSubstreams-1):
                    if idx < numEntryPointOffsets:
                        pSubstreamSizes[idx] = entryPointOffset[idx] << 3
                    else:
                        pSubstreamSizes[idx] = 0

            if entryPointOffset:
                del entryPointOffset
        else:
            rpcSlice.setNumEntryPointOffsets(0)

        if pps.getSliceHeaderExtensionPresentFlag():
            uiCode = self.xReadUvlc(uiCode, 'slice_header_extension_length')
            if i in xrange(uiCode):
                ignore = 0
                ignore = self.xReadCode(8, ignore, 'slice_header_extension_data_byte')
        self.m_pcBitstream.readByteAlignment()

    def parseTerminatingBit(self, ruiBit):
        ruiBit = False
        iBitsLeft = self.m_pcBitstream.getNumBitsLeft()
        if iBitsLeft <= 8:
            uiPeekValue = self.m_pcBitstream.peekBits(iBitsLeft)
            if uiPeekValue == (1 << (iBitsLeft-1)):
                ruiBit = True
        return ruiBit

    def parseMVPIdx(self, riMVPIdx):
        assert(False)
    def parseSkipFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseCUTransquantBypassFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseMergeFlag(self, pcCU, uiAbsPartIdx, uiDepth, uiPUIdx):
        assert(False)
    def parseMergeIndex(self, pcCU, ruiMergeIndex):
        assert(False)
    def parseSplitFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parsePartSize(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parsePredMode(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)

    def parseIntraDirLumaAng(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseIntraDirChroma(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)

    def parseInterDir(self, pcCU, ruiInterDir, uiAbsPartIdx):
        assert(False)
    def parseRefFrmIdx(self, pcCU, riRefFrmIdx, eRefList):
        assert(False)
    def parseMvd(self, pcCU, uiAbsPartIdx, uiPartIdx, uiDepth, eRefList):
        assert(False)

    def parseDeltaQP(self, pcCU, uiAbsPartIdx, uiDepth):
        iDQp = 0
        iDQp = self.xReadSvlc(iDQp)

        qpBdOffsetY = pcCU.getSlice().getSPS().getQpBDOffsetY()
        qp = ((pcCU.getRefQP(uiAbsPartIdx) + iDQp + 52 + 2*qpBdOffsetY) % (52 + qpBdOffsetY)) - qpBdOffsetY

        uiAbsQpCUPartIdx = (uiAbsPartIdx >> ((cvar.g_uiMaxCUDepth - pcCU.getSlice().getPPS().getMaxCUDQPDepth()) << 1)) << \
                                            ((cvar.g_uiMaxCUDepth - pcCU.getSlice().getPPS().getMaxCUDQPDepth()) << 1)
        uiQpCUDepth = min(uiDepth, pcCU.getSlice().getPPS().getMaxCUDQPDepth())

        pcCU.setQPSubParts(qp, uiAbsQpCUPartIdx, uiQpCUDepth)

    def parseCoeffNxN(self, pcCU, pcCoef, uiAbsPartIdx, uiWidth, uiHeight, uiDepth, eTType):
        assert(False)
    def parseTransformSkipFlags(self, pcCU, uiAbsPartIdx, width, height, uiDepth, eTType):
        assert(False)
    def parseIPCMInfo(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)

    def updateContextTables(self, eSliceType, iQp):
        pass

    def xParsePredWeightTable(self, pcSlice):
        wp = None
        bChroma = True # color always present in HEVC ?
        eSliceType = pcSlice.getSliceType()
        iNbRef = 2 if eSliceType == B_SLICE else 1
        uiLog2WeightDenomLuma = uiLog2WeightDenomChroma = 0
        uiTotalSignalledWeightFlags = 0

        iDeltaDenom = 0
        # decode delta_luma_log2_weight_denom :
        uiLog2WeightDenomLuma = self.xReadUvlc(uiLog2WeightDenomLuma, 'luma_log2_weight_denom') # ue(v): luma_log2_weight_denom
        if bChroma:
            iDeltaDenom = self.xReadSvlc(iDeltaDenom, 'delta_chroma_log2_weight_denom') # se(v): delta_chroma_log2_weight_denom
            assert(iDeltaDenom + uiLog2WeightDenomLuma >= 0)
            uiLog2WeightDenomChroma = iDeltaDenom + uiLog2WeightDenomLuma

        for iNumRef in xrange(iNbRef):
            eRefPicList = REF_PIC_LIST_1 if iNumRef else REF_PIC_LIST_0
            for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList)):
                wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)

                wp[0].uiLog2WeightDenom = uiLog2WeightDenomLuma
                wp[1].uiLog2WeightDenom = uiLog2WeightDenomChroma
                wp[2].uiLog2WeightDenom = uiLog2WeightDenomChroma

                uiCode = 0
                uiCode = self.xReadFlag(uiCode, 'luma_weight_lX_flag') # u(1): luma_weight_l0_flag
                wp[0].bPresentFlag = (uiCode == 1)
                uiTotalSignalledWeightFlags += wp[0].bPresentFlag
            if bChroma:
                uiCode = 0
                for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList)):
                    wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)
                    uiCode = self.xReadFlag(uiCode, 'chroma_weight_lX_flag') # u(1): chroma_weight_l0_flag
                    wp[1].bPresentFlag = (uiCode == 1)
                    wp[2].bPresentFlag = (uiCode == 1)
                    uiTotalSignalledWeightFlags += 2 * wp[1].bPresentFlag
            for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList)):
                wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)
                if wp[0].bPresentFlag:
                    iDeltaWeight = 0
                    iDeltaWeight = self.xReadSvlc(iDeltaWeight, 'delta_luma_weight_lX') # se(v): delta_luma_weight_l0[i]
                    wp[0].iWeight = iDeltaWeight + (1<<wp[0].uiLog2WeightDenom)
                    wp[0].iOffset = self.xReadSvlc(wp[0].iOffset, 'luma_offset_lX') # se(v): luma_offset_l0[i]
                else:
                    wp[0].iWeight = 1 << wp[0].uiLog2WeightDenom
                    wp[0].iOffset = 0
                if bChroma:
                    if wp[1].bPresentFlag:
                        for j in xrange(1, 3):
                            iDeltaWeight = 0
                            iDeltaWeight = self.xReadSvlc(iDeltaWeight, 'delta_chroma_weight_lX') # se(v): chroma_weight_l0[i][j]
                            wp[j].iWeight = iDeltaWeight + (1<<wp[1].uiLog2WeightDenom)

                            iDeltaChroma = 0
                            iDeltaChroma = self.xReadSvlc(iDeltaChroma, 'delta_chroma_offset_lX') # se(v): delta_chroma_offset_l0[i][j]
                            pred = 128 - ((128*wp[j].iWeight) >> wp[j].uiLog2WeightDenom)
                            wp[j].iOffset = Clip3(-128, 127, iDeltaChroma+pred)
                    else:
                        for j in xrange(1, 3):
                            wp[j].iWeight = 1 << wp[j].uiLog2WeightDenom
                            wp[j].iOffset = 0

            for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList), MAX_NUM_REF):
                wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)

                wp[0].bPresentFlag = False
                wp[1].bPresentFlag = False
                wp[2].bPresentFlag = False
        assert(uiTotalSignalledWeightFlags <= 24)

    def parseScalingList(self, scalingList):
        code = sizeId = listId = 0
        scalingListPredModeFlag = False
        # for each size
        for sizeId in xrange(SCALING_LIST_SIZE_NUM):
            for listId in xrange(g_scalingListNum[sizeId]):
                code = self.xReadFlag(code, 'scaling_list_pred_mode_flag')
                scalingListPredModeFlag = True if code else False
                if not scalingListPredModeFlag: # Copy Mode
                    code = self.xReadUvlc(code, 'scaling_list_pred_matrix_id_delta')
                    scalingList.setRefMatrixId(sizeId, listId, listId-code)
                    if sizeId > SCALING_LIST_8x8:
                        scalingList.setScalingListDC(sizeId, listId,
                            16 if listId == scalingList.getRefMatrixId(sizeId, listId) else
                            scalingList.getScalingListDC(sizeId, scalingList.getRefMatrixId(sizeId, listId)))
                    scalingList.processRefMatrix(sizeId, listId, scalingList.getRefMatrixId(sizeId, listId))
                else: #DPCM Mode
                    self.xDecodeScalingList(scalingList, sizeId, listId)

    def xDecodeScalingList(self, scalingList, sizeId, listId):
        i = 0
        coefNum = min(MAX_MATRIX_COEF_NUM, g_scalingListSize[sizeId])
        data = 0
        scalingListDcCoefMinus8 = 0
        nextCoef = SCALING_LIST_START_VALUE
        scan = g_auiSigLastScan[SCAN_DIAG][1] if sizeId == 0 else g_sigLastScanCG32x32
        dst = scalingList.getScalingListAddress(sizeId, listId)

        if sizeId > SCALING_LIST_8x8:
            scalingListDcCoefMinus8 = self.xReadSvlc(scalingListDcCoefMinus8, 'scaling_list_dc_coef_minus8')
            scalingList.setScalingListDC(sizeId, listId, scalingListDcCoefMinus8+8)
            nextCoef = scalingList.getScalingListDC(sizeId, listId)

        for i in xrange(coefNum):
            data = self.xReadSvlc(data, 'scaling_list_delta_coef')
            nextCoef = (nextCoef + data + 256) % 256
            dst[scan[i]] = nextCoef

    def xMoreRbspData(self):
        bitsLeft = self.m_pcBitstream.getNumBitsLeft()

        # if there are more than 8 bits, it cannot be rbsp_trailing_bits
        if bitsLeft > 8:
            return True

        lastByte = self.m_pcBitstream.peekBits(bitsLeft)
        cnt = bitsLeft

        # remove trailing bits equal to zero
        while cnt > 0 and (lastByte & 1) == 0:
            lastByte >>= 1
            cnt -= 1
        # remove bit equal to one
        cnt -= 1

        # we should not have a negative number of bits
        assert(cnt >= 0)

        # we have more data, if cnt is not zero
        return cnt > 0
