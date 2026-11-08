#!/usr/bin/env bash
# Repository settings as code (IMP-M21-08, D12). Idempotent.
#
# Usage: scripts/repo-settings.sh [--check|--apply] [--harden] [REPO...]
#   --check   (default) read every setting and report drift; exit 1 if any.
#   --apply   set what differs.
#   --harden  also the flip-time hardening of IMP-M21-10 step 3 (secret scanning and push protection,
#             private vulnerability reporting, Dependabot alerts on / security updates off, CodeQL default
#             setup, a ruleset on master, read-only GITHUB_TOKEN, fork-PR approval, Pages on gh-pages for
#             common and sdk). Needs PUBLIC repositories: run it at the flip, not before. GHCR package
#             visibility has no API and stays with the owner.
# Without REPO arguments: the umbrella, the seven components and `.github`, whichever exist.
# Needs `gh` authenticated with admin rights on the organisation's repositories.
set -u

ORG="turnbase-platform"
HOME_URL="https://github.com/$ORG/turnbase"
MODE=check; HARDEN=0; repos=()
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE=check ;;
    --apply) MODE=apply ;;
    --harden) HARDEN=1 ;;
    -h|--help) sed -n '2,15p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) repos+=("$1") ;;
  esac
  shift
done
[ ${#repos[@]} -eq 0 ] && repos=(turnbase turnbase-common turnbase-sdk turnbase-platform turnbase-game-host \
  turnbase-frontend turnbase-game-tictactoe turnbase-game-7wonders-duel .github)

desc() {
  case "$1" in
    turnbase) echo "TurnBase — a platform and SDK for turn-based multiplayer games. Architecture, specs and the story of building it with AI agents." ;;
    turnbase-common) echo "TurnBase internal shared library: gRPC stubs and shared models" ;;
    turnbase-sdk) echo "TurnBase Game Development Kit — the Java and TypeScript SDK for building games" ;;
    turnbase-platform) echo "TurnBase Platform Monolith — Spring Boot 4.1, modular, Java 21" ;;
    turnbase-game-host) echo "TurnBase Game Host — GraalVM Espresso sandbox that runs game backends" ;;
    turnbase-frontend) echo "TurnBase web app — React 19, TypeScript, Astryx" ;;
    turnbase-game-tictactoe) echo "Tic-Tac-Toe for TurnBase — the reference game built on the SDK" ;;
    turnbase-game-7wonders-duel) echo "7 Wonders Duel for TurnBase — an unofficial implementation built on the SDK" ;;
    .github) echo "TurnBase organisation profile and community health files" ;;
  esac
}
topics() {
  local base="turnbase turn-based-games multiplayer"
  case "$1" in
    turnbase) echo "$base architecture spring-boot react ai-agents" ;;
    turnbase-common) echo "turnbase grpc java" ;;
    turnbase-sdk) echo "turnbase sdk game-development java typescript" ;;
    turnbase-platform) echo "turnbase spring-boot spring-modulith java websocket" ;;
    turnbase-game-host) echo "turnbase graalvm espresso sandbox java grpc" ;;
    turnbase-frontend) echo "turnbase react typescript vite websocket" ;;
    turnbase-game-tictactoe) echo "turnbase tic-tac-toe game-development" ;;
    turnbase-game-7wonders-duel) echo "turnbase 7-wonders-duel game-development" ;;
    .github) echo "turnbase" ;;
  esac
}
homepage() { [ "$1" = turnbase ] || [ "$1" = .github ] && echo "" || echo "$HOME_URL"; }

drift=0
note() { echo "DRIFT  $1: $2"; drift=$((drift + 1)); }

