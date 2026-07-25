
# AI Cartoon Reel — 3D character mini-cartoons for Reels/Shorts

Prompt system for **AI-generated cartoon Reels** (ИИ-мультфильмы): recurring 3D characters,
short serial stories, commissioned commercial work. Built for **Seedance 2.0** (Higgsfield) but
the block structure ports to any text-to-video model. Consulted by **scene-director** (shot
language for cartoon briefs) and **asset-director** (prompt construction + character consistency).
Not a standalone skill — reference material inside the zavod brain.

Source: distilled from the *Soyuz AI Lab* commissioned-cartoon course (owner's purchased course;
full transcripts in the owner Obsidian vault `ԴԱՍ Ai/`). Techniques adapted, not reproduced.

## Seedance 2.0 on Higgsfield — Input Specs

- **Images:** up to 9 reference images (character sheets, style refs, location boards)
- **Videos:** up to 3 clips (motion refs)
- **Audio:** up to 3 files (voiceover, music, SFX)
- **Text:** full structured prompt (see 6-block structure)
- **Max Assets:** 12 combined · **Output:** 4–15s, vertical 9:16, synced audio
- **Reference syntax:** `@material[name]` to point at an uploaded character sheet / style board

---

## The 6-Block Prompt Structure (core method)

Seedance rewards **structured, detailed** prompts. Split every prompt into six ordered blocks.
The model does **not** invent the story — you are the director handing it a finished shot list.

| # | Block | What it controls | Example line |
|---|---|---|---|
| 1 | **Visual Style** | animation style, atmosphere, palette, lighting, detail, quality | `Premium 3D animated short in the style of Pixar and DreamWorks. Warm palette, soft light, high detail.` |
| 2 | **Technical** | aspect, duration, subtitles/dialogue flags (often set in the UI, can be omitted) | `Format: Vertical 9:16 · Duration: 10s` |
| 3 | **Characters** | each character **described separately** — look, age, hair, eyes, clothes, proportions, mood | `3 y.o. girl, blonde hair, blue eyes, red jacket + red skirt, white shoes, large head / tiny body, playful.` |
| 4 | **Setting** | location, **described apart from characters** | `Cozy sunny living room, warm morning light.` |
| 5 | **Shot-by-shot** | the actual sequence, broken into timestamped beats | `Shot 1 (00:00–00:02) girl sneaks with a cookie jar. Shot 2 (00:02–00:03) takes a cookie. Shot 3 (00:03–00:04) dog notices crumbs.` |
| 6 | **Style Requirements** | closing quality/consistency clause | `consistent character design, cinematic lighting, ultra-detailed, clean render.` |

**Golden rule:** describe **characters and location in separate blocks** — never mixed. The model
tracks the scene more reliably that way.

### Ready skeleton

```text
[1 VISUAL STYLE] Premium 3D animated short, <studio-look> style, <palette>, <lighting>, high detail.
[2 TECHNICAL] Vertical 9:16, <N> seconds.
[3 CHARACTERS]
  - <Character A>: <appearance / age / hair / eyes / clothes / proportions / mood>
  - <Character B>: <...>   (each described separately)
[4 SETTING] <location>, <time of day / light>.
[5 SHOT-BY-SHOT]
  Shot 1 (00:00–00:0X): <action>
  Shot 2 (00:0X–00:0Y): <action>
  ...
[6 STYLE REQUIREMENTS] consistent character design, <mood> lighting, ultra-detailed, clean render.
```

---

## Character consistency — the Character Sheet method

The #1 failure of AI cartoons is a character that **drifts between shots**. Fix it upstream: build a
**Character Sheet** once, then feed it as a reference (`@material[...]`) into every scene.

Generate the sheet from a source photo (or invented design) and lock these views:

- **Full body:** front, 3/4, side, back
- **Head turnaround:** front, 3/4 L, profile L, 3/4 R, profile R
- **Expression sheet:** neutral, smile, laugh, surprise, sadness, anger, fear, close-up
- **Detail plates:** hairstyle, footwear, accessories

Quality clause: `professional animation model sheet, character turnaround, expression sheet, clean
white background, consistent character design, ultra detailed`.

**Never-change list** (record per character, hold across the whole cartoon): face shape, eye color,
hairstyle, key features, signature clothing/accessories, body proportions. When location or lighting
changes, or the hero appears in several shots in a row — **always** attach the reference.

---

## Format map (pick the container after the character exists)

Create the **character first**, then choose the format it lives in. One character reuses across all.

| Format | Length | Job | Beat |
|---|---|---|---|
| **Animated Reel/Short** | 15–60s | grab attention fast; trend/joke/serial hook | most common commercial order |
| **Character story** | 1–3 min | full arc: goal → obstacle → development → finale | hero learns / overcomes |
| **Explainer cartoon** | short | teach through story, not a dry manual | apps, courses, clinics, experts, kids |
| **Ad cartoon** | short | product/service told *through* a story | reads as content, not an ad |
| **Kids content** | serial | fairy-tale / adventure / musical; builds a universe | each episode = new character/story |

---

## Style map — 14 ready style clauses

