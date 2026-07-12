from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.output import print_run_summary  # noqa: E402
from bff_tools.redaction import redact_mapping, redact_uri  # noqa: E402


class RedactionTests(unittest.TestCase):
    def test_redact_uri_preserves_target_but_removes_credentials(self) -> None:
        value = redact_uri("mongodb://user:password@mongo:27017/beacon?authSource=admin")
        self.assertEqual(value, "mongodb://<redacted>@mongo:27017/beacon?authSource=admin")

    def test_redact_mapping_handles_nested_sensitive_keys(self) -> None:
        redacted = redact_mapping(
            {
                "mongodburi": "mongodb://root:secret@mongo:27017/beacon",
                "nested": {"api_token": "abc", "ordinary": "value"},
            }
        )
        self.assertNotIn("root", redacted["mongodburi"])
        self.assertNotIn("secret", redacted["mongodburi"])
        self.assertEqual(redacted["nested"]["api_token"], "<redacted>")
        self.assertEqual(redacted["nested"]["ordinary"], "value")

    def test_run_summary_does_not_print_mongodb_credentials(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_run_summary(
                arg={"mode": "load"},
                config={"mongodburi": "mongodb://root:secret@mongo:27017/beacon"},
                param={"projectdir": "job", "pipeline": {}, "bff": {}},
                version="test",
                executable=Path("bin/bff-tools"),
                no_color=True,
                no_emoji=True,
            )
        text = output.getvalue()
        self.assertNotIn("root", text)
        self.assertNotIn("secret", text)
        self.assertIn("mongodb://<redacted>@mongo:27017/beacon", text)


if __name__ == "__main__":
    unittest.main()
