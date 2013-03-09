# -*- coding: utf-8 -*-
"""
    module : src/App/TAppDecoder/TAppDecCfg.py
    HM 10.0 Python Implementation
"""

import sys
import optparse

from ...Lib.TLibCommon.TypeDef import MAX_NUM_LAYER_IDS


class TAppDecCfg(object):

    def __init__(self):
        self.m_pchBitstreamFile             = ''
        self.m_pchReconFile                 = ''
        self.m_iSkipFrame                   = 0
        self.m_outputBitDepthY              = 0
        self.m_outputBitDepthC              = 0

        self.m_iMaxTemporalLayer            = -1
        self.m_decodedPictureHashSEIEnabled = 0

        self.m_targetDecLayerIdSet          = []
        self.m_respectDefDispWindow         = 0

    def parseCfg(self, argv):
        p = optparse.OptionParser()

        p.add_option('-b', '--BitstreamFile',
            action='store', type='string', dest='m_pchBitstreamFile', default='',
            help='bitstream input file name')
        p.add_option('-o', '--ReconFile',
            action='store', type='string', dest='m_pchReconFile', default='',
            help='reconstructed YUV output file name\n' +
                 'YUV writing is skipped if omitted')
        p.add_option('-s', '--SkipFrames',
            action='store', type='int', dest='m_iSkipFrame', default=0,
            help='number of frames to skip before random access')
        p.add_option('-d', '--OutputBitDepth',
            action='store', type='int', dest='m_outputBitDepthY', default=0,
            help='bit depth of YUV output luma component (default: use 0 for native depth)')
        p.add_option('-e', '--OutputBitDepthC',
            action='store', type='int', dest='m_outputBitDepthC', default=0,
            help='bit depth of YUV output chroma component (default: use 0 for native depth)')
        p.add_option('-t', '--MaxTemporalLayer',
            action='store', type='int', dest='m_iMaxTemporalLayer', default=-1,
            help='Maximum Temporal Layer to be decoded. -1 to decode all layers')
        p.add_option('--SEIDecodedPictureHash',
            action='store', type='int', dest='m_decodedPictureHashSEIEnabled', default=1,
            help='Control handling of decoded picture hash SEI messages\n' +
                 '\t1: check hash in SEI messages if available in the bitstream\n' +
                 '\t0: ignore SEI message')
        p.add_option('--SEIpictureDigest',
            action='store', type='int', dest='m_decodedPictureHashSEIEnabled', default=1,
            help='deprecated alias for SEIDecodedPictureHash')
        p.add_option('-l', '--TarDecLayerIdSetFile',
            action='store', type='string', dest='m_targetDecLayerIdSetFile', default='',
            help='targetDecLayerIdSet file name. ' +
                 'The file should include white space seperated LayerId values to be decoded. ' +
                 'Omitting the option or a value of -1 in the file decodes all layers.')
        p.add_option('-w', '--RespectDefDispWindow',
            action='store', type='int', dest='m_respectDefDispWindow', default=0,
            help='Only output content inside the default display window\n')

        opt, args = p.parse_args(argv[1:])

        for it in args:
            sys.stderr.write("Unhandled argument ignored: `%s'\n" % it)

        if not argv[1:]:
            # print help()
            return False

        # convert std::string to c string for compatability
        self.m_pchBitstreamFile             = opt.m_pchBitstreamFile
        self.m_pchReconFile                 = opt.m_pchReconFile
        self.m_iSkipFrame                   = opt.m_iSkipFrame
        self.m_outputBitDepthY              = opt.m_outputBitDepthY
        self.m_outputBitDepthC              = opt.m_outputBitDepthC
        self.m_iMaxTemporalLayer            = opt.m_iMaxTemporalLayer
        self.m_decodedPictureHashSEIEnabled = opt.m_decodedPictureHashSEIEnabled
        self.m_respectDefDispWindow         = opt.m_respectDefDispWindow

        if not self.m_pchBitstreamFile:
            sys.stderr.write("No input file specifed, aborting\n")
            return False

        if opt.m_targetDecLayerIdSetFile:
            try:
                targetDecLayerIdSetFile = open(opt.m_targetDecLayerIdSetFile, 'r')
                isLayerIdZeroIncluded = False
                for layerid in targetDecLayerIdSetFile.read().split(' '):
                    layerIdParsed = 0
                    try:
                        layerIdParsed = int(layerid)
                    except ValueError:
                        if len(self.m_targetDecLayerIdSet) == 0:
                            sys.stderr.write('No LayerId could be parsed in file %s. Decoding all LayerIds as default.\n' % opt.m_targetDecLayerIdSetFile)
                        break
                    if layerIdParsed == -1: # The file includes a -1, which means all LayerIds are to be decoded.
                        self.m_targetDecLayerIdSet = [] # Empty set means decoding all layers.
                        break
                    if layerIdParsed < 0 or layerIdParsed >= MAX_NUM_LAYER_IDS:
                        sys.stderr.write('Warning! Parsed LayerId %d is not withing allowed range [0,%d]. Ignoring this value.\n' % (layerIdParsed, MAX_NUM_LAYER_IDS-1))
                    else:
                        isLayerIdZeroIncluded = True if layerIdParsed == 0 else isLayerIdZeroIncluded
                        self.m_targetDecLayerIdSet.append(layerIdParsed)
                targetDecLayerIdSetFile.close()
                if len(self.m_targetDecLayerIdSet) > 0 and not isLayerIdZeroIncluded:
                    sys.stderr.write('TargetDecLayerIdSet must contain LayerId=0, aborting')
                    return False
            except IOError:
                sys.stderr.write('File %s could not be opened. Using all LayerIds as default.\n' % opt.m_targetDecLayerIdSetFile)

        return True
