"""
Implementation of the version scheme defined in PEP 386.
"""
import re

from .compat import string_types, total_ordering


__all__ = ["Version", "VersionPredicate", "suggest_normalized_version"]

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


@total_ordering
class Version(object):

    _version_regex = re.compile(r"""
        ^
        (?P<version>\d+\.\d+(?:\.\d+)*)          # minimum 'N.N'
        (?:
            (?P<prerel>[abc]|rc)       # 'a'=alpha, 'b'=beta, 'c'=release candidate
                                       # 'rc'= alias for release candidate
            (?P<prerelversion>\d+(?:\.\d+)*)
        )?
        (?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?
        $""", re.VERBOSE)

    def __init__(self, version, *args, **kwargs):
        super(Version, self).__init__(*args, **kwargs)

        self.version = version
        self.parts = self._parse(self.version)

    def __str__(self):
        return self.version

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self)

    def __eq__(self, other):
        if not isinstance(other, Version):
            raise TypeError("Cannot compare {left} and {right}".format(left=type(self).__name__, right=type(other).__name__))
        left, right = self._normalize(self.parts, other.parts)
        return left == right

    def __lt__(self, other):
        if not isinstance(other, Version):
            raise TypeError("Cannot compare {left} and {right}".format(left=type(self).__name__, right=type(other).__name__))
        left, right = self._normalize(self.parts, other.parts)
        return left < right

    def __hash__(self):
        return hash(self.parts)

    @property
    def final(self):
        return all([x[-1] == "z" for x in self.parts[1:]])

    def _parse(self, version):
        """
        Parses a string version into parts.
        """
        def _parse_numerical(numerical):
            """
            Parse 'N.N.N' sequences, return a list of ints.
            """
            def cast(number):
                if len(number) > 1 and number.startswith("0"):
                    raise ValueError("Cannot have leading zero in a version number segment: '{number}' in '{version}'".format(number=number, version=version))
                return int(number)

            return [cast(n) for n in numerical.split(".")]

        match = self._version_regex.search(version)

        if not match:
            raise ValueError("Invalid version '{version}'".format(version=version))

        groups = match.groupdict()

        # main version
        parts = [tuple(_parse_numerical(groups["version"]))]

        # prerelease
        prerel = groups.get("prerel")
        if prerel is not None:
            parts += [tuple([prerel] + _parse_numerical(groups.get("prerelversion")))]
        else:
            parts += [("z",)]

        # postdev
        if groups.get("postdev"):
            post, dev = groups.get("post"), groups.get("dev")

            _parts = []

            if not post is None:
                _parts += ["z", "post", int(post)]

                if dev is None:
                    _parts += ["z"]

            if not dev is None:
                _parts += ["dev", int(dev)]

            parts += [tuple(_parts)]
        else:
            parts += [("z",)]

        if parts[0][0] > 1980:
            raise ValueError("Huge major version number '{major}' in '{version}', which might cause future problems".format(major=parts[0][0], version=version))

        return tuple(parts)

    @staticmethod
    def _normalize(*all_parts):
        def pad(parts, target):
            amount = target - len(parts[0])
            return (parts[0] + (0,) * amount,) + parts[1:]

        length = max([len(parts[0]) for parts in all_parts])
        return [pad(parts, length) for parts in all_parts]


