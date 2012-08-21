import os
import string

from pyplusplus.function_transformers import transformer as transformer
from pyplusplus.function_transformers import controllers as controllers

from pygccxml import declarations
from pyplusplus import code_repository

def is_ref_or_ptr( type_ ):
    return declarations.is_pointer( type_ ) or declarations.is_reference( type_ )

def is_ptr_or_array( type_ ):
    return declarations.is_pointer( type_ ) or declarations.is_array( type_ )

def remove_ref_or_ptr( type_ ):
    if declarations.is_pointer( type_ ):
        return declarations.remove_pointer( type_ )
    elif declarations.is_reference( type_ ):
        return declarations.remove_reference( type_ )
    else:
        raise TypeError( 'Type should be reference or pointer, got %s.' % type_ )

_seq2arr = string.Template( os.linesep.join([
              'int size_$pylist = bp::len ( $pylist );'
              ,'if (size_$pylist > $max_size - 1 ) size_$pylist = $max_size - 1; // check max buffer size'
              ,'$native_pointer = new char [ size_$pylist + 1 ]; // extra space for terminating zero'
              ,'pyplus_conv::ensure_uniform_sequence< $type >( $pylist, size_$pylist );'
              ,'pyplus_conv::copy_sequence( $pylist, pyplus_conv::array_inserter( $native_pointer, size_$pylist ) );'
              ,'$native_pointer[ size_$pylist ] = 0;'
              ] ) )

_arr2seq = string.Template(os.linesep.join([
            '// set a max inbound string length to ensure some level of saftey'
            ,'int len_$pylist = strnlen ( $native_pointer, $max_size );'
            ,'pyplus_conv::copy_container( $native_pointer, $native_pointer + len_$pylist, pyplus_conv::list_inserter( $pylist ) );']))
if os.sys.platform == 'darwin':
    _arr2seq = string.Template(os.linesep.join([
            '// set a max inbound string length to ensure some level of saftey'
            ,'int len_$pylist = strlen ( $native_pointer ); // note no strnlen on mac!!, $max_size )'
            ,'if ( len_$pylist > $max_size ) len_$pylist = $max_size;'
            ,'pyplus_conv::copy_container( $native_pointer, $native_pointer + len_$pylist, pyplus_conv::list_inserter( $pylist ) );']))
    
_cleanUp = string.Template(  
            'delete $native_name;' )
                         
class input_c_string_t(transformer.transformer_t):
    """Handles an input char * as a python list.

    void do_something(char * v) ->  do_something(object v2)

    where v2 is a Python sequence/string
    """

    def __init__(self, function, arg_ref, size):
        """Constructor.

        :param maxsize: The maximum string size we will allow...
        :type maxsize: int
        """
        transformer.transformer_t.__init__( self, function )

        self.arg = self.get_argument( arg_ref )
        self.arg_index = self.function.arguments.index( self.arg )

        if not is_ptr_or_array( self.arg.type ):
            raise ValueError( '%s\nin order to use "input_array" transformation, argument %s type must be a array or a pointer (got %s).' ) \
                  % ( function, self.arg.name, self.arg.type)

        self.max_size = size
        self.array_item_type = declarations.remove_const( declarations.array_item_type( self.arg.type ) )
        self.array_item_rawtype = declarations.remove_cv( self.arg.type )
        self.array_item_rawtype = declarations.pointer_t( self.array_item_type )
        

    def __str__(self):
        return "input_array(%s,%d)"%( self.arg.name, self.max_size)

    def required_headers( self ):
        """Returns list of header files that transformer generated code depends on."""
        return [ code_repository.convenience.file_name ]

    def __configure_sealed(self, controller):
        global _seq2arr, _cleanUp
        w_arg = controller.find_wrapper_arg( self.arg.name )
        w_arg.type = declarations.dummy_type_t( "boost::python::str" )

        # Declare a variable that will hold the C array...
        native_pointer = controller.declare_variable( self.array_item_rawtype
                                                    , "native_" + self.arg.name
                                                    , '' )

        copy_pylist2arr = _seq2arr.substitute( type=self.array_item_type
                                                , pylist=w_arg.name
                                                , max_size=self.max_size
                                                , native_pointer=native_pointer )

        cleanUp = _cleanUp.substitute ( native_name =   "native_" + self.arg.name )                                                                                               

        controller.add_pre_call_code( copy_pylist2arr )
        
        controller.add_post_call_code ( cleanUp )

        controller.modify_arg_expression( self.arg_index, native_pointer )

    def __configure_v_mem_fun_default( self, controller ):
        self.__configure_sealed( controller )

    def __configure_v_mem_fun_override( self, controller ):
        global _arr2seq
        pylist = controller.declare_py_variable( declarations.dummy_type_t( 'boost::python::list' )
                                                 , 'py_' + self.arg.name )

        copy_arr2pylist = _arr2seq.substitute( native_pointer=self.arg.name
                                                , max_size=self.max_size
                                                , pylist=pylist )

        controller.add_py_pre_call_code( copy_arr2pylist )

    def configure_mem_fun( self, controller ):
        self.__configure_sealed( controller )

    def configure_free_fun(self, controller ):
        self.__configure_sealed( controller )

    def configure_virtual_mem_fun( self, controller ):
        self.__configure_v_mem_fun_override( controller.override_controller )
        self.__configure_v_mem_fun_default( controller.default_controller )

def input_c_string( *args, **keywd ):
    def creator( function ):
        return input_c_string_t( function, *args, **keywd )
    return creator
