# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/trace.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar

from .pointer import pointer

from .TComRom import g_auiRasterToZscan

use_trace = False


def trace(enable, init=None, wrapper=None, before=None, after=None):
    if enable:
        if init:
            init()

        def trace_func(func):
            if wrapper:
                def func_hook(*args, **kwargs):
                    return wrapper(func)(*args, **kwargs)
            else:
                def func_hook(*args, **kwargs):
                    if before:
                        before(*args, **kwargs)
                    ret = func(*args, **kwargs)
                    if after:
                        after(*args, **kwargs)
                    return ret
            return func_hook
        return trace_func
    else:
        def trace_none(func):
            return func
        return trace_none


g_hTrace = None
g_nSymbolCounter = 0

def initCavlc():
    global g_hTrace
    global g_nSymbolCounter
    if not g_hTrace:
        g_hTrace = open('trace_dec.txt', 'wt')
        g_nSymbolCounter = 0

def traceSPSHeader(pSPS):
    g_hTrace.write("=========== Sequence Parameter Set ID: %d ===========\n" % pSPS.getSPSId())

def tracePPSHeader(pPPS):
    g_hTrace.write("=========== Picture Parameter Set ID: %d ===========\n" % pPPS.getPPSId())

def traceSliceHeader(pSlice):
    g_hTrace.write("=========== Slice ===========\n")

def traceReadCode(func):
    def wrap(self, length, pSymbolName=''):
        rValue = func(self, length)
        if pSymbolName:
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_hTrace.write("%-40s u(%d) : %d\n" % (pSymbolName, length, rValue))
            g_hTrace.flush()
            g_nSymbolCounter += 1
        return rValue
    return wrap

def traceReadUvlc(func):
    def wrap(self, pSymbolName=''):
        rValue = func(self)
        if pSymbolName:
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_hTrace.write("%-40s u(v) : %d\n" % (pSymbolName, rValue))
            g_hTrace.flush()
            g_nSymbolCounter += 1
        return rValue
    return wrap

def traceReadSvlc(func):
    def wrap(self, pSymbolName=''):
        rValue = func(self)
        if pSymbolName:
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_hTrace.write("%-40s s(v) : %d\n" % (pSymbolName, rValue))
            g_hTrace.flush()
            g_nSymbolCounter += 1
        return rValue
    return wrap

def traceReadFlag(func):
    def wrap(self, pSymbolName=''):
        rValue = func(self)
        if pSymbolName:
            global g_nSymbolCounter
            g_hTrace.write("%8d  " % g_nSymbolCounter)
            g_hTrace.write("%-40s u(1) : %d\n" % (pSymbolName, rValue))
            g_hTrace.flush()
            g_nSymbolCounter += 1
        return rValue
    return wrap

COUNTER_START = 1
COUNTER_END   = 0 #( UInt64(1) << 63 )

def DTRACE_CABAC_F(x):
    g_hTrace.write("%f" % x)
    g_hTrace.flush()
def DTRACE_CABAC_V(x):
    g_hTrace.write("%d" % x)
    g_hTrace.flush()
def DTRACE_CABAC_VL(x):
    g_hTrace.write("%d" % x)
    g_hTrace.flush()
def DTRACE_CABAC_T(x):
    g_hTrace.write("%s" % x)
    g_hTrace.flush()
def DTRACE_CABAC_X(x):
    g_hTrace.write("%x" % x)
    g_hTrace.flush()
def DTRACE_CABAC_R(x, y):
    g_hTrace.write(x % y)
    g_hTrace.flush()
def DTRACE_CABAC_N():
    g_hTrace.write("\n")
    g_hTrace.flush()


fpCU = None

use_trace_cu_info = True
use_trace_cu_tcoeff = False
use_trace_cu_recon = False

def initCU():
    global fpCU
    fpCU = open('dumpCU.txt', 'wt')

