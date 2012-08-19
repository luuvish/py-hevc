#!/usr/bin/env python

import sys
import optparse

class TAppEncCfg(object):

    def __init__(self):
        self.m_pchInputFile = ''
        self.m_pchBitstreamFile = ''
        self.m_pchReconFile = ''
        self.m_adLambdaModifier = []

        self.m_iFrameRate = 0
        self.m_FrameSkip = 0
        self.m_iSourceWidth = 0
        self.m_iSourceHeight = 0
        self.m_croppingMode = 0
        self.m_cropLeft = 0
        self.m_cropRight = 0
        self.m_cropTop = 0
        self.m_cropBottom = 0
        self.m_iFrameToBeEncoded = 0
        self.m_aiPad = []

        self.m_iIntraPeriod = 0
        self.m_iDecodingRefreshType = 0
        self.m_iGOPSize = 0
        self.m_extraRPSs = 0
        self.m_GOPList = []
        self.m_numReorderPics = []
        self.m_maxDecPicBuffering = []
        self.m_bUseLComb = False
        self.m_useTansformSkip = False
        self.m_useTansformSkipFast = False
        self.m_enableAMP = False
        self.m_fQP = 0.0
        self.m_iQP = 0
        self.m_pchdQPFile = ''
        self.m_aidQP = None
        self.m_iMaxDeltaQP = 0
        self.m_uiDeltaQpRD = 0
        self.m_iMaxCuDQPDepth = 0

        self.m_cbQpOffset = 0
        self.m_crQpOffset = 0

        self.m_bUseAdaptQpSelect = False

        self.m_bUseAdaptiveQP = False
        self.m_iQPAdaptationRange = 0

        self.m_maxTempLayer = 0

        self.m_uiMaxCUWidth = 0
        self.m_uiMaxCUHeight = 0
        self.m_uiMaxCUDepth = 0

        self.m_uiQuadtreeTULog2MaxSize = 0
        self.m_uiQuadtreeTULog2MinSize = 0

        self.m_uiQuadtreeTUMaxDepthInter = 0
        self.m_uiQuadtreeTUMaxDepthIntra = 0

        self.m_uiInputBitDepth = 0
        self.m_uiOutputBitDepth = 0
        self.m_uiInternalBitDepth = 0

        self.m_bPCMInputBitDepthFlag = False
        self.m_uiPCMBitDepthLuma = 0

        self.m_useLossless = False
        self.m_bUseSAO = False
        self.m_maxNumOffsetsPerPic = 0
        self.m_saoLcuBoundary = False
        self.m_saoLcuBasedOptimization = False
        self.m_bLoopFilterDisable = False
        self.m_loopFilterOffsetInPPS = False
        self.m_loopFilterBetaOffsetDiv2 = 0
        self.m_loopFilterTcOffsetDiv2 = 0
        self.m_DeblockingFilterControlPresent = False

        self.m_usePCM = False
        self.m_pcmLog2MaxSize = 0
        self.m_uiPCMLog2MinSize = 0
        self.m_bPCMFilterDisableFlag = False

        self.m_bUseSBACRD = False
        self.m_bUseASR = False
        self.m_bUseHADME = False
        self.m_bUseRDOQ = False
        self.m_iFastSearch = 0
        self.m_iSearchRange = 0
        self.m_bipredSearchRange = 0
        self.m_bUseFastEnc = False
        self.m_bUseEarlyCU = False
        self.m_useFastDecisionForMerge = False
        self.m_bUseCbfFastMode = False
        self.m_useEarlySkipDetection = False
        self.m_iSliceMode = 0
        self.m_iSliceArgument = 0
        self.m_iDependentSliceMode = 0
        self.m_iDependentSliceArgument = 0
        self.m_bCabacIndependentFlag = False

        self.m_bLFCrossSliceBoundaryFlag = False
        self.m_bLFCrossTileBoundaryFlag = False
        self.m_iUniformSpacingIdr = 0
        self.m_iNumColumnsMinus1 = 0
        self.m_pchColumnWidth = ''
        self.m_iNumRowsMinus1 = 0
        self.m_pchRowHeight = ''
        self.m_iWaveFrontSynchro = 0
        self.m_iWaveFrontSubstreams = 0

        self.m_bUseConstrainedIntraPred = False
        self.m_pictureDigestEnabled = 0

        self.m_bUseWeightPred = False
        self.m_useWeightedBiPred = False
        self.m_log2ParallelMergeLevel = 0

        self.m_TMVPModeId = 0
        self.m_signHideFlag = 0
        self.m_enableRateCtrl = False
        self.m_targetBitrate = 0
        self.m_numLCUInUnit = 0
        self.m_useScalingListId = 0
        self.m_scalingListFile = ''

        self.m_TransquantBypassEnableFlag = False
        self.m_CUTransquantBypassFlagValue = False
        self.m_recalculateQPAccordingToLambda = False

    def create(self):
        pass

    def destroy(self):
        pass

