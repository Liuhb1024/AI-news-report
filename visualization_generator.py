"""
可视化生成器模块
生成各类图表用于报告增强
支持两种图表引擎：ECharts（推荐）和 Matplotlib（备选）
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

# 尝试导入ECharts生成器
try:
    from echarts_generator import EChartsGenerator
    ECHARTS_AVAILABLE = True
except ImportError:
    ECHARTS_AVAILABLE = False
    print("   ⚠️  ECharts未安装，将使用Matplotlib")

# Matplotlib后备方案
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体
def setup_chinese_font():
    """配置matplotlib中文字体"""
    # Windows系统字体路径（优先使用）
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",    # 宋体
        "C:/Windows/Fonts/simhei.ttf",    # 黑体
        "fonts/msyh.ttc",                 # 项目字体目录
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # 使用FontProperties获取字体名称
                font_prop = fm.FontProperties(fname=font_path)
                font_name = font_prop.get_name()
                
                # 配置matplotlib使用该字体
                plt.rcParams['font.sans-serif'] = [font_name, 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                plt.rcParams['font.size'] = 10
                
                print(f"   ✅ 已配置中文字体: {font_name}")
                return
            except Exception as e:
                continue
    
    # 如果都失败，尝试使用系统默认中文字体
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        print("   ⚠️  使用系统默认中文字体（可能显示不完整）")
    except:
        print("   ⚠️  未找到中文字体，图表文字可能显示为方框")


class VisualizationGenerator:
    """可视化生成器（支持ECharts和Matplotlib两种引擎）"""
    
    def __init__(self, output_dir: str = None, engine: str = "auto"):
        """
        初始化可视化生成器
        
        参数:
            output_dir: 图表输出目录
            engine: 图表引擎选择
                - "auto": 自动选择（优先ECharts，不可用则降级到Matplotlib）
                - "echarts": 强制使用ECharts
                - "matplotlib": 强制使用Matplotlib
        """
        self.output_dir = output_dir or "outputs/charts"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 选择图表引擎
        if engine == "echarts":
            if not ECHARTS_AVAILABLE:
                raise RuntimeError("ECharts不可用，请安装: pip install pyecharts snapshot-selenium")
            self.engine = "echarts"
            self.echarts_gen = EChartsGenerator(output_dir=self.output_dir)
            print("   📊 使用图表引擎: ECharts")
        elif engine == "matplotlib":
            self.engine = "matplotlib"
            setup_chinese_font()
            plt.style.use('seaborn-v0_8-darkgrid')
            print("   📊 使用图表引擎: Matplotlib")
        else:  # auto
            if ECHARTS_AVAILABLE:
                self.engine = "echarts"
                self.echarts_gen = EChartsGenerator(output_dir=self.output_dir)
                print("   📊 使用图表引擎: ECharts（现代化图表）")
            else:
                self.engine = "matplotlib"
                setup_chinese_font()
                plt.style.use('seaborn-v0_8-darkgrid')
                print("   📊 使用图表引擎: Matplotlib（备选方案）")
        
    def generate_radar_chart(self, 
                            scores: Dict[str, float], 
                            title: str,
                            filename: str) -> str:
        """
        生成雷达图（用于投资方向多维度评分）
        
        参数:
            scores: 评分字典，如 {"确定性": 9, "回报率": 8, "风险": 4, "紧迫性": 10, "门槛": 3}
            title: 图表标题
            filename: 保存文件名
            
        返回:
            str: 图片文件路径
        """
        # 根据引擎选择实现
        if self.engine == "echarts":
            return self.echarts_gen.generate_radar_chart(scores, title, filename)
        
        # Matplotlib实现
        labels = list(scores.keys())
        values = list(scores.values())
        
        # 闭合雷达图
        values += values[:1]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        ax.plot(angles, values, 'o-', linewidth=2, label=title, color='#3498db')
        ax.fill(angles, values, alpha=0.25, color='#3498db')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=12)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_title(title, size=16, weight='bold', pad=20)
        ax.grid(True)
        ax.legend(loc='upper right')
        
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def generate_policy_strength_chart(self,
                                      policy_signals: List[Dict],
                                      filename: str) -> str:
        """
        生成政策强度对比柱状图
        
        参数:
            policy_signals: 政策信号列表，如 [{"topic": "海南自贸港", "strength_score": 9.5}, ...]
            filename: 保存文件名
            
        返回:
            str: 图片文件路径
        """
        # 根据引擎选择实现
        if self.engine == "echarts":
            return self.echarts_gen.generate_policy_strength_chart(policy_signals, filename)
        
        # Matplotlib实现
        topics = [signal.get('topic', '') for signal in policy_signals]
        scores = [signal.get('strength_score', 0) for signal in policy_signals]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#e74c3c' if s >= 8 else '#f39c12' if s >= 6 else '#3498db' for s in scores]
        
        bars = ax.barh(topics, scores, color=colors, alpha=0.8)
        
        # 添加数值标签
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(score + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{score:.1f}', 
                   va='center', fontsize=11, weight='bold')
        
        ax.set_xlabel('政策强度评分', fontsize=12)
        ax.set_title('政策信号强度对比', fontsize=14, weight='bold', pad=15)
        ax.set_xlim(0, 10.5)
        ax.grid(axis='x', alpha=0.3)
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#e74c3c', alpha=0.8, label='强信号 (≥8分)'),
            Patch(facecolor='#f39c12', alpha=0.8, label='中等信号 (6-8分)'),
            Patch(facecolor='#3498db', alpha=0.8, label='弱信号 (<6分)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def generate_market_forecast_chart(self,
                                      years: List[str],
                                      tam: List[float],
                                      sam: List[float],
                                      title: str,
                                      filename: str) -> str:
        """
        生成市场规模预测图（TAM/SAM）
        
        参数:
            years: 年份列表，如 ["2025", "2026", "2027"]
            tam: 总市场规模列表（亿元）
            sam: 可服务市场列表（亿元）
            title: 图表标题
            filename: 保存文件名
            
        返回:
            str: 图片文件路径
        """
        # 根据引擎选择实现
        if self.engine == "echarts":
            return self.echarts_gen.generate_market_forecast_chart(years, tam, sam, title, filename)
        
        # Matplotlib实现
        x = np.arange(len(years))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars1 = ax.bar(x - width/2, tam, width, label='总市场(TAM)', 
                      color='#3498db', alpha=0.8)
        bars2 = ax.bar(x + width/2, sam, width, label='目标市场(SAM)', 
                      color='#2ecc71', alpha=0.8)
        
        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}亿',
                       ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('年份', fontsize=12)
        ax.set_ylabel('市场规模（亿元）', fontsize=12)
        ax.set_title(title, fontsize=14, weight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def generate_risk_matrix(self,
                            risks: Dict[str, Dict],
                            filename: str) -> str:
        """
        生成风险评估矩阵热力图
        
        参数:
            risks: 风险字典，如 {
                "政策风险": {"level": "中", "score": 5},
                "竞争风险": {"level": "高", "score": 7},
                ...
            }
            filename: 保存文件名
            
        返回:
            str: 图片文件路径
        """
        # 根据引擎选择实现
        if self.engine == "echarts":
            return self.echarts_gen.generate_risk_matrix(risks, filename)
        
        # Matplotlib实现
        risk_names = list(risks.keys())
        risk_scores = [risks[name].get('score', self._level_to_score(risks[name].get('level', '中'))) 
                      for name in risk_names]
        
        fig, ax = plt.subplots(figsize=(8, len(risk_names) * 0.8 + 2))
        
        # 创建颜色映射
        colors = plt.cm.RdYlGn_r(np.array(risk_scores) / 10)
        
        bars = ax.barh(risk_names, risk_scores, color=colors, alpha=0.8)
        
        # 添加数值和等级标签
        for i, (bar, score, name) in enumerate(zip(bars, risk_scores, risk_names)):
            level = risks[name].get('level', self._score_to_level(score))
            ax.text(score + 0.2, bar.get_y() + bar.get_height()/2, 
                   f'{level} ({score:.1f})', 
                   va='center', fontsize=11)
        
        ax.set_xlabel('风险评分 (0=低, 10=高)', fontsize=12)
        ax.set_title('风险评估矩阵', fontsize=14, weight='bold', pad=15)
        ax.set_xlim(0, 11)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def generate_investment_comparison(self,
                                      directions: List[Dict],
                                      filename: str) -> str:
        """
        生成投资方向对比气泡图
        
        参数:
            directions: 投资方向列表，每个包含 quantitative_scores
            filename: 保存文件名
            
        返回:
            str: 图片文件路径
        """
        # 根据引擎选择实现
        if self.engine == "echarts":
            return self.echarts_gen.generate_investment_comparison(directions, filename)
        
        # Matplotlib实现
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for direction in directions:
            name = direction.get('name', '')
            scores = direction.get('quantitative_scores', {})
            
            certainty = scores.get('certainty', 5)
            risk = scores.get('risk_level', 5)
            urgency = scores.get('urgency', 5)
            
            # 气泡大小代表紧迫性
            size = urgency * 100
            
            # 颜色代表风险等级
            color_map = plt.cm.RdYlGn_r(risk / 10)
            
            ax.scatter(certainty, 10 - risk, s=size, alpha=0.6, c=[color_map])
            ax.annotate(name, (certainty, 10 - risk), 
                       fontsize=10, ha='center', va='bottom')
        
        ax.set_xlabel('确定性 →', fontsize=12)
        ax.set_ylabel('安全性 (低风险) →', fontsize=12)
        ax.set_title('投资机会对比分析（气泡大小=紧迫性）', fontsize=14, weight='bold', pad=15)
        ax.set_xlim(0, 11)
        ax.set_ylim(0, 11)
        ax.grid(True, alpha=0.3)
        
        # 添加象限线
        ax.axhline(y=5, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=5, color='gray', linestyle='--', alpha=0.5)
        
        # 添加象限标签
        ax.text(8, 8, '最优区域\n高确定性+低风险', ha='center', fontsize=10, 
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return filepath
    
    def _level_to_score(self, level: str) -> float:
        """将风险等级转为分数"""
        mapping = {"低": 3, "中": 5, "高": 7, "极高": 9}
        return mapping.get(level, 5)
    
    def _score_to_level(self, score: float) -> str:
        """将分数转为风险等级"""
        if score >= 8:
            return "极高"
        elif score >= 6:
            return "高"
        elif score >= 4:
            return "中"
        else:
            return "低"


# 测试函数
def test_visualizations():
    """测试各类图表生成"""
    generator = VisualizationGenerator(output_dir="test_charts")
    
    print("测试图表生成...")
    
    # 1. 测试雷达图
    scores = {
        "确定性": 9,
        "回报率": 8,
        "风险": 4,
        "紧迫性": 10,
        "门槛": 3
    }
    path1 = generator.generate_radar_chart(scores, "海南自贸港投资评估", "test_radar.png")
    print(f"✅ 雷达图: {path1}")
    
    # 2. 测试政策强度图
    signals = [
        {"topic": "海南自贸港", "strength_score": 9.5},
        {"topic": "新型储能", "strength_score": 8.2},
        {"topic": "北斗产业", "strength_score": 7.5},
        {"topic": "环境监测", "strength_score": 8.0}
    ]
    path2 = generator.generate_policy_strength_chart(signals, "test_policy_strength.png")
    print(f"✅ 政策强度图: {path2}")
    
    # 3. 测试市场预测图
    years = ["2025", "2026", "2027"]
    tam = [100, 135, 180]
    sam = [30, 45, 65]
    path3 = generator.generate_market_forecast_chart(years, tam, sam, "海南跨境服务市场预测", "test_market.png")
    print(f"✅ 市场预测图: {path3}")
    
    # 4. 测试风险矩阵
    risks = {
        "政策风险": {"level": "中", "score": 5},
        "竞争风险": {"level": "高", "score": 7},
        "运营风险": {"level": "中", "score": 5},
        "合规风险": {"level": "低", "score": 3}
    }
    path4 = generator.generate_risk_matrix(risks, "test_risk.png")
    print(f"✅ 风险矩阵: {path4}")
    
    print("\n所有图表生成完成！")


if __name__ == "__main__":
    test_visualizations()

