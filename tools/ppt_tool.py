"""
ppt_tool.py
-----------
Comprehensive PowerPoint creation tool for Synergy Agent.

Capabilities:
  - Create multi-slide presentations with various layouts
  - Apply professional themes (colors, fonts, backgrounds)
  - Add title slides, bullet slides, section headers, image slides
  - Support comparison / two-column layouts
  - Build entire presentations from structured JSON-like data

All outputs are saved to the working directory or a user-specified path.
Requires: python-pptx (already in requirements.txt)

NOTE: All pptx imports are LAZY (inside functions) to avoid smolagents
sandbox validation errors.
"""

import os
import logging
from smolagents import tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ppt_tool")


# ── Helpers ───────────────────────────────────────────────────────────

def _get_safe_path(filename: str) -> str:
    """Resolve an absolute path, creating parent directories as needed."""
    full_path = os.path.abspath(filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path


# ── Pre-defined colour themes (stored as raw RGB tuples) ─────────────

THEMES = {
    "default": {
        "title_color": (0x1A, 0x1A, 0x2E),
        "subtitle_color": (0x6C, 0x75, 0x7D),
        "heading_color": (0x0D, 0x6E, 0xFD),
        "body_color": (0x33, 0x33, 0x33),
        "accent_color": (0x0D, 0x6E, 0xFD),
        "bg_color": (0xFF, 0xFF, 0xFF),
        "title_font": "Calibri",
        "body_font": "Calibri",
    },
    "dark": {
        "title_color": (0xFF, 0xFF, 0xFF),
        "subtitle_color": (0xBB, 0xBB, 0xBB),
        "heading_color": (0x00, 0xD4, 0xFF),
        "body_color": (0xDD, 0xDD, 0xDD),
        "accent_color": (0x00, 0xD4, 0xFF),
        "bg_color": (0x1E, 0x1E, 0x2E),
        "title_font": "Calibri",
        "body_font": "Calibri",
    },
    "corporate": {
        "title_color": (0x00, 0x2B, 0x5C),
        "subtitle_color": (0x5A, 0x5A, 0x5A),
        "heading_color": (0x00, 0x2B, 0x5C),
        "body_color": (0x33, 0x33, 0x33),
        "accent_color": (0xC8, 0x10, 0x2E),
        "bg_color": (0xF8, 0xF9, 0xFA),
        "title_font": "Arial",
        "body_font": "Arial",
    },
    "creative": {
        "title_color": (0x6C, 0x2E, 0xB9),
        "subtitle_color": (0x99, 0x99, 0x99),
        "heading_color": (0xE9, 0x1E, 0x63),
        "body_color": (0x33, 0x33, 0x33),
        "accent_color": (0xFF, 0x98, 0x00),
        "bg_color": (0xFF, 0xFF, 0xFF),
        "title_font": "Georgia",
        "body_font": "Calibri",
    },
}


def _get_theme(name: str) -> dict:
    """Return a theme dict by name, falling back to 'default'."""
    return THEMES.get(name.lower(), THEMES["default"])


def _rgb(tup):
    """Convert an (r, g, b) tuple to a pptx RGBColor object."""
    from pptx.dml.color import RGBColor
    return RGBColor(tup[0], tup[1], tup[2])


def _set_slide_bg(slide, color_tuple):
    """Apply a solid background colour to a slide."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(color_tuple)


def _add_text_box(slide, left, top, width, height, text, font_name, font_size,
                  font_color_tuple, bold=False, alignment=None):
    """Add a styled text box to a slide."""
    from pptx.util import Pt
    from pptx.enum.text import PP_ALIGN

    if alignment is None:
        alignment = PP_ALIGN.LEFT

    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = font_name
    p.font.size = Pt(font_size)
    p.font.color.rgb = _rgb(font_color_tuple)
    p.font.bold = bold
    p.alignment = alignment
    return txBox


def _add_accent_bar(slide, color_tuple, left=None, top=None, width=None, height=None):
    """Add a thin coloured accent bar (rectangle) to a slide."""
    from pptx.util import Inches
    from pptx.enum.shapes import MSO_SHAPE

    if left is None:
        left = Inches(0)
    if top is None:
        top = Inches(0)
    if width is None:
        width = Inches(0.15)
    if height is None:
        height = Inches(7.5)

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(color_tuple)
    shape.line.fill.background()
    return shape


# ── Slide builders (internal) ────────────────────────────────────────

def _build_bullet_slide(prs, data: dict, t: dict):
    from pptx.util import Inches, Pt

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["bg_color"])
    _add_accent_bar(slide, t["accent_color"])

    heading = data.get("heading", "")
    bullets = data.get("bullets", [])

    _add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(1),
                  heading, t["title_font"], 28, t["heading_color"], bold=True)

    txBox = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(10.5), Inches(5))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = bullet
        p.font.name = t["body_font"]
        p.font.size = Pt(18)
        p.font.color.rgb = _rgb(t["body_color"])
        p.space_after = Pt(10)
        p.level = 0


def _build_section_slide(prs, data: dict, t: dict):
    from pptx.util import Inches
    from pptx.enum.text import PP_ALIGN

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["accent_color"])

    heading = data.get("heading", "")
    sub = data.get("subtitle", "")

    _add_text_box(slide, Inches(1), Inches(2.5), Inches(11), Inches(1.5),
                  heading, t["title_font"], 36, (0xFF, 0xFF, 0xFF),
                  bold=True, alignment=PP_ALIGN.CENTER)
    if sub:
        _add_text_box(slide, Inches(1), Inches(4.2), Inches(11), Inches(0.8),
                      sub, t["body_font"], 18, (0xEE, 0xEE, 0xEE),
                      alignment=PP_ALIGN.CENTER)


def _build_text_slide(prs, data: dict, t: dict):
    from pptx.util import Inches

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["bg_color"])
    _add_accent_bar(slide, t["accent_color"])

    heading = data.get("heading", "")
    body = data.get("body", "")

    _add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(1),
                  heading, t["title_font"], 28, t["heading_color"], bold=True)
    _add_text_box(slide, Inches(1), Inches(1.8), Inches(10.5), Inches(5),
                  body, t["body_font"], 16, t["body_color"])


def _build_comparison_slide(prs, data: dict, t: dict):
    from pptx.util import Inches, Pt
    from pptx.enum.shapes import MSO_SHAPE

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["bg_color"])
    _add_accent_bar(slide, t["accent_color"])

    heading = data.get("heading", "")
    _add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(1),
                  heading, t["title_font"], 28, t["heading_color"], bold=True)

    # Left column
    left_title = data.get("left_title", "Option A")
    left_items = data.get("left_items", [])
    _add_text_box(slide, Inches(0.8), Inches(1.8), Inches(5), Inches(0.6),
                  left_title, t["title_font"], 20, t["accent_color"], bold=True)

    txBox = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(5), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(left_items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.name = t["body_font"]
        p.font.size = Pt(16)
        p.font.color.rgb = _rgb(t["body_color"])
        p.space_after = Pt(6)

    # Divider line
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(6.4), Inches(1.8), Inches(0.05), Inches(5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(t["accent_color"])
    shape.line.fill.background()

    # Right column
    right_title = data.get("right_title", "Option B")
    right_items = data.get("right_items", [])
    _add_text_box(slide, Inches(6.8), Inches(1.8), Inches(5), Inches(0.6),
                  right_title, t["title_font"], 20, t["accent_color"], bold=True)

    txBox = slide.shapes.add_textbox(Inches(7), Inches(2.5), Inches(5), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(right_items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.name = t["body_font"]
        p.font.size = Pt(16)
        p.font.color.rgb = _rgb(t["body_color"])
        p.space_after = Pt(6)


def _build_image_slide(prs, data: dict, t: dict):
    from pptx.util import Inches
    from pptx.enum.text import PP_ALIGN

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["bg_color"])
    _add_accent_bar(slide, t["accent_color"])

    heading = data.get("heading", "")
    image_path = data.get("image_path", "")
    caption = data.get("caption", "")

    _add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(1),
                  heading, t["title_font"], 28, t["heading_color"], bold=True)

    if image_path and os.path.exists(image_path):
        try:
            slide.shapes.add_picture(image_path, Inches(2), Inches(1.8),
                                     Inches(9), Inches(4.8))
        except Exception as e:
            _add_text_box(slide, Inches(2), Inches(3), Inches(9), Inches(1),
                          f"[Image could not be loaded: {e}]",
                          t["body_font"], 14, t["subtitle_color"],
                          alignment=PP_ALIGN.CENTER)
    else:
        _add_text_box(slide, Inches(2), Inches(3), Inches(9), Inches(1),
                      f"[Image not found: {image_path}]",
                      t["body_font"], 14, t["subtitle_color"],
                      alignment=PP_ALIGN.CENTER)

    if caption:
        _add_text_box(slide, Inches(1), Inches(6.8), Inches(11), Inches(0.5),
                      caption, t["body_font"], 12, t["subtitle_color"],
                      alignment=PP_ALIGN.CENTER)


# ── Public @tool functions ────────────────────────────────────────────

@tool
def create_presentation(
    filename: str,
    title: str,
    slides_data: list,
    theme: str = "default",
    subtitle: str = "Generated by Synergy Agent",
    author: str = "Synergy Agent",
) -> str:
    """Create a professional multi-slide PowerPoint presentation (.pptx).

    This is the primary tool for building presentations. Pass structured
    slide data and the tool handles layout, styling, and saving.

    Args:
        filename: Output filename (e.g. 'output/report.pptx'). Include .pptx extension.
        title: Main title shown on the first (cover) slide.
        slides_data: A list of dicts, one per slide. Each dict MUST have a
                     'type' key. Supported types and their keys:
                     type='bullet' with heading (str) and bullets (list of str).
                     type='section' with heading (str) and subtitle (str, optional).
                     type='text' with heading (str) and body (str).
                     type='comparison' with heading (str), left_title (str),
                       left_items (list), right_title (str), right_items (list).
                     type='image' with heading (str), image_path (str),
                       caption (str, optional).
        theme: Colour theme. One of 'default', 'dark', 'corporate', 'creative'.
        subtitle: Subtitle on the title slide.
        author: Author name placed on the title slide.

    Returns:
        Confirmation message with file path and slide count.
    """
    try:
        from pptx import Presentation as PptxPresentation
        from pptx.util import Inches
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        return "Error: python-pptx is required. Install with: pip install python-pptx"

    t = _get_theme(theme)
    full_path = _get_safe_path(filename)
    prs = PptxPresentation()

    # Set default slide dimensions (widescreen 16:9)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ── Title slide ───────────────────────────────────────────────────
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    _set_slide_bg(slide, t["bg_color"])
    _add_accent_bar(slide, t["accent_color"])

    _add_text_box(slide, Inches(1), Inches(1.8), Inches(10), Inches(1.5),
                  title, t["title_font"], 40, t["title_color"], bold=True,
                  alignment=PP_ALIGN.LEFT)
    _add_text_box(slide, Inches(1), Inches(3.5), Inches(9), Inches(0.8),
                  subtitle, t["body_font"], 20, t["subtitle_color"],
                  alignment=PP_ALIGN.LEFT)
    _add_text_box(slide, Inches(1), Inches(5.5), Inches(9), Inches(0.5),
                  f"By {author}", t["body_font"], 14, t["subtitle_color"],
                  alignment=PP_ALIGN.LEFT)

    # ── Content slides ────────────────────────────────────────────────
    for idx, s in enumerate(slides_data):
        slide_type = s.get("type", "bullet")

        if slide_type == "bullet":
            _build_bullet_slide(prs, s, t)
        elif slide_type == "section":
            _build_section_slide(prs, s, t)
        elif slide_type == "text":
            _build_text_slide(prs, s, t)
        elif slide_type == "comparison":
            _build_comparison_slide(prs, s, t)
        elif slide_type == "image":
            _build_image_slide(prs, s, t)
        else:
            _build_bullet_slide(prs, s, t)

    # ── Thank-you / end slide ─────────────────────────────────────────
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["bg_color"])
    _add_accent_bar(slide, t["accent_color"])
    _add_text_box(slide, Inches(1), Inches(2.5), Inches(10), Inches(1.5),
                  "Thank You!", t["title_font"], 44, t["title_color"],
                  bold=True, alignment=PP_ALIGN.CENTER)
    _add_text_box(slide, Inches(1), Inches(4.2), Inches(10), Inches(0.8),
                  title, t["body_font"], 20, t["subtitle_color"],
                  alignment=PP_ALIGN.CENTER)

    prs.save(full_path)
    total = len(prs.slides)
    logger.info(f"PPT saved: {full_path} ({total} slides)")
    return f"Presentation saved to {full_path} ({total} slides)"


@tool
def create_quick_ppt(
    filename: str,
    title: str,
    bullet_points: list,
    theme: str = "default",
) -> str:
    """Create a quick 3-slide PowerPoint: title slide, bullet slide, thank-you slide.

    Use this when the user wants a simple, fast presentation with one set of bullets.
    For multi-slide presentations prefer create_presentation.

    Args:
        filename: Output filename ending in .pptx (e.g. 'output/summary.pptx').
        title: Main presentation title.
        bullet_points: List of bullet-point strings (max 7 recommended).
        theme: Colour theme. One of 'default', 'dark', 'corporate', 'creative'.

    Returns:
        Confirmation message with file path and slide count.
    """
    slides = [
        {"type": "bullet", "heading": title, "bullets": bullet_points},
    ]
    return create_presentation(filename, title, slides, theme=theme)


@tool
def add_slide_to_ppt(
    filepath: str,
    slide_type: str,
    heading: str,
    content: list,
) -> str:
    """Open an existing .pptx file and append a new slide to it.

    Use this to incrementally build a presentation one slide at a time.

    Args:
        filepath: Path to the existing .pptx file.
        slide_type: One of 'bullet', 'text', or 'section'.
        heading: Heading text for the new slide.
        content: For 'bullet' a list of bullet strings.
                 For 'text' a list with a single paragraph string.
                 For 'section' a list with an optional subtitle string.

    Returns:
        Confirmation message with updated slide count.
    """
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"

    try:
        from pptx import Presentation as PptxPresentation
        from pptx.util import Inches, Pt
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        return "Error: python-pptx is required. Install with: pip install python-pptx"

    prs = PptxPresentation(filepath)
    t = _get_theme("default")

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, t["bg_color"])

    if slide_type == "section":
        _set_slide_bg(slide, t["accent_color"])
        _add_text_box(slide, Inches(1), Inches(2.5), Inches(11), Inches(1.5),
                      heading, t["title_font"], 36, (0xFF, 0xFF, 0xFF),
                      bold=True, alignment=PP_ALIGN.CENTER)
        if content:
            _add_text_box(slide, Inches(1), Inches(4.2), Inches(11), Inches(0.8),
                          content[0], t["body_font"], 18,
                          (0xEE, 0xEE, 0xEE),
                          alignment=PP_ALIGN.CENTER)
    elif slide_type == "text":
        _add_accent_bar(slide, t["accent_color"])
        _add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(1),
                      heading, t["title_font"], 28, t["heading_color"], bold=True)
        body = content[0] if content else ""
        _add_text_box(slide, Inches(1), Inches(1.8), Inches(10.5), Inches(5),
                      body, t["body_font"], 16, t["body_color"])
    else:
        # Default: bullet
        _add_accent_bar(slide, t["accent_color"])
        _add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(1),
                      heading, t["title_font"], 28, t["heading_color"], bold=True)

        txBox = slide.shapes.add_textbox(Inches(1), Inches(1.8),
                                         Inches(10.5), Inches(5))
        tf = txBox.text_frame
        tf.word_wrap = True
        for i, bullet in enumerate(content):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = bullet
            p.font.name = t["body_font"]
            p.font.size = Pt(18)
            p.font.color.rgb = _rgb(t["body_color"])
            p.space_after = Pt(10)

    prs.save(filepath)
    total = len(prs.slides)
    logger.info(f"Added slide to {filepath} ({total} slides)")
    return f"Slide added. Presentation now has {total} slides. Saved to {filepath}"


@tool
def list_ppt_themes() -> str:
    """List all available PowerPoint colour themes with a short description.

    Returns:
        Formatted string of theme names and their colour palettes.
    """
    descriptions = {
        "default":   "Clean white background, navy titles, blue accents",
        "dark":      "Dark charcoal background, white text, cyan accents",
        "corporate": "Light grey background, dark navy titles, red accents",
        "creative":  "White background, purple/pink titles, orange accents",
    }
    lines = ["Available PPT themes:", ""]
    for name, desc in descriptions.items():
        lines.append(f"  - {name:12s}: {desc}")
    lines.append("")
    lines.append("Pass the theme name to create_presentation() or create_quick_ppt().")
    return "\n".join(lines)


# ── Export list (follows project convention) ──────────────────────────

PPT_TOOLS = [
    create_presentation,
    create_quick_ppt,
    add_slide_to_ppt,
    list_ppt_themes,
]


# ── Self-test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("TEST: create_presentation (default theme)")
    print("=" * 60)

    test_slides = [
        {"type": "section", "heading": "Introduction", "subtitle": "Why this matters"},
        {
            "type": "bullet",
            "heading": "Key Highlights",
            "bullets": [
                "Revenue grew 25% year-over-year",
                "Customer base expanded to 10,000+",
                "Launched 3 new product lines",
                "Net promoter score reached 72",
            ],
        },
        {
            "type": "text",
            "heading": "Executive Summary",
            "body": (
                "This quarter marked a significant milestone for the company. "
                "We achieved record revenue while maintaining strong margins."
            ),
        },
        {
            "type": "comparison",
            "heading": "Q1 vs Q2 Performance",
            "left_title": "Q1 Results",
            "left_items": ["$2.1M revenue", "8,200 customers", "NPS: 68"],
            "right_title": "Q2 Results",
            "right_items": ["$2.6M revenue", "10,100 customers", "NPS: 72"],
        },
    ]

    result = create_presentation(
        "test_presentation.pptx",
        "Quarterly Business Review",
        test_slides,
        theme="default",
        subtitle="Q2 2026 Performance",
        author="Synergy Agent",
    )
    print(f"  OK: {result}")

    print("\nTEST: create_quick_ppt (dark theme)")
    result2 = create_quick_ppt(
        "test_quick.pptx",
        "AI Trends 2026",
        ["Multimodal models dominate", "Agents become mainstream", "Edge AI rises"],
        theme="dark",
    )
    print(f"  OK: {result2}")

    print("\nTEST: add_slide_to_ppt")
    result3 = add_slide_to_ppt(
        "test_quick.pptx",
        "bullet",
        "Additional Insights",
        ["Open-source gains traction", "Regulation increases globally"],
    )
    print(f"  OK: {result3}")

    print("\nTEST: list_ppt_themes")
    print(list_ppt_themes())

    print("\nAll tests passed.")
