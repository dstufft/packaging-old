"""
Implementation of the version scheme defined in PEP 386.
"""
import re


__all__ = ["Version", "suggest_normalized_version", "VersionPredicate"]

# A marker used in the second and third parts of the `parts` tuple, for
# versions that don't have those segments, to sort properly. An example
# of versions in sort order ('highest' last):
#   1.0b1                 ((1,0), ('b',1), ('z',))
#   1.0.dev345            ((1,0), ('z',),  ('dev', 345))
#   1.0                   ((1,0), ('z',),  ('z',))
#   1.0.post256.dev345    ((1,0), ('z',),  ('z', 'post', 256, 'dev', 345))
#   1.0.post345           ((1,0), ('z',),  ('z', 'post', 345, 'z'))
#                                   ^        ^                 ^
#   'b' < 'z' ---------------------/         |                 |
#                                            |                 |
#   'dev' < 'z' ----------------------------/                  |
#                                                              |
#   'dev' < 'z' ----------------------------------------------/
# 'f' for 'final' would be kind of nice, but due to bugs in the support of
# 'rc' we must use 'z'
_FINAL_MARKER = ('z',)

_VERSION_RE = re.compile(r'''
    ^
    (?P<version>\d+\.\d+)          # minimum 'N.N'
    (?P<extraversion>(?:\.\d+)*)   # any number of extra '.N' segments
    (?:
        (?P<prerel>[abc]|rc)       # 'a'=alpha, 'b'=beta, 'c'=release candidate
                                   # 'rc'= alias for release candidate
        (?P<prerelversion>\d+(?:\.\d+)*)
    )?
    (?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?
    $''', re.VERBOSE)


class Version(object):
    """A rational version.

    Good:
        1.2         # equivalent to "1.2.0"
        1.2.0
        1.2a1
        1.2.3a2
        1.2.3b1
        1.2.3c1
        1.2.3.4
        TODO: fill this out

    Bad:
        1           # mininum two numbers
        1.2a        # release level must have a release serial
        1.2.3b
    """
    def __init__(self, version, error_on_huge_major_num=True, drop_trailing_zeros=False):
        """Create a Version instance from a version string.

        @param s {str} The version string.
        @param error_on_huge_major_num {bool} Whether to consider an
            apparent use of a year or full date as the major version number
            an error. Default True. One of the observed patterns on PyPI before
            the introduction of `Version` was version numbers like
            this:
                2009.01.03
                20040603
                2005.01
            This guard is here to strongly encourage the package author to
            use an alternate version, because a release deployed into PyPI
            and, e.g. downstream Linux package managers, will forever remove
            the possibility of using a version number like "1.0" (i.e.
            where the major number is less than that huge major number).
        @param drop_trailing_zeros {bool} Whether to drop trailing zeros

            from the returned list. Default True.
        """
        self.version = version
        self.is_final = True  # by default, consider a version as final.
        self.drop_trailing_zeros = drop_trailing_zeros
        self._parse(self.version, error_on_huge_major_num)

    @classmethod
    def from_parts(cls, version, prerelease=_FINAL_MARKER,
                   devpost=_FINAL_MARKER):
        return cls(cls.parts_to_str((version, prerelease, devpost)))

    def _parse(self, s, error_on_huge_major_num=True):
        """Parses a string version into parts."""
        match = _VERSION_RE.search(s)
        if not match:
            raise ValueError("Invalid version '{version}'".format(version=s))

        groups = match.groupdict()
        parts = []

        # main version
        block = self._parse_numdots(groups['version'], s, 2)
        extraversion = groups.get('extraversion')
        if extraversion not in ('', None):
            block += self._parse_numdots(extraversion[1:], s)
        parts.append(tuple(block))

        # prerelease
        prerel = groups.get('prerel')
        if prerel is not None:
            block = [prerel]
            block += self._parse_numdots(groups.get('prerelversion'), s,
                                         pad_zeros_length=1)
            parts.append(tuple(block))
            self.is_final = False
        else:
            parts.append(_FINAL_MARKER)

        # postdev
        if groups.get('postdev'):
            post = groups.get('post')
            dev = groups.get('dev')
            postdev = []
            if post is not None:
                postdev.extend((_FINAL_MARKER[0], 'post', int(post)))
                if dev is None:
                    postdev.append(_FINAL_MARKER[0])
            if dev is not None:
                postdev.extend(('dev', int(dev)))
                self.is_final = False
            parts.append(tuple(postdev))
        else:
            parts.append(_FINAL_MARKER)
        self.parts = tuple(parts)
        if error_on_huge_major_num and self.parts[0][0] > 1980:
            raise ValueError("Huge major version number '{major}' in '{version}', which might cause future problems".format(major=self.parts[0][0], version=s))

    def _parse_numdots(self, s, full_ver_str, pad_zeros_length=0):
        """Parse 'N.N.N' sequences, return a list of ints.

        @param s {str} 'N.N.N...' sequence to be parsed
        @param full_ver_str {str} The full version string from which this
            comes. Used for error strings.
                @param pad_zeros_length {int} The length to which to pad the
            returned list with zeros, if necessary. Default 0.
        """
        nums = []
        for n in s.split("."):
            if len(n) > 1 and n[0] == '0':
                raise ValueError("Cannot have leading zero in a version number segment: '{number}' in '{version}'".format(number=n, version=full_ver_str))
            nums.append(int(n))
        if self.drop_trailing_zeros:
            while nums and nums[-1] == 0:
                nums.pop()
        while len(nums) < pad_zeros_length:
            nums.append(0)  # @@@ Not tested
        return nums

    def __str__(self):
        return self.parts_to_str(self.parts)

    @classmethod
    def parts_to_str(cls, parts):
        """Transforms a version expressed in tuple into its string
        representation."""
        # XXX This doesn't check for invalid tuples
        main, prerel, postdev = parts
        s = '.'.join(str(v) for v in main)
        if prerel is not _FINAL_MARKER:
            s += prerel[0]
            s += '.'.join(str(v) for v in prerel[1:])
        # XXX clean up: postdev is always true; code is obscure
        if postdev and postdev is not _FINAL_MARKER:
            if postdev[0] == _FINAL_MARKER[0]:
                postdev = postdev[1:]
            i = 0
            while i < len(postdev):
                if i % 2 == 0:
                    s += '.'
                s += str(postdev[i])
                i += 1
        return s

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self)

    def __eq__(self, other):
        if not isinstance(other, Version):
            raise TypeError("Cannot compare {left} and {right}".format(left=type(self).__name__, right=type(other).__name__))
        return self.parts == other.parts

    def __lt__(self, other):
        if not isinstance(other, Version):
            raise TypeError("Cannot compare {left} and {right}".format(left=type(self).__name__, right=type(other).__name__))
        return self.parts < other.parts

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return not (self.__lt__(other) or self.__eq__(other))

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)

    # See http://docs.python.org/reference/datamodel#object.__hash__
    def __hash__(self):
        return hash(self.parts)


