# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComDump.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import cvar
    from swig.hevc import ArrayUInt, ArrayInt, ArrayPel

g_auiRasterToZscan = ArrayUInt.frompointer(cvar.g_auiRasterToZscan)


fpCU = open('dumpCU.txt', 'wt')

def dumpCU(pcCU):
    width, height = cvar.g_uiMaxCUWidth, cvar.g_uiMaxCUHeight

    poc = pcCU.getPic().getPOC()
    cua = pcCU.getAddr()

    fpCU.write('POC[%d] CUA[%d]\n' % (poc, cua))
    fpCU.write('\n')

    if True:
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

    if True:
        fpCU.write('tcoeff\n')
        tc = (ArrayInt.frompointer(pcCU.getCoeffY()),
              ArrayInt.frompointer(pcCU.getCoeffCb()),
              ArrayInt.frompointer(pcCU.getCoeffCr()))
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

    if True:
        fpCU.write('reconst\n')
        zorder = pcCU.getZorderIdxInCU()
        pic = pcCU.getPic().getPicYuvRec()
        yuv = (ArrayPel.frompointer(pic.getLumaAddr(cua, zorder)),
               ArrayPel.frompointer(pic.getCbAddr(cua, zorder)),
               ArrayPel.frompointer(pic.getCrAddr(cua, zorder)))
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
