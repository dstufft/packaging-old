import pytest

from packaging.version import Version as V
from packaging.version import suggest_normalized_version as suggest
from packaging.version import VersionPredicate


VERSIONS = [
    (V("1.0"), "1.0"),
    (V("1.1"), "1.1"),
    (V("1.2.3"), "1.2.3"),
    (V("1.2"), "1.2"),
    (V("1.2.3a4"), "1.2.3a4"),
    (V("1.2c4"), "1.2c4"),
    (V("4.17rc2"), "4.17rc2"),
    (V("1.2.3.4"), "1.2.3.4"),
    (V("1.2.3.4.0b3", drop_trailing_zeros=True), "1.2.3.4b3"),
    (V("1.2.0.0.0", drop_trailing_zeros=True), "1.2"),
    (V("1.0.dev345"), "1.0.dev345"),
    (V("1.0.post456.dev623"), "1.0.post456.dev623"),
]

PREDICATES = [
    "zope.interface (>3.5.0)",
    "AnotherProject (3.4)",
    "OtherProject (<3.0)",
    "NoVersion",
    "Hey (>=2.5,<2.7)",
]


def test_repr():
    assert repr(V("1.0")) == "Version('1.0')"


@pytest.mark.parametrize(("version", "expected"), VERSIONS)
def test_basic_versions(version, expected):
    assert str(version) == expected


@pytest.mark.parametrize(("version", "vstring"), VERSIONS)
def test_hash(version, vstring):
    assert hash(version) == hash(V(vstring))
    assert set([version]) == set([version, V(vstring)])


@pytest.mark.parametrize(("version",), [x[:1] for x in VERSIONS])
def test_from_parts(version):
    v2 = V.from_parts(*version.parts)
    assert version == v2
    assert str(version) == str(v2)


@pytest.mark.parametrize("version", [
    "1", "1.2a", "1.2.3b", "1.02", "1.2a03", "1.2a3.04", "1.2.dev.2",
    "1.2.dev.2", "1.2dev", "1.2.dev", "1.2.dev2.post2", "1.2.post2.dev3.post4"
])
def test_irrational_versions(version):
    with pytest.raises(ValueError):
        V(version)


def test_huge_version():
    assert str(V("1980.0")) == "1980.0"
    assert str(V("1981.0", error_on_huge_major_num=False)) == "1981.0"

    with pytest.raises(ValueError):
        V("1981.0")


def test_comparison():
    with pytest.raises(TypeError):
        V("1.2.0") == "1.2"

    with pytest.raises(TypeError):
        V("1.2") < "1.3"

    assert V("1.2.0") != V("1.2.3")
    assert V("1.2.0") < V("1.2.3")
    assert V("1.2.0") <= V("1.2.0")
    assert V("1.2.0") <= V("1.2.3")
    assert V("1.2.0") >= V("1.2.0")
    assert V("1.2.3") >= V("1.2.0")
    assert V("1.0") > V("1.0b2")
    assert V("1.0") > V("1.0c2")
    assert V("1.0") > V("1.0rc2")
    assert V("1.0rc2") > V("1.0rc1")
    assert V("1.0c4") > V("1.0c1")
    assert V("1.0") < V("1.0.post456.dev623")
    assert V("1.2.0rc1") <= V("1.2.0")
    assert V("1.0") > V("1.0c2")
    assert V("1.0") > V("1.0rc2")
    assert V("1.0rc2") > V("1.0rc1")
    assert V("1.0c4") > V("1.0c1")

    assert not V("1.2.0") == V("1.2.3")
    assert not V("1.2.0") < V("1.2.0")
    assert not V("1.2.3") <= V("1.2.0")
    assert not V("1.2.0") >= V("1.2.3")
    assert not V("1.2.0rc1") >= V("1.2.0")

    assert V("1.0.post456.dev623") < V("1.0.post456") < V("1.0.post1234")
    assert V("1.0") > V("1.0c2") > V("1.0c1") > V("1.0b2") > V("1.0b1") > V("1.0a2") > V("1.0a1")
    assert V("1.0.0") > V("1.0.0c2") > V("1.0.0c1") > V("1.0.0b2") > V("1.0.0b1") > V("1.0.0a2") > V("1.0.0a1")
    # assert (
    #         V("1.0a1")
    #       < V("1.0a2.dev456")
    #       < V("1.0a2")
    #       < V("1.0a2.1.dev456")
    #       < V("1.0a2.1")
    #       < V("1.0b1.dev456")
    #       < V("1.0b2")
    #       < V("1.0c1.dev456")
    #       < V("1.0c1")
    #       < V("1.0.dev7")
    #       < V("1.0.dev18")
    #       < V("1.0.dev456")
    #       < V("1.0.dev1234")
    #       < V("1.0rc1")
    #       < V("1.0rc2")
    #       < V("1.0")
    #       < V("1.0.post456.dev623")
    #       < V("1.0.post456")
    #     )


