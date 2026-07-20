from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools import console


class _TTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class ConsoleTests(unittest.TestCase):
    def test_colors_require_a_tty_and_respect_all_disable_controls(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(console.colors_enabled(stream=io.StringIO()))
            self.assertTrue(console.colors_enabled(stream=_TTY()))
            self.assertFalse(console.colors_enabled(no_color=True, stream=_TTY()))

        for variable in ("NO_COLOR", "ANSI_COLORS_DISABLED"):
            with self.subTest(variable=variable), mock.patch.dict(
                os.environ, {variable: ""}, clear=True
            ):
                self.assertFalse(console.colors_enabled(stream=_TTY()))

    def test_sections_and_status_lines_are_colored_but_messages_are_not(self) -> None:
        stream = _TTY()
        with mock.patch.dict(os.environ, {}, clear=True):
            console.section("Diagnostics", console.CYAN, stream=stream)
            console.status_line("PASS", "ready", indent=2, stream=stream)
            console.status_line("custom", "detail", stream=stream)

        rendered = stream.getvalue()
        self.assertIn("\033[", rendered)
        self.assertIn("[PASS]", rendered)
        self.assertIn("[CUSTOM]", rendered)
        self.assertIn("  \033[", rendered)

        plain = console.status_tag("WARN", width=9, no_color=True, stream=_TTY())
        self.assertEqual(plain, "[WARN]   ")

    def test_colorize_can_be_forced_for_existing_renderers(self) -> None:
        self.assertEqual(
            console.colorize("value", console.GREEN, use_color=False),
            "value",
        )
        self.assertEqual(
            console.colorize("value", console.GREEN, use_color=True),
            f"{console.GREEN}value{console.RESET}",
        )


if __name__ == "__main__":
    unittest.main()
