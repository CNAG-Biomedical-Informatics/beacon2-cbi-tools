from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Any

ARROW = "=>"

RESET = "[0m"
BOLD = "[1m"
WHITE = "[37m"
GREEN = "[32m"
YELLOW = "[33m"
BLUE = "[34m"
CYAN = "[36m"


def _plain(value: Any) -> str:
    if value is None:
        return "(undef)"
    text = str(value)
    return text if text else "(undef)"


def short_path(value: Any) -> str:
    if value is None:
        return "(undef)"
    text = str(value)
    if not text:
        return "(undef)"

    path = Path(text)
    display = text
    try:
        resolved = path.resolve()
        home = Path.home().resolve()
        try:
            return str(Path("~") / resolved.relative_to(home))
        except ValueError:
            display = str(resolved)
    except Exception:
        display = text

    parts = Path(display).parts
    if len(parts) > 4:
        return str(Path("...") / Path(*parts[-3:]))
    return display


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _colorize(text: str, *codes: str, use_color: bool) -> str:
    if not use_color:
        return text
    return ''.join(codes) + text + RESET


def _section(title: str, color: str, *, use_color: bool) -> None:
    print(_colorize(title, BOLD, color, use_color=use_color))


def _row(label: str, value: Any, *, use_color: bool) -> None:
    line = f"  {label:<12} {ARROW} {_plain(value)}"
    print(_colorize(line, WHITE, use_color=use_color))


def _print_mapping(title: str, data: Mapping[str, Any], color: str, *, use_color: bool) -> None:
    _section(title, color, use_color=use_color)
    if not data:
        print()
        return
    width = max(len(str(key)) for key in data.keys())
    for key in sorted(data.keys()):
        line = f"  {str(key):<{width}} {ARROW} {_plain(data[key])}"
        print(_colorize(line, WHITE, use_color=use_color))
    print()


def print_run_summary(*, arg: Mapping[str, Any], config: Mapping[str, Any], param: Mapping[str, Any], version: str, executable: Path, no_color: bool = False, no_emoji: bool = False) -> None:
    use_color = not no_color and os.environ.get('ANSI_COLORS_DISABLED') != '1'
    _section(f"BFF-Tools {version}", CYAN, use_color=use_color)
    _row("Executable", short_path(executable), use_color=use_color)
    _row("Mode", arg.get("mode"), use_color=use_color)
    _row("Input", short_path(arg.get("inputfile")), use_color=use_color)
    _row("Project", short_path(param.get("projectdir")), use_color=use_color)
    _row("Run ID", param.get("jobid"), use_color=use_color)
    _row("Genome", param.get("genome"), use_color=use_color)
    _row("Threads", arg.get("threads") or param.get("threadsless"), use_color=use_color)
    print()

    display_arg = {"mode": arg.get("mode")}
    flag_map = {
        "inputfile": "--i",
        "configfile": "--c",
        "paramfile": "--p",
        "threads": "--t",
        "debug": "--debug",
        "verbose": "--verbose",
        "nocolor": "--nc",
        "noemoji": "--ne",
        "projectdir_override": "--po",
    }
    for key, label in flag_map.items():
        value = arg.get(key)
        if value not in (None, False, ""):
            display_arg[label] = value

    _print_mapping("Arguments", display_arg, YELLOW, use_color=use_color)
    _print_mapping("Resolved Configuration", config, BLUE, use_color=use_color)

    display_param = dict(param)
    for nested in ("pipeline", "bff"):
        if nested in display_param:
            display_param[nested] = f"See {_plain(param.get('log'))}"
    _print_mapping("Input Parameters", display_param, GREEN, use_color=use_color)


def print_start_banner(*, no_color: bool = False, no_emoji: bool = False) -> None:
    use_color = not no_color and os.environ.get('ANSI_COLORS_DISABLED') != '1'
    _section("Starting BFF-Tools", CYAN, use_color=use_color)
    print(_colorize("  Pipeline execution begins now", WHITE, use_color=use_color))
    print()


def print_pipeline_status(pipeline: str, *, no_color: bool = False, no_emoji: bool = False) -> None:
    use_color = not no_color and os.environ.get('ANSI_COLORS_DISABLED') != '1'
    emoji_map = {
        'tsv2vcf': '📄',
        'vcf2bff': '🧬',
        'bff2html': '🌐',
        'bff2mongodb': '📥',
    }
    prefix = '' if no_emoji else f"{emoji_map.get(pipeline, '')} "
    print(_colorize(f"  {prefix}{pipeline.upper()}", BOLD, WHITE, use_color=use_color))


def print_finish_banner(*, runtime: float, goodbye: str, no_color: bool = False, no_emoji: bool = False) -> None:
    use_color = not no_color and os.environ.get('ANSI_COLORS_DISABLED') != '1'
    _section("BFF-Tools Finished", GREEN, use_color=use_color)
    _row("Status", "OK", use_color=use_color)
    _row("Runtime", format_duration(runtime), use_color=use_color)
    print()
    farewell = goodbye if no_emoji else f"👋 {goodbye}"
    print(_colorize(farewell, WHITE, use_color=use_color))
