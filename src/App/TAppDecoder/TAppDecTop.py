# -*- coding: utf-8 -*-
"""
    module : src/App/TAppDecoder/TAppDecTop.py
    HM 9.2 Python Implementation
"""

import sys

from ... import InputByteStream, AnnexBStats, byteStreamNALUnit
from ... import InputNALUnit, read
from ... import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
from ... import VectorUint8

from ... import cvar
from ... import TDecTop
from ... import TVideoIOYuv
from ... import Window

from .TAppDecCfg import TAppDecCfg

from ...Lib.TLibCommon.CommonDef import (
    MAX_GOP,
    MAX_INT,
    NAL_UNIT_CODED_SLICE_BLA,
    NAL_UNIT_CODED_SLICE_BLA_N_LP,
    NAL_UNIT_CODED_SLICE_BLANT,
    NAL_UNIT_CODED_SLICE_IDR,
    NAL_UNIT_CODED_SLICE_IDR_N_LP
)


class TAppDecTop(TAppDecCfg):

    def __init__(self):
        super(TAppDecTop, self).__init__()

        self.m_cTDecTop              = TDecTop()
        self.m_cTVideoIOYuvReconFile = TVideoIOYuv()
        self.m_abDecFlag             = [0] * MAX_GOP
        self.m_iPOCLastDisplay       = -MAX_INT

    def create(self):
        pass

    def destroy(self):
        if self.m_pchBitstreamFile:
            self.m_pchBitstreamFile = ''
        if self.m_pchReconFile:
            self.m_pchReconFile = ''

    def decode(self):
        poc = 0
        pcListPic = None

        bitstreamFile = istream_open(self.m_pchBitstreamFile, 'rb')
        if istream_not(bitstreamFile):
            sys.stderr.write("\nfailed to open bitstream file `%s' for reading\n" % self.m_pchBitstreamFile)
            sys.exit(False)

        bytestream = InputByteStream(bitstreamFile)

        # create & initialize internal classes
        self.xCreateDecLib()
        self.xInitDecLib()
        self.m_iPOCLastDisplay += self.m_iSkipFrame # set the last displayed POC correctly for skip forward.

        # main decoder loop
        recon_opened = False # reconstruction file not yet opened. (must be performed after SPS is seen)

        while not istream_not(bitstreamFile):
            # location serves to work around a design fault in the decoder, whereby
            # the process of reading a new slice that is the first slice of a new frame
            # requires the TDecTop::decode() method to be called again with the same
            # nal unit.
            location = istream_tellg(bitstreamFile)
            stats = AnnexBStats()
            bPreviousPictureDecoded = False

            nalUnit = VectorUint8()
            nalu = InputNALUnit()
            byteStreamNALUnit(bytestream, nalUnit, stats)

            # call actual decoding function
            bNewPicture = False
            if nalUnit.empty():
                # this can happen if the following occur:
                #  - empty input file
                #  - two back-to-back start_code_prefixes
                #  - start_code_prefix immediately followed by EOF
                sys.stderr.write("Warning: Attempt to decode an empty NAL unit\n")
            else:
                read(nalu, nalUnit)
                if self.m_iMaxTemporalLayer >= 0 and nalu.m_temporalId > self.m_iMaxTemporalLayer or \
                   not self.isNaluWithinTargetDecLayerIdSet(nalu):
                    if bPreviousPictureDecoded:
                        bNewPicture = True
                        bPreviousPictureDecoded = False
                    else:
                        bNewPicture = False
                else:
                    bNewPicture, self.m_iSkipFrame, self.m_iPOCLastDisplay = \
                        self.m_cTDecTop.decode(nalu, self.m_iSkipFrame, self.m_iPOCLastDisplay)
                    if bNewPicture:
                        istream_clear(bitstreamFile)
                        # location points to the current nalunit payload[1] due to the
                        # need for the annexB parser to read three extra bytes.
                        # [1] except for the first NAL unit in the file
                        #     (but bNewPicture doesn't happen then)
                        istream_seekg(bitstreamFile, location - 3)
                        bytestream.reset()
                    bPreviousPictureDecoded = True
            if bNewPicture or istream_not(bitstreamFile):
                rpcListPic, poc = self.m_cTDecTop.executeLoopFilters(poc)
                if rpcListPic:
                    pcListPic = rpcListPic

            if pcListPic:
                if self.m_pchReconFile and not recon_opened:
                    if not self.m_outputBitDepthY:
                        self.m_outputBitDepthY = cvar.g_bitDepthY
                    if not self.m_outputBitDepthC:
                        self.m_outputBitDepthC = cvar.g_bitDepthC

                    self.m_cTVideoIOYuvReconFile.open(self.m_pchReconFile, True,
                        self.m_outputBitDepthY, self.m_outputBitDepthC, cvar.g_bitDepthY, cvar.g_bitDepthC)
                    recon_opened = True
                if bNewPicture and \
                    (nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR or
                     nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR_N_LP or
                     nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA_N_LP or
                     nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLANT or
                     nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA):
                    self.xFlushOutput(pcListPic)
                # write reconstruction to file
                if bNewPicture:
                    self.xWriteOutput(pcListPic, nalu.m_temporalId)

        self.xFlushOutput(pcListPic)
        # delete buffers
        self.m_cTDecTop.deletePicBuffer()

        # destroy internal classes
        self.xDestroyDecLib()

    def xCreateDecLib(self):
        # create decoder class
        self.m_cTDecTop.create()

    def xDestroyDecLib(self):
        if self.m_pchReconFile:
            self.m_cTVideoIOYuvReconFile.close()

        # destroy decoder class
        self.m_cTDecTop.destroy()

    def xInitDecLib(self):
        # initialize decoder class
        self.m_cTDecTop.init()
        self.m_cTDecTop.setDecodedPictureHashSEIEnabled(self.m_decodedPictureHashSEIEnabled)

    def xWriteOutput(self, pcListPic, tId):
        not_displayed = 0

        for pcPic in pcListPic:
            if pcPic.getOutputMark() and pcPic.getPOC() > self.m_iPOCLastDisplay:
                not_displayed += 1

        for pcPic in pcListPic:
            if pcPic.getOutputMark() and \
               not_displayed > pcPic.getNumReorderPics(tId) and \
               pcPic.getPOC() > self.m_iPOCLastDisplay:
                # write to file
                not_displayed -= 1
                if self.m_pchReconFile:
                    conf = pcPic.getConformanceWindow()
                    defDisp = pcPic.getSlice(0).getSPS().getVuiParameters().getDefaultDisplayWindow() \
                        if self.m_respectDefDispWindow or not pcPic.getSlice(0).getSPS().getVuiParametersPresentFlag() else Window()
                    self.m_cTVideoIOYuvReconFile.write(pcPic.getPicYuvRec(),
                        conf.getWindowLeftOffset() + defDisp.getWindowLeftOffset(),
                        conf.getWindowRightOffset() + defDisp.getWindowRightOffset(),
                        conf.getWindowTopOffset() + defDisp.getWindowTopOffset(),
                        conf.getWindowBottomOffset() + defDisp.getWindowBottomOffset())

                # update POC of display order
                self.m_iPOCLastDisplay = pcPic.getPOC()

                # erase non-referenced picture in the reference picture list after display
                if not pcPic.getSlice(0).isReferenced() and pcPic.getReconMark():
                    pcPic.setReconMark(False)

                    # mark it should be extended later
                    pcPic.getPicYuvRec().setBorderExtension(False)
                pcPic.setOutputMark(False)

    def xFlushOutput(self, pcListPic):
        if not pcListPic:
            return

        for pcPic in pcListPic:
            if pcPic.getOutputMark():
                # write to file
                if self.m_pchReconFile:
                    conf = pcPic.getConformanceWindow()
                    defDisp = pcPic.getSlice(0).getSPS().getVuiParameters().getDefaultDisplayWindow() \
                        if self.m_respectDefDispWindow or not pcPic.getSlice(0).getSPS().getVuiParametersPresentFlag() else Window()
                    self.m_cTVideoIOYuvReconFile.write(pcPic.getPicYuvRec(),
                        conf.getWindowLeftOffset() + defDisp.getWindowLeftOffset(),
                        conf.getWindowRightOffset() + defDisp.getWindowRightOffset(),
                        conf.getWindowTopOffset() + defDisp.getWindowTopOffset(),
                        conf.getWindowBottomOffset() + defDisp.getWindowBottomOffset())

                # update POC of display order
                self.m_iPOCLastDisplay = pcPic.getPOC()

                # erase non-referenced picture in the reference picture list after display
                if not pcPic.getSlice(0).isReferenced() and pcPic.getReconMark():
                    pcPic.setReconMark(False)

                    # mark it should be extended later
                    pcPic.getPicYuvRec().setBorderExtension(False)
                pcPic.setOutputMark(False)

            if pcPic:
                pcPic.destroy()
                pcPic = None

        pcListPic.clear()
        self.m_iPOCLastDisplay = -MAX_INT

    def isNaluWithinTargetDecLayerIdSet(self, nalu):
        if len(self.m_targetDecLayerIdSet) == 0: # By default, the set is empty, meaning all LayerIds are allowed
            return True
        for it in self.m_targetDecLayerIdSet:
            if nalu.m_reservedZero6Bits == it:
                return True
        return False
