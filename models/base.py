"""模型调用的抽象基类与数据结构。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ModelRequest:
    """表示一次模型调用所需的最小信息。"""

    prompt: str
    messages: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelResponse:
    """模型返回的统一结构。"""

    content: str
    provider: str
    raw: Any = None
    usage: Optional[Dict[str, Any]] = None


class ModelError(Exception):
    """模型调用失败时抛出的异常。"""


class ModelClient:
    """所有具体模型客户端的基类。"""

    name: str

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.config = config or {}

    def generate(self, request: ModelRequest) -> ModelResponse:  # pragma: no cover - 抽象方法
        """执行一次生成请求。子类需实现具体逻辑。"""
        raise NotImplementedError

    def supports(self, capability: str) -> bool:
        """判断模型是否支持某类任务。默认全部支持，可在子类中覆写。"""
        return True

