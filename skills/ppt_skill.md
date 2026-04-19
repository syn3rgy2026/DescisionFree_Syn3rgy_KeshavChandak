# PowerPoint Skill — SYNERGY AGENT

> *Owner:* Person 3

---

## When This Skill Is Active

This skill is loaded when the task involves:
- Creating presentations, PPTs, slides, or decks
- Pitch decks for hackathons or startups
- Business proposals or reports
- Academic presentations
- Keywords: "presentation", "ppt", "slides", "deck", "powerpoint"

---

## Available Tools

You have access to these PPT tools:

1. *create_presentation()* - Main tool for multi-slide presentations
2. *create_quick_ppt()* - Fast 3-slide presentations
3. *add_slide_to_ppt()* - Add slides to existing presentations
4. *list_ppt_themes()* - See available themes

You also have *browser* tool for image acquisition.

---

## Step-by-Step Process

### STEP 1: Understand Context (MANDATORY)

Before creating any slides, identify:

*Presentation Type:*
- Hackathon → Modern, bold, tech-focused
- Business → Professional, clean, corporate
- Academic → Formal, structured, minimal
- Startup Pitch → Dynamic, impact-driven
- Technical → Diagram-heavy, structured

*Choose Theme:*
python
list_ppt_themes()  # See available themes

# Themes available:
# - "default"   → Clean white · navy titles · blue accents
# - "dark"      → Dark background · white text · cyan accents
# - "corporate" → Light grey · dark navy · red accents
# - "creative"  → White · purple/pink · orange accents


*Example:*
User asks: "Create a hackathon pitch for our AI traffic system"
→ Type: Hackathon
→ Theme: "default" or "creative"
→ Style: Modern, visual-heavy, impact-driven

---

### STEP 2: Create Structured Plan (MANDATORY)

*For Hackathon Projects (10-12 slides):*

Title Slide
Problem Statement
Existing Solutions & Gaps
Our Solution
How It Works (Flow Diagram)
Architecture (System Diagram)
Tech Stack
Key Features
Demo/Screenshots
Impact & Results
Future Roadmap
Team & Thank You


*For Business Presentations (8-10 slides):*

Title Slide
Executive Summary
Market Analysis
Our Solution
Business Model
Competitive Advantage
Go-to-Market Strategy
Financial Projections
Team
Ask/Next Steps


*For Technical Presentations (8-10 slides):*

Title Slide
Overview
System Architecture
Component Breakdown
Data Flow
Technology Stack
Implementation Details
Performance Metrics
Security & Scalability
Conclusion


*Log the plan:*
[STEP 2/10] Creating presentation plan...
Identified: Hackathon pitch
Theme: default
Structure: 12 slides
✅ Plan created

---

### STEP 3: Gather Images (CRITICAL)

*For EACH slide, identify what images would enhance it:*

*Example - Problem Statement Slide:*
python
# Search for relevant image
browser(
    action="search",
    query="traffic congestion city problem illustration high quality"
)

# Navigate to a good result
browser(
    action="navigate",
    url="<best_image_source_url>"
)

# Download the image (use appropriate method)
# Save to: output/assets/slide_02_problem.jpg


*Image Requirements by Slide Type:*
Slide Type              Image Needed            Search Query Examples
─────────────────────────────────────────────────────────────────────
Title                   Hero/background         "tech innovation hero image"
Problem Statement       Illustration            "traffic problem illustration"
Solution                Product/demo            "AI dashboard screenshot"
Architecture            Diagram                 "cloud architecture diagram"
Tech Stack              Logos (3-6)             "Python logo official high res"
Features                Icons (3-6)             "AI feature icons modern"
Demo                    Screenshots (2-4)       Actual product screenshots
Impact                  Charts/graphs           "data visualization chart"
Team                    Photos                  Team member photos

*Image Download Pattern:*
[STEP 3/10] Gathering images for all slides...
[3.1] Title slide background...
→ Searching: "AI technology hero background"
→ Downloading: output/assets/slide_01_hero.jpg
✅ Image saved (1920x1080)
[3.2] Problem illustration...
→ Searching: "traffic congestion city illustration"
→ Downloading: output/assets/slide_02_problem.jpg
✅ Image saved
[3.3] Architecture diagram...
→ Searching: "cloud system architecture diagram"
→ Downloading: output/assets/slide_05_architecture.png
✅ Diagram saved
[3.4] Tech stack logos...
→ Downloading: Python logo
→ Downloading: React logo
→ Downloading: PostgreSQL logo
✅ 3 logos acquired
[3.5] Feature icons...
→ Searching: "AI feature icons set"
→ Downloading 3 icons
✅ Icons ready
✅ All images acquired (8 total)

*Validation:*
After downloading each image, verify:
- File exists
- File size > 10KB (not broken)
- Proper format (.jpg, .png)

---

### STEP 4: Create Content (Text Guidelines)

*Rules:*
- *Maximum 5 bullet points* per slide
- *Maximum 10 words* per bullet
- Use *action verbs* and *concrete numbers*
- No full sentences - use phrases
- Keep it sharp and impactful

