from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from .config import DATA_ROOT_ENV


BUNDLE_REVISION = "r3"
BUNDLE_NAME = "beacon2-cbi-tools-data-r3.tar.gz"
CHECKSUM_NAME = f"{BUNDLE_NAME}.md5"
PART_NAMES = tuple(f"{BUNDLE_NAME}.part-{index:02d}" for index in range(7))
FOLDER_URL = "https://drive.google.com/drive/folders/1dGSM-0F-855NjkDCkyIPCYItCF9hragT"
BUNDLE_FILES = {
    CHECKSUM_NAME: "178LHkzI8dZ5VB7_IhLmALtfcsbeOrqu3",
    PART_NAMES[0]: "11PjCf4gGhaM9qAdRDW-mE_or1kj_l9wU",
    PART_NAMES[1]: "1ttIn_xMBOCcxGKufQ5TwaqWoDAkct2ic",
    PART_NAMES[2]: "17r3Yr6kIqNpdX_xYw5zfPl4Jn6gQoIiB",
    PART_NAMES[3]: "1Fagi3Yb0jaD9LKkOVqlVdNss1LjX9OVd",
    PART_NAMES[4]: "1xwBVR2D9SlaasBVkSkIyyhFdmiytzxn5",
    PART_NAMES[5]: "1wMhCtTA2EeV-dzE_dsl82lZQJISCWSP2",
    PART_NAMES[6]: "1qqmz7sK5B_CP8IyBvVhQqyAnaPTpmk1J",
}
EXPECTED_DIRECTORIES = ("databases", "soft")
INSTALL_MARKER = ".beacon2-cbi-tools-data-r3.installed"


class ResourceInstallError(RuntimeError):
    pass


def google_drive_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def resolve_data_directory(value: str | None = None) -> Path:
    configured = value or os.environ.get(DATA_ROOT_ENV)
    if not configured:
        raise ResourceInstallError(
            f"Set {DATA_ROOT_ENV} or pass --data-dir to select the installation directory"
        )
    return Path(configured).expanduser().resolve()


def print_download_links() -> None:
    print(f"Beacon v2 CBI Tools annotation bundle {BUNDLE_REVISION}")
    print(f"Folder: {FOLDER_URL}")
    for filename, file_id in BUNDLE_FILES.items():
        print(f"{filename}\n  {google_drive_url(file_id)}")


def _gdown_download(url: str, destination: Path) -> object:
    try:
        import gdown
    except ImportError as exc:  # pragma: no cover - declared package dependency
        raise ResourceInstallError(
            "Automatic download requires gdown; reinstall beacon2-cbi-tools"
        ) from exc
    try:
        return gdown.download(url, str(destination), quiet=False, fuzzy=True)
    except Exception as exc:
        raise ResourceInstallError(
            f"Google Drive download failed for {destination.name}: {exc}"
        ) from exc


def download_missing_files(
    data_dir: Path,
    *,
    downloader: Callable[[str, Path], object] = _gdown_download,
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, file_id in BUNDLE_FILES.items():
        destination = data_dir / filename
        if destination.is_file() and destination.stat().st_size > 0:
            print(f"Found {filename}; skipping download")
            continue
        if destination.exists():
            destination.unlink()
        print(f"Downloading {filename}")
        result = downloader(google_drive_url(file_id), destination)
        if result is None or not destination.is_file() or destination.stat().st_size == 0:
            raise ResourceInstallError(
                f"Download failed for {filename}. Use --print-links for manual download."
            )


def read_part_checksums(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ResourceInstallError(f"Cannot read checksum manifest {path}: {exc}") from exc

    checksums: dict[str, str] = {}
    for line in lines:
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2 or len(fields[0]) != 32:
            continue
        filename = Path(fields[1].lstrip("*").strip()).name
        checksums[filename] = fields[0].lower()

    missing = [name for name in PART_NAMES if name not in checksums]
    if missing:
        raise ResourceInstallError(
            "Checksum manifest does not cover all archive parts: " + ", ".join(missing)
        )
    return checksums


def file_md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(8 * 1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise ResourceInstallError(f"Cannot read bundle part {path}: {exc}") from exc
    return digest.hexdigest()


def verify_parts(data_dir: Path) -> None:
    checksums = read_part_checksums(data_dir / CHECKSUM_NAME)
    for part_name in PART_NAMES:
        part = data_dir / part_name
        if not part.is_file():
            raise ResourceInstallError(f"Missing bundle part: {part}")
        print(f"Verifying {part_name}", flush=True)
        observed = file_md5(part)
        if observed != checksums[part_name]:
            raise ResourceInstallError(
                f"Checksum failed for {part_name}: expected {checksums[part_name]}, "
                f"observed {observed}"
            )
    print("All bundle-part checksums passed")


def assemble_archive(data_dir: Path) -> Path:
    archive = data_dir / BUNDLE_NAME
    expected_size = sum((data_dir / name).stat().st_size for name in PART_NAMES)
    if archive.is_file() and archive.stat().st_size == expected_size:
        print(f"Found assembled {BUNDLE_NAME}; skipping assembly")
        return archive

    temporary = data_dir / f".{BUNDLE_NAME}.tmp"
    if temporary.exists():
        temporary.unlink()
    print(f"Assembling {BUNDLE_NAME}")
    try:
        with temporary.open("wb") as output:
            for part_name in PART_NAMES:
                print(f"  adding {part_name}", flush=True)
                with (data_dir / part_name).open("rb") as source:
                    shutil.copyfileobj(source, output, length=8 * 1024 * 1024)
        temporary.replace(archive)
    except OSError as exc:
        if temporary.exists():
            temporary.unlink()
        raise ResourceInstallError(f"Cannot assemble {archive}: {exc}") from exc
    return archive


def layout_is_ready(data_dir: Path) -> bool:
    return all((data_dir / name).is_dir() for name in EXPECTED_DIRECTORIES)


def extract_archive(
    archive: Path,
    data_dir: Path,
    *,
    run: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
) -> None:
    tar = shutil.which("tar")
    if tar is None:
        raise ResourceInstallError("The 'tar' command is required to extract the bundle")
    print(f"Extracting {archive.name} into {data_dir}")
    try:
        run([tar, "-xzf", str(archive), "-C", str(data_dir)], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ResourceInstallError(f"Cannot extract {archive}: {exc}") from exc
    if not layout_is_ready(data_dir):
        expected = ", ".join(EXPECTED_DIRECTORIES)
        raise ResourceInstallError(
            f"Extraction finished without the expected directories: {expected}"
        )


def install_resources(data_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    marker = data_dir / INSTALL_MARKER
    if marker.is_file() and layout_is_ready(data_dir):
        (data_dir / "tmp").mkdir(exist_ok=True)
        print(f"Annotation resources already installed in {data_dir}")
        return data_dir
    if any((data_dir / name).exists() for name in EXPECTED_DIRECTORIES):
        raise ResourceInstallError(
            f"{data_dir} contains an unversioned or incomplete annotation layout. "
            "Install r3 into a clean directory to avoid retaining files from an older bundle."
        )

    download_missing_files(data_dir)
    verify_parts(data_dir)
    archive = assemble_archive(data_dir)
    extract_archive(archive, data_dir)
    (data_dir / "tmp").mkdir(exist_ok=True)
    marker.write_text(f"{BUNDLE_REVISION}\n", encoding="utf-8")
    print(f"Annotation resources installed in {data_dir}")
    print(f"Set {DATA_ROOT_ENV}={data_dir}")
    return data_dir
