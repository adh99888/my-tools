"""
主题管理器

管理UI主题（深色/浅色模式），支持自定义主题和动态切换。
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..core.events import EventBus
from ..config.manager import ConfigManager
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class ThemeManager:
    """
    主题管理器
    
    负责：
    1. 管理UI主题配置
    2. 支持深色/浅色模式切换
    3. 管理自定义主题
    4. 动态主题切换通知
    """
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        """
        初始化主题管理器
        
        Args:
            config_manager: 配置管理器
            event_bus: 事件总线
        """
        self._config_manager = config_manager
        self._event_bus = event_bus
        
        # 主题配置
        self._ui_config = config_manager.config.ui
        
        # 主题状态
        self._current_theme = self._ui_config.theme
        self._available_themes = ["dark", "light", "system"]
        self._custom_themes: Dict[str, Dict[str, Any]] = {}
        
        # 主题监听器（用于实时更新UI）
        self._theme_listeners: List[callable] = []
        
        logger.debug_struct("主题管理器初始化", current_theme=self._current_theme)
    
    def initialize(self) -> None:
        """
        初始化主题管理器
        """
        logger.debug("初始化主题管理器")
        
        try:
            # 1. 加载自定义主题
            self._load_custom_themes()
            
            # 2. 应用当前主题
            self._apply_theme(self._current_theme)
            
            # 3. 订阅主题相关事件
            self._subscribe_events()
            
            logger.info_struct("主题管理器初始化完成", theme=self._current_theme)
            
        except Exception as e:
            logger.error("主题管理器初始化失败", exc_info=True)
            raise UIError(f"主题管理器初始化失败: {e}")
    
    def _load_custom_themes(self) -> None:
        """加载自定义主题"""
        logger.debug("加载自定义主题")
        
        # 这里可以从配置文件或主题目录加载自定义主题
        # 目前使用内置的默认主题
        
        # 内置主题定义
        builtin_themes = {
            "blue": {
                "name": "蓝色主题",
                "description": "默认蓝色主题",
                "colors": {
                    "primary": "#2b5b84",
                    "secondary": "#3a7ebf",
                    "accent": "#1e3a5f",
                    "text": "#ffffff",
                    "background": "#1a1a1a",
                    "surface": "#2d2d2d"
                }
            },
            "green": {
                "name": "绿色主题",
                "description": "环保绿色主题",
                "colors": {
                    "primary": "#2d7d46",
                    "secondary": "#3d8b5a",
                    "accent": "#1e5c32",
                    "text": "#ffffff",
                    "background": "#1a1a1a",
                    "surface": "#2d2d2d"
                }
            },
            "purple": {
                "name": "紫色主题",
                "description": "优雅紫色主题",
                "colors": {
                    "primary": "#6a4c9c",
                    "secondary": "#7b5cad",
                    "accent": "#4d3673",
                    "text": "#ffffff",
                    "background": "#1a1a1a",
                    "surface": "#2d2d2d"
                }
            }
        }
        
        self._custom_themes.update(builtin_themes)
        logger.debug_struct("自定义主题加载完成", theme_count=len(builtin_themes))
    
    def _subscribe_events(self) -> None:
        """订阅主题相关事件"""
        logger.debug("订阅主题相关事件")
        
        # 主题切换请求
        self._event_bus.subscribe("theme.change_request", self._handle_theme_change_request)
        
        # 主题配置更新
        self._event_bus.subscribe("config.updated", self._handle_config_updated)
        
        logger.debug("主题事件订阅完成")
    
    def _apply_theme(self, theme: str) -> None:
        """
        应用主题
        
        Args:
            theme: 主题名称（dark, light, system 或自定义主题）
        """
        logger.debug_struct("应用主题", theme=theme)
        
        if theme in ["dark", "light", "system"]:
            # 系统主题
            ctk.set_appearance_mode(theme)
            self._current_theme = theme
            
            # 更新配置
            self._update_theme_config(theme)
            
        elif theme in self._custom_themes:
            # 自定义主题
            custom_theme = self._custom_themes[theme]
            self._apply_custom_theme(custom_theme)
            self._current_theme = theme
            
            # 更新配置
            self._update_theme_config(theme)
            
        else:
            logger.warning_struct("未知主题，使用默认主题", requested_theme=theme)
            # 回退到默认主题
            ctk.set_appearance_mode("dark")
            self._current_theme = "dark"
        
        # 通知主题监听器
        self._notify_theme_listeners()
        
        # 发布主题已更改事件
        self._event_bus.publish("theme.changed", {
            "theme": self._current_theme,
            "theme_type": "system" if theme in ["dark", "light", "system"] else "custom"
        })
        
        logger.info_struct("主题应用完成", theme=self._current_theme)
    
    def _apply_custom_theme(self, theme_config: Dict[str, Any]) -> None:
        """
        应用自定义主题
        
        Args:
            theme_config: 主题配置
        """
        logger.debug_struct("应用自定义主题", theme_name=theme_config.get("name", "unknown"))
        
        # 这里可以实现自定义主题的应用逻辑
        # 目前CustomTkinter主要支持外观模式，颜色主题需要更多配置
        
        # 暂时使用系统深色模式作为基础
        ctk.set_appearance_mode("dark")
        
        # 可以在这里设置自定义颜色
        colors = theme_config.get("colors", {})
        if colors:
            # 设置CustomTkinter自定义颜色
            # 注意：CustomTkinter的颜色主题设置有限制
            pass
    
    def _update_theme_config(self, theme: str) -> None:
        """
        更新主题配置
        
        Args:
            theme: 主题名称
        """
        # 更新内存中的配置
        self._ui_config.theme = theme
        
        # 可以在这里保存配置到文件（如果需要持久化）
        # self._config_manager.update_config({"ui": {"theme": theme}})
    
    def _notify_theme_listeners(self) -> None:
        """通知主题监听器"""
        for listener in self._theme_listeners:
            try:
                listener(self._current_theme)
            except Exception as e:
                logger.warning_struct("主题监听器通知失败", error=str(e))
    
    # 事件处理
    def _handle_theme_change_request(self, event) -> None:
        """处理主题切换请求"""
        new_theme = event.data.get("theme")
        if new_theme:
            logger.debug_struct("收到主题切换请求", new_theme=new_theme)
            self.set_theme(new_theme)
    
    def _handle_config_updated(self, event) -> None:
        """处理配置更新事件"""
        config_data = event.data.get("config", {})
        ui_config = config_data.get("ui", {})
        
        if "theme" in ui_config:
            new_theme = ui_config["theme"]
            if new_theme != self._current_theme:
                logger.debug_struct("配置更新触发主题切换", new_theme=new_theme)
                self.set_theme(new_theme)
    
    # 公共API
    def set_theme(self, theme: str) -> bool:
        """
        设置主题
        
        Args:
            theme: 主题名称
            
        Returns:
            是否成功设置主题
        """
        if theme not in self._available_themes and theme not in self._custom_themes:
            logger.warning_struct("主题不存在", requested_theme=theme)
            return False
        
        try:
            self._apply_theme(theme)
            return True
        except Exception as e:
            logger.error_struct("主题设置失败", theme=theme, error=str(e))
            return False
    
    def get_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme
    
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return self._available_themes + list(self._custom_themes.keys())
    
    def get_theme_info(self, theme: str) -> Optional[Dict[str, Any]]:
        """
        获取主题信息
        
        Args:
            theme: 主题名称
            
        Returns:
            主题信息字典，如果主题不存在则返回None
        """
        if theme in ["dark", "light", "system"]:
            return {
                "name": theme.capitalize(),
                "description": f"系统{theme}主题",
                "type": "system"
            }
        elif theme in self._custom_themes:
            info = self._custom_themes[theme].copy()
            info["type"] = "custom"
            return info
        
        return None
    
    def register_theme_listener(self, listener: callable) -> None:
        """
        注册主题监听器
        
        Args:
            listener: 监听器函数，接收主题名称作为参数
        """
        if listener not in self._theme_listeners:
            self._theme_listeners.append(listener)
            logger.debug_struct("主题监听器注册", listener_count=len(self._theme_listeners))
    
    def unregister_theme_listener(self, listener: callable) -> bool:
        """
        取消注册主题监听器
        
        Args:
            listener: 监听器函数
            
        Returns:
            是否成功取消注册
        """
        if listener in self._theme_listeners:
            self._theme_listeners.remove(listener)
            logger.debug_struct("主题监听器取消注册", listener_count=len(self._theme_listeners))
            return True
        return False
    
    def add_custom_theme(self, name: str, theme_config: Dict[str, Any]) -> bool:
        """
        添加自定义主题
        
        Args:
            name: 主题名称
            theme_config: 主题配置
            
        Returns:
            是否成功添加
        """
        if name in self._custom_themes:
            logger.warning_struct("自定义主题已存在", name=name)
            return False
        
        # 验证主题配置
        required_fields = ["name", "description", "colors"]
        for field in required_fields:
            if field not in theme_config:
                logger.warning_struct("自定义主题缺少必要字段", name=name, missing_field=field)
                return False
        
        self._custom_themes[name] = theme_config
        logger.info_struct("自定义主题添加成功", name=name)
        
        # 发布主题添加事件
        self._event_bus.publish("theme.added", {
            "theme_name": name,
            "theme_config": theme_config
        })
        
        return True
    
    def remove_custom_theme(self, name: str) -> bool:
        """
        移除自定义主题
        
        Args:
            name: 主题名称
            
        Returns:
            是否成功移除
        """
        if name not in self._custom_themes:
            logger.warning_struct("自定义主题不存在", name=name)
            return False
        
        # 不能移除当前使用的主题
        if self._current_theme == name:
            logger.warning_struct("不能移除当前使用的主题", name=name)
            return False
        
        removed_theme = self._custom_themes.pop(name)
        logger.info_struct("自定义主题移除成功", name=name)
        
        # 发布主题移除事件
        self._event_bus.publish("theme.removed", {
            "theme_name": name,
            "theme_config": removed_theme
        })
        
        return True
    
    def get_custom_themes(self) -> Dict[str, Dict[str, Any]]:
        """获取所有自定义主题"""
        return self._custom_themes.copy()
    
    def cycle_theme(self) -> str:
        """
        循环切换主题（dark -> light -> system -> dark）
        
        Returns:
            新的主题名称
        """
        themes = self._available_themes
        current_index = themes.index(self._current_theme) if self._current_theme in themes else 0
        
        next_index = (current_index + 1) % len(themes)
        next_theme = themes[next_index]
        
        self.set_theme(next_theme)
        return next_theme
    
    def shutdown(self) -> None:
        """关闭主题管理器"""
        logger.debug("关闭主题管理器")
        
        # 清理监听器
        self._theme_listeners.clear()
        
        logger.debug("主题管理器已关闭")
    
    # 属性访问
    @property
    def current_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme
    
    @property
    def theme_count(self) -> int:
        """获取主题总数（系统主题 + 自定义主题）"""
        return len(self._available_themes) + len(self._custom_themes)
    
    def get_status(self) -> Dict[str, Any]:
        """获取主题管理器状态"""
        return {
            "current_theme": self._current_theme,
            "theme_type": "system" if self._current_theme in self._available_themes else "custom",
            "available_themes": self.get_available_themes(),
            "custom_theme_count": len(self._custom_themes),
            "listener_count": len(self._theme_listeners)
        }