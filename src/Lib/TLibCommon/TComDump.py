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
    cuAddr = pcCU.getAddr()
    coeffY = ArrayInt.frompointer(pcCU.getCoeffY())
    coeffCb = ArrayInt.frompointer(pcCU.getCoeffCb())
    coeffCr = ArrayInt.frompointer(pcCU.getCoeffCr())
    fpTCoeff.write('CU[%d]\n' % cuAddr)
    for uiY in range(uiHeight):
        for uiX in range(uiWidth):
            fpTCoeff.write('%2x ' % coeffY[uiY * uiWidth + uiX])
        fpTCoeff.write('\n')
    for uiY in range(uiHeight/2):
        for uiX in range(uiWidth/2):
            fpTCoeff.write('%2x ' % coeffCb[uiY * uiWidth/2 + uiX])
        fpTCoeff.write('   ')
        for uiX in range(uiWidth/2):
            fpTCoeff.write('%2x ' % coeffCr[uiY * uiWidth/2 + uiX])
        fpTCoeff.write('\n')
    fpTCoeff.write('\n')

fpTComPic = open('./dumpTComPic.txt', 'wt')

def dumpTComPic(pcCU):
    uiWidth = 64
    uiHeight = 64
    cuAddr = pcCU.getAddr()
    uiZOrder = pcCU.getZorderIdxInCU()
    picYuv = pcCU.getPic().getPicYuvRec()
    reconY = ArrayPel.frompointer(picYuv.getLumaAddr(cuAddr, uiZOrder))
    reconCb = ArrayPel.frompointer(picYuv.getCbAddr(cuAddr, uiZOrder))
    reconCr = ArrayPel.frompointer(picYuv.getCrAddr(cuAddr, uiZOrder))
    strideY = picYuv.getStride()
    strideC = picYuv.getCStride()
    fpTComPic.write('CU[%d]\n' % cuAddr)
    for uiY in range(uiHeight):
        for uiX in range(uiWidth):
            fpTComPic.write('%2x ' % reconY[uiY * strideY + uiX])
        fpTComPic.write('\n')
    for uiY in range(uiHeight/2):
        for uiX in range(uiWidth/2):
            fpTComPic.write('%2x ' % reconCb[uiY * strideC + uiX])
        fpTComPic.write('   ')
        for uiX in range(uiWidth/2):
            fpTComPic.write('%2x ' % reconCr[uiY * strideC + uiX])
        fpTComPic.write('\n')
    fpTComPic.write('\n')
