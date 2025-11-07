"""Insight Agent：负责安全补充权威数据并生成 enriched 结果。"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentMessage, AgentStepResult
from .constants import ENRICHED_DATA_KEY, POLICY_ANALYSIS_KEY
from config import get_config
from data_enrichment import SafeDataEnrichment


logger = logging.getLogger(__name__)


class InsightAgent(Agent):
    """基于初步方向补充权威资讯与政策数据。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="InsightAgent", config=config)
        self.app_config = self.config.get("app_config") or get_config()

    def run(self, context: AgentContext) -> AgentStepResult:
        analysis = context.shared_state.get(POLICY_ANALYSIS_KEY)
        if not analysis:
            raise RuntimeError("缺少投资方向数据，无法执行补充")

        self.log("开始安全补充权威数据")

        enricher = SafeDataEnrichment(config=self.app_config, date_str=context.date_str)
        enriched = enricher.enrich_all_directions(analysis)
        enricher.save_enriched_data(enriched, context.date_str)

        directions = enriched.get("directions", [])
        news_total = sum(len(item.get("recent_news", [])) for item in directions)
        policy_total = sum(len(item.get("related_policies", [])) for item in directions)

        payload = {ENRICHED_DATA_KEY: enriched}
        message = AgentMessage(
            role="agent",
            name=self.name,
            content="补充数据完成",
            data={
                "directions": len(directions),
                "news": news_total,
                "policies": policy_total,
            },
        )

        diagnostics = {
            "total_requests": enriched.get("_enrichment_metadata", {}).get("total_requests"),
            "safe_mode": enriched.get("_enrichment_metadata", {}).get("safe_mode", True),
        }

        self.log(
            "补充数据完成",
            extra={
                "directions": len(directions),
                "news_count": news_total,
                "policy_count": policy_total,
            },
        )

        return AgentStepResult(message=message, payload=payload, diagnostics=diagnostics)

