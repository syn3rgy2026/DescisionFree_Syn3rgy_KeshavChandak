# PowerPoint Skill — Industry-Grade Presentations

> **Owner:** Person 3

## Description

This skill enables the agent to create **consulting-grade, visually rich**
PowerPoint presentations with charts, diagrams, images, and professional
layouts. Every deck should tell a story with visuals — not just text.

**IMPORTANT:** The following tools are REGISTERED and AVAILABLE in the runtime.
They are real, callable functions — DO NOT say they are unavailable. Call them directly.

## Available Tools (all registered, all callable)

### Primary Tool
- **`create_presentation(filename, title, slides_data, theme, subtitle, author)`**
  Creates a complete multi-slide deck with professional design. Supports: bullet,
  section, text, comparison, image, chart, diagram slide types.

### Visual Generation Tools
- **`generate_chart_image(data, chart_type, filename, title, xlabel, ylabel, theme)`**
  Generate bar/line/pie/horizontal_bar charts with matplotlib. Returns image path.
- **`generate_diagram_image(diagram_type, content, filename, theme)`**
  Generate flowcharts, architecture diagrams, and pipelines. Returns image path.
- **`fetch_relevant_image(query, filename)`**
  Fetch stock photos from the web. Returns image path.

### Design Enhancement Tools
- **`enhance_slide_design(filepath, theme)`**
  Apply professional design elements to an existing presentation.
- **`insert_visual_element(filepath, image_path, slide_index, layout_type)`**
  Insert images/charts/diagrams at smart positions on existing slides.

### Helper Tools
- **`create_quick_ppt(filename, title, bullet_points, theme)`**
  Fast 3-slide deck (title, bullets, thank-you). Use for simple requests.
- **`add_slide_to_ppt(filepath, slide_type, heading, content)`**
  Append a slide to an existing .pptx file.
- **`list_ppt_themes()`**
  Show available colour themes.

## Trigger Conditions

Use this skill when the user says any of:
- "ppt", "pptx", "powerpoint", "presentation", "slides", "slide", "deck"
- "make a deck", "build slides", "create a presentation"

---

## Instructions — FOLLOW THIS EXACT ORDER

### Step 1 — Think in STORY FORMAT

Every presentation should follow a narrative arc:
1. **Problem / Context** — Why does this matter?
2. **Insight / Analysis** — What does the data show?
3. **Solution / Approach** — What's the plan?
4. **Impact / Results** — What will change?

**Use strong slide titles:**
- BAD: "Introduction"
- GOOD: "Why This Problem Matters Now"
- BAD: "Data"
- GOOD: "Revenue Grew 3x in 12 Months"
- BAD: "Conclusion"
- GOOD: "The Path Forward: A $2M Opportunity"

### Step 2 — Decide What Visuals to Use

For EVERY slide, ask yourself: **can this be visual?**

| Content Type | Best Visual | Tool to Use |
|---|---|---|
| Numbers / metrics / comparisons | Chart (bar, line, pie) | `generate_chart_image()` or `type='chart'` |
| Processes / workflows / steps | Diagram (flowchart, pipeline) | `generate_diagram_image()` or `type='diagram'` |
| System design / architecture | Architecture diagram | `generate_diagram_image(diagram_type='architecture')` |
| Concepts / abstract topics | Stock image | `fetch_relevant_image()` then `type='image'` |
| Before vs After / two options | Comparison slide | `type='comparison'` |
| Key takeaways / summary points | Bullet slide | `type='bullet'` (max 6 bullets) |
| Long explanation | Text slide | `type='text'` (use sparingly) |

**Rules:**
- NEVER create a presentation with ONLY bullet slides
- ALWAYS include at least 1 visual (chart, diagram, or image) in decks with 5+ slides
- Avoid text-heavy slides — max 6 bullets, each under 12 words

### Step 3 — Build slides_data

Build a Python list of dicts. Each dict MUST have a `type` key.

#### Slide Types & Examples:

**Bullet slide** (max 6 concise bullets):
```python
{"type": "bullet", "heading": "Key Growth Drivers", "bullets": ["Revenue up 25% YoY", "10K+ customers acquired", "NPS score reached 72"]}
```

**Section divider** (use between major sections):
```python
{"type": "section", "heading": "Deep Dive: Market Analysis", "subtitle": "Understanding the competitive landscape"}
```

**Text slide** (for executive summaries):
```python
{"type": "text", "heading": "Executive Summary", "body": "Our analysis reveals a significant opportunity..."}
```

**Comparison slide** (two columns):
```python
{"type": "comparison", "heading": "Current vs Proposed", "left_title": "Today", "left_items": ["Manual process", "3-day turnaround"], "right_title": "Proposed", "right_items": ["Fully automated", "Real-time"]}
```

**Chart slide** (auto-generates chart image):
```python
{"type": "chart", "heading": "Revenue by Quarter", "chart_type": "bar", "chart_data": {"labels": ["Q1","Q2","Q3","Q4"], "values": [2100, 2600, 3200, 4100]}}
```

Multi-series chart:
```python
{"type": "chart", "heading": "Revenue vs Cost", "chart_type": "line", "chart_data": {"labels": ["Q1","Q2","Q3","Q4"], "series": [{"name": "Revenue", "values": [2100,2600,3200,4100]}, {"name": "Cost", "values": [1500,1700,1900,2100]}]}}
```

