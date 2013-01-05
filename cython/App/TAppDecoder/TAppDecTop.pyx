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

cdef extern from "<list>" namespace "std":
    cdef cppclass list[T]:
        list()

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

cdef extern from "TAppDecCfg.h":
    cdef cppclass TAppDecCfg:
        TAppDecCfg() except +
        bint parseCfg(int argc, char *argv[])

cdef extern from "NALread.h":
    cdef cppclass InputNALUnit:
        InputNALUnit() except +

cdef extern from "TComPic.h":
    cdef cppclass TComPic:
        TComPic() except +


cdef class TAppDecTop(TAppDecCfg):
    # class interface
    cdef TDecTop m_cTDecTop
    cdef TVideoIOYuv m_cTVideoIOYuvReconFile

    # for output control
    cdef bint m_abDecFlag
    cdef int m_iPOCLastDisplay

    def __cinit__(self): pass
    def __init__(self): pass

    cpdef create(self): pass
    cpdef destroy(self): pass
    cpdef decode(self): pass

    cdef void xCreateDecLib(self): pass
    cdef void xDestroyDecLib(self): pass
    cdef void xInitDecLib(self): pass

    cdef void xWriteOutput(self, TComList[TComPic*]* pcListPic, unsigned int iId): pass
    cdef void xFlushOutput(self, TComList[TComPic*]* pcListPic): pass
    cdef bint isNaluWithinTargetDecLayerIdSet(self, InputNALUnit* nalu): pass
