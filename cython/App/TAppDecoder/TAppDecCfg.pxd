from libcpp.vector cimport vector

cdef class TAppDecCfg:
    cdef char*       m_pchBitstreamFile
    cdef char*       m_pchReconFile
    cdef int         m_iSkipFrame
    cdef int         m_outputBitDepthY
    cdef int         m_outputBitDepthC

    cdef int         m_iMaxTemporalLayer
    cdef int         m_decodedPictureHashSEIEnabled

    cdef vector[int] m_targetDecLayerIdSet
    cdef int         m_respectDefDispWindow

    cdef bint parseCfg(self, int argc, char* argv[])