Pie chart:
```python
{"type": "chart", "heading": "Market Share", "chart_type": "pie", "chart_data": {"labels": ["Us","Competitor A","Competitor B","Others"], "values": [35,25,20,20]}}
```

**Diagram slide** (auto-generates diagram image):

Flowchart:
```python
{"type": "diagram", "heading": "Process Flow", "diagram_type": "flowchart", "diagram_content": {"steps": ["User Submits", "Validate Data", "Process Payment", "Send Confirmation"]}}
```

Architecture:
```python
{"type": "diagram", "heading": "System Architecture", "diagram_type": "architecture", "diagram_content": {"layers": [{"name": "Frontend", "items": ["React", "Next.js"]}, {"name": "Backend", "items": ["FastAPI", "Redis"]}, {"name": "Database", "items": ["PostgreSQL", "S3"]}]}}
```

Pipeline:
```python
{"type": "diagram", "heading": "Data Pipeline", "diagram_type": "pipeline", "diagram_content": {"stages": ["Ingest", "Clean", "Transform", "Model", "Deploy"]}}
```

**Image slide** (for fetched images):
```python
# First fetch the image
img_path = fetch_relevant_image(query="data analytics dashboard", filename="output/analytics.jpg")
# Then use it
{"type": "image", "heading": "Our Analytics Platform", "image_path": img_path, "caption": "Real-time business intelligence"}
```

### Step 4 — Choose a Theme

| Theme | Best For | Look |
|---|---|---|
| `default` | General purpose | White, blue accents |
| `dark` | Tech / modern | Dark background, cyan accents |
| `corporate` | Business / formal | Grey, navy + red |
| `creative` | Marketing / design | White, purple/pink/orange |
| `consulting` | Board / strategy | White, navy + orange (McKinsey-style) |

### Step 5 — Call the Tool

```python
slides_data = [
    {"type": "section", "heading": "Market Opportunity", "subtitle": "A $5B untapped market"},
    {"type": "chart", "heading": "Revenue Growth Trajectory", "chart_type": "bar",
     "chart_data": {"labels": ["2023","2024","2025","2026"], "values": [1.2, 2.4, 4.1, 6.8]}},
    {"type": "bullet", "heading": "Our Strategic Advantages", "bullets": [
        "First-mover in AI-powered automation",
        "Patent-pending technology",
        "95% customer retention rate",
        "3x faster than competitors",
    ]},
    {"type": "diagram", "heading": "Implementation Roadmap", "diagram_type": "pipeline",
     "diagram_content": {"stages": ["Discovery", "Design", "Build", "Launch", "Scale"]}},
    {"type": "comparison", "heading": "Before vs After Implementation",
     "left_title": "Before", "left_items": ["Manual data entry", "3-day processing", "60% accuracy"],
     "right_title": "After", "right_items": ["Full automation", "Real-time", "95% accuracy"]},
]

result = create_presentation(
    filename="output/strategy_deck.pptx",
    title="Strategic Growth Initiative",
    slides_data=slides_data,
    theme="consulting",
    subtitle="Board Presentation — Q2 2026",
    author="Strategy Team"
)
print(result)
```

### Step 6 — Visual Quality Assurance & Iteration (CRITICAL)

After creating the file, you **MUST** verify its layout and present it to the user:
1. **Self-Check:** Call `analyze_ppt_layout(filepath)`. If it reports overlaps or visual issues (e.g., elements overlapping, text too dense), use `create_presentation` again with adjusted `slides_data` (e.g., shorter text, different layout) to fix it.
2. **Generate Screenshots:** Call `generate_ppt_preview(filepath)`. This creates a layout thumbnail (PNG) of the presentation.
3. **Get User Feedback:** Call `ask_human_confirmation` from the runtime environment. 
   Set `action="Review PPT Preview"`, `reason=f"Please review the screenshot at {png_path}."`, and `risk_level="LOW"`.
4. **Re-iterate:** If the user is NOT satisfied and replies with changes (e.g., "make the theme dark", "shorten the text"), update your `slides_data` and repeat the creation and review steps.

### Step 7 — Report the Result

After the user approves the layout, tell them:
- The file path where the .pptx was saved
- How many slides were created
- Which theme was used
- What visuals were generated (charts, diagrams)

---

## CRITICAL RULES

1. **ALWAYS save to the output/ directory** — e.g. `output/my_deck.pptx`
2. **NEVER create empty presentations.** Every deck must have at least one content slide.
3. **Keep bullet points concise** — max 6 bullets per slide, each under 12 words.
4. **Use section slides** to break up decks with more than 5 content slides.
5. **Pick a theme that matches the tone** — use `dark` for tech, `consulting` for business.
6. **ALWAYS include visuals** — at least 1 chart or diagram in decks with 5+ slides.
7. **NEVER create text-only presentations** — always enhance with visuals if applicable.
8. **NEVER say "I can't create PowerPoint files"** — the PPT tools ARE REGISTERED.
9. **NEVER try to import the tools** — they are already callable functions.
10. **Use storytelling structure** — Problem → Insight → Solution → Impact.
11. **If the user wants to add slides later**, use `add_slide_to_ppt`.
12. **Generate charts/diagrams AUTOMATICALLY** when `type='chart'` or `type='diagram'` is used — the tool handles image creation internally.

## Output Format

Always include in your final answer:
- File path to the .pptx
- Number of slides created
- Theme used
- List of visuals generated (charts, diagrams, images)
- Brief summary of the slide structure
