"""模型注册与路由初始化。"""

from __future__ import annotations

import logging
from typing import Optional

from config import get_config
from .base import ModelError
from .clients import DeepSeekClient, QwenClient
from .registry import ModelRegistry
from .router import ModelRouter


logger = logging.getLogger(__name__)


def create_model_registry(config=None) -> ModelRegistry:
    config = config or get_config()
    providers = config.get("models.providers", {}) or {}

    registry = ModelRegistry()

    for name, provider_conf in providers.items():
        try:
            if name == "deepseek":
                registry.register(DeepSeekClient(provider_conf))
            elif name == "qwen":
                registry.register(QwenClient(provider_conf))
            else:
                logger.warning("未知模型提供方，暂不注册: %s", name)
        except ModelError as exc:
            logger.warning("注册模型 %s 失败: %s", name, exc)

    return registry


def create_model_router(config=None, registry: Optional[ModelRegistry] = None) -> ModelRouter:
    config = config or get_config()
    registry = registry or create_model_registry(config)
    routing_conf = config.get("models.routing", {}) or {}
    return ModelRouter(registry=registry, routing_config=routing_conf)

