# -*- coding: utf-8 -*-
"""
    module : src/App/TAppDecoder/TAppDecTop.py
    HM 8.0 Python Implementation
"""

import sys

from ... import InputByteStream, AnnexBStats, byteStreamNALUnit
from ... import InputNALUnit, read
from ... import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
from ... import VectorUint8

from ... import cvar
from ... import TDecTop
from ... import TVideoIOYuv

from .TAppDecCfg import TAppDecCfg

from ...Lib.TLibCommon.CommonDef import (
    MAX_INT,
    NAL_UNIT_CODED_SLICE_BLA,
    NAL_UNIT_CODED_SLICE_BLANT,
    NAL_UNIT_CODED_SLICE_IDR,
    NAL_UNIT_SPS
)


class TAppDecTop(TAppDecCfg):

    def __init__(self):
        super(TAppDecTop, self).__init__()

        self.m_cTDecTop = TDecTop()
        self.m_cTVideoIOYuvReconFile = TVideoIOYuv()
        self.m_abDecFlag = []
        self.m_iPOCLastDisplay = -MAX_INT

    def create(self):
        pass

    def destroy(self):
        if self.m_pchBitstreamFile:
            self.m_pchBitstreamFile = ''
        if self.m_pchReconFile:
            self.m_pchReconFile = ''

    def decode(self):
        uiPOC = 0
        pcListPic = None

        bitstreamFile = istream_open(self.m_pchBitstreamFile, 'rb')
        if istream_not(bitstreamFile):
            sys.stderr.write("\nfailed to open bitstream file `%s' for reading\n" % self.m_pchBitstreamFile)
            sys.exit(False)

        bytestream = InputByteStream(bitstreamFile)

        self._xCreateDecLib()
        self._xInitDecLib()
        self.m_iPOCLastDisplay += self.m_iSkipFrame

        recon_opened = False

        while not istream_not(bitstreamFile):
            location = istream_tellg(bitstreamFile)
            stats = AnnexBStats()
            bPreviousPictureDecoded = False

            nalUnit = VectorUint8()
            nalu = InputNALUnit()
            byteStreamNALUnit(bytestream, nalUnit, stats)

            bNewPicture = False
            if nalUnit.empty():
                sys.stderr.write("Warning: Attempt to decode an empty NAL unit\n")
            else:
                read(nalu, nalUnit)
                if nalu.m_nalUnitType == NAL_UNIT_SPS:
                    assert(nalu.m_temporalId == 0)
                if self.m_iMaxTemporalLayer >= 0 and nalu.m_temporalId > self.m_iMaxTemporalLayer:
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
                        istream_seekg(bitstreamFile, location - 3)
                        bytestream.reset()
                    bPreviousPictureDecoded = True
            if bNewPicture or istream_not(bitstreamFile):
                rpcListPic, uiPOC, self.m_iSkipFrame, self.m_iPOCLastDisplay = \
                    self.m_cTDecTop.executeDeblockAndAlf(uiPOC, self.m_iSkipFrame, self.m_iPOCLastDisplay)
                if rpcListPic:
                    pcListPic = rpcListPic

            if pcListPic:
                if self.m_pchReconFile and not recon_opened:
                    if self.m_outputBitDepth == 0:
                        self.m_outputBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement

                    self.m_cTVideoIOYuvReconFile.open(self.m_pchReconFile, True,
                        self.m_outputBitDepth, cvar.g_uiBitDepth + cvar.g_uiBitIncrement)
                    recon_opened = True
                if bNewPicture and \
                    (nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR or
                     nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLANT or
                     nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA):
                    self._xFlushOutput(pcListPic)
                if bNewPicture:
                    self._xWriteOutput(pcListPic, nalu.m_temporalId)

        self._xFlushOutput(pcListPic)
        self.m_cTDecTop.deletePicBuffer()

        self._xDestroyDecLib()

    def _xCreateDecLib(self):
        self.m_cTDecTop.create()

    def _xDestroyDecLib(self):
        if self.m_pchReconFile:
            self.m_cTVideoIOYuvReconFile.close()

        self.m_cTDecTop.destroy()

    def _xInitDecLib(self):
        self.m_cTDecTop.init()
        self.m_cTDecTop.setPictureDigestEnabled(self.m_pictureDigestEnabled)

    def _xWriteOutput(self, pcListPic, tId):
        not_displayed = 0

        for pcPic in pcListPic:
            if pcPic.getOutputMark() and pcPic.getPOC() > self.m_iPOCLastDisplay:
                not_displayed += 1

        for pcPic in pcListPic:
            sps = pcPic.getSlice(0).getSPS()

            if pcPic.getOutputMark() and \
               not_displayed > pcPic.getSlice(0).getSPS().getNumReorderPics(tId) and \
               pcPic.getPOC() > self.m_iPOCLastDisplay:
                not_displayed -= 1
                if self.m_pchReconFile:
                    self.m_cTVideoIOYuvReconFile.write(pcPic.getPicYuvRec(),
                        sps.getPicCropLeftOffset(), sps.getPicCropRightOffset(),
                        sps.getPicCropTopOffset(), sps.getPicCropBottomOffset())

                self.m_iPOCLastDisplay = pcPic.getPOC()

                if not pcPic.getSlice(0).isReferenced() and pcPic.getReconMark():
                    pcPic.setReconMark(False)
                    pcPic.getPicYuvRec().setBorderExtension(False)
                pcPic.setOutputMark(False)

    def _xFlushOutput(self, pcListPic):
        if not pcListPic:
            return

        for pcPic in pcListPic:
            sps = pcPic.getSlice(0).getSPS()

            if pcPic.getOutputMark():
                if self.m_pchReconFile:
                    self.m_cTVideoIOYuvReconFile.write(pcPic.getPicYuvRec(),
                        sps.getPicCropLeftOffset(), sps.getPicCropRightOffset(),
                        sps.getPicCropTopOffset(), sps.getPicCropBottomOffset())

                self.m_iPOCLastDisplay = pcPic.getPOC()

                if not pcPic.getSlice(0).isReferenced() and pcPic.getReconMark():
                    pcPic.setReconMark(False)
                    pcPic.getPicYuvRec().setBorderExtension(False)
                pcPic.setOutputMark(False)

            if pcPic:
                pcPic.destroy()
                pcPic = None

        pcListPic.clear()
        self.m_iPOCLastDisplay = -MAX_INT
