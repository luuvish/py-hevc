/* -----------------------------------------------------------------------------
 * %array_value(TYPE,NAME)
 *
 * Generates a class wrapper around a C array.  The class has the following
 * interface:
 *
 *          struct NAME {
 *              NAME(int nelements);
 *             ~NAME();
 *              TYPE __getitem__(int index);
 *              void __setitem__(int index, TYPE value);
 *              TYPE * cast();
 *              static NAME *frompointer(TYPE *t);
  *         }
 *
 * ----------------------------------------------------------------------------- */

%define %array_value(TYPE,NAME)

%{
typedef TYPE NAME;
%}
typedef struct {
  /* Put language specific enhancements here */
} NAME;

%extend NAME {

  #ifdef __cplusplus
  NAME(size_t nelements) {
    return new TYPE[nelements];
  }
  ~NAME() {
    delete [] self;
  }
  #else
  NAME(int nelements) {
    return (TYPE *) calloc(nelements,sizeof(TYPE));
  }
  ~NAME() {
    free(self);
  }
  #endif

  TYPE &__getitem__(size_t index) {
    return self[index];
  }
  TYPE * cast() {
    return self;
  }
  static NAME *frompointer(TYPE *t) {
    return (NAME *) t;
  }
};

%types(NAME = TYPE);

%enddef
