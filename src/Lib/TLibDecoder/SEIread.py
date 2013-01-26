# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/SEIread.py
    HM 9.1 Python Implementation
"""

import sys

from ... import Trace

from ... import ArrayUChar

from .SyntaxElementParser import SyntaxElementParser

from ..TLibCommon.CommonDef import NAL_UNIT_SEI

from ..TLibCommon.SEI import (
    SEI,
    SEIuserDataUnregistered,
    SEIDecodedPictureHash,
    SEIActiveParameterSets,
    SEIBufferingPeriod,
    SEIPictureTiming,
    SEIRecoveryPoint,
    SEIDisplayOrientation,
    SEITemporalLevel0Index
)


def xTraceSEIHeader():
    Trace.g_hTrace.write("=========== SEI message ===========\n")

def xTraceSEIMessageType(payloadType):
    if payloadType == SEI.DECODED_PICTURE_HASH:
        Trace.g_hTrace.write("=========== Decoded picture hash SEI message ===========\n")
    elif payloadType == SEI.ACTIVE_PARAMETER_SETS:
        Trace.g_hTrace.write("=========== Active Parameter Sets SEI message ===========\n")
    elif payloadType == SEI.USER_DATA_UNREGISTERED:
        Trace.g_hTrace.write("=========== User Data Unregistered SEI message ===========\n")
    elif payloadType == SEI.DISPLAY_ORIENTATION:
        Trace.g_hTrace.write("=========== Display Orientation SEI message ===========\n")
    elif payloadType == SEI.TEMPORAL_LEVEL0_INDEX:
        Trace.g_hTrace.write("=========== Temporal Level Zero Index SEI message ===========\n")
    else:
        Trace.g_hTrace.write("=========== Unknown SEI message ===========\n")


class SEIReader(SyntaxElementParser):

    def parseSEImessage(self, bs, seis, nalUnitType):
        self.setBitstream(bs)

        assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
        while True:
            self.xReadSEImessage(seis, nalUnitType)
            # SEI messages are an integer number of bytes, something has failed
            # in the parsing if bitstream not byte-aligned
            assert(not self.m_pcBitstream.getNumBitsUntilByteAligned())
            if self.m_pcBitstream.getNumBitsLeft() <= 8:
                break

        rbspTrailingBits = 0
        rbspTrailingBits = self.xReadCode(8, rbspTrailingBits, 'rbsp_trailing_bits')
        assert(rbspTrailingBits == 0x80)

    def xReadSEImessage(self, seis, nalUnitType):
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

        if nalUnitType == NAL_UNIT_SEI:
            if payloadType == SEI.USER_DATA_UNREGISTERED:
                seis.user_data_unregistered = SEIuserDataUnregistered()
                self.xParseSEIuserDataUnregistered(seis.user_data_unregistered, payloadSize)
            elif payloadType == SEI.ACTIVE_PARAMETER_SETS:
                seis.active_parameter_sets = SEIActiveParameterSets()
                self.xParseSEIActiveParameterSets(seis.active_parameter_sets, payloadSize)
            elif payloadType == SEI.BUFFERING_PERIOD:
                seis.buffering_period = SEIBufferingPeriod()
                seis.buffering_period.m_sps = seis.m_pSPS
                self.xParseSEIBufferingPeriod(seis.buffering_period, payloadSize)
            elif payloadType == SEI.PICTURE_TIMING:
                seis.picture_timing = SEIPictureTiming()
                seis.picture_timing.m_sps = seis.m_pSPS
                self.xParseSEIPictureTiming(seis.picture_timing, payloadSize)
            elif payloadType == SEI.RECOVERY_POINT:
                seis.recovery_point = SEIRecoveryPoint()
                self.xParseSEIRecoveryPoint(seis.recovery_point, payloadSize)
            elif payloadType == SEI.DISPLAY_ORIENTATION_:
                seis.display_orientation = SEIDisplayOrientation()
                self.xParseSEIDisplayOrientation(seis.display_orientation, payloadSize)
            elif payloadType == SEI.TEMPORAL_LEVEL0_INDEX_:
                seis.temporal_level0_index = SEITemporalLevel0Index()
                self.xParseSEITemporalLevel0Index(seis.temporal_level0_index, payloadSize)
            else:
                for i in xrange(payloadSize):
                    seiByte = 0
                    seiByte = self.xReadCode(8, seiByte, 'unknown prefix SEI payload byte')
                sys.stdout.write("Unknown prefix SEI message (payloadType = %d) was found!\n" % payloadType)
        else:
            if payloadType == SEI.DECODED_PICTURE_HASH:
                seis.picture_digest = SEIDecodedPictureHash()
                self.xParseSEIDecodedPictureHash(seis.picture_digest, payloadSize)
            else:
                for i in xrange(payloadSize):
                    seiByte = 0
                    seiByte = self.xReadCode(8, seiByte, 'unknown suffix SEI payload byte')
                sys.stdout.write("Unknown suffix SEI message (payloadType = %d) was found!\n" % payloadType)

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

        val = self.xReadCode(1, val, 'active_sps_id_present_flag')
        sei.activeSPSIdPresentFlag = val

        if sei.activeSPSIdPresentFlag:
            val = self.xReadUvlc(val, 'active_seq_param_set_id')
            sei.activeSeqParamSetId = val

        uibits = self.m_pcBitstream.getNumBitsUntilByteAligned()

        while uibits:
            val = self.xReadFlag(val, 'alignment_bit')
            uibits -= 1

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

    def xParseSEIBufferingPeriod(self, sei, payloadSize):
        pVUI = sei.m_sps.getVuiParameters()

        code = 0
        code = self.xReadUvlc(code, 'seq_parameter_set_id')
        sei.m_seqParameterSetId = code
        if not pVUI.getSubPicCpbParamsPresentFlag():
            code = self.xReadFlag(code, 'alt_cpb_params_present_flag')
            sei.m_altCpbParamsPresentFlag = code

        for nalOrVcl in xrange(2):
            if (nalOrVcl == 0 and pVUI.getNalHrdParametersPresentFlag()) or \
               (nalOrVcl == 1 and pVUI.getVclHrdParametersPresentFlag()):
                for i in xrange(pVUI.getCpbCntMinus1(0)+1):
                    code = self.xReadCode(pVUI.getInitialCpbRemovalDelayLengthMinus1()+1, code, 'initial_cpb_removal_delay')
                    sei.m_initialCpbRemovalDelay[i][nalOrVcl] = code
                    code = self.xReadCode(pVUI.getInitialCpbRemovalDelayLengthMinus1()+1, code, 'initial_cpb_removal_delay_offset')
                    sei.m_initialCpbRemovalDelayOffset[i][nalOrVcl] = code
                    if pVUI.getSubPicCpbParamsPresentFlag() or sei.m_altCpbParamsPresentFlag:
                        code = self.xReadCode(pVUI.getInitialCpbRemovalDelayLengthMinus1()+1, code, 'initial_alt_cpb_removal_delay')
                        sei.m_initialAltCpbRemovalDelay[i][nalOrVcl] = code
                        code = self.xReadCode(pVUI.getInitialCpbRemovalDelayLengthMinus1()+1, code, 'initial_alt_cpb_removal_delay_offset')
                        sei.m_initialAltCpbRemovalDelayOffset[i][nalOrVcl] = code
        self.xParseByteAlign()

    def xParseSEIPictureTiming(self, sei, payloadSize):
        pVUI = sei.m_sps.getVuiParameters()

        if not pVUI.getNalHrdParametersPresentFlag() and not pVUI.getVclHrdParametersPresentFlag():
            return

        code = 0
        code = self.xReadCode(pVUI.getCpbRemovalDelayLengthMinus1()+1, code, 'au_cpb_removal_delay')
        sei.m_auCpbRemovalDelay = code
        code = self.xReadCode(pVUI.getDpbOutputDelayLengthMinus1()+1, code, 'pic_dpb_output_delay')
        sei.m_picDpbOutputDelay = code

        if sei.m_sps.getVuiParameters().getSubPicCpbParamsPresentFlag():
            code = self.xReadUvlc(code, 'num_decoding_units_minus1')
            sei.m_numDecodingUnitsMinus1 = code
            code = self.xReadFlag(code, 'du_common_cpb_removal_delay_flag')
            sei.m_duCommonCpbRemovalDelayFlag = code
            if sei.m_duCommonCpbRemovalDelayFlag:
                code = self.xReadCode(pVUI.getDuCpbRemovalDelayLengthMinus1()+1, code, 'du_common_cpb_removal_delay_minus1')
                sei.m_duCommonCpbRemovalDelayMinus1 = code
            else:
                if sei.m_numNalusInDuMinus1 != None:
                    del sei.m_numNalusInDuMinus1
                sei.m_numNalusInDuMinus1 = ArrayUInt(sei.m_numDecodingUnitsMinus1+1)
                if sei.m_duCpbRemovalDelayMinus1 != None:
                    del sei.m_duCpbRemovalDelayMinus1
                sei.m_duCpbRemovalDelayMinus1 = ArrayUInt(sei.m_numDecodingUnitsMinus1+1)

                for i in xrange(sei.m_numDecodingUnitsMinus1+1):
                    code = self.xReadUvlc(code, 'num_nalus_in_du_minus1')
                    sei.m_numNalusInDuMinus1[i] = code
                    code = self.xReadCode(pVUI.getDuCpbRemovalDelayLengthMinus1()+1, code, 'du_cpb_removal_delay_minus1')
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
            val = self.xReadUvlc(val, 'display_orientation_repetition_period')
            sei.repetitionPeriod = val
            val = self.xReadFlag(val, 'display_orientation_extension_flag')
            sei.extentionFlag = val
            assert(not sei.extentionFlag)
        self.xParseByteAlign()

    def xParseSEITemporalLevel0Index(self, sei, payloadSize):
        val = 0
        val = self.xReadCode(8, val, 'tl0_idx')
        sei.tl0Idx = val
        val = self.xReadCode(8, val, 'rap_idx')
        sei.rapIdx = val
        self.xParseByteAlign()

    def xParseByteAlign(self):
        code = 0
        if self.m_pcBitstream.getNumBitsRead() % 8 != 0:
            code = self.xReadFlag(code, 'bit_equal_to_one')
            assert(code == 1)
        while self.m_pcBitstream.getNumBitsRead() % 8 != 0:
            code = self.xReadFlag(code, 'bit_equal_to_zero')
            assert(code == 0)
