"""
设置界面

提供用户友好的系统设置界面，包括：
1. 外观设置（主题、字体、窗口）
2. 聊天设置（历史记录、Markdown渲染）
3. 快捷键设置
4. 开发者选项
5. 保存和应用设置
"""

import customtkinter as ctk
import logging
import json
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..config.models import UIConfig, Theme, Language, AppConfig, AIConfig
from .manager import UIManager
from .widgets import BaseWidget, Panel, ScrollPanel, Card, Button, Label, Switch, TextArea, InputField
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class SettingsCategory(str, Enum):
    """设置分类枚举"""
    APPEARANCE = "appearance"      # 外观设置
    CHAT = "chat"                  # 聊天设置
    SHORTCUTS = "shortcuts"        # 快捷键设置
    DEVELOPER = "developer"        # 开发者选项
    GENERAL = "general"            # 通用设置


class SettingItem:
    """设置项"""
    
    def __init__(
        self,
        category: SettingsCategory,
        key: str,
        label: str,
        description: str,
        value_type: str,  # "bool", "int", "float", "str", "enum", "color"
        default_value: Any,
        current_value: Any,
        options: Optional[List[Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        widget_type: Optional[str] = None,  # "switch", "input", "select", "slider"
        on_change: Optional[Callable[[Any], None]] = None
    ):
        self.category = category
        self.key = key
        self.label = label
        self.description = description
        self.value_type = value_type
        self.default_value = default_value
        self.current_value = current_value
        self.original_value = current_value
        self.options = options or []
        self.constraints = constraints or {}
        self.widget_type = widget_type or self._infer_widget_type()
        self.on_change = on_change
        self.is_modified = False
    
    def _infer_widget_type(self) -> str:
        """根据值类型推断控件类型"""
        if self.value_type == "bool":
            return "switch"
        elif self.value_type == "enum" and self.options:
            return "select"
        elif self.value_type in ["int", "float"]:
            if "ge" in self.constraints and "le" in self.constraints:
                return "slider"
            else:
                return "input"
        else:
            return "input"
    
    def set_value(self, value: Any) -> bool:
        """设置值"""
        try:
            # 类型转换
            if self.value_type == "bool":
                if isinstance(value, str):
                    value = value.lower() in ("true", "yes", "1", "on")
                validated_value = bool(value)
            elif self.value_type == "int":
                validated_value = int(value)
                if "ge" in self.constraints and validated_value < self.constraints["ge"]:
                    return False
                if "le" in self.constraints and validated_value > self.constraints["le"]:
                    return False
            elif self.value_type == "float":
                validated_value = float(value)
                if "ge" in self.constraints and validated_value < self.constraints["ge"]:
                    return False
                if "le" in self.constraints and validated_value > self.constraints["le"]:
                    return False
            elif self.value_type == "enum" and self.options:
                if value not in self.options:
                    return False
                validated_value = value
            else:
                validated_value = str(value)
            
            # 检查是否修改
            self.is_modified = (validated_value != self.original_value)
            self.current_value = validated_value
            
            # 调用变更回调
            if self.on_change:
                self.on_change(validated_value)
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def reset_to_default(self) -> None:
        """重置为默认值"""
        self.set_value(self.default_value)
    
    def reset_to_original(self) -> None:
        """重置为原始值"""
        self.set_value(self.original_value)


class SettingCard(BaseWidget):
    """设置卡片组件"""
    
    def __init__(
        self,
        parent,
        setting_item: SettingItem,
        widget_id: Optional[str] = None,
        **kwargs
    ):
        """
        初始化设置卡片
        
        Args:
            parent: 父组件
            setting_item: 设置项
            widget_id: 组件ID
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None)
        self._setting_item = setting_item
        self._kwargs = kwargs
        
        # UI组件
        self._card = None
        self._title_label = None
        self._description_label = None
        self._control_widget = None
        self._value_label = None
        
        self.initialize()
        
        logger.debug_struct("设置卡片初始化", key=setting_item.key)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建设置卡片组件"""
        # 创建卡片
        self._card = Card(self._parent, style={
            "fg_color": ("white", "gray20"),
            "border_color": ("gray80", "gray40"),
            "border_width": 1,
            "corner_radius": 8,
            "padding": 15
        })
        card_widget = self._card.get_widget()
        
        # 配置卡片网格
        card_widget.grid_columnconfigure(1, weight=1)  # 控制区域
        
        # 标题和描述
        self._create_info_area(card_widget)
        
        # 控制组件
        self._create_control_area(card_widget)
        
        # 修改指示器
        if self._setting_item.is_modified:
            self._add_modified_indicator(card_widget)
        
        return card_widget
    
    def _create_info_area(self, parent) -> None:
        """创建信息区域"""
        # 信息框架
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 15))
        
        # 标题
        self._title_label = ctk.CTkLabel(
            info_frame,
            text=self._setting_item.label,
            font=("Microsoft YaHei", 12, "bold"),
            anchor="w"
        )
        self._title_label.pack(anchor="w", pady=(0, 5))
        
        # 描述
        if self._setting_item.description:
            self._description_label = ctk.CTkLabel(
                info_frame,
                text=self._setting_item.description,
                font=("Microsoft YaHei", 10),
                anchor="w",
                text_color=("gray50", "gray60"),
                wraplength=300,
                justify="left"
            )
            self._description_label.pack(anchor="w", fill="x")
        
        self.register_widget("info_frame", info_frame)
    
    def _create_control_area(self, parent) -> None:
        """创建控制区域"""
        # 控制框架
        control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        control_frame.grid(row=0, column=1, sticky="e")
        
        # 根据控件类型创建相应控件
        widget_type = self._setting_item.widget_type
        value = self._setting_item.current_value
        
        if widget_type == "switch":
            self._control_widget = ctk.CTkSwitch(
                control_frame,
                text="",
                width=40,
                command=self._on_switch_toggle
            )
            self._control_widget.select() if value else self._control_widget.deselect()
            self._control_widget.pack(side="right")
            
        elif widget_type == "select" and self._setting_item.options:
            # 创建选项文本列表
            option_texts = [str(opt) for opt in self._setting_item.options]
            self._control_widget = ctk.CTkComboBox(
                control_frame,
                values=option_texts,
                width=150,
                command=self._on_combo_select
            )
            self._control_widget.set(str(value))
            self._control_widget.pack(side="right")
            
        elif widget_type == "slider":
            # 创建滑块
            min_val = self._setting_item.constraints.get("ge", 0)
            max_val = self._setting_item.constraints.get("le", 100)
            
            slider_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
            slider_frame.pack(side="right", fill="x", expand=True)
            
            # 值标签
            self._value_label = ctk.CTkLabel(
                slider_frame,
                text=str(value),
                width=40,
                anchor="center"
            )
            self._value_label.pack(side="right", padx=(5, 0))
            
            # 滑块
            self._control_widget = ctk.CTkSlider(
                slider_frame,
                from_=min_val,
                to=max_val,
                width=120,
                command=self._on_slider_change
            )
            self._control_widget.set(float(value))
            self._control_widget.pack(side="right")
            
        else:  # input
            self._control_widget = ctk.CTkEntry(
                control_frame,
                width=150,
                placeholder_text="输入值..."
            )
            self._control_widget.insert(0, str(value))
            self._control_widget.bind("<Return>", lambda e: self._on_input_change())
            self._control_widget.pack(side="right")
        
        self.register_widget("control_frame", control_frame)
    
    def _add_modified_indicator(self, parent) -> None:
        """添加修改指示器"""
        modified_frame = ctk.CTkFrame(parent, fg_color="transparent")
        modified_frame.grid(row=1, column=1, sticky="e", pady=(5, 0))
        
        modified_label = ctk.CTkLabel(
            modified_frame,
            text="已修改",
            font=("Microsoft YaHei", 9),
            text_color="orange"
        )
        modified_label.pack(side="right")
        
        # 重置按钮
        reset_btn = ctk.CTkButton(
            modified_frame,
            text="重置",
            width=50,
            height=20,
            font=("Microsoft YaHei", 8),
            command=self._reset_setting
        )
        reset_btn.pack(side="right", padx=(5, 0))
        
        self.register_widget("modified_frame", modified_frame)
        self.register_widget("modified_label", modified_label)
        self.register_widget("reset_btn", reset_btn)
    
    def _on_switch_toggle(self) -> None:
        """处理开关切换"""
        if self._control_widget:
            new_value = self._control_widget.get()
            success = self._setting_item.set_value(new_value)
            if success:
                self._update_modified_indicator()
    
    def _on_combo_select(self, choice: str) -> None:
        """处理下拉选择"""
        # 找到对应的原始值
        for option in self._setting_item.options:
            if str(option) == choice:
                success = self._setting_item.set_value(option)
                if success:
                    self._update_modified_indicator()
                break
    
    def _on_slider_change(self, value: float) -> None:
        """处理滑块变化"""
        if self._value_label:
            self._value_label.configure(text=f"{value:.0f}")
        
        # 立即更新设置项
        success = self._setting_item.set_value(value)
        if success:
            self._update_modified_indicator()
    
    def _on_input_change(self) -> None:
        """处理输入框变化"""
        if self._control_widget:
            new_value = self._control_widget.get()
            success = self._setting_item.set_value(new_value)
            if success:
                self._update_modified_indicator()
    
    def _reset_setting(self) -> None:
        """重置设置项"""
        self._setting_item.reset_to_original()
        self._update_control_widget()
        self._update_modified_indicator()
    
    def _update_control_widget(self) -> None:
        """更新控制组件"""
        value = self._setting_item.current_value
        
        if self._setting_item.widget_type == "switch" and self._control_widget:
            if value:
                self._control_widget.select()
            else:
                self._control_widget.deselect()
        elif self._setting_item.widget_type == "select" and self._control_widget:
            self._control_widget.set(str(value))
        elif self._setting_item.widget_type == "slider" and self._control_widget:
            self._control_widget.set(float(value))
            if self._value_label:
                self._value_label.configure(text=str(value))
        elif self._control_widget:
            self._control_widget.delete(0, "end")
            self._control_widget.insert(0, str(value))
    
    def _update_modified_indicator(self) -> None:
        """更新修改指示器"""
        # 移除现有指示器
        modified_frame = self.get_widget("modified_frame")
        if modified_frame:
            modified_frame.destroy()
        
        # 如果需要，添加新指示器
        if self._setting_item.is_modified:
            self._add_modified_indicator(self._card.get_widget())


