import py
import sys
from ffi import FFI

SIZE_OF_LONG = 4 if sys.maxint == 2147483647 else 8


class BackendTests:

    def test_integer_ranges(self):
        ffi = FFI(backend=self.Backend())
        for (c_type, size) in [('char', 1),
                               ('short', 2),
                               ('short int', 2),
                               ('', 4),
                               ('int', 4),
                               ('long', SIZE_OF_LONG),
                               ('long int', SIZE_OF_LONG),
                               ('long long', 8),
                               ('long long int', 8),
                               ]:
            for unsigned in [None, False, True]:
                c_decl = {None: '',
                          False: 'signed ',
                          True: 'unsigned '}[unsigned] + c_type
                if c_decl == 'char' or c_decl == '':
                    continue
                if unsigned:
                    min = 0
                    max = (1 << (8*size)) - 1
                else:
                    min = -(1 << (8*size-1))
                    max = (1 << (8*size-1)) - 1
                p = ffi.new(c_decl, min)
                assert int(p) == min
                p = ffi.new(c_decl, max)
                assert int(p) == max
                py.test.raises(OverflowError, ffi.new, c_decl, min - 1)
                py.test.raises(OverflowError, ffi.new, c_decl, max + 1)

    def test_int_equality(self):
        ffi = FFI(backend=self.Backend())
        n = ffi.new("short", -123)
        assert bool(n)
        assert n == -123
        assert n == ffi.new("int", -123)
        assert not bool(ffi.new("short", 0))
        assert n != ffi.new("short", 123)
        assert hash(n) == hash(-123)
        assert int(n) == -123 and type(int(n)) is int
        py.test.raises(TypeError, "n < -122")
        py.test.raises(TypeError, "n <= -123")
        py.test.raises(TypeError, "n > -124")
        py.test.raises(TypeError, "n >= -123")
        py.test.raises(TypeError, "n >= n")

    def test_new_array_no_arg(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("int[10]")
        # the object was zero-initialized:
        for i in range(10):
            assert p[i] == 0

    def test_array_indexing(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("int[10]")
        p[0] = 42
        p[9] = 43
        assert p[0] == 42
        assert p[9] == 43
        py.test.raises(IndexError, "p[10]")
        py.test.raises(IndexError, "p[10] = 44")
        py.test.raises(IndexError, "p[-1]")
        py.test.raises(IndexError, "p[-1] = 44")

    def test_new_array_args(self):
        ffi = FFI(backend=self.Backend())
        # this tries to be closer to C: where we say "int x[5] = {10, 20, ..}"
        # then here we must enclose the items in a list
        p = ffi.new("int[5]", [10, 20, 30, 40, 50])
        assert p[0] == 10
        assert p[1] == 20
        assert p[2] == 30
        assert p[3] == 40
        assert p[4] == 50
        p = ffi.new("int[4]", [25])
        assert p[0] == 25
        assert p[1] == 0     # follow C convention rather than LuaJIT's
        assert p[2] == 0
        assert p[3] == 0
        p = ffi.new("int[4]", [ffi.new("int", -5)])
        assert p[0] == -5

    def test_new_array_varsize(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("int[]", 10)     # a single integer is the length
        assert p[9] == 0
        py.test.raises(IndexError, "p[10]")
        #
        py.test.raises(TypeError, ffi.new, "int[]")
        #
        p = ffi.new("int[]", [-6, -7])    # a list is all the items, like C
        assert p[0] == -6
        assert p[1] == -7
        py.test.raises(IndexError, "p[2]")

    def test_cannot_cast(self):
        ffi = FFI(backend=self.Backend())
        a = ffi.new("short int[10]")
        e = py.test.raises(TypeError, ffi.new, "long int *", a)
        assert str(e.value) == "cannot convert 'short[10]' to 'long *'"

    def test_new_pointer_to_array(self):
        ffi = FFI(backend=self.Backend())
        a = ffi.new("int[4]", [100, 102, 104, 106])
        p = ffi.new("int *", a)
        assert p[0] == 100
        assert p[1] == 102
        assert p[2] == 104
        assert p[3] == 106
        # keepalive: a

    def test_pointer_direct(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("int*")
        assert bool(p) is False
        assert p == ffi.new("int*")
        a = ffi.new("int[]", [123, 456])
        p = ffi.new("int*", a)
        assert bool(p) is True
        assert p == ffi.new("int*", a)
        assert p != ffi.new("int*")
        assert p[0] == 123
        assert p[1] == 456

    def test_repr(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("unsigned short int")
        assert repr(p) == "<cdata 'unsigned short'>"
        assert repr(type(p)) == "<class 'ffi.CData<unsigned short>'>"
        p = ffi.new("int*")
        assert repr(p) == "<cdata 'int *'>"
        assert repr(type(p)) == "<class 'ffi.CData<int *>'>"
        p = ffi.new("int [2]")
        assert repr(p) == "<cdata 'int[2]'>"
        assert repr(type(p)) == "<class 'ffi.CData<int[2]>'>"
        p = ffi.new("int*[2][3]")
        assert repr(p) == "<cdata 'int *[2][3]'>"
        assert repr(type(p)) == "<class 'ffi.CData<int *[2][3]>'>"

    def test_new_array_of_array(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("int[3][4]")
        p[0][0] = 10
        p[2][3] = 33
        assert p[0][0] == 10
        assert p[2][3] == 33
        py.test.raises(IndexError, "p[1][-1]")

    def test_new_array_of_pointer(self):
        ffi = FFI(backend=self.Backend())
        n = ffi.new("int[1]", [99])
        p = ffi.new("int*[4]")
        p[3] = n
        a = p[3]
        assert repr(a) == "<cdata 'int *'>"
        assert a[0] == 99

    def test_char(self):
        ffi = FFI(backend=self.Backend())
        assert int(ffi.new("char", "\xff")) == 0xFF
        assert int(ffi.new("char")) == 0
        assert bool(ffi.new("char", "\x80"))
        assert not bool(ffi.new("char"))
        py.test.raises(TypeError, ffi.new, "char", 32)
        p = ffi.new("char[]", ['a', 'b', '\x9c'])
        assert len(p) == 3
        assert p[0] == 'a'
        assert p[1] == 'b'
        assert p[2] == '\x9c'
        p[0] = '\xff'
        assert p[0] == '\xff'
        p = ffi.new("char[]", "abcd")
        assert len(p) == 4

    def test_none_as_null(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("int*[1]")
        assert p[0] is None
        #
        n = ffi.new("int[1]", [99])
        p = ffi.new("int*[1]", [n])
        assert p[0][0] == 99
        p[0] = None
        assert p[0] is None
        assert ffi.new("int*") == None
        assert ffi.new("int*") is not None

    def test_float(self):
        ffi = FFI(backend=self.Backend())
        p = ffi.new("float[]", [-2, -2.5])
        assert p[0] == -2.0
        assert p[1] == -2.5
        p[1] += 17.75
        assert p[1] == 15.25
        #
        f = ffi.new("float", 15.75)
        assert int(f) == 15 and type(int(f)) is int
        assert float(f) == 15.75 and type(float(f)) is float
        assert bool(f) is True
        assert bool(ffi.new("float", 0.0)) is False
        assert f == 15.75
        assert f != 16.2
        #
        f = ffi.new("float", 1.1)
        assert f != 1.1      # because of rounding effect
        assert abs(float(f) - 1.1) < 1E-7
        f = ffi.new("float", 1E200)
        assert float(f) == 1E200 * 1E200     # infinite, not enough precision

    def test_struct_simple(self):
        ffi = FFI(backend=self.Backend())
        ffi.cdef("struct foo { int a; short b, c; };")
        s = ffi.new("struct foo")
        assert s.a == s.b == s.c == 0
        s.b = -23
        assert s.b == -23
        py.test.raises(OverflowError, "s.b = 32768")
        #
        s = ffi.new("struct foo", [-2, -3])
        assert s.a == -2
        assert s.b == -3
        assert s.c == 0
        py.test.raises((AttributeError, TypeError), "del s.a")
        #
        py.test.raises(ValueError, ffi.new, "struct foo", [1, 2, 3, 4])

    def test_struct_opaque(self):
        ffi = FFI(backend=self.Backend())
        py.test.raises(TypeError, ffi.new, "struct baz")
        ffi.new("struct baz *")   # this works

    def test_union_simple(self):
        ffi = FFI(backend=self.Backend())
        ffi.cdef("union foo { int a; short b, c; };")
        u = ffi.new("union foo")
        assert u.a == u.b == u.c == 0
        u.b = -23
        assert u.b == -23
        assert u.a != 0
        py.test.raises(OverflowError, "u.b = 32768")
        #
        u = ffi.new("union foo", -2)
        assert u.a == -2
        py.test.raises((AttributeError, TypeError), "del u.a")

    def test_union_opaque(self):
        ffi = FFI(backend=self.Backend())
        py.test.raises(TypeError, ffi.new, "union baz")
        ffi.new("union baz *")   # this works

    def test_sizeof_type(self):
        ffi = FFI(backend=self.Backend())
        ffi.cdef("""
            struct foo { int a; short b, c, d; };
            union foo { int a; short b, c, d; };
        """)
        for c_type, expected_size in [
            ('char', 1),
            ('unsigned int', 4),
            ('char *', SIZE_OF_LONG),
            ('int[5]', 20),
            ('struct foo', 12),
            ('union foo', 4),
            ]:
            size = ffi.sizeof(c_type)
            assert size == expected_size

    def test_sizeof_cdata(self):
        ffi = FFI(backend=self.Backend())
        assert ffi.sizeof(ffi.new("short")) == 2
        #
        a = ffi.new("int[]", [10, 11, 12, 13, 14])
        assert len(a) == 5
        assert ffi.sizeof(a) == 20

    def test_string_from_char_array(self):
        ffi = FFI(backend=self.Backend())
        assert str(ffi.new("char", "x")) == "x"
        p = ffi.new("char[]", "hello.")
        p[5] = '!'
        assert str(p) == "hello!"
        a = ffi.new("char[]", "hello\x00world")
        p = ffi.new("char *", a)
        assert str(p) == 'hello'