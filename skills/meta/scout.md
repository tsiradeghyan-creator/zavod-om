# Scout — self-improvement loop (meta skill)

## Goal
Keep ZavodOM at the frontier: when a better model / tool / technique appears online, find it,
evaluate it, and (on human approval) adopt it. Never auto-install — always gated.

## Cadence
Weekly, scheduled via the `/schedule` cloud routine (or run on demand). Pairs with `lib/scout.py`
and the registry `library/known_capabilities.json`.

## Protocol
1. **Search** (15-25 queries): new video/image/audio models, Remotion/render libs, transition/effect
   packages, competitor agentic-video pipelines, relevant papers/Reddit/HN/release notes. Use the
   web tools. Include "since:<last run date>".
2. **Dedup**: drop anything already in `library/known_capabilities.json` (`scout.is_new`).
3. **Score** each survivor with the agent's estimates → `scout.score_finding`:
   capability_gain, quality_gain (vs our current best), cost, license_ok, fit (0-1).
4. **Memo**: `scout.build_memo(findings, registry)` → a gated upgrade memo. Present to the owner.
   Nothing is installed. Flag paid tools (config `require_approval_for_new_paid_tool: true`).
5. **On approval**: for each adopted item — draft a Layer-2 skill via `meta/skill-creator.md`
   (or a per-model prompting file under `skills/creative/prompting/`), add a `providers/` adapter
   if it's a new gen backend, register it in `known_capabilities.json`, and log to the project log.
6. **Benchmark** (periodic): re-score our stations vs the market using `world-benchmark.md`; flag any
   station that's been beaten.

## Reliability (wake-safe — the recurring failure the audit flagged)
The prior zavod's automation kept dying silently: cron jobs asleep at night, DNS errors, an
obsidian-sync blocked by macOS TCC. Scout must not repeat that.
- Schedule via **launchd** (`tools/com.zavodom.scout.plist`), NOT cron — `StartCalendarInterval`
  fires on next wake if the machine was asleep. (cron skips missed runs.)
- Each run **first executes `lib/healthcheck.py`**; if RED, Scout posts the health failure instead
  of silently proceeding (human-readable signal — the council's #1 ask).
- Network failures → retry with backoff, then log a "scout-degraded" note rather than dying quiet.
- On macOS, the launchd job needs Full Disk Access if it touches `~/Documents` (TCC).
- Install (owner action, not auto): `cp tools/com.zavodom.scout.plist ~/Library/LaunchAgents/ &&
  launchctl load ~/Library/LaunchAgents/com.zavodom.scout.plist`.

## Hard rule
Scout proposes; the owner disposes. No capability is wired into a pipeline without an approved memo.
