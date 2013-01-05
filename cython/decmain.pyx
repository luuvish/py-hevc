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

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

NV_VERSION          = "9.1" # Current software version

__GNUC__            = 4
__GNUC_MINOR__      = 2
__GNUC_PATCHLEVEL__ = 1

NVM_COMPILEDBY      = "[GCC %d.%d.%d]" % (__GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__)
NVM_ONARCH          = "[on 64-bit] "
NVM_ONOS            = "[Mac OS X]" # "[Windows]" "[Linux]" "[Cygwin]"
NVM_BITS            = "[%d bit] " % 64 # used for checking 64-bit O/S


cdef extern from "TAppDecCfg.h":
    cdef cppclass TAppDecCfg:
        TAppDecCfg() except +
        bint parseCfg(int argc, char *argv[])


cdef extern from "TAppDecTop.h":
    cdef cppclass TAppDecTop(TAppDecCfg):
        TAppDecTop() except +
        void create()
        void destroy()
        void decode()


cdef bint g_md5_mismatch = False

cdef int main(int argc, char *argv[]):
    cdef TAppDecTop cTAppDecTop

    # print information
    sys.stdout.write("\n")
    sys.stdout.write("HM software: Decoder Version [%s]" % NV_VERSION)
    sys.stdout.write(NVM_ONOS)
    sys.stdout.write(NVM_COMPILEDBY)
    sys.stdout.write(NVM_BITS)
    sys.stdout.write("\n")

    # create application decoder class
    cTAppDecTop.create()

    # parse configuration
    if not cTAppDecTop.parseCfg(argc, argv):
        cTAppDecTop.destroy()
        return 1

    # starting time
    cdef double dResult
    cdef long lBefore = clock()

    # call decoding function
    cTAppDecTop.decode()

    if g_md5_mismatch:
        sys.stdout.write("\n\n***ERROR*** A decoding mismatch occured: signalled md5sum does not match\n")

    # ending time
    dResult = (clock()-lBefore) / CLOCKS_PER_SEC
    sys.stdout.write("\n Total Time: %12.3f sec.\n" % dResult)

    # destroy application decoder class
    cTAppDecTop.destroy()

    return EXIT_FAILURE if g_md5_mismatch else EXIT_SUCCESS


from libc.stdlib cimport malloc, free

cpdef int decmain(args):
    cdef int argc = len(args)
    cdef char **string_buf = <char**>malloc(argc * sizeof(char*))
    for i in xrange(argc):
        string_buf[i] = <char*>args[i]

    ret = main(argc, string_buf)

    free(string_buf)
    return ret
