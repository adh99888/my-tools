"""
小盘古 - 轻量级、插件化的个人AI数字分身助手
版本 4.0.0
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("smallpangu")
except importlib.metadata.PackageNotFoundError:
    __version__ = "4.0.0-dev"

__author__ = "小盘古项目组"
__license__ = "MIT"

# 核心框架导出 - 使用延迟导入以避免循环依赖
try:
    from .config.manager import ConfigManager
except ImportError:
    ConfigManager = None  # 类型: ignore

try:
    from .core.events import EventBus
    from .core.di import Container
    from .core.logging import setup_logging, get_logger
except ImportError:
    EventBus = Container = None  # 类型: ignore
    def setup_logging(*args, **kwargs):
        pass
    def get_logger(name):
        import logging
        return logging.getLogger(name)

# 其他模块延迟导入
try:
    from .app import SmallPanguApp
except ImportError:
    SmallPanguApp = None  # 类型: ignore

try:
    from .plugins.base import Plugin, PluginContext
    from .plugins.loader import PluginLoader
except ImportError:
    Plugin = PluginContext = PluginLoader = None  # 类型: ignore

try:
    from .api.types import Message, Conversation, AIResponse
    from .api.contracts import AIProvider, ToolProvider
except ImportError:
    Message = Conversation = AIResponse = None  # 类型: ignore
    AIProvider = ToolProvider = None  # 类型: ignore

# 公共API
__all__ = [
    # 配置管理
    "ConfigManager",
    
    # 核心框架
    "EventBus",
    "Container",
    "setup_logging",
    "get_logger",
    
    # 应用核心（可能为None）
    "SmallPanguApp",
    
    # 插件系统（可能为None）
    "Plugin",
    "PluginContext",
    "PluginLoader",
    
    # API类型（可能为None）
    "Message",
    "Conversation",
    "AIResponse",
    
    # 接口契约（可能为None）
    "AIProvider",
    "ToolProvider",
]

# 应用实例（单例模式）
_app_instance = None

def get_app():
    """获取应用单例实例"""
    global _app_instance
    if _app_instance is None:
        try:
            from .app import SmallPanguApp
            _app_instance = SmallPanguApp()
        except ImportError:
            _app_instance = None
    return _app_instance

def run_app(config_path: str = None):
    """运行小盘古应用"""
    app = get_app()
    if app is None:
        raise ImportError("应用模块未安装或初始化失败")
    app.initialize(config_path)
    app.run()

# 模块初始化时设置默认日志
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())