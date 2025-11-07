"""
报告生成模块
基于补充后的数据生成投资分析报告
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import get_config
from models import ModelRequest, ModelRouter
from utils.path_helper import get_output_paths
from visualization_generator import VisualizationGenerator


class ReportGenerator:
    """投资报告生成器"""
    
    def __init__(self, config=None, model_router: Optional[ModelRouter] = None):
        """
        初始化报告生成器
        
        参数：
            config: 配置对象（可选）
            model_router: 模型路由器（可选，用于深度分析）
        """
        self.config = config or get_config()
        self.model_router = model_router
        self.model_task = "report_generation"
        self.viz_generator = None  # 延迟初始化
    
    def _get_confidence(self, direction):
        """
        获取置信度/确定性评分（兼容新旧格式）
        
        新格式：direction['quantitative_scores']['certainty']
        旧格式：direction['confidence']
        """
        # 优先使用新格式
        if 'quantitative_scores' in direction:
            return direction['quantitative_scores'].get('certainty', 5)
        # 降级到旧格式
        return direction.get('confidence', 5)
        
    def generate_full_report(self, enriched_data, date_str):
        """
        生成完整的投资分析报告
        
        参数：
            enriched_data: 补充后的数据
            date_str: 日期字符串 YYYYMMDD
        
        返回：
            str: Markdown格式的报告内容
        """
        print("\n" + "="*60)
        print("📝 开始生成投资分析报告...")
        print("="*60)
        
        # 初始化可视化生成器
        paths = get_output_paths(self.config, date_str)
        charts_dir = os.path.join(paths['reports_dir'], 'charts')
        self.viz_generator = VisualizationGenerator(output_dir=charts_dir)
        self.reports_dir = paths['reports_dir']  # 保存reports目录路径，用于计算相对路径
        print("📊 可视化生成器已初始化")
        
        # 解析日期
        try:
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            formatted_date = date_obj.strftime("%Y年%m月%d日")
        except:
            formatted_date = date_str
        
        # 构建报告
        sections = []
        
        # 1. 标题和概述
        sections.append(self._generate_header(enriched_data, formatted_date))
        
        # 2. 执行摘要
        sections.append(self._generate_executive_summary(enriched_data))
        
        # 2.5. 政策玄机解读（如果有）
        if 'policy_insights' in enriched_data:
            sections.append(self._generate_policy_insights(enriched_data))
        
        # 3. 政策基调分析
        sections.append(self._generate_policy_overview(enriched_data))
        
        # 4. 投资方向详细分析
        sections.append(self._generate_directions_analysis(enriched_data, date_str))
        
        # 5. 风险提示
        sections.append(self._generate_risk_disclaimer())
        
        # 6. 附录
        sections.append(self._generate_appendix(enriched_data))
        
        report = "\n\n".join(sections)
        
        print("✅ 报告生成完成")
        return report
    
    def _generate_header(self, data, formatted_date):
        """生成报告标题"""
        summary = data.get('summary', '政策导向投资机会分析')
        
        header = f"""# 投资机会分析报告

**日期**: {formatted_date}  
**主题**: {summary}  
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---"""
        return header
    
    def _generate_executive_summary(self, data):
        """生成执行摘要"""
        directions = data.get('directions', [])
        metadata = data.get('_enrichment_metadata', {})
        
        if not directions:
            return """## 📋 执行摘要

**当日未识别出明确的投资机会。**

基于当日新闻联播内容分析，未发现符合以下标准的投资方向：
- 政策支持明确
- 资金门槛适中（≤500万）
- 具有可落地性

建议继续关注后续政策动态。"""
        
        # 统计信息
        high_confidence = [d for d in directions if self._get_confidence(d) >= 8]
        urgent = [d for d in directions if d.get('urgency') == '高']
        
        summary = f"""## 📋 执行摘要

**核心发现**：

- 📊 **投资方向数量**: {len(directions)} 个
- ⭐ **高置信度方向**: {len(high_confidence)} 个（置信度≥8）
- 🔥 **高紧迫性方向**: {len(urgent)} 个
- 📰 **权威资讯**: {metadata.get('total_requests', 0)} 条
- 🛡️  **数据来源**: {', '.join(metadata.get('sources_used', []))}

**重点关注方向**：

"""
        
        # 列出高置信度方向
        for i, direction in enumerate(high_confidence[:3], 1):
            summary += f"{i}. **{direction['name']}** "
            summary += f"（置信度: {self._get_confidence(direction)}/10, "
            summary += f"类别: {direction.get('category', '未分类')}）\n"
        
        if not high_confidence:
            # 如果没有高置信度的，列出置信度最高的3个
            sorted_dirs = sorted(directions, key=lambda x: self._get_confidence(x), reverse=True)
            for i, direction in enumerate(sorted_dirs[:3], 1):
                summary += f"{i}. **{direction['name']}** "
                summary += f"（置信度: {self._get_confidence(direction)}/10, "
                summary += f"类别: {direction.get('category', '未分类')}）\n"
        
        return summary
    
    def _generate_policy_insights(self, data):
        """生成政策玄机深度解读"""
        policy_insights = data.get('policy_insights', {})
        key_signals = policy_insights.get('key_signals', [])
        overall_tone = policy_insights.get('overall_tone', '稳健')
        
        section = f"""## 🔍 政策玄机深度解读

