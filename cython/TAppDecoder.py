#!/usr/bin/env python

from hevc import decmain as TAppDecoder


config_dir = '../../../video/h265'
stream_dir = '../../../video/h265'
output_dir = '.'
decode_opt = ('--OutputBitDepth=8',
			  '--BitstreamFile=%s' % (stream_dir+'/phantom-hm9.1.265'),
			  '--ReconFile=%s' % (output_dir+'/phantom-hm9.1.yuv'))

TAppDecoder(['TAppDecoder'] + list(decode_opt))
