# Frontend Design Skill — SYNERGY AGENT

> *Owner:* Synergy Agent

---

## When This Skill Is Active

This skill is loaded when the task involves:
- Building websites, web pages, landing pages, portfolios
- Creating HTML/CSS/JS components or layouts
- Designing dashboards, admin panels, or web UIs
- Styling or beautifying any web interface
- Creating posters, banners, or visual artifacts in HTML
- React, Vue, or any frontend framework work
- Keywords: "website", "frontend", "html", "css", "landing page", "dashboard", "ui", "design", "poster", "component", "layout", "web app", "page", "beautify", "style"

---

## Design Philosophy

**NEVER create generic, cookie-cutter designs.** Every interface must feel intentionally designed for its specific context.

### Before Writing Code — Design Thinking (MANDATORY)

Identify these before touching any code:

**Purpose:** What problem does this interface solve? Who uses it?

**Aesthetic Direction — Pick ONE and commit:**
- Brutally Minimal — extreme whitespace, surgical typography
- Maximalist Chaos — layered, dense, controlled visual noise
- Retro-Futuristic — CRT scanlines, neon, monospace fonts
- Organic/Natural — earth tones, flowing shapes, hand-drawn feel
- Luxury/Refined — gold accents, serif fonts, dark backgrounds
- Playful/Toy-like — rounded corners, bright colors, bouncy animations
- Editorial/Magazine — grid-based, dramatic typography, whitespace
- Brutalist/Raw — system fonts, harsh borders, exposed structure
- Art Deco/Geometric — repeating patterns, metallic colors, symmetry
- Soft/Pastel — gentle gradients, rounded forms, warm palette
- Industrial/Utilitarian — monospace, dark mode, technical feel
- Glassmorphism — frosted glass, blur effects, layered transparency

**Differentiation:** What's the ONE thing someone will remember about this design?

---

## Implementation Guidelines

### Typography
- **NEVER use:** Arial, Inter, Roboto, system-ui, sans-serif defaults
- **DO use:** Distinctive Google Fonts that match the aesthetic
- **Examples by style:**
  - Luxury → Playfair Display + Cormorant Garamond
  - Tech → JetBrains Mono + Space Grotesk
  - Editorial → Fraunces + Source Serif Pro
  - Playful → Outfit + Nunito
  - Brutalist → IBM Plex Mono + Archivo Black
  - Art Deco → Poiret One + Josefin Sans
- **Always pair:** A display/heading font with a body font

### Color & Theme
- Use CSS custom properties (variables) for all colors
- Dominant color + sharp accent > evenly distributed palette
- **AVOID:** Purple gradients on white (cliché AI look)
- **DO:** Commit to a cohesive palette — 2-3 main colors max
- Dark themes: Use `#0d1117` to `#161b22` range, not pure black
- Light themes: Use warm whites `#faf9f6` to `#f5f0eb`, not pure white

### Motion & Animation
- Prioritize CSS-only animations for HTML projects
- Focus on HIGH-IMPACT moments:
  - Page load: staggered reveals with `animation-delay`
  - Scroll-triggered: `IntersectionObserver` for reveal effects
  - Hover states: subtle transforms, color shifts, scale changes
- **One orchestrated entrance > many scattered micro-interactions**
- Use `transform` and `opacity` for performance (GPU-accelerated)

### Layout & Composition
- Break the grid intentionally — overlap, asymmetry, diagonal flow
- Generous negative space OR controlled density (not in-between)
- Use CSS Grid for complex layouts, Flexbox for component alignment
- Consider viewport-relative units (`vh`, `vw`, `clamp()`)

### Visual Depth & Texture
- Add atmosphere: gradient meshes, noise textures, grain overlays
- Layered transparencies with `backdrop-filter: blur()`
- Dramatic shadows: `box-shadow` with multiple layers
- Decorative borders, custom dividers, geometric patterns

---

## Step-by-Step Process

### STEP 1: Understand Context
- Identify the purpose, audience, and tone
- Choose an aesthetic direction from the list above
- Plan the color palette and font pairing

### STEP 2: Create the Structure
- Write semantic HTML5 structure
- Use proper heading hierarchy (`h1` > `h2` > `h3`)
- Include all sections needed

### STEP 3: Apply Styling
- Set up CSS variables for colors, fonts, spacing
- Import Google Fonts
- Build the layout with CSS Grid/Flexbox
- Apply the chosen aesthetic with precision

### STEP 4: Add Motion
- Page entrance animations (staggered)
- Hover effects on interactive elements
- Scroll-triggered reveals
- Smooth transitions on state changes

### STEP 5: Polish & Verify
- Check responsiveness (mobile, tablet, desktop)
- Ensure text contrast meets accessibility standards
- Verify all animations are smooth (60fps)
- Test in browser using visit_url tool

---

## Code Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Page Title]</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=[Font1]&family=[Font2]&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #[value];
            --bg-secondary: #[value];
            --text-primary: #[value];
            --text-secondary: #[value];
            --accent: #[value];
            --accent-hover: #[value];
            --font-display: '[Font1]', serif;
            --font-body: '[Font2]', sans-serif;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: var(--font-body);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        /* ... rest of styles ... */
    </style>
</head>
<body>
    <!-- Semantic HTML structure -->
</body>
</html>
```

---

## Anti-Patterns (NEVER DO)

❌ Plain white background with blue links
❌ Generic card layouts with rounded corners and shadows
❌ Default browser form elements without styling
❌ Stock photo hero sections
❌ Purple-to-blue gradient backgrounds (AI cliché)
❌ Using more than 3 fonts
❌ Animations without purpose
❌ Placeholder content ("Lorem ipsum")
❌ Using inline styles instead of CSS variables
❌ Ignoring mobile responsiveness

---

## Delivery

Always save the final HTML file to `output/` directory.
Verify the design by opening it in the browser.
Report the file path and a summary of design choices made.

---

## Remember

- **Bold choices > safe choices** — commit to a direction
- **Cohesion > variety** — one strong theme beats many weak ones
- **Details matter** — the 5% of polish makes 95% of the impression
- **Every pixel is intentional** — no default values left unstyled
- **Show, don't tell** — the design should speak for itself
