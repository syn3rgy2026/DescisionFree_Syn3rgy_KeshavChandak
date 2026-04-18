"""
skill_router.py
---------------
Loads skill markdown files from the skills/ folder and routes
them to the agent based on keyword matching against the user's task.
"""

import os
import config


def load_skill_file(filename: str) -> str:
    """
    Read a single skill file from the skills folder.

    Args:
        filename: Name of the .md file inside SKILLS_FOLDER.

    Returns:
        Contents of the file as a string.
        Returns empty string if file not found.
    """
    filepath = os.path.join(config.SKILLS_FOLDER, filename)
    if not os.path.exists(filepath):
        print(f"⚠️  Warning: Skill file not found — {filepath}")
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def get_skills_for_task(task: str) -> str:
    """
    Analyse the task string, load core_agent_skill.md plus any
    keyword-matched skill files, and return them combined.

    Args:
        task: The raw task string from the user.

    Returns:
        A single string containing all relevant skill file contents,
        separated by dividers.
    """
    task_lower = task.lower()
    loaded_sections: list[str] = []

    # ── Always load the core skill ────────────────────────────────────
    core = load_skill_file("core_agent_skill.md")
    if core:
        loaded_sections.append(core)

    # ── Keyword → skill file mapping ─────────────────────────────────
    skill_map: dict[str, list[str]] = {
        "web_skill.md":  ["search", "browse", "scrape", "url", "web", "http", "website", "crawl"],
        "file_skill.md": ["save", "write", "read", "csv", "json", "file", "txt", "download", "upload"],
        "code_skill.md": ["code", "script", "python", "flask", "backend", "deploy", "run", "execute", "pip"],
        "ppt_skill.md":  ["ppt", "slides", "powerpoint", "presentation", "slide", "deck"],
        "social_media_skill.md": ["instagram", "linkedin", "post", "social media", "caption", "marketing", "story"],
    }

    already_loaded: set[str] = set()

    for skill_file, keywords in skill_map.items():
        if skill_file in already_loaded:
            continue
        for kw in keywords:
            if kw in task_lower:
                content = load_skill_file(skill_file)
                if content:
                    loaded_sections.append(content)
                    already_loaded.add(skill_file)
                break  # one keyword match is enough for this skill

    # ── Combine with separators ───────────────────────────────────────
    separator = "\n\n---\n\n"
    return separator.join(loaded_sections)


# ── Quick self-test ───────────────────────────────────────────────────
if __name__ == "__main__":
    test_tasks = [
        "Search the web for Python tutorials",
        "Save the results to a CSV file",
        "Write a Flask backend API",
        "Create a PowerPoint presentation about AI",
        "Summarise the meeting notes for me",
    ]

    for t in test_tasks:
        print(f"\n{'='*60}")
        print(f"Task: {t}")
        print(f"{'='*60}")
        result = get_skills_for_task(t)
        if result:
            # Show first 120 chars of each loaded section
            for i, section in enumerate(result.split("---"), 1):
                preview = section.strip()[:120]
                print(f"  Skill {i}: {preview}...")
        else:
            print("  (no skills matched)")
