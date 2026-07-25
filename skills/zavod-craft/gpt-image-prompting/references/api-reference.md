# API Reference — OpenAI GPT Image Models

Everything needed to emit runnable code: the one-time setup helper, the two
call shapes, the parameters, the model table, and the `gpt-image-2` size
constraints.

## Setup (run once)

Creates the client, ensures the input/output folders exist, and defines a
`save_image` helper that decodes the first returned base64 image to disk.
Adjust the folder paths to match the project.

```python
import os
import base64
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment

os.makedirs("images/input_images", exist_ok=True)
os.makedirs("images/output_images", exist_ok=True)

def save_image(result, filename: str) -> None:
    """Save the first returned image into images/output_images/."""
    image_base64 = result.data[0].b64_json
    out_path = os.path.join("images/output_images", filename)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(image_base64))
```

## Generate (text → image)

```python
result = client.images.generate(
    model="gpt-image-2",
    prompt=prompt,
    size="1024x1536",
    quality="medium",   # "low" | "medium" | "high"
)
save_image(result, "output.png")
```

## Edit (text + image → image)

Pass one or more open file handles in `image=[...]`. When multiple inputs are
given, reference them in the prompt by index/description (see the multi-image
fundamentals in SKILL.md).

```python
result = client.images.edit(
    model="gpt-image-2",
    image=[
        open("images/input_images/base.png", "rb"),
        open("images/input_images/reference.png", "rb"),
    ],
    prompt=prompt,
    size="1024x1536",
    quality="medium",
    # background="opaque",     # force an opaque background (product mockups)
    # input_fidelity="high",   # older models only; ignored by gpt-image-2
)
save_image(result, "edited.png")
```

## Generating multiple variations (`n`)

Ask for several candidates in one call (e.g. logo options) and save each.

```python
result = client.images.generate(
    model="gpt-image-2",
    prompt=prompt,
    size="1024x1536",
    quality="medium",
    n=4,
)
for i, item in enumerate(result.data, start=1):
    with open(f"images/output_images/logo_{i}.png", "wb") as f:
        f.write(base64.b64decode(item.b64_json))
```

## Parameters

| Parameter | Values | Notes |
| --- | --- | --- |
| `model` | `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` | Default to `gpt-image-2`. |
| `quality` | `low`, `medium`, `high` | `low` = fast/cheap; `medium`/`high` for text, portraits, dense detail, high-res. |
| `size` | see constraints | Portrait/landscape/square + arbitrary sizes on `gpt-image-2`. |
| `input_fidelity` | `low`, `high` | **Edits only, older models only.** Helps preserve likeness during large edits. Not used on `gpt-image-2` (already high fidelity). |
| `background` | `opaque`, `transparent`, `auto` | Force opaque for product mockups; do a downstream cutout for a final transparent asset. |
| `n` | integer | Number of variations per call. |

## Model comparison (as of April 2026)

| Model | `quality` | `input_fidelity` | Resolutions | Recommended use |
| --- | --- | --- | --- | --- |
| `gpt-image-2` | low/medium/high | Disabled (already high fidelity) | Any size meeting the constraints below | **Default for new builds.** Highest-quality generation & editing, text-heavy images, photorealism, compositing, identity-sensitive edits, flexible sizing. |
| `gpt-image-1.5` | low/medium/high | low/high | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | Keep for validated workflows during migration; prefer `gpt-image-2` for new work. |
| `gpt-image-1` | low/medium/high | low/high | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | Legacy compatibility only. |
| `gpt-image-1-mini` | low/medium/high | low/high | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | Cheapest / highest throughput: big batches, rapid ideation, previews, drafts. |

## `gpt-image-2` size constraints

Any `size` is valid when **all** of these hold:

- Max edge length **< 3840px**
- Both edges are a **multiple of 16**
- Long:short edge ratio **≤ 3:1**
- Total pixels **≤ 8,294,400** and **≥ 655,360**

Above `2560x1440` (2K, 3,686,400 px) treat results as **experimental** — more
variable. For 4K/UHD targets, round down to a valid size such as `3824x2144`.

### Handy sizes

| Label | Resolution |
| --- | --- |
| Square (general default) | `1024x1024` |
| HD portrait | `1024x1536` |
| HD landscape | `1536x1024` |
| Deck slide (landscape) | `1536x864` |
| 2K / QHD (reliability ceiling) | `2560x1440` |
