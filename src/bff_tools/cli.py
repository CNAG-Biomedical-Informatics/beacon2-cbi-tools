from __future__ import annotations

import argparse
import random
import subprocess
import sys
import threading
import time
from pathlib import Path

from .config import ConfigError, read_config_file, read_param_file
from .orchestrator import ExecutionError, PipelineRunner
from .output import (
    format_duration,
    print_finish_banner,
    print_pipeline_status,
    print_run_summary,
    print_start_banner,
)

VERSION = "2.0.12"
GOODBYES = [
    "Aavjo",
    "Abar Dekha-Hobe",
    "Adeus",
    "Adios",
    "Aloha",
    "Alvida",
    "Ambera",
    "Annyong hi Kashipshio",
    "Arrivederci",
    "Auf Wiedersehen",
    "Au Revoir",
    "Ba'adan Mibinamet",
    "Dasvidania",
    "Donadagohvi",
    "Do Pobatchenya",
    "Do Widzenia",
    "Eyvallah",
    "Farvel",
    "Ha Det",
    "Hamba Kahle",
    "Hooroo",
    "Hwyl",
    "Kan Ga Waanaa",
    "Khuda Hafiz",
    "Kwa Heri",
    "La Revedere",
    "Le Hitra Ot",
    "Ma'as Salaam",
    "Mikonan",
    "Na-Shledanou",
    "Ni Sa Moce",
    "Paalam",
    "Rhonanai",
    "Sawatdi",
    "Sayonara",
    "Selavu",
    "Shalom",
    "Totsiens",
    "Tot Ziens",
    "Ukudigada",
    "Vale",
    "Zai Geen",
    "Zai Jian",
    "Zay Gesunt",
]
SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    for mode in ("vcf", "tsv", "full"):
        sub = subparsers.add_parser(mode)
        _add_common_options(sub, require_input=True)

    load = subparsers.add_parser("load")
    _add_common_options(load, require_input=False)

    validate = subparsers.add_parser("validate", add_help=False)
    validate.add_argument("validate_args", nargs=argparse.REMAINDER)
    return parser


def _add_common_options(parser: argparse.ArgumentParser, *, require_input: bool) -> None:
    parser.add_argument("-i", "--input", dest="inputfile", required=require_input)
    parser.add_argument("-c", "--config", dest="configfile")
    parser.add_argument("-p", "--param", dest="paramfile")
    parser.add_argument("-t", "--threads", dest="threads", type=int)
    parser.add_argument("--debug", dest="debug", type=int, default=0)
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    parser.add_argument("-nc", "--no-color", dest="nocolor", action="store_true")
    parser.add_argument("-ne", "--no-emoji", dest="noemoji", action="store_true")
    parser.add_argument("-po", "--projectdir-override", dest="projectdir_override")


def _validate_args(arg: dict[str, object]) -> None:
    mode = arg["mode"]
    inputfile = arg.get("inputfile")
    if mode in {"vcf", "tsv", "full"} and not inputfile:
        raise ConfigError("Modes vcf|tsv|full require an input file")
    if mode == "vcf" and not arg.get("paramfile"):
        raise ConfigError("Mode vcf requires a param file")
    if arg.get("configfile") and not Path(str(arg["configfile"])).is_file():
        raise ConfigError("Option --c requires a config file")
    if arg.get("paramfile") and not Path(str(arg["paramfile"])).is_file():
        raise ConfigError("Option --p requires a param file")
    if arg.get("threads") is not None and int(arg["threads"]) <= 0:
        raise ConfigError("Option --t requires a positive integer")

    if inputfile:
        value = str(inputfile).lower()
        allowed = {
            "vcf": (".vcf", ".vcf.gz"),
            "tsv": (".tsv", ".txt", ".tsv.gz", ".txt.gz"),
            "full": (".vcf", ".vcf.gz", ".tsv", ".txt", ".tsv.gz", ".txt.gz"),
        }
        if mode in allowed and not any(value.endswith(suffix) for suffix in allowed[mode]):
            raise ConfigError(f"Mode '{mode}' requires a valid input extension")


def handle_validate(validate_args: list[str]) -> int:
    validator = Path(__file__).resolve().parents[2] / "utils" / "bff_validator" / "bff-validator"
    result = subprocess.run([str(validator), *validate_args])
    return result.returncode


def _spinner_worker(*, stop_event: threading.Event, no_emoji: bool) -> None:
    start = time.time()
    index = 0
    while not stop_event.is_set():
        frame = SPINNER_FRAMES[index % len(SPINNER_FRAMES)]
        elapsed = format_duration(time.time() - start)
        message = f"\r{frame} Working"
        if not no_emoji:
            message += " ⏳"
        message += f"  elapsed: {elapsed}"
        sys.stdout.write(message)
        sys.stdout.flush()
        index += 1
        stop_event.wait(1.0)
    sys.stdout.write("\r\033[2K")
    sys.stdout.flush()


def _run_pipeline(runner: PipelineRunner, pipeline_name: str, *, debug: int, verbose: bool, no_emoji: bool) -> None:
    if debug or verbose or not sys.stdout.isatty():
        runner.run_named(pipeline_name)
        return

    stop_event = threading.Event()
    thread = threading.Thread(
        target=_spinner_worker,
        kwargs={"stop_event": stop_event, "no_emoji": no_emoji},
        daemon=True,
    )
    thread.start()
    try:
        runner.run_named(pipeline_name)
    finally:
        stop_event.set()
        thread.join()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "validate":
        return handle_validate(argv[1:])

    parser = build_parser()
    namespace = parser.parse_args(argv)

    arg = vars(namespace)
    _validate_args(arg)

    start = time.time()
    config = read_config_file(arg.get("configfile"))
    config["version"] = VERSION
    param = read_param_file(arg)

    executable = Path(sys.argv[0]).resolve()
    print_run_summary(
        arg=arg,
        config=config,
        param=param,
        version=VERSION,
        executable=executable,
        no_color=bool(arg.get("nocolor")),
        no_emoji=bool(arg.get("noemoji")),
    )
    print_start_banner(
        no_color=bool(arg.get("nocolor")),
        no_emoji=bool(arg.get("noemoji")),
    )

    runner = PipelineRunner(arg=arg, config=config, param=param)
    try:
        runner.prepare()
        for pipeline_name in ("tsv2vcf", "vcf2bff", "bff2html", "bff2mongodb"):
            if param["pipeline"].get(pipeline_name):
                print_pipeline_status(
                    pipeline_name,
                    no_color=bool(arg.get("nocolor")),
                    no_emoji=bool(arg.get("noemoji")),
                )
                _run_pipeline(
                    runner,
                    pipeline_name,
                    debug=int(arg.get("debug") or 0),
                    verbose=bool(arg.get("verbose")),
                    no_emoji=bool(arg.get("noemoji")),
                )
    except (ConfigError, ExecutionError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print_finish_banner(
        runtime=time.time() - start,
        goodbye=random.choice(GOODBYES),
        no_color=bool(arg.get("nocolor")),
        no_emoji=bool(arg.get("noemoji")),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
