from __future__ import annotations

import contextlib
import hashlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import cli  # noqa: E402
from bff_tools import resource_installer as installer  # noqa: E402
from bff_tools.config import DATA_ROOT_ENV  # noqa: E402


class ResourceInstallerTests(unittest.TestCase):
    def test_r3_bundle_definition_is_complete(self) -> None:
        self.assertEqual(installer.BUNDLE_REVISION, "r3")
        self.assertEqual(len(installer.PART_NAMES), 7)
        self.assertEqual(
            set(installer.BUNDLE_FILES),
            {installer.CHECKSUM_NAME, *installer.PART_NAMES},
        )
        self.assertTrue(all(installer.BUNDLE_FILES.values()))

    def test_data_directory_uses_explicit_path_then_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit = Path(tmpdir) / "explicit"
            configured = Path(tmpdir) / "configured"
            with mock.patch.dict(
                "os.environ", {DATA_ROOT_ENV: str(configured)}, clear=False
            ):
                self.assertEqual(
                    installer.resolve_data_directory(str(explicit)),
                    explicit.resolve(),
                )
                self.assertEqual(
                    installer.resolve_data_directory(), configured.resolve()
                )

        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(installer.ResourceInstallError, DATA_ROOT_ENV):
                installer.resolve_data_directory()

    def test_manual_links_include_every_file_and_folder(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            installer.print_download_links()
        rendered = stdout.getvalue()
        self.assertIn(installer.FOLDER_URL, rendered)
        for filename, file_id in installer.BUNDLE_FILES.items():
            self.assertIn(filename, rendered)
            self.assertIn(file_id, rendered)

    def test_download_only_fetches_missing_or_empty_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "present").write_bytes(b"complete")
            (data_dir / "empty").touch()
            calls = []

            def download(url: str, destination: Path) -> str:
                calls.append((url, destination.name))
                destination.write_bytes(destination.name.encode("ascii"))
                return str(destination)

            with mock.patch.object(
                installer,
                "BUNDLE_FILES",
                {"present": "id-present", "empty": "id-empty", "missing": "id-missing"},
            ), contextlib.redirect_stdout(io.StringIO()):
                installer.download_missing_files(data_dir, downloader=download)

            self.assertEqual(
                calls,
                [
                    (installer.google_drive_url("id-empty"), "empty"),
                    (installer.google_drive_url("id-missing"), "missing"),
                ],
            )

            with mock.patch.object(
                installer, "BUNDLE_FILES", {"bad": "id-bad"}
            ), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(installer.ResourceInstallError, "Download failed"):
                    installer.download_missing_files(
                        data_dir, downloader=lambda _url, _destination: None
                    )

            with mock.patch("gdown.download", side_effect=RuntimeError("blocked")):
                with self.assertRaisesRegex(installer.ResourceInstallError, "blocked"):
                    installer._gdown_download("https://example.test", data_dir / "part")

            destination = data_dir / "resumable"
            with mock.patch(
                "gdown.download", return_value=str(destination)
            ) as download:
                self.assertEqual(
                    installer._gdown_download("https://example.test", destination),
                    str(destination),
                )
            download.assert_called_once_with(
                "https://example.test",
                str(destination),
                quiet=False,
                resume=True,
            )

    def test_checksum_parsing_and_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            parts = ("bundle.part-00", "bundle.part-01")
            payloads = (b"first", b"second")
            for name, payload in zip(parts, payloads):
                (data_dir / name).write_bytes(payload)
            manifest = data_dir / "bundle.md5"
            manifest.write_text(
                "\n".join(
                    f"{hashlib.md5(payload, usedforsecurity=False).hexdigest()}  {name}"
                    for name, payload in zip(parts, payloads)
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(installer, "PART_NAMES", parts), mock.patch.object(
                installer, "CHECKSUM_NAME", manifest.name
            ), contextlib.redirect_stdout(io.StringIO()):
                installer.verify_parts(data_dir)
                (data_dir / parts[1]).write_bytes(b"corrupt")
                with self.assertRaisesRegex(installer.ResourceInstallError, "Checksum failed"):
                    installer.verify_parts(data_dir)

            manifest.write_text("not a checksum\n", encoding="utf-8")
            with mock.patch.object(installer, "PART_NAMES", parts):
                with self.assertRaisesRegex(installer.ResourceInstallError, "does not cover"):
                    installer.read_part_checksums(manifest)

            with self.assertRaisesRegex(installer.ResourceInstallError, "Cannot read"):
                installer.read_part_checksums(data_dir / "missing.md5")

    def test_archive_assembly_is_streamed_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            parts = ("bundle.part-00", "bundle.part-01")
            (data_dir / parts[0]).write_bytes(b"abc")
            (data_dir / parts[1]).write_bytes(b"def")
            with mock.patch.object(installer, "PART_NAMES", parts), mock.patch.object(
                installer, "BUNDLE_NAME", "bundle.tar.gz"
            ), contextlib.redirect_stdout(io.StringIO()):
                archive = installer.assemble_archive(data_dir)
                self.assertEqual(archive.read_bytes(), b"abcdef")
                self.assertEqual(installer.assemble_archive(data_dir), archive)

    def test_extraction_checks_command_and_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            archive = data_dir / "bundle.tar.gz"
            archive.touch()

            def successful_run(command, *, check):
                self.assertTrue(check)
                self.assertEqual(command[1:3], ["-xzf", str(archive)])
                (data_dir / "databases").mkdir()
                (data_dir / "soft").mkdir()
                return subprocess.CompletedProcess(command, 0)

            with mock.patch("bff_tools.resource_installer.shutil.which", return_value="/bin/tar"), contextlib.redirect_stdout(io.StringIO()):
                installer.extract_archive(archive, data_dir, run=successful_run)

            empty = data_dir / "empty"
            empty.mkdir()
            with mock.patch("bff_tools.resource_installer.shutil.which", return_value=None), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(installer.ResourceInstallError, "tar"):
                    installer.extract_archive(archive, empty)

            with mock.patch("bff_tools.resource_installer.shutil.which", return_value="/bin/tar"), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(installer.ResourceInstallError, "Cannot extract"):
                    installer.extract_archive(
                        archive,
                        empty,
                        run=mock.Mock(side_effect=subprocess.CalledProcessError(2, "tar")),
                    )

    def test_install_is_idempotent_and_creates_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            for name in installer.EXPECTED_DIRECTORIES:
                (data_dir / name).mkdir()
            (data_dir / installer.INSTALL_MARKER).write_text("r3\n", encoding="utf-8")
            with mock.patch.object(
                installer, "download_missing_files"
            ) as download_mock, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.install_resources(data_dir), data_dir)
            download_mock.assert_not_called()
            self.assertTrue((data_dir / "tmp").is_dir())

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / installer.EXPECTED_DIRECTORIES[0]).mkdir()
            with self.assertRaisesRegex(installer.ResourceInstallError, "clean directory"):
                installer.install_resources(data_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            archive = data_dir / "bundle.tar.gz"

            def extract(_archive: Path, target: Path) -> None:
                for name in installer.EXPECTED_DIRECTORIES:
                    (target / name).mkdir()

            with mock.patch.object(
                installer, "download_missing_files"
            ) as download_mock, mock.patch.object(
                installer, "verify_parts"
            ) as verify_mock, mock.patch.object(
                installer, "assemble_archive", return_value=archive
            ) as assemble_mock, mock.patch.object(
                installer, "extract_archive", side_effect=extract
            ) as extract_mock, contextlib.redirect_stdout(io.StringIO()):
                installer.install_resources(data_dir)

            download_mock.assert_called_once_with(data_dir)
            verify_mock.assert_called_once_with(data_dir)
            assemble_mock.assert_called_once_with(data_dir)
            extract_mock.assert_called_once_with(archive, data_dir)
            self.assertTrue((data_dir / "tmp").is_dir())
            self.assertEqual(
                (data_dir / installer.INSTALL_MARKER).read_text(encoding="utf-8"),
                "r3\n",
            )

    def test_cli_prints_links_and_reports_missing_directory(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(cli.main(["install-resources", "--print-links"]), 0)
        self.assertIn(installer.BUNDLE_REVISION, stdout.getvalue())

        stderr = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=True), contextlib.redirect_stderr(stderr):
            self.assertEqual(cli.main(["install-resources"]), 1)
        self.assertIn(DATA_ROOT_ENV, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