**整体政策基调**: {overall_tone}

"""
        
        if key_signals:
            # 生成政策强度对比图
            if self.viz_generator and len(key_signals) > 0:
                try:
                    chart_path = self.viz_generator.generate_policy_strength_chart(
                        key_signals, 
                        'policy_strength.png'
                    )
                    # 转换为相对于报告文件的相对路径
                    chart_rel_path = os.path.relpath(chart_path, self.reports_dir).replace('\\', '/')
                    section += f"\n![政策信号强度对比]({chart_rel_path})\n\n"
                    print(f"   ✅ 生成政策强度图: {chart_path}")
                except Exception as e:
                    print(f"   ⚠️  政策强度图生成失败: {e}")
            
            section += "**本期重大政策信号**：\n\n"
            for i, signal in enumerate(key_signals, 1):
                topic = signal.get('topic', '未知')
                strength = signal.get('strength_score', 5)
                message = signal.get('hidden_message', '')
                urgency = signal.get('urgency_indicator', '')
                
                # 强度emoji
                strength_emoji = "🔴" if strength >= 9 else "🟠" if strength >= 7 else "🟡"
                
                section += f"{i}. {strength_emoji} **{topic}**（强度: {strength}/10）\n"
                section += f"   - **潜台词解读**: {message}\n"
                section += f"   - **紧迫性**: {urgency}\n\n"
        
        return section
    
    def _generate_policy_overview(self, data):
        """生成政策概述"""
        key_policies = data.get('key_policies', [])
        summary = data.get('summary', '')
        
        section = f"""## 🎯 政策基调分析

**今日政策导向**: {summary}

"""
        
        if key_policies:
            section += "**核心政策要点**：\n\n"
            for i, policy in enumerate(key_policies, 1):
                section += f"{i}. {policy}\n"
        else:
            section += "*本日未提取到明确的核心政策。*\n"
        
        return section
    
    def _generate_directions_analysis(self, data, date_str):
        """生成投资方向详细分析"""
        directions = data.get('directions', [])
        
        if not directions:
            return """## 💡 投资方向分析

*当日未识别出具体投资方向。*"""
        
        section = f"""## 💡 投资方向分析

共识别 **{len(directions)}** 个投资方向，详细分析如下：

"""
        
        # 生成投资方向对比气泡图
        if self.viz_generator and len(directions) >= 2:
            try:
                chart_path = self.viz_generator.generate_investment_comparison(
                    directions,
                    'investment_comparison.png'
                )
                chart_rel_path = os.path.relpath(chart_path, self.reports_dir).replace('\\', '/')
                section += f"\n![投资方向对比分析]({chart_rel_path})\n\n"
                section += "*图：气泡大小表示紧迫性，横轴表示确定性，纵轴表示低风险程度*\n\n"
                print(f"   ✅ 生成投资方向对比图: {chart_path}")
            except Exception as e:
                print(f"   ⚠️  投资对比图生成失败: {e}")
        
        section += "\n---\n\n"
        
        # 按置信度排序
        sorted_directions = sorted(directions, key=lambda x: self._get_confidence(x), reverse=True)
        
        for i, direction in enumerate(sorted_directions, 1):
            section += self._generate_single_direction(direction, i, date_str)
            section += "\n---\n\n"
        
        return section
    
    def _generate_single_direction(self, direction, index, date_str):
        """生成单个投资方向的分析"""
        name = direction.get('name', '未命名')
        confidence = self._get_confidence(direction)
        category = direction.get('category', '未分类')
        keywords = direction.get('keywords', [])
        policy_signal = direction.get('policy_signal', '无')
        policy_strength = direction.get('policy_strength', '未知')
        urgency = direction.get('urgency', '未知')
        threshold = direction.get('investment_threshold', '未知')
        reason = direction.get('reason', '无详细说明')
        recent_news = direction.get('recent_news', [])
        related_policies = direction.get('related_policies', [])
        
        # 置信度emoji
        confidence_emoji = "🔥" if confidence >= 9 else "⭐" if confidence >= 7 else "💡"
        
        # 紧迫性emoji
        urgency_emoji = "🔴" if urgency == "高" else "🟡" if urgency == "中" else "🟢"
        
        analysis = f"""### {index}. {confidence_emoji} {name}

**基本信息**：

| 项目 | 内容 |
|------|------|
| 置信度 | {confidence}/10 {self._get_confidence_desc(confidence)} |
| 行业类别 | {category} |
| 政策强度 | {policy_strength} |
| 紧迫性 | {urgency_emoji} {urgency} |
| 投资门槛 | {threshold} |
| 关键词 | {', '.join(keywords[:5])} |

