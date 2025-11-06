"""
主流程：爬取新闻 → LLM分析 → 安全数据补充 → 生成报告
"""

from scraper import XinwenliboScraper
from llm_analyzer import LLMAnalyzer
from data_enrichment import SafeDataEnrichment
from report_generator import ReportGenerator
from config import get_config
from utils.path_helper import get_output_paths, print_output_structure, create_latest_link
from datetime import date
import os

def main(date_str=None, env=None):
    """主流程：爬取新闻 -> AI分析 -> 数据补充 -> 生成报告"""
    config = get_config(env)
    
    # 验证配置
    if not config.validate():
        print("\n❌ 配置验证失败，程序退出")
        return
    
    if not date_str:
        date_str = date.today().strftime("%Y%m%d")
    
    paths = get_output_paths(config, date_str)
    
    cache_dir = config.get('paths.cache_dir')
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print(f"🚀 投资机会分析系统 - {date_str}")
    print(f"   环境: {config.env.upper()}")
    print(f"   模型: {config.get('llm.model')}")
    print("="*60)
    print_output_structure(config, date_str)
    
    # ===== 步骤1: 爬取新闻联播 =====
    print("\n📰 [步骤 1/5] 爬取新闻联播...")
    print("-"*60)
    
    scraper = XinwenliboScraper(config=config)
    news_data = scraper.scrape_date(date_str)
    
    if not news_data:
        print("\n❌ 没有爬取到新闻数据，程序退出")
        return
    
    # 保存原始数据
    scraper.save_to_file(news_data, date_str)
    
    print(f"\n✅ 步骤1完成：成功爬取 {len(news_data)} 条新闻")
    
    # ===== 步骤2: LLM分析投资方向 =====
    print("\n🤖 [步骤 2/5] AI分析投资方向...")
    print("-"*60)
    
    try:
        analyzer = LLMAnalyzer(config=config)
        analysis_result = analyzer.extract_investment_directions(news_data)
        
        if not analysis_result:
            print("\n❌ AI分析失败，程序退出")
            return
        
        print("\n✅ 步骤2完成：AI分析成功")
        
        # 保存分析结果
        analyzer.save_analysis(analysis_result, date_str)
        
    except Exception as e:
        print(f"\n❌ 分析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ===== 步骤3: 安全数据补充 =====
    print("\n🔍 [步骤 3/5] 安全数据补充...")
    print("-"*60)
    
    try:
        enricher = SafeDataEnrichment(config=config, date_str=date_str)
        enriched_data = enricher.enrich_all_directions(analysis_result)
        
        print("\n✅ 步骤3完成：数据补充成功")
        
    except Exception as e:
        print(f"\n⚠️  数据补充出错: {e}")
        print("   使用原始分析结果继续...")
        enriched_data = analysis_result
    
    # ===== 步骤4: 保存中间结果 =====
    print("\n💾 [步骤 4/5] 保存中间数据...")
    print("-"*60)
    
    try:
        enricher.save_enriched_data(enriched_data, date_str)
        print("\n✅ 步骤4完成：中间数据已保存")
    except:
        print("\n⚠️  保存中间数据失败")
    
    # ===== 步骤5: 生成最终报告 =====
    print("\n📝 [步骤 5/5] 生成投资分析报告...")
    print("-"*60)
    
    try:
        generator = ReportGenerator(config=config)
        report = generator.generate_full_report(enriched_data, date_str)
        
        if report:
            generator.save_report(report, date_str)
            print("\n✅ 步骤5完成：报告生成成功")
        else:
            print("\n⚠️  步骤5警告：报告生成失败，但其他数据已保存")
        
    except Exception as e:
        print(f"\n⚠️  步骤5警告：报告生成出错: {e}")
        print("   其他数据已成功保存，可手动分析")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("🎉 全部完成！")
    print("="*60)
    
    create_latest_link(config, date_str)
    
    if config.get('paths.group_by_date', True):
        print(f"\n📂 生成的文件（{paths['date_dir']}/）：")
        print(f"\n  📊 data/ - 数据文件：")
        print(f"    • xinwenlianbo_{date_str}.json  - 新闻原始数据")
        print(f"    • xinwenlianbo_{date_str}.txt   - 新闻文本版")
        print(f"    • xinwenlianbo_{date_str}.md    - 新闻Markdown版")
        print(f"    • analysis_{date_str}.json      - AI分析结果")
        print(f"    • enriched_{date_str}.json      - 完整数据（含补充）")
        
        print(f"\n  📝 reports/ - 报告文件：")
        print(f"    • report_{date_str}.md          - ⭐⭐⭐ 投资分析报告")
        print(f"    • summary_{date_str}.txt        - 报告摘要")
        print(f"    • report_{date_str}.html        - HTML版报告")
        if config.get('report.export_formats.pdf', True):
            print(f"    • report_{date_str}.pdf         - PDF版报告")
        
        print(f"\n  📋 logs/ - 日志文件：")
        print(f"    • scraper.log                   - 爬取日志")
        print(f"    • xinwenlianbo_{date_str}_debug.html (如有)")
        
        print(f"\n💡 重点查看: {paths['reports_dir']}/report_{date_str}.md")
    else:
        data_dir = config.get('paths.data_dir', '.')
        output_dir = config.get('paths.output_dir', '.')
        log_dir = config.get('paths.log_dir', 'logs')
        
        print(f"\n📂 生成的文件：")
        print(f"\n  📊 数据文件（{data_dir}/）：")
        print(f"    1. xinwenlianbo_{date_str}.json  - 新闻原始数据")
        print(f"    2. xinwenlianbo_{date_str}.txt   - 新闻文本版")
        print(f"    3. xinwenlianbo_{date_str}.md    - 新闻Markdown版")
        print(f"    4. analysis_{date_str}.json      - AI分析结果")
        print(f"    5. enriched_{date_str}.json      - 完整数据（含补充）")
        print(f"\n  📝 报告文件（{output_dir}/）：")
        print(f"    6. report_{date_str}.md          - ⭐⭐⭐ 投资分析报告")
        print(f"    7. summary_{date_str}.txt        - 报告摘要")
        print(f"    8. report_{date_str}.html        - HTML版报告")
        if config.get('report.export_formats.pdf', True):
            print(f"    9. report_{date_str}.pdf         - PDF版报告")
        print(f"\n  📋 日志文件（{log_dir}/）：")
        print(f"    scraper.log                      - 爬取日志")
        print(f"\n💡 重点查看: {output_dir}/report_{date_str}.md")
    
    print()

if __name__ == "__main__":
    # 可以指定日期，也可以留空使用今天
    main("20251104")  # 分析指定日期
    # main()  # 分析今天