def suggest_normalized_version(s):
    """Suggest a normalized version close to the given version string.

    If you have a version string that isn't rational (i.e. Version
    doesn't like it) then you might be able to get an equivalent (or close)
    rational version from this function.

    This does a number of simple normalizations to the given string, based
    on observation of versions currently in use on PyPI. Given a dump of
    those version during PyCon 2009, 4287 of them:
    - 2312 (53.93%) match Version without change
      with the automatic suggestion
    - 3474 (81.04%) match when using this suggestion method

    @param s {str} An irrational version string.
    @returns A rational version string, or None, if couldn't determine one.
    """
    try:
        Version(s)
        return s   # already rational
    except ValueError:
        pass

    rs = s.lower()

    # part of this could use maketrans
    for orig, repl in (('-alpha', 'a'), ('-beta', 'b'), ('alpha', 'a'),
                       ('beta', 'b'), ('rc', 'c'), ('-final', ''),
                       ('-pre', 'c'),
                       ('-release', ''), ('.release', ''), ('-stable', ''),
                       ('+', '.'), ('_', '.'), (' ', ''), ('.final', ''),
                       ('final', '')):
        rs = rs.replace(orig, repl)

    # if something ends with dev or pre, we add a 0
    rs = re.sub(r"pre$", r"pre0", rs)
    rs = re.sub(r"dev$", r"dev0", rs)

    # if we have something like "b-2" or "a.2" at the end of the
    # version, that is pobably beta, alpha, etc
    # let's remove the dash or dot
    rs = re.sub(r"([abc]|rc)[\-\.](\d+)$", r"\1\2", rs)

    # 1.0-dev-r371 -> 1.0.dev371
    # 0.1-dev-r79 -> 0.1.dev79
    rs = re.sub(r"[\-\.](dev)[\-\.]?r?(\d+)$", r".\1\2", rs)

    # Clean: 2.0.a.3, 2.0.b1, 0.9.0~c1
    rs = re.sub(r"[.~]?([abc])\.?", r"\1", rs)

    # Clean: v0.3, v1.0
    if rs.startswith('v'):
        rs = rs[1:]

    # Clean leading '0's on numbers.
    #TODO: unintended side-effect on, e.g., "2003.05.09"
    # PyPI stats: 77 (~2%) better
    rs = re.sub(r"\b0+(\d+)(?!\d)", r"\1", rs)

    # Clean a/b/c with no version. E.g. "1.0a" -> "1.0a0". Setuptools infers
    # zero.
    # PyPI stats: 245 (7.56%) better
    rs = re.sub(r"(\d+[abc])$", r"\g<1>0", rs)

    # the 'dev-rNNN' tag is a dev tag
    rs = re.sub(r"\.?(dev-r|dev\.r)\.?(\d+)$", r".dev\2", rs)

    # clean the - when used as a pre delimiter
    rs = re.sub(r"-(a|b|c)(\d+)$", r"\1\2", rs)

    # a terminal "dev" or "devel" can be changed into ".dev0"
    rs = re.sub(r"[\.\-](dev|devel)$", r".dev0", rs)

    # a terminal "dev" can be changed into ".dev0"
    rs = re.sub(r"(?![\.\-])dev$", r".dev0", rs)

    # a terminal "final" or "stable" can be removed
    rs = re.sub(r"(final|stable)$", "", rs)

    # The 'r' and the '-' tags are post release tags
    #   0.4a1.r10       ->  0.4a1.post10
    #   0.9.33-17222    ->  0.9.33.post17222
    #   0.9.33-r17222   ->  0.9.33.post17222
    rs = re.sub(r"\.?(r|-|-r)\.?(\d+)$", r".post\2", rs)

    # Clean 'r' instead of 'dev' usage:
    #   0.9.33+r17222   ->  0.9.33.dev17222
    #   1.0dev123       ->  1.0.dev123
    #   1.0.git123      ->  1.0.dev123
    #   1.0.bzr123      ->  1.0.dev123
    #   0.1a0dev.123    ->  0.1a0.dev123
    # PyPI stats:  ~150 (~4%) better
    rs = re.sub(r"\.?(dev|git|bzr)\.?(\d+)$", r".dev\2", rs)

    # Clean '.pre' (normalized from '-pre' above) instead of 'c' usage:
    #   0.2.pre1        ->  0.2c1
    #   0.2-c1         ->  0.2c1
    #   1.0preview123   ->  1.0c123
    # PyPI stats: ~21 (0.62%) better
    rs = re.sub(r"\.?(pre|preview|-c)(\d+)$", r"c\g<2>", rs)

    # Tcl/Tk uses "px" for their post release markers
    rs = re.sub(r"p(\d+)$", r".post\1", rs)

    try:
        Version(rs)
        return rs   # already rational
    except ValueError:
        pass
    return None


