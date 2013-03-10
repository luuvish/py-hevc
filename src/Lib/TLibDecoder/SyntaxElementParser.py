# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/SyntaxElementParser.py
    HM 10.0 Python Implementation
"""

import sys

from ... import Trace

def xReadCodeTr(xReadCode):
    def wrap(self, length, rValue, pSymbolName=''):
        rValue = xReadCode(self, length, rValue)
        Trace.g_hTrace.write("%8d  " % Trace.g_nSymbolCounter)
        Trace.g_nSymbolCounter += 1
        if length < 10:
            Trace.g_hTrace.write("%-50s u(%d)  : %d\n" % (pSymbolName, length, rValue))
        else:
            Trace.g_hTrace.write("%-50s u(%d) : %d\n" % (pSymbolName, length, rValue))
        Trace.g_hTrace.flush()
        return rValue
    return wrap

def xReadUvlcTr(xReadUvlc):
    def wrap(self, rValue, pSymbolName=''):
        rValue = xReadUvlc(self, rValue)
        Trace.g_hTrace.write("%8d  " % Trace.g_nSymbolCounter)
        Trace.g_nSymbolCounter += 1
        Trace.g_hTrace.write("%-50s ue(v) : %d\n" % (pSymbolName, rValue))
        Trace.g_hTrace.flush()
        return rValue
    return wrap

def xReadSvlcTr(xReadSvlc):
    def wrap(self, rValue, pSymbolName=''):
        rValue = xReadSvlc(self, rValue)
        Trace.g_hTrace.write("%8d  " % Trace.g_nSymbolCounter)
        Trace.g_nSymbolCounter += 1
        Trace.g_hTrace.write("%-50s se(v) : %d\n" % (pSymbolName, rValue))
        Trace.g_hTrace.flush()
        return rValue
    return wrap

def xReadFlagTr(xReadFlag):
    def wrap(self, rValue, pSymbolName=''):
        rValue = xReadFlag(self, rValue)
        Trace.g_hTrace.write("%8d  " % Trace.g_nSymbolCounter)
        Trace.g_nSymbolCounter += 1
        Trace.g_hTrace.write("%-50s u(1)  : %d\n" % (pSymbolName, rValue))
        Trace.g_hTrace.flush()
        return rValue
    return wrap


class SyntaxElementParser(object):

    def __init__(self):
        self.m_pcBitstream = None


    @Trace.trace(Trace.on, wrapper=xReadCodeTr)
    def xReadCode(self, uiLength, ruiCode, pSymbolName=''):
        assert(uiLength > 0)
        ruiCode = self.m_pcBitstream.read(uiLength, ruiCode)
        return ruiCode

    @Trace.trace(Trace.on, wrapper=xReadUvlcTr)
    def xReadUvlc(self, ruiVal, pSymbolName=''):
        uiVal = 0
        uiCode = 0
        uiCode = self.m_pcBitstream.read(1, uiCode)

        if uiCode == 0:
            uiLength = 0

            while not (uiCode & 1):
                uiCode = self.m_pcBitstream.read(1, uiCode)
                uiLength += 1

            uiVal = self.m_pcBitstream.read(uiLength, uiVal)
            uiVal += (1 << uiLength) - 1

        ruiVal = uiVal
        return ruiVal

    @Trace.trace(Trace.on, wrapper=xReadSvlcTr)
    def xReadSvlc(self, riVal, pSymbolName=''):
        uiBits = 0
        uiBits = self.m_pcBitstream.read(1, uiBits)

        if uiBits == 0:
            uiLength = 0

            while not (uiBits & 1):
                uiBits = self.m_pcBitstream.read(1, uiBits)
                uiLength += 1

            uiBits = self.m_pcBitstream.read(uiLength, uiBits)
            uiBits += (1 << uiLength)
            riVal = -(uiBits>>1) if (uiBits & 1) else (uiBits>>1)
        else:
            riVal = 0

        return riVal

    @Trace.trace(Trace.on, wrapper=xReadFlagTr)
    def xReadFlag(self, ruiCode, pSymbolName=''):
        ruiCode = self.m_pcBitstream.read(1, ruiCode)
        return ruiCode

    def setBitstream(self, p):
        self.m_pcBitstream = p
    def getBitstream(self):
        return self.m_pcBitstream
