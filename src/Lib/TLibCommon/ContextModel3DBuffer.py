# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/ContextModel3DBuffer.py
    HM 10.0 Python Implementation
"""

from ... import pointer

from .ContextModel import ContextModel


class ContextModel3DBuffer(object):

    def __init__(self, uiSizeZ, uiSizeY, uiSizeX, basePtr, count):
        self.m_sizeX = uiSizeX
        self.m_sizeXY = uiSizeX * uiSizeY
        self.m_sizeXYZ = uiSizeX * uiSizeY * uiSizeZ
        self.m_contextModel = pointer(basePtr)

        count[0] += self.m_sizeXYZ

    def get(self, uiZ, uiY=None, uiX=None):
        if uiY == None and uiX == None:
            return pointer(self.m_contextModel, base=(uiZ * self.m_sizeXY))
        elif uiX == None:
            return pointer(self.m_contextModel, base=(uiZ * self.m_sizeXY + uiY * self.m_sizeX))
        else:
            return self.m_contextModel[uiZ * self.m_sizeXY + uiY * self.m_sizeX + uiX]

    def initBuffer(self, sliceType, qp, ctxModel):
        ctxModel = ctxModel[sliceType]

        for n in xrange(self.m_sizeXYZ):
            self.m_contextModel[n].init(qp, ctxModel[n])
            self.m_contextModel[n].setBinsCoded(0)

    def calcCost(self, sliceType, qp, ctxModel):
        cost = 0
        ctxModel = ctxModel[sliceType]

        for n in xrange(self.m_sizeXYZ):
            tmpContextModel = ContextModel()
            tmpContextModel.init(qp, ctxModel[n])

            # Map the 64 CABAC states to their corresponding probability values
            aStateToProbLPS = (
                0.50000000, 0.47460857, 0.45050660, 0.42762859,
                0.40591239, 0.38529900, 0.36573242, 0.34715948,
                0.32952974, 0.31279528, 0.29691064, 0.28183267,
                0.26752040, 0.25393496, 0.24103941, 0.22879875,
                0.21717969, 0.20615069, 0.19568177, 0.18574449,
                0.17631186, 0.16735824, 0.15885931, 0.15079198,
                0.14313433, 0.13586556, 0.12896592, 0.12241667,
                0.11620000, 0.11029903, 0.10469773, 0.09938088,
                0.09433404, 0.08954349, 0.08499621, 0.08067986,
                0.07658271, 0.07269362, 0.06900203, 0.06549791,
                0.06217174, 0.05901448, 0.05601756, 0.05317283,
                0.05047256, 0.04790942, 0.04547644, 0.04316702,
                0.04097487, 0.03889405, 0.03691890, 0.03504406,
                0.03326442, 0.03157516, 0.02997168, 0.02844963,
                0.02700488, 0.02563349, 0.02433175, 0.02309612,
                0.02192323, 0.02080991, 0.01975312, 0.01875000
            )

            probLPS = aStateToProbLPS[self.m_contextModel[n].getState()]
            prob0 = prob1 = 0.0
            if self.m_contextModel[n].getMps() == 1:
                prob0 = probLPS
                prob1 = 1.0 - prob0
            else:
                prob1 = probLPS
                prob0 = 1.0 - prob1

            if self.m_contextModel[n].getBinsCoded() > 0:
                cost += prob0 * tmpContextModel.getEntropyBits(0) + \
                        prob1 * tmpContextModel.getEntropyBits(1)

        return cost

    def copyFrom(self, src):
        assert(self.m_sizeXYZ == src.m_sizeXYZ)
        for i in xrange(self.m_sizeXYZ):
            self.m_contextModel[i].m_ucState = src.m_contextModel[i].m_ucState
            self.m_contextModel[i].m_binsCoded = src.m_contextModel[i].m_binsCoded
