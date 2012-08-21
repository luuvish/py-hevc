#!/usr/bin/env python

import os
import sys
from pygccxml import declarations
from pyplusplus import messages
from pyplusplus import module_builder
from pyplusplus import function_transformers as ft
from pyplusplus.module_builder import call_policies as cp
from input_c_string import input_c_string

ft.input_c_string = input_c_string

gccxml_executable = '/opt/local/bin/gccxml'

hm_dir = '/Users/injoh/Documents/workspace/video/hm-8.0'
hm_obj = hm_dir + '/build/linux/app'

include_dirs = [hm_dir+'/source/'+inc for inc in ['Lib', 'App/TAppDecoder', 'App/TAppEncoder']]
define_macros = ['MSYS_LINUX', '_LARGEFILE64_SOURCE', '_FILE_OFFSET_BITS=64', 'MSYS_UNIX_LARGEFILE']
extra_compile_args = ['-fPIC', '-Wall', '-Wno-sign-compare', '-O3', '-Wuninitialized']


module_name = 'hevc'
module_license = '//Boost Software License( http://boost.org/more/license_info.html )'

messages.disable( 
#   messages.W1020,
#   messages.W1021,
#   messages.W1022,
#   messages.W1023,
#   messages.W1024,
    messages.W1025, # `Py++` will generate class wrapper - class contains "xxx" - T* member variable
#   messages.W1026,
    messages.W1027, # `Py++` will generate class wrapper - class contains "xxx" - array member variable
#   messages.W1028,
#   messages.W1029,
#   messages.W1030,
#   messages.W1031
)

mb = module_builder.module_builder_t(
        files=['decmain.h', 'encmain.h', 'TAppDecTop.h', 'TAppEncTop.h'], #'TLibDecoder/NALread.h'],
        gccxml_path=gccxml_executable,
        include_paths=include_dirs,
        define_symbols=define_macros,
        cflags=' '.join(extra_compile_args))


mb.constructors().allow_implicit_conversion = False                                           
mb.BOOST_PYTHON_MAX_ARITY = 25
mb.classes().always_expose_using_scope = True

main_ns = mb.global_ns

classes = [
#   'SEI',
#   'SEIuserDataUnregistered',
#   'SEIpictureDigest',
#   'SEImessages',
#   'TComOutputBitstream',
#   'TComInputBitstream',
#   'InputNALUnit',
#   'TComSlice',
#   'TComDataCU',
#   'TComPicSym',
#   'TComPicYuv',
#   'TComPic',
#   'TComList<TComPic*>',
#   'TDecTop',
    'TAppDecCfg',
    'TAppDecTop',
    'TAppEncCfg',
    'TAppEncTop',
]

functions = [
    '::read',
]

mb.classes(lambda c: c.name in classes).include()
#for c in classes:
#    cls = mb.class_(c)
#    members = cls.decls(declarations.virtuality_type_matcher(declarations.VIRTUALITY_TYPES.PURE_VIRTUAL),
#                        decl_type=declarations.calldef.member_calldef_t,
#                        allow_empty=True)
#    members.set_virtuality(declarations.VIRTUALITY_TYPES.NOT_VIRTUAL)
#    members = cls.decls(declarations.virtuality_type_matcher(declarations.VIRTUALITY_TYPES.ALL),
#                        decl_type=declarations.calldef.member_calldef_t,
#                        allow_empty=True)
#    members.set_virtuality(declarations.VIRTUALITY_TYPES.NOT_VIRTUAL)
#    cls.constructors().exclude()


#mb.enum('::SEI::PayloadType').include()
#mb.print_declarations(mb.class_('::TComInputBitstream'))
#for decl in mb.decls('::SEI'):
#    mb.print_declarations(decl)

#x = mb.mem_fun('::TComOutputBitstream::getByteStream')
#x.call_policies = cp.return_value_policy(cp.return_pointee_value)
#x = mb.mem_fun('::TComInputBitstream::pseudoRead', arg_types=['::UInt', '::UInt &'])
#x.add_transformation(ft.output('ruiBits'))
#x = mb.mem_fun('::TComInputBitstream::read', arg_types=['::UInt', '::UInt &'])
#x.add_transformation(ft.output('ruiBits'))
#x = mb.mem_fun('::TComInputBitstream::readByte', arg_types=['::UInt &'])
#x.add_transformation(ft.output('ruiBits'))
#x = mb.mem_fun('::TComInputBitstream::extractSubstream')
#x.call_policies = cp.return_value_policy(cp.return_pointee_value)


#mb.calldef('::TDecTop::decode').add_transformation(ft.inout(0), ft.inout(1), ft.inout(2))
#mb.calldef('::TDecTop::executeDeblockAndAlf').add_transformation(ft.inout(0), ft.inout(1), ft.inout(2))

x = mb.mem_fun('::TAppDecCfg::parseCfg')
x.add_transformation(ft.input_c_buffer('argv', 'argc'))
x = mb.mem_fun('::TAppEncCfg::parseCfg')
x.add_transformation(ft.input_c_buffer('argv', 'argc'))

mb.mem_fun('::TAppEncTop::getTEncTop').exclude() # public

x = mb.free_fun('::decmain')
x.add_transformation(ft.input_c_buffer('argv', 'argc'))
x = mb.free_fun('::encmain')
x.add_transformation(ft.input_c_buffer('argv', 'argc'))

mb.decls(declarations.access_type_matcher_t('private')).exclude()
mb.decls(declarations.access_type_matcher_t('protected')).exclude()

#I can print declarations to see what is going on
#mb.print_declarations()

mb.build_code_creator(module_name=module_name)
mb.code_creator.license = module_license
mb.code_creator.user_defined_directories.append(os.path.abspath('.'))
mb.write_module(os.path.join(os.path.abspath('.'), module_name+'.pypp.cpp'))
