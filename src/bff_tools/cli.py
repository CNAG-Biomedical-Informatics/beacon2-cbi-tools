from __future__ import annotations

import argparse
import random
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
from .validator import ValidatorError, export_template, print_report, validate_inputs
from .version import VERSION

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

    for mode in ("vcf", "tsv"):
        sub = subparsers.add_parser(mode)
        _add_common_options(sub, require_input=True)

    validate = subparsers.add_parser(
        "validate",
        help="validate Beacon metadata and write BFF JSON collections",
    )
    input_group = validate.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-i",
        "--input",
        dest="input_files",
        nargs="+",
        metavar="FILE",
        help="XLSX workbook or BFF JSON collection file(s)",
    )
    input_group.add_argument(
        "--template-out",
        metavar="PATH",
        help="write a fresh Beacon metadata workbook template",
    )
    validate.add_argument("-s", "--schema-dir")
    validate.add_argument("-o", "--out-dir", default=".")
    validate.add_argument("-gv", "--gv", action="store_true")
    validate.add_argument("-gv-vcf", "--gv-vcf", action="store_true")
    validate.add_argument("--ignore-validation", action="store_true")
    validate.add_argument("--debug", type=int, default=0)
    validate.add_argument("--verbose", action="store_true")
    validate.add_argument("-nc", "--no-color", action="store_true")
    validate.add_argument("-ne", "--no-emoji", action="store_true")
    return parser


def _add_common_options(parser: argparse.ArgumentParser, *, require_input: bool) -> None:
    parser.add_argument("-i", "--input", dest="inputfile", required=require_input)
    parser.add_argument("-c", "--config", dest="configfile")
    parser.add_argument("-p", "--param", dest="paramfile")
    parser.add_argument("-t", "--threads", dest="threads", type=int)
    parser.add_argument("--genome", choices=("b37", "hs37", "hg19", "hg38"))
    parser.add_argument("--dataset-id", dest="datasetid")
    parser.add_argument("--sample-id", dest="sampleid")
    parser.add_argument(
        "--annotate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="annotate raw input with SnpEff/SnpSift (default: enabled)",
    )
    parser.add_argument(
        "--browser",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="generate a standalone HTML variant report",
    )
    parser.add_argument(
        "--jsonl",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="write JSON Lines genomic variations instead of a JSON array",
    )
    parser.add_argument("--debug", dest="debug", type=int, default=0)
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    parser.add_argument(
        "--progress-every",
        dest="progress_every",
        type=int,
        metavar="N",
        help="report VCF progress every N records (default: 10000)",
    )
    parser.add_argument("-nc", "--no-color", dest="nocolor", action="store_true")
    parser.add_argument("-ne", "--no-emoji", dest="noemoji", action="store_true")
    parser.add_argument(
        "-o",
        "-po",
        "--project-dir",
        "--projectdir-override",
        dest="projectdir_override",
    )


def _validate_args(arg: dict[str, object]) -> None:
    mode = arg["mode"]
    inputfile = arg.get("inputfile")
    if mode in {"vcf", "tsv"} and not inputfile:
        raise ConfigError("Modes vcf|tsv require an input file")
    if arg.get("configfile") and not Path(str(arg["configfile"])).is_file():
        raise ConfigError("Option --c requires a config file")
    if arg.get("paramfile") and not Path(str(arg["paramfile"])).is_file():
        raise ConfigError("Option --p requires a param file")
    if arg.get("threads") is not None and int(arg["threads"]) <= 0:
        raise ConfigError("Option --t requires a positive integer")
    if arg.get("progress_every") is not None and int(arg["progress_every"]) <= 0:
        raise ConfigError("Option --progress-every requires a positive integer")

    if inputfile:
        value = str(inputfile).lower()
        allowed = {
            "vcf": (".vcf", ".vcf.gz"),
            "tsv": (".tsv", ".txt", ".tsv.gz", ".txt.gz"),
        }
        if mode in allowed and not any(value.endswith(suffix) for suffix in allowed[mode]):
            raise ConfigError(f"Mode '{mode}' requires a valid input extension")


def handle_validate(arg: dict[str, object]) -> int:
    template_out = arg.get("template_out")
    if template_out:
        destination = export_template(Path(str(template_out)).resolve())
        print(f"Wrote {destination}")
        return 0

    report = validate_inputs(
        [Path(str(path)) for path in arg.get("input_files") or []],
        schema_dir=Path(str(arg["schema_dir"])) if arg.get("schema_dir") else None,
        output_dir=Path(str(arg.get("out_dir") or ".")),
        include_genomic=bool(arg.get("gv")),
        streamed_genomic=bool(arg.get("gv_vcf")),
        ignore_validation=bool(arg.get("ignore_validation")),
        verbose=bool(arg.get("verbose")) or bool(arg.get("debug")),
    )
    print_report(
        report,
        ignore_validation=bool(arg.get("ignore_validation")),
        no_color=bool(arg.get("no_color")),
        no_emoji=bool(arg.get("no_emoji")),
    )
    return 0 if report.ok or bool(arg.get("ignore_validation")) else 1


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
    parser = build_parser()
    namespace = parser.parse_args(argv)
    arg = vars(namespace)
    if arg["mode"] == "validate":
        try:
            return handle_validate(arg)
        except ValidatorError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    start = time.time()
    try:
        _validate_args(arg)
        param = read_param_file(arg)
        config = read_config_file(
            arg.get("configfile"),
            mode=str(arg["mode"]),
            annotate=bool(param.get("annotate")),
            genome=str(param["genome"]),
            browser=bool(param.get("bff2html")),
        )
        config["version"] = VERSION

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
        runner.prepare()
        for pipeline_name in ("tsv2vcf", "vcf2bff", "bff2html"):
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
                for notice in runner.notices:
                    print(f"Warning: {notice}", file=sys.stderr)
                runner.notices.clear()
    except (ConfigError, ExecutionError, FileExistsError, OSError) as exc:
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
