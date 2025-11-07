"""模型路由器：支持任务级主备模型调度。"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .base import ModelError, ModelRequest, ModelResponse
from .registry import ModelRegistry


logger = logging.getLogger(__name__)


class ModelRouter:
    """根据任务类型从注册器中选择模型执行请求。"""

    def __init__(self, registry: ModelRegistry, routing_config: Optional[Dict[str, Dict]] = None) -> None:
        self.registry = registry
        self.routing_config = routing_config or {}

    def provider_sequence(self, task: str) -> List[str]:
        entry = self.routing_config.get(task, {})
        sequence: List[str] = []
        primary = entry.get("primary")
        if primary:
            sequence.append(primary)
        sequence.extend(entry.get("fallbacks", []))
        return sequence

    def generate(self, task: str, request: ModelRequest) -> ModelResponse:
        errors: List[str] = []
        for provider_name in self.provider_sequence(task):
            client = self.registry.get(provider_name)
            if not client:
                errors.append(f"未注册模型: {provider_name}")
                continue

            try:
                response = client.generate(request)
                logger.debug("任务 %s 使用模型 %s 成功", task, provider_name)
                return response
            except ModelError as exc:
                error_msg = f"模型 {provider_name} 失败: {exc}"
                logger.warning(error_msg)
                errors.append(error_msg)

        raise ModelError(f"任务 {task} 的所有候选模型均失败: {errors}")