std::istringstream &operator>>(std::istringstream &in, GOPEntry &entry)     //input
{
  in>>entry.m_sliceType;
  in>>entry.m_POC;
  in>>entry.m_QPOffset;
  in>>entry.m_QPFactor;
  in>>entry.m_temporalId;
  in>>entry.m_numRefPicsActive;
  in>>entry.m_refPic;
  in>>entry.m_numRefPics;
  for ( Int i = 0; i < entry.m_numRefPics; i++ )
  {
    in>>entry.m_referencePics[i];
  }
  in>>entry.m_interRPSPrediction;
#if AUTO_INTER_RPS
  if (entry.m_interRPSPrediction==1)
  {
#if !J0234_INTER_RPS_SIMPL
    in>>entry.m_deltaRIdxMinus1;
#endif
    in>>entry.m_deltaRPS;
    in>>entry.m_numRefIdc;
    for ( Int i = 0; i < entry.m_numRefIdc; i++ )
    {
      in>>entry.m_refIdc[i];
    }
  }
  else if (entry.m_interRPSPrediction==2)
  {
#if !J0234_INTER_RPS_SIMPL
    in>>entry.m_deltaRIdxMinus1;
#endif
    in>>entry.m_deltaRPS;
  }
#else
  if (entry.m_interRPSPrediction)
  {
#if !J0234_INTER_RPS_SIMPL
    in>>entry.m_deltaRIdxMinus1;
#endif
    in>>entry.m_deltaRPS;
    in>>entry.m_numRefIdc;
    for ( Int i = 0; i < entry.m_numRefIdc; i++ )
    {
      in>>entry.m_refIdc[i];
    }
  }
#endif
  return in;
}

    def parseCfg(self, argv):
        p = optparse.OptionParser()

  ("c", po::parseConfigFile, "configuration file name")
        p.add_option('-c', action='store', type='string', dest='bitstreamFile', default='', help='configuration file name')

        p.add_option('-i', '--InputFile', action='store', type='string', dest='inputFile', default='', help='Original YUV input file name')
        p.add_option('-b', '--BitstreamFile', action='store', type='string', dest='bitstreamFile', default='', help='Bitstream output file name')
        p.add_option('-o', '--ReconFile', action='store', type='string', dest='reconFile', default='', help='Reconstructed YUV output file name')
        p.add_option('-wdt', '--SourceWidth', action='store', type='int', dest='m_iSourceWidth', default=0, help='Source picture width')
        p.add_option('-hgt', '--SourceHeight', action='store', type='int', dest='m_iSourceHeight', default=0, help='Source picture height')
        p.add_option('--InputBitDepth', action='store', type='int', dest='m_uiInputBitDepth', default=8, help='Bit-depth of input file')
        p.add_option('--OutputBitDepth', action='store', type='int', dest='m_uiOutputBitDepth', default=0, help='Bit-depth of output file')
        p.add_option('--InternalBitDepth', action='store', type='int', dest='m_uiInternalBitDepth', default=0, help='Internal bit-depth (BitDepth+BitIncrement)')
        p.add_option('--CroppingMode', action='store', type='int', dest='m_croppingMode', default=0, help='Cropping mode (0: no cropping, 1:automatic padding, 2: padding, 3:cropping')

        p.add_option('-pdx', '--HorizontalPadding', action='store', type='int', dest='m_aiPad0', default=0, help='Horizontal source padding for cropping mode 2')
        p.add_option('-pdy', '--VerticalPadding', action='store', type='int', dest='m_aiPad1', default=0, help='Vertical source padding for cropping mode 2')
        p.add_option('--CropLeft', action='store', type='int', dest='m_cropLeft', default=0, help='Left cropping for cropping mode 3')
        p.add_option('--CropRight', action='store', type='int', dest='m_cropRight', default=0, help='Right cropping for cropping mode 3')
        p.add_option('--CropTop', action='store', type='int', dest='m_cropTop', default=0, help='Top cropping for cropping mode 3')
        p.add_option('--CropBottom', action='store', type='int', dest='m_cropBottom', default=0, help='Bottom cropping for cropping mode 3')
        p.add_option('--FrameRate', action='store', type='int', dest='m_iFrameRate', default=0, help='Frame rate')
        p.add_option('--FrameSkip', action='store', type='int', dest='m_FrameSkip', default=0, help='Number of frames to skip at start of input YUV')
        p.add_option('-f', '--FramesToBeEncoded', action='store', type='int', dest='m_iFrameToBeEncoded', default=0, help='Number of frames to be encoded (default=all)')

        # Unit definition parameters
        p.add_option('--MaxCUWidth', action='store', type='int', dest='m_uiMaxCUWidth', default=64, help='Maximum CU size')
        p.add_option('--MaxCUHeight', action='store', type='int', dest='m_uiMaxCUHeight', default=64, help='Maximum CU size')

        p.add_option('--QuadtreeTULog2MaxSize', action='store', type='int', dest='m_uiQuadtreeTULog2MaxSize', default=6, help='Maximum TU size in logarithm base 2')
        p.add_option('--QuadtreeTULog2MinSize', action='store', type='int', dest='m_uiQuadtreeTULog2MinSize', default=2, help='Minimum TU size in logarithm base 2')

        p.add_option('--QuadtreeTUMaxDepthIntra', action='store', type='int', dest='m_uiQuadtreeTUMaxDepthIntra', default=1, help='Depth of TU tree for intra CUs')
        p.add_option('--QuadtreeTUMaxDepthInter', action='store', type='int', dest='m_uiQuadtreeTUMaxDepthInter', default=2, help='Depth of TU tree for inter CUs')

        # Coding structure paramters
        p.add_option('-ip', '--IntraPeriod', action='store', type='int', dest='m_iIntraPeriod', default=-1, help='Intra period in frames, (-1: only first frame)')
        p.add_option('-dr', '--DecodingRefreshType', action='store', type='int', dest='m_iDecodingRefreshType', default=0, help='Intra refresh type (0:none 1:CRA 2:IDR)')
        p.add_option('-g', '--GOPSize', action='store', type='int', dest='m_iGOPSize', default=1, help='GOP size of temporal structure')
        p.add_option('-lc', '--ListCombination', action='store', type='boolean', dest='m_bUseLComb', default=True, help='Combined reference list for uni-prediction estimation in B-slices')
        # motion options
        p.add_option('--FastSearch', action='store', type='int', dest='m_iFastSearch', default=1, help='0:Full search  1:Diamond  2:PMVFAST')
        p.add_option('-sr', '--SearchRange', action='store', type='int', dest='m_iSearchRange', default=96, help='Motion search range')
        p.add_option('--BipredSearchRange', action='store', type='int', dest='m_bipredSearchRange', default=4, help='Motion search range for bipred refinement')
        p.add_option('--HadamardME', action='store', type='boolean', dest='m_bUseHADME', default=True, help='Hadamard ME for fractional-pel')
        p.add_option('--ASR', action='store', type='boolean', dest='m_bUseASR', default=False, help='Adaptive motion search range')

        # Mode decision parameters
        p.add_option('-LM0', '--LambdaModifier0', action='store', type='float', dest='m_adLambdaModifier0', default=1.0, help='Lambda modifier for temporal layer 0')
        p.add_option('-LM1', '--LambdaModifier1', action='store', type='float', dest='m_adLambdaModifier1', default=1.0, help='Lambda modifier for temporal layer 1')
        p.add_option('-LM2', '--LambdaModifier2', action='store', type='float', dest='m_adLambdaModifier2', default=1.0, help='Lambda modifier for temporal layer 2')
        p.add_option('-LM3', '--LambdaModifier3', action='store', type='float', dest='m_adLambdaModifier3', default=1.0, help='Lambda modifier for temporal layer 3')
        p.add_option('-LM4', '--LambdaModifier4', action='store', type='float', dest='m_adLambdaModifier4', default=1.0, help='Lambda modifier for temporal layer 4')
        p.add_option('-LM5', '--LambdaModifier5', action='store', type='float', dest='m_adLambdaModifier5', default=1.0, help='Lambda modifier for temporal layer 5')
        p.add_option('-LM6', '--LambdaModifier6', action='store', type='float', dest='m_adLambdaModifier6', default=1.0, help='Lambda modifier for temporal layer 6')
        p.add_option('-LM7', '--LambdaModifier7', action='store', type='float', dest='m_adLambdaModifier7', default=1.0, help='Lambda modifier for temporal layer 7')

        # Quantization parameters
        p.add_option('-q', '--QP', action='store', type='float', dest='m_fQP', default=30.0, help='Qp value, if value is float, QP is switched once during encoding')
        p.add_option('-dqr', '--DeltaQpRD', action='store', type='int', dest='m_uiDeltaQpRD', default=0, help='max dQp offset for slice')
        p.add_option('-d', '--MaxDeltaQP', action='store', type='int', dest='m_iMaxDeltaQP', default=0, help='max dQp offset for block')
        p.add_option('-dqd', '--MaxCuDQPDepth', action='store', type='int', dest='m_iMaxCuDQPDepth', default=0, help='max depth for a minimum CuDQP')

        p.add_option('-cbqpofs', '--CbQpOffset', action='store', type='int', dest='m_cbQpOffset', default=0, help='Chroma Cb QP Offset')
        p.add_option('-crqpofs', '--CrQpOffset', action='store', type='int', dest='m_crQpOffset', default=0, help='Chroma Cr QP Offset')

        p.add_option('-aqps', '--AdaptiveQpSelection', action='store', type='boolean', dest='m_bUseAdaptQpSelect', default=False, help='AdaptiveQpSelection')

        p.add_option('-aq', '--AdaptiveQP', action='store', type='boolean', dest='m_bUseAdaptiveQP', default=False, help='QP adaptation based on a psycho-visual model')
        p.add_option('-aqr', '--MaxQPAdaptationRange', action='store', type='int', dest='m_iQPAdaptationRange', default=6, help='QP adaptation range')
        p.add_option('-m', '--dQPFile', action='store', type='string', dest='dQPFile', default='', help='dQP file name')
        p.add_option('--RDOQ', action='store', type='boolean', dest='m_bUseRDOQ', default=True, help='')
  
        # Entropy coding parameters
        p.add_option('--SBACRD', action='store', type='boolean', dest='m_bUseSBACRD', default=True, help='SBAC based RD estimation')
  
        # Deblocking filter parameters
        p.add_option('--LoopFilterDisable', action='store', type='boolean', dest='m_bLoopFilterDisable', default=False, help='')
        p.add_option('--LoopFilterOffsetInPPS', action='store', type='boolean', dest='m_loopFilterOffsetInPPS', default=False, help='')
        p.add_option('--LoopFilterBetaOffset_div2', action='store', type='int', dest='m_loopFilterBetaOffsetDiv2', default=0, help='')
        p.add_option('--LoopFilterTcOffset_div2', action='store', type='int', dest='m_loopFilterTcOffsetDiv2', default=0, help='')
        p.add_option('--DeblockingFilterControlPresent', action='store', type='boolean', dest='m_DeblockingFilterControlPresent', default=False, help='')

        # Coding tools
        p.add_option('--AMP', action='store', type='boolean', dest='m_enableAMP', default=True, help='Enable asymmetric motion partitions')
        p.add_option('--TS', action='store', type='boolean', dest='m_useTansformSkip', default=False, help='Intra transform skipping')
        p.add_option('--TSFast', action='store', type='boolean', dest='m_useTansformSkipFast', default=False, help='Fast intra transform skipping')
        p.add_option('--SAO', action='store', type='boolean', dest='m_bUseSAO', default=True, help='Enable Sample Adaptive Offset')
        p.add_option('--MaxNumOffsetsPerPic', action='store', type='int', dest='m_maxNumOffsetsPerPic', default=2048, help='Max number of SAO offset per picture (Default: 2048)')
        p.add_option('--SAOLcuBoundary', action='store', type='boolean', dest='m_saoLcuBoundary', default=False, help='0: right/bottom LCU boundary areas skipped from SAO parameter estimation, 1: non-deblocked pixels are used for those areas')
        p.add_option('--SAOLcuBasedOptimization', action='store', type='boolean', dest='m_saoLcuBasedOptimization', default=True, help='0: SAO picture-based optimization, 1: SAO LCU-based optimization ')
        p.add_option('--SliceMode', action='store', type='int', dest='m_iSliceMode', default=0, help='0: Disable all Recon slice limits, 1: Enforce max # of LCUs, 2: Enforce max # of bytes')
        p.add_option('--SliceArgument', action='store', type='int', dest='m_iSliceArgument', default=0, help='if SliceMode==1 SliceArgument represents max # of LCUs. if SliceMode==2 SliceArgument represents max # of bytes.')
        p.add_option('--DependentSliceMode', action='store', type='int', dest='m_iDependentSliceMode', default=0, help='0: Disable all dependent slice limits, 1: Enforce max # of LCUs, 2: Enforce constraint based dependent slices')
        p.add_option('--DependentSliceArgument', action='store', type='int', dest='m_iDependentSliceArgument', default=0, help='if DependentSliceMode==1 SliceArgument represents max # of LCUs. if DependentSliceMode==2 DependentSliceArgument represents max # of bins.')
        p.add_option('--CabacIndependentFlag', action='store', type='boolean', dest='m_bCabacIndependentFlag', default=False, help='')
        p.add_option('--LFCrossSliceBoundaryFlag', action='store', type='boolean', dest='m_bLFCrossSliceBoundaryFlag', default=True, help='')

        p.add_option('--ConstrainedIntraPred', action='store', type='boolean', dest='m_bUseConstrainedIntraPred', default=False, help='Constrained Intra Prediction')
        p.add_option('--PCMEnabledFlag', action='store', type='boolean', dest='m_usePCM', default=False, help='')
        p.add_option('--PCMLog2MaxSize', action='store', type='int', dest='m_pcmLog2MaxSize', default=5, help='')
        p.add_option('--PCMLog2MinSize', action='store', type='int', dest='m_uiPCMLog2MinSize', default=3, help='')

        p.add_option('--PCMInputBitDepthFlag', action='store', type='boolean', dest='m_bPCMInputBitDepthFlag', default=True, help='')
        p.add_option('--PCMFilterDisableFlag', action='store', type='boolean', dest='m_bPCMFilterDisableFlag', default=False, help='')
        p.add_option('--LosslessCuEnabled', action='store', type='boolean', dest='m_useLossless', default=False, help='')
        p.add_option('-wpP', '--weighted_pred_flag', action='store', type='boolean', dest='m_bUseWeightPred', default=False, help='weighted prediction flag (P-Slices)')
        p.add_option('-wpB', '--weighted_bipred_flag', action='store', type='boolean', dest='m_useWeightedBiPred', default=False, help='weighted bipred flag (B-Slices)')
        p.add_option('--Log2ParallelMergeLevel', action='store', type='int', dest='m_log2ParallelMergeLevel', default=2, help='Parallel merge estimation region')
        p.add_option('--UniformSpacingIdc', action='store', type='int', dest='m_iUniformSpacingIdr', default=0, help='Indicates if the column and row boundaries are distributed uniformly')
        p.add_option('--NumTileColumnsMinus1', action='store', type='int', dest='m_iNumColumnsMinus1', default=0, help='Number of columns in a picture minus 1')
        p.add_option('--ColumnWidthArray', action='store', type='string', dest='columnWidth', default='', help='Array containing ColumnWidth values in units of LCU')
        p.add_option('--NumTileRowsMinus1', action='store', type='int', dest='m_iNumRowsMinus1', default=0, help='Number of rows in a picture minus 1')
        p.add_option('--RowHeightArray', action='store', type='string', dest='rowHeight', default='', help='Array containing RowHeight values in units of LCU')
        p.add_option('--LFCrossTileBoundaryFlag', action='store', type='boolean', dest='m_bLFCrossTileBoundaryFlag', default=True, help='1: cross-tile-boundary loop filtering. 0:non-cross-tile-boundary loop filtering')
        p.add_option('--WaveFrontSynchro', action='store', type='int', dest='m_iWaveFrontSynchro', default=0, help='0: no synchro; 1 synchro with TR; 2 TRR etc')
        p.add_option('--ScalingList', action='store', type='int', dest='m_useScalingListId', default=0, help='0: no scaling list, 1: default scaling lists, 2: scaling lists specified in ScalingListFile')
        p.add_option('--ScalingListFile', action='store', type='string', dest='scalingListFile', default='', help='Scaling list file name')
        p.add_option('-SBH', '--SignHideFlag', action='store', type='int', dest='m_signHideFlag', default=1, help='')
        # Misc.
        p.add_option('--SEIpictureDigest', action='store', type='int', dest='m_pictureDigestEnabled', default=0, help='Control generation of picture_digest SEI messages\n\t3: checksum\n\t2: CRC\n\t1: use MD5\n\t0: disable')
        p.add_option('--TMVPMode', action='store', type='int', dest='m_TMVPModeId', default=1, help='TMVP mode 0: TMVP disable for all slices. 1: TMVP enable for all slices (default) 2: TMVP enable for certain slices only')
        p.add_option('--FEN', action='store', type='boolean', dest='m_bUseFastEnc', default=False, help='fast encoder setting')
        p.add_option('--ECU', action='store', type='boolean', dest='m_bUseEarlyCU', default=False, help='Early CU setting')
        p.add_option('--FDM', action='store', type='boolean', dest='m_useFastDecisionForMerge', default=True, help='Fast decision for Merge RD Cost')
        p.add_option('--CFM', action='store', type='boolean', dest='m_bUseCbfFastMode', default=False, help='Cbf fast mode setting')
        p.add_option('--ESD', action='store', type='boolean', dest='m_useEarlySkipDetection', default=False, help='Early SKIP detection setting')
        p.add_option('-rc', '--RateCtrl', action='store', type='boolean', dest='m_enableRateCtrl', default=False, help='Rate control on/off')
        p.add_option('-tbr', '--TargetBitrate', action='store', type='int', dest='m_targetBitrate', default=0, help='Input target bitrate')
        p.add_option('-nu', '--NumLCUInUnit', action='store', type='int', dest='m_numLCUInUnit', default=0, help='Number of LCUs in an Unit')

        p.add_option('--TransquantBypassEnableFlag', action='store', type='boolean', dest='m_TransquantBypassEnableFlag', default=False, help='transquant_bypass_enable_flag indicator in PPS')
        p.add_option('--CUTransquantBypassFlagValue', action='store', type='boolean', dest='m_CUTransquantBypassFlagValue', default=False, help='Fixed cu_transquant_bypass_flag value, when transquant_bypass_enable_flag is enabled')
        p.add_option('--RecalculateQPAccordingToLambda', action='store', type='boolean', dest='m_recalculateQPAccordingToLambda', default=False, help='Recalculate QP values according to lambda values. Do not suggest to be enabled in all intra case')

        for i in range(1, MAX_GOP+1):
            p.add_option('--Frame%d'%i, dest=self.m_GOPList[i-1], default=GOPEntry())

        opt, args = p.parse_args(argv[1:])

        for it in args:
            sys.stderr.write("Unhandled argument ignored: `%s'\n" % it)

        if not argv[1:]:
            # po::doHelp(cout, opts);
            return False
  
        # Set any derived parameters
        # convert std::string to c string for compatability
        self.m_pchInputFile = opt.inputFile
        self.m_pchBitstreamFile = opt.bitstreamFile
        self.m_pchReconFile = opt.reconFile
        self.m_pchdQPFile = opt.dQPFile
  
        self.m_pchColumnWidth = opt.columnWidth
        self.m_pchRowHeight = opt.rowHeight
        self.m_scalingListFile = opt.scalingListFile
  
        # TODO:ChromaFmt assumes 4:2:0 below
        if self.m_croppingMode == 0:
            # no cropping or padding
            self.m_cropLeft = self.m_cropRight = self.m_cropTop = self.m_cropBottom = 0
            self.m_aiPad = [0, 0]
        elif self.m_croppingMode == 1:
            # automatic padding to minimum CU size
            minCuSize = self.m_uiMaxCUHeight >> (self.m_uiMaxCUDepth - 1)
            if self.m_iSourceWidth % minCuSize:
                self.m_aiPad[0] = self.m_cropRight = ((self.m_iSourceWidth/minCuSize)+1) * minCuSize - self.m_iSourceWidth
                self.m_iSourceWidth += self.m_cropRight
            if self.m_iSourceHeight % minCuSize:
                self.m_aiPad[1] = self.m_cropBottom = ((self.m_iSourceHeight/minCuSize)+1) * minCuSize - self.m_iSourceHeight
                self.m_iSourceHeight += self.m_cropBottom
            if self.m_aiPad[0] % TComSPS::getCropUnitX(CHROMA_420) != 0:
                sys.stderr.write("Error: picture width is not an integer multiple of the specified chroma subsampling\n")
                sys.exit(False)
            if self.m_aiPad[1] % TComSPS::getCropUnitY(CHROMA_420) != 0:
                sys.stderr.write("Error: picture height is not an integer multiple of the specified chroma subsampling\n")
                sys.exit(False)
        elif self.m_croppingMode == 2:
            #padding
            self.m_iSourceWidth += self.m_aiPad[0]
            self.m_iSourceHeight += self.m_aiPad[1]
            self.m_cropRight = self.m_aiPad[0]
            self.m_cropBottom = self.m_aiPad[1]
        elif self.m_croppingMode == 3:
            # cropping
            if self.m_cropLeft == 0 and self.m_cropRight == 0 and \
               self.m_cropTop == 0 and self.m_cropBottom == 0:
                sys.stderr.write("Warning: Cropping enabled, but all cropping parameters set to zero\n")
            if self.m_aiPad[1] != 0 or self.m_aiPad[0] != 0:
                sys.stderr.write("Warning: Cropping enabled, padding parameters will be ignored\n")
            self.m_aiPad = [0, 0]
  
        # allocate slice-based dQP values
        self.m_aidQP = []
        for i in range(self.m_iFrameToBeEncoded + self.m_iGOPSize + 1):
            self.m_aidQP[i] = 0

        # handling of floating-point QP values
        # if QP is not integer, sequence is split into two sections having QP and QP+1
        self.m_iQP = int(self.m_fQP)
        if self.m_iQP < self.m_fQP:
            iSwitchPOC = int(self.m_iFrameToBeEncoded - (self.m_fQP - self.m_iQP) * self.m_iFrameToBeEncoded + 0.5)
            iSwitchPOC = int(iSwitchPOC / self.m_iGOPSize + 0.5) * self.m_iGOPSize
            for i in range(iSwitchPOC, self.m_iFrameToBeEncoded + self.m_iGOPSize + 1):
                self.m_aidQP[i] = 1
  
        # reading external dQP description from file
        if self.m_pchdQPFile:
            fpt = open(self.m_pchdQPFile, "r")
            if fpt:
                Int iValue
                iPOC = 0
                while iPOC < self.m_iFrameToBeEncoded:
                    if ( fscanf(fpt, "%d", &iValue ) == EOF ) break;
                    self.m_aidQP[iPOC] = iValue
                    iPOC += 1
            fpt.close()
        self.m_iWaveFrontSubstreams = (self.m_iSourceHeight + self.m_uiMaxCUHeight - 1) / self.m_uiMaxCUHeight if self.m_iWaveFrontSynchro else 1
        if self.m_iDependentSliceMode:
            self.m_iWaveFrontSubstreams = 1
        # check validity of input parameters
        self._xCheckParameter()

        # set global varibles
        self._xSetGlobal()

        # print-out parameters
        self._xPrintParameter()

        return True

    def _xCheckParameter(self):
        def confirmPara(bflag, message):
            if not bflag
                return False
        
            sys.stdout.write("Error: %s\n" % message)
            return True

        if not self.m_pictureDigestEnabled:
            sys.stderr.write("*************************************************************\n")
            sys.stderr.write("** WARNING: --SEIpictureDigest is now disabled by default. **\n")
            sys.stderr.write("**          Automatic verification of decoded pictures by  **\n")
            sys.stderr.write("**          a decoder requires this option to be enabled.  **\n")
            sys.stderr.write("*************************************************************\n")

        check_failed = False # abort if there is a fatal configuration problem
        xConfirmPara = lambda a, b: check_failed |= confirmPara(a, b)
        # check range of parameters
        xConfirmPara(self.m_uiInputBitDepth < 8,                  "InputBitDepth must be at least 8")
        xConfirmPara(self.m_iFrameRate <= 0,                      "Frame rate must be more than 1")
        xConfirmPara(self.m_iFrameToBeEncoded <= 0,               "Total Number Of Frames encoded must be more than 0")
        xConfirmPara(self.m_iGOPSize < 1,                         "GOP Size must be greater or equal to 1")
        xConfirmPara(self.m_iGOPSize > 1 and self.m_iGOPSize % 2, "GOP Size must be a multiple of 2, if GOP Size is greater than 1")
        xConfirmPara((self.m_iIntraPeriod > 0 and self.m_iIntraPeriod < self.m_iGOPSize) or self.m_iIntraPeriod == 0,
                     "Intra period must be more than GOP size, or -1 , not 0")
        xConfirmPara(self.m_iDecodingRefreshType < 0 or self.m_iDecodingRefreshType > 2,
                     "Decoding Refresh Type must be equal to 0, 1 or 2")
        xConfirmPara(self.m_iQP < -6 * (self.m_uiInternalBitDepth - 8) or self.m_iQP > 51,
                     "QP exceeds supported range (-QpBDOffsety to 51)")
        xConfirmPara(self.m_loopFilterBetaOffsetDiv2 < -13 or self.m_loopFilterBetaOffsetDiv2 > 13,
                     "Loop Filter Beta Offset div. 2 exceeds supported range (-13 to 13)")
        xConfirmPara(self.m_loopFilterTcOffsetDiv2 < -13 or self.m_loopFilterTcOffsetDiv2 > 13,
                     "Loop Filter Tc Offset div. 2 exceeds supported range (-13 to 13)")
        xConfirmPara(self.m_iFastSearch < 0 or self.m_iFastSearch > 2, "Fast Search Mode is not supported value (0:Full search  1:Diamond  2:PMVFAST)")
        xConfirmPara(self.m_iSearchRange < 0,                          "Search Range must be more than 0")
        xConfirmPara(self.m_bipredSearchRange < 0,                     "Search Range must be more than 0")
        xConfirmPara(self.m_iMaxDeltaQP > 7,                           "Absolute Delta QP exceeds supported range (0 to 7)")
        xConfirmPara(self.m_iMaxCuDQPDepth > self.m_uiMaxCUDepth - 1,  "Absolute depth for a minimum CuDQP exceeds maximum coding unit depth")

        xConfirmPara(self.m_cbQpOffset < -12, "Min. Chroma Cb QP Offset is -12")
        xConfirmPara(self.m_cbQpOffset >  12, "Max. Chroma Cb QP Offset is  12")
        xConfirmPara(self.m_crQpOffset < -12, "Min. Chroma Cr QP Offset is -12")
        xConfirmPara(self.m_crQpOffset >  12, "Max. Chroma Cr QP Offset is  12")

        xConfirmPara(self.m_iQPAdaptationRange <= 0, "QP Adaptation Range must be more than 0" );
        if self.m_iDecodingRefreshType == 2:
            xConfirmPara(self.m_iIntraPeriod > 0 and self.m_iIntraPeriod <= self.m_iGOPSize,
                         "Intra period must be larger than GOP size for periodic IDR pictures")
        xConfirmPara((self.m_uiMaxCUWidth >> self.m_uiMaxCUDepth) < 4,  "Minimum partition width size should be larger than or equal to 8")
        xConfirmPara((self.m_uiMaxCUHeight >> self.m_uiMaxCUDepth) < 4, "Minimum partition height size should be larger than or equal to 8")
        xConfirmPara(self.m_uiMaxCUWidth < 16,                          "Maximum partition width size should be larger than or equal to 16")
        xConfirmPara(self.m_uiMaxCUHeight < 16,                         "Maximum partition height size should be larger than or equal to 16")
        xConfirmPara((self.m_iSourceWidth % (self.m_uiMaxCUWidth  >> (self.m_uiMaxCUDepth-1))) != 0,
                     "Resulting coded frame width must be a multiple of the minimum CU size")
        xConfirmPara((self.m_iSourceHeight % (self.m_uiMaxCUHeight >> (self.m_uiMaxCUDepth-1))) != 0,
                     "Resulting coded frame height must be a multiple of the minimum CU size")

        xConfirmPara(self.m_uiQuadtreeTULog2MinSize < 2, "QuadtreeTULog2MinSize must be 2 or greater.")
        xConfirmPara(self.m_uiQuadtreeTULog2MinSize > 5, "QuadtreeTULog2MinSize must be 5 or smaller.")
        xConfirmPara(self.m_uiQuadtreeTULog2MaxSize < 2, "QuadtreeTULog2MaxSize must be 2 or greater.")
        xConfirmPara(self.m_uiQuadtreeTULog2MaxSize > 5, "QuadtreeTULog2MaxSize must be 5 or smaller.")
        xConfirmPara(self.m_uiQuadtreeTULog2MaxSize < self.m_uiQuadtreeTULog2MinSize,
                     "QuadtreeTULog2MaxSize must be greater than or equal to m_uiQuadtreeTULog2MinSize.")
        xConfirmPara((1<<self.m_uiQuadtreeTULog2MinSize) > (self.m_uiMaxCUWidth>>(self.m_uiMaxCUDepth-1)),
                     "QuadtreeTULog2MinSize must not be greater than minimum CU size")
        xConfirmPara((1<<self.m_uiQuadtreeTULog2MinSize) > (self.m_uiMaxCUHeight>>(self.m_uiMaxCUDepth-1)),
                     "QuadtreeTULog2MinSize must not be greater than minimum CU size")
        xConfirmPara((1<<self.m_uiQuadtreeTULog2MinSize) > (self.m_uiMaxCUWidth>>self.m_uiMaxCUDepth),
                     "Minimum CU width must be greater than minimum transform size." )
        xConfirmPara((1<<self.m_uiQuadtreeTULog2MinSize) > (self.m_uiMaxCUHeight>>self.m_uiMaxCUDepth),
                     "Minimum CU height must be greater than minimum transform size.")
        xConfirmPara(self.m_uiQuadtreeTUMaxDepthInter < 1, "QuadtreeTUMaxDepthInter must be greater than or equal to 1")
        xConfirmPara(self.m_uiQuadtreeTUMaxDepthInter > self.m_uiQuadtreeTULog2MaxSize - self.m_uiQuadtreeTULog2MinSize + 1,
                     "QuadtreeTUMaxDepthInter must be less than or equal to the difference between QuadtreeTULog2MaxSize and QuadtreeTULog2MinSize plus 1")
        xConfirmPara(self.m_uiQuadtreeTUMaxDepthIntra < 1, "QuadtreeTUMaxDepthIntra must be greater than or equal to 1")
        xConfirmPara(self.m_uiQuadtreeTUMaxDepthIntra > self.m_uiQuadtreeTULog2MaxSize - self.m_uiQuadtreeTULog2MinSize + 1,
                     "QuadtreeTUMaxDepthIntra must be less than or equal to the difference between QuadtreeTULog2MaxSize and QuadtreeTULog2MinSize plus 1")

        xConfirmPara(self.m_bUseAdaptQpSelect == true and self.m_iQP < 0, 
                     "AdaptiveQpSelection must be disabled when QP < 0.")
        xConfirmPara(self.m_bUseAdaptQpSelect == true and (self.m_cbQpOffset !=0 or self._crQpOffset != 0),
                     "AdaptiveQpSelection must be disabled when ChromaQpOffset is not equal to 0.")

        if self.m_usePCM:
            xConfirmPara(self.m_uiPCMLog2MinSize < 3,                     "PCMLog2MinSize must be 3 or greater.")
            xConfirmPara(self.m_uiPCMLog2MinSize > 5,                     "PCMLog2MinSize must be 5 or smaller.")
            xConfirmPara(self.m_pcmLog2MaxSize > 5,                       "PCMLog2MaxSize must be 5 or smaller.")
            xConfirmPara(self.m_pcmLog2MaxSize < self.m_uiPCMLog2MinSize, "PCMLog2MaxSize must be equal to or greater than m_uiPCMLog2MinSize.")

        xConfirmPara(self.m_iSliceMode < 0 or self.m_iSliceMode > 3, "SliceMode exceeds supported range (0 to 3)")
        if self.m_iSliceMode != 0:
            xConfirmPara(self.m_iSliceArgument < 1, "SliceArgument should be larger than or equal to 1")
        xConfirmPara(self.m_iDependentSliceMode < 0 or self.m_iDependentSliceMode > 2, "DependentSliceMode exceeds supported range (0 to 2)")
        if self.m_iDependentSliceMode != 0:
            xConfirmPara(self.m_iDependentSliceArgument < 1, "DependentSliceArgument should be larger than or equal to 1")
  
        tileFlag = self.m_iNumColumnsMinus1 > 0 or self.m_iNumRowsMinus1 > 0
        xConfirmPara(tileFlag and self.m_iDependentSliceMode, "Tile and Dependent Slice can not be applied together")
        xConfirmPara(tileFlag and self.m_iWaveFrontSynchro,   "Tile and Wavefront can not be applied together")
        xConfirmPara(self.m_iWaveFrontSynchro and self.m_bCabacIndependentFlag,
                     "Wavefront and CabacIndependentFlag can not be applied together")

        #TODO:ChromaFmt assumes 4:2:0 below
        xConfirmPara(self.m_iSourceWidth % TComSPS::getCropUnitX(CHROMA_420) != 0,
                     "Picture width must be an integer multiple of the specified chroma subsampling")
        xConfirmPara(self.m_iSourceHeight % TComSPS::getCropUnitY(CHROMA_420) != 0,
                     "Picture height must be an integer multiple of the specified chroma subsampling")

        xConfirmPara(self.m_aiPad[0] % TComSPS::getCropUnitX(CHROMA_420) != 0,
                     "Horizontal padding must be an integer multiple of the specified chroma subsampling")
        xConfirmPara(self.m_aiPad[1] % TComSPS::getCropUnitY(CHROMA_420) != 0,
                     "Vertical padding must be an integer multiple of the specified chroma subsampling")

        xConfirmPara(self.m_cropLeft % TComSPS::getCropUnitX(CHROMA_420) != 0,
                     "Left cropping must be an integer multiple of the specified chroma subsampling")
        xConfirmPara(self.m_cropRight % TComSPS::getCropUnitX(CHROMA_420) != 0,
                     "Right cropping must be an integer multiple of the specified chroma subsampling")
        xConfirmPara(self.m_cropTop % TComSPS::getCropUnitY(CHROMA_420) != 0,
                     "Top cropping must be an integer multiple of the specified chroma subsampling")
        xConfirmPara(self.m_cropBottom % TComSPS::getCropUnitY(CHROMA_420) != 0,
                     "Bottom cropping must be an integer multiple of the specified chroma subsampling")

        # max CU width and height should be power of 2
        ui = self.m_uiMaxCUWidth
        while ui:
            ui >>= 1
            if (ui & 1) == 1:
                xConfirmPara(ui != 1, "Width should be 2^n")
        ui = self.m_uiMaxCUHeight
        while ui:
            ui >>= 1
            if (ui & 1) == 1:
                xConfirmPara(ui != 1, "Height should be 2^n")
  
        verifiedGOP = False
        errorGOP = False
        checkGOP = 1
        numRefs = 1
        refList = [0]
        isOK = []
        for i range(MAX_GOP):
            isOK[i] = False
        numOK = 0
        xConfirmPara(self.m_iIntraPeriod >= 0 and (self.m_iIntraPeriod % self.m_iGOPSize != 0),
                     "Intra period must be a multiple of GOPSize, or -1")

        for i in range(self.m_iGOPSize):
            if self.m_GOPList[i].m_POC == self.m_iGOPSize:
                xConfirmPara(self.m_GOPList[i].m_temporalId != 0,
                             "The last frame in each GOP must have temporal ID = 0 ")

        self.m_extraRPSs = 0
        #start looping through frames in coding order until we can verify that the GOP structure is correct.
        while not verifiedGOP and not errorGOP:
            curGOP = (checkGOP-1) % self.m_iGOPSize
            curPOC = ((checkGOP-1)/self.m_iGOPSize) * self.m_iGOPSize + self.m_GOPList[curGOP].m_POC
            if self.m_GOPList[curGOP].m_POC < 0:
                sys.stdout.write("\nError: found fewer Reference Picture Sets than GOPSize\n")
                errorGOP = True
            else:
                #check that all reference pictures are available, or have a POC < 0 meaning they might be available in the next GOP.
                beforeI = False
                for i in range(self.m_GOPList[curGOP].m_numRefPics):
                    absPOC = curPOC + self.m_GOPList[curGOP].m_referencePics[i]
                    if absPOC < 0:
                        beforeI = True
                    else:
                        found = False
                        for j in range(numRefs):
                            if refList[j] == absPOC:
                                found = True
                                for k in range(self.m_iGOPSize):
                                    if absPOC % self.m_iGOPSize == self.m_GOPList[k].m_POC % self.m_iGOPSize:
                                        self.m_GOPList[curGOP].m_usedByCurrPic[i] = self.m_GOPList[k].m_temporalId <= self.m_GOPList[curGOP].m_temporalId
                        if not found:
                            sys.stdout.write("\nError: ref pic %d is not available for GOP frame %d\n" %
                                             (self.m_GOPList[curGOP].m_referencePics[i],curGOP + 1)
                            errorGOP = True
                if not beforeI and not errorGOP:
                    #all ref frames were present
                    if not isOK[curGOP]:
                        numOK += 1
                        isOK[curGOP] = True
                        if numOK == self.m_iGOPSize:
                            verifiedGOP = True
                else:
                    #create a new GOPEntry for this frame containing all the reference pictures that were available (POC > 0)
                    self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs] = self.m_GOPList[curGOP]
                    newRefs = 0
                    for i in range(self.m_GOPList[curGOP].m_numRefPics):
                        absPOC = curPOC + self.m_GOPList[curGOP].m_referencePics[i]
                        if absPOC >= 0:
                            self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[newRefs] = self.m_GOPList[curGOP].m_referencePics[i]
                            self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_usedByCurrPic[newRefs] = self.m_GOPList[curGOP].m_usedByCurrPic[i]
                            newRefs += 1
                    numPrefRefs = self.m_GOPList[curGOP].m_numRefPicsActive

                    for offset in range(-1, -checkGOP, -1):
                        #step backwards in coding order and include any extra available pictures we might find useful to replace the ones with POC < 0.
                        offGOP = (checkGOP-1+offset) % self.m_iGOPSize
                        offPOC = ((checkGOP-1+offset)/self.m_iGOPSize) * self.m_iGOPSize + self.m_GOPList[offGOP].m_POC
                        if offPOC >= 0 and self.m_GOPList[offGOP].m_refPic and \
                           self.m_GOPList[offGOP].m_temporalId <= self.m_GOPList[curGOP].m_temporalId:
                            newRef = False
                            for i in range(numRefs):
                                if refList[i] == offPOC:
                                    newRef = True
                            for i in range(newRefs):
                                if self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[i] == offPOC - curPOC:
                                    newRef = False
                            if newRef:
                                insertPoint = newRefs
                                #this picture can be added, find appropriate place in list and insert it.
                                for j in range(newRefs):
                                    if self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[j] < offPOC - curPOC or \
                                       self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[j] > 0:
                                    insertPoint = j
                                    break
                                prev = offPOC - curPOC
                                prevUsed = self.m_GOPList[offGOP].m_temporalId <= self.m_GOPList[curGOP].m_temporalId
                                for j in range(insertPoint, newRefs+1):
                                    newPrev = self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[j]
                                    newUsed = self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_usedByCurrPic[j]
                                    self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[j] = prev
                                    self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_usedByCurrPic[j] = prevUsed
                                    prevUsed = newUsed
                                    prev = newPrev
                                newRefs += 1
                        if newRefs >= numPrefRefs:
                            break
                    self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_numRefPics = newRefs
                    self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_POC = curPOC
                    if self.m_extraRPSs == 0:
                        self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_interRPSPrediction = 0
                        self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_numRefIdc = 0
                    else:
                        rIdx = self.m_iGOPSize + self.m_extraRPSs - 1
                        refPOC = self.m_GOPList[rIdx].m_POC
                        refPics = self.m_GOPList[rIdx].m_numRefPics
                        newIdc = 0
                        for i in range(refPics):
                            deltaPOC = self.m_GOPList[rIdx].m_referencePics[i] if i != refPics else 0 # check if the reference abs POC is >= 0
                            absPOCref = refPOC + deltaPOC
                            refIdc = 0
                            for j in range(self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_numRefPics):
                                if (absPOCref - curPOC) == self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_referencePics[j]:
                                    if self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_usedByCurrPic[j]:
                                        refIdc = 1
                                    else:
                                        refIdc = 2
                            self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_refIdc[newIdc] = refIdc
                            newIdc += 1
                        self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_interRPSPrediction = 1
                        self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_numRefIdc = newIdc
                        self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_deltaRPS = refPOC - self.m_GOPList[self.m_iGOPSize+self.m_extraRPSs].m_POC
                    curGOP = self.m_iGOPSize + self.m_extraRPSs
                    self.m_extraRPSs += 1
                numRefs = 0
                for i in range(self.m_GOPList[curGOP].m_numRefPics):
                    absPOC = curPOC + self.m_GOPList[curGOP].m_referencePics[i]
                    if absPOC >= 0:
                        refList[numRefs] = absPOC
                        numRefs += 1
                refList[numRefs] = curPOC
                numRefs += 1
            checkGOP += 1
        xConfirmPara(errorGOP, "Invalid GOP structure given")
        self.m_maxTempLayer = 1
        for i in range(self.m_iGOPSize):
            if self.m_GOPList[i].m_temporalId >= self.m_maxTempLayer:
                self.m_maxTempLayer = self.m_GOPList[i].m_temporalId + 1
            xConfirmPara(self.m_GOPList[i].m_sliceType != 'B' and self.m_GOPList[i].m_sliceType != 'P',
                         "Slice type must be equal to B or P")
        for i in range(MAX_TLAYER):
            self.m_numReorderPics[i] = 0
            self.m_maxDecPicBuffering[i] = 0
        for i in range(self.m_iGOPSize):
            if self.m_GOPList[i].m_numRefPics > self.m_maxDecPicBuffering[self.m_GOPList[i].m_temporalId]:
                self.m_maxDecPicBuffering[self.m_GOPList[i].m_temporalId] = self.m_GOPList[i].m_numRefPics
            highestDecodingNumberWithLowerPOC = 0
            for j in range(self.m_iGOPSize):
                if self.m_GOPList[j].m_POC <= self.m_GOPList[i].m_POC:
                    highestDecodingNumberWithLowerPOC = j
            numReorder = 0
            for j in range(highestDecodingNumberWithLowerPOC):
                if self.m_GOPList[j].m_temporalId <= self.m_GOPList[i].m_temporalId and \
                   self.m_GOPList[j].m_POC > self.m_GOPList[i].m_POC:
                    numReorder += 1
            if numReorder > self.m_numReorderPics[self.m_GOPList[i].m_temporalId]:
                self.m_numReorderPics[self.m_GOPList[i].m_temporalId] = numReorder
        for i in range(MAX_TLAYER-1):
            # a lower layer can not have higher value of m_numReorderPics than a higher layer
            if self.m_numReorderPics[i+1] < self.m_numReorderPics[i]:
                self.m_numReorderPics[i+1] = self.m_numReorderPics[i]
            # the value of num_reorder_pics[ i ] shall be in the range of 0 to max_dec_pic_buffering[ i ], inclusive
            if self.m_numReorderPics[i] > self.m_maxDecPicBuffering[i]:
                self.m_maxDecPicBuffering[i] = self.m_numReorderPics[i]
            # a lower layer can not have higher value of m_uiMaxDecPicBuffering than a higher layer
            if self.m_maxDecPicBuffering[i+1] < self.m_maxDecPicBuffering[i]:
                self.m_maxDecPicBuffering[i+1] = self.m_maxDecPicBuffering[i]
        # the value of num_reorder_pics[ i ] shall be in the range of 0 to max_dec_pic_buffering[ i ], inclusive
        if self.m_numReorderPics[MAX_TLAYER-1] > self.m_maxDecPicBuffering[MAX_TLAYER-1]:
            self.m_maxDecPicBuffering[MAX_TLAYER-1] = self.m_numReorderPics[MAX_TLAYER-1]

        xConfirmPara(self.m_bUseLComb == False and self.m_numReorderPics[MAX_TLAYER-1] != 0,
                     "ListCombination can only be 0 in low delay coding (more precisely when L0 and L1 are identical)")
                     # Note however this is not the full necessary condition as ref_pic_list_combination_flag can only be 0 if L0 == L1.
        xConfirmPara(self.m_iWaveFrontSynchro < 0, "WaveFrontSynchro cannot be negative")
        xConfirmPara(self.m_iWaveFrontSubstreams <= 0, "WaveFrontSubstreams must be positive")
        xConfirmPara(self.m_iWaveFrontSubstreams > 1 and not self.m_iWaveFrontSynchro, "Must have WaveFrontSynchro > 0 in order to have WaveFrontSubstreams > 1")

        xConfirmPara(self.m_pictureDigestEnabled < 0 or self.m_pictureDigestEnabled > 3, "this hash type is not correct!\n")

        if self.m_enableRateCtrl:
            numLCUInWidth = (self.m_iSourceWidth / self.m_uiMaxCUWidth) + (1 if (self.m_iSourceWidth % self.m_uiMaxCUWidth) else 0)
            numLCUInHeight = (self.m_iSourceHeight / self.m_uiMaxCUHeight) + (1 if (self.m_iSourceHeight % self.m_uiMaxCUHeight) else 0)
            numLCUInPic = numLCUInWidth * numLCUInHeight

            xConfirmPara((numLCUInPic % self.m_numLCUInUnit) != 0, "total number of LCUs in a frame should be completely divided by NumLCUInUnit")

            self.m_iMaxDeltaQP = MAX_DELTA_QP
            self.m_iMaxCuDQPDepth = MAX_CUDQP_DEPTH

        xConfirmPara(not self.m_TransquantBypassEnableFlag and self.m_CUTransquantBypassFlagValue, "CUTransquantBypassFlagValue cannot be 1 when TransquantBypassEnableFlag is 0")

        xConfirmPara(self.m_log2ParallelMergeLevel < 2, "Log2ParallelMergeLevel should be larger than or equal to 2")

        if check_failed:
            sys.exit(False)

    def _xSetGlobal(self):
        # set max CU width & height
        cvar.g_uiMaxCUWidth = self.m_uiMaxCUWidth
        cvar.g_uiMaxCUHeight = self.m_uiMaxCUHeight

        # compute actual CU depth with respect to config depth and max transform size
        cvar.g_uiAddCUDepth = 0
        while (self.m_uiMaxCUWidth >> self.m_uiMaxCUDepth) >
              (1 << (self.m_uiQuadtreeTULog2MinSize + cvar.g_uiAddCUDepth)):
            cvar.g_uiAddCUDepth += 1

        self.m_uiMaxCUDepth += cvar.g_uiAddCUDepth
        cvar.g_uiAddCUDepth += 1
        cvar.g_uiMaxCUDepth = self.m_uiMaxCUDepth

        # set internal bit-depth and constants
        cvar.g_uiBitDepth = 8
        cvar.g_uiBitIncrement = self.m_uiInternalBitDepth - cvar.g_uiBitDepth

        cvar.g_uiBASE_MAX = (1 << cvar.g_uiBitDepth) - 1
        cvar.g_uiIBDI_MAX = (1 << (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)) - 1

        if self.m_uiOutputBitDepth == 0:
            self.m_uiOutputBitDepth = self.m_uiInternalBitDepth

        cvar.g_uiPCMBitDepthLuma = self.m_uiPCMBitDepthLuma = self.m_uiInputBitDepth if self.m_bPCMInputBitDepthFlag else self.m_uiInternalBitDepth
        cvar.g_uiPCMBitDepthChroma = self.m_uiInputBitDepth if self.m_bPCMInputBitDepthFlag else self.m_uiInternalBitDepth

    def _xPrintParameter(self):
        sys.stdout.write("\n")
        sys.stdout.write("Input          File          : %s\n" % self.m_pchInputFile)
        sys.stdout.write("Bitstream      File          : %s\n" % self.m_pchBitstreamFile)
        sys.stdout.write("Reconstruction File          : %s\n" % self.m_pchReconFile)
        sys.stdout.write("Real     Format              : %dx%d %dHz\n" % (self.m_iSourceWidth - self.m_cropLeft - self.m_cropRight, self.m_iSourceHeight - self.m_cropTop - self.m_cropBottom, self.m_iFrameRate))
        sys.stdout.write("Internal Format              : %dx%d %dHz\n" % (self.m_iSourceWidth, self.m_iSourceHeight, self.m_iFrameRate))
        sys.stdout.write("Frame index                  : %u - %d (%d frames)\n" % (self.m_FrameSkip, self.m_FrameSkip + self.m_iFrameToBeEncoded - 1, self.m_iFrameToBeEncoded))
        sys.stdout.write("CU size / depth              : %d / %d\n" % (self.m_uiMaxCUWidth, self.m_uiMaxCUDepth))
        sys.stdout.write("RQT trans. size (min / max)  : %d / %d\n" % (1 << self.m_uiQuadtreeTULog2MinSize, 1 << self.m_uiQuadtreeTULog2MaxSize))
        sys.stdout.write("Max RQT depth inter          : %d\n" % self.m_uiQuadtreeTUMaxDepthInter)
        sys.stdout.write("Max RQT depth intra          : %d\n" % self.m_uiQuadtreeTUMaxDepthIntra)
        sys.stdout.write("Min PCM size                 : %d\n" % (1 << self.m_uiPCMLog2MinSize))
        sys.stdout.write("Motion search range          : %d\n" % self.m_iSearchRange)
        sys.stdout.write("Intra period                 : %d\n" % self.m_iIntraPeriod)
        sys.stdout.write("Decoding refresh type        : %d\n" % self.m_iDecodingRefreshType)
        sys.stdout.write("QP                           : %5.2f\n" % self.m_fQP)
        sys.stdout.write("Max dQP signaling depth      : %d\n" % self.m_iMaxCuDQPDepth)

        sys.stdout.write("Cb QP Offset                 : %d\n" % self.m_cbQpOffset)
        sys.stdout.write("Cr QP Offset                 : %d\n" % self.m_crQpOffset)

        sys.stdout.write("QP adaptation                : %d (range=%d)\n" % (self.m_bUseAdaptiveQP, self.m_iQPAdaptationRange if self.m_bUseAdaptiveQP else 0))
        sys.stdout.write("GOP size                     : %d\n" % self.m_iGOPSize)
        sys.stdout.write("Internal bit depth           : %d\n" % self.m_uiInternalBitDepth)
        sys.stdout.write("PCM sample bit depth         : %d\n" % self.m_uiPCMBitDepthLuma)
        sys.stdout.write("RateControl                  : %d\n" % self.m_enableRateCtrl)
        if self.m_enableRateCtrl:
            sys.stdout.write("TargetBitrate                : %d\n" % self.m_targetBitrate)
            sys.stdout.write("NumLCUInUnit                 : %d\n" % self.m_numLCUInUnit)
        sys.stdout.write("\n")

        sys.stdout.write("TOOL CFG: ")
        sys.stdout.write("IBD:%d " % (not not cvar.g_uiBitIncrement))
        sys.stdout.write("HAD:%d " % self.m_bUseHADME)
        sys.stdout.write("SRD:%d " % self.m_bUseSBACRD)
        sys.stdout.write("RDQ:%d " % self.m_bUseRDOQ)
        sys.stdout.write("SQP:%d " % self.m_uiDeltaQpRD)
        sys.stdout.write("ASR:%d " % self.m_bUseASR)
        sys.stdout.write("LComb:%d " % self.m_bUseLComb)
        sys.stdout.write("FEN:%d " % self.m_bUseFastEnc)
        sys.stdout.write("ECU:%d " % self.m_bUseEarlyCU)
        sys.stdout.write("FDM:%d " % self.m_useFastDecisionForMerge)
        sys.stdout.write("CFM:%d " % self.m_bUseCbfFastMode)
        sys.stdout.write("ESD:%d " % self.m_useEarlySkipDetection)
        sys.stdout.write("RQT:%d " % 1)
        sys.stdout.write("TS:%d " % self.m_useTansformSkip)
        sys.stdout.write("TSFast:%d " % self.m_useTansformSkipFast)
        sys.stdout.write("Slice: M=%d " % self.m_iSliceMode)
        if self.m_iSliceMode != 0:
            sys.stdout.write("A=%d " % self.m_iSliceArgument)
        sys.stdout.write("DependentSlice: M=%d " % self.m_iDependentSliceMode)
        if self.m_iDependentSliceMode != 0:
            sys.stdout.write("A=%d " % self.m_iDependentSliceArgument)
        sys.stdout.write("CIP:%d " % self.m_bUseConstrainedIntraPred)
        sys.stdout.write("SAO:%d " % (1 if self.m_bUseSAO else 0))
        sys.stdout.write("PCM:%d " % (1 if self.m_usePCM and (1<<self.m_uiPCMLog2MinSize) <= self.m_uiMaxCUWidth else 0))
        sys.stdout.write("SAOLcuBasedOptimization:%d " % (1 if self.m_saoLcuBasedOptimization else 0))

        sys.stdout.write("LosslessCuEnabled:%d " % (1 if self.m_useLossless else 0))
        sys.stdout.write("WPP:%d " % self.m_bUseWeightPred)
        sys.stdout.write("WPB:%d " % self.m_useWeightedBiPred)
        sys.stdout.write("PME:%d " % self.m_log2ParallelMergeLevel)
        sys.stdout.write(" WaveFrontSynchro:%d WaveFrontSubstreams:%d" %
                         (self.m_iWaveFrontSynchro, self.m_iWaveFrontSubstreams))
        sys.stdout.write(" ScalingList:%d " % self.m_useScalingListId)
        sys.stdout.write("TMVPMode:%d " % self.m_TMVPModeId)
        sys.stdout.write("AQpS:%d" % self.m_bUseAdaptQpSelect)

        sys.stdout.write(" SignBitHidingFlag:%d " % self.m_signHideFlag)
        sys.stdout.write("RecalQP:%d" % (1 if self.m_recalculateQPAccordingToLambda else 0))
        sys.stdout.write("\n\n")

        sys.stdout.flush()
