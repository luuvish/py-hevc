#!/usr/bin/env python

import sys
import optparse

class TAppDecCfg:

    def __init__(self):
        self.m_pchBitstreamFile = ''
        self.m_pchReconFile = ''
        self.m_iSkipFrame = 0
        self.m_outputBitDepth = 0
        self.m_iMaxTemporalLayer = -1
        self.m_pictureDigestEnabled = 1

    def parseCfg(self, argv):
        p = optparse.OptionParser()

        p.add_option('-b', '--BitstreamFile', action='store', type='string', dest='bitstreamFile', default='', help='bitstream input file name')
        p.add_option('-o', '--ReconFile', action='store', type='string', dest='reconFile', default='', help='reconstructed YUV output file name\nYUV writing is skipped if omitted')
        p.add_option('-s', '--SkipFrames', action='store', type='int', dest='skipFrame', default=0, help='number of frames to skip before random access')
        p.add_option('-d', '--OutputBitDepth', action='store', type='int', dest='outputBitDepth', default=0, help='bit depth of YUV output file (use 0 for native depth)')
        p.add_option('-t', '--MaxTemporalLayer', action='store', type='int', dest='maxTemporalLayer', default=-1, help='Maximum Temporal Layer to be decoded. -1 to decode all layers')
        p.add_option('--SEIpictureDigest', action='store', type='int', dest='pictureDigestEnabled', default=1, help='Control handling of picture_digest SEI messages\n\t3: checksum\n\t2: CRC\n\t1: MD5\n\t0: ignore')

        opt, args = p.parse_args(argv[1:])

        for it in args:
            sys.stderr.write("Unhandled argument ignored: `%s'\n" % it)

        if not argv[1:]:
            # print help()
            return False

        self.m_pchBitstreamFile = opt.bitstreamFile
        self.m_pchReconFile = opt.reconFile
        self.m_iSkipFrame = opt.skipFrame
        self.m_outputBitDepth = opt.outputBitDepth
        self.m_iMaxTemporalLayer = opt.maxTemporalLayer
        self.m_pictureDigestEnabled = opt.pictureDigestEnabled

        if not self.m_pchBitstreamFile:
            sys.stderr.write("No input file specifed, aborting\n")
            return False

        return True
