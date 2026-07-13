from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, BinaryIO, Iterator

try:
    import orjson as _orjson
except ImportError:  # pragma: no cover - exercised through the explicit fallback test
    _orjson = None

try:
    from isal import igzip as _igzip
except ImportError:  # pragma: no cover - exercised through the explicit fallback test
    _igzip = None


class ParityError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParityResult:
    records: int
    first_difference: int | None = None
    path: str | None = None
    expected: Any = None
    actual: Any = None

    @property
    def equal(self) -> bool:
        return self.first_difference is None


def _open_binary(path: Path) -> BinaryIO:
    if path.suffix == ".gz":
        if _igzip is not None:
            return _igzip.open(path, "rb")
        return gzip.open(path, "rb")
    return path.open("rb")


def _loads(value: bytes) -> Any:
    if _orjson is not None:
        return _orjson.loads(value)
    return json.loads(value)


def _canonical_json(value: Any) -> bytes | None:
    if _orjson is None:
        return None
    return _orjson.dumps(value, option=_orjson.OPT_SORT_KEYS)


def _sort_key(value: Any) -> bytes | str:
    canonical = _canonical_json(value)
    if canonical is not None:
        return canonical
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def iter_streamed_bff(path: Path) -> Iterator[Any]:
    try:
        with _open_binary(path) as handle:
            if path.name.endswith((".jsonl", ".jsonl.gz")):
                for line_number, raw_line in enumerate(handle, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        yield _loads(line)
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        raise ParityError(
                            f"Invalid JSON Lines record on line {line_number} of {path}: {exc}"
                        ) from exc
                return

            started = False
            closed = False
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                if not started:
                    if line.startswith(b"[") and line.endswith(b"]") and line != b"[":
                        try:
                            records = _loads(line)
                        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                            raise ParityError(
                                f"Invalid JSON on line {line_number} of {path}: {exc}"
                            ) from exc
                        if not isinstance(records, list):
                            raise ParityError(f"Expected a JSON array in {path}")
                        yield from records
                        started = True
                        closed = True
                        break
                    if line != b"[":
                        raise ParityError(f"Expected '[' on line {line_number} of {path}")
                    started = True
                    continue
                if line == b"]":
                    closed = True
                    break
                if line.endswith(b","):
                    line = line[:-1]
                try:
                    yield _loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise ParityError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
            if not started or not closed:
                raise ParityError(f"Incomplete streamed BFF array: {path}")
    except OSError as exc:
        raise ParityError(f"Cannot read BFF file {path}: {exc}") from exc


def normalise_bff_record(record: Any) -> Any:
    if not isinstance(record, dict):
        return record
    # Streamed records are disposable, so normalize in place to keep memory
    # bounded to one record from each converter.
    info = record.get("_info")
    if isinstance(info, dict):
        info.pop("vcf2bff", None)
    identifiers = record.get("identifiers")
    if isinstance(identifiers, dict):
        alternatives = identifiers.get("variantAlternativeIds")
        if isinstance(alternatives, list):
            alternatives.sort(key=_sort_key)
    variant_level = record.get("variantLevelData")
    if isinstance(variant_level, dict):
        interpretations = variant_level.get("clinicalInterpretations")
        if isinstance(interpretations, list):
            interpretations.sort(key=_sort_key)
    return record


def _pointer(path: str, value: Any) -> str:
    token = str(value).replace("~", "~0").replace("/", "~1")
    return f"{path}/{token}"


def first_value_difference(expected: Any, actual: Any, path: str = "") -> tuple[str, Any, Any] | None:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(expected) is not type(actual) or expected != actual:
            return path or "/", expected, actual
        return None
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return None if expected == actual else (path or "/", expected, actual)
    if type(expected) is not type(actual):
        return path or "/", expected, actual
    if isinstance(expected, dict):
        for key in sorted(expected.keys() - actual.keys()):
            return _pointer(path, key), expected[key], "<missing>"
        for key in sorted(actual.keys() - expected.keys()):
            return _pointer(path, key), "<missing>", actual[key]
        for key in sorted(expected):
            difference = first_value_difference(
                expected[key], actual[key], _pointer(path, key)
            )
            if difference is not None:
                return difference
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return _pointer(path, "length"), len(expected), len(actual)
        for index, (expected_value, actual_value) in enumerate(zip(expected, actual)):
            difference = first_value_difference(
                expected_value, actual_value, _pointer(path, index)
            )
            if difference is not None:
                return difference
        return None
    return None if expected == actual else (path or "/", expected, actual)


def compare_bff_files(expected_path: Path, actual_path: Path) -> ParityResult:
    sentinel = object()
    records = 0
    for records, (expected, actual) in enumerate(
        zip_longest(
            iter_streamed_bff(expected_path),
            iter_streamed_bff(actual_path),
            fillvalue=sentinel,
        ),
        start=1,
    ):
        if expected is sentinel or actual is sentinel:
            return ParityResult(
                records=records - 1,
                first_difference=records,
                path="/records",
                expected=None if expected is sentinel else expected,
                actual=None if actual is sentinel else actual,
            )
        expected_normalised = normalise_bff_record(expected)
        actual_normalised = normalise_bff_record(actual)
        expected_canonical = _canonical_json(expected_normalised)
        if expected_canonical is not None and expected_canonical == _canonical_json(
            actual_normalised
        ):
            continue
        difference = first_value_difference(expected_normalised, actual_normalised)
        if difference is not None:
            path, expected_value, actual_value = difference
            return ParityResult(
                records=records - 1,
                first_difference=records,
                path=path,
                expected=expected_value,
                actual=actual_value,
            )
    return ParityResult(records=records)
