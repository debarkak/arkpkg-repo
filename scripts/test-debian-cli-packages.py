#!/usr/bin/env python3
"""Test license paths shared through package dependency symlinks."""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

BUILDER_PATH = Path(__file__).with_name("build-debian-cli-packages.py")
SPEC = importlib.util.spec_from_file_location("debian_cli_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load the Debian package builder")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class LicensePathTests(unittest.TestCase):
    def test_dependency_license_resolves_through_shared_doc_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "payload"
            docs = payload / "usr/share/doc"
            docs.mkdir(parents=True)
            (docs / "cpp-13").symlink_to("gcc-13-base")
            dependency_license = docs / "gcc-13-base/copyright"
            dependency_license.parent.mkdir()
            dependency_license.write_text("license text\n", encoding="utf-8")

            self.assertTrue(
                BUILDER.license_path_resolves_to(
                    payload,
                    "usr/share/doc/cpp-13/copyright",
                    "usr/share/doc/gcc-13-base/copyright",
                )
            )

    def test_unrelated_license_path_does_not_resolve_to_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "payload"
            docs = payload / "usr/share/doc"
            docs.mkdir(parents=True)
            (docs / "cpp-13").symlink_to("gcc-13-base")

            self.assertFalse(
                BUILDER.license_path_resolves_to(
                    payload,
                    "usr/share/doc/cpp-13/copyright",
                    "usr/share/doc/libgcc-13/copyright",
                )
            )

    def test_license_source_can_name_an_aliased_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "payload"
            docs = payload / "usr/share/doc"
            docs.mkdir(parents=True)
            (docs / "tcpd").symlink_to("libwrap0")
            license_file = docs / "libwrap0/copyright"
            license_file.parent.mkdir()
            license_file.write_text("license text\n", encoding="utf-8")

            self.assertTrue(
                BUILDER.license_is_provided_by_dependency(
                    payload,
                    "usr/share/doc/tcpd/copyright",
                    "usr/share/doc/libwrap0/copyright",
                    ["libwrap-libs"],
                    "libwrap0",
                    "libwrap-libs",
                )
            )

    def test_requested_closure_reuses_an_exact_repository_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            recipe = repo_root / "packages/recipes/runtime/ARKPKG"
            archive = repo_root / "packages/runtime-1.0-x86_64.ark"
            recipe.parent.mkdir(parents=True)
            archive.parent.mkdir(parents=True, exist_ok=True)
            recipe.write_text(
                "Name: runtime\nVersion: 1.0\nArch: x86_64\n",
                encoding="utf-8",
            )
            archive.touch()
            packages = [
                {"name": "app", "dependencies": ["runtime"]},
                {"name": "runtime", "version": "1.0", "arch": "x86_64"},
            ]

            closure = BUILDER.requested_package_closure(
                repo_root, packages, {"app"}
            )

            self.assertEqual(closure, {"app"})


class PayloadOmissionTests(unittest.TestCase):
    def test_omits_only_the_declared_payload_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "package"
            binaries = payload / "usr/bin"
            binaries.mkdir(parents=True)
            (binaries / "pdfinfo").write_text("duplicate\n", encoding="utf-8")
            (binaries / "pdfsig").write_text("unique\n", encoding="utf-8")

            BUILDER.omit_payload_paths(
                payload,
                {"usr/bin/pdfinfo": "provided by xpdf-tools"},
                "poppler-utils",
            )

            self.assertFalse((binaries / "pdfinfo").exists())
            self.assertEqual(
                (binaries / "pdfsig").read_text(encoding="utf-8"), "unique\n"
            )

    def test_omissions_reject_traversal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "package"
            payload.mkdir()

            with self.assertRaisesRegex(ValueError, "unsafe omitted payload path"):
                BUILDER.omit_payload_paths(
                    payload, {"../outside": "duplicate"}, "sample"
                )

    def test_omissions_cannot_follow_a_symlink_outside_the_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "package"
            outside = root / "outside"
            payload.mkdir()
            outside.mkdir()
            secret = outside / "secret"
            secret.write_text("keep\n", encoding="utf-8")
            (payload / "escape").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "escapes its payload"):
                BUILDER.omit_payload_paths(
                    payload, {"escape/secret": "duplicate"}, "sample"
                )

            self.assertTrue(secret.is_file())

    def test_omissions_require_the_declared_path_to_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "package"
            payload.mkdir()

            with self.assertRaisesRegex(ValueError, "does not exist in payload"):
                BUILDER.omit_payload_paths(
                    payload, {"usr/bin/missing": "duplicate"}, "sample"
                )


class RepositoryProviderTests(unittest.TestCase):
    def test_runtime_analysis_reports_needed_sonames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary)
            shutil.copy2("/bin/true", payload / "true")

            dependencies, missing, needed = BUILDER.runtime_dependency_details(
                payload, {"libc.so.6": "libc"}, None, "sample"
            )

            self.assertIn("libc", dependencies)
            self.assertIn("libc.so.6", needed)
            self.assertEqual(missing, [])

    def test_public_library_provider_beats_private_application_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            recipes = Path(temporary)
            private = recipes / "firefox-esr" / "ARKPKG"
            public = recipes / "libnss3" / "ARKPKG"
            private.parent.mkdir(parents=True)
            public.parent.mkdir(parents=True)
            private.write_text(
                "Name: firefox-esr\n"
                "Provides: libnss3.so=/usr/lib/firefox-esr/libnss3.so\n",
                encoding="utf-8",
            )
            public.write_text(
                "Name: libnss3\n"
                "Provides: libnss3.so=/usr/lib/x86_64-linux-gnu/libnss3.so.3\n",
                encoding="utf-8",
            )

            providers = BUILDER.repository_providers(recipes)

            self.assertEqual(providers["libnss3.so"], "libnss3")

    def test_private_provider_is_kept_when_no_public_library_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            recipes = Path(temporary)
            recipe = recipes / "libstrongswan" / "ARKPKG"
            recipe.parent.mkdir(parents=True)
            recipe.write_text(
                "Name: libstrongswan\n"
                "Provides: libstrongswan.so.0=/usr/lib/ipsec/libstrongswan.so.0\n",
                encoding="utf-8",
            )

            providers = BUILDER.repository_providers(recipes)

            self.assertEqual(providers["libstrongswan.so.0"], "libstrongswan")


if __name__ == "__main__":
    unittest.main()
