#!/usr/bin/env python3
"""Fetch fixtures, available pre-match odds and recent team form from API-Football."""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://v3.football.api-sports.io"
TZ = ZoneInfo("Asia/Bangkok")
KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
OUT = Path("data/football.json")
MAX_FORM_TEAMS = 16

if not KEY:
    print("Missing API_FOOTBALL_KEY secret", file=sys.stderr); sys.exit(1)

def get(endpoint, params):
    req = urllib.request.Request(
        f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}",
        headers={"x-apisports-key": KEY, "User-Agent": "lite-football-scout/1.0"},
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
    "app":"LITE FOOTBALL SCOUT","schema_version":2,"timezone":"Asia/Bangkok",
    "fetched_at":now.isoformat(),"dates":dates,"fixtures":[],"odds":[],
    "team_form":{},"errors":[],"quota_remaining":None,
    "sources":["API-Football v3"]
}
remaining_values=[]
def record_remaining(value):
    if value is not None:
        try: remaining_values.append(int(value))
        except (ValueError, TypeError): pass

for day in dates:
    for endpoint, params, key in [
        ("fixtures", {"date":day,"timezone":"Asia/Bangkok"}, "fixtures"),
        ("odds", {"date":day,"timezone":"Asia/Bangkok","page":1}, "odds"),
    ]:
        try:
            rows, remaining=get(endpoint,params)
            snapshot[key].extend(rows); record_remaining(remaining)
        except Exception as exc:
            snapshot["errors"].append(f"{endpoint} {day}: {exc}")

seen=set(); unique=[]
for item in snapshot["fixtures"]:
    fx=item.get("fixture") or {}; fid=fx.get("id")
    if fid and fid not in seen:
        seen.add(fid); unique.append(item)
snapshot["fixtures"]=sorted(unique,key=lambda x:((x.get("fixture") or {}).get("date") or ""))

# Fetch last five completed fixtures for up to 16 unique teams (8 matches).
team_ids=[]
for match in snapshot["fixtures"]:
    teams=match.get("teams") or {}
    for side in ("home","away"):
        tid=(teams.get(side) or {}).get("id")
        if tid and tid not in team_ids: team_ids.append(tid)
        if len(team_ids)>=MAX_FORM_TEAMS: break
    if len(team_ids)>=MAX_FORM_TEAMS: break

for tid in team_ids:
    try:
        rows,remaining=get("fixtures",{"team":tid,"last":5,"timezone":"Asia/Bangkok"})
        record_remaining(remaining)
        snapshot["team_form"][str(tid)]=rows
    except Exception as exc:
        snapshot["errors"].append(f"team form {tid}: {exc}")

if remaining_values: snapshot["quota_remaining"]=min(remaining_values)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Saved {len(snapshot['fixtures'])} fixtures, {len(snapshot['odds'])} odds rows, "
      f"{len(snapshot['team_form'])} team forms; quota_remaining={snapshot['quota_remaining']}; "
      f"errors={len(snapshot['errors'])}")
if not snapshot["fixtures"] and snapshot["errors"]: sys.exit(1)
