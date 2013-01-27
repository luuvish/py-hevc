# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibVideoIO/TVideoIOYuv.py
    HM 9.2 Python Implementation
"""

import os
import sys

from ... import pointer
from ... import TComPicYuv

from ..TLibCommon.CommonDef import Clip3


def scalePlane(img, stride, width, height, shiftbits, minval, maxval):

    def _invScalePlane(img, stride, width, height, shiftbits, minval, maxval):
        img = pointer(img, type='short *')
        offset = 1 << (shiftbits-1)
        for y in xrange(height):
            for x in xrange(width):
                val = (img[x] + offset) >> shiftbits
                img[x] = Clip3(minval, maxval, val)
            img += stride

    def _scalePlane(img, stride, width, height, shiftbits):
        img = pointer(img, type='short *')
        for y in xrange(height):
            for x in xrange(width):
                img[x] <<= shiftbits
            img += stride

    if shiftbits == 0:
        return

    if shiftbits > 0:
        _scalePlane(img, stride, width, height, shiftbits)
    else:
        _invScalePlane(img, stride, width, height, -shiftbits, minval, maxval)


class TVideoIOYuv(object):

    def __init__(self):
        self.m_cHandle        = None
        self.m_fileBitDepthY  = 0
        self.m_fileBitDepthC  = 0
        self.m_bitDepthShiftY = 0
        self.m_bitDepthShiftC = 0

    def open(self, pchFile, bWriteMode,
             fileBitDepthY, fileBitDepthC, internalBitDepthY, internalBitDepthC):
        self.m_bitDepthShiftY = internalBitDepthY - fileBitDepthY
        self.m_bitDepthShiftC = internalBitDepthC - fileBitDepthC
        self.m_fileBitDepthY = fileBitDepthY
        self.m_fileBitDepthC = fileBitDepthC

        if bWriteMode:
            try:
                self.m_cHandle = open(pchFile, "wb")
            except IOError:
                sys.stdout.write("\nfailed to write reconstructed YUV file\n")
                sys.exit(False)
        else:
            try:
                self.m_cHandle = open(pchFile, "rb")
            except IOError:
                sys.stdout.write("\nfailed to open Input YUV file\n")
                sys.exit(False)

    def close(self):
        self.m_cHandle.close()

    def skipFrames(self, numFrames, width, height):
        if numFrames == 0:
            return

        wordsize = 2 if self.m_fileBitDepthY > 8 or self.m_fileBitDepthC > 8 else 1
        framesize = wordsize * width * height * 3 / 2
        offset = framesize * numFrames

        # attempt to seek
        self.m_cHandle.seek(offset, os.SEEK_CUR)
        return

        # fall back to consuming the input
        BUF_SIZE = 512
        offset_mod_bufsize = offset % BUF_SIZE
        for i in xrange(0, offset - offset_mod_bufsize, BUF_SIZE):
            buf = self.m_cHandle.read(BUF_SIZE)
        buf = self.m_cHandle.read(offset_mod_bufsize)

    def read(self, pPicYuv, aiPad):

        def readPlane(dst, fd, is16bit, stride, width, height, pad_x, pad_y):
            read_len = width * (2 if is16bit else 1)
            dst = pointer(dst, type='short *')
            buf = bytearray(read_len)
            for y in xrange(height):
                buf = fd.read(read_len)
            #   if fd.eof() or fd.fail():
            #       buf = []
            #       return False

                if not is16bit:
                    for x in xrange(width):
                        dst[x] = buf[x]
                else:
                    for x in xrange(width):
                        dst[x] = (buf[2*x+1] << 8) | buf[2*x]

                for x in xrange(width, width + pad_x):
                    dst[x] = dst[width - 1]
                dst += stride
            for y in xrange(height, height + pad_y):
                for x in xrange(width + pad_x):
                    dst[x] = dst[x - stride]
                dst += stride
            del buf
            return True

        # check end-of-file
        if self.isEof():
            return False

        iStride = pPicYuv.getStride()

        # compute actual YUV width & height excluding padding size
        aiPad = pointer(aiPad, type='int *')
        pad_h = aiPad[0]
        pad_v = aiPad[1]
        width_full = pPicYuv.getWidth()
        height_full = pPicYuv.getHeight()
        width = width_full - pad_h
        height = height_full - pad_v
        is16bit = self.m_fileBitDepthY > 8 or self.m_fileBitDepthC > 8

        desired_bitdepthY = self.m_fileBitDepthY + self.m_bitDepthShiftY
        desired_bitdepthC = self.m_fileBitDepthC + self.m_bitDepthShiftC
        minvalY = 0
        minvalC = 0
        maxvalY = (1 << desired_bitdepthY) - 1
        maxvalC = (1 << desired_bitdepthC) - 1

        if not readPlane(pPicYuv.getLumaAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(pPicYuv.getLumaAddr(), iStride, width_full, height_full, self.m_bitDepthShiftY, minvalY, maxvalY)

        iStride >>= 1
        width_full >>= 1
        height_full >>= 1
        width >>= 1
        height >>= 1
        pad_h >>= 1
        pad_v >>= 1

        if not readPlane(pPicYuv.getCbAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(pPicYuv.getCbAddr(), iStride, width_full, height_full, self.m_bitDepthShiftC, minvalC, maxvalC)

        if not readPlane(pPicYuv.getCrAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(pPicYuv.getCrAddr(), iStride, width_full, height_full, self.m_bitDepthShiftC, minvalC, maxvalC)

        return True

    def write(self, pPicYuv, cropLeft=0, cropRight=0, cropTop=0, cropBottom=0):

        def writePlane(fd, src, is16bit, stride, width, height):
            write_len = width * (2 if is16bit else 1)
            src = pointer(src, type='short *')
            buf = bytearray(write_len)
            for y in xrange(height):
                if not is16bit:
                    for x in xrange(width):
                        buf[x] = src[x]
                else:
                    for x in xrange(width):
                        buf[2*x+0] = src[x] & 0xff
                        buf[2*x+1] = (src[x] >> 8) & 0xff

                fd.write(buf)
            #   if fd.eof() or fd.fail():
            #       buf = []
            #       return False
                src += stride
            del buf
            return False

        # compute actual YUV frame size excluding padding size
        iStride = pPicYuv.getStride()
        width = pPicYuv.getWidth() - cropLeft - cropRight
        height = pPicYuv.getHeight() - cropTop - cropBottom
        is16bit = self.m_fileBitDepthY > 8 or self.m_fileBitDepthC > 8
        dstPicYuv = None
        retval = True

        if self.m_bitDepthShiftY != 0 or self.m_bitDepthShiftC != 0:
            dstPicYuv = TComPicYuv()
            dstPicYuv.create(pPicYuv.getWidth(), pPicYuv.getHeight(), 1, 1, 0)
            pPicYuv.copyToPic(dstPicYuv)

            minvalY = 0
            minvalC = 0
            maxvalY = (1 << self.m_fileBitDepthY) - 1
            maxvalC = (1 << self.m_fileBitDepthC) - 1

            scalePlane(dstPicYuv.getLumaAddr(), dstPicYuv.getStride(), dstPicYuv.getWidth(), dstPicYuv.getHeight(), -self.m_bitDepthShiftY, minvalY, maxvalY)
            scalePlane(dstPicYuv.getCbAddr(), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitDepthShiftC, minvalC, maxvalC)
            scalePlane(dstPicYuv.getCrAddr(), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitDepthShiftC, minvalC, maxvalC)
        else:
            dstPicYuv = pPicYuv

        # location of upper left pel in a plane
        planeOffset = 0 #cropLeft + cropTop * iStride;

        if not writePlane(self.m_cHandle, pointer(dstPicYuv.getLumaAddr(), base=planeOffset, type='short *'), is16bit, iStride, width, height):
            retval = False

        width >>= 1
        height >>= 1
        iStride >>= 1
        cropLeft >>= 1
        cropRight >>= 1

        planeOffset = 0 # cropLeft + cropTop * iStride;

        if not writePlane(self.m_cHandle, pointer(dstPicYuv.getCbAddr(), base=planeOffset, type='short *'), is16bit, iStride, width, height):
            retval = False

        if not writePlane(self.m_cHandle, pointer(dstPicYuv.getCrAddr(), base=planeOffset, type='short *'), is16bit, iStride, width, height):
            retval = False

        if self.m_bitDepthShiftY != 0 or self.m_bitDepthShiftC != 0:
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