*Good Examples:*
✅ "Reduced processing time by 60%"
✅ "Real-time AI traffic optimization"
✅ "Served 50,000+ users in 3 months"
✅ "Built with Python, React, PostgreSQL"

*Bad Examples:*
❌ "We have successfully reduced the processing time"
❌ "The application uses artificial intelligence"
❌ "Our system is very efficient and scalable"

---

### STEP 5: Build slides_data Structure

*Prepare the data for create_presentation():*

python
slides_data = [
    # Slide 1: Section header
    {
        "type": "section",
        "heading": "The Problem",
        "subtitle": "Why current solutions fail"
    },
    
    # Slide 2: Bullet points
    {
        "type": "bullet",
        "heading": "Traffic Challenges",
        "bullets": [
            "Congestion costs $87B annually",
            "54 hours lost per driver yearly",
            "Current systems are reactive",
            "No predictive capabilities",
            "Limited real-time data"
        ]
    },
    
    # Slide 3: Text slide
    {
        "type": "text",
        "heading": "Our Solution",
        "body": "AI-powered traffic optimization platform using real-time data from 10,000+ sensors. Predicts congestion 30 minutes in advance with 94% accuracy."
    },
    
    # Slide 4: Comparison
    {
        "type": "comparison",
        "heading": "Before vs After",
        "left_title": "Current System",
        "left_items": [
            "Reactive traffic signals",
            "No prediction",
            "Manual adjustments",
            "Limited coverage"
        ],
        "right_title": "Our System",
        "right_items": [
            "AI-powered optimization",
            "30-min prediction",
            "Automated real-time",
            "City-wide coverage"
        ]
    },
    
    # Slide 5: Image slide (for diagrams)
    {
        "type": "image",
        "heading": "System Architecture",
        "image_path": "output/assets/slide_05_architecture.png",
        "caption": "Cloud-based AI processing with edge computing"
    },
    
    # Add more slides...
]


*Important Notes:*
- Use *"type": "image"* for any slides with diagrams, screenshots, or large visuals
- Use *"type": "comparison"* for before/after, option A vs B, etc.
- Use *"type": "section"* for section breaks (full-color background slides)
- Use *"type": "bullet"* for standard content slides
- Use *"type": "text"* for paragraph-heavy slides (use sparingly)

---

### STEP 6: Generate the Presentation

*Call create_presentation():*

python
[STEP 6/10] Generating presentation...

result = create_presentation(
    filename="output/ai_traffic_system_pitch.pptx",
    title="SmartFlow AI",
    slides_data=slides_data,
    theme="default",
    subtitle="AI-Powered Traffic Optimization",
    author="Team Synergy"
)

✅ Presentation created: output/ai_traffic_system_pitch.pptx (14 slides)


*For quick presentations (3 slides only):*
python
create_quick_ppt(
    filename="output/quick_summary.pptx",
    title="Project Summary",
    bullet_points=[
        "AI traffic optimization",
        "94% prediction accuracy",
        "50,000+ users served"
    ],
    theme="default"
)


---

### STEP 7: Verify Output with Screenshots (CRITICAL)

*After creating the PPT, verify the output:*

python
[STEP 7/10] Verifying presentation quality...

# Take screenshot of the saved PPT file
# (This might require converting PPT to images first)

# Alternative: Open the file location and take screenshot
browser(
    action="navigate",
    url="file:///absolute/path/to/output/ai_traffic_system_pitch.pptx"
)

browser(
    action="screenshot",
    filename="ppt_verification.png"
)

✅ Screenshot saved for verification


*Quality Checks:*
✅ Visual Verification:

All slides present (count matches plan)
Images loaded correctly (not broken)
Text is readable
Colors are consistent
Layout looks professional

✅ Content Verification:

No typos
Bullet points are concise
Images are relevant
Proper sequencing


*Report results:*
[STEP 7/10] Verification complete
Total slides: 14
Images used: 8
Theme: default
File size: 2.4 MB
✅ All checks passed

---

### STEP 8: Iterative Refinement (If Needed)

*If user requests changes, use add_slide_to_ppt():*

python
# User says: "Add a slide about team members"

[STEP 8/10] Adding requested slide...

add_slide_to_ppt(
    filepath="output/ai_traffic_system_pitch.pptx",
    slide_type="bullet",
    heading="Our Team",
    content=[
        "John Doe - AI/ML Lead",
        "Jane Smith - Backend Engineer",
        "Bob Wilson - Frontend Developer",
        "Alice Chen - Data Scientist"
    ]
)

✅ Slide added. Presentation now has 15 slides.


*For different slide types:*
python
# Add section header
add_slide_to_ppt(
    filepath="path/to/file.pptx",
    slide_type="section",
    heading="Future Roadmap",
    content=["Q3-Q4 2026 Plans"]  # Subtitle
)

# Add text slide
add_slide_to_ppt(
    filepath="path/to/file.pptx",
    slide_type="text",
    heading="Technical Details",
    content=["Long paragraph of explanation..."]
)


*DO NOT regenerate entire presentation for small changes.*

---

### STEP 9: Final Delivery

