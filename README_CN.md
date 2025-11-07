# AI新闻投资分析系统

> 基于新闻联播自动生成投资机会分析报告 | v2.0

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ 功能特性

- 🤖 **智能分析** - 使用大语言模型深度分析政策信号
- 📊 **可视化图表** - 支持ECharts和Matplotlib双引擎
- 📝 **多格式报告** - 导出Markdown/HTML/PDF格式
- 🔍 **政策玄机** - 深度解读政策潜台词和信号强度
- 🎯 **Agent架构** - 模块化设计，易于扩展

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/Liuhb1024/AI-news-report.git
cd AI-news-report

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

创建`.env`文件，添加API密钥：
```bash
OPENAI_API_KEY=your-deepseek-api-key
```

### 3. 运行

```bash
python main.py
```

生成的报告在 `outputs/YYYYMMDD/reports/` 目录

---

## 📊 系统架构

```
新闻抓取 → LLM分析 → 数据补充 → 报告生成 → 多格式导出
   ↓          ↓          ↓          ↓          ↓
QueryAgent PolicyAgent InsightAgent ReportAgent 输出文件
```

### 核心模块

| 模块 | 功能 | 文件 |
|-----|------|------|
| **Agent系统** | 模块化任务编排 | `agents/` |
| **新闻爬虫** | 抓取CCTV新闻 | `scraper.py` |
| **LLM分析** | 提取投资方向 | `llm_analyzer.py` |
| **模型路由** | 多LLM支持 | `models/` |
| **图表生成** | 可视化数据 | `visualization_generator.py` |
| **报告生成** | 输出报告 | `report_generator.py` |

---

## 📦 主要依赖

```
requests          # HTTP请求
beautifulsoup4    # HTML解析
openai            # LLM调用
pyecharts         # 现代图表
matplotlib        # 传统图表
weasyprint        # PDF生成
```

详细依赖见 `requirements.txt`

---

## 📖 文档

- **详细技术文档**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
  - 完整架构说明
  - 模块详解
  - 开发指南
  - 改进方向

- **使用指南**: 
  - 快速开始 → 上方
  - 配置说明 → 技术文档第5章
  - 常见问题 → 技术文档第9章

---

## 📂 输出示例

```
outputs/20251106/
├── data/
│   ├── xinwenlianbo_20251106.json    # 原始新闻
│   ├── analysis_20251106.json        # AI分析结果
│   └── enriched_20251106.json        # 完整数据
├── reports/
│   ├── report_20251106.md            # ⭐ Markdown报告
│   ├── report_20251106.html          # HTML版
│   ├── report_20251106.pdf           # PDF版
│   └── charts/                       # 图表文件夹
│       ├── policy_strength.png       # 政策强度图
│       └── investment_comparison.png # 投资对比图
└── logs/
    └── scraper.log                   # 运行日志
```

---

## 🎨 图表示例

系统支持多种图表类型：

- 📊 **雷达图** - 投资方向多维度评分
- 📈 **柱状图** - 政策信号强度对比
- 📉 **折线图** - 市场规模预测
- 🔵 **散点图** - 投资机会对比分析
- 🟥 **矩阵图** - 风险评估可视化

---

## ⚙️ 配置说明

### 环境变量 (`.env`)
```bash
OPENAI_API_KEY=your-api-key
```

### 配置文件 (`config/`)
```yaml
# development.yaml
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  temperature:
    analysis: 0.3

report:
  chart_engine: "auto"  # auto/echarts/matplotlib
  export_formats:
    pdf: true
```

---

## 🔧 开发指南

### 添加新Agent

```python
# agents/custom_agent.py
from .base import Agent, AgentContext, AgentStepResult

class CustomAgent(Agent):
    def run(self, context: AgentContext) -> AgentStepResult:
        # 实现逻辑
        pass
```

### 添加新图表

```python
# echarts_generator.py
def generate_custom_chart(self, data, title, filename):
    # 实现图表生成
    pass
```

详见 [技术文档 - 开发指南](TECHNICAL_DOCUMENTATION.md#7-开发指南)

---

## 📈 改进计划

### 短期 (1-2周)
- ✅ 完善图表功能
- ✅ 实现数据补充爬取
- ✅ 优化PDF生成

### 中期 (1-2月)
- 🔄 历史数据分析
- 🔄 多模型对比
- 🔄 Web交互界面

### 长期 (3-6月)
- 📅 智能推荐系统
- 📅 实时监控预警
- 📅 投资组合管理

详见 [技术文档 - 改进方向](TECHNICAL_DOCUMENTATION.md#8-改进方向)

---

## ❓ 常见问题

**Q: ECharts图表生成失败？**
```bash
# 方案1: 安装驱动管理器
pip install webdriver-manager

# 方案2: 切换到Matplotlib
# 修改config: chart_engine: "matplotlib"
```

**Q: PDF中文显示方框？**
```bash
# 确保字体文件存在
ls fonts/msyh.ttc

# 或手动下载放到fonts/目录
```

**Q: LLM调用失败？**
```bash
# 检查API密钥
echo $OPENAI_API_KEY

# 检查网络连接
curl https://api.deepseek.com
```

更多问题见 [技术文档 - 常见问题](TECHNICAL_DOCUMENTATION.md#9-常见问题)

---

## 📜 更新日志

### v2.0 (2025-11-07)
- ✨ 新增Agent架构（Query/Policy/Insight/Report/Moderator）
- ✨ 集成ECharts图表生成器（5种图表类型）
- ✨ 添加Matplotlib备选引擎（智能降级）
- ✨ 恢复政策玄机深度解读功能
- ✨ 新增模型路由系统（支持多LLM）
- 🔧 修复PDF生成的中文字体和路径问题
- 🔧 简化数据补充模块
- 📝 完善技术文档

### v1.0 (2025-11-06)
- 🎉 初始版本发布
- ✅ 基础新闻抓取
- ✅ LLM分析
- ✅ 报告生成

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献步骤
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📧 联系方式

- GitHub: [@Liuhb1024](https://github.com/Liuhb1024)
- Issues: [提交问题](https://github.com/Liuhb1024/AI-news-report/issues)

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## ⭐ Star History

如果这个项目对你有帮助，请给个Star⭐支持一下！

---

*最后更新: 2025-11-07*

