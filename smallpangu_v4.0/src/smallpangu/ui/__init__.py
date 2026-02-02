"""
小盘古UI框架

提供现代化、模块化、可插拔的UI系统，支持主题切换、国际化、响应式布局。
"""

from .manager import UIManager
from .window import BaseWindow, MainWindow
from .widgets import BaseWidget, Panel, Card, Button, Label, TextArea
from .theme import ThemeManager
from .i18n import I18nManager
from .chat_interface import ChatInterface, ChatView, ChatMessage, MessageRole, MessageStatus
from .plugin_interface import PluginViewType, PluginFilter, PluginCard, PluginInterface, PluginView
from .config_interface import ConfigViewType, ConfigSection, ConfigItem, ConfigCard, ConfigInterface, ConfigView
from .monitor_interface import MonitorViewType, MetricType, MetricData, MetricCard, MonitorInterface, MonitorView, MetricHistory, ChartCanvas, EnhancedMonitorInterface
from .help_interface import HelpViewType, HelpSection, HelpCard, HelpInterface, HelpView

__version__ = "1.0.0"
__author__ = "小盘古项目组"

__all__ = [
    "UIManager",
    "BaseWindow",
    "MainWindow",
    "BaseWidget",
    "Panel",
    "Card",
    "Button",
    "Label",
    "TextArea",
    "ThemeManager",
    "I18nManager",
    "ChatInterface",
    "ChatView",
    "ChatMessage",
    "MessageRole",
    "MessageStatus",
    "PluginViewType",
    "PluginFilter",
    "PluginCard",
    "PluginInterface",
    "PluginView",
    "ConfigViewType",
    "ConfigSection",
    "ConfigItem",
    "ConfigCard",
    "ConfigInterface",
    "ConfigView",
    "MonitorViewType",
    "MetricType",
    "MetricData",
    "MetricCard",
    "MonitorInterface",
    "MonitorView",
    "MetricHistory",
    "ChartCanvas",
    "EnhancedMonitorInterface",
    "HelpViewType",
    "HelpSection",
    "HelpCard",
    "HelpInterface",
    "HelpView"
]