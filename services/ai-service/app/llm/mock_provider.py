from typing import Any

from app.llm.base import LlmProvider


class MockLlmProvider(LlmProvider):
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        del system_prompt, schema
        priority = "high" if "risk" in user_prompt or "风险" in user_prompt else "medium"
        return {
            "title": "先把风险拆清楚",
            "problem_essence": "当前讨论需要把影响范围、责任人和回滚条件说清楚。",
            "risk": "如果边界和回滚条件不明确，后续上线或交付容易失控。",
            "suggested_reply": "我们先确认影响范围、验收标准和回滚触发条件，再决定是否进入下一步。",
            "follow_up_question": "这件事的 owner、截止时间和失败回滚方案分别是什么？",
            "action_item": "补齐影响范围、owner、截止时间和回滚条件。",
            "priority": priority,
        }
