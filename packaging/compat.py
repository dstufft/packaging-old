import sys
import types

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
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
            "__lt__": [("__gt__", lambda self, other: not (self < other or self == other)),
                       ("__le__", lambda self, other: self < other or self == other),
                       ("__ge__", lambda self, other: not self < other)],
            "__le__": [("__ge__", lambda self, other: not self <= other or self == other),
                       ("__lt__", lambda self, other: self <= other and not self == other),
                       ("__gt__", lambda self, other: not self <= other)],
            "__gt__": [("__lt__", lambda self, other: not (self > other or self == other)),
                       ("__ge__", lambda self, other: self > other or self == other),
                       ("__le__", lambda self, other: not self > other)],
            "__ge__": [("__le__", lambda self, other: (not self >= other) or self == other),
                       ("__gt__", lambda self, other: self >= other and not self == other),
                       ("__lt__", lambda self, other: not self >= other)]
        }
        # Find user-defined comparisons (not those inherited from object).
        roots = [op for op in convert if getattr(cls, op, None) is not getattr(object, op, None)]
        if not roots:
            raise ValueError("must define at least one ordering operation: < > <= >=")
        root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
        for opname, opfunc in convert[root]:
            if opname not in roots:
                opfunc.__name__ = opname
                opfunc.__doc__ = getattr(int, opname).__doc__
                setattr(cls, opname, opfunc)
        return cls