def test_comparision_trailing_zero():
    assert V("1.2.0") == V("1.2")
    assert V("1.2.0.0.0.0.0") == V("1.2")


@pytest.mark.parametrize(("input", "expected"), [
    ("1.0", "1.0"),
    ("1.0-alpha1", "1.0a1"),
    ("1.0c2", "1.0c2"),
    ("walla walla washington", None),
    ("2.4c1", "2.4c1"),
    ("v1.0", "1.0"),

    # setuptools
    ("0.4a1.r10", "0.4a1.post10"),
    ("0.7a1dev-r66608", "0.7a1.dev66608"),
    ("0.6a9.dev-r41475", "0.6a9.dev41475"),
    ("2.4preview1", "2.4c1"),
    ("2.4pre1", "2.4c1"),
    ("2.1-rc2", "2.1c2"),

    # PyPI
    ("0.1dev", "0.1.dev0"),
    ("0.1.dev", "0.1.dev0"),

    # Twisted development versions
    ("9.0.0+r2363", "9.0.0.post2363"),

    # pre-releases using markings like 'pre1'
    ("9.0.0pre1", "9.0.0c1"),

    # Tcl-TK post-releases 'p1', 'p2'
    ("1.4p1", "1.4.post1"),
])
def test_suggest_normalized_version(input, expected):
    assert suggest(input) == expected


@pytest.mark.parametrize(("version", "final"), [
    ("1.0", True),
    ("1.0.post456", True),
    ("1.0.dev1", False),
    ("1.0a2", False),
    ("1.0c3", False),
])
def test_version_is_final(version, final):
    assert V(version).is_final == final


@pytest.mark.parametrize("predicate", PREDICATES)
def test_basic_predicate(predicate):
    VersionPredicate(predicate)


@pytest.mark.parametrize("predicate", PREDICATES)
def test_repr_predicate(predicate):
    assert str(VersionPredicate(predicate)) == predicate


def test_invalid_predicate_raises():
    with pytest.raises(ValueError):
        VersionPredicate("")


@pytest.mark.parametrize(("predicate", "target", "matches"), [
    ("Hey (>=2.5,<2.7)", "2.6", True),
    ("Ho", "2.6", True),
    ("Ho (<3.0)", "2.6", True),
    ("Ho (<3.0,!=2.5)", "2.6.0", True),
    ("Ho (2.5)", "2.5.4", True),
    ("Hey (<=2.5)", "2.5.9", True),
    ("Hey (>=2.5)", "2.5.1", True),
    ("Hey 2.5", "2.5.1", True),
    ("virtualenv5 (1.0)", "1.0", True),
    ("virtualenv5", "1.0", True),
    ("vi5two", "1.0", True),
    ("5two", "1.0", True),
    ("vi5two 1.0", "1.0", True),
    ("5two 1.0", "1.0", True),

    ("Hey (>=2.5,!=2.6,<2.7)", "2.6", False),
    ("Ho (<3.0,!=2.6)", "2.6.0", False),
    ("Ho (!=2.5)", "2.5.2", False),
    ("Hey (<=2.5)", "2.6.0", False),
    ("Ho (<3.0,!=2.6)", "2.6.3", False),
])
def test_predicates_match(predicate, target, matches):
    assert VersionPredicate(predicate).match(target) == matches


@pytest.mark.parametrize(("predicate", "expected"), [
    ("Hey (<1.1)", "Hey"),
    ("Foo-Bar (1.1)", "Foo-Bar"),
    ("Foo Bar (1.1)", "Foo Bar"),
])
def test_predicate_name(predicate, expected):
    assert VersionPredicate(predicate).name == expected


def test_micro_predicate():
    predicate = VersionPredicate("zope.event (3.4.0)")
    assert predicate.match("3.4.0")
    assert not predicate.match("3.4.1")
