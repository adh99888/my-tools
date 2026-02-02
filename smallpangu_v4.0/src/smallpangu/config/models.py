"""
配置数据模型 - 基于Pydantic的强类型配置定义
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Literal, Union
from pathlib import Path

from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Theme(str, Enum):
    """UI主题枚举"""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class Language(str, Enum):
    """界面语言枚举"""
    ZH_CN = "zh-CN"
    EN_US = "en-US"


class StorageType(str, Enum):
    """存储类型枚举"""
    FILE = "file"
    SQLITE = "sqlite"
    REDIS = "redis"


class SwitchStrategy(str, Enum):
    """AI模型切换策略枚举"""
    COST_EFFECTIVE = "cost_effective"
    CAPABILITY_PRIORITY = "capability_priority"
    CONTEXT_PRIORITY = "context_priority"


class ConfirmLevel(str, Enum):
    """操作确认级别枚举"""
    NOTIFICATION = "notification"
    SIMPLE = "simple"
    DETAILED = "detailed"


class OperationType(str, Enum):
    """安全操作类型枚举"""
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_CREATE = "file.create"
    FILE_DELETE = "file.delete"
    COMMAND_EXECUTE = "command.execute"


class LogHandlerConfig(BaseModel):
    """日志处理器配置"""
    enabled: bool = Field(default=True, description="是否启用")
    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    format: str = Field(default="", description="日志格式")
    filename: Optional[str] = Field(default=None, description="日志文件路径")
    max_size_mb: Optional[int] = Field(default=None, ge=1, description="最大文件大小(MB)")
    backup_count: Optional[int] = Field(default=None, ge=0, description="备份数量")


class LoggingConfig(BaseModel):
    """日志配置"""
    handlers: Dict[str, LogHandlerConfig] = Field(
        default_factory=dict,
        description="日志处理器配置"
    )
    
    @validator("handlers")
    def validate_handlers(cls, v):
        """验证至少有一个启用的处理器"""
        enabled_handlers = [h for h in v.values() if h.enabled]
        if not enabled_handlers:
            raise ValueError("至少需要启用一个日志处理器")
        return v


class AppConfig(BaseModel):
    """应用配置"""
    name: str = Field(default="小盘古", description="应用名称")
    version: str = Field(default="4.0.0", description="应用版本")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    data_dir: str = Field(default="./data", description="数据存储目录")
    cache_dir: str = Field(default="./.cache", description="缓存目录")
    max_workers: int = Field(default=4, ge=1, description="最大并发工作线程数")
    request_timeout: int = Field(default=30, ge=1, description="API请求超时时间（秒）")
    enable_profiling: bool = Field(default=False, description="是否启用性能分析")
    check_for_updates: bool = Field(default=True, description="是否检查更新")
    update_check_interval: int = Field(default=86400, ge=60, description="检查间隔（秒）")
    debug_mode: bool = Field(default=False, description="调试模式")
    hot_reload: bool = Field(default=False, description="热重载支持")
    
    @validator("data_dir", "cache_dir")
    def validate_dirs(cls, v):
        """验证目录路径"""
        if not v:
            raise ValueError("目录路径不能为空")
        # 尝试转换为Path对象进行基本验证
        Path(v)
        return v


class PluginConfig(BaseModel):
    """插件配置"""
    search_paths: List[str] = Field(
        default_factory=lambda: ["./plugins", "~/.smallpangu/plugins"],
        description="插件搜索路径（按顺序搜索）"
    )
    enabled: List[str] = Field(
        default_factory=list,
        description="默认启用的插件（插件模块路径）"
    )
    config: Dict[str, Any] = Field(
        default_factory=lambda: {"auto_reload": False, "sandbox_mode": True},
        description="插件配置"
    )
    loading_strategy: Literal["eager", "lazy"] = Field(
        default="lazy",
        description="插件加载策略: eager-启动时加载, lazy-使用时加载"
    )


class EventBusConfig(BaseModel):
    """事件总线配置"""
    max_queue_size: int = Field(default=1000, ge=10, description="最大事件队列大小")
    worker_threads: int = Field(default=2, ge=1, le=32, description="事件处理工作线程数")
    enable_debug_log: bool = Field(default=False, description="是否启用事件调试日志")


class AIConfig(BaseModel):
    """AI配置"""
    default_provider: str = Field(default="deepseek", description="默认AI提供商")
    max_tokens: int = Field(default=4000, ge=1, le=128000, description="默认最大token数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="默认温度参数")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="默认top_p参数")
    max_context_length: int = Field(default=8000, ge=100, le=1000000, description="最大上下文长度（token）")
    enable_context_summary: bool = Field(default=True, description="是否启用上下文摘要")
    summary_threshold: int = Field(default=6000, ge=100, description="开始摘要的阈值")
    switch_strategy: SwitchStrategy = Field(default=SwitchStrategy.COST_EFFECTIVE, description="模型切换策略")
    enable_auto_switch: bool = Field(default=True, description="是否启用自动切换")
    enable_debug_log: bool = Field(default=False, description="是否启用调试日志")
    log_requests: bool = Field(default=False, description="是否记录AI请求和响应")


class SecurityConfig(BaseModel):
    """安全配置"""
    enable_encryption: bool = Field(default=True, description="是否启用加密")
    master_key_path: str = Field(default="~/.smallpangu/master.key", description="主密钥存储路径")
    backup_enabled: bool = Field(default=True, description="是否启用自动备份")
    max_backup_count: int = Field(default=10, ge=0, description="最大备份数量")
    confirm_levels: Dict[str, ConfirmLevel] = Field(
        default_factory=lambda: {
            "low_risk": ConfirmLevel.NOTIFICATION,
            "medium_risk": ConfirmLevel.SIMPLE,
            "high_risk": ConfirmLevel.DETAILED
        },
        description="操作确认级别"
    )
    allowed_operations: List[OperationType] = Field(
        default_factory=lambda: [
            OperationType.FILE_READ,
            OperationType.FILE_WRITE,
            OperationType.FILE_CREATE
        ],
        description="允许的操作类型"
    )


class UIConfig(BaseModel):
    """UI配置"""
    framework: Literal["customtkinter", "tkinter", "qt"] = Field(
        default="customtkinter",
        description="UI框架"
    )
    theme: Theme = Field(default=Theme.DARK, description="UI主题")
    language: Language = Field(default=Language.ZH_CN, description="界面语言")
    window_width: int = Field(default=1280, ge=400, description="窗口宽度")
    window_height: int = Field(default=720, ge=300, description="窗口高度")
    min_width: int = Field(default=800, ge=200, description="最小宽度")
    min_height: int = Field(default=600, ge=200, description="最小高度")
    font_family: str = Field(default="Microsoft YaHei", description="字体家族")
    font_size: int = Field(default=12, ge=8, le=72, description="字体大小")
    chat_history_limit: int = Field(default=100, ge=10, description="保留的聊天记录数量")
    auto_scroll: bool = Field(default=True, description="是否自动滚动")
    markdown_render: bool = Field(default=True, description="是否渲染Markdown")
    show_developer_tools: bool = Field(default=False, description="显示开发者工具")
    enable_inspector: bool = Field(default=False, description="启用UI检查器")


class StorageConfig(BaseModel):
    """存储配置"""
    type: StorageType = Field(default=StorageType.FILE, description="存储类型")
    file: Dict[str, Any] = Field(
        default_factory=lambda: {"data_dir": "./data", "backup_dir": "./backups"},
        description="文件存储配置"
    )
    sqlite: Dict[str, Any] = Field(
        default_factory=lambda: {"database_path": "./data/smallpangu.db"},
        description="SQLite存储配置"
    )
    cache: Dict[str, Any] = Field(
        default_factory=lambda: {"enabled": True, "max_size_mb": 100, "ttl_seconds": 3600},
        description="缓存配置"
    )


class MetricsConfig(BaseModel):
    """指标收集配置"""
    enabled: bool = Field(default=True, description="是否启用指标收集")
    export_interval: int = Field(default=60, ge=1, description="导出间隔（秒）")
    exporters: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "console": {"enabled": False},
            "file": {"enabled": True, "path": "./logs/metrics.log"},
            "prometheus": {"enabled": False, "port": 9090}
        },
        description="导出目标配置"
    )


class TestingConfig(BaseModel):
    """测试配置（开发环境）"""
    enable_mock_providers: bool = Field(default=False, description="启用模拟AI提供商")
    mock_response_delay: float = Field(default=0.1, ge=0.0, description="模拟响应延迟（秒）")
    enable_failure_testing: bool = Field(default=False, description="是否启用故障测试模式")


class SmallPanguConfig(BaseSettings):
    """小盘古完整配置模型"""
    model_config = ConfigDict(
        env_prefix="SMALLPANGU_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    app: AppConfig = Field(default_factory=AppConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    event_bus: EventBusConfig = Field(default_factory=EventBusConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    testing: Optional[TestingConfig] = Field(default=None, description="测试配置（仅开发环境）")
    
    # 环境变量配置
    environment: str = Field(default="production", description="运行环境")
    config_path: Optional[str] = Field(default=None, description="配置文件路径")
    
    @validator("environment")
    def validate_environment(cls, v):
        """验证环境值"""
        valid_environments = ["production", "development", "testing", "staging"]
        if v not in valid_environments:
            raise ValueError(f"环境必须是: {', '.join(valid_environments)}")
        return v


# 配置模型导出
__all__ = [
    "LogLevel",
    "Theme",
    "Language",
    "StorageType",
    "SwitchStrategy",
    "ConfirmLevel",
    "OperationType",
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
    "SmallPanguConfig"
]