from __future__ import annotations

from typing import Sequence

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    from .cli import main as cli_main

    return cli_main(list(argv) if argv is not None else None)
