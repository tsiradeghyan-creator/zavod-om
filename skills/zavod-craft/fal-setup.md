# fal.ai Engine — Setup (Station 2 upgrade)

fal.ai is the single engine that exposes **Seedance · Kling · Veo · Nano Banana** together
(matches the Jack-vs-AI workflow). It needs one API key tied to the user's fal.ai account.

## Official setup (recommended) — hosted MCP
fal-ի պաշտոնական MCP-ն hosted սերվեր է՝ `https://mcp.fal.ai/mcp-relay`, մուտքը OAuth-ով
(fal.ai account-ով), API key պետք չէ (fal docs-ով ստուգված 2026-11-26՝
[Setting up MCP](https://fal.ai/docs/documentation/setting-up/mcp))։ Հին ձևը՝
`https://mcp.fal.ai/mcp` + `Authorization: Bearer` header, այլևս առաջարկվող չէ (verify live)։

1. Սեփականատերը terminal-ում ավելացնում է սերվերը.
```bash
claude mcp add --transport http fal-ai https://mcp.fal.ai/mcp-relay
```
2. Restart Claude Code, `/mcp` → fal-ai → մուտք fal.ai account-ով (OAuth)։ Բանալին չատով չի ուղարկվում։
3. Պաշտոնական գործիքները՝ `search_models` · `get_model_schema` · `get_pricing` ·
   `search_docs` · `recommend_model` · `run_model` · `submit_job` · `check_job` ·
   `get_job_result` · `cancel_job` · `upload_file`։

## Old laptop install (legacy, gone with the old computer)
Հին laptop-ի `~/.claude.json`-ում դրված էր **երրորդ կողմի** `fal-ai-mcp-server` npm փաթեթը
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

Status (2026-11-26): the old laptop is replaced; on the new computer set up the official hosted
MCP above (OAuth) instead of the legacy npm server։

> **This file is setup only.** The 2026 engine lineup (which model per need), the
> Armenian-text protocol, the consistency/seed/cost workflow and render QC all live in
> **`ai-pipeline.md`** — don't duplicate the model list here; it drifts. Point to that file.