**政策依据**：

> {policy_signal}

**投资机会分析**：

{reason}

"""
        
        # 量化评分（如果有）
        if 'quantitative_scores' in direction:
            analysis += self._format_quantitative_scores(direction['quantitative_scores'])
            
            # 生成雷达图
            if self.viz_generator:
                try:
                    scores = direction['quantitative_scores']
                    radar_data = {
                        '确定性': scores.get('certainty', 5),
                        '回报潜力': min(scores.get('return_rate_3y', {}).get('neutral', 20) / 4, 10),  # 归一化到10分制
                        '风险等级': 10 - scores.get('risk_level', 5),  # 反转，使得低风险得分高
                        '紧迫性': scores.get('urgency', 5),
                        '进入门槛': 10 - scores.get('entry_barrier', 5)  # 反转，使得低门槛得分高
                    }
                    
                    # 使用纯数字命名避免中文乱码问题
                    chart_filename = f"radar_{index}.png"
                    chart_path = self.viz_generator.generate_radar_chart(
                        radar_data,
                        f"{name} - 多维度评估",
                        chart_filename
                    )
                    chart_rel_path = os.path.relpath(chart_path, self.reports_dir).replace('\\', '/')
                    analysis += f"\n![{name}多维度评估]({chart_rel_path})\n\n"
                    print(f"   ✅ 生成雷达图 {index}: {name}")
                except Exception as e:
                    print(f"   ⚠️  雷达图生成失败 ({name}): {e}")
        
        # 市场分析（如果有）
        if 'market_analysis' in direction:
            analysis += self._format_market_analysis(direction['market_analysis'])
            
            # 生成市场预测图
            if self.viz_generator:
                try:
                    market = direction['market_analysis']
                    cagr = market.get('cagr_3y', 0)
                    
                    # 简单估算未来三年市场规模（基于CAGR）
                    tam_str = market.get('tam_estimate', '0')
                    sam_str = market.get('sam_estimate', '0')
                    
                    # 提取数字（假设格式如"100亿元"）
                    import re
                    tam_base = float(re.findall(r'[\d.]+', tam_str)[0]) if re.findall(r'[\d.]+', tam_str) else 100
                    sam_base = float(re.findall(r'[\d.]+', sam_str)[0]) if re.findall(r'[\d.]+', sam_str) else 30
                    
                    from datetime import datetime
                    current_year = datetime.now().year
                    years = [str(current_year + i) for i in range(3)]
                    
                    growth_factor = [1, 1 + cagr/100, (1 + cagr/100)**2]
                    tam_values = [tam_base * g for g in growth_factor]
                    sam_values = [sam_base * g for g in growth_factor]
                    
                    # 使用纯数字命名避免中文乱码问题
                    chart_filename = f"market_{index}.png"
                    chart_path = self.viz_generator.generate_market_forecast_chart(
                        years,
                        tam_values,
                        sam_values,
                        f"{name} - 市场规模预测",
                        chart_filename
                    )
                    chart_rel_path = os.path.relpath(chart_path, self.reports_dir).replace('\\', '/')
                    analysis += f"\n![{name}市场规模预测]({chart_rel_path})\n\n"
                    print(f"   ✅ 生成市场预测图 {index}: {name}")
                except Exception as e:
                    print(f"   ⚠️  市场预测图生成失败 ({name}): {e}")
        
        # 投资方案（如果有）
        if 'investment_plans' in direction:
            analysis += self._format_investment_plans(direction['investment_plans'])
        
        # 风险矩阵（如果有）
        if 'risk_matrix' in direction:
            analysis += self._format_risk_matrix(direction['risk_matrix'])
            
            # 生成风险矩阵图
            if self.viz_generator:
                try:
                    risk_matrix = direction['risk_matrix']
                    # 转换为可视化格式
                    risk_viz_data = {}
                    risk_type_names = {
                        'policy_risk': '政策风险',
                        'competition_risk': '竞争风险',
                        'operation_risk': '运营风险',
                        'compliance_risk': '合规风险'
                    }
                    
                    for key, name in risk_type_names.items():
                        if key in risk_matrix:
                            risk_item = risk_matrix[key]
                            level = risk_item.get('level', '中')
                            risk_viz_data[name] = {
                                'level': level,
                                'score': self._level_to_risk_score(level)
                            }
                    
                    if risk_viz_data:
                        # 使用纯数字命名避免中文乱码问题
                        chart_filename = f"risk_{index}.png"
                        chart_path = self.viz_generator.generate_risk_matrix(
                            risk_viz_data,
                            chart_filename
                        )
                        chart_rel_path = os.path.relpath(chart_path, self.reports_dir).replace('\\', '/')
                        analysis += f"\n![{name}风险评估矩阵]({chart_rel_path})\n\n"
                        print(f"   ✅ 生成风险矩阵图 {index}: {name}")
                except Exception as e:
                    print(f"   ⚠️  风险矩阵图生成失败 ({name}): {e}")
        
        # 深度分析（使用LLM）
        if self.model_router and confidence >= 7:
            deep_analysis = self._generate_deep_analysis(direction, recent_news, related_policies)
            if deep_analysis:
                analysis += f"""**深度洞察**：

