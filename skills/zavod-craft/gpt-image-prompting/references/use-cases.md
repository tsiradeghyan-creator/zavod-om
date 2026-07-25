# Use-Case Prompt Templates

Copy-ready prompts and the reasoning behind each, grouped into **Generate**
(text → image) and **Edit** (text + image → image). Read the section matching
the task and adapt the wording. All examples target `gpt-image-2`; see
`api-reference.md` for the call shape and `save_image` helper.

---

## Generate (text → image)

### Infographics
Explain structured information for a specific audience. For dense layouts or
heavy in-image text, use `quality="high"`.

```
Create a detailed infographic of the functioning and flow of an automatic
coffee machine like a Jura. From bean basket, to grinding, to scale, water
tank, boiler, etc. Show the flow technically and visually.
```

### Photorealism that feels natural
Prompt as if a real photo is being captured in the moment. Use photography
language and ask for real texture; avoid words implying studio polish. Use
`quality="high"` when detail matters.

```
Create a photorealistic candid photograph of an elderly sailor on a small
fishing boat. Weathered skin with visible wrinkles, pores, and sun texture; a
few faded sailor tattoos. He calmly adjusts a net while his dog sits on the
deck. Shot like 35mm film, medium close-up at eye level, 50mm lens. Soft
coastal daylight, shallow depth of field, subtle film grain, natural color.
Honest and unposed — real skin texture, worn materials. No glamorization, no
heavy retouching.
```

### World knowledge
The model pairs reasoning with world knowledge — give it time/place and let it
infer the context.

```
Create a realistic outdoor crowd scene in Bethel, New York on August 16, 1969.
Photorealistic, period-accurate clothing, staging, and environment.
```

### Logo generation
Clear brand constraints + simplicity. Use `n` for variations.

```
Create an original, non-infringing logo for "Field & Flour", a local bakery.
Warm, simple, timeless. Clean vector-like shapes, strong silhouette, balanced
negative space. Favor simplicity so it reads at small and large sizes. Flat
design, minimal strokes, no gradients unless essential. Plain background,
single centered logo with generous padding. No watermark.
```

### Ads
Write a creative brief, not a technical spec: brand, audience, culture,
concept, composition, exact copy. Quote taglines that must appear.

```
A cool, in-culture fashion ad for "Thread", a hip young streetwear brand. A
group of friends hanging out, tagline "Yours to Create." Polished campaign
image for a youth streetwear audience: stylish, contemporary, energetic.
Clean composition, strong color direction, natural poses, premium fashion
photography cues. Render the tagline exactly once, clearly and legibly. No
extra text, no watermarks, no unrelated logos.
```

### Story-to-comic strip
Define the narrative as clear visual beats, one per panel.

```
Create a short vertical comic-style reel with 4 equal-sized panels.
Panel 1: The owner leaves through the front door; the pet is framed in the
window behind, small against the glass, eyes wide.
Panel 2: The door clicks shut; the pet turns toward the empty house, eyes
sharp with possibility.
Panel 3: The house transformed — the pet sprawls across the couch like it owns
the place, sunlight cutting across the room.
Panel 4: The door opens; the pet sits perfectly by the entrance, composed, as
if nothing happened.
```

### UI mockups
Describe the product as if it already exists. Focus on layout, hierarchy,
spacing, real interface elements — avoid concept-art language.

```
Create a realistic mobile app UI mockup for a local farmers market. Simple
header, a short list of vendors with small photos and categories, a "Today's
specials" section, and location/hours. Practical and easy to use. White
background, subtle natural accent colors, clear typography, minimal
decoration. Place the UI in an iPhone frame.
```

### Scientific / educational visuals
Prompt like an instructional-design brief: audience, objective, format,
required labels, constraints. List required components and what to exclude.
Use `quality="high"` for dense labels.

```
Create a simple biology diagram titled "Cellular Respiration at a Glance" for
high-school students. Show how glucose becomes energy: glycolysis, the Krebs
cycle, the electron transport chain. Use arrows to connect steps; label
glucose, pyruvate, ATP, NADH, FADH2, CO2, O2, H2O. Clean classroom handout —
white background, simple icons, clear labels, easy-to-read text. Avoid tiny
text or extra decoration.
```

### Slides, diagrams, charts
Write an artifact spec: name the deliverable, define canvas + hierarchy, give
real text/data, describe the visual language. Landscape size + `quality="high"`
for small text/legends/axes.

```
Create one pitch-deck slide titled "Market Opportunity" that feels like a real
Series A slide. Clean white background, modern sans-serif (Inter), crisp
minimal layout. Include: a TAM/SAM/SOM concentric-circle diagram in muted
blues/grays; numbers TAM $42B, SAM $8.7B, SOM $340M; a bar chart of market
growth 2021–2026 with a subtle upward trend; footnotes "AGI Research, 2024"
and "Internal analysis"; a logo placeholder bottom-right. Highly readable,
clear data hierarchy, polished spacing. Avoid clip art, stock photos,
gradients, shadows, or decorative clutter.
```
(size `1536x864`)

### Holiday card / product-style mock
Emphasize tactile realism so it reads as a photographed physical product.

