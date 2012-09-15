# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecTop.py
    HM 8.0 Python Implementation
"""

import sys

from ... import TComPic
from ... import ParameterSetManagerDecoder
from ... import TComListTComPic
from ... import TComSlice
from ... import SEImessages
from ... import TComVPS, TComSPS, TComPPS

from ... import cvar
from ... import initROM, destroyROM

from ... import TComPrediction
from ... import TComTrQuant
from ... import TComLoopFilter
from ... import TComSampleAdaptiveOffset

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
    NAL_UNIT_CODED_SLICE,
    NAL_UNIT_CODED_SLICE_TFD,
    NAL_UNIT_CODED_SLICE_TLA,
    NAL_UNIT_CODED_SLICE_CRA,
    NAL_UNIT_CODED_SLICE_CRANT,
    NAL_UNIT_CODED_SLICE_BLA,
    NAL_UNIT_CODED_SLICE_BLANT,
    NAL_UNIT_CODED_SLICE_IDR,
    NAL_UNIT_VPS,
    NAL_UNIT_SPS,
    NAL_UNIT_PPS,
    NAL_UNIT_SEI
)


warningMessage = False

class TDecTop(object):

    def __init__(self):
        self.m_iGopSize = 0
        self.m_bGopSizeSet = False
        self.m_iMaxRefPicNum = 0

        self.m_bRefreshPending = False
        self.m_pocCRA = 0
        self.m_prevRAPisBLA = False
        self.m_pocRandomAccess = MAX_INT

        self.m_cListPic = TComListTComPic()
        self.m_parameterSetManagerDecoder = ParameterSetManagerDecoder()
        self.m_apcSlicePilot = None

        self.m_SEIs = None

        self.m_cPrediction = TComPrediction()
        self.m_cTrQuant = TComTrQuant()
        self.m_cGopDecoder = TDecGop()
        self.m_cSliceDecoder = TDecSlice()
        self.m_cCuDecoder = TDecCu()
        self.m_cEntropyDecoder = TDecEntropy()
        self.m_cCavlcDecoder = TDecCavlc()
        self.m_cSbacDecoder = TDecSbac()
        self.m_cBinCABAC = TDecBinCABAC()
        self.m_cLoopFilter = TComLoopFilter()
        self.m_cSAO = TComSampleAdaptiveOffset()

        self.m_pcPic = None
        self.m_uiSliceIdx = 0
        self.m_prevPOC = MAX_INT
        self.m_bFirstSliceInPicture = True
        self.m_bFirstSliceInSequence = True

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

    def setPictureDigestEnabled(self, enabled):
        self.m_cGopDecoder.setPictureDigestEnabled(enabled)

    def init(self):
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
            self._xDecodeVPS()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_SPS:
            self._xDecodeSPS()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_PPS:
            self._xDecodePPS()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_SEI:
            self._xDecodeSEI()
            return False, iSkipFrame, iPOCLastDisplay

        elif nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TFD or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_TLA or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_CRA or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_CRANT or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_BLANT or \
             nalu.m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR:
            return self._xDecodeSlice(nalu, iSkipFrame, iPOCLastDisplay)

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

        destroyROM()

    def executeDeblockAndAlf(self, ruiPOC, iSkipFrame, iPOCLastDisplay):
        if not self.m_pcPic:
            return None, ruiPOC, iSkipFrame, iPOCLastDisplay

        rpcListPic = None
        pcPic = self.m_pcPic

        # Execute Deblock and ALF only + Cleanup
        self.m_cGopDecoder.filterPicture(pcPic)

        TComSlice.sortPicList(self.m_cListPic) # sorting for application output
        ruiPOC = pcPic.getSlice(self.m_uiSliceIdx-1).getPOC()
        rpcListPic = self.m_cListPic
        self.m_cCuDecoder.destroy()
        self.m_bFirstSliceInPicture = True

        return rpcListPic, ruiPOC, iSkipFrame, iPOCLastDisplay

    def _isSkipPictureForBLA(self, iPOCLastDisplay):
        if self.m_prevRAPisBLA and \
           self.m_apcSlicePilot.getPOC() < self.m_pocCRA and \
           self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_TFD:
            iPOCLastDisplay += 1
            return True, iPOCLastDisplay
        return False, iPOCLastDisplay

    def _isRandomAccessSkipPicture(self, iSkipFrame, iPOCLastDisplay):
        if iSkipFrame:
            iSkipFrame -= 1
            return True, iSkipFrame, iPOCLastDisplay
        # start of random access point, m_pocRandomAccess has not been set yet.
        elif self.m_pocRandomAccess == MAX_INT:
            if self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_CRA or \
               self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_CRANT or \
               self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLA or \
               self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_BLANT:
                # set the POC random access since we need to skip the reordered pictures in the case of CRA/CRANT/BLA/BLANT.
                self.m_pocRandomAccess = self.m_apcSlicePilot.getPOC()
            elif self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_IDR:
                # no need to skip the reordered pictures in IDR, they are decodable.
                self.m_pocRandomAccess = 0;
            else:
                global warningMessage
                if not warningMessage:
                    sys.stdout.write("\nWarning: this is not a valid random access point and the data is discarded until the first CRA picture")
                    warningMessage = True
                return True, iSkipFrame, iPOCLastDisplay
        # skip the reordered pictures, if necessary
        elif self.m_apcSlicePilot.getPOC() < self.m_pocRandomAccess and \
             self.m_apcSlicePilot.getNalUnitType() == NAL_UNIT_CODED_SLICE_TFD:
            iPOCLastDisplay += 1
            return True, iSkipFrame, iPOCLastDisplay
        # if we reach here, then the picture is not skipped.
        return False, iSkipFrame, iPOCLastDisplay

    def _xGetNewPicBuffer(self, pcSlice, rpcPic):
        self._xUpdateGopSize(pcSlice)

        self.m_iMaxRefPicNum = pcSlice.getSPS().getMaxDecPicBuffering(pcSlice.getTLayer()) + \
                               pcSlice.getSPS().getNumReorderPics(pcSlice.getTLayer()) + 1
                               # +1 to have space for the picture currently being decoded
        if self.m_cListPic.size() < self.m_iMaxRefPicNum:
            rpcPic = TComPic(); rpcPic.thisown = False

            rpcPic.create(pcSlice.getSPS().getPicWidthInLumaSamples(),
                          pcSlice.getSPS().getPicHeightInLumaSamples(),
                          cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth, True)
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
                      cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth, True)
        rpcPic.getPicSym().allocSaoParam(self.m_cSAO)

        return rpcPic

    def _xUpdateGopSize(self, pcSlice):
        if not pcSlice.isIntra() and not self.m_bGopSizeSet:
            self.m_iGopSize = pcSlice.getPOC()
            self.m_bGopSizeSet = True

            self.m_cGopDecoder.setGopSize(self.m_iGopSize)

    def _xCreateLostPicture(self, iLostPoc):
        sys.stdout.write("\ninserting lost poc : %d\n" % iLostPoc)
        cFillSlice = TComSlice()
        cFillSlice.setSPS(self.m_parameterSetManagerDecoder.getFirstSPS())
        cFillSlice.setPPS(self.m_parameterSetManagerDecoder.getFirstPPS())
        cFillSlice.initSlice()
        cFillSlice.initTiles()
        cFillPic = None
        cFillPic = self._xGetNewPicBuffer(cFillSlice, cFillPic)
        cFillPic.getSlice(0).setSPS(self.m_parameterSetManagerDecoder.getFirstSPS())
        cFillPic.getSlice(0).setPPS(self.m_parameterSetManagerDecoder.getFirstPPS())
        cFillPic.getSlice(0).initSlice()
        cFillPic.getSlice(0).initTiles()

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

    def _xActiveParameterSets(self):
        self.m_parameterSetManagerDecoder.applyPrefetchedPS()

        pps = self.m_parameterSetManagerDecoder.getPPS(self.m_apcSlicePilot.getPPSId())
        assert(pps)

        sps = self.m_parameterSetManagerDecoder.getSPS(pps.getSPSId())
        assert(sps)

        self.m_apcSlicePilot.setPPS(pps)
        self.m_apcSlicePilot.setSPS(sps)
        pps.setSPS(sps)
        pps.setNumSubstreams(
            (sps.getPicHeightInLumaSamples() + sps.getMaxCUHeight() - 1) / sps.getMaxCUHeight() *
            (pps.getNumColumnsMinus1() + 1) if pps.getTilesOrEntropyCodingSyncIdc() == 2 else 1)
        if pps.getDependentSlicesEnabledFlag():
            pps.setNumSubstreams(1)
        pps.setMinCuDQPSize(sps.getMaxCUWidth() >> pps.getMaxCuDQPDepth())

        for i in xrange(sps.getMaxCUDepth() - cvar.g_uiAddCUDepth):
            sps.setAMPAcc(i, sps.getUseAMP())
        for i in xrange(sps.getMaxCUDepth() - cvar.g_uiAddCUDepth, sps.getMaxCUDepth()):
            sps.setAMPAcc(i, 0)

        self.m_cSAO.destroy()
        self.m_cSAO.create(sps.getPicWidthInLumaSamples(), sps.getPicHeightInLumaSamples(),
            cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth)
        self.m_cLoopFilter.create(cvar.g_uiMaxCUDepth)

    def _xDecodeSlice(self, nalu, iSkipFrame, iPOCLastDisplay):
        pcPic = self.m_pcPic
        self.m_apcSlicePilot.initSlice()

        self.m_apcSlicePilot.setPPSId(0)
        self.m_apcSlicePilot.setPPS(self.m_parameterSetManagerDecoder.getPrefetchedPPS(0))
        self.m_apcSlicePilot.setSPS(self.m_parameterSetManagerDecoder.getPrefetchedSPS(0))
        self.m_apcSlicePilot.initTiles()

        if self.m_bFirstSliceInPicture:
            self.m_uiSliceIdx = 0
        self.m_apcSlicePilot.setSliceIdx(self.m_uiSliceIdx)
        if not self.m_bFirstSliceInPicture:
            self.m_apcSlicePilot.copySliceInfo(pcPic.getPicSym().getSlice(self.m_uiSliceIdx-1))

        self.m_apcSlicePilot.setNalUnitType(nalu.m_nalUnitType)
        # Putting this as true ensures that picture is referenced the first time it is in an RPS
        self.m_apcSlicePilot.setReferenced(True)
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
        self._xActiveParameterSets()
        self.m_apcSlicePilot.initTiles()

        if self.m_apcSlicePilot.isNextSlice():
            self.m_prevPOC = self.m_apcSlicePilot.getPOC()
        self.m_bFirstSliceInSequence = False
        if self.m_apcSlicePilot.isNextSlice():
            # Skip pictures due to random access
            ret, iSkipFrame, iPOCLastDisplay = \
                self._isRandomAccessSkipPicture(iSkipFrame, iPOCLastDisplay)
            if ret:
                return False, iSkipFrame, iPOCLastDisplay
            # Skip TFD pictures associated with BLA/BLANT pictures
            ret, iPOCLastDisplay = self._isSkipPictureForBLA(iPOCLastDisplay)
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
            self._xCreateLostPicture(lostPoc-1)
        if self.m_bFirstSliceInPicture:
            # Buffer initialize for prediction.
            self.m_cPrediction.initTempBuff()
            self.m_apcSlicePilot.applyReferencePictureSet(self.m_cListPic, self.m_apcSlicePilot.getRPS())
            # Get a new picture buffer
            pcPic = self.m_pcPic = self._xGetNewPicBuffer(self.m_apcSlicePilot, pcPic)

            # transfer any SEI messages that have been received to the picture
            pcPic.setSEIs(self.m_SEIs)
            self.m_SEIs = None

            # Recursive structure
            self.m_cCuDecoder.create(cvar.g_uiMaxCUDepth, cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight)
            self.m_cCuDecoder.init(self.m_cEntropyDecoder, self.m_cTrQuant, self.m_cPrediction)
            self.m_cTrQuant.init(cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, self.m_apcSlicePilot.getSPS().getMaxTrSize())

            self.m_cSliceDecoder.create(self.m_apcSlicePilot,
                self.m_apcSlicePilot.getSPS().getPicWidthInLumaSamples(),
                self.m_apcSlicePilot.getSPS().getPicHeightInLumaSamples(),
                cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight, cvar.g_uiMaxCUDepth)

        # Set picture slice pointer
        pcSlice = self.m_apcSlicePilot
        bNextSlice = pcSlice.isNextSlice()

        # set NumColumnsMins1 and NumRowsMinus1
        pcPic.getPicSym().setNumColumnsMinus1(pcSlice.getPPS().getNumColumnsMinus1())
        pcPic.getPicSym().setNumRowsMinus1(pcSlice.getPPS().getNumRowsMinus1())

        # create the TComTileArray
        pcPic.getPicSym().xCreateTComTileArray()

        if pcSlice.getPPS().getUniformSpacingIdr() == 1:
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
        pcSlice.setDependentSliceCurStartCUAddr(
            pcPic.getPicSym().getPicSCUEncOrder(pcSlice.getDependentSliceCurStartCUAddr()))
        pcSlice.setDependentSliceCurEndCUAddr(
            pcPic.getPicSym().getPicSCUEncOrder(pcSlice.getDependentSliceCurEndCUAddr()))
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
            self.m_pocCRA, self.m_prevRAPisBLA = pcSlice.checkCRA(pcSlice.getRPS(), self.m_pocCRA, self.m_prevRAPisBLA, self.m_cListPic)
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
            if pcSlice.isInterB():
                bLowDelay = True
                iCurrPOC = pcSlice.getPOC()

                for iRefIdx in xrange(pcSlice.getNumRefIdx(REF_PIC_LIST_0)):
                    if pcSlice.getRefPic(REF_PIC_LIST_0, iRefIdx).getPOC() > iCurrPOC:
                        bLowDelay = False
                        break
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
            if pcSlice.getSPS().getScalingListPresentFlag():
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

    def _xDecodeVPS(self):
        vps = TComVPS(); vps.thisown = False
        self.m_cEntropyDecoder.decodeVPS(vps)
        self.m_parameterSetManagerDecoder.storePrefetchedVPS(vps)

    def _xDecodeSPS(self):
        sps = TComSPS(); sps.thisown = False
        self.m_cEntropyDecoder.decodeSPS(sps)
        self.m_parameterSetManagerDecoder.storePrefetchedSPS(sps)

    def _xDecodePPS(self):
        pps = TComPPS(); pps.thisown = False
        self.m_cEntropyDecoder.decodePPS(pps, self.m_parameterSetManagerDecoder)
        self.m_parameterSetManagerDecoder.storePrefetchedPPS(pps)

        self.m_apcSlicePilot.setPPSId(pps.getPPSId())
        self._xActiveParameterSets()
        self.m_apcSlicePilot.initTiles()

    def _xDecodeSEI(self):
        self.m_SEIs = SEImessages(); self.m_SEIs.thisown = False
        self.m_cEntropyDecoder.decodeSEI(self.m_SEIs)
