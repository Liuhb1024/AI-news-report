"""通义千问（Qwen）模型客户端。"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

from ..base import ModelClient, ModelError, ModelRequest, ModelResponse


logger = logging.getLogger(__name__)


class QwenClient(ModelClient):
    """适配通义千问的 OpenAI 兼容接口。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="qwen", config=config)

        if OpenAI is None:
            raise ModelError("未安装 openai 库，无法初始化 Qwen 客户端")

        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ModelError("Qwen 未配置 api_key")

        self.base_url = self.config.get(
            "base_url",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model_name = self.config.get("model", "qwen-plus")
        timeout = self.config.get("timeout", 60)

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)

    def generate(self, request: ModelRequest) -> ModelResponse:
        messages = request.messages or [{"role": "user", "content": request.prompt}]
        metadata = request.metadata or {}
        temperature = metadata.get("temperature", self.config.get("temperature", 0.3))
        max_tokens = metadata.get("max_tokens", self.config.get("max_tokens", 4000))

        extra_kwargs: Dict[str, Any] = {}
        if "top_p" in metadata:
            extra_kwargs["top_p"] = metadata["top_p"]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_kwargs,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Qwen 调用失败")
            raise ModelError(str(exc)) from exc

        content = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        usage_dict = usage.to_dict() if hasattr(usage, "to_dict") else (usage or None)

        return ModelResponse(content=content, provider=self.name, raw=response, usage=usage_dict)

