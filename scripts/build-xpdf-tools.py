#!/usr/bin/env python3
"""Build the Xpdf command-line tools against the arkanaOS sysroot."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid
from pathlib import Path, PurePosixPath

NAME = "xpdf-tools"
VERSION = "4.06"
SOURCE_ROOT = f"xpdf-{VERSION}"
SOURCE_URL = f"https://dl.xpdfreader.com/{SOURCE_ROOT}.tar.gz"
SOURCE_SHA256 = "1c38f527c46caee0f712386d42a885b96a31ed9ce11904e872559859894d137e"
TOOLS = (
    "pdfdetach",
    "pdffonts",
    "pdfimages",
    "pdfinfo",
    "pdftohtml",
    "pdftoppm",
    "pdftopng",
    "pdftops",
    "pdftotext",
)


def privileged(command: list[str], *, log: Path | None = None) -> None:
    full = command if os.geteuid() == 0 else ["sudo", *command]
    if log is None:
        subprocess.run(full, check=True)
    else:
        with log.open("w", encoding="utf-8") as output:
            subprocess.run(full, stdout=output, stderr=subprocess.STDOUT, check=True)


def obtain_source(cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    archive_path = cache / f"{SOURCE_ROOT}.tar.gz"
    if not archive_path.is_file():
        request = urllib.request.Request(
            SOURCE_URL, headers={"User-Agent": "arkpkg-repo-xpdf-builder/1"}
        )
        with (
            urllib.request.urlopen(request, timeout=90) as response,
            archive_path.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"SHA-256 mismatch for {archive_path.name}: {digest}")

    roots = set()
    with tarfile.open(archive_path, "r:gz") as source:
        for member in source:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe source path: {member.name!r}")
            if path.parts:
                roots.add(path.parts[0])
    if roots != {SOURCE_ROOT}:
        raise ValueError(f"unexpected source roots: {sorted(roots)}")
    return archive_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sysroot", type=Path, required=True)
    parser.add_argument("--arkpkg-build", type=Path, required=True)
    parser.add_argument("--source-cache", type=Path, default=Path("/tmp/arkpkg-xpdf-sources"))
    parser.add_argument(
        "--output-staging", type=Path, default=Path("/tmp/arkpkg-xpdf-staging")
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--jobs", type=int, default=1, choices=(1, 2))
    args = parser.parse_args()

    sysroot = args.sysroot.resolve()
    for binary in ("cmake", "gcc", "g++", "make", "tar", "strip"):
        if not (sysroot / "usr/bin" / binary).exists():
            raise FileNotFoundError(f"target build root lacks /usr/bin/{binary}")
    source = obtain_source(args.source_cache.resolve())
    output_staging = args.output_staging.resolve()
    shutil.rmtree(output_staging, ignore_errors=True)
    output_staging.mkdir(parents=True)

    work_rel = f"/tmp/arkpkg-xpdf-{uuid.uuid4().hex}"
    work_host = sysroot / work_rel.lstrip("/")
    logs = Path(tempfile.mkdtemp(prefix="arkpkg-xpdf-logs-"))
    log = logs / "build.log"
    shell = "\n".join(
        (
            "set -eu",
            f"cd {work_rel}",
            f"/usr/bin/tar -xzf {SOURCE_ROOT}.tar.gz",
            (
                f"/usr/bin/cmake -S {SOURCE_ROOT} -B build "
                "-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr "
                "-DCMAKE_INSTALL_BINDIR=bin -DCMAKE_INSTALL_MANDIR=share/man "
                "-DUSE_XDG=ON -DNO_FONTCONFIG=ON "
                "-DCMAKE_DISABLE_FIND_PACKAGE_Qt4=ON "
                "-DCMAKE_DISABLE_FIND_PACKAGE_Qt5Widgets=ON "
                "-DCMAKE_DISABLE_FIND_PACKAGE_Qt6Widgets=ON"
            ),
            f"/usr/bin/cmake --build build --parallel {args.jobs}",
            (
                f"/usr/bin/install -d -m 755 {work_rel}/payload/usr/bin "
                f"{work_rel}/payload/usr/share/man/man1 "
                f"{work_rel}/payload/usr/share/man/man5"
            ),
            *(
                f"/usr/bin/install -m 755 build/xpdf/{tool} "
                f"{work_rel}/payload/usr/bin/{tool}"
                for tool in TOOLS
            ),
            *(
                f"/usr/bin/install -m 644 {SOURCE_ROOT}/doc/{tool}.1 "
                f"{work_rel}/payload/usr/share/man/man1/{tool}.1"
                for tool in TOOLS
            ),
            (
                f"/usr/bin/install -m 644 {SOURCE_ROOT}/doc/xpdfrc.5 "
                f"{work_rel}/payload/usr/share/man/man5/xpdfrc.5"
            ),
            (
                f"/usr/bin/install -D -m 644 {SOURCE_ROOT}/COPYING "
                f"{work_rel}/payload/usr/share/licenses/{NAME}/COPYING"
            ),
            (
                f"/usr/bin/install -m 644 {SOURCE_ROOT}/COPYING3 "
                f"{work_rel}/payload/usr/share/licenses/{NAME}/COPYING3"
            ),
            " ".join(f"test -x {work_rel}/payload/usr/bin/{tool} &&" for tool in TOOLS)
            + " true",
            f"/usr/bin/strip --strip-unneeded {work_rel}/payload/usr/bin/*",
        )
    )
    try:
        privileged(["install", "-d", "-m", "755", str(work_host)])
        privileged(["install", "-m", "644", str(source), str(work_host / source.name)])
        try:
            privileged(
                [
                    "chroot",
                    str(sysroot),
                    "/usr/bin/env",
                    "LC_ALL=C",
                    "LANG=C",
                    "PATH=/usr/bin:/bin",
                    "/usr/bin/bash",
                    "-c",
                    shell,
                ],
                log=log,
            )
        except subprocess.CalledProcessError:
            print(
                "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]),
                file=sys.stderr,
            )
            raise

        payload = work_host / "payload"
        for tool in TOOLS:
            if not (payload / "usr/bin" / tool).is_file():
                raise FileNotFoundError(f"Xpdf failed to build {tool}")
        shutil.copytree(payload, output_staging, dirs_exist_ok=True, symlinks=True)
    finally:
        privileged(
            [
                "/usr/bin/python3",
                "-c",
                "import shutil,sys; shutil.rmtree(sys.argv[1],ignore_errors=True)",
                str(work_host),
            ]
        )
        shutil.rmtree(logs, ignore_errors=True)

    repo_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        str(repo_root / "scripts/build-arkana-packages.py"),
        "--staging",
        str(output_staging),
        "--arkpkg-build",
        str(args.arkpkg_build.resolve()),
        "--packages",
        NAME,
    ]
    if args.output_dir is not None:
        command.extend(("--output-dir", str(args.output_dir.resolve())))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
