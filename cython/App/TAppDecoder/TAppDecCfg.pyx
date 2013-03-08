# distutils: language = c++
# distutils: include_dirs = ../hm-9.1/source/App/TAppDecoder
# distutils: define_macros = MSYS_LINUX=1 _LARGEFILE64_SOURCE=1 _FILE_OFFSET_BITS=64 MSYS_UNIX_LARGEFILE=1
# distutils: library_dirs = ../hm-9.1/lib
# distutils: libraries = dl pthread TLibCommonStatic TLibVideoIOStatic TLibDecoderStatic TLibEncoderStatic TAppCommonStatic
# distutils: extra_objects = ../hm-9.1/build/linux/app/TAppDecoder/objects/TAppDecCfg.r.o ../hm-9.1/build/linux/app/TAppDecoder/objects/TAppDecTop.r.o ../hm-9.1/build/linux/app/TAppDecoder/objects/decmain.r.o
# distutils: extra_compile_args = -fPIC -Wall -Wno-sign-compare -O3 -Wuninitialized
# distutils: extra_link_args = -Wall


import sys
import optparse

from libc.stdio cimport FILE, stderr, fopen, fclose, feof, fscanf, fprintf
from libcpp.vector cimport vector


MAX_NUM_LAYER_IDS = 64


cdef class TAppDecCfg:

    def __cinit__(self):
        self.m_pchBitstreamFile             = NULL
        self.m_pchReconFile                 = NULL
        self.m_iSkipFrame                   = 0
        self.m_outputBitDepthY              = 0
        self.m_outputBitDepthC              = 0
        self.m_iMaxTemporalLayer            = -1
        self.m_decodedPictureHashSEIEnabled = 0
        self.m_respectDefDispWindow         = 0

    def __dealloc__(self):
        pass

    cdef bint parseCfg(self, int argc, char* argv[]):
        cdef FILE* targetDecLayerIdSetFile
        cdef bint isLayerIdZeroIncluded
        cdef int layerIdParsed

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
        p.add_option('--SEIpictureDigest',
            action='store', type='int', dest='m_decodedPictureHashSEIEnabled', default=1,
            help='Control handling of decoded picture hash SEI messages\n' +
                 '\t1: check hash in SEI messages if available in the bitstream\n' +
                 '\t0: ignore SEI message')
        p.add_option('-l', '--TarDecLayerIdSetFile',
            action='store', type='string', dest='m_targetDecLayerIdSetFile', default='',
            help='targetDecLayerIdSet file name. ' +
                 'The file should include white space separated LayerId values to be decoded. ' +
                 'Omitting the option or a value of -1 in the file decodes all layers.')
        p.add_option('-w', '--RespectDefDispWindow',
            action='store', type='int', dest='m_respectDefDispWindow', default=0,
            help='Only output content inside the default display window\n')

        args = [argv[i] for i in xrange(argc)]
        opt, args = p.parse_args(args)

        for it in args:
            fprintf(stderr, "Unhandled argument ignored: `%s'\n", <char*>it)

        if argc == 1:
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
            fprintf(stderr, "No input file specifed, aborting\n")
            return False

        if opt.m_targetDecLayerIdSetFile:
            targetDecLayerIdSetFile = fopen(opt.m_targetDecLayerIdSetFile, 'r')
            if targetDecLayerIdSetFile:
                isLayerIdZeroIncluded = False
                while not feof(targetDecLayerIdSetFile):
                    layerIdParsed = 0
                    if fscanf(targetDecLayerIdSetFile, "%d", &layerIdParsed) != 1:
                        if self.m_targetDecLayerIdSet.size() == 0:
                            fprintf(stderr, "No LayerId could be parsed in file %s. Decoding all LayerIds as default.\n", <char*>opt.m_targetDecLayerIdSetFile)
                        break
                    if layerIdParsed == -1: # The file includes a -1, which means all LayerIds are to be decoded.
                        self.m_targetDecLayerIdSet.clear() # Empty set means decoding all layers.
                        break
                    if layerIdParsed < 0 or layerIdParsed >= MAX_NUM_LAYER_IDS:
                        fprintf(stderr, "Warning! Parsed LayerId %d is not withing allowed range [0,%d]. Ignoring this value.\n", layerIdParsed, <int>(MAX_NUM_LAYER_IDS-1))
                    else:
                        isLayerIdZeroIncluded = True if layerIdParsed == 0 else isLayerIdZeroIncluded
                        self.m_targetDecLayerIdSet.push_back(layerIdParsed)
                fclose(targetDecLayerIdSetFile)
                if self.m_targetDecLayerIdSet.size() > 0 and not isLayerIdZeroIncluded:
                    fprintf(stderr, "TargetDecLayerIdSet must contain LayerId=0, aborting")
                    return False
            else:
                fprintf(stderr, "File %s could not be opened. Using all LayerIds as default.\n", <char*>opt.m_targetDecLayerIdSetFile)

        return True
