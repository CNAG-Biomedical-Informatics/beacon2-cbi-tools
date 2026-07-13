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
        value = redact_uri("https://user:password@example.org/api")
        self.assertEqual(value, "https://<redacted>@example.org/api")

    def test_redact_uri_handles_plain_invalid_and_ipv6_values(self) -> None:
        self.assertEqual(redact_uri("not-a-uri"), "not-a-uri")
        self.assertEqual(
            redact_uri("http://example.org/path"), "http://example.org/path"
        )
        self.assertEqual(
            redact_uri("mongodb://user:pass@[::1]:27017/db"),
            "mongodb://<redacted>@[::1]:27017/db",
        )
        self.assertEqual(redact_uri("http://[invalid"), "<redacted>")

    def test_redact_mapping_handles_nested_sensitive_keys(self) -> None:
        redacted = redact_mapping(
            {
                "service_uri": "https://root:secret@example.org/api",
                "nested": {"api_token": "abc", "ordinary": "value"},
            }
        )
        self.assertNotIn("root", redacted["service_uri"])
        self.assertNotIn("secret", redacted["service_uri"])
        self.assertEqual(redacted["nested"]["api_token"], "<redacted>")
        self.assertEqual(redacted["nested"]["ordinary"], "value")

    def test_redact_mapping_preserves_tuple_and_list_shapes(self) -> None:
        redacted = redact_mapping(
            {
                "values": ({"api_key": "secret"}, "plain"),
                "items": [{"password": "hidden"}],
            }
        )
        self.assertIsInstance(redacted["values"], tuple)
        self.assertEqual(redacted["values"][0]["api_key"], "<redacted>")
        self.assertEqual(redacted["items"][0]["password"], "<redacted>")

    def test_run_summary_does_not_print_uri_credentials(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_run_summary(
                arg={"mode": "vcf"},
                config={"service_uri": "https://root:secret@example.org/api"},
                param={"projectdir": "job", "pipeline": {}},
                version="test",
                executable=Path("bin/bff-tools"),
                no_color=True,
                no_emoji=True,
            )
        text = output.getvalue()
        self.assertNotIn("root", text)
        self.assertNotIn("secret", text)
        self.assertIn("https://<redacted>@example.org/api", text)


if __name__ == "__main__":
    unittest.main()
