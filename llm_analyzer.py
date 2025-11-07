"""
LLM分析器模块
用于从新闻联播中提取投资方向
"""

import json
import re
from datetime import datetime
from typing import Optional

from config import get_config
from models import ModelRequest, ModelRouter, ModelError

class LLMAnalyzer:
    """LLM分析器：通过模型路由提取投资方向"""
    
    def __init__(self, model=None, config=None, model_router: Optional[ModelRouter] = None):
        """
        初始化分析器
        
        参数：
            model: 使用的模型代号（可选，默认从配置读取）
            config: 配置对象（可选，默认使用全局配置）
            model_router: 模型路由器，负责选择具体模型
        """
        # 获取配置
        self.config = config or get_config()
        
        if not model_router:
            raise ValueError("LLMAnalyzer 需要提供 model_router")

        self.model_router = model_router
        self.model_task = "policy_analysis"
        self.model = model or self.config.get("llm.model", "deepseek-chat")
        print("✅ LLM分析器初始化成功 (使用模型路由)")
    
    def extract_investment_directions(self, news_data, use_enhanced=False):
        """
        从新闻数据中提取投资方向
        
        参数：
            news_data: 爬取的新闻列表，格式：
                [
                    {
                        "index": 1,
                        "title": "标题",
                        "content": "内容"
                    },
                    ...
                ]
            use_enhanced: 已废弃的参数，保留以兼容旧代码
        
        返回：
            dict: 分析结果，包含投资方向
        """
        print("<br />" + "="*60)
        print("🤖 开始AI深度分析...")
        print("="*60)
        
        # 格式化新闻内容
        news_text = self._format_news(news_data)
        
        # 构建提示词
        prompt = self._build_prompt_v2(news_text)
        
        # 调用LLM
        try:
            print("📤 正在发送请求到模型服务...")
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一位资深的政策分析师和投资顾问，擅长从新闻中提取投资机会。"
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
                    "temperature": self.config.get("llm.temperature.analysis", 0.3),
                    "max_tokens": self.config.get("llm.max_tokens.analysis", 4000),
                },
            )

            response = self.model_router.generate(self.model_task, request)
            content = response.content
            provider = response.provider
            usage_info = response.usage or {}
            print("📥 收到响应，正在解析...")

            # 尝试解析JSON
            result = self._parse_response(content)
            
            # 如果LLM没有生成policy_insights，自动补充
            if 'policy_insights' not in result:
                result = self._enhance_with_policy_insights(result)
            
            # 添加元数据
            result['_metadata'] = {
                'model': provider,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tokens_used': usage_info.get('total_tokens', 0) if isinstance(usage_info, dict) else usage_info,
            }
            
            print(f"✅ 分析完成！使用了约 {result['_metadata']['tokens_used']} tokens")
            
            return result
            
        except ModelError as e:
            print(f"❌ 模型路由调用失败: {e}")
            return None

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"原始响应: {content[:500]}...")
            return None
            
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return None
    
    def _format_news(self, news_data):
        """将新闻数据格式化为文本"""
        formatted = []

        for news in news_data:
            if not isinstance(news, dict):
                continue

            index = news.get('index', '')
            title = news.get('title', '').strip()
            raw_content = news.get('content', '') or ''

            # 统一清洗 HTML 换行与标签
            content = re.sub(r'<br\s*/?>', '\n', raw_content, flags=re.IGNORECASE)
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+\n', '\n', content)
            content = re.sub(r'\n{2,}', '\n', content).strip()

            formatted.append(
                f"【新闻{index}】{title}\n{content}\n"
            )

        return "\n".join(formatted)
    
    def _build_prompt(self, news_text):
        """构建提示词"""
        prompt = f"""请分析以下新闻联播内容，提取最有价值的投资方向。

【新闻内容】
{news_text}

【分析要求】
1. 仔细阅读所有新闻，识别政策信号
2. 提取3-5个最具投资价值的方向
3. 每个方向需满足：
   - 有明确的政策支持或资金投入
   - 适合中小创业者（资金门槛≤500万）
   - 有具体的行业指向
   - 具有时效性

【输出格式】
必须严格按以下JSON格式输出（不要有任何其他文字）：

{{
  "date": "新闻日期（从标题推断）",
  "summary": "今日政策基调总结（50字内）",
  "key_policies": ["核心政策1", "核心政策2"],
  "directions": [
    {{
      "name": "投资方向名称（6-8字）",
      "confidence": 8,
      "category": "行业分类（如：科技/消费/制造/医疗/农业等）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "policy_signal": "从新闻中摘录的政策原文（30字内）",
      "policy_strength": "高/中/低",
      "urgency": "高/中/低",
      "investment_threshold": "≤50万/50-100万/100-500万/>500万",
      "search_queries": [
        "搜索该方向资讯的关键词1 投资",
        "搜索该方向资讯的关键词2 融资 2024",
        "搜索该方向政策的关键词3 政策"
      ],
      "reason": "选择理由（100字内，需引用新闻中的具体内容）"
    }}
  ]
}}

【评分说明】
confidence置信度（1-10分）：
- 9-10分：政策明确提及金额、时间、具体目标
- 7-8分：政策方向明确，有实质措施
- 5-6分：仅提及概念，细节较少
- 1-4分：不推荐（不输出）

【注意】
- 如果某天没有明显投资机会，directions可为空数组
- 只输出JSON，不要有任何解释文字
- reason必须引用新闻中的具体表述

现在开始分析："""
        
        return prompt
    
    def _build_prompt_v2(self, news_text):
        """构建用于抽取投资方向的专业提示词（v2）"""
        prompt = f"""
请基于以下新闻联播文本，识别当日最具投资价值的方向，并仅以严格 JSON 返回结果。

【新闻原文】
{news_text}

【任务要求】
- 从政策强度、资金承诺、时间表、产业指向、执行主体等维度判断投资机会；
- 产出 3–5 个方向，若不满足条件可少于 3 个；
- 每个方向需可落地、适合中小创业者（资金门槛 ≤ 500 万），并标注关键词与检索词；
- 重要：reason 字段需引用新闻中的具体表述（可精简转述，但必须可回溯）。

【输出格式（只输出 JSON，无任何额外文字）】
{{
  "date": "YYYY-MM-DD 或从标题推断",
  "summary": "50 字内的政策基调概述",
  "key_policies": ["核心政策1", "核心政策2"],
  
  "policy_insights": {{
    "overall_tone": "积极进取/稳中求进/谨慎观望",
    "key_signals": [
      {{
        "topic": "主题（如：海南自贸港）",
        "strength_score": 9.5,
        "hidden_message": "政策潜台词和深层含义（50字内）",
        "urgency_indicator": "时间紧迫性描述"
      }}
    ]
  }},
  
  "directions": [
    {{
      "name": "方向名（4-12字）",
      "confidence": 8,
      "category": "行业分类（如 科技/消费/制造/医疗/农业/能源/基建 等）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "policy_signal": "摘录的政策原文或高度贴近原文的精简表述（≤30字）",
      "policy_strength": "高/中/低",
      "urgency": "高/中/低",
      "investment_threshold": "<50 / 50-100 / 100-500 / >500（单位：万元）",
      "search_queries": [
        "关键词 投资",
        "关键词 融资 YYYY",
        "关键词 政策"
      ],
      "reason": "≤200字，明确引用新闻要点，说明机会判断逻辑与可落地性"
    }}
  ]
}}

【评分参考】
- 9–10：资金、时间、目标明确且近期落地
- 7–8：方向清晰，有实质举措
- 5–6：概念性为主，执行细节弱
- ≤4：不输出

仅输出 JSON。
"""

        return prompt

    def _parse_response(self, content):
        """解析LLM返回的内容"""
        # 尝试提取JSON
        # 有时LLM会在JSON前后加一些文字，需要清理
        
        # 查找第一个 { 和最后一个 }
        start = content.find('{')
        end = content.rfind('}')
        
        if start == -1 or end == -1:
            raise json.JSONDecodeError("未找到有效的JSON", content, 0)
        
        json_str = content[start:end+1]
        
        # 解析JSON
        result = json.loads(json_str)
        
        return result
    
    def _enhance_with_policy_insights(self, result):
        """为分析结果自动生成政策玄机解读"""
        directions = result.get('directions', [])
        
        if not directions:
            return result
        
        # 生成key_signals
        key_signals = []
        for direction in directions[:3]:  # 取前3个最重要的方向
            confidence = direction.get('confidence', 5)
            urgency = direction.get('urgency', '中')
            policy_strength = direction.get('policy_strength', '中')
            
            # 根据置信度和紧迫性生成潜台词
            if confidence >= 9 and urgency == '高':
                message = "政策进入冲刺期，配套措施将密集出台，建议立即布局"
            elif confidence >= 8 and urgency == '高':
                message = "政策方向明确且紧迫，市场机会窗口已打开，适合积极跟进"
            elif confidence >= 8:
                message = "政策方向明确，建议提前准备，等待配套细则"
            elif confidence >= 7:
                message = "政策信号清晰，可稳步推进，持续关注"
            else:
                message = "政策处于培育期，建议持续观察"
            
            # 生成紧迫性指标
            urgency_map = {
                '高': '明确时间节点或短期窗口期',
                '中': '中期规划，需在半年内布局',
                '低': '长期趋势，可从容准备'
            }
            urgency_indicator = urgency_map.get(urgency, '观察期')
            
            # 计算强度分数
            strength_score = confidence * 0.8
            if policy_strength == '高':
                strength_score = min(10, strength_score + 1.5)
            elif policy_strength == '低':
                strength_score = max(1, strength_score - 1.5)
            
            signal = {
                'topic': direction.get('name', '未知'),
                'strength_score': round(strength_score, 1),
                'hidden_message': message,
                'urgency_indicator': urgency_indicator
            }
            key_signals.append(signal)
        
        # 判断整体基调
        avg_confidence = sum(d.get('confidence', 0) for d in directions) / len(directions)
        if avg_confidence >= 8:
            overall_tone = '积极进取'
        elif avg_confidence >= 6:
            overall_tone = '稳中求进'
        else:
            overall_tone = '谨慎观望'
        
        # 添加policy_insights
        result['policy_insights'] = {
            'overall_tone': overall_tone,
            'key_signals': key_signals
        }
        
        print("   💡 已自动生成政策玄机解读")
        return result
    
    def save_analysis(self, result, date_str):
        """保存分析结果"""
        if not result:
            print("❌ 没有分析结果可保存")
            return
        
        import os
        from utils.path_helper import get_output_paths
        paths = get_output_paths(self.config, date_str)
        
        filename = os.path.join(paths['data_dir'], f"analysis_{date_str}.json")
        
        # 保存JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"<br />✅ 分析结果已保存到: {filename}")
        
        # 打印摘要
        self._print_summary(result)
    
    def _print_summary(self, result):
        """打印分析摘要"""
        print("<br />" + "="*60)
        print("📊 分析摘要")
        print("="*60)
        
        print(f"日期: {result.get('date', '未知')}")
        print(f"政策基调: {result.get('summary', '无')}")
        
        if result.get('key_policies'):
            print(f"<br />核心政策:")
            for policy in result['key_policies']:
                print(f"  • {policy}")
        
        directions = result.get('directions', [])
        
        if not directions:
            print("<br />⚠️  未识别出明确的投资方向")
            return
        
        print(f"<br />识别出 {len(directions)} 个投资方向：<br />")
        
        for i, direction in enumerate(directions, 1):
            print(f"{i}. {direction['name']}")
            print(f"   类别: {direction.get('category', '未知')}")
            print(f"   置信度: {direction['confidence']}/10")
            print(f"   政策强度: {direction.get('policy_strength', '未知')}")
            print(f"   紧迫性: {direction['urgency']}")
            print(f"   投资门槛: {direction.get('investment_threshold', '未知')}")
            print(f"   政策依据: {direction.get('policy_signal', '无')[:50]}...")
            print(f"   理由: {direction['reason'][:80]}...")
            print()

# 测试函数
def test_analyzer():
    """测试LLM分析器"""
    print("="*60)
    print("🧪 测试DeepSeek连接")
    print("="*60)
    
    try:
        # 初始化分析器
        analyzer = LLMAnalyzer(model="deepseek-chat")
        
        # 模拟简单测试
        test_response = analyzer.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "请回复：测试成功"}
            ],
            max_tokens=50
        )
        
        print(f"<br />✅ DeepSeek连接成功！")
        print(f"回复: {test_response.choices[0].message.content}")
        print(f"使用tokens: {test_response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"<br />❌ 测试失败: {e}")
        print("<br />请检查：")
        print("1. .env 文件是否存在")
        print("2. API密钥是否正确")
        print("3. 网络连接是否正常")
        return False

if __name__ == "__main__":
    # 直接运行此文件时，执行测试
    test_analyzer()
