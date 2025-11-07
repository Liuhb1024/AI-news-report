"""
数据补充模块 - 简化版
为投资方向补充权威资讯和政策数据
"""

import json
from datetime import datetime
from typing import Dict, List
from config import get_config


class SafeDataEnrichment:
    """安全的数据补充器（简化版）"""
    
    def __init__(self, config=None, date_str=None, safe_mode=True):
        """
        初始化数据补充器
        
        参数：
            config: 配置对象
            date_str: 日期字符串
            safe_mode: 安全模式（暂未实现网络爬取功能）
        """
        self.config = config or get_config()
        self.date_str = date_str
        self.safe_mode = safe_mode
        self.request_count = {}
    
    def enrich_all_directions(self, analysis_data: Dict) -> Dict:
        """
        为所有投资方向补充数据（简化版 - 不进行实际爬取）
        
        参数：
            analysis_data: 分析数据
            
        返回：
            enriched_data: 补充后的数据
        """
        print("\n" + "="*60)
        print("📊 数据补充（简化模式）")
        print("="*60)
        print("   ℹ️  当前版本不进行网络数据补充")
        print("   💡 如需补充功能，可在此模块中实现")
        
        directions = analysis_data.get('directions', [])
        
        if not directions:
            print("   ⚠️  没有投资方向需要补充")
            return analysis_data
        
        # 为每个方向添加空的补充数据结构
        enriched_directions = []
        for i, direction in enumerate(directions, 1):
            print(f"\n   方向 {i}/{len(directions)}: {direction['name']}")
            
            # 添加空的补充数据结构
            enriched = direction.copy()
            enriched['recent_news'] = []  # 权威资讯（空）
            enriched['related_policies'] = []  # 相关政策（空）
            enriched['keyword_analysis'] = {
                'main_keyword': direction.get('name'),
                'related_keywords': direction.get('keywords', []),
                'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'note': '简化模式：未进行实际数据补充'
            }
            
            enriched_directions.append(enriched)
        
        # 更新结果
        result = analysis_data.copy()
        result['directions'] = enriched_directions
        result['_enrichment_metadata'] = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_directions': len(enriched_directions),
            'safe_mode': self.safe_mode,
            'sources_used': [],  # 简化模式不使用外部数据源
            'total_requests': 0,
            'mode': 'simplified'
        }
        
        print("\n✅ 数据结构补充完成")
        return result
    
    def save_enriched_data(self, enriched_data: Dict, date_str: str):
        """
        保存补充后的数据
        
        参数：
            enriched_data: 补充后的数据
            date_str: 日期字符串
        """
        import os
        from utils.path_helper import get_output_paths
        
        paths = get_output_paths(self.config, date_str)
        filename = os.path.join(paths['data_dir'], f"enriched_{date_str}.json")
        
        # 保存JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 补充数据已保存到: {filename}")
        
        # 打印统计
        self._print_enrichment_stats(enriched_data)
    
    def _print_enrichment_stats(self, data: Dict):
        """打印补充数据统计"""
        print("\n" + "="*60)
        print("📊 数据补充统计")
        print("="*60)
        
        directions = data.get('directions', [])
        total_news = sum(len(d.get('recent_news', [])) for d in directions)
        total_policies = sum(len(d.get('related_policies', [])) for d in directions)
        
        print(f"投资方向数: {len(directions)}")
        print(f"权威资讯: {total_news} 条")
        print(f"相关政策: {total_policies} 条")
        print(f"模式: 简化模式（不爬取外部数据）")
        print()


# 兼容性：保留旧的函数接口
def load_analysis_result(date_str):
    """加载AI分析结果"""
    from config import get_config
    from utils.path_helper import get_output_paths
    import os
    
    config = get_config()
    paths = get_output_paths(config, date_str)
    filename = os.path.join(paths['data_dir'], f"analysis_{date_str}.json")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ 未找到文件: {filename}")
        return None
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

