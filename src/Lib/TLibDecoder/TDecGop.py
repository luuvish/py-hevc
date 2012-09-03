# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/TDecGop.py
    HM 8.0 Python Implementation
"""

import sys
from time import clock

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar

    from swig.hevc import TDecCavlc
    from swig.hevc import TDecSbac
    from swig.hevc import TDecBinCABAC
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString

    from swig.hevc import VectorBool, VectorInt
    from swig.hevc import ArrayBool
    from swig.hevc import ArrayTComInputBitstream, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import SEIpictureDigest, digest_get
else:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar

    from swig.hevc import TDecCavlc
    from swig.hevc import TDecSbac
    from swig.hevc import TDecBinCABAC
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString

    from swig.hevc import VectorBool, VectorInt
    from swig.hevc import ArrayBool
    from swig.hevc import ArrayTComInputBitstream, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import SEIpictureDigest, digest_get

CLOCKS_PER_SEC = 1


def _calcAndPrintHashStatus(pic, seis):
    dummy = SEIpictureDigest()
    recon_digest = dummy.digest;
    numChar = 0
    hashType = ''

    if seis and seis.picture_digest.method == SEIpictureDigest.MD5:
        hashType = 'MD5'
        calcMD5(pic, recon_digest)
        numChar = 16
    elif seis and seis.picture_digest.method == SEIpictureDigest.CRC:
        hashType = 'CRC'
        calcCRC(pic, recon_digest)
        numChar = 2
    elif seis and seis.picture_digest.method == SEIpictureDigest.CHECKSUM:
        hashType = 'Checksum'
        calcChecksum(pic, recon_digest)
        numChar = 4
    else:
        hashType = '\0'

    ok = '(unk)'
    mismatch = False

    if seis and seis.picture_digest:
        ok = '(OK)'
        for yuvIdx in xrange(3):
            for i in xrange(numChar):
                if digest_get(recon_digest, yuvIdx, i) != digest_get(seis.picture_digest.digest, yuvIdx, i):
                    ok = '(***ERROR***)'
                    mismatch = True

    sys.stdout.write("[%s:%s,%s] " % (hashType, digestToString(recon_digest, numChar), ok))

    if mismatch:
        cvar.g_md5_mismatch = True
        sys.stdout.write("[rx%s:%s] " % (hashType, digestToString(seis.picture_digest.digest, numChar)))

class TDecGop(object):

    def __init__(self):
        self.m_iGopSize = 0

        self.m_pcEntropyDecoder = None
        self.m_pcSbacDecoder = None
        self.m_pcBinCABAC = None
        self.m_pcSbacDecoders = None
        self.m_pcBinCABACs = None
        self.m_pcCavlcDecoder = None
        self.m_pcSliceDecoder = None
        self.m_pcLoopFilter = None

        self.m_pcSAO = None
        self.m_dDecTime = 0.0
        self.m_pictureDigestEnabled = False

        self.m_sliceStartCUAddress = VectorInt()
        self.m_LFCrossSliceBoundaryFlag = VectorBool()

    def init(self, pcEntropyDecoder, pcSbacDecoder, pcBinCABAC, pcCavlcDecoder,
             pcSliceDecoder, pcLoopFilter, pcSAO):
        self.m_pcEntropyDecoder = pcEntropyDecoder
        self.m_pcSbacDecoder = pcSbacDecoder
        self.m_pcBinCABAC = pcBinCABAC
        self.m_pcSliceDecoder = pcSliceDecoder
        self.m_pcCavlcDecoder = pcCavlcDecoder
        self.m_pcLoopFilter = pcLoopFilter
        self.m_pcSAO = pcSAO

    def create(self):
        pass

    def destroy(self):
        pass

    def decompressSlice(self, pcBitstream, rpcPic):
        pcSlice = rpcPic.getSlice(rpcPic.getCurrSliceIdx())
        # Table of extracted substreams.
        # These must be deallocated AND their internal fifos, too.
        ppcSubstreams = None

        #-- For time output for each slice
        iBeforeTime = clock()

        uiStartCUAddr = pcSlice.getDependentSliceCurStartCUAddr()

        uiSliceStartCuAddr = pcSlice.getSliceCurStartCUAddr()
        if uiSliceStartCuAddr == uiStartCUAddr:
            self.m_sliceStartCUAddress.push_back(uiSliceStartCuAddr)

        self.m_pcSbacDecoder.init(self.m_pcBinCABAC)
        self.m_pcEntropyDecoder.setEntropyDecoder(self.m_pcSbacDecoder)

        uiNumSubstreams = pcSlice.getPPS().getNumSubstreams()

        # init each couple {EntropyDecoder, Substream}
        puiSubstreamSizes = pcSlice.getSubstreamSizes()
        ppcSubstreams = ArrayTComInputBitstream(uiNumSubstreams)
        self.m_pcSbacDecoders = ArrayTDecSbac(uiNumSubstreams)
        self.m_pcBinCABACs = ArrayTDecBinCABAC(uiNumSubstreams)
        for ui in xrange(uiNumSubstreams):
            self.m_pcSbacDecoders[ui].init(self.m_pcBinCABACs[ui])
            ppcSubstreams[ui] = pcBitstream.extractSubstream(
                puiSubstreamSizes[ui] if ui+1 < uiNumSubstreams else pcBitstream.getNumBitsLeft())

        if uiNumSubstreams > 1:
            for ui in xrange(uiNumSubstreams-1):
                self.m_pcEntropyDecoder.setEntropyDecoder(self.m_pcSbacDecoders[uiNumSubstreams-1-ui])
                self.m_pcEntropyDecoder.setBitstream(ppcSubstreams[uiNumSubstreams-1-ui])
                self.m_pcEntropyDecoder.resetEntropy(pcSlice)

        self.m_pcEntropyDecoder.setEntropyDecoder(self.m_pcSbacDecoder)
        self.m_pcEntropyDecoder.setBitstream(ppcSubstreams[0])
        self.m_pcEntropyDecoder.resetEntropy(pcSlice)

        if uiSliceStartCuAddr == uiStartCUAddr:
            self.m_LFCrossSliceBoundaryFlag.push_back(pcSlice.getLFCrossSliceBoundaryFlag())
        if pcSlice.getPPS().getDependentSlicesEnabledFlag() and \
           not pcSlice.getPPS().getCabacIndependentFlag():
            pcSlice.initCTXMem_dec(2)
            for st in xrange(2):
                ctx = TDecSbac()
                ctx.init(self.m_pcBinCABAC)
                ctx.load(self.m_pcSbacDecoder)
                pcSlice.setCTXMem_dec(ctx, st)

        self.m_pcSbacDecoders[0].load(self.m_pcSbacDecoder)
        self.m_pcSliceDecoder.decompressSlice(
            pcBitstream, ppcSubstreams.cast(), rpcPic,
            self.m_pcSbacDecoder, self.m_pcSbacDecoders.cast())
        self.m_pcEntropyDecoder.setBitstream(ppcSubstreams[uiNumSubstreams-1])
        # deallocate all created substreams, including internal buffers.
        for ui in xrange(uiNumSubstreams):
            ppcSubstreams[ui].deleteFifo()
            p = ppcSubstreams[ui]; del p
        del ppcSubstreams
        del self.m_pcSbacDecoders
        self.m_pcSbacDecoders = None
        del self.m_pcBinCABACs
        self.m_pcBinCABACs = None

        self.m_dDecTime += (clock() - iBeforeTime) / CLOCKS_PER_SEC

    def filterPicture(self, rpcPic):
        pcSlice = rpcPic.getSlice(rpcPic.getCurrSliceIdx())

        #-- For time output for each slice
        iBeforeTime = clock()

        # deblocking filter
        bLFCrossTileBoundary = pcSlice.getPPS().getLFCrossTileBoundaryFlag()
        if pcSlice.getPPS().getDeblockingFilterControlPresent():
            if pcSlice.getPPS().getLoopFilterOffsetInPPS():
                pcSlice.setLoopFilterDisable(pcSlice.getPPS().getLoopFilterDisable())
                if not pcSlice.getLoopFilterDisable:
                    pcSlice.setLoopFilterBetaOffset(pcSlice.getPPS().getLoopFilterBetaOffset())
                    pcSlice.setLoopFilterTcOffset(pcSlice.getPPS().getLoopFilterTcOffset())
        self.m_pcLoopFilter.setCfg(
            pcSlice.getPPS().getDeblockingFilterControlPresent(),
            pcSlice.getLoopFilterDisable(),
            pcSlice.getLoopFilterBetaOffset(),
            pcSlice.getLoopFilterTcOffset(),
            bLFCrossTileBoundary)
        self.m_pcLoopFilter.loopFilterPic(rpcPic)

        pcSlice = rpcPic.getSlice(0)
        if pcSlice.getSPS().getUseSAO():
            self.m_sliceStartCUAddress.push_back(rpcPic.getNumCUsInFrame() * rpcPic.getNumPartInCU())
            rpcPic.createNonDBFilterInfo(
                self.m_sliceStartCUAddress, 0, self.m_LFCrossSliceBoundaryFlag,
                rpcPic.getPicSym().getNumTiles(), bLFCrossTileBoundary)

        if pcSlice.getSPS().getUseSAO():
            if pcSlice.getSaoEnabledFlag() or pcSlice.getSaoEnabledFlagChroma():
                saoParam = rpcPic.getPicSym().getSaoParam()
                abSaoFlag = ArrayBool.frompointer(saoParam.bSaoFlag)
                abSaoFlag[0] = pcSlice.getSaoEnabledFlag()
                abSaoFlag[1] = pcSlice.getSaoEnabledFlagChroma()
                self.m_pcSAO.setSaoLcuBasedOptimization(1)
                self.m_pcSAO.createPicSaoInfo(rpcPic, self.m_sliceStartCUAddress.size()-1)
                self.m_pcSAO.SAOProcess(rpcPic, saoParam)
                self.m_pcSAO.destroyPicSaoInfo()

        if pcSlice.getSPS().getUseSAO():
            rpcPic.destroyNonDBFilterInfo()

        rpcPic.compressMotion()
        c = 'I' if pcSlice.isIntra() else 'P' if pcSlice.isInterP() else 'B'
        if not pcSlice.isReferenced():
            c.lower()

        #-- For time output for each slice
        sys.stdout.write("\nPOC %4d TId: %1d ( %c-SLICE, QP%3d ) " %
            (pcSlice.getPOC(), pcSlice.getTLayer(), c, pcSlice.getSliceQp()))

        self.m_dDecTime += (clock() - iBeforeTime) / CLOCKS_PER_SEC
        sys.stdout.write("[DT %6.3f] " % self.m_dDecTime)
        self.m_dDecTime = 0.0

        for iRefList in xrange(2):
            sys.stdout.write("[L%d " % iRefList)
            for iRefIndex in xrange(pcSlice.getNumRefIdx(iRefList)):
                sys.stdout.write("%d " % pcSlice.getRefPOC(iRefList, iRefIndex))
            sys.stdout.write("] ")
        if self.m_pictureDigestEnabled:
            _calcAndPrintHashStatus(rpcPic.getPicYuvRec(), rpcPic.getSEIs())

        rpcPic.setOutputMark(True)
        rpcPic.setReconMark(True)
        self.m_sliceStartCUAddress.clear()
        self.m_LFCrossSliceBoundaryFlag.clear()

    def setGopSize(self, i):
        self.m_iGopSize = i

    def setPictureDigestEnabled(self, enabled):
        self.m_pictureDigestEnabled = enabled
