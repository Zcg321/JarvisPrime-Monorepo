#!/usr/bin/env bash
set -euo pipefail
URL="http://127.0.0.1:8000/chat"
cmd=${1-}
if [[ -n "$cmd" ]]; then
  case "$cmd" in
    list)
      payload='{"message":"list_tools"}'
      ;;
    pool)
      payload='{"message":"dfs_pool","args":{"source":"mock","N":5,"salary_cap":50000,"roster_slots":{"PG":2,"SG":2,"SF":2,"PF":2,"C":1},"max_from_team":3,"seed":7}}'
      ;;
    expose)
      payload='{"message":"dfs_exposure_solve","args":{"target_size":5,"per_player_max_pct":0.6,"team_max":3,"diversity_lambda":0.1,"seed":7}}'
      ;;
    showdown)
      payload='{"message":"dfs_showdown","args":{"salary_cap":50000,"max_from_team":5,"seed":11}}'
      ;;
    record)
      payload='{"message":"dfs_record_result","args":{"slate_id":"LOCAL-TEST","entry_fee":100,"winnings":150,"lineup_signature":"auto"}}'
      ;;
    ghost-seed)
      payload='{"message":"dfs_ghost_seed","args":{"lineups_from":"pool_top","k":4,"slate_id":"LOCAL-TEST"}}'
      ;;
    ghost-inject)
      payload='{"message":"dfs_ghost_inject","args":{"k":3,"mutate_rate":0.1,"salary_cap":50000,"roster_slots":{"PG":2,"SG":2,"SF":2,"PF":2,"C":1},"max_from_team":3,"seed":19}}'
      ;;
    *)
      payload='{"message":"'"$cmd"'"}'
      ;;
  esac
  curl -s "$URL" -H "Content-Type: application/json" -d "$payload" | jq .
  exit 0
fi

python3 - <<'PY'
import json, urllib.request
print("Jarvis CLI (stub). Type ':q' to exit.")
while True:
    t = input("\nYou> ").strip()
    if t in (":q", "quit", "exit"):
        break
    req = urllib.request.Request(
        "http://127.0.0.1:8000/chat",
        data=json.dumps({"message": t}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        print(r.read().decode())
PY
