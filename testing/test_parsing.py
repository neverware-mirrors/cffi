from cffi import FFI

class FakeBackend(object):

    def nonstandard_integer_types(self):
        return {}

    def sizeof(self, name):
        return 1

    def load_library(self, name):
        assert "libc" in name or "libm" in name
        return FakeLibrary()

    def new_function_type(self, args, result, has_varargs):
        return '<func (%s), %s, %s>' % (', '.join(args), result, has_varargs)

    def new_primitive_type(self, name):
        assert name == name.lower()
        return '<%s>' % name

    def new_pointer_type(self, itemtype):
        return '<pointer to %s>' % (itemtype,)

    def new_struct_type(self, name):
        return FakeStruct(name)

    def complete_struct_or_union(self, s, fields, tp=None):
        assert isinstance(s, FakeStruct)
        s.fields = fields
    
    def new_array_type(self, ptrtype, length):
        return '<array %s x %s>' % (ptrtype, length)

class FakeStruct(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return ', '.join([y + x for x, y, z in self.fields])

class FakeLibrary(object):
    
    def load_function(self, BType, name):
        return FakeFunction(BType, name)

class FakeFunction(object):

    def __init__(self, BType, name):
        self.BType = BType
        self.name = name


def test_simple():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("double sin(double x);")
    m = ffi.rawload("m")
    func = m.sin    # should be a callable on real backends
    assert func.name == 'sin'
    assert func.BType == '<func (<double>), <double>, False>'

def test_pipe():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("int pipe(int pipefd[2]);")
    C = ffi.rawload(None)
    func = C.pipe
    assert func.name == 'pipe'
    assert func.BType == '<func (<pointer to <int>>), <int>, False>'

def test_vararg():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("short foo(int, ...);")
    C = ffi.rawload(None)
    func = C.foo
    assert func.name == 'foo'
    assert func.BType == '<func (<int>), <short>, True>'

def test_no_args():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("""
        int foo(void);
        """)
    C = ffi.rawload(None)
    assert C.foo.BType == '<func (), <int>, False>'

def test_typedef():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("""
        typedef unsigned int UInt;
        typedef UInt UIntReally;
        UInt foo(void);
        """)
    C = ffi.rawload(None)
    assert ffi.typeof("UIntReally") == '<unsigned int>'
    assert C.foo.BType == '<func (), <unsigned int>, False>'

def test_typedef_more_complex():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("""
        typedef struct { int a, b; } foo_t, *foo_p;
        int foo(foo_p[]);
        """)
    C = ffi.rawload(None)
    assert str(ffi.typeof("foo_t")) == '<int>a, <int>b'
    assert ffi.typeof("foo_p") == '<pointer to <int>a, <int>b>'
    assert C.foo.BType == ('<func (<pointer to <pointer to '
                           '<int>a, <int>b>>), <int>, False>')

def test_typedef_array_force_pointer():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("""
        typedef int array_t[5];
        """)
    type = ffi._parser.parse_type("array_t", force_pointer=True)
    BType = ffi._get_cached_btype(type)
    assert BType == '<array <pointer to <int>> x 5>'

def test_typedef_array_convert_array_to_pointer():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("""
        typedef int (*fn_t)(int[5]);
        """)
    type = ffi._parser.parse_type("fn_t")
    BType = ffi._get_cached_btype(type)
    assert BType == '<func (<pointer to <int>>), <int>, False>'

def test_remove_comments():
    ffi = FFI(backend=FakeBackend())
    ffi.cdef("""
        double /*comment here*/ sin   // blah blah
        /* multi-
           line-
           //comment */  (
        // foo
        double // bar      /* <- ignored, because it's in a comment itself
        x, double/*several*//*comment*/y) /*on the same line*/
        ;
    """)
    m = ffi.rawload("m")
    func = m.sin
    assert func.name == 'sin'
    assert func.BType == '<func (<double>, <double>), <double>, False>'
