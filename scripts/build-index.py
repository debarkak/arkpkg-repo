#!/usr/bin/env python3
"""Build the static index served by GitHub Pages from packages/*.ark files."""

import argparse
import hashlib
import html
import json
import re
import shutil
import tarfile
from pathlib import Path, PurePosixPath

import lz4.frame

PACKAGE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")
PACKAGE_ATOM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")

PAGE_STYLE = """
body { font-family: sans-serif; line-height: 1.5; margin: 0; padding: 2rem; }
main { margin: 0 auto; max-width: 72rem; }
label { display: block; margin-bottom: .35rem; }
input { box-sizing: border-box; max-width: 28rem; padding: .5rem; width: 100%; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; margin-top: 1rem; width: 100%; }
th, td { border: 1px solid #8888; padding: .5rem .65rem; text-align: left; }
th { white-space: nowrap; }
th button { background: none; border: 0; cursor: pointer; font: inherit; font-weight: 600; padding: 0; }
th button:focus-visible, input:focus-visible { outline: 2px solid; outline-offset: 2px; }
[hidden] { display: none !important; }
"""

PAGE_SCRIPT = """
(() => {
  const search = document.querySelector("#package-search");
  const table = document.querySelector("#package-table");
  const body = table.querySelector("tbody");
  const count = document.querySelector("#package-count");
  const headers = [...table.querySelectorAll("th[data-sort-key]")];
  const rows = [...body.querySelectorAll("tr[data-package-row]")];
  const noResults = body.querySelector("[data-no-results]");
  let sortKey = "name";
  let sortDirection = 1;

  function updateResults() {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const row of rows) {
      row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
      if (!row.hidden) visible += 1;
    }
    noResults.hidden = rows.length === 0 || visible > 0;
    count.textContent = rows.length === 0
      ? "0 packages available"
      : `${visible} of ${rows.length} packages shown`;
  }

  function sortBy(key) {
    if (key === sortKey) {
      sortDirection *= -1;
    } else {
      sortKey = key;
      sortDirection = 1;
    }
    const column = headers.findIndex((header) => header.dataset.sortKey === key);
    rows.sort((left, right) => {
      const a = left.cells[column].textContent.trim();
      const b = right.cells[column].textContent.trim();
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
        * sortDirection;
    });
    body.append(...rows, noResults);
    for (const header of headers) {
      const active = header.dataset.sortKey === sortKey;
      header.setAttribute("aria-sort", active
        ? (sortDirection === 1 ? "ascending" : "descending")
        : "none");
      header.querySelector("span").textContent = active
        ? (sortDirection === 1 ? "↑" : "↓")
        : "↕";
    }
    updateResults();
  }

  search.addEventListener("input", updateResults);
  for (const button of table.querySelectorAll("button[data-sort-key]")) {
    button.addEventListener("click", () => sortBy(button.dataset.sortKey));
  }
  updateResults();
})();
"""


