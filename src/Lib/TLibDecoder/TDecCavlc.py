# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecCavlc.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import parseSEImessage
    from swig.hevc import ArrayUInt
    Char = lambda c: ord(c)
else:
    sys.path.insert(0, '../../..')
    from ..TLibCommon import TComRom as cvar
    from swig.hevc import parseSEImessage
    ArrayUInt = lambda size: [0 for i in xrange(size)] # TComPPS
    Char = lambda c: c

from .TDecEntropy import TDecEntropy

from ..TLibCommon.pointer import pointer

from ..TLibCommon.trace import (
    trace, initCavlc,
    traceSPSHeader, tracePPSHeader, traceSliceHeader,
    traceReadCode, traceReadUvlc, traceReadSvlc, traceReadFlag
)

use_trace = False

from ..TLibCommon.TypeDef import (
    MRG_MAX_NUM_CANDS_SIGNALED,
    SAO_BO_LEN, SAO_BO,
    B_SLICE, P_SLICE, I_SLICE,
    REF_PIC_LIST_0, REF_PIC_LIST_1,
    SCAN_DIAG
)

from ..TLibCommon.CommonDef import (
    MAX_NUM_REF, Clip3, MRG_MAX_NUM_CANDS,
    NAL_UNIT_CODED_SLICE_CRA,
    NAL_UNIT_CODED_SLICE_CRANT,
    NAL_UNIT_CODED_SLICE_BLA,
    NAL_UNIT_CODED_SLICE_BLANT,
    NAL_UNIT_CODED_SLICE_IDR
)

from ..TLibCommon.TComRom import (
    SCALING_LIST_START_VALUE, MAX_MATRIX_COEF_NUM,
    SCALING_LIST_8x8, SCALING_LIST_SIZE_NUM,
    g_auiSigLastScan,
    g_sigLastScanCG32x32,
    g_scalingListSize,
    g_scalingListNum
)


