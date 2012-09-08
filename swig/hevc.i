/* hevc.i : HM 8.0 Python Swig Wrapper */

%module hevc

%include "argv.i"
%typemap(in) (Int argc, Char *argv[]) = (int argc, char *argv[]);

%include "std_vector.i"
namespace std {
  %template(VectorBool) vector<bool>;
  %template(VectorInt) vector<int>;
  %template(VectorUint8) vector<uint8_t>;
}

%include "typemaps.i"
%apply bool &INOUT { bool & };
%apply int &INOUT { int & };
%apply short &INOUT { short & };
%apply long &INOUT { long & };
%apply unsigned int &INOUT { unsigned int & };
%apply unsigned short &INOUT { unsigned short & };
%apply unsigned long &INOUT { unsigned long & };
%apply double &INOUT { double & };
%apply float &INOUT { float & };


%{
  #include "TLibCommon/TypeDef.h"
  #include "TLibCommon/CommonDef.h"
  #include "TLibCommon/TComRom.h"
  #include "TLibCommon/NAL.h"
  #include "TLibCommon/SEI.h"
  #include "TLibCommon/AccessUnit.h"
  #include "TLibCommon/ContextModel.h"
  #include "TLibCommon/ContextModel3DBuffer.h"
  #include "TLibCommon/ContextTables.h"
  #include "TLibCommon/TComCABACTables.h"
  #include "TLibCommon/TComBitStream.h"
  #include "TLibCommon/TComBitCounter.h"
  #include "TLibCommon/TComList.h"
  #include "TLibCommon/TComPicSym.h"
  #include "TLibCommon/TComPicYuv.h"
  #include "TLibCommon/TComPic.h"
  #include "TLibCommon/TComYuv.h"
  #include "TLibCommon/TComDataCU.h"
  #include "TLibCommon/TComSlice.h"
  #include "TLibCommon/TComTrQuant.h"
  #include "TLibCommon/TComInterpolationFilter.h"
  #include "TLibCommon/TComMotionInfo.h"
  #include "TLibCommon/TComMv.h"
  #include "TLibCommon/TComPattern.h"
  #include "TLibCommon/TComWeightPrediction.h"
  #include "TLibCommon/TComPrediction.h"
  #include "TLibCommon/TComRdCostWeightPrediction.h"
  #include "TLibCommon/TComRdCost.h"
  #include "TLibCommon/TComLoopFilter.h"
  #include "TLibCommon/TComAdaptiveLoopFilter.h"
  #include "TLibCommon/TComSampleAdaptiveOffset.h"

  #include "TLibDecoder/AnnexBread.h"
  #include "TLibDecoder/NALread.h"
  #include "TLibDecoder/SEIread.h"
  #include "TLibDecoder/TDecBinCoder.h"
  #include "TLibDecoder/TDecBinCoderCABAC.h"
  #include "TLibDecoder/TDecEntropy.h"
  #include "TLibDecoder/TDecCAVLC.h"
  #include "TLibDecoder/TDecSbac.h"
  #include "TLibDecoder/TDecCu.h"
  #include "TLibDecoder/TDecSlice.h"
  #include "TLibDecoder/TDecGop.h"
  #include "TLibDecoder/TDecTop.h"

  #include "TLibEncoder/AnnexBwrite.h"
  #include "TLibEncoder/NALwrite.h"
  #include "TLibEncoder/SEIwrite.h"
  #include "TLibEncoder/TEncBinCoder.h"
  #include "TLibEncoder/TEncBinCoderCABAC.h"
  #include "TLibEncoder/TEncBinCoderCABACCounter.h"
  #include "TLibEncoder/TEncEntropy.h"
  #include "TLibEncoder/TEncCavlc.h"
  #include "TLibEncoder/TEncSbac.h"
  #include "TLibEncoder/TEncCfg.h"
  #include "TLibEncoder/TEncPic.h"
  #include "TLibEncoder/WeightPredAnalysis.h"
  #include "TLibEncoder/TEncPreanalyzer.h"
  #include "TLibEncoder/TEncAnalyze.h"
  #include "TLibEncoder/TEncRateCtrl.h"
  #include "TLibEncoder/TEncSearch.h"
  #include "TLibEncoder/TEncAdaptiveLoopFilter.h"
  #include "TLibEncoder/TEncSampleAdaptiveOffset.h"
  #include "TLibEncoder/TEncCu.h"
  #include "TLibEncoder/TEncSlice.h"
  #include "TLibEncoder/TEncGOP.h"
  #include "TLibEncoder/TEncTop.h"

  #include "TLibVideoIO/TVideoIOYuv.h"

  #include "libmd5/MD5.h"

  #include "TAppDecCfg.h"
  #include "TAppDecTop.h"
  #include "TAppEncCfg.h"
  #include "TAppEncTop.h"

  extern bool g_md5_mismatch;
  extern int decmain(int argc, char* argv[]);
  extern int encmain(int argc, char* argv[]);
%}