def dumpCU(pcCU):
    width, height = cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight

    poc = pcCU.getPic().getPOC()
    cua = pcCU.getAddr()

    fpCU.write('POC[%d] CUA[%d]\n' % (poc, cua))
    fpCU.write('\n')

    if use_trace_cu_info:
        fpCU.write('depth\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                fpCU.write('%1x' % pcCU.getDepth(g_auiRasterToZscan[y * width/4 + x]))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('transquant_bypass\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                transquant_bypass = pcCU.getCUTransquantBypass(g_auiRasterToZscan[y * width/4 + x])
                fpCU.write('%c' % ('T' if transquant_bypass else 'F'))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('skip_flag\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                skip_flag = pcCU.getSkipFlag(g_auiRasterToZscan[y * width/4 + x])
                fpCU.write('%c' % ('T' if skip_flag else 'F'))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('pred_mode\n')
        pred_mode_name = ('INTER', 'INTRA', ' NONE')
        for y in xrange(height/4):
            for x in xrange(width/4):
                pred_mode = pcCU.getPredictionMode(g_auiRasterToZscan[y * width/4 + x])
                fpCU.write('%s ' % pred_mode_name[pred_mode if pred_mode < 2 else 2])
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('part_size\n')
        part_size_name = ('2Nx2N', '2NxN ', ' Nx2N', ' NxN ',
                          '2NxnU', '2NxnD', 'nLx2N', 'nRx2N', ' NONE')
        for y in xrange(height/4):
            for x in xrange(width/4):
                part_size = pcCU.getPartitionSize(g_auiRasterToZscan[y * width/4 + x])
                fpCU.write('%s ' % part_size_name[part_size if part_size < 8 else 8])
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('width\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                fpCU.write('%2x ' % pcCU.getWidth(g_auiRasterToZscan[y * width/4 + x]))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('height\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                fpCU.write('%2x ' % pcCU.getHeight(g_auiRasterToZscan[y * width/4 + x]))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('transform_idx\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                fpCU.write('%2x ' % pcCU.getTransformIdx(g_auiRasterToZscan[y * width/4 + x]))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('ipcm_flag\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                ipcm_flag = pcCU.getIPCMFlag(g_auiRasterToZscan[y * width/4 + x])
                fpCU.write('%c' % ('T' if ipcm_flag else 'F'))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('intra_dir_l\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                fpCU.write('%2x ' % pcCU.getLumaIntraDir(g_auiRasterToZscan[y * width/4 + x]))
            fpCU.write('\n')
        fpCU.write('\n')

        fpCU.write('intra_dir_c\n')
        for y in xrange(height/4):
            for x in xrange(width/4):
                fpCU.write('%2x ' % pcCU.getChromaIntraDir(g_auiRasterToZscan[y * width/4 + x]))
            fpCU.write('\n')
        fpCU.write('\n')

    if use_trace_cu_tcoeff:
        fpCU.write('tcoeff\n')
        tc = (pointer(pcCU.getCoeffY(), type='int *'),
              pointer(pcCU.getCoeffCb(), type='int *'),
              pointer(pcCU.getCoeffCr(), type='int *'))
        for y in xrange(height):
            for x in xrange(width):
                fpCU.write('%-03x ' % tc[0][y * width + x])
            fpCU.write('\n')
        for y in xrange(height/2):
            for x in xrange(width/2):
                fpCU.write('%-03x ' % tc[1][y * width/2 + x])
            fpCU.write('   ')
            for x in xrange(width/2):
                fpCU.write('%-03x ' % tc[2][y * width/2 + x])
            fpCU.write('\n')
        fpCU.write('\n')

    if use_trace_cu_recon:
        fpCU.write('reconst\n')
        zorder = pcCU.getZorderIdxInCU()
        pic = pcCU.getPic().getPicYuvRec()
        yuv = (pointer(pic.getLumaAddr(cua, zorder), type='short *'),
               pointer(pic.getCbAddr(cua, zorder), type='short *'),
               pointer(pic.getCrAddr(cua, zorder), type='short *'))
        stride = (pic.getStride(), pic.getCStride())
        for y in xrange(height):
            for x in xrange(width):
                fpCU.write('%02x ' % yuv[0][y * stride[0] + x])
            fpCU.write('\n')
        for y in xrange(height/2):
            for x in xrange(width/2):
                fpCU.write('%02x ' % yuv[1][y * stride[1] + x])
            fpCU.write('   ')
            for x in xrange(width/2):
                fpCU.write('%02x ' % yuv[2][y * stride[1] + x])
            fpCU.write('\n')
        fpCU.write('\n')
