# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibDecoder/SyntaxElementParser.py
    HM 9.1 Python Implementation
"""

import sys

from ... import trace


class SyntaxElementParser(object):

    def __init__(self):
        self.m_pcBitstream = None

    def xReadCodeTr(self, XReadCode):
        def wrap(self, length, rValue, pSymbolName=''):
            rValue = xReadCode(self, length, rValue)
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_nSymbolCounter += 1
            if length < 10:
                g_hTrace.write("%-50s u(%d)  : %d\n" % (pSymbolName, length, rValue))
            else:
                g_hTrace.write("%-50s u(%d) : %d\n" % (pSymbolName, length, rValue))
            g_hTrace.flush()
            return rValue
        return wrap

    def xReadUvlcTr(self, xReadUvlc):
        def wrap(self, rValue, pSymbolName=''):
            rValue = xReadUvlc(self, rValue)
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_nSymbolCounter += 1
            g_hTrace.write("%-50s ue(v) : %d\n" % (pSymbolName, rValue))
            g_hTrace.flush()
            return rValue
        return wrap

    def xReadSvlcTr(self, xReadSvlc):
        def wrap(self, rValue, pSymbolName=''):
            rValue = xReadSvlc(self, rValue)
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_nSymbolCounter += 1
            g_hTrace.write("%-50s se(v) : %d\n" % (pSymbolName, rValue))
            g_hTrace.flush()
            return rValue
        return wrap

    def xReadFlagTr(self, xReadFlag):
        def wrap(self, rValue, pSymbolName=''):
            rValue = xReadFlag(self, rValue)
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_nSymbolCounter += 1
            g_hTrace.write("%-50s u(1)  : %d\n" % (pSymbolName, rValue))
            g_hTrace.flush()
            return rValue
        return wrap

    @trace.trace(trace.use_trace, wrapper=trace.traceReadCode)
    def xReadCode(self, uiLength, ruiCode, pSymbolName=''):
        assert(uiLength > 0)
        ruiCode = self.m_pcBitstream.read(uiLength, ruiCode)
        return ruiCode

    @trace.trace(trace.use_trace, wrapper=trace.traceReadUvlc)
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

    @trace.trace(trace.use_trace, wrapper=trace.traceReadSvlc)
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

    @trace.trace(trace.use_trace, wrapper=trace.traceReadFlag)
    def xReadFlag(self, ruiCode, pSymbolName=''):
        ruiCode = self.m_pcBitstream.read(1, ruiCode)
        return ruiCode

    def setBitstream(self, p):
        self.m_pcBitstream = p
    def getBitstream(self):
        return self.m_pcBitstream