Clients ask "make it like Pixar / Disney / anime." Keep one **fixed character prefix**
(`<subject>, <fixed features>, <expression>,`) and swap only the **style clause** + background
(ФОН). Same character, 14 looks. (Reference chart in owner vault `ԴԱՍ Ai/визуальные-шпаргалки/mult stile.png`.)

| # | Style | Style clause (append after the character prefix) | Background cue |
|---|---|---|---|
| 1 | **Stylized 3D** | `stylized 3D animation, cinematic lighting, high detail` | modern apartment, big windows, warm light |
| 2 | **Pixar-like 3D** | `Pixar style 3D animation, family-friendly, colorful, soft lighting` | cozy kitchen, morning, warm atmosphere |
| 3 | **2D Cartoon** | `2D cartoon style, clean lines, flat colors` | bright simple room, plants, window |
| 4 | **Anime** | `anime style, detailed cel shading, expressive eyes, sunset lighting` | japanese apartment, evening |
| 5 | **Comic** | `comic book illustration, ink outlines, halftone texture, graphic novel style` | comic-panel interior, textures |
| 6 | **Clay animation** | `clay animation style, plasticine texture, stop motion look, handcrafted set` | plasticine room, toy objects |
| 7 | **Cut-out** | `cut-out animation style, paper textures, layered shapes, kids TV aesthetic` | paper clouds/trees/house, bright bg |
| 8 | **Storybook** | `storybook illustration, watercolor texture, children's book style, soft colors` | fairytale room, books, flowers |
| 9 | **Low poly 3D** | `low poly 3D style, geometric shapes, minimal environment, clean lighting` | minimalist room, simple forms |
| 10 | **Arcane** | `Arcane style, painterly, dramatic lighting, rich textures, fantasy city background` | Piltover-like workshop, industrial |
| 11 | **Anime 80s** | `80s anime style, vintage animation, hand painted look, nostalgic atmosphere` | retro apartment, old TV, sunset |
| 12 | **Urban anime** | `urban anime style, streetwear, neon city, night lighting, cyberpunk atmosphere` | neon streets, megacity, signs |
| 13 | **Wool stop-motion** | `wool stop motion style, felt texture, handmade look, cozy lighting` | knitted room, wool toys |
| 14 | **Painterly 2D** | `hand painted animation style, visible brush strokes, vibrant colors, artistic background` | artist's room, brushes, paints |

### Uniqueness formula + IP-safe mixing

`Style = Direction 1 + Direction 2 + your own element`. Mixing general techniques makes an original
look that copies **no single studio** — which is also the rights-safe path (own character + own
world + general techniques = safe; cloning a franchise's characters/world = not). Two worked mixes:

- `<char prefix>, stylized 3D animation, Pixar lighting, anime expressions, storybook textures, cozy room, warm sunlight, soft colors, cinematic composition`
- `<char prefix>, stylized 3D animation, DreamWorks proportions, comic outlines, cinematic lighting, modern apartment, city view, soft shadows, dynamic composition, graphic novel vibe`

Keep the **character** recognizable across every style (face shape, features, emotion). Build a
5-min/day "watched-ness" habit; adapt trends, don't clone them. On any franchise-lookalike request,
the rights gate (`../business-affairs.md`, `provenance`) still governs before generation.

---

## Retention spine (why it gets watched to the end)

Beauty does not retain — **story** does. Clients pay for views, watch-time, engagement, emotion.

**Formula:** `hook → conflict → development → emotion → finale`.

- **First 3 seconds decide everything** — open on a question/surprise/curiosity. *Girl finds a
  mysterious door in a park* ✅ beats *girl walks down a street* ❌.
- **Emotional characters** — viewers remember heroes, not graphics. The hero must feel: joy,
  surprise, anger, worry, fear, mistakes.
- **Conflict** — even a tiny one (running late, lost item, wants a gift) starts the story.
- **Cliffhanger** — end on "what happens next?" (hero opens a mysterious box, cut on the reaction).
- **Cut tempo** — if nothing changes for 5–7s, attention drops. Alternate wide / medium / close /
  emotion (this is why the shot list already varies planes).
- Pre-publish test: *"do I want to know what happens next?"* If no → strengthen. People forward an
  **emotion / joke / surprise**, not a pretty frame.

---

## Cross-refs inside the zavod

- Idea/serial beats → `../idea-lab.md`, `../serial-structure.md`
- Character asset consistency → `../art-department.md`, `../identity-guard.md`, `../no-duplicate-character-empty-plate.md`
- Prompt axes / shot language → `../prompt-axes.md`, `../director-craft.md`, `../storyboard.md`
- Montage, sound, retention finish → `../ai-cartoon-production-notes.md`, `../post-production.md`, `../sound-craft.md`
- Publishing / pricing → `../growth-analytics.md`, `../business-affairs.md`, `../ai-cartoon-production-notes.md`

**Կանոն.** Ձևանմուշները անգլերեն են; հայերեն արտադրության ժամանակ ամբողջ տեքստը անցնում է
glyph gate-ով, on-screen տեքստը՝ միայն overlay (ոչ AI-baked)։ Դեմքի/likeness policy-ն որոշվում է
`creative_identity`-ով նախքան գեներացիան։
