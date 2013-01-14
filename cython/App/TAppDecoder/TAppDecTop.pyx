# distutils: language = c++
# distutils: include_dirs = ../hm-9.1/source/App/TAppDecoder
# distutils: define_macros = MSYS_LINUX=1 _LARGEFILE64_SOURCE=1 _FILE_OFFSET_BITS=64 MSYS_UNIX_LARGEFILE=1
# distutils: library_dirs = ../hm-9.1/lib
# distutils: libraries = dl pthread TLibCommonStatic TLibVideoIOStatic TLibDecoderStatic TLibEncoderStatic TAppCommonStatic
# distutils: extra_objects = ../hm-9.1/build/linux/app/TAppDecoder/objects/TAppDecCfg.r.o ../hm-9.1/build/linux/app/TAppDecoder/objects/TAppDecTop.r.o ../hm-9.1/build/linux/app/TAppDecoder/objects/decmain.r.o
# distutils: extra_compile_args = -fPIC -Wall -Wno-sign-compare -O3 -Wuninitialized
# distutils: extra_link_args = -Wall


import sys
from time import clock
CLOCKS_PER_SEC = 1


cdef extern from "TLibVideoIO/TVideoIOYuv.h":
    cdef cppclass TVideoIOYuv:
        TVideoIOYuv() except +
        void open(char* pchFile, bint bWriteMode, int fileBitDepthY, int fileBitDepthC, int internalBitDepthY, int internalBitDepthC)
        void close()
        void skipFrame(unsigned int numFrames, unsigned int width, unsigned int height)
        bint read(TComPicYuv* pPicYuv, int aiPad[2])
        bint write(TComPicYuv* pPicYuv, int cropLeft=0, int cropRight=0, int cropTop=0, int cropBottom=0)
        bint isEof()
        bint isFail()

cdef extern from "TLibCommon/TComList.h":
    cdef cppclass TComList[C]:
        #ctypedef list[C].iterator TComIterator
        #TComList& operator+= (TComList& rcTComList)
        C popBack()
        C popFront()
        void pushBack(C& rcT)
        void pushFront(C& rcT)
        #TComIterator find(C& rcT)

cdef extern from "TLibCommon/TComPicYuv.h":
    cdef cppclass TComPicYuv:
        TComPicYuv() except +
        void create(int iPicWidth, int iPicHeight, unsigned int uiMaxCUWidth, unsigned int uiMaxCUHeight, unsigned int uiMaxCUDepth)
        void destroy()
        void createLuma(int iPicWidth, int iPicHeight, unsigned int uiMaxCUWidth, unsigned int uiMaxCUHeight, unsigned int uhMaxCUDepth)
        void destroy()
        int getWidth()
        int getHeight()
        int getStride()
        int getCStride()
        int getLumaMargin()
        int getChromaMargin()
        short* getBufY()
        short* getBufU()
        short* getBufV()
        short* getLumaAddr()
        short* getCbAddr()
        short* getCrAddr()
        short* getLumaAddr(int iCuAddr)
        short* getCrAddr(int iCuAddr)
        short* getCbAddr(int iCuAddr)
        short* getLumaAddr(int iCuAddr)
        short* getCbAddr(int iCuAddr)
        short* getCrAddr(int iCuAddr)
        void copyToPic(TComPicYuv* pcPicYuvDst)
        void copyToPicLuma(TComPicYuv* pcPicYuvDst)
        void copyToPicCb(TComPicYuv* pcPicYuvDst)
        void copyToPicCr(TComPicYuv* pcPicYuvDst)
        void extendPicBorder()
        void dump(char* pFileName, bint bAdd=False)
        void setBorderExtension(bint b)

cdef extern from "TLibDecoder/TDecTop.h":
    cdef cppclass TDecTop:
        TDecTop() except +
        void create()
        void destroy()
        void setDecodedPictureHashSEIEnabled(int enabled)
        void init()
        bint decode(InputNALUnit &nalu, int& iSkipFrame, int& iPOCLastDisplay)
        void deletePicBuffer()
        void executeLoopFilters(int& poc, TComList[TComPic*]*& rpcListPic, int& iSkipFrame, int& iPocLastDisplay)

cdef extern from "TLibDecoder/NALread.h":
    cdef cppclass InputNALUnit:
        InputNALUnit() except +

cdef extern from "TLibCommon/TComPic.h":
    cdef cppclass TComPic:
        TComPic() except +

from TAppDecCfg cimport TAppDecCfg

cdef class TAppDecTop(TAppDecCfg):
    # class interface
    cdef TDecTop m_cTDecTop
    cdef TVideoIOYuv m_cTVideoIOYuvReconFile

    # for output control
    cdef bint m_abDecFlag[MAX_GOP]
    cdef int m_iPOCLastDisplay

    def __cinit__(self):
        self.m_iPOCLastDisplay = -MAX_INT
        for i in xrange(MAX_GOP):
            self.m_abDecFlag[i] = 0

    def __dealloc__(self):
        pass

    def __init__(self):
        pass

    cdef void create(self):
        pass

    cdef void destroy(self):
        if self.m_pchBitstreamFile:
            self.m_pchBitstreamFile = NULL
        if self.m_pchReconFile:
            self.m_pchReconFile = NULL

    cdef void decode(self):
        cdef int poc
        cdef TComList[TComPic*]* pcListPic = NULL

    cdef void xCreateDecLib(self):
        self.m_cTDecTop.create()

    cdef void xDestroyDecLib(self):
        if self.m_pchReconFile:
            self.m_cTVideoIOYuvReconFile.close()

        self.m_cTDecTop.destroy()

    cdef void xInitDecLib(self):
        self.m_cTDecTop.init()
        self.m_cTDecTop.setDecodedPictureHashSEIEnabled(self.m_decodedPictureHashSEIEnabled)

    cdef void xWriteOutput(self, TComList[TComPic*]* pcListPic, uint iId): pass
    cdef void xFlushOutput(self, TComList[TComPic*]* pcListPic): pass
    cdef bint isNaluWithinTargetDecLayerIdSet(self, InputNALUnit* nalu): pass