*Report to user:*
✅ Presentation Created Successfully!
📊 Details:
* File: output/ai_traffic_system_pitch.pptx
* Slides: 14
* Theme: default
* Images: 8
* File size: 2.4 MB
📋 Slide Breakdown:

Title: SmartFlow AI
Section: The Problem
Bullet: Traffic Challenges
Text: Our Solution
Comparison: Before vs After
Image: System Architecture
Bullet: Tech Stack
Bullet: Key Features
Image: Demo Screenshots
Bullet: Impact & Results
Bullet: Future Roadmap
Bullet: Our Team
Thank You

Would you like any changes or additions?

---

## Complete Workflow Example
User: "Create a hackathon pitch for our AI traffic system"
[STEP 1/10] Understanding context...
→ Type: Hackathon pitch
→ Theme: default
→ Style: Modern, visual-heavy
✅ Context identified
[STEP 2/10] Creating presentation plan...
→ Structure: 12 slides
→ Sections: Problem, Solution, Tech, Demo, Impact
✅ Plan created
[STEP 3/10] Gathering images...
[3.1] Title background... ✅
[3.2] Problem illustration... ✅
[3.3] Architecture diagram... ✅
[3.4] Tech logos (3)... ✅
[3.5] Feature icons (4)... ✅
✅ 10 images acquired
[STEP 4/10] Creating content...
→ Writing concise bullet points
→ Crafting impactful headlines
✅ Content ready
[STEP 5/10] Structuring slides_data...
→ 12 slides configured
→ Images mapped to slides
✅ Data structure complete
[STEP 6/10] Generating presentation...
create_presentation(
filename="output/smartflow_pitch.pptx",
title="SmartFlow AI",
slides_data=[...],
theme="default"
)
✅ PPT created (14 slides including title & thank you)
[STEP 7/10] Verifying output...
→ Taking screenshot
→ Checking slide count
→ Validating images
✅ Verification complete
[STEP 8/10] Final review...
✅ All slides present
✅ Images loaded correctly
✅ Text is readable
✅ Professional appearance
✅ TASK COMPLETE
📊 Presentation: output/smartflow_pitch.pptx
Slides: 14
Theme: default
Images: 10
Ready for presentation!
Would you like any changes?

---

## Best Practices

### Image Acquisition
- *Always search* for high-quality images (1920x1080+)
- *Download* before building slides
- *Validate* each file after download
- *Organize* in output/assets/ folder
- *Use descriptive* filenames (slide_05_architecture.png)

### Content Writing
- *Be concise* - max 10 words per bullet
- *Use numbers* - "60% faster" not "much faster"
- *Action verbs* - "Reduced", "Achieved", "Built"
- *No jargon* - keep language simple
- *Impactful* - every word counts

### Slide Design
- *Max 5 bullets* per slide
- *One key idea* per slide
- *Images > text* - visual heavy
- *Consistent* theme throughout
- *White space* - don't overcrowd

### Tools Usage
- Use *create_presentation()* for full presentations
- Use *create_quick_ppt()* only for simple 3-slide decks
- Use *add_slide_to_ppt()* for refinements (don't regenerate)
- Use *list_ppt_themes()* to show theme options

---

## Common Patterns

### Pattern 1: Hackathon Pitch
Structure: Title → Problem → Solution → How It Works →
Tech Stack → Features → Demo → Impact → Team
Images: Hero background, problem illustration, architecture,
tech logos, feature icons, demo screenshots
Theme: "default" or "creative"

### Pattern 2: Business Proposal
Structure: Title → Executive Summary → Market → Solution →
Business Model → Competition → Financials → Team → Ask
Images: Professional stock photos, charts, graphs, logos
Theme: "corporate"

### Pattern 3: Technical Presentation
Structure: Title → Overview → Architecture → Components →
Data Flow → Tech Stack → Implementation →
Performance → Security → Conclusion
Images: Diagrams (many!), architecture charts, code snippets,
performance graphs
Theme: "default"

---

## Error Handling

*If image download fails:*
⚠️ Image download failed for slide 5
→ Action: Continue without image or use placeholder
→ Note in output: "Architecture slide created without diagram"

*If theme doesn't exist:*
⚠️ Theme "purple" not found
→ Action: Use "default" theme
→ Notify user: "Using default theme instead"

*If PPT creation fails:*
❌ create_presentation() failed
→ Action: Try create_quick_ppt() as fallback
→ OR: Ask user for simpler structure

---

## Success Criteria

A presentation task is complete when:

✅ Presentation file created in output/ folder
✅ All planned slides are present
✅ Images are loaded and visible
✅ Content is concise and impactful
✅ Theme is applied consistently
✅ File is verified with screenshot
✅ User is informed of result
✅ Offer made for refinements

---

## Remember

- *Plan first* - don't jump straight to coding
- *Images matter* - spend time finding good ones
- *Be concise* - fewer words, more impact
- *Verify output* - always check the final file
- *Iterate* - use add_slide_to_ppt() for changes
- *Theme matters* - match context (hackathon ≠ corporate)

This skill makes you excellent at creating professional, impactful presentations.
Use it to deliver presentation files that win hackathons and close deals