#!/usr/bin/env python

from swig.hevc import MAX_TLAYER,
                      SHARP_FIXED_NUMBER_OF_LCU_IN_DEPENDENT_SLICE,
                      AD_HOC_SLICES_FIXED_NUMBER_OF_LCU_IN_SLICE,
                      AD_HOC_SLICES_FIXED_NUMBER_OF_TILES_IN_SLICE
from swig.hevc import cvar
from swig.hevc import TComVPS, writeAnnexB
from swig.hevc import TEncTop, TVideoYuv

from .TAppEncCfg import TAppEncCfg

class TAppEncTop(TAppEncCfg):

    def __init__(self):
        super(TAppEncTop, self).__init__(self)
        self.m_cTEncTop = TEncTop()
        self.m_cTVideoIOYuvInputFile = TVideoYuv()
        self.m_cTVideoIOYuvReconFile = TVideoYuv()
        self.m_cListPicYuvRec = []
        self.m_iFrameRcvd = 0
        self.m_essentialBytes = 0
        self.m_totalBytes = 0

    def encode(self):
        bitstreamFile = open(m_pchBitstreamFile, "wb")
        if not bitstreamFile:
            sys.stderr.write("\nfailed to open bitstream file `%s' for writing\n" % m_pchBitstreamFile)
            sys.exit(False)

        pcPicYuvOrg = TComPicYuv()
        pcPicYuvRec = None

        # initialize internal class & member variables
        self._xInitLibCfg()
        self._xCreateLib()
        self._xInitLib()

        # main encoder loop
        iNumEncoded = 0
        bEos = False

        list<AccessUnit> outputAccessUnits; # list of access units to write out.  is populated by the encoding process

        # allocate original YUV buffer
        pcPicYuvOrg.create(self.m_iSourceWidth, self.m_iSourceHeight, self.m_uiMaxCUWidth, self.m_uiMaxCUHeight, self.m_uiMaxCUDepth)

        while not bEos:
            # get buffers
            self._xGetBuffer(pcPicYuvRec)

            # read input YUV file
            self.m_cTVideoIOYuvInputFile.read(pcPicYuvOrg, self.m_aiPad)

            # increase number of received frames
            self.m_iFrameRcvd++

            # check end of file
            bEos = self.m_cTVideoIOYuvInputFile.isEof() == 1
            bEos = True if self.m_iFrameRcvd == self.m_iFrameToBeEncoded else bEos

            # call encoding function for one frame
            self.m_cTEncTop.encode(bEos, pcPicYuvOrg, self.m_cListPicYuvRec, outputAccessUnits, iNumEncoded)

            # write bistream to file if necessary
            if iNumEncoded > 0:
                self._xWriteOutput(bitstreamFile, iNumEncoded, outputAccessUnits)
                outputAccessUnits.clear()
        # delete original YUV buffer
        pcPicYuvOrg.destroy()
        pcPicYuvOrg = None

        # delete used buffers in encoder class
        self.m_cTEncTop.deletePicBuffer()

        # delete buffers & classes
        self._xDeleteBuffer()
        self._xDestroyLib()

        self._printRateSummary()

    def getTEncTop(self):
        return self.m_cTEncTop

    def _xCreateLib(self):
        self.m_cTVideoIOYuvInputFile.open(self.m_pchInputFile, False,
            self.m_uiInputBitDepth, self.m_uiInternalBitDepth)
        self.m_cTVideoIOYuvInputFile.skipFrames(self.m_FrameSkip,
            self.m_iSourceWidth - self.m_aiPad[0], self.m_iSourceHeight - self.m_aiPad[1])

        if self.m_pchReconFile:
            self.m_cTVideoIOYuvReconFile.open(self.m_pchReconFile, True,
                self.m_uiOutputBitDepth, self.m_uiInternalBitDepth)
  
        self.m_cTEncTop.create()

    def _xInitLibCfg(self):
        vps = TComVPS()
        vps.setMaxTLayers(self.m_maxTempLayer)
        vps.setMaxLayers(1)
        for i in range(MAX_TLAYER):
            vps.setNumReorderPics(self.m_numReorderPics[i], i)
            vps.setMaxDecPicBuffering(self.m_maxDecPicBuffering[i], i)
        self.m_cTEncTop.setVPS(vps)
        self.m_cTEncTop.setFrameRate(self.m_iFrameRate)
        self.m_cTEncTop.setFrameSkip(self.m_FrameSkip)
        self.m_cTEncTop.setSourceWidth(self.m_iSourceWidth)
        self.m_cTEncTop.setSourceHeight(self.m_iSourceHeight)
        self.m_cTEncTop.setCroppingMode(self.m_croppingMode)
        self.m_cTEncTop.setCropLeft(self.m_cropLeft)
        self.m_cTEncTop.setCropRight(self.m_cropRight)
        self.m_cTEncTop.setCropTop(self.m_cropTop)
        self.m_cTEncTop.setCropBottom(self.m_cropBottom)
        self.m_cTEncTop.setFrameToBeEncoded(self.m_iFrameToBeEncoded)

        #====== Coding Structure ========
        self.m_cTEncTop.setIntraPeriod(self.m_iIntraPeriod)
        self.m_cTEncTop.setDecodingRefreshType(self.m_iDecodingRefreshType)
        self.m_cTEncTop.setGOPSize(self.m_iGOPSize)
        self.m_cTEncTop.setGopList(self.m_GOPList)
        self.m_cTEncTop.setExtraRPSs(self.m_extraRPSs)
        for i in range(MAX_TLAYER):
            self.m_cTEncTop.setNumReorderPics(self.m_numReorderPics[i], i)
            self.m_cTEncTop.setMaxDecPicBuffering(self.m_maxDecPicBuffering[i], i)
        for uiLoop in range(MAX_TLAYER):
            self.m_cTEncTop.setLambdaModifier(uiLoop, self.m_adLambdaModifier[uiLoop])
        self.m_cTEncTop.setQP(self.m_iQP)
        self.m_cTEncTop.setPad(self.m_aiPad)
        self.m_cTEncTop.setMaxTempLayer(self.m_maxTempLayer)
        self.m_cTEncTop.setUseAMP(self.m_enableAMP)

        #===== Slice ========

        #====== Loop/Deblock Filter ========
        self.m_cTEncTop.setLoopFilterDisable(self.m_bLoopFilterDisable)
        self.m_cTEncTop.setLoopFilterOffsetInPPS(self.m_loopFilterOffsetInPPS)
        self.m_cTEncTop.setLoopFilterBetaOffset(self.m_loopFilterBetaOffsetDiv2)
        self.m_cTEncTop.setLoopFilterTcOffset(self.m_loopFilterTcOffsetDiv2)
        self.m_cTEncTop.setDeblockingFilterControlPresent(self.m_DeblockingFilterControlPresent)

        #====== Motion search ========
        self.m_cTEncTop.setFastSearch(self.m_iFastSearch)
        self.m_cTEncTop.setSearchRange(self.m_iSearchRange)
        self.m_cTEncTop.setBipredSearchRange(self.m_bipredSearchRange)

        #====== Quality control ========
        self.m_cTEncTop.setMaxDeltaQP(self.m_iMaxDeltaQP)
        self.m_cTEncTop.setMaxCuDQPDepth(self.m_iMaxCuDQPDepth)

        self.m_cTEncTop.setChromaCbQpOffset(self.m_cbQpOffset)
        self.m_cTEncTop.setChromaCrQpOffset(self.m_crQpOffset)

        self.m_cTEncTop.setUseAdaptQpSelect(self.m_bUseAdaptQpSelect)

        lowestQP = -6 * (cvar.g_uiBitDepth + cvar.g_uiBitIncrement - 8)

        if self.m_iMaxDeltaQP == 0 and self.m_iQP == lowestQP and self.m_useLossless:
            self.m_bUseAdaptiveQP = False
        self.m_cTEncTop.setUseAdaptiveQP(self.m_bUseAdaptiveQP)
        self.m_cTEncTop.setQPAdaptationRange(self.m_iQPAdaptationRange)

        #====== Tool list ========
        self.m_cTEncTop.setUseSBACRD(self.m_bUseSBACRD)
        self.m_cTEncTop.setDeltaQpRD(self.m_uiDeltaQpRD)
        self.m_cTEncTop.setUseASR(self.m_bUseASR)
        self.m_cTEncTop.setUseHADME(self.m_bUseHADME)
        self.m_cTEncTop.setUseLossless(self.m_useLossless)
        self.m_cTEncTop.setUseLComb(self.m_bUseLComb)
        self.m_cTEncTop.setdQPs(self.m_aidQP)
        self.m_cTEncTop.setUseRDOQ(self.m_bUseRDOQ)
        self.m_cTEncTop.setQuadtreeTULog2MaxSize(self.m_uiQuadtreeTULog2MaxSize)
        self.m_cTEncTop.setQuadtreeTULog2MinSize(self.m_uiQuadtreeTULog2MinSize)
        self.m_cTEncTop.setQuadtreeTUMaxDepthInter(self.m_uiQuadtreeTUMaxDepthInter)
        self.m_cTEncTop.setQuadtreeTUMaxDepthIntra(self.m_uiQuadtreeTUMaxDepthIntra)
        self.m_cTEncTop.setUseFastEnc(self.m_bUseFastEnc)
        self.m_cTEncTop.setUseEarlyCU(self.m_bUseEarlyCU) 
        self.m_cTEncTop.setUseFastDecisionForMerge(self.m_useFastDecisionForMerge)
        self.m_cTEncTop.setUseCbfFastMode(self.m_bUseCbfFastMode)
        self.m_cTEncTop.setUseEarlySkipDetection(self.m_useEarlySkipDetection)

        self.m_cTEncTop.setUseTransformSkip(self.m_useTansformSkip)
        self.m_cTEncTop.setUseTransformSkipFast(self.m_useTansformSkipFast)
        self.m_cTEncTop.setUseConstrainedIntraPred(self.m_bUseConstrainedIntraPred)
        self.m_cTEncTop.setPCMLog2MinSize(self.m_uiPCMLog2MinSize)
        self.m_cTEncTop.setUsePCM(self.m_usePCM)
        self.m_cTEncTop.setPCMLog2MaxSize(self.m_pcmLog2MaxSize)

        #====== Weighted Prediction ========
        self.m_cTEncTop.setUseWP(self.m_bUseWeightPred)
        self.m_cTEncTop.setWPBiPred(self.m_useWeightedBiPred)
        #====== Parallel Merge Estimation ========
        self.m_cTEncTop.setLog2ParallelMergeLevelMinus2(self.m_log2ParallelMergeLevel - 2)

        #====== Slice ========
        self.m_cTEncTop.setSliceMode(self.m_iSliceMode)
        self.m_cTEncTop.setSliceArgument(self.m_iSliceArgument)

        #====== Dependent Slice ========
        self.m_cTEncTop.setDependentSliceMode(self.m_iDependentSliceMode)
        self.m_cTEncTop.setDependentSliceArgument(self.m_iDependentSliceArgument)
        self.m_cTEncTop.setCabacIndependentFlag(self.m_bCabacIndependentFlag)
        iNumPartInCU = 1 << (self.m_uiMaxCUDepth << 1)
        if self.m_iDependentSliceMode == SHARP_FIXED_NUMBER_OF_LCU_IN_DEPENDENT_SLICE:
            self.m_cTEncTop.setDependentSliceArgument(self.m_iDependentSliceArgument * iNumPartInCU)
        if self.m_iSliceMode == AD_HOC_SLICES_FIXED_NUMBER_OF_LCU_IN_SLICE:
            self.m_cTEncTop.setSliceArgument(self.m_iSliceArgument * iNumPartInCU)
        if self.m_iSliceMode == AD_HOC_SLICES_FIXED_NUMBER_OF_TILES_IN_SLICE:
            self.m_cTEncTop.setSliceArgument(self.m_iSliceArgument)

        if self.m_iSliceMode == 0:
            self.m_bLFCrossSliceBoundaryFlag = True
        self.m_cTEncTop.setLFCrossSliceBoundaryFlag(self.m_bLFCrossSliceBoundaryFlag)
        self.m_cTEncTop.setUseSAO(self.m_bUseSAO)
        self.m_cTEncTop.setMaxNumOffsetsPerPic(self.m_maxNumOffsetsPerPic)

        self.m_cTEncTop.setSaoLcuBoundary(self.m_saoLcuBoundary)
        self.m_cTEncTop.setSaoLcuBasedOptimization(self.m_saoLcuBasedOptimization)
        self.m_cTEncTop.setPCMInputBitDepthFlag(self.m_bPCMInputBitDepthFlag)
        self.m_cTEncTop.setPCMFilterDisableFlag(self.m_bPCMFilterDisableFlag)

        self.m_cTEncTop.setPictureDigestEnabled(self.m_pictureDigestEnabled)

        self.m_cTEncTop.setUniformSpacingIdr(self.m_iUniformSpacingIdr)
        self.m_cTEncTop.setNumColumnsMinus1 (self.m_iNumColumnsMinus1)
        self.m_cTEncTop.setNumRowsMinus1    (self.m_iNumRowsMinus1)
        if self.m_iUniformSpacingIdr == 0:
            self.m_cTEncTop.setColumnWidth(self.m_pchColumnWidth)
            self.m_cTEncTop.setRowHeight(self.m_pchRowHeight)
        self.m_cTEncTop.xCheckGSParameters()
        uiTilesCount = (self.m_iNumRowsMinus1+1) * (self.m_iNumColumnsMinus1+1)
        if self.uiTilesCount == 1:
            self.m_bLFCrossTileBoundaryFlag = True
        self.m_cTEncTop.setLFCrossTileBoundaryFlag(self.m_bLFCrossTileBoundaryFlag)
        self.m_cTEncTop.setWaveFrontSynchro(self.m_iWaveFrontSynchro)
        self.m_cTEncTop.setWaveFrontSubstreams(self.m_iWaveFrontSubstreams)
        self.m_cTEncTop.setTMVPModeId(self.m_TMVPModeId)
        self.m_cTEncTop.setUseScalingListId(self.m_useScalingListId)
        self.m_cTEncTop.setScalingListFile(self.m_scalingListFile)
        self.m_cTEncTop.setSignHideFlag(self.m_signHideFlag)
        self.m_cTEncTop.setUseRateCtrl(self.m_enableRateCtrl)
        self.m_cTEncTop.setTargetBitrate(self.m_targetBitrate)
        self.m_cTEncTop.setNumLCUInUnit(self.m_numLCUInUnit)
        self.m_cTEncTop.setTransquantBypassEnableFlag(self.m_TransquantBypassEnableFlag)
        self.m_cTEncTop.setCUTransquantBypassFlagValue(self.m_CUTransquantBypassFlagValue)
        self.m_cTEncTop.setUseRecalculateQPAccordingToLambda(self.m_recalculateQPAccordingToLambda)

    def _xInitLib(self):
        self.m_cTEncTop.init()

    def _xDestroyLib(self):
        self.m_cTVideoIOYuvInputFile.close()
        self.m_cTVideoIOYuvReconFile.close()

        self.m_cTEncTop.destroy()

    def _xGetBuffer(self, rpcPicYuvRec):
        assert(self.m_iGOPSize > 0)
  
        if self.m_cListPicYuvRec.size() == self.m_iGOPSize:
            rpcPicYuvRec = self.m_cListPicYuvRec.popFront()
        else:
            rpcPicYuvRec = TComPicYuv()
            rpcPicYuvRec.create(self.m_iSourceWidth, self.m_iSourceHeight, self.m_uiMaxCUWidth, self.m_uiMaxCUHeight, self.m_uiMaxCUDepth)

        self.m_cListPicYuvRec.pushBack(rpcPicYuvRec)

    def _xDeleteBuffer(self):
        for pcPicYuvRec in self.m_cListPicYuvRec:
            pcPicYuvRec.destroy()
            pcPicYuvRec = None
  
    def _xWriteOutput(self, bitstreamFile, iNumEncoded, accessUnits):
        cListPicYuvRec = self.m_cListPicYuvRec[-iNumEncoded:]

        for i in range(iNumEncoded):
            pcPicYuvRec  = cListPicYuvRec[i]
            if self.m_pchReconFile:
                self.m_cTVideoIOYuvReconFile.write(pcPicYuvRec,
                    self.m_cropLeft, self.m_cropRight, self.m_cropTop, self.m_cropBottom)
    
            au = accessUnits[i]
            stats = writeAnnexB(bitstreamFile, au)
            self._rateStatsAccum(au, stats)

    def _rateStatsAccum(self, au, stats):
        for i in range(len(au)):
            if au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_TFD or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_TLA or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_CRA or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_CRANT or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_BLA or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_BLANT or \
               au[i].m_nalUnitType == NAL_UNIT_CODED_SLICE_IDR or \
               au[i].m_nalUnitType == NAL_UNIT_VPS or \
               au[i].m_nalUnitType == NAL_UNIT_SPS or \
               au[i].m_nalUnitType == NAL_UNIT_PPS:
                self.m_essentialBytes += stats[i]
            self.m_totalBytes += stats[i]

    def _printRateSummary(self):
        time = self.m_iFrameRcvd / self.m_iFrameRate
        sys.stdout.write("Bytes written to file: %u (%.3f kbps)\n" % (self.m_totalBytes, 0.008 * self.m_totalBytes / time))
