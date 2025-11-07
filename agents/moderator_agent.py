"""Moderator Agent：负责对多 Agent 结果进行复核与总结。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import Agent, AgentContext, AgentMessage, AgentStepResult
from .constants import (
    ENRICHED_DATA_KEY,
    NEWS_ITEMS_KEY,
    POLICY_ANALYSIS_KEY,
    REPORT_METADATA_KEY,
)


logger = logging.getLogger(__name__)


class ModeratorAgent(Agent):
    """简单的主持/评审 Agent，用于流程校验与总结。"""

    REQUIRED_KEYS = [
        NEWS_ITEMS_KEY,
        POLICY_ANALYSIS_KEY,
        ENRICHED_DATA_KEY,
        REPORT_METADATA_KEY,
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="ModeratorAgent", config=config)

    def run(self, context: AgentContext) -> AgentStepResult:
        missing = [key for key in self.REQUIRED_KEYS if key not in context.shared_state]
        status = "✅ 流程完整" if not missing else "⚠️ 存在缺失"

        summary_lines: List[str] = [status]
        if missing:
            summary_lines.append("缺少以下关键步骤：" + ", ".join(missing))
        else:
            summary_lines.append("全部关键产物已生成，可进入复核或发布阶段。")

        message = AgentMessage(
            role="moderator",
            name=self.name,
            content="\n".join(summary_lines),
            data={
                "missing": missing,
                "total_messages": len(context.messages),
            },
        )

        diagnostics = {
            "missing_count": len(missing),
            "messages": len(context.messages),
        }

        self.log("主持人检查完成", extra={"missing": missing})

        return AgentStepResult(message=message, diagnostics=diagnostics)

