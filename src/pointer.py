# -*- coding: utf-8 -*-
"""
    module : src/pointer.py
    HM 10.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import ArrayBool, ArrayChar, ArrayUChar, ArrayShort, \
                          ArrayUShort, ArrayInt, ArrayUInt, ArrayDouble, \
                          ArrayPxl, ArrayPel, ArrayTCoeff
    from swig.hevc import BoolAdd, CharAdd, UCharAdd, ShortAdd, \
                          UShortAdd, IntAdd, UIntAdd, DoubleAdd, \
                          PxlAdd, PelAdd, TCoeffAdd
    from swig.hevc import ArrayTDecSbac, ArrayTDecBinCABAC, \
                          ArrayTComInputBitstream, ArrayTComDataCU, \
                          ArrayTComMvField, ArrayTComMv, \
                          ArraySaoLcuParamPtr, ArraySaoLcuParam

class pointer(object):

    _prim = {
        'bool *'  : ArrayBool,
        'char *'  : ArrayChar,
        'uchar *' : ArrayUChar,
        'short *' : ArrayShort,
        'ushort *': ArrayUShort,
        'int *'   : ArrayInt,
        'uint *'  : ArrayUInt,
        'double *': ArrayDouble,
        'pxl *'   : ArrayPxl,
        'pel *'   : ArrayPel,
        'tcoeff *': ArrayTCoeff
    }

    _bias = {
        ArrayBool  : BoolAdd,
        ArrayChar  : CharAdd,
        ArrayUChar : UCharAdd,
        ArrayShort : ShortAdd,
        ArrayUShort: UShortAdd,
        ArrayInt   : IntAdd,
        ArrayUInt  : UIntAdd,
        ArrayDouble: DoubleAdd,
        ArrayPxl   : PxlAdd,
        ArrayPel   : PelAdd,
        ArrayTCoeff: TCoeffAdd
    }

    _swig = {
        'TDecSbac *'           : ArrayTDecSbac,
        'TDecBinCabac *'       : ArrayTDecBinCABAC,
        'TComInputBitstream **': ArrayTComInputBitstream,
        'TComDataCU *'         : ArrayTComDataCU,
        'TComMvField *'        : ArrayTComMvField,
        'TComMv *'             : ArrayTComMv,
        'SaoLcuParam **'       : ArraySaoLcuParamPtr,
        'SaoLcuParam *'        : ArraySaoLcuParam
    }

    def __init__(self, *args, **kwargs):
        self.frompointer(*args, **kwargs)

    def __len__(self):
        return self._this.__len__() - self._base

    def __add__(self, offset):
        return pointer(self, base=offset)

    def __sub__(self, offset):
        return pointer(self, base=-offset)

    def __iadd__(self, offset):
        self._base += offset
        return self

    def __isub__(self, offset):
        self._base -= offset
        return self

    def __getitem__(self, index):
        return self._this.__getitem__(self._base - self._bias + index)

    def __setitem__(self, index, item):
        return self._this.__setitem__(self._base - self._bias + index, item)

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            return self.cast()
        else:
            return self.frompointer(*args, **kwargs)

    def frompointer(self, *args, **kwargs):
        if 'type' not in kwargs:
            kwargs['type'] = None
        if 'bias' not in kwargs:
            kwargs['bias'] = 0
        if 'base' not in kwargs:
            kwargs['base'] = 0

        if len(args) == 1:

            this, bias, base = args[0], 0, 0
            if isinstance(this, pointer):
                this, bias, base = this._this, this._bias, this._base

            if isinstance(this, list):
                self._this = this
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if isinstance(this, tuple):
                self._this = this
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if isinstance(this, str):
                self._this = this
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if type(this) in pointer._prim.values():
                atype = type(this)
                this = this.cast()
                if kwargs['bias'] != 0:
                    this = pointer._bias[atype](this, kwargs['bias'])
                    bias += kwargs['bias']
                self._this = atype.frompointer(this)
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if type(this) in pointer._swig.values():
                self._this = this
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if kwargs['type'] in pointer._prim:
                atype = pointer._prim[kwargs['type']]
                if kwargs['bias'] != 0:
                    this = pointer._bias[atype](this, kwargs['bias'])
                    bias += kwargs['bias']
                self._this = atype.frompointer(this)
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if kwargs['type'] in pointer._swig:
                atype = pointer._swig[kwargs['type']]
                self._this = atype.frompointer(this)
                self._bias = bias
                self._base = base + kwargs['base']
                return self

        self._this = list(*args)
        self._bias = kwargs['bias']
        self._base = kwargs['base']
        return self

    def cast(self):
        if type(self._this) in pointer._prim.values():
            this = self._this.cast()
            if self._base - self._bias != 0:
                this = pointer._bias[type(self._this)](this, self._base - self._bias)
            return this

        if type(self._this) in pointer._swig.values():
            this = self._this.cast()
            return this

        return self
