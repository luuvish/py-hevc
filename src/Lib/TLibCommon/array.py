# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/array.py
    HM 8.0 Python Implementation
"""

import sys

use_swig = True
if use_swig:
    sys.path.insert(0, '../../..')
    from swig.hevc import ArrayBool, ArrayChar, ArrayUChar, ArrayShort, \
                          ArrayUShort, ArrayInt, ArrayUInt, ArrayDouble, \
                          ArrayPxl, ArrayPel, ArrayTCoeff, \
                          BoolAdd, CharAdd, UCharAdd, ShortAdd, \
                          UShortAdd, IntAdd, UIntAdd, DoubleAdd, \
                          PxlAdd, PelAdd, TCoeffAdd

class array(object):

    _types = {
        'bool *': ArrayBool,
        'char *': ArrayChar,
        'uchar *': ArrayUChar,
        'short *': ArrayShort,
        'ushort *': ArrayUShort,
        'int *': ArrayInt,
        'uint *': ArrayUInt,
        'double *': ArrayDouble,
        'pxl *': ArrayPxl,
        'pel *': ArrayPel,
        'tcoeff *': ArrayTCoeff
    }

    _adds = {
        ArrayBool: BoolAdd,
        ArrayChar: CharAdd,
        ArrayUChar: UCharAdd,
        ArrayShort: ShortAdd,
        ArrayUShort: UShortAdd,
        ArrayInt: IntAdd,
        ArrayUInt: UIntAdd,
        ArrayDouble: DoubleAdd,
        ArrayPxl: PxlAdd,
        ArrayPel: PelAdd,
        ArrayTCoeff: TCoeffAdd
    }

    def __init__(self, *args, **kwargs):
        self.frompointer(*args, **kwargs)

    def __len__(self):
        return self._this.__len__() - self._base

    def __add__(self, offset):
        return array(self, base=offset)

    def __sub__(self, offset):
        return array(self, base=-offset)

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
            if isinstance(this, array):
                this, bias, base = this._this, this._bias, this._base

            if isinstance(this, list):
                self._this = this
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if type(this) in array._types.values():
                atype = type(this)
                this = this.cast()
                if kwargs['bias'] != 0:
                    this = array._adds[atype](this, kwargs['bias'])
                    bias += kwargs['bias']
                self._this = atype.frompointer(this)
                self._bias = bias
                self._base = base + kwargs['base']
                return self

            if kwargs['type'] in array._types:
                atype = array._types[kwargs['type']]
                if kwargs['bias'] != 0:
                    this = array._adds[atype](this, kwargs['bias'])
                    bias += kwargs['bias']
                self._this = atype.frompointer(this)
                self._bias = bias
                self._base = base + kwargs['base']
                return self

        self._this = list(*args)
        self._bias = kwargs['bias']
        self._base = kwargs['base']
        return self

    def cast(self):
        if type(self._this) in array._types.values():
            this = self._this.cast()
            if self._base - self._bias != 0:
                this = array._adds[type(self._this)](this, self._base - self._bias)
            return this
        return self
