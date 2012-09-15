import sys
import types

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3:
    string_type = str
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
else:
    string_type = basestring
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

try:
    from functools import total_ordering
except ImportError:
    def total_ordering(cls):
        """
        Class decorator that fills in missing ordering methods
        """
        convert = {
            "__lt__": [("__gt__", lambda self, other: other < self),
                       ("__le__", lambda self, other: not other < self),
                       ("__ge__", lambda self, other: not self < other)],
            "__le__": [("__ge__", lambda self, other: other <= self),
                       ("__lt__", lambda self, other: not other <= self),
                       ("__gt__", lambda self, other: not self <= other)],
            "__gt__": [("__lt__", lambda self, other: other > self),
                       ("__ge__", lambda self, other: not other > self),
                       ("__le__", lambda self, other: not self > other)],
            "__ge__": [("__le__", lambda self, other: other >= self),
                       ("__gt__", lambda self, other: not other >= self),
                       ("__lt__", lambda self, other: not self >= other)]
        }
        roots = set(dir(cls)) & set(convert)
        if not roots:
            raise ValueError("must define at least one ordering operation: < > <= >=")
        root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
        for opname, opfunc in convert[root]:
            if opname not in roots:
                opfunc.__name__ = opname
                opfunc.__doc__ = getattr(int, opname).__doc__
                setattr(cls, opname, opfunc)
        return cls
