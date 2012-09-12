# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TypeDef.py
    HM 8.0 Python Implementation
"""

SAO_LUM_CHROMA_ONOFF_FLAGS       = 1  # J0087: slice-level independent luma/chroma SAO on/off flag 
LTRP_IN_SPS                      = 1  # J0116: Include support for signalling LTRP LSBs in the SPS, and index them in the slice header.
CHROMA_QP_EXTENSION              = 1  # J0342: Extend mapping table from luma QP to chroma QP, introduce slice-level chroma offsets, apply limits on offset values
SIMPLE_LUMA_CBF_CTX_DERIVATION   = 1  # J0303: simplified luma_CBF context derivation

COEF_REMAIN_BIN_REDUCTION        = 3  # J0142: Maximum codeword length of coeff_abs_level_remaining reduced to 32.
                                      # COEF_REMAIN_BIN_REDUCTION is also used to indicate the level at which the VLC 
                                      # transitions from Golomb-Rice to TU+EG(k)

CU_DQP_TU_EG                     = 1  # J0089: Bin reduction for delta QP coding
if CU_DQP_TU_EG:
	CU_DQP_TU_CMAX               = 5  #max number bins for truncated unary
	CU_DQP_EG_k                  = 0  #expgolomb order

NAL_UNIT_HEADER                  = 1  # J0550: Define nal_unit_header() method
REMOVE_NAL_REF_FLAG              = 1  # J0550: Remove nal_ref_flag, and allocate extra bit to reserved bits, and re-order syntax to put reserved bits after nal_unit_type
TEMPORAL_ID_PLUS1                = 1  # J0550: Signal temporal_id_plus1 instead of temporal_id in NAL unit, and change reserved_one_5bits
                                      #        value to zero
REFERENCE_PICTURE_DEFN           = 1  # J0118: Reflect change of defn. of referece picture in semantics of delta_poc_msb_present_flag
MOVE_LOOP_FILTER_SLICES_FLAG     = 1  # J0288: Move seq_loop_filter_across_slices_enabled_flag from SPS to PPS
SPLICING_FRIENDLY_PARAMS         = 1  # J0108: Remove rap_pic_id and move no_output_prior_pic_flag

SKIP_FLAG                        = 1  # J0336: store skip flag

PPS_TS_FLAG                      = 1  # J0184: move transform_skip_enabled_flag from SPS to PPS
if PPS_TS_FLAG:
	TS_FLAT_QUANTIZATION_MATRIX  = 1  # I0408: set default quantization matrix to be flat if TS is enabled in PPS
INTER_TRANSFORMSKIP              = 1  # J0237: inter transform skipping (inter-TS)
INTRA_TRANSFORMSKIP_FAST         = 1  # J0572: fast encoding for intra transform skipping

REMOVAL_8x2_2x8_CG               = 1  # J0256: removal of 8x2 / 2x8 coefficient groups
REF_IDX_BYPASS                   = 1  # J0098: bypass coding starting from the second bin for reference index

RECALCULATE_QP_ACCORDING_LAMBDA  = 1  # J0242: recalculate QP value according to lambda value
TU_ZERO_CBF_RDO                  = 1  # J0241: take the bits to represent zero cbf into consideration when doing TU RDO
REMOVE_NUM_GREATER1              = 1  # J0408: numGreater1 removal and ctxset decision with c1 

INTRA_TRANS_SIMP                 = 1  # J0035: Use DST for 4x4 luma intra TU's (regardless of the intra prediction direction)

J0234_INTER_RPS_SIMPL            = 1  # J0234: Do not signal delta_idx_minus1 when building the RPS-list in SPS
NUM_WP_LIMIT                     = 1  # J0571: number of total signalled weight flags <=24
DISALLOW_BIPRED_IN_8x4_4x8PUS    = 1  # J0086: disallow bi-pred for 8x4 and 4x8 inter PUs
SAO_SINGLE_MERGE                 = 1  # J0355: Single SAO merge flag for all color components (per Left and Up merge)
SAO_TYPE_SHARING                 = 1  # J0045: SAO types, merge left/up flags are shared between Cr and Cb
SAO_TYPE_CODING                  = 1  # J0268: SAO type signalling using 1 ctx on/off flag + 1 bp BO/EO flag + 2 bp bins for EO class
SAO_MERGE_ONE_CTX                = 1  # J0041: SAO merge left/up flags share the same ctx
SAO_ABS_BY_PASS                  = 1  # J0043: by pass coding for SAO magnitudes 
SAO_LCU_BOUNDARY                 = 1  # J0139: SAO parameter estimation using non-deblocked pixels for LCU bottom and right boundary areas
MODIFIED_CROSS_SLICE             = 1  # J0266: SAO slice boundary control for GDR
CU_DQP_ENABLE_FLAG               = 1  # J0220: cu_qp_delta_enabled_flag in PPS
REMOVE_ZIGZAG_SCAN               = 1  # J0150: removal of zigzag scan

TRANS_SPLIT_FLAG_CTX_REDUCTION   = 1  # J0133: Reduce the context number of transform split flag to 3

WP_PARAM_RANGE_LIMIT             = 1  # J0221: Range limit of delta_weight and delta_offset for chroma.
J0260                            = 1  # Fix in rate control equations

SLICE_HEADER_EXTENSION           = 1  # II0235: Slice header extension mechanism

REMOVE_NSQT                      = 1  # Disable NSQT-related code
REMOVE_LM_CHROMA                 = 1  # Disable LM_Chroma-related code
REMOVE_FGS                       = 1  # Disable fine-granularity slices code
REMOVE_ALF                       = 1  # Disable ALF-related code
REMOVE_APS                       = 1  # Disable APS-related code

PREVREFPIC_DEFN                  = 0  # J0248: Shall be set equal to 0! (prevRefPic definition reverted to CD definition)
BYTE_ALIGNMENT                   = 1  # I0330: Add byte_alignment() procedure to end of slice header

SBH_THRESHOLD                    = 4  # I0156: value of the fixed SBH controlling threshold
  
SEQUENCE_LEVEL_LOSSLESS          = 0  # H0530: used only for sequence or frame-level lossless coding

DISABLING_CLIP_FOR_BIPREDME      = 1  # Ticket #175
  
C1FLAG_NUMBER                    = 8  # maximum number of largerThan1 flag coded in one chunk :  16 in HM5
C2FLAG_NUMBER                    = 1  # maximum number of largerThan2 flag coded in one chunk:  16 in HM5 

REMOVE_SAO_LCU_ENC_CONSTRAINTS_3 = 1  # disable the encoder constraint that conditionally disable SAO for chroma for entire slice in interleaved mode

SAO_SKIP_RIGHT                   = 1  # H1101: disallow using unavailable pixel during RDO

SAO_ENCODING_CHOICE              = 1  # I0184: picture early termination
PICTURE_SAO_RDO_FIX              = 0  # J0097: picture-based SAO optimization fix
if SAO_ENCODING_CHOICE:
	SAO_ENCODING_RATE            = 0.75
	SAO_ENCODING_CHOICE_CHROMA   = 1  # J0044: picture early termination Luma and Chroma are handled separatenly
	if SAO_ENCODING_CHOICE_CHROMA:
		SAO_ENCODING_RATE_CHROMA = 0.5

MAX_NUM_SPS                      = 32
MAX_NUM_PPS                      = 256
MAX_NUM_APS                      = 32 # !!!KS: number not defined in WD yet

MRG_MAX_NUM_CANDS_SIGNALED       = 5  # G091: value of maxNumMergeCand signaled in slice header 

WEIGHTED_CHROMA_DISTORTION       = 1  # F386: weighting of chroma for RDO
RDOQ_CHROMA_LAMBDA               = 1  # F386: weighting of chroma for RDOQ
ALF_CHROMA_LAMBDA                = 1  # F386: weighting of chroma for ALF
SAO_CHROMA_LAMBDA                = 1  # F386: weighting of chroma for SAO

MIN_SCAN_POS_CROSS               = 4

FAST_BIT_EST                     = 1  # G763: Table-based bit estimation for CABAC

MLS_GRP_NUM                      = 64 # G644 : Max number of coefficient groups, max(16, 64)
MLS_CG_SIZE                      = 4  # G644 : Coefficient group size of 4x4

ADAPTIVE_QP_SELECTION            = 1  # G382: Adaptive reconstruction levels, non-normative part for adaptive QP selection
if ADAPTIVE_QP_SELECTION:
	ARL_C_PRECISION              = 7  # G382: 7-bit arithmetic precision
	LEVEL_RANGE                  = 30 # G382: max coefficient level in statistics collection

if REMOVE_NSQT:
	NS_HAD                       = 0
else:
	NS_HAD                       = 1

APS_BITS_FOR_SAO_BYTE_LENGTH     = 12           
APS_BITS_FOR_ALF_BYTE_LENGTH     = 8

HHI_RQT_INTRA_SPEEDUP            = 1  # tests one best mode with full rqt
HHI_RQT_INTRA_SPEEDUP_MOD        = 0  # tests two best modes with full rqt

if HHI_RQT_INTRA_SPEEDUP_MOD and not HHI_RQT_INTRA_SPEEDUP:
	assert(False)

VERBOSE_RATE                     = 0  # Print additional rate information in encoder

AMVP_DECIMATION_FACTOR           = 4

SCAN_SET_SIZE                    = 16
LOG2_SCAN_SET_SIZE               = 4

FAST_UDI_MAX_RDMODE_NUM          = 35 # maximum number of RD comparison in fast-UDI estimation loop 

ZERO_MVD_EST                     = 0  # Zero Mvd Estimation in normal mode

NUM_INTRA_MODE                   = 36
if not REMOVE_LM_CHROMA:
	LM_CHROMA_IDX                = 35

IBDI_DISTORTION                  = 0  # enable/disable SSE modification when IBDI is used (JCTVC-D152)
FIXED_ROUNDING_FRAME_MEMORY      = 0  # enable/disable fixed rounding to 8-bitdepth of frame memory when IBDI is used  

WRITE_BACK                       = 1  # Enable/disable the encoder to replace the deltaPOC and Used by current from the config file with the values derived by the refIdc parameter.
AUTO_INTER_RPS                   = 1  # Enable/disable the automatic generation of refIdc from the deltaPOC and Used by current from the config file.
PRINT_RPS_INFO                   = 0  # Enable/disable the printing of bits used to send the RPS.
                                      # using one nearest frame as reference frame, and the other frames are high quality (POC%4==0) frames (1+X)
                                      # this should be done with encoder only decision
                                      # but because of the absence of reference frame management, the related code was hard coded currently

RVM_VCEGAM10_M                   = 4

PLANAR_IDX                       = 0
VER_IDX                          = 26 # index for intra VERTICAL   mode
HOR_IDX                          = 10 # index for intra HORIZONTAL mode
DC_IDX                           = 1  # index for intra DC mode
if REMOVE_LM_CHROMA:
	NUM_CHROMA_MODE              = 5  # total number of chroma modes
else:
	NUM_CHROMA_MODE              = 6  # total number of chroma modes
DM_CHROMA_IDX                    = 36 # chroma mode index for derived from luma intra mode


FAST_UDI_USE_MPM                 = 1

RDO_WITHOUT_DQP_BITS             = 0  # Disable counting dQP bits in RDO-based mode decision

FULL_NBIT                        = 0  # When enabled, does not use g_uiBitIncrement anymore to support > 8 bit data

AD_HOC_SLICES_FIXED_NUMBER_OF_LCU_IN_SLICE   = 1  # OPTION IDENTIFIER. mode==1 -> Limit maximum number of largest coding tree blocks in a slice
AD_HOC_SLICES_FIXED_NUMBER_OF_BYTES_IN_SLICE = 2  # OPTION IDENTIFIER. mode==2 -> Limit maximum number of bins/bits in a slice
AD_HOC_SLICES_FIXED_NUMBER_OF_TILES_IN_SLICE = 3

DEPENDENT_SLICES                 = 1  # JCTVC-I0229
# Dependent slice options
SHARP_FIXED_NUMBER_OF_LCU_IN_DEPENDENT_SLICE    = 1  # OPTION IDENTIFIER. Limit maximum number of largest coding tree blocks in an dependent slice
SHARP_MULTIPLE_CONSTRAINT_BASED_DEPENDENT_SLICE = 2  # OPTION IDENTIFIER. Limit maximum number of bins/bits in an dependent slice
if DEPENDENT_SLICES:
	FIXED_NUMBER_OF_TILES_IN_DEPENDENT_SLICE    = 3  # JCTVC-I0229

LOG2_MAX_NUM_COLUMNS_MINUS1      = 7
LOG2_MAX_NUM_ROWS_MINUS1         = 7
LOG2_MAX_COLUMN_WIDTH            = 13
LOG2_MAX_ROW_HEIGHT              = 13

MATRIX_MULT                      = 0  # Brute force matrix multiplication instead of partial butterfly

REG_DCT                          = 65535

AMP_SAD                          = 1  # dedicated SAD functions for AMP
AMP_ENC_SPEEDUP                  = 1  # encoder only speed-up by AMP mode skipping
if AMP_ENC_SPEEDUP:
	AMP_MRG                      = 1  # encoder only force merge for AMP partition (no motion search for AMP)

SCALING_LIST_OUTPUT_RESULT       = 0  # JCTVC-G880/JCTVC-G1016 quantization matrices

CABAC_INIT_PRESENT_FLAG          = 1


MAX_LAYER_NUM                    = 10
MAX_NUM_VPS                      = 16


NUM_DOWN_PART = 4

# SAOTypeLen
SAO_EO_LEN         = 4 
SAO_BO_LEN         = 4
SAO_MAX_BO_CLASSES = 32

# SAOType
SAO_EO_0         = 0
SAO_EO_1         = 1
SAO_EO_2         = 2
SAO_EO_3         = 3
SAO_BO           = 4
MAX_NUM_SAO_TYPE = 5


class SaoQTPart(object):

	def __init__(self):
		self.iBestType = 0
		self.iLength = 0

		self.subTypeIdx = 0

		self.iOffset = 4 * [0]
		self.StartCUX = 0
		self.StartCUY = 0
		self.EndCUX = 0
		self.EndCUY = 0

		self.PartIdx = 0
		self.PartLevel = 0
		self.PartCol = 0
		self.PartRow = 0

		self.DownPartsIdx = NUM_DOWN_PART * [0]
		self.UpPartIdx = 0

		self.bSplit = False

		#---- encoder only start -----
		self.bProcessed = False
		self.dMinCost = 0.0
		self.iMinDist = 0
		self.iMinRate = 0
		#---- encoder only start -----

class SaoLcuParam(object):

	def __init__(self):
		self.mergeUpFlag = False
		self.mergeLeftFlag = False
		self.typeIdx = 0

		self.subTypeIdx = 0

		self.offset = 4 * [0]
		self.partIdx = 0
		self.partIdxTmp = 0
		self.legnth = 0

class SaoParam(object):

	def __init__(self):
		self.bSaoFlag = 2 * [False]

		self.psSaoPart = 3 * [None]
		self.iMaxSplitLevel = 0
		self.iNumClass = MAX_NUM_SAO_TYPE * [0]
		self.oneUnitFlag = 3 * [False]
		self.saoLcuParam = 3 * [None]
		self.numCuInHeight = 0
		self.numCuInWidth = 0

class LFCUParam(object):

	def __init__(self):
		self.bInternalEdge = False
		self.bLeftEdge = False
		self.bTopEdge = False


# supported slice type
# SliceType
B_SLICE = 0
P_SLICE = 1
I_SLICE = 2

# chroma formats (according to semantics of chroma_format_idc)
# ChromaFormat
CHROMA_400 = 0
CHROMA_420 = 1
CHROMA_422 = 2
CHROMA_444 = 3

# supported partition shape
# PartSize
SIZE_2Nx2N = 0  # symmetric motion partition,  2Nx2N
SIZE_2NxN  = 1  # symmetric motion partition,  2Nx N
SIZE_Nx2N  = 2  # symmetric motion partition,   Nx2N
SIZE_NxN   = 3  # symmetric motion partition,   Nx N
SIZE_2NxnU = 4  # asymmetric motion partition, 2Nx( N/2) + 2Nx(3N/2)
SIZE_2NxnD = 5  # asymmetric motion partition, 2Nx(3N/2) + 2Nx( N/2)
SIZE_nLx2N = 6  # asymmetric motion partition, ( N/2)x2N + (3N/2)x2N
SIZE_nRx2N = 7  # asymmetric motion partition, (3N/2)x2N + ( N/2)x2N
SIZE_NONE  = 15

# supported prediction type
# PredMode
MODE_INTER = 0  # inter-prediction mode
MODE_INTRA = 1  # intra-prediction mode
MODE_NONE  = 15

# texture component type
# TextType
TEXT_LUMA     = 0  # luma
TEXT_CHROMA   = 1  # chroma (U+V)
TEXT_CHROMA_U = 2  # chroma U
TEXT_CHROMA_V = 3  # chroma V
TEXT_ALL      = 4  # Y+U+V
TEXT_NONE     = 15

# reference list index
# RefPicList
REF_PIC_LIST_0 = 0   # reference list 0
REF_PIC_LIST_1 = 1   # reference list 1
REF_PIC_LIST_C = 2   # combined reference list for uni-prediction in B-Slices
REF_PIC_LIST_X = 100 # special mark

# distortion function index
# DFunc
DF_DEFAULT   = 0
DF_SSE       = 1  # general size SSE
DF_SSE4      = 2  #   4xM SSE
DF_SSE8      = 3  #   8xM SSE
DF_SSE16     = 4  #  16xM SSE
DF_SSE32     = 5  #  32xM SSE
DF_SSE64     = 6  #  64xM SSE
DF_SSE16N    = 7  # 16NxM SSE
  
DF_SAD       = 8  # general size SAD
DF_SAD4      = 9  #   4xM SAD
DF_SAD8      = 10 #   8xM SAD
DF_SAD16     = 11 #  16xM SAD
DF_SAD32     = 12 #  32xM SAD
DF_SAD64     = 13 #  64xM SAD
DF_SAD16N    = 14 # 16NxM SAD

DF_SADS      = 15 # general size SAD with step
DF_SADS4     = 16 #   4xM SAD with step
DF_SADS8     = 17 #   8xM SAD with step
DF_SADS16    = 18 #  16xM SAD with step
DF_SADS32    = 19 #  32xM SAD with step
DF_SADS64    = 20 #  64xM SAD with step
DF_SADS16N   = 21 # 16NxM SAD with step
  
DF_HADS      = 22 # general size Hadamard with step
DF_HADS4     = 23 #   4xM HAD with step
DF_HADS8     = 24 #   8xM HAD with step
DF_HADS16    = 25 #  16xM HAD with step
DF_HADS32    = 26 #  32xM HAD with step
DF_HADS64    = 27 #  64xM HAD with step
DF_HADS16N   = 28 # 16NxM HAD with step
  
DF_SAD12     = 43
DF_SAD24     = 44
DF_SAD48     = 45

DF_SADS12    = 46
DF_SADS24    = 47
DF_SADS48    = 48

DF_SSE_FRAME = 50 # Frame-based SSE

# index for SBAC based RD optimization
# CI_IDX
CI_CURR_BEST     = 0  # best mode index
CI_NEXT_BEST     = 1  # next best index
CI_TEMP_BEST     = 2  # temporal index
CI_CHROMA_INTRA  = 3  # chroma intra index
CI_QT_TRAFO_TEST = 4
CI_QT_TRAFO_ROOT = 5
CI_NUM           = 6  # total number

# motion vector predictor direction used in AMVP
# MVP_DIR
MD_LEFT        = 0  # MVP of left block
MD_ABOVE       = 1  # MVP of above block
MD_ABOVE_RIGHT = 2  # MVP of above right block
MD_BELOW_LEFT  = 3  # MVP of below left block
MD_ABOVE_LEFT  = 4  # MVP of above left block

# motion vector prediction mode used in AMVP
# AMVP_MODE
AM_NONE = 0 # no AMVP mode
AM_EXPL = 1 # explicit signalling of motion vector index

# coefficient scanning type used in ACS
# COEFF_SCAN_TYPE
SCAN_ZIGZAG = 0 # typical zigzag scan
SCAN_HOR    = 1 # horizontal first scan
SCAN_VER    = 2 # vertical first scan
SCAN_DIAG   = 3 # up-right diagonal scan
