from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import bff_tools.validator as validator  # noqa: E402
from bff_tools.validator import ValidatorError  # noqa: E402


class SchemaRegistryTests(unittest.TestCase):
    def test_current_schema_manifest_matches_complete_dereferenced_set(self) -> None:
        version = validator.current_schema_version()
        schema_dir = validator.default_schema_dir()
        manifest = json.loads(
            (schema_dir / "manifest.json").read_text(encoding="utf-8")
        )

        self.assertEqual(version, "v2.0.0")
        self.assertEqual(schema_dir.name, version)
        self.assertEqual(manifest["schemaVersion"], version)
        self.assertIs(manifest["dereferenced"], True)
        self.assertEqual(set(manifest["collections"]), set(validator.COLLECTIONS))

        for collection, metadata in manifest["collections"].items():
            with self.subTest(collection=collection):
                path = schema_dir / metadata["path"]
                payload = path.read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), metadata["sha256"])
                self.assertNotIn(b'"$ref"', payload)
                validator._schema_validator(
                    json.loads(payload),
                    check_schema=True,
                    schema_path=path,
                )

    def test_current_schema_pointer_reports_missing_invalid_and_unknown_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with mock.patch.object(validator, "SCHEMA_ROOT", root):
                with self.assertRaisesRegex(ValidatorError, "Cannot read"):
                    validator.current_schema_version()

                (root / "CURRENT").write_text("../outside\n", encoding="utf-8")
                with self.assertRaisesRegex(ValidatorError, "Invalid current"):
                    validator.current_schema_version()

                (root / "CURRENT").write_text("v9.9.9\n", encoding="utf-8")
                with self.assertRaisesRegex(ValidatorError, "does not exist"):
                    validator.default_schema_dir()

    def test_cineca_current_mirror_matches_schema_and_snapshot_checksums(self) -> None:
        root = ROOT / "CINECA_synthetic_cohort_EUROPE_UK1"
        current = root / "current"
        snapshot = root / "versions" / "v2.0.0"

        self.assertTrue(current.is_dir())
        self.assertFalse(current.is_symlink())
        self.assertTrue((root / "Beacon-v2-Models_CINECA_UK1.xlsx").is_symlink())
        self.assertTrue((root / "bff").is_symlink())
        self.assertEqual(
            (root / "Beacon-v2-Models_CINECA_UK1.xlsx").resolve(),
            (current / "Beacon-v2-Models_CINECA_UK1.xlsx").resolve(),
        )
        self.assertEqual((root / "bff").resolve(), (current / "bff").resolve())

        manifest = json.loads(
            (snapshot / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schemaVersion"], validator.current_schema_version())
        self.assertEqual(
            (current / "manifest.json").read_bytes(),
            (snapshot / "manifest.json").read_bytes(),
        )

        artifacts = [manifest["workbook"], *manifest["bffCollections"].values()]
        for metadata in artifacts:
            with self.subTest(path=metadata["path"]):
                payload = (snapshot / metadata["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), metadata["sha256"])
                self.assertEqual((current / metadata["path"]).read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
