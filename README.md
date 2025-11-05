# AI News Investment Report

基于“新闻联播”当日信息，自动提取投资方向，并在安全白名单站点补充权威数据，最终生成结构化的投资分析报告与摘要。

## 功能特性
- 新闻抓取：按日期抓取“新闻联播”内容，保存为 JSON/TXT/MD
- LLM 分析：调用 DeepSeek 兼容接口提取 3–5 个可落地投资方向（结构化 JSON）
- 安全补充：仅访问白名单（新华社/人民网/中国政府网/巨潮等），频控+随机 UA
- 报告生成：对每个方向做深度分析，输出 Markdown 报告与摘要
- 可观测：生成日志与中间产物，便于排查与复用

## 目录结构
- `main.py` 全流程编排（抓取 → 分析 → 补充 → 持久化 → 报告）
- `scraper.py` 新闻抓取
- `llm_analyzer.py` 投资方向抽取（LLM）
- `data_enrichment.py` 权威数据补充（安全模式）
- `report_generator.py` 报告生成（含二次深度分析）

## 环境准备
1) Python 版本：3.9+
2) 安装依赖：
```
python -m pip install -r requirements.txt
```
3) 创建 `.env`（放在项目根目录）：
```
OPENAI_API_KEY=sk-你的密钥
# 可选：DeepSeek 兼容基地址（已在代码中设为 https://api.deepseek.com）
# OPENAI_BASE_URL=https://api.deepseek.com
```

## 运行
- 分析指定日期（YYYYMMDD）：
```
python main.py
```
修改 `main.py` 末尾的示例日期，或调用 `main("20251104")`。不传入则默认今天。

## 产物说明
- `xinwenlianbo_{date}.json|txt|md` 原始新闻数据（JSON/纯文本/Markdown）
- `analysis_{date}.json` LLM 抽取的投资方向（结构化）
- `enriched_{date}.json` 安全补充后的完整数据
- `report_{date}.md` 最终投资分析报告（推荐重点阅读）
- `summary_{date}.txt` 报告执行摘要（精简版）
- `scraper_log.txt` 补充阶段日志

## 导出 PDF（推荐）
本项目内置“无系统依赖”的 PDF 导出优先策略：

1) 安装依赖（推荐）：
```
python -m pip install Markdown xhtml2pdf
```

2) 中文字体（避免 PDF 文本变黑块/方框）
- 在项目根目录创建 `fonts/` 目录，并放入一个支持中文的 TTF，如：`fonts/NotoSansSC-Regular.ttf`
- 若没有该文件，PDF 可能会出现中文缺字或黑条的问题。

3) 运行后会尝试生成：
- `report_{date}.html`
- `report_{date}.pdf`（优先使用 xhtml2pdf 生成）

4) 备用路径（可选）：
- 若需要更高的排版能力，可安装 WeasyPrint：`python -m pip install weasyprint`（Windows 需额外系统库）
- 若仍失败：
  - 浏览器打开 `report_{date}.html` → 打印为 PDF；
  - 或使用 Pandoc：`pandoc report_{date}.md -o report_{date}.pdf`。

## .gitignore 说明
本仓库已添加 `.gitignore`：
- 忽略 `.env` 与本地密钥
- 忽略虚拟环境、缓存与系统文件
- 忽略日志、调试 HTML 与所有运行产物（report/analysis/xinwenlianbo/enriched/summary 等文件）
如需额外忽略自定义文件，可在 `.gitignore` 末尾追加相应规则。

## 配置与安全
- 补充阶段默认安全模式（仅允许白名单域名，带频控与随机 UA）
- 如需扩展白名单域名或调整频控阈值，可在 `data_enrichment.py` 内修改：
  - `safe_sources` 白名单
  - `max_requests_per_domain`、`min_delay`、`max_delay`

## 常见问题
- 未生成报告：多因当日未识别到方向或 LLM API 失败。请先检查 `analysis_{date}.json` 是否有效。
- 网络/频控：白名单站点访问失败会自动重试并记录日志，请查看 `scraper_log.txt`。
- 字符显示：Windows 终端若出现中文/Emoji 乱码，建议使用 UTF-8 编码终端或 VSCode 终端。

## 许可证
仅限个人学习与研究用途；如需商用请审核数据来源与合规边界。
