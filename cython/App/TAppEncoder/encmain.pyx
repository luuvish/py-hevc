# distutils: language = c++
# distutils: include_dirs = ../hm-9.1/source/App/TAppEncoder
# distutils: define_macros = MSYS_LINUX=1 _LARGEFILE64_SOURCE=1 _FILE_OFFSET_BITS=64 MSYS_UNIX_LARGEFILE=1
# distutils: library_dirs = ../hm-9.1/lib
# distutils: libraries = dl pthread TLibCommonStatic TLibVideoIOStatic TLibDecoderStatic TLibEncoderStatic TAppCommonStatic
# distutils: extra_objects = ../hm-9.1/build/linux/app/TAppEncoder/objects/TAppEncCfg.r.o ../hm-9.1/build/linux/app/TAppEncoder/objects/TAppEncTop.r.o ../hm-9.1/build/linux/app/TAppEncoder/objects/encmain.r.o
# distutils: extra_compile_args = -fPIC -Wall -Wno-sign-compare -O3 -Wuninitialized
# distutils: extra_link_args = -Wall


import sys
from time import clock
CLOCKS_PER_SEC = 1

NV_VERSION          = "9.1" # Current software version

__GNUC__            = 4
__GNUC_MINOR__      = 2
__GNUC_PATCHLEVEL__ = 1

NVM_COMPILEDBY      = "[GCC %d.%d.%d]" % (__GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__)
NVM_ONARCH          = "[on 64-bit] "
NVM_ONOS            = "[Mac OS X]" # "[Windows]" "[Linux]" "[Cygwin]"
NVM_BITS            = "[%d bit] " % 64 # used for checking 64-bit O/S


cdef extern from "TAppEncCfg.h":
    cdef cppclass TAppEncCfg:
        TAppEncCfg() except +
        bint parseCfg(int argc, char *argv[])


cdef extern from "TAppEncTop.h":
    cdef cppclass TAppEncTop(TAppEncCfg):
        TAppEncTop() except +
        void create()
        void destroy()
        void encode()


cdef int main(int argc, char *argv[]):
    cdef TAppEncTop cTAppEncTop

    # print information
    sys.stdout.write("\n")
    sys.stdout.write("HM software: Encoder Version [%s]" % NV_VERSION)
    sys.stdout.write(NVM_ONOS)
    sys.stdout.write(NVM_COMPILEDBY)
    sys.stdout.write(NVM_BITS)
    sys.stdout.write("\n")

    # create application encoder class
    cTAppEncTop.create()

    # parse configuration
    try:
        if not cTAppEncTop.parseCfg(argc, argv):
            cTAppEncTop.destroy()
            return 1
    except ValueError as e:
        sys.stderr.write("Error parsing option \"%s\" with argument \"%s\".\n" % (e.arg, e.val))
        return 1

    # starting time
    cdef double dResult
    cdef long lBefore = clock()

    # call encoding function
    cTAppEncTop.encode()

    # ending time
    dResult = (clock()-lBefore) / CLOCKS_PER_SEC
    sys.stdout.write("\n Total Time: %12.3f sec.\n" % dResult)

    # destroy application encoder class
    cTAppEncTop.destroy()

    return 0


from libc.stdlib cimport malloc, free

cpdef int encmain(args):
    cdef int argc = len(args)
    cdef char **string_buf = <char**>malloc(argc * sizeof(char*))
    for i in xrange(argc):
        string_buf[i] = <char*>args[i]

    ret = main(argc, string_buf)

    free(string_buf)
    return ret
