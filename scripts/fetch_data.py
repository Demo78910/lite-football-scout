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
MAX_DETAIL_FIXTURES = 5
DETAIL_ENDPOINTS = ("statistics", "injuries", "predictions", "lineups")

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
    "team_form":{},"fixture_details":{},"data_quality":{},"errors":[],"quota_remaining":None,
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

# Select form teams from fixtures with available odds first, then fill the
# remaining slots in kickoff order. The Free plan does not allow "last".
odds_fixture_ids={
    (row.get("fixture") or {}).get("id")
    for row in snapshot["odds"]
    if (row.get("fixture") or {}).get("id")
}
ordered_fixtures=sorted(
    snapshot["fixtures"],
    key=lambda row: (
        0 if ((row.get("fixture") or {}).get("id") in odds_fixture_ids) else 1,
        ((row.get("fixture") or {}).get("date") or "")
    )
)
team_ids=[]
for match in ordered_fixtures:
    teams=match.get("teams") or {}
    for side in ("home","away"):
        tid=(teams.get(side) or {}).get("id")
        if tid and tid not in team_ids:
            team_ids.append(tid)
        if len(team_ids)>=MAX_FORM_TEAMS: break
    if len(team_ids)>=MAX_FORM_TEAMS: break

form_from=(now-timedelta(days=120)).date().isoformat()
form_to=(now-timedelta(days=1)).date().isoformat()
finished={"FT","AET","PEN"}
for tid in team_ids:
    try:
        rows,remaining=get("fixtures",{
            "team":tid,"from":form_from,"to":form_to,
            "timezone":"Asia/Bangkok"
        })
        record_remaining(remaining)
        completed=[
            row for row in rows
            if ((row.get("fixture") or {}).get("status") or {}).get("short") in finished
            and (row.get("goals") or {}).get("home") is not None
            and (row.get("goals") or {}).get("away") is not None
        ]
        completed.sort(
            key=lambda row: ((row.get("fixture") or {}).get("date") or ""),
            reverse=True
        )
        snapshot["team_form"][str(tid)]=completed[:5]
    except Exception as exc:
        snapshot["errors"].append(f"team form {tid}: {exc}")

# Enrich a small, deterministic shortlist to stay within the Free plan's
# 100 requests/day budget. Five fixtures x four endpoints = 20 calls/run.
# With two scheduled runs plus the 20 base calls, expected use is ~80/day.
detail_fixtures=[]
seen_detail=set()
for match in ordered_fixtures:
    fid=(match.get("fixture") or {}).get("id")
    if fid and fid not in seen_detail:
        seen_detail.add(fid)
        detail_fixtures.append(match)
    if len(detail_fixtures)>=MAX_DETAIL_FIXTURES: break

for match in detail_fixtures:
    fixture=match.get("fixture") or {}
    fid=fixture.get("id")
    detail={"fixture_id":fid,"fetched_at":now.isoformat(),"statistics":[],
            "injuries":[],"predictions":[],"lineups":[],"available":{}}
    for endpoint in DETAIL_ENDPOINTS:
        try:
            rows,remaining=get(endpoint,{"fixture":fid})
            record_remaining(remaining)
            detail[endpoint]=rows
            detail["available"][endpoint]=bool(rows)
        except Exception as exc:
            detail["available"][endpoint]=False
            snapshot["errors"].append(f"{endpoint} fixture {fid}: {exc}")
    snapshot["fixture_details"][str(fid)]=detail
    snapshot["data_quality"][str(fid)]={
        "form_home":len(snapshot["team_form"].get(str((match.get("teams") or {}).get("home",{}).get("id")),[])),
        "form_away":len(snapshot["team_form"].get(str((match.get("teams") or {}).get("away",{}).get("id")),[])),
        "details_available":sum(1 for value in detail["available"].values() if value),
        "details_checked":len(DETAIL_ENDPOINTS)
    }

if remaining_values: snapshot["quota_remaining"]=min(remaining_values)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Saved {len(snapshot['fixtures'])} fixtures, {len(snapshot['odds'])} odds rows, "
      f"{len(snapshot['team_form'])} team forms; quota_remaining={snapshot['quota_remaining']}; "
      f"errors={len(snapshot['errors'])}")
if not snapshot["fixtures"] and snapshot["errors"]: sys.exit(1)
