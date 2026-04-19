"""Tests for prompt assembly (no live LLM calls)."""

from unittest.mock import patch

import agent.core_agent as ca


def test_load_master_prompt_non_empty():
    text = ca.load_master_prompt()
    assert len(text) > 100
    assert "Synergy" in text or "agent" in text.lower()


def test_build_system_prompt_has_machine_paths():
    with patch.object(ca, "_memory") as m:
        m.build_memory_context.return_value = ""
        sp = ca.build_system_prompt("write tests and deploy to vercel")
    assert "Paths on this machine" in sp
