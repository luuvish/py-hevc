# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/TComDump.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import ArrayInt, ArrayPel


fpTCoeff = open('./dumpTCoeff.txt', 'wt')

def dumpTCoeff(pcCU):
    uiWidth = 64
    uiHeight = 64
    poc = pcCU.getPic().getPOC()
    cuAddr = pcCU.getAddr()
    coeffY = ArrayInt.frompointer(pcCU.getCoeffY())
    coeffCb = ArrayInt.frompointer(pcCU.getCoeffCb())
    coeffCr = ArrayInt.frompointer(pcCU.getCoeffCr())
    fpTCoeff.write('POC[%d] CU[%d]\n' % (poc, cuAddr))
    for uiY in xrange(uiHeight):
        for uiX in xrange(uiWidth):
            fpTCoeff.write('%02x ' % coeffY[uiY * uiWidth + uiX])
        fpTCoeff.write('\n')
    for uiY in xrange(uiHeight/2):
        for uiX in xrange(uiWidth/2):
            fpTCoeff.write('%02x ' % coeffCb[uiY * uiWidth/2 + uiX])
        fpTCoeff.write('   ')
        for uiX in xrange(uiWidth/2):
            fpTCoeff.write('%02x ' % coeffCr[uiY * uiWidth/2 + uiX])
        fpTCoeff.write('\n')
    fpTCoeff.write('\n')

fpTComPic = open('./dumpTComPic.txt', 'wt')

def dumpTComPic(pcCU):
    uiWidth = 64
    uiHeight = 64
    poc = pcCU.getPic().getPOC()
    cuAddr = pcCU.getAddr()
    uiZOrder = pcCU.getZorderIdxInCU()
    picYuv = pcCU.getPic().getPicYuvRec()
    reconY = ArrayPel.frompointer(picYuv.getLumaAddr(cuAddr, uiZOrder))
    reconCb = ArrayPel.frompointer(picYuv.getCbAddr(cuAddr, uiZOrder))
    reconCr = ArrayPel.frompointer(picYuv.getCrAddr(cuAddr, uiZOrder))
    strideY = picYuv.getStride()
    strideC = picYuv.getCStride()
    fpTComPic.write('POC[%d] CU[%d]\n' % (poc, cuAddr))
    for uiY in xrange(uiHeight):
        for uiX in xrange(uiWidth):
            fpTComPic.write('%02x ' % reconY[uiY * strideY + uiX])
        fpTComPic.write('\n')
    for uiY in xrange(uiHeight/2):
        for uiX in xrange(uiWidth/2):
            fpTComPic.write('%02x ' % reconCb[uiY * strideC + uiX])
        fpTComPic.write('   ')
        for uiX in xrange(uiWidth/2):
            fpTComPic.write('%02x ' % reconCr[uiY * strideC + uiX])
        fpTComPic.write('\n')
    fpTComPic.write('\n')
