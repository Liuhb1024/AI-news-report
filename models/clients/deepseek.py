"""DeepSeek 模型客户端实现。"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 环境未安装 openai
    OpenAI = None  # type: ignore

from ..base import ModelClient, ModelError, ModelRequest, ModelResponse


logger = logging.getLogger(__name__)


class DeepSeekClient(ModelClient):
    """适配 DeepSeek OpenAI 兼容接口。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="deepseek", config=config)

        if OpenAI is None:
            raise ModelError("未安装 openai 库，无法初始化 DeepSeek 客户端")

        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ModelError("DeepSeek 未配置 api_key")

        self.base_url = self.config.get("base_url", "https://api.deepseek.com")
        self.model_name = self.config.get("model", "deepseek-chat")
        timeout = self.config.get("timeout", 60)

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)

    def generate(self, request: ModelRequest) -> ModelResponse:
        messages = request.messages or [{"role": "user", "content": request.prompt}]
        temperature = (request.metadata or {}).get("temperature", self.config.get("temperature", 0.3))
        max_tokens = (request.metadata or {}).get("max_tokens", self.config.get("max_tokens", 4000))

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("DeepSeek 调用失败")
            raise ModelError(str(exc)) from exc

        content = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        usage_dict = usage.to_dict() if hasattr(usage, "to_dict") else (usage or None)

        return ModelResponse(content=content, provider=self.name, raw=response, usage=usage_dict)

