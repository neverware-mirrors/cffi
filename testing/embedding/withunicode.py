import sys, cffi
if sys.version_info < (3,):
    u_prefix = "u"
else:
    u_prefix = ""
    unichr = chr


ffi = cffi.FFI()

ffi.embedding_api(u"""
    int add1(int, int);
""")

ffi.embedding_init_code(("""
    import sys, time
    for c in %s'""" + unichr(0x00ff) + unichr(0x1234) + unichr(0xfedc) + """':
        sys.stdout.write(str(ord(c)) + '\\n')
    sys.stdout.flush()
""") % u_prefix)

ffi.set_source("_withunicode_cffi", """
""")

fn = ffi.compile(verbose=True)
print('FILENAME: %s' % (fn,))
