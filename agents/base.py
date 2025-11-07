"""Agent 基础类型与共享上下文定义。"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Agent 间传递的消息对象。"""

    role: str
    content: str
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentStepResult:
    """Agent 执行单步后的产物。"""

    message: AgentMessage
    payload: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = None


@dataclass
class AgentContext:
    """Agent 共享的运行上下文。"""

    date_str: str
    messages: List[AgentMessage] = field(default_factory=list)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        logger.debug("记录消息: role=%s name=%s", message.role, message.name)
        self.messages.append(message)

    def update_state(self, key: str, value: Any) -> None:
        logger.debug("更新共享状态: %s", key)
        self.shared_state[key] = value


class Agent(ABC):
    """所有具体 Agent 的抽象基类。"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.config = config or {}

    @abstractmethod
    def run(self, context: AgentContext) -> AgentStepResult:
        """执行 Agent 逻辑并返回结果。"""

    def log(self, message: str, level: int = logging.INFO, **kwargs: Any) -> None:
        logger.log(level, "[%s] %s", self.name, message, extra=kwargs or None)

