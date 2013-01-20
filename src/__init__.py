# -*- coding: utf-8 -*-
"""
	module : src
    HM 9.1 Python Implementation
"""

import sys
sys.path.insert(0, '..')

from time import clock
CLOCKS_PER_SEC = 1


from src.Lib.TLibCommon.pointer import pointer
from src.Lib.TLibCommon import trace


use_swig = 5

if use_swig == 0:
    from swig.hevc import decmain as TAppDecoder

elif use_swig == 1:
    from swig.hevc import cvar
    from swig.hevc import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 2:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import VectorUint8

    from swig.hevc import cvar
    from swig.hevc import TDecTop
    from swig.hevc import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 3:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import VectorUint8
    from swig.hevc import ArrayInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv

    from swig.hevc import cvar
    from swig.hevc import initROM, destroyROM
    from swig.hevc import TVideoIOYuv
    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from swig.hevc import SEIReader
    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac
    from swig.hevc import TDecCavlc
    from swig.hevc import TDecEntropy
    from swig.hevc import TDecCu
    from swig.hevc import TDecSlice
    from swig.hevc import TDecGop

    from src.Lib.TLibDecoder.TDecTop import TDecTop

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 4:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import SEIDecodedPictureHash, digest_get
    from swig.hevc import VectorBool, VectorUint8, VectorInt
    from swig.hevc import ArrayInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv

    from swig.hevc import cvar
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
        swig_initZscanToRaster(iMaxDepth, iDepth, uiStartVal, rpuiCurrIdx)
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

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TDecSbac, ArrayTDecSbac, ArrayTDecBinCABAC

    from swig.hevc import TVideoIOYuv
    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from swig.hevc import SEIReader
    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac
    from swig.hevc import TDecCavlc
    from swig.hevc import TDecEntropy
    from swig.hevc import TDecCu
    from swig.hevc import TDecSlice

    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 5:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import SEIDecodedPictureHash, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt
    from swig.hevc import ArrayInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv

    from swig.hevc import cvar
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

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TDecSbac, VectorTDecSbac, ArrayTDecSbac, ArrayTDecBinCABAC

    from swig.hevc import TVideoIOYuv
    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from swig.hevc import SEIReader
    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac
    from swig.hevc import TDecCavlc
    from swig.hevc import TDecEntropy
    from swig.hevc import TDecCu

    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 6:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TDecSbac, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import TComYuv, ArrayTComYuv
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac
    from swig.hevc import TDecCavlc
    from swig.hevc import TDecEntropy

    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 7:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TDecSbac, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import TComYuv, ArrayTComYuv
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac
    from swig.hevc import TDecCavlc

    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 8:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import parseSEImessage, SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TDecSbac, ArrayTDecSbac, ArrayTDecBinCABAC
    from swig.hevc import TComYuv, ArrayTComYuv
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar
    from swig.hevc import ArrayUInt

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from swig.hevc import TDecBinCABAC
    from swig.hevc import TDecSbac

    from src.Lib.TLibDecoder.TDecCavlc import TDecCavlc
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 9:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import parseSEImessage, SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TComYuv, ArrayTComYuv
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar
    from swig.hevc import ArrayUInt, ArrayInt, ArrayBool
    from swig.hevc import ArraySaoLcuParamPtr, ArraySaoLcuParam
    def ArrayTDecBinCABAC(size):
        from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac
        return pointer([TDecBinCabac() for i in xrange(size)])
    def ArrayTDecSbac(size):
        from src.Lib.TLibDecoder.TDecSbac import TDecSbac
        return pointer([TDecSbac() for i in xrange(size)])

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant
    from swig.hevc import TComPrediction

    from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac as TDecBinCABAC
    from src.Lib.TLibDecoder.TDecSbac import TDecSbac
    from src.Lib.TLibDecoder.TDecCavlc import TDecCavlc
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 10:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import parseSEImessage, SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TComYuv, ArrayTComYuv
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar
    from swig.hevc import ArrayUInt, ArrayInt, ArrayBool
    from swig.hevc import ArraySaoLcuParamPtr, ArraySaoLcuParam
    def ArrayTDecBinCABAC(size):
        from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac
        return pointer([TDecBinCabac() for i in xrange(size)])
    def ArrayTDecSbac(size):
        from src.Lib.TLibDecoder.TDecSbac import TDecSbac
        return pointer([TDecSbac() for i in xrange(size)])

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter
    from swig.hevc import TComTrQuant

    from src.Lib.TLibCommon.TComPrediction import TComPrediction

    from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac as TDecBinCABAC
    from src.Lib.TLibDecoder.TDecSbac import TDecSbac
    from src.Lib.TLibDecoder.TDecCavlc import TDecCavlc
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 11:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import parseSEImessage, SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar
    from swig.hevc import ArrayUInt, ArrayInt, ArrayBool
    from swig.hevc import ArraySaoLcuParamPtr, ArraySaoLcuParam
    from src.Lib.TLibCommon.TComYuv import TComYuv
    def ArrayTComYuv(size):
        return [TComYuv() for i in xrange(size)]
    def ArrayTDecBinCABAC(size):
        from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac
        return pointer([TDecBinCabac() for i in xrange(size)])
    def ArrayTDecSbac(size):
        from src.Lib.TLibDecoder.TDecSbac import TDecSbac
        return pointer([TDecSbac() for i in xrange(size)])

    from swig.hevc import TComSampleAdaptiveOffset
    from swig.hevc import TComLoopFilter

    from src.Lib.TLibCommon.TComTrQuant import TComTrQuant
    from src.Lib.TLibCommon.TComPrediction import TComPrediction

    from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac as TDecBinCABAC
    from src.Lib.TLibDecoder.TDecSbac import TDecSbac
    from src.Lib.TLibDecoder.TDecCavlc import TDecCavlc
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 12:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import parseSEImessage, SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import TComDataCU, ArrayTComDataCU
    from swig.hevc import ArrayTComMvField, ArrayUChar
    from swig.hevc import ArrayUInt, ArrayInt, ArrayBool
    from swig.hevc import ArraySaoLcuParamPtr, ArraySaoLcuParam
    from src.Lib.TLibCommon.TComYuv import TComYuv
    def ArrayTComYuv(size):
        return [TComYuv() for i in xrange(size)]
    def ArrayTDecBinCABAC(size):
        from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac
        return pointer([TDecBinCabac() for i in xrange(size)])
    def ArrayTDecSbac(size):
        from src.Lib.TLibDecoder.TDecSbac import TDecSbac
        return pointer([TDecSbac() for i in xrange(size)])

    from swig.hevc import TComSampleAdaptiveOffset

    from src.Lib.TLibCommon.TComLoopFilter import TComLoopFilter
    from src.Lib.TLibCommon.TComTrQuant import TComTrQuant
    from src.Lib.TLibCommon.TComPrediction import TComPrediction

    from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac as TDecBinCABAC
    from src.Lib.TLibDecoder.TDecSbac import TDecSbac
    from src.Lib.TLibDecoder.TDecCavlc import TDecCavlc
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 13:
    from swig.hevc import InputByteStream, AnnexBStats, byteStreamNALUnit
    from swig.hevc import InputNALUnit, read
    from swig.hevc import istream_open, istream_clear, istream_not, istream_tellg, istream_seekg
    from swig.hevc import calcMD5, calcCRC, calcChecksum, digestToString
    from swig.hevc import parseSEImessage, SEIpictureDigest, digest_get
    from swig.hevc import ParameterSetManager
    from swig.hevc import ParameterSetMapTComVPS, ParameterSetMapTComSPS, ParameterSetMapTComPPS
    from swig.hevc import VectorBool, VectorUint8, VectorInt
    from swig.hevc import VectorNDBFBlockInfo

    from swig.hevc import TComPic
    from swig.hevc import ParameterSetManagerDecoder
    from swig.hevc import TComListTComPic
    from swig.hevc import TComSlice
    from swig.hevc import SEImessages
    from swig.hevc import TComVPS, TComSPS, TComPPS
    from swig.hevc import TComPicYuv
    from swig.hevc import TComMv

    from swig.hevc import cvar
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
    def initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth):
        from src.Lib.TLibCommon.TComRom import initMotionReferIdx as luuvc_initMotionReferIdx
        from swig.hevc import initMotionReferIdx as swig_initMotionReferIdx
        swig_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)
        luuvc_initMotionReferIdx(uiMaxCUWidth, uiMaxCUHeight, uiMaxDepth)

    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import ArrayTComMvField, ArrayUChar
    from swig.hevc import ArrayUInt, ArrayInt, ArrayBool
    from swig.hevc import ArraySaoLcuParamPtr, ArraySaoLcuParam
    from swig.hevc import TComMvField, TComCUMvField, ArrayTComCUMvField
    from src.Lib.TLibCommon.TComDataCU import TComDataCU
    def ArrayTComDataCU(size):
        return pointer([TComDataCU() for i in xrange(size)])
    from src.Lib.TLibCommon.TComYuv import TComYuv
    def ArrayTComYuv(size):
        return [TComYuv() for i in xrange(size)]
    def ArrayTDecBinCABAC(size):
        from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac
        return pointer([TDecBinCabac() for i in xrange(size)])
    def ArrayTDecSbac(size):
        from src.Lib.TLibDecoder.TDecSbac import TDecSbac
        return pointer([TDecSbac() for i in xrange(size)])

    from swig.hevc import TComSampleAdaptiveOffset

    from src.Lib.TLibCommon.TComLoopFilter import TComLoopFilter
    from src.Lib.TLibCommon.TComTrQuant import TComTrQuant
    from src.Lib.TLibCommon.TComPrediction import TComPrediction

    from src.Lib.TLibDecoder.TDecBinCabac import TDecBinCabac as TDecBinCABAC
    from src.Lib.TLibDecoder.TDecSbac import TDecSbac
    from src.Lib.TLibDecoder.TDecCavlc import TDecCavlc
    from src.Lib.TLibDecoder.TDecEntropy import TDecEntropy
    from src.Lib.TLibDecoder.TDecCu import TDecCu
    from src.Lib.TLibDecoder.TDecSlice import TDecSlice
    from src.Lib.TLibDecoder.TDecGop import TDecGop
    from src.Lib.TLibDecoder.TDecTop import TDecTop
    from src.Lib.TLibVideoIO.TVideoIOYuv import TVideoIOYuv

    from src.App.TAppDecoder.TAppDecCfg import TAppDecCfg
    from src.App.TAppDecoder.TAppDecTop import TAppDecTop
    from src.App.TAppDecoder.TAppDecoder import TAppDecoder

elif use_swig == 14:
    from ..TLibCommon import TComRom as cvar # depend on TDecCavlc
    from swig.hevc import ArrayTComInputBitstream
    from swig.hevc import VectorBool, VectorInt # depend on TComPic

    ArrayUInt = lambda size: [0 for i in xrange(size)] # TComPPS
