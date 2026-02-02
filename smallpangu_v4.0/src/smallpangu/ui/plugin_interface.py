"""
插件管理界面

提供现代化的插件管理界面，包括：
1. 插件列表显示
2. 插件启用/禁用控制
3. 插件状态监控
4. 插件配置管理
5. 插件依赖关系可视化
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..plugins.registry import PluginRegistry
from ..plugins.base import PluginType, PluginStatus, PluginInfo, PluginMetadata
from .manager import UIManager
from .widgets import BaseWidget, Panel, ScrollPanel, Card, Button, Label, Switch, TextArea
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class PluginViewType(str, Enum):
    """插件视图类型枚举"""
    LIST = "list"          # 列表视图
    GRID = "grid"          # 网格视图
    DETAIL = "detail"      # 详情视图


@dataclass
class PluginFilter:
    """插件过滤器"""
    plugin_type: Optional[PluginType] = None
    enabled_only: bool = False
    search_text: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def matches(self, plugin_info: PluginInfo) -> bool:
        """检查插件是否匹配过滤器"""
        # 插件类型过滤
        if self.plugin_type and plugin_info.metadata.plugin_type != self.plugin_type:
            return False
        
        # 启用状态过滤
        if self.enabled_only and not plugin_info.is_enabled:
            return False
        
        # 搜索文本过滤
        if self.search_text:
            search_lower = self.search_text.lower()
            name_match = self.search_text.lower() in plugin_info.metadata.name.lower()
            display_match = self.search_text.lower() in plugin_info.metadata.display_name.lower()
            desc_match = self.search_text.lower() in plugin_info.metadata.description.lower()
            tags_match = any(self.search_text.lower() in tag.lower() for tag in plugin_info.metadata.tags)
            
            if not (name_match or display_match or desc_match or tags_match):
                return False
        
        # 标签过滤
        if self.tags:
            plugin_tags = set(tag.lower() for tag in plugin_info.metadata.tags)
            filter_tags = set(tag.lower() for tag in self.tags)
            if not plugin_tags.intersection(filter_tags):
                return False
        
        return True


class PluginCard(BaseWidget):
    """插件卡片组件"""
    
    def __init__(
        self,
        parent,
        plugin_info: PluginInfo,
        widget_id: Optional[str] = None,
        on_toggle: Optional[Callable] = None,
        on_configure: Optional[Callable] = None,
        on_details: Optional[Callable] = None,
        **kwargs
    ):
        """
        初始化插件卡片
        
        Args:
            parent: 父组件
            plugin_info: 插件信息
            widget_id: 组件ID
            on_toggle: 切换启用状态回调
            on_configure: 配置按钮回调
            on_details: 详情按钮回调
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None)
        self._plugin_info = plugin_info
        self._on_toggle = on_toggle
        self._on_configure = on_configure
        self._on_details = on_details
        self._kwargs = kwargs
        
        # UI组件
        self._card = None
        self._title_label = None
        self._status_label = None
        self._toggle_switch = None
        self._configure_button = None
        self._details_button = None
        
        self.initialize()
        
        logger.debug_struct("插件卡片初始化", plugin_name=plugin_info.metadata.name)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建插件卡片组件"""
        # 根据插件状态确定卡片样式
        if self._plugin_info.status == PluginStatus.ERROR:
            card_style = {
                "fg_color": ("#ffebee", "#3a1c1c"),
                "border_color": ("#ef9a9a", "#7b3f3f"),
                "border_width": 2
            }
        elif not self._plugin_info.is_enabled:
            card_style = {
                "fg_color": ("#f5f5f5", "#2d2d2d"),
                "border_color": ("#e0e0e0", "#404040"),
                "border_width": 1
            }
        else:
            card_style = {
                "fg_color": ("white", "gray20"),
                "border_color": ("gray70", "gray40"),
                "border_width": 1
            }
        
        # 创建卡片
        self._card = Card(self._parent, style=card_style)
        card_widget = self._card.get_widget()
        
        # 配置卡片网格
        card_widget.grid_columnconfigure(0, weight=1)  # 内容区域
        card_widget.grid_columnconfigure(1, weight=0)  # 按钮区域
        card_widget.grid_rowconfigure(0, weight=1)
        
        # 左侧内容区域
        content_frame = ctk.CTkFrame(card_widget, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        
        # 标题和状态
        self._create_title_area(content_frame)
        
        # 描述
        self._create_description_area(content_frame)
        
        # 元数据
        self._create_metadata_area(content_frame)
        
        # 右侧按钮区域
        button_frame = ctk.CTkFrame(card_widget, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        
        # 控制按钮
        self._create_control_buttons(button_frame)
        
        return card_widget
    
    def _create_title_area(self, parent) -> None:
        """创建标题区域"""
        # 标题框架
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=0, pady=(0, 5))
        
        # 插件类型图标
        type_icons = {
            PluginType.TOOL: "🛠️",
            PluginType.AI_PROVIDER: "🤖",
            PluginType.UI_COMPONENT: "🎨",
            PluginType.INTEGRATION: "🔌",
            PluginType.STORAGE: "💾",
            PluginType.ANALYTICS: "📊",
            PluginType.CUSTOM: "📦"
        }
        
        type_icon = type_icons.get(self._plugin_info.metadata.plugin_type, "📦")
        icon_label = ctk.CTkLabel(
            title_frame,
            text=type_icon,
            font=("Segoe UI", 16)
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # 插件名称
        self._title_label = ctk.CTkLabel(
            title_frame,
            text=self._plugin_info.metadata.display_name,
            font=("Microsoft YaHei", 14, "bold"),
            anchor="w"
        )
        self._title_label.pack(side="left", fill="x", expand=True)
        
        # 版本标签
        version_label = ctk.CTkLabel(
            title_frame,
            text=f"v{self._plugin_info.metadata.version}",
            font=("Microsoft YaHei", 10),
            text_color=("gray50", "gray60")
        )
        version_label.pack(side="right", padx=(10, 0))
        
        # 注册组件
        self.register_widget("title_frame", title_frame)
        self.register_widget("icon_label", icon_label)
        self.register_widget("version_label", version_label)
    
    def _create_description_area(self, parent) -> None:
        """创建描述区域"""
        if not self._plugin_info.metadata.description:
            return
        
        desc_label = ctk.CTkLabel(
            parent,
            text=self._plugin_info.metadata.description,
            font=("Microsoft YaHei", 11),
            wraplength=300,
            justify="left",
            anchor="w"
        )
        desc_label.pack(fill="x", padx=0, pady=(0, 10))
        
        self.register_widget("desc_label", desc_label)
    
    def _create_metadata_area(self, parent) -> None:
        """创建元数据区域"""
        meta_frame = ctk.CTkFrame(parent, fg_color="transparent")
        meta_frame.pack(fill="x", padx=0, pady=0)
        
        # 作者
        if self._plugin_info.metadata.author:
            author_label = ctk.CTkLabel(
                meta_frame,
                text=f"作者: {self._plugin_info.metadata.author}",
                font=("Microsoft YaHei", 10),
                text_color=("gray50", "gray60")
            )
            author_label.pack(side="left", padx=(0, 10))
        
        # 插件类型
        type_label = ctk.CTkLabel(
            meta_frame,
            text=f"类型: {self._plugin_info.metadata.plugin_type.value}",
            font=("Microsoft YaHei", 10),
            text_color=("gray50", "gray60")
        )
        type_label.pack(side="left", padx=(0, 10))
        
        # 状态标签
        status_colors = {
            PluginStatus.REGISTERED: ("gray", "gray"),
            PluginStatus.INITIALIZED: ("blue", "blue"),
            PluginStatus.STARTED: ("green", "green"),
            PluginStatus.STOPPED: ("orange", "orange"),
            PluginStatus.ERROR: ("red", "red"),
            PluginStatus.DISABLED: ("gray", "gray")
        }
        
        status_color = status_colors.get(self._plugin_info.status, ("gray", "gray"))
        self._status_label = ctk.CTkLabel(
            meta_frame,
            text=f"状态: {self._plugin_info.status.value}",
            font=("Microsoft YaHei", 10, "bold"),
            text_color=status_color
        )
        self._status_label.pack(side="right")
        
        self.register_widget("meta_frame", meta_frame)
        self.register_widget("type_label", type_label)
    
    def _create_control_buttons(self, parent) -> None:
        """创建控制按钮"""
        # 启用/禁用开关
        switch_frame = ctk.CTkFrame(parent, fg_color="transparent")
        switch_frame.pack(fill="x", padx=0, pady=(0, 10))
        
        switch_label = ctk.CTkLabel(
            switch_frame,
            text="启用",
            font=("Microsoft YaHei", 10)
        )
        switch_label.pack(side="left", padx=(0, 5))
        
        self._toggle_switch = Switch(
            switch_frame,
            text="",
            widget_id=f"{self._widget_id}_toggle"
        )
        switch_widget = self._toggle_switch.get_widget()
        switch_widget.pack(side="left")
        
        # 设置初始状态
        is_enabled = self._plugin_info.is_enabled
        self._toggle_switch.set_value(is_enabled)
        
        # 绑定切换事件
        def on_switch_toggled():
            new_value = self._toggle_switch.get_value()
            if self._on_toggle:
                self._on_toggle(self._plugin_info, new_value)
        
        switch_widget.configure(command=on_switch_toggled)
        
        # 配置按钮（如果插件有配置）
        if self._plugin_info.metadata.config_schema:
            self._configure_button = Button(
                parent,
                text="配置",
                widget_id=f"{self._widget_id}_configure",
                width=60,
                height=30
            )
            configure_widget = self._configure_button.get_widget()
            configure_widget.pack(fill="x", padx=0, pady=(0, 5))
            
            # 绑定点击事件
            configure_widget.configure(
                command=lambda: self._on_configure(self._plugin_info) if self._on_configure else None
            )
        
        # 详情按钮
        self._details_button = Button(
            parent,
            text="详情",
            widget_id=f"{self._widget_id}_details",
            width=60,
            height=30,
            fg_color="transparent",
            border_width=1
        )
        details_widget = self._details_button.get_widget()
        details_widget.pack(fill="x", padx=0, pady=0)
        
        # 绑定点击事件
        details_widget.configure(
            command=lambda: self._on_details(self._plugin_info) if self._on_details else None
        )
        
        # 注册组件
        self.register_widget("switch_frame", switch_frame)
        self.register_widget("switch_label", switch_label)
        self.register_widget("toggle_switch", switch_widget)
    
    def update_plugin_info(self, plugin_info: PluginInfo) -> None:
        """
        更新插件信息
        
        Args:
            plugin_info: 新的插件信息
        """
        self._plugin_info = plugin_info
        
        # 更新卡片样式
        if self._card and self._card.get_widget():
            card_widget = self._card.get_widget()
            
            if plugin_info.status == PluginStatus.ERROR:
                card_widget.configure(
                    fg_color=("#ffebee", "#3a1c1c"),
                    border_color=("#ef9a9a", "#7b3f3f")
                )
            elif not plugin_info.is_enabled:
                card_widget.configure(
                    fg_color=("#f5f5f5", "#2d2d2d"),
                    border_color=("#e0e0e0", "#404040")
                )
            else:
                card_widget.configure(
                    fg_color=("white", "gray20"),
                    border_color=("gray70", "gray40")
                )
        
        # 更新状态标签
        if self._status_label:
            status_colors = {
                PluginStatus.REGISTERED: ("gray", "gray"),
                PluginStatus.INITIALIZED: ("blue", "blue"),
                PluginStatus.STARTED: ("green", "green"),
                PluginStatus.STOPPED: ("orange", "orange"),
                PluginStatus.ERROR: ("red", "red"),
                PluginStatus.DISABLED: ("gray", "gray")
            }
            
            status_color = status_colors.get(plugin_info.status, ("gray", "gray"))
            self._status_label.configure(
                text=f"状态: {plugin_info.status.value}",
                text_color=status_color
            )
        
        # 更新开关状态
        if self._toggle_switch:
            is_enabled = plugin_info.is_enabled
            self._toggle_switch.set_value(is_enabled)
        
        logger.debug_struct("插件卡片更新", plugin_name=plugin_info.metadata.name)


class PluginInterface(BaseWidget):
    """
    插件管理界面
    
    现代化插件管理界面，支持：
    1. 插件列表显示和过滤
    2. 插件启用/禁用控制
    3. 插件状态监控
    4. 插件配置管理
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        container: Optional[Container] = None,
        plugin_registry: Optional[PluginRegistry] = None,
        **kwargs
    ):
        """
        初始化插件管理界面
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            plugin_registry: 插件注册表
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None, config_manager, event_bus)
        self._container = container
        self._plugin_registry = plugin_registry
        
        # 视图状态
        self._view_type = PluginViewType.LIST
        self._current_filter = PluginFilter()
        
        # 插件卡片映射
        self._plugin_cards: Dict[str, PluginCard] = {}
        
        # UI组件
        self._main_panel = None
        self._filter_panel = None
        self._plugin_panel = None
        self._detail_panel = None
        
        # 初始化
        self.initialize()
        
        logger.debug_struct("插件管理界面初始化", widget_id=self._widget_id)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建插件管理界面组件"""
        # 创建主面板
        self._main_panel = Panel(self._parent)
        main_widget = self._main_panel.get_widget()
        
        # 配置网格布局
        main_widget.grid_rowconfigure(1, weight=1)  # 插件区域
        main_widget.grid_columnconfigure(0, weight=1)
        
        # 1. 创建过滤器面板
        self._create_filter_panel(main_widget)
        
        # 2. 创建插件显示面板
        self._create_plugin_panel(main_widget)
        
        # 3. 加载插件列表
        self._load_plugins()
        
        # 注册主面板
        self.register_widget("main_panel", main_widget)
        
        return main_widget
    
    def _create_filter_panel(self, parent) -> None:
        """创建过滤器面板"""
        logger.debug("创建过滤器面板")
        
        # 过滤器面板
        filter_style = {
            "fg_color": ("gray90", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray70", "gray30"),
            "height": 60
        }
        
        self._filter_panel = Panel(parent, style=filter_style)
        filter_widget = self._filter_panel.get_widget()
        filter_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        filter_widget.grid_propagate(False)
        
        # 配置过滤器网格
        filter_widget.grid_columnconfigure(0, weight=1)  # 搜索框
        filter_widget.grid_columnconfigure(1, weight=0)  # 类型过滤
        filter_widget.grid_columnconfigure(2, weight=0)  # 启用过滤
        filter_widget.grid_columnconfigure(3, weight=0)  # 刷新按钮
        
        # 搜索框
        search_frame = ctk.CTkFrame(filter_widget, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="搜索:",
            font=("Microsoft YaHei", 11)
        )
        search_label.pack(side="left", padx=(0, 5))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="插件名称、描述或标签...",
            width=200
        )
        search_entry.pack(side="left", fill="x", expand=True)
        
        # 绑定搜索事件
        def on_search_changed(*args):
            search_text = search_entry.get().strip()
            self._current_filter.search_text = search_text if search_text else None
            self._apply_filter()
        
        search_entry.bind("<KeyRelease>", on_search_changed)
        
        # 插件类型过滤
        type_frame = ctk.CTkFrame(filter_widget, fg_color="transparent")
        type_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        
        type_label = ctk.CTkLabel(
            type_frame,
            text="类型:",
            font=("Microsoft YaHei", 11)
        )
        type_label.pack(side="left", padx=(0, 5))
        
        # 类型下拉菜单
        type_options = ["全部"] + [t.value for t in PluginType]
        type_combo = ctk.CTkComboBox(
            type_frame,
            values=type_options,
            width=120,
            command=self._on_type_filter_changed
        )
        type_combo.set("全部")
        type_combo.pack(side="left")
        
        # 启用状态过滤
        enable_frame = ctk.CTkFrame(filter_widget, fg_color="transparent")
        enable_frame.grid(row=0, column=2, sticky="ew", padx=5, pady=10)
        
        enable_switch = Switch(
            enable_frame,
            text="仅显示已启用"
        )
        enable_widget = enable_switch.get_widget()
        enable_widget.pack(side="left")
        
        # 绑定启用过滤事件
        def on_enable_filter_toggled():
            self._current_filter.enabled_only = enable_switch.get_value()
            self._apply_filter()
        
        enable_widget.configure(command=on_enable_filter_toggled)
        
        # 刷新按钮
        refresh_button = Button(
            filter_widget,
            text="刷新",
            widget_id="refresh_plugins",
            width=80,
            command=self._load_plugins
        )
        refresh_widget = refresh_button.get_widget()
        refresh_widget.grid(row=0, column=3, sticky="e", padx=10, pady=10)
        
        # 注册组件
        self.register_widget("filter_panel", filter_widget)
        self.register_widget("search_entry", search_entry)
        self.register_widget("type_combo", type_combo)
        self.register_widget("enable_switch", enable_widget)
        self.register_widget("refresh_button", refresh_widget)
    
    def _on_type_filter_changed(self, choice: str) -> None:
        """
        处理类型过滤变化
        
        Args:
            choice: 选择的类型
        """
        if choice == "全部":
            self._current_filter.plugin_type = None
        else:
            try:
                self._current_filter.plugin_type = PluginType(choice)
            except ValueError:
                self._current_filter.plugin_type = None
        
        self._apply_filter()
    
    def _create_plugin_panel(self, parent) -> None:
        """创建插件显示面板"""
        logger.debug("创建插件显示面板")
        
        # 插件面板
        plugin_style = {
            "fg_color": ("gray95", "gray15"),
            "corner_radius": 0,
            "border_width": 0
        }
        
        self._plugin_panel = ScrollPanel(parent, style=plugin_style)
        plugin_widget = self._plugin_panel.get_widget()
        plugin_widget.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 配置滚动面板内部框架
        content_frame = self._plugin_panel.get_content_frame()
        if content_frame:
            content_frame.grid_columnconfigure(0, weight=1)
        
        # 注册组件
        self.register_widget("plugin_panel", plugin_widget)
        self.register_widget("plugin_content_frame", content_frame)
    
    def _load_plugins(self) -> None:
        """加载插件列表"""
        logger.debug("加载插件列表")
        
        if not self._plugin_registry:
            logger.warning("插件注册表未设置，无法加载插件")
            return
        
        # 获取所有插件
        all_plugins = self._plugin_registry.get_all_plugins()
        
        # 清理现有卡片
        for card in self._plugin_cards.values():
            card.destroy()
        self._plugin_cards.clear()
        
        # 创建插件卡片
        content_frame = self._plugin_panel.get_content_frame()
        if not content_frame:
            return
        
        for plugin_info in all_plugins.values():
            if self._current_filter.matches(plugin_info):
                self._create_plugin_card(content_frame, plugin_info)
        
        logger.debug_struct("插件加载完成", total=len(all_plugins), filtered=len(self._plugin_cards))
    
    def _create_plugin_card(self, parent, plugin_info: PluginInfo) -> None:
        """
        创建插件卡片
        
        Args:
            parent: 父组件
            plugin_info: 插件信息
        """
        try:
            plugin_card = PluginCard(
                parent,
                plugin_info=plugin_info,
                widget_id=f"plugin_card_{plugin_info.metadata.name}",
                on_toggle=self._on_plugin_toggle,
                on_configure=self._on_plugin_configure,
                on_details=self._on_plugin_details
            )
            
            card_widget = plugin_card.get_widget()
            if card_widget:
                card_widget.pack(fill="x", padx=10, pady=5, anchor="nw")
            
            # 存储卡片引用
            self._plugin_cards[plugin_info.metadata.name] = plugin_card
            
            logger.debug_struct("插件卡片创建", plugin_name=plugin_info.metadata.name)
            
        except Exception as e:
            logger.error_struct("插件卡片创建失败", plugin_name=plugin_info.metadata.name, error=str(e))
    
    def _apply_filter(self) -> None:
        """应用过滤器"""
        logger.debug("应用过滤器")
        
        if not self._plugin_registry:
            return
        
        # 获取所有插件
        all_plugins = self._plugin_registry.get_all_plugins()
        
        # 获取内容框架
        content_frame = self._plugin_panel.get_content_frame()
        if not content_frame:
            return
        
        # 隐藏所有卡片
        for card in self._plugin_cards.values():
            card_widget = card.get_widget()
            if card_widget:
                card_widget.pack_forget()
        
        # 显示匹配的卡片
        for plugin_info in all_plugins.values():
            plugin_name = plugin_info.metadata.name
            
            if plugin_name in self._plugin_cards:
                card = self._plugin_cards[plugin_name]
                card_widget = card.get_widget()
                
                if self._current_filter.matches(plugin_info):
                    # 显示匹配的卡片
                    card_widget.pack(fill="x", padx=10, pady=5, anchor="nw")
                    
                    # 更新插件信息（状态可能已改变）
                    card.update_plugin_info(plugin_info)
                else:
                    # 隐藏不匹配的卡片
                    card_widget.pack_forget()
        
        logger.debug_struct("过滤器应用完成", total_plugins=len(all_plugins))
    
    def _on_plugin_toggle(self, plugin_info: PluginInfo, enabled: bool) -> None:
        """
        处理插件启用/禁用切换
        
        Args:
            plugin_info: 插件信息
            enabled: 是否启用
        """
        logger.debug_struct("插件状态切换", plugin_name=plugin_info.metadata.name, enabled=enabled)
        
        # 这里应该调用插件注册表的方法来启用/禁用插件
        # 暂时只是模拟
        if self._event_bus:
            self._event_bus.publish("plugin.toggle_request", {
                "plugin_name": plugin_info.metadata.name,
                "enabled": enabled,
                "timestamp": time.time()
            })
    
    def _on_plugin_configure(self, plugin_info: PluginInfo) -> None:
        """
        处理插件配置
        
        Args:
            plugin_info: 插件信息
        """
        logger.debug_struct("插件配置请求", plugin_name=plugin_info.metadata.name)
        
        # 这里应该打开插件配置对话框
        if self._event_bus:
            self._event_bus.publish("plugin.configure_request", {
                "plugin_name": plugin_info.metadata.name,
                "config_schema": plugin_info.metadata.config_schema,
                "default_config": plugin_info.metadata.default_config,
                "timestamp": time.time()
            })
    
    def _on_plugin_details(self, plugin_info: PluginInfo) -> None:
        """
        处理插件详情查看
        
        Args:
            plugin_info: 插件信息
        """
        logger.debug_struct("插件详情查看", plugin_name=plugin_info.metadata.name)
        
        # 这里应该显示插件详情对话框
        if self._event_bus:
            self._event_bus.publish("plugin.details_request", {
                "plugin_name": plugin_info.metadata.name,
                "plugin_info": plugin_info,
                "timestamp": time.time()
            })
    
    def update_plugin_list(self) -> None:
        """更新插件列表"""
        self._load_plugins()
    
    def set_plugin_registry(self, plugin_registry: PluginRegistry) -> None:
        """
        设置插件注册表
        
        Args:
            plugin_registry: 插件注册表
        """
        self._plugin_registry = plugin_registry
        self._load_plugins()
        
        logger.debug_struct("插件注册表设置", has_registry=plugin_registry is not None)
    
    def set_view_type(self, view_type: PluginViewType) -> None:
        """
        设置视图类型
        
        Args:
            view_type: 视图类型
        """
        self._view_type = view_type
        # TODO: 实现不同视图类型的切换
    
    def get_plugin_count(self) -> int:
        """获取插件数量"""
        return len(self._plugin_cards)
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件管理界面状态"""
        return {
            "widget_id": self._widget_id,
            "view_type": self._view_type.value,
            "plugin_count": self.get_plugin_count(),
            "filter_enabled_only": self._current_filter.enabled_only,
            "filter_plugin_type": self._current_filter.plugin_type.value if self._current_filter.plugin_type else None,
            "filter_search_text": self._current_filter.search_text,
            "has_plugin_registry": self._plugin_registry is not None
        }


class PluginView:
    """
    插件管理视图
    
    集成插件管理界面到主窗口视图框架中
    """
    
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化插件管理视图
        
        Args:
            parent: 父组件
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
        """
        self._parent = parent
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._container = container
        
        # 主框架
        self._main_frame = None
        self._plugin_interface = None
        
        # 插件注册表（从容器获取）
        self._plugin_registry = None
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("插件管理视图初始化")
    
    def _initialize(self) -> None:
        """初始化插件管理视图"""
        try:
            # 创建主框架
            self._main_frame = ctk.CTkFrame(self._parent)
            self._main_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            # 配置网格
            self._main_frame.grid_rowconfigure(0, weight=1)
            self._main_frame.grid_columnconfigure(0, weight=1)
            
            # 尝试从容器获取插件注册表
            try:
                self._plugin_registry = self._container.resolve(PluginRegistry)
            except Exception:
                logger.warning("无法从容器获取插件注册表")
            
            # 创建插件管理界面
            self._plugin_interface = PluginInterface(
                self._main_frame,
                widget_id="plugin_management",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container,
                plugin_registry=self._plugin_registry
            )
            
            plugin_widget = self._plugin_interface.get_widget()
            if plugin_widget:
                plugin_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # 订阅插件相关事件
            self._subscribe_events()
            
            logger.info("插件管理视图初始化完成")
            
        except Exception as e:
            logger.error("插件管理视图初始化失败", exc_info=True)
            raise UIError(f"插件管理视图初始化失败: {e}")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 插件状态更新事件
        self._event_bus.subscribe("plugin.status.updated", self._on_plugin_status_updated)
        
        # 插件注册事件
        self._event_bus.subscribe("plugin.registered", self._on_plugin_registered)
        
        # 插件注册表更新事件
        self._event_bus.subscribe("plugin.registry.updated", self._on_plugin_registry_updated)
    
    def _on_plugin_status_updated(self, event) -> None:
        """处理插件状态更新"""
        data = event.data
        plugin_name = data.get("plugin_name")
        new_status = data.get("status")
        
        logger.debug_struct("插件状态更新", plugin_name=plugin_name, status=new_status)
        
        # 刷新插件列表
        if self._plugin_interface:
            self._plugin_interface.update_plugin_list()
    
    def _on_plugin_registered(self, event) -> None:
        """处理插件注册"""
        data = event.data
        plugin_name = data.get("plugin_name")
        
        logger.debug_struct("插件注册", plugin_name=plugin_name)
        
        # 刷新插件列表
        if self._plugin_interface:
            self._plugin_interface.update_plugin_list()
    
    def _on_plugin_registry_updated(self, event) -> None:
        """处理插件注册表更新"""
        logger.debug("插件注册表更新")
        
        # 刷新插件列表
        if self._plugin_interface:
            self._plugin_interface.update_plugin_list()
    
    def get_widget(self):
        """获取主框架"""
        return self._main_frame
    
    def get_plugin_interface(self) -> PluginInterface:
        """获取插件管理界面"""
        return self._plugin_interface
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件管理视图状态"""
        if self._plugin_interface:
            return self._plugin_interface.get_status()
        return {"initialized": False}


# 导出
__all__ = [
    "PluginViewType",
    "PluginFilter",
    "PluginCard",
    "PluginInterface",
    "PluginView"
]