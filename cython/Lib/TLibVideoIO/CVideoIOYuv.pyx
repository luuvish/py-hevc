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

from libc.stdio cimport fopen, fclose, fread, fwrite, feof, ferror
from libc.stdio cimport SEEK_SET, SEEK_CUR, SEEK_END, fseek
from libc.stdlib cimport malloc, free


cdef _invScalePlane(short *img, unsigned int stride, unsigned int width, unsigned int height,
                    unsigned int shiftbits, short minval, short maxval):
    cdef short offset = 1 << (shiftbits-1)
    cdef unsigned int x, y
    cdef short val
    for y in xrange(height):
        for x in xrange(width):
            val = (img[x] + offset) >> shiftbits
            img[x] = Clip3(minval, maxval, val)
        img += stride

cdef _scalePlane(short *img, unsigned int stride, unsigned int width, unsigned int height, unsigned int shiftbits):
    cdef unsigned int x, y
    for y in xrange(height):
        for x in xrange(width):
            img[x] <<= shiftbits
        img += stride

cdef scalePlane(short *img, unsigned int stride, unsigned int width, unsigned int height, shiftbits, short minval, short maxval):
    if shiftbits == 0:
        return

    if shiftbits > 0:
        _scalePlane(img, stride, width, height, shiftbits)
    else:
        _invScalePlane(img, stride, width, height, -shiftbits, minval, maxval)


cdef bint readPlane(short *dst, FILE *fd, bint is16bit, int stride, int width, int height, int pad_x, int pad_y):
    cdef int read_len
    cdef unsigned char *buf
    read_len = width * (2 if is16bit else 1)
    buf = <unsigned char*>malloc(read_len)
    for y in xrange(height):
        fread(buf, read_len, 1, fd)
        if feof(fd) or ferror(fd):
            free(buf)
            return False

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
    free(buf)
    return True

cdef bint writePlane(FILE *fd, short *src, bint is16bit, int stride, int width, int height):
    cdef int write_len
    cdef unsigned char *buf
    write_len = width * (2 if is16bit else 1)
    buf = <unsigned char*>malloc(write_len)
    for y in xrange(height):
        if not is16bit:
            for x in xrange(width):
                buf[x] = src[x]
        else:
            for x in xrange(width):
                buf[2*x+0] = (src[x]     ) & 0xff
                buf[2*x+1] = (src[x] >> 8) & 0xff

        fwrite(buf, write_len, 1, fd)
        if feof(fd) or ferror(fd):
            free(buf)
            return False
        src += stride
    free(buf)
    return False


