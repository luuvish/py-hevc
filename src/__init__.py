# -*- coding: utf-8 -*-
"""
	module : src
    HM 9.2 Python Implementation
"""

import sys
sys.path.insert(0, '..')

from time import clock
CLOCKS_PER_SEC = 1


from .pointer import pointer
from .trace import Trace


use_swig = 2


from swig.hevc import VectorBool, VectorUint8, VectorInt
from swig.hevc import ArrayBool, ArrayUChar, ArrayUInt, ArrayInt


from swig.hevc import cvar
if use_swig == 3:
    from swig.hevc import initROM, destroyROM
elif 4 <= use_swig:
    def initROM():
        from src.Lib.TLibCommon.TComRom import initROM as luuvc_initROM
        from swig.hevc import initROM as swig_initROM
        swig_initROM()
        luuvc_initROM()
    def destroyROM():
        from src.Lib.TLibCommon.TComRom import destroyROM as luuvc_destroyROM
        from swig.hevc import destroyROM as swig_destroyROM
        swig_destroyROM()
        luuvc_destroyROM()
    def initZscanToRaster(iMaxDepth, iDepth, uiStartVal, rpuiCurrIdx):
        from src.Lib.TLibCommon.TComRom import initZscanToRaster as luuvc_initZscanToRaster
        from swig.hevc import initZscanToRaster as swig_initZscanToRaster
        swig_initZscanToRaster(iMaxDepth, iDepth, uiStartVal, cvar.g_auiZscanToRaster)
        luuvc_initZscanToRaster(iMaxDepth, iDepth, uiStartVal, rpuiCurrIdx)
    def initRasterToZscan(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initRasterToZscan as luuvc_initRasterToZscan
        from swig.hevc import initRasterToZscan as swig_initRasterToZscan
        swig_initRasterToZscan(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initRasterToZscan(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
    def initRasterToPelXY(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initRasterToPelXY as luuvc_initRasterToPelXY
        from swig.hevc import initRasterToPelXY as swig_initRasterToPelXY
        swig_initRasterToPelXY(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initRasterToPelXY(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

if 2 <= use_swig:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
if 2 <= use_swig:
    from swig.hevc import TComPicYuv
    from swig.hevc import Window
if 3 <= use_swig:
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComPic, TComListTComPic
    from swig.hevc import TComSlice, TComVPS, TComSPS, TComPPS
if 4 <= use_swig:
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString, digest_get
if 5 <= use_swig:
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS

if 4 <= use_swig <= 8:
    from swig.hevc import ArrayTDecSbac, ArrayTDecBinCABAC
elif 9 <= use_swig:
    def ArrayTDecBinCABAC(size):
        from src.Lib.TLibDecoder.TDecBinCoderCABAC import TDecBinCABAC
        return pointer([TDecBinCABAC() for i in xrange(size)])
    def ArrayTDecSbac(size):
        from src.Lib.TLibDecoder.TDecSbac import TDecSbac
        return pointer([TDecSbac() for i in xrange(size)])
if 4 <= use_swig:
    from swig.hevc import ArrayTComInputBitstream
if 5 <= use_swig:
    from swig.hevc import VectorTDecSbac
if 6 <= use_swig:
    from swig.hevc import TComYuv, ArrayTComYuv
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import TComMv, ArrayTComMvField
if 9 <= use_swig:
    from swig.hevc import ArraySaoLcuParamPtr, ArraySaoLcuParam





if 3 <= use_swig <= 9:
    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

elif use_swig == 10:
    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant

    from src.Lib.TLibCommon.TComPrediction import TComPrediction

elif use_swig == 11:
    from src.Lib.TLibCommon.TComYuv import TComYuv
    def ArrayTComYuv(size):
        return [TComYuv() for i in xrange(size)]

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter

    from src.Lib.TLibCommon.TComTrQuant import TComTrQuant
    from src.Lib.TLibCommon.TComPrediction import TComPrediction

elif use_swig == 12:
    from src.Lib.TLibCommon.TComYuv import TComYuv
    def ArrayTComYuv(size):
        return [TComYuv() for i in xrange(size)]

    from swig.hevc import TComSampleAdaptiveOffset

    from src.Lib.TLibCommon.TComLoopFilter import TComLoopFilter
    from src.Lib.TLibCommon.TComTrQuant import TComTrQuant
    from src.Lib.TLibCommon.TComPrediction import TComPrediction

elif use_swig == 13:
    from swig.hevc import VectorNDBFBlockInfo

    from swig.hevc import TComMvField, TComCUMvField, ArrayTComCUMvField
    from src.Lib.TLibCommon.TComDataCU import TComDataCU
    def ArrayTComDataCU(size):
        return pointer([TComDataCU() for i in xrange(size)])
    from src.Lib.TLibCommon.TComYuv import TComYuv
    def ArrayTComYuv(size):
        return [TComYuv() for i in xrange(size)]

    from swig.hevc import TComSampleAdaptiveOffset

    from src.Lib.TLibCommon.TComLoopFilter import TComLoopFilter
    from src.Lib.TLibCommon.TComTrQuant import TComTrQuant
    from src.Lib.TLibCommon.TComPrediction import TComPrediction

elif use_swig == 14:
    from ..TLibCommon import TComRom as cvar # depend on TDecCavlc

    ArrayUInt = lambda size: [0 for i in xrange(size)] # TComPPS



if 3 <= use_swig:
    from swig.hevc import SEIDecodedPictureHash, SEImessages
    from swig.hevc import SEIReader
elif 9 <= use_swig:
    from src.Lib.TLibCommon.SEI import SEIDecodedPictureHash, SEImessages
    from src.Lib.TLibDecoder.SEIread import SEIReader

if 3 <= use_swig <= 8:
    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac
elif 9 <= use_swig:
    from src.Lib.TLibDecoder.TDecBinCoderCABAC import TDecBinCABAC
    from src.Lib.TLibDecoder.TDecSbac import TDecSbac
if 3 <= use_swig <= 7:
    from swig.hevc import TDecCavlc
elif 8 <= use_swig:
    from src.Lib.TLibDecoder.SyntaxElementParser import SyntaxElementParser
    from src.Lib.TLibDecoder.TDecCAVLC import TDecCavlc
if 3 <= use_swig <= 6:
    from swig.hevc import TDecEntropy
elif 7 <= use_swig:
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy

if 2 <= use_swig:
    from swig.hevc import TVideoIOYuv
elif 6 <= use_swig:
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

if 3 <= use_swig <= 5:
    from swig.hevc import TDecCu
elif 6 <= use_swig:
    from src.Lib.TLibDecoder.TDecCu import TDecCu
if 3 <= use_swig <= 4:
    from swig.hevc import TDecSlice
elif 5 <= use_swig:
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
if use_swig == 3:
    from swig.hevc import TDecGop
elif 4 <= use_swig:
    from src.Lib.TLibDecoder.TDecGop import TDecGop
if use_swig == 2:
    from swig.hevc import TDecTop
elif 3 <= use_swig:
    from src.Lib.TLibDecoder.TDecTop import TDecTop

if use_swig == 1:
    from swig.hevc import TAppDecTop
elif 2 <= use_swig:
    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
if use_swig == 0:
    from swig.hevc import decmain as TAppDecoder
elif 1 <= use_swig:
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder
