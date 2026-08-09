#!/usr/bin/env python3
"""
Combine PRISM results_{index}.csv files and prism_log_{row} files into a
single combined CSV.

For each results_{index}.csv:
    - same columns, same number of rows, same row order across all files
    - 1st column (index 0): id
    - 2nd column (index 1): configuration  <- this is the real per-row key
      (ids can repeat across rows, but configuration does not)
    - 3rd column (index 2): a property's values; the header of this column
      is itself the property name
    - row N (0-indexed, excluding header) in every results_{index}.csv
      refers to the same configuration

For each prism_log_{row} (row = 0 .. N-1, N = number of data rows in a
results file):
    - extract States and Transitions (from the "States:" / "Transitions:" lines)
    - the FILENAME's row index corresponds directly to the row position
      (0-indexed) in the results_{index}.csv files - i.e. prism_log_0 goes
      with row 0 (the first data row), prism_log_1 with row 1, etc.
    - the id found inside the log file (from the "Results (including zeros)"
      block) is kept only as an informational column, not used for matching

Output CSV columns:
    id, configuration, States, Transitions, <property_1>, <property_2>, ...
one row per row-position (i.e. per prism_log_{row} file / per results-file
row), in row-position order.

Usage:
    python combine_results.py [directory] [--out combined.csv]

If no directory is given, the current directory is used.
"""

import argparse
import csv
import glob
import os
import re
import sys


RESULTS_PATTERN = re.compile(r"^results_(\d+)\.csv$")
LOG_PATTERN = re.compile(r"^prism_log_(\d+)$")

STATES_RE = re.compile(r"^States:\s*(\d+)")
TRANSITIONS_RE = re.compile(r"^Transitions:\s*(\d+)")
RESULTS_HEADER_RE = re.compile(r'^Results \(including zeros\) for filter')
ID_LINE_RE = re.compile(r"^(\d+):")


def find_results_files(directory):
    """Return list of (index, filepath) for results_{index}.csv files, sorted by index."""
    files = []
    for path in glob.glob(os.path.join(directory, "results_*.csv")):
        fname = os.path.basename(path)
        m = RESULTS_PATTERN.match(fname)
        if m:
            files.append((int(m.group(1)), path))
    files.sort(key=lambda x: x[0])
    return files


def find_log_files(directory):
    """Return dict {row_index: filepath} for prism_log_{row} files."""
    logs = {}
    for path in glob.glob(os.path.join(directory, "prism_log_*")):
        fname = os.path.basename(path)
        m = LOG_PATTERN.match(fname)
        if m:
            logs[int(m.group(1))] = path
    return logs


def parse_log_file(path):
    """
    Parse a prism_log_{row} file.
    Returns (id_str, states, transitions).
    The id is kept only as an informational column (not used for matching).
    """
    states = None
    transitions = None
    log_id = None

    with open(path, "r", errors="replace") as f:
        in_results_block = False
        for line in f:
            stripped = line.strip()

            if states is None:
                m = STATES_RE.match(stripped)
                if m:
                    states = m.group(1)
                    continue

            if transitions is None:
                m = TRANSITIONS_RE.match(stripped)
                if m:
                    transitions = m.group(1)
                    continue

            if log_id is None:
                if RESULTS_HEADER_RE.match(stripped):
                    in_results_block = True
                    continue
                if in_results_block:
                    m = ID_LINE_RE.match(stripped)
                    if m:
                        log_id = m.group(1)
                        in_results_block = False
                        continue
                    if stripped:
                        # blank lines are fine, but a non-matching non-empty
                        # line means the block ended without an id line
                        in_results_block = False

            if states is not None and transitions is not None and log_id is not None:
                break

    missing = []
    if states is None:
        missing.append("States")
    if transitions is None:
        missing.append("Transitions")
    if log_id is None:
        missing.append("id")
    if missing:
        raise ValueError(
            f"Could not find {', '.join(missing)} in log file: {path}"
        )

    return log_id, states, transitions


