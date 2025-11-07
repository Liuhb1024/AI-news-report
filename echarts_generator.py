"""
ECharts图表生成器模块
使用PyEcharts生成现代化、美观的图表
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from pyecharts import options as opts
from pyecharts.charts import Radar, Bar, Line, Scatter, HeatMap
from pyecharts.globals import ThemeType
from pyecharts.render import make_snapshot

# 使用snapshot-selenium代替phantomjs（更可靠）
try:
    from snapshot_selenium import snapshot as selenium_snapshot
    snapshot = selenium_snapshot
except ImportError:
    # 降级到phantomjs
    try:
        from snapshot_phantomjs import snapshot
    except ImportError:
        snapshot = None
        print("警告：未安装图片渲染库，请运行: pip install snapshot-selenium")


class EChartsGenerator:
    """基于PyEcharts的图表生成器"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化ECharts生成器
        
        参数:
            output_dir: 图表输出目录
        """
        self.output_dir = output_dir or "outputs/charts"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 默认主题配置
        self.theme = ThemeType.LIGHT
        
        # 默认颜色方案（现代化配色）
        self.colors = [
            '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
            '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
        ]
    
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
        # 准备数据
        indicators = [{"name": k, "max": 10} for k in scores.keys()]
        values = [list(scores.values())]
        
        # 创建雷达图
        radar = (
            Radar(init_opts=opts.InitOpts(
                width="800px",
                height="600px",
                theme=self.theme,
                bg_color='white'
            ))
            .add_schema(
                schema=indicators,
                shape="polygon",
                center=["50%", "50%"],
                radius="65%",
                angleaxis_opts=opts.AngleAxisOpts(
                    min_=0,
                    max_=10,
                    is_clockwise=False,
                    axislabel_opts=opts.LabelOpts(font_size=14, font_weight="bold"),
                ),
                radiusaxis_opts=opts.RadiusAxisOpts(
                    min_=0,
                    max_=10,
                    interval=2,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True,
                        areastyle_opts=opts.AreaStyleOpts(opacity=0.3)
                    ),
                ),
                splitarea_opt=opts.SplitAreaOpts(
                    is_show=True,
                    areastyle_opts=opts.AreaStyleOpts(opacity=0.2)
                ),
            )
            .add(
                series_name=title,
                data=values,
                label_opts=opts.LabelOpts(is_show=False),
                areastyle_opts=opts.AreaStyleOpts(opacity=0.3, color=self.colors[0]),
                linestyle_opts=opts.LineStyleOpts(width=3, color=self.colors[0]),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=20,
                        font_weight="bold",
                        color="#2c3e50"
                    )
                ),
                legend_opts=opts.LegendOpts(
                    pos_top="bottom",
                    pos_left="center"
                ),
            )
        )
        
        # 保存为图片
        filepath = os.path.join(self.output_dir, filename)
        make_snapshot(snapshot, radar.render(), filepath, pixel_ratio=2)
        
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
        # 准备数据
        topics = [signal.get('topic', '') for signal in policy_signals]
        scores = [signal.get('strength_score', 0) for signal in policy_signals]
        
        # 根据分数设置颜色
        def get_color(score):
            if score >= 8:
                return '#e74c3c'  # 红色（强信号）
            elif score >= 6:
                return '#f39c12'  # 橙色（中等信号）
            else:
                return '#3498db'  # 蓝色（弱信号）
        
        colors = [get_color(s) for s in scores]
        
        # 创建柱状图（横向）
        bar = (
            Bar(init_opts=opts.InitOpts(
                width="1000px",
                height="600px",
                theme=self.theme,
                bg_color='white'
            ))
            .add_xaxis(topics)
            .add_yaxis(
                "政策强度",
                scores,
                category_gap="40%",
                itemstyle_opts=opts.ItemStyleOpts(
                    color=lambda x: colors[x.index]
                ),
                label_opts=opts.LabelOpts(
                    is_show=True,
                    position="right",
                    formatter="{c}",
                    font_size=12,
                    font_weight="bold"
                ),
            )
            .reversal_axis()  # 翻转为横向
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="政策信号强度对比",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=20,
                        font_weight="bold",
                        color="#2c3e50"
                    )
                ),
                xaxis_opts=opts.AxisOpts(
                    name="评分",
                    name_location="middle",
                    name_gap=30,
                    max_=11,
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                yaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(font_size=12, interval=0),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        
        # 保存为图片
        filepath = os.path.join(self.output_dir, filename)
        make_snapshot(snapshot, bar.render(), filepath, pixel_ratio=2)
        
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
        # 创建柱状图
        bar = (
            Bar(init_opts=opts.InitOpts(
                width="1000px",
                height="600px",
                theme=self.theme,
                bg_color='white'
            ))
            .add_xaxis(years)
            .add_yaxis(
                "总市场(TAM)",
                tam,
                itemstyle_opts=opts.ItemStyleOpts(color=self.colors[0]),
                label_opts=opts.LabelOpts(
                    is_show=True,
                    position="top",
                    formatter="{c}亿"
                ),
            )
            .add_yaxis(
                "目标市场(SAM)",
                sam,
                itemstyle_opts=opts.ItemStyleOpts(color=self.colors[1]),
                label_opts=opts.LabelOpts(
                    is_show=True,
                    position="top",
                    formatter="{c}亿"
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=title,
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=20,
                        font_weight="bold",
                        color="#2c3e50"
                    )
                ),
                xaxis_opts=opts.AxisOpts(
                    name="年份",
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                yaxis_opts=opts.AxisOpts(
                    name="市场规模（亿元）",
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                legend_opts=opts.LegendOpts(
                    pos_top="bottom",
                    pos_left="center"
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="shadow"
                ),
            )
        )
        
        # 保存为图片
        filepath = os.path.join(self.output_dir, filename)
        make_snapshot(snapshot, bar.render(), filepath, pixel_ratio=2)
        
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
        risk_names = list(risks.keys())
        risk_scores = [
            risks[name].get('score', self._level_to_score(risks[name].get('level', '中'))) 
            for name in risk_names
        ]
        
        # 创建横向柱状图
        bar = (
            Bar(init_opts=opts.InitOpts(
                width="800px",
                height=f"{max(400, len(risk_names) * 80)}px",
                theme=self.theme,
                bg_color='white'
            ))
            .add_xaxis(risk_names)
            .add_yaxis(
                "风险评分",
                risk_scores,
                category_gap="40%",
                itemstyle_opts=opts.ItemStyleOpts(
                    color=lambda x: self._get_risk_color(risk_scores[x.index])
                ),
                label_opts=opts.LabelOpts(
                    is_show=True,
                    position="right",
                    formatter=lambda x: f"{risks[risk_names[x.index]].get('level', '')} ({x.value})",
                    font_size=12
                ),
            )
            .reversal_axis()
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="风险评估矩阵",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=20,
                        font_weight="bold",
                        color="#2c3e50"
                    )
                ),
                xaxis_opts=opts.AxisOpts(
                    name="风险评分 (0=低, 10=高)",
                    max_=11,
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                yaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        
        # 保存为图片
        filepath = os.path.join(self.output_dir, filename)
        make_snapshot(snapshot, bar.render(), filepath, pixel_ratio=2)
        
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
        # 准备数据
        data = []
        for direction in directions:
            name = direction.get('name', '')
            scores = direction.get('quantitative_scores', {})
            
            certainty = scores.get('certainty', 5)
            risk = scores.get('risk_level', 5)
            urgency = scores.get('urgency', 5)
            
            # [x, y, size, name]
            data.append({
                'value': [certainty, 10 - risk, urgency * 10],
                'name': name
            })
        
        # 创建散点图
        scatter = (
            Scatter(init_opts=opts.InitOpts(
                width="1200px",
                height="800px",
                theme=self.theme,
                bg_color='white'
            ))
            .add_xaxis([d['value'][0] for d in data])
            .add_yaxis(
                "投资机会",
                [d['value'][1] for d in data],
                symbol_size=[d['value'][2] for d in data],
                itemstyle_opts=opts.ItemStyleOpts(
                    opacity=0.7,
                    color=self.colors[0]
                ),
                label_opts=opts.LabelOpts(
                    is_show=True,
                    position="top",
                    formatter=lambda x: data[x.dataIndex]['name'] if hasattr(x, 'dataIndex') else "",
                    font_size=11
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="投资机会对比分析（气泡大小=紧迫性）",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=20,
                        font_weight="bold",
                        color="#2c3e50"
                    )
                ),
                xaxis_opts=opts.AxisOpts(
                    name="确定性 →",
                    min_=0,
                    max_=11,
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                yaxis_opts=opts.AxisOpts(
                    name="安全性 (低风险) →",
                    min_=0,
                    max_=11,
                    splitline_opts=opts.SplitLineOpts(is_show=True),
                    axislabel_opts=opts.LabelOpts(font_size=12),
                ),
                legend_opts=opts.LegendOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(
                    trigger="item",
                    formatter="{b}<br/>确定性: {c0}<br/>安全性: {c1}"
                ),
            )
        )
        
        # 保存为图片
        filepath = os.path.join(self.output_dir, filename)
        make_snapshot(snapshot, scatter.render(), filepath, pixel_ratio=2)
        
        return filepath
    
    def _level_to_score(self, level: str) -> float:
        """将风险等级转为分数"""
        mapping = {"极低": 1, "低": 3, "中": 5, "高": 7, "极高": 9}
        return mapping.get(level, 5)
    
    def _get_risk_color(self, score: float) -> str:
        """根据风险分数获取颜色"""
        if score >= 8:
            return '#e74c3c'  # 红色（极高风险）
        elif score >= 6:
            return '#f39c12'  # 橙色（高风险）
        elif score >= 4:
            return '#f1c40f'  # 黄色（中等风险）
        else:
            return '#2ecc71'  # 绿色（低风险）


# 测试函数
def test_echarts():
    """测试ECharts图表生成"""
    generator = EChartsGenerator(output_dir="test_echarts_output")
    
    print("测试ECharts图表生成...")
    
    # 1. 测试雷达图
    print("\n1. 生成雷达图...")
    scores = {
        "确定性": 9,
        "回报率": 8,
        "风险": 4,
        "紧迫性": 10,
        "门槛": 3
    }
    path1 = generator.generate_radar_chart(scores, "海南自贸港投资评估", "test_radar.png")
    print(f"   ✅ 雷达图: {path1}")
    
    # 2. 测试政策强度图
    print("\n2. 生成政策强度图...")
    signals = [
        {"topic": "海南自贸港", "strength_score": 9.5},
        {"topic": "新型储能", "strength_score": 8.2},
        {"topic": "北斗产业", "strength_score": 7.5},
        {"topic": "环境监测", "strength_score": 8.0}
    ]
    path2 = generator.generate_policy_strength_chart(signals, "test_policy_strength.png")
    print(f"   ✅ 政策强度图: {path2}")
    
    # 3. 测试市场预测图
    print("\n3. 生成市场预测图...")
    years = ["2025", "2026", "2027"]
    tam = [100, 135, 180]
    sam = [30, 45, 65]
    path3 = generator.generate_market_forecast_chart(years, tam, sam, "海南跨境服务市场预测", "test_market.png")
    print(f"   ✅ 市场预测图: {path3}")
    
    # 4. 测试风险矩阵
    print("\n4. 生成风险矩阵...")
    risks = {
        "政策风险": {"level": "中", "score": 5},
        "竞争风险": {"level": "高", "score": 7},
        "运营风险": {"level": "中", "score": 5},
        "合规风险": {"level": "低", "score": 3}
    }
    path4 = generator.generate_risk_matrix(risks, "test_risk.png")
    print(f"   ✅ 风险矩阵: {path4}")
    
    print("\n✅ 所有图表生成完成！")
    print(f"\n📂 图表保存在: test_echarts_output/")


if __name__ == "__main__":
    test_echarts()

