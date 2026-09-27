from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import opendataloader_pdf


class ConversionError(RuntimeError):
    """Raised when the conversion engine cannot complete a batch."""


@dataclass(frozen=True)
class ConversionResult:
    input_paths: List[Path]
    output_dir: Path
    image_output: str


def normalize_input_paths(input_paths: Iterable[Path | str]) -> List[Path]:
    paths = [Path(path).expanduser() for path in input_paths]
    if not paths:
        raise ConversionError("Add at least one PDF before converting.")
    return paths


def convert_pdfs(
    input_paths: Iterable[Path | str],
    output_dir: Path | str,
    *,
    extract_images: bool = True,
) -> ConversionResult:
    paths = normalize_input_paths(input_paths)
    target_dir = Path(output_dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    image_output = "external" if extract_images else "off"

    try:
        opendataloader_pdf.convert(
            input_path=[str(path) for path in paths],
            output_dir=str(target_dir),
            format=["markdown"],
            quiet=True,
            image_output=image_output,
        )
    except FileNotFoundError as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if isinstance(exc.stderr, str) else ""
        stdout = exc.stdout.strip() if isinstance(exc.stdout, str) else ""
        detail = stderr or stdout or str(exc)
        raise ConversionError(f"Conversion failed: {detail}") from exc
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc

    return ConversionResult(input_paths=paths, output_dir=target_dir, image_output=image_output)
