# Higgsfield — full capability map (read before choosing any gen tool)

> GENERAL provider knowledge for **every** ZavodOM agent (director/operator/art/editor/etc.).
> Higgsfield exposes one big arsenal — image, video, audio, 3D, editing, and marketing tools.
> Pick the right tool deliberately. Always `get_cost: true` to preflight credits.
> Account: PLUS (~1000 cr/mo). Verify live with `balance`. Discover live with `models_explore`.

## HARD invocation rules (never break)
- **`medias` go INSIDE `params`**: `params:{model,…,medias:[{role,value}]}`. Outside `params` → silently
  ignored → `input_images:[]` → runs as text-to-image with NO reference (the 06-15 wrong-villa bug).
- `medias[].value` = a **media_id** (from `media_upload`/`media_import_url`) or a **job_id** from a prior
  generation. Never a raw https URL.
- **Real-subject edits = image-to-image**: attach the real photo as reference (`nano_banana_pro`), prompt
  "keep this exact scene/architecture/light unchanged, add …". Generic text-to-image makes a *different*
  subject — banned for real-property/product posts.
- **Branded on-image text = overlay, not AI-baked** (fonts drift). Generate clean image, overlay type later.
- Poll async jobs with `job_status (sync:true)`; download `rawUrl` immediately (URLs expire).

## IMAGE models (`generate_image`)
| Model | Best for | Key params | Notes |
|---|---|---|---|
| `nano_banana_pro` | **real-photo edits**, text/diagrams, 4K | resolution 1k/2k/4k | top image-to-image; ratios incl 4:5,9:16,16:9 |
| `nano_banana_2` / `nano_banana` | fast / budget realistic | resolution | next-gen / cheap |
| `soul_2` (`soul_v2`) | **UGC, fashion editorial, character** | quality 1.5k/2k, `soul_id` | use trained Soul-ID for recurring faces |
| `soul_cinematic` | cinema-grade stills, concept art | quality, soul_id | dramatic lighting |
| `soul_cast` | consistent cinematic **character identity** | budget 10-500 | persona stills (16:9) |
| `soul_location` | **environments/locations/backgrounds** | — | empty-plate backgrounds |
| `seedream_v4_5` | 4K, precise control, transformations | quality basic/high | strong editing |
| `seedream_v5_lite` | instruction-based editing, reasoning | quality | smart edits |
| `flux_2` (pro/flex/max) | precise prompt adherence | resolution, model | |
| `flux_kontext` | context-aware editing, style transfer, typography | — | remix |
| `kling_omni_image` | versatile photorealistic, wide ratios | resolution | |
| `gpt_image` / `gpt_image_2` | **best text rendering**, logos, infographics | quality, resolution(2) | typography |
| `grok_image` | expressive, high-contrast, bold | mode std/quality | |
| `recraft-v4-1` | **logos/icons/vector/SVG**, product mockups, palettes | model_type standard/vector/utility/utility_vector, colors[], bg | brand assets |
| `cinematic_studio_2_5` | cinematic stills up to 4K | resolution | |
| `marketing_studio_image` / `ms_image` (DTC) | **product ad images**, brand-kit-aware | `style_id`(req for ms_image), brand_kit_id, product_ids | run `show_marketing_studio` first |
| `image_auto` | auto-routes to best image model | — | when unsure |
| `autosprite` | **game sprite sheets** from a character image | kind, frame_count/size, video_tier | atlas+audio |

## VIDEO models (`generate_video`)
| Model | Best for | Key params | Roles / notes |
|---|---|---|---|
| `kling3_0` | **multi-shot, motion-transfer, cinematic, audio** | mode std/pro/4k, sound on/off | start+end_image; permissive on tasteful swimwear |
| `kling3_0_turbo` | fast/budget single-frame animate or t2v | resolution 720/1080 | start_image; ~10cr/5s |
| `kling2_6` | cinematic motion, advanced physics | sound | start_image |
| `veo3_1` | **top-tier ultra-real cinematic**, audio | quality basic/high/ultra, model preview/fast | ⚠️ Google **moderation rejects swimwear/“revealing” start-frames** |
| `veo3_1_lite` / `veo3` | fast/affordable batch / reliable | resolution, generate_audio | |
| `seedance_2_0` | **reference-driven, consistent identity, multi-SKU**, audio-ref | mode std/fast, resolution, bitrate, genre | image/start/end/video/audio roles; ~90cr std 1080p 10s |
| `seedance_1_5` | reliable motion, versatile | resolution | start+end |
| `minimax_hailuo` | natural physics, **facial emotion** | model variant, resolution | start+end (order matters) |
| `grok_video_v15` / `grok_video` | image-to-video, **physics + native audio** | resolution | most permissive |
| `wan2_6` / `wan2_7` | stylized/experimental / **synced audio + char-consistent** | quality | open-weight |
| `cinematic_studio_3_0` / `_video` / `_v2` | Higgsfield **cinema-grade**, genre/slow-mo control | genre, mode, slow_motion, sound | film look |
| `marketing_studio_video` | **product ads, TikTok/Reels**, hooks/settings/ad_reference | resolution, generate_audio, hook_id, setting_id, product_ids | run `show_marketing_studio` |
| `higgsfield_preset` | preset-routed viral templates | `preset_id` (from `presets_show`) | image-to-video |

