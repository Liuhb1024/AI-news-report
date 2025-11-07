"""Query Agent：负责抓取新闻联播原文并做初步清洗。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import Agent, AgentContext, AgentMessage, AgentStepResult
from .constants import NEWS_ITEMS_KEY
from scraper import XinwenliboScraper


logger = logging.getLogger(__name__)


class QueryAgent(Agent):
    """封装新闻抓取逻辑的 Agent。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="QueryAgent", config=config)
        self.scraper = XinwenliboScraper(config=self.config.get("app_config"))

    def run(self, context: AgentContext) -> AgentStepResult:
        self.log(f"开始抓取 {context.date_str} 的新闻联播")

        news_data = self.scraper.scrape_date(context.date_str)
        if not news_data:
            raise RuntimeError("未抓取到任何新闻数据")

        cleaned_news = [self._to_schema(item) for item in news_data]

        try:
            self.scraper.save_to_file(cleaned_news, context.date_str)
        except Exception as exc:  # pylint: disable=broad-except
            self.log(
                "保存新闻数据失败",
                level=logging.WARNING,
                extra={"error": str(exc)},
            )

        payload = {NEWS_ITEMS_KEY: cleaned_news}
        message = AgentMessage(
            role="agent",
            name=self.name,
            content=f"抓取完成，共 {len(cleaned_news)} 条新闻",
            data={"count": len(cleaned_news)},
        )

        self.log("抓取完毕", extra={"news_count": len(cleaned_news)})

        return AgentStepResult(message=message, payload=payload)

    def _to_schema(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """规整化输出结构，确保下游消费稳定。"""
        index = item.get("index")
        title = (item.get("title") or "").strip()
        url = item.get("url")
        content = (item.get("content") or "").strip()

        cleaned_content = self.scraper.get_news_content(url) if content == "未能提取到内容" else content

        return {
            "index": index,
            "title": title,
            "url": url,
            "content": cleaned_content,
        }

