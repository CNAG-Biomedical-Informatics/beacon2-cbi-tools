from __future__ import annotations

import os
import sys
from typing import TextIO


RESET = "\033[0m"
BOLD = "\033[1m"
WHITE = "\033[37m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"


def colors_enabled(
    *,
    no_color: bool = False,
    stream: TextIO | None = None,
) -> bool:
    """Return whether ANSI styling is appropriate for the selected stream."""
    if (
        no_color
        or "NO_COLOR" in os.environ
        or "ANSI_COLORS_DISABLED" in os.environ
    ):
        return False
    target = stream or sys.stdout
    return bool(target.isatty())


def colorize(
    value: str,
    *codes: str,
    no_color: bool = False,
    stream: TextIO | None = None,
    use_color: bool | None = None,
) -> str:
    enabled = (
        colors_enabled(no_color=no_color, stream=stream)
        if use_color is None
        else use_color
    )
    if not enabled:
        return value
    return "".join(codes) + value + RESET


def section(
    title: str,
    color: str = WHITE,
    *,
    no_color: bool = False,
    stream: TextIO | None = None,
) -> None:
    target = stream or sys.stdout
    print(
        colorize(title, BOLD, color, no_color=no_color, stream=target),
        file=target,
    )


def status_tag(
    status: str,
    *,
    width: int = 0,
    no_color: bool = False,
    stream: TextIO | None = None,
) -> str:
    normalized = status.upper()
    color = {
        "PASS": GREEN,
        "FAIL": RED,
        "WARN": YELLOW,
        "SKIP": YELLOW,
        "INFO": CYAN,
    }.get(normalized, WHITE)
    token = f"[{normalized}]"
    rendered = colorize(
        token,
        BOLD,
        color,
        no_color=no_color,
        stream=stream,
    )
    return rendered + (" " * max(0, width - len(token)))


def status_line(
    status: str,
    message: str,
    *,
    indent: int = 0,
    no_color: bool = False,
    stream: TextIO | None = None,
) -> None:
    target = stream or sys.stdout
    tag = status_tag(status, no_color=no_color, stream=target)
    print(f"{' ' * indent}{tag} {message}", file=target)
