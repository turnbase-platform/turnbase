#!/usr/bin/env bash
# The post-run correctness check (IMP-M18-14, load-testing-phase-b.md §6), in addition to the k6 thresholds.
# Usage: loadtest/correctness.sh <run-dir> [wait_seconds=60]
# Reads <run-dir>/summary.json (k6's --summary-export) and the database, and prints one line per rule and a verdict:
#   games     tb_games_started == tb_games_completed + tb_games_abandoned (every started game is finished, or the
#             harness gave up on it and said so); scale-in.js / failover runs count tb_si_games_lost instead (must be 0)
#   sequence  tb_seq_gaps == 0 and tb_seq_dups == 0, over tb_seq_checked > 0 events (no GAME_EVENT sequence gap or duplicate seen by a client after dedup)
#   rooms     no room left IN_PROGRESS and no active session once the load is gone (polled up to <wait_seconds>)
# Writes the same text to <run-dir>/correctness.txt. Ends with `CORRECTNESS: PASS` or `CORRECTNESS: FAIL <rules>`.
# A run that was killed before summary.json was written fails the games rule.
set -uo pipefail
DIR="${1:?usage: correctness.sh <run-dir> [wait_seconds=60]}"
WAIT="${2:-60}"
S="$DIR/summary.json"
OUT="$DIR/correctness.txt"
val() { jq -r --arg m "$1" --arg k "$2" '.metrics[$m][$k] // 0' "$S" 2>/dev/null || echo 0; }
failed=()
{
  if [ ! -s "$S" ]; then
    echo "games: no summary.json"; failed+=(games)
  else
    started="$(val tb_games_started count)"; done_="$(val tb_games_completed count)"; aband="$(val tb_games_abandoned count)"
    lost="$(val tb_si_games_lost count)"; sifin="$(val tb_si_games_finished count)"
    if [ "$(jq -e '.metrics.tb_si_games_finished' "$S" >/dev/null 2>&1; echo $?)" = 0 ]; then
      echo "games: scale-in client: finished $sifin, lost $lost"
      [ "$lost" = 0 ] || failed+=(games)
    fi
    if [ "$started" = "$((done_ + aband))" ]; then
      echo "games: started $started = completed $done_ + abandoned $aband"
    else
      echo "games: started $started != completed $done_ + abandoned $aband (a started game is neither)"; failed+=(games)
    fi
    gaps="$(val tb_seq_gaps count)"; dups="$(val tb_seq_dups count)"
    checked="$(val tb_seq_checked count)"
    echo "sequence: gaps $gaps, duplicates $dups, over $checked broadcast GAME_EVENTs checked"
    [ "$started" = 0 ] || [ "$checked" != 0 ] || { echo "sequence: games ran but no event was checked"; failed+=(sequence); }
    [ "$gaps" = 0 ] && [ "$dups" = 0 ] || failed+=(sequence)
  fi
  q="select (select count(*) from room where state = 'IN_PROGRESS') || ',' || (select count(*) from room where active_session_id is not null and closed_at is null)"
  rooms=""
  for _ in $(seq $((WAIT / 5 + 1))); do
    rooms="$(kubectl exec statefulset/turnbase-postgres -- psql -U turnbase_owner -d turnbase -Atc "$q" 2>/dev/null)"
    [ "$rooms" = "0,0" ] && break
    sleep 5
  done
  if [ "$rooms" = "0,0" ]; then echo "rooms: none IN_PROGRESS, none with an active session"
  else echo "rooms: IN_PROGRESS,with-active-session = ${rooms:-unavailable}"; failed+=(rooms); fi
  if [ ${#failed[@]} = 0 ]; then echo "CORRECTNESS: PASS"; else echo "CORRECTNESS: FAIL ${failed[*]}"; fi
} | tee "$OUT"
[ ${#failed[@]} = 0 ]
