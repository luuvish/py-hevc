#!/usr/bin/env python

from distutils.core import setup, Extension

hm_dir = '../hm-8.0'
hm_obj = hm_dir + '/build/linux/app'

include_dirs = [hm_dir+'/source/'+inc for inc in ['Lib', 'App/TAppDecoder', 'App/TAppEncoder']]
define_macros = [('MSYS_LINUX',1), ('_LARGEFILE64_SOURCE',1), ('_FILE_OFFSET_BITS',64), ('MSYS_UNIX_LARGEFILE',1)]

library_dirs  = [hm_dir+'/lib']
libraries = ['dl', 'pthread', 'TLibCommonStatic', 'TLibVideoIOStatic',
             'TLibDecoderStatic', 'TLibEncoderStatic', 'TAppCommonStatic']
extra_objects = [hm_obj+'/TAppDecoder/objects/'+obj+'.r.o' for obj in ['TAppDecCfg', 'TAppDecTop']] + \
                [hm_obj+'/TAppEncoder/objects/'+obj+'.r.o' for obj in ['TAppEncCfg', 'TAppEncTop']]

extra_compile_args = ['-fPIC', '-Wall', '-Wno-sign-compare', '-O3', '-Wuninitialized']
extra_link_args = ['-Wall']

setup(name = 'hevc',
      version = '0.8.0',
      py_modules = ['hevc.py'],
      ext_modules = [
        Extension('_hevc',
                  sources = ['hevc.i', 'decmain.cpp', 'encmain.cpp'],
                  include_dirs = include_dirs,
                  define_macros = define_macros,
                  library_dirs = library_dirs,
                  libraries = libraries,
                  extra_objects = extra_objects,
                  extra_compile_args = extra_compile_args,
                  extra_link_args = extra_link_args,
                  swig_opts = ['-c++'] + ['-I'+inc for inc in include_dirs]
        )
      ]
)
