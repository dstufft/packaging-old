import pytest

from packaging.validation import validators
from packaging.version import Version, VersionPredicate


@pytest.mark.parametrize(("validator", "inp", "expected"), [
    # metadata/name
    (validators.metadata_name, "packaging", "packaging"),

    # metadata/version
    (validators.metadata_version, "1.0", Version("1.0")),

    # metadata/summary
    (validators.metadata_summary, "Test Summary", "Test Summary"),

    # metadata/description
    (validators.metadata_description, "Test description", "Test description"),

    # metadata/keywords
    (validators.metadata_keywords, ["packages", "foos"], ["packages", "foos"]),

    # metadata/author
    (validators.metadata_author, "Donald Stufft", "Donald Stufft"),

    # metadata/author-email
    (validators.metadata_author_email, "donald.stufft@gmail.com", "donald.stufft@gmail.com"),
    (validators.metadata_author_email, "Donald Stufft <donald.stufft@gmail.com>", "Donald Stufft <donald.stufft@gmail.com>"),

    # metadata/maintainer
    (validators.metadata_maintainer, "Donald Stufft", "Donald Stufft"),

    # metadata/maintainer-email
    (validators.metadata_maintainer_email, "donald.stufft@gmail.com", "donald.stufft@gmail.com"),
    (validators.metadata_maintainer_email, "Donald Stufft <donald.stufft@gmail.com>", "Donald Stufft <donald.stufft@gmail.com>"),

    # metadata/license
    (validators.metadata_license, "GPL version 3, excluding DRM provisions", "GPL version 3, excluding DRM provisions"),

    # metadata/classifiers
    (validators.metadata_classifiers, ["Development Status :: 5 - Production/Stable", "Intended Audience :: Developers"], ["Development Status :: 5 - Production/Stable", "Intended Audience :: Developers"]),

    # metadata/uris
    (validators.metadata_uris, {"Home page": "http://google.com/"}, {"Home page": "http://google.com/"}),

    # metadata/platforms
    (validators.metadata_platforms, ["ObscureUnix", "RareDOS"], ["ObscureUnix", "RareDOS"]),

    # metadata/supported-platforms
    (validators.metadata_supported_platforms, ["RedHat 7.2", "i386-win32-2791"], ["RedHat 7.2", "i386-win32-2791"]),

    # dependencies/python
    (validators.dependencies_python, ">=2.6", ">=2.6"),

    # dependencies/extras
    (validators.dependencies_extras, ["tests", "docs"], ["tests", "docs"]),

    # dependencies/setup-requires
    (validators.dependencies_setup_requires, ["custom_setup_command"], [VersionPredicate("custom_setup_command")]),

    # dependencies/requires
    (validators.dependencies_requires, ["pkginfo", "PasteDeploy", "zope.interface (>3.5.0)"], [VersionPredicate("pkginfo"), VersionPredicate("PasteDeploy"), VersionPredicate("zope.interface (>3.5.0)")]),

    # dependencies/provides
    (validators.dependencies_provides, ["packaging (0.1)"], [VersionPredicate("packaging (0.1)")]),

    # dependencies/obsoletes
    (validators.dependencies_obsoletes, ["distutils"], [VersionPredicate("distutils")]),

    # dependencies/externals
    (validators.dependencies_externals, ["C", "libpng (>=1.5)"], ["C", "libpng (>=1.5)"]),
])
def test_metadata_fields_valid(validator, inp, expected):
    assert validator.validate(inp) == expected


@pytest.mark.parametrize(("validator", "inp"), [
    # metadata/name
    (validators.metadata_name, "invalid/name"),
    (validators.metadata_name, None),

    # metadata/version
    (validators.metadata_version, "1.0-invalid"),
    (validators.metadata_version, None),

    # metadata/summary
    (validators.metadata_summary, None),

    # metadata/description
    (validators.metadata_description, None),

    # metadata/keywords
    (validators.metadata_keywords, "packages, foos"),
    (validators.metadata_keywords, "packages foos"),
    (validators.metadata_keywords, None),

    # metadata/author
    (validators.metadata_author, None),

    # metadata/author-email
    (validators.metadata_author_email, None),

    # metadata/maintainer
    (validators.metadata_maintainer, None),

    # metadata/maintainer-email
    (validators.metadata_maintainer_email, None),

    # metadata/license
    (validators.metadata_license, None),

    # metadata/classifiers
    (validators.metadata_classifiers, None),
    (validators.metadata_classifiers, "Development Status :: 5 - Production/Stable"),

    # metadata/uris
    (validators.metadata_uris, None),
    (validators.metadata_uris, {"A label that is way to long and shouldn't be verified": "http://google.com/"}),

    # metadata/platforms
    (validators.metadata_platforms, None),
    (validators.metadata_platforms, "ObscureUnix"),

    # metadata/supported-platforms
    (validators.metadata_supported_platforms, None),
    (validators.metadata_supported_platforms, "RedHat 7.2"),

    # dependencies/python
    (validators.dependencies_python, None),

    # dependencies/extras
    (validators.dependencies_extras, None),
    (validators.dependencies_extras, "tests"),
    (validators.dependencies_extras, ["tests[]", "docs"]),

    # dependencies/setup-requires
    (validators.dependencies_setup_requires, None),
    (validators.dependencies_setup_requires, "custom_setup_command"),
    (validators.dependencies_setup_requires, ["custom_setup_command )"]),

    # dependencies/requires
    (validators.dependencies_requires, None),

    # dependencies/provides
    (validators.dependencies_provides, None),

    # dependencies/obsoletes
    (validators.dependencies_obsoletes, None),

    # dependencies/externals
    (validators.dependencies_externals, None),
    (validators.dependencies_externals, [None]),
])
def test_metadata_fields_invalid(validator, inp):
    with pytest.raises(validators.SchemaError):
        validator.validate(inp)
