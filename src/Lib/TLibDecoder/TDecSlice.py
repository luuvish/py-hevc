# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecSlice.py
    HM 8.0 Python Implementation
"""

import sys
from time import clock

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import MAX_NUM_VPS, MAX_NUM_SPS, MAX_NUM_PPS
    from swig.hevc import P_SLICE, B_SLICE
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS

    from swig.hevc import ArrayTComInputBitstream, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import ArrayBool_Set, ArrayBool_Get
else:
    sys.path.insert(0, '../../..')
    from swig.hevc import MAX_NUM_VPS, MAX_NUM_SPS, MAX_NUM_PPS
    from swig.hevc import P_SLICE, B_SLICE
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS

    from swig.hevc import ArrayTComInputBitstream, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import ArrayBool_Set, ArrayBool_Get


class TDecSlice(object):

    def __init__(self):
        self.m_pcEntropyDecoder = None
        self.m_pcCuDecoder = None
        self.m_uiCurrSliceIdx = 0

        self.m_pcBufferSbacDecoders = None
        self.m_pcBufferBinCABACs = None
        self.m_pcBufferLowLatSbacDecoders = None
        self.m_pcBufferLowLatBinCABACs = None

    def init(self, pcEntropyDecoder, pcCuDecoder):
        self.m_pcEntropyDecoder = pcEntropyDecoder
        self.m_pcCuDecoder = pcCuDecoder

    def create(self, pcSlice, iWidth, iHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth):
        pass

    def destroy(self):
        if self.m_pcBufferSbacDecoders:
            del self.m_pcBufferSbacDecoders
            self.m_pcBufferSbacDecoders = None
        if self.m_pcBufferBinCABACs:
            del self.m_pcBufferBinCABACs
            self.m_pcBufferBinCABACs = None
        if self.m_pcBufferLowLatSbacDecoders:
            del self.m_pcBufferLowLatSbacDecoders
            self.m_pcBufferLowLatSbacDecoders = None
        if self.m_pcBufferLowLatBinCABACs:
            del self.m_pcBufferLowLatBinCABACs
            self.m_pcBufferLowLatBinCABACs = None

    def decompressSlice(self, pcBitstream, ppcSubstreams, rpcPic, pcSbacDecoder, pcSbacDecoders):
        p = ArrayTComInputBitstream(0)
        p.data = ppcSubstreams
        ppcSubstreams = p
        p = ArrayTDecSbac(0)
        p.data = pcSbacDecoders
        pcSbacDecoders = p

        pcCU = None
        uiIsLast = 0
        iStartCUEncOrder = max(rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getSliceCurStartCUAddr() / rpcPic.getNumPartInCU(),
                               rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getDependentSliceCurStartCUAddr() / rpcPic.getNumPartInCU())
        iStartCUAddr = rpcPic.getPicSym().getCUOrderMap(iStartCUEncOrder)

        # decoder don't need prediction & residual frame buffer
        rpcPic.setPicYuvPred(None)
        rpcPic.setPicYuvResi(None)

        uiTilesAcross = rpcPic.getPicSym().getNumColumnsMinus1() + 1
        pcSlice = rpcPic.getSlice(rpcPic.getCurrSliceIdx())
        iNumSubstreams = pcSlice.getPPS().getNumSubstreams()

        # delete decoders if already allocated in previous slice
        if self.m_pcBufferSbacDecoders:
            del self.m_pcBufferSbacDecoders
        if self.m_pcBufferBinCABACs:
            del self.m_pcBufferBinCABACs
        # allocate new decoders based on tile numbaer
        self.m_pcBufferSbacDecoders = ArrayTDecSbac(uiTilesAcross)
        self.m_pcBufferBinCABACs = ArrayTDecBinCABAC(uiTilesAcross)
        for ui in range(uiTilesAcross):
            self.m_pcBufferSbacDecoders.get(ui).init(self.m_pcBufferBinCABACs.get(ui))
        #save init. state
        for ui in range(uiTilesAcross):
            self.m_pcBufferSbacDecoders.get(ui).load(pcSbacDecoder)

        # free memory if already allocated in previous call
        if self.m_pcBufferLowLatSbacDecoders:
            del self.m_pcBufferLowLatSbacDecoders
        if self.m_pcBufferLowLatBinCABACs:
            del self.m_pcBufferLowLatBinCABACs
        self.m_pcBufferLowLatSbacDecoders = ArrayTDecSbac(uiTilesAcross)
        self.m_pcBufferLowLatBinCABACs = ArrayTDecBinCABAC(uiTilesAcross)
        for ui in range(uiTilesAcross):
            self.m_pcBufferLowLatSbacDecoders.get(ui).init(self.m_pcBufferLowLatBinCABACs.get(ui))
        #save init. state
        for ui in range(uiTilesAcross):
            self.m_pcBufferLowLatSbacDecoders.get(ui).load(pcSbacDecoder)

        uiWidthInLCUs = rpcPic.getPicSym().getFrameWidthInCU()
        uiCol = uiLin = uiSubStrm = 0

        uiTileCol = uiTileStartLCU = 0
        uiTileLCUX = uiTileLCUY = 0
        uiTileWidth = uiTileHeight = 0
        iNumSubstreamsPerTile = 1 # if independent.

        bAllowDependence = False
        if rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getPPS().getDependentSlicesEnabledFlag() and \
           not rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getPPS().getCabacIndependentFlag():
            bAllowDependence = True
        if bAllowDependence:
            if not rpcPic.getSlice(rpcPic.getCurrSliceIdx()).isNextSlice():
                uiTileCol = 0
                if pcSlice.getPPS().getTilesOrEntropyCodingSyncIdx() == 2:
                    self.m_pcBufferSbacDecoders.get(uiTileCol).loadContexts(
                        rpcPic.getSlice(rpcPic.getCurrSliceIdx()-1).getCTXMem_dec(0)) #2.LCU
                pcSbacDecoder.loadContexts(rpcPic.getSlice(rpcPic.getCurrSliceIdx()-1).getCTXMem_dec(1)) # end of depSlice-1
                pcSbacDecoders.get(uiSubStrm).loadContexts(pcSbacDecoder)

        iCUAddr = iStartCUAddr
        while not uiIsLast:
            if iCUAddr >= rpcPic.getNumCUsInFrame():
                break
            pcCU = rpcPic.getCU(iCUAddr)
            pcCU.initCU(rpcPic, iCUAddr)
            uiTileCol = rpcPic.getPicSym().getTileIdxMap(iCUAddr) % \
                (rpcPic.getPicSym().getNumColumnsMinus1()+1) # what column of tiles are we in?
            uiTileStartLCU = rpcPic.getPicSym().getTComTile(rpcPic.getPicSym().getTileIdxMap(iCUAddr)).getFirstCUAddr()
            uiTileLCUX = uiTileStartLCU % uiWidthInLCUs
            uiTileLCUY = uiTileStartLCU / uiWidthInLCUs
            uiTileWidth = rpcPic.getPicSym().getTComTile(rpcPic.getPicSym().getTileIdxMap(iCUAddr)).getTileWidth()
            uiTileHeight = rpcPic.getPicSym().getTComTile(rpcPic.getPicSym().getTileIdxMap(iCUAddr)).getTileHeight()
            uiCol = iCUAddr % uiWidthInLCUs
            uiLin = iCUAddr / uiWidthInLCUs

            # inherit from TR if necessary, select substream to use.
            if (pcSlice.getPPS().getNumSubstreams() > 1) or \
               (bAllowDependence and uiCol == uiTileLCUX and
                pcSlice.getPPS().getTilesOrEntropyCodingSyncIdx() == 2):
                iNumSubstreamsPerTile = iNumSubstreams / rpcPic.getPicSym().getNumTiles()
                uiSubStrm = rpcPic.getPicSym().getTileIdxMap(iCUAddr) * iNumSubstreamsPerTile + \
                            uiLin % iNumSubstreamsPerTile
                self.m_pcEntropyDecoder.setBitstream(ppcSubstreams.get(uiSubStrm))
                # Synchronize cabac probabilities with upper-right LCU if it's available and we're at the start of a line.
                if (pcSlice.getPPS().getNumSubstreams() > 1) or \
                   (bAllowDependence and uiCol == uiTileLCUX and
                    pcSlice.getPPS().getTilesOrEntropyCodingSyncIdx() == 2):
                    # We'll sync if the TR is available.
                    pcCUUp = pcCU.getCUAbove()
                    uiWidthInLCU = rpcPic.getFrameWidthInCU()
                    pcCUTR = None
                    if pcCUUp and (iCUAddr % uiWidthInLCU + 1) < uiWidthInLCU:
                        pcCUTR = rpcPic.getCU(iCUAddr - uiWidthInLCU + 1)
                    uiMaxParts = 1 << (pcSlice.getSPS().getMaxCUDepth()<<1)

                    if pcCUTR == None or pcCUTR.getSlice() == None or \
                       rpcPic.getPicSym().getTileIdxMap(pcCUTR.getAddr()) != rpcPic.getPicSym().getTileIdxMap(iCUAddr) or \
                       (pcCUTR.getSCUAddr() + uiMaxParts - 1) < pcSlice.getSliceCurStartCUAddr() or \
                       (pcCUTR.getSCUAddr() + uiMaxParts - 1) < pcSlice.getDependentSliceCurStartCUAddr():
                        if iCUAddr != 0 and \
                           (pcCUTR.getSCUAddr() + uiMaxParts - 1) >= pcSlice.getSliceCurStartCUAddr() and \
                           bAllowDependence:
                            pcSbacDecoders.get(uiSubStrm).loadContexts(self.m_pcBufferSbacDecoders.get(uiTileCol))
                        # TR not available.
                    else:
                        # TR is available, we use it.
                        pcSbacDecoders.get(uiSubStrm).loadContexts(self.m_pcBufferSbacDecoders.get(uiTileCol))
                pcSbacDecoder.load(pcSbacDecoders.get(uiSubStrm))
                # this load is used to simplify the code (avoid to change all the call to pcSbacDecoders)
            elif pcSlice.getPPS().getNumSubstreams() <= 1:
                # Set variables to appropriate values to avoid later code change.
                iNumSubstreamsPerTile = 1

               # 1st in tile.
            if iCUAddr == rpcPic.getPicSym().getTComTile(rpcPic.getPicSym().getTileIdxMap(iCUAddr)).getFirstCUAddr() and \
               iCUAddr != 0 and \
               iCUAddr != rpcPic.getPicSym().getPicSCUAddr(rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getSliceCurStartCUAddr()) / rpcPic.getNumPartInCU() and \
               iCUAddr != rpcPic.getPicSym().getPicSCUAddr(rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getDependentSliceCurStartCUAddr()) / rpcPic.getNumPartInCU():
               # !1st in frame && !1st in slice
                if pcSlice.getPPS().getNumSubstreams() > 1:
                    # We're crossing into another tile, tiles are independent.
                    # When tiles are independent, we have "substreams per tile".  Each substream has already been terminated, and we no longer
                    # have to perform it here.
                    # For TILES_DECODER, there can be a header at the start of the 1st substream in a tile.  These are read when the substreams
                    # are extracted, not here.
                    pass
                else:
                    sliceType = pcSlice.getSliceType()
                    if pcSlice.getCabacInitFlag():
                        if sliceType == P_SLICE: # change initialization table to B_SLICE intialization
                            sliceType = B_SLICE
                        elif sliceType == B_SLICE: # change initialization table to P_SLICE intialization
                            sliceType = P_SLICE
                        else: # should not occur
                            assert(False)
                    self.m_pcEntropyDecoder.updateContextTables(sliceType, pcSlice.getSliceQp())

            if pcSlice.getSPS().getUseSAO() and \
               (pcSlice.getSaoEnabledFlag() or pcSlice.getSaoEnabledFlagChroma()):
                saoParam = rpcPic.getPicSym().getSaoParam()
                ArrayBool_Set(saoParam.bSaoFlag, 0, pcSlice.getSaoEnabledFlag())
                if iCUAddr == iStartCUAddr:
                    ArrayBool_Set(saoParam.bSaoFlag, 1, pcSlice.getSaoEnabledFlagChroma())
                numCuInWidth = saoParam.numCuInWidth
                cuAddrInSlice = iCUAddr - rpcPic.getPicSym().getCUOrderMap(pcSlice.getSliceCurStartCUAddr() / rpcPic.getNumPartInCU())
                cuAddrUpInSlice = cuAddrInSlice - numCuInWidth
                rx = iCUAddr % numCuInWidth
                ry = iCUAddr / numCuInWidth
                allowMergeLeft = 1
                allowMergeUp = 1
                if rx != 0:
                    if rpcPic.getPicSym().getTileIdxMap(iCUAddr-1) != rpcPic.getPicSym().getTileIdxMap(iCUAddr):
                        allowMergeLeft = 0
                if ry != 0:
                    if rpcPic.getPicSym().getTileIdxMap(iCUAddr-numCuInWidth) != rpcPic.getPicSym().getTileIdxMap(iCUAddr):
                        allowMergeUp = 0
                pcSbacDecoder.parseSaoOneLcuInterleaving(rx, ry, saoParam, pcCU,
                    cuAddrInSlice, cuAddrUpInSlice, allowMergeLeft, allowMergeUp)

            self.m_pcCuDecoder.decodeCU(pcCU, uiIsLast)
            self.m_pcCuDecoder.decompressCU(pcCU)

            # If at the end of a LCU line but not at the end of a substream, perform CABAC flush
            if not uiIsLast and pcSlice.getPPS().getNumSubstreams() > 1:
                if uiCol == uiTileLCUX + uiTileWidth - 1 and \
                   uiLin + iNumSubstreamsPerTile < uiTileLCUY + uiTileHeight:
                    self.m_pcEntropyDecoder.decodeFlush()
            pcSbacDecoders.get(uiSubStrm).load(pcSbacDecoder)

            # Store probabilities of second LCU in line into buffer
            if uiCol == uiTileLCUX + 1 and \
               (bAllowDependence or pcSlice.getPPS().getNumSubstreams() > 1) and \
               pcSlice.getPPS().getTilesOrEntropyCodingSyncIdx() == 2:
                self.m_pcBufferSbacDecoders.get(uiTileCol).loadContexts(pcSbacDecoders.get(uiSubStrm))
            if uiIsLast and bAllowDependence:
                if pcSlice.getPPS().getTilesOrEntropyCodingSyncIdx() == 2:
                    rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getCTXMem_dec(0).loadContexts(self.m_pcBufferSbacDecoders.get(uiTileCol)) #ctx 2.LCU
                rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getCTXMem_dec(1).loadContexts(pcSbacDecoder) #ctx end of dep.slice

                ppcSubstreams.data = None
                pcSbacDecoders.data = None
                return

            iCUAddr = rpcPic.getPicSym().xCalculateNxtCUAddr(iCUAddr)

        ppcSubstreams.data = None
        pcSbacDecoders.data = None


class ParameterSetManagerDecoder(ParameterSetManager):

    def __init__(self):
        super(ParameterSetManager, self).__init__()
        self.m_vpsBuffer = ParameterSetMapTComVPS(MAX_NUM_VPS)
        self.m_spsBuffer = ParameterSetMapTComSPS(MAX_NUM_SPS)
        self.m_ppsBuffer = ParameterSetMapTComPPS(MAX_NUM_PPS)

    def storePrefetchedVPS(self, vps):
        self.m_vpsBuffer.storePS(vps.getVPSId(), vps)

    def getPrefetchedVPS(self, vpsId):
        if self.m_vpsBuffer.getPS(vpsId):
            return self.m_vpsBuffer.getPS(vpsId)
        else:
            return self.getVPS(vpsId)

    def storePrefetchedSPS(self, sps):
        self.m_spsBuffer.storePS(sps.getSPSId(), sps)

    def getPrefetchedSPS(self, spsId):
        if self.m_spsBuffer.getPS(spsId):
            return self.m_spsBuffer.getPS(spsId)
        else:
            return self.getSPS(spsId)

    def storePrefetchedPPS(self, pps):
        self.m_ppsBuffer.storePS(pps.getPPSId(), pps)

    def getPrefetchedPPS(self, ppsId):
        if self.m_ppsBuffer.getPS(ppsId):
            return self.m_ppsBuffer.getPS(ppsId)
        else:
            return self.getPPS(ppsId)
