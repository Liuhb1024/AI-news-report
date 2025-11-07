"""Policy Agent：负责调用 LLM 提炼投资方向。"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentMessage, AgentStepResult
from .constants import NEWS_ITEMS_KEY, POLICY_ANALYSIS_KEY
from config import get_config
from llm_analyzer import LLMAnalyzer


logger = logging.getLogger(__name__)


class PolicyAgent(Agent):
    """基于新闻内容识别政策/投资方向。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="PolicyAgent", config=config)
        self.app_config = self.config.get("app_config") or get_config()
        self.model_router = self.config.get("model_router")

    def run(self, context: AgentContext) -> AgentStepResult:
        news_items = context.shared_state.get(NEWS_ITEMS_KEY)
        if not news_items:
            raise RuntimeError("缺少新闻数据，无法执行政策分析")

        self.log("开始调用 LLM 提炼投资方向", extra={"news_count": len(news_items)})

        analyzer = LLMAnalyzer(config=self.app_config, model_router=self.model_router)

        analysis = analyzer.extract_investment_directions(news_items)
        if not analysis:
            raise RuntimeError("LLM 未返回有效的投资方向")

        metadata = analysis.get("_metadata", {})
        summary = analysis.get("summary", "")
        policy_count = len(analysis.get("key_policies", []))
        directions_count = len(analysis.get("directions", []))

        payload = {POLICY_ANALYSIS_KEY: analysis}
        message = AgentMessage(
            role="agent",
            name=self.name,
            content="政策分析完成",
            data={
                "summary": summary,
                "key_policies": policy_count,
                "directions": directions_count,
            },
        )

        diagnostics = {
            "tokens": metadata.get("tokens_used"),
            "model": metadata.get("model"),
        }

        self.log(
            "政策分析完成",
            extra={
                "directions": directions_count,
                "token_usage": diagnostics["tokens"],
            },
        )

        return AgentStepResult(message=message, payload=payload, diagnostics=diagnostics)