class SettingsInterface(BaseWidget):
    """
    设置界面
    
    提供用户友好的系统设置界面，支持实时预览和应用设置
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
        初始化设置界面
        
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
        
        # 设置状态
        self._current_category = SettingsCategory.APPEARANCE
        self._setting_items: Dict[str, SettingItem] = {}
        self._setting_cards: Dict[str, SettingCard] = {}
        
        # UI组件
        self._main_panel = None
        self._sidebar = None
        self._content_area = None
        self._action_bar = None
        
        # 初始化设置项
        self._initialize_setting_items()
        
        # 初始化
        self.initialize()
        
        logger.debug_struct("设置界面初始化", widget_id=self._widget_id)
    
    def _initialize_setting_items(self) -> None:
        """初始化设置项"""
        logger.debug("初始化设置项")
        
        # 从配置管理器获取当前配置
        ui_config = self._get_ui_config()
        
        # 外观设置
        self._add_setting_item(
            SettingsCategory.APPEARANCE,
            "theme",
            "主题",
            "选择界面主题",
            "enum",
            Theme.DARK.value,
            ui_config.theme.value,
            options=[t.value for t in Theme],
            on_change=self._on_theme_changed
        )
        
        self._add_setting_item(
            SettingsCategory.APPEARANCE,
            "language",
            "语言",
            "选择界面语言",
            "enum",
            Language.ZH_CN.value,
            ui_config.language.value,
            options=[l.value for l in Language],
            on_change=self._on_language_changed
        )
        
        self._add_setting_item(
            SettingsCategory.APPEARANCE,
            "font_family",
            "字体",
            "选择界面字体",
            "str",
            "Microsoft YaHei",
            ui_config.font_family
        )
        
        self._add_setting_item(
            SettingsCategory.APPEARANCE,
            "font_size",
            "字体大小",
            "调整字体大小",
            "int",
            12,
            ui_config.font_size,
            constraints={"ge": 8, "le": 24}
        )
        
        self._add_setting_item(
            SettingsCategory.APPEARANCE,
            "window_width",
            "窗口宽度",
            "设置窗口宽度",
            "int",
            1280,
            ui_config.window_width,
            constraints={"ge": 400, "le": 2560}
        )
        
        self._add_setting_item(
            SettingsCategory.APPEARANCE,
            "window_height",
            "窗口高度",
            "设置窗口高度",
            "int",
            720,
            ui_config.window_height,
            constraints={"ge": 300, "le": 1440}
        )
        
        # 聊天设置
        self._add_setting_item(
            SettingsCategory.CHAT,
            "chat_history_limit",
            "聊天历史记录",
            "保留的聊天记录数量",
            "int",
            100,
            ui_config.chat_history_limit,
            constraints={"ge": 10, "le": 1000}
        )
        
        self._add_setting_item(
            SettingsCategory.CHAT,
            "auto_scroll",
            "自动滚动",
            "是否自动滚动到最新消息",
            "bool",
            True,
            ui_config.auto_scroll
        )
        
        self._add_setting_item(
            SettingsCategory.CHAT,
            "markdown_render",
            "Markdown渲染",
            "是否渲染Markdown格式",
            "bool",
            True,
            ui_config.markdown_render
        )
        
        # 通用设置
        self._add_setting_item(
            SettingsCategory.GENERAL,
            "show_developer_tools",
            "开发者工具",
            "显示开发者工具菜单",
            "bool",
            False,
            ui_config.show_developer_tools
        )
        
        self._add_setting_item(
            SettingsCategory.GENERAL,
            "enable_inspector",
            "UI检查器",
            "启用UI组件检查器",
            "bool",
            False,
            ui_config.enable_inspector
        )
        
        # 快捷键设置（占位符）
        self._add_setting_item(
            SettingsCategory.SHORTCUTS,
            "shortcut_new_chat",
            "新建对话",
            "新建聊天对话的快捷键",
            "str",
            "Ctrl+N",
            "Ctrl+N"
        )
        
        self._add_setting_item(
            SettingsCategory.SHORTCUTS,
            "shortcut_save",
            "保存",
            "保存配置的快捷键",
            "str",
            "Ctrl+S",
            "Ctrl+S"
        )
        
        self._add_setting_item(
            SettingsCategory.SHORTCUTS,
            "shortcut_quit",
            "退出",
            "退出应用的快捷键",
            "str",
            "Ctrl+Q",
            "Ctrl+Q"
        )
        
        logger.debug_struct("设置项初始化完成", item_count=len(self._setting_items))
    
    def _get_ui_config(self) -> UIConfig:
        """获取UI配置"""
        if self._config_manager:
            return self._config_manager.config.ui
        else:
            # 返回默认配置
            return UIConfig()
    
    def _add_setting_item(
        self,
        category: SettingsCategory,
        key: str,
        label: str,
        description: str,
        value_type: str,
        default_value: Any,
        current_value: Any,
        options: Optional[List[Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        on_change: Optional[Callable[[Any], None]] = None
    ) -> None:
        """添加设置项"""
        full_key = f"{category.value}.{key}"
        
        setting_item = SettingItem(
            category=category,
            key=key,
            label=label,
            description=description,
            value_type=value_type,
            default_value=default_value,
            current_value=current_value,
            options=options,
            constraints=constraints,
            on_change=on_change
        )
        
        self._setting_items[full_key] = setting_item
    
    def _on_theme_changed(self, theme_value: str) -> None:
        """处理主题变更"""
        logger.debug_struct("主题设置变更", theme=theme_value)
        
        # 发布主题变更事件
        if self._event_bus:
            self._event_bus.publish("theme.changed", {
                "theme": theme_value,
                "source": "settings"
            })
    
    def _on_language_changed(self, language_value: str) -> None:
        """处理语言变更"""
        logger.debug_struct("语言设置变更", language=language_value)
        
        # 发布语言变更事件
        if self._event_bus:
            self._event_bus.publish("language.changed", {
                "language": language_value,
                "source": "settings"
            })
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建设置界面组件"""
        # 创建主面板
        self._main_panel = Panel(self._parent)
        main_widget = self._main_panel.get_widget()
        
        # 配置网格布局
        main_widget.grid_rowconfigure(1, weight=1)  # 内容区域
        main_widget.grid_columnconfigure(1, weight=1)  # 内容区域
        
        # 1. 创建侧边栏
        self._create_sidebar(main_widget)
        
        # 2. 创建内容区域
        self._create_content_area(main_widget)
        
        # 3. 创建操作栏
        self._create_action_bar(main_widget)
        
        # 4. 加载默认分类
        self._load_category(self._current_category)
        
        # 注册主面板
        self.register_widget("main_panel", main_widget)
        
        return main_widget
    
    def _create_sidebar(self, parent) -> None:
        """创建侧边栏"""
        logger.debug("创建设置侧边栏")
        
        # 侧边栏框架
        sidebar_style = {
            "fg_color": ("gray95", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray80", "gray30"),
            "width": 200
        }
        
        self._sidebar = Panel(parent, style=sidebar_style)
        sidebar_widget = self._sidebar.get_widget()
        sidebar_widget.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=0, pady=0)
        sidebar_widget.grid_propagate(False)
        
        # 配置网格
        sidebar_widget.grid_rowconfigure(1, weight=1)  # 分类区域
        
        # 侧边栏标题
        title_frame = ctk.CTkFrame(sidebar_widget, fg_color="transparent", height=60)
        title_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        title_frame.grid_propagate(False)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="设置分类",
            font=("Microsoft YaHei", 14, "bold"),
            anchor="center"
        )
        title_label.pack(expand=True, fill="both", padx=20, pady=10)
        
        # 分类框架
        category_frame = ctk.CTkScrollableFrame(sidebar_widget, fg_color="transparent")
        category_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 创建分类按钮
        self._category_buttons: Dict[SettingsCategory, ctk.CTkButton] = {}
        
        categories = [
            (SettingsCategory.APPEARANCE, "🎨 外观", "主题、字体、窗口设置"),
            (SettingsCategory.CHAT, "💬 聊天", "聊天相关设置"),
            (SettingsCategory.SHORTCUTS, "⌨️ 快捷键", "键盘快捷键设置"),
            (SettingsCategory.DEVELOPER, "🔧 开发者", "开发者选项"),
            (SettingsCategory.GENERAL, "⚙️ 通用", "通用设置")
        ]
        
        for category, title, description in categories:
            self._create_category_button(category_frame, category, title, description)
        
        # 注册组件
        self.register_widget("sidebar", sidebar_widget)
        self.register_widget("category_frame", category_frame)
    
    def _create_category_button(
        self, 
        parent, 
        category: SettingsCategory, 
        title: str, 
        description: str
    ) -> None:
        """创建分类按钮"""
        # 按钮框架
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=70)
        button_frame.pack(fill="x", padx=5, pady=2)
        
        # 按钮
        button = ctk.CTkButton(
            button_frame,
            text=title,
            anchor="w",
            height=60,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda cat=category: self._on_category_click(cat)
        )
        button.pack(fill="x", padx=5, pady=5)
        
        # 存储按钮引用
        self._category_buttons[category] = button
        
        # 注册组件
        self.register_widget(f"category_btn_{category.value}", button)
    
    def _on_category_click(self, category: SettingsCategory) -> None:
        """处理分类按钮点击"""
        logger.debug_struct("设置分类点击", category=category.value)
        
        # 切换分类
        self.switch_category(category)
        
        # 更新按钮状态
        self._update_category_button_states(category)
    
    def _update_category_button_states(self, selected_category: SettingsCategory) -> None:
        """更新分类按钮状态"""
        for category, button in self._category_buttons.items():
            if category == selected_category:
                # 选中状态
                button.configure(fg_color=("gray75", "gray25"))
            else:
                # 默认状态
                button.configure(fg_color="transparent")
    
    def _create_content_area(self, parent) -> None:
        """创建内容区域"""
        logger.debug("创建设置内容区域")
        
        # 内容区域框架
        content_style = {
            "fg_color": ("gray98", "gray15"),
            "corner_radius": 0,
            "border_width": 0
        }
        
        self._content_area = ScrollPanel(parent, style=content_style)
        content_widget = self._content_area.get_widget()
        content_widget.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # 配置内容框架
        content_frame = self._content_area.get_content_frame()
        if content_frame:
            content_frame.grid_columnconfigure(0, weight=1)
        
        # 注册组件
        self.register_widget("content_area", content_widget)
    
    def _create_action_bar(self, parent) -> None:
        """创建操作栏"""
        logger.debug("创建设置操作栏")
        
        # 操作栏框架
        action_style = {
            "fg_color": ("gray90", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray70", "gray30"),
            "height": 60
        }
        
        self._action_bar = Panel(parent, style=action_style)
        action_widget = self._action_bar.get_widget()
        action_widget.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        action_widget.grid_propagate(False)
        
        # 配置网格
        action_widget.grid_columnconfigure(0, weight=1)  # 状态区域
        action_widget.grid_columnconfigure(1, weight=0)  # 按钮区域
        
        # 状态标签
        self._status_label = ctk.CTkLabel(
            action_widget,
            text="就绪",
            font=("Microsoft YaHei", 11),
            anchor="w"
        )
        self._status_label.grid(row=0, column=0, sticky="w", padx=20, pady=0)
        
        # 按钮框架
        button_frame = ctk.CTkFrame(action_widget, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="e", padx=20, pady=0)
        
        # 重置按钮
        reset_button = ctk.CTkButton(
            button_frame,
            text="重置所有",
            width=100,
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray30"),
            command=self._reset_all_settings
        )
        reset_button.pack(side="left", padx=(0, 10))
        
        # 应用按钮
        self._apply_button = ctk.CTkButton(
            button_frame,
            text="应用设置",
            width=100,
            command=self._apply_settings
        )
        self._apply_button.pack(side="left", padx=(0, 10))
        
        # 保存按钮
        self._save_button = ctk.CTkButton(
            button_frame,
            text="保存",
            width=80,
            command=self._save_settings
        )
        self._save_button.pack(side="left")
        
        # 注册组件
        self.register_widget("action_bar", action_widget)
        self.register_widget("status_label", self._status_label)
    
    def _load_category(self, category: SettingsCategory) -> None:
        """加载分类设置"""
        logger.debug_struct("加载设置分类", category=category.value)
        
        # 清空内容区域
        content_frame = self._content_area.get_content_frame()
        if not content_frame:
            return
        
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        # 分类标题
        title_texts = {
            SettingsCategory.APPEARANCE: "🎨 外观设置",
            SettingsCategory.CHAT: "💬 聊天设置",
            SettingsCategory.SHORTCUTS: "⌨️ 快捷键设置",
            SettingsCategory.DEVELOPER: "🔧 开发者选项",
            SettingsCategory.GENERAL: "⚙️ 通用设置"
        }
        
        title = title_texts.get(category, "设置")
        
        title_label = ctk.CTkLabel(
            content_frame,
            text=title,
            font=("Microsoft YaHei", 18, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))
        
        # 加载该分类的设置项
        category_items = [
            item for item in self._setting_items.values()
            if item.category == category
        ]
        
        for i, item in enumerate(category_items, 1):
            # 创建设置卡片
            setting_card = SettingCard(
                content_frame,
                setting_item=item,
                widget_id=f"setting_card_{item.key}"
            )
            
            card_widget = setting_card.get_widget()
            if card_widget:
                card_widget.grid(row=i, column=0, sticky="nsew", padx=30, pady=(0, 15))
                
                # 存储卡片引用
                self._setting_cards[item.key] = setting_card
        
        # 添加底部空白
        bottom_spacer = ctk.CTkFrame(content_frame, fg_color="transparent", height=20)
        bottom_spacer.grid(row=len(category_items) + 1, column=0, sticky="nsew")
        
        # 更新状态
        self._update_status()
    
    def _update_status(self) -> None:
        """更新状态栏"""
        if not hasattr(self, '_status_label'):
            return
        
        # 计算修改的数量
        modified_count = sum(1 for item in self._setting_items.values() if item.is_modified)
        
        if modified_count == 0:
            self._status_label.configure(text="就绪")
        else:
            self._status_label.configure(
                text=f"有 {modified_count} 项设置已修改",
                text_color="orange"
            )
    
    def _reset_all_settings(self) -> None:
        """重置所有设置"""
        logger.debug("重置所有设置")
        
        for item in self._setting_items.values():
            item.reset_to_default()
        
        # 更新所有卡片
        for card in self._setting_cards.values():
            if hasattr(card, '_update_control_widget'):
                card._update_control_widget()
            if hasattr(card, '_update_modified_indicator'):
                card._update_modified_indicator()
        
        self._update_status()
        
        # 显示成功消息
        self._show_message("所有设置已重置为默认值", "green")
    
    def _apply_settings(self) -> None:
        """应用设置"""
        logger.debug("应用设置")
        
        try:
            # 收集修改的设置
            modified_settings = {}
            for full_key, item in self._setting_items.items():
                if item.is_modified:
                    category, key = full_key.split(".", 1)
                    
                    if category not in modified_settings:
                        modified_settings[category] = {}
                    
                    modified_settings[category][key] = item.current_value
            
            # 更新配置管理器
            if self._config_manager and modified_settings:
                for category, settings in modified_settings.items():
                    for key, value in settings:
                        config_path = f"ui.{key}" if category == "appearance" else f"{category}.{key}"
                        self._config_manager.set_value(config_path, value)
                
                # 标记为已应用
                for item in self._setting_items.values():
                    if item.is_modified:
                        item.original_value = item.current_value
                        item.is_modified = False
                
                # 更新卡片
                for card in self._setting_cards.values():
                    if hasattr(card, '_update_modified_indicator'):
                        card._update_modified_indicator()
                
                self._update_status()
                
                # 显示成功消息
                self._show_message("设置已应用", "green")
                
                # 发布设置已应用事件
                if self._event_bus:
                    self._event_bus.publish("settings.applied", {
                        "modified_count": len(modified_settings),
                        "timestamp": time.time()
                    })
            
        except Exception as e:
            logger.error_struct("应用设置失败", error=str(e))
            self._show_message(f"应用设置失败: {e}", "red")
    
    def _save_settings(self) -> None:
        """保存设置到文件"""
        logger.debug("保存设置")
        
        try:
            if self._config_manager:
                # 先应用设置
                self._apply_settings()
                
                # 保存到文件
                success = self._config_manager.save()
                
                if success:
                    self._show_message("设置已保存到文件", "green")
                else:
                    self._show_message("保存设置失败", "red")
            else:
                self._show_message("配置管理器不可用", "red")
                
        except Exception as e:
            logger.error_struct("保存设置失败", error=str(e))
            self._show_message(f"保存设置失败: {e}", "red")
    
    def _show_message(self, message: str, color: str = "green") -> None:
        """显示消息"""
        if hasattr(self, '_status_label'):
            self._status_label.configure(text=message, text_color=color)
            
            # 3秒后恢复
            def restore_status():
                self._update_status()
            
            self._parent.after(3000, restore_status)
    
    def switch_category(self, category: SettingsCategory) -> bool:
        """
        切换设置分类
        
        Args:
            category: 分类
            
        Returns:
            是否成功切换
        """
        logger.debug_struct("切换设置分类", category=category.value)
        
        try:
            self._current_category = category
            self._load_category(category)
            
            logger.debug_struct("设置分类切换成功", category=category.value)
            return True
            
        except Exception as e:
            logger.error_struct("设置分类切换失败", category=category.value, error=str(e))
            return False
    
    def get_current_category(self) -> SettingsCategory:
        """获取当前分类"""
        return self._current_category
    
    def get_modified_count(self) -> int:
        """获取修改的设置项数量"""
        return sum(1 for item in self._setting_items.values() if item.is_modified)
    
    def get_status(self) -> Dict[str, Any]:
        """获取设置界面状态"""
        return {
            "widget_id": self._widget_id,
            "current_category": self._current_category.value,
            "setting_item_count": len(self._setting_items),
            "modified_count": self.get_modified_count(),
            "has_config_manager": self._config_manager is not None
        }


class SettingsView:
    """
    设置视图
    
    集成设置界面到主窗口视图框架中
    """
    
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化设置视图
        
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
        self._settings_interface = None
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("设置视图初始化")
    
    def _initialize(self) -> None:
        """初始化设置视图"""
        try:
            # 创建主框架
            self._main_frame = ctk.CTkFrame(self._parent)
            self._main_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            # 配置网格
            self._main_frame.grid_rowconfigure(0, weight=1)
            self._main_frame.grid_columnconfigure(0, weight=1)
            
            # 创建设置界面
            self._settings_interface = SettingsInterface(
                self._main_frame,
                widget_id="settings",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            settings_widget = self._settings_interface.get_widget()
            if settings_widget:
                settings_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # 订阅设置相关事件
            self._subscribe_events()
            
            logger.info("设置视图初始化完成")
            
        except Exception as e:
            logger.error("设置视图初始化失败", exc_info=True)
            raise UIError(f"设置视图初始化失败: {e}")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 设置请求事件
        self._event_bus.subscribe("settings.request", self._on_settings_request)
    
    def _on_settings_request(self, event) -> None:
        """处理设置请求"""
        data = event.data
        category = data.get("category")
        
        logger.debug_struct("设置请求", category=category)
        
        # 根据分类切换到相应视图
        if category == "appearance":
            self._settings_interface.switch_category(SettingsCategory.APPEARANCE)
        elif category == "chat":
            self._settings_interface.switch_category(SettingsCategory.CHAT)
        elif category == "shortcuts":
            self._settings_interface.switch_category(SettingsCategory.SHORTCUTS)
        elif category == "developer":
            self._settings_interface.switch_category(SettingsCategory.DEVELOPER)
    
    def get_widget(self):
        """获取主框架"""
        return self._main_frame
    
    def get_settings_interface(self) -> SettingsInterface:
        """获取设置界面"""
        return self._settings_interface
    
    def get_status(self) -> Dict[str, Any]:
        """获取设置视图状态"""
        if self._settings_interface:
            return self._settings_interface.get_status()
        return {"initialized": False}


# 导出
__all__ = [
    "SettingsCategory",
    "SettingItem",
    "SettingCard",
    "SettingsInterface",
    "SettingsView"
]