# A predicate is: "ProjectName (VERSION1, VERSION2, ..)
_PREDICATE = re.compile(r"(?i)^\s*(\w[\s\w-]*(?:\.\w*)*)(.*)")
_VERSIONS = re.compile(r"^\s*\((?P<versions>.*)\)\s*$")
_PLAIN_VERSIONS = re.compile(r"^\s*(.*)\s*$")
_SPLIT_CMP = re.compile(r"^\s*(<=|>=|<|>|!=|==)\s*([^\s,]+)\s*$")


def _split_predicate(predicate):
    match = _SPLIT_CMP.match(predicate)
    if match is None:
        # probably no op, we'll use "=="
        comp, version = '==', predicate
    else:
        comp, version = match.groups()
    return comp, Version(version)


class VersionPredicate(object):
    """Defines a predicate: ProjectName (>ver1,ver2, ..)"""

    _operators = {"<": lambda x, y: x < y,
                  ">": lambda x, y: x > y,
                  "<=": lambda x, y: str(x).startswith(str(y)) or x < y,
                  ">=": lambda x, y: str(x).startswith(str(y)) or x > y,
                  "==": lambda x, y: str(x).startswith(str(y)),
                  "!=": lambda x, y: not str(x).startswith(str(y)),
                  }

    def __init__(self, predicate):
        self._string = predicate
        predicate = predicate.strip()
        match = _PREDICATE.match(predicate)
        if match is None:
            raise ValueError('Bad predicate "%s"' % predicate)

        name, predicates = match.groups()
        self.name = name.strip()
        self.predicates = []

        if not predicates:
            return

        predicates = _VERSIONS.match(predicates.strip())
        predicates = predicates.groupdict()

        if predicates["versions"]:
            for version in predicates["versions"].split(","):
                if version.strip():
                    self.predicates.append(_split_predicate(version))

    def match(self, version):
        """Check if the provided version matches the predicates."""
        if isinstance(version, basestring):
            version = Version(version)
        for operator, predicate in self.predicates:
            if not self._operators[operator](version, predicate):
                return False
        return True

    def __repr__(self):
        return self._string
