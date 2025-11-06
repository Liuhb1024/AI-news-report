"""路径辅助函数 - 支持按日期分组存储"""
import os
from datetime import datetime
from pathlib import Path


def get_output_paths(config, date_str):
    """获取输出路径（按日期分组或传统模式）"""
    group_by_date = config.get('paths.group_by_date', True)
    
    if group_by_date:
        output_root = config.get('paths.output_root', 'outputs')
        date_format = config.get('paths.date_folder_format', '%Y-%m-%d')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            date_folder = date_obj.strftime(date_format)
        except ValueError:
            date_folder = date_str
        
        date_dir = os.path.join(output_root, date_folder)
        data_dir = os.path.join(date_dir, 'data')
        reports_dir = os.path.join(date_dir, 'reports')
        logs_dir = os.path.join(date_dir, 'logs')
        
        for directory in [data_dir, reports_dir, logs_dir]:
            os.makedirs(directory, exist_ok=True)
        
        return {
            'date_dir': date_dir,
            'data_dir': data_dir,
            'reports_dir': reports_dir,
            'logs_dir': logs_dir,
        }
    else:
        data_dir = config.get('paths.data_dir', 'data')
        output_dir = config.get('paths.output_dir', '.')
        log_dir = config.get('paths.log_dir', 'logs')
        
        for directory in [data_dir, output_dir, log_dir]:
            if directory and directory != '.':
                os.makedirs(directory, exist_ok=True)
        
        return {
            'date_dir': None,
            'data_dir': data_dir,
            'reports_dir': output_dir,
            'logs_dir': log_dir,
        }


def get_data_file_path(config, date_str, filename):
    """获取数据文件路径"""
    paths = get_output_paths(config, date_str)
    return os.path.join(paths['data_dir'], filename)


def get_report_file_path(config, date_str, filename):
    """获取报告文件路径"""
    paths = get_output_paths(config, date_str)
    return os.path.join(paths['reports_dir'], filename)


def get_log_file_path(config, date_str, filename):
    """获取日志文件路径"""
    paths = get_output_paths(config, date_str)
    return os.path.join(paths['logs_dir'], filename)


def create_latest_link(config, date_str):
    """创建指向最新目录的链接（Windows: LATEST.txt / Linux: 符号链接）"""
    if not config.get('paths.group_by_date', True):
        return
    
    try:
        import platform
        output_root = config.get('paths.output_root', 'outputs')
        date_format = config.get('paths.date_folder_format', '%Y-%m-%d')
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        date_folder = date_obj.strftime(date_format)
        
        if platform.system() == 'Windows':
            latest_file = os.path.join(output_root, 'LATEST.txt')
            with open(latest_file, 'w', encoding='utf-8') as f:
                f.write(f"最新输出目录：{date_folder}\n")
                f.write(f"完整路径：{os.path.abspath(os.path.join(output_root, date_folder))}\n")
                f.write(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        else:
            latest_link = os.path.join(output_root, 'latest')
            if os.path.islink(latest_link):
                os.unlink(latest_link)
            elif os.path.exists(latest_link):
                os.remove(latest_link)
            os.symlink(date_folder, latest_link, target_is_directory=True)
    except Exception:
        pass


def print_output_structure(config, date_str):
    """打印输出目录结构"""
    paths = get_output_paths(config, date_str)
    
    if paths['date_dir']:
        print(f"\n📂 输出目录结构：")
        print(f"   {paths['date_dir']}/")
        print(f"   ├── data/       # 数据文件")
        print(f"   ├── reports/    # 报告文件")
        print(f"   └── logs/       # 日志文件")
    else:
        print(f"\n📂 输出目录：")
        print(f"   数据: {paths['data_dir']}")
        print(f"   报告: {paths['reports_dir']}")
        print(f"   日志: {paths['logs_dir']}")

