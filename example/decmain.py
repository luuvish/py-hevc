#!/usr/bin/env python

import sys
sys.path.insert(0, '..')

from swig.hevc import decmain as TAppDecoder


config_dir = '../../h265'
stream_dir = '../../h265'
output_dir = '.'
decode_opt = ('--OutputBitDepth=8',
			  '--BitstreamFile=%s' % (stream_dir+'/phantom.265'),
			  '--ReconFile=%s' % (output_dir+'/phantom.yuv'))

TAppDecoder(['TAppDecoder'] + list(decode_opt))