{deep_analysis}

"""
        
        # 权威资讯
        if recent_news:
            analysis += f"""**权威资讯** ({len(recent_news)} 条)：

"""
            for i, news in enumerate(recent_news[:5], 1):
                title = news.get('title', '无标题')
                source = news.get('source', '未知来源')
                link = news.get('link', '#')
                pub_time = news.get('pub_time', '')
                
                analysis += f"{i}. **{title}**\n"
                analysis += f"   - 来源: {source}\n"
                if pub_time:
                    analysis += f"   - 时间: {pub_time}\n"
                analysis += f"   - 链接: [{link}]({link})\n\n"
        
        # 相关政策
        if related_policies:
            analysis += f"""**相关政策文件** ({len(related_policies)} 条)：

"""
            for i, policy in enumerate(related_policies[:5], 1):
                title = policy.get('title', '无标题')
                department = policy.get('department', '')
                link = policy.get('link', '#')
                pub_time = policy.get('pub_time', '')
                
                analysis += f"{i}. **{title}**\n"
                if department:
                    analysis += f"   - 发文单位: {department}\n"
                if pub_time:
                    analysis += f"   - 发布时间: {pub_time}\n"
                analysis += f"   - 链接: [{link}]({link})\n\n"
        
        # 行动建议
        analysis += self._generate_action_suggestions(direction)
        
        return analysis
    
    def _get_confidence_desc(self, confidence):
        """获取置信度描述"""
        if confidence >= 9:
            return "（极高 - 政策明确，建议重点关注）"
        elif confidence >= 7:
            return "（高 - 方向清晰，可积极布局）"
        elif confidence >= 5:
            return "（中 - 概念性机会，需谨慎评估）"
        else:
            return "（低 - 不建议投入）"
    
    def _format_quantitative_scores(self, scores):
        """格式化量化评分"""
        certainty = scores.get('certainty', 0)
        return_rate = scores.get('return_rate_3y', {})
        risk = scores.get('risk_level', 0)
        urgency = scores.get('urgency', 0)
        barrier = scores.get('entry_barrier', 0)
        
        section = f"""**📊 量化评估**：

| 维度 | 评分 | 说明 |
|------|------|------|
| 确定性 | {certainty}/10 | {'极高' if certainty >= 9 else '高' if certainty >= 7 else '中' if certainty >= 5 else '低'} |
| 预期回报率（3年） | 保守{return_rate.get('conservative', 0)}% / 中性{return_rate.get('neutral', 0)}% / 乐观{return_rate.get('optimistic', 0)}% | 基于政策强度预测 |
| 风险等级 | {risk}/10 | {'高风险' if risk >= 7 else '中等风险' if risk >= 4 else '低风险'} |
| 紧迫性 | {urgency}/10 | {'立即行动' if urgency >= 8 else '3个月内' if urgency >= 5 else '长期关注'} |
| 进入门槛 | {barrier}/10 | {'高门槛' if barrier >= 7 else '中等门槛' if barrier >= 4 else '低门槛'} |

"""
        return section
    
    def _format_market_analysis(self, market):
        """格式化市场分析"""
        tam = market.get('tam_estimate', '未知')
        sam = market.get('sam_estimate', '未知')
        cagr = market.get('cagr_3y', 0)
        rationale = market.get('rationale', '')
        
        section = f"""**📈 市场容量分析**：

- **总市场规模（TAM）**: {tam}
- **目标市场（SAM）**: {sam}（中小企业可切入）
- **3年复合增长率（CAGR）**: {cagr}%
- **估算依据**: {rationale}

"""
        return section
    
    def _format_investment_plans(self, plans):
        """格式化投资方案"""
        section = """**💰 分级投资方案**：

"""
        
        for plan in plans:
            scale = plan.get('scale', '')
            scale_name = {'small': '小微方案', 'medium': '中型方案', 'large': '规模方案'}.get(scale, scale)
            budget = plan.get('budget_range', '')
            entry = plan.get('entry_point', '')
            timeline = plan.get('timeline', '')
            roi = plan.get('roi_expected', '')
            steps = plan.get('action_steps', [])
            
            section += f"""#### {scale_name}（{budget}）

- **切入点**: {entry}
- **时间周期**: {timeline}
- **预期ROI**: {roi}

**行动步骤**：
"""
            for step in steps:
                section += f"- {step}\n"
            section += "\n"
        
        return section
    
    def _format_risk_matrix(self, risk_matrix):
        """格式化风险矩阵"""
        section = """**⚠️ 风险评估矩阵**：

