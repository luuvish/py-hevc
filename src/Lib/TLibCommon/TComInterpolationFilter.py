# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComInterpolationFilter.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
else:
    from . import TComRom as cvar

from .pointer import pointer

NTAPS_LUMA = 8
NTAPS_CHROMA = 4
IF_INTERNAL_PREC = 14
IF_FILTER_PREC = 6
IF_INTERNAL_OFFS = 1 << (IF_INTERNAL_PREC-1)


class TComInterpolationFilter(object):

    m_lumaFilter = (
        ( 0, 0,   0, 64,  0,   0, 0,  0),
        (-1, 4, -10, 58, 17,  -5, 1,  0),
        (-1, 4, -11, 40, 40, -11, 4, -1),
        ( 0, 1,  -5, 17, 58, -10, 4, -1)
    )

    m_chromaFilter = (
        ( 0, 64,  0,  0),
        (-2, 58, 10, -2),
        (-4, 54, 16, -2),
        (-6, 46, 28, -4),
        (-4, 36, 36, -4),
        (-4, 28, 46, -6),
        (-2, 16, 54, -4),
        (-2, 10, 58, -2)
    )

    def __init__(self):
        pass

    @staticmethod
    def filterCopy(src, srcStride, dst, dstStride, width, height, isFirst, isLast):
        src = pointer(src.cast(), type='short *')
        dst = pointer(dst, type='short *')

        if isFirst == isLast:
            for row in xrange(height):
                for col in xrange(width):
                    dst[col] = src[col]

                src += srcStride
                dst += dstStride
        elif isFirst:
            shift = IF_INTERNAL_PREC - (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)

            for row in xrange(height):
                for col in xrange(width):
                    val = src[col] << shift
                    dst[col] = val - IF_INTERNAL_OFFS

                src += srcStride
                dst += dstStride
        else:
            shift = IF_INTERNAL_PREC - (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)
            offset = IF_INTERNAL_OFFS
            offset += 1 << (shift-1) if shift else 0
            maxVal = cvar.g_uiIBDI_MAX
            minVal = 0
            for row in xrange(height):
                for col in xrange(width):
                    val = src[col]
                    val = (val + offset) >> shift
                    if val < minVal:
                        val = minVal
                    if val > maxVal:
                        val = maxVal
                    dst[col] = val

                src += srcStride
                dst += dstStride

    @staticmethod
    def filter(N, isVertical, isFirst, isLast):
        def _filter(src, srcStride, dst, dstStride, width, height, coeff):
            c = 8 * [0]
            c[0] = coeff[0]
            c[1] = coeff[1]
            if N >= 4:
                c[2] = coeff[2]
                c[3] = coeff[3]
            if N >= 6:
                c[4] = coeff[4]
                c[5] = coeff[5]
            if N == 8:
                c[6] = coeff[6]
                c[7] = coeff[7]

            cStride = srcStride if isVertical else 1
            src -= (N/2 - 1) * cStride
            src = pointer(src.cast(), type='short *')
            dst = pointer(dst, type='short *')

            offset = 0
            maxVal = 0
            headRoom = IF_INTERNAL_PREC - (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)
            shift = IF_FILTER_PREC
            if isLast:
                shift += (0 if isFirst else headRoom)
                offset = 1 << (shift-1)
                offset += (0 if isFirst else IF_INTERNAL_OFFS << IF_FILTER_PREC)
                maxVal = cvar.g_uiIBDI_MAX
            else:
                shift -= (headRoom if isFirst else 0)
                offset = (-IF_INTERNAL_OFFS << shift if isFirst else 0)
                maxVal = 0

            for row in xrange(height):
                for col in xrange(width):
                    sum  = src[col + 0 * cStride] * c[0]
                    sum += src[col + 1 * cStride] * c[1]
                    if N >= 4:
                        sum += src[col + 2 * cStride] * c[2]
                        sum += src[col + 3 * cStride] * c[3]
                    if N >= 6:
                        sum += src[col + 4 * cStride] * c[4]
                        sum += src[col + 5 * cStride] * c[5]
                    if N == 8:
                        sum += src[col + 6 * cStride] * c[6]
                        sum += src[col + 7 * cStride] * c[7]

                    val = (sum + offset) >> shift
                    if isLast:
                        val = (0 if val < 0 else val)
                        val = (maxVal if val > maxVal else val)
                    dst[col] = val

                src += srcStride
                dst += dstStride
        return _filter

    @staticmethod
    def filterHor(N):
        def _filter(src, srcStride, dst, dstStride, width, height, isLast, coeff):
            if isLast:
                TComInterpolationFilter.filter(N, False, True, True)(src, srcStride, dst, dstStride, width, height, coeff)
            else:
                TComInterpolationFilter.filter(N, False, True, False)(src, srcStride, dst, dstStride, width, height, coeff)
        return _filter

    @staticmethod
    def filterVer(N):
        def _filter(src, srcStride, dst, dstStride, width, height, isFirst, isLast, coeff):
            if isFirst and isLast:
                TComInterpolationFilter.filter(N, True, True, True)(src, srcStride, dst, dstStride, width, height, coeff)
            elif isFirst and not isLast:
                TComInterpolationFilter.filter(N, True, True, False)(src, srcStride, dst, dstStride, width, height, coeff)
            elif not isFirst and isLast:
                TComInterpolationFilter.filter(N, True, False, True)(src, srcStride, dst, dstStride, width, height, coeff)
            else:
                TComInterpolationFilter.filter(N, True, False, False)(src, srcStride, dst, dstStride, width, height, coeff)
        return _filter

    def filterHorLuma(self, src, srcStride, dst, dstStride, width, height, frac, isLast):
        assert(frac >= 0 and frac < 4)

        if frac == 0:
            TComInterpolationFilter.filterCopy(
                src, srcStride, dst, dstStride, width, height, True, isLast)
        else:
            TComInterpolationFilter.filterHor(NTAPS_LUMA)(
                src, srcStride, dst, dstStride, width, height, isLast,
                TComInterpolationFilter.m_lumaFilter[frac])

    def filterVerLuma(self, src, srcStride, dst, dstStride, width, height, frac, isFirst, isLast):
        assert(frac >= 0 and frac < 4)

        if frac == 0:
            TComInterpolationFilter.filterCopy(
                src, srcStride, dst, dstStride, width, height, isFirst, isLast)
        else:
            TComInterpolationFilter.filterVer(NTAPS_LUMA)(
                src, srcStride, dst, dstStride, width, height, isFirst, isLast,
                TComInterpolationFilter.m_lumaFilter[frac])

    def filterHorChroma(self, src, srcStride, dst, dstStride, width, height, frac, isLast):
        assert(frac >= 0 and frac < 8)

        if frac == 0:
            TComInterpolationFilter.filterCopy(
                src, srcStride, dst, dstStride, width, height, True, isLast)
        else:
            TComInterpolationFilter.filterHor(NTAPS_CHROMA)(
                src, srcStride, dst, dstStride, width, height, isLast,
                TComInterpolationFilter.m_chromaFilter[frac])

    def filterVerChroma(self, src, srcStride, dst, dstStride, width, height, frac, isFirst, isLast):
        assert(frac >= 0 and frac < 8)

        if frac == 0:
            TComInterpolationFilter.filterCopy(
                src, srcStride, dst, dstStride, width, height, isFirst, isLast)
        else:
            TComInterpolationFilter.filterVer(NTAPS_CHROMA)(
                src, srcStride, dst, dstStride, width, height, isFirst, isLast,
                TComInterpolationFilter.m_chromaFilter[frac])
