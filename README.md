![Banner](https://raw.githubusercontent.com/arkana-team/branding/refs/heads/main/arkana_banner.png)

<h1 align="center">arkpkg-repo</h1>
<p align="center">Optional packages for arkanaOS, served through GitHub Pages.</p>

## Use the repository

The package index and downloadable archives are published at:

- Repository: <https://arkana-team.github.io/arkpkg-repo>
- Package index: <https://arkana-team.github.io/arkpkg-repo/index.json>

Add the repository once, then search for and install optional packages with
`arkpkg`:

```sh
sudo arkpkg repo add arkanaOS https://arkana-team.github.io/arkpkg-repo
arkpkg repo list
arkpkg search nedit
sudo arkpkg install nedit
```

Replace `nedit` with a package name such as `dillo`, `xfe`, or `firefox`.
The package manager resolves dependencies from configured repositories.

## What's here

- `packages/*.ark` contains the built package archives served to clients.
- `packages/recipes/<name>/ARKPKG` records package metadata and dependencies.
- `scripts/` contains package builders, index generation, and repository tests.
- `.github/workflows/pages.yml` publishes the package index and archives through
  GitHub Pages when package files are merged into `main`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for package and contribution guidelines.