#define __inline

%include "TLibCommon/TypeDef.h"
%include "TLibCommon/CommonDef.h"
%include "TLibCommon/TComRom.h"
%include "TLibCommon/NAL.h"
%include "TLibCommon/SEI.h"

%include "std_list.i"
%template(ListNALUnitEBSP) std::list<NALUnitEBSP *>;

%include "TLibCommon/AccessUnit.h"
%include "TLibCommon/ContextModel.h"
%include "TLibCommon/ContextModel3DBuffer.h"
%include "TLibCommon/ContextTables.h"
%include "TLibCommon/TComCABACTables.h"
%include "TLibCommon/TComBitStream.h"
%include "TLibCommon/TComBitCounter.h"
%include "TLibCommon/TComList.h"
%include "TLibCommon/TComPicSym.h"
%include "TLibCommon/TComPicYuv.h"
%include "TLibCommon/TComPic.h"
%include "TLibCommon/TComYuv.h"
%include "TLibCommon/TComDataCU.h"
%include "TLibCommon/TComSlice.h"
%include "TLibCommon/TComTrQuant.h"
%include "TLibCommon/TComInterpolationFilter.h"
%include "TLibCommon/TComMotionInfo.h"
%include "TLibCommon/TComMv.h"
%include "TLibCommon/TComPattern.h"
%include "TLibCommon/TComWeightPrediction.h"
%include "TLibCommon/TComPrediction.h"
%include "TLibCommon/TComRdCostWeightPrediction.h"
%include "TLibCommon/TComRdCost.h"
%include "TLibCommon/TComLoopFilter.h"
%include "TLibCommon/TComAdaptiveLoopFilter.h"
%include "TLibCommon/TComSampleAdaptiveOffset.h"

%include "TLibDecoder/AnnexBread.h"
%include "TLibDecoder/NALread.h"
%include "TLibDecoder/SEIread.h"
%include "TLibDecoder/TDecBinCoder.h"
%include "TLibDecoder/TDecBinCoderCABAC.h"
%include "TLibDecoder/TDecEntropy.h"
%include "TLibDecoder/TDecCAVLC.h"
%include "TLibDecoder/TDecSbac.h"
%include "TLibDecoder/TDecCu.h"
%include "TLibDecoder/TDecSlice.h"
%include "TLibDecoder/TDecGop.h"
%include "TLibDecoder/TDecTop.h"

%include "TLibEncoder/AnnexBwrite.h"
%include "TLibEncoder/NALwrite.h"
%include "TLibEncoder/SEIwrite.h"
%include "TLibEncoder/TEncBinCoder.h"
%include "TLibEncoder/TEncBinCoderCABAC.h"
%include "TLibEncoder/TEncBinCoderCABACCounter.h"
%include "TLibEncoder/TEncEntropy.h"
%include "TLibEncoder/TEncCavlc.h"
%include "TLibEncoder/TEncSbac.h"
%include "TLibEncoder/TEncCfg.h"
%include "TLibEncoder/TEncPic.h"
%include "TLibEncoder/WeightPredAnalysis.h"
%include "TLibEncoder/TEncPreanalyzer.h"
%include "TLibEncoder/TEncAnalyze.h"
%include "TLibEncoder/TEncRateCtrl.h"
%include "TLibEncoder/TEncSearch.h"
%include "TLibEncoder/TEncAdaptiveLoopFilter.h"
%include "TLibEncoder/TEncSampleAdaptiveOffset.h"
%include "TLibEncoder/TEncCu.h"
%include "TLibEncoder/TEncSlice.h"
%include "TLibEncoder/TEncGOP.h"
%include "TLibEncoder/TEncTop.h"