cdef class CVideoIOYuv:

    def __cinit__(self):
        self.m_cHandle        = NULL
        self.m_fileBitDepthY  = 0
        self.m_fileBitDepthC  = 0
        self.m_bitDepthShiftY = 0
        self.m_bitDepthShiftC = 0

    def __init__(self):
        pass

    cpdef open(self, char* pchFile, bint bWriteMode,
               int fileBitDepthY, int fileBitDepthC, int internalBitDepthY, int internalBitDepthC):
        self.m_bitDepthShiftY = internalBitDepthY - fileBitDepthY
        self.m_bitDepthShiftC = internalBitDepthC - fileBitDepthC
        self.m_fileBitDepthY = fileBitDepthY
        self.m_fileBitDepthC = fileBitDepthC

        if bWriteMode:
            self.m_cHandle = fopen(pchFile, "wb")
            if self.m_cHandle == NULL:
                sys.stdout.write("\nfailed to write reconstructed YUV file\n")
                sys.exit(False)
        else:
            self.m_cHandle = fopen(pchFile, "rb")
            if self.m_cHandle == NULL:
                sys.stdout.write("\nfailed to open Input YUV file\n")
                sys.exit(False)

    cpdef close(self):
        fclose(self.m_cHandle)

    cpdef skipFrames(self, unsigned int numFrames, unsigned int width, unsigned int height):
        cdef unsigned int wordsize
        cdef unsigned int framesize
        cdef unsigned int offset
        cdef unsigned int offset_mod_bufsize
        DEF BUF_SIZE = 512
        cdef char buf[BUF_SIZE]

        if numFrames == 0:
            return

        wordsize = 2 if self.m_fileBitDepthY > 8 or self.m_fileBitDepthC > 8 else 1
        framesize = wordsize * width * height * 3 / 2
        offset = framesize * numFrames

        # attempt to seek
        if fseek(self.m_cHandle, offset, SEEK_CUR):
            return

        # fall back to consuming the input
        offset_mod_bufsize = offset % BUF_SIZE
        for i in xrange(0, offset - offset_mod_bufsize, BUF_SIZE):
            fread(buf, BUF_SIZE, 1, self.m_cHandle)
        fread(buf, offset_mod_bufsize, 1, self.m_cHandle)

    cpdef bint read(self, pPicYuv, int aiPad[2]):
        cdef int iStride
        cdef unsigned int pad_h, pad_v, width_full, height_full, width, height
        cdef bint is16bit
        cdef int desired_bitdepthY, desired_bitdepthC
        cdef short minvalY, minvalC, maxvalY, maxvalC
        cdef short *lumaAddr = <short*>pPicYuv.getLumaAddr().frompointer()
        cdef short *cbAddr = <short*>pPicYuv.getCbAddr().frompointer()
        cdef short *crAddr = <short*>pPicYuv.getCrAddr().frompointer()

        # check end-of-file
        if self.isEof():
            return False

        iStride = pPicYuv.getStride()

        # compute actual YUV width & height excluding padding size
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

        if not readPlane(<short*>pPicYuv.getCbAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(<short*>pPicYuv.getCbAddr(), iStride, width_full, height_full, self.m_bitDepthShiftC, minvalC, maxvalC)

        if not readPlane(<short*>pPicYuv.getCrAddr(), self.m_cHandle, is16bit, iStride, width, height, pad_h, pad_v):
            return False
        scalePlane(<short*>pPicYuv.getCrAddr(), iStride, width_full, height_full, self.m_bitDepthShiftC, minvalC, maxvalC)

        return True

    cpdef bint write(self, pPicYuv, int confLeft=0, int confRight=0, int confTop=0, int confBottom=0):
        cdef int iStride
        cdef unsigned int width, height
        cdef bint is16bit
        cdef bint retval
        cdef short *lumaAddr
        cdef short *cbAddr
        cdef short *crAddr

        # compute actual YUV frame size excluding padding size
        iStride = pPicYuv.getStride()
        width = pPicYuv.getWidth() - confLeft - confRight
        height = pPicYuv.getHeight() - confTop - confBottom
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

            lumaAddr = dstPicYuv.getLumaAddr()
            cbAddr = dstPicYuv.getCbAddr()
            crAddr = dstPicYuv.getCrAddr()
            scalePlane(dstPicYuv.getLumaAddr(), dstPicYuv.getStride(), dstPicYuv.getWidth(), dstPicYuv.getHeight(), -self.m_bitDepthShiftY, minvalY, maxvalY)
            scalePlane(dstPicYuv.getCbAddr(), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitDepthShiftC, minvalC, maxvalC)
            scalePlane(dstPicYuv.getCrAddr(), dstPicYuv.getCStride(), dstPicYuv.getWidth()>>1, dstPicYuv.getHeight()>>1, -self.m_bitDepthShiftC, minvalC, maxvalC)
        else:
            dstPicYuv = pPicYuv
            lumaAddr = dstPicYuv.getLumaAddr()
            cbAddr = dstPicYuv.getCbAddr()
            crAddr = dstPicYuv.getCrAddr()

        # location of upper left pel in a plane
        planeOffset = 0 #cropLeft + cropTop * iStride;

        if not writePlane(self.m_cHandle, <short*>dstPicYuv.getLumaAddr() + planeOffset, is16bit, iStride, width, height):
            retval = False

        width >>= 1
        height >>= 1
        iStride >>= 1
        confLeft >>= 1
        confRight >>= 1

        planeOffset = 0 # cropLeft + cropTop * iStride;

        if not writePlane(self.m_cHandle, <short*>dstPicYuv.getCbAddr() + planeOffset, is16bit, iStride, width, height):
            retval = False

        if not writePlane(self.m_cHandle, <short*>dstPicYuv.getCrAddr() + planeOffset, is16bit, iStride, width, height):
            retval = False

        if self.m_bitDepthShiftY != 0 or self.m_bitDepthShiftC != 0:
            dstPicYuv.destroy()
            dstPicYuv = None
        return retval

    cpdef bint isEof(self):
        return feof(self.m_cHandle)

    cpdef bint isFail(self):
        return self.m_cHandle == NULL or ferror(self.m_cHandle)
