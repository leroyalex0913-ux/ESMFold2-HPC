#!/usr/bin/env python3
"""
copy_best_cifs_from_summary.py

Reads a summary CSV with columns:
    pair_id, seed, sample, plddt_mean, ptm, iptm, cif_path

Usage:
    python3 copy_best_cifs_ef2.py /path/to/summary.csv /path/to/output_dir
    python3 copy_best_cifs_ef2.py /path/to/summary.csv /path/to/output_dir --dry-run
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Copy the highest-iPTM cif file for each protein pair from a summary CSV.")
    parser.add_argument("summary_csv", help="Path to the summary CSV file")
    parser.add_argument("output_dir", help="Path to the directory where winning .cif files (and the iptm score log) will be written")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually copying/writing")
    args = parser.parse_args()

    summary_path = Path(args.summary_csv)
    if not summary_path.is_file():
        print(f"Error: {summary_path} is not a file", file=sys.stderr)
        sys.exit(1)

    # The actual .cif files live alongside the summary CSV, regardless of
    # what path is recorded in the "cif_path" column.
    cif_source_dir = summary_path.parent

    output_dir = Path(args.output_dir)
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    # best[pair_id] = row dict with the highest iptm seen so far
    best = {}

    with open(summary_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pair_id = row["pair_id"]
            try:
                iptm = float(row["iptm"])
            except (KeyError, ValueError):
                print(f"  [warn] Could not parse iptm for row: {row}")
                continue

            if pair_id not in best or iptm > float(best[pair_id]["iptm"]):
                best[pair_id] = row

    if not best:
        print("No valid rows found in summary CSV.")
        sys.exit(0)

    print(f"Found {len(best)} unique protein pairs in {summary_path}")
    print(f"Cif source directory: {cif_source_dir}")
    print(f"Output directory: {output_dir}\n")

    fieldnames = list(next(iter(best.values())).keys())
    log_lines = [",".join(fieldnames)]

    for pair_id in sorted(best):
        row = best[pair_id]
        iptm = float(row["iptm"])
        cif_filename = Path(row["cif_path"]).name
        src = cif_source_dir / cif_filename
        dest = output_dir / cif_filename

        print(f"{pair_id}: best seed={row['seed']} sample={row['sample']} iptm={iptm}")

        if not src.exists():
            print(f"  [warn] Expected cif file not found: {src}")
            continue

        print(f"  Copying: {src.name} -> {dest}")
        if not args.dry_run:
            shutil.copy2(src, dest)

        log_lines.append(",".join(str(row[field]) for field in fieldnames))

    log_path = output_dir / "summary_scores.csv"
    print(f"\nWriting best-row log: {log_path}")
    if not args.dry_run:
        with open(log_path, "w") as f:
            f.write("\n".join(log_lines) + "\n")


if __name__ == "__main__":
    main()