## AUDIO (`generate_audio`)
| Model | Use | Params |
|---|---|---|
| `inworld_text_to_speech` | **narration/VO/dialogue** | `voice` (110+ voices). Langs: en,zh,nl,fr,de,it,ja,ko,pl,pt,es,ru,hi,he,ar. **No Armenian** → for hy use ElevenLabs externally |
| `sonilo_music` | **music bed / score** | duration (req) |
| `mirelo_text_to_audio` | **sound effects (SFX)** | duration (req) |

## 3D & GAMES
- `generate_3d` — image/text → 3D asset. · `autosprite` (above) — 2D sprite sheets. · game-creation bundle:
  `get_game_creation_instructions` / `get_game_creation_bundle_file` / `deploy_game` / `publish_game`.

## EDITING / UTILITY tools (not generation models — call directly)
- `motion_control` — apply camera/motion control to a clip.
- `animation_actions` — drive character actions/animation.
- `outpaint_image` — extend/expand image canvas. · `reframe` — re-aspect a video (e.g. 16:9→9:16).
- `remove_background` — image bg removal. · `upscale_image` / `upscale_video` — super-resolution.
- `personal_clipper_create/_jobs/_status` — long video → short clips (auto-clipping).
- `video_analysis_create/_status` — scene-by-scene analysis of a video/YouTube URL.
- `virality_predictor` — predict engagement/retention/hook strength of a video.
- `upscale_video` — final delivery upres.

## MARKETING STUDIO (campaign system) — `show_marketing_studio`
Manages `hook`, `setting`, `brand_kit`, `product`, `ad_reference`, `image_style`. Feeds `marketing_studio_*`
and `ms_image`/DTC. Use for product ads, UGC, virtual try-on, "recreate this ad" (ad_reference).

## CHARACTER CONSISTENCY (Soul ID)
- Train a reusable **Soul ID** from 5-20 photos via `show_characters(action='train')` → consistent recurring
  "hero" faces across `soul_2`/`soul_cinematic`. `show_characters` lists trained IDs. `show_reference_elements`
  for reusable elements.

## ACCOUNT / COST
- `balance` (credits+plan), `transactions`, `show_plans_and_credits`. **Always `get_cost:true` first.**
- Rough costs seen: nano_banana_pro ~0.5cr/img · kling3_0 turbo 5s ~10cr · kling3_0 pro 5s ~12.5cr ·
  veo3_1 fast 6s ~16.5cr · grok 6s ~27cr · seedance_2_0 std 1080p 10s ~90cr · inworld TTS a few cr.

## RUNTIME ROUTING (how generation actually flows in ZavodOM)
Generation is **agent-driven via the Higgsfield MCP tools** at runtime (generate_image/video/audio,
job_status, media_upload, etc.) — not a Python provider class. This capability map is the reference the
asset-director reads to pick the right model + params. The `lib/scoring.py` code-path defaults to **fal**
(FAL_KEY configured) when a non-interactive selection is needed; Higgsfield is the primary interactive
backend because of the PLUS credit balance. New backends register in `library/known_capabilities.json` (Scout).

## DECISION QUICK-PICK
- Real photo + add people/edit → `nano_banana_pro` (image role, real photo attached).
- Recurring character → train Soul ID → `soul_2`/`soul_cinematic`.
- Cinematic clip from a still, tasteful people → `kling3_0` (pro, sound). Avoid `veo3_1` for swimwear.
- Max realism, no moderation-risky content → `veo3_1` (high/ultra).
- Physics/splash/native audio → `grok_video_v15` or `kling`.
- Consistent multi-scene / product identity → `seedance_2_0` (multi reference).
- Product/UGC ad → `marketing_studio_video` / `ms_image` + brand_kit.
- Music → `sonilo_music`; SFX → `mirelo_text_to_audio`; VO → `inworld_text_to_speech` (non-Armenian).
- Re-aspect / upscale / bg-remove / outpaint → the editing tools above (don't regenerate).
- Long video → shorts → `personal_clipper`. Predict virality → `virality_predictor`.
