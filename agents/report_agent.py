"""Report Agent：负责生成最终投资报告与摘要。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentMessage, AgentStepResult
from .constants import ENRICHED_DATA_KEY, REPORT_METADATA_KEY
from config import get_config
from report_generator import ReportGenerator
from utils.path_helper import get_output_paths


logger = logging.getLogger(__name__)


class ReportAgent(Agent):
    """根据 enriched 数据生成 Markdown/HTML/PDF 报告。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="ReportAgent", config=config)
        self.app_config = self.config.get("app_config") or get_config()
        self.model_router = self.config.get("model_router")
        self.generator = ReportGenerator(config=self.app_config, model_router=self.model_router)

    def run(self, context: AgentContext) -> AgentStepResult:
        enriched = context.shared_state.get(ENRICHED_DATA_KEY)
        if not enriched:
            raise RuntimeError("缺少补充数据，无法生成报告")

        self.log("开始生成最终报告")

        report_content = self.generator.generate_full_report(enriched, context.date_str)
        if not report_content:
            raise RuntimeError("未能生成报告内容")

        self.generator.save_report(report_content, context.date_str)

        paths = get_output_paths(self.app_config, context.date_str)
        report_path = Path(paths["reports_dir"]) / f"report_{context.date_str}.md"
        summary_path = Path(paths["reports_dir"]) / f"summary_{context.date_str}.txt"

        payload = {
            REPORT_METADATA_KEY: {
                "report_path": str(report_path),
                "summary_path": str(summary_path),
            }
        }

        message = AgentMessage(
            role="agent",
            name=self.name,
            content="报告生成完成",
            data={
                "report": str(report_path),
                "summary": str(summary_path),
            },
        )

        diagnostics = {
            "sections": report_content.count("##"),
            "length": len(report_content),
        }

        self.log(
            "报告生成完成",
            extra={
                "report_path": str(report_path),
                "summary_path": str(summary_path),
            },
        )

        return AgentStepResult(message=message, payload=payload, diagnostics=diagnostics)

