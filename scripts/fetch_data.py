#!/usr/bin/env python3
"""Fetch a small daily football snapshot from API-Football.
Uses only Python standard library. API key is read from environment, never written to disk.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://v3.football.api-sports.io"
TZ = ZoneInfo("Asia/Bangkok")
KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
OUT = Path("data/football.json")

if not KEY:
    print("Missing API_FOOTBALL_KEY secret", file=sys.stderr)
    sys.exit(1)

def get(endpoint, params):
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{BASE}/{endpoint}?{query}",
        headers={"x-apisports-key": KEY, "User-Agent": "lite-football-scout/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
        remaining = response.headers.get("x-ratelimit-requests-remaining")
    if payload.get("errors"):
        raise RuntimeError(f"{endpoint}: {payload['errors']}")
    return payload.get("response", []), remaining

now = datetime.now(TZ)
dates = [(now + timedelta(days=i)).date().isoformat() for i in (0, 1)]
snapshot = {
    "app": "LITE FOOTBALL SCOUT",
    "schema_version": 1,
    "timezone": "Asia/Bangkok",
    "fetched_at": now.isoformat(),
    "dates": dates,
    "fixtures": [],
    "odds": [],
    "errors": [],
    "quota_remaining": None,
    "sources": ["API-Football v3"],
}

remaining_values = []
for day in dates:
    try:
        rows, remaining = get("fixtures", {"date": day, "timezone": "Asia/Bangkok"})
        snapshot["fixtures"].extend(rows)
        if remaining is not None:
            remaining_values.append(int(remaining))
    except Exception as exc:
        snapshot["errors"].append(f"fixtures {day}: {exc}")
    try:
        rows, remaining = get("odds", {"date": day, "timezone": "Asia/Bangkok", "page": 1})
        snapshot["odds"].extend(rows)
        if remaining is not None:
            remaining_values.append(int(remaining))
    except Exception as exc:
        snapshot["errors"].append(f"odds {day}: {exc}")

# Keep only one copy of each fixture and sort by kickoff.
seen = set()
unique = []
for item in snapshot["fixtures"]:
    fixture_id = (item.get("fixture") or {}).get("id")
    if fixture_id and fixture_id not in seen:
        seen.add(fixture_id)
        unique.append(item)
snapshot["fixtures"] = sorted(
    unique, key=lambda x: ((x.get("fixture") or {}).get("date") or "")
)
if remaining_values:
    snapshot["quota_remaining"] = min(remaining_values)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    f"Saved {len(snapshot['fixtures'])} fixtures and {len(snapshot['odds'])} odds rows "
    f"for {', '.join(dates)}; errors={len(snapshot['errors'])}; "
    f"quota_remaining={snapshot['quota_remaining']}"
)
if not snapshot["fixtures"] and snapshot["errors"]:
    sys.exit(1)
