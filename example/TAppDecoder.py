#!/usr/bin/env python

import sys
sys.path.insert(0, '..')

from src import TAppDecoder


config_dir = '../../h265'
stream_dir = '.'
output_dir = '.'
decode_opt = ('--OutputBitDepth=8',
			  '--BitstreamFile=%s' % (stream_dir+'/phantom-hm9.2.265'),
			  '--ReconFile=%s' % (output_dir+'/phantom-hm9.2.yuv'))

TAppDecoder(['TAppDecoder'] + list(decode_opt))
