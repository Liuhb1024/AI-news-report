"""Agent 调度器与运行记录。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .base import Agent, AgentContext, AgentMessage, AgentStepResult


logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """调度器运行配置。"""

    run_id: str
    output_root: Path
    save_manifest: bool = True
    manifest_filename: str = "manifest.json"


@dataclass
class AgentRunRecord:
    """用于记录单个 Agent 的执行信息。"""

    agent_name: str
    started_at: str
    finished_at: str
    tokens_used: Optional[int] = None
    diagnostics: Optional[Dict[str, Any]] = None


class AgentOrchestrator:
    """负责安排多个 Agent 协作的调度器。"""

    def __init__(self, config: OrchestratorConfig, agents: Optional[Sequence[Agent]] = None) -> None:
        self.config = config
        self.agents: List[Agent] = list(agents) if agents else []
        self.records: List[AgentRunRecord] = []

    def register(self, agent: Agent) -> None:
        logger.debug("注册 Agent: %s", agent.name)
        self.agents.append(agent)

    def register_many(self, agents: Iterable[Agent]) -> None:
        for agent in agents:
            self.register(agent)

    def run(self, date_str: str, initial_state: Optional[Dict[str, Any]] = None) -> AgentContext:
        logger.info("开始 orchestrator 流程: run_id=%s", self.config.run_id)
        context = AgentContext(date_str=date_str, shared_state=initial_state or {})

        for agent in self.agents:
            logger.info("执行 Agent: %s", agent.name)
            started = datetime.now().isoformat()
            try:
                result = agent.run(context)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Agent 执行失败: %s", agent.name)
                raise
            finished = datetime.now().isoformat()

            self._handle_result(context, result)
            self.records.append(
                AgentRunRecord(
                    agent_name=agent.name,
                    started_at=started,
                    finished_at=finished,
                    tokens_used=(result.diagnostics or {}).get("tokens"),
                    diagnostics=result.diagnostics,
                )
            )

        if self.config.save_manifest:
            self._persist_manifest(context)

        return context

    def _handle_result(self, context: AgentContext, result: AgentStepResult) -> None:
        context.add_message(result.message)

        if result.payload:
            for key, value in result.payload.items():
                context.update_state(key, value)

    def _persist_manifest(self, context: AgentContext) -> None:
        manifest = {
            "run_id": self.config.run_id,
            "generated_at": datetime.now().isoformat(),
            "date": context.date_str,
            "agents": [record.__dict__ for record in self.records],
            "shared_state_keys": sorted(context.shared_state.keys()),
            "message_count": len(context.messages),
        }

        output_dir = self.config.output_root
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / self.config.manifest_filename

        logger.debug("写入 manifest: %s", manifest_path)
        with manifest_path.open("w", encoding="utf-8") as fp:
            json.dump(manifest, fp, ensure_ascii=False, indent=2)

