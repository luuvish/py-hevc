#!/usr/bin/env python

SLICE_HEADER_EXTENSION = 1 # II0235: Slice header extension mechanism

PREVREFPIC_DEFN = 1 # I0345: prevRefPic defined as previous reference picture that is at same or lower 
                    # temporal layer.
BYTE_ALIGNMENT = 0 # I0330: Add byte_alignment() procedure to end of slice header

SBH_THRESHOLD = 4 # I0156: value of the fixed SBH controlling threshold
  
SEQUENCE_LEVEL_LOSSLESS = 0 # H0530: used only for sequence or frame-level lossless coding

DISABLING_CLIP_FOR_BIPREDME = 1 # Ticket #175
  
C1FLAG_NUMBER = 8 # maximum number of largerThan1 flag coded in one chunk :  16 in HM5
C2FLAG_NUMBER = 1 # maximum number of largerThan2 flag coded in one chunk:  16 in HM5 

REMOVE_SAO_LCU_ENC_CONSTRAINTS_3 = 1 # disable the encoder constraint that conditionally disable SAO for chroma for entire slice in interleaved mode

SAO_SKIP_RIGHT = 1 # H1101: disallow using unavailable pixel during RDO

SAO_ENCODING_CHOICE = 1 # I0184: picture early termination
SAO_ENCODING_RATE = 0.75

MAX_NUM_SPS = 32
MAX_NUM_PPS = 256
MAX_NUM_APS = 32 # !!!KS: number not defined in WD yet

MRG_MAX_NUM_CANDS_SIGNALED = 5 # G091: value of maxNumMergeCand signaled in slice header 

WEIGHTED_CHROMA_DISTORTION = 1 # F386: weighting of chroma for RDO
RDOQ_CHROMA_LAMBDA = 1 # F386: weighting of chroma for RDOQ
ALF_CHROMA_LAMBDA = 1 # F386: weighting of chroma for ALF
SAO_CHROMA_LAMBDA = 1 # F386: weighting of chroma for SAO

MIN_SCAN_POS_CROSS = 4

FAST_BIT_EST = 1 # G763: Table-based bit estimation for CABAC

MLS_GRP_NUM = 64 # G644 : Max number of coefficient groups, max(16, 64)
MLS_CG_SIZE = 4 # G644 : Coefficient group size of 4x4

ADAPTIVE_QP_SELECTION = 1 # G382: Adaptive reconstruction levels, non-normative part for adaptive QP selection
ARL_C_PRECISION = 7 # G382: 7-bit arithmetic precision
LEVEL_RANGE = 30 # G382: max coefficient level in statistics collection

NS_HAD = 1

APS_BITS_FOR_SAO_BYTE_LENGTH = 12
APS_BITS_FOR_ALF_BYTE_LENGTH = 8

HHI_RQT_INTRA_SPEEDUP = 1 # tests one best mode with full rqt
HHI_RQT_INTRA_SPEEDUP_MOD = 0 # tests two best modes with full rqt

VERBOSE_RATE = 0 # Print additional rate information in encoder

AMVP_DECIMATION_FACTOR = 4

SCAN_SET_SIZE = 16
LOG2_SCAN_SET_SIZE = 4

FAST_UDI_MAX_RDMODE_NUM = 35 # maximum number of RD comparison in fast-UDI estimation loop 

ZERO_MVD_EST = 0 # Zero Mvd Estimation in normal mode

NUM_INTRA_MODE = 36
LM_CHROMA_IDX = 35

IBDI_DISTORTION = 0 # enable/disable SSE modification when IBDI is used (JCTVC-D152)
FIXED_ROUNDING_FRAME_MEMORY = 0 # enable/disable fixed rounding to 8-bitdepth of frame memory when IBDI is used  

WRITE_BACK = 1 # Enable/disable the encoder to replace the deltaPOC and Used by current from the config file with the values derived by the refIdc parameter.
AUTO_INTER_RPS = 1 # Enable/disable the automatic generation of refIdc from the deltaPOC and Used by current from the config file.
PRINT_RPS_INFO = 0 # Enable/disable the printing of bits used to send the RPS.
                   # using one nearest frame as reference frame, and the other frames are high quality (POC%4==0) frames (1+X)
                   # this should be done with encoder only decision
                   # but because of the absence of reference frame management, the related code was hard coded currently

