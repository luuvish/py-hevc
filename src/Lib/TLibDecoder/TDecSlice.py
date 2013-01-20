# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecSlice.py
    HM 9.1 Python Implementation
"""

import sys

from ... import clock
from ... import pointer
from ... import trace

from ... import ParameterSetManager
from ... import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS

from ... import VectorTDecSbac, ArrayTDecSbac, ArrayTDecBinCABAC

from ..TLibCommon.TypeDef import (
    MAX_NUM_SPS, MAX_NUM_PPS, MAX_NUM_VPS,
    B_SLICE, P_SLICE
)


class TDecSlice(object):

    def __init__(self):
        self.m_pcEntropyDecoder           = None
        self.m_pcCuDecoder                = None
        self.m_uiCurrSliceIdx             = 0

        self.m_pcBufferSbacDecoders       = None
        self.m_pcBufferBinCABACs          = None
        self.m_pcBufferLowLatSbacDecoders = None
        self.m_pcBufferLowLatBinCABACs    = None

        self.CTXMem                       = VectorTDecSbac()

    def init(self, pcEntropyDecoder, pcCuDecoder):
        self.m_pcEntropyDecoder = pcEntropyDecoder
        self.m_pcCuDecoder = pcCuDecoder

    def create(self, pcSlice, iWidth, iHeight, uiMaxWidth, uiMaxHeight, uiMaxDepth):
        pass

    def destroy(self):
        if self.m_pcBufferSbacDecoders != None:
            del self.m_pcBufferSbacDecoders
            self.m_pcBufferSbacDecoders = None
        if self.m_pcBufferBinCABACs != None:
            del self.m_pcBufferBinCABACs
            self.m_pcBufferBinCABACs = None
        if self.m_pcBufferLowLatSbacDecoders != None:
            del self.m_pcBufferLowLatSbacDecoders
            self.m_pcBufferLowLatSbacDecoders = None
        if self.m_pcBufferLowLatBinCABACs != None:
            del self.m_pcBufferLowLatBinCABACs
            self.m_pcBufferLowLatBinCABACs = None

    def decompressSlice(self, pcBitstream, ppcSubstreams, rpcPic, pcSbacDecoder, pcSbacDecoders):
        ppcSubstreams = pointer(ppcSubstreams, type='TComInputBitstream **')
        pcSbacDecoders = pointer(pcSbacDecoders, type='TDecSbac *')

        pcCU = None
        uiIsLast = 0
        iStartCUEncOrder = max(rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getSliceCurStartCUAddr() // rpcPic.getNumPartInCU(),
                               rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getDependentSliceCurStartCUAddr() // rpcPic.getNumPartInCU())
        iStartCUAddr = rpcPic.getPicSym().getCUOrderMap(iStartCUEncOrder)

        # decoder don't need prediction & residual frame buffer
        rpcPic.setPicYuvPred(None)
        rpcPic.setPicYuvResi(None)

        if trace.use_trace:
            trace.DTRACE_CABAC_VL(trace.g_nSymbolCounter)
            trace.g_nSymbolCounter += 1
            trace.DTRACE_CABAC_T('\tPOC: ')
            trace.DTRACE_CABAC_V(rpcPic.getPOC())
            trace.DTRACE_CABAC_T('\n')

        uiTilesAcross = rpcPic.getPicSym().getNumColumnsMinus1() + 1
        pcSlice = rpcPic.getSlice(rpcPic.getCurrSliceIdx())
        iNumSubstreams = pcSlice.getPPS().getNumSubstreams()

        # delete decoders if already allocated in previous slice
        if self.m_pcBufferSbacDecoders != None:
            del self.m_pcBufferSbacDecoders
        if self.m_pcBufferBinCABACs != None:
            del self.m_pcBufferBinCABACs
        # allocate new decoders based on tile numbaer
        self.m_pcBufferSbacDecoders = ArrayTDecSbac(uiTilesAcross)
        self.m_pcBufferBinCABACs = ArrayTDecBinCABAC(uiTilesAcross)
        for ui in xrange(uiTilesAcross):
            self.m_pcBufferSbacDecoders[ui].init(self.m_pcBufferBinCABACs[ui])
        #save init. state
        for ui in xrange(uiTilesAcross):
            self.m_pcBufferSbacDecoders[ui].load(pcSbacDecoder)

        # free memory if already allocated in previous call
        if self.m_pcBufferLowLatSbacDecoders != None:
            del self.m_pcBufferLowLatSbacDecoders
        if self.m_pcBufferLowLatBinCABACs != None:
            del self.m_pcBufferLowLatBinCABACs
        self.m_pcBufferLowLatSbacDecoders = ArrayTDecSbac(uiTilesAcross)
        self.m_pcBufferLowLatBinCABACs = ArrayTDecBinCABAC(uiTilesAcross)
        for ui in xrange(uiTilesAcross):
            self.m_pcBufferLowLatSbacDecoders[ui].init(self.m_pcBufferLowLatBinCABACs[ui])
        #save init. state
        for ui in xrange(uiTilesAcross):
            self.m_pcBufferLowLatSbacDecoders[ui].load(pcSbacDecoder)

        uiWidthInLCUs = rpcPic.getPicSym().getFrameWidthInCU()
        uiCol = uiLin = uiSubStrm = 0

        uiTileCol = uiTileStartLCU = uiTileLCUX = 0
        iNumSubstreamsPerTile = 1 # if independent.

        bAllowDependence = False
        if rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getPPS().getDependentSliceEnabledFlag():
            bAllowDependence = True
        if bAllowDependence:
            if not rpcPic.getSlice(rpcPic.getCurrSliceIdx()).isNextSlice():
                uiTileCol = 0
                if pcSlice.getPPS().getEntropyCodingSyncEnabledFlag():
                    self.m_pcBufferSbacDecoders[uiTileCol].loadContexts(self.CTXMem[1]) #2.LCU
                pcSbacDecoder.loadContexts(self.CTXMem[0]) # end of depSlice-1
                pcSbacDecoders[uiSubStrm].loadContexts(pcSbacDecoder)
            else:
                if pcSlice.getPPS().getEntropyCodingSyncEnabledFlag():
                    self.CTXMem[1].loadContexts(pcSbacDecoder)
                self.CTXMem[0].loadContexts(pcSbacDecoder)

        iCUAddr = iStartCUAddr
        while not uiIsLast and iCUAddr < rpcPic.getNumCUsInFrame():
            pcCU = rpcPic.getCU(iCUAddr)
            pcCU.initCU(rpcPic, iCUAddr)
            uiTileCol = rpcPic.getPicSym().getTileIdxMap(iCUAddr) % \
                (rpcPic.getPicSym().getNumColumnsMinus1()+1) # what column of tiles are we in?
            uiTileStartLCU = rpcPic.getPicSym().getTComTile(rpcPic.getPicSym().getTileIdxMap(iCUAddr)).getFirstCUAddr()
            uiTileLCUX = uiTileStartLCU % uiWidthInLCUs
            uiCol = iCUAddr % uiWidthInLCUs
            # The 'line' is now relative to the 1st line in the slice, not the 1st line in the picture.
            uiLin = (iCUAddr//uiWidthInLCUs) - (iStartCUAddr//uiWidthInLCUs)
            # inherit from TR if necessary, select substream to use.
            if (pcSlice.getPPS().getNumSubstreams() > 1) or \
               (bAllowDependence and uiCol == uiTileLCUX and
                pcSlice.getPPS().getEntropyCodingSyncEnabledFlag()):
                # independent tiles => substreams are "per tile".  iNumSubstreams has already been multiplied.
                iNumSubstreamsPerTile = iNumSubstreams / rpcPic.getPicSym().getNumTiles()
                uiSubStrm = rpcPic.getPicSym().getTileIdxMap(iCUAddr) * iNumSubstreamsPerTile + \
                            uiLin % iNumSubstreamsPerTile
                self.m_pcEntropyDecoder.setBitstream(ppcSubstreams[uiSubStrm])
                # Synchronize cabac probabilities with upper-right LCU if it's available and we're at the start of a line.
                if (pcSlice.getPPS().getNumSubstreams() > 1) or \
                   (bAllowDependence and uiCol == uiTileLCUX and
                    pcSlice.getPPS().getEntropyCodingSyncEnabledFlag()):
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
                        if iCUAddr != 0 and pcCUTR and \
                           (pcCUTR.getSCUAddr() + uiMaxParts - 1) >= pcSlice.getSliceCurStartCUAddr() and \
                           bAllowDependence:
                            pcSbacDecoders[uiSubStrm].loadContexts(self.m_pcBufferSbacDecoders[uiTileCol])
                        # TR not available.
                    else:
                        # TR is available, we use it.
                        pcSbacDecoders[uiSubStrm].loadContexts(self.m_pcBufferSbacDecoders[uiTileCol])
                pcSbacDecoder.load(pcSbacDecoders[uiSubStrm])
                # this load is used to simplify the code (avoid to change all the call to pcSbacDecoders)
            elif pcSlice.getPPS().getNumSubstreams() <= 1:
                # Set variables to appropriate values to avoid later code change.
                iNumSubstreamsPerTile = 1

               # 1st in tile.
            if iCUAddr == rpcPic.getPicSym().getTComTile(rpcPic.getPicSym().getTileIdxMap(iCUAddr)).getFirstCUAddr() and \
               iCUAddr != 0 and \
               iCUAddr != rpcPic.getPicSym().getPicSCUAddr(rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getSliceCurStartCUAddr()) // rpcPic.getNumPartInCU() and \
               iCUAddr != rpcPic.getPicSym().getPicSCUAddr(rpcPic.getSlice(rpcPic.getCurrSliceIdx()).getDependentSliceCurStartCUAddr()) // rpcPic.getNumPartInCU():
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
                abSaoFlag = pointer(saoParam.bSaoFlag, type='bool *')
                abSaoFlag[0] = pcSlice.getSaoEnabledFlag()
                if iCUAddr == iStartCUAddr:
                    abSaoFlag[1] = pcSlice.getSaoEnabledFlagChroma()
                numCuInWidth = saoParam.numCuInWidth
                cuAddrInSlice = iCUAddr - rpcPic.getPicSym().getCUOrderMap(pcSlice.getSliceCurStartCUAddr() // rpcPic.getNumPartInCU())
                cuAddrUpInSlice = cuAddrInSlice - numCuInWidth
                rx = iCUAddr % numCuInWidth
                ry = iCUAddr // numCuInWidth
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

            uiIsLast = self.m_pcCuDecoder.decodeCU(pcCU, uiIsLast)
            self.m_pcCuDecoder.decompressCU(pcCU)
 
            pcSbacDecoders[uiSubStrm].load(pcSbacDecoder)

            # Store probabilities of second LCU in line into buffer
            if uiCol == uiTileLCUX + 1 and \
               (bAllowDependence or pcSlice.getPPS().getNumSubstreams() > 1) and \
               pcSlice.getPPS().getEntropyCodingSyncEnabledFlag():
                self.m_pcBufferSbacDecoders[uiTileCol].loadContexts(pcSbacDecoders[uiSubStrm])
            if uiIsLast and bAllowDependence:
                if pcSlice.getPPS().getEntropyCodingSyncEnabledFlag():
                    self.CTXMem[1].loadContexts(self.m_pcBufferSbacDecoders[uiTileCol]) #ctx 2.LCU
                self.CTXMem[0].loadContexts(pcSbacDecoder) #ctx end of dep.slice
                return

            iCUAddr = rpcPic.getPicSym().xCalculateNxtCUAddr(iCUAddr)

    def initCtxMem(self, i):
        for j in self.CTXMem:
            del j
        self.CTXMem.clear()
        self.CTXMem.resize(i)

    def setCtxMem(self, sb, b):
        self.CTXMem[b] = sb


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

    def applyPrefetchedPS(self):
        self.m_vpsMap.mergePSList(self.m_vpsBuffer)
        self.m_ppsMap.mergePSList(self.m_ppsBuffer)
        self.m_spsMap.mergePSList(self.m_spsBuffer)
