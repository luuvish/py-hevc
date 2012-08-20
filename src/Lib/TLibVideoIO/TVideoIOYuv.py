# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibVideoIO/TVideoIOYuv.py
    HM 8.0 Python Implementation
"""

import os
import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import TComPicYuv
    from swig.hevc import PelArray_frompointer as Pel
else:
    from ..TLibCommon.TComPicYuv import TComPicYuv
    def Pel(pel): return pel


def _scalePlane(img, stride, width, height, shiftbits, minval, maxval):

    def invScalePlane(img, stride, width, height, shiftbits, minval, maxval):
        Clip3 = lambda min, max, i: min if i < min else max if i > max else i
        offset = 1 << (shiftbits-1)
        base = 0
        for y in range(height):
            for x in range(width):
                val = (img[base + x] + offset) >> shiftbits
                img[base + x] = Clip3(minval, maxval, val)
            base += stride

    def scalePlane(img, stride, width, height, shiftbits):
        base = 0
        for y in range(height):
            for x in range(width):
                img[base + x] <<= shiftbits
            base += stride

    if shiftbits == 0:
        return

    if shiftbits > 0:
        scalePlane(img, stride, width, height, shiftbits)
    else:
        invScalePlane(img, stride, width, height, -shiftbits, minval, maxval)


class TVideoIOYuv(object):

    def __init__(self):
        self.m_cHandle = None
        self.m_fileBitdepth = 0
        self.m_bitdepthShift = 0

    def open(self, pchFile, bWriteMode, fileBitDepth, internalBitDepth):
        self.m_bitdepthShift = internalBitDepth - fileBitDepth
        self.m_fileBitdepth = fileBitDepth

        if bWriteMode:
            self.m_cHandle = open(pchFile, "wb")

            if not self.m_cHandle:
                sys.stdout.write("\nfailed to write reconstructed YUV file\n")
                sys.exit(False)
        else:
            self.m_cHandle = open(pchFile, "rb")

            if not self.m_cHandle:
                sys.stdout.write("\nfailed to open Input YUV file\n")
                sys.exit(False)

    def close(self):
        self.m_cHandle.close()

    def skipFrames(self, numFrames, width, height):
        if numFrames == 0:
            return

        WORD_SIZE = 2 if self.m_fileBitdepth > 8 else 1
        FRAME_SIZE = WORD_SIZE * width * height * 3 / 2
        OFFSET = FRAME_SIZE * numFrames

        self.m_cHandle.seek(OFFSET, os.SEEK_CUR)
    #   self.m_cHandle.clear()

    #   BUF_SIZE = 512
    #   OFFSET_MOD_BUFSIZE = OFFSET % BUF_SIZE
    #   for i in range(OFFSET - OFFSET_MOD_BUFSIZE, BUF_SIZE):
    #       buf = self.m_cHandle.read(BUF_SIZE)
    #   buf = self.m_cHandle.read(OFFSET_MOD_BUFSIZE)

    def read(self, pPicYuv, aiPad):

        def readPlane(dst, fd, is16bit, stride, width, height, pad_x, pad_y):
            read_len = width * (2 if is16bit else 1)
            buf = [] #bytearray(read_len)
            base = 0
            for y in range(height):
                buf = fd.read(read_len)
            #   if fd.eof() or fd.fail():
            #       buf = []
            #       return False

                if not is16bit:
                    for x in range(width):
                        dst[base + x] = buf[x]
                else:
                    for x in range(width):
                        dst[base + x] = (buf[2*x+1] << 8) | buf[2*x]

                for x in range(width, width + pad_x):
                    dst[base + x] = dst[base + width - 1]
                base += stride
            for y in range(height, height + pad_y):
                for x in range(width + pad_x):
                    dst[base + x] = dst[base - stride + x]
                base += stride
            buf = []
            return True

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

        if not readPlane(Pel(pPicYuv.getLumaAddr()), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        _scalePlane(Pel(pPicYuv.getLumaAddr()), iStride, width_full, height_full, self.m_bitdepthShift, minval, maxval)

        iStride >>= 1
        width_full >>= 1
        height_full >>= 1
        width >>= 1
        height >>= 1
        pad_h >>= 1
        pad_v >>= 1

        if not readPlane(Pel(pPicYuv.getCbAddr()), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        _scalePlane(Pel(pPicYuv.getCbAddr()), iStride, width_full, height_full, self.m_bitdepthShift, minval, maxval)

        if not readPlane(Pel(pPicYuv.getCrAddr()), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        _scalePlane(Pel(pPicYuv.getCrAddr()), iStride, width_full, height_full, self.m_bitdepthShift, minval, maxval)

        return True

    def write(self, pPicYuv, cropLeft=0, cropRight=0, cropTop=0, cropBottom=0):

        def writePlane(fd, src, base, is16bit, stride, width, height):
            write_len = width * (2 if is16bit else 1)
            buf = bytearray(write_len)
            for y in range(height):
                if not is16bit:
                    for x in range(width):
                        buf[x] = src[base + x]
                else:
                    for x in range(width):
                        buf[2*x] = src[base + x] & 0xff
                        buf[2*x+1] = (src[base + x] >> 8) & 0xff

                fd.write(buf)
            #   if fd.eof() or fd.fail():
            #       buf = []
            #       return False
                base += stride
            buf = []
            return False

        iStride = pPicYuv.getStride()
        width = pPicYuv.getWidth() - cropLeft - cropRight
        height = pPicYuv.getHeight() - cropTop - cropBottom
        is16bit = self.m_fileBitdepth > 8
        dstPicYuv = None
        retval = True

        if self.m_bitdepthShift != 0:
            dstPicYuv = TComPicYuv()
            dstPicYuv.create(pPicYuv.getWidth(), pPicYuv.getHeight(), 1, 1, 0)
            pPicYuv.copyToPic(dstPicYuv)

            minval = 0
            maxval = (1 << self.m_fileBitdepth) - 1
            _scalePlane(Pel(dstPicYuv.getLumaAddr()), dstPicYuv.getStride(), dstPicYuv.getWidth(), dstPicYuv.getHeight(), -self.m_bitdepthShift, minval, maxval)
            _scalePlane(Pel(dstPicYuv.getCbAddr()), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitdepthShift, minval, maxval)
            _scalePlane(Pel(dstPicYuv.getCrAddr()), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitdepthShift, minval, maxval)
        else:
            dstPicYuv = pPicYuv

        planeOffset = 0

        if not writePlane(self.m_cHandle, Pel(dstPicYuv.getLumaAddr()), planeOffset, is16bit, iStride, width, height):
            retval = False

        width >>= 1
        height >>= 1
        iStride >>= 1
        cropLeft >>= 1
        cropRight >>= 1

        planeOffset = 0

        if not writePlane(self.m_cHandle, Pel(dstPicYuv.getCbAddr()), planeOffset, is16bit, iStride, width, height):
            retval = False

        if not writePlane(self.m_cHandle, Pel(dstPicYuv.getCrAddr()), planeOffset, is16bit, iStride, width, height):
            retval = False

        if self.m_bitdepthShift != 0:
            dstPicYuv.destroy()
            dstPicYuv = None
        return retval

    def isEof(self):
        cur = self.m_cHandle.tell()
        self.m_cHandle.seek(0, os.SEEK_END)
        end = self.m_cHandle.tell()
        self.m_cHandle.seek(cur, os.SEEK_SET)
        return cur == end

    def isFail(self):
        return not self.m_cHandle
