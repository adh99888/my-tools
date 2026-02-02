"""
统一管理后台界面

现代化、卡片式的统一管理后台，提供：
1. 所有模块的集中配置管理
2. 实时搜索和过滤
3. 模块分类导航
4. 统计面板和健康检查
5. 配置变更的热重载管理
"""

import customtkinter as ctk
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union, Tuple, Set
from uuid import uuid4

from .widgets import BaseWidget, Panel, ScrollPanel, Card, Button, Label, Switch, InputField, WidgetStyle
from .theme import ThemeManager
from ..core.events import EventBus, Event
from ..core.di import Container
from ..config.manager import ConfigManager
from ..services.module_registry import ModuleRegistry, ModuleRegistration, ModuleCategory, ReloadStrategy
from ..services.config_form_service import ConfigFormService, FormConfig, FormField
from ..services.hot_reload_orchestrator import HotReloadOrchestrator
from .config_form_view import ConfigFormView
from ..services.admin_state_service import AdminStateService, ModuleUIState, SearchFilter, OperationType
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class ViewMode(str, Enum):
    """视图模式枚举"""
    CARDS = "cards"        # 卡片视图
    LIST = "list"          # 列表视图
    TABLE = "table"        # 表格视图
    DETAIL = "detail"      # 详情视图


class SortBy(str, Enum):
    """排序方式枚举"""
    NAME = "name"          # 按名称
    CATEGORY = "category"  # 按分类
    PRIORITY = "priority"  # 按优先级
    LAST_MODIFIED = "last_modified"  # 按最后修改时间
    ACCESS_COUNT = "access_count"    # 按访问次数


@dataclass
class ModuleCardData:
    """模块卡片数据"""
    module_id: str
    display_name: str
    description: str
    category: ModuleCategory
    icon: str
    enabled: bool
    has_config: bool
    can_reload_immediately: bool
    requires_restart: bool
    tags: List[str]
    priority: int
    reload_strategy: ReloadStrategy


@dataclass
class ModuleFilter:
    """模块过滤器"""
    categories: Set[ModuleCategory] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    enabled_only: bool = True
    has_config_only: bool = False
    search_query: str = ""
    reload_strategy: Optional[ReloadStrategy] = None


