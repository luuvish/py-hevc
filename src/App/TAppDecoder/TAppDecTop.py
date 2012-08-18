#!/usr/bin/env python

import sys

from hmpy import InputByteStream, AnnexBStats, byteStreamNALUnit
from hmpy import TDecTop
from hmpy import TVideoIOYuv

from ...Lib.TLibCommon.CommonDef import *
from ...Lib.TLibCommon.TComRom import g_uiBitDepth, g_uiBitIncrement
from .TAppDecCfg import TAppDecCfg

import InputNALUnit
import read


class TAppDecTop(TAppDecCfg):

    def __init__(self):
        super(TAppDecTop, self).__init__(self)
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
        pcListPic = []

        bitstreamFile = open(m_pchBitstreamFile, 'rb')
        if not bitstreamFile:
            sys.stderr.write("\nfailed to open bitstream file `%s' for reading\n" % self.m_pchBitstreamFile)
            sys.exit(False)

        bytestream = InputByteStream(bitstreamFile)

        self._xCreateDecLib()
        self._xInitDecLib()
        self.m_iPOCLastDisplay += self.m_iSkipFrame

        recon_opened = False

        while bitstreamFile:
            location = bitstream.tellg()
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
                    bNewPicture = self.m_cTDecTop.decode(nalu, self.m_iSkipFrame, self.m_iPOCLastDisplay)
                    if bNewPicture:
                        bitstreamFile.clear()
                        bitstreamFile.seek(location - streamoff(3))
                        bytestream.reset()
                    bPreviousPictureDecoded = True
            if bNewPicture or not bitstreamFile:
                self.m_cTDecTop.executeDeblockAndAlf(uiPoc, pcListPic, self.m_iSkipFrame, self.m_iPOCLastDisplay)

            if pcListPic:
                if self.m_pchReconFile and not recon_opened:
                    if self.m_outputBitDepth == 0:
                        self.m_outputBitDepth = g_uiBitDepth + g_uiBitIncrement

                    self.m_cTVideoIOYuvReconFile.open(self.m_pchReconFile, True, self.m_outputBitDepth, g_uiBitDepth + g_uiBitIncrement)
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

            if pcPic.getOutputMark() and not_displayed > pcPic.getSlice(0).getSPS().getNumReorderPics(iId) and pcPic.getPOC() > self.m_iPOCLastDisplay:
                not_displayed -= 1
                if self.m_pchReconFile:
                    self.m_cTVideoIOYuvReconFile.write(pcPic.getPicYuvRec(), sps.getPicCropLeftOffset(), sps.getPicCropRightOffset(), sps.getPicCropTopOffset(), sps.getPicCropBottomOffset())

                self.m_iPOCLastDisplay = pcPic.getPOC()

                if not pcPic.getSlice(0).isReferenced() and pcPic.getReconMark():
                    pcPic.setReconMark(False)
                    pcPic.getPicYuvRec().setBorderExtension(False)
                pcPic.getOutputMark(False)

    def _xFlushOutput(self, pcListPic):
        if not pcListPic:
            return

        for pcPic in pcListPic:
            sps = pcPic.getSlice(0).getSPS()

            if pcPic.getOutputMark():
                if self.m_pchReconFile:
                    self.m_cTVideoIOYuvReconFile.write(pcPic.getPicYuvRec(), sps.getPicCropLeftOffset(), sps.getPicCropRightOffset(), sps.getPicCropTopOffset(), sps.getPicCropBottomOffset())

                self.m_iPOCLastDisplay = pcPic.getPOC()

                if not pcPic.getSlice(0).isReferenced() and pcPic.getReconMark():
                    pcPic.setReconMark(False)
                    pcPic.getPicYuvRec().setBorderExtension(False)
                pcPic.getOutputMark(False)
        pcListPic.clear()
        self.m_iPOCLastDisplay = -MAX_INT
