# Contributing to arkpkg-repo

Contributions of useful, optional packages and improvements to the repository
tools are welcome. Open a focused pull request against `main`; do not merge your
own contribution unless you have repository permission to do so.

## Repository layout

- `packages/*.ark` contains the archives clients download.
- `packages/recipes/<name>/ARKPKG` contains each package's metadata.
- `scripts/build-*.py` builds packages from pinned upstream sources or staged
  sysroot files.
- `scripts/build-index.py` creates the static Pages site and `index.json`.
- `scripts/test-packages.py` checks archive metadata, dependencies, file
  ownership, and install/verify/remove behavior.

## Adding or updating a package

Check existing package names and payload paths first. Add a recipe with accurate
`Name`, `Description`, `Version`, `Arch`, `URL`, `License`, and `Maintainer`
fields. Add `Dependencies` and `Provides` where applicable, with one value per
indented line. Use `any` for architecture-independent data packages and
`x86_64` for architecture-specific packages.

Build output must be a valid `.ark` archive with a root `ARKPKG` file and a
non-empty `package/` payload. Name the archive
`<name>-<version>-<arch>.ark`, matching its metadata. Use an existing helper
where possible; inspect its options with `python3 scripts/build-<helper>.py
--help`. For staged packages, the general builder accepts a sysroot and the
`arkpkg-build` executable, for example:

```sh
python3 scripts/build-arkana-packages.py \
  --staging /path/to/sysroot \
  --arkpkg-build /path/to/arkpkg-build \
  --packages dillo
```

Pin upstream versions and verify source checksums in build helpers. Preserve
upstream license files. Keep package payload ownership disjoint: files must not
be shipped by two packages. The `system-docs` archive is generated to exclude
files already owned by other packages.

## Validation

Install the Python `lz4` module and have a built `arkpkg` executable available.
Run the repository audit and generate a preview of the Pages site:

```sh
ruff check scripts/*.py
python3 -m py_compile scripts/*.py
python3 scripts/test-packages.py --repo-root . --arkpkg /path/to/arkpkg
python3 scripts/build-index.py --repo-root . --site-dir /tmp/arkpkg-site
```

The full package test uses a temporary root and installs, verifies, and removes
every archive. Inspect the generated index and site before submitting. Do not
commit the generated `site/` directory; GitHub Actions publishes it after
package changes reach `main`.

## Pull requests

Use a specific title such as `feat: add xfe package` or
`fix: correct pkgconf package metadata`. Describe the package, its upstream
source and license, dependencies, and the checks you ran. Keep package names
lowercase and spell the distribution name `arkanaOS`.
