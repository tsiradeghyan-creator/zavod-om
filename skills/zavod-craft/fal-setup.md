# fal.ai Engine — One-Step Setup (Station 2 upgrade)

fal.ai is the single engine that exposes **Seedance · Kling · Veo · Nano Banana** together
(matches the Jack-vs-AI workflow). It needs one API key tied to the user's fal.ai account.

## What the user does (one step, plain language)
1. Go to **fal.ai**, sign in (Google login is fine).
2. Open the **Keys / API Keys** page, click **Create key**, copy it.
3. Paste the key to Claude: "aha fal բանալին: <key>".

## What Claude does when the key arrives
Safely add the server to `~/.claude.json` (back up first), preserving all existing servers
(`filesystem`, `fetch`, `chrome-devtools`). Insert under `mcpServers`:

```json
"fal-ai": {
  "command": "npx",
  "args": ["-y", "fal-ai-mcp-server"],
  "env": { "FAL_KEY": "<PASTED_KEY>" }
}
```

Safe edit (do not hand-edit JSON blindly):
```bash
python3 - "$FAL_KEY" <<'PY'
import json, os, sys, shutil
p = os.path.expanduser('~/.claude.json')
shutil.copy(p, p + '.bak')
d = json.load(open(p))
d.setdefault('mcpServers', {})['fal-ai'] = {
    "command": "npx", "args": ["-y", "fal-ai-mcp-server"],
    "env": {"FAL_KEY": sys.argv[1]}
}
json.dump(d, open(p, 'w'), indent=2, ensure_ascii=False)
print("added fal-ai")
PY
```
Then tell the user to restart Claude Code so the engine loads. After that the `fal-ai-media`
skill's tools (`search`/`find`/`generate`/`result`) are live.

## Until the key is added — fallback engines (already live, no setup)
- **Canva** + **Adobe Firefly** MCP for photo/carousel backgrounds.
- **Adobe Firefly** has Kling inside for short video.
So the zavod is fully operational for photos/carousels today; fal.ai is the video/quality upgrade.

Status: ✅ CONFIGURED (FAL_KEY added 2026-06-05). Restart Claude Code to load `fal-ai`,
then the `fal-ai-media` tools (`search`/`find`/`generate`/`result`) are live.

> **This file is setup only.** The 2026 engine lineup (which model per need), the
> Armenian-text protocol, the consistency/seed/cost workflow and render QC all live in
> **`ai-pipeline.md`** — don't duplicate the model list here; it drifts. Point to that file.
