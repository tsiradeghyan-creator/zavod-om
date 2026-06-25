# Liquid Glass — design_styles

- id: liquid_glass
- essence: Apple's 2025 material — translucent glass that REFRACTS the content behind it, not a flat frosted blur.
- signature markers: real-time refraction, bright **edge lensing** (light bends at the rim), specular sheen, adaptive tint that samples what's behind, layered depth, generous corner radius, subtle motion-reactive parallax.
- AI / CSS keywords: "translucent refractive glass panel, edge lensing, specular highlight, layered depth, adaptive tint, soft caustics" · CSS: `backdrop-filter` + displacement/refraction map, not just `blur()`.
- when to use: premium UI-driven titles, tech/product overlays, bento cells, Lane-A (Apple-polish) projects.
- Maghakian application: title cards & lower-thirds over still photography — the glass tints to the show palette (#0D0D0D + gold) so it reads on-brand, never a generic iOS panel. Armenian display text stays overlay (glyph gate), refraction never distorts the letterforms.
- anti-pattern: plain `blur()` frosted box = cheap glassmorphism, NOT liquid glass; no refraction/lensing = the dead giveaway. Over-tint kills legibility.
- reference: Apple Liquid Glass (WWDC 2025).
