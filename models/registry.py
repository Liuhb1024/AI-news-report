"""模型注册器：统一管理可用模型。"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .base import ModelClient


class ModelRegistry:
    """管理模型实例，支持动态注册与查询。"""

    def __init__(self) -> None:
        self._clients: Dict[str, ModelClient] = {}

    def register(self, client: ModelClient) -> None:
        if client.name in self._clients:
            raise ValueError(f"模型已存在: {client.name}")
        self._clients[client.name] = client

    def unregister(self, name: str) -> None:
        self._clients.pop(name, None)

    def get(self, name: str) -> Optional[ModelClient]:
        return self._clients.get(name)

    def list(self) -> Iterable[str]:
        return self._clients.keys()

    def clear(self) -> None:
        self._clients.clear()