```
Create a Christmas holiday card illustration. Scene: a cozy scene with an old
teddy bear in a keepsake box, slightly worn fur, near a window with falling
snow — the child has grown up but the memories remain. Mood: warm, nostalgic,
gentle. Style: premium holiday-card photography, soft cinematic lighting,
realistic textures, shallow depth of field, tasteful bokeh. Constraints:
original artwork only, no trademarks/watermarks/logos. Include ONLY this text
(verbatim): "Merry Christmas — some memories never fade."
```

### Merch concept (collectible / packaging)
Premium product-photography cues; keep designs original.

```
Create a collectible action figure of a vintage-style toy propeller airplane
(rounded wings, front propeller, slightly worn paint) in blister packaging. A
nostalgic holiday collectible evoking childhood wonder. Premium toy
photography, realistic plastic/painted-metal textures, studio lighting,
shallow depth of field, sharp label printing. Original design only, no
trademarks/watermarks/logos. Include ONLY this packaging text (verbatim):
"Christmas Memories Edition".
```

### Children's-book character consistency (multi-step)
Step 1 — establish a reusable **character anchor** (lock appearance,
proportions, outfit, tone, plain background). Step 2 — *edit* that anchor image
to advance the story, restating what must stay identical.

```
Step 1 (generate): Create a children's-book illustration introducing a main
character: a young storybook forest hero in a green hooded tunic, brown boots,
belt pouch; kind expression, carries a small wooden bow used only for helping.
Hand-painted watercolor look, soft outlines, warm earthy colors, picture-book
proportions. Original character, no text, no watermarks, plain forest
background.

Step 2 (edit the step-1 image): Continue the story with the SAME character.
Scene: he gently helps a frightened squirrel from a fallen tree after a storm,
kneeling beside it. Keep the same tunic, facial features, proportions, and
palette. Same watercolor style, snowy forest, warm mood. Do not redesign the
character. No text, no watermarks.
```

---

## Edit (text + image → image)

The recurring principle: **separate what changes from what must be preserved,
and repeat the preserve-list every iteration** so the image doesn't drift.

### Style transfer
Keep the reference's visual language; change the subject.

```
Use the same style from the input image and generate a man riding a
motorcycle on a white background.
```

### Virtual clothing try-on
Lock the person; change only garments. Require realistic fit and matched
lighting.

```
Dress the woman using the provided clothing images. Do not change her face,
features, skin tone, body shape, pose, or identity. Preserve her exact
likeness, expression, hairstyle, and proportions. Replace only the clothing,
fitting garments naturally to her pose and body with realistic fabric
behavior. Match lighting, shadows, and color temperature so the outfit looks
photorealistically worn, not pasted on. Do not change background, camera
angle, framing, or quality; add no accessories, text, logos, or watermarks.
```
(pass the person as image 1, then each garment)

### Drawing → photorealistic render
Preserve layout/perspective; add plausible materials + lighting.

```
Turn this drawing into a photorealistic image. Preserve the exact layout,
proportions, and perspective. Choose realistic materials and lighting
consistent with the sketch intent. Do not add new elements or text.
```

### Product mockup (clean background + label integrity)
Keep the background opaque; preserve geometry and label legibility. Use
`background="opaque"`.

```
Extract the product from the input image and place it on a plain white opaque
background. Centered product, crisp silhouette, no halos/fringing. Preserve
product geometry and label legibility exactly. Add only light polishing and a
subtle realistic contact shadow. Do not restyle the product.
```

### Marketing creative with real in-image text
Quote the copy, demand verbatim rendering, describe placement + font.

```
Create a realistic billboard mockup of the shampoo on a highway at sunset.
Billboard text (EXACT, verbatim, no extra characters): "Fresh and clean".
Typography: bold sans-serif, high contrast, centered, clean kerning. Text
appears once and is perfectly legible. No watermarks, no logos.
```

### Lighting / weather transformation
Change only environmental conditions; preserve composition, geometry, camera
angle, and object placement. `input_fidelity="high"` helps on older models.

```
Make it look like a winter evening with snowfall.
```

### Object removal
Surgical removal; keep everything else identical.

```
Remove the flower from the man's hand. Do not change anything else.
```

### Insert a person into a scene
Preserve identity; anchor a grounded photographic look (avoid cinematic
grading). `input_fidelity="high"` helps likeness during large edits.

```
Generate a highly realistic action scene where this person runs away from a
large brown bear attacking a campsite. Look like a real photograph, not a
cinematic movie poster. She is centered but looking away from the camera, in
outdoorsy camping attire, dirt on her face, torn clothing, clearly afraid but
focused on escaping. Campsite in Yosemite at dusk, natural lighting, realistic
colors. Grounded and unstyled. Avoid cinematic lighting, dramatic color
grading, or stylized composition.
```

### Multi-image compositing
Say what to transplant, where it goes, and what stays unchanged; match
lighting/perspective/scale/shadows.

```
Place the dog from the second image into the setting of image 1, right next to
the woman. Use the same lighting, composition, and background. Do not change
anything else.
```

### Interior design swap (precision edit)
Swap a single object; preserve camera angle, lighting, shadows, surroundings.

```
In this room photo, replace ONLY the white chairs with chairs made of wood.
Preserve camera angle, room lighting, floor shadows, and surrounding objects.
Keep all other aspects unchanged. Photorealistic contact shadows and texture.
```

### Translation in-image
Localize an existing design without rebuilding it: translate the text only,
verbatim, preserving typography, placement, spacing, hierarchy, and imagery.

```
Translate the text in the infographic to Spanish. Do not change any other
aspect of the image.
```
