# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/CommonDef.py
    HM 9.1 Python Implementation
"""

from .TComRom import g_uiIBDI_MAX


NV_VERSION                  = "9.1" # Current software version

__GNUC__                    = 4
__GNUC_MINOR__              = 2
__GNUC_PATCHLEVEL__         = 1

NVM_COMPILEDBY              = "[GCC %d.%d.%d]" % (__GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__)
NVM_ONARCH                  = "[on 64-bit] "

#NVM_ONOS                    = "[Windows]"
#NVM_ONOS                    = "[Linux]"
#NVM_ONOS                    = "[Cygwin]"
NVM_ONOS                    = "[Mac OS X]"

NVM_BITS                    = "[%d bit] " % 64 # used for checking 64-bit O/S

NULL                        = 0


_SUMMARY_OUT_               = 0  # print-out PSNR results of all slices to summary.txt
_SUMMARY_PIC_               = 0  # print-out PSNR results for each slice type to summary.txt

MAX_GOP                     = 64 # max. value of hierarchical GOP size

MAX_NUM_REF                 = 4  # max. value of multiple reference frames
MAX_NUM_REF_LC              = 8  # max. value of combined reference frames

MAX_UINT                    = 0xFFFFFFFF  # max. value of unsigned 32-bit integer
MAX_INT                     = 2147483647  # max. value of signed 32-bit integer
MAX_INT64                   = 0x7FFFFFFFFFFFFFFF  # max. value of signed 64-bit integer
MAX_DOUBLE                  = 1.7e+308    # max. value of double-type value

MIN_QP                      = 0
MAX_QP                      = 51

NOT_VALID                   = -1


# clip x, such that 0 <= x <= #g_uiIBDI_MAX
Clip = lambda x: min(g_uiIBDI_MAX, max(0, x))

# clip a, such that minVal <= a <= maxVal
Clip3 = lambda minVal, maxVal, a: min(max(minVal, a), maxVal)


# AMVP: advanced motion vector prediction
AMVP_MAX_NUM_CANDS          = 2    # max number of final candidates
AMVP_MAX_NUM_CANDS_MEM      = 3    # max number of candidates
# MERGE
MRG_MAX_NUM_CANDS           = 5

# Reference memory management
DYN_REF_FREE                = 0    # dynamic free of reference memories

# Explicit temporal layer QP offset
MAX_TLAYER                  = 8    # max number of temporal layer
HB_LAMBDA_FOR_LDC           = 1    # use of B-style lambda for non-key pictures in low-delay mode

# Fast estimation of generalized B in low-delay mode
GPB_SIMPLE                  = 1    # Simple GPB mode
if GPB_SIMPLE:
    GPB_SIMPLE_UNI          = 1    # Simple mode for uni-direction

# Fast ME using smoother MV assumption
FASTME_SMOOTHER_MV          = 1    # reduce ME time using faster option

# Adaptive search range depending on POC difference
ADAPT_SR_SCALE              = 1    # division factor for adaptive search range

CLIP_TO_709_RANGE           = 0

# Early-skip threshold (encoder)
EARLY_SKIP_THRES            = 1.50 # if RD < thres*avg[BestSkipRD]

MAX_CHROMA_FORMAT_IDC       = 3


#NalUnitType
NAL_UNIT_CODED_SLICE_TRAIL_N   =  0
NAL_UNIT_CODED_SLICE_TRAIL_R   =  1
NAL_UNIT_CODED_SLICE_TSA_N     =  2
NAL_UNIT_CODED_SLICE_TLA       =  3 # Current name in the spec: TSA_R
NAL_UNIT_CODED_SLICE_STSA_N    =  4
NAL_UNIT_CODED_SLICE_STSA_R    =  5
NAL_UNIT_CODED_SLICE_RADL_N    =  6
NAL_UNIT_CODED_SLICE_DLP       =  7 # Current name in the spec: RADL_R
NAL_UNIT_CODED_SLICE_RASL_N    =  8
NAL_UNIT_CODED_SLICE_TFD       =  9 # Current name in the spec: RASL_R
NAL_UNIT_RESERVED_10           = 10
NAL_UNIT_RESERVED_11           = 11
NAL_UNIT_RESERVED_12           = 12
NAL_UNIT_RESERVED_13           = 13
NAL_UNIT_RESERVED_14           = 14
NAL_UNIT_RESERVED_15           = 15
NAL_UNIT_CODED_SLICE_BLA       = 16 # Current name in the spec: BLA_W_LP
NAL_UNIT_CODED_SLICE_BLANT     = 17 # Current name in the spec: BLA_W_DLP
NAL_UNIT_CODED_SLICE_BLA_N_LP  = 18
NAL_UNIT_CODED_SLICE_IDR       = 19 # Current name in the spec: IDR_W_DLP
NAL_UNIT_CODED_SLICE_IDR_N_LP  = 20
NAL_UNIT_CODED_SLICE_CRA       = 21
NAL_UNIT_RESERVED_22           = 22
NAL_UNIT_RESERVED_23           = 23
NAL_UNIT_RESERVED_24           = 24
NAL_UNIT_RESERVED_25           = 25
NAL_UNIT_RESERVED_26           = 26
NAL_UNIT_RESERVED_27           = 27
NAL_UNIT_RESERVED_28           = 28
NAL_UNIT_RESERVED_29           = 29
NAL_UNIT_RESERVED_30           = 30
NAL_UNIT_RESERVED_31           = 31
NAL_UNIT_VPS                   = 32
NAL_UNIT_SPS                   = 33
NAL_UNIT_PPS                   = 34
NAL_UNIT_ACCESS_UNIT_DELIMITER = 35
NAL_UNIT_EOS                   = 36
NAL_UNIT_EOB                   = 37
NAL_UNIT_FILLER_DATA           = 38
NAL_UNIT_SEI                   = 39 # Prefix SEI
NAL_UNIT_SEI_SUFFIX            = 40 # Suffix SEI
NAL_UNIT_RESERVED_41           = 41
NAL_UNIT_RESERVED_42           = 42
NAL_UNIT_RESERVED_43           = 43
NAL_UNIT_RESERVED_44           = 44
NAL_UNIT_RESERVED_45           = 45
NAL_UNIT_RESERVED_46           = 45
NAL_UNIT_RESERVED_47           = 47
NAL_UNIT_UNSPECIFIED_48        = 48
NAL_UNIT_UNSPECIFIED_49        = 49
NAL_UNIT_UNSPECIFIED_50        = 50
NAL_UNIT_UNSPECIFIED_51        = 51
NAL_UNIT_UNSPECIFIED_52        = 52
NAL_UNIT_UNSPECIFIED_53        = 53
NAL_UNIT_UNSPECIFIED_54        = 54
NAL_UNIT_UNSPECIFIED_55        = 55
NAL_UNIT_UNSPECIFIED_56        = 56
NAL_UNIT_UNSPECIFIED_57        = 57
NAL_UNIT_UNSPECIFIED_58        = 58
NAL_UNIT_UNSPECIFIED_59        = 59
NAL_UNIT_UNSPECIFIED_60        = 60
NAL_UNIT_UNSPECIFIED_61        = 61
NAL_UNIT_UNSPECIFIED_62        = 62
NAL_UNIT_UNSPECIFIED_63        = 63
NAL_UNIT_INVALID               = 64
