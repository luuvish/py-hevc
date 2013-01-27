# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecTop.py
    HM 9.2 Python Implementation
"""

import sys

from ... import ArrayInt
from ... import ParameterSetManagerDecoder
from ... import TComPic
from ... import TComListTComPic
from ... import SEI, SEIMessages
from ... import getSeisByType, extractSeisByType, deleteSEIs
from ... import TComSlice, TComVPS, TComSPS, TComPPS

from ... import cvar
from ... import initROM, destroyROM

from ... import TComPrediction
from ... import TComTrQuant
from ... import TComLoopFilter
from ... import TComSampleAdaptiveOffset

from ... import SEIReader
from ... import TDecBinCABAC
from ... import TDecSbac
from ... import TDecCavlc
from ... import TDecEntropy
from ... import TDecCu
from ... import TDecSlice
from ... import TDecGop

from ..TLibCommon.TypeDef import (
    B_SLICE, REF_PIC_LIST_0, REF_PIC_LIST_1
)

from ..TLibCommon.CommonDef import (
    MAX_INT,
    MAX_TLAYER,
    NAL_UNIT_CODED_SLICE_TRAIL_R,
    NAL_UNIT_CODED_SLICE_TRAIL_N,
    NAL_UNIT_CODED_SLICE_TSA_N,
    NAL_UNIT_CODED_SLICE_TLA,
    NAL_UNIT_CODED_SLICE_STSA_R,
    NAL_UNIT_CODED_SLICE_STSA_N,
    NAL_UNIT_CODED_SLICE_DLP,
    NAL_UNIT_CODED_SLICE_TFD,
    NAL_UNIT_CODED_SLICE_BLA,
    NAL_UNIT_CODED_SLICE_BLANT,
    NAL_UNIT_CODED_SLICE_BLA_N_LP,
    NAL_UNIT_CODED_SLICE_IDR,
    NAL_UNIT_CODED_SLICE_IDR_N_LP,
    NAL_UNIT_CODED_SLICE_CRA,
    NAL_UNIT_VPS,
    NAL_UNIT_SPS,
    NAL_UNIT_PPS,
    NAL_UNIT_SEI,
    NAL_UNIT_SEI_SUFFIX
)


class TDecTop(object):

    warningMessage = False

    def __init__(self):
        self.m_iMaxRefPicNum              = 0

        self.m_pocCRA                     = 0
        self.m_prevRAPisBLA               = False
        self.m_pocRandomAccess            = MAX_INT

        self.m_cListPic                   = TComListTComPic()
        self.m_parameterSetManagerDecoder = ParameterSetManagerDecoder()
        self.m_apcSlicePilot              = None

        self.m_SEIs                       = SEIMessages()

        self.m_cPrediction                = TComPrediction()
        self.m_cTrQuant                   = TComTrQuant()
        self.m_cGopDecoder                = TDecGop()
        self.m_cSliceDecoder              = TDecSlice()
        self.m_cCuDecoder                 = TDecCu()
        self.m_cEntropyDecoder            = TDecEntropy()
        self.m_cCavlcDecoder              = TDecCavlc()
        self.m_cSbacDecoder               = TDecSbac()
        self.m_cBinCABAC                  = TDecBinCABAC()
        self.m_seiReader                  = SEIReader()
        self.m_cLoopFilter                = TComLoopFilter()
        self.m_cSAO                       = TComSampleAdaptiveOffset()

        self.m_pcPic                      = None
        self.m_uiSliceIdx                 = 0
        self.m_prevPOC                    = MAX_INT
        self.m_bFirstSliceInPicture       = True
        self.m_bFirstSliceInSequence      = True

    def isSkipPictureForBLA(self, iPOCLastDisplay):
        if self.m_prevRAPisBLA and \
           self.m_apcSlicePilot.getPOC() < self.m_pocCRA and \
           self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_TFD:
            iPOCLastDisplay += 1
            return True, iPOCLastDisplay
        return False, iPOCLastDisplay

    def isRandomAccessSkipPicture(self, iSkipFrame, iPOCLastDisplay):
        if iSkipFrame:
            iSkipFrame -= 1 # decrement the counter
            return True, iSkipFrame, iPOCLastDisplay
        # start of random access point, m_pocRandomAccess has not been set yet.
        elif self.m_pocRandomAccess == MAX_INT:
            if self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_CRA or \
               self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA or \
               self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA_N_LP or \
               self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT:
                # set the POC random access since we need to skip the reordered pictures in the case of CRA/CRANT/BLA/BLANT.
                self.m_pocRandomAccess = self.m_apcSlicePilot.getPOC()
            elif self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_IDR or \
                 self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_IDR_N_LP:
                self.m_pocRandomAccess = -MAX_INT; # no need to skip the reordered pictures in IDR, they are decodable.
            else:
                if not TDecTop.warningMessage:
                    sys.stdout.write("\nWarning: this is not a valid random access point and the data is discarded until the first CRA picture")
                    TDecTop.warningMessage = True
                return True, iSkipFrame, iPOCLastDisplay
        # skip the reordered pictures, if necessary
        elif self.m_apcSlicePilot.getPOC() < self.m_pocRandomAccess and \
             self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_TFD:
            iPOCLastDisplay += 1
            return True, iSkipFrame, iPOCLastDisplay
        # if we reach here, then the picture is not skipped.
        return False, iSkipFrame, iPOCLastDisplay

    def create(self):
        self.m_cGopDecoder.create()
        self.m_apcSlicePilot = TComSlice()
        self.m_apcSlicePilot.thisown = False
        self.m_uiSliceIdx = 0

    def destroy(self):
        self.m_cGopDecoder.destroy()

        self.m_apcSlicePilot.thisown = True
        del self.m_apcSlicePilot
        self.m_apcSlicePilot = None

        self.m_cSliceDecoder.destroy()

    def setDecodedPictureHashSEIEnabled(self, enabled):
        self.m_cGopDecoder.setDecodedPictureHashSEIEnabled(enabled)

    def init(self):
        # initialize ROM
        initROM()
        self.m_cGopDecoder.init(
            self.m_cEntropyDecoder, self.m_cSbacDecoder, self.m_cBinCABAC, self.m_cCavlcDecoder,
            self.m_cSliceDecoder, self.m_cLoopFilter, self.m_cSAO)
        self.m_cSliceDecoder.init(self.m_cEntropyDecoder, self.m_cCuDecoder)
        self.m_cEntropyDecoder.init(self.m_cPrediction)

    def decode(self, nalu, iSkipFrame, iPOCLastDisplay):
        # Initialize entropy decoder
        self.m_cEntropyDecoder.setEntropyDecoder(self.m_cCavlcDecoder)
        self.m_cEntropyDecoder.setBitstream(nalu.m_Bitstream)

        if nalu.m_nalUnitType == NAL_UNIT_VPS:
            self.xDecodeVPS()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_SPS:
            self.xDecodeSPS()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_PPS:
            self.xDecodePPS()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_SEI or \
             nalu.m_nalUnitType == NAL_UNIT_SEI_SUFFIX:
            self.xDecodeSEI(nalu.m_Bitstream, nalu.m_nalUnitType)
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TRAIL_R or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TRAIL_N or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TLA or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TSA_N or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_STSA_R or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_STSA_N or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLANT or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA_N_LP or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR_N_LP or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_CRA or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_DLP or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TFD:
            return self.xDecodeSlice(nalu, iSkipFrame, iPOCLastDisplay)

        else:
            assert(True)

        return False, iSkipFrame, iPOCLastDisplay

    def deletePicBuffer(self):
        for pcPic in self.m_cListPic:
            pcPic.destroy()

            pcPic.thisown = True
            del pcPic

        self.m_cSAO.destroy()
        self.m_cLoopFilter.destroy()

        # destroy ROM
        destroyROM()

    def executeLoopFilters(self, poc):
        if not self.m_pcPic:
            # nothing to deblock
            return None, poc

        rpcListPic = None
        pcPic = self.m_pcPic

        # Execute Deblock + Cleanup
        self.m_cGopDecoder.filterPicture(pcPic)

        TComSlice.sortPicList(self.m_cListPic) # sorting for application output
        poc = pcPic.getSlice(self.m_uiSliceIdx-1).getPOC()
        rpcListPic = self.m_cListPic
        self.m_cCuDecoder.destroy()
        self.m_bFirstSliceInPicture = True

        return rpcListPic, poc

    def xGetNewPicBuffer(self, pcSlice, rpcPic):
        numReorderPics = ArrayInt(MAX_TLAYER)
        conformanceWindow = pcSlice.getSPS().getConformanceWindow()

        for temporalLayer in xrange(MAX_TLAYER):
            numReorderPics[temporalLayer] = pcSlice.getSPS().getNumReorderPics(temporalLayer)

        self.m_iMaxRefPicNum = pcSlice.getSPS().getMaxDecPicBuffering(pcSlice.getTLayer()) + \
                               pcSlice.getSPS().getNumReorderPics(pcSlice.getTLayer()) + 1
                               # +1 to have space for the picture currently being decoded
        if self.m_cListPic.size() < self.m_iMaxRefPicNum:
            rpcPic = TComPic(); rpcPic.thisown = False

            rpcPic.create(pcSlice.getSPS().getPicWidthInLumaSamples(),
                          pcSlice.getSPS().getPicHeightInLumaSamples(),
                          cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth,
                          conformanceWindow, numReorderPics.cast(), True)
            rpcPic.getPicSym().allocSaoParam(self.m_cSAO)
            self.m_cListPic.pushBack(rpcPic)

            return rpcPic

        bBufferInAvailable = False
        for rpcPic in self.m_cListPic:
            if rpcPic.getReconMark() == False and rpcPic.getOutputMark() == False:
                rpcPic.setOutputMark(False)
                bBufferInAvailable = True
                break

            if rpcPic.getSlice(0).isReferenced() == False and rpcPic.getOutputMark() == False:
                rpcPic.setOutputMark(False)
                rpcPic.setReconMark(False)
                rpcPic.getPicYuvRec().setBorderExtension(False)
                bBufferInAvailable = True
                break

        if not bBufferInAvailable:
            # There is no room for this picture, either because of faulty encoder or dropped NAL. Extend the buffer.
            self.m_iMaxRefPicNum += 1
            rpcPic = TComPic(); rpcPic.thisown = False
            self.m_cListPic.pushBack(rpcPic)
        rpcPic.destroy()
        rpcPic.create(pcSlice.getSPS().getPicWidthInLumaSamples(),
                      pcSlice.getSPS().getPicHeightInLumaSamples(),
                      cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth,
                      conformanceWindow, numReorderPics.cast(), True)
        rpcPic.getPicSym().allocSaoParam(self.m_cSAO)

        return rpcPic

    def xCreateLostPicture(self, iLostPoc):
        sys.stdout.write("\ninserting lost poc : %d\n" % iLostPoc)
        cFillSlice = TComSlice()
        cFillSlice.setSPS(self.m_parameterSetManagerDecoder.getFirstSPS())
        cFillSlice.setPPS(self.m_parameterSetManagerDecoder.getFirstPPS())
        cFillSlice.initSlice()
        cFillPic = None
        cFillPic = self.xGetNewPicBuffer(cFillSlice, cFillPic)
        cFillPic.getSlice(0).setSPS(self.m_parameterSetManagerDecoder.getFirstSPS())
        cFillPic.getSlice(0).setPPS(self.m_parameterSetManagerDecoder.getFirstPPS())
        cFillPic.getSlice(0).initSlice()

        closestPoc = 1000000
        for rpcPic in self.m_cListPic:
            if abs(rpcPic.getPicSym().getSlice(0).getPOC() - iLostPoc) < closestPoc and \
               abs(rpcPic.getPicSym().getSlice(0).getPOC() - iLostPoc) != 0 and \
               rpcPic.getPicSym().getSlice(0).getPOC() != self.m_apcSlicePilot.getPOC():
                closestPoc = abs(rpcPic.getPicSym().getSlice(0).getPOC() - iLostPoc)
        for rpcPic in self.m_cListPic:
            if abs(rpcPic.getPicSym().getSlice(0).getPOC() - iLostPoc) == closestPoc and \
               rpcPic.getPicSym().getSlice(0).getPOC() != self.m_apcSlicePilot.getPOC():
                sys.stdout.write("copying picture %d to %d (%d)\n" %
                    (rpcPic.getPicSym().getSlice(0).getPOC(), iLostPoc, self.m_apcSlicePilot.getPOC()))
                rpcPic.getPicYuvRec().copyToPic(cFillPic.getPicYuvRec())
                break
        cFillPic.setCurrSliceIdx(0)
        for i in xrange(cFillPic.getNumCUsInFrame()):
            cFillPic.getCU(i).initCU(cFillPic, i)
        cFillPic.getSlice(0).setReferenced(True)
        cFillPic.getSlice(0).setPOC(iLostPoc)
        cFillPic.setReconMark(True)
        cFillPic.setOutputMark(True)
        if self.m_pocRandomAccess == MAX_INT:
            self.m_pocRandomAccess = iLostPoc

    def xActiveParameterSets(self):
        self.m_parameterSetManagerDecoder.applyPrefetchedPS()

        pps = self.m_parameterSetManagerDecoder.getPPS(self.m_apcSlicePilot.getPPSId())
        assert(pps)

        sps = self.m_parameterSetManagerDecoder.getSPS(pps.getSPSId())
        assert(sps)

        if self.m_parameterSetManagerDecoder.activatePPS(
            self.m_apcSlicePilot.getPPSId(), self.m_apcSlicePilot.getIdrPicFlag()) == False:
            sys.stdout.write("Parameter set activation failed!")
            assert(False)

        self.m_apcSlicePilot.setPPS(pps)
        self.m_apcSlicePilot.setSPS(sps)
        pps.setSPS(sps)
        pps.setNumSubstreams(
            (sps.getPicHeightInLumaSamples() + sps.getMaxCUHeight() - 1) / sps.getMaxCUHeight() *
            (pps.getNumColumnsMinus1() + 1) if pps.getEntropyCodingSyncEnabledFlag() else 1)
        pps.setMinCuDQPSize(sps.getMaxCUWidth() >> pps.getMaxCuDQPDepth())

        for i in xrange(sps.getMaxCUDepth() - cvar.g_uiAddCUDepth):
            sps.setAMPAcc(i, sps.getUseAMP())

        for i in xrange(sps.getMaxCUDepth() - cvar.g_uiAddCUDepth, sps.getMaxCUDepth()):
            sps.setAMPAcc(i, 0)

        self.m_cSAO.destroy()
        self.m_cSAO.create(
            sps.getPicWidthInLumaSamples(), sps.getPicHeightInLumaSamples(),
            cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight)
        self.m_cLoopFilter.create(cvar.g_uiMaxCUDepth)

    def xDecodeSlice(self, nalu, iSkipFrame, iPOCLastDisplay):
        pcPic = self.m_pcPic
        self.m_apcSlicePilot.initSlice()

        if self.m_bFirstSliceInPicture:
            self.m_uiSliceIdx = 0
        self.m_apcSlicePilot.setSliceIdx(self.m_uiSliceIdx)
        if not self.m_bFirstSliceInPicture:
            self.m_apcSlicePilot.copySliceInfo(pcPic.getPicSym().getSlice(self.m_uiSliceIdx-1))

        self.m_apcSlicePilot.setNalUnitType(nalu.m_nalUnitType)
        if self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_TRAIL_N or \
           self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_TSA_N or \
           self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_STSA_N:
            self.m_apcSlicePilot.setTemporalLayerNonReferenceFlag(True)
        self.m_apcSlicePilot.setReferenced(True) # Putting this as true ensures that picture is referenced the first time it is in an RPS
        self.m_apcSlicePilot.setTLayerInfo(nalu.m_temporalId)

        self.m_cEntropyDecoder.decodeSliceHeader(self.m_apcSlicePilot, self.m_parameterSetManagerDecoder)
        # exit when a new picture is found
        if self.m_apcSlicePilot.isNextSlice() and \
           self.m_apcSlicePilot.getPOC() != self.m_prevPOC and \
           not self.m_bFirstSliceInSequence:
            if self.m_prevPOC >= self.m_pocRandomAccess:
                self.m_prevPOC = self.m_apcSlicePilot.getPOC()
                return True, iSkipFrame, iPOCLastDisplay
            self.m_prevPOC = self.m_apcSlicePilot.getPOC()
        # actual decoding starts here
        self.xActiveParameterSets()

        if self.m_apcSlicePilot.isNextSlice():
            self.m_prevPOC = self.m_apcSlicePilot.getPOC()
        self.m_bFirstSliceInSequence = False
        if self.m_apcSlicePilot.isNextSlice():
            # Skip pictures due to random access
            ret, iSkipFrame, iPOCLastDisplay = \
                self.isRandomAccessSkipPicture(iSkipFrame, iPOCLastDisplay)
            if ret:
                return False, iSkipFrame, iPOCLastDisplay
            # Skip TFD pictures associated with BLA/BLANT pictures
            ret, iPOCLastDisplay = self.isSkipPictureForBLA(iPOCLastDisplay)
            if ret:
                return False, iSkipFrame, iPOCLastDisplay
        # detect lost reference picture and insert copy of earlier frame.
        lostPoc = 0
        while True:
            lostPoc = self.m_apcSlicePilot.checkThatAllRefPicsAreAvailable(
                self.m_cListPic, self.m_apcSlicePilot.getRPS(),
                True, self.m_pocRandomAccess)
            if lostPoc <= 0:
                break
            self.xCreateLostPicture(lostPoc-1)
        if self.m_bFirstSliceInPicture:
            # Buffer initialize for prediction.
            self.m_cPrediction.initTempBuff()
            self.m_apcSlicePilot.applyReferencePictureSet(self.m_cListPic, self.m_apcSlicePilot.getRPS())
            # Get a new picture buffer
            pcPic = self.m_pcPic = self.xGetNewPicBuffer(self.m_apcSlicePilot, pcPic)

            # transfer any SEI messages that have been received to the picture
            pcPic.setSEIs(self.m_SEIs)
            self.m_SEIs.clear()

            # Recursive structure
            self.m_cCuDecoder.create(cvar.g_uiMaxCUDepth, cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight)
            self.m_cCuDecoder.init(self.m_cEntropyDecoder, self.m_cTrQuant, self.m_cPrediction)
            self.m_cTrQuant.init(cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, self.m_apcSlicePilot.getSPS().getMaxTrSize())

            self.m_cSliceDecoder.create()
        else:
            # Check if any new SEI has arrived
            if not self.m_SEIs.empty():
                # Currently only decoding Unit SEI message occurring between VCL NALUs copied
                picSEI = pcPic.getSEIs()
                decodingUnitInfos = extractSeisByType(self.m_SEIs, SEI.DECODING_UNIT_INFO)
                picSEI.insert(picSEI.end(), decodingUnitInfos.begin(), decodingUnitInfos.end())
                deleteSEIs(self.m_SEIs)

        # Set picture slice pointer
        pcSlice = self.m_apcSlicePilot
        bNextSlice = pcSlice.isNextSlice()

        # set NumColumnsMins1 and NumRowsMinus1
        pcPic.getPicSym().setNumColumnsMinus1(pcSlice.getPPS().getNumColumnsMinus1())
        pcPic.getPicSym().setNumRowsMinus1(pcSlice.getPPS().getNumRowsMinus1())

        # create the TComTileArray
        pcPic.getPicSym().xCreateTComTileArray()

        if pcSlice.getPPS().getUniformSpacingFlag():
            # set the width for each tile
            for j in xrange(pcPic.getPicSym().getNumRowsMinus1()+1):
                for p in xrange(pcPic.getPicSym().getNumColumnsMinus1()+1):
                    pcPic.getPicSym().getTComTile(j * (pcPic.getPicSym().getNumColumnsMinus1()+1) + p).setTileWidth(
                        (p+1)*pcPic.getPicSym().getFrameWidthInCU()/(pcPic.getPicSym().getNumColumnsMinus1()+1) -
                        p*pcPic.getPicSym().getFrameWidthInCU()/(pcPic.getPicSym().getNumColumnsMinus1()+1))

            # set the height for each tile
            for j in xrange(pcPic.getPicSym().getNumColumnsMinus1()+1):
                for p in xrange(pcPic.getPicSym().getNumRowsMinus1()+1):
                    pcPic.getPicSym().getTComTile(p * (pcPic.getPicSym().getNumColumnsMinus1()+1) + j).setTileHeight(
                        (p+1)*pcPic.getPicSym().getFrameHeightInCU()/(pcPic.getPicSym().getNumRowsMinus1()+1) -
                        p*pcPic.getPicSym().getFrameHeightInCU()/(pcPic.getPicSym().getNumRowsMinus1()+1))
        else:
            # set the width for each tile
            for j in xrange(pcSlice.getPPS().getNumRowsMinus1()+1):
                uiCummulativeTileWidth = 0
                for p in xrange(pcSlice.getPPS().getNumColumnsMinus1()):
                    pcPic.getPicSym().getTComTile(j * (pcSlice.getPPS().getNumColumnsMinus1()+1) + p).setTileWidth(
                        pcSlice.getPPS().getColumnWidth(p))
                    uiCummulativeTileWidth += pcSlice.getPPS().getColumnWidth(p)
                p = pcSlice.getPPS().getNumColumnsMinus1()
                pcPic.getPicSym().getTComTile(j * (pcSlice.getPPS().getNumColumnsMinus1()+1) + p).setTileWidth(
                    pcPic.getPicSym().getFrameWidthInCU() - uiCummulativeTileWidth)

            # set the height for each tile
            for j in xrange(pcSlice.getPPS().getNumColumnsMinus1()+1):
                uiCummulativeTileHeight = 0
                for p in xrange(pcSlice.getPPS().getNumRowsMinus1()):
                    pcPic.getPicSym().getTComTile(p * (pcSlice.getPPS().getNumColumnsMinus1()+1) + j).setTileHeight(
                        pcSlice.getPPS().getRowHeight(p))
                    uiCummulativeTileHeight += pcSlice.getPPS().getRowHeight(p)
                p = pcSlice.getPPS().getNumRowsMinus1()
                pcPic.getPicSym().getTComTile(p * (pcSlice.getPPS().getNumColumnsMinus1()+1) + j).setTileHeight(
                    pcPic.getPicSym().getFrameHeightInCU() - uiCummulativeTileHeight)

        pcPic.getPicSym().xInitTiles()

        # generate the Coding Order Map and Inverse Coding Order Map
        uiEncCUAddr = 0
        for i in xrange(pcPic.getPicSym().getNumberOfCUsInFrame()):
            pcPic.getPicSym().setCUOrderMap(i, uiEncCUAddr)
            pcPic.getPicSym().setInverseCUOrderMap(uiEncCUAddr, i)
            uiEncCUAddr = pcPic.getPicSym().xCalculateNxtCUAddr(uiEncCUAddr)
        pcPic.getPicSym().setCUOrderMap(pcPic.getPicSym().getNumberOfCUsInFrame(),
                                        pcPic.getPicSym().getNumberOfCUsInFrame())
        pcPic.getPicSym().setInverseCUOrderMap(pcPic.getPicSym().getNumberOfCUsInFrame(),
                                               pcPic.getPicSym().getNumberOfCUsInFrame())

        # convert the start and end CU addresses of the slice and dependent slice into encoding order
        pcSlice.setSliceSegmentCurStartCUAddr(
            pcPic.getPicSym().getPicSCUEncOrder(pcSlice.getSliceSegmentCurStartCUAddr()))
        pcSlice.setSliceSegmentCurEndCUAddr(
            pcPic.getPicSym().getPicSCUEncOrder(pcSlice.getSliceSegmentCurEndCUAddr()))
        if pcSlice.isNextSlice():
            pcSlice.setSliceCurStartCUAddr(
                pcPic.getPicSym().getPicSCUEncOrder(pcSlice.getSliceCurStartCUAddr()))
            pcSlice.setSliceCurEndCUAddr(
                pcPic.getPicSym().getPicSCUEncOrder(pcSlice.getSliceCurEndCUAddr()))

        if self.m_bFirstSliceInPicture:
            if pcPic.getNumAllocatedSlice() != 1:
                pcPic.clearSliceBuffer()
        else:
            pcPic.allocateNewSlice()
        assert(pcPic.getNumAllocatedSlice() == (self.m_uiSliceIdx+1))
        self.m_apcSlicePilot = pcPic.getPicSym().getSlice(self.m_uiSliceIdx)
        pcPic.getPicSym().setSlice(pcSlice, self.m_uiSliceIdx)

        pcPic.setTLayer(nalu.m_temporalId)

        if bNextSlice:
            self.m_pocCRA, self.m_prevRAPisBLA = pcSlice.checkCRA(pcSlice.getRPS(), self.m_pocCRA, self.m_prevRAPisBLA)
            # Set reference list
            pcSlice.setRefPicList(self.m_cListPic)

            # For generalized B
            # note: maybe not existed case (always L0 is copied to L1 if L1 is empty)
            if pcSlice.isInterB() and pcSlice.getNumRefIdx(REF_PIC_LIST_1) == 0:
                iNumRefIdx = pcSlice.getNumRefIdx(REF_PIC_LIST_0)
                pcSlice.setNumRefIdx(REF_PIC_LIST_1, iNumRefIdx)

                for iRefIdx in xrange(iNumRefIdx):
                    pcSlice.setRefIdx(
                        pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx),
                        REF_PIC_LIST_1, iRefIdx)
            if not pcSlice.isIntra():
                bLowDelay = True
                iCurrPOC = pcSlice.getPOC()

                for iRefIdx in xrange(pcSlice.getNumRefIdx(REF_PIC_LIST_0)):
                    if pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx).getPOC() > iCurrPOC:
                        bLowDelay = False
                        break
                if pcSlice.isInterB():
                    for iRefIdx in xrange(pcSlice.getNumRefIdx(REF_PIC_LIST_1)):
                        if pcSlice.getRefPic(REF_PIC_LIST_1, iRefIdx).getPOC() > iCurrPOC:
                            bLowDelay = False
                            break

                pcSlice.setCheckLDC(bLowDelay)

            pcSlice.setRefPOCList()
            pcSlice.setNoBackPredFlag(False)
            if pcSlice.getSliceType() == B_SLICE:
                if pcSlice.getNumRefIdx(0) == pcSlice.getNumRefIdx(1):
                    pcSlice.setNoBackPredFlag(True)
                    for i in xrange(pcSlice.getNumRefIdx(1)):
                        if pcSlice.getRefPOC(1, i) != pcSlice.getRefPOC(0, i):
                            pcSlice.setNoBackPredFlag(False)
                            break

        pcPic.setCurrSliceIdx(self.m_uiSliceIdx)
        if pcSlice.getSPS().getScalingListFlag():
            pcSlice.setScalingList(pcSlice.getSPS().getScalingList())
            if pcSlice.getPPS().getScalingListPresentFlag():
                pcSlice.setScalingList(pcSlice.getPPS().getScalingList())
            pcSlice.getScalingList().setUseTransformSkip(pcSlice.getPPS().getUseTransformSkip())
            if not pcSlice.getPPS().getScalingListPresentFlag() and \
               not pcSlice.getSPS().getScalingListPresentFlag():
                pcSlice.setDefaultScalingList()
            self.m_cTrQuant.setScalingListDec(pcSlice.getScalingList())
            self.m_cTrQuant.setUseScalingList(True)
        else:
            self.m_cTrQuant.setFlatScalingList()
            self.m_cTrQuant.setUseScalingList(False)

        # Decode a picture
        self.m_cGopDecoder.decompressSlice(nalu.m_Bitstream, pcPic)

        self.m_bFirstSliceInPicture = False
        self.m_uiSliceIdx += 1 

        return False, iSkipFrame, iPOCLastDisplay

    def xDecodeVPS(self):
        vps = TComVPS(); vps.thisown = False
        self.m_cEntropyDecoder.decodeVPS(vps)
        self.m_parameterSetManagerDecoder.storePrefetchedVPS(vps)

    def xDecodeSPS(self):
        sps = TComSPS(); sps.thisown = False
        self.m_cEntropyDecoder.decodeSPS(sps)
        self.m_parameterSetManagerDecoder.storePrefetchedSPS(sps)

    def xDecodePPS(self):
        pps = TComPPS(); pps.thisown = False
        self.m_cEntropyDecoder.decodePPS(pps)
        self.m_parameterSetManagerDecoder.storePrefetchedPPS(pps)

        if pps.getDependentSliceSegmentsEnabledFlag():
            NumCtx = 2 if pps.getEntropyCodingSyncEnabledFlag() else 1
            self.m_cSliceDecoder.initCtxMem(NumCtx)
            for st in xrange(NumCtx):
                ctx = TDecSbac(); ctx.thisown = False
                ctx.init(self.m_cBinCABAC)
                self.m_cSliceDecoder.setCtxMem(ctx, st)

    def xDecodeSEI(self, bs, nalUnitType):
        if nalUnitType == NAL_UNIT_SEI_SUFFIX:
            self.m_seiReader.parseSEImessage(
                bs, self.m_pcPic.getSEIs(), nalUnitType,
                self.m_parameterSetManagerDecoder.getActiveSPS())
        else:
            self.m_seiReader.parseSEImessage(
                bs, self.m_SEIs, nalUnitType,
                self.m_parameterSetManagerDecoder.getActiveSPS())
            activeParamSets = getSeisByType(self.m_SEIs, SEI.ACTIVE_PARAMETER_SETS)
            if activeParamSets.size() > 0:
                seiAps = activeParamSets.front()
                self.m_parameterSetManagerDecoder.applyPrefetchedPS()
                if not self.m_parameterSetManagerDecoder.activateSPSWithSEI(seiAps.activeSeqParamSetId[0]):
                    sys.stdout.write("Warning SPS activation with Active parameter set SEI failed")
