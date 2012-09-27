#!/usr/bin/env python2.7
"""
Checks packaging.version against PyPI and setuptools/distribute
"""
from distutils.version import StrictVersion, LooseVersion
from packaging.version import Version, suggest
from pkg_resources import parse_version
from xmlrpclib import ServerProxy

import pickle

import progress.bar


client = ServerProxy("http://pypi.python.org/pypi")

results = {
    "packaging.version": {
        "valid": set(),
        "fuzzy": set(),
        "invalid": set(),
    },
    "ordering": {
        "valid": set(),
        "invalid": set(),
        "unknown": set(),
    },
}


try:
    with open("version_data.pickle", "rb") as fp:
        packages, package_versions, all_versions = pickle.load(fp)
except IOError:
    packages = client.list_packages()
    package_versions = [(p, client.package_releases(p, True)) for p in progress.bar.ShadyBar("Loading versions", max=len(packages)).iter(packages)]

    all_versions = []
    for p, vs in package_versions:
        all_versions.extend([(p, v) for v in vs])

    with open("version_data.pickle", "wb") as fp:
        pickle.dump((packages, package_versions, all_versions), fp, -1)

for package, ver in progress.bar.ShadyBar("Trying packaging.version", max=len(all_versions)).iter(all_versions):
    try:
        Version(ver)
    except ValueError:
        suggested = suggest(ver)

        try:
            Version(suggested)
        except (ValueError, TypeError):
            results["packaging.version"]["invalid"].add((package, ver))
        else:
            results["packaging.version"]["fuzzy"].add((package, ver))
    else:
        results["packaging.version"]["valid"].add((package, ver))


for package, versions in progress.bar.ShadyBar("Check version ordering", max=len(package_versions)).iter(package_versions):
    pvers = []

    valid = True

    for v in versions:
        try:
            pvers.append((v, Version(v)))
        except ValueError:
            suggested = suggest(v)

            try:
                pvers.append((v, Version(suggested)))
            except (ValueError, TypeError):
                # Can't order this set
                results["ordering"]["unknown"].add((package, tuple(versions)))
                valid = False
                break

    if not valid:
        continue

    rvers = [(v, parse_version(v)) for v in versions]

    # Sort the lists
    pvers.sort(key=lambda x: x[1])
    rvers.sort(key=lambda x: x[1])

    if [p[0] for p in pvers] == [r[0] for r in rvers]:
        results["ordering"]["valid"].add((package, tuple(versions)))
    else:
        results["ordering"]["invalid"].add((package, tuple(versions)))


print ""
print "packaging.version"
print "================="
print "  Valid: {}".format(len(results["packaging.version"]["valid"]))
print "  Fuzzy: {}".format(len(results["packaging.version"]["fuzzy"]))
print "  Invalid: {}".format(len(results["packaging.version"]["invalid"]))
print "  Total: {}".format(len(results["packaging.version"]["valid"]) + len(results["packaging.version"]["fuzzy"]) + len(results["packaging.version"]["invalid"]))
print ""
print "ordering"
print "========"
print "  Valid: {}".format(len(results["ordering"]["valid"]))
print "  Invalid: {}".format(len(results["ordering"]["invalid"]))
print "  Unknown: {}".format(len(results["ordering"]["unknown"]))
print "  Total: {}".format(len(results["ordering"]["valid"]) + len(results["ordering"]["invalid"]) + len(results["ordering"]["unknown"]))
