# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComWeightPrediction.py
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

from .TypeDef import (REF_PIC_LIST_0, REF_PIC_LIST_1)

IF_INTERNAL_PREC = 14
IF_INTERNAL_OFFS = 1 << (IF_INTERNAL_PREC-1)


class TComWeightPrediction(object):

    def __init__(self):
        self.m_wp0 = None
        self.m_wp1 = None
        self.m_ibdi = 0

    def _xWeightPredictionUni(self, cCU, pcYuvSrc, uiPartAddr, iWidth, iHeight, eRefPicList, rpcYuvPred, iPartIdx, iRefIdx=-1):
        if iRefIdx < 0:
            iRefIdx = pcCU.getCUMvField(eRefPicList).getRefIdx(uiPartAddr)
        assert(iRefIdx >= 0)

        ibdi = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        pwp, pwpTmp = None, None

        if eRefPicList == REF_PIC_LIST_0:
            pwp, pwpTmp = self._getWpScaling(pcCU, iRefIdx, -1, ibdi)
        else:
            pwpTmp, pwp = self._getWpScaling(pcCU, -1, iRefIdx, ibdi)
        self._addWeightUni(pcYuvSrc, uiPartAddr, iWidth, iHeight, pwp, rpcYuvPred)

    def _xWeightPredictionBi(self, pcCU, pcYuvSrc0, pcYuvSrc1, iRefIdx0, iRefIdx1, uiPartIdx, iWidth, iHeight, rpcYuvDst):
        pps = pcCU.getSlice().getPPS()
        assert(pps.getWPBiPred())

        ibdi = cvar.g_uiBitDepth + cvar.g_uiBitIncrement
        pwp0, pwp1 = self._getWpScaling(pcCU, iRefIdx0, iRefIdx1, ibdi)

        if iRefIdx0 >= 0 and iRefIdx1 >= 0:
            self._addWeightBi(pcYuvSrc0, pcYuvSrc1, uiPartIdx, iWidth, iHeight, pwp0, pwp1, rpcYuvDst)
        elif iRefIdx0 >= 0 and iRefIdx1 < 0:
            self._addWeightUni(pcYuvSrc0, uiPartIdx, iWidth, iHeight, pwp0, rpcYuvDst)
        elif iRefIdx0 < 0 and iRefIdx1 >= 0:
            self._addWeightUni(pcYuvSrc1, uiPartIdx, iWidth, iHeight, pwp1, rpcYuvDst)
        else:
            assert(False)

    def _getWpScaling(self, pcCU, iRefIdx0, iRefIdx1, ibd1=None):
        wp0, wp1 = None, None
        ibd1 = (cvar.g_uiBitDepth + cvar.g_uiBitIncrement) if ibd1 == None else ibd1

        pcSlice = pcCU.getSlice()
        pps = pcCU.getSlice().getPPS()
        wpBiPred = pps.getWPBiPred()
        bBiDir = iRefIdx0 >= 0 and iRefIdx1 >= 0
        bUniDir = not bBiDir

        self.m_ibdi = ibd1
        if bUniDir or wpBiPred:
            if iRefIdx0 >= 0:
                wp0 = pcSlice.getWpScaling(REF_PIC_LIST_0, iRefIdx0)
            if iRefIdx1 >= 0:
                wp1 = pcSlice.getWpScaling(REF_PIC_LIST_1, iRefIdx1)
        else:
            assert(False)

        if iRefIdx0 < 0:
            wp0 = None
        if iRefIdx1 < 0:
            wp1 = None

        if bBiDir:
            for yuv in xrange(3):
                wp0[yuv].w = wp0[yuv].iWeight
                wp0[yuv].o = wp0[yuv].iOffset * (1 << (self.m_ibdi-8))
                wp1[yuv].w = wp1[yuv].iWeight
                wp1[yuv].o = wp1[yuv].iOffset * (1 << (self.m_ibdi-8))
                wp0[yuv].offset = wp0[yuv].o + wp1[yuv].o
                wp0[yuv].shift = wp0[yuv].uiLog2WeightDenom + 1
                wp0[yuv].round = 1 << wp0[yuv].uiLog2WeightDenom
                wp1[yuv].offset = wp0[yuv].offset
                wp1[yuv].shift = wp0[yuv].shift
                wp1[yuv].round = wp0[yuv].round
        else:
            pwp = wp0 if iRefIdx0 >= 0 else wp1
            for yuv in xrange(3):
                pwp[yuv].w = pwp[yuv].iWeight
                pwp[yuv].offset = pwp[yuv].iOffset * (1 << (self.m_ibdi-8))
                pwp[yuv].shift = pwp[yuv].uiLog2WeightDenom
                pwp[yuv].round = (1 << (pwp[yuv].uiLog2WeightDenom-1)) if pwp[yuv].uiLog2WeightDenom >= 1 else 0

        return wp0, wp1

    def _addWeightBi(self, pcYuvSrc0, pcYuvSrc1, iPartUnitIdx, iWidth, iHeight, wp0, wp1, rpcYuvDst, bRound=True):
        bRound = 1 if bRound else 0

        pSrcY0 = pointer(pcYuvSrc0.getLumaAddr(iPartUnitIdx), type='short *')
        pSrcU0 = pointer(pcYuvSrc0.getCbAddr(iPartUnitIdx), type='short *')
        pSrcV0 = pointer(pcYuvSrc0.getCrAddr(iPartUnitIdx), type='short *')

        pSrcY1 = pointer(pcYuvSrc1.getLumaAddr(iPartUnitIdx), type='short *')
        pSrcU1 = pointer(pcYuvSrc1.getCbAddr(iPartUnitIdx), type='short *')
        pSrcV1 = pointer(pcYuvSrc1.getCrAddr(iPartUnitIdx), type='short *')

        pDstY = pointer(rpcYuvDst.getLumaAddr(iPartUnitIdx), type='short *')
        pDstU = pointer(rpcYuvDst.getCbAddr(iPartUnitIdx), type='short *')
        pDstV = pointer(rpcYuvDst.getCrAddr(iPartUnitIdx), type='short *')

        # Luma : --------------------------------------------
        w0 = wp0[0].w
        offset = wp0[0].offset
        shiftnum = IF_INTERNAL_PREC - (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)
        shift = wp0[0].shift - shiftnum
        round = (1 << (shift-1)) * bRound if shift else 0
        w1 = wp1[0].w

        iSrc0Stride = pcYuvSrc0.getStride()
        iSrc1Stride = pcYuvSrc1.getStride()
        iDstStride = rpcYuvDst.getStride()

        for y in xrange(iHeight-1, -1, -1):
            for x in xrange(iWidth-1, -1, -4):
                # note: luma min width is 4
                pDstY[x-0] = self._weightBidir(w0, pSrcY0[x-0], w1, pSrcY1[x-0], round, shift, offset)
                pDstY[x-1] = self._weightBidir(w0, pSrcY0[x-1], w1, pSrcY1[x-1], round, shift, offset)
                pDstY[x-2] = self._weightBidir(w0, pSrcY0[x-2], w1, pSrcY1[x-2], round, shift, offset)
                pDstY[x-3] = self._weightBidir(w0, pSrcY0[x-3], w1, pSrcY1[x-3], round, shift, offset)
            pSrcY0 += iSrc0Stride
            pSrcY1 += iSrc1Stride
            pDstY += iDstStride

        # Chroma U : --------------------------------------------
        w0 = wp0[1].w
        offset = wp0[1].offset
        shift = wp0[1].shift + shiftnum
        round = (1 << (shift-1)) if shift else 0
        w1 = wp1[1].w

        iSrc0Stride = pcYuvSrc0.getCStride()
        iSrc1Stride = pcYuvSrc1.getCStride()
        iDstStride = rpcYuvDst.getCStride()

        iWidth >>= 1
        iHeight >>= 1

        for y in xrange(iHeight-1, -1, -1):
            for x in xrange(iWidth-1, -1, -2):
                # note: chroma min width is 2
                pDstU[x-0] = self._weightBidir(w0, pSrcU0[x-0], w1, pSrcU1[x-0], round, shift, offset)
                pDstU[x-1] = self._weightBidir(w0, pSrcU0[x-1], w1, pSrcU1[x-1], round, shift, offset)
            pSrcU0 += iSrc0Stride
            pSrcU1 += iSrc1Stride
            pDstU += iDstStride

        # Chroma V : --------------------------------------------
        w0 = wp0[2].w
        offset = wp0[2].offset
        shift = wp0[2].shift + shiftnum
        round = (1 << (shift-1)) if shift else 0
        w1 = wp1[2].w

        for y in xrange(iHeight-1, -1, -1):
            for x in xrange(iWidth-1, -1, -2):
                # note: chroma min width is 2
                pDstV[x-0] = self._weightBidir(w0, pSrcV0[x-0], w1, pSrcV1[x-0], round, shift, offset)
                pDstV[x-1] = self._weightBidir(w0, pSrcV0[x-1], w1, pSrcV1[x-1], round, shift, offset)
            pSrcV0 += iSrc0Stride
            pSrcV1 += iSrc1Stride
            pDstV += iDstStride

    def _addWeightUni(self, pcYuvSrc0, iPartUnitIdx, iWidth, iHeight, wp0, rpcYuvDst):
        pSrcY0 = pointer(pcYuvSrc0.getLumaAddr(iPartUnitIdx), type='short *')
        pSrcU0 = pointer(pcYuvSrc0.getCbAddr(iPartUnitIdx), type='short *')
        pSrcV0 = pointer(pcYuvSrc0.getCrAddr(iPartUnitIdx), type='short *')

        pDstY = pointer(rpcYuvDst.getLumaAddr(iPartUnitIdx), type='short *')
        pDstU = pointer(rpcYuvDst.getCbAddr(iPartUnitIdx), type='short *')
        pDstV = pointer(rpcYuvDst.getCrAddr(iPartUnitIdx), type='short *')

        # Luma : --------------------------------------------
        w0 = wp0[0].w
        offset = wp0[0].offset
        shiftnum = IF_INTERNAL_PREC - (cvar.g_uiBitDepth + cvar.g_uiBitIncrement)
        shift = wp0[0].shift - shiftnum
        round = (1 << (shift-1)) if shift else 0

        iSrc0Stride = pcYuvSrc0.getStride()
        iDstStride = rpcYuvDst.getStride()

        for y in xrange(iHeight-1, -1, -1):
            for x in xrange(iWidth-1, -1, -4):
                # note: luma min width is 4
                pDstY[x-0] = self._weightUnidir(w0, pSrcY0[x-0], round, shift, offset)
                pDstY[x-1] = self._weightUnidir(w0, pSrcY0[x-1], round, shift, offset)
                pDstY[x-2] = self._weightUnidir(w0, pSrcY0[x-2], round, shift, offset)
                pDstY[x-3] = self._weightUnidir(w0, pSrcY0[x-3], round, shift, offset)
            pSrcY0 += iSrc0Stride
            pDstY += iDstStride

        # Chroma U : --------------------------------------------
        w0 = wp0[1].w
        offset = wp0[1].offset
        shift = wp0[1].shift + shiftnum
        round = (1 << (shift-1)) if shift else 0

        iSrc0Stride = pcYuvSrc0.getCStride()
        iDstStride = rpcYuvDst.getCStride()

        iWidth >>= 1
        iHeight >>= 1

        for y in xrange(iHeight-1, -1, -1):
            for x in xrange(iWidth-1, -1, -2):
                # note: chroma min width is 2
                pDstU[x-0] = self._weightUnidir(w0, pSrcU0[x-0], round, shift, offset)
                pDstU[x-1] = self._weightUnidir(w0, pSrcU0[x-1], round, shift, offset)
            pSrcU0 += iSrc0Stride
            pDstU += iDstStride

        # Chroma V : --------------------------------------------
        w0 = wp0[2].w
        offset = wp0[2].offset
        shift = wp0[2].shift + shiftnum
        round = (1 << (shift-1)) if shift else 0

        for y in xrange(iHeight-1, -1, -1):
            for x in xrange(iWidth-1, -1, -2):
                # note: chroma min width is 2
                pDstV[x-0] = self._weightUnidir(w0, pSrcV0[x-0], round, shift, offset)
                pDstV[x-1] = self._weightUnidir(w0, pSrcV0[x-1], round, shift, offset)
            pSrcV0 += iSrc0Stride
            pDstV += iDstStride

    def _xClip(self, x):
        max = cvar.g_uiIBDI_MAX
        pel = 0 if x < 0 else max if x > max else x
        return pel

    def _weightBidir(self, w0, P0, w1, P1, round, shift, offset):
        return self._xClip((w0 * (P0 + IF_INTERNAL_OFFS) +
                           w1 * (P1 + IF_INTERNAL_OFFS) +
                           round + (offset << (shift-1))) >> shift)

    def _weightUnidir(self, w0, P0, round, shift, offset):
        return self._xClip(((w0 * (P0 + IF_INTERNAL_OFFS) + round) >> shift) + offset)
