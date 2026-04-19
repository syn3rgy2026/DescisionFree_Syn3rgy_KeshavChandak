# Web Automation & Research Skill

> **Owner:** Person 3

## Description

This skill enables you to navigate the web, scrape content, and interact with web pages autonomously.

## Trigger Conditions

Use this skill whenever the user asks you to:
- "Search the web"
- "Scrape a website"
- Automate interactions on a webpage (e.g., "login", "fill form")
- Capture or analyze what is on the screen for web context

## Instructions

1. Use your available web browsing or searching tools to perform the task.
2. **Crucial Visual Verification**: During web automation, whenever you need to "see" the website to understand the layout, verify your progress, or read visual data, you MUST use the `take_and_analyze_screenshot("question")` tool. 
   - Note: The tool returns the raw visual image directly into your observation framework!
   - **IMPORTANT**: In `smolagents`, to ensure the image appears in your chat sequence observation, you must leave the variable as the final unassigned expression in your python block. 
   Like this:
   ```python
   # DO THIS:
   my_screen = take_and_analyze_screenshot("what is on the screen?")
   from time import sleep
   sleep(1) # arbitrary
   my_screen # <-- Bare expression as the last line to observe it!
   ```
3. Use the visual observation from the screenshot to answer questions or proceed to the next automation step!

## Output Format

A clear textual summary of what you found, alongside any visual observations if the user asked what was on the screen.
