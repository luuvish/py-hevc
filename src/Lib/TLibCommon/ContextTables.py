# -*- coding: utf-8 -*-
"""
    module : src/Lib/TLibCommon/ContextTables.py
    HM 10.0 Python Implementation
"""


MAX_NUM_CTX_MOD                   = 512

NUM_SPLIT_FLAG_CTX                =   3
NUM_SKIP_FLAG_CTX                 =   3

NUM_MERGE_FLAG_EXT_CTX            =   1
NUM_MERGE_IDX_EXT_CTX             =   1

NUM_PART_SIZE_CTX                 =   4
NUM_CU_AMP_CTX                    =   1
NUM_PRED_MODE_CTX                 =   1

NUM_ADI_CTX                       =   1

NUM_CHROMA_PRED_CTX               =   2
NUM_INTER_DIR_CTX                 =   5
NUM_MV_RES_CTX                    =   2

NUM_REF_NO_CTX                    =   2
NUM_TRANS_SUBDIV_FLAG_CTX         =   3
NUM_QT_CBF_CTX                    =   5
NUM_QT_ROOT_CBF_CTX               =   1
NUM_DELTA_QP_CTX                  =   3

NUM_SIG_CG_FLAG_CTX               =   2

NUM_SIG_FLAG_CTX                  =  42
NUM_SIG_FLAG_CTX_LUMA             =  27
NUM_SIG_FLAG_CTX_CHROMA           =  15

NUM_CTX_LAST_FLAG_XY              =  15

NUM_ONE_FLAG_CTX                  =  24
NUM_ONE_FLAG_CTX_LUMA             =  16
NUM_ONE_FLAG_CTX_CHROMA           =   8
NUM_ABS_FLAG_CTX                  =   6
NUM_ABS_FLAG_CTX_LUMA             =   4
NUM_ABS_FLAG_CTX_CHROMA           =   2

NUM_MVP_IDX_CTX                   =   2

NUM_SAO_MERGE_FLAG_CTX            =   1
NUM_SAO_TYPE_IDX_CTX              =   1

NUM_TRANSFORMSKIP_FLAG_CTX        =   1
NUM_CU_TRANSQUANT_BYPASS_FLAG_CTX =   1 
CNU                               = 154


INIT_CU_TRANSQUANT_BYPASS_FLAG = (
    (154, ),
    (154, ),
    (154, ),
)

INIT_SPLIT_FLAG = (
    (107, 139, 126),
    (107, 139, 126),
    (139, 141, 157),
)

INIT_SKIP_FLAG = (
    (197, 185, 201),
    (197, 185, 201),
    (CNU, CNU, CNU),
)

INIT_MERGE_FLAG_EXT = (
    (154, ),
    (110, ),
    (CNU, ),
)

INIT_MERGE_IDX_EXT = (
    (137, ),
    (122, ),
    (CNU, ),
)

INIT_PART_SIZE = (
    (154, 139, CNU, CNU),
    (154, 139, CNU, CNU),
    (184, CNU, CNU, CNU),
)

INIT_CU_AMP_POS = (
    (154, ),
    (154, ),
    (CNU, ),
)

INIT_PRED_MODE = (
    (134, ),
    (149, ),
    (CNU, ),
)

INIT_INTRA_PRED_MODE = (
    (183, ),
    (154, ),
    (184, ),
)

INIT_CHROMA_PRED_MODE = (
    (152, 139),
    (152, 139),
    ( 63, 139),
)

INIT_INTER_DIR = (
    ( 95,  79,  63,  31,  31),
    ( 95,  79,  63,  31,  31),
    (CNU, CNU, CNU, CNU, CNU),
)

INIT_MVD = (
    (169, 198),
    (140, 198),
    (CNU, CNU),
)

INIT_REF_PIC = (
    (153, 153),
    (153, 153),
    (CNU, CNU),
)

INIT_DQP = (
    (154, 154, 154),
    (154, 154, 154),
    (154, 154, 154),
)

INIT_QT_CBF = (
    (153, 111, CNU, CNU, CNU, 149,  92, 167, CNU, CNU),
    (153, 111, CNU, CNU, CNU, 149, 107, 167, CNU, CNU),
    (111, 141, CNU, CNU, CNU,  94, 138, 182, CNU, CNU),
)

INIT_QT_ROOT_CBF = (
    ( 79, ),
    ( 79, ),
    (CNU, ),
)

INIT_LAST = (
    (125, 110, 124, 110,  95,  94, 125, 111, 111,  79, 125, 126, 111, 111,  79,
     108, 123,  93, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU),
    (125, 110,  94, 110,  95,  79, 125, 111, 110,  78, 110, 111, 111,  95,  94,
     108, 123, 108, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU),
    (110, 110, 124, 125, 140, 153, 125, 127, 140, 109, 111, 143, 127, 111,  79,
     108, 123,  63, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU, CNU),
)

INIT_SIG_CG_FLAG = (
    (121, 140,  61, 154),
    (121, 140,  61, 154),
    ( 91, 171, 134, 141),
)

INIT_SIG_FLAG = (
    (170, 154, 139, 153, 139, 123, 123,  63, 124, 166, 183, 140, 136, 153,
     154, 166, 183, 140, 136, 153, 154, 166, 183, 140, 136, 153, 154, 170,
     153, 138, 138, 122, 121, 122, 121, 167, 151, 183, 140, 151, 183, 140),
    (155, 154, 139, 153, 139, 123, 123,  63, 153, 166, 183, 140, 136, 153,
     154, 166, 183, 140, 136, 153, 154, 166, 183, 140, 136, 153, 154, 170,
     153, 123, 123, 107, 121, 107, 121, 167, 151, 183, 140, 151, 183, 140),
    (111, 111, 125, 110, 110,  94, 124, 108, 124, 107, 125, 141, 179, 153,
     125, 107, 125, 141, 179, 153, 125, 107, 125, 141, 179, 153, 125, 140,
     139, 182, 182, 152, 136, 152, 136, 153, 136, 139, 111, 136, 139, 111),
)

INIT_ONE_FLAG = (
    (154, 196, 167, 167, 154, 152, 167, 182, 182, 134, 149, 136,
     153, 121, 136, 122, 169, 208, 166, 167, 154, 152, 167, 182),
    (154, 196, 196, 167, 154, 152, 167, 182, 182, 134, 149, 136,
     153, 121, 136, 137, 169, 194, 166, 167, 154, 167, 137, 182),
    (140,  92, 137, 138, 140, 152, 138, 139, 153,  74, 149,  92,
     139, 107, 122, 152, 140, 179, 166, 182, 140, 227, 122, 197),
)

INIT_ABS_FLAG = (
    (107, 167,  91, 107, 107, 167),
    (107, 167,  91, 122, 107, 167),
    (138, 153, 136, 167, 152, 152),
)

INIT_MVP_IDX = (
    (168, CNU),
    (168, CNU),
    (CNU, CNU),
)

INIT_SAO_MERGE_FLAG = (
    (153, ),
    (153, ),
    (153, ),
)

INIT_SAO_TYPE_IDX = (
    (160, ),
    (185, ),
    (200, ),
)

INIT_TRANS_SUBDIV_FLAG = (
    (224, 167, 122),
    (124, 138,  94),
    (153, 138, 138),
)

INIT_TRANSFORMSKIP_FLAG = (
    (139, 139),
    (139, 139),
    (139, 139),
)