class TDecCavlc(TDecEntropy):

    def __init__(self):
        super(TDecCavlc, self).__init__()

        self.m_pcBitstream = None

    def resetEntropy(self, pcSlice):
        assert(False)
    def setBitstream(self, p):
        self.m_pcBitstream = p
    def updateContextTables(self, eSliceType, iQp):
        pass
    def decodeFlush(self):
        pass

    def parseVPS(self, pcVPS):
        uiCode = self._xReadCode(3, 'vps_max_temporal_layers_minus1')
        pcVPS.setMaxTLayers(uiCode+1)
        uiCode = self._xReadCode(5, 'vps_max_layers_minus1')
        pcVPS.setMaxLayers(uiCode+1)
        uiCode = self._xReadUvlc('video_parameter_set_id')
        pcVPS.setVPSId(uiCode)
        uiCode = self._xReadFlag('vps_temporal_id_nesting_flag')
        pcVPS.setTemporalNestingFlag(True if uiCode else False)

        for i in xrange(pcVPS.getMaxTLayers()):
            uiCode = self._xReadUvlc('vps_max_dec_pic_buffering[i]')
            pcVPS.setMaxDecPicBuffering(uiCode, i)
            uiCode = self._xReadUvlc('vps_num_reorder_pics[i]')
            pcVPS.setNumReorderPics(uiCode, i)
            uiCode = self._xReadUvlc('vps_max_latency_increase[i]')
            pcVPS.setMaxLatencyIncrease(uiCode, i)

        uiCode = self._xReadFlag('vps_extension_flag')
        assert(not uiCode)

    @trace(use_trace, init=initCavlc, before=lambda self, pcSPS: traceSPSHeader(pcSPS))
    def parseSPS(self, pcSPS):
        uiCode = self._xReadCode(3, 'profile_space')
        pcSPS.setProfileSpace(uiCode)
        uiCode = self._xReadCode(5, 'profile_idc')
        pcSPS.setProfileIdc(uiCode)
        uiCode = self._xReadCode(16, 'reserved_indicator_flags')
        pcSPS.setRsvdIndFlags(uiCode)
        uiCode = self._xReadCode(8, 'level_idc')
        pcSPS.setLevelIdc(uiCode)
        uiCode = self._xReadCode(32, 'profile_compatibility')
        pcSPS.setProfileCompat(uiCode)
        uiCode = self._xReadUvlc('seq_parameter_set_id')
        pcSPS.setSPSId(uiCode)
        uiCode = self._xReadUvlc('video_parameter_set_id')
        pcSPS.setVPSId(uiCode)
        uiCode = self._xReadUvlc('chroma_format_idc')
        pcSPS.setChromaFormatIdc(uiCode)
        uiCode = self._xReadCode(3, 'max_temporal_layers_minus1')
        pcSPS.setMaxTLayers(uiCode+1)
        uiCode = self._xReadUvlc('pic_width_in_luma_samples')
        pcSPS.setPicWidthInLumaSamples(uiCode)
        uiCode = self._xReadUvlc('pic_height_in_luma_samples')
        pcSPS.setPicHeightInLumaSamples(uiCode)
        uiCode = self._xReadFlag('pic_cropping_flag')
        pcSPS.setPicCroppingFlag(True if uiCode else False)
        if uiCode:
            uiCode = self._xReadUvlc('pic_crop_left_offset')
            pcSPS.setPicCropLeftOffset(uiCode * TComSPS.getCropUnitX(pcSPS.getChromaFormatIdc()))
            uiCode = self._xReadUvlc('pic_crop_right_offset')
            pcSPS.setPicCropRightOffset(uiCode * TComSPS.getCropUnitX(pcSPS.getChromaFormatIdc()))
            uiCode = self._xReadUvlc('pic_crop_top_offset')
            pcSPS.setPicCropTopOffset(uiCode * TComSPS.getCropUnitY(pcSPS.getChromaFormatIdc()))
            uiCode = self._xReadUvlc('pic_crop_bottom_offset')
            pcSPS.setPicCropBottomOffset(uiCode * TComSPS.getCropUnitY(pcSPS.getChromaFormatIdc()))

        uiCode = self._xReadUvlc('bit_depth_luma_minus8')
        cvar.g_uiBitDepth = 8
        cvar.g_uiBitIncrement = uiCode
        pcSPS.setBitDepth(cvar.g_uiBitDepth)
        pcSPS.setBitIncrement(cvar.g_uiBitIncrement)
        pcSPS.setQpBDOffsetY(6*uiCode)

        cvar.g_uiBASE_MAX = (1 << cvar.g_uiBitDepth) - 1
        cvar.g_uiIBDI_MAX = (1 << (cvar.g_uiBitDepth+cvar.g_uiBitIncrement)) - 1

        uiCode = self._xReadUvlc('bit_depth_chroma_minus8')
        pcSPS.setQpBDOffsetC(6*uiCode)

        uiCode = self._xReadFlag('pcm_enabled_flag')
        pcSPS.setUsePCM(True if uiCode else False)

        if pcSPS.getUsePCM():
            uiCode = self._xReadCode(4, 'pcm_bit_depth_luma_minus1')
            pcSPS.setPCMBitDepthLuma(1+uiCode)
            uiCode = self._xReadCode(4, 'pcm_bit_depth_chroma_minus1')
            pcSPS.setPCMBitDepthChroma(1+uiCode)

        uiCode = self._xReadUvlc('log2_max_pic_order_cnt_lsb_minus4')
        pcSPS.setBitsForPOC(4+uiCode)
        for i in xrange(pcSPS.getMaxTLayers()):
            uiCode = self._xReadUvlc('max_dec_pic_buffering')
            pcSPS.setMaxDecPicBuffering(uiCode, i)
            uiCode = self._xReadUvlc('num_reorder_pics')
            pcSPS.setNumReorderPics(uiCode, i)
            uiCode = self._xReadUvlc('max_latency_increase')
            pcSPS.setMaxLatencyIncrease(uiCode, i)

        uiCode = self._xReadFlag('restricted_ref_pic_lists_flag')
        pcSPS.setRestrictedRefPicListsFlag(uiCode)
        if pcSPS.getRestrictedRefPicListsFlag():
            uiCode = self._xReadFlag('lists_modification_present_flag')
            pcSPS.setListsModificationPresentFlag(uiCode)
        else:
            pcSPS.setListsModificationPresentFlag(True)
        uiCode = self._xReadUvlc('log2_min_coding_block_size_minus3')
        log2MinCUSize = uiCode + 3
        uiCode = self._xReadUvlc('log2_diff_max_min_coding_block_size')
        uiMaxCUDepthCorret = uiCode
        pcSPS.setMaxCUWidth(1 << (log2MinCUSize + uiMaxCUDepthCorret))
        cvar.g_uiMaxCUWidth = 1 << (log2MinCUSize + uiMaxCUDepthCorret)
        pcSPS.setMaxCUHeight(1 << (log2MinCUSize + uiMaxCUDepthCorret))
        cvar.g_uiMaxCUHeight = 1 << (log2MinCUSize + uiMaxCUDepthCorret)
        uiCode = self._xReadUvlc('log2_min_transform_block_size_minus2')
        pcSPS.setQuadtreeTULog2MinSize(uiCode+2)
        uiCode = self._xReadUvlc('log2_diff_max_min_transform_block_size')
        pcSPS.setQuadtreeTULog2MaxSize(uiCode + pcSPS.getQuadtreeTULog2MinSize())
        pcSPS.setMaxTrSize(1 << (uiCode + pcSPS.getQuadtreeTULog2MinSize()))
        if pcSPS.getUsePCM():
            uiCode = self._xReadUvlc('log2_min_pcm_coding_block_size_minus3')
            pcSPS.setPCMLog2MinSize(uiCode+3)
            uiCode = self._xReadUvlc('log2_diff_max_min_pcm_coding_block_size')
            pcSPS.setPCMLog2MaxSize(uiCode + pcSPS.getPCMLog2MinSize())

        uiCode = self._xReadUvlc('max_transform_hierarchy_depth_inter')
        pcSPS.setQuadtreeTUMaxDepthInter(uiCode+1)
        uiCode = self._xReadUvlc('max_transform_hierarchy_depth_intra')
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
        uiCode = self._xReadFlag('scaling_list_enabled_flag')
        pcSPS.setScalingListFlag(uiCode)
        if pcSPS.getScalingListFlag():
            uiCode = self._xReadFlag('sps_scaling_list_data_present_flag')
            pcSPS.setScalingListPresentFlag(uiCode)
            if pcSPS.getScalingListPresentFlag():
                self._parseScalingList(pcSPS.getScalingList())
        uiCode = self._xReadFlag('asymmetric_motion_partitions_enabled_flag')
        pcSPS.setUseAMP(uiCode)
        uiCode = self._xReadFlag('sample_adaptive_offset_enabled_flag')
        pcSPS.setUseSAO(True if uiCode else False)
        if pcSPS.getUsePCM():
            uiCode = self._xReadFlag('pcm_loop_filter_disable_flag')
            pcSPS.setPCMFilterDisableFlag(True if uiCode else False)

        uiCode = self._xReadFlag('temporal_id_nesting_flag')
        pcSPS.setTemporalIdNestingFlag(True if uiCode > 0 else False)

        uiCode = self._xReadUvlc('num_short_term_ref_pic_sets')
        pcSPS.createRPSList(uiCode)

        rpsList = pcSPS.getRPSList()
        for i in xrange(rpsList.getNumberOfReferencePictureSets()):
            rps = rpsList.getReferencePictureSet(i)
            self._parseShortTermRefPicSet(pcSPS, rps, i)
        uiCode = self._xReadFlag('long_term_ref_pics_present_flag')
        pcSPS.setLongTermRefsPresent(uiCode)

        if pcSPS.getLongTermRefsPresent():
            uiCode = self._xReadUvlc('num_long_term_ref_pic_sps')
            pcSPS.setNumLongTermRefPicSPS(uiCode)
            for k in xrange(pcSPS.getNumLongTermRefPicSPS()):
                uiCode = self._xReadCode(pcSPS.getBitsForPOC(), 'lt_ref_pic_poc_lsb_sps')
                pcSPS.setLtRefPicPocLsbSps(uiCode, k)
                uiCode = self._xReadFlag('used_by_curr_pic_lt_sps_flag[i]')
                pcSPS.setUsedByCurrPicLtSPSFlag(k, 1 if uiCode else 0)

        uiCode = self._xReadFlag('sps_temporal_mvp_enable_flag')
        pcSPS.setTMVPFlagsPresent(uiCode)
        # AMVP mode for each depth (AM_NONE or AM_EXPL)
        for i in xrange(pcSPS.getMaxCUDepth()):
            uiCode = self._xReadFlag()
            pcSPS.setAMVPMode(i, uiCode)

        uiCode = self._xReadFlag('sps_extension_flag')
        if uiCode:
            while self._xMoreRbspData():
                uiCode = self._xReadFlag('sps_extension_data_flag')

    @trace(use_trace, before=lambda self, pcPPS: tracePPSHeader(pcPPS))
    def parsePPS(self, pcPPS):
        uiCode = self._xReadUvlc('pic_parameter_set_id')
        pcPPS.setPPSId(uiCode)
        uiCode = self._xReadUvlc('seq_parameter_set_id')
        pcPPS.setSPSId(uiCode)

        uiCode = self._xReadFlag('sign_data_hiding_flag')
        pcPPS.setSignHideFlag(uiCode)

        uiCode = self._xReadFlag('cabac_init_present_flag')
        pcPPS.setCabacInitPresentFlag(True if uiCode else False)

        uiCode = self._xReadUvlc('num_ref_idx_l0_default_active_minus1')
        pcPPS.setNumRefIdxL0DefaultActive(uiCode+1)
        uiCode = self._xReadUvlc('num_ref_idx_l1_default_active_minus1')
        pcPPS.setNumRefIdxL1DefaultActive(uiCode+1)

        iCode = self._xReadSvlc('pic_init_qp_minus26')
        pcPPS.setPicInitQPMinus26(iCode)
        uiCode = self._xReadFlag('constrained_intra_pred_flag')
        pcPPS.setConstrainedIntraPred(True if uiCode else False)
        uiCode = self._xReadFlag('transform_skip_enabled_flag')
        pcPPS.setUseTransformSkip(True if uiCode else False)

        # alf_param() ?
        uiCode = self._xReadFlag('cu_qp_delta_enabled_flag')
        pcPPS.setUseDQP(True if uiCode else False)
        if pcPPS.getUseDQP():
            uiCode = self._xReadUvlc('diff_cu_qp_delta_depth')
            pcPPS.setMaxCuDQPDepth(uiCode)
        else:
            pcPPS.setMaxCuDQPDepth(0)

        iCode = self._xReadSvlc('cb_qp_offset')
        pcPPS.setChromaCbQpOffset(iCode)
        assert(pcPPS.getChromaCbQpOffset() >= -12)
        assert(pcPPS.getChromaCbQpOffset() <= 12)

        iCode = self._xReadSvlc('cr_qp_offset')
        pcPPS.setChromaCrQpOffset(iCode)
        assert(pcPPS.getChromaCrQpOffset() >= -12)
        assert(pcPPS.getChromaCrQpOffset() <= 12)

        uiCode = self._xReadFlag('slicelevel_chroma_qp_flag')
        pcPPS.setSliceChromaQpFlag(True if uiCode else False)

        uiCode = self._xReadFlag('weighted_pred_flag') # Use of Weighting Prediction (P_SLICE)
        pcPPS.setUseWP(uiCode == 1)
        uiCode = self._xReadFlag('weighted_bipred_flag') # Use of Bi-Directional Weighting Prediction (B_SLICE)
        pcPPS.setWPBiPred(uiCode == 1)
        sys.stdout.write("TDecCavlc::parsePPS():\tm_bUseWeightPred=%d\tm_uiBiPredIdc=%d\n" %
            (pcPPS.getUseWP(), pcPPS.getWPBiPred()))

        uiCode = self._xReadFlag('output_flag_present_flag')
        pcPPS.setOutputFlagPresentFlag(uiCode == 1)

        uiCode = self._xReadFlag('dependent_slices_enabled_flag')
        pcPPS.setDependentSlicesEnabledFlag(uiCode == 1)

        uiCode = self._xReadFlag('transquant_bypass_enable_flag')
        pcPPS.setTransquantBypassEnableFlag(True if uiCode else False)

        uiCode = self._xReadCode(2, 'tiles_or_entropy_coding_sync_idc')
        pcPPS.setTilesOrEntropyCodingSyncIdc(uiCode)
        if pcPPS.getTilesOrEntropyCodingSyncIdc() == 1:
            uiCode = self._xReadUvlc('num_tile_columns_minus1')
            pcPPS.setNumColumnsMinus1(uiCode)
            uiCode = self._xReadUvlc('num_tile_rows_minus1')
            pcPPS.setNumRowsMinus1(uiCode)
            uiCode = self._xReadFlag('uniform_spacing_flag')
            pcPPS.setUniformSpacingIdr(uiCode)

            if pcPPS.getUniformSpacingIdr() == 0:
                columnWidth = ArrayUInt(pcPPS.getNumColumnsMinus1())
                for i in xrange(pcPPS.getNumColumnsMinus1()):
                    uiCode = self._xReadUvlc('column_width')
                    columnWidth[i] = uiCode
                pcPPS.setColumnWidth(columnWidth.cast())
                del columnWidth

                rowHeight = ArrayUInt(pcPPS.getNumRowsMinus1())
                for i in xrange(pcPPS.getNumRowsMinus1()):
                    uiCode = self._xReadUvlc('row_height')
                    rowHeight[i] = uiCode
                pcPPS.setRowHeight(rowHeight.cast())
                del rowHeight

            if pcPPS.getNumColumnsMinus1() != 0 or pcPPS.getNumRowsMinus1() != 0:
                uiCode = self._xReadFlag('loop_filter_across_tiles_enabled_flag')
                pcPPS.setLFCrossTileBoundaryFlag(True if uiCode == 1 else False)
        elif pcPPS.getTilesOrEntropyCodingSyncIdc() == 3:
            uiCode = self._xReadFlag('cabac_independent_flag')
            pcPPS.setCabacIndependentFlag(True if uiCode == 1 else False)

        uiCode = self._xReadFlag('loop_filter_across_slice_flag')
        pcPPS.setLFCrossSliceBoundaryFlag(True if uiCode else False)

        uiCode = self._xReadFlag('deblocking_filter_control_present_flag')
        pcPPS.setDeblockingFilterControlPresent(True if uiCode else False)
        if pcPPS.getDeblockingFilterControlPresent():
            uiCode = self._xReadFlag('pps_deblocking_filter_flag')
            pcPPS.setLoopFilterOffsetInPPS(True if uiCode == 1 else False)
            if pcPPS.getLoopFilterOffsetInPPS():
                uiCode = self._xReadFlag('disable_deblocking_filter_flag')
                pcPPS.setLoopFilterDisable(1 if uiCode else 0)
                if not pcPPS.getLoopFilterDisable():
                    iCode = self._xReadSvlc('pps_beta_offset_div2')
                    pcPPS.setLoopFilterBetaOffset(iCode)
                    iCode = self._xReadSvlc('pps_tc_offset_div2')
                    pcPPS.setLoopFilterTcOffset(iCode)
        uiCode = self._xReadFlag('pps_scaling_list_data_present_flag')
        pcPPS.setScalingListPresentFlag(True if uiCode == 1 else False)
        if pcPPS.getScalingListPresentFlag():
            self._parseScalingList(pcPPS.getScalingList())
        uiCode = self._xReadUvlc('log2_parallel_merge_level_minus2')
        pcPPS.setLog2ParallelMergeLevelMinus2(uiCode)

        uiCode = self._xReadFlag('slice_header_extension_present_flag')
        pcPPS.setSliceHeaderExtensionPresentFlag(uiCode)

        uiCode = self._xReadFlag('pps_extension_flag')
        if uiCode:
            while self._xMoreRbspData():
                uiCode = self._xReadFlag('pps_extension_data_flag')

    def parseSEI(self, seis):
        assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
        while True:
            parseSEImessage(self.m_pcBitstream, seis)
            # SEI messages are an integer number of bytes, something has failed
            # in the parsing if bitstream not byte-aligned
            assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
            if 0x80 == self.m_pcBitstream.peekBits(8):
                break
        assert(self.m_pcBitstream.getNumBitsLeft() == 8) # rsbp_trailing_bits

    @trace(use_trace, before=lambda self, pSlice, psm: traceSliceHeader(pSlice))
    def parseSliceHeader(self, rpcSlice, parameterSetManager):
        firstSliceInPic = self._xReadFlag('first_slice_in_pic_flag')

        if rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_IDR or \
           rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT or \
           rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA or \
           rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_CRANT or \
           rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_CRA:
            uiCode = self._xReadFlag('no_output_of_prior_pics_flag') #ignored

        uiCode = self._xReadUvlc('pic_parameter_set_id')
        rpcSlice.setPPSId(uiCode)
        pps = parameterSetManager.getPrefetchedPPS(uiCode)
        #!KS: need to add error handling code here, if PPS is not available
        assert(pps != None)
        sps = parameterSetManager.getPrefetchedSPS(pps.getSPSId())
        #!KS: need to add error handling code here, if SPS is not available
        assert(sps != None)
        rpcSlice.setSPS(sps)
        rpcSlice.setPPS(pps)

        numCUs = ((sps.getPicWidthInLumaSamples() + sps.getMaxCUWidth() - 1) / sps.getMaxCUWidth()) * \
                 ((sps.getPicHeightInLumaSamples() + sps.getMaxCUHeight() - 1) / sps.getMaxCUHeight())
        maxParts = 1 << (sps.getMaxCUDepth()<<1)
        numParts = 0
        lCUAddress = 0
        reqBitsOuter = 0
        while numCUs > (1<<reqBitsOuter):
            reqBitsOuter += 1
        reqBitsInner = 0
        while numParts > (1<<reqBitsInner):
            reqBitsInner += 1

        innerAddress = 0
        if not firstSliceInPic:
            address = self._xReadCode(reqBitsOuter+reqBitsInner, 'slice_address')
            lCUAddress = address >> reqBitsInner
            innerAddress = address - (lCUAddress << reqBitsInner)

        #set uiCode to equal slice start address (or dependent slice start address)
        uiCode = maxParts * lCUAddress + innerAddress

        rpcSlice.setDependentSliceCurStartCUAddr(uiCode)
        rpcSlice.setDependentSliceCurEndCUAddr(numCUs * maxParts)

        # slice_type
        uiCode = self._xReadUvlc('slice_type')
        rpcSlice.setSliceType(uiCode)
        # lightweight_slice_flag
        uiCode = self._xReadFlag('dependent_slice_flag')
        bDependentSlice = True if uiCode else False
        if rpcSlice.getPPS().getDependentSlicesEnabledFlag():
            if bDependentSlice:
                rpcSlice.setNextSlice(False)
                rpcSlice.setNextDependentSlice(True)
                self.m_pcBitstream.readByteAlignment()
                return

        if bDependentSlice:
            rpcSlice.setNextSlice(False)
            rpcSlice.setNextDependentSlice(True)
        else:
            rpcSlice.setNextSlice(True)
            rpcSlice.setNextDependentSlice(False)

            uiCode = maxParts * lCUAddress + innerAddress

            rpcSlice.setSliceCurStartCUAddr(uiCode)
            rpcSlice.setSliceCurEndCUAddr(numCUs * maxParts)

        if not bDependentSlice:
            if pps.getOutputFlagPresentFlag():
                uiCode = self._xReadFlag('pic_output_flag')
                rpcSlice.setPicOutputFlag(True if uiCode else False)
            else:
                rpcSlice.setPicOutputFlag(True)
            if rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_IDR:
                rpcSlice.setPOC(0)
                rps = rpcSlice.getLocalRPS()
                rps.setNumberOfNegativePictures(0)
                rps.setNumberOfPositivePictures(0)
                rps.setNumberOfLongtermPictures(0)
                rps.setNumberOfPictures(0)
                rpcSlice.setRPS(rps)
            else:
                uiCode = self._xReadCode(sps.getBitsForPOC(), 'pic_order_cnt_lsb')
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
                   rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT:
                    # For BLA/BLANT, POCmsb is set to 0.
                    iPOCmsb = 0
                rpcSlice.setPOC(iPOCmsb + iPOClsb)

                rps = None
                uiCode = self._xReadFlag('short_term_ref_pic_set_sps_flag')
                if uiCode == 0: # use short-term reference picture set explicitly signalled in slice header
                    rps = rpcSlice.getLocalRPS()
                    self._parseShortTermRefPicSet(
                        sps, rps, sps.getRPSList().getNumberOfReferencePictureSets())
                    rpcSlice.setRPS(rps)
                else: # use reference to short-term reference picture set in PPS
                    uiCode = self._xReadUvlc('short_term_ref_pic_set_idx')
                    rpcSlice.setRPS(sps.getRPSList().getReferencePictureSet(uiCode))
                if sps.getLongTermRefsPresent():
                    offset = rps.getNumberOfNegativePictures() + rps.getNumberOfPositivePictures()
                    numOfLtrp = 0
                    numLtrpInSPS = 0
                    if rpcSlice.getSPS().getNumLongTermRefPicSPS() > 0:
                        uiCode = self._xReadUvlc('num_long_term_sps')
                        numLtrpInSPS = uiCode
                        numOfLtrp += numLtrpInSPS
                        rps.setNumberOfLongtermPictures(numOfLtrp)
                    bitsForLtrpInSPS = 1
                    while rpcSlice.getSPS().getNumLongTermRefPicSPS() > (1<<bitsForLtrpInSPS):
                        bitsForLtrpInSPS += 1
                    uiCode = self._xReadUvlc('num_long_term_pics')
                    rps.setNumberOfLongtermPictures(uiCode)
                    numOfLtrp += uiCode
                    rps.setNumberOfLongtermPictures(numOfLtrp)
                    maxPicOrderCntLSB = 1 << rpcSlice.getSPS().getBitsForPOC()
                    prevLSB = prevDeltaMSB = deltaPocMSBCycleLT = 0
                    j = offset + rps.getNumberOfLongtermPictures() - 1
                    for k in xrange(numOfLtrp):
                        if k < numLtrpInSPS:
                            uiCode = self._xReadCode(bitsForLtrpInSPS, 'lt_idx_sps[i]')
                            usedByCurrFromSPS = rpcSlice.getSPS().getUsedByCurrPicLtSPSFlag(uiCode)

                            uiCode = rpcSlice.getSPS().getLtRefPicPocLsbSps(uiCode)
                            rps.setUsed(j, usedByCurrFromSPS)
                        else:
                            uiCode = self._xReadCode(rpcSlice.getSPS().getBitsForPOC(), 'poc_lsb_lt')
                            uiCode = self._xReadFlag('used_by_curr_pic_lt_flag')
                            rps.setUsed(j, uiCode)
                        poc_lsb_lt = uiCode
                        uiCode = self._xReadFlag('delta_poc_msb_present_flag')
                        mSBPresentFlag = True if uiCode else False
                        if mSBPresentFlag:
                            uiCode = self._xReadUvlc(uiCode, 'delta_poc_msb_cycle_lt[i]')
                            deltaFlag = False
                            if j == offset + rps.getNumberOfLongtermPictures() - 1 or \
                               j == offset + (numOfLtrp - numLtrpInSPS) - 1 or \
                               poc_lsb_lt != prevLSB:
                                deltaFlag = True
                            if deltaFlag:
                                deltaPocMSBCycleLT = uiCode
                            else:
                                deltaPocMSBCycleLT = uiCode + prevDeltaMSB

                            pocLTCurr = rpcSlice.getPOC() - \
                                        deltaPocMSBCycleLT * maxPicOrderCntLSB - \
                                        iPOClsb + poc_lsb_lt
                            rps.setPOC(j, pocLTCurr)
                            rps.setDeltaPOC(j, - rpcSlice.getPOC() + pocLTCurr)
                            rps.setCheckLTMSBPresent(j, True)
                        else:
                            rps.setPOC(j, poc_lsb_lt)
                            rps.setDeltaPOC(j, - rpcSlice.getPOC() + poc_lsb_lt)
                            rps.setCheckLTMSBPresent(j, False)

                        prevLSB = poc_lsb_lt
                        prevDeltaMSB = deltaPocMSBCycleLT
                        j -= 1
                    offset += rps.getNumberOfLongtermPictures()
                    rps.setNumberOfPictures(offset)
                if rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA or \
                   rpcSlice.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT:
                    # In the case of BLA/BLANT, rps data is read from slice header but ignored
                    rps = rpcSlice.getLocalRPS()
                    rps.setNumberOfNegativePictures(0)
                    rps.setNumberOfPositivePictures(0)
                    rps.setNumberOfLongtermPictures(0)
                    rps.setNumberOfPictures(0)
                    rpcSlice.setRPS(rps)

            if sps.getUseSAO():
                uiCode = self._xReadFlag('slice_sample_adaptive_offset_flag')
                rpcSlice.setSaoEnabledFlag(uiCode)
                uiCode = self._xReadFlag('sao_chroma_enable_flag')
                rpcSlice.setSaoEnabledFlagChroma(uiCode)

            if not rpcSlice.isIntra():
                if rpcSlice.getSPS().getTMVPFlagsPresent():
                    uiCode = self._xReadFlag('enable_temporal_mvp_flag')
                    rpcSlice.setEnableTMVPFlag(uiCode)
                else:
                    rpcSlice.setEnableTMVPFlag(False)
                uiCode = self._xReadFlag('num_ref_idx_active_override_flag')
                if uiCode:
                    uiCode = self._xReadUvlc('num_ref_idx_l0_active_minus1')
                    rpcSlice.setNumRefIdx(REF_PIC_LIST_0, uiCode+1)
                    if rpcSlice.isInterB():
                        uiCode = self._xReadUvlc('num_ref_idx_l1_active_minus1')
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
                if not rpcSlice.getSPS().getListsModificationPresentFlag():
                    refPicListModification.setRefPicListModificationFlagL0(0)
                else:
                    uiCode = self._xReadFlag('ref_pic_list_modification_flag_l0')
                    refPicListModification.setRefPicListModificationFlagL0(1 if uiCode else 0)

                if refPicListModification.getRefPicListModificationFlagL0():
                    numRpsCurrTempList0 = rpcSlice.getNumRpsCurrTempList()
                    if numRpsCurrTempList0 > 1:
                        length = 1
                        numRpsCurrTempList0 -= 1
                        while numRpsCurrTempList0 >> 1:
                            numRpsCurrTempList0 >>= 1
                            length += 1
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_0)):
                            uiCode = self._xReadCode(length, 'list_entry_l0')
                            refPicListModification.setRefPicSetIdxL0(i, uiCode)
                    else:
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_0)):
                            refPicListModification.setRefPicSetIdxL0(i, 0)
            else:
                refPicListModification.setRefPicListModificationFlagL0(0)
            if rpcSlice.isInterB():
                if not rpcSlice.getSPS().getListsModificationPresentFlag():
                    refPicListModification.setRefPicListModificationFlagL1(0)
                else:
                    uiCode = self._xReadFlag('ref_pic_list_modification_flag_l1')
                    refPicListModification.setRefPicListModificationFlagL1(1 if uiCode else 0)
                if refPicListModification.getRefPicListModificationFlagL1():
                    numRpsCurrTempList1 = rpcSlice.getNumRpsCurrTempList()
                    if numRpsCurrTempList1 > 1:
                        length = 1
                        numRpsCurrTempList1 -= 1
                        while numRpsCurrTempList1 >> 1:
                            numRpsCurrTempList1 >>= 1
                            length += 1
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_1)):
                            uiCode = self._xReadCode(length, 'list_entry_l1')
                            refPicListModification.setRefPicSetIdxL1(i, uiCode)
                    else:
                        for i in xrange(rpcSlice.getNumRefIdx(REF_PIC_LIST_1)):
                            refPicListModification.setRefPicSetIdxL1(i, 0)
            else:
                refPicListModification.setRefPicListModificationFlagL1(0)
        else:                
            # initialize from previous slice
            pps = rpcSlice.getPPS()
            sps = rpcSlice.getSPS()

        if rpcSlice.isInterB():
            uiCode = self._xReadFlag('mvd_l1_zero_flag')
            rpcSlice.setMvdL1ZeroFlag(True if uiCode else False)

        rpcSlice.setCabacInitFlag(False) # default
        if pps.getCabacInitPresentFlag() and not rpcSlice.isIntra():
            uiCode = self._xReadFlag('cabac_init_flag')
            rpcSlice.setCabacInitFlag(True if uiCode else False)

        if not bDependentSlice:
            iCode = self._xReadSvlc('slice_qp_delta')
            rpcSlice.setSliceQp(26 + pps.getPicInitQPMinus26() + iCode)

            assert(rpcSlice.getSliceQp() >= -sps.getQpBDOffsetY())
            assert(rpcSlice.getSliceQp() <= 51)

            if rpcSlice.getPPS().getSliceChromaQpFlag():
                iCode = self._xReadSvlc('slice_qp_delta_cb')
                rpcSlice.setSliceQpDeltaCb(iCode)
                assert(rpcSlice.getSliceQpDeltaCb() >= -12)
                assert(rpcSlice.getSliceQpDeltaCb() <= 12)
                assert(rpcSlice.getPPS().getChromaCbQpOffset() + rpcSlice.getSliceQpDeltaCb() >= -12)
                assert(rpcSlice.getPPS().getChromaCbQpOffset() + rpcSlice.getSliceQpDeltaCb() <= 12)

                iCode = self._xReadSvlc('slice_qp_delta_cr')
                rpcSlice.setSliceQpDeltaCr(iCode)
                assert(rpcSlice.getSliceQpDeltaCr() >= -12)
                assert(rpcSlice.getSliceQpDeltaCr() <= 12)
                assert(rpcSlice.getPPS().getChromaCrQpOffset() + rpcSlice.getSliceQpDeltaCr() >= -12)
                assert(rpcSlice.getPPS().getChromaCrQpOffset() + rpcSlice.getSliceQpDeltaCr() <= 12)

            if rpcSlice.getPPS().getDeblockingFilterControlPresent():
                if rpcSlice.getPPS().getLoopFilterOffsetInPPS():
                    uiCode = self._xReadFlag('inherit_dbl_param_from_PPS_flag')
                    rpcSlice.setInheritDblParamFromPPS(1 if uiCode else 0)
                else:
                    rpcSlice.setInheritDblParamFromPPS(0)
                if not rpcSlice.getInheritDblParamFromPPS():
                    uiCode = self._xReadFlag('disable_deblocking_filter_flag')
                    rpcSlice.setLoopFilterDisable(1 if uiCode else 0)
                    if not rpcSlice.getLoopFilterDisable():
                        iCode = self._xReadSvlc('beta_offset_div2')
                        rpcSlice.setLoopFilterBetaOffset(iCode)
                        iCode = self._xReadSvlc('tc_offset_div2')
                        rpcSlice.setLoopFilterTcOffset(iCode)
                else:
                    rpcSlice.setLoopFilterDisable(rpcSlice.getPPS().getLoopFilterDisable())
                    rpcSlice.setLoopFilterBetaOffset(rpcSlice.getPPS().getLoopFilterBetaOffset())
                    rpcSlice.setLoopFilterTcOffset(rpcSlice.getPPS().getLoopFilterTcOffset())
            if rpcSlice.getEnableTMVPFlag():
                if rpcSlice.getSliceType() == B_SLICE:
                    uiCode = self._xReadFlag('collocated_from_l0_flag')
                    rpcSlice.setColDir(uiCode)

                if rpcSlice.getSliceType() != I_SLICE and \
                   ((rpcSlice.getColDir() == 0 and rpcSlice.getNumRefIdx(REF_PIC_LIST_0) > 1) or
                    (rpcSlice.getColDir() == 1 and rpcSlice.getNumRefIdx(REF_PIC_LIST_1) > 1)):
                    uiCode = self._xReadUvlc('collocated_ref_idx')
                    rpcSlice.setColRefIdx(uiCode)
            if (pps.getUseWP() and rpcSlice.getSliceType() == P_SLICE) or \
               (pps.getWPBiPred() and rpcSlice.getSliceType() == B_SLICE):
                self._xParsePredWeightTable(rpcSlice)
                rpcSlice.initWpScaling()

        uiCode = self._xReadUvlc('5_minus_max_num_merge_cand')
        rpcSlice.setMaxNumMergeCand(MRG_MAX_NUM_CANDS - uiCode)
        assert(rpcSlice.getMaxNumMergeCand() == MRG_MAX_NUM_CANDS_SIGNALED)

        if not bDependentSlice:
            isSAOEnabled = False if not rpcSlice.getSPS().getUseSAO() else \
                           (rpcSlice.getSaoEnabledFlag() or rpcSlice.getSaoEnabledFlagChroma())
            isDBFEnabled = not rpcSlice.getLoopFilterDisable()

        if rpcSlice.getPPS().getLFCrossSliceBoundaryFlag() and (isSAOEnabled or isDBFEnabled):
            uiCode = self._xReadFlag('slice_loop_filter_across_slices_enabled_flag')
        else:
            uiCode = 1 if rpcSlice.getPPS().getLFCrossSliceBoundaryFlag() else 0
        rpcSlice.setLFCrossSliceBoundaryFlag(True if uiCode == 1 else False)

        if pps.getDependentSlicesEnabledFlag() == False:
            tilesOrEntropyCodingSyncIdc = pps.getTilesOrEntropyCodingSyncIdc()
            entryPointOffset = None
            numEntryPointOffsets = offsetLenMinus1 = 0

            rpcSlice.setNumEntryPointOffsets(0) # default

            if tilesOrEntropyCodingSyncIdc > 0:
                numEntryPointOffsets = self._xReadUvlc('num_entry_point_offsets')
                rpcSlice.setNumEntryPointOffsets(numEntryPointOffsets)
                if numEntryPointOffsets > 0:
                    offsetLenMinus1 = self._xReadUvlc('offset_len_minus1')
                entryPointOffset = numEntryPointOffsets * [0]
                for idx in xrange(numEntryPointOffsets):
                    uiCode = self._xReadCode(offsetLenMinus1+1, 'entry_point_offset')
                    entryPointOffset[idx] = uiCode

            if tilesOrEntropyCodingSyncIdc == 1: # tiles
                rpcSlice.setTileLocationCount(numEntryPointOffsets)

                prevPos = 0
                for idx in xrange(rpcSlice.getTileLocationCount()):
                    rpcSlice.setTileLocation(idx, prevPos + entryPointOffset[idx])
                    prevPos += entryPointOffset[idx]
            elif tilesOrEntropyCodingSyncIdc == 2: # wavefront
                numSubstreams = pps.getNumSubstreams()
                rpcSlice.allocSubstreamSizes(numSubstreams)
                pSubstreamSizes = pointer(rpcSlice.getSubstreamSizes(), type='uint *')
                for idx in xrange(numSubstreams-1):
                    if idx < numEntryPointOffsets:
                        pSubstreamSizes[idx] = entryPointOffset[idx] << 3
                    else:
                        pSubstreamSizes[idx] = 0

            if entryPointOffset:
                del entryPointOffset

        if pps.getSliceHeaderExtensionPresentFlag():
            uiCode = self._xReadUvlc('slice_header_extension_length')
            if i in xrange(uiCode):
                ignore = self._xReadCode(8, 'slice_header_extension_data_byte')
        self.m_pcBitstream.readByteAlignment()

    def parseTerminatingBit(self, ruiBit):
        ruiBit = False
        iBitsLeft = self.m_pcBitstream.getNumBitsLeft()
        if iBitsLeft <= 8:
            uiPeekValue = self.m_pcBitstream.peekBits(iBitsLeft)
            if uiPeekValue == (1 << (iBitsLeft-1)):
                ruiBit = True
        return ruiBit

    def parseSkipFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseCUTransquantBypassFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseMVPIdx(self, riMVPIdx):
        assert(False)
    def parseSplitFlag(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parsePartSize(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parsePredMode(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)

    def parseIPCMInfo(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseIntraDirLumaAng(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseIntraDirChroma(self, pcCU, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseInterDir(self, pcCU, ruiInterDir, uiAbsPartIdx, uiDepth):
        assert(False)
    def parseRefFrmIdx(self, pcCU, riRefFrmIdx, uiAbsPartIdx, uiDepth, eRefList):
        assert(False)
    def parseMvd(self, pcCU, uiAbsPartIdx, uiPartIdx, uiDepth, eRefList):
        assert(False)

    def parseDeltaQP(self, pcCU, uiAbsPartIdx, uiDepth):
        iDQp = self._xReadSvlc()

        qpBdOffsetY = pcCU.getSlice().getSPS().getQpBDOffsetY()
        qp = ((Char(pcCU.getRefQP(uiAbsPartIdx)) + iDQp + 52 + 2*qpBdOffsetY) % (52 + qpBdOffsetY)) - qpBdOffsetY

        uiAbsQpCUPartIdx = (uiAbsPartIdx >> ((cvar.g_uiMaxCUDepth - pcCU.getSlice().getPPS().getMaxCUDQPDepth()) << 1)) << \
                                            ((cvar.g_uiMaxCUDepth - pcCU.getSlice().getPPS().getMaxCUDQPDepth()) << 1)
        uiQpCUDepth = min(uiDepth, pcCU.getSlice().getPPS().getMaxCUDQPDepth())

        pcCU.setQPSubParts(qp, uiAbsPartIdx, uiQpCUDepth)

    def parseCoeffNxN(self, pcCU, pcCoef, uiAbsPartIdx, uiWidth, uiHeight, uiDepth, eTType):
        assert(False)
    def parseTransformSubdivFlag(self, ruiSubdivFlag, uiLog2TransformBlockSize):
        assert(False)
    def parseQtCbf(self, pcCU, uiAbsPartIdx, eType, uiTrDepth, uiDepth):
        assert(False)
    def parseQtRootCbf(self, pcCU, uiAbsPartIdx, uiDepth, uiQtRootCbf):
        assert(False)
    def parseTransformSkilFlags(self, pcCU, uiAbsPartIdx, width, height, uiDepth, eTType):
        assert(False)
    def parseMergeFlag(self, pcCU, uiAbsPartIdx, uiDepth, uiPUIdx):
        assert(False)
    def parseMergeIndex(self, pcCU, ruiMergeIndex, uiAbsPartIdx, uiDepth):
        assert(False)

    @trace(use_trace, wrapper=traceReadCode)
    def _xReadCode(self, uiLength, pSymbolName=''):
        assert(uiLength > 0)
        ruiCode = 0
        ruiCode = self.m_pcBitstream.read(uiLength, ruiCode)
        return ruiCode

    @trace(use_trace, wrapper=traceReadUvlc)
    def _xReadUvlc(self, pSymbolName=''):
        ruiVal = 0
        uiCode = 0
        uiCode = self.m_pcBitstream.read(1, uiCode)

        if uiCode == 0:
            uiLength = 0

            while not (uiCode & 1):
                uiCode = self.m_pcBitstream.read(1, uiCode)
                uiLength += 1

            ruiVal = self.m_pcBitstream.read(uiLength, ruiVal)
            ruiVal += (1 << uiLength) - 1

        return ruiVal

    @trace(use_trace, wrapper=traceReadSvlc)
    def _xReadSvlc(self, pSymbolName=''):
        riVal = 0
        uiBits = 0
        uiBits = self.m_pcBitstream.read(1, uiBits)

        if uiBits == 0:
            uiLength = 0

            while not (uiBits & 1):
                uiBits = self.m_pcBitstream.read(1, uiBits)
                uiLength += 1

            uiBits = self.m_pcBitstream.read(uiLength, uiBits)
            uiBits += (1 << uiLength)
            riVal = -(uiBits>>1) if (uiBits & 1) else (uiBits>>1)

        return riVal

    @trace(use_trace, wrapper=traceReadFlag)
    def _xReadFlag(self, pSymbolName=''):
        ruiCode = 0
        ruiCode = self.m_pcBitstream.read(1, ruiCode)
        return ruiCode

    def _xReadEpExGolomb(self, uiCount):
        ruiSymbol = 0
        uiBit = 1

        while uiBit:
            uiBit = self._xReadFlag()
            ruiSymbol += uiBit << uiCount
            uiCount += 1

        uiCount -= 1
        while uiCount:
            uiCount -= 1
            uiBit = self._xReadFlag()
            ruiSymbol += uiBit << uiCount

        return ruiSymbol

    def _xReadExGolombLevel(self):
        ruiSymbol = 0
        uiSymbol = 0
        uiCount = 0

        while True:
            uiSymbol = self._xReadFlag()
            uiCount += 1
            if not (uiSymbol and uiCount != 13):
                break

        ruiSymbol = uiCount - 1

        if uiSymbol:
            uiSymbol = self._xReadEpExGolomb(0)
            ruiSymbol += uiSymbol + 1

        return ruiSymbol

    def _xReadUnaryMaxSymbol(self, uiMaxSymbol):
        ruiSymbol = 0
        if uiMaxSymbol == 0:
            ruiSymbol = 0
            return ruiSymbol

        ruiSymbol = self._xReadFlag()

        if ruiSymbol == 0 or uiMaxSymbol == 1:
            return ruiSymbol

        ruiSymbol = 0
        uiCont = 0

        while True:
            uiCont = self._xReadFlag()
            uiSymbol += 1
            if not (uiCont and ruiSymbol < uiMaxSymbol-1):
                break

        if uiCont and ruiSymbol == uiMaxSymbol-1:
            ruiSymbol += 1

        return ruiSymbol

    def _xReadPCMAlignZero(self):
        uiNumberOfBits = self.m_pcBitstream.getNumBitsUntilByteAligned()

        if uiNumberOfBits:
            uiSymbol = 0

            for uiBits in xrange(uiNumberOfBits):
                uiSymbol = self._xReadFlag()

                if uiSymbol:
                    sys.stdout.write("\nWarning! pcm_align_zero include a non-zero value.\n")

    def _xGetBit(self):
        ruiCode = 0
        ruiCode = self.m_pcBitstream.read(1, ruiCode)
        return ruiCode

    def _xMoreRbspData(self):
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

    def _xDecodeScalingList(self, scalingList, sizeId, listId):
        coefNum = min(MAX_MATRIX_COEF_NUM, g_scalingListSize[sizeId])
        scalingListDcCoefMinus8 = 0
        nextCoef = SCALING_LIST_START_VALUE
        scan = g_auiSigLastScan[SCAN_DIAG][1] if sizeId == 0 else g_sigLastScanCG32x32
        dst = scalingList.getScalingListAddress(sizeId, listId)

        if sizeId > SCALING_LIST_8x8:
            scalingListDcCoefMinus8 = self._xReadSvlc('scaling_list_dc_coef_minus8')
            scalingList.setScalingListDC(sizeId, listId, scalingListDcCoefMinus8+8)
            nextCoef = scalingList.getScalingListDC(sizeId, listId)

        for i in xrange(coefNum):
            data = self._xReadSvlc('scaling_list_delta_coef')
            nextCoef = (nextCoef + data + 256) % 256
            dst[scan[i]] = nextCoef

    def _parseScalingList(self, scalingList):
        for sizeId in xrange(SCALING_LIST_SIZE_NUM):
            for listId in xrange(g_scalingListNum[sizeId]):
                code = self._xReadFlag('scaling_list_pred_mode_flag')
                scalingListPredModeFlag = True if code else False
                if not scalingListPredModeFlag: # Copy Mode
                    code = self._xReadUvlc('scaling_list_pred_matrix_id_delta')
                    scalingList.setRefMatrixId(sizeId, listId, listId-code)
                    if sizeId > SCALING_LIST_8x8:
                        scalingList.setScalingListDC(sizeId, listId,
                            16 if listId == scalingList.getRefMatrixId(sizeId, listId) else
                            scalingList.getScalingListDC(sizeId, scalingList.getRefMatrixId(sizeId, listId)))
                    scalingList.processRefMatrix(sizeId, listId, scalingList.getRefMatrixId(sizeId, listId))
                else: #DPCM Mode
                    self._xDecodeScalingList(scalingList, sizeId, listId)

    def _parseShortTermRefPicSet(self, sps, rps, idx):
        code = 0
        interRPSPred = self._xReadFlag('inter_ref_pic_set_prediction_flag')
        rps.setInterRPSPrediction(interRPSPred)
        if interRPSPred:
            if idx == sps.getRPSList().getNumberOfReferencePictureSets():
                code = self._xReadUvlc('delta_idx_minus1') # delta index of the Reference Picture Set used for prediction minus 1
            else:
                code = 0
            assert(code <= idx-1) # delta_idx_minus1 shall not be larger than idx-1, otherwise we will predict from a negative row position that does not exist. When idx equals 0 there is no legal value and interRPSPred must be zero. See J0185-r2
            rIdx = idx - 1 - code
            assert(0 <= rIdx <= idx-1) # Made assert tighter; if rIdx = idx then prediction is done from itself. rIdx must belong to range 0, idx-1, inclusive, see J0185-r2
            rpsRef = sps.getRPSList().getReferencePictureSet(rIdx)
            k = k0 = k1 = 0
            bit = self._xReadCode(1, 'delta_rps_sign') # delta_RPS_sign
            code = self._xReadUvlc('abs_delta_rps_minus1') # absolute delta RPS minus 1
            deltaRPS = (1 - (bit<<1)) * (code + 1) # delta_RPS
            for j in xrange(rpsRef.getNumberOfPictures()+1):
                bit = self._xReadCode(1, 'used_by_curr_pic_flag') #first bit is "1" if Idc is 1
                refIdc = bit
                if refIdc == 0:
                    bit = self._xReadCode(1, 'use_delta_flag') #second bit is "1" if Idc is 2, "0" otherwise.
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
            code = self._xReadUvlc('num_negative_pics')
            rps.setNumberOfNegativePictures(code)
            code = self._xReadUvlc('num_positive_pics')
            rps.setNumberOfPositivePictures(code)
            prev = 0
            poc = 0
            for j in xrange(rps.getNumberOfNegativePictures()):
                code = self._xReadUvlc('delta_poc_s0_minus1')
                poc = prev - code - 1
                prev = poc
                rps.setDeltaPOC(j, poc)
                code = self._xReadFlag('used_by_curr_pic_s0_flag')
                rps.setUsed(j, code)
            prev = 0
            for j in xrange(rps.getNumberOfNegativePictures(),
                            rps.getNumberOfNegativePictures()+rps.getNumberOfPositivePictures()):
                code = self._xReadUvlc('delta_poc_s1_minus1')
                poc = prev + code + 1
                prev = poc
                rps.setDeltaPOC(j, poc)
                code = self._xReadFlag('used_by_curr_pic_s1_flag')
                rps.setUsed(j, code)
            rps.setNumberOfPictures(rps.getNumberOfNegativePictures()+rps.getNumberOfPositivePictures())

    def _xParsePredWeightTable(self, pcSlice):
        bChroma = True # color always present in HEVC ?
        pps = pcSlice.getPPS()
        eSliceType = pcSlice.getSliceType()
        iNbRef = 2 if eSliceType == B_SLICE else 1
        uiMode = 0
        uiTotalSignalledWeightFlags = 0
        if (eSliceType == P_SLICE and pps.getUseWP()) or \
           (eSliceType == B_SLICE and pps.getWPBiPred()):
            uiMode = 1 # explicit
        if uiMode == 1: # explicit
            sys.stdout.write("\nTDecCavlc::xParsePredWeightTable(poc=%d) explicit...\n" % pcSlice.getPOC())
            iDeltaDenom = 0
            # decode delta_luma_log2_weight_denom :
            uiLog2WeightDenomLuma = self._xReadUvlc('luma_log2_weight_denom') # ue(v): luma_log2_weight_denom
            if bChroma:
                iDeltaDenom = self._xReadSvlc('delta_chroma_log2_weight_denom') # se(v): delta_chroma_log2_weight_denom
                assert(iDeltaDenom + uiLog2WeightDenomLuma >= 0)
                uiLog2WeightDenomChroma = iDeltaDenom + uiLog2WeightDenomLuma

            for iNumRef in xrange(iNbRef):
                eRefPicList = REF_PIC_LIST_1 if iNumRef else REF_PIC_LIST_0
                for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList)):
                    wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)

                    wp[0].uiLog2WeightDenom = uiLog2WeightDenomLuma
                    wp[1].uiLog2WeightDenom = uiLog2WeightDenomChroma
                    wp[2].uiLog2WeightDenom = uiLog2WeightDenomChroma

                    uiCode = self._xReadFlag('luma_weight_lX_flag') # u(1): luma_weight_l0_flag
                    wp[0].bPresentFlag = (uiCode == 1)
                    uiTotalSignalledWeightFlags += wp[0].bPresentFlag
                if bChroma:
                    for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList)):
                        wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)
                        uiCode = self._xReadFlag('chroma_weight_lX_flag') # u(1): chroma_weight_l0_flag
                        wp[1].bPresentFlag = (uiCode == 1)
                        wp[2].bPresentFlag = (uiCode == 1)
                        uiTotalSignalledWeightFlags += 2 * wp[1].bPresentFlag
                for iRefIdx in xrange(pcSlice.getNumRefIdx(eRefPicList)):
                    wp = pcSlice.getWpScaling(eRefPicList, iRefIdx)
                    if wp[0].bPresentFlag:
                        iDeltaWeight = self._xReadSvlc('delta_luma_weight_lX') # se(v): delta_luma_weight_l0[i]
                        wp[0].iWeight = iDeltaWeight + (1<<wp[0].uiLog2WeightDenom)
                        wp[0].iOffset = self._xReadSvlc('luma_offset_lX') # se(v): luma_offset_l0[i]
                    else:
                        wp[0].iWeight = 1 << wp[0].uiLog2WeightDenom
                        wp[0].iOffset = 0
                    if bChroma:
                        if wp[1].bPresentFlag:
                            for j in xrange(1, 3):
                                iDeltaWeight = self._xReadSvlc('delta_chroma_weight_lX') # se(v): chroma_weight_l0[i][j]
                                wp[j].iWeight = iDeltaWeight + (1<<wp[1].uiLog2WeightDenom)

                                iDeltaChroma = self._xReadSvlc('delta_chroma_offset_lX') # se(v): delta_chroma_offset_l0[i][j]
                                shift = 1 << (cvar.g_uiBitDepth + cvar.g_uiBitIncrement - 1)
                                pred = shift - ((shift*wp[j].iWeight) >> wp[j].uiLog2WeightDenom)
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
        else:
            sys.stdout.write("\n wrong weight pred table syntax \n ")
            assert(False)
