import string

from .schema import Schema, And, Use, Optional, SchemaError
from ..version import Version, VersionPredicate
from ..compat import string_type

# manifest-version
manifest_version = Schema(And(string_type, "2.0"))

# metadata
metadata_name = Schema(And(string_type, lambda x: "/" not in x))  # @@@ What exactly is "ok" for a name?
metadata_version = Schema(Use(Version))
metadata_summary = Schema(string_type)
metadata_description = Schema(string_type)  # @@@ Verify ReST?
metadata_keywords = Schema([string_type])
metadata_author = Schema(string_type)
metadata_author_email = Schema(string_type)  # @@@ Verify Proper Email
metadata_maintainer = Schema(string_type)
metadata_maintainer_email = Schema(string_type)  # @@@ Verify Proper Email
metadata_license = Schema(string_type)
metadata_classifiers = Schema([string_type])
metadata_uris = Schema({And(string_type, lambda x: len(x) <= 32,): string_type})
metadata_platforms = Schema([string_type])
metadata_supported_platforms = Schema([string_type])

metadata = Schema({
    "name": metadata_name,
    "version": metadata_version,
    "summary": metadata_summary,
    Optional("description"): metadata_description,
    Optional("keywords"): metadata_keywords,
    Optional("author"): metadata_author,
    Optional("author-email"): metadata_author_email,
    Optional("maintainer"): metadata_maintainer,
    Optional("maintainer-email"): metadata_maintainer_email,
    Optional("classifiers"): metadata_classifiers,
    Optional("uris"): metadata_uris,
    Optional("platforms"): metadata_platforms,
    Optional("supported-platforms"): metadata_supported_platforms,
})

# dependencies
dependencies_python = Schema(string_type)  # @@@ Validate the version spec
dependencies_extras = Schema([And(string_type, lambda x: not set(x) - (set(string.digits + string.ascii_letters + string.punctuation) - set("[],")))])
dependencies_setup_requires = Schema([Use(VersionPredicate)])
dependencies_requires = Schema([Use(VersionPredicate)])
dependencies_provides = Schema([Use(VersionPredicate)])  # @@@ Any way to validate this has at least one that is name (version)?
dependencies_obsoletes = Schema([Use(VersionPredicate)])
dependencies_externals = Schema([string_type])

dependencies = Schema({
    Optional("python"): dependencies_python,
    Optional("extras"): dependencies_extras,
    Optional("setup-requires"): dependencies_setup_requires,
    Optional("requires"): dependencies_requires,
    "provides": dependencies_provides,
    Optional("obsoletes"): dependencies_obsoletes,
    Optional("externals"): dependencies_externals,
})


distribution = Schema({
    "manifest-version": manifest_version,
    "metadata": metadata,
    "dependencies": dependencies,
})
