#!/usr/bin/env python

import os
import sys


def invScalePlane(base, img, stride, width, height, shiftbits, minval, maxval):
    Clip3 = lambda min, max, i: min if i < min else max if i > max else i

    offset = 1 << (shiftbits-1)

    for y in range(0, height):
        for x in range(0, width):
            val = (base[img + x] + offset) >> shiftbits
            base[img + x] = Clip3(minval, maxval, val)
        img += stride

def scalePlane(base, img, stride, width, height, shiftbits):
    for y in range(0, height):
        for x in range(0, width):
            base[img + x] <<= shiftbits
        img += stride

def scalePlane(base, img, stride, width, height, shiftbits, minval, maxval):
    if shiftbits == 0:
        return

    if shiftbits > 0:
        scalePlane(base, img, stride, width, height, shiftbits)
    else:
        invScalePlane(base, img, stride, width, height, -shiftbits, minval, maxval)

def readPlane(base, dst, fd, is16bit, stride, width, height, pad_x, pad_y):
    read_len = width * (2 if is16bit else 1)
    buf = [] # array('B') (read_len)
    for y in range(0, height):
        buf = fd.read(read_len)
        if fd.eof() or fd.fail():
            buf = []
            return False

        if not is16bit:
            for x in range(0, width):
                base[dst + x] = buf[x]
        else:
            for x in range(0, width):
                base[dst + x] = (buf[2*x+1] << 8) | buf[2*x]

        for x in range(width, width + pad_x):
            base[dst + x] = base[dst + width - 1]
        dst += stride
    for y in range(height, height + pad_y):
        for x in range(0, width + pad_x):
            base[dst + x] = base[dst - stride + x]
        dst += stride
    buf = []
    return True

def writePlane(fd, base, src, is16bit, stride, width, height):
    write_len = width * (2 if is16bit else 1)
    buf = [] # array('B') (write_len)
    for y in range(0, height):
        if not is16bit:
            for x in range(0, width):
                buf[x] = base[src + x]
        else:
            for x in range(0, width):
                buf[2*x] = base[src + x] & 0xff
                buf[2*x+1] = (base[src + x] >> 8) & 0xff

        fd.write(buf)
        if fd.eof() or fd.fail():
            buf = []
            return False
        src += stride
    buf = []
    return False


class TVideoIOYuv:

    def __init__(self):
        self.m_cHandle = None

    def open(self, pchFile, bWriteMode, fileBitdepth, internalBitdepth):
        self.m_bitdepthShift = internalBitdepth - fileBitdepth
        self.m_fileBitdepth = fileBitdepth

        if bWriteMode:
            self.m_cHandle = open(pchFile, "wb")

            if not self.m_cHandle:
                print("\nfailed to write reconstructed YUV file\n")
                sys.exit(0)
        else:
            self.m_cHandle = open(pchFile, "wb")

            if not self.m_cHandle:
                print("\nfailed to open Input YUV file\n")
                sys.exit(0)

    def close(self):
        self.m_cHandle.close()

    def skipFrames(self, numFrames, width, height):
        if not numFrames:
            return

        WORDS_SIZE = 2 if self.m_fileBitdepth > 8 else 1
        FRAME_SIZE = WORDS_SIZE * width * height * 3 / 2
        OFFSET = FRAME_SIZE * numFrames

        self.m_cHandle.seek(OFFSET, os.SEEK_CUR)

    #   self.m_cHandle.clear()

    #   BUF_SIZE = 512
    #   OFFSET_MOD_BUFSIZE = OFFSET % BUF_SIZE
    #   for i in range(0, OFFSET - OFFSET_MOD_BUFSIZE, BUF_SIZE):
    #       buf = self.m_cHandle.read(BUF_SIZE)
    #   buf = self.m_cHandle.read(OFFSET_MOD_BUFSIZE)

    def read(self, pPicYuv, aiPad):
        if self.isEof():
            return False

        iStride = pPicYuv.getStride()

        pad_h = aiPad[0]
        pad_v = aiPad[1]
        width_full = pPicYuv.getWidth()
        height_full = pPicYuv.getHeight()
        width = width_full - pad_h
        height = height_full - pad_v
        is16bit = self.m_fileBitdepth > 8

        desired_bitdepth = self.m_fileBitdepth + self.m_bitdepthShift
        minval = 0
        maxval = (1 << desired_bitdepth) - 1

        if not readPlane(pPicYuv.getBufY(), pPicYuv.getLumaAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(pPicYuv.getBufY(), pPicYuv.getLumaAddr(), iStride, width_full, height_full, self.m_bitdepthShift, minval, maxval)

        iStride >>= 1
        width_full >>= 1
        height_full >>= 1
        width >>= 1
        height >>= 1
        pad_h >>= 1
        pad_v >>= 1

        if not readPlane(pPicYuv.getBufU(), pPicYuv.getCbAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(pPicYuv.getBufU(), pPicYuv.getCbAddr(), iStride, width_full, height_full, self.m_bitdepthShift, minval, maxval)

        if not readPlane(pPicYuv.getBufV(), pPicYuv.getCrAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(pPicYuv.getBufV(), pPicYuv.getCrAddr(), iStride, width_full, height_full, self.m_bitdepthShift, minval, maxval)

        return True

    def write(self, pPicYuv, cropLeft=0, cropRight=0, cropTop=0, cropBottom=0):
        iStride = pPicYuv.getStride()
        width = pPicYuv.getWidth() - cropLeft - cropRight
        height = pPicYuv.getHeight() - cropTop - cropBottom
        is16bit = self.m_fileBitdepth > 8
        retval = True

        if self.m_bitdepthShift != 0:
            dstPicYuv = TComPicYuv()
            dstPicYuv.create(pPicYuv.getWidth(), pPicYuv.getHeight(), 1, 1, 0)
            pPicYuv.copyToPic(dstPicYuv)

            minval = 0
            maxval = (1 << self.m_fileBitdepth) - 1
            scalePlane(dstPicYuv.getBufY(), dstPicYuv.getLumaAddr(), dstPicYuv.getStride(), dstPicYuv.getWidth(), dstPicYuv.getHeight(), -self.m_bitdepthShift, minval, maxval)
            scalePlane(dstPicYuv.getBufU(), dstPicYuv.getCbAddr(), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitdepthShift, minval, maxval)
            scalePlane(dstPicYuv.getBufV(), dstPicYuv.getCrAddr(), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitdepthShift, minval, maxval)
        else:
            dstPicYuv = pPicYuv

        planeOffset = 0

        if not writePlane(self.m_cHandle, dstPicYuv.getBufY(), dstPicYuv.getLumaAddr() + planeOffset, is16bit, iStride, width, height):
            retval = False

        width >>= 1
        height >>= 1
        iStride >>= 1
        cropLeft >>= 1
        cropRight >>= 1

        planeOffset = 0

        if not writePlane(self.m_cHandle, dstPicYuv.getBufU(), dstPicYuv.getCbAddr() + planeOffset, is16bit, iStride, width, height):
            retval = False

        if not writePlane(self.m_cHandle, dstPicYuv.getBufV(), dstPicYuv.getCrAddr() + planeOffset, is16bit, iStride, width, height):
            retval = False

        if self.m_bitdepthShift != 0:
            dstPicYuv.destroy()
            del dstPicYuv
        return retval

    def isEof(self):
        cur = self.m_cHandle.tell()
        self.m_cHandle.seek(0, os.SEEK_END)
        end = self.m_cHandle.tell()
        self.m_cHandle.seek(cur, os.SEEK_SET)
        return cur == end

    def isFail(self):
        return not self.m_cHandle
