#!/usr/bin/env python

level = 'AppTop'

if level == 'main':
    from hmswig import decmain
    from hmswig import encmain
    print 'HM Swig function'
else:
    if level == 'AppTop':
        from hmswig import TAppDecTop
        from hmswig import TAppEncTop
    else:
        from hmswig import InputByteStream, AnnexBStats, byteStreamNALUnit
        from hmswig import TVideoIOYuv
        from hmswig import TDecTop
        from hmswig import TEncTop
        from App.TAppDecoder.TAppDecTop import TAppDecTop
        from App.TAppEncoder.TAppEncTop import TAppEncTop
        print 'HM Python TAppDecTop()/TAppEncTop() function'

    from hmswig import cvar
    from App.TAppDecoder.decmain import decmain
    from App.TAppEncoder.encmain import encmain
    print 'HM Python main() function'
