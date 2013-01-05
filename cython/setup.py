#!/usr/bin/env python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

hm_dir = '../hm-9.1'
hm_obj = hm_dir + '/build/linux/app'

include_dirs = [hm_dir+'/source/'+inc for inc in ['Lib', 'App/TAppDecoder', 'App/TAppEncoder']]
define_macros = [
    ('MSYS_LINUX',1),
    ('_LARGEFILE64_SOURCE',1),
    ('_FILE_OFFSET_BITS',64),
    ('MSYS_UNIX_LARGEFILE',1)
]

library_dirs  = [hm_dir+'/lib']
libraries = [
    'dl', 'pthread',
    'TLibCommonStatic', 'TLibVideoIOStatic',
    'TLibDecoderStatic', 'TLibEncoderStatic',
    'TAppCommonStatic'
]

extra_objects = [hm_obj+'/TAppDecoder/objects/'+obj+'.r.o' for obj in ['TAppDecCfg', 'TAppDecTop', 'decmain']] + \
                [hm_obj+'/TAppEncoder/objects/'+obj+'.r.o' for obj in ['TAppEncCfg', 'TAppEncTop', 'encmain']]

extra_compile_args = ['-fPIC', '-Wall', '-Wno-sign-compare', '-O3', '-Wuninitialized']
extra_link_args = ['-Wall']

setup(
    name='py-hevc',
    version='0.9.1',
    cmdclass={'build_ext': build_ext},
    ext_modules=cythonize([
        Extension(
            'App/TAppDecoder/decmain',
            sources=['App/TAppDecoder/decmain.pyx'],
            include_dirs=include_dirs,
            define_macros=define_macros,
            library_dirs=library_dirs,
            libraries=libraries,
            extra_objects=extra_objects,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
            language='c++'
        ),
        Extension(
            'App/TAppEncoder/encmain',
            sources=['App/TAppEncoder/encmain.pyx'],
            include_dirs=include_dirs,
            define_macros=define_macros,
            library_dirs=library_dirs,
            libraries=libraries,
            extra_objects=extra_objects,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
            language='c++'
        )
    ])
)
