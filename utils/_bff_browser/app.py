#!/usr/bin/env python3
"""Compatibility entry point for the retired Flask-based BFF Browser."""

from __future__ import annotations

import sys


MESSAGE = """\
The Flask BFF Browser has been retired.

Set `bff2html: true` in the bff-tools parameter file. The pipeline now writes a
standalone HTML report under:

    <projectdir>/browser/<job-id>.html

Open that file directly in a browser. No local web server or database is needed.
"""


def main() -> int:
    print(MESSAGE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
