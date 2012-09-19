# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComRom.py
    HM 8.0 Python Implementation
"""

import sys

from ... import pointer

from .TypeDef import NUM_INTRA_MODE, SCAN_DIAG


# TAppDecTop.py
g_md5_mismatch = False


MAX_CU_DEPTH  = 7 # log2(LCUSize)
MAX_CU_SIZE   = (1 << MAX_CU_DEPTH) # maximum allowable size of CU
MIN_PU_SIZE   = 4
MAX_NUM_SPU_W = MAX_CU_SIZE / MIN_PU_SIZE # maximum number of SPU in horizontal line

# flexible conversion from relative to absolute index
g_auiZscanToRaster = (MAX_NUM_SPU_W * MAX_NUM_SPU_W) * [0]
g_auiRasterToZscan = (MAX_NUM_SPU_W * MAX_NUM_SPU_W) * [0]
g_motionRefer      = (MAX_NUM_SPU_W * MAX_NUM_SPU_W) * [0]

# conversion of partition index to picture pel position
g_auiRasterToPelX = (MAX_NUM_SPU_W * MAX_NUM_SPU_W) * [0]
g_auiRasterToPelY = (MAX_NUM_SPU_W * MAX_NUM_SPU_W) * [0]

# global variable (LCU width/height, max. CU depth)
g_uiMaxCUWidth  = MAX_CU_SIZE
g_uiMaxCUHeight = MAX_CU_SIZE
g_uiMaxCUDepth  = MAX_CU_DEPTH
g_uiAddCUDepth  = 0

MAX_TS_WIDTH  = 4
MAX_TS_HEIGHT = 4

g_auiPUOffset = (0, 8, 4, 4, 2, 10, 1, 5)

QUANT_IQUANT_SHIFT   = 20 # Q(QP%6) * IQ(QP%6) = 2^20
QUANT_SHIFT          = 14 # Q(4) = 2^14
SCALE_BITS           = 15 # Inherited from TMuC, pressumably for fractional bit estimates in RDOQ
MAX_TR_DYNAMIC_RANGE = 15 # Maximum transform dynamic range (excluding sign bit)

SHIFT_INV_1ST =  7 # Shift after first inverse transform stage
SHIFT_INV_2ND = 12 # Shift after second inverse transform stage

g_quantScales = (26214, 23302, 20560, 18396, 16384, 14564)
g_invQuantScales = (40, 45, 51, 57, 64, 72)

g_aiT4 = (
    (64, 64, 64, 64),
    (83, 36,-36,-83),
    (64,-64,-64, 64),
    (36,-83, 83,-36)
)

g_aiT8 = (
    (64, 64, 64, 64, 64, 64, 64, 64),
    (89, 75, 50, 18,-18,-50,-75,-89),
    (83, 36,-36,-83,-83,-36, 36, 83),
    (75,-18,-89,-50, 50, 89, 18,-75),
    (64,-64,-64, 64, 64,-64,-64, 64),
    (50,-89, 18, 75,-75,-18, 89,-50),
    (36,-83, 83,-36,-36, 83,-83, 36),
    (18,-50, 75,-89, 89,-75, 50,-18)
)

g_aiT16 = (
    (64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64),
    (90, 87, 80, 70, 57, 43, 25,  9, -9,-25,-43,-57,-70,-80,-87,-90),
    (89, 75, 50, 18,-18,-50,-75,-89,-89,-75,-50,-18, 18, 50, 75, 89),
    (87, 57,  9,-43,-80,-90,-70,-25, 25, 70, 90, 80, 43, -9,-57,-87),
    (83, 36,-36,-83,-83,-36, 36, 83, 83, 36,-36,-83,-83,-36, 36, 83),
    (80,  9,-70,-87,-25, 57, 90, 43,-43,-90,-57, 25, 87, 70, -9,-80),
    (75,-18,-89,-50, 50, 89, 18,-75,-75, 18, 89, 50,-50,-89,-18, 75),
    (70,-43,-87,  9, 90, 25,-80,-57, 57, 80,-25,-90, -9, 87, 43,-70),
    (64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64),
    (57,-80,-25, 90, -9,-87, 43, 70,-70,-43, 87,  9,-90, 25, 80,-57),
    (50,-89, 18, 75,-75,-18, 89,-50,-50, 89,-18,-75, 75, 18,-89, 50),
    (43,-90, 57, 25,-87, 70,  9,-80, 80, -9,-70, 87,-25,-57, 90,-43),
    (36,-83, 83,-36,-36, 83,-83, 36, 36,-83, 83,-36,-36, 83,-83, 36),
    (25,-70, 90,-80, 43,  9,-57, 87,-87, 57, -9,-43, 80,-90, 70,-25),
    (18,-50, 75,-89, 89,-75, 50,-18,-18, 50,-75, 89,-89, 75,-50, 18),
    ( 9,-25, 43,-57, 70,-80, 87,-90, 90,-87, 80,-70, 57,-43, 25, -9)
)

g_aiT32 = (
    (64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64),
    (90, 90, 88, 85, 82, 78, 73, 67, 61, 54, 46, 38, 31, 22, 13,  4, -4,-13,-22,-31,-38,-46,-54,-61,-67,-73,-78,-82,-85,-88,-90,-90),
    (90, 87, 80, 70, 57, 43, 25,  9, -9,-25,-43,-57,-70,-80,-87,-90,-90,-87,-80,-70,-57,-43,-25, -9,  9, 25, 43, 57, 70, 80, 87, 90),
    (90, 82, 67, 46, 22, -4,-31,-54,-73,-85,-90,-88,-78,-61,-38,-13, 13, 38, 61, 78, 88, 90, 85, 73, 54, 31,  4,-22,-46,-67,-82,-90),
    (89, 75, 50, 18,-18,-50,-75,-89,-89,-75,-50,-18, 18, 50, 75, 89, 89, 75, 50, 18,-18,-50,-75,-89,-89,-75,-50,-18, 18, 50, 75, 89),
    (88, 67, 31,-13,-54,-82,-90,-78,-46, -4, 38, 73, 90, 85, 61, 22,-22,-61,-85,-90,-73,-38,  4, 46, 78, 90, 82, 54, 13,-31,-67,-88),
    (87, 57,  9,-43,-80,-90,-70,-25, 25, 70, 90, 80, 43, -9,-57,-87,-87,-57, -9, 43, 80, 90, 70, 25,-25,-70,-90,-80,-43,  9, 57, 87),
    (85, 46,-13,-67,-90,-73,-22, 38, 82, 88, 54, -4,-61,-90,-78,-31, 31, 78, 90, 61,  4,-54,-88,-82,-38, 22, 73, 90, 67, 13,-46,-85),
    (83, 36,-36,-83,-83,-36, 36, 83, 83, 36,-36,-83,-83,-36, 36, 83, 83, 36,-36,-83,-83,-36, 36, 83, 83, 36,-36,-83,-83,-36, 36, 83),
    (82, 22,-54,-90,-61, 13, 78, 85, 31,-46,-90,-67,  4, 73, 88, 38,-38,-88,-73, -4, 67, 90, 46,-31,-85,-78,-13, 61, 90, 54,-22,-82),
    (80,  9,-70,-87,-25, 57, 90, 43,-43,-90,-57, 25, 87, 70, -9,-80,-80, -9, 70, 87, 25,-57,-90,-43, 43, 90, 57,-25,-87,-70,  9, 80),
    (78, -4,-82,-73, 13, 85, 67,-22,-88,-61, 31, 90, 54,-38,-90,-46, 46, 90, 38,-54,-90,-31, 61, 88, 22,-67,-85,-13, 73, 82,  4,-78),
    (75,-18,-89,-50, 50, 89, 18,-75,-75, 18, 89, 50,-50,-89,-18, 75, 75,-18,-89,-50, 50, 89, 18,-75,-75, 18, 89, 50,-50,-89,-18, 75),
    (73,-31,-90,-22, 78, 67,-38,-90,-13, 82, 61,-46,-88, -4, 85, 54,-54,-85,  4, 88, 46,-61,-82, 13, 90, 38,-67,-78, 22, 90, 31,-73),
    (70,-43,-87,  9, 90, 25,-80,-57, 57, 80,-25,-90, -9, 87, 43,-70,-70, 43, 87, -9,-90,-25, 80, 57,-57,-80, 25, 90,  9,-87,-43, 70),
    (67,-54,-78, 38, 85,-22,-90,  4, 90, 13,-88,-31, 82, 46,-73,-61, 61, 73,-46,-82, 31, 88,-13,-90, -4, 90, 22,-85,-38, 78, 54,-67),
    (64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64, 64,-64,-64, 64),
    (61,-73,-46, 82, 31,-88,-13, 90, -4,-90, 22, 85,-38,-78, 54, 67,-67,-54, 78, 38,-85,-22, 90,  4,-90, 13, 88,-31,-82, 46, 73,-61),
    (57,-80,-25, 90, -9,-87, 43, 70,-70,-43, 87,  9,-90, 25, 80,-57,-57, 80, 25,-90,  9, 87,-43,-70, 70, 43,-87, -9, 90,-25,-80, 57),
    (54,-85, -4, 88,-46,-61, 82, 13,-90, 38, 67,-78,-22, 90,-31,-73, 73, 31,-90, 22, 78,-67,-38, 90,-13,-82, 61, 46,-88,  4, 85,-54),
    (50,-89, 18, 75,-75,-18, 89,-50,-50, 89,-18,-75, 75, 18,-89, 50, 50,-89, 18, 75,-75,-18, 89,-50,-50, 89,-18,-75, 75, 18,-89, 50),
    (46,-90, 38, 54,-90, 31, 61,-88, 22, 67,-85, 13, 73,-82,  4, 78,-78, -4, 82,-73,-13, 85,-67,-22, 88,-61,-31, 90,-54,-38, 90,-46),
    (43,-90, 57, 25,-87, 70,  9,-80, 80, -9,-70, 87,-25,-57, 90,-43,-43, 90,-57,-25, 87,-70, -9, 80,-80,  9, 70,-87, 25, 57,-90, 43),
    (38,-88, 73, -4,-67, 90,-46,-31, 85,-78, 13, 61,-90, 54, 22,-82, 82,-22,-54, 90,-61,-13, 78,-85, 31, 46,-90, 67,  4,-73, 88,-38),
    (36,-83, 83,-36,-36, 83,-83, 36, 36,-83, 83,-36,-36, 83,-83, 36, 36,-83, 83,-36,-36, 83,-83, 36, 36,-83, 83,-36,-36, 83,-83, 36),
    (31,-78, 90,-61,  4, 54,-88, 82,-38,-22, 73,-90, 67,-13,-46, 85,-85, 46, 13,-67, 90,-73, 22, 38,-82, 88,-54, -4, 61,-90, 78,-31),
    (25,-70, 90,-80, 43,  9,-57, 87,-87, 57, -9,-43, 80,-90, 70,-25,-25, 70,-90, 80,-43, -9, 57,-87, 87,-57,  9, 43,-80, 90,-70, 25),
    (22,-61, 85,-90, 73,-38, -4, 46,-78, 90,-82, 54,-13,-31, 67,-88, 88,-67, 31, 13,-54, 82,-90, 78,-46,  4, 38,-73, 90,-85, 61,-22),
    (18,-50, 75,-89, 89,-75, 50,-18,-18, 50,-75, 89,-89, 75,-50, 18, 18,-50, 75,-89, 89,-75, 50,-18,-18, 50,-75, 89,-89, 75,-50, 18),
    (13,-38, 61,-78, 88,-90, 85,-73, 54,-31,  4, 22,-46, 67,-82, 90,-90, 82,-67, 46,-22, -4, 31,-54, 73,-85, 90,-88, 78,-61, 38,-13),
    ( 9,-25, 43,-57, 70,-80, 87,-90, 90,-87, 80,-70, 57,-43, 25, -9, -9, 25,-43, 57,-70, 80,-87, 90,-90, 87,-80, 70,-57, 43,-25,  9),
    ( 4,-13, 22,-31, 38,-46, 54,-61, 67,-73, 78,-82, 85,-88, 90,-90, 90,-90, 88,-85, 82,-78, 73,-67, 61,-54, 46,-38, 31,-22, 13, -4)
)

g_aucChromaScale = (
     0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,
    17,18,19,20,21,22,23,24,25,26,27,28,29,29,30,31,32,
    33,33,34,34,35,35,36,36,37,37,38,39,40,41,42,43,44,
    45,46,47,48,49,50,51
)

g_auiSigLastScan = [[None for j in xrange(MAX_CU_DEPTH)] for i in xrange(4)]

g_auiNonSquareSigLastScan = 4 * [0]

g_uiGroupIdx = (0,1,2,3,4,4,5,5,6,6,6,6,7,7,7,7,8,8,8,8,8,8,8,8,9,9,9,9,9,9,9,9)
g_uiMinInGroup = (0,1,2,3,4,6,8,12,16,24)

# Rice parameters for absolute transform levels
g_auiGoRiceRange = (7, 14, 26, 46, 78)
g_auiGoRicePrefixLen = (8, 7, 6, 5, 4)

g_sigLastScan8x8 = (
    (0, 1, 2, 3),
    (0, 1, 2, 3),
    (0, 2, 1, 3),
    (0, 2, 1, 3)
)
g_sigLastScanCG32x32 = 64 * [0]

g_aucIntraModeNumFast = (
    3, #   2x2
    8, #   4x4
    8, #   8x8
    3, #  16x16   
    3, #  32x32   
    3, #  64x64   
    3  # 128x128  
)

g_aucIntraModeNumAng   = 7 * [0]
g_aucIntraModeBitsAng  = 7 * [0]
g_aucAngIntraModeOrder = NUM_INTRA_MODE * [0]

g_uiBitDepth          = 8 # base bit-depth
g_uiBitIncrement      = 0 # increments
g_uiIBDI_MAX          = 255 # max. value after  IBDI
g_uiBASE_MAX          = 255 # max. value before IBDI
g_uiPCMBitDepthLuma   = 8 # PCM bit-depth
g_uiPCMBitDepthChroma = 8 # PCM bit-depth

# chroma
g_aucConvertTxtTypeToIdx = (0, 1, 1, 2)

# Mode-Dependent DCT/DST 
g_as_DST_MAT_4 = (
    (29, 55, 74, 84),
    (74, 74,  0,-74),
    (84,-29,-74, 55),
    (55,-84, 74,-29),
)
g_aucDCTDSTMode_Vert = NUM_INTRA_MODE * [0]
g_aucDCTDSTMode_Hor  = NUM_INTRA_MODE * [0]

g_aucConvertToBit = (MAX_CU_SIZE + 1) * [0]

SCALING_LIST_NUM         = 6 # list number for quantization matrix
SCALING_LIST_NUM_32x32   = 2 # list number for quantization matrix 32x32
SCALING_LIST_REM_NUM     = 6 # remainder of QP/6
SCALING_LIST_START_VALUE = 8 # start value for dpcm mode
MAX_MATRIX_COEF_NUM      = 64 # max coefficient number for quantization matrix
MAX_MATRIX_SIZE_NUM      = 8 # max size number for quantization matrix
SCALING_LIST_DC          = 16 # default DC value

# ScalingListDIR
SCALING_LIST_SQT     = 0
SCALING_LIST_VER     = 1
SCALING_LIST_HOR     = 2
SCALING_LIST_DIR_NUM = 3

# ScalingListSize
SCALING_LIST_4x4      = 0
SCALING_LIST_8x8      = 1
SCALING_LIST_16x16    = 2
SCALING_LIST_32x32    = 3
SCALING_LIST_SIZE_NUM = 4

MatrixType = (
    ("INTRA4X4_LUMA",
     "INTRA4X4_CHROMAU",
     "INTRA4X4_CHROMAV",
     "INTER4X4_LUMA",
     "INTER4X4_CHROMAU",
     "INTER4X4_CHROMAV"),
    ("INTRA8X8_LUMA",
     "INTRA8X8_CHROMAU",
     "INTRA8X8_CHROMAV",
     "INTER8X8_LUMA",
     "INTER8X8_CHROMAU",
     "INTER8X8_CHROMAV"),
    ("INTRA16X16_LUMA",
     "INTRA16X16_CHROMAU",
     "INTRA16X16_CHROMAV",
     "INTER16X16_LUMA",
     "INTER16X16_CHROMAU",
     "INTER16X16_CHROMAV"),
    ("INTRA32X32_LUMA",
     "INTER32X32_LUMA")
)
MatrixType_DC = (
    (),
    (),
    ("INTRA16X16_LUMA_DC",
     "INTRA16X16_CHROMAU_DC",
     "INTRA16X16_CHROMAV_DC",
     "INTER16X16_LUMA_DC",
     "INTER16X16_CHROMAU_DC",
     "INTER16X16_CHROMAV_DC"),
    ("INTRA32X32_LUMA_DC",
     "INTER32X32_LUMA_DC")
)

g_quantIntraDefault4x4 = (
    16,16,17,21,
    16,17,20,25,
    17,20,30,41,
    21,25,41,70
)

g_quantInterDefault4x4 = (
    16,16,17,21,
    16,17,21,24,
    17,21,24,36,
    21,24,36,57
)

g_quantTSDefault4x4 = (
    16,16,16,16,
    16,16,16,16,
    16,16,16,16,
    16,16,16,16
)

g_quantIntraDefault8x8 = (
    16,16,16,16,17,18,21,24,
    16,16,16,16,17,19,22,25,
    16,16,17,18,20,22,25,29,
    16,16,18,21,24,27,31,36,
    17,17,20,24,30,35,41,47,
    18,19,22,27,35,44,54,65,
    21,22,25,31,41,54,70,88,
    24,25,29,36,47,65,88,115
)

g_quantInterDefault8x8 = (
    16,16,16,16,17,18,20,24,
    16,16,16,17,18,20,24,25,
    16,16,17,18,20,24,25,28,
    16,17,18,20,24,25,28,33,
    17,18,20,24,25,28,33,41,
    18,20,24,25,28,33,41,54,
    20,24,25,28,33,41,54,71,
    24,25,28,33,41,54,71,91
)

g_quantIntraDefault16x16 = 256 * [0]
g_quantInterDefault16x16 = 256 * [0]
g_quantIntraDefault32x32 = 1024 * [0]
g_quantInterDefault32x32 = 1024 * [0]

g_scalingListSize = (16, 64, 256, 1024)
g_scalingListSizeX = (4, 8, 16, 32)
g_scalingListNum = (6, 6, 6, 2)
g_eTTable = (0, 3, 1, 2)


def initROM():
    # g_aucConvertToBit[ x ]: log2(x/4), if x=4 -> 0, x=8 -> 1, x=16 -> 2, ...
    for i in xrange(len(g_aucConvertToBit)):
        g_aucConvertToBit[i] = -1
    c = 0
    i = 4
    while i < MAX_CU_SIZE:
        g_aucConvertToBit[i] = c
        c += 1
        i *= 2
    g_aucConvertToBit[i] = c

    # g_auiFrameScanXY[ g_aucConvertToBit[ transformSize ] ]: zigzag scan array for transformSize
    c = 2
    for i in xrange(MAX_CU_DEPTH):
        g_auiSigLastScan[0][i] = (c*c) * [0]
        g_auiSigLastScan[1][i] = (c*c) * [0]
        g_auiSigLastScan[2][i] = (c*c) * [0]
        g_auiSigLastScan[3][i] = (c*c) * [0]
        initSigLastScan(
            g_auiSigLastScan[0][i], g_auiSigLastScan[1][i],
            g_auiSigLastScan[2][i], g_auiSigLastScan[3][i],
            c, c, i)
        c <<= 1

def destroyROM():
    pass
#   for i in xrange(MAX_CU_DEPTH):
#       del g_auiSigLastScan[0][i]
#       del g_auiSigLastScan[1][i]
#       del g_auiSigLastScan[2][i]
#       del g_auiSigLastScan[3][i]

def initZscanToRaster(iMaxDepth, iDepth, uiStartVal, rpuiCurrIdx):
    def _initZscanToRaster(iMaxDepth, iDepth, uiStartVal, rpuiCurrIdx):
        iStride = 1 << (iMaxDepth - 1)

        if iDepth == iMaxDepth:
            rpuiCurrIdx[0] = uiStartVal
            rpuiCurrIdx += 1
        else:
            iStep = iStride >> iDepth
            _initZscanToRaster(iMaxDepth, iDepth+1, uiStartVal, rpuiCurrIdx)
            _initZscanToRaster(iMaxDepth, iDepth+1, uiStartVal+iStep, rpuiCurrIdx)
            _initZscanToRaster(iMaxDepth, iDepth+1, uiStartVal+iStep*iStride, rpuiCurrIdx)
            _initZscanToRaster(iMaxDepth, iDepth+1, uiStartVal+iStep*iStride+iStep, rpuiCurrIdx)

    _initZscanToRaster(iMaxDepth, iDepth, uiStartVal, pointer(rpuiCurrIdx))

def initRasterToZscan(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
    uiMinCUWidth = uiMaxCUWidth  >> (uiMaxDepth - 1)
    uiMinCUHeight = uiMaxCUHeight >> (uiMaxDepth - 1)
  
    uiNumPartInWidth = uiMaxCUWidth / uiMinCUWidth
    uiNumPartInHeight = uiMaxCUHeight / uiMinCUHeight
  
    for i in xrange(uiNumPartInWidth*uiNumPartInHeight):
        g_auiRasterToZscan[g_auiZscanToRaster[i]] = i

def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
    minSUWidth = uiMaxCUWidth >> (uiMaxDepth - 1)
    minSUHeight = uiMaxCUHeight >> (uiMaxDepth - 1)

    numPartInWidth = uiMaxCUWidth / minSUWidth
    numPartInHeight = uiMaxCUHeight / minSUHeight

    for i in xrange(numPartInWidth*numPartInHeight):
        g_motionRefer[i] = i

    maxCUDepth = g_uiMaxCUDepth - (g_uiAddCUDepth - 1)
    minCUWidth = uiMaxCUWidth >> (maxCUDepth - 1)

    if not (minCUWidth == 8 and minSUWidth == 4): #check if Minimum PU width == 4
        return

    compressionNum = 2

    for i in xrange(numPartInWidth*(numPartInHeight-1), numPartInWidth*numPartInHeight, compressionNum*2):
        for j in xrange(1, compressionNum):
            g_motionRefer[g_auiRasterToZscan[i+j]] = g_auiRasterToZscan[i]

    for i in xrange(numPartInWidth*(numPartInHeight-1)+compressionNum*2-1, numPartInWidth*numPartInHeight, compressionNum*2):
        for j in xrange(1, compressionNum):
            g_motionRefer[g_auiRasterToZscan[i-j]] = g_auiRasterToZscan[i]

def initRasterToPelXY(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
    uiTempX = pointer(g_auiRasterToPelX)
    uiTempY = pointer(g_auiRasterToPelY)
  
    uiMinCUWidth = uiMaxCUWidth >> (uiMaxDepth - 1)
    uiMinCUHeight = uiMaxCUHeight >> (uiMaxDepth - 1)
  
    uiNumPartInWidth = uiMaxCUWidth / uiMinCUWidth
    uiNumPartInHeight = uiMaxCUHeight / uiMinCUHeight

    uiTempX[0] = 0
    uiTempX += 1
    for i in xrange(1, uiNumPartInWidth):
        uiTempX[0] = uiTempX[-1] + uiMinCUWidth
        uiTempX += 1
    for i in xrange(1, uiNumPartInHeight):
        for j in xrange(uiNumPartInWidth):
            uiTempX[j] = uiTempX[j-uiNumPartInWidth]
        uiTempX += uiNumPartInWidth

    for i in xrange(1, uiNumPartInWidth*uiNumPartInHeight):
        uiTempY[i] = (i / uiNumPartInWidth) * uiMinCUWidth

def initSigLastScan(pBuffZ, pBuffH, pBuffV, pBuffD, iWidth, iHeight, iDepth):
    pBuffZ = pointer(pBuffZ)
    pBuffH = pointer(pBuffH)
    pBuffV = pointer(pBuffV)
    pBuffD = pointer(pBuffD)

    uiNumScanPos = iWidth * iWidth
    uiNextScanPos = 0

    if iWidth < 16:
        pBuffTemp = pointer(pBuffD)
        if iWidth == 8:
            pBuffTemp = pointer(g_sigLastScanCG32x32)
        uiScanLine = 0
        while uiNextScanPos < uiNumScanPos:
            iPrimDim = uiScanLine
            iScndDim = 0
            while iPrimDim >= iWidth:
                iScndDim += 1
                iPrimDim -= 1
            while iPrimDim >= 0 and iScndDim < iWidth:
                pBuffTemp[uiNextScanPos] = iPrimDim * iWidth + iScndDim
                uiNextScanPos += 1
                iScndDim += 1
                iPrimDim -= 1
            uiScanLine += 1
    if iWidth > 4:
        uiNumBlkSide = iWidth >> 2
        uiNumBlks = uiNumBlkSide * uiNumBlkSide
        log2Blk = g_aucConvertToBit[uiNumBlkSide] + 1

        for uiBlk in xrange(uiNumBlks):
            uiNextScanPos = 0
            initBlkPos = g_auiSigLastScan[SCAN_DIAG][log2Blk][uiBlk]
            if iWidth == 32:
                initBlkPos = g_sigLastScanCG32x32[uiBlk]
            offsetY = initBlkPos / uiNumBlkSide
            offsetX = initBlkPos - offsetY * uiNumBlkSide
            offsetD = 4 * (offsetX + offsetY * iWidth)
            offsetScan = 16 * uiBlk
            uiScanLine = 0
            while uiNextScanPos < 16:
                iPrimDim = uiScanLine
                iScndDim = 0
                while iPrimDim >= 4:
                    iScndDim += 1
                    iPrimDim -= 1
                while iPrimDim >= 0 and iScndDim < 4:
                    pBuffD[uiNextScanPos + offsetScan] = iPrimDim * iWidth + iScndDim + offsetD
                    uiNextScanPos += 1
                    iScndDim += 1
                    iPrimDim -= 1
                uiScanLine += 1

    uiCnt = 0
    if iWidth > 2:
        numBlkSide = iWidth >> 2
        for blkY in xrange(numBlkSide):
            for blkX in xrange(numBlkSide):
                offset = blkY * 4 * iWidth + blkX * 4
                for y in xrange(4):
                    for x in xrange(4):
                        pBuffH[uiCnt] = y * iWidth + x + offset
                        uiCnt += 1

        uiCnt = 0
        for blkX in xrange(numBlkSide):
            for blkY in xrange(numBlkSide):
                offset = blkY * 4 * iWidth + blkX * 4
                for x in xrange(4):
                    for y in xrange(4):
                        pBuffV[uiCnt] = y * iWidth + x + offset
                        uiCnt += 1
    else:
        for iY in xrange(iHeight):
            for iX in xrange(iWidth):
                pBuffH[uiCnt] = iY * iWidth + iX
                uiCnt += 1

        uiCnt = 0
        for iX in xrange(iWidth):
            for iY in xrange(iHeight):
                pBuffV[uiCnt] = iY * iWidth + iX
                uiCnt += 1

def initNonSquareSigLastScan(pBuffZ, uiWidth, uiHeight):
    pBuffZ = pointer(pBuffZ)
    c = 0

    # starting point
    pBuffZ[c] = 0
    c += 1

    # loop
    if uiWidth > uiHeight:
        x = 0
        y = 1
        while True:
            # increase loop
            while y >= 0:
                if 0 <= x < uiWidth and 0 <= y < uiHeight:
                    pBuffZ[c] = x + y * uiWidth
                    c += 1
                x += 1
                y -= 1
            y = 0

            # decrease loop
            while x >= 0:
                if 0 <= x < uiWidth and 0 <= y < uiHeight:
                    pBuffZ[c] = x + y * uiWidth
                    c += 1
                x -= 1
                y += 1
            x = 0

            # termination condition
            if c >= uiWidth * uiHeight:
                break
    else:
        x = 1
        y = 0
        while True:
            # increase loop
            while x >= 0:
                if 0 <= x < uiWidth and 0 <= y < uiHeight:
                    pBuffZ[c] = x + y * uiWidth
                    c += 1
                x -= 1
                y += 1
            x = 0
    
            # decrease loop
            while y >= 0:
                if 0 <= x < uiWidth and 0 <= y < uiHeight:
                    pBuffZ[c] = x + y * uiWidth
                    c += 1
                x += 1
                y -= 1
            y = 0

            # termination condition
            if c >= uiWidth * uiHeight:
                break;
