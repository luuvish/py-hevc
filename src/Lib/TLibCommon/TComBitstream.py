#!/usr/bin/env python

from ...Lib.TLibCommon.CommonDef import *
from ...Lib.TLibCommon.TComBitstream import TComBitstream

class TComBitIf:

    def __init__(self):
        pass

    def writeAlignOne(self):
        pass
    def writeAlignZero(self):
        pass
    def write(self, uiBits, uiNumberofBits):
        pass
    def resetBits(self):
        pass
    def getNumberOfWrittenBits(self):
        pass

class TComOutputBitstream(TComBitIf):

    def __init__(self):
        self.m_fifo = []
        self.clear()

    def write(self, uiBits, uiNumberofBits):
        assert(uiNumberofBits <= 32)

        num_total_bits = uiNumberofBits + self.m_num_held_bits
        next_num_held_bits = num_total_bits % 8

        next_held_bits = uiBits << (8 - next_num_held_bits)

        if not (num_total_bits >> 3):
            self.m_held_bits |= next_held_bits
            self.m_num_held_bits = next_num_held_bits
            return

        topword = (uiNumberofBits - next_num_held_bits) & ~((1 << 3) - 1)
        write_bits = (self.m_held_bits << topword) | (uiBits >> next_num_held_bits)

        if (num_total_bits >> 3) == 4:
            self.m_fifo.push_back(write_bits >> 24)
        elif (num_total_bits >> 3) == 3:
            self.m_fifo.push_back(write_bits >> 16)
        elif (num_total_bits >> 3) == 2:
            self.m_fifo.push_back(write_bits >> 8)
        elif (num_total_bits >> 3) == 1:
            self.m_fifo.push_back(write_bits)

        self.m_held_bits = next_held_bits
        self.m_num_held_bits = next_num_held_bits

    def writeAlignOne(self):
        num_bits = self.getNumBitsUntilByteAligned()
        self.write((1 << num_bits) - 1, num_bits)

    def writeAlignZero(self):
        if self.m_num_held_bits == 0:
            return
        self.m_fifo.push_back(self.m_held_bits)
        self.m_held_bits = 0
        self.m_num_held_bits = 0

    def resetBits(self):
        assert(0)

    def getByteStream(self):
        return self.m_fifo.front()

    def getByteStreamLength(self):
        return self.m_fifo.size()

    def clear(self):
        self.m_fifo.clear()
        self.m_held_bits = 0
        self.m_num_held_bits = 0

    def getNumBitsUntilByteAligned(self):
        pass
    def getNumberOfWrittenBits(self):
        pass
    def insertAt(self, src, pos):
        pass
    def getFIFO(self):
        pass
    def getHeldBits(self):
        pass
    def __eq__(self, src):
        pass
    def addSubstream(self, pcSubstream):
        uiNumBits = pcSubstream.getNumberOfWrittenBits()

        rbsp = pcSubstream.getFIFO()
        for it in rbsp:
            self.write(it, 8)
        if uiNumBits & 0x7:
            self.write(pcSubstream.getHeldBits() >> (8 - (uiNumBits & 0x7)), uiNumBits & 0x7)

class TComInputBitstream:

    def __init__(self, buf):
        self.m_fifo = buf
        self.m_fifo_idx = 0
        self.m_held_bits = 0
        self.m_num_held_bits = 0
        self.m_numBitsRead = 0

    def pseudoRead(self, uiNumberOfBits, ruiBits):
        pass
    def read(self, uiNumberOfBits, ruiBits):
        pass
    def readByte(self, ruiBits):
        assert(self.m_fifo_idx < self.m_fifo.size())
        ruiBits = self.m_fifo[self.m_fifo_idx]
        self.m_fifo_idx += 1

    def getNumberOfWrittenBits(self):
        pass
    def insertAt(self, src, pos):
        pass
    def getFIFO(self):
        pass
    def getHeldBits(self):
        pass
    def __eq__(self, src):
        pass
