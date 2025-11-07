"""
配置管理模块
支持从YAML文件加载配置，并支持环境变量覆盖
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""
    
    def __init__(self, env: str = None):
        """
        初始化配置
        
        参数:
            env: 环境名称 (development/production)，默认从环境变量 ENV 读取
        """
        self.env = env or os.getenv("ENV", "development")
        self._config = {}
        self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self):
        """加载配置文件"""
        config_dir = Path(__file__).parent / "config"
        
        # 1. 加载默认配置
        default_config_path = config_dir / "default.yaml"
        if default_config_path.exists():
            with open(default_config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"默认配置文件不存在: {default_config_path}")
        
        # 2. 加载环境特定配置（覆盖默认配置）
        env_config_path = config_dir / f"{self.env}.yaml"
        if env_config_path.exists():
            with open(env_config_path, 'r', encoding='utf-8') as f:
                env_config = yaml.safe_load(f) or {}
                self._deep_merge(self._config, env_config)
    
    def _deep_merge(self, base: dict, override: dict):
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        if model := os.getenv("LLM_MODEL"):
            self._config.setdefault("llm", {})["model"] = model

        # 日志级别
        if log_level := os.getenv("LOG_LEVEL"):
            self._config.setdefault("logging", {})["level"] = log_level.upper()
        
        # 调试模式
        if debug := os.getenv("DEBUG"):
            self._config.setdefault("system", {})["debug"] = debug.lower() in ("true", "1", "yes")

        models_section = self._config.setdefault("models", {})
        providers = models_section.setdefault("providers", {})

        if deepseek_key := os.getenv("DEEPSEEK_API_KEY"):
            providers.setdefault("deepseek", {})["api_key"] = deepseek_key
        if deepseek_base := os.getenv("DEEPSEEK_BASE_URL"):
            providers.setdefault("deepseek", {})["base_url"] = deepseek_base
        if deepseek_model := os.getenv("DEEPSEEK_MODEL"):
            providers.setdefault("deepseek", {})["model"] = deepseek_model

        if qwen_key := os.getenv("QWEN_API_KEY"):
            providers.setdefault("qwen", {})["api_key"] = qwen_key
        if qwen_base := os.getenv("QWEN_BASE_URL"):
            providers.setdefault("qwen", {})["base_url"] = qwen_base
        if qwen_model := os.getenv("QWEN_MODEL"):
            providers.setdefault("qwen", {})["model"] = qwen_model
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）
        
        示例:
            config.get("llm.model")
            config.get("scraper.timeout", 15)
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值（支持点号路径）
        
        示例:
            config.set("llm.model", "gpt-4")
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置段"""
        return self.get(section, {})
    
    # ==================== 便捷访问方法 ====================
    
    @property
    def llm(self) -> Dict[str, Any]:
        """LLM配置"""
        return self.get_section("llm")
    
    @property
    def scraper(self) -> Dict[str, Any]:
        """爬虫配置"""
        return self.get_section("scraper")
    
    @property
    def enrichment(self) -> Dict[str, Any]:
        """数据补充配置"""
        return self.get_section("enrichment")
    
    @property
    def report(self) -> Dict[str, Any]:
        """报告配置"""
        return self.get_section("report")
    
    @property
    def paths(self) -> Dict[str, Any]:
        """路径配置"""
        return self.get_section("paths")
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """日志配置"""
        return self.get_section("logging")
    
    @property
    def cache_config(self) -> Dict[str, Any]:
        """缓存配置"""
        return self.get_section("cache")
    
    @property
    def system(self) -> Dict[str, Any]:
        """系统配置"""
        return self.get_section("system")
    
    def validate(self) -> bool:
        """
        验证配置有效性
        
        返回:
            bool: 配置是否有效
        """
        errors = []
        
        # 验证模型密钥（至少有一个可用提供方）
        providers = self.get("models.providers", {}) or {}
        if not any(cfg.get("api_key") for cfg in providers.values()):
            errors.append("❌ 未配置任何可用的模型密钥 (models.providers.*.api_key)")
        
        # 验证路径
        paths = self.paths
        group_by_date = paths.get("group_by_date", True)

        # 当未启用按日期分组时，需要提前创建传统目录
        if not group_by_date:
            for path_key in ["data_dir", "log_dir"]:
                path = paths.get(path_key)
                if path:
                    Path(path).mkdir(parents=True, exist_ok=True)

        # output_dir 只有在指定了自定义路径时需要创建（默认 "." 无需处理）
        output_dir = paths.get("output_dir")
        if output_dir and output_dir not in [".", "./"]:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        # cache 目录仅在显式配置时创建
        cache_dir = paths.get("cache_dir")
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        # 打印错误
        if errors:
            for error in errors:
                print(error)
            return False
        
        return True
    
    def print_config(self, section: Optional[str] = None):
        """
        打印配置信息（脱敏）
        
        参数:
            section: 指定打印的配置段，None表示打印全部
        """
        print("="*60)
        print(f"📋 配置信息 [环境: {self.env.upper()}]")
        print("="*60)
        
        config_to_print = self.get_section(section) if section else self._config
        
        self._print_dict(config_to_print)
        print("="*60)
    
    def _print_dict(self, d: dict, indent: int = 0):
        """递归打印字典（脱敏）"""
        for key, value in d.items():
            prefix = "  " * indent
            
            # 脱敏处理
            if "key" in key.lower() or "password" in key.lower() or "secret" in key.lower():
                if value and isinstance(value, str) and len(value) > 8:
                    value = f"{value[:4]}...{value[-4:]}"
                elif value:
                    value = "***"
            
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self._print_dict(value, indent + 1)
            elif isinstance(value, list):
                print(f"{prefix}{key}: [{len(value)} items]")
            else:
                print(f"{prefix}{key}: {value}")


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(env: str = None) -> Config:
    """
    获取全局配置实例（单例模式）
    
    参数:
        env: 环境名称，仅首次调用时有效
    
    返回:
        Config: 配置实例
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(env)
    
    return _config_instance


def reload_config(env: str = None):
    """
    重新加载配置
    
    参数:
        env: 环境名称
    """
    global _config_instance
    _config_instance = Config(env)
    return _config_instance


# 便捷导出
__all__ = ['Config', 'get_config', 'reload_config']


if __name__ == "__main__":
    # 测试配置加载
    config = get_config()
    
    # 验证配置
    if config.validate():
        print("\n✅ 配置验证通过")
        
        # 打印配置
        config.print_config()
        
        # 测试访问
        print("\n📝 配置访问测试:")
        print(f"LLM模型: {config.get('llm.model')}")
        print(f"爬虫超时: {config.get('scraper.timeout')}秒")
        print(f"安全模式: {config.get('enrichment.safe_mode')}")
        print(f"日志级别: {config.get('logging.level')}")
    else:
        print("\n❌ 配置验证失败")