| 风险类型 | 等级 | 说明 |
|---------|------|------|
"""
        
        risk_types = {
            'policy_risk': '政策风险',
            'competition_risk': '竞争风险',
            'operation_risk': '运营风险',
            'compliance_risk': '合规风险'
        }
        
        for key, name in risk_types.items():
            if key in risk_matrix:
                risk_data = risk_matrix[key]
                level = risk_data.get('level', '未知')
                desc = risk_data.get('desc', '')
                
                # 等级emoji
                level_emoji = '🔴' if level == '极高' or level == '高' else '🟡' if level == '中' else '🟢'
                
                section += f"| {name} | {level_emoji} {level} | {desc} |\n"
        
        section += "\n"
        return section
    
    def _generate_deep_analysis(self, direction, news_list, policy_list):
        """
        使用LLM生成深度分析
        
        参数：
            direction: 投资方向数据
            news_list: 相关新闻列表
            policy_list: 相关政策列表
        """
        if not self.model_router:
            return None
        
        try:
            # 构建分析提示词
            prompt = self._build_deep_analysis_prompt(direction, news_list, policy_list)
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一位资深的投资分析师，擅长结合政策和市场动态进行深度分析。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            request = ModelRequest(
                prompt=prompt,
                messages=messages,
                metadata={
                    "temperature": self.config.get("llm.temperature.report", 0.4),
                    "max_tokens": 800,
                },
            )
            
            response = self.model_router.generate(self.model_task, request)
            return response.content.strip()
            
        except Exception as e:
            print(f"   ⚠️  深度分析生成失败: {e}")
            return None
    
    def _build_deep_analysis_prompt(self, direction, news_list, policy_list):
        """构建深度分析提示词"""
        name = direction.get('name', '')
        reason = direction.get('reason', '')
        
        # 构建新闻摘要
        news_summary = ""
        if news_list:
            news_summary = "\n相关新闻：\n"
            for i, news in enumerate(news_list[:3], 1):
                news_summary += f"{i}. {news.get('title', '')} ({news.get('source', '')})\n"
                snippet = news.get('snippet', '')
                if snippet:
                    news_summary += f"   摘要：{snippet[:100]}...\n"
        
        # 构建政策摘要
        policy_summary = ""
        if policy_list:
            policy_summary = "\n相关政策：\n"
            for i, policy in enumerate(policy_list[:3], 1):
                policy_summary += f"{i}. {policy.get('title', '')} ({policy.get('department', '')})\n"
        
        prompt = f"""请对以下投资方向进行深度分析（150字以内）：

投资方向：{name}

基础分析：{reason}
{news_summary}
{policy_summary}

请从以下角度简要分析：
1. 市场机会大小与可行性
2. 具体的落地方式或切入点
3. 需要注意的关键要素

要求：
- 简明扼要，150字以内
- 突出实操性
- 不要重复已有信息"""
        
        return prompt
    
    def _generate_action_suggestions(self, direction):
        """生成行动建议"""
        name = direction.get('name', '')
        urgency = direction.get('urgency', '中')
        threshold = direction.get('investment_threshold', '')
        keywords = direction.get('keywords', [])
        
        suggestions = """**行动建议**：

"""
        
        # 根据紧迫性给出建议
        if urgency == "高":
            suggestions += "- ⏰ **立即行动**：该方向时效性强，建议尽快评估可行性\n"
        elif urgency == "中":
            suggestions += "- 📅 **近期布局**：建议在1-2周内完成市场调研\n"
        else:
            suggestions += "- 🔍 **持续关注**：可作为中长期储备方向\n"
        
        # 投资门槛建议
        suggestions += f"- 💰 **资金规划**：预估门槛 {threshold}，建议准备10-20%的风险预留\n"
        
        # 调研建议
        suggestions += f"- 🔎 **深入调研**：重点搜索「{keywords[0] if keywords else name}」相关的成功案例与竞品\n"
        
        # 资源对接
        suggestions += "- 🤝 **资源对接**：联系行业协会、地方招商部门了解扶持政策细则\n"
        
        return suggestions
    
    def _level_to_risk_score(self, level: str) -> float:
        """将风险等级转换为评分"""
        level_map = {
            '极低': 1,
            '低': 3,
            '中': 5,
            '高': 7,
            '极高': 9
        }
        return level_map.get(level, 5)
    
    def _generate_risk_disclaimer(self):
        """生成风险提示"""
        return """## ⚠️ 风险提示

**重要声明**：

1. **投资有风险，入市需谨慎**：本报告仅供参考，不构成投资建议
2. **政策解读**：政策分析基于公开信息，具体执行以当地细则为准
3. **市场变化**：投资环境瞬息万变，建议持续跟踪最新动态
4. **尽职调查**：投资前请进行充分的市场调研和风险评估
5. **专业咨询**：重大投资决策建议咨询专业的法律和财务顾问

**数据来源**：
- 新闻联播官方内容
- 新华社、人民网等权威媒体
- 中国政府网政策文件

**生成方式**：
- AI辅助分析 + 人工审核
- 数据采集时间：报告生成当日

---

