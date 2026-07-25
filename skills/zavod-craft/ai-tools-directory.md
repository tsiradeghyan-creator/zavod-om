# AI Tools Directory — which tool for which job

Cross-stage reference: a categorized map of AI production tools, for picking an engine per task.
Distilled from the owner's *Soyuz AI Lab* "Шпаргалка по нейросетям" (full sheet with pricing/mode
notes in the owner vault `ԴԱՍ Ai/материалы/СОЮЗ. Шпаргалка по нейросетям.xlsx`). Orientation only —
verify current pricing/limits before spend. Consulted by **asset-director** (engine choice),
**executive-producer** (budget/tooling), and `world-benchmark.md` (competitive baseline).

> Engine-lock still governs: media generation runs one of the two locked lanes (Higgsfield AI-footage
> lane vs Remotion programmatic lane) — this directory informs the choice, it does not relax the lock.

## Text / reasoning
- **ChatGPT** — universal LLM: scripts, ideas, structure, code. (Projects to keep briefs separate; custom instructions for persona.)
- **Claude** — long-doc analysis, writing, code; strong safety/reasoning.
- **Gemini** — multimodal, Google Workspace integration.
- **DeepSeek** — open-source, free coding/analysis assistant.

## Image
- **OpenAI gpt-image** (`gpt-image-2` default) — text→image + image-edit; strongest for in-image text, logos, ads, infographics, product/UI mockups, style transfer, object removal, character consistency. Prompt/API guidance → `gpt-image-prompting/` skill (use-case routing + generate/edit code).
- **Midjourney** — top all-round quality, wide style range.
- **Freepik (FLUX)** — versatile, custom character/style + LoRA, editing, some video.
- **Ideogram** — images **with legible text** (logos, posters); inpaint/outpaint.
- **Leonardo AI** — design/concepts, trainable models (DreamBooth/LoRA).
- **DALL·E 3** — strong prompt-following in ChatGPT/Bing.
- **Krea** — free generator + prompt inspiration, cloud style training.

## Video (text/image → video)
- **Sora (OpenAI)** — remix/extend/loop/blend/storyboard.
- **Google Veo** — native audio (dialogue/SFX), realistic physics, lip-sync.
- **Kling** — face-swap, motion brush, start/end frames, lip-sync.
- **Runway** — text/image→video + editor (bg/light/object replace).
- **Higgsfield AI** — 80+ camera presets, VFX, upscale (the zavod's Higgsfield lane; see the `higgsfield` skill).
- **MiniMax / Pika / Luma** — fast short clips; Luma Reframe does 16:9→9:16.

## Voice / speech / avatars
- **ElevenLabs** — realistic TTS, voice cloning, emotion.
- **HeyGen** — talking-avatar from photo/video, lip-sync 40+ languages, subtitles.
- **D-ID** — face animation from a photo + TTS.
- **Speechmatics** — speech-to-text, 40+ languages, diarization.

## Music / audio
- **Suno / Udio** — songs (music + vocals) from text.
- **Soundraw / AIVA** — background/instrumental scoring, MIDI export.
- **UVR (Ultimate Vocal Remover)** — split vocals/instrumental, local & open-source.

## Chatbots / no-code / worth watching
- **SaleBot / BotHelp / ChatPlace** — messenger bots, funnels, lead capture (IG/TG).
- **Weavy** — node-based no-code workflow builder chaining AI models.
- **ComfyOnline** — run ComfyUI workflows in the cloud, auto-API.
- **Flawless / Papercup** — lip-sync dubbing/translation with voice retention.
- **Ebsynth / Kaiber / LeiaPix** — stylize video from one frame · image→clip · image→3D parallax.

## Cross-refs
Engine mechanics → `ai-pipeline.md`, `prompt-axes.md`, `providers/higgsfield-capabilities.md` +
the standalone `higgsfield` skill. Cartoon-specific prompting → `commercial-prompt-library/ai-cartoon-reel.md`.
Competitive baselines → `world-benchmark.md`.
