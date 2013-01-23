# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/ContextModel.py
    HM 9.1 Python Implementation
"""

from .CommonDef import Clip3


class ContextModel(object):

    m_aucNextStateMPS = (
          2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,  16,  17,
         18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,  29,  30,  31,  32,  33,
         34,  35,  36,  37,  38,  39,  40,  41,  42,  43,  44,  45,  46,  47,  48,  49,
         50,  51,  52,  53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,  65,
         66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,  78,  79,  80,  81,
         82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  92,  93,  94,  95,  96,  97,
         98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
        114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 124, 125, 126, 127
    )

    m_aucNextStateLPS = (
          1,   0,   0,   1,   2,   3,   4,   5,   4,   5,   8,   9,   8,   9,  10,  11,
         12,  13,  14,  15,  16,  17,  18,  19,  18,  19,  22,  23,  22,  23,  24,  25,
         26,  27,  26,  27,  30,  31,  30,  31,  32,  33,  32,  33,  36,  37,  36,  37,
         38,  39,  38,  39,  42,  43,  42,  43,  44,  45,  44,  45,  46,  47,  48,  49,
         48,  49,  50,  51,  52,  53,  52,  53,  54,  55,  54,  55,  56,  57,  58,  59,
         58,  59,  60,  61,  60,  61,  60,  61,  62,  63,  64,  65,  64,  65,  66,  67,
         66,  67,  66,  67,  68,  69,  68,  69,  70,  71,  70,  71,  70,  71,  72,  73,
         72,  73,  72,  73,  74,  75,  74,  75,  74,  75,  76,  77,  76,  77, 126, 127
    )

    m_entropyBits = (
        # Corrected table, most notably for last state
        0x07b23, 0x085f9, 0x074a0, 0x08cbc, 0x06ee4, 0x09354, 0x067f4, 0x09c1b,
        0x060b0, 0x0a62a, 0x05a9c, 0x0af5b, 0x0548d, 0x0b955, 0x04f56, 0x0c2a9,
        0x04a87, 0x0cbf7, 0x045d6, 0x0d5c3, 0x04144, 0x0e01b, 0x03d88, 0x0e937,
        0x039e0, 0x0f2cd, 0x03663, 0x0fc9e, 0x03347, 0x10600, 0x03050, 0x10f95,
        0x02d4d, 0x11a02, 0x02ad3, 0x12333, 0x0286e, 0x12cad, 0x02604, 0x136df,
        0x02425, 0x13f48, 0x021f4, 0x149c4, 0x0203e, 0x1527b, 0x01e4d, 0x15d00,
        0x01c99, 0x166de, 0x01b18, 0x17017, 0x019a5, 0x17988, 0x01841, 0x18327,
        0x016df, 0x18d50, 0x015d9, 0x19547, 0x0147c, 0x1a083, 0x0138e, 0x1a8a3,
        0x01251, 0x1b418, 0x01166, 0x1bd27, 0x01068, 0x1c77b, 0x00f7f, 0x1d18e,
        0x00eda, 0x1d91a, 0x00e19, 0x1e254, 0x00d4f, 0x1ec9a, 0x00c90, 0x1f6e0,
        0x00c01, 0x1fef8, 0x00b5f, 0x208b1, 0x00ab6, 0x21362, 0x00a15, 0x21e46,
        0x00988, 0x2285d, 0x00934, 0x22ea8, 0x008a8, 0x239b2, 0x0081d, 0x24577,
        0x007c9, 0x24ce6, 0x00763, 0x25663, 0x00710, 0x25e8f, 0x006a0, 0x26a26,
        0x00672, 0x26f23, 0x005e8, 0x27ef8, 0x005ba, 0x284b5, 0x0055e, 0x29057,
        0x0050c, 0x29bab, 0x004c1, 0x2a674, 0x004a7, 0x2aa5e, 0x0046f, 0x2b32f,
        0x0041f, 0x2c0ad, 0x003e7, 0x2ca8d, 0x003ba, 0x2d323, 0x0010c, 0x3bfbb
    )

    m_nextState = [[0, 0] for i in xrange(128)]

    def __init__(self):
        self.m_ucState = 0
        self.m_binsCoded = 0

    def getState(self):
        return self.m_ucState >> 1
    def getMps(self):
        return self.m_ucState & 1
    def setStateAndMps(self, ucState, ucMPS):
        self.m_ucState = (ucState << 1) + ucMPS

    def init(self, qp, initValue):
        qp = Clip3(0, 51, qp)

        slope = (initValue>>4) * 5 - 45
        offset = ((initValue&15) << 3) - 16
        initState = min(max(1, ((slope * qp) >> 4) + offset), 126)
        mpState = initState >= 64
        self.m_ucState = ((initState-64 if mpState else 63-initState) << 1) + (1 if mpState else 0)

    def updateLPS(self):
        self.m_ucState = ContextModel.m_aucNextStateLPS[self.m_ucState]
    def updateMPS(self):
        self.m_ucState = ContextModel.m_aucNextStateMPS[self.m_ucState]

    def getEntropyBits(self, val):
        return ContextModel.m_entropyBits[self.m_ucState ^ val]

    def update(self, binVal):
        self.m_ucState = ContextModel.m_nextState[self.m_ucState][binVal]

    @staticmethod
    def buildNextStateTable():
        for i in xrange(128):
            for j in xrange(2):
                ContextModel.m_nextState[i][j] = \
                    ContextModel.m_aucNextStateMPS[i] if i & 1 == j else \
                    ContextModel.m_aucNextStateLPS[i]

    @staticmethod
    def getEntropyBitsTrm(val):
        return ContextModel.m_entropyBits[126 ^ val]

    def setBinsCoded(self, val):
        self.m_binsCoded = val
    def getBinsCoded(self):
        return self.m_binsCoded