%include "TLibVideoIO/TVideoIOYuv.h"

%include "libmd5/MD5.h"

%include "TAppDecCfg.h"
%include "TAppDecTop.h"
%include "TAppEncCfg.h"
%include "TAppEncTop.h"

extern bool g_md5_mismatch;
extern int decmain(int argc, char* argv[]);
extern int encmain(int argc, char* argv[]);


%include "carrays.i"
%include "carray_value.i"

%array_class(Pel, PelArray);

%inline %{
  typedef TComInputBitstream *PtrTComInputBitstream;
%}

%array_class(Bool,   ArrayBool  );
%array_class(Char,   ArrayChar  );
%array_class(UChar,  ArrayUChar );
%array_class(Short,  ArrayShort );
%array_class(UShort, ArrayUShort);
%array_class(Int,    ArrayInt   );
%array_class(UInt,   ArrayUInt  );
%array_class(Double, ArrayDouble);

%array_class(Pxl,    ArrayPxl   );
%array_class(Pel,    ArrayPel   );
%array_class(TCoeff, ArrayTCoeff);

%array_class(PtrTComInputBitstream, ArrayTComInputBitstream);
%array_value(TDecSbac,              ArrayTDecSbac          );
%array_value(TDecBinCABAC,          ArrayTDecBinCABAC      );
%array_value(TComYuv,               ArrayTComYuv           );
%array_value(TComDataCU,            ArrayTComDataCU        );
%array_value(TComMvField,           ArrayTComMvField       );
%array_value(TComMv,                ArrayTComMv            );

namespace std {
  %template(ListTComPic   ) list<TComPic *>;
  %template(ListTComPicYuv) list<TComPicYuv *>;
}
%template(TComListTComPic   ) TComList<TComPic *>;
%template(TComListTComPicYuv) TComList<TComPicYuv *>;

%template(ParameterSetMapTComVPS) ParameterSetMap<TComVPS>;
%template(ParameterSetMapTComSPS) ParameterSetMap<TComSPS>;
%template(ParameterSetMapTComPPS) ParameterSetMap<TComPPS>;


%inline %{
  std::istream &istream_open(const char *filename, const char *mode) {
    std::ifstream *file =
      new std::ifstream(filename, std::ifstream::in | std::ifstream::binary);
    return *file;
  }
  void istream_clear(std::istream &is) { is.clear(); }
  bool istream_not(std::istream &is) { return !is; }
  unsigned long
  istream_tellg(std::istream &is) { return is.tellg(); }
  std::istream &
  istream_seekg(std::istream &is, unsigned long pos) { return is.seekg(pos); }
%}

%inline %{
  unsigned char
  digest_get(unsigned char digest[3][16], int i, int j) { return digest[i][j]; }

  Bool   *BoolAdd  (Bool   *base, Int offset) { return base + offset; }
  Char   *CharAdd   (Char   *base, Int offset) { return base + offset; }
  UChar  *UCharAdd (UChar  *base, Int offset) { return base + offset; }
  Short  *ShortAdd (Short  *base, Int offset) { return base + offset; }
  UShort *UShortAdd(UShort *base, Int offset) { return base + offset; }
  Int    *IntAdd   (Int    *base, Int offset) { return base + offset; }
  UInt   *UIntAdd  (UInt   *base, Int offset) { return base + offset; }
  Double *DoubleAdd(Double *base, Int offset) { return base + offset; }

  Pxl    *PxlAdd   (Pxl    *base, Int offset) { return base + offset; }
  Pel    *PelAdd   (Pel    *base, Int offset) { return base + offset; }
  TCoeff *TCoeffAdd(TCoeff *base, Int offset) { return base + offset; }
%}