def read_metadata(archive_path: Path) -> dict[str, str]:
    metadata = None
    has_package_tree = False
    with (
        lz4.frame.open(archive_path, "rb") as compressed,
        tarfile.open(fileobj=compressed, mode="r|") as archive,
    ):
        for member in archive:
            member_path = PurePosixPath(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"unsafe path in archive: {member.name!r}")
            normalized_name = "/".join(
                part for part in member_path.parts if part not in {"", "."}
            )
            if normalized_name == "package" or normalized_name.startswith("package/"):
                has_package_tree = True
            if normalized_name == "ARKPKG" and member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    break
                values: dict[str, str] = {}
                for line in stream.read().decode("utf-8").splitlines():
                    key, separator, value = line.partition(":")
                    if separator and key in {"Name", "Description", "Version", "Arch"}:
                        if key in values:
                            raise ValueError(f"duplicate {key} field")
                        values[key] = value.strip()
                required = {"Name", "Description", "Version", "Arch"}
                missing = required.difference(values)
                if missing:
                    raise ValueError(
                        f"missing metadata fields: {', '.join(sorted(missing))}"
                    )
                if metadata is not None:
                    raise ValueError("archive contains multiple root ARKPKG files")
                metadata = values
    if metadata is None:
        raise ValueError("archive does not contain a root ARKPKG metadata file")
    if not has_package_tree:
        raise ValueError("archive does not contain the required package/ tree")
    if not PACKAGE_NAME.fullmatch(metadata["Name"]):
        raise ValueError(f"invalid package name: {metadata['Name']!r}")
    if not PACKAGE_ATOM.fullmatch(metadata["Version"]):
        raise ValueError(f"invalid package version: {metadata['Version']!r}")
    if not PACKAGE_ATOM.fullmatch(metadata["Arch"]):
        raise ValueError(f"invalid package architecture: {metadata['Arch']!r}")
    return metadata


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_site(repo_root: Path, site_dir: Path) -> None:
    package_root = repo_root / "packages"
    if package_root.is_symlink():
        raise ValueError("packages/ must not be a symbolic link")
    site_packages = site_dir / "packages"
    site_dir.mkdir(parents=True, exist_ok=True)
    if site_packages.exists():
        shutil.rmtree(site_packages)
    site_packages.mkdir(parents=True)

    entries = []
    seen = set()
    for archive_path in (
        sorted(package_root.rglob("*.ark")) if package_root.exists() else []
    ):
        if archive_path.is_symlink() or not archive_path.is_file():
            raise ValueError(f"package archive must be a regular file: {archive_path}")
        metadata = read_metadata(archive_path)
        package_key = (metadata["Name"], metadata["Version"], metadata["Arch"])
        if package_key in seen:
            raise ValueError(
                f"duplicate package version and architecture: {package_key}"
            )
        seen.add(package_key)
        relative_path = archive_path.relative_to(repo_root)
        destination = site_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive_path, destination)

        digest = sha256_file(archive_path)
        entries.append(
            {
                "name": metadata["Name"],
                "version": metadata["Version"],
                "arch": metadata["Arch"],
                "description": metadata["Description"],
                "file": relative_path.as_posix(),
                "sha256": digest,
            }
        )

    entries.sort(key=lambda item: (item["name"].lower(), item["version"], item["arch"]))
    (site_dir / "index.json").write_text(
        json.dumps({"schema_version": 1, "packages": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    package_rows = "\n".join(
        "<tr data-package-row><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(item["name"]),
            html.escape(item["version"]),
            html.escape(item["arch"]),
            html.escape(item["description"]),
        )
        for item in entries
    )
    if not package_rows:
        package_rows = '<tr><td colspan="4">no packages published yet.</td></tr>'
    package_count = len(entries)
    table_headers = "".join(
        '<th data-sort-key="{0}" aria-sort="{1}"><button type="button" '
        'data-sort-key="{0}">{0} <span aria-hidden="true">{2}</span></button></th>'.format(
            key,
            "ascending" if key == "name" else "none",
            "↑" if key == "name" else "↕",
        )
        for key in ("name", "version", "architecture", "description")
    )
    (site_dir / "index.html").write_text(
        "<!doctype html>\n"
        '<html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<style>{PAGE_STYLE}</style>"
        "<title>arkpkg package repository</title>"
        "<body><main><h1>arkpkg package repository</h1>"
        "<p>static package repository for arkanaOS. configure it with:</p>"
        "<pre>arkpkg repo add arkanaOS https://arkana-team.github.io/arkpkg-repo</pre>"
        '<label for="package-search">search packages</label>'
        '<input id="package-search" type="search" autocomplete="off" '
        'placeholder="search by name, version, architecture, or description">'
        f'<p id="package-count" aria-live="polite">{package_count} packages available</p>'
        '<p><a href="index.json">package index (json)</a></p>'
        f'<div class="table-wrap"><table id="package-table"><thead><tr>{table_headers}'
        "</tr></thead><tbody>"
        f'{package_rows}<tr data-no-results hidden><td colspan="4">no packages match your search.</td></tr>'
        "</tbody></table></div>"
        f"<script>{PAGE_SCRIPT}</script>"
        "</main></body></html>\n",
        encoding="utf-8",
    )
    (site_dir / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, required=True)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    build_site(args.repo_root.resolve(), args.site_dir.resolve())


if __name__ == "__main__":
    main()