class ModuleCard(BaseWidget):
    """模块卡片组件"""
    
    DEFAULT_CARD_SIZE = (300, 180)
    MIN_CARD_SIZE = (280, 160)
    
    def __init__(
        self,
        parent,
        module_data: ModuleCardData,
        widget_id: Optional[str] = None,
        style: Optional[Union[WidgetStyle, Dict[str, Any]]] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None
    ):
        """初始化模块卡片"""
        super().__init__(parent, widget_id, style, config_manager, event_bus)
        self._module_data = module_data
        
        # UI组件
        self._card_widget: Optional[Card] = None
        self._header_panel: Optional[Panel] = None
        self._icon_label: Optional[Label] = None
        self._title_label: Optional[Label] = None
        self._status_badge: Optional[Label] = None
        self._content_panel: Optional[Panel] = None
        self._description_label: Optional[Label] = None
        self._tags_panel: Optional[Panel] = None
        self._footer_panel: Optional[Panel] = None
        self._config_button: Optional[Button] = None
        self._reload_button: Optional[Button] = None
        self._enable_switch: Optional[Switch] = None
        
        # 状态
        self._is_expanded = False
        self._is_selected = False
        
        # 初始化
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建卡片组件"""
        # 卡片容器
        self._card_widget = Card(
            self._parent,
            widget_id=f"card_{self._module_data.module_id}",
            style=WidgetStyle(
                bg_color="#ffffff",
                fg_color="#f8f9fa",
                border_color="#e9ecef",
                border_width=1,
                corner_radius=12,
                padding=(16, 16)
            )
        )
        
        # 创建布局
        self._create_header()
        self._create_content()
        self._create_footer()
        
        assert self._card_widget is not None
        return self._card_widget.get_widget()  # type: ignore
    
    def _create_header(self) -> None:
        """创建卡片头部"""
        self._header_panel = Panel(
            self._card_widget,
            widget_id=f"header_{self._module_data.module_id}",
            style=WidgetStyle(orientation="horizontal", padding=(0, 0, 0, 8))
        )
        
        # 图标
        self._icon_label = Label(
            self._header_panel,
            text=self._module_data.icon,
            widget_id=f"icon_{self._module_data.module_id}",
            style=WidgetStyle(
                font=("Segoe UI Emoji", 24),
                padding=(0, 0, 12, 0)
            )
        )
        
        # 标题和状态
        title_panel = Panel(
            self._header_panel,
            widget_id=f"title_panel_{self._module_data.module_id}",
            style=WidgetStyle(orientation="vertical", fill="both", expand=True)
        )
        
        self._title_label = Label(
            title_panel,
            text=self._module_data.display_name,
            widget_id=f"title_{self._module_data.module_id}",
            style=WidgetStyle(
                font=("Segoe UI", 16, "bold"),
                text_color="#212529"
            )
        )
        
        # 状态徽章
        status_text = "已启用" if self._module_data.enabled else "已禁用"
        status_color = "#28a745" if self._module_data.enabled else "#6c757d"
        self._status_badge = Label(
            title_panel,
            text=status_text,
            widget_id=f"status_{self._module_data.module_id}",
            style=WidgetStyle(
                font=("Segoe UI", 10),
                text_color=status_color,
                bg_color=f"{status_color}15",
                corner_radius=4,
                padding=(4, 2)
            )
        )
        
        # 添加到头部面板
        self._header_panel.add_widget(self._icon_label)
        self._header_panel.add_widget(title_panel)
    
    def _create_content(self) -> None:
        """创建卡片内容区域"""
        self._content_panel = Panel(
            self._card_widget,
            widget_id=f"content_{self._module_data.module_id}",
            style=WidgetStyle(orientation="vertical", padding=(0, 8, 0, 8))
        )
        
        # 描述
        if self._module_data.description:
            self._description_label = Label(
                self._content_panel,
                text=self._module_data.description,
                widget_id=f"desc_{self._module_data.module_id}",
                style=WidgetStyle(
                    font=("Segoe UI", 12),
                    text_color="#6c757d",
                    wraplength=260,
                    justify="left"
                )
            )
        
        # 标签面板
        if self._module_data.tags:
            self._tags_panel = Panel(
                self._content_panel,
                widget_id=f"tags_{self._module_data.module_id}",
                style=WidgetStyle(orientation="horizontal", wrap=True, padding=(0, 8, 0, 0))
            )
            
            for tag in self._module_data.tags[:3]:  # 最多显示3个标签
                tag_label = Label(
                    self._tags_panel,
                    text=tag,
                    widget_id=f"tag_{tag}_{self._module_data.module_id}",
                    style=WidgetStyle(
                        font=("Segoe UI", 9),
                        text_color="#6c757d",
                        bg_color="#e9ecef",
                        corner_radius=10,
                        padding=(6, 2, 6, 2),
                        margin=(0, 2, 4, 2)
                    )
                )
    
    def _create_footer(self) -> None:
        """创建卡片底部操作栏"""
        self._footer_panel = Panel(
            self._card_widget,
            widget_id=f"footer_{self._module_data.module_id}",
            style=WidgetStyle(orientation="horizontal", padding=(0, 8, 0, 0))
        )
        
        # 配置按钮（如果有配置）
        if self._module_data.has_config:
            self._config_button = Button(
                self._footer_panel,
                text="⚙️ 配置",
                widget_id=f"config_btn_{self._module_data.module_id}",
                style=WidgetStyle(
                    font=("Segoe UI", 11),
                    bg_color="#007bff",
                    hover_color="#0056b3",
                    fg_color="#ffffff",
                    corner_radius=6,
                    padding=(8, 4),
                    margin=(0, 0, 8, 0)
                ),
                command=self._on_config_click
            )
        
        # 重载按钮（如果可以立即重载）
        if self._module_data.can_reload_immediately:
            reload_text = "↻ 重载" if not self._module_data.requires_restart else "🔄 需重启"
            self._reload_button = Button(
                self._footer_panel,
                text=reload_text,
                widget_id=f"reload_btn_{self._module_data.module_id}",
                style=WidgetStyle(
                    font=("Segoe UI", 11),
                    bg_color="#6c757d" if self._module_data.requires_restart else "#17a2b8",
                    hover_color="#545b62" if self._module_data.requires_restart else "#117a8b",
                    fg_color="#ffffff",
                    corner_radius=6,
                    padding=(8, 4),
                    margin=(0, 0, 8, 0)
                ),
                command=self._on_reload_click
            )
        
        # 启用开关
        self._enable_switch = Switch(
            self._footer_panel,
            text="启用",
            initial_value=self._module_data.enabled,
            widget_id=f"enable_switch_{self._module_data.module_id}",
            style=WidgetStyle(
                font=("Segoe UI", 11),
                text_color="#212529",
                margin=(0, 0, 0, 0)
            ),
            command=self._on_enable_toggle
        )
        
        # 添加弹性空间
        Panel(
            self._footer_panel,
            widget_id=f"spacer_{self._module_data.module_id}",
            style=WidgetStyle(fill="both", expand=True)
        )
        
        # 将启用开关添加到右侧
        if self._enable_switch:
            self._footer_panel.add_widget(self._enable_switch)
    
    def _on_config_click(self) -> None:
        """配置按钮点击事件"""
        logger.info(f"打开模块配置: {self._module_data.display_name}")
        if self._event_bus:
            self._event_bus.publish(
                "admin.module.config.open",
                {"module_id": self._module_data.module_id}
            )
    
    def _on_reload_click(self) -> None:
        """重载按钮点击事件"""
        logger.info(f"重载模块: {self._module_data.display_name}")
        if self._event_bus:
            self._event_bus.publish(
                "admin.module.reload.request",
                {
                    "module_id": self._module_data.module_id,
                    "requires_restart": self._module_data.requires_restart
                }
            )
    
    def _on_enable_toggle(self, enabled: bool) -> None:
        """启用开关切换事件"""
        logger.info(f"切换模块启用状态: {self._module_data.display_name} -> {enabled}")
        if self._event_bus:
            self._event_bus.publish(
                "admin.module.enable.toggle",
                {
                    "module_id": self._module_data.module_id,
                    "enabled": enabled
                }
            )
    
    def update_card_style(self, style: Dict[str, Any]) -> None:
        """更新卡片样式"""
        if self._card_widget:
            self._card_widget.update_style(**style)
    
    def set_selected(self, selected: bool) -> None:
        """设置卡片选中状态"""
        self._is_selected = selected
        border_color = "#007bff" if selected else "#e9ecef"
        border_width = 2 if selected else 1
        
        if self._card_widget:
            self._card_widget.update_style(border_color=border_color, border_width=border_width)
    
    def get_module_id(self) -> str:
        """获取模块ID"""
        return self._module_data.module_id


class AdminInterface(BaseWidget):
    """
    统一管理后台界面
    
    提供现代化、卡片式的模块管理界面，支持：
    1. 模块分类和过滤
    2. 实时搜索
    3. 配置管理
    4. 状态监控
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[Union[WidgetStyle, Dict[str, Any]]] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        container: Optional[Container] = None,
        module_registry: Optional[ModuleRegistry] = None,
        config_form_service: Optional[ConfigFormService] = None,
        hot_reload_orchestrator: Optional[HotReloadOrchestrator] = None,
        admin_state_service: Optional[AdminStateService] = None
    ):
        """
        初始化管理界面
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            style: 组件样式
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            module_registry: 模块注册表服务
            config_form_service: 配置表单服务
            hot_reload_orchestrator: 热重载协调器
            admin_state_service: 状态管理服务
        """
        super().__init__(parent, widget_id, style, config_manager, event_bus)
        
        # 服务依赖
        self._container = container
        self._module_registry = module_registry
        self._config_form_service = config_form_service
        self._hot_reload_orchestrator = hot_reload_orchestrator
        self._admin_state_service = admin_state_service
        
        # UI状态
        self._view_mode = ViewMode.CARDS
        self._sort_by = SortBy.NAME
        self._current_filter = ModuleFilter()
        self._selected_module_id: Optional[str] = None
        
        # UI组件
        self._main_panel: Optional[Panel] = None
        self._sidebar: Optional[Panel] = None
        self._content_area: Optional[Panel] = None
        self._search_panel: Optional[Panel] = None
        self._search_input: Optional[InputField] = None
        self._categories_panel: Optional[Panel] = None
        self._module_cards_panel: Optional[Panel] = None
        self._stats_panel: Optional[Panel] = None
        
        # 数据缓存
        self._module_cards: Dict[str, ModuleCard] = {}
        self._category_filters: Dict[ModuleCategory, Switch] = {}
        
        # 定时刷新
        self._refresh_timer: Optional[threading.Timer] = None
        self._refresh_interval = 5.0  # 秒
        
        # 初始化
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建管理界面主组件"""
        # 主面板（左右布局）
        self._main_panel = Panel(
            self._parent,
            widget_id="admin_main_panel",
            style=WidgetStyle(orientation="horizontal", fill="both", expand=True)
        )
        
        # 左侧边栏
        self._sidebar = Panel(
            self._main_panel,
            widget_id="admin_sidebar",
            style=WidgetStyle(
                orientation="vertical",
                width=240,
                bg_color="#f8f9fa",
                border_color="#e9ecef",
                border_width=1,
                padding=(16, 16, 16, 16)
            )
        )
        
        # 主内容区域
        self._content_area = Panel(
            self._main_panel,
            widget_id="admin_content_area",
            style=WidgetStyle(orientation="vertical", fill="both", expand=True, padding=(16, 16, 16, 16))
        )
        
        # 构建侧边栏
        self._build_sidebar()
        
        # 构建内容区域
        self._build_content_area()
        
        # 订阅事件
        if self._event_bus:
            self._event_bus.subscribe("admin.module.config.open", self._on_module_config_open)
            logger.info("管理后台已订阅配置打开事件")
        
        return self._main_panel.get_widget()  # type: ignore
    
    def _build_sidebar(self) -> None:
        """构建侧边栏"""
        # 搜索面板
        self._search_panel = Panel(
            self._sidebar,
            widget_id="search_panel",
            style=WidgetStyle(orientation="vertical", padding=(0, 0, 0, 20))
        )
        
        search_label = Label(
            self._search_panel,
            text="🔍 搜索模块",
            widget_id="search_label",
            style=WidgetStyle(font=("Segoe UI", 12, "bold"), text_color="#495057", padding=(0, 0, 0, 8))
        )
        
        self._search_input = InputField(
            self._search_panel,
            placeholder="输入模块名称或描述...",
            widget_id="search_input",
            style=WidgetStyle(
                font=("Segoe UI", 11),
                bg_color="#ffffff",
                border_color="#ced4da",
                border_width=1,
                corner_radius=6,
                padding=(8, 8)
            ),
            on_change=self._on_search_change
        )
        
        # 分类过滤器
        self._categories_panel = Panel(
            self._sidebar,
            widget_id="categories_panel",
            style=WidgetStyle(orientation="vertical", padding=(0, 0, 0, 20))
        )
        
        categories_label = Label(
            self._categories_panel,
            text="📂 分类",
            widget_id="categories_label",
            style=WidgetStyle(font=("Segoe UI", 12, "bold"), text_color="#495057", padding=(0, 0, 0, 12))
        )
        
        # 添加分类开关
        if self._module_registry:
            self._build_category_filters()
        
        # 统计面板
        stats_panel = Panel(
            self._sidebar,
            widget_id="stats_panel",
            style=WidgetStyle(orientation="vertical", padding=(0, 0, 0, 20))
        )
        
        stats_label = Label(
            stats_panel,
            text="📊 系统统计",
            widget_id="stats_label",
            style=WidgetStyle(font=("Segoe UI", 12, "bold"), text_color="#495057", padding=(0, 0, 0, 12))
        )
        
        # 统计信息
        self._stats_labels = {}
        stats_items = [
            ("📦 模块总数", "total_modules", "0"),
            ("✅ 已启用", "enabled_modules", "0"),
            ("⚙️ 可配置", "configurable_modules", "0"),
            ("🔄 需重启", "restart_required", "0"),
            ("📝 操作记录", "operation_count", "0")
        ]
        
        for text, key, default in stats_items:
            label = Label(
                stats_panel,
                text=f"{text}: {default}",
                widget_id=f"stats_{key}",
                style=WidgetStyle(font=("Segoe UI", 11), text_color="#6c757d", padding=(0, 0, 0, 4))
            )
            self._stats_labels[key] = label
        
        # 更新统计信息
        self._update_stats_display()
        
        # 视图模式选择器
        view_panel = Panel(
            self._sidebar,
            widget_id="view_panel",
            style=WidgetStyle(orientation="vertical", padding=(0, 0, 0, 20))
        )
        
        view_label = Label(
            view_panel,
            text="👁️ 视图模式",
            widget_id="view_label",
            style=WidgetStyle(font=("Segoe UI", 12, "bold"), text_color="#495057", padding=(0, 0, 0, 12))
        )
        
        # 添加组件到侧边栏
        self._search_panel.add_widget(search_label)
        self._search_panel.add_widget(self._search_input)  # type: ignore
        self._sidebar.add_widget(self._search_panel)  # type: ignore
        self._sidebar.add_widget(self._categories_panel)  # type: ignore
        self._sidebar.add_widget(stats_panel)  # type: ignore
        self._sidebar.add_widget(view_panel)  # type: ignore
    
    def _build_category_filters(self) -> None:
        """构建分类过滤器"""
        # 清除现有过滤器
        for switch in self._category_filters.values():
            self._categories_panel.remove_widget(switch)  # type: ignore
        self._category_filters.clear()
        
        # 获取所有分类
        if not self._module_registry:
            return
        
        try:
            categories = self._module_registry.get_all_categories()  # type: ignore
            for category in categories:
                switch = Switch(
                    self._categories_panel,
                    text=self._get_category_display_name(category),
                    initial_value=True,
                    widget_id=f"category_{category.value}",
                    style=WidgetStyle(
                        font=("Segoe UI", 11),
                        text_color="#495057",
                        padding=(0, 0, 0, 6)
                    ),
                    command=lambda cat=category: self._on_category_toggle(cat, switch.get_value())
                )
                self._category_filters[category] = switch
                self._categories_panel.add_widget(switch)  # type: ignore
        except Exception as e:
            logger.error(f"构建分类过滤器失败: {e}")
    
    def _get_category_display_name(self, category: ModuleCategory) -> str:
        """获取分类显示名称"""
        display_names = {
            ModuleCategory.AI: "🤖 AI模块",
            ModuleCategory.PLUGIN: "🧩 插件模块",
            ModuleCategory.SYSTEM: "⚙️ 系统模块",
            ModuleCategory.UI: "🎨 UI模块",
            ModuleCategory.DATA: "💾 数据模块",
            ModuleCategory.SECURITY: "🔒 安全模块",
            ModuleCategory.MONITOR: "📊 监控模块",
            ModuleCategory.DEVELOPER: "🔧 开发者工具",
            ModuleCategory.CUSTOM: "📦 自定义模块"
        }
        return display_names.get(category, f"📦 {category.value}")
    
    def _update_stats_display(self) -> None:
        """更新统计信息显示"""
        try:
            if not self._module_registry or not hasattr(self, '_stats_labels'):
                return
            
            # 获取模块统计
            all_modules = self._module_registry.get_all_modules()
            total_modules = len(all_modules)
            enabled_modules = sum(1 for m in all_modules if m.enabled)
            configurable_modules = sum(1 for m in all_modules if m.config_schema)
            restart_required = sum(1 for m in all_modules if m.requires_restart)
            
            # 获取操作统计
            operation_count = 0
            if self._admin_state_service:
                stats = self._admin_state_service.get_statistics()
                operation_count = stats.get('operation_count', 0)
            
            # 更新标签
            stats_data = {
                "total_modules": str(total_modules),
                "enabled_modules": str(enabled_modules),
                "configurable_modules": str(configurable_modules),
                "restart_required": str(restart_required),
                "operation_count": str(operation_count)
            }
            
            for key, label in self._stats_labels.items():
                if key in stats_data:
                    original_text = label.get_text()
                    # 提取文本前缀（emoji + 标签）
                    if ": " in original_text:
                        prefix = original_text.split(": ")[0] + ": "
                        new_text = prefix + stats_data[key]
                        label.set_text(new_text)
                        
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def _build_content_area(self) -> None:
        """构建内容区域"""
        # 顶部工具栏
        toolbar_panel = Panel(
            self._content_area,
            widget_id="toolbar_panel",
            style=WidgetStyle(orientation="horizontal", padding=(0, 0, 0, 20))
        )
        
        # 标题
        title_label = Label(
            toolbar_panel,
            text="🚀 统一管理后台",
            widget_id="admin_title",
            style=WidgetStyle(font=("Segoe UI", 24, "bold"), text_color="#212529")
        )
        
        # 统计信息
        if self._admin_state_service:
            stats = self._admin_state_service.get_statistics()
            stats_text = f"📊 模块: {len(self._module_cards)} | 📝 操作: {stats.get('operation_count', 0)}"
            stats_label = Label(
                toolbar_panel,
                text=stats_text,
                widget_id="stats_label",
                style=WidgetStyle(font=("Segoe UI", 11), text_color="#6c757d")
            )
        
        # 操作按钮
        action_panel = Panel(
            toolbar_panel,
            widget_id="action_panel",
            style=WidgetStyle(orientation="horizontal", padding=(0, 0, 0, 0))
        )
        
        refresh_btn = Button(
            action_panel,
            text="↻ 刷新",
            widget_id="refresh_btn",
            style=WidgetStyle(
                font=("Segoe UI", 11),
                bg_color="#6c757d",
                hover_color="#545b62",
                fg_color="#ffffff",
                corner_radius=6,
                padding=(8, 4),
                margin=(0, 0, 8, 0)
            ),
            command=self._refresh_modules
        )
        
        # 添加到工具栏
        toolbar_panel.add_widget(title_label)
        Panel(toolbar_panel, widget_id="toolbar_spacer", style=WidgetStyle(fill="both", expand=True))
        if self._admin_state_service:
            toolbar_panel.add_widget(stats_label)  # type: ignore
        toolbar_panel.add_widget(action_panel)
        action_panel.add_widget(refresh_btn)
        
        # 模块卡片面板（滚动区域）
        self._module_cards_panel = ScrollPanel(  # type: ignore
            self._content_area,
            widget_id="module_cards_panel",
            style=WidgetStyle(orientation="vertical", fill="both", expand=True)
        )
        
        # 添加组件到内容区域
        self._content_area.add_widget(toolbar_panel)  # type: ignore
        self._content_area.add_widget(self._module_cards_panel)  # type: ignore
        
        # 初始加载模块
        self._refresh_modules()
        
        # 启动定时刷新
        self._start_refresh_timer()
    
    def _refresh_modules(self) -> None:
        """刷新模块显示"""
        try:
            if not self._module_registry:
                logger.warning("模块注册表未提供，跳过模块刷新")
                return
            
            # 清除现有卡片
            for card_id, card in list(self._module_cards.items()):
                self._module_cards_panel.remove_widget(card)  # type: ignore
            self._module_cards.clear()
            
            # 获取所有模块
            all_modules = self._module_registry.get_all_modules()
            
            # 应用过滤器
            filtered_modules = self._apply_filters(all_modules)
            
            # 排序
            sorted_modules = self._sort_modules(filtered_modules)
            
            # 创建卡片
            for module in sorted_modules:
                self._create_module_card(module)
            
            logger.info(f"模块刷新完成，显示 {len(sorted_modules)}/{len(all_modules)} 个模块")
            
            # 更新统计信息
            self._update_stats_display()
            
        except Exception as e:
            logger.error(f"刷新模块失败: {e}", exc_info=True)
    
    def _apply_filters(self, modules: List[ModuleRegistration]) -> List[ModuleRegistration]:
        """应用过滤器"""
        if not self._current_filter:
            return modules
        
        filtered = []
        
        for module in modules:
            # 分类过滤
            if (self._current_filter.categories and 
                module.category not in self._current_filter.categories):
                continue
            
            # 标签过滤
            if self._current_filter.tags:
                module_tags = set(module.tags or [])
                if not any(tag in module_tags for tag in self._current_filter.tags):
                    continue
            
            # 启用状态过滤
            if self._current_filter.enabled_only and not module.enabled:
                continue
            
            # 配置过滤
            if self._current_filter.has_config_only and not module.config_schema:
                continue
            
            # 重载策略过滤
            if (self._current_filter.reload_strategy and 
                module.reload_strategy != self._current_filter.reload_strategy):
                continue
            
            # 搜索过滤
            if self._current_filter.search_query:
                query = self._current_filter.search_query.lower()
                search_text = f"{module.display_name} {module.description}".lower()
                if query not in search_text:
                    continue
            
            filtered.append(module)
        
        return filtered
    
    def _sort_modules(self, modules: List[ModuleRegistration]) -> List[ModuleRegistration]:
        """排序模块"""
        if self._sort_by == SortBy.NAME:
            return sorted(modules, key=lambda m: m.display_name)
        elif self._sort_by == SortBy.CATEGORY:
            return sorted(modules, key=lambda m: (m.category.value, m.display_name))
        elif self._sort_by == SortBy.PRIORITY:
            return sorted(modules, key=lambda m: (-m.priority, m.display_name))
        else:
            return modules
    
    def _create_module_card(self, module: ModuleRegistration) -> None:
        """创建模块卡片"""
        try:
            # 准备卡片数据
            card_data = ModuleCardData(
                module_id=module.module_id,
                display_name=module.display_name,
                description=module.description or "",
                category=module.category,
                icon=module.get_display_info().get("icon", "📦"),
                enabled=module.enabled,
                has_config=bool(module.config_schema),
                can_reload_immediately=module.can_reload_immediately,
                requires_restart=module.requires_restart,
                tags=module.tags or [],
                priority=module.priority,
                reload_strategy=module.reload_strategy
            )
            
            # 创建卡片
            card = ModuleCard(
                self._module_cards_panel,
                card_data,
                widget_id=f"module_card_{module.module_id}",
                config_manager=self._config_manager,
                event_bus=self._event_bus
            )
            
            # 添加到面板
            self._module_cards_panel.add_widget(card)  # type: ignore
            self._module_cards[module.module_id] = card
            
        except Exception as e:
            logger.error(f"创建模块卡片失败 {module.module_id}: {e}", exc_info=True)
    
    def _on_search_change(self, value: str) -> None:
        """搜索输入变化事件"""
        self._current_filter.search_query = value.strip()
        self._refresh_modules()
    
    def _on_category_toggle(self, category: ModuleCategory, enabled: bool) -> None:
        """分类开关切换事件"""
        if enabled:
            self._current_filter.categories.add(category)
        else:
            self._current_filter.categories.discard(category)
        self._refresh_modules()
    
    def _start_refresh_timer(self) -> None:
        """启动定时刷新"""
        def refresh_task():
            try:
                if self._refresh_timer:
                    self._refresh_timer.cancel()
                
                # 刷新模块
                self._refresh_modules()
                
                # 重新安排定时器
                if self._widget is not None:  # 检查组件是否仍然存在
                    self._refresh_timer = threading.Timer(
                        self._refresh_interval,
                        refresh_task
                    )
                    self._refresh_timer.daemon = True
                    self._refresh_timer.start()
                    
            except Exception as e:
                logger.error(f"定时刷新失败: {e}")
        
        self._refresh_timer = threading.Timer(
            self._refresh_interval,
            refresh_task
        )
        self._refresh_timer.daemon = True
        self._refresh_timer.start()
    
    def _on_module_config_open(self, event: Event) -> None:
        """处理模块配置打开事件"""
        module_id = event.data.get("module_id") if isinstance(event.data, dict) else None
        if not module_id:
            logger.error("配置打开事件缺少module_id")
            return
        
        logger.info(f"打开模块配置表单: {module_id}")
        self._show_config_form(module_id)
    
    def _show_config_form(self, module_id: str) -> None:
        """显示模块配置表单"""
        try:
            if not self._config_form_service:
                logger.error("配置表单服务未提供，无法显示配置")
                return
            
            # 获取模块配置
            module = self._module_registry.get_module(module_id) if self._module_registry else None
            if not module:
                logger.error(f"模块不存在: {module_id}")
                return
            
            # 生成表单配置
            schema = module.config_schema
            if not schema:
                logger.error(f"模块没有配置schema: {module_id}")
                return
            
            form_config = self._config_form_service.create_form_from_schema(
                module_id, schema, None
            )  # type: ignore
            if not form_config:
                logger.error(f"无法为模块生成表单配置: {module_id}")
                return
            
            # 创建并显示配置对话框
            self._show_config_dialog(module.display_name, form_config)
            
        except Exception as e:
            logger.error(f"显示配置表单失败: {e}", exc_info=True)
    
    def _show_config_dialog(self, title: str, form_config: FormConfig) -> None:
        """显示配置对话框"""
        try:
            # 创建顶级窗口
            dialog = ctk.CTkToplevel(self._widget)
            dialog.title(f"配置 - {title}")
            dialog.geometry("800x600")
            dialog.resizable(True, True)
            
            # 设置窗口属性
            dialog.grab_set()  # 模态
            dialog.transient(self._widget)  # 附加到主窗口
            
            # 创建配置表单视图
            form_view = ConfigFormView(
                dialog,
                widget_id=f"config_form_{title}",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                form_config=form_config,
                on_submit=lambda values: self._on_config_form_submit(form_config, values),
                on_cancel=lambda: dialog.destroy()
            )
            
            # 布局
            form_view.get_widget().pack(fill="both", expand=True, padx=16, pady=16)
            
            # 居中显示
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            logger.info(f"配置对话框已显示: {title}")
            
        except Exception as e:
            logger.error(f"显示配置对话框失败: {e}", exc_info=True)
    
    def _on_config_form_submit(self, form_config: FormConfig, values: Dict[str, Any]) -> None:
        """配置表单提交事件"""
        try:
            logger.info(f"配置表单提交: {form_config.id}, {len(values)} 个字段")
            
            # 保存配置
            if self._config_form_service:
                success, errors = self._config_form_service.update_form_with_values(form_config, values)
                if success:
                    logger.info(f"配置保存成功: {form_config.id}")
                    
                    # 触发重载
                    if self._hot_reload_orchestrator:
                        module_id = form_config.id
                        self._hot_reload_orchestrator.request_reload(module_id)
                        logger.info(f"已请求重载模块: {module_id}")
                    
                    # 发布事件
                    if self._event_bus:
                        self._event_bus.publish("admin.config.saved", {
                            "module_id": form_config.id,
                            "field_count": len(values),
                            "success": True
                        })
                else:
                    logger.error(f"配置保存失败: {errors}")
                    # TODO: 显示错误信息给用户
            else:
                logger.error("配置表单服务不可用")
                
        except Exception as e:
            logger.error(f"配置提交处理失败: {e}", exc_info=True)
    
    def _on_config_submit(self, values: Dict[str, Any]) -> None:
        """向后兼容的配置提交事件"""
        logger.warning("使用旧版配置提交回调，请更新代码")
        self._on_config_form_submit(None, values)
    
    def destroy(self) -> None:
        """销毁组件"""
        # 停止定时器
        if self._refresh_timer:
            self._refresh_timer.cancel()
            self._refresh_timer = None
        
        # 取消事件订阅
        if self._event_bus:
            self._event_bus.unsubscribe("admin.module.config.open", self._on_module_config_open)
        
        # 调用父类销毁
        super().destroy()
    
    # ========== 公共API方法 ==========
    
    def set_view_mode(self, mode: ViewMode) -> None:
        """设置视图模式"""
        self._view_mode = mode
        logger.info(f"切换到视图模式: {mode}")
        # TODO: 根据视图模式重新渲染
    
    def set_sort_by(self, sort_by: SortBy) -> None:
        """设置排序方式"""
        self._sort_by = sort_by
        self._refresh_modules()
        logger.info(f"设置排序方式: {sort_by}")
    
    def get_selected_module(self) -> Optional[str]:
        """获取选中的模块ID"""
        return self._selected_module_id
    
    def show_module_config(self, module_id: str) -> bool:
        """显示模块配置"""
        try:
            self._show_config_form(module_id)
            return True
        except Exception as e:
            logger.error(f"显示模块配置失败: {e}")
            return False
    
    def reload_module(self, module_id: str) -> bool:
        """重载模块"""
        if not self._hot_reload_orchestrator:
            logger.error("热重载协调器未提供")
            return False
        
        try:
            self._hot_reload_orchestrator.request_reload(module_id)
            logger.info(f"已请求重载模块: {module_id}")
            return True
        except Exception as e:
            logger.error(f"请求重载模块失败: {e}")
            return False