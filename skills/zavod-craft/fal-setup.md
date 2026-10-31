# fal.ai Engine — Setup (Station 2 upgrade)

fal.ai is the single engine that exposes **Seedance · Kling · Veo · Nano Banana** together
(matches the Jack-vs-AI workflow). It needs one API key tied to the user's fal.ai account.

## Official setup (recommended) — hosted MCP
fal-ի պաշտոնական MCP-ն hosted սերվեր է՝ `https://mcp.fal.ai/mcp`; բանալին ուղարկվում է
per-request `Authorization` header-ով և ոչ մի տեղ չի պահվում սերվերի կողմից։
([fal docs → Setting up MCP](https://fal.ai/docs/documentation/setting-up/mcp))

1. Սեփականատերը fal.ai dashboard-ից ստեղծում է API key։
2. **Բանալին ՉԻ ուղարկվում չատով** (չատի պատմությունը log/cache է լինում)։ Փոխարենը՝
   սեփականատերն ինքն է վազեցնում terminal-ում.
```bash
claude mcp add --transport http fal-ai \
  https://mcp.fal.ai/mcp \
  --header "Authorization: Bearer YOUR_FAL_KEY"
```
3. Restart Claude Code։ Պաշտոնական գործիքները՝ `search_models` · `get_model_schema` ·
   `get_pricing` · `search_docs` · `run_model` · `submit_job` · `check_job` ·
   `get_job_result` · `cancel_job` · `upload_file` · `recommend_model`։

## Current install on this machine (legacy, works)
Հիմա `~/.claude.json`-ում դրված է **երրորդ կողմի** `fal-ai-mcp-server` npm փաթեթը
(`npx -y fal-ai-mcp-server`, `FAL_KEY` env-ով)։ Այն աշխատում է և `fal-ai-media` skill-ի
գործիքներն էլ դրանից են — 2026-07 դրությամբ 12 գործիք՝ `search` · `find` · `models` ·
`generate` · `result` · `status` · `cancel` · `upload` · `pricing` · `estimate_cost` ·
`usage` · `analytics`։ Սա պաշտոնական սերվերը ՉԷ —
supply-chain ռիսկը սեփականատիրոջ գիտակցված ընտրությունն է։ Migration official hosted-ին՝
վերևի մեկ հրամանով; անելուց հետո `fal-ai-media` skill-ի գործիքների անունները թարմացնել։

## Fallback engines (no fal key needed)
- **Canva** + **Adobe Firefly** MCP for photo/carousel backgrounds.
- **Adobe Firefly** has Kling inside for short video.
So the zavod is fully operational for photos/carousels without fal; fal.ai is the
video/quality upgrade.

Status: ✅ CONFIGURED via legacy npm server (FAL_KEY added 2026-06-05)։ Official hosted
migration՝ pending owner decision։

> **This file is setup only.** The 2026 engine lineup (which model per need), the
> Armenian-text protocol, the consistency/seed/cost workflow and render QC all live in
> **`ai-pipeline.md`** — don't duplicate the model list here; it drifts. Point to that file.
