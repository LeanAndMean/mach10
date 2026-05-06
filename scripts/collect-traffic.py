#!/usr/bin/env python3
"""Collect GitHub traffic data for long-term retention.

GitHub retains only 14 days of traffic data. This script fetches views,
clones, referrers, and paths. Views and clones are merged into JSON files
keyed by date (upsert semantics). Referrers and paths are appended as
timestamped snapshots to JSONL files. Designed to run daily via cron.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAFFIC_DIR = REPO_ROOT / "traffic"
GH = shutil.which("gh")
if GH is None:
    print("ERROR: 'gh' CLI not found on PATH", file=sys.stderr)
    sys.exit(1)
REPO = "LeanAndMean/mach10"


def gh_api(endpoint):
    """Fetch a GitHub API endpoint. Returns (data, None) or (None, error_msg)."""
    try:
        result = subprocess.run(
            [GH, "api", f"repos/{REPO}/{endpoint}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None, f"gh api {endpoint}: timed out after 60s"
    if result.returncode != 0:
        return None, f"gh api {endpoint}: {result.stderr.strip()}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"gh api {endpoint}: invalid JSON response: {exc}"


def atomic_write_json(filepath, data):
    """Write JSON atomically via temp file + rename."""
    content = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=filepath.parent, suffix=".tmp")
    closed = False
    try:
        os.write(fd, content.encode())
        os.close(fd)
        closed = True
        os.replace(tmp_path, filepath)
    except BaseException:
        try:
            if not closed:
                os.close(fd)
        except OSError:
            pass
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _backup_corrupt(filepath, reason):
    """Back up a corrupt file and return an error message describing the outcome."""
    try:
        filepath.rename(filepath.with_suffix(".corrupt"))
        return f"{filepath.name}: {reason}; backed up, starting fresh"
    except OSError as exc:
        return f"{filepath.name}: {reason}; backup failed ({exc}), starting fresh"


def merge_timeseries(filepath, new_entries):
    """Upsert daily entries by date key. Returns (new_count, error_msg_or_none)."""
    existing = {}
    error_msg = None
    if filepath.exists():
        try:
            existing = json.loads(filepath.read_text())
        except json.JSONDecodeError as exc:
            error_msg = _backup_corrupt(filepath, f"corrupt JSON: {exc}")
            existing = {}
        if not isinstance(existing, dict):
            error_msg = _backup_corrupt(
                filepath, f"expected dict, got {type(existing).__name__}"
            )
            existing = {}

    new_count = 0
    skipped = 0
    first_bad = None
    for entry in new_entries:
        try:
            date_key = entry["timestamp"][:10]
            record = {"count": entry["count"], "uniques": entry["uniques"]}
        except (KeyError, TypeError):
            skipped += 1
            if first_bad is None:
                first_bad = repr(entry)[:200]
            continue
        if date_key not in existing:
            new_count += 1
        existing[date_key] = record

    if skipped:
        if skipped == len(new_entries) and len(new_entries) > 0:
            skip_msg = (
                f"{filepath.name}: ALL {skipped} entries malformed"
                f" -- possible API format change (sample: {first_bad})"
            )
        else:
            skip_msg = (
                f"{filepath.name}: skipped {skipped} malformed entries"
                f" (sample: {first_bad})"
            )
        error_msg = f"{error_msg}; {skip_msg}" if error_msg else skip_msg

    atomic_write_json(filepath, existing)
    return new_count, error_msg


def append_snapshot(filepath, data):
    """Append a timestamped snapshot to a JSONL file."""
    snapshot = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    line = json.dumps(snapshot) + "\n"
    with open(filepath, "a") as f:
        f.write(line)


def rotate_log():
    """Rotate cron.log if it exceeds 1MB."""
    log_path = TRAFFIC_DIR / "cron.log"
    if log_path.exists() and log_path.stat().st_size > 1_000_000:
        log_path.replace(TRAFFIC_DIR / "cron.log.1")


def collect_timeseries(endpoint, list_key, filename, errors):
    """Fetch a timeseries endpoint and merge into a JSON file.

    Returns the number of new date entries added (0 on any failure).
    Appends error descriptions to the errors list.
    """
    data, err = gh_api(endpoint)
    if err:
        errors.append(err)
        return 0

    entries = data.get(list_key) if isinstance(data, dict) else None
    if not isinstance(entries, list):
        errors.append(f"{endpoint}: response missing '{list_key}' list")
        return 0

    try:
        new_count, err = merge_timeseries(TRAFFIC_DIR / filename, entries)
    except OSError as exc:
        errors.append(f"{filename}: {exc}")
        return 0
    if err:
        errors.append(err)
    return new_count


def collect_snapshot(endpoint, filename, errors):
    """Fetch a snapshot endpoint and append to a JSONL file.

    Appends error descriptions to the errors list.
    """
    data, err = gh_api(endpoint)
    if err:
        errors.append(err)
        return
    try:
        append_snapshot(TRAFFIC_DIR / filename, data)
    except (OSError, TypeError) as exc:
        errors.append(f"{filename}: {exc}")


def main():
    TRAFFIC_DIR.mkdir(exist_ok=True)
    errors = []

    try:
        rotate_log()
    except OSError as exc:
        print(f"  WARNING: rotate_log: {exc}", file=sys.stderr)

    new_views = collect_timeseries("traffic/views", "views", "views.json", errors)
    new_clones = collect_timeseries("traffic/clones", "clones", "clones.json", errors)
    collect_snapshot("traffic/popular/referrers", "referrers.jsonl", errors)
    collect_snapshot("traffic/popular/paths", "paths.jsonl", errors)

    # Report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{now}] Traffic collected: {new_views} new view days, {new_clones} new clone days")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