RVM_VCEGAM10_M = 4

PLANAR_IDX = 0
VER_IDX = 26 # index for intra VERTICAL   mode
HOR_IDX = 10 # index for intra HORIZONTAL mode
DC_IDX = 1 # index for intra DC mode
NUM_CHROMA_MODE = 6 # total number of chroma modes
DM_CHROMA_IDX = 36 # chroma mode index for derived from luma intra mode


FAST_UDI_USE_MPM = 1

RDO_WITHOUT_DQP_BITS = 0 # Disable counting dQP bits in RDO-based mode decision

FULL_NBIT = 0 # When enabled, does not use g_uiBitIncrement anymore to support > 8 bit data

AD_HOC_SLICES_FIXED_NUMBER_OF_LCU_IN_SLICE = 1 # OPTION IDENTIFIER. mode==1 -> Limit maximum number of largest coding tree blocks in a slice
AD_HOC_SLICES_FIXED_NUMBER_OF_BYTES_IN_SLICE = 2 # OPTION IDENTIFIER. mode==2 -> Limit maximum number of bins/bits in a slice
AD_HOC_SLICES_FIXED_NUMBER_OF_TILES_IN_SLICE = 3

DEPENDENT_SLICES = 1 # JCTVC-I0229
# Dependent slice options
SHARP_FIXED_NUMBER_OF_LCU_IN_DEPENDENT_SLICE = 1 # OPTION IDENTIFIER. Limit maximum number of largest coding tree blocks in an dependent slice
SHARP_MULTIPLE_CONSTRAINT_BASED_DEPENDENT_SLICE = 2 # OPTION IDENTIFIER. Limit maximum number of bins/bits in an dependent slice
FIXED_NUMBER_OF_TILES_IN_DEPENDENT_SLICE = 3 # JCTVC-I0229

LOG2_MAX_NUM_COLUMNS_MINUS1 = 7
LOG2_MAX_NUM_ROWS_MINUS1 = 7
LOG2_MAX_COLUMN_WIDTH = 13
LOG2_MAX_ROW_HEIGHT = 13

MATRIX_MULT = 0 # Brute force matrix multiplication instead of partial butterfly

REG_DCT = 65535

AMP_SAD = 1 # dedicated SAD functions for AMP
AMP_ENC_SPEEDUP = 1 # encoder only speed-up by AMP mode skipping
AMP_MRG = 1 # encoder only force merge for AMP partition (no motion search for AMP)

SCALING_LIST_OUTPUT_RESULT = 0 #JCTVC-G880/JCTVC-G1016 quantization matrices

CABAC_INIT_PRESENT_FLAG = 1

# ====================================================================================================================
# VPS constants
# ====================================================================================================================
MAX_LAYER_NUM = 10
MAX_NUM_VPS = 16

# ====================================================================================================================
# Type definition
# ====================================================================================================================

NUM_DOWN_PART = 4

# SAOTypeLen
SAO_EO_LEN = 4 
SAO_BO_LEN = 4
SAO_MAX_BO_CLASSES = 32

# SAOType
SAO_EO_0 = 0
SAO_EO_1 = 1
SAO_EO_2 = 2
SAO_EO_3 = 3
SAO_BO = 4
MAX_NUM_SAO_TYPE = 5

# ====================================================================================================================
# Enumeration
# ====================================================================================================================

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
SIZE_2Nx2N = 0 # symmetric motion partition,  2Nx2N
SIZE_2NxN = 1  # symmetric motion partition,  2Nx N
SIZE_Nx2N = 2  # symmetric motion partition,   Nx2N
SIZE_NxN = 3   # symmetric motion partition,   Nx N
SIZE_2NxnU = 4 # asymmetric motion partition, 2Nx( N/2) + 2Nx(3N/2)
SIZE_2NxnD = 5 # asymmetric motion partition, 2Nx(3N/2) + 2Nx( N/2)
SIZE_nLx2N = 6 # asymmetric motion partition, ( N/2)x2N + (3N/2)x2N
SIZE_nRx2N = 7 # asymmetric motion partition, (3N/2)x2N + ( N/2)x2N
SIZE_NONE = 15

