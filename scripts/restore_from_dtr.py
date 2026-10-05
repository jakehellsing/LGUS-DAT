"""One-off recovery tool: repopulate wiped employee fields from generated DTR PDFs.

A generated DTR page carries:
  NAME:     -> employees.full_name (or device name if full_name was never set)
  POSITION: -> employees.position
  signature block verifying officer -> department via head_name/head_position

Only empty (NULL/'') fields are filled; existing values are never overwritten.

Usage:
    python scripts/restore_from_dtr.py <folder-or-pdf> [--db PATH] [--apply]

Runs as a dry run unless --apply is given.
Requires: pip install pypdf
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

_LABELS = {"NAME:", "POSITION:", "For the", "Month of:", "Day"}
_VERIFIED_LINE = "Verified as to the prescribed office hours"
_DEFAULT_OFFICER = "Verifying Officer"


def _norm(text: str) -> str:
    """Uppercase, strip punctuation/dots, collapse whitespace."""
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", text.upper()).split())


def _first_half_lines(text: str) -> list[str]:
    """Return stripped lines for the left copy of the duplicated two-column DTR."""
    lines = [ln.strip() for ln in text.splitlines()]
    title_hits = [i for i, ln in enumerate(lines) if ln == "DAILY TIME RECORD"]
    if len(title_hits) >= 2:
        lines = lines[: title_hits[1]]
    return [ln for ln in lines if ln]


def _value_after(lines: list[str], label: str, stops: set[str]) -> str | None:
    """Collect lines following `label` until a stop label (handles wrapping)."""
    try:
        start = lines.index(label) + 1
    except ValueError:
        return None
    out: list[str] = []
    for ln in lines[start:]:
        if ln in stops:
            break
        out.append(ln)
    return " ".join(out).strip() or None


def parse_dtr_page(text: str) -> dict:
    """Extract name, position, and verifying-officer info from one DTR page."""
    lines = _first_half_lines(text)

    name = _value_after(lines, "NAME:", {"POSITION:", "For the", "Month of:", "Day"})
    position = _value_after(lines, "POSITION:", {"For the", "Month of:", "Day"})

    head_name = None
    head_position = None
    for i, ln in enumerate(lines):
        if _VERIFIED_LINE in ln:
            tail = lines[i + 1 :]
            if len(tail) >= 2:
                head_name, head_position = tail[0], tail[1]
            elif len(tail) == 1:
                head_position = tail[0]
            break

    if head_position == _DEFAULT_OFFICER:
        head_name = None
        head_position = None

    return {
        "name": name,
        "position": position,
        "head_name": head_name,
        "head_position": head_position,
    }


def _id_from_filename(path: Path, known_ids: set[str], page_count: int) -> str | None:
    """Recover the employee ID from a single-employee export filename.

    Single exports are named DTR_<id>_<safe_name>_<YYYY>_<MM>.pdf; bulk exports
    are DTR_<YYYY>_<MM>.pdf. Only trust the token when the file has exactly one
    page, the stem has an extra name segment, and the token is a known ID.
    """
    parts = path.stem.split("_")
    if len(parts) >= 5 and parts[0].upper() == "DTR" and page_count == 1:
        candidate = parts[1]
        if re.fullmatch(r"\d{4}", parts[-2]) and re.fullmatch(r"\d{2}", parts[-1]):
            if candidate in known_ids:
                return candidate
    return None


def _device_parts(device_name: str) -> tuple[list[str], str] | None:
    """Split a device name like 'DELA CRUZ_C' into surname tokens + initial."""
    if "_" not in device_name:
        return None
    surname, _, initial = device_name.partition("_")
    tokens = _norm(surname).split()
    initial = _norm(initial)[:1]
    if not tokens or not initial:
        return None
    return tokens, initial


def _match_employee(
    extracted_name: str | None,
    employees: list[sqlite3.Row],
) -> tuple[sqlite3.Row | None, str | None, list[str]]:
    """Resolve an extracted NAME to an employees row.

    Returns (row, how, candidates). `how` is 'exact', 'heuristic', or None.
    """
    if not extracted_name:
        return None, None, []

    norm_name = _norm(extracted_name)

    # Exact match on device name or full_name.
    exact = [
        e for e in employees
        if _norm(e["name"] or "") == norm_name
        or _norm(e["full_name"] or "") == norm_name
    ]
    if len(exact) == 1:
        return exact[0], "exact", []
    if len(exact) > 1:
        return None, None, [e["device_user_id"] for e in exact]

    # Heuristic: device names are SURNAME_INITIAL (e.g. OMONGIA_J) while DTR
    # full names are "FIRST M. SURNAME". Match trailing surname tokens plus
    # the first initial.
    name_tokens = norm_name.split()
    candidates = []
    for e in employees:
        parts = _device_parts(e["name"] or "")
        if not parts:
            continue
        surname_tokens, initial = parts
        n = len(surname_tokens)
        if len(name_tokens) <= n:
            continue
        if name_tokens[-n:] == surname_tokens and name_tokens[0].startswith(initial):
            candidates.append(e)

    if len(candidates) == 1:
        return candidates[0], "heuristic", []
    return None, None, [e["device_user_id"] for e in candidates]


def _match_department(
    head_name: str | None,
    head_position: str | None,
    departments: list[sqlite3.Row],
) -> int | None:
    """Map the verifying officer back to a department_id."""
    if head_name:
        norm = _norm(head_name)
        for d in departments:
            if _norm(d["head_name"] or "") == norm:
                return d["department_id"]
    if head_position:
        norm = _norm(head_position)
        hits = [d for d in departments if _norm(d["head_position"] or "") == norm]
        if len(hits) == 1:
            return hits[0]["department_id"]
    return None


def scan_pdfs(paths: list[Path]) -> tuple[list[dict], dict[str, int]]:
    """Extract per-page DTR info from all PDFs.

    Returns (pages, page_counts) where page_counts maps filename to page count.
    """
    pages: list[dict] = []
    page_counts: dict[str, int] = {}
    for pdf_path in paths:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"  ! cannot read {pdf_path.name}: {exc}")
            continue
        page_counts[pdf_path.name] = len(reader.pages)
        for i, page in enumerate(reader.pages):
            info = parse_dtr_page(page.extract_text() or "")
            info["file"] = pdf_path.name
            info["file_path"] = pdf_path
            info["page"] = i + 1
            pages.append(info)
    return pages, page_counts


def _interactive_args() -> argparse.Namespace:
    """Prompt-based flow for double-clicking the exe on a client PC."""
    source = Path(input("Folder containing DTR PDFs: ").strip().strip('"'))
    db_default = Path("lgus_registry.db")
    db_in = input(f"Path to lgus_registry.db [{db_default}]: ").strip().strip('"')
    db = Path(db_in) if db_in else db_default
    apply = input("Type APPLY to write recovered data, or press Enter for dry run: ").strip() == "APPLY"
    return argparse.Namespace(source=source, db=db, apply=apply, interactive=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, nargs="?", help="Folder of DTR PDFs or a single PDF file")
    parser.add_argument("--db", type=Path, default=Path("lgus_registry.db"), help="Path to lgus_registry.db")
    parser.add_argument("--apply", action="store_true", help="Write recovered data (default is dry run)")
    args = parser.parse_args()

    interactive = args.source is None
    if interactive:
        args = _interactive_args()

    if args.source.is_dir():
        pdf_paths = sorted(args.source.rglob("*.pdf"))
    elif args.source.is_file():
        pdf_paths = [args.source]
    else:
        print(f"Not found: {args.source}")
        return 1
    if not pdf_paths:
        print("No PDF files found.")
        return 1

    if not args.db.exists():
        print(f"Database not found: {args.db}")
        return 1

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    employees = conn.execute(
        "SELECT device_user_id, name, full_name, position, department_id FROM employees"
    ).fetchall()
    departments = conn.execute(
        "SELECT department_id, name, head_name, head_position FROM departments"
    ).fetchall()
    known_ids = {e["device_user_id"] for e in employees}

    print(f"Scanning {len(pdf_paths)} PDF(s) from {args.source} ...")
    pages, page_counts = scan_pdfs(pdf_paths)
    for page in pages:
        page["_file_id"] = _id_from_filename(
            page["file_path"], known_ids, page_counts[page["file"]]
        )

    # Aggregate candidates per employee (same employee may appear in several months).
    recovered: dict[str, dict[str, Counter]] = {}
    unmatched: list[dict] = []
    ambiguous: list[tuple[dict, list[str]]] = []

    for page in pages:
        emp_row = None
        how = None
        if page["_file_id"]:
            emp_row = next(e for e in employees if e["device_user_id"] == page["_file_id"])
            how = "filename"
        else:
            emp_row, how, cands = _match_employee(page["name"], employees)
            if emp_row is None:
                if cands:
                    ambiguous.append((page, cands))
                else:
                    unmatched.append(page)
                continue

        emp_id = emp_row["device_user_id"]
        entry = recovered.setdefault(emp_id, {"full_name": Counter(), "position": Counter(), "department_id": Counter()})

        # NAME on the DTR is full_name or device name; only keep it as a
        # full_name candidate when it differs from the device name.
        if page["name"] and _norm(page["name"]) != _norm(emp_row["name"] or ""):
            entry["full_name"][page["name"]] += 1
        if page["position"]:
            entry["position"][page["position"]] += 1
        dept_id = _match_department(page["head_name"], page["head_position"], departments)
        if dept_id is not None:
            entry["department_id"][dept_id] += 1

    # Decide final values per employee and report.
    updates: list[tuple[str, dict[str, object]]] = []
    dept_names = {d["department_id"]: d["name"] for d in departments}
    emp_by_id = {e["device_user_id"]: e for e in employees}

    print("\n=== Recovery preview ===")
    for emp_id in sorted(recovered, key=lambda x: (int(x) if x.isdigit() else 10**9, x)):
        emp = emp_by_id[emp_id]
        fields: dict[str, object] = {}
        notes: list[str] = []
        for field in ("full_name", "position", "department_id"):
            counter = recovered[emp_id][field]
            if not counter:
                continue
            value, _ = counter.most_common(1)[0]
            if len(counter) > 1:
                notes.append(f"{field}: conflicting values {list(counter)} (using most common)")
            current = emp[field]
            if current not in (None, ""):
                if _norm(str(current)) != _norm(str(value)):
                    notes.append(f"{field}: keeping existing '{current}' (PDF says '{value}')")
                continue
            fields[field] = value

        if fields or notes:
            label = ", ".join(
                f"{k}={dept_names.get(v, v) if k == 'department_id' else v!r}" for k, v in fields.items()
            ) or "(nothing new)"
            print(f"  {emp_id} {emp['name']}: {label}")
            for n in notes:
                print(f"      note: {n}")
            if fields:
                updates.append((emp_id, fields))

    if unmatched:
        print(f"\n=== Unmatched pages ({len(unmatched)}) ===")
        for page in unmatched:
            print(f"  {page['file']} p{page['page']}: NAME={page['name']!r}")

    if ambiguous:
        print(f"\n=== Ambiguous pages ({len(ambiguous)}) ===")
        for page, cands in ambiguous:
            print(f"  {page['file']} p{page['page']}: NAME={page['name']!r} -> candidates {cands}")

    if not args.apply:
        print(f"\nDry run: {len(updates)} employee(s) would be updated. Re-run with --apply to write.")
        conn.close()
        return 0

    for emp_id, fields in updates:
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE employees SET {sets} WHERE device_user_id = ?",
            (*fields.values(), emp_id),
        )
        if "position" in fields:
            conn.execute("INSERT OR IGNORE INTO positions (name) VALUES (?)", (fields["position"],))
    conn.commit()
    conn.close()
    print(f"\nApplied: updated {len(updates)} employee(s).")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:  # noqa: BLE001 - keep console open on failure
        print(f"\nERROR: {exc}")
        code = 1
    if not sys.argv[1:]:
        input("\nPress Enter to exit...")
    sys.exit(code)
