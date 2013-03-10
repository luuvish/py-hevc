# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/SEIread.py
    HM 10.0 Python Implementation
"""

import sys

from ... import Trace

from ... import ArrayUChar, ArrayUint

from .SyntaxElementParser import SyntaxElementParser

from ..TLibCommon.CommonDef import NAL_UNIT_SEI

from ..TLibCommon.SEI import (
    SEI,
    SEIuserDataUnregistered,
    SEIActiveParameterSets,
    SEIDecodingUnitInfo,
    SEIBufferingPeriod,
    SEIPictureTiming,
    SEIRecoveryPoint,
    SEIFramePacking,
    SEIDisplayOrientation,
    SEITemporalLevel0Index,
    SEIGradualDecodingRefreshInfo,
    SEIDecodedPictureHash
)


def xTraceSEIHeader():
    Trace.g_hTrace.write("=========== SEI message ===========\n")

def xTraceSEIMessageType(payloadType):
    if payloadType == SEI.DECODED_PICTURE_HASH:
        Trace.g_hTrace.write("=========== Decoded picture hash SEI message ===========\n")
    elif payloadType == SEI.USER_DATA_UNREGISTERED:
        Trace.g_hTrace.write("=========== User Data Unregistered SEI message ===========\n")
    elif payloadType == SEI.ACTIVE_PARAMETER_SETS:
        Trace.g_hTrace.write("=========== Active Parameter Sets SEI message ===========\n")
    elif payloadType == SEI.BUFFERING_PERIOD:
        Trace.g_hTrace.write("=========== Buffering period SEI message ===========\n")
    elif payloadType == SEI.PICTURE_TIMING:
        Trace.g_hTrace.write("=========== Picture timing SEI message ===========\n")
    elif payloadType == SEI.RECOVERY_POINT:
        Trace.g_hTrace.write("=========== Recovery point SEI message ===========\n")
    elif payloadType == SEI.FRAME_PACKING:
        Trace.g_hTrace.write("=========== Frame Packing Arrangement SEI message ===========\n")
    elif payloadType == SEI.DISPLAY_ORIENTATION:
        Trace.g_hTrace.write("=========== Display Orientation SEI message ===========\n")
    elif payloadType == SEI.TEMPORAL_LEVEL0_INDEX:
        Trace.g_hTrace.write("=========== Temporal Level Zero Index SEI message ===========\n")
    elif payloadType == SEI.REGION_REFRESH_INFO:
        Trace.g_hTrace.write("=========== Gradual Decoding Refresh Information SEI message ===========\n")
    elif payloadType == SEI.DECODING_UNIT_INFO:
        Trace.g_hTrace.write("=========== Decoding Unit Information SEI message ===========\n")
    else:
        Trace.g_hTrace.write("=========== Unknown SEI message ===========\n")


class SEIReader(SyntaxElementParser):

    def parseSEImessage(self, bs, seis, nalUnitType, sps):
        self.setBitstream(bs)

        assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
        while True:
            self.xReadSEImessage(seis, nalUnitType, sps)
            # SEI messages are an integer number of bytes, something has failed
            # in the parsing if bitstream not byte-aligned
            assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
            if self.m_pcBitstream.getNumBitsLeft() <= 8:
                break

        rbspTrailingBits = 0
        rbspTrailingBits = self.xReadCode(8, rbspTrailingBits, 'rbsp_trailing_bits')
        assert(rbspTrailingBits == 0x80)

    def xReadSEImessage(self, seis, nalUnitType, sps):
        if Trace.on:
            xTraceSEIHeader()

        payloadType = 0
        val = 0

        while True:
            val = self.xReadCode(8, val, 'payload_type')
            payloadType += val
            if val != 0xFF:
                break

        payloadSize = 0
        while True:
            val = self.xReadCode(8, val, 'payload_size')
            payloadSize += val
            if val != 0xFF:
                break

        if Trace.on:
            xTraceSEIMessageType(payloadType)

        # extract the payload for this single SEI message.
        # This allows greater safety in erroneous parsing of an SEI message
        # from affecting subsequent messages.
        # After parsing the payload, bs needs to be restored as the primary
        # bitstream.
        bs = self.getBitstream()
        self.setBitstream(bs.extractSubstream(payloadSize * 8))

        sei = None

        if nalUnitType == NAL_UNIT_SEI:
            if payloadType == SEI.USER_DATA_UNREGISTERED:
                sei = SEIuserDataUnregistered()
                self.xParseSEIuserDataUnregistered(sei, payloadSize)
            elif payloadType == SEI.ACTIVE_PARAMETER_SETS:
                sei = SEIActiveParameterSets()
                self.xParseSEIActiveParameterSets(sei, payloadSize)
            elif payloadType == SEI.DECODING_UNIT_INFO:
                if not sps:
                    sys.stdout.write("Warning: Found Decoding unit SEI message, but no active SPS is available. Ignoring.")
                else:
                    sei = SEIDecodingUnitInfo()
                self.xParseSEIDecodingUnitInfo(sei, payloadSize, sps)
            elif payloadType == SEI.BUFFERING_PERIOD:
                if not sps:
                    sys.stdout.write("Warning: Found Buffering period SEI message, but no active SPS is available. Ignoring.")
                else:
                    sei = SEIBufferingPeriod()
                self.xParseSEIBufferingPeriod(sei, payloadSize, sps)
            elif payloadType == SEI.PICTURE_TIMING:
                if not sps:
                    sys.stdout.write("Warning: Found Picture timing SEI message, but no active SPS is available. Ignoring.")
                else:
                    sei = SEIPictureTiming()
                self.xParseSEIPictureTiming(sei, payloadSize, sps)
            elif payloadType == SEI.RECOVERY_POINT:
                sei = SEIRecoveryPoint()
                self.xParseSEIRecoveryPoint(sei, payloadSize)
            elif payloadType == SEI.FRAME_PACKING:
                sei = SEIFramePacking()
                self.xParseSEIFramePacking(sei, payloadSize)
            elif payloadType == SEI.DISPLAY_ORIENTATION:
                sei = SEIDisplayOrientation()
                self.xParseSEIDisplayOrientation(sei, payloadSize)
            elif payloadType == SEI.TEMPORAL_LEVEL0_INDEX:
                sei = SEITemporalLevel0Index()
                self.xParseSEITemporalLevel0Index(sei, payloadSize)
            elif payloadType == SEI.REGION_REFRESH_INFO:
                sei = SEIGradualDecodingRefreshInfo()
                self.xParseSEIGradualDecodingRefreshInfo(sei, payloadSize)
            else:
                for i in xrange(payloadSize):
                    seiByte = 0
                    seiByte = self.xReadCode(8, seiByte, 'unknown prefix SEI payload byte')
                sys.stdout.write("Unknown prefix SEI message (payloadType = %d) was found!\n" % payloadType)
        else:
            if payloadType == SEI.USER_DATA_UNREGISTERED:
                sei = SEIuserDataUnregistered()
                self.xParseSEIuserDataUnregistered(sei, payloadSize)
            elif payloadType == SEI.DECODED_PICTURE_HASH:
                sei = SEIDecodedPictureHash()
                self.xParseSEIDecodedPictureHash(sei, payloadSize)
            else:
                for i in xrange(payloadSize):
                    seiByte = 0
                    seiByte = self.xReadCode(8, seiByte, 'unknown suffix SEI payload byte')
                sys.stdout.write("Unknown suffix SEI message (payloadType = %d) was found!\n" % payloadType)
        if sei != None:
            seis.push_back(sei)

        # By definition the underlying bitstream terminates in a byte-aligned manner.
        # 1. Extract all bar the last MIN(bitsremaining,nine) bits as reserved_payload_extension_data
        # 2. Examine the final 8 bits to determine the payload_bit_equal_to_one marker
        # 3. Extract the remainingreserved_payload_extension_data bits.
        #
        # If there are fewer than 9 bits available, extract them.
        payloadBitsRemaining = self.getBitstream().getNumBitsLeft()
        if payloadBitsRemaining: # more_data_in_payload()
            while payloadBitsRemaining > 9:
                reservedPayloadExtensionData = 0
                reservedPayloadExtensionData = self.xReadCode(1, reservedPayloadExtensionData, 'reserved_payload_extension_data')
                payloadBitsRemaining -= 1

            # 2
            finalBits = self.getBitstream().peekBits(payloadBitsRemaining)
            finalPayloadBits = 0
            mask = 0xff
            while finalBits & (mask >> finalPayloadBits):
                finalPayloadBits += 1

            # 3
            while payloadBitsRemaining > 9 - finalPayloadBits:
                reservedPayloadExtensionData = 0
                reservedPayloadExtensionData = self.xReadCode(1, reservedPayloadExtensionData, 'reserved_payload_extension_data')
                payloadBitsRemaining -= 1

            dummy = 0
            dummy = self.xReadCode(1, dummy, 'payload_bit_equal_to_one')
            dummy = self.xReadCode(payloadBitsRemaining-1, dummy, 'payload_bit_equal_to_zero')

        # restore primary bitstream for sei_message
        p = self.getBitstream()
        del p
        self.setBitstream(bs)

    def xParseSEIuserDataUnregistered(self, sei, payloadSize):
        assert(payloadSize >= 16)
        val = 0

        for i in xrange(16):
            val = self.xReadCode(8, val, 'uuid_iso_iec_11578')
            sei.uuid_iso_iec_11578[i] = val

        sei.userDataLength = payloadSize - 16
        if not sei.userDataLength:
            sei.userData = 0
            return

        sei.userData = ArrayUChar(sei.userDataLength)
        for i in xrange(sei.userDataLength):
            val = self.xReadCode(8, val, 'user_data')
            sei.userData[i] = val

    def xParseSEIActiveParameterSets(self, sei, payloadSize):
        val = 0
        val = self.xReadCode(4, val, 'active_vps_id')
        sei.activeVPSId = val
        val = self.xReadFlag(val, 'full_random_access_flag')
        sei.m_fullRandomAccessFlag = True if val else False
        val = self.xReadFlag(val, 'no_param_set_update_flag')
        sei.m_noParamSetUpdateFlag = True if val else False
        val = self.xReadUvlc(val, 'num_sps_ids_minus1')
        sei.numSpsIdsMinus1 = val

        sei.activeSeqParamSetId.resize(sei.numSpsIdsMinus1 + 1)
        for i in xrange(sei.numSpsIdsMinus1 + 1):
            val = self.xReadUvlc(val, 'active_seq_param_set_id')
            sei.activeSeqParamSetId[i] = val

        uibits = self.m_pcBitstream.getNumBitsUntilByteAligned()

        while uibits:
            val = self.xReadFlag(val, 'alignment_bit')
            uibits -= 1

    def xParseSEIDecodingUnitInfo(self, sei, payloadSize, sps):
        val = 0
        val = self.xReadUvlc(val, 'decoding_unit_idx')
        sei.m_decodingUnitIdx = val

        vui = sps.getVuiParameters()
        if vui.getHrdParameters().getSubPicCpbParamsInPicTimingSEIFlag():
            val = self.xReadCode(vui.getHrdParameters().getDuCpbRemovalDelayLengthMinus1() + 1,
                val, 'du_spt_cpb_removal_delay')
            sei.m_duSptCpbRemovalDelay = val
        else:
            sei.m_duSptCpbRemovalDelay = 0

        val = self.xReadFlag(val, 'dpb_output_du_delay_present_flag')
        sei.m_dpbOutputDuDelayPresentFlag = True if val else False
        if sei.m_dpbOutputDuDelayPresentFlag:
            val = self.xReadCode(vui.getHrdParameters().getDpbOutputDelayDuLengthMinus1() + 1,
                val, 'pic_spt_dpb_output_du_delay')
            sei.m_picSptDpbOutputDuDelay = val
        self.xParseByteAlign()

    def xParseSEIDecodedPictureHash(self, sei, payloadSize):
        val = 0
        val = self.xReadCode(8, val, 'hash_type')
        sei.method = val
        for yuvIdx in xrange(3):
            if SEIDecodedPictureHash.MD5 == sei.method:
                for i in xrange(16):
                    val = self.xReadCode(8, val, 'picture_md5')
                    sei.digest[yuvIdx][i] = val
            elif SEIDecodedPictureHash.CRC == sei.method:
                val = self.xReadCode(16, val, 'picture_crc')
                sei.digest[yuvIdx][0] = (val >> 8) & 0xff
                sei.digest[yuvIdx][1] = val & 0xff
            elif SEIDecodedPictureHash.CHECKSUM == sei.method:
                val = self.xReadCode(32, val, 'picture_checksum')
                sei.digest[yuvIdx][0] = (val >> 24) & 0xff
                sei.digest[yuvIdx][1] = (val >> 16) & 0xff
                sei.digest[yuvIdx][2] = (val >>  8) & 0xff
                sei.digest[yuvIdx][3] = (val      ) & 0xff

    def xParseSEIBufferingPeriod(self, sei, payloadSize, sps):
        pVUI = sps.getVuiParameters()
        pHRD = pVUI.getHrdParameters()

        code = 0
        code = self.xReadUvlc(code, 'bp_seq_parameter_set_id')
        sei.m_bpSeqParameterSetId = code
        if not pHRD.getSubPicCpbParamsPresentFlag():
            code = self.xReadFlag(code, 'rap_cpb_params_present_flag')
            sei.m_rapCpbParamsPresentFlag = code

        #read splicing flag and cpb_removal_delay_delta
        code = self.xReadFlag(code, 'concatenation_flag')
        sei.m_concatenationFlag = code
        code = self.xReadCode(pHRD.getCpbRemovalDelayLengthMinus1() + 1,
            code, 'au_cpb_removal_delay_delta_minus1')
        sei.m_auCpbRemovalDelayDelta = code + 1

        if sei.m_rapCpbParamsPresentFlag:
            code = self.xReadCode(pHRD.getCpbRemovalDelayLengthMinus1() + 1,
                code, 'cpb_delay_offset')
            sei.m_cpbDelayOffset = code
            code = self.xReadCode(pHRD.getDpbOutputDelayLengthMinus1() + 1,
                code, 'dpb_delay_offset')
            sei.m_dpbDelayOffset = code

        for nalOrVcl in xrange(2):
            if (nalOrVcl == 0 and pVUI.getNalHrdParametersPresentFlag()) or \
               (nalOrVcl == 1 and pVUI.getVclHrdParametersPresentFlag()):
                for i in xrange(pHRD.getCpbCntMinus1(0)+1):
                    code = self.xReadCode(pHRD.getInitialCpbRemovalDelayLengthMinus1() + 1,
                        code, 'initial_cpb_removal_delay')
                    sei.m_initialCpbRemovalDelay[i][nalOrVcl] = code
                    code = self.xReadCode(pHRD.getInitialCpbRemovalDelayLengthMinus1() + 1,
                        code, 'initial_cpb_removal_delay_offset')
                    sei.m_initialCpbRemovalDelayOffset[i][nalOrVcl] = code
                    if pHRD.getSubPicCpbParamsPresentFlag() or sei.m_rapCpbParamsPresentFlag:
                        code = self.xReadCode(pHRD.getInitialCpbRemovalDelayLengthMinus1() + 1,
                            code, 'initial_alt_cpb_removal_delay')
                        sei.m_initialAltCpbRemovalDelay[i][nalOrVcl] = code
                        code = self.xReadCode(pHRD.getInitialCpbRemovalDelayLengthMinus1() + 1,
                            code, 'initial_alt_cpb_removal_delay_offset')
                        sei.m_initialAltCpbRemovalDelayOffset[i][nalOrVcl] = code
        self.xParseByteAlign()

    def xParseSEIPictureTiming(self, sei, payloadSize, sps):
        code = 0

        pVUI = sps.getVuiParameters()
        pHRD = pVUI.getHrdParameters()

        if pVUI.getFrameFieldInfoPresentFlag():
            code = self.xReadCode(4, code, 'pic_struct')
            self.m_picStruct = code
            code = self.xReadCode(2, code, 'source_scan_type')
            self.m_sourceScanType = code
            code = self.xReadFlag(code, 'duplicate_flag')
            self.m_duplicateFlag = True if code else False

        if pHRD.getCpbDelayPresentFlag():
            code = self.xReadCode(pHRD.getCpbRemovalDelayLengthMinus1() + 1,
                code, 'au_cpb_removal_delay_minus1')
            sei.m_auCpbRemovalDelay = code + 1
            code = self.xReadCode(pHRD.getDpbOutputDelayLengthMinus1() + 1,
                code, 'pic_dpb_output_delay')
            sei.m_picDpbOutputDelay = code

            if pHRD.getSubPicCpbParamsPresentFlag():
                code = self.xReadCode(pHRD.getDpbOutputDelayDuLengthMinus1() + 1,
                    code, 'pic_dpb_output_du_delay')
                sei.m_picDpbOutputDuDelay = code

            if pHRD.getSubPicCpbParamsPresentFlag() or pHRD.getSubPicCpbParamsInPicTimingSEIFlag():
                code = self.xReadUvlc(code, 'num_decoding_units_minus1')
                sei.m_numDecodingUnitsMinus1 = code
                code = self.xReadFlag(code, 'du_common_cpb_removal_delay_flag')
                sei.m_duCommonCpbRemovalDelayFlag = code
                if sei.m_duCommonCpbRemovalDelayFlag:
                    code = self.xReadCode(pVUI.getDuCpbRemovalDelayLengthMinus1() + 1,
                        code, 'du_common_cpb_removal_delay_minus1')
                    sei.m_duCommonCpbRemovalDelayMinus1 = code
                if sei.m_numNalusInDuMinus1 != None:
                    del sei.m_numNalusInDuMinus1
                sei.m_numNalusInDuMinus1 = ArrayUInt(sei.m_numDecodingUnitsMinus1+1)
                if sei.m_duCpbRemovalDelayMinus1 != None:
                    del sei.m_duCpbRemovalDelayMinus1
                sei.m_duCpbRemovalDelayMinus1 = ArrayUInt(sei.m_numDecodingUnitsMinus1+1)

                for i in xrange(sei.m_numDecodingUnitsMinus1 + 1):
                    code = self.xReadUvlc(code, 'num_nalus_in_du_minus1')
                    sei.m_numNalusInDuMinus1[i] = code
                    if not sei.m_duCommonCpbRemovalDelayFlag and i < sei.m_numDecodingUnitsMinus1:
                        code = self.xReadCode(pHRD.getDuCpbRemovalDelayLengthMinus1() + 1,
                            code, 'du_cpb_removal_delay_minus1')
                        sei.m_duCpbRemovalDelayMinus1[i] = code
        self.xParseByteAlign()

    def xParseSEIRecoveryPoint(self, sei, payloadSize):
        iCode = 0
        uiCode = 0
        iCode = self.xReadSvlc(iCode, 'recovery_poc_cnt')
        sei.m_recoveryPocCnt = iCode
        uiCode = self.xReadFlag(uiCode, 'exact_matching_flag')
        sei.m_exactMatchingFlag = uiCode
        uiCode = self.xReadFlag(uiCode, 'broken_link_flag')
        sei.m_brokenLinkFlag = uiCode
        self.xParseByteAlign()

    def xParseSEIFramePacking(self, sei, payloadSize):
        val = 0
        val = self.xReadUvlc(val, 'frame_packing_arrangement_id')
        sei.m_arrangementId = val
        val = self.xReadFlag(val, 'frame_packing_arrangement_cancel_flag')
        sei.m_arrangementCancelFlag = val

        if not sei.m_arrangementCancelFlag:
            val = self.xReadCode(7, val, 'frame_packing_arrangement_type')
            sei.m_arrangementType = val
            assert(sei.m_arrangementType > 2 and sei.m_arrangementType < 6)
            val = self.xReadFlag(val, 'quincunx_sampling_flag')
            sei.m_quincunxSamplingFlag = val

            val = self.xReadCode(6, val, 'content_interpretation_type')
            sei.m_contentInterpretationType = val
            val = self.xReadFlag(val, 'spatial_flipping_flag')
            sei.m_spatialFlippingFlag = val
            val = self.xReadFlag(val, 'frame0_flipped_flag')
            sei.m_frame0FlippedFlag = val
            val = self.xReadFlag(val, 'current_frame_is_frame0_flag')
            sei.m_currentFrameIsFrame0Flag = val
            val = self.xReadFlag(val, 'frame0_self_contained_flag')
            sei.m_frame0SelfContainedFlag = val
            val = self.xReadFlag(val, 'frame1_self_contained_flag')
            sei.m_frame1SelfContainedFlag = val

            if sei.m_quincunxSamplingFlag == 0 and sei.m_arrangementType != 5:
                val = self.xReadCode(4, val, 'frame0_grid_position_x')
                sei.m_frame0GridPositionX = val
                val = self.xReadCode(4, val, 'frame0_grid_position_y')
                sei.m_frame0GridPositionY = val
                val = self.xReadCode(4, val, 'frame1_grid_position_x')
                sei.m_frame1GridPositionX = val
                val = self.xReadCode(4, val, 'frame1_grid_position_y')
                sei.m_frame1GridPositionY = val

            val = self.xReadCode(8, val, 'frame_packing_arrangement_reserved_byte')
            sei.m_arrangementReservedByte = val
            val = self.xReadFlag(val, 'frame_packing_arrangement_persistence_flag')
            sei.m_arrangementPersistenceFlag = True if val else False
        val = self.xReadFlag(val, 'upsampled_aspect_ratio')
        sei.m_upsampledAspectRatio = val

        self.xParseByteAlign()

    def xParseSEIDisplayOrientation(self, sei, payloadSize):
        val = 0
        val = self.xReadFlag(val, 'display_orientation_cancel_flag')
        sei.cancelFlag = val
        if not sei.cancelFlag:
            val = self.xReadFlag(val, 'hor_flip')
            sei.horFlip = val
            val = self.xReadFlag(val, 'ver_flip')
            sei.verFlip = val
            val = self.xReadCode(16, val, 'anticlockwise_rotation')
            sei.anticlockwiseRotation = val
            val = self.xReadFlag(val, 'display_orientation_persistence_flag')
            sei.persistenceFlag = val
        self.xParseByteAlign()

    def xParseSEITemporalLevel0Index(self, sei, payloadSize):
        val = 0
        val = self.xReadCode(8, val, 'tl0_idx')
        sei.tl0Idx = val
        val = self.xReadCode(8, val, 'rap_idx')
        sei.rapIdx = val
        self.xParseByteAlign()

    def xParseSEIGradualDecodingRefreshInfo(self, sei, payloadSize):
        val = 0
        val = self.xReadFlag(val, 'gdr_foreground_flag')
        sei.m_gdrForegroundFlag = 1 if val else 0
        self.xParseByteAlign()

    def xParseByteAlign(self):
        code = 0
        if self.m_pcBitstream.getNumBitsRead() % 8 != 0:
            code = self.xReadFlag(code, 'bit_equal_to_one')
            assert(code == 1)
        while self.m_pcBitstream.getNumBitsRead() % 8 != 0:
            code = self.xReadFlag(code, 'bit_equal_to_zero')
            assert(code == 0)