def read_results_csv(path):
    """
    Read a results_{index}.csv file.
    Returns (property_name, rows) where rows is an ordered list of
    (id, configuration, value) tuples - one per data row, in file order.
    property_name is taken from the header of the 3rd column (index 2).
    """
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if len(header) < 3:
            raise ValueError(f"Expected at least 3 columns in {path}, got {len(header)}")
        property_name = header[2]

        rows = []
        for row in reader:
            if not row:
                continue
            row_id = row[0]
            configuration = row[1]
            value = row[2]
            rows.append((row_id, configuration, value))

    return property_name, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="Directory containing results_{index}.csv and prism_log_{row} files (default: current directory)"
    )
    parser.add_argument(
        "--out", default="combined.csv",
        help="Output CSV file path (default: combined.csv)"
    )
    args = parser.parse_args()

    directory = args.directory

    # --- Locate input files ---
    results_files = find_results_files(directory)
    if not results_files:
        sys.exit(f"No results_{{index}}.csv files found in: {directory}")

    log_files = find_log_files(directory)
    if not log_files:
        sys.exit(f"No prism_log_{{row}} files found in: {directory}")

    print(f"Found {len(results_files)} results file(s): "
          f"{[os.path.basename(p) for _, p in results_files]}")
    print(f"Found {len(log_files)} log file(s) (rows 0..{max(log_files)})")

    # --- Parse all results_{index}.csv files ---
    properties = []        # ordered list of property names
    property_rows = []     # parallel list: rows (id, configuration, value) per property
    row_count = None

    for idx, path in results_files:
        prop_name, rows = read_results_csv(path)

        if row_count is None:
            row_count = len(rows)
        elif len(rows) != row_count:
            print(f"Warning: {os.path.basename(path)} has {len(rows)} rows, "
                  f"expected {row_count} (based on first results file)", file=sys.stderr)

        properties.append(prop_name)
        property_rows.append(rows)
        print(f"  {os.path.basename(path)} -> property: {prop_name!r} "
              f"({len(rows)} rows)")

    # sanity check: configuration (and id) at each row position should match
    # across all results files, since row position is now the join key
    base_rows = property_rows[0]
    for prop_name, rows in zip(properties[1:], property_rows[1:]):
        min_len = min(len(base_rows), len(rows))
        for i in range(min_len):
            base_id, base_config, _ = base_rows[i]
            this_id, this_config, _ = rows[i]
            if this_config != base_config:
                print(f"Warning: row {i} configuration mismatch between "
                      f"'{properties[0]}' ('{base_config}') and "
                      f"'{prop_name}' ('{this_config}')", file=sys.stderr)
            elif this_id != base_id:
                print(f"Warning: row {i} id mismatch between "
                      f"'{properties[0]}' ('{base_id}') and "
                      f"'{prop_name}' ('{this_id}') despite matching configuration",
                      file=sys.stderr)

    # --- Parse all prism_log_{row} files ---
    # row_index -> (id, states, transitions)
    log_data = {}
    for row_idx, path in sorted(log_files.items()):
        log_id, states, transitions = parse_log_file(path)
        log_data[row_idx] = (log_id, states, transitions)

    if row_count is not None and len(log_data) != row_count:
        print(f"Warning: found {len(log_data)} log file(s) but results files "
              f"have {row_count} row(s)", file=sys.stderr)

    # --- Build combined rows, ordered strictly by row position ---
    output_rows = []
    for row_idx in sorted(log_data.keys()):
        log_id, states, transitions = log_data[row_idx]

        if row_idx >= len(base_rows):
            print(f"Warning: prism_log_{row_idx} has no corresponding row "
                  f"in results files (only {len(base_rows)} row(s) present) - skipping",
                  file=sys.stderr)
            continue

        results_id, configuration, _ = base_rows[row_idx]
        if results_id != log_id:
            print(f"Warning: row {row_idx} - id from log file ('{log_id}') "
                  f"differs from id in results file ('{results_id}')", file=sys.stderr)

        row = {
            "id": results_id,
            "configuration": configuration,
            "States": states,
            "Transitions": transitions,
        }
        for prop_name, rows in zip(properties, property_rows):
            _, _, value = rows[row_idx]
            row[prop_name] = value
        output_rows.append(row)

    # --- Write output CSV ---
    fieldnames = ["id", "configuration", "States", "Transitions"] + properties
    out_path = args.out
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\nWrote {len(output_rows)} rows to {out_path}")


if __name__ == "__main__":
    main()