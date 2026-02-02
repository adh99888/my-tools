"""
配置模块 - 小盘古配置管理系统

提供完整的配置管理功能：
1. 基于Pydantic的强类型配置模型
2. YAML配置文件加载和验证
3. 环境变量支持
4. 热重载和配置变更通知
5. 统一的配置访问接口
"""

from .models import (
    LogLevel,
    Theme,
    Language,
    StorageType,
    SwitchStrategy,
    ConfirmLevel,
    OperationType,
    LogHandlerConfig,
    LoggingConfig,
    AppConfig,
    PluginConfig,
    EventBusConfig,
    AIConfig,
    SecurityConfig,
    UIConfig,
    StorageConfig,
    MetricsConfig,
    TestingConfig,
    SmallPanguConfig
)

from .loader import (
    ConfigLoader,
    get_config_loader,
    load_config,
    reload_config
)

from .manager import (
    ConfigManager,
    get_config_manager,
    reset_config_manager
)

# 主要导出
__all__ = [
    # 配置模型
    "SmallPanguConfig",
    "LogLevel",
    "Theme",
    "Language",
    "StorageType",
    "SwitchStrategy",
    "ConfirmLevel",
    "OperationType",
    
    # 配置子模型
    "LogHandlerConfig",
    "LoggingConfig",
    "AppConfig",
    "PluginConfig",
    "EventBusConfig",
    "AIConfig",
    "SecurityConfig",
    "UIConfig",
    "StorageConfig",
    "MetricsConfig",
    "TestingConfig",
    
    # 配置加载器
    "ConfigLoader",
    "get_config_loader",
    "load_config",
    "reload_config",
    
    # 配置管理器
    "ConfigManager",
    "get_config_manager",
    "reset_config_manager"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "小盘古项目组"