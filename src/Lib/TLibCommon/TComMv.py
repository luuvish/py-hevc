# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComMv.py
    HM 8.0 Python Implementation
"""

import sys

from .CommonDef import Clip3


class TComMv(object):

    def __init__(self, iHor=0, iVer=0):
        self.m_iHor = iHor
        self.m_iVer = iVer

    def set(self, iHor, iVer):
        self.m_iHor = iHor
        self.m_iVer = iVer
    def setHor(self, i):
        self.m_iHor = i
    def setVer(self, i):
        self.m_iVer = i
    def setZero(self):
        self.m_iHor = self.m_iVer = 0

    def getHor(self):
        return self.m_iHor
    def getVer(self):
        return self.m_iVer
    def getAbsHor(self):
        return abs(self.m_iHor)
    def getAbsVer(self):
        return abs(self.m_iVer)

    def __iadd__(self, rcMv):
        self.m_iHor += rcMv.m_iHor
        self.m_iVer += rcMv.m_iVer
        return self

    def __isub__(self, rcMv):
        self.m_iHor -= rcMv.m_iHor
        self.m_iVer -= rcMv.m_iVer
        return self

    def __irshift__(self, i):
        self.m_iHor >>= i
        self.m_iVer >>= i
        return self

    def __ilshift__(self, i):
        self.m_iHor <<= i
        self.m_iVer <<= i
        return self

    def __sub__(self, rcMv):
        return TComMv(self.m_iHor - rcMv.m_iHor, self.m_iVer - rcMv.m_iVer)

    def __add__(self, rcMv):
        return TComMv(self.m_iHor + rcMv.m_iHor, self.m_iVer + rcMv.m_iVer)

    def __eq__(self, rcMv):
        return self.m_iHor == rcMv.m_iHor and self.m_iVer == rcMv.m_iVer

    def __ne__(self, rcMv):
        return self.m_iHor != rcMv.m_iHor or self.m_iVer != rcMv.m_iVer

    def scaleMv(iScale):
        mvx = Clip3(-32768, 32767, (iScale * self.getHor() + 127 + (1 if iScale * self.getHor() < 0 else 0)) >> 8)
        mvy = Clip3(-32768, 32767, (iScale * self.getVer() + 127 + (1 if iScale * self.getVer() < 0 else 0)) >> 8)
        return TComMv(mvx, mvy)
