"""
UI管理器

管理UI系统的生命周期、主题、语言和组件注册。
"""

import customtkinter as ctk
import logging
from typing import Dict, List, Optional, Any, Type, Callable
from pathlib import Path

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..plugins.base import UIPlugin, PluginType
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class UIManager:
    """
    UI管理器
    
    负责：
    1. 管理UI框架初始化和生命周期
    2. 主题管理（深色/浅色主题切换）
    3. 国际化支持
    4. UI组件注册和管理
    5. 与插件系统集成
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container,
        app_name: str = "小盘古"
    ):
        """
        初始化UI管理器
        
        Args:
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            app_name: 应用名称
        """
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._container = container
        self._app_name = app_name
        
        # UI配置
        self._ui_config = config_manager.config.ui
        
        # UI框架状态
        self._is_initialized = False
        self._is_running = False
        self._root_window = None
        
        # 组件注册表
        self._widget_registry: Dict[str, Type[ctk.CTkBaseClass]] = {}
        self._ui_plugins: Dict[str, UIPlugin] = {}
        
        # 主题管理器（延迟初始化）
        self._theme_manager = None
        self._i18n_manager = None
        
        logger.debug_struct("UI管理器初始化", app_name=app_name)
    
    def initialize(self) -> None:
        """
        初始化UI系统
        """
        if self._is_initialized:
            logger.warning("UI系统已初始化，跳过重复初始化")
            return
        
        logger.info("初始化UI系统")
        
        try:
            # 1. 初始化CustomTkinter框架
            self._initialize_framework()
            
            # 2. 初始化主题管理器
            self._initialize_theme_manager()
            
            # 3. 初始化国际化管理器
            self._initialize_i18n_manager()
            
            # 4. 注册内置组件
            self._register_builtin_widgets()
            
            # 5. 订阅UI相关事件
            self._subscribe_events()
            
            self._is_initialized = True
            logger.info("UI系统初始化完成")
            
        except Exception as e:
            logger.error("UI系统初始化失败", exc_info=True)
            raise UIError(f"UI系统初始化失败: {e}")
    
    def _initialize_framework(self) -> None:
        """初始化UI框架"""
        logger.debug("初始化UI框架")
        
        # 设置CustomTkinter外观模式
        appearance_mode = self._ui_config.theme
        if appearance_mode == "system":
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(appearance_mode)
        
        # 设置颜色主题
        ctk.set_default_color_theme("blue")  # 默认蓝色主题
        
        # 获取窗口配置
        window_width = self._ui_config.window_width
        window_height = self._ui_config.window_height
        min_width = self._ui_config.min_width
        min_height = self._ui_config.min_height
        
        logger.info(f"UI窗口配置: {window_width}x{window_height}, 最小: {min_width}x{min_height}")
        
        # 创建根窗口（但不立即显示）
        self._root_window = ctk.CTk()
        self._root_window.title(self._app_name)
        
        # 设置窗口尺寸
        geometry_str = f"{window_width}x{window_height}"
        self._root_window.geometry(geometry_str)
        self._root_window.minsize(min_width, min_height)
        self._root_window.update()  # 强制更新窗口几何尺寸
        
        logger.info(f"窗口几何设置: {geometry_str}, 实际: {self._root_window.winfo_geometry()}")
        
        # 设置窗口图标（如果有）
        # 这里可以添加图标设置逻辑
        
        logger.debug_struct(
            "UI框架初始化完成",
            theme=self._ui_config.theme,
            window_size=f"{window_width}x{window_height}"
        )
    
    def _initialize_theme_manager(self) -> None:
        """初始化主题管理器"""
        logger.debug("初始化主题管理器")
        
        # 延迟导入以避免循环依赖
        from .theme import ThemeManager
        
        self._theme_manager = ThemeManager(
            config_manager=self._config_manager,
            event_bus=self._event_bus
        )
        self._theme_manager.initialize()
        
        logger.debug("主题管理器初始化完成")
    
    def _initialize_i18n_manager(self) -> None:
        """初始化国际化管理器"""
        logger.debug("初始化国际化管理器")
        
        # 延迟导入以避免循环依赖
        from .i18n import I18nManager
        
        self._i18n_manager = I18nManager(
            config_manager=self._config_manager,
            event_bus=self._event_bus
        )
        self._i18n_manager.initialize()
        
        logger.debug("国际化管理器初始化完成")
    
    def _register_builtin_widgets(self) -> None:
        """注册内置UI组件"""
        logger.debug("注册内置UI组件")
        
        # 延迟导入以避免循环依赖
        from .widgets import (
            BaseWidget, Panel, Card, Button, 
            Label, TextArea, InputField, ScrollPanel
        )
        
        # 注册常用组件
        widgets = {
            "panel": Panel,
            "card": Card,
            "button": Button,
            "label": Label,
            "textarea": TextArea,
            "input": InputField,
            "scrollpanel": ScrollPanel
        }
        
        for name, widget_class in widgets.items():
            self.register_widget(name, widget_class)
        
        logger.debug_struct("内置组件注册完成", widget_count=len(widgets))
    
    def _subscribe_events(self) -> None:
        """订阅UI相关事件"""
        logger.debug("订阅UI相关事件")
        
        # 主题切换事件
        self._event_bus.subscribe("theme.changed", self._handle_theme_changed)
        
        # 语言切换事件
        self._event_bus.subscribe("language.changed", self._handle_language_changed)
        
        # 窗口事件
        self._event_bus.subscribe("window.*", self._handle_window_event)
        
        logger.debug("UI事件订阅完成")
    
    def register_widget(self, name: str, widget_class: Type[ctk.CTkBaseClass]) -> None:
        """
        注册UI组件
        
        Args:
            name: 组件名称
            widget_class: 组件类
        """
        if name in self._widget_registry:
            logger.warning_struct("UI组件重复注册", name=name)
            return
        
        self._widget_registry[name] = widget_class
        logger.debug_struct("UI组件注册", name=name, class_name=widget_class.__name__)
    
    def get_widget_class(self, name: str) -> Optional[Type[ctk.CTkBaseClass]]:
        """
        获取UI组件类
        
        Args:
            name: 组件名称
            
        Returns:
            组件类，如果未找到则返回None
        """
        return self._widget_registry.get(name)
    
    def register_ui_plugin(self, plugin: UIPlugin) -> None:
        """
        注册UI插件
        
        Args:
            plugin: UI插件实例
        """
        plugin_name = plugin.name if hasattr(plugin, 'name') else plugin.__class__.__name__
        
        if plugin_name in self._ui_plugins:
            logger.warning_struct("UI插件重复注册", name=plugin_name)
            return
        
        self._ui_plugins[plugin_name] = plugin
        logger.debug_struct("UI插件注册", name=plugin_name)
        
        # 发布插件注册事件
        self._event_bus.publish("ui.plugin.registered", {
            "plugin_name": plugin_name,
            "plugin_type": PluginType.UI_COMPONENT.value
        })
    
    def create_widget(self, widget_type: str, parent, **kwargs) -> Optional[ctk.CTkBaseClass]:
        """
        创建UI组件
        
        Args:
            widget_type: 组件类型
            parent: 父组件
            **kwargs: 组件参数
            
        Returns:
            创建的组件，如果类型未找到则返回None
        """
        widget_class = self.get_widget_class(widget_type)
        if widget_class is None:
            logger.warning_struct("UI组件类型未找到", type=widget_type)
            return None
        
        try:
            widget = widget_class(parent, **kwargs)
            logger.debug_struct("UI组件创建成功", type=widget_type)
            return widget
        except Exception as e:
            logger.error_struct("UI组件创建失败", type=widget_type, error=str(e))
            return None
    
    def start(self) -> None:
        """
        启动UI系统（显示主窗口）
        """
        if not self._is_initialized:
            raise UIError("UI系统未初始化，请先调用initialize()")
        
        if self._is_running:
            logger.warning("UI系统已在运行中")
            return
        
        logger.info("启动UI系统")
        
        try:
            # 创建主窗口
            from .window import MainWindow
            main_window = MainWindow(
                root=self._root_window,
                ui_manager=self,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            # 初始化主窗口（创建布局）
            main_window.initialize()
            
            # 将主窗口注册到容器
            self._container.register_instance(MainWindow, main_window)
            
            # 发布UI启动事件
            self._event_bus.publish("ui.started", {
                "timestamp": "now",  # 这里应该使用实际时间戳
                "theme": self._ui_config.theme,
                "language": self._ui_config.language
            })
            
            self._is_running = True
            logger.info("UI系统启动完成")
            
        except Exception as e:
            logger.error("UI系统启动失败", exc_info=True)
            raise UIError(f"UI系统启动失败: {e}")
    
    def run(self) -> None:
        """
        运行UI主循环（阻塞调用）
        """
        if not self._is_running:
            self.start()
        
        logger.info("UI系统进入主循环")
        
        try:
            self._root_window.mainloop()
        except KeyboardInterrupt:
            logger.info("收到键盘中断，停止UI系统")
            self.stop()
        except Exception as e:
            logger.error("UI主循环异常", exc_info=True)
            self.stop()
            raise
    
    def stop(self) -> None:
        """
        停止UI系统
        """
        if not self._is_running:
            logger.warning("UI系统未运行，无需停止")
            return
        
        logger.info("停止UI系统")
        
        try:
            # 发布UI停止事件
            self._event_bus.publish("ui.stopped", {
                "timestamp": "now"  # 这里应该使用实际时间戳
            })
            
            # 销毁根窗口
            if self._root_window:
                self._root_window.destroy()
            
            self._is_running = False
            logger.info("UI系统已停止")
            
        except Exception as e:
            logger.error("UI系统停止失败", exc_info=True)
            raise UIError(f"UI系统停止失败: {e}")
    
    def shutdown(self) -> None:
        """
        关闭UI系统（完全清理）
        """
        logger.info("关闭UI系统")
        
        try:
            if self._is_running:
                self.stop()
            
            # 清理主题管理器
            if self._theme_manager:
                self._theme_manager.shutdown()
            
            # 清理国际化管理器
            if self._i18n_manager:
                self._i18n_manager.shutdown()
            
            # 清理组件注册表
            self._widget_registry.clear()
            self._ui_plugins.clear()
            
            self._is_initialized = False
            logger.info("UI系统关闭完成")
            
        except Exception as e:
            logger.error("UI系统关闭失败", exc_info=True)
            raise UIError(f"UI系统关闭失败: {e}")
    
    # 事件处理
    def _handle_theme_changed(self, event) -> None:
        """处理主题切换事件"""
        logger.debug_struct("处理主题切换事件", data=event.data)
        
        if self._theme_manager:
            new_theme = event.data.get("theme")
            if new_theme:
                self._theme_manager.set_theme(new_theme)
    
    def _handle_language_changed(self, event) -> None:
        """处理语言切换事件"""
        logger.debug_struct("处理语言切换事件", data=event.data)
        
        if self._i18n_manager:
            new_language = event.data.get("language")
            if new_language:
                self._i18n_manager.set_language(new_language)
    
    def _handle_window_event(self, event) -> None:
        """处理窗口事件"""
        logger.debug_struct("处理窗口事件", event_type=event.type, data=event.data)
        
        # 这里可以添加窗口事件的具体处理逻辑
        pass
    
    # 属性访问
    @property
    def root_window(self):
        """获取根窗口"""
        return self._root_window
    
    @property
    def theme_manager(self):
        """获取主题管理器"""
        return self._theme_manager
    
    @property
    def i18n_manager(self):
        """获取国际化管理器"""
        return self._i18n_manager
    
    @property
    def is_initialized(self) -> bool:
        """UI系统是否已初始化"""
        return self._is_initialized
    
    @property
    def is_running(self) -> bool:
        """UI系统是否正在运行"""
        return self._is_running
    
    @property
    def widget_count(self) -> int:
        """注册的UI组件数量"""
        return len(self._widget_registry)
    
    @property
    def plugin_count(self) -> int:
        """注册的UI插件数量"""
        return len(self._ui_plugins)
    
    def get_status(self) -> Dict[str, Any]:
        """获取UI系统状态"""
        return {
            "initialized": self._is_initialized,
            "running": self._is_running,
            "theme": self._ui_config.theme,
            "language": self._ui_config.language,
            "widget_count": self.widget_count,
            "plugin_count": self.plugin_count,
            "window_size": f"{self._ui_config.window_width}x{self._ui_config.window_height}"
        }


# 便捷函数
def create_ui_manager(
    config_manager: ConfigManager,
    event_bus: EventBus,
    container: Container,
    app_name: str = "小盘古"
) -> UIManager:
    """创建UI管理器实例"""
    return UIManager(config_manager, event_bus, container, app_name)