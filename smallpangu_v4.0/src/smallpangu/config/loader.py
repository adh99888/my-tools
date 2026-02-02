"""
配置加载器 - YAML配置文件加载和验证
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from functools import lru_cache

from .models import SmallPanguConfig, LoggingConfig, AppConfig
from ..core.errors import ConfigError, AppError
from ..core.logging import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self):
        self._config_cache: Dict[str, SmallPanguConfig] = {}
    
    def load(
        self,
        config_path: Optional[Union[str, Path]] = None,
        environment: Optional[str] = None,
        validate: bool = True
    ) -> SmallPanguConfig:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径或目录
            environment: 运行环境（production/development/testing/staging）
            validate: 是否验证配置
            
        Returns:
            SmallPanguConfig: 加载的配置对象
        """
        try:
            logger.debug_struct(
                "加载配置", 
                config_path=str(config_path), 
                environment=environment
            )
            
            # 解析环境
            env = self._resolve_environment(environment, config_path)
            
            # 获取配置路径
            config_dir, config_files = self._resolve_config_paths(config_path, env)
            
            # 加载和合并配置
            raw_config = self._load_and_merge_configs(config_dir, config_files)
            
            # 设置环境
            raw_config["environment"] = env
            
            # 创建配置对象
            config = self._create_config_object(raw_config, validate)
            
            # 缓存配置
            cache_key = f"{config_dir}:{env}"
            self._config_cache[cache_key] = config
            
            logger.info_struct("配置加载成功", environment=env, config_files=config_files)
            return config
            
        except Exception as e:
            error_msg = f"配置加载失败: {str(e)}"
            logger.error_struct(error_msg, exc_info=True)
            raise ConfigError(
                error_msg,
                config_path=str(config_path),
                details={"environment": environment}
            ) from e
    
    def _resolve_environment(
        self, 
        environment: Optional[str], 
        config_path: Optional[Union[str, Path]]
    ) -> str:
        """解析运行环境"""
        # 1. 优先使用传入的环境参数
        if environment:
            return environment
        
        # 2. 检查环境变量
        env_var = os.environ.get("SMALLPANGU_ENVIRONMENT")
        if env_var:
            return env_var.lower()
        
        # 3. 根据配置文件路径推断
        if config_path:
            config_str = str(config_path)
            if "development" in config_str or "dev" in config_str:
                return "development"
            elif "testing" in config_str or "test" in config_str:
                return "testing"
            elif "staging" in config_str:
                return "staging"
        
        # 4. 默认生产环境
        return "production"
    
    def _resolve_config_paths(
        self, 
        config_path: Optional[Union[str, Path]], 
        environment: str
    ) -> tuple[Path, List[str]]:
        """解析配置路径和文件列表"""
        
        # 如果提供了具体文件路径
        if config_path and Path(config_path).is_file():
            config_dir = Path(config_path).parent
            config_files = [Path(config_path).name]
            return config_dir, config_files
        
        # 如果提供了目录路径
        if config_path and Path(config_path).is_dir():
            config_dir = Path(config_path)
        else:
            # 默认配置目录
            config_dir = Path.cwd() / "configs"
            if not config_dir.exists():
                # 回退到包内配置目录
                config_dir = Path(__file__).parent.parent.parent.parent / "configs"
        
        # 确保配置目录存在
        if not config_dir.exists():
            raise ConfigError(
                f"配置目录不存在: {config_dir}",
                config_path=str(config_dir),
                details={"config_dir": str(config_dir)}
            )
        
        # 确定要加载的配置文件
        config_files = []
        
        # 总是加载基础配置
        base_config = config_dir / "base.yaml"
        if base_config.exists():
            config_files.append("base.yaml")
        else:
            logger.warning_struct("基础配置文件不存在", path=str(base_config))
        
        # 加载环境特定配置
        env_config = config_dir / f"{environment}.yaml"
        if env_config.exists():
            config_files.append(f"{environment}.yaml")
        else:
            logger.debug_struct(
                "环境特定配置文件不存在", 
                environment=environment, 
                path=str(env_config)
            )
        
        # 检查是否有自定义配置文件
        custom_config = config_dir / "custom.yaml"
        if custom_config.exists():
            config_files.append("custom.yaml")
        
        if not config_files:
            raise ConfigError(
                f"在目录中未找到任何配置文件: {config_dir}",
                config_path=str(config_dir),
                details={"config_dir": str(config_dir)}
            )
        
        return config_dir, config_files
    
    def _load_and_merge_configs(
        self, 
        config_dir: Path, 
        config_files: List[str]
    ) -> Dict[str, Any]:
        """加载并合并多个配置文件"""
        merged_config: Dict[str, Any] = {}
        
        for config_file in config_files:
            file_path = config_dir / config_file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                
                if file_config:
                    merged_config = self._deep_merge(merged_config, file_config)
                    logger.debug_struct(
                        "配置文件加载成功", 
                        file=config_file, 
                        path=str(file_path)
                    )
                
            except yaml.YAMLError as e:
                raise ConfigError(
                    f"YAML解析失败: {file_path}",
                    config_path=str(file_path),
                    details={"error": str(e)}
                ) from e
            except Exception as e:
                raise ConfigError(
                    f"配置文件读取失败: {file_path}",
                    config_path=str(file_path),
                    details={"error": str(e)}
                ) from e
        
        return merged_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_config_object(
        self, 
        raw_config: Dict[str, Any], 
        validate: bool
    ) -> SmallPanguConfig:
        """创建配置对象"""
        try:
            # 处理路径扩展（~扩展为家目录）
            raw_config = self._expand_paths(raw_config)
            
            # 创建配置对象
            config = SmallPanguConfig(**raw_config)
            
            # 验证配置（Pydantic已经验证，这里可以添加自定义验证）
            if validate:
                self._validate_config(config)
            
            return config
            
        except Exception as e:
            raise ConfigError(
                "配置验证失败",
                details={"error": str(e), "raw_config_keys": list(raw_config.keys())}
            ) from e
    
    def _expand_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """展开配置中的路径（~扩展为家目录）"""
        def expand_value(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("~"):
                return os.path.expanduser(value)
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand_value(item) for item in value]
            else:
                return value
        
        return expand_value(config)
    
    def _validate_config(self, config: SmallPanguConfig):
        """自定义配置验证"""
        # 验证日志配置
        if config.logging and config.app:
            log_level = config.app.log_level
            # 确保应用日志级别不高于任何启用的处理器级别
            for handler_name, handler in config.logging.handlers.items():
                if handler.enabled:
                    # 将日志级别转换为数值进行比较
                    level_order = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
                    app_level = level_order.get(log_level.value, 20)
                    handler_level = level_order.get(handler.level.value, 20)
                    
                    if app_level > handler_level:
                        logger.warning_struct(
                            "应用日志级别高于处理器级别可能导致日志丢失",
                            handler=handler_name,
                            app_level=log_level.value,
                            handler_level=handler.level.value
                        )
        
        # 验证插件搜索路径存在
        for search_path in config.plugins.search_paths:
            expanded_path = os.path.expanduser(search_path)
            if not os.path.exists(expanded_path):
                logger.debug_struct("插件搜索路径不存在", path=search_path, expanded_path=expanded_path)
        
        # 验证数据目录和缓存目录可写
        data_dir = Path(config.app.data_dir).expanduser()
        cache_dir = Path(config.app.cache_dir).expanduser()
        
        for dir_path, dir_name in [(data_dir, "数据目录"), (cache_dir, "缓存目录")]:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.debug_struct(f"{dir_name}创建成功", path=str(dir_path))
                except Exception as e:
                    raise ConfigError(
                        f"{dir_name}创建失败: {dir_path}",
                        details={"path": str(dir_path), "error": str(e)}
                    )
            
            # 检查目录是否可写
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                raise ConfigError(
                    f"{dir_name}不可写: {dir_path}",
                    details={"path": str(dir_path), "error": str(e)}
                )
    
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        logger.debug("配置缓存已清除")


