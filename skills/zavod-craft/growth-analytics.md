# Growth & Analytics — Աճ և վերլուծություն (Station 4.5)

The growth analyst + community ops station. Posting mechanics live in `playbook.md`; this
file closes the LOOP — turning numbers into next week's content and feeding decisions back
upstream to story and producing. Without this station the zavod ships blind.

## Live-data layer (our doctrine, their real-time numbers)

Static rules go stale; specialized tools have the live API data we don't. **We own the
decisions; they own the feed.** Plug in one and read it into the loop below:
- **Metricool** — real posting-time heatmap per OUR audience, competitor benchmarking,
  scheduling. (Replaces the generic "19:00–21:00" guess with this account's actual curve.)
  **2026: Metricool Studio** — plain-language → auto charts/tables/takeaways, shared as a
  live always-current URL (client reporting solved) + **Campaign Dashboard** (organic + paid
  in one combined view).
- **Predis.ai** — surfaces under-served themes in the niche + analytics → feeds `idea-lab.md`.
  2026 adds an AI Ad Maker (one-click ad creative) — relevant only for the boost lane below.
- **Predictive pre-publish scoring (2026 trend):** tools now forecast a post's reach BEFORE
  publishing. Treat like every ranker in this zavod: **it proposes, taste decides** — a low
  predicted score on an on-voice post is information, never a veto.
- **Flick / Iris** — live trend + trending-audio detection for Reels hooks.
- **Iconosquare** — deep IG analytics + competitor tracking.
Rule: a number from the live tool **overrides** a number written in any zavod file — then
update the file (the self-improving loop). Without a feed, fall back to the file defaults.

## Weekly analytics loop (numbers → next week's plan, written down)

| Metric | Decides |
|---|---|
| Saves / reach | next carousel TOPIC (what they want to keep) |
| Follows / reach | which HOOKS convert strangers |
| Swipe-through rate | carousel SLIDE COUNT (where they drop) |
| Retention curve (Reels) | cut RHYTHM and ideal length |
| Paywall-conversion (vertical) | which cliffhanger TYPES sell (`serial-structure.md`) |
| Second-by-second drop-off | corrects the **predicted tension curve** (`serial-structure.md` / `post-production.md`) — where the audience actually left vs. where we predicted a dip |

Every Monday: read last week's numbers, write the three content decisions they imply,
schedule against them. Audience pain in comments feeds `idea-lab.md` (comment-mining).

## Trial Reels A/B protocol (the hook engine)

- 3–5 Trial Reels/week to **non-followers**, zero profile risk, 72h verdict window.
- **2026 platform rules: max 5 trials/day, and IG scans trials for near-duplicates** — a
  slightly re-edited copy of the same video risks a spam flag on the account.
- **One variable per trial — but the variable must be a genuinely different TAKE,** not a
  re-render: a different hook ANGLE (fear vs nostalgia vs numbers), a different frame-1 scene,
  a different structure. Never the same footage with one word swapped (that's now
  self-sabotage, not science).
- Winners graduate to the main feed; log what won and why (the hook bank).

## Community ops

- **First hour:** DM/share the drop to the 8–12 person close circle / Telegram group
  (keep consistent with `playbook.md` velocity gate). The math behind it (2026 weights):
  a DM send ≈ 15 likes, a save ≈ 10 — twelve close-circle sends outweigh ~180 likes.
- **Comment-keyword → auto-DM funnel** (ManyChat-class): a keyword in comments triggers a
  DM with the lead magnet — DM sends are a top ranking signal AND convert viewers to leads.
- **Broadcast channel:** weekly cadence, no follower minimum — a loyalty signal IG rewards.

## Telegram editor

- Native Telegram formats (NOT IG screenshots): folder cross-promo packs, forward-from-channel
  CTA, premium emoji, **Stars** monetization (`playbook.md` monetization layer).

## Paid amplification

- **Boost only proven organic winners** (never cold creative); Spark-style ads on the
  Reels that already cleared the audition.
- **Geo-target** Glendale + Moscow evenings — the diaspora window (`localization.md`).

## Arbitrage ROI tracker (the diaspora play, by the numbers)

Makes the «Armenian arbitrage» strategy (`producer-craft.md`) data-driven: shoot once in
Armenian, AI-dub EN/RU, sell to platforms — but only translate what pays.
- **Track per episode/language:** paywall revenue on each foreign platform (RU for Moscow,
  EN for LA/Glendale) vs. the **dub cost** (ElevenLabs v3 minutes + localization QC time).
- **Net ROI = revenue − (dub + sub + QC cost)**; rank languages/episodes by ROI.
- **Decision output:** which episodes to dub NEXT (highest projected ROI first), which language
  to prioritize per title, and when an episode's ROI goes negative → stop translating it.
- Feeds `producer-craft.md` greenlights and `localization.md` the dub queue. Pull revenue from
  the platform dashboards (live-data layer above); pull dub cost from the fal/ElevenLabs usage logs.

## Feeding decisions upstream

- Episode-level retention + paywall-conversion dashboards inform greenlights in
  `producer-craft.md` (replace gut with episode-8 conversion data).
- Cliffhanger-type performance feeds the typed menu in `serial-structure.md`.

## Growth checklist
- [ ] Monday analytics loop run; three content decisions written and scheduled.
- [ ] Trial Reels live (one variable each); winners logged to the hook bank.
- [ ] First-hour share + auto-DM funnel firing; broadcast channel posted weekly.
- [ ] Boosts only on proven winners; diaspora geo-targeting on.
- [ ] Retention/paywall data fed back to producing + serial-structure.