for r in "${repos[@]}"; do
  full="$ORG/$r"
  if ! cur=$(gh api "repos/$full" 2>/dev/null); then echo "SKIP   $r: does not exist"; continue; fi
  want_desc="$(desc "$r")"; want_home="$(homepage "$r")"
  want_topics="$(topics "$r" | tr ' ' '\n' | sort | tr '\n' ' ')"
  got_topics="$(echo "$cur" | python3 -c 'import json,sys; print(" ".join(sorted(json.load(sys.stdin)["topics"])), "")')"
  field() { echo "$cur" | python3 -c "import json,sys; v=json.load(sys.stdin)[\"$1\"]; print('' if v is None else str(v).lower() if isinstance(v,bool) else v)"; }
  patch=()
  [ "$(field description)" = "$want_desc" ] || { note "$r" "description"; patch+=(-f "description=$want_desc"); }
  [ "$(field homepage)" = "$want_home" ] || { note "$r" "homepage"; patch+=(-f "homepage=$want_home"); }
  [ "$(field has_issues)" = true ] || { note "$r" "issues off"; patch+=(-F has_issues=true); }
  [ "$(field has_projects)" = false ] || { note "$r" "projects on"; patch+=(-F has_projects=false); }
  [ "$(field has_wiki)" = false ] || { note "$r" "wiki on"; patch+=(-F has_wiki=false); }
  if [ "$got_topics" != "$want_topics" ]; then
    note "$r" "topics ($got_topics != $want_topics)"
    [ "$MODE" = apply ] && { args=(); for t in $want_topics; do args+=(-f "names[]=$t"); done
      gh api -X PUT "repos/$full/topics" "${args[@]}" >/dev/null || echo "FAIL   $r: topics"; }
  fi
  if [ "$MODE" = apply ] && [ ${#patch[@]} -gt 0 ]; then
    gh api -X PATCH "repos/$full" "${patch[@]}" >/dev/null || echo "FAIL   $r: patch"
  fi

  [ "$HARDEN" = 1 ] || continue
  # --- hardening (public repositories) ---
  sa() { echo "$cur" | python3 -c "import json,sys; print((json.load(sys.stdin).get('security_and_analysis') or {}).get('$1',{}).get('status',''))"; }
  for k in secret_scanning secret_scanning_push_protection; do
    if [ "$(sa $k)" != enabled ]; then
      note "$r" "$k"
      [ "$MODE" = apply ] && gh api -X PATCH "repos/$full" -f "security_and_analysis[$k][status]=enabled" >/dev/null
    fi
  done
  gh api "repos/$full/private-vulnerability-reporting" --jq .enabled 2>/dev/null | grep -q true || {
    note "$r" "private vulnerability reporting"
    [ "$MODE" = apply ] && gh api -X PUT "repos/$full/private-vulnerability-reporting" >/dev/null; }
  gh api "repos/$full/vulnerability-alerts" >/dev/null 2>&1 || {
    note "$r" "Dependabot alerts"
    [ "$MODE" = apply ] && gh api -X PUT "repos/$full/vulnerability-alerts" >/dev/null; }
  if gh api "repos/$full/automated-security-fixes" --jq .enabled 2>/dev/null | grep -q true; then
    note "$r" "Dependabot security updates on (the freeze, conventions.md section 6)"
    [ "$MODE" = apply ] && gh api -X DELETE "repos/$full/automated-security-fixes" >/dev/null
  fi
  gh api "repos/$full/code-scanning/default-setup" --jq .state 2>/dev/null | grep -qx configured || {   # -x: "not-configured" contains "configured"
    note "$r" "CodeQL default setup"
    [ "$MODE" = apply ] && { gh api -X PATCH "repos/$full/code-scanning/default-setup" -f state=configured >/dev/null \
      || echo "FAIL   $r: CodeQL default setup"; }; }
  gh api "repos/$full/rulesets" --jq '.[].name' 2>/dev/null | grep -qx master-protect || {
    note "$r" "ruleset master-protect"
    [ "$MODE" = apply ] && gh api -X POST "repos/$full/rulesets" --input - >/dev/null <<'JSON'
{"name":"master-protect","target":"branch","enforcement":"active",
 "conditions":{"ref_name":{"include":["refs/heads/master"],"exclude":[]}},
 "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}
JSON
  }
  gh api "repos/$full/actions/permissions/workflow" --jq .default_workflow_permissions 2>/dev/null | grep -qx read || {
    note "$r" "default GITHUB_TOKEN not read-only"
    [ "$MODE" = apply ] && gh api -X PUT "repos/$full/actions/permissions/workflow" -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false >/dev/null; }
  gh api "repos/$full/actions/permissions/fork-pr-contributor-approval" --jq .approval_policy 2>/dev/null | grep -qx all_external_contributors || {
    note "$r" "fork-PR workflows do not need approval"
    [ "$MODE" = apply ] && gh api -X PUT "repos/$full/actions/permissions/fork-pr-contributor-approval" -f approval_policy=all_external_contributors >/dev/null; }
  case "$r" in turnbase-common|turnbase-sdk)
    gh api "repos/$full/pages" >/dev/null 2>&1 || {
      note "$r" "Pages not enabled"
      [ "$MODE" = apply ] && gh api -X POST "repos/$full/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null; } ;;
  esac
done

if [ "$drift" -eq 0 ]; then echo "OK     no drift"; exit 0; fi
if [ "$MODE" = apply ]; then echo "APPLIED $drift change(s); re-run with --check to confirm"; exit 0; fi
echo "$drift drift(s)"; exit 1
