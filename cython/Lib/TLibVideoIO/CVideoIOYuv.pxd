from libc.stdio cimport FILE

cdef class CVideoIOYuv:
    cdef FILE *m_cHandle
    cdef int   m_fileBitDepthY
    cdef int   m_fileBitDepthC
    cdef int   m_bitDepthShiftY
    cdef int   m_bitDepthShiftC
    cpdef open(self, char* pchFile, bint bWriteMode, int fileBitDepthY, int fileBitDepthC, int internalBitDepthY, int internalBitDepthC)
    cpdef close(self)
    cpdef skipFrames(self, unsigned int numFrames, unsigned int width, unsigned int height)
    cpdef bint read(self, pPicYuv, int aiPad[2])
    cpdef bint write(self, pPicYuv, int confLeft=*, int confRight=*, int confTop=*, int confBottom=*)
    cpdef bint isEof(self)
    cpdef bint isFail(self)
