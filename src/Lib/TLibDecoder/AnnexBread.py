#!/usr/bin/env python

class InputByteStream:

    def __init__(self, istream):
        self.m_NumFutureBytes = 0
        self.m_FutureBytes = 0
        self.m_Input = istream
        istream.exception(eofbit)

    def reset(self):
        self.m_NumFutureBytes = 0
        self.m_FutureBytes = 0

    def eofBeforeNBytes(self, n):
        assert(n <= 4)
        if self.m_NumFutureBytes >= n:
            return False

        n -= self.m_NumFutureBytes
        try:
            for i in range(n):
                self.m_FutureBytes = (self.m_FutureBytes << 8) | self.m_Input.get()
                self.m_NumFutureBytes += 1
        except:
            return True
        return False

    def peekBytes(self, n):
        self.eofBeforeNBytes(n)
        return self.m_FutureBytes >> 8 * (self.m_NumFutureBytes - n)

    def readByte(self):
        if not self.m_NumFutureBytes:
            byte = self.m_Input.get()
            return byte
        self.m_NumFutureBytes -= 1
        wanted_byte = self.m_FutureBytes >> 8 * self.m_NumFutureBytes
        self.m_FutureBytes &= ~(0xff << 8 * self.m_NumFutureBytes)
        return wanted_byte

    def readBytes(self, n):
        val = 0
        for i in range(n):
            val = (val << 8) | self.readByte()
        return val

class AnnexBStats:
    def __add__(self, rhs):
        self.m_numLeadingZero8BitsBytes += rhs.m_numLeadingZero8BitsBytes
        self.m_numZeroByteBytes += rhs.m_numZeroByteBytes
        self.m_numStartCodePrefixBytes += rhs.m_numStartCodePrefixBytes
        self.m_numBytesInNALUnit += rhs.m_numBytesInNALUnit
        self.m_numTrailingZero8BitsBytes += rhs.m_numTrailingZero8BitsBytes
        return self

def byteStreamNALUnit(bs, nalUnit, stats):

    def _byteStreamNALUnit(bs, nalUnit, stats):
        while (bs.eofBeforeNBytes(24/8) or bs.eofBeforeNBytes(24/8) != 0x000001) and \
              (bs.eofBeforeNBytes(32/8) or bs.eofBeforeNBytes(32/8) != 0x00000001):
            leading_zero_8bits = bs.readByte()
            assert(leading_zero_8bits == 0)
            stats.m_numLeadingZero8BitsBytes += 1

        if bs.peekBytes(24/8) != 0x000001:
            zero_byte = bs.readByte()
            assert(zero_byte == 0)
            stats.m_numZeroByteBytes += 1

        start_code_prefix_one_3bytes = bs.readBytes(24/8)
        assert(start_code_prefix_one_3bytes == 0x000001)
        stats.m_numStartCodePrefixBytes += 3

        while bs.eofBeforeNBytes(24/8) or bs.peekBytes(24/8) > 2:
            nalUnit.push_back(bs.readByte())

        while (bs.eofBeforeNBytes(24/8) or bs.eofBeforeNBytes(24/8) != 0x000001) and \
              (bs.eofBeforeNBytes(32/8) or bs.eofBeforeNBytes(32/8) != 0x00000001):
            trailing_zero_8bits = bs.readByte()
            assert(trailing_zero_8bits == 0)
            stats.m_numTrailingZero8BitsBytes += 1

    eof = False
    try:
        _byteStreamNALUnit(bs, nalUnit, stats)
    except:
        eof = True
    stats.m_numBytesInNALUnit = nalUnit.size()
    return eof
