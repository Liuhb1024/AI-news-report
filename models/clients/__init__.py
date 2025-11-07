"""具体模型客户端集合。"""

from .deepseek import DeepSeekClient
from .qwen import QwenClient

__all__ = [
    "DeepSeekClient",
    "QwenClient",
]