# 全局配置加载器实例
_loader = None

def get_config_loader() -> ConfigLoader:
    """获取配置加载器实例（单例）"""
    global _loader
    if _loader is None:
        _loader = ConfigLoader()
    return _loader


@lru_cache(maxsize=4)
def load_config(
    config_path: Optional[Union[str, Path]] = None,
    environment: Optional[str] = None,
    validate: bool = True
) -> SmallPanguConfig:
    """
    加载配置（带缓存）
    
    Args:
        config_path: 配置文件路径或目录
        environment: 运行环境
        validate: 是否验证配置
        
    Returns:
        SmallPanguConfig: 加载的配置对象
    """
    loader = get_config_loader()
    return loader.load(config_path, environment, validate)


def reload_config(
    config_path: Optional[Union[str, Path]] = None,
    environment: Optional[str] = None,
    validate: bool = True
) -> SmallPanguConfig:
    """
    重新加载配置（清除缓存后加载）
    
    Args:
        config_path: 配置文件路径或目录
        environment: 运行环境
        validate: 是否验证配置
        
    Returns:
        SmallPanguConfig: 重新加载的配置对象
    """
    loader = get_config_loader()
    loader.clear_cache()
    load_config.cache_clear()
    return loader.load(config_path, environment, validate)


__all__ = [
    "ConfigLoader",
    "get_config_loader",
    "load_config",
    "reload_config"
]