*本报告由AI自动生成，仅供学习研究使用。*"""
    
    def _generate_appendix(self, data):
        """生成附录"""
        metadata = data.get('_metadata', {})
        enrich_metadata = data.get('_enrichment_metadata', {})
        
        appendix = f"""## 📎 附录

### 报告元数据

- **分析模型**: {metadata.get('model', '未知')}
- **Token使用**: {metadata.get('tokens_used', 0)}
- **分析时间**: {metadata.get('timestamp', '未知')}
- **补充时间**: {enrich_metadata.get('timestamp', '未知')}
- **总请求数**: {enrich_metadata.get('total_requests', 0)}
- **安全模式**: {'已启用' if enrich_metadata.get('safe_mode') else '未启用'}

### 关键词索引

"""
        
        # 收集所有关键词
        all_keywords = set()
        directions = data.get('directions', [])
        for direction in directions:
            keywords = direction.get('keywords', [])
            all_keywords.update(keywords)
        
        if all_keywords:
            appendix += "、".join(sorted(all_keywords))
        else:
            appendix += "*无*"
        
        return appendix
    
    def save_report(self, report_content, date_str):
        """
        保存报告到文件
        
        参数：
            report_content: Markdown格式的报告内容
            date_str: 日期字符串 YYYYMMDD
        """
        paths = get_output_paths(self.config, date_str)
        reports_dir = paths['reports_dir']
        
        # 1. 保存Markdown
        md_path = os.path.join(reports_dir, f"report_{date_str}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"✅ Markdown报告: {md_path}")
        
        # 2. 生成并保存HTML
        if self.config.get('report.export_formats.html', True):
            html_path = self._export_html(report_content, date_str, reports_dir)
            if html_path:
                print(f"✅ HTML报告: {html_path}")
        
        # 3. 生成并保存PDF
        if self.config.get('report.export_formats.pdf', True):
            pdf_path = self._export_pdf(report_content, date_str, reports_dir)
            if pdf_path:
                print(f"✅ PDF报告: {pdf_path}")
        
        # 4. 生成并保存摘要
        if self.config.get('report.export_formats.summary', True):
            summary_path = self._generate_summary(report_content, date_str, reports_dir)
            if summary_path:
                print(f"✅ 摘要文件: {summary_path}")
    
    def _export_html(self, markdown_content, date_str, output_dir):
        """导出为HTML"""
        try:
            import markdown
            
            # Markdown转HTML
            html_body = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code', 'nl2br']
            )
            
            # 添加样式（带完整的打印媒体查询）
            html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投资机会分析报告 - {date_str}</title>
    <style>
        /* 屏幕显示样式 */
        body {{
            font-family: "Microsoft YaHei", "PingFang SC", "SimSun", "SimHei", 
                         "STHeiti", "Noto Sans CJK SC", sans-serif;
            line-height: 1.8;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 28px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            font-size: 22px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
            font-size: 18px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        blockquote {{
            border-left: 4px solid #e74c3c;
            padding-left: 15px;
            margin: 15px 0;
            color: #555;
            background-color: #fef5f5;
            padding: 10px 15px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Courier New", monospace;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: none;
            border-top: 2px solid #eee;
            margin: 30px 0;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        li {{
            margin: 8px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
        
        /* 打印样式优化 */
        @media print {{
            @page {{
                size: A4;
                margin: 2cm 1.5cm;
            }}
            
            body {{
                background-color: white;
                padding: 0;
                margin: 0;
                font-size: 11pt;
            }}
            
            .container {{
                box-shadow: none;
                border-radius: 0;
                padding: 0;
            }}
            
            /* 避免标题孤立 */
            h1, h2, h3, h4, h5, h6 {{
                page-break-after: avoid;
                page-break-inside: avoid;
            }}
            
            /* H1标题前强制分页 */
            h1 {{
                page-break-before: always;
            }}
            
            /* 第一个H1不分页 */
            h1:first-of-type {{
                page-break-before: avoid;
            }}
            
            /* 避免表格、图片、引用块跨页断裂 */
            table, img, blockquote, pre {{
                page-break-inside: avoid;
            }}
            
            /* 优化表格打印 */
            table {{
                font-size: 10pt;
            }}
            
            th {{
                background-color: #3498db !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            /* 链接显示URL */
            a[href]:after {{
                content: " (" attr(href) ")";
                font-size: 9pt;
                color: #666;
            }}
            
            /* 移除页面装饰 */
            .footer {{
                page-break-before: avoid;
                margin-top: 30px;
                font-size: 10pt;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>"""
            
            html_path = os.path.join(output_dir, f"report_{date_str}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
            
            return html_path
            
        except ImportError:
            print("   ⚠️  缺少 markdown 库，跳过HTML导出")
            print("   提示：运行 pip install Markdown 安装")
            return None
        except Exception as e:
            print(f"   ⚠️  HTML导出失败: {e}")
            return None
    
    def _export_pdf(self, markdown_content, date_str, output_dir):
        """导出为PDF - 优先使用WeasyPrint（中文支持最佳）"""
        # 方案1：优先使用 WeasyPrint（推荐，完美支持中文）
        pdf_path = self._export_pdf_weasyprint(markdown_content, date_str, output_dir)
        if pdf_path:
            return pdf_path
        
        # 方案2：尝试 xhtml2pdf（备选，中文支持有限）
        pdf_path = self._export_pdf_xhtml2pdf(markdown_content, date_str, output_dir)
        if pdf_path:
            return pdf_path
        
        # 方案3：两者都失败，提示用户使用浏览器打印
        print("   💡 PDF库未安装，建议使用以下方案：")
        print("      1. [推荐] 安装 WeasyPrint: pip install weasyprint")
        print('      2. 或使用浏览器打开HTML文件并"打印为PDF"')
        html_path = os.path.join(output_dir, f"report_{date_str}.html")
        print(f"      HTML文件: {html_path}")
        return None
    
    def _export_pdf_weasyprint(self, markdown_content, date_str, output_dir):
        """使用WeasyPrint导出PDF（推荐方案，完美支持中文）"""
        try:
            from weasyprint import HTML, CSS
            import markdown
            
            # 转换Markdown为HTML
            html_body = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code', 'nl2br']
            )
            
            # 优化的PDF样式（完整的中文字体支持 + 打印优化）
            html_string = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投资机会分析报告 - {date_str}</title>
    <style>
        /* 页面设置 */
        @page {{
            size: A4;
            margin: 2cm 1.5cm;
            
            /* 页眉页脚 */
            @top-center {{
                content: "投资机会分析报告";
                font-size: 9pt;
                color: #999;
            }}
            @bottom-right {{
                content: "第 " counter(page) " 页";
                font-size: 9pt;
                color: #999;
            }}
        }}
        
        /* 基础样式 */
        body {{
            font-family: "Microsoft YaHei", "PingFang SC", "SimSun", "SimHei", 
                         "STHeiti", "Noto Sans CJK SC", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            text-align: justify;
        }}
        
        /* 标题样式 */
        h1 {{
            color: #2c3e50;
            font-size: 24pt;
            font-weight: bold;
            border-bottom: 3px solid #3498db;
            padding-bottom: 8pt;
            margin-top: 0;
            page-break-after: avoid;
        }}
        
        h2 {{
            color: #34495e;
            font-size: 18pt;
            font-weight: bold;
            margin-top: 24pt;
            margin-bottom: 12pt;
            border-left: 4px solid #3498db;
            padding-left: 12pt;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #555;
            font-size: 14pt;
            font-weight: bold;
            margin-top: 18pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
        }}
        
        /* 段落 */
        p {{
            margin: 8pt 0;
            text-indent: 0;
        }}
        
        /* 表格样式 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12pt 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            padding: 8pt 10pt;
            text-align: left;
            font-weight: bold;
        }}
        
        td {{
            border: 1px solid #ddd;
            padding: 8pt 10pt;
            text-align: left;
        }}
        
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        /* 引用块 */
        blockquote {{
            border-left: 4px solid #e74c3c;
            background-color: #fef5f5;
            padding: 10pt 15pt;
            margin: 12pt 0;
            font-style: italic;
            color: #555;
            page-break-inside: avoid;
        }}
        
        /* 列表 */
        ul, ol {{
            margin: 8pt 0;
            padding-left: 24pt;
        }}
        
        li {{
            margin: 6pt 0;
            line-height: 1.5;
        }}
        
        /* 链接 */
        a {{
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
        }}
        
        /* 分隔线 */
        hr {{
            border: none;
            border-top: 2px solid #eee;
            margin: 20pt 0;
        }}
        
        /* 代码 */
        code {{
            background-color: #f4f4f4;
            padding: 2pt 6pt;
            border-radius: 3pt;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 10pt;
        }}
        
        /* 强调 */
        strong {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        em {{
            font-style: italic;
            color: #555;
        }}
        
        /* 图片样式 */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15pt auto;
            page-break-inside: avoid;
            border: 1px solid #ddd;
            border-radius: 4pt;
            padding: 5pt;
            background-color: white;
        }}
        
        /* 避免孤立标题和列表项 */
        h1, h2, h3, h4, h5, h6 {{
            page-break-after: avoid;
        }}
        
        /* 避免表格和块引用跨页断裂 */
        table, blockquote, pre {{
            page-break-inside: avoid;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
            
            # 使用WeasyPrint生成PDF，指定base_url让它能找到相对路径的图片
            # base_url必须是绝对路径，且以file://开头
            import os
            from pathlib import Path
            
            # 转换为绝对路径
            abs_output_dir = os.path.abspath(output_dir)
            base_url = Path(abs_output_dir).as_uri() + '/'
            pdf_path = os.path.join(output_dir, f"report_{date_str}.pdf")
            
            print(f"   📂 PDF生成目录: {output_dir}")
            print(f"   🔗 Base URL: {base_url}")
            
            try:
                HTML(string=html_string, base_url=base_url).write_pdf(pdf_path)
                
                # 验证PDF文件是否正常生成
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    return pdf_path
                else:
                    print(f"   ⚠️  PDF文件生成失败或文件为空")
                    return None
                    
            except Exception as pdf_error:
                print(f"   ⚠️  PDF生成出错: {pdf_error}")
                import traceback
                traceback.print_exc()
                
                # 删除空的或损坏的PDF文件
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                return None
            
        except ImportError:
            # WeasyPrint未安装
            return None
        except Exception as e:
            print(f"   ⚠️  WeasyPrint导出失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _export_pdf_xhtml2pdf(self, markdown_content, date_str, output_dir):
        """使用xhtml2pdf导出PDF（备选方案，中文支持有限）"""
        try:
            from xhtml2pdf import pisa
            import markdown
            
            # 转换Markdown为HTML
            html_body = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code']
            )
            
            # 获取字体配置
            font_path = self.config.get('report.pdf_font_path', '')
            font_face = ""
            
            # 如果配置了字体文件且存在，则使用
            if font_path and os.path.exists(font_path):
                font_face = f"""
        @font-face {{
            font-family: CustomFont;
            src: url("{font_path}");
        }}"""
            
            # xhtml2pdf的HTML模板（简化样式，避免不支持的CSS）
            html_for_pdf = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <style>
        {font_face}
        
        @page {{
            size: A4;
            margin: 2cm 1.5cm;
        }}
        
        body {{
            font-family: {'CustomFont,' if font_face else ''} "SimSun", "Microsoft YaHei", "SimHei", sans-serif;
            line-height: 1.6;
            font-size: 12pt;
            color: #333;
        }}
        
        h1 {{
            color: #2c3e50;
            font-size: 24pt;
            margin-top: 0;
        }}
        
        h2 {{
            color: #34495e;
            font-size: 18pt;
            margin-top: 20pt;
        }}
        
        h3 {{
            color: #555;
            font-size: 14pt;
            margin-top: 16pt;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 10pt 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 8pt;
            text-align: left;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
        }}
        
        blockquote {{
            border-left: 3px solid #e74c3c;
            padding-left: 10pt;
            margin-left: 0;
            color: #555;
        }}
        
        ul, ol {{
            margin: 8pt 0;
            padding-left: 20pt;
        }}
        
        li {{
            margin: 5pt 0;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
            
            pdf_path = os.path.join(output_dir, f"report_{date_str}.pdf")
            
            with open(pdf_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_for_pdf.encode('utf-8'),
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            if pisa_status.err:
                raise Exception("xhtml2pdf生成出现错误")
            
            print("   ⚠️  使用xhtml2pdf生成（中文显示可能不完整）")
            return pdf_path
            
        except ImportError:
            # xhtml2pdf未安装
            return None
        except Exception as e:
            print(f"   ⚠️  xhtml2pdf导出失败: {e}")
            return None
    
    def _generate_summary(self, report_content, date_str, output_dir):
        """生成文字摘要"""
        try:
            # 提取关键信息生成摘要
            lines = report_content.split('\n')
            
            summary_lines = []
            summary_lines.append(f"投资机会分析报告摘要 - {date_str}")
            summary_lines.append("=" * 60)
            summary_lines.append("")
            
            # 提取执行摘要部分
            in_summary = False
            for line in lines:
                if '## 📋 执行摘要' in line:
                    in_summary = True
                    continue
                if in_summary:
                    if line.startswith('## '):
                        break
                    if line.strip() and not line.startswith('#'):
                        summary_lines.append(line)
            
            summary_lines.append("")
            summary_lines.append("=" * 60)
            summary_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary_lines.append("")
            summary_lines.append("详细报告请查看:")
            summary_lines.append(f"- Markdown: report_{date_str}.md")
            summary_lines.append(f"- HTML: report_{date_str}.html")
            summary_lines.append(f"- PDF: report_{date_str}.pdf")
            
            summary_path = os.path.join(output_dir, f"summary_{date_str}.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_lines))
            
            return summary_path
            
        except Exception as e:
            print(f"   ⚠️  摘要生成失败: {e}")
            return None


# ========== 测试函数 ==========

def test_report_generator(date_str):
    """测试报告生成器"""
    print("="*60)
    print(f"🧪 测试报告生成器 - {date_str}")
    print("="*60)
    
    # 加载补充后的数据
    from utils.path_helper import get_output_paths
    config = get_config()
    paths = get_output_paths(config, date_str)
    
    enriched_file = os.path.join(paths['data_dir'], f"enriched_{date_str}.json")
    
    try:
        with open(enriched_file, 'r', encoding='utf-8') as f:
            enriched_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 未找到文件: {enriched_file}")
        print("   请先运行完整流程生成补充数据")
        return
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 初始化生成器
    generator = ReportGenerator()
    
    # 生成报告
    report = generator.generate_full_report(enriched_data, date_str)
    
    # 保存报告
    generator.save_report(report, date_str)
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    # 测试
    from datetime import date
    today = date.today().strftime("%Y%m%d")
    test_report_generator(today)

