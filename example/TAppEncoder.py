#!/usr/bin/env python

import sys
sys.path.insert(0, '..')

use_swig = True
if use_swig:
	from swig.hevc import encmain as TAppEncoder
else:
	from src.App.TAppEncoder.TAppEncoder import TAppEncoder


config_dir = '../../h265/binary'
stream_dir = '../../h265/binary'
output_dir = '.'
encode_opt = ('-c', config_dir+'/h265enc.cfg',
              '--SourceWidth=1920', '--SourceHeight=1080',
              '--IntraPeriod=32', '--GOPSize=8', '--FramesToBeEncoded=600', '--FrameRate=60',
              '--SEIpictureDigest=1',
              '--InputFile=%s' % (stream_dir+'/phantom.yuv'),
              '--BitstreamFile=%s' % (output_dir+'/phantom.265'))

TAppEncoder(['TAppEncoder'] + list(encode_opt))
