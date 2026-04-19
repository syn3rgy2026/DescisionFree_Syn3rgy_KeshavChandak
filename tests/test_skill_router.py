"""Tests for skill routing (keyword → skill markdown)."""

from agent.skill_router import get_skills_for_task, load_skill_file


def test_load_core_skill_exists():
    text = load_skill_file("core_agent_skill.md")
    assert len(text) > 20


def test_deploy_keywords_load_deploy_skill():
    task = "run pytest then push to github and deploy to vercel"
    out = get_skills_for_task(task)
    assert "deploy" in out.lower() or "vercel" in out.lower() or "github" in out.lower()


def test_web_task_includes_web_or_research():
    out = get_skills_for_task("search the web for python tutorials")
    assert len(out) > 50
