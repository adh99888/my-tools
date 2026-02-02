"""
配置管理界面

提供现代化、直观的配置管理界面，包括：
1. 配置项分组和树形浏览
2. 实时配置编辑和验证
3. 配置导入/导出
4. 配置版本管理
5. 环境变量覆盖显示
"""

import customtkinter as ctk
import logging
import json
import yaml
from typing import Dict, Any, Optional, List, Callable, Union, Tuple, Literal
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import copy

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..config.models import (
    SmallPanguConfig, AppConfig, PluginConfig, EventBusConfig, LoggingConfig,
    AIConfig, SecurityConfig, UIConfig, StorageConfig, MetricsConfig, TestingConfig,
    LogLevel, Theme, Language, StorageType, SwitchStrategy, ConfirmLevel, OperationType
)
from .manager import UIManager
from .widgets import BaseWidget, Panel, ScrollPanel, Card, Button, Label, Switch, TextArea, InputField
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class ConfigViewType(str, Enum):
    """配置视图类型枚举"""
    TREE = "tree"          # 树形视图
    FORM = "form"          # 表单视图
    JSON = "json"          # JSON编辑视图
    COMPARE = "compare"    # 比较视图


class ConfigSection(str, Enum):
    """配置分区枚举"""
    APP = "app"
    PLUGINS = "plugins"
    EVENT_BUS = "event_bus"
    LOGGING = "logging"
    AI = "ai"
    SECURITY = "security"
    UI = "ui"
    STORAGE = "storage"
    METRICS = "metrics"
    TESTING = "testing"
    ENVIRONMENT = "environment"


@dataclass
class ConfigItem:
    """配置项数据类"""
    section: ConfigSection
    key: str
    value: Any
    data_type: str
    description: str
    default_value: Any
    constraints: Dict[str, Any] = field(default_factory=dict)
    is_modified: bool = False
    original_value: Optional[Any] = None
    
    def get_display_value(self) -> str:
        """获取显示值"""
        if self.value is None:
            return "null"
        elif isinstance(self.value, (list, dict)):
            return json.dumps(self.value, ensure_ascii=False, indent=2)
        else:
            return str(self.value)
    
    def validate(self, new_value: Any) -> Tuple[bool, Optional[str]]:
        """验证新值"""
        try:
            # 类型转换
            if self.data_type == "int":
                converted = int(new_value)
                if "ge" in self.constraints and converted < self.constraints["ge"]:
                    return False, f"值必须 >= {self.constraints['ge']}"
                if "le" in self.constraints and converted > self.constraints["le"]:
                    return False, f"值必须 <= {self.constraints['le']}"
                return True, None
            elif self.data_type == "float":
                converted = float(new_value)
                if "ge" in self.constraints and converted < self.constraints["ge"]:
                    return False, f"值必须 >= {self.constraints['ge']}"
                if "le" in self.constraints and converted > self.constraints["le"]:
                    return False, f"值必须 <= {self.constraints['le']}"
                return True, None
            elif self.data_type == "bool":
                if isinstance(new_value, bool):
                    return True, None
                if isinstance(new_value, str):
                    lower = new_value.lower()
                    if lower in ["true", "false", "1", "0", "yes", "no"]:
                        return True, None
                return False, "必须是布尔值 (true/false)"
            elif self.data_type == "enum":
                # 枚举值验证
                if new_value in [e.value for e in self.constraints.get("enum_class", [])]:
                    return True, None
                return False, f"必须是有效的枚举值: {[e.value for e in self.constraints.get('enum_class', [])]}"
            elif self.data_type == "str":
                if not self.constraints:
                    return True, None
                if "min_length" in self.constraints and len(new_value) < self.constraints["min_length"]:
                    return False, f"长度必须 >= {self.constraints['min_length']}"
                if "max_length" in self.constraints and len(new_value) > self.constraints["max_length"]:
                    return False, f"长度必须 <= {self.constraints['max_length']}"
                return True, None
            else:
                return True, None
        except (ValueError, TypeError) as e:
            return False, f"类型转换失败: {e}"
    
    def update_value(self, new_value: Any) -> bool:
        """更新值并返回是否成功"""
        is_valid, error = self.validate(new_value)
        if is_valid:
            self.value = new_value
            self.is_modified = self.value != self.original_value
            return True
        return False


