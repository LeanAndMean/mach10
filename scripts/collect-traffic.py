#!/usr/bin/env python3
"""Collect GitHub traffic data and merge into local JSON store.

GitHub retains only 14 days of traffic data. This script fetches views,
clones, referrers, and paths, then merges them into local files for
long-term retention. Designed to run daily via cron.
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAFFIC_DIR = REPO_ROOT / "traffic"
GH = "/usr/bin/gh"
REPO = "LeanAndMean/mach10"


def gh_api(endpoint):
    """Fetch a GitHub API endpoint. Returns (data, None) or (None, error_msg)."""
    result = subprocess.run(
        [GH, "api", f"repos/{REPO}/{endpoint}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None, f"gh api {endpoint}: {result.stderr.strip()}"
    return json.loads(result.stdout), None


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
        if not closed:
            os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def merge_timeseries(filepath, new_entries):
    """Upsert daily entries by date key. Returns count of new dates added."""
    existing = {}
    if filepath.exists():
        existing = json.loads(filepath.read_text())

    new_count = 0
    for entry in new_entries:
        date_key = entry["timestamp"][:10]
        if date_key not in existing:
            new_count += 1
        existing[date_key] = {"count": entry["count"], "uniques": entry["uniques"]}

    atomic_write_json(filepath, existing)
    return new_count


def append_snapshot(filepath, data):
    """Append a timestamped snapshot to a JSONL file."""
    snapshot = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    with open(filepath, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


def rotate_log():
    """Rotate cron.log if it exceeds 1MB."""
    log_path = TRAFFIC_DIR / "cron.log"
    if log_path.exists() and log_path.stat().st_size > 1_000_000:
        log_path.replace(TRAFFIC_DIR / "cron.log.1")


def main():
    TRAFFIC_DIR.mkdir(exist_ok=True)
    rotate_log()
    errors = []

    # Views
    views_data, err = gh_api("traffic/views")
    if err:
        errors.append(err)
        new_views = 0
    else:
        new_views = merge_timeseries(TRAFFIC_DIR / "views.json", views_data["views"])

    # Clones
    clones_data, err = gh_api("traffic/clones")
    if err:
        errors.append(err)
        new_clones = 0
    else:
        new_clones = merge_timeseries(
            TRAFFIC_DIR / "clones.json", clones_data["clones"]
        )

    # Referrers
    referrers_data, err = gh_api("traffic/popular/referrers")
    if err:
        errors.append(err)
    else:
        append_snapshot(TRAFFIC_DIR / "referrers.jsonl", referrers_data)

    # Paths
    paths_data, err = gh_api("traffic/popular/paths")
    if err:
        errors.append(err)
    else:
        append_snapshot(TRAFFIC_DIR / "paths.jsonl", paths_data)

    # Report
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{now}] Traffic collected: {new_views} new view days, {new_clones} new clone days")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