def suggest_normalized_version(version, cls=Version):
    """
    Suggest a normalized version close to the given version string.

    If you have a version string that isn't rational (i.e. Version
    doesn't like it) then you might be able to get an equivalent (or close)
    rational version from this function.

    This does a number of simple normalizations to the given string, based
    on observation of versions currently in use on PyPI. Given a dump of
    those version during PyCon 2009, 4287 of them:
    - 2312 (53.93%) match Version without change
      with the automatic suggestion
    - 3474 (81.04%) match when using this suggestion method

    @param version {str} An irrational version string.
    @returns A rational version string, or None, if couldn't determine one.
    """
    try:
        cls(version)
        return version   # already rational
    except ValueError:
        pass

    rversion = version.lower()

    # part of this could use maketrans
    for orig, repl in (("-alpha", "a"), ("-beta", "b"), ("alpha", "a"),
                       ("beta", "b"), ("rc", "c"), ("-final", ""),
                       ("-pre", "c"),
                       ("-release", ""), (".release", ""), ("-stable", ""),
                       ("+", "."), ("_", "."), (" ", ""), (".final", ""),
                       ("final", "")):
        rversion = rversion.replace(orig, repl)

    # if something ends with dev or pre, we add a 0
    rversion = re.sub(r"pre$", r"pre0", rversion)
    rversion = re.sub(r"dev$", r"dev0", rversion)

    # if we have something like "b-2" or "a.2" at the end of the
    # version, that is probably beta, alpha, etc
    # let's remove the dash or dot
    rversion = re.sub(r"([abc]|rc)[\-\.](\d+)$", r"\1\2", rversion)

    # 1.0-dev-r371 -> 1.0.dev371
    # 0.1-dev-r79 -> 0.1.dev79
    rversion = re.sub(r"[\-\.](dev)[\-\.]?r?(\d+)$", r".\1\2", rversion)

    # Clean: 2.0.a.3, 2.0.b1, 0.9.0~c1
    rversion = re.sub(r"[.~]?([abc])\.?", r"\1", rversion)

    # Clean: v0.3, v1.0
    if rversion.startswith('v'):
        rversion = rversion[1:]

    # Clean leading '0's on numbers.
    #TODO: unintended side-effect on, e.g., "2003.05.09"
    # PyPI stats: 77 (~2%) better
    rversion = re.sub(r"\b0+(\d+)(?!\d)", r"\1", rversion)

    # Clean a/b/c with no version. E.g. "1.0a" -> "1.0a0". Setuptools infers
    # zero.
    # PyPI stats: 245 (7.56%) better
    rversion = re.sub(r"(\d+[abc])$", r"\g<1>0", rversion)

    # the 'dev-rNNN' tag is a dev tag
    rversion = re.sub(r"\.?(dev-r|dev\.r)\.?(\d+)$", r".dev\2", rversion)

    # clean the - when used as a pre delimiter
    rversion = re.sub(r"-(a|b|c)(\d+)$", r"\1\2", rversion)

    # a terminal "dev" or "devel" can be changed into ".dev0"
    rversion = re.sub(r"[\.\-](dev|devel)$", r".dev0", rversion)

    # a terminal "dev" can be changed into ".dev0"
    rversion = re.sub(r"(?![\.\-])dev$", r".dev0", rversion)

    # a terminal "final" or "stable" can be removed
    rversion = re.sub(r"(final|stable)$", "", rversion)

    # The 'r' and the '-' tags are post release tags
    #   0.4a1.r10       ->  0.4a1.post10
    #   0.9.33-17222    ->  0.9.33.post17222
    #   0.9.33-r17222   ->  0.9.33.post17222
    rversion = re.sub(r"\.?(r|-|-r)\.?(\d+)$", r".post\2", rversion)

    # Clean 'r' instead of 'dev' usage:
    #   0.9.33+r17222   ->  0.9.33.dev17222
    #   1.0dev123       ->  1.0.dev123
    #   1.0.git123      ->  1.0.dev123
    #   1.0.bzr123      ->  1.0.dev123
    #   0.1a0dev.123    ->  0.1a0.dev123
    # PyPI stats:  ~150 (~4%) better
    rversion = re.sub(r"\.?(dev|git|bzr)\.?(\d+)$", r".dev\2", rversion)

    # Clean '.pre' (normalized from '-pre' above) instead of 'c' usage:
    #   0.2.pre1        ->  0.2c1
    #   0.2-c1         ->  0.2c1
    #   1.0preview123   ->  1.0c123
    # PyPI stats: ~21 (0.62%) better
    rversion = re.sub(r"\.?(pre|preview|-c)(\d+)$", r"c\g<2>", rversion)

    # Tcl/Tk uses "px" for their post release markers
    rversion = re.sub(r"p(\d+)$", r".post\1", rversion)

    try:
        cls(rversion)
        return rversion
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
        if isinstance(version, string_types):
            version = Version(version)
        for operator, predicate in self.predicates:
            if not self._operators[operator](version, predicate):
                return False
        return True

    def __repr__(self):
        return self._string