class ConfigCard(BaseWidget):
    """配置卡片组件"""
    
    def __init__(
        self,
        parent,
        config_item: ConfigItem,
        widget_id: Optional[str] = None,
        on_save: Optional[Callable] = None,
        on_reset: Optional[Callable] = None,
        **kwargs
    ):
        """
        初始化配置卡片
        
        Args:
            parent: 父组件
            config_item: 配置项
            widget_id: 组件ID
            on_save: 保存回调
            on_reset: 重置回调
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None)
        self._config_item = config_item
        self._on_save = on_save
        self._on_reset = on_reset
        self._kwargs = kwargs
        
        # UI组件
        self._card = None
        self._title_label = None
        self._value_entry = None
        self._save_button = None
        self._reset_button = None
        self._error_label = None
        
        self.initialize()
        
        logger.debug_struct("配置卡片初始化", section=config_item.section.value, key=config_item.key)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建配置卡片组件"""
        # 根据是否修改确定卡片样式
        if self._config_item.is_modified:
            card_style = {
                "fg_color": ("#fff3e0", "#332d1c"),
                "border_color": ("#ff9800", "#8a5b00"),
                "border_width": 2
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
        
        # 标题和描述
        self._create_title_area(content_frame)
        
        # 值编辑区域
        self._create_edit_area(content_frame)
        
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
        
        # 配置键名
        self._title_label = ctk.CTkLabel(
            title_frame,
            text=self._config_item.key,
            font=("Microsoft YaHei", 12, "bold"),
            anchor="w"
        )
        self._title_label.pack(side="left", fill="x", expand=True)
        
        # 数据类型标签
        type_label = ctk.CTkLabel(
            title_frame,
            text=f"({self._config_item.data_type})",
            font=("Microsoft YaHei", 10),
            text_color=("gray50", "gray60")
        )
        type_label.pack(side="right", padx=(10, 0))
        
        # 注册组件
        self.register_widget("title_frame", title_frame)
        self.register_widget("type_label", type_label)
        
        # 描述文本（如果有）
        if self._config_item.description:
            desc_label = ctk.CTkLabel(
                parent,
                text=self._config_item.description,
                font=("Microsoft YaHei", 10),
                wraplength=400,
                justify="left",
                anchor="w",
                text_color=("gray60", "gray50")
            )
            desc_label.pack(fill="x", padx=0, pady=(0, 10))
            self.register_widget("desc_label", desc_label)
    
    def _create_edit_area(self, parent) -> None:
        """创建编辑区域"""
        edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
        edit_frame.pack(fill="x", padx=0, pady=0)
        
        # 根据数据类型创建不同的编辑控件
        value_str = self._config_item.get_display_value()
        
        if self._config_item.data_type == "bool":
            # 使用开关控件
            switch_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
            switch_frame.pack(fill="x", padx=0, pady=0)
            
            switch_label = ctk.CTkLabel(
                switch_frame,
                text="值:",
                font=("Microsoft YaHei", 11)
            )
            switch_label.pack(side="left", padx=(0, 10))
            
            bool_switch = Switch(
                switch_frame,
                text="启用" if self._config_item.value else "禁用",
                widget_id=f"{self._widget_id}_switch"
            )
            switch_widget = bool_switch.get_widget()
            switch_widget.pack(side="left")
            
            # 设置初始值
            bool_switch.set_value(bool(self._config_item.value))
            
            # 绑定切换事件
            def on_switch_toggled():
                new_value = bool_switch.get_value()
                self._config_item.update_value(new_value)
                bool_switch.configure(text="启用" if new_value else "禁用")
                self._update_card_style()
            
            switch_widget.configure(command=on_switch_toggled)
            
            self.register_widget("bool_switch", switch_widget)
            
        elif self._config_item.data_type == "enum":
            # 使用下拉菜单
            enum_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
            enum_frame.pack(fill="x", padx=0, pady=0)
            
            enum_label = ctk.CTkLabel(
                enum_frame,
                text="值:",
                font=("Microsoft YaHei", 11)
            )
            enum_label.pack(side="left", padx=(0, 10))
            
            # 获取枚举值
            enum_class = self._config_item.constraints.get("enum_class")
            if enum_class:
                enum_values = [e.value for e in enum_class]
            else:
                enum_values = [str(self._config_item.value)]
            
            enum_combo = ctk.CTkComboBox(
                enum_frame,
                values=enum_values,
                width=200,
                command=self._on_enum_changed
            )
            enum_combo.set(str(self._config_item.value))
            enum_combo.pack(side="left")
            
            self.register_widget("enum_combo", enum_combo)
            
        else:
            # 使用文本输入框
            entry_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
            entry_frame.pack(fill="x", padx=0, pady=0)
            
            entry_label = ctk.CTkLabel(
                entry_frame,
                text="值:",
                font=("Microsoft YaHei", 11)
            )
            entry_label.pack(side="left", padx=(0, 10))
            
            # 多行文本用于复杂值
            if isinstance(self._config_item.value, (dict, list)) or len(value_str) > 50:
                self._value_entry = TextArea(
                    entry_frame,
                    widget_id=f"{self._widget_id}_text",
                    height=100 if isinstance(self._config_item.value, (dict, list)) else 60
                )
                entry_widget = self._value_entry.get_widget()
                entry_widget.pack(side="left", fill="x", expand=True)
                entry_widget.insert("1.0", value_str)
                
                # 绑定文本变更事件
                def on_text_changed(*args):
                    new_value = entry_widget.get("1.0", "end-1c")
                    success = self._config_item.update_value(new_value)
                    self._update_card_style()
                    self._show_error(not success, "值格式错误" if not success else "")
                
                entry_widget.bind("<KeyRelease>", on_text_changed)
                
            else:
                # 单行输入框
                self._value_entry = InputField(
                    entry_frame,
                    widget_id=f"{self._widget_id}_entry",
                    width=300,
                    placeholder=""
                )
                entry_widget = self._value_entry.get_widget()
                entry_widget.pack(side="left", fill="x", expand=True)
                entry_widget.insert(0, value_str)
                
                # 绑定文本变更事件
                def on_entry_changed(*args):
                    new_value = entry_widget.get()
                    success = self._config_item.update_value(new_value)
                    self._update_card_style()
                    self._show_error(not success, "值格式错误" if not success else "")
                
                entry_widget.bind("<KeyRelease>", on_entry_changed)
        
        # 默认值提示
        default_frame = ctk.CTkFrame(parent, fg_color="transparent")
        default_frame.pack(fill="x", padx=0, pady=(5, 0))
        
        default_label = ctk.CTkLabel(
            default_frame,
            text=f"默认值: {self._config_item.default_value}",
            font=("Microsoft YaHei", 9),
            text_color=("gray50", "gray60")
        )
        default_label.pack(side="left")
        
        # 约束条件提示（如果有）
        if self._config_item.constraints:
            constraints_text = ", ".join([f"{k}: {v}" for k, v in self._config_item.constraints.items() 
                                          if k not in ["enum_class"]])
            if constraints_text:
                constraints_label = ctk.CTkLabel(
                    default_frame,
                    text=f"约束: {constraints_text}",
                    font=("Microsoft YaHei", 9),
                    text_color=("gray50", "gray60")
                )
                constraints_label.pack(side="right")
                self.register_widget("constraints_label", constraints_label)
        
        # 错误标签（初始隐藏）
        self._error_label = ctk.CTkLabel(
            parent,
            text="",
            font=("Microsoft YaHei", 10),
            text_color=("red", "#ff6666")
        )
        self._error_label.pack(fill="x", padx=0, pady=(5, 0))
        self._error_label.pack_forget()
        
        self.register_widget("edit_frame", edit_frame)
        self.register_widget("default_label", default_label)
    
    def _on_enum_changed(self, choice: str) -> None:
        """处理枚举值变化"""
        self._config_item.update_value(choice)
        self._update_card_style()
    
    def _create_control_buttons(self, parent) -> None:
        """创建控制按钮"""
        # 保存按钮（仅当值被修改时启用）
        self._save_button = Button(
            parent,
            text="保存",
            widget_id=f"{self._widget_id}_save",
            width=60,
            height=30,
            state="normal" if self._config_item.is_modified else "disabled"
        )
        save_widget = self._save_button.get_widget()
        save_widget.pack(fill="x", padx=0, pady=(0, 5))
        
        # 绑定点击事件
        save_widget.configure(
            command=lambda: self._on_save(self._config_item) if self._on_save else None
        )
        
        # 重置按钮（仅当值被修改时启用）
        self._reset_button = Button(
            parent,
            text="重置",
            widget_id=f"{self._widget_id}_reset",
            width=60,
            height=30,
            fg_color="transparent",
            border_width=1,
            state="normal" if self._config_item.is_modified else "disabled"
        )
        reset_widget = self._reset_button.get_widget()
        reset_widget.pack(fill="x", padx=0, pady=0)
        
        # 绑定点击事件
        reset_widget.configure(
            command=lambda: self._on_reset(self._config_item) if self._on_reset else None
        )
        
        # 注册组件
        self.register_widget("save_button", save_widget)
        self.register_widget("reset_button", reset_widget)
    
    def _update_card_style(self) -> None:
        """更新卡片样式"""
        if not self._card or not self._card.get_widget():
            return
        
        card_widget = self._card.get_widget()
        
        if self._config_item.is_modified:
            card_widget.configure(
                fg_color=("#fff3e0", "#332d1c"),
                border_color=("#ff9800", "#8a5b00")
            )
            
            # 启用保存和重置按钮
            if self._save_button:
                self._save_button.get_widget().configure(state="normal")
            if self._reset_button:
                self._reset_button.get_widget().configure(state="normal")
        else:
            card_widget.configure(
                fg_color=("white", "gray20"),
                border_color=("gray70", "gray40")
            )
            
            # 禁用保存和重置按钮
            if self._save_button:
                self._save_button.get_widget().configure(state="disabled")
            if self._reset_button:
                self._reset_button.get_widget().configure(state="disabled")
    
    def _show_error(self, show: bool, message: str = "") -> None:
        """显示或隐藏错误消息"""
        if not self._error_label:
            return
        
        if show and message:
            self._error_label.configure(text=message)
            self._error_label.pack(fill="x", padx=0, pady=(5, 0))
        else:
            self._error_label.pack_forget()
    
    def update_config_item(self, config_item: ConfigItem) -> None:
        """
        更新配置项
        
        Args:
            config_item: 新的配置项
        """
        self._config_item = config_item
        
        # 更新卡片样式
        self._update_card_style()
        
        # TODO: 更新其他UI元素
        
        logger.debug_struct("配置卡片更新", section=config_item.section.value, key=config_item.key)


class ConfigInterface(BaseWidget):
    """
    配置管理界面
    
    现代化配置管理界面，支持：
    1. 配置项分组和树形浏览
    2. 实时配置编辑和验证
    3. 配置导入/导出
    4. 配置版本管理
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        container: Optional[Container] = None,
        **kwargs
    ):
        """
        初始化配置管理界面
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None, config_manager, event_bus)
        self._container = container
        
        # 视图状态
        self._view_type = ConfigViewType.TREE
        self._current_section = ConfigSection.APP
        
        # 配置项映射
        self._config_items: Dict[str, ConfigItem] = {}
        self._config_cards: Dict[str, ConfigCard] = {}
        
        # UI组件
        self._main_panel = None
        self._sidebar_panel = None
        self._content_panel = None
        self._action_panel = None
        
        # 初始化
        self.initialize()
        
        logger.debug_struct("配置管理界面初始化", widget_id=self._widget_id)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建配置管理界面组件"""
        # 创建主面板
        self._main_panel = Panel(self._parent)
        main_widget = self._main_panel.get_widget()
        
        # 配置网格布局
        main_widget.grid_rowconfigure(1, weight=1)  # 内容区域
        main_widget.grid_columnconfigure(1, weight=1)  # 主内容
        
        # 0. 创建操作面板（顶部）
        self._create_action_panel(main_widget)
        
        # 1. 创建侧边栏（左侧）
        self._create_sidebar_panel(main_widget)
        
        # 2. 创建内容区域（右侧）
        self._create_content_panel(main_widget)
        
        # 3. 加载配置
        self._load_config()
        
        # 注册主面板
        self.register_widget("main_panel", main_widget)
        
        return main_widget
    
    def _create_action_panel(self, parent) -> None:
        """创建操作面板"""
        logger.debug("创建操作面板")
        
        # 操作面板
        action_style = {
            "fg_color": ("gray90", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray70", "gray30"),
            "height": 50
        }
        
        self._action_panel = Panel(parent, style=action_style)
        action_widget = self._action_panel.get_widget()
        action_widget.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
        # action_widget.grid_propagate(False)  # CTkFrame可能不支持此方法
        
        # 配置操作面板网格
        action_widget.grid_columnconfigure(0, weight=1)  # 标题
        action_widget.grid_columnconfigure(1, weight=0)  # 视图切换
        action_widget.grid_columnconfigure(2, weight=0)  # 操作按钮
        
        # 标题
        title_label = ctk.CTkLabel(
            action_widget,
            text="配置管理",
            font=("Microsoft YaHei", 16, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=0)
        
        # 视图切换
        view_frame = ctk.CTkFrame(action_widget, fg_color="transparent")
        view_frame.grid(row=0, column=1, sticky="e", padx=10, pady=0)
        
        view_label = ctk.CTkLabel(
            view_frame,
            text="视图:",
            font=("Microsoft YaHei", 11)
        )
        view_label.pack(side="left", padx=(0, 5))
        
        view_options = [t.value for t in ConfigViewType]
        view_combo = ctk.CTkComboBox(
            view_frame,
            values=view_options,
            width=120,
            command=self._on_view_type_changed
        )
        view_combo.set(self._view_type.value)
        view_combo.pack(side="left")
        
        # 操作按钮
        button_frame = ctk.CTkFrame(action_widget, fg_color="transparent")
        button_frame.grid(row=0, column=2, sticky="e", padx=10, pady=0)
        
        # 保存所有按钮
        save_all_button = Button(
            button_frame,
            text="保存所有更改",
            widget_id="save_all_config",
            width=120,
            command=self._save_all_changes
        )
        save_all_widget = save_all_button.get_widget()
        save_all_widget.pack(side="left", padx=5)
        
        # 重置所有按钮
        reset_all_button = Button(
            button_frame,
            text="重置所有更改",
            widget_id="reset_all_config",
            width=120,
            fg_color="transparent",
            border_width=1,
            command=self._reset_all_changes
        )
        reset_all_widget = reset_all_button.get_widget()
        reset_all_widget.pack(side="left", padx=5)
        
        # 注册组件
        self.register_widget("action_panel", action_widget)
        self.register_widget("title_label", title_label)
        self.register_widget("view_combo", view_combo)
        self.register_widget("save_all_button", save_all_widget)
        self.register_widget("reset_all_button", reset_all_widget)
    
    def _on_view_type_changed(self, choice: str) -> None:
        """
        处理视图类型变化
        
        Args:
            choice: 选择的视图类型
        """
        try:
            self._view_type = ConfigViewType(choice)
            logger.debug_struct("视图类型变更", view_type=self._view_type.value)
            # TODO: 实现视图切换
        except ValueError:
            logger.warning_struct("无效的视图类型", choice=choice)
    
    def _create_sidebar_panel(self, parent) -> None:
        """创建侧边栏面板"""
        logger.debug("创建侧边栏面板")
        
        # 侧边栏面板
        sidebar_style = {
            "fg_color": ("gray95", "gray15"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray70", "gray30"),
            "width": 200
        }
        
        self._sidebar_panel = ScrollPanel(parent, style=sidebar_style)
        sidebar_widget = self._sidebar_panel.get_widget()
        sidebar_widget.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        # sidebar_widget.grid_propagate(False)  # CTkScrollableFrame可能不支持此方法
        
        # 侧边栏内容
        content_frame = self._sidebar_panel.get_content_frame()
        if content_frame:
            content_frame.grid_columnconfigure(0, weight=1)
            
            # 创建分区按钮
            for section in ConfigSection:
                self._create_section_button(content_frame, section)
        
        # 注册组件
        self.register_widget("sidebar_panel", sidebar_widget)
    
    def _create_section_button(self, parent, section: ConfigSection) -> None:
        """创建分区按钮"""
        # 分区显示名称
        section_names = {
            ConfigSection.APP: "应用设置",
            ConfigSection.PLUGINS: "插件设置",
            ConfigSection.EVENT_BUS: "事件总线",
            ConfigSection.LOGGING: "日志设置",
            ConfigSection.AI: "AI设置",
            ConfigSection.SECURITY: "安全设置",
            ConfigSection.UI: "界面设置",
            ConfigSection.STORAGE: "存储设置",
            ConfigSection.METRICS: "指标设置",
            ConfigSection.TESTING: "测试设置",
            ConfigSection.ENVIRONMENT: "环境变量"
        }
        
        section_name = section_names.get(section, section.value)
        
        # 创建按钮
        button = ctk.CTkButton(
            parent,
            text=section_name,
            anchor="w",
            height=40,
            corner_radius=10,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda s=section: self._on_section_selected(s)
        )
        button.pack(fill="x", padx=10, pady=2)
        
        # 注册组件
        self.register_widget(f"section_btn_{section.value}", button)
    
    def _on_section_selected(self, section: ConfigSection) -> None:
        """
        处理分区选择
        
        Args:
            section: 选中的分区
        """
        logger.debug_struct("分区选择", section=section.value)
        self._current_section = section
        self._load_section_config(section)
        
        # 更新按钮状态（高亮当前选中项）
        self._update_section_button_states(section)
    
    def _update_section_button_states(self, selected_section: ConfigSection) -> None:
        """更新分区按钮状态"""
        # TODO: 实现按钮状态更新
        pass
    
    def _create_content_panel(self, parent) -> None:
        """创建内容面板"""
        logger.debug("创建内容面板")
        
        # 内容面板
        content_style = {
            "fg_color": ("gray98", "gray10"),
            "corner_radius": 0,
            "border_width": 0
        }
        
        self._content_panel = ScrollPanel(parent, style=content_style)
        content_widget = self._content_panel.get_widget()
        content_widget.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        
        # 注册组件
        self.register_widget("content_panel", content_widget)
    
    def _load_config(self) -> None:
        """加载配置"""
        logger.debug("加载配置")
        
        if not self._config_manager:
            logger.warning("配置管理器未设置，无法加载配置")
            return
        
        # 从配置管理器获取配置
        config = self._config_manager.config
        
        # 解析配置项
        self._parse_config_items(config)
        
        # 加载默认分区
        self._load_section_config(self._current_section)
    
    def _parse_config_items(self, config: SmallPanguConfig) -> None:
        """解析配置项"""
        self._config_items.clear()
        
        # 解析应用配置
        self._parse_section_config(ConfigSection.APP, config.app)
        
        # 解析插件配置
        self._parse_section_config(ConfigSection.PLUGINS, config.plugins)
        
        # 解析事件总线配置
        self._parse_section_config(ConfigSection.EVENT_BUS, config.event_bus)
        
        # 解析日志配置
        self._parse_section_config(ConfigSection.LOGGING, config.logging)
        
        # 解析AI配置
        self._parse_section_config(ConfigSection.AI, config.ai)
        
        # 解析安全配置
        self._parse_section_config(ConfigSection.SECURITY, config.security)
        
        # 解析UI配置
        self._parse_section_config(ConfigSection.UI, config.ui)
        
        # 解析存储配置
        self._parse_section_config(ConfigSection.STORAGE, config.storage)
        
        # 解析指标配置
        self._parse_section_config(ConfigSection.METRICS, config.metrics)
        
        # 解析测试配置（如果存在）
        if config.testing:
            self._parse_section_config(ConfigSection.TESTING, config.testing)
        
        logger.debug_struct("配置项解析完成", total_items=len(self._config_items))
    
    def _parse_section_config(self, section: ConfigSection, section_config: BaseModel) -> None:
        """解析分区配置"""
        for field_name, field_info in section_config.model_fields.items():
            field_value = getattr(section_config, field_name, None)
            
            # 确定数据类型
            if field_info.annotation == int:
                data_type = "int"
            elif field_info.annotation == float:
                data_type = "float"
            elif field_info.annotation == bool:
                data_type = "bool"
            elif field_info.annotation == str:
                data_type = "str"
            elif hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ == Literal:
                data_type = "enum"
            elif isinstance(field_value, Enum):
                data_type = "enum"
            else:
                data_type = "str"
            
            # 提取约束条件
            constraints = {}
            if field_info.json_schema_extra:
                constraints.update(field_info.json_schema_extra)
            
            # 如果是枚举类型，添加枚举类信息
            if isinstance(field_value, Enum):
                constraints["enum_class"] = type(field_value)
            
            # 创建配置项
            item_id = f"{section.value}.{field_name}"
            config_item = ConfigItem(
                section=section,
                key=field_name,
                value=field_value,
                data_type=data_type,
                description=field_info.description or "",
                default_value=field_info.default,
                constraints=constraints,
                original_value=field_value
            )
            
            self._config_items[item_id] = config_item
    
    def _load_section_config(self, section: ConfigSection) -> None:
        """加载分区配置"""
        logger.debug_struct("加载分区配置", section=section.value)
        
        # 清理现有卡片
        for card in self._config_cards.values():
            card.destroy()
        self._config_cards.clear()
        
        # 获取内容框架
        content_frame = self._content_panel.get_content_frame()
        if not content_frame:
            return
        
        # 配置内容框架网格
        content_frame.grid_columnconfigure(0, weight=1)
        
        # 创建该分区的配置卡片
        section_items = [(item_id, item) for item_id, item in self._config_items.items() 
                         if item.section == section]
        
        for item_id, config_item in section_items:
            self._create_config_card(content_frame, config_item)
        
        logger.debug_struct("分区配置加载完成", section=section.value, item_count=len(section_items))
    
    def _create_config_card(self, parent, config_item: ConfigItem) -> None:
        """创建配置卡片"""
        try:
            config_card = ConfigCard(
                parent,
                config_item=config_item,
                widget_id=f"config_card_{config_item.section.value}_{config_item.key}",
                on_save=self._on_config_save,
                on_reset=self._on_config_reset
            )
            
            card_widget = config_card.get_widget()
            if card_widget:
                card_widget.pack(fill="x", padx=10, pady=5, anchor="nw")
            
            # 存储卡片引用
            item_id = f"{config_item.section.value}.{config_item.key}"
            self._config_cards[item_id] = config_card
            
            logger.debug_struct("配置卡片创建", section=config_item.section.value, key=config_item.key)
            
        except Exception as e:
            logger.error_struct("配置卡片创建失败", 
                               section=config_item.section.value, 
                               key=config_item.key, 
                               error=str(e))
    
    def _on_config_save(self, config_item: ConfigItem) -> None:
        """
        处理配置保存
        
        Args:
            config_item: 配置项
        """
        logger.debug_struct("配置保存请求", 
                           section=config_item.section.value, 
                           key=config_item.key,
                           value=config_item.value)
        
        # 调用配置管理器保存配置
        if self._config_manager:
            full_key = f"{config_item.section.value}.{config_item.key}"
            success = self._config_manager.set_value(full_key, config_item.value, persistent=True)
            if not success:
                logger.error_struct("配置保存失败", 
                                  section=config_item.section.value, 
                                  key=config_item.key,
                                  value=config_item.value)
                # 可以考虑显示错误消息给用户
                return
        
        # 发布事件（供其他组件监听）
        if self._event_bus:
            self._event_bus.publish("config.save_request", {
                "section": config_item.section.value,
                "key": config_item.key,
                "value": config_item.value,
                "timestamp": "now"
            })
        
        # 更新原始值
        config_item.original_value = copy.deepcopy(config_item.value)
        config_item.is_modified = False
        
        # 更新卡片样式
        item_id = f"{config_item.section.value}.{config_item.key}"
        if item_id in self._config_cards:
            self._config_cards[item_id].update_config_item(config_item)
    
    def _on_config_reset(self, config_item: ConfigItem) -> None:
        """
        处理配置重置
        
        Args:
            config_item: 配置项
        """
        logger.debug_struct("配置重置请求", 
                           section=config_item.section.value, 
                           key=config_item.key)
        
        # 重置为原始值
        config_item.value = copy.deepcopy(config_item.original_value)
        config_item.is_modified = False
        
        # 更新卡片
        item_id = f"{config_item.section.value}.{config_item.key}"
        if item_id in self._config_cards:
            self._config_cards[item_id].update_config_item(config_item)
    
    def _save_all_changes(self) -> None:
        """保存所有更改"""
        logger.debug("保存所有更改")
        
        modified_items = [item for item in self._config_items.values() if item.is_modified]
        
        for item in modified_items:
            self._on_config_save(item)
        
        logger.debug_struct("所有更改保存完成", modified_count=len(modified_items))
        
        # 发布事件
        if self._event_bus:
            self._event_bus.publish("config.all_saved", {
                "modified_count": len(modified_items),
                "timestamp": "now"
            })
    
    def _reset_all_changes(self) -> None:
        """重置所有更改"""
        logger.debug("重置所有更改")
        
        modified_items = [item for item in self._config_items.values() if item.is_modified]
        
        for item in modified_items:
            self._on_config_reset(item)
        
        logger.debug_struct("所有更改重置完成", modified_count=len(modified_items))
    
    def refresh_config(self) -> None:
        """刷新配置"""
        self._load_config()
    
    def get_modified_count(self) -> int:
        """获取已修改的配置项数量"""
        return len([item for item in self._config_items.values() if item.is_modified])
    
    def get_status(self) -> Dict[str, Any]:
        """获取配置管理界面状态"""
        return {
            "widget_id": self._widget_id,
            "view_type": self._view_type.value,
            "current_section": self._current_section.value,
            "total_items": len(self._config_items),
            "modified_items": self.get_modified_count(),
            "has_config_manager": self._config_manager is not None
        }


class ConfigView:
    """
    配置管理视图
    
    集成配置管理界面到主窗口视图框架中
    """
    
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化配置管理视图
        
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
        self._config_interface = None
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("配置管理视图初始化")
    
    def _initialize(self) -> None:
        """初始化配置管理视图"""
        try:
            # 创建主框架
            self._main_frame = ctk.CTkFrame(self._parent)
            self._main_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            # 配置网格
            self._main_frame.grid_rowconfigure(0, weight=1)
            self._main_frame.grid_columnconfigure(0, weight=1)
            
            # 创建配置管理界面
            self._config_interface = ConfigInterface(
                self._main_frame,
                widget_id="config_management",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            config_widget = self._config_interface.get_widget()
            if config_widget:
                config_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # 订阅配置相关事件
            self._subscribe_events()
            
            logger.info("配置管理视图初始化完成")
            
        except Exception as e:
            logger.error("配置管理视图初始化失败", exc_info=True)
            raise UIError(f"配置管理视图初始化失败: {e}")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 配置更新事件
        self._event_bus.subscribe("config.updated", self._on_config_updated)
        
        # 配置重载事件
        self._event_bus.subscribe("config.reloaded", self._on_config_reloaded)
        
        # 环境变量变更事件
        self._event_bus.subscribe("environment.changed", self._on_environment_changed)
    
    def _on_config_updated(self, event) -> None:
        """处理配置更新"""
        data = event.data
        section = data.get("section")
        key = data.get("key")
        
        logger.debug_struct("配置更新", section=section, key=key)
        
        # 刷新配置界面
        if self._config_interface:
            self._config_interface.refresh_config()
    
    def _on_config_reloaded(self, event) -> None:
        """处理配置重载"""
        logger.debug("配置重载")
        
        # 刷新配置界面
        if self._config_interface:
            self._config_interface.refresh_config()
    
    def _on_environment_changed(self, event) -> None:
        """处理环境变量变更"""
        logger.debug("环境变量变更")
        
        # 刷新配置界面
        if self._config_interface:
            self._config_interface.refresh_config()
    
    def get_widget(self):
        """获取主框架"""
        return self._main_frame
    
    def get_config_interface(self) -> ConfigInterface:
        """获取配置管理界面"""
        return self._config_interface
    
    def get_status(self) -> Dict[str, Any]:
        """获取配置管理视图状态"""
        if self._config_interface:
            return self._config_interface.get_status()
        return {"initialized": False}


# 导出
__all__ = [
    "ConfigViewType",
    "ConfigSection",
    "ConfigItem",
    "ConfigCard",
    "ConfigInterface",
    "ConfigView"
]