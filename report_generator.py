"""
报告生成模块
基于补充数据生成深度投资分析报告
"""

import json
import os
from openai import OpenAI
from datetime import datetime
from config import get_config
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except Exception:
    pdfmetrics = None
    TTFont = None

# Optional dependencies for PDF export
try:
    import markdown as md  # Markdown -> HTML
except Exception:
    md = None

# Prefer pure-Python xhtml2pdf first (no system libs)
PISA_IMPORT_ERR = None
try:
    from xhtml2pdf import pisa  # HTML -> PDF (pure Python)
except Exception as _e:
    pisa = None
    PISA_IMPORT_ERR = str(_e)

# Optional WeasyPrint (needs system libs on Windows)
WEASY_IMPORT_ERR = None
try:
    from weasyprint import HTML as WEASY_HTML  # HTML -> PDF
except Exception as _e:
    WEASY_HTML = None
    WEASY_IMPORT_ERR = str(_e)

class ReportGenerator:
    """投资分析报告生成器"""
    
    def __init__(self, api_key=None, model=None, config=None):
        """
        初始化报告生成器
        
        参数：
            api_key: API密钥（可选，默认从配置读取）
            model: 使用的模型（可选，默认从配置读取）
            config: 配置对象（可选，默认使用全局配置）
        """
        # 获取配置
        self.config = config or get_config()
        
        # 获取API密钥和模型配置
        self.api_key = api_key or self.config.get("llm.api_key")
        
        if not self.api_key:
            raise ValueError("❌ 未找到API密钥！")
        
        self.model = model or self.config.get("llm.model", "deepseek-chat")
        self.base_url = self.config.get("llm.base_url", "https://api.deepseek.com")
        self.timeout = self.config.get("llm.timeout", 60)
        
        # 初始化DeepSeek客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        print(f"✅ 报告生成器初始化成功")
        print(f"   模型: {self.model}")
    
    def generate_full_report(self, enriched_data, date_str):
        """
        生成完整的投资分析报告
        
        参数：
            enriched_data: 补充后的完整数据
            date_str: 日期字符串
        
        返回：
            str: Markdown格式的报告
        """
        print("\n" + "="*60)
        print("📝 开始生成投资分析报告...")
        print("="*60)
        
        # 获取投资方向
        directions = enriched_data.get('directions', [])
        
        if not directions:
            print("❌ 没有投资方向，无法生成报告")
            return None
        
        # 生成报告各部分
        report_parts = []
        
        # 1. 报告头部
        print("\n📋 生成报告头部...")
        header = self._generate_header(enriched_data, date_str)
        report_parts.append(header)
        
        # 2. 执行摘要
        print("📊 生成执行摘要...")
        summary = self._generate_executive_summary(enriched_data)
        report_parts.append(summary)
        
        # 3. 为每个方向生成深度分析
        for i, direction in enumerate(directions, 1):
            print(f"\n🔍 分析方向 {i}/{len(directions)}: {direction['name']}...")
            
            direction_report = self._generate_direction_analysis(
                direction, 
                enriched_data,
                i
            )
            report_parts.append(direction_report)
        
        # 4. 报告尾部
        print("\n📌 生成总结与建议...")
        footer = self._generate_footer(enriched_data)
        report_parts.append(footer)
        
        # 组合完整报告
        full_report = "\n\n".join(report_parts)
        
        print("\n✅ 报告生成完成！")
        
        return full_report
    
    def _generate_header(self, data, date_str):
        """生成报告头部"""
        # 格式化日期
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        date_formatted = f"{year}年{month}月{day}日"
        
        summary = data.get('summary', '政策信号分析')
        key_policies = data.get('key_policies', [])
        
        header = f"""# 投资机会分析报告

**报告日期**: {date_formatted}  
**数据来源**: 新闻联播 + 权威媒体补充  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📌 政策基调

> {summary}

"""
        
        if key_policies:
            header += "\n**核心政策关键词**：\n"
            for i, policy in enumerate(key_policies[:5], 1):
                header += f"{i}. {policy}  \n"
        
        header += "\n---\n"
        
        return header
    
    def _generate_executive_summary(self, data):
        """生成执行摘要"""
        directions = data.get('directions', [])
        
        summary = f"""## 🎯 执行摘要

本报告基于 **{len(directions)}** 个识别出的投资方向进行深度分析：

"""
        
        for i, direction in enumerate(directions, 1):
            confidence = direction.get('confidence', 0)
            urgency = direction.get('urgency', '未知')
            category = direction.get('category', '未知')
            threshold = direction.get('investment_threshold', '未知')
            
            # 置信度星级
            stars = '⭐' * min(confidence, 10)
            
            summary += f"{i}. **{direction['name']}** {'⭐' * min(int(confidence) if isinstance(confidence, (int, float)) else 0, 10)}\n"
            summary += f"   - 置信度: {confidence}/10 | 紧迫性: {urgency} | 类别: {category} | 门槛: {threshold}\n\n"
        
        summary += "---\n"
        
        return summary
    
    def _generate_direction_analysis(self, direction, full_data, index):
        """
        为单个投资方向生成深度分析
        这是报告的核心部分
        """
        # 准备提示词数据
        analysis_input = self._prepare_analysis_input(direction)
        
        # 构建提示词
        prompt = self._build_deep_analysis_prompt(analysis_input, index)
        
        # 调用LLM
        try:
            print(f"   📤 发送请求到DeepSeek...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位资深的产业投资分析师，拥有10年以上的投资研究经验，擅长从政策、市场、竞争等多维度分析投资机会。你的分析报告以数据驱动、逻辑清晰、可执行性强著称。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.get("llm.temperature.report", 0.4),
                max_tokens=self.config.get("llm.max_tokens.report", 6000)
            )
            
            analysis = response.choices[0].message.content
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            print(f"   ✅ 分析完成（使用 ~{tokens_used} tokens）")
            
            return analysis
            
        except Exception as e:
            print(f"   ❌ 分析失败: {e}")
            return self._generate_fallback_analysis(direction, index)
    
    def _prepare_analysis_input(self, direction):
        """准备分析输入数据"""
        return {
            'name': direction.get('name', ''),
            'confidence': direction.get('confidence', 0),
            'category': direction.get('category', ''),
            'keywords': direction.get('keywords', []),
            'policy_signal': direction.get('policy_signal', ''),
            'policy_strength': direction.get('policy_strength', ''),
            'urgency': direction.get('urgency', ''),
            'investment_threshold': direction.get('investment_threshold', ''),
            'reason': direction.get('reason', ''),
            'search_queries': direction.get('search_queries', []),
            'recent_news': direction.get('recent_news', []),
            'related_policies': direction.get('related_policies', []),
            'keyword_analysis': direction.get('keyword_analysis', {})
        }
    
    def _build_deep_analysis_prompt(self, data, index):
        """构建深度分析提示词"""
        
        # 格式化新闻
        news_text = self._format_news_for_prompt(data['recent_news'])
        
        # 格式化政策
        policy_text = self._format_policies_for_prompt(data['related_policies'])
        
        prompt = f"""请为以下投资方向生成一份专业、深入、可执行的投资分析报告。

## 投资方向：{data['name']}

### 基础信息
- **置信度**: {data['confidence']}/10
- **行业分类**: {data['category']}
- **政策信号**: {data['policy_signal']}
- **政策强度**: {data['policy_strength']}
- **紧迫性**: {data['urgency']}
- **投资门槛**: {data['investment_threshold']}
- **关键词**: {', '.join(data['keywords'])}

### AI初步判断理由
{data['reason']}

### 最新资讯（权威来源）
{news_text}

### 相关政策文件
{policy_text}

---

## 📋 报告要求

请严格按照以下结构生成分析报告（Markdown格式）：

## 方向{index}：{data['name']}

### 一、机会判断 ⭐

**一句话结论**：（50字内，直接说这个方向值不值得关注，态度要明确）

**核心逻辑**：（200-300字）
1. **政策逻辑**：政府为什么支持这个方向？背后的战略考量是什么？
2. **市场逻辑**：当前市场处于什么阶段（萌芽/成长/成熟）？供需关系如何？
3. **时间窗口**：为什么是现在？这个窗口期大概多长？

---

### 二、产业链分析 🔗

**产业链位置图**：
上游：[具体举例2-3个企业或类型]
↓
中游：[具体举例2-3个企业或类型]
↓
下游：[具体举例2-3个企业或类型]

**最适合切入的环节**：
- **推荐环节**：XXX（明确说是上游/中游/下游的哪个具体位置）
- **理由**：为什么这个环节最适合中小投资者/创业者（3-4点）
- **资金门槛**：XX-XX万（给出范围）
- **技术门槛**：高/中/低，具体需要什么技术或能力
- **竞争程度**：高/中/低，说明现有玩家数量和竞争格局
- **盈利周期**：多久可以实现盈亏平衡

---

### 三、具体机会（3个） 💡

#### 机会1：[机会名称 - 6-10个字]

**机会描述**：（50-80字，说清楚具体做什么产品/服务）

**为什么可行**：
- **数据支撑1**：（从上面的新闻或政策中引用具体内容）
- **数据支撑2**：（继续引用）
- **数据支撑3**：（继续引用）

**需要的资源/能力**：
- **资金**：XX-XX万
  - 产品开发：XX万
  - 初期运营：XX万
  - 市场推广：XX万
- **团队**：X-X人
  - [角色1]：XX人（需要什么能力）
  - [角色2]：XX人（需要什么能力）
- **技术**：
  - [技术1]
  - [技术2]
- **其他关键资源**：
  - 渠道、牌照、场地等

**3个月MVP路线图**：
- **第1个月**：
  - 做什么（具体任务）
  - 预期产出（具体成果）
  
- **第2个月**：
  - 做什么
  - 预期产出
  
- **第3个月**：
  - 做什么
  - 关键里程碑（如首批用户数、收入等）

**成功案例参考**：（如果上面新闻中有相关案例，列举1-2个；没有就说"该细分领域尚处早期，可参考XXX类似模式"）

---

#### 机会2：[机会名称]

（完全按照机会1的结构，但内容要完全不同，从不同角度切入）

---

#### 机会3：[机会名称]

（完全按照机会1的结构，但内容要完全不同）

---

### 四、风险提示 ⚠️

用表格形式列出：

| 风险类型 | 具体风险描述 | 应对建议 |
|---------|-------------|---------|
| **政策风险** | [具体说明可能的政策变化] | [给出2-3条具体建议] |
| **市场风险** | [具体说明市场可能的变化] | [给出2-3条具体建议] |
| **竞争风险** | [具体说明竞争对手威胁] | [给出2-3条具体建议] |
| **技术风险** | [具体说明技术不确定性] | [给出2-3条具体建议] |
| **资金风险** | [具体说明资金链风险] | [给出2-3条具体建议] |

---

### 五、行动建议 ✅

**如果你打算立即行动，推荐按以下步骤进行**：

**第一步（本周内）**：
- [ ] [具体行动1]
- [ ] [具体行动2]
- [ ] [具体行动3]
- **预期结果**：[明确的成果]

**第二步（本月内）**：
- [ ] [具体行动1]
- [ ] [具体行动2]
- [ ] [具体行动3]
- **预期结果**：[明确的成果]

**第三步（3个月内）**：
- [ ] [具体行动1]
- [ ] [具体行动2]
- [ ] [具体行动3]
- **预期结果**：[明确的成果，如用户数、收入等]

**关键决策指标**：
- 如果[指标1]低于[数值]，则[调整建议]
- 如果[指标2]低于[数值]，则[调整建议]
- 如果[指标3]达到[数值]，则[下一步行动]

---

### 六、补充信息 📚

**本分析基于**：
- 政策信号来源：新闻联播
- 权威资讯：{len(data['recent_news'])} 条（新华社、人民网等）
- 政策文件：{len(data['related_policies'])} 条（中国政府网）
- 搜索关键词：{', '.join(data['search_queries'][:3])}

---

## ✍️ 写作要求

**必须做到**：
1. **数据驱动**：每个判断都必须引用上面的新闻、政策或给出清晰逻辑
2. **具体可执行**：避免"加强布局""深化合作"等空话，给出可操作的具体动作
3. **风险透明**：客观指出所有潜在问题，不能只说好处
4. **适合小团队**：所有建议都要考虑资金≤500万的实际约束
5. **时效性强**：强调当前时间窗口，给出紧迫感

**禁止**：
- 不要编造数据或案例
- 不要使用模糊表述（如"可能""或许"太多）
- 不要给出无法验证的建议
- 不要忽视风险只说机会

现在开始生成详细的分析报告。
"""
        
        return prompt
    
    def _format_news_for_prompt(self, news_list):
        """格式化新闻列表供LLM分析"""
        if not news_list:
            return "（暂无相关资讯）"
        
        formatted = []
        for i, news in enumerate(news_list[:8], 1):  # 最多8条
            title = news.get('title', '无标题')
            source = news.get('source', '未知来源')
            snippet = news.get('snippet', '')
            pub_time = news.get('pub_time', '未知时间')
            
            formatted.append(
                f"**[{i}] {source} | {pub_time}**\n"
                f"标题：{title}\n"
                f"摘要：{snippet[:200] if snippet else '无摘要'}..."
            )
        
        return "\n\n".join(formatted)
    
    def _format_policies_for_prompt(self, policy_list):
        """格式化政策列表供LLM分析"""
        if not policy_list:
            return "（暂无相关政策）"
        
        formatted = []
        for i, policy in enumerate(policy_list[:5], 1):  # 最多5条
            title = policy.get('title', '无标题')
            dept = policy.get('department', '未知部门')
            pub_time = policy.get('pub_time', '未知时间')
            
            formatted.append(
                f"**[{i}] {title}**\n"
                f"发文单位：{dept}\n"
                f"发布时间：{pub_time}"
            )
        
        return "\n\n".join(formatted)
    
    def _generate_fallback_analysis(self, direction, index):
        """当LLM失败时的降级分析"""
        return f"""## 方向{index}：{direction.get('name', '未知方向')}

### 一、机会判断 ⭐

**一句话结论**：基于政策信号"{direction.get('policy_signal', '')}"，该方向具有投资价值，建议深入研究。

**核心逻辑**：
{direction.get('reason', '暂无详细分析')}

---

### 二、基础信息

| 维度 | 评估 |
|-----|------|
| **置信度** | {direction.get('confidence', 0)}/10 |
| **行业分类** | {direction.get('category', '未知')} |
| **政策强度** | {direction.get('policy_strength', '未知')} |
| **紧迫性** | {direction.get('urgency', '中')} |
| **投资门槛** | {direction.get('investment_threshold', '未知')} |

---

### 三、数据来源

- **权威资讯**: {len(direction.get('recent_news', []))} 条
- **政策文件**: {len(direction.get('related_policies', []))} 条
- **关键词**: {', '.join(direction.get('keywords', []))}

---

### 四、资讯摘要

"""
        # 添加新闻标题
        news_list = direction.get('recent_news', [])
        if news_list:
            for i, news in enumerate(news_list[:5], 1):
                fallback += f"{i}. [{news.get('source', '未知')}] {news.get('title', '')}\n"
        else:
            fallback += "暂无相关资讯\n"
        
        fallback += "\n---\n\n"
        fallback += "**注意**：由于AI分析服务暂时不可用，以上为基础信息汇总。建议结合资讯内容人工进一步研判。\n\n---\n"
        
        return fallback
    
    def _generate_footer(self, data):
        """生成报告尾部"""
        metadata = data.get('_enrichment_metadata', {})
        
        footer = f"""---

## 📊 报告说明

### 数据来源
本报告数据来自以下权威渠道：
- **新闻联播**：政策信号提取（央视网）
- **权威媒体**：{', '.join(metadata.get('sources_used', ['新华社', '人民网', '中国政府网']))}
- **政策文件**：中国政府网政策文件库

### 生成方法
1. **步骤1**：AI从新闻联播中自动提取投资方向
2. **步骤2**：爬取权威来源补充行业资讯和政策文件
3. **步骤3**：DeepSeek深度分析生成投资报告
4. **质量保证**：所有数据源均为权威公开渠道

### 适用场景
- ✅ 个人创业方向选择参考
- ✅ 小团队项目立项依据
- ✅ 投资人行业趋势研判
- ✅ 政策学习和行业研究

### 使用建议
1. 本报告提供方向性参考，具体决策需结合自身情况
2. 建议优先关注"置信度≥8且紧迫性高"的方向
3. 每个机会都需要进一步尽调验证
4. 风险提示部分必须认真阅读

### 免责声明
1. 本报告仅供研究学习使用，不构成任何投资建议
2. 投资决策需独立判断，投资有风险，入市需谨慎
3. 报告内容基于公开信息，时效性以实际情况为准
4. 对因使用本报告而产生的任何后果，报告生成方不承担责任

---

## 📅 报告元数据

**报告生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}  
**数据爬取时间**: {metadata.get('timestamp', '未知')}  
**总请求次数**: {metadata.get('total_requests', 0)} 次  
**数据源数量**: {len(metadata.get('sources_used', []))} 个  
**安全模式**: {'已启用' if metadata.get('safe_mode', True) else '未启用'}

---

## 🔗 相关资源

**如需更多信息**：
- 新华社：https://www.news.cn
- 人民网：http://www.people.com.cn
- 中国政府网：http://www.gov.cn
- 国家政务服务平台：https://www.gjzwfw.gov.cn

---

**技术支持**: DeepSeek AI | **数据来源**: 多源权威渠道  
**版本**: v1.0 | **更新频率**: 每日

---

© 2024 投资机会分析系统 | Powered by AI Technology
"""
        return footer
    
    def save_report(self, report_content, date_str):
        """保存报告到文件"""
        if not report_content:
            print("❌ 没有报告内容可保存")
            return
        
        from utils.path_helper import get_output_paths
        paths = get_output_paths(self.config, date_str)
        
        filename = os.path.join(paths['reports_dir'], f"report_{date_str}.md")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n✅ 报告已保存到: {filename}")
        
        # 统计信息
        word_count = len(report_content)
        line_count = report_content.count('\n')
        section_count = report_content.count('##')
        
        print(f"\n📈 报告统计:")
        print(f"   字数: {word_count:,} 字符")
        print(f"   行数: {line_count:,} 行")
        print(f"   章节数: {section_count} 个")
        
        # 生成简化版摘要
        self._save_summary(report_content, date_str)

        # 优先尝试使用 xhtml2pdf（无系统库依赖）
        self._export_pdf_simple(report_content, date_str)

        # 兼容旧路径：如可用则尝试 WeasyPrint
        self._maybe_save_pdf(report_content, date_str)
    
    def _save_summary(self, report_content, date_str):
        """
        生成并保存报告摘要（纯文本版）
        """
        try:
            # 提取标题和执行摘要
            lines = report_content.split('\n')
            summary_lines = []
            in_summary = False
            
            for line in lines:
                if '## 🎯 执行摘要' in line:
                    in_summary = True
                    summary_lines.append(line)
                    continue
                
                if in_summary:
                    if line.startswith('## ') and '执行摘要' not in line:
                        break
                    summary_lines.append(line)
            
            from utils.path_helper import get_output_paths
            paths = get_output_paths(self.config, date_str)
            summary_file = os.path.join(paths['reports_dir'], f"summary_{date_str}.txt")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"投资机会分析摘要 - {date_str}\n")
                f.write("="*60 + "\n\n")
                f.write('\n'.join(summary_lines))
                f.write(f"\n\n{'='*60}\n")
                f.write(f"完整报告请查看: report_{date_str}.md\n")
            
            print(f"   摘要文件: summary_{date_str}.txt")
            
        except Exception as e:
            print(f"   ⚠️  摘要生成失败: {e}")

    def _export_pdf_simple(self, report_content, date_str):
        """首选方案：使用 xhtml2pdf 将报告转为 PDF，避免系统依赖。"""
        try:
            if md is None:
                return
            if 'pisa' not in globals() or pisa is None:
                return
            # Markdown -> HTML
            html_body = md.markdown(report_content, extensions=['extra'])
            full_html = (
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<style>"
                "body{font-family:'NotoSansSC','Microsoft YaHei','SimSun','SimHei',Arial,Helvetica,sans-serif;line-height:1.6;font-size:14px;}"
                "h1,h2,h3{margin:16px 0;}"
                "code, pre {font-family:Consolas,'Courier New',monospace;}"
                "table{border-collapse:collapse;width:100%;}"
                "table,th,td{border:1px solid #ddd;padding:6px;}"
                "blockquote{color:#555;border-left:4px solid #ddd;padding-left:10px;margin-left:0;}"
                "</style></head><body>" + html_body + "</body></html>"
            )
            from utils.path_helper import get_output_paths
            paths = get_output_paths(self.config, date_str)
            pdf_path = os.path.join(paths['reports_dir'], f"report_{date_str}.pdf")
            # Register project font if present (improves CJK rendering)
            fonts_dir = os.path.join(os.getcwd(), 'fonts')
            font_file = os.path.join(fonts_dir, 'NotoSansSC-Regular.ttf')
            try:
                if os.path.exists(font_file) and pdfmetrics is not None and TTFont is not None:
                    pdfmetrics.registerFont(TTFont('NotoSansSC', font_file))
            except Exception:
                pass
            with open(pdf_path, 'wb') as out:
                result = pisa.CreatePDF(src=full_html, dest=out, encoding='utf-8')
            if getattr(result, 'err', 0):
                # 留给备用方案处理
                return
            print(f"   PDF文件: {pdf_path} (xhtml2pdf)")
        except Exception:
            # 不中断主流程
            pass

    def _maybe_save_pdf(self, report_content, date_str):
        """尝试将 Markdown 报告转为 PDF（若依赖可用）。"""
        try:
            if md is None:
                print("   ⚠️  未安装 Markdown 库（python-Markdown），跳过 PDF 生成")
                return

            # Markdown -> HTML
            html_body = md.markdown(report_content, extensions=['extra'])
            full_html = (
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<style>"
                "body{font-family:'Microsoft YaHei',Arial,Helvetica,sans-serif;line-height:1.6;font-size:14px;}"
                "h1,h2,h3{margin:16px 0;}"
                "code, pre {font-family:Consolas,'Courier New',monospace;}"
                "table{border-collapse:collapse;width:100%;}"
                "table,th,td{border:1px solid #ddd;padding:6px;}"
                "blockquote{color:#555;border-left:4px solid #ddd;padding-left:10px;margin-left:0;}"
                "</style></head><body>" + html_body + "</body></html>"
            )

            from utils.path_helper import get_output_paths
            paths = get_output_paths(self.config, date_str)
            html_path = os.path.join(paths['reports_dir'], f"report_{date_str}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"   HTML文件: {html_path}")

            # HTML -> PDF（可选 weasyprint）
            if WEASY_HTML is None:
                print("   ⚠️  未安装 WeasyPrint 或系统依赖，暂不生成 PDF。")
                if WEASY_IMPORT_ERR:
                    print(f"      具体原因：{WEASY_IMPORT_ERR}")
                print("      可用浏览器打开 HTML 打印为 PDF，或安装 weasyprint/系统依赖后重试。")
                return

            try:
                from utils.path_helper import get_output_paths
                paths = get_output_paths(self.config, date_str)
                pdf_path = os.path.join(paths['reports_dir'], f"report_{date_str}.pdf")
                WEASY_HTML(string=full_html, base_url=os.getcwd()).write_pdf(pdf_path)
                print(f"   PDF文件: {pdf_path}")
            except Exception as e:
                print(f"   ⚠️  PDF生成失败：{e}")
                print("      可用浏览器打开 HTML 打印为 PDF，或安装 pandoc 进行转换。")
        except Exception as e:
            print(f"   ⚠️  Markdown→HTML 转换失败：{e}")

def load_enriched_data(date_str):
    """加载补充后的数据"""
    from config import get_config
    from utils.path_helper import get_output_paths
    
    config = get_config()
    paths = get_output_paths(config, date_str)
    filename = os.path.join(paths['data_dir'], f"enriched_{date_str}.json")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ 未找到文件: {filename}")
        print("   请先运行 main.py 完成前面的步骤")
        return None
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

def test_report_generator(date_str):
    """测试报告生成器"""
    print("="*60)
    print(f"🧪 测试报告生成器 - {date_str}")
    print("="*60)
    
    # 加载数据
    enriched_data = load_enriched_data(date_str)
    
    if not enriched_data:
        return
    
    # 初始化生成器
    try:
        generator = ReportGenerator(model="deepseek-chat")
        
        # 生成报告
        report = generator.generate_full_report(enriched_data, date_str)
        
        if report:
            # 保存报告
            generator.save_report(report, date_str)
            
            print("\n✅ 测试完成！")
            print(f"\n💡 查看报告:")
            print(f"   完整版: report_{date_str}.md")
            print(f"   摘要版: summary_{date_str}.txt")
        else:
            print("\n❌ 报告生成失败")
    
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 测试时使用今天的日期
    from datetime import date
    today = date.today().strftime("%Y%m%d")
    test_report_generator(today)
