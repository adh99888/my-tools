"""
插件系统 - 小盘古插件框架

提供完整的插件化架构支持：
1. 插件定义和协议
2. 插件发现和加载
3. 插件注册和管理
4. 插件上下文和生命周期
"""

from .base import (
    PluginType,
    PluginStatus,
    PluginMetadata,
    PluginInfo,
    PluginContext,
    Plugin,
    ToolPlugin,
    AIProviderPlugin,
    UIPlugin,
    create_plugin_metadata,
    plugin
)

# 其他模块将延迟导入
try:
    from .loader import PluginLoader, create_plugin_loader
except ImportError:
    PluginLoader = create_plugin_loader = None  # 类型: ignore

PluginRegistry = None

__all__ = [
    # 基础类型
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginInfo",
    "PluginContext",
    
    # 插件基类
    "Plugin",
    "ToolPlugin",
    "AIProviderPlugin",
    "UIPlugin",
    
    # 工具函数
    "create_plugin_metadata",
    "plugin",
    
    # 加载器
    "PluginLoader",
    "create_plugin_loader",
    
    # 管理类（稍后定义）
    "PluginRegistry"
]

__version__ = "1.0.0"
__author__ = "小盘古项目组"