# supported prediction type
# PredMode
MODE_INTER = 0 # inter-prediction mode
MODE_INTRA = 1 # intra-prediction mode
MODE_NONE = 15

# texture component type
# TextType
TEXT_LUMA = 0     # luma
TEXT_CHROMA = 1   # chroma (U+V)
TEXT_CHROMA_U = 2 # chroma U
TEXT_CHROMA_V = 3 # chroma V
TEXT_ALL = 4      # Y+U+V
TEXT_NONE = 15

# reference list index
# RefPicList
REF_PIC_LIST_0 = 0   # reference list 0
REF_PIC_LIST_1 = 1   # reference list 1
REF_PIC_LIST_C = 2   # combined reference list for uni-prediction in B-Slices
REF_PIC_LIST_X = 100 # special mark

# distortion function index
# DFunc
DF_DEFAULT = 0
DF_SSE = 1      # general size SSE
DF_SSE4 = 2     #   4xM SSE
DF_SSE8 = 3     #   8xM SSE
DF_SSE16 = 4    #  16xM SSE
DF_SSE32 = 5    #  32xM SSE
DF_SSE64 = 6    #  64xM SSE
DF_SSE16N = 7   # 16NxM SSE
  
DF_SAD = 8      # general size SAD
DF_SAD4 = 9     #   4xM SAD
DF_SAD8 = 10    #   8xM SAD
DF_SAD16 = 11   #  16xM SAD
DF_SAD32 = 12   #  32xM SAD
DF_SAD64 = 13   #  64xM SAD
DF_SAD16N = 14  # 16NxM SAD

DF_SADS = 15    # general size SAD with step
DF_SADS4 = 16   #   4xM SAD with step
DF_SADS8 = 17   #   8xM SAD with step
DF_SADS16 = 18  #  16xM SAD with step
DF_SADS32 = 19  #  32xM SAD with step
DF_SADS64 = 20  #  64xM SAD with step
DF_SADS16N = 21 # 16NxM SAD with step
  
DF_HADS = 22    # general size Hadamard with step
DF_HADS4 = 23   #   4xM HAD with step
DF_HADS8 = 24   #   8xM HAD with step
DF_HADS16 = 25  #  16xM HAD with step
DF_HADS32 = 26  #  32xM HAD with step
DF_HADS64 = 27  #  64xM HAD with step
DF_HADS16N = 28 # 16NxM HAD with step
  
DF_SAD12 = 43
DF_SAD24 = 44
DF_SAD48 = 45

DF_SADS12 = 46
DF_SADS24 = 47
DF_SADS48 = 48

DF_SSE_FRAME = 50 # Frame-based SSE

# index for SBAC based RD optimization
# CI_IDX
CI_CURR_BEST = 0     # best mode index
CI_NEXT_BEST = 1     # next best index
CI_TEMP_BEST = 2     # temporal index
CI_CHROMA_INTRA = 3  # chroma intra index
CI_QT_TRAFO_TEST = 4
CI_QT_TRAFO_ROOT = 5
CI_NUM = 6           # total number

# motion vector predictor direction used in AMVP
# MVP_DIR
MD_LEFT = 0        # MVP of left block
MD_ABOVE = 1       # MVP of above block
MD_ABOVE_RIGHT = 2 # MVP of above right block
MD_BELOW_LEFT = 3  # MVP of below left block
MD_ABOVE_LEFT = 4  # MVP of above left block

# motion vector prediction mode used in AMVP
# AMVP_MODE
AM_NONE = 0 # no AMVP mode
AM_EXPL = 1 # explicit signalling of motion vector index

# coefficient scanning type used in ACS
# COEFF_SCAN_TYPE
SCAN_ZIGZAG = 0 # typical zigzag scan
SCAN_HOR = 1    # horizontal first scan
SCAN_VER = 2    # vertical first scan
SCAN_DIAG = 3   # up-right diagonal scan
