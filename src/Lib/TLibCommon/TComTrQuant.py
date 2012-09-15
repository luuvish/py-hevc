# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComTrQuant.py
    HM 8.0 Python Implementation
"""

import sys

from ... import pointer
from ... import cvar

from .TypeDef import (
    COEF_REMAIN_BIN_REDUCTION, SBH_THRESHOLD, C1FLAG_NUMBER, C2FLAG_NUMBER,
    MLS_GRP_NUM, MLS_CG_SIZE, ARL_C_PRECISION, LEVEL_RANGE,
    SCAN_SET_SIZE, LOG2_SCAN_SET_SIZE, REG_DCT,
    I_SLICE, MODE_INTRA, TEXT_LUMA, TEXT_CHROMA,
    SCAN_ZIGZAG, SCAN_HOR, SCAN_VER, SCAN_DIAG
)

from .CommonDef import (
    MAX_INT, MAX_INT64, MAX_DOUBLE, MAX_QP,
    Clip3
)

from .TComRom import (
    MAX_CU_DEPTH, MAX_CU_SIZE, QUANT_IQUANT_SHIFT, QUANT_SHIFT, SCALE_BITS,
    MAX_TR_DYNAMIC_RANGE, SHIFT_INV_1ST, SHIFT_INV_2ND, MAX_MATRIX_SIZE_NUM,
    SCALING_LIST_NUM, SCALING_LIST_REM_NUM, SCALING_LIST_SQT,
    SCALING_LIST_VER, SCALING_LIST_HOR, SCALING_LIST_DIR_NUM,
    SCALING_LIST_8x8, SCALING_LIST_16x16, SCALING_LIST_32x32, SCALING_LIST_SIZE_NUM,
    g_quantScales, g_invQuantScales, g_aucConvertToBit,
    g_aiT4, g_aiT8, g_aiT16, g_aiT32,
    g_aucChromaScale, g_auiSigLastScan,
    g_uiGroupIdx, g_auiGoRiceRange, g_auiGoRicePrefixLen,
    g_sigLastScan8x8, g_sigLastScanCG32x32,
    g_scalingListSize, g_scalingListSizeX, g_scalingListNum, g_eTTable
)

from .ContextTables import (
    NUM_QT_CBF_CTX,
    NUM_SIG_CG_FLAG_CTX,
    NUM_SIG_FLAG_CTX,
    NUM_ONE_FLAG_CTX,
    NUM_ABS_FLAG_CTX
)


QP_BITS = 15
RDOQ_CHROMA = 1

class estBitsSbacStruct(object):

    def __init__(self):
        self.significantCoeffGroupBits = [[0,0] for i in xrange(NUM_SIG_CG_FLAG_CTX)]
        self.significantBits = [[0,0] for i in xrange(NUM_SIG_FLAG_CTX)]
        self.lastXBits = 32 * [0]
        self.lastYBits = 32 * [0]
        self.m_greaterOneBits = [[0,0] for i in xrange(NUM_ONE_FLAG_CTX)]
        self.m_levelAbsBits = [[0,0] for i in xrange(NUM_ABS_FLAG_CTX)]

        self.blockCbpBits = [[0,0] for i in xrange(3*NUM_QT_CBF_CTX)]
        self.blockRootCbpBits = [[0,0] for i in xrange(4)]
        self.scanZigzag = [0,0]
        self.scanNonZigzag = [0,0]

class coeffGroupRDStats(object):

    def __init__(self):
        self.iNNZbeforePos0 = 0
        self.d64CodedLevelandDist = 0.0
        self.d64UncodedDist = 0.0
        self.d64SigCost = 0.0
        self.d64SigCost_0 = 0.0

class QpParam(object):

    def __init__(self):
        self.m_iQP = 0
        self.m_iPer = 0
        self.m_iRem = 0
        self.m_iBits = 0

    def setQpParam(self, qpScaled):
        self.m_iQP = qpScaled
        self.m_iPer = qpScaled / 6
        self.m_iRem = qpScaled % 6
        self.m_iBits = QP_BITS + self.m_iPer

    def clear(self):
        self.m_iQP = 0
        self.m_iPer = 0
        self.m_iRem = 0
        self.m_iBits = 0

    def per(self):
        return self.m_iPer
    def rem(self):
        return self.m_iRem
    def bits(self):
        return self.m_iBits
    def qp(self):
        return self.m_iQP        


def fastForwardDst(block, coeff, shift):
    c = 4 * [0]
    rnd_factor = 1 << (shift-1)
    for i in xrange(4):
        c[0] = block[4*i+0] + block[4*i+3]
        c[1] = block[4*i+1] + block[4*i+3]
        c[2] = block[4*i+0] - block[4*i+1]
        c[3] = 74 * block[4*i+2]

        coeff[   i] = (29 * c[0] + 55 * c[1] + c[3] + rnd_factor) >> shift
        coeff[ 4+i] = (74 * (block[4*i]+block[4*i+1]-block[4*i+3]) + rnd_factor) >> shift
        coeff[ 8+i] = (29 * c[2] + 55 * c[0] - c[3] + rnd_factor) >> shift
        coeff[12+i] = (55 * c[2] - 29 * c[1] + c[3] + rnd_factor) >> shift

def fastInverseDst(tmp, block, shift):
    c = 4 * [0]
    rnd_factor = 1 << (shift-1)
    for i in xrange(4):
        c[0] = tmp[  i] + tmp[ 8+i]
        c[1] = tmp[8+i] + tmp[12+i]
        c[2] = tmp[  i] - tmp[12+i]
        c[3] = 74 * tmp[4+i]

        block[4*i+0] = Clip3(-32768, 32767, (29 * c[0] + 55 * c[1] + c[3] + rnd_factor) >> shift)
        block[4*i+1] = Clip3(-32768, 32767, (55 * c[2] - 29 * c[1] + c[3] + rnd_factor) >> shift)
        block[4*i+2] = Clip3(-32768, 32767, (74 * (tmp[i]-tmp[8+i]+tmp[12+i]) + rnd_factor) >> shift)
        block[4*i+3] = Clip3(-32768, 32767, (55 * c[0] + 29 * c[2] - c[3] + rnd_factor) >> shift)

def partialButterfly4(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        # E and O
        E[0] = src[0] + src[3]
        O[0] = src[0] - src[3]
        E[1] = src[1] + src[2]
        O[1] = src[1] - src[2]

        dst[0*line] = (g_aiT4[0][0] * E[0] + g_aiT4[0][1] * E[1] + add) >> shift
        dst[2*line] = (g_aiT4[2][0] * E[0] + g_aiT4[2][1] * E[1] + add) >> shift
        dst[1*line] = (g_aiT4[1][0] * O[0] + g_aiT4[1][1] * O[1] + add) >> shift
        dst[3*line] = (g_aiT4[3][0] * O[0] + g_aiT4[3][1] * O[1] + add) >> shift

        src += 4
        dst += 1

def partialButterflyInverse4(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        O[0] = g_aiT4[1][0] * src[1*line] + g_aiT4[3][0] * src[3*line]
        O[1] = g_aiT4[1][1] * src[1*line] + g_aiT4[3][1] * src[3*line]
        E[0] = g_aiT4[0][0] * src[0*line] + g_aiT4[2][0] * src[2*line]
        E[1] = g_aiT4[0][1] * src[0*line] + g_aiT4[2][1] * src[2*line]

        dst[0] = Clip3(-32768, 32767, (E[0] + O[0] + add) >> shift)
        dst[1] = Clip3(-32768, 32767, (E[1] + O[1] + add) >> shift)
        dst[2] = Clip3(-32768, 32767, (E[1] - O[1] + add) >> shift)
        dst[3] = Clip3(-32768, 32767, (E[0] - O[0] + add) >> shift)

        src += 1
        dst += 4

def partialButterfly8(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 4 * [0], 4 * [0]
    EE, EO = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        # E and O
        for k in xrange(4):
            E[k] = src[k] + src[7-k]
            O[k] = src[k] - src[7-k]
        # EE and EO
        EE[0] = E[0] + E[3]
        EO[0] = E[0] - E[3]
        EE[1] = E[1] + E[2]
        EO[1] = E[1] - E[2]

        dst[0*line] = (g_aiT8[0][0] * EE[0] + g_aiT8[0][1] * EE[1] + add) >> shift
        dst[4*line] = (g_aiT8[4][0] * EE[0] + g_aiT8[4][1] * EE[1] + add) >> shift
        dst[2*line] = (g_aiT8[2][0] * EO[0] + g_aiT8[2][1] * EO[1] + add) >> shift
        dst[6*line] = (g_aiT8[6][0] * EO[0] + g_aiT8[6][1] * EO[1] + add) >> shift

        dst[1*line] = (g_aiT8[1][0] * O[0] + g_aiT8[1][1] * O[1] + g_aiT8[1][2] * O[2] + g_aiT8[1][3] * O[3] + add) >> shift
        dst[3*line] = (g_aiT8[3][0] * O[0] + g_aiT8[3][1] * O[1] + g_aiT8[3][2] * O[2] + g_aiT8[3][3] * O[3] + add) >> shift
        dst[5*line] = (g_aiT8[5][0] * O[0] + g_aiT8[5][1] * O[1] + g_aiT8[5][2] * O[2] + g_aiT8[5][3] * O[3] + add) >> shift
        dst[7*line] = (g_aiT8[7][0] * O[0] + g_aiT8[7][1] * O[1] + g_aiT8[7][2] * O[2] + g_aiT8[7][3] * O[3] + add) >> shift

        src += 8
        dst += 1

def partialButterflyInverse8(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 4 * [0], 4 * [0]
    EE, EO = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        for k in xrange(4):
            O[k] = g_aiT8[1][k] * src[1*line] + g_aiT8[3][k] * src[3*line] + \
                   g_aiT8[5][k] * src[5*line] + g_aiT8[7][k] * src[7*line]

        EO[0] = g_aiT8[2][0] * src[2*line] + g_aiT8[6][0] * src[6*line]
        EO[1] = g_aiT8[2][1] * src[2*line] + g_aiT8[6][1] * src[6*line]
        EE[0] = g_aiT8[0][0] * src[0*line] + g_aiT8[4][0] * src[4*line]
        EE[1] = g_aiT8[0][1] * src[0*line] + g_aiT8[4][1] * src[4*line]

        E[0] = EE[0] + EO[0]
        E[3] = EE[0] - EO[0]
        E[1] = EE[1] + EO[1]
        E[2] = EE[1] - EO[1]
        for k in xrange(4):
            dst[k+0] = Clip3(-32768, 32767, (E[  k] + O[  k] + add) >> shift)
            dst[k+4] = Clip3(-32768, 32767, (E[3-k] - O[3-k] + add) >> shift)

        src += 1
        dst += 8

def partialButterfly16(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 8 * [0], 8 * [0]
    EE, EO = 4 * [0], 4 * [0]
    EEE, EEO = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        # E and O
        for k in xrange(8):
            E[k] = src[k] + src[15-k]
            O[k] = src[k] - src[15-k]
        # EE and EO
        for k in xrange(4):
            EE[k] = E[k] + E[7-k]
            EO[k] = E[k] - E[7-k]
        # EEE and EEO
        EEE[0] = EE[0] + EE[3]
        EEO[0] = EE[0] - EE[3]
        EEE[1] = EE[1] + EE[2]
        EEO[1] = EE[1] - EE[2]

        dst[ 0*line] = (g_aiT16[ 0][0] * EEE[0] + g_aiT16[ 0][1] * EEE[1] + add) >> shift
        dst[ 8*line] = (g_aiT16[ 8][0] * EEE[0] + g_aiT16[ 8][1] * EEE[1] + add) >> shift
        dst[ 4*line] = (g_aiT16[ 4][0] * EEO[0] + g_aiT16[ 4][1] * EEO[1] + add) >> shift
        dst[12*line] = (g_aiT16[12][0] * EEO[0] + g_aiT16[12][1] * EEO[1] + add) >> shift

        for k in xrange(2, 16, 4):
            dst[k*line] = (g_aiT16[k][0] * EO[0] + g_aiT16[k][1] * EO[1] + 
                           g_aiT16[k][2] * EO[2] + g_aiT16[k][3] * EO[3] + add) >> shift

        for k in xrange(1, 16, 2):
            dst[k*line] = (g_aiT16[k][0] * O[0] + g_aiT16[k][1] * O[1] + 
                           g_aiT16[k][2] * O[2] + g_aiT16[k][3] * O[3] +
                           g_aiT16[k][4] * O[4] + g_aiT16[k][5] * O[5] +
                           g_aiT16[k][6] * O[6] + g_aiT16[k][7] * O[7] + add) >> shift

        src += 16
        dst += 1

def partialButterflyInverse16(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 8 * [0], 8 * [0]
    EE, EO = 4 * [0], 4 * [0]
    EEE, EEO = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        for k in xrange(8):
            O[k] = g_aiT16[ 1][k] * src[ 1*line] + g_aiT16[ 3][k] * src[ 3*line] + \
                   g_aiT16[ 5][k] * src[ 5*line] + g_aiT16[ 7][k] * src[ 7*line] + \
                   g_aiT16[ 9][k] * src[ 9*line] + g_aiT16[11][k] * src[11*line] + \
                   g_aiT16[13][k] * src[13*line] + g_aiT16[15][k] * src[15*line]
        for k in xrange(4):
            EO[k] = g_aiT16[ 2][k] * src[ 2*line] + g_aiT16[ 6][k] * src[ 6*line] + \
                    g_aiT16[10][k] * src[10*line] + g_aiT16[14][k] * src[14*line]
        EEO[0] = g_aiT16[4][0] * src[4*line] + g_aiT16[12][0] * src[12*line]
        EEE[0] = g_aiT16[0][0] * src[0*line] + g_aiT16[ 8][0] * src[ 8*line]
        EEO[1] = g_aiT16[4][1] * src[4*line] + g_aiT16[12][1] * src[12*line]
        EEE[1] = g_aiT16[0][1] * src[0*line] + g_aiT16[ 8][1] * src[ 8*line]

        for k in xrange(2):
            EE[k  ] = EEE[  k] + EEO[  k]
            EE[k+2] = EEE[1-k] - EEO[1-k]
        for k in xrange(4):
            E[k  ] = EE[  k] + EO[  k]
            E[k+4] = EE[3-k] - EO[3-k]
        for k in xrange(8):
            dst[k+0] = Clip3(-32768, 32767, (E[  k] + O[  k] + add) >> shift)
            dst[k+8] = Clip3(-32768, 32767, (E[7-k] - O[7-k] + add) >> shift)

        src += 1
        dst += 16

def partialButterfly32(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 16 * [0], 16 * [0]
    EE, EO = 8 * [0], 8 * [0]
    EEE, EEO = 4 * [0], 4 * [0]
    EEEE, EEEO = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        # E and O
        for k in xrange(16):
            E[k] = src[k] + src[31-k]
            O[k] = src[k] - src[31-k]
        # EE and EO
        for k in xrange(8):
            EE[k] = E[k] + E[15-k]
            EO[k] = E[k] - E[15-k]
        # EEE and EEO
        for k in xrange(4):
            EEE[k] = EE[k] + EE[7-k]
            EEO[k] = EE[k] - EE[7-k]
        # EEEE and EEEO
        EEEE[0] = EEE[0] + EEE[3]
        EEEO[0] = EEE[0] - EEE[3]
        EEEE[1] = EEE[1] + EEE[2]
        EEEO[1] = EEE[1] - EEE[2]

        dst[ 0*line] = (g_aiT32[ 0][0] * EEEE[0] + g_aiT32[ 0][1] * EEEE[1] + add) >> shift
        dst[16*line] = (g_aiT32[16][0] * EEEE[0] + g_aiT32[16][1] * EEEE[1] + add) >> shift
        dst[ 8*line] = (g_aiT32[ 8][0] * EEEO[0] + g_aiT32[ 8][1] * EEEO[1] + add) >> shift
        dst[24*line] = (g_aiT32[24][0] * EEEO[0] + g_aiT32[24][1] * EEEO[1] + add) >> shift
        for k in xrange(4, 32, 8):
            dst[k*line] = (g_aiT32[k][0] * EEO[0] + g_aiT32[k][1] * EEO[1] + 
                           g_aiT32[k][2] * EEO[2] + g_aiT32[k][3] * EEO[3] + add) >> shift
        for k in xrange(2, 32, 4):
            dst[k*line] = (g_aiT32[k][0] * EO[0] + g_aiT32[k][1] * EO[1] + 
                           g_aiT32[k][2] * EO[2] + g_aiT32[k][3] * EO[3] +
                           g_aiT32[k][4] * EO[4] + g_aiT32[k][5] * EO[5] +
                           g_aiT32[k][6] * EO[6] + g_aiT32[k][7] * EO[7] + add) >> shift
        for k in xrange(1, 32, 2):
            dst[k*line] = (g_aiT32[k][ 0] * O[ 0] + g_aiT32[k][ 1] * O[ 1] + 
                           g_aiT32[k][ 2] * O[ 2] + g_aiT32[k][ 3] * O[ 3] +
                           g_aiT32[k][ 4] * O[ 4] + g_aiT32[k][ 5] * O[ 5] +
                           g_aiT32[k][ 6] * O[ 6] + g_aiT32[k][ 7] * O[ 7] +
                           g_aiT32[k][ 8] * O[ 8] + g_aiT32[k][ 9] * O[ 9] +
                           g_aiT32[k][10] * O[10] + g_aiT32[k][11] * O[11] +
                           g_aiT32[k][12] * O[12] + g_aiT32[k][13] * O[13] +
                           g_aiT32[k][14] * O[14] + g_aiT32[k][15] * O[15] + add) >> shift

        src += 32
        dst += 1

def partialButterflyInverse32(src, dst, shift, line):
    src = pointer(src)
    dst = pointer(dst)

    E, O = 16 * [0], 16 * [0]
    EE, EO = 8 * [0], 8 * [0]
    EEE, EEO = 4 * [0], 4 * [0]
    EEEE, EEEO = 2 * [0], 2 * [0]
    add = 1 << (shift-1)

    for j in xrange(line):
        for k in xrange(16):
            O[k] = g_aiT32[ 1][k] * src[ 1*line] + g_aiT32[ 3][k] * src[ 3*line] + \
                   g_aiT32[ 5][k] * src[ 5*line] + g_aiT32[ 7][k] * src[ 7*line] + \
                   g_aiT32[ 9][k] * src[ 9*line] + g_aiT32[11][k] * src[11*line] + \
                   g_aiT32[13][k] * src[13*line] + g_aiT32[15][k] * src[15*line] + \
                   g_aiT32[17][k] * src[17*line] + g_aiT32[19][k] * src[19*line] + \
                   g_aiT32[21][k] * src[21*line] + g_aiT32[23][k] * src[23*line] + \
                   g_aiT32[25][k] * src[25*line] + g_aiT32[27][k] * src[27*line] + \
                   g_aiT32[29][k] * src[29*line] + g_aiT32[31][k] * src[31*line]
        for k in xrange(8):
            EO[k] = g_aiT32[ 2][k] * src[ 2*line] + g_aiT32[ 6][k] * src[ 6*line] + \
                    g_aiT32[10][k] * src[10*line] + g_aiT32[14][k] * src[14*line] + \
                    g_aiT32[18][k] * src[18*line] + g_aiT32[22][k] * src[22*line] + \
                    g_aiT32[26][k] * src[26*line] + g_aiT32[30][k] * src[30*line]
        for k in xrange(4):
            EEO[k] = g_aiT32[ 4][k] * src[ 4*line] + g_aiT32[12][k] * src[12*line] + \
                     g_aiT32[20][k] * src[20*line] + g_aiT32[28][k] * src[28*line]
        EEEO[0] = g_aiT32[8][0] * src[8*line] + g_aiT32[24][0] * src[24*line]
        EEEO[1] = g_aiT32[8][1] * src[8*line] + g_aiT32[24][1] * src[24*line]
        EEEE[0] = g_aiT32[0][0] * src[0*line] + g_aiT32[16][0] * src[16*line]
        EEEE[1] = g_aiT32[0][1] * src[0*line] + g_aiT32[16][1] * src[16*line]

        EEE[0] = EEEE[0] + EEEO[0]
        EEE[3] = EEEE[0] - EEEO[0]
        EEE[1] = EEEE[1] + EEEO[1]
        EEE[2] = EEEE[1] - EEEO[1]
        for k in xrange(4):
            EE[k  ] = EEE[  k] + EEO[  k]
            EE[k+4] = EEE[3-k] - EEO[3-k]
        for k in xrange(8):
            E[k  ] = EE[  k] + EO[  k]
            E[k+8] = EE[7-k] - EO[7-k]
        for k in xrange(16):
            dst[k+ 0] = Clip3(-32768, 32767, (E[   k] + O[   k] + add) >> shift)
            dst[k+16] = Clip3(-32768, 32767, (E[15-k] - O[15-k] + add) >> shift)

        src += 1
        dst += 32

def xTrMxN(block, coeff, iWidth, iHeight, uiMode):
    shift_1st = g_aucConvertToBit[iWidth] + 1 + cvar.g_uiBitIncrement
    shift_2nd = g_aucConvertToBit[iHeight] + 8
    tmp = (64*64) * [0]

    if iWidth == 4 and iHeight == 4:
        if uiMode != REG_DCT:
            fastForwardDst(block, tmp, shift_1st)
            fastForwardDst(tmp, coeff, shift_2nd)
        else:
            partialButterfly4(block, tmp, shift_1st, iHeight)
            partialButterfly4(tmp, coeff, shift_2nd, iWidth)
    elif iWidth == 8 and iHeight == 8:
        partialButterfly8(block, tmp, shift_1st, iHeight)
        partialButterfly8(tmp, coeff, shift_2nd, iWidth)
    elif iWidth == 16 and iHeight == 16:
        partialButterfly16(block, tmp, shift_1st, iHeight)
        partialButterfly16(tmp, coeff, shift_2nd, iWidth)
    elif iWidth == 32 and iHeight == 32:
        partialButterfly32(block, tmp, shift_1st, iHeight)
        partialButterfly32(tmp, coeff, shift_2nd, iWidth)

def xITrMxN(coeff, block, iWidth, iHeight, uiMode):
    shift_1st = SHIFT_INV_1ST
    shift_2nd = SHIFT_INV_2ND - cvar.g_uiBitIncrement
    tmp = (64*64) * [0]

    if iWidth == 4 and iHeight == 4:
        if uiMode != REG_DCT:
            fastInverseDst(coeff, tmp, shift_1st)
            fastInverseDst(tmp, block, shift_2nd)
        else:
            partialButterflyInverse4(coeff, tmp, shift_1st, iWidth)
            partialButterflyInverse4(tmp, block, shift_2nd, iHeight)
    elif iWidth == 8 and iHeight == 8:
        partialButterflyInverse8(coeff, tmp, shift_1st, iWidth)
        partialButterflyInverse8(tmp, block, shift_2nd, iHeight)
    elif iWidth == 16 and iHeight == 16:
        partialButterflyInverse16(coeff, tmp, shift_1st, iWidth)
        partialButterflyInverse16(tmp, block, shift_2nd, iHeight)
    elif iWidth == 32 and iHeight == 32:
        partialButterflyInverse32(coeff, tmp, shift_1st, iWidth)
        partialButterflyInverse32(tmp, block, shift_2nd, iHeight)


class TComTrQuant(object):

    def __init__(self):
        self.m_pcEstBitsSbac = None

        self.m_qpDelta = (MAX_QP+1) * [0]
        self.m_sliceNsamples = (LEVEL_RANGE+1) * [0]
        self.m_sliceSumC = (LEVEL_RANGE+1) * [0.0]
        self.m_plTempCoeff = None

        self.m_cQP = QpParam()
        self.m_dLambdaLuma = 0.0
        self.m_dLambdaChroma = 0.0
        self.m_dLambda = 0.0
        self.m_uiRDOQOffset = 0
        self.m_uiMaxTrSize = 0
        self.m_bEnc = False
        self.m_bUseRDOQ = False
        self.m_bUseAdaptQpSelect = False
        self.m_useTansformSkipFast = False
        self.m_scalingListEnabledFlag = False
        self.m_quantCoef = [[[[
                        None for l in xrange(SCALING_LIST_DIR_NUM)
                    ] for k in xrange(SCALING_LIST_REM_NUM)
                ] for j in xrange(SCALING_LIST_NUM)
            ] for i in xrange(SCALING_LIST_SIZE_NUM)
        ]
        self.m_dequantCoef = [[[[
                        None for l in xrange(SCALING_LIST_DIR_NUM)
                    ] for k in xrange(SCALING_LIST_REM_NUM)
                ] for j in xrange(SCALING_LIST_NUM)
            ] for i in xrange(SCALING_LIST_SIZE_NUM)
        ]
        self.m_errScale = [[[[
                        None for l in xrange(SCALING_LIST_DIR_NUM)
                    ] for k in xrange(SCALING_LIST_REM_NUM)
                ] for j in xrange(SCALING_LIST_NUM)
            ] for i in xrange(SCALING_LIST_SIZE_NUM)
        ]

        self.m_cQP.clear()
  
        # allocate temporary buffers
        self.m_plTempCoeff = (MAX_CU_SIZE*MAX_CU_SIZE) * [0]
  
        # allocate bit estimation class  (for RDOQ)
        self.m_pcEstBitsSbac = estBitsSbacStruct()
        self._initScalingList()

    def init(self, uiMaxWidth, uiMaxHeight, uiMaxTrSize,
             iSymbolMode=0, aTable4=None, aTable8=None, aTableLastPosVlcIndex=None,
             bUseRDOQ=False, bEnc=False,
             useTransformSkipFast=False, bUseAdaptQpSelect=False):
        self.m_uiMaxTrSize = uiMaxTrSize
        self.m_bEnc = bEnc
        self.m_bUseRDOQ = bUseRDOQ
        self.m_bUseAdaptQpSelect = bUseAdaptQpSelect
        self.m_useTansformSkipFast = useTransformSkipFast

    def transformNxN(self, pcCU, rpcResidual, uiStride, rpcCoeff, rpcArlCoeff,
                     uiWidth, uiHeight, uiAbsSum, eTType, uiAbsPartIdx,
                     useTransformSkip=False):
        rpcArlCoeff = pointer(rpcArlCoeff)
        rpcCoeff = pointer(rpcCoeff, type='int *')
        rpcResidual = pointer(rpcResidual, type='short *')

        if pcCU.getCUTransquantBypass(uiAbsPartIdx):
            uiAbsSum = 0
            for k in xrange(uiHeight):
                for j in xrange(uiWidth):
                    rpcCoeff[k * uiWidth + j] = rpcResidual[k * uiStride + j]
                    uiAbsSum += abs(rpcResidual[k * uiStride + j])
            return uiAbsSum

        uiMode = 0
        if eTType == TEXT_LUMA and pcCU.getPredictionMode(uiAbsPartIdx) == MODE_INTRA:
            uiMode = pcCU.getLumaIntraDir(uiAbsPartIdx)
        else:
            uiMode = REG_DCT

        uiAbsSum = 0
        assert(pcCU.getSlice().getSPS().getMaxTrSize() >= uiWidth)
        if useTransformSkip:
            self._xTransformSkip(rpcResidual, uiStride, self.m_plTempCoeff, uiWidth, uiHeight)
        else:
            self._xT(uiMode, rpcResidual, uiStride, self.m_plTempCoeff, uiWidth, uiHeight)
        self._xQuant(pcCU, self.m_plTempCoeff, rpcCoeff, rpcArlCoeff,
                     uiWidth, uiHeight, uiAbsSum, eTType, uiAbsPartIdx)
        return uiAbsSum

    def invtransformNxN(self, transQuantBypass, eText, uiMode,
                        rpcResidual, uiStride, rpcCoeff,
                        uiWidth, uiHeight, scalingListType, useTransformSkip=False):
        rpcCoeff = pointer(rpcCoeff, type='int *')
        rpcResidual = pointer(rpcResidual, type='short *')

        if transQuantBypass:
            for k in xrange(uiHeight):
                for j in xrange(uiWidth):
                    rpcResidual[k * uiStride + j] = rpcCoeff[k * uiWidth + j]
            return
        self._xDeQuant(rpcCoeff, self.m_plTempCoeff, uiWidth, uiHeight, scalingListType)
        if useTransformSkip:
            self._xITransformSkip(self.m_plTempCoeff, rpcResidual, uiStride, uiWidth, uiHeight)
        else:
            self._xIT(uiMode, self.m_plTempCoeff, rpcResidual, uiStride, uiWidth, uiHeight)

    def invRecurTransformNxN(self, pcCU, uiAbsPartIdx, eTxt,
                             rpcResidual, uiAddr, uiStride,
                             uiWidth, uiHeight, uiMaxTrMode, uiTrMode, rpcCoeff):
        rpcCoeff = pointer(rpcCoeff, type='int *')
        rpcResidual = pointer(rpcResidual, type='short *')

        if not pcCU.getCbf(uiAbsPartIdx, eTxt, uiTrMode):
            return

        uiLumaTrMode = uiChromaTrMode = 0
        uiLumaTrMode, uiChromaTrMode = \
            pcCU.convertTransIdx(uiAbsPartIdx, pcCU.getTransformIdx(uiAbsPartIdx),
            uiLumaTrMode, uiChromaTrMode)
        uiStopTrMode = (uiLumaTrMode if eTxt == TEXT_LUMA else uiChromaTrMode)

        if uiTrMode == uiStopTrMode:
            uiDepth = pcCU.getDepth(uiAbsPartIdx) + uiTrMode
            uiLog2TrSize = g_aucConvertToBit[pcCU.getSlice().getSPS().getMaxCUWidth() >> uiDepth] + 2
            if eTxt != TEXT_LUMA and uiLog2TrSize == 2:
                uiQPDiv = pcCU.getPic().getNumPartInCU() >> ((uiDepth-1) << 1)
                if (uiAbsPartIdx % uiQPDiv) != 0:
                    return
                uiWidth <<= 1
                uiHeight <<= 1
            pResi = rpcResidual + uiAddr

            scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[eTxt]
            assert(scalingListType < 6)
            self.invtransformNxN(pcCU.getCUTransquantBypass(uiAbsPartIdx), eTxt, REG_DCT,
                pResi, uiStride, rpcCoeff, uiWidth, uiHeight, scalingListType,
                pcCU.getTransformSkip(uiAbsPartIdx, eTxt))
        else:
            uiTrMode += 1
            uiWidth >>= 1
            uiHeight >>= 1
            trWidth = uiWidth
            trHeight = uiHeight
            uiAddrOffset = trHeight * uiStride
            uiCoefOffset = trWidth * trHeight
            uiPartOffset = pcCU.getTotalNumPart() >> (uiTrMode << 1)

            self.invRecurTransformNxN(pcCU, uiAbsPartIdx, eTxt, rpcResidual, uiAddr,
                uiStride, uiWidth, uiHeight, uiMaxTrMode, uiTrMode, rpcCoeff)
            rpcCoeff += uiCoefOffset
            uiAbsPartIdx += uiPartOffset
            self.invRecurTransformNxN(pcCU, uiAbsPartIdx, eTxt, rpcResidual, uiAddr+trWidth,
                uiStride, uiWidth, uiHeight, uiMaxTrMode, uiTrMode, rpcCoeff)
            rpcCoeff += uiCoefOffset
            uiAbsPartIdx += uiPartOffset
            self.invRecurTransformNxN(pcCU, uiAbsPartIdx, eTxt, rpcResidual, uiAddr+uiAddrOffset,
                uiStride, uiWidth, uiHeight, uiMaxTrMode, uiTrMode, rpcCoeff)
            rpcCoeff += uiCoefOffset
            uiAbsPartIdx += uiPartOffset
            self.invRecurTransformNxN(pcCU, uiAbsPartIdx, eTxt, rpcResidual, uiAddr+uiAddrOffset+trWidth,
                uiStride, uiWidth, uiHeight, uiMaxTrMode, uiTrMode, rpcCoeff)

    def setQPforQuant(self, qpy, eTxtType, qpBdOffset, chromaQPOffset):
        qpScaled = 0

        if eTxtType == TEXT_LUMA:
            qpScaled = qpy + qpBdOffset
        else:
            qpScaled = Clip3(-qpBdOffset, 57, qpy + chromaQPOffset)

            if qpScaled < 0:
                qpScaled = qpScaled + qpBdOffset
            else:
                qpScaled = g_aucChromaScale[qpScaled] + qpBdOffset
        self.m_cQP.setQpParam(qpScaled)

    def setLambda(self, dLambdaLuma, dLambdaChroma):
        self.m_dLambdaLuma = dLambdaLuma
        self.m_dLambdaChroma = dLambdaChroma
    def selectLambda(self, eTType):
        self.dLambda = self.m_dLambdaLuma if eTType == TEXT_LUMA else self.m_dLambdaChroma
    def setRDOQOffset(self, uiRDOQOffset):
        self.m_uiRDOQOffset = uiRDOQOffset

    @staticmethod
    def calcPatternSigCtx(sigCoeffGroupFlag, posXCG, posYCG, width, height):
        sigCoeffGroupFlag = pointer(sigCoeffGroupFlag, type='uint *')

        if width == 4 and height == 4:
            return -1

        sigRight = 0
        sigLower = 0

        width >>= 2
        height >>= 2
        if posXCG < width-1:
            sigRight = (1 if sigCoeffGroupFlag[posYCG * width + posXCG + 1] != 0 else 0)
        if posYCG < height-1:
            sigLower = (1 if sigCoeffGroupFlag[(posYCG+1) * width + posXCG] != 0 else 0)
        return sigRight + (sigLower<<1)

    @staticmethod
    def getSigCtxInc(patternSigCtx, scanIdx, posX, posY, blockType, width, height, textureType):
        ctxIndMap = (
            0, 1, 4, 5,
            2, 3, 4, 5,
            6, 6, 8, 8,
            7, 7, 8, 8
        )

        if posX + posY == 0:
            return 0

        if blockType == 2:
            return ctxIndMap[4 * posY + posX]

        offset = (9 if scanIdx == SCAN_DIAG else 15) if blockType == 3 else \
                 (21 if textureType == TEXT_LUMA else 12)

        posXinSubset = posX - ((posX>>2) << 2)
        posYinSubset = posY - ((posY>>2) << 2)
        cnt = 0
        if patternSigCtx == 0:
            cnt = (2 if posXinSubset + posYinSubset == 0 else 1) if posXinSubset + posYinSubset <= 2 else 0
        elif patternSigCtx == 1:
            cnt = (2 if posYinSubset == 0 else 1) if posYinSubset <= 1 else 0
        elif patternSigCtx == 2:
            cnt = (2 if posXinSubset == 0 else 1) if posXinSubset <= 1 else 0
        else:
            cnt = 2

        return (3 if textureType == TEXT_LUMA and (posX>>2) + (posY>>2) > 0 else 0) + offset + cnt

    @staticmethod
    def getSigCoeffGroupCtxInc(uiSigCoeffGroupFlag, uiCGPosX, uiCGPosY, scanIdx, width, height):
        uiSigCoeffGroupFlag = pointer(uiSigCoeffGroupFlag, type='uint *')

        uiRight = 0
        uiLower = 0

        width >>= 2
        height >>= 2

        if uiCGPosX < width-1:
            uiRight = (1 if uiSigCoeffGroupFlag[uiCGPosY * width + uiCGPosX + 1] != 0 else 0)
        if uiCGPosY < height-1:
            uiLower = (1 if uiSigCoeffGroupFlag[(uiCGPosY+1) * width + uiCGPosX] != 0 else 0)
        return uiRight or uiLower

    def _initScalingList(self):
        for sizeId in xrange(SCALING_LIST_SIZE_NUM):
            for listId in xrange(g_scalingListNum[sizeId]):
                for qp in xrange(SCALING_LIST_REM_NUM):
                    self.m_quantCoef[sizeId][listId][qp][SCALING_LIST_SQT] = g_scalingListSize[sizeId] * [0]
                    self.m_dequantCoef[sizeId][listId][qp][SCALING_LIST_SQT] = g_scalingListSize[sizeId] * [0]
                    self.m_errScale[sizeId][listId][qp][SCALING_LIST_SQT] = g_scalingListSize[sizeId] * [0.0]

                    if sizeId == SCALING_LIST_8x8 or (sizeId == SCALING_LIST_16x16 and listId < 2):
                        for dir in xrange(SCALING_LIST_VER, SCALING_LIST_DIR_NUM):
                            self.m_quantCoef[sizeId][listId][qp][dir] = g_scalingListSize[sizeId] * [0]
                            self.m_dequantCoef[sizeId][listId][qp][dir] = g_scalingListSize[sizeId] * [0]
                            self.m_errScale[sizeId][listId][qp][dir] = g_scalingListSize[sizeId] * [0.0]
        #copy for NSQT
        for qp in xrange(SCALING_LIST_REM_NUM):
            for dir in xrange(SCALING_LIST_VER, SCALING_LIST_DIR_NUM):
                self.m_quantCoef[SCALING_LIST_16x16][3][qp][dir] = self.m_quantCoef[SCALING_LIST_16x16][1][qp][dir]
                self.m_dequantCoef[SCALING_LIST_16x16][3][qp][dir] = self.m_dequantCoef[SCALING_LIST_16x16][1][qp][dir]
                self.m_errScale[SCALING_LIST_16x16][3][qp][dir] = self.m_errScale[SCALING_LIST_16x16][1][qp][dir]
            self.m_quantCoef[SCALING_LIST_32x32][3][qp][SCALING_LIST_SQT] = self.m_quantCoef[SCALING_LIST_32x32][1][qp][SCALING_LIST_SQT]
            self.m_dequantCoef[SCALING_LIST_32x32][3][qp][SCALING_LIST_SQT] = self.m_dequantCoef[SCALING_LIST_32x32][1][qp][SCALING_LIST_SQT]
            self.m_errScale[SCALING_LIST_32x32][3][qp][SCALING_LIST_SQT] = self.m_errScale[SCALING_LIST_32x32][1][qp][SCALING_LIST_SQT]

    def _destroyScalingList(self):
        for sizeId in xrange(SCALING_LIST_SIZE_NUM):
            for listId in xrange(g_scalingListNum[sizeId]):
                for qp in xrange(SCALING_LIST_REM_NUM):
                    if self.m_quantCoef[sizeId][listId][qp][SCALING_LIST_SQT]:
                        del self.m_quantCoef[sizeId][listId][qp][SCALING_LIST_SQT]
                    if self.m_dequantCoef[sizeId][listId][qp][SCALING_LIST_SQT]:
                        del self.m_dequantCoef[sizeId][listId][qp][SCALING_LIST_SQT]
                    if self.m_errScale[sizeId][listId][qp][SCALING_LIST_SQT]:
                        del self.m_errScale[sizeId][listId][qp][SCALING_LIST_SQT]
                    if sizeId == SCALING_LIST_8x8 or (sizeId == SCALING_LIST_16x16 and listId < 2):
                        for dir in xrange(SCALING_LIST_VER, SCALING_LIST_DIR_NUM):
                            if self.m_quantCoef[sizeId][listId][qp][dir]:
                                del self.m_quantCoef[sizeId][listId][qp][dir]
                            if self.m_dequantCoef[sizeId][listId][qp][dir]:
                                del self.m_dequantCoef[sizeId][listId][qp][dir]
                            if self.m_errScale[sizeId][listId][qp][dir]:
                                del self.m_errScale[sizeId][listId][qp][dir]

    def setErrScaleCoeff(self, list, size, qp, dir):
        uiLog2TrSize = g_aucConvertToBit[g_scalingListSizeX[size]] + 2
        uiBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement

        iTransformShift = MAX_TR_DYNAMIC_RANGE - uiBitDepth - uiLog2TrSize

        uiMaxNumCoeff = g_scalingListSize[size]
        piQuantCoeff = self.getQuantCoeff(list, qp, size, dir)
        pdErrScale = self.getErrScaleCoeff(list, size, qp, dir)

        dErrScale = float(1 << SCALE_BITS)
        dErrScale = dErrScale * pow(2.0, -2.0*iTransformShift)
        for i in xrange(uiMaxNumCoeff):
            pdErrScale[i] = dErrScale / \
                float(piQuantCoeff[i]) / float(piQuantCoeff[i]) / \
                float(1 << (2 * cvar.g_uiBitIncrement))

    def getErrScaleCoeff(self, list, size, qp, dir):
        return self.m_errScale[size][list][qp][dir]
    def getQuantCoeff(self, list, qp, size, dir):
        return self.m_quantCoef[size][list][qp][dir]
    def getDequantCoeff(self, list, qp, size, dir):
        return self.m_dequantCoef[size][list][qp][dir]
    def setUseScalingList(self, bUseScalingList):
        self.m_scalingListEnabledFlag = bUseScalingList
    def getUseScalingList(self):
        return self.m_scalingListEnabledFlag
    def setFlatScalingList(self):
        for size in xrange(SCALING_LIST_SIZE_NUM):
            for list in xrange(g_scalingListNum[size]):
                for qp in xrange(SCALING_LIST_REM_NUM):
                    self.xSetFlatScalingList(list, size, qp)
                    self.setErrScaleCoeff(list, size, qp, SCALING_LIST_SQT)
                    if size == SCALING_LIST_32x32 or size == SCALING_LIST_16x16:
                        self.setErrScaleCoeff(list, size-1, qp, SCALING_LIST_HOR)
                        self.setErrScaleCoeff(list, size-1, qp, SCALING_LIST_VER)

    def xSetFlatScalingList(self, list, size, qp):
        num = g_scalingListSize[size]
        numDiv4 = num >> 2
        quantScales = g_quantScales[qp]
        invQuantScales = g_invQuantScales[qp] << 4

        quantcoeff = self.getQuantCoeff(list, qp, size, SCALING_LIST_SQT)
        dequantcoeff = self.getDequantCoeff(list, qp, size, SCALING_LIST_SQT)

        for i in xrange(num):
            quantcoeff[i] = quantScales
            dequantcoeff[i] = invQuantScales

        if size == SCALING_LIST_32x32 or size == SCALING_LIST_16x16:
            quantcoeff = self.getQuantCoeff(list, qp, size-1, SCALING_LIST_HOR)
            dequantcoeff = self.getDequantCoeff(list, qp, size-1, SCALING_LIST_HOR)

            for i in xrange(numDiv4):
                quantcoeff[i] = quantScales
                dequantcoeff[i] = invQuantScales

            quantcoeff = self.getQuantCoeff(list, qp, size-1, SCALING_LIST_VER)
            dequantcoeff = self.getDequantCoeff(list, qp, size-1, SCALING_LIST_VER)

            for i in xrange(numDiv4):
                quantcoeff[i] = quantScales
                dequantcoeff[i] = invQuantScales

    def xSetScalingListEnc(self, scalingList, list, size, qp):
        width = g_scalingListSizeX[size]
        height = g_scalingListSizeX[size]
        ratio = g_scalingListSizeX[size] / \
            min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size]))
        coeff = scalingList.getScalingListAddress(size, list)
        quantcoeff = self.getQuantCoeff(list, qp, size, SCALING_LIST_SQT)

        self.processScalingListEnc(
            coeff, quantcoeff, g_quantScales[qp]<<4, height, width, ratio,
            min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size])),
            scalingList.getScalingListDC(size, list))

        if size == SCALING_LIST_32x32 or size == SCALING_LIST_16x16:
            quantcoeff = self.getQuantCoeff(list, qp, size-1, SCALING_LIST_VER)
            self.processScalingListEnc(
                coeff, quantcoeff, g_quantScales[qp]<<4, height, width>>2, ratio,
                min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size])),
                scalingList.getScalingListDC(size, list))

            quantcoeff = self.getQuantCoeff(list, qp, size-1, SCALING_LIST_HOR)
            self.processScalingListEnc(
                coeff, quantcoeff, g_quantScales[qp]<<4, height>>2, width, ratio,
                min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size])),
                scalingList.getScalingListDC(size, list))

    def xSetScalingListDec(self, scalingList, list, size, qp):
        width = g_scalingListSizeX[size]
        height = g_scalingListSizeX[size]
        ratio = g_scalingListSizeX[size] / \
            min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size]))
        coeff = scalingList.getScalingListAddress(size, list)
        dequantcoeff = self.getDequantCoeff(list, qp, size, SCALING_LIST_SQT)

        self.processScalingListDec(
            coeff, dequantcoeff, g_invQuantScales[qp], height, width, ratio,
            min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size])),
            scalingList.getScalingListDC(size, list))

        if size == SCALING_LIST_32x32 or size == SCALING_LIST_16x16:
            dequantcoeff = self.getDequantCoeff(list, qp, size-1, SCALING_LIST_VER)
            self.processScalingListDec(
                coeff, dequantcoeff, g_invQuantScales[qp], height, width>>2, ratio,
                min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size])),
                scalingList.getScalingListDC(size, list))

            dequantcoeff = self.getDequantCoeff(list, qp, size-1, SCALING_LIST_HOR)
            self.processScalingListDec(
                coeff, dequantcoeff, g_invQuantScales[qp], height>>2, width, ratio,
                min(MAX_MATRIX_SIZE_NUM, int(g_scalingListSizeX[size])),
                scalingList.getScalingListDC(size, list))

    def setScalingList(self, scalingList):
        for size in xrange(SCALING_LIST_SIZE_NUM):
            for list in xrange(g_scalingListNum[size]):
                for qp in xrange(SCALING_LIST_REM_NUM):
                    self.xSetScalingListEnc(scalingList, list, size, qp)
                    self.xSetScalingListDec(scalingList, list, size, qp)
                    self.setErrScaleCoeff(list, size, qp, SCALING_LIST_SQT)
                    if size == SCALING_LIST_32x32 or size == SCALING_LIST_16x16:
                        self.setErrScaleCoeff(list, size-1, qp, SCALING_LIST_HOR)
                        self.setErrScaleCoeff(list, size-1, qp, SCALING_LIST_VER)

    def setScalingListDec(self, scalingList):
        for size in xrange(SCALING_LIST_SIZE_NUM):
            for list in xrange(g_scalingListNum[size]):
                for qp in xrange(SCALING_LIST_REM_NUM):
                    self.xSetScalingListDec(scalingList, list, size, qp)

    def processScalingListEnc(self, coeff, quantcoeff, quantScales, height, width, ratio, sizuNum, dc):
        nsqth = (4 if height < width else 1) #height ratio for NSQT
        nsqtw = (4 if width < height else 1) #width ratio for NSQT
        for j in xrange(height):
            for i in xrange(width):
                quantcoeff[j * width + i] = \
                    quantScales / coeff[sizuNum * (j * nsqth / ratio) + i * nsqtw / ratio]
        if ratio > 1:
            quantcoeff[0] = quantScales / dc

    def processScalingListDec(self, coeff, dequantcoeff, invQuantScales, height, width, ratio, sizuNum, dc):
        for j in xrange(height):
            for i in xrange(width):
                dequantcoeff[j * width + i] = \
                    invQuantScales * coeff[sizuNum * (j / ratio) + i / ratio]
        if ratio > 1:
            dequantcoeff[0] = invQuantScales * dc

    def initSliceQpDelta(self):
        for qp in xrange(MAX_QP+1):
            self.m_qpDelta[qp] = (0 if qp < 17 else 1)

    def storeSliceQpNext(self, pcSlice):
        qpBase = pcSlice.getSliceQpBase()
        sliceQpused = pcSlice.getSliceQp()
        sliceQpnext = 0
        alpha = 0.5 if qpBase < 17 else 1.0

        cnt = 0
        for u in xrange(1, LEVEL_RANGE+1):
            cnt += self.m_sliceNsamples[u]

        if not self.m_bUseRDOQ:
            alpha = 0.5

        if cnt > 120:
            sum = 0.0
            k = 0
            for u in xrange(1, LEVEL_RANGE):
                sum += u * self.m_sliceSumC[u]
                k += u * u * self.m_sliceNsamples[u]

            v = 0
            q = (MAX_QP+1) * [0.0]
            for v in xrange(0, MAX_QP+1):
                q[v] = float(g_invQuantScales[v%6] * (1<<(v/6))) / 64

            qnext = sum/k * q[sliceQpused] / (1<<ARL_C_PRECISION)

            for v in xrange(MAX_QP):
                if qnext < alpha * q[v] + (1-alpha) * q[v+1]:
                    break
            sliceQpnext = Clip3(sliceQpused-3, sliceQpused+3, v)
        else:
            sliceQpnext = sliceQpused

        self.m_qpDelta[qpBase] = sliceQpnext - qpBase

    def clearSliceARLCnt(self):
        for i in xrange(LEVEL_RANGE+1):
            self.m_sliceSumC[i] = 0.0
            self.m_sliceNsamples[i] = 0

    def getQpDelta(self, qp):
        return self.m_qpDelta[qp]
    def getSliceNSamples(self):
        return self.m_sliceNsamples
    def getSliceSumC(self):
        return self.m_sliceSumC

    def _xT(self, uiMode, piBlkResi, uiStride, psCoeff, iWidth, iHeight):
        block = (64*64) * [0]
        coeff = (64*64) * [0]
        for j in xrange(iHeight):
            for i in xrange(iWidth):
                block[j * iWidth + i] = piBlkResi[j * uiStride + i]
        xTrMxN(block, coeff, iWidth, iHeight, uiMode)
        for j in xrange(iHeight * iWidth):
            psCoeff[j] = coeff[j]

    def _xTransformSkip(self, piBlkResi, uiStride, psCoeff, width, height):
        assert(width == height)
        uiLog2TrSize = g_aucConvertToBit[width] + 2
        uiBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        shift = MAX_TR_DYNAMIC_RANGE - uiBitDepth - uiLog2TrSize
        if shift >= 0:
            transformSkipShift = shift
            for j in xrange(height):
                for k in xrange(width):
                    psCoeff[j * height + k] = piBlkResi[j * uiStride + k] << transformSkipShift
        else:
            #The case when uiBitDepth > 13
            transformSkipShift = -shift
            offset = 1 << (transformSkipShift-1)
            for j in xrange(height):
                for k in xrange(width):
                    psCoeff[j * height + k] = (piBlkResi[j * uiStride + k] + offset) >> transformSkipShift

    def _signBitHidingHDQ(self, pcCU, pQCoef, pCoef, scan, deltaU, width, height):
        lastCG = -1
        absSum = 0

        for subSet in xrange((width*height-1) >> LOG2_SCAN_SET_SIZE, -1, -1):
            subPos = subSet << LOG2_SCAN_SET_SIZE
            firstNZPosInCG = SCAN_SET_SIZE
            lastNZPosInCG = -1
            absSum = 0

            for n in xrange(SCAN_SET_SIZE-1, -1, -1):
                if pQCoef[scan[n + subPos]]:
                    lastNZPosInCG = n
                    break

            for n in xrange(SCAN_SET_SIZE):
                if pQCoef[scan[n + subPos]]:
                    firstNZPosInCG = n
                    break

            for n in xrange(firstNZPosInCG, lastNZPosInCG+1):
                absSum += pQCoef[scan[n + subPos]]

            if lastNZPosInCG >= 0 and lastCG == -1:
                lastCG = 1

            if lastNZPosInCG - firstNZPosInCG >= SBH_THRESHOLD:
                signbit = (0 if pQCoef[scan[subPos+firstNZPosInCG]] > 0 else 1)
                if signbit != (absSum & 0x1): # compare signbit with sum_parity
                    minCostInc = MAX_INT
                    minPos = -1
                    finalChange = 0
                    curCost = MAX_INT
                    curChange = 0

                    for n in xrange(lastNZPosInCG if lastCG == 1 else SCAN_SET_SIZE-1, -1, -1):
                        blkPos = scan[n + subPos]
                        if pQCoef[blkPos] != 0:
                            if deltaU[blkPos] > 0:
                                curCost = -deltaU[blkPos]
                                curChange = 1
                            else:
                                # curChange = -1
                                if n == firstNZPosInCG and abs(pQCoef[blkPos]) == 1:
                                    curCost = MAX_INT
                                else:
                                    curCost = deltaU[blkPos]
                                    curChange = -1
                        else:
                            if n < firstNZPosInCG:
                                thisSignBit = (0 if pCoef[blkPos] >= 0 else 1)
                                if thisSignBit != signbit:
                                    curCost = MAX_INT
                                else:
                                    curCost = -deltaU[blkPos]
                                    curChange = 1
                            else:
                                curCost = -deltaU[blkPos]
                                curChange = 1

                        if curCost < minCostInc:
                            minCostInc = curCost
                            finalChange = curChange
                            minPos = blkPos

                    if pQCoef[minPos] == 32767 or pQCoef[minPos] == -32768:
                        finalChange = -1

                    if pQCoef[minPos] >= 0:
                        pQCoef[minPos] += finalChange
                    else:
                        pQCoef[minPos] -= finalChange
            if lastCG == 1:
                lastCG = 0

    def _xQuant(self, pcCU, pSrc, pDes, pArlDes, iWidth, iHeight, uiAcSum, eTType, uiAbsPartIdx):
        piCoef = pSrc
        piQCoef = pDes
        piArlCCoef = pArlDes
        iAdd = 0

        useRDOQForTransformSkip = not (self.m_useTansformSkipFast and pcCU.getTransformSkip(uiAbsPartIdx, eTType))
        if self.m_bUseRDOQ and (eTType == TEXT_LUMA or RDOQ_CHROMA) and useRDOQForTransformSkip:
            self._xRateDistOptQuant(pcCU, piCoef, pDes, pArlDes, iWidth, iHeight, uiAcSum, eTType, uiAbsPartIdx)
        else:
            log2BlockSize = g_aucConvertToBit[iWidth] + 2

            scanIdx = pcCU.getCoefScanIdx(uiAbsPartIdx, iWidth, eTType==TEXT_LUMA, pcCU.isIntra(uiAbsPartIdx))
            if scanIdx == SCAN_ZIGZAG:
                scanIdx = SCAN_DIAG

            scan = g_auiSigLastScan[scanIdx][log2BlockSize-1]
            deltaU = (32*32) * [0]

            cQpBase = QpParam()
            iQpBase = pcCU.getSlice().getSliceQpBase()

            qpScaled = 0
            qpBDOffset = pcCU.getSlice().getSPS().getQpBDOffsetY() if eTType == TEXT_LUMA else \
                         pcCU.getSlice().getSPS().getQpBDOffsetC()

            if eTType == TEXT_LUMA:
                qpScaled = iQpBase + qpBDOffset
            else:
                qpScaled = Clip3(-qpBDOffset, 57, iQpBase)

                if qpScaled < 0:
                    qpScaled = qpScaled + qpBDOffset
                else:
                    qpScaled = g_aucChromaScale[qpScaled] + qpBDOffset
            cQpBase.setQpParam(qpScaled)

            dir = SCALING_LIST_SQT

            uiLog2TrSize = g_aucConvertToBit[iWidth] + 2
            scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[eTType]
            assert(scalingListType < 6)
            piQuantCoeff = self.getQuantCoeff(scalingListType, self.m_cQP.m_iRem, uiLog2TrSize-2, dir)

            uiBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
            iTransformShift = MAX_TR_DYNAMIC_RANGE - uiBitDepth - uiLog2TrSize

            iQBits = QUANT_SHIFT + self.m_cQP.m_iPer + iTransformShift

            iAdd = (171 if pcCU.getSlice().getSliceType() == I_SLICE else 85) << (iQBits-9)

            iQBits = QUANT_SHIFT + cQpBase.m_iPer + iTransformShift
            iAdd = (171 if pcCU.getSlice().getSliceType() == I_SLICE else 85) << (iQBits-9)
            iQBitsC = QUANT_SHIFT + cQpBase.m_iPer + iTransformShift - ARL_C_PRECISION
            iAddC = 1 << (iQBits-1)

            qBits8 = iQBits - 8
            for n in xrange(iWidth * iHeight):
                uiBlockPos = n
                iLevel = piCoef[uiBlockPos]
                iSign = (-1 if iLevel < 0 else 1)

                tmpLevel = abs(iLevel) * piQuantCoeff[uiBlockPos]
                if self.m_bUseAdaptQpSelect:
                    piArlCCoef[uiBlockPos] = (tmpLevel + iAddC) >> iQBitsC
                iLevel = (tmpLevel + iAdd) >> iQBits
                deltaU[uiBlockPos] = (tmpLevel - (iLevel<<iQBits)) >> qBits8
                uiAcSum += iLevel
                iLevel *= iSign
                piQCoef[uiBlockPos] = Clip3(-32768, 32767, iLevel)
            if pcCU.getSlice().getPPS().getSignHighFlag():
                if uiAcSum >= 2:
                    self._signBitHidingHDQ(pcCU, piQCoef, piCoef, scan, deltaU, iWidth, iHeight)

    def _xRateDistOptQuant(self, pcCU, plSrcCoeff, piDstCoeff, piArlDstCoeff,
                           uiWidth, uiHeight, uiAbsSum, eTType, uiAbsPartIdx):
        iQBits = self.m_cQP.m_iBits
        dTemp = 0
        dir = SCALING_LIST_SQT
        uiLog2TrSize = g_aucConvertToBit[uiWidth] + 2
        uiQ = g_quantScales[self.m_cQP.rem()]

        uiBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        iTransformShift = MAX_TR_DYNAMIC_RANGE - uiBitDepth - uiLog2TrSize
        uiGoRiceParam = 0
        d64BlockUncodedCost = 0.0
        uiLog2BlkSize = g_aucConvertToBit[uiWidth] + 2
        uiMaxNumCoeff = uiWidth * uiHeight
        scalingListType = (0 if pcCU.isIntra(uiAbsPartIdx) else 3) + g_eTTable[eTType]
        assert(scalingListType < 6)

        iQBits = QUANT_SHIFT + self.m_cQP.m_iPer + iTransformShift
        dErrScale = 0.0
        pdErrScaleOrg = set.getErrScaleCoeff(scalingListType, uiLog2TrSize-2, self.m_cQP.m_iRem, dir)
        piQCoefOrg = self.getQuantCoeff(scalingListType, self.m_cQP.m_iRem, uiLog2TrSize-2, dir)
        piQCoef = piQCoefOrg
        pdErrScale = pdErrScaleOrg
        iQBitsC = iQBits - ARL_C_PRECISION
        iAddC = 1 << (iQBitsC-1)
        uiScanIdx = pcCU.getCoefScanIdx(uiAbsPartIdx, uiWidth, eTType==TEXT_LUMA, pcCU.isIntra(uiAbsPartIdx))
        if uiScanIdx == SCAN_ZIGZAG:
            uiScanIdx = SCAN_DIAG
        blockType = uiLog2BlkSize

        for i in xrange(uiMaxNumCoeff):
            piArlCCoef[i] = 0

        pdCostCoeff = (32*32) * [0.0]
        pdCostSig = (32*32) * [0.0]
        pdCostCoeff0 = (32*32) * [0.0]
        rateIncUp = (32*32) * [0]
        rateIncDown = (32*32) * [0]
        sigRateDelta = (32*32) * [0]
        deltaU = (32*32) * [0]

        scanCG = g_auiSigLastScan[uiScanIdx][uiLog2BlkSize-2-1 if uiLog2BlkSize > 3 else 0]
        if uiLog2BlkSize == 3:
            scanCG = g_sigLastScan8x8[uiScanIdx]
        elif uiLog2BlkSize == 5:
            scanCG = g_sigLastScanCG32x32
        uiCGSize = (1 << MLS_CG_SIZE)
        pdCostCoeffGroupSig = MLS_GRP_NUM * [0.0]
        uiSigCoeffGroupFlag = MLS_GRP_NUM * [0]
        uiNumBlkSide = uiWidth / MLS_CG_SIZE
        iCGLastScanPos = -1

        uiCtxSet = 0
        c1 = 1
        c2 = 0
        d64BaseCost = 0.0
        iLastScanPos = -1
        dTemp = dErrScale

        c1Idx = 0
        c2Idx = 0
        baseLevel = 0

        scan = g_auiSigLastScan[uiScanIdx][uiLog2BlkSize-1]

        uiCGNum = uiWidth * uiHeight >> MLS_CG_SIZE
        iScanPos = 0
        rdStats = coeffGroupRDStats()

        for iCGScanPos in xrange(uiCGNum-1, -1, -1):
            uiCGBlkPos = scanCG[iCGScanPos]
            uiCGPosY = uiCGBlkPos / uiNumBlkSide
            uiCGPosX = uiCGBlkPos - (uiCGPosY * uiNumBlkSide)
            rdStats = coeffGroupRDStats()

            patternSigCtx = TComTrQuant.calcPatternSigCtx(
                uiSigCoeffGroupFlag, uiCGPosX, uiCGPosY, uiWidth, uiHeight)
            for iScanPosinCG in xrange(uiCGSize-1, -1, -1):
                iScanPos = iCGScanPos * uiCGSize + iScanPosinCG
                #===== quantization =====
                uiBlkPos = scan[iScanPos]
                # set coeff
                uiQ = piQCoef[uiBlkPos]
                dTemp = pdErrScale[uiBlkPos]
                lLevelDouble = plSrcCoeff[uiBlkPos]
                lLevelDouble = min(abs(lLevelDouble) * uiQ, MAX_INT - (1 << (iQBits-1)))
                if self.m_bUseAdaptQpSelect:
                    piArlDstCoeff[uiBlkPos] = int((lLevelDouble+iAddC) >> iQBitsC)
                uiMaxAbsLevel = (lLevelDouble + (1 << (iQBits-1))) >> iQBits

                dErr = float(lLevelDouble)
                pdCostCoeff0[iScanPos] = dErr * dErr * dTemp
                d64BlockUncodedCost += pdCostCoeff0[iScanPos]
                piDstCoeff[uiBlkPos] = uiMaxAbsLevel

                if uiMaxAbsLevel > 0 and iLastScanPos < 0:
                    iLastScanPos = iScanPos
                    uiCtxSet = (0 if iScanPos < SCAN_SET_SIZE or eTType != TEXT_LUMA else 2)
                    iCGLastScanPos = iCGScanPos

                if iLastScanPos >= 0:
                    #===== coefficient level estimation =====
                    uiLevel = 0
                    uiOneCtx = 4 * uiCtxSet + c1
                    uiAbsCtx = uiCtxSet + c2

                    if iScanPos == iLastScanPos:
                        uiLevel = self._xGetCodedLevel(
                            pdCostCoeff[iScanPos], pdCostCoeff0[iScanPos], pdCostSig[iScanPos],
                            lLevelDouble, uiMaxAbsLevel, 0, uiOneCtx, uiAbsCtx, uiGoRiceParam,
                            c1Idx, c2Idx, iQBits, dTemp, 1)
                    else:
                        uiPosX = uiBlkPos >> uiLog2BlkSize
                        uiPosX = uiBlkPos - (uiPosY << uiLog2BlkSize)
                        uiCtxSig = self.getSigCtxInc(patternSigCtx, uiScanIdx, uiPosX, uiPosY, blockType, uiWidth, uiHeight, eTType)
                        uiLevel = self._xGetCodedLevel(
                            pdCostCoeff[iScanPos], pdCostCoeff0[iScanPos], pdCostSig[iScanPos],
                            lLevelDouble, uiMaxAbsLevel, uiCtxSig, uiOneCtx, uiAbsCtx, uiGoRiceParam,
                            c1Idx, c2Idx, iQBits, dTemp, 0)
                        sigRateDelta[uiBlkPos] = self.m_pcEstBitsSbac.significantBits[uiCtxSig][1] - \
                                                 self.m_pcEstBitsSbac.significantBits[uiCtxSig][0]
                    deltaU[uiBlkPos] = (lLevelDouble - (uiLevel << iQBits)) >> (iQBits-8)
                    if uiLevel > 0:
                        rateNow = self._xGetICRate(uiLevel, uiOneCtx, uiAbsCtx, uiGoRiceParam, c1Idx, c2Idx)
                        rateIncUp[uiBlkPos] = self._xGetICRate(uiLevel+1, uiOneCtx, uiAbsCtx, uiGoRiceParam, c1Idx, c2Idx) - rateNow
                        rateIncDown[uiBlkPos] = self._xGetICRate(uiLevel-1, uiOneCtx, uiAbsCtx, uiGoRiceParam, c1Idx, c2Idx) - rateNow
                    else:
                        rateIncUp[uiBlkPos] = self.m_pcEstBitsSbac.m_greaterOneBits[uiOneCtx][0]
                    piDstCoeff[uiBlkPos] = uiLevel
                    d64BaseCost += pdCostCoeff[iScanPos]

                    baseLevel = 2 + (1 if c2Idx < C2FLAG_NUMBER else 0) if c1Idx < C1FLAG_NUMBER else 1
                    if uiLevel >= baseLevel:
                        if uiLevel > 3 * (1 << uiGoRiceParam):
                            uiGoRiceParam = min(uiGoRiceParam+1, 4)
                    if uiLevel >= 1:
                        c1Idx += 1

                    #===== update bin model =====
                    if uiLevel > 1:
                        c1 = 0
                        c2 += c2 < 2
                        c2Idx += 1
                    elif c1 < 3 and c1 > 0 and uiLevel:
                        c1 += 1

                    if (iScanPos % SCAN_SET_SIZE) == 0 and (iScanPos > 0):
                        c2 = 0
                        uiGoRiceParam = 0

                        c1Idx = 0
                        c2Idx = 0
                        uiCtxSet = (0 if iScanPos == SCAN_SET_SIZE or eTType != TEXT_LUMA else 2)
                        if c1 == 0:
                            uiCtxSet += 1
                        c1 = 1
                else:
                    d64BaseCost += pdCostCoeff0[iScanPos]
                rdStats.d64SigCost += pdCostSig[iScanPos]
                if iScanPosinCG == 0:
                    rdStats.d64SigCost_0 = pdCostSig[iScanPos]
                if piDstCoeff[uiBlkPos]:
                    uiSigCoeffGroupFlag[uiCGBlkPos] = 1
                    rdStats.d64CodedLevelandDist += pdCostCoeff[iScanPos] - pdCostSig[iScanPos]
                    rdStats.d64UncodedDist += pdCostCoeff0[iScanPos]
                    if iScanPosinCG != 0:
                        rdStats.iNNZbeforePos0 += 1

            if iCGLastScanPos >= 0:
                if iCGScanPos:
                    if uiSigCoeffGroupFlag[uiCGBlkPos] == 0:
                        uiCtxSig = self.getSigCoeffGroupCtxInc(
                            uiSigCoeffGroupFlag, uiCGPosX, uiCGPosY, uiScanIdx, uiWidth, uiHeight)
                        d64BaseCost += self._xGetRateSigCoeffGroup(0, uiCtxSig) - rdStats.d64SigCost
                        pdCostCoeffGroupSig[iCGScanPos] = self._xGetRateSigCoeffGroup(0, uiCtxSig)
                    else:
                        if iCGScanPos < iCGLastScanPos: #skip the last coefficient group, which will be handled together with last position below.
                            if rdStats.iNNZbeforePos0 == 0:
                                d64BaseCost += rdStats.d64SigCost_0
                                rdStats.d64SigCost -= rdStats.d64SigCost_0
                            # rd-cost if SigCoeffGroupFlag = 0, initialization
                            d64CostZeroCG = d64BaseCost

                            # add SigCoeffGroupFlag cost to total cost
                            uiCtxSig = self.getSigCoeffGroupCtxInc(
                                uiSigCoeffGroupFlag, uiCGPosX, uiCGPosY, uiScanIdx, uiWidth, uiHeight)
                            if iCGScanPos < iCGLastScanPos:
                                d64BaseCost += self._xGetRateSigCoeffGroup(1, uiCtxSig)
                                d64CostZeroCG += self._xGetRateSigCoeffGroup(0, uiCtxSig)
                                pdCostCoeffGroupSig[iCGScanPos] = self._xGetRateSigCoeffGroup(1, uiCtxSig)

                            # try to convert the current coeff group from non-zero to all-zero
                            d64CostZeroCG += rdStats.d64UncodedDist # distortion for resetting non-zero levels to zero levels
                            d64CostZeroCG -= rdStats.d64CodedLevelandDist # distortion and level cost for keeping all non-zero levels
                            d64CostZeroCG -= rdStats.d64SigCost # sig cost for all coeffs, including zero levels and non-zerl levels

                            # if we can save cost, change this block to all-zero block
                            if d64CostZeroCG < d64BaseCost:
                                uiSigCoeffGroupFlag[uiCGBlkPos] = 0
                                d64BaseCost = d64CostZeroCG
                                if iCGScanPos < iCGLastScanPos:
                                    pdCostCoeffGroupSig[iCGScanPos] = self._xGetRateSigCoeffGroup(0, uiCtxSig)
                                # reset coeffs to 0 in this block  
                                for iScanPosinCG in xrange(uiCGSize-1, -1, -1):
                                    iScanPos = iCGScanPos * uiCGSize + iScanPosinCG
                                    uiBlkPos = scan[iScanPos]

                                    if piDstCoeff[uiBlkPos]:
                                        piDstCoeff[uiBlkPos] = 0
                                        pdCostCoeff[iScanPos] = pdCostCoeff0[iScanPos]
                                        pdCostSig[iScanPos] = 0
                else:
                    uiSigCoeffGroupFlag[uiCGBlkPos] = 1

        #===== estimate last position =====
        if iLastScanPos < 0:
            return uiAbsSum

        d64BaseCost = 0.0
        ui16CtxCbf = 0
        iBestLastIdxP1 = 0
        if not pcCU.isIntra(uiAbsPartIdx) and eTType == TEXT_LUMA and \
           pcCU.getTransformIdx(uiAbsPartIdx) == 0:
            ui16CtxCbf = 0
            d64BaseCost = d64BlockUncodedCost + \
                self._xGetICost(self.m_pcEstBitsSbac.blockRootCbpBits[ui16CtxCbf][0])
            d64BaseCost += self._xGetICost(self.m_pcEstBitsSbac.blockRootCbpBits[ui16CtxCbf][1])
        else:
            ui16CtxCbf = pcCU.getCtxQtCbf(uiAbsPartIdx, eTType, pcCU.getTransformIdx(uiAbsPartIdx))
            ui16CtxCbf = (TEXT_CHROMA if eTType else eTType) * NUM_QT_CBF_CTX + ui16CtxCbf
            d64BaseCost = d64BlockUncodedCost + \
                self._xGetICost(self.m_pcEstBitsSbac.blockRootCbpBits[ui16CtxCbf][0])
            d64BaseCost += self._xGetICost(self.m_pcEstBitsSbac.blockCbpBits[ui16CtxCbf][1])

        bFoundLast = False
        for iCGScanPos in xrange(iCGLastScanPos, -1, -1):
            uiCGBlkPos = scanCG[iCGScanPos]

            d64BaseCost -= pdCostCoeffGroupSig[iCGScanPos]
            if uiSigCoeffGroupFlag[uiCGBlkPos]:
                for iScanPosinCG in xrange(uiCGSize-1, -1, -1):
                    iScanPos = iCGScanPos * uiCGSize + iScanPosinCG
                    if iScanPos > iLastScanPos:
                        continue
                    uiBlkPos = scan[iScanPos]

                    if piDstCoeff[uiBlkPos]:
                        uiPosX = uiBlkPos >> uiLog2BlkSize
                        uiPosY = uiBlkPos - (uiPosX << uiLog2BlkSize)

                        d64CostLast = \
                            self._xGetRateLast(uiPosY, uiPosX, uiWidth) if uiScanIdx == SCAN_VER else \
                            self._xGetRateLast(uiPosX, uiPosY, uiWidth)
                        totalCost = d64BaseCost + d64CostLast - pdCostSig[iScanPos]

                        if totalCost < d64BaseCost:
                            iBestLastIdxP1 = iScanPos + 1
                            d64BaseCost = totalCost
                        if piDstCoeff[uiBlkPos] > 1:
                            bFoundLast = True
                            break
                        d64BaseCost -= pdCostCoeff[iScanPos]
                        d64BaseCost += pdCostCoeff0[iScanPos]
                    else:
                        d64BaseCost -= pdCostSig[iScanPos]
                if bFoundLast:
                    break

        for scanPos in xrange(iBestLastIdxP1):
            blkPos = scan[scanPos]
            level = piDstCoeff[blkPos]
            uiAbsSum += level
            piDstCoeff[blkPos] = (-level if plSrcCoeff[blkPos] < 0 else level)

        #===== clean uncoded coefficients =====
        for scanPos in xrange(iBestLastIdxP1, iLastScanPos+1):
            piDstCoeff[scan[scanPos]] = 0

        if pcCU.getSlice().getPPS().getSignHighFlag() and uiAbsSum >= 2:
            rdFactor = int(
                float(g_invQuantScales[self.m_cQP.rem()]) *
                float(g_invQuantScales[self.m_cQP.rem()]) *
                float(1 << (2*self.m_cQP.m_iPer)) / self.m_dLambda / 16 /
                float(1 << (2*cvar.g_uiBitIncrement)) + 0.5)
            lastCG = -1
            absSum = 0

            for subSet in xrange((uiWidth*uiHeight-1) >> LOG2_SCAN_SET_SIZE, -1, -1):
                subPos = subSet << LOG2_SCAN_SET_SIZE
                firstNZPosInCG = SCAN_SET_SIZE
                lastNZPosInCG = -1
                absSum = 0

                for n in xrange(SCAN_SET_SIZE-1, -1, -1):
                    if piDstCoeff[scan[n + subPos]]:
                        lastNZPosInCG = n
                        break

                for n in xrange(SCAN_SET_SIZE):
                    if piDstCoeff[scan[n + subPos]]:
                        firstNZPosInCG = n
                        break

                for n in xrange(firstNZPosInCG, lastNZPosInCG+1):
                    absSum += piDstCoeff[scan[n + subPos]]

                if lastNZPosInCG >= 0 and lastCG == -1:
                    lastCG = 1

                if lastNZPosInCG - firstNZPosInCG >= SBH_THRESHOLD:
                    signbit = (0 if piDstCoeff[scan[subPos + firstNZPosInCG]] > 0 else 1)
                    if signbit != (absSum & 0x1):
                        minCostInc = MAX_INT64
                        curCost = MAX_INT64
                        minPos = -1
                        finalChange = 0
                        curChange = 0

                        for n in xrange(lastNZPosInCG if lastCG == 1 else SCAN_SET_SIZE-1, -1, -1):
                            uiBlkPos = scan[n + subPos]
                            if piDstCoeff[uiBlkPos] != 0:
                                costUp = rdFactor * (-deltaU[uiBlkPos]) + rateIncUp[uiBlkPos]
                                costDown = rdFactor * (deltaU[uiBlkPos]) + rateIncDown[uiBlkPos] - \
                                    ((1<<15)+sigRateDelta[uiBlkPos] if abs(piDstCoeff[uiBlkPos]) == 1 else 0)

                                if lastCG == 1 and lastNZPosInCG == n and abs(piDstCoeff[uiBlkPos]) == 1:
                                    costDown -= (4 << 15)

                                if costUp < costDown:
                                    curCost = costUp
                                    curChange = 1
                                else:
                                    curChange = -1
                                    if n == firstNZPosInCG and abs(piDstCoeff[uiBlkPos]) == 1:
                                        curCost = MAX_INT64
                                    else:
                                        curCost = costDown
                            else:
                                curCost = rdFactor * (-abs(deltaU[uiBlkPos])) + \
                                    (1<<15) + rateIncUp[uiBlkPos] + sigRateDelta[uiBlkPos]
                                curChange = 1

                                if n < firstNZPosInCG:
                                    thissignbit = (0 if plSrcCoeff[uiBlkPos] >= 0 else 1)
                                    if thissignbit != signbit:
                                        curCost = MAX_INT64

                            if curCost < minCostInc:
                                minCostInc = curCost
                                finalChange = curChange
                                minPos = uiBlkPos

                        if piDstCoeff[minPos] == 32767 or piQCoef[minPos] == -32768:
                            finalChange = -1

                        if plSrcCoeff[minPos] >= 0:
                            piDstCoeff[minPos] += finalChange
                        else:
                            piDstCoeff[minPos] -= finalChange

                if lastCG == 1:
                    lastCG = 0

        return uiAbsSum

    def _xGetCodedLevel(self, rd64CodedCost, rd64CodedCost0, rd64CodedCostSig,
                        lLevelDouble, uiMaxAbsLevel,
                        ui16CtxNumSig, ui16CtxNumOne, ui16CtxNumAbs, ui16AbsGoRice,
                        c1Idx, c2Idx, iQBits, dTemp, bLast):
        dCurrCostSig = 0.0
        uiBestAbsLevel = 0

        if not bLast and uiMaxAbsLevel < 3:
            rd64CodedCostSig = self._xGetRateSigCoef(0, ui16CtxNumSig)
            rd64CodedCost = rd64CodedCost0 + rd64CodedCostSig
            if uiMaxAbsLevel == 0:
                return uiBestAbsLevel
        else:
            rd64CodedCost = MAX_DOUBLE

        if not bLast:
            dCurrCostSig = self._xGetRateSigCoef(1, ui16CtxNumSig)

        uiMinAbsLevel = (uiMaxAbsLevel-1 if uiMaxAbsLevel > 1 else 1)
        for uiAbsLevel in xrange(uiMaxAbsLevel, uiMinAbsLevel-1, -1):
            dErr = float(lLevelDouble - (uiAbsLevel << iQBits))
            dCurrCost = dErr * dErr * dTemp + \
                self._xGetICRateCost(uiAbsLevel, ui16CtxNumOne, ui16CtxNumAbs, ui16AbsGoRice, c1Idx, c2Idx)
            dCurrCost += dCurrCostSig

            if dCurrCost < rd64CodedCost:
                uiBestAbsLevel = uiAbsLevel
                rd64CodedCost = dCurrCost
                rd64CodedCostSig = dCurrCostSig

        return uiBestAbsLevel

    def _xGetICRateCost(self, uiAbsLevel, ui16CtxNumOne, ui16CtxNumAbs, ui16AbsGoRice,
                        c1Idx, c2Idx):
        iRate = self._xGetIEPRate()
        baseLevel = (2 + (1 if c2Idx < C2FLAG_NUMBER else 0) if c1Idx < C1FLAG_NUMBER else 1)

        if uiAbsLevel >= baseLevel:
            symbol = uiAbsLevel - baseLevel
            length = 0
            if symbol < (COEF_REMAIN_BIN_REDUCTION << ui16AbsGoRice):
                length = symbol >> ui16AbsGoRice
                iRate += (length + 1 + ui16AbsGoRice) << 15
            else:
                length = ui16AbsGoRice
                symbol = symbol - (COEF_REMAIN_BIN_REDUCTION << ui16AbsGoRice)
                while symbol >= (1<<length):
                    symbol -= (1<<length)
                    length += 1
                iRate += (COEF_REMAIN_BIN_REDUCTION + length + 1 - ui16AbsGoRice + length) << 15
            if c1Idx < C1FLAG_NUMBER:
                iRate += self.m_pcEstBitsSbac.m_greaterOneBits[ui16CtxNumOne][1]

                if c2Idx < C2FLAG_NUMBER:
                    iRate += self.m_pcEstBitsSbac.m_levelAbsBits[ui16CtxNumOne][1]
        elif uiAbsLevel == 1:
            iRate += self.m_pcEstBitsSbac.m_greaterOneBits[ui16CtxNumOne][0]
        elif uiAbsLevel == 2:
            iRate += self.m_pcEstBitsSbac.m_greaterOneBits[ui16CtxNumOne][1]
            iRate += self.m_pcEstBitsSbac.m_levelAbsBits[ui16CtxNumAbs][0]
        else:
            assert(False)
        return self._xGetICost(iRate)

    def _xGetICRate(self, uiAbsLevel, ui16CtxNumOne, ui16CtxNumAbs, ui16AbsGoRice,
                    c1Idx, c2Idx):
        iRate = 0
        baseLevel = (2 + (1 if c2Idx < C2FLAG_NUMBER else 0) if c1Idx < C1FLAG_NUMBER else 1)

        if uiAbsLevel >= baseLevel:
            uiSymbol = uiAbsLevel - baseLevel
            uiMaxVlc = g_auiGoRiceRange[ui16AbsGoRice]
            bExpGolomb = uiSymbol > uiMaxVlc

            if bExpGolomb:
                uiAbsLevel = uiSymbol - uiMaxVlc
                iEGS = 1
                uiMax = 2
                while uiAbsLevel >= uiMax:
                    uiMax <<= 1
                    iEGS += 2
                iRate += iEGS << 15
                uiSymbol = min(uiSymbol, uiMaxVlc+1)

            ui16PrefLen = (uiSymbol >> ui16AbsGoRice) + 1
            ui16NumBins = min(ui16PrefLen, g_auiGoRicePrefLen[ui16AbsGoRice])

            iRate += ui16NumBins << 15

            if c1Idx < C1FLAG_NUMBER:
                iRate += self.m_pcEstBitsSbac.m_greaterOneBits[ui16CtxNumOne][1]

                if c2Idx < C2FLAG_NUMBER:
                    iRate += self.m_pcEstBitsSbac.m_levelAbsBits[ui16CtxNumOne][1]
        elif uiAbsLevel == 0:
            return 0
        elif uiAbsLevel == 1:
            iRate += self.m_pcEstBitsSbac.m_greaterOneBits[ui16CtxNumOne][0]
        elif uiAbsLevel == 2:
            iRate += self.m_pcEstBitsSbac.m_greaterOneBits[ui16CtxNumOne][1]
            iRate += self.m_pcEstBitsSbac.m_levelAbsBits[ui16CtxNumAbs][0]
        else:
            assert(False)
        return iRate

    def _xGetRateLast(self, uiPosX, uiPosY, uiBlkWdth):
        uiCtxX = g_uiGroupIdx[uiPosX]
        uiCtxY = g_uiGroupIdx[uiPosY]
        uiCost = self.m_pcEstBitsSbac.lastXBits[uiCtxX] + self.m_pcEstBitsSbac.lastYBits[uiCtxY]
        if uiCtxX > 3:
            uiCost += self._xGetIEPRate() * ((uiCtxX-2) >> 1)
        if uiCtxY > 3:
            uiCost += self._xGetIEPRate() * ((uiCtxY-2) >> 1)
        return self._xGetICost(uiCost)

    def _xGetRateSigCoeffGroup(self, uiSignificanceCoeffGroup, ui16CtxNumSig):
        return self._xGetICost(
            self.m_pcEstBitsSbac.significantCoeffGroupBits[ui16CtxNumSig][uiSignificanceCoeffGroup]
        )
    def _xGetRateSigCoef(self, uiSignificance, ui16CtxNumSig):
        return self._xGetICost(
            self.m_pcEstBitsSbac.significantBits[ui16CtxNumSig][uiSignificance]
        )
    def _xGetICost(self, dRate):
        return self.m_dLambda * dRate
    def _xGetIEPRate(self):
        return 32768

    def _xDeQuant(self, pSrc, pDes, iWidth, iHeight, scalingListType):
        piQCoef = pSrc
        piCoef = pDes
        dir = SCALING_LIST_SQT

        if iWidth > self.m_uiMaxTrSize:
            iWidth = self.m_uiMaxTrSize
            iHeight = self.m_uiMaxTrSize

        uiLog2TrSize = g_aucConvertToBit[iWidth] + 2

        uiBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        iTransformShift = MAX_TR_DYNAMIC_RANGE - uiBitDepth - uiLog2TrSize

        iShift = QUANT_IQUANT_SHIFT - QUANT_SHIFT - iTransformShift

        bitRange = min(15, 12+uiLog2TrSize+uiBitDepth-self.m_cQP.m_iPer)
        levelLimit = 1 << bitRange

        if self.getUseScalingList():
            iShift += 4
            if iShift > self.m_cQP.m_iPer:
                iAdd = 1 << (iShift - self.m_cQP.m_iPer - 1)
            else:
                iAdd = 0
            piDequantCoef = self.getDequantCoeff(scalingListType, self.m_cQP.m_iRem, uiLog2TrSize-2, dir)

            if iShift > self.m_cQP.m_iPer:
                for n in xrange(iWidth * iHeight):
                    clipQCoef = Clip3(-32768, 32767, piQCoef[n])
                    iCoeffQ = (clipQCoef * piDequantCoef[n] + iAdd) >> (iShift - self.m_cQP.m_iPer)
                    piCoef[n] = Clip3(-32768, 32767, iCoeffQ)
            else:
                for n in xrange(iWidth * iHeight):
                    clipQCoef = Clip3(-levelLimit, levelLimit-1, piQCoef[n])
                    iCoeffQ = (clipQCoef * piDequantCoef[n]) << (self.m_cQP.m_iPer - iShift)
                    piCoef[n] = Clip3(-32768, 32767, iCoeffQ)
        else:
            iAdd = 1 << (iShift-1)
            scale = g_invQuantScales[self.m_cQP.m_iRem] << self.m_cQP.m_iPer

            for n in xrange(iWidth * iHeight):
                clipQCoef = Clip3(-32768, 32767, piQCoef[n])
                iCoeffQ = (clipQCoef * scale + iAdd) >> iShift
                piCoef[n] = Clip3(-32768, 32767, iCoeffQ)

    def _xIT(self, uiMode, plCoef, pResidual, uiStride, iWidth, iHeight):
        block = (64*64) * [0]
        coeff = (64*64) * [0]
        for j in xrange(iHeight * iWidth):
            coeff[j] = plCoef[j]
        xITrMxN(coeff, block, iWidth, iHeight, uiMode)
        for j in xrange(iHeight):
            for i in xrange(iWidth):
                pResidual[j * uiStride + i] = block[j * iWidth + i]

    def _xITransformSkip(self, plCoef, pResidual, uiStride, width, height):
        assert(width == height)
        uiLog2TrSize = g_aucConvertToBit[width] + 2
        uiBitDepth = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        shift = MAX_TR_DYNAMIC_RANGE - uiBitDepth - uiLog2TrSize
        if shift > 0:
            transformSkipShift = shift
            offset = 1 << (transformSkipShift-1)
            for j in xrange(height):
                for k in xrange(width):
                    pResidual[j * uiStride + k] = (plCoef[j * width + k] + offset) >> transformSkipShift
        else:
            #The case when uiBitDepth >= 13
            transformSkipShift = -shift
            for j in xrange(height):
                for k in xrange(width):
                    pResidual[j * uiStride + k] = plCoef[j * width + k] << transformSkipShift
