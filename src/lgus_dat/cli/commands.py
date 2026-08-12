"""Command-line entry point for the .DAT processor."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from lgus_dat.output.csv_writer import write_csv
from lgus_dat.parser.dat_parser import parse_dat_file
from lgus_dat.processing.sequence_processor import process_records


def _archive_source(input_path: Path, archive_dir: Path) -> Path:
    """Copy the original .DAT file to an archive directory before processing."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archive_name = f"{input_path.stem}_{timestamp}{input_path.suffix}"
    archive_path = archive_dir / archive_name
    shutil.copy2(input_path, archive_path)
    return archive_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Process MB10-VL .DAT attendance exports into IN/OUT records."
    )
    parser.add_argument("input", type=Path, help="Path to the .DAT attendance export.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for processed output (default: ./output).",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=Path("archive"),
        help="Directory to archive original .DAT files (default: ./archive).",
    )
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: input file not found: {args.input}")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _archive_source(args.input, args.archive_dir)

    parsed, errors = parse_dat_file(args.input)
    if errors:
        print("Parse errors:")
        for error in errors:
            print(error)

    processed = process_records(parsed)
    output_path = args.output_dir / f"{args.input.stem}_processed.csv"
    write_csv(processed, output_path)
    print(f"Wrote {len(processed)} processed records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
