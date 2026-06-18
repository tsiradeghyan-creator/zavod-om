# Serial Structure — Սերիալի ճարտարապետություն (Station 0.5)

The missing structural station between idea and script. `idea-lab.md` decides IF a world
should be a serial (the character-engine test); this file decides HOW the season is built
so threads, turns and cliffhangers compound instead of drift. Voice stays `style-profile.md`.

## Season arc grid (a live tracker, not a sketch)

A matrix: **episodes (rows) × threads (columns)** — kept as a real trackable table in
`bible-<slug>.md`, the way Laper-class tools track arcs, but voice-tuned. Each thread carries
three running counters so nothing drifts:
- **State** — setup / escalation / reversal / payoff (the cell's beat).
- **Heat (1–10)** — emotional intensity this episode (drives the intercut energy match).
- **Turns-due** — episodes since this thread last turned; **must reset to 0 every ≤3 eps**, or
  the thread is flagged cold and gets the next turn.

| Ep | A: Rob⟂Eva (heat) | B: Arsen⟂Sofi | C: Edgar⟂Anna | Convergence? |
|----|----|----|----|----|
| 1 | setup · 6 · 0 | setup · 4 · 0 | — | — |
| 2 | escalate · 7 · 0 | — (cold:1) | setup · 5 · 0 | — |
| 3 | reversal · 9 · 0 | escalate · 6 · 0 | — (cold:1) | A×B first shared scene |

- Her signature is **intercut parallel threads that converge** (e.g. «Ֆեզանից հետո»:
  Rob⟂Eva + Arsen⟂Sofi + Edgar⟂Anna) — the grid's Convergence column pre-places the joins.
- **Heat-direction match at the joins:** when two threads cut together, one should be rising
  while the other falls (`director-craft.md` screen-direction maps execute it).

## A/B/C braiding map

- Assign tempo per thread: A = engine (fastest turns), B = slow-burn, C = comic/relief.
- **Energy-direction matching at the joins:** A ends rising → B opens falling, so the
  intercut breathes (`director-craft.md` screen-direction maps execute this on screen).
- Convergence episodes = where two threads first share a scene/axis — pre-place them.

## Tentpole planning (place these before writing episodes)

| Tentpole | Where | Her house model |
|---|---|---|
| Ep-1 hook / explosion point | first 15s (vertical) / ep 1 | a vet dancer who can't walk |
| First reveal | early act 1 | the false identity («Խաղալիք») |
| Midpoint reversal | center of season | the secret-carrier flips |
| False victory | ~3/4 | the relief before the gut-punch |
| Finale recontextualization | last episode | the end-revealed frame («Ճերմակ շապիկ») |

## Typed cliffhanger menu (rotate — never the same type twice running)

She defaults to collapse/door; rotate across these eight so endings don't blur:
1. **Collapse / medical** (Eva faints into Rob's arms)
2. **Door opens / arrival** (police at the door)
3. **Reveal to audience only** (dramatic irony — we know, they don't)
4. **Reveal to a character** (they finally learn what we knew)
5. **Decision on the brink** (cut before the choice)
6. **Wrong conclusion** (a character believes the false thing)
7. **Ticking clock** (a deadline named, then cut)
8. **Question-voiceover** (her «արտակադրային ձայն» poses the turn)

Rule: log the last type used per thread; the next cliffhanger on that thread is a
different number.

## Vertical micro-drama beat math

- **Hook ≤3–5s**, conflict immediately; ep-1 first 15s = built-in trailer.
- **Micro-cliff every episode**; a **mini-arc every 3 episodes**.
- **Paywall-grade turn at eps 8–12** — the strongest cliffhanger of act one IS the
  purchase (`director-craft.md` gives those eps double prep).
- **60–100 (up to 120) episodes** per season standard (`producer-craft.md` economics).

## Tension curve (the retention = money tool, vertical)

In a 60–100×1–2min season, holding attention to the paywall (eps 8–12) IS the business.
Map a **tension curve** per episode at the WRITING stage — honest rubric, not neuro-magic:
- Plot each beat's tension 1–10 across the minute; mark every spot where the curve **dips**
  (exposition, repetition, a held beat with no escalating info).
- **Every dip gets a fix scheduled:** a reversal, a reveal, a subtext-object plant, or a
  cliffhanger micro-turn (`typed cliffhanger menu` above) — no flat stretch longer than ~10–15s.
- The curve must **rise into the paywall episode**, not peak early.
- The edit stage re-checks this on the timeline (`post-production.md`); the real drop-off
  data from `growth-analytics.md` then corrects the rubric (the self-improving loop — predict,
  measure, adjust). Treat the predictive curve as a hypothesis the data confirms or kills.

## Story bible / lore-keeper protocol

Promote the `corpus-notes.md` reading-log pattern into a **living per-project bible**,
filed as `bible-<slug>.md` next to the idea bank:
- **Characters:** want / wound / secret per lead (who carries which secret — her engine).
- **Timeline** + a **what-each-character-knows table** (drives dramatic irony, prevents
  continuity breaks across out-of-order shooting — `production-team.md` continuity).
- **Plant / payoff registry + callback ledger:** every planted object/line and where it
  pays off; nothing is planted without a scheduled payoff, nothing pays off unplanted.
- The lore keeper owns continuity of FACTS across episodes; the script supervisor owns
  continuity on set.

**Active continuity guard (the Meta-Archivist — for 100s-of-episode serials).** The bible is
not a passive file; it ACTIVELY checks. When a new scene is written, match it against the
`bible-<slug>.md` facts + the who-knows table and **red-flag any contradiction**: a character
knowing something they shouldn't yet, a fact that conflicts with an earlier episode, a dead/
absent character appearing, a relationship state that regressed. Example: ep 130 references a
secret revealed differently in ep 15 → flag before it ships. This is where human memory fails
on daily serials (her biggest volume — «Ստար», «Էլենի որդին», «Կախարդություն» run 100–220+ eps);
runnable by the `zavod-scout` loop or a `python-docx` checker, output = a flag list, never a
silent edit.

## Serial-structure checklist
- [ ] Season grid built; every thread turns at least every 3 episodes.
- [ ] A/B/C tempo assigned; energy directions matched at the joins.
- [ ] Five tentpoles pre-placed, including the finale recontextualization.
- [ ] Cliffhanger types logged per thread — no repeat back-to-back.
- [ ] Vertical: hook ≤5s, paywall turn at eps 8–12, season length 60–100.
- [ ] `bible-<slug>.md` live: want/wound/secret, knows-table, plant/payoff registry.
