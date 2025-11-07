"""
主流程：多 Agent 协作完成新闻抓取、分析、补充与报告生成
"""

from datetime import date, datetime
from pathlib import Path
import os
import traceback

from agents import (
    AgentOrchestrator,
    InsightAgent,
    ModeratorAgent,
    OrchestratorConfig,
    PolicyAgent,
    QueryAgent,
    ReportAgent,
    NEWS_ITEMS_KEY,
    POLICY_ANALYSIS_KEY,
    REPORT_METADATA_KEY,
)
from config import get_config
from models import create_model_registry, create_model_router
from utils.path_helper import get_output_paths, print_output_structure, create_latest_link


def build_default_orchestrator(config, date_str, paths, model_router):
    """构建默认的 Agent 调度器。"""
    manifest_root = Path(paths['date_dir'] or paths['reports_dir'])
    orchestrator_config = OrchestratorConfig(
        run_id=f"{date_str}-{datetime.now().strftime('%H%M%S')}",
        output_root=manifest_root,
    )

    agent_config = {
        "app_config": config,
        "model_router": model_router,
    }
    agents = [
        QueryAgent(config=agent_config),
        PolicyAgent(config=agent_config),
        InsightAgent(config=agent_config),
        ReportAgent(config=agent_config),
        ModeratorAgent(config=agent_config),
    ]

    return AgentOrchestrator(orchestrator_config, agents)


def print_agent_summary(context):
    """输出 Agent 执行摘要。"""
    print("\n🧠 Agent 运行摘要")
    print("-" * 60)
    for message in context.messages:
        header = f"[{message.role}] {message.name or ''}".strip()
        print(f"{header}: {message.content}")
        if message.data:
            print(f"   数据: {message.data}")


def print_context_highlights(context):
    """打印关键产物概览。"""
    news_count = len(context.shared_state.get(NEWS_ITEMS_KEY, []))
    directions_count = len(context.shared_state.get(POLICY_ANALYSIS_KEY, {}).get('directions', []))
    report_info = context.shared_state.get(REPORT_METADATA_KEY, {})

    print(f"\n📊 数据概览：新闻 {news_count} 条 | 投资方向 {directions_count} 个")

    if report_info:
        print(f"📄 报告路径: {report_info.get('report_path')}")
        print(f"📝 摘要路径: {report_info.get('summary_path')}")


def main(date_str=None, env=None):
    """主流程入口：构建并运行多 Agent Pipeline。"""
    config = get_config(env)

    if not config.validate():
        print("\n❌ 配置验证失败，程序退出")
        return

    if not date_str:
        date_str = date.today().strftime("%Y%m%d")

    paths = get_output_paths(config, date_str)

    cache_dir = config.get('paths.cache_dir')
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print(f"🚀 投资机会分析系统 - {date_str}")
    print(f"   环境: {config.env.upper()}")
    print(f"   模型: {config.get('llm.model')}")
    print("=" * 60)
    print_output_structure(config, date_str)

    model_registry = create_model_registry(config)
    model_router = create_model_router(config, registry=model_registry)

    orchestrator = build_default_orchestrator(config, date_str, paths, model_router)

    try:
        context = orchestrator.run(date_str=date_str)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n❌ 流程执行失败: {exc}")
        traceback.print_exc()
        return

    print_agent_summary(context)
    print_context_highlights(context)

    if orchestrator.config.save_manifest:
        manifest_path = orchestrator.config.output_root / orchestrator.config.manifest_filename
        print(f"\n🗂️ Manifest: {manifest_path}")

    print("\n" + "=" * 60)
    print("🎉 全部完成！")
    print("=" * 60)

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
    main("20251106")  # 分析指定日期
    # main()  # 分析今天