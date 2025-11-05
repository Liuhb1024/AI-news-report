"""
LLM分析器模块
用于从新闻联播中提取投资方向
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

class LLMAnalyzer:
    """LLM分析器：使用DeepSeek提取投资方向"""
    
    def __init__(self, api_key=None, model="deepseek-chat"):
        """
        初始化分析器
        
        参数：
            api_key: API密钥（可选，默认从环境变量读取）
            model: 使用的模型，默认 deepseek-chat
        """
        # 获取API密钥
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "❌ 错误：未找到API密钥！<br />"
                "请确保 .env 文件存在，并包含 OPENAI_API_KEY=你的密钥"
            )
        
        self.model = model
        
        # 初始化DeepSeek客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        print(f"✅ LLM分析器初始化成功")
        print(f"   模型: {self.model}")
        print(f"   密钥: {self._mask_api_key()}")
    
    def _mask_api_key(self):
        """脱敏显示API密钥"""
        if len(self.api_key) > 12:
            return f"{self.api_key[:8]}...{self.api_key[-4:]}"
        return "***"
    
    def extract_investment_directions(self, news_data):
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
        
        返回：
            dict: 分析结果，包含投资方向
        """
        print("<br />" + "="*60)
        print("🤖 开始AI分析...")
        print("="*60)
        
        # 格式化新闻内容
        news_text = self._format_news(news_data)
        
        # 构建提示词
        prompt = self._build_prompt_v2(news_text)
        
        # 调用LLM
        try:
            print("📤 正在发送请求到DeepSeek...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位资深的政策分析师和投资顾问，擅长从新闻中提取投资机会。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 降低随机性
                max_tokens=4000   # 限制输出长度
            )
            
            print("📥 收到响应，正在解析...")
            
            # 提取返回内容
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            result = self._parse_response(content)
            
            # 添加元数据
            result['_metadata'] = {
                'model': self.model,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
            print(f"✅ 分析完成！使用了约 {result['_metadata']['tokens_used']} tokens")
            
            return result
            
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
            # 清理内容中的<br />标签
            content = news['content'].replace('<br />', '<br />')
            
            formatted.append(
                f"【新闻{news['index']}】{news['title']}<br />"
                f"{content}<br />"
            )
        
        return "<br />".join(formatted)
    
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
    
    def save_analysis(self, result, date_str):
        """
        保存分析结果到文件
        
        参数：
            result: 分析结果
            date_str: 日期字符串（YYYYMMDD）
        """
        if not result:
            print("❌ 没有分析结果可保存")
            return
        
        filename = f"analysis_{date_str}.json"
        
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
