"""
帮助与支持界面

提供用户帮助文档和系统信息，包括：
1. 用户手册和指南
2. 快捷键列表
3. 常见问题解答
4. 系统信息显示
5. 关于页面和版本信息
6. 反馈和支持链接
"""

import customtkinter as ctk
import logging
import webbrowser
import sys
import platform
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..config.models import AppConfig
from .manager import UIManager
from .widgets import BaseWidget, Panel, ScrollPanel, Card, Button, Label, Switch, TextArea
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class HelpViewType(str, Enum):
    """帮助视图类型枚举"""
    GETTING_STARTED = "getting_started"  # 入门指南
    USER_GUIDE = "user_guide"            # 用户指南
    SHORTCUTS = "shortcuts"              # 快捷键
    FAQ = "faq"                          # 常见问题
    SYSTEM_INFO = "system_info"          # 系统信息
    ABOUT = "about"                      # 关于页面


class HelpSection:
    """帮助章节"""
    
    def __init__(self, title: str, content: str, view_type: HelpViewType):
        self.title = title
        self.content = content
        self.view_type = view_type
        self.children: List['HelpSection'] = []
    
    def add_child(self, child: 'HelpSection') -> None:
        """添加子章节"""
        self.children.append(child)


class HelpCard(BaseWidget):
    """帮助卡片组件"""
    
    def __init__(
        self,
        parent,
        title: str,
        content: str,
        widget_id: Optional[str] = None,
        icon: Optional[str] = None,
        **kwargs
    ):
        """
        初始化帮助卡片
        
        Args:
            parent: 父组件
            title: 标题
            content: 内容
            widget_id: 组件ID
            icon: 图标（可选）
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None)
        self._title = title
        self._content = content
        self._icon = icon
        self._kwargs = kwargs
        
        # UI组件
        self._card = None
        self._title_label = None
        self._content_label = None
        
        self.initialize()
        
        logger.debug_struct("帮助卡片初始化", title=title)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建帮助卡片组件"""
        # 创建卡片
        self._card = Card(self._parent, style={
            "fg_color": ("white", "gray20"),
            "border_color": ("gray80", "gray40"),
            "border_width": 1,
            "corner_radius": 10
        })
        card_widget = self._card.get_widget()
        
        # 配置卡片网格
        card_widget.grid_columnconfigure(0, weight=1)
        
        # 内容框架
        content_frame = ctk.CTkFrame(card_widget, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # 标题区域
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=0, pady=(0, 10))
        
        # 图标（如果有）
        if self._icon:
            icon_label = ctk.CTkLabel(
                title_frame,
                text=self._icon,
                font=("Segoe UI Emoji", 16),
                anchor="w"
            )
            icon_label.pack(side="left", padx=(0, 10))
        
        # 标题
        self._title_label = ctk.CTkLabel(
            title_frame,
            text=self._title,
            font=("Microsoft YaHei", 14, "bold"),
            anchor="w"
        )
        self._title_label.pack(side="left", fill="x", expand=True)
        
        # 内容
        self._content_label = ctk.CTkLabel(
            content_frame,
            text=self._content,
            font=("Microsoft YaHei", 11),
            anchor="w",
            justify="left",
            wraplength=400
        )
        self._content_label.pack(fill="x", padx=0, pady=0)
        
        # 注册组件
        self.register_widget("card", card_widget)
        self.register_widget("title_label", self._title_label)
        self.register_widget("content_label", self._content_label)
        
        return card_widget
    
    def update_content(self, title: Optional[str] = None, content: Optional[str] = None) -> None:
        """更新卡片内容"""
        if title is not None:
            self._title = title
            if self._title_label:
                self._title_label.configure(text=title)
        
        if content is not None:
            self._content = content
            if self._content_label:
                self._content_label.configure(text=content)


class HelpInterface(BaseWidget):
    """
    帮助与支持界面
    
    提供完整的帮助文档系统和用户支持功能
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
        初始化帮助界面
        
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
        self._view_type = HelpViewType.GETTING_STARTED
        self._help_sections: Dict[HelpViewType, List[HelpSection]] = {}
        
        # UI组件
        self._main_panel = None
        self._sidebar = None
        self._content_area = None
        
        # 初始化帮助内容
        self._initialize_help_content()
        
        # 初始化
        self.initialize()
        
        logger.debug_struct("帮助界面初始化", widget_id=self._widget_id)
    
    def _initialize_help_content(self) -> None:
        """初始化帮助内容"""
        logger.debug("初始化帮助内容")
        
        # 入门指南
        getting_started = [
            HelpSection(
                "欢迎使用小盘古 4.0",
                "小盘古 4.0 是一个现代化、插件化的AI助手系统。"
                "本指南将帮助您快速上手使用系统。",
                HelpViewType.GETTING_STARTED
            ),
            HelpSection(
                "首次使用步骤",
                "1. 配置您的API密钥和模型设置\n"
                "2. 安装需要的插件\n"
                "3. 开始对话或执行任务",
                HelpViewType.GETTING_STARTED
            ),
            HelpSection(
                "核心概念",
                "• 插件系统: 可插拔的功能模块\n"
                "• 事件总线: 组件间通信机制\n"
                "• 配置管理: 统一的配置系统\n"
                "• 主题切换: 支持深色/浅色主题",
                HelpViewType.GETTING_STARTED
            )
        ]
        self._help_sections[HelpViewType.GETTING_STARTED] = getting_started
        
        # 用户指南
        user_guide = [
            HelpSection(
                "聊天功能",
                "在聊天界面中，您可以与AI助手对话，支持：\n"
                "• 文本对话\n"
                "• 上下文记忆\n"
                "• 对话历史\n"
                "• 快捷指令",
                HelpViewType.USER_GUIDE
            ),
            HelpSection(
                "插件管理",
                "插件管理界面允许您：\n"
                "• 查看已安装插件\n"
                "• 启用/禁用插件\n"
                "• 配置插件参数\n"
                "• 安装新插件",
                HelpViewType.USER_GUIDE
            ),
            HelpSection(
                "配置管理",
                "配置管理界面提供：\n"
                "• 系统设置调整\n"
                "• 主题和外观设置\n"
                "• 插件配置管理\n"
                "• 配置导入/导出",
                HelpViewType.USER_GUIDE
            ),
            HelpSection(
                "系统监控",
                "监控界面显示：\n"
                "• 系统资源使用情况\n"
                "• 插件状态\n"
                "• 性能指标\n"
                "• 实时图表",
                HelpViewType.USER_GUIDE
            )
        ]
        self._help_sections[HelpViewType.USER_GUIDE] = user_guide
        
        # 快捷键
        shortcuts = [
            HelpSection(
                "通用快捷键",
                "Ctrl+N: 新建对话\n"
                "Ctrl+S: 保存配置\n"
                "Ctrl+Q: 退出应用\n"
                "Ctrl+T: 切换主题\n"
                "F1: 显示帮助",
                HelpViewType.SHORTCUTS
            ),
            HelpSection(
                "编辑快捷键",
                "Ctrl+C: 复制\n"
                "Ctrl+V: 粘贴\n"
                "Ctrl+X: 剪切\n"
                "Ctrl+Z: 撤销\n"
                "Ctrl+Y: 重做",
                HelpViewType.SHORTCUTS
            ),
            HelpSection(
                "导航快捷键",
                "Ctrl+1: 切换到聊天视图\n"
                "Ctrl+2: 切换到插件视图\n"
                "Ctrl+3: 切换到配置视图\n"
                "Ctrl+4: 切换到监控视图\n"
                "Ctrl+5: 切换到帮助视图",
                HelpViewType.SHORTCUTS
            )
        ]
        self._help_sections[HelpViewType.SHORTCUTS] = shortcuts
        
        # 常见问题
        faq = [
            HelpSection(
                "如何安装插件？",
                "1. 打开插件管理界面\n"
                "2. 点击'安装插件'按钮\n"
                "3. 选择插件文件或输入插件URL\n"
                "4. 点击安装并重启应用",
                HelpViewType.FAQ
            ),
            HelpSection(
                "如何配置API密钥？",
                "1. 打开配置管理界面\n"
                "2. 导航到AI配置部分\n"
                "3. 输入您的API密钥\n"
                "4. 保存配置并重启应用",
                HelpViewType.FAQ
            ),
            HelpSection(
                "如何切换主题？",
                "1. 点击状态栏的主题切换按钮\n"
                "2. 或在配置管理界面的UI设置中更改主题",
                HelpViewType.FAQ
            ),
            HelpSection(
                "如何导出对话记录？",
                "功能正在开发中，将在后续版本中提供。",
                HelpViewType.FAQ
            )
        ]
        self._help_sections[HelpViewType.FAQ] = faq
        
        logger.debug_struct("帮助内容初始化完成", section_count=len(self._help_sections))
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建帮助界面组件"""
        # 创建主面板
        self._main_panel = Panel(self._parent)
        main_widget = self._main_panel.get_widget()
        
        # 配置网格布局
        main_widget.grid_rowconfigure(0, weight=1)
        main_widget.grid_columnconfigure(1, weight=1)  # 内容区域
        
        # 1. 创建侧边栏
        self._create_sidebar(main_widget)
        
        # 2. 创建内容区域
        self._create_content_area(main_widget)
        
        # 3. 加载默认视图
        self._load_view(self._view_type)
        
        # 注册主面板
        self.register_widget("main_panel", main_widget)
        
        return main_widget
    
    def _create_sidebar(self, parent) -> None:
        """创建侧边栏"""
        logger.debug("创建帮助侧边栏")
        
        # 侧边栏框架
        sidebar_style = {
            "fg_color": ("gray95", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray80", "gray30"),
            "width": 220
        }
        
        self._sidebar = Panel(parent, style=sidebar_style)
        sidebar_widget = self._sidebar.get_widget()
        sidebar_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar_widget.grid_propagate(False)
        
        # 配置网格
        sidebar_widget.grid_rowconfigure(1, weight=1)  # 导航区域
        
        # 侧边栏标题
        title_frame = ctk.CTkFrame(sidebar_widget, fg_color="transparent", height=60)
        title_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        title_frame.grid_propagate(False)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="帮助主题",
            font=("Microsoft YaHei", 14, "bold"),
            anchor="center"
        )
        title_label.pack(expand=True, fill="both", padx=20, pady=10)
        
        # 导航框架
        nav_frame = ctk.CTkScrollableFrame(sidebar_widget, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 创建导航按钮
        self._nav_buttons: Dict[HelpViewType, ctk.CTkButton] = {}
        
        nav_items = [
            (HelpViewType.GETTING_STARTED, "🚀 入门指南", "快速上手使用系统"),
            (HelpViewType.USER_GUIDE, "📚 用户指南", "详细功能说明"),
            (HelpViewType.SHORTCUTS, "⌨️ 快捷键", "键盘快捷键列表"),
            (HelpViewType.FAQ, "❓ 常见问题", "常见问题解答"),
            (HelpViewType.SYSTEM_INFO, "💻 系统信息", "查看系统状态"),
            (HelpViewType.ABOUT, "ℹ️ 关于", "版本信息和许可")
        ]
        
        for view_type, title, description in nav_items:
            self._create_nav_button(nav_frame, view_type, title, description)
        
        # 注册组件
        self.register_widget("sidebar", sidebar_widget)
        self.register_widget("nav_frame", nav_frame)
    
    def _create_nav_button(
        self, 
        parent, 
        view_type: HelpViewType, 
        title: str, 
        description: str
    ) -> None:
        """创建导航按钮"""
        # 按钮框架
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        button_frame.pack(fill="x", padx=5, pady=2)
        
        # 按钮
        button = ctk.CTkButton(
            button_frame,
            text=title,
            anchor="w",
            height=50,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda vt=view_type: self._on_nav_button_click(vt)
        )
        button.pack(fill="x", padx=5, pady=5)
        
        # 存储按钮引用
        self._nav_buttons[view_type] = button
        
        # 注册组件
        self.register_widget(f"nav_btn_{view_type.value}", button)
    
    def _on_nav_button_click(self, view_type: HelpViewType) -> None:
        """处理导航按钮点击"""
        logger.debug_struct("帮助导航按钮点击", view_type=view_type.value)
        
        # 切换视图
        self.switch_view(view_type)
        
        # 更新按钮状态
        self._update_nav_button_states(view_type)
    
    def _update_nav_button_states(self, selected_type: HelpViewType) -> None:
        """更新导航按钮状态"""
        for view_type, button in self._nav_buttons.items():
            if view_type == selected_type:
                # 选中状态
                button.configure(fg_color=("gray75", "gray25"))
            else:
                # 默认状态
                button.configure(fg_color="transparent")
    
    def _create_content_area(self, parent) -> None:
        """创建内容区域"""
        logger.debug("创建帮助内容区域")
        
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
    
    def _load_view(self, view_type: HelpViewType) -> None:
        """加载视图"""
        logger.debug_struct("加载帮助视图", view_type=view_type.value)
        
        # 清空内容区域
        content_frame = self._content_area.get_content_frame()
        if not content_frame:
            return
        
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        # 根据视图类型加载内容
        if view_type == HelpViewType.SYSTEM_INFO:
            self._load_system_info_view(content_frame)
        elif view_type == HelpViewType.ABOUT:
            self._load_about_view(content_frame)
        else:
            self._load_help_content_view(content_frame, view_type)
    
    def _load_help_content_view(self, parent, view_type: HelpViewType) -> None:
        """加载帮助内容视图"""
        # 视图标题
        title_texts = {
            HelpViewType.GETTING_STARTED: "🚀 入门指南",
            HelpViewType.USER_GUIDE: "📚 用户指南",
            HelpViewType.SHORTCUTS: "⌨️ 快捷键",
            HelpViewType.FAQ: "❓ 常见问题"
        }
        
        title = title_texts.get(view_type, "帮助")
        
        title_label = ctk.CTkLabel(
            parent,
            text=title,
            font=("Microsoft YaHei", 20, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))
        
        # 加载帮助内容
        sections = self._help_sections.get(view_type, [])
        
        for i, section in enumerate(sections, 1):
            # 创建帮助卡片
            help_card = HelpCard(
                parent,
                title=section.title,
                content=section.content,
                widget_id=f"help_card_{view_type.value}_{i}",
                icon="•"
            )
            
            card_widget = help_card.get_widget()
            if card_widget:
                card_widget.grid(row=i, column=0, sticky="nsew", padx=30, pady=(0, 15))
        
        # 添加底部空白
        bottom_spacer = ctk.CTkFrame(parent, fg_color="transparent", height=20)
        bottom_spacer.grid(row=len(sections) + 1, column=0, sticky="nsew")
    
    def _load_system_info_view(self, parent) -> None:
        """加载系统信息视图"""
        # 标题
        title_label = ctk.CTkLabel(
            parent,
            text="💻 系统信息",
            font=("Microsoft YaHei", 20, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))
        
        # 收集系统信息
        system_info = self._collect_system_info()
        
        # 显示系统信息卡片
        info_card = Card(parent, style={
            "fg_color": ("white", "gray20"),
            "border_color": ("gray80", "gray40"),
            "border_width": 1,
            "corner_radius": 10
        })
        card_widget = info_card.get_widget()
        card_widget.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 15))
        
        # 信息内容框架
        info_frame = ctk.CTkFrame(card_widget, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 显示系统信息
        row = 0
        for category, info_dict in system_info.items():
            # 类别标题
            category_label = ctk.CTkLabel(
                info_frame,
                text=category,
                font=("Microsoft YaHei", 12, "bold"),
                anchor="w"
            )
            category_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 5))
            row += 1
            
            # 信息项
            for key, value in info_dict.items():
                key_label = ctk.CTkLabel(
                    info_frame,
                    text=f"{key}:",
                    font=("Microsoft YaHei", 10),
                    anchor="w",
                    text_color=("gray50", "gray60")
                )
                key_label.grid(row=row, column=0, sticky="w", padx=(20, 10), pady=2)
                
                value_label = ctk.CTkLabel(
                    info_frame,
                    text=str(value),
                    font=("Microsoft YaHei", 10),
                    anchor="w"
                )
                value_label.grid(row=row, column=1, sticky="w", pady=2)
                row += 1
        
        # 操作按钮
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="w", padx=30, pady=20)
        
        # 复制系统信息按钮
        copy_button = ctk.CTkButton(
            button_frame,
            text="复制系统信息",
            width=120,
            command=lambda: self._copy_system_info_to_clipboard(system_info)
        )
        copy_button.pack(side="left", padx=(0, 10))
        
        # 刷新按钮
        refresh_button = ctk.CTkButton(
            button_frame,
            text="刷新",
            width=80,
            command=lambda: self._refresh_system_info(parent)
        )
        refresh_button.pack(side="left")
    
    def _collect_system_info(self) -> Dict[str, Dict[str, str]]:
        """收集系统信息"""
        import os
        import psutil
        
        info = {}
        
        # 应用信息
        app_info = {}
        if self._config_manager:
            app_config = self._config_manager.config.app
            app_info["应用名称"] = app_config.name
            app_info["版本"] = app_config.version
            app_info["环境"] = self._config_manager.config.environment
        
        info["应用信息"] = app_info
        
        # Python信息
        python_info = {
            "Python版本": platform.python_version(),
            "Python实现": platform.python_implementation(),
            "Python路径": sys.executable
        }
        info["Python环境"] = python_info
        
        # 系统信息
        system_info = {
            "操作系统": platform.system(),
            "系统版本": platform.version(),
            "系统架构": platform.machine(),
            "处理器": platform.processor()
        }
        info["操作系统"] = system_info
        
        # 资源信息
        resource_info = {}
        try:
            if psutil:
                # CPU信息
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count()
                resource_info["CPU使用率"] = f"{cpu_percent:.1f}%"
                resource_info["CPU核心数"] = cpu_count
                
                # 内存信息
                memory = psutil.virtual_memory()
                memory_used_gb = memory.used / (1024**3)
                memory_total_gb = memory.total / (1024**3)
                resource_info["内存使用"] = f"{memory_used_gb:.1f} GB / {memory_total_gb:.1f} GB"
                resource_info["内存使用率"] = f"{memory.percent:.1f}%"
        except Exception as e:
            logger.warning(f"获取资源信息失败: {e}")
            resource_info["状态"] = "资源监控不可用"
        
        info["系统资源"] = resource_info
        
        # 路径信息
        path_info = {
            "工作目录": os.getcwd(),
            "Python路径": ";".join(sys.path[:3]) + "..."
        }
        info["路径信息"] = path_info
        
        return info
    
    def _copy_system_info_to_clipboard(self, system_info: Dict[str, Dict[str, str]]) -> None:
        """复制系统信息到剪贴板"""
        try:
            import tkinter as tk
            
            # 构建文本
            lines = []
            for category, info_dict in system_info.items():
                lines.append(f"=== {category} ===")
                for key, value in info_dict.items():
                    lines.append(f"{key}: {value}")
                lines.append("")
            
            text = "\n".join(lines)
            
            # 复制到剪贴板
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            
            logger.info("系统信息已复制到剪贴板")
            
        except Exception as e:
            logger.error(f"复制系统信息失败: {e}")
    
    def _refresh_system_info(self, parent) -> None:
        """刷新系统信息视图"""
        logger.debug("刷新系统信息视图")
        self._load_system_info_view(parent)
    
    def _load_about_view(self, parent) -> None:
        """加载关于页面视图"""
        # 标题
        title_label = ctk.CTkLabel(
            parent,
            text="ℹ️ 关于小盘古",
            font=("Microsoft YaHei", 20, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=30, pady=(30, 20))
        
        # 关于卡片
        about_card = Card(parent, style={
            "fg_color": ("white", "gray20"),
            "border_color": ("gray80", "gray40"),
            "border_width": 1,
            "corner_radius": 10
        })
        card_widget = about_card.get_widget()
        card_widget.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 15))
        
        # 关于内容框架
        about_frame = ctk.CTkFrame(card_widget, fg_color="transparent")
        about_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        
        # 应用名称和版本
        app_name = "小盘古 AI 助手系统"
        app_version = "4.0.0"
        
        if self._config_manager:
            app_config = self._config_manager.config.app
            app_name = app_config.name
            app_version = app_config.version
        
        name_label = ctk.CTkLabel(
            about_frame,
            text=app_name,
            font=("Microsoft YaHei", 24, "bold"),
            anchor="center"
        )
        name_label.pack(pady=(0, 5))
        
        version_label = ctk.CTkLabel(
            about_frame,
            text=f"版本 {app_version}",
            font=("Microsoft YaHei", 14),
            text_color=("gray50", "gray60"),
            anchor="center"
        )
        version_label.pack(pady=(0, 20))
        
        # 描述
        description_text = (
            "小盘古是一个现代化、插件化的AI助手系统，"
            "旨在提供灵活、可扩展的人工智能助手平台。"
            "\n\n"
            "核心特性：\n"
            "• 模块化插件架构\n"
            "• 现代化UI界面\n"
            "• 多主题支持\n"
            "• 国际化支持\n"
            "• 实时系统监控"
        )
        
        description_label = ctk.CTkLabel(
            about_frame,
            text=description_text,
            font=("Microsoft YaHei", 11),
            anchor="w",
            justify="left",
            wraplength=500
        )
        description_label.pack(fill="x", pady=(0, 20))
        
        # 链接和按钮
        link_frame = ctk.CTkFrame(about_frame, fg_color="transparent")
        link_frame.pack(fill="x", pady=(0, 10))
        
        # 项目链接
        project_button = ctk.CTkButton(
            link_frame,
            text="🌐 项目主页",
            width=120,
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            command=lambda: webbrowser.open("https://github.com/smallpangu")
        )
        project_button.pack(side="left", padx=(0, 10))
        
        # 文档链接
        docs_button = ctk.CTkButton(
            link_frame,
            text="📖 在线文档",
            width=120,
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            command=lambda: webbrowser.open("https://smallpangu.github.io/docs")
        )
        docs_button.pack(side="left", padx=(0, 10))
        
        # 反馈链接
        feedback_button = ctk.CTkButton(
            link_frame,
            text="💬 反馈问题",
            width=120,
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            command=lambda: webbrowser.open("https://github.com/smallpangu/issues")
        )
        feedback_button.pack(side="left")
        
        # 许可证信息
        license_frame = ctk.CTkFrame(about_frame, fg_color="transparent")
        license_frame.pack(fill="x", pady=(20, 0))
        
        license_label = ctk.CTkLabel(
            license_frame,
            text="© 2023-2024 小盘古项目组 - MIT License",
            font=("Microsoft YaHei", 9),
            text_color=("gray50", "gray60"),
            anchor="center"
        )
        license_label.pack()
    
    def switch_view(self, view_type: HelpViewType) -> bool:
        """
        切换帮助视图
        
        Args:
            view_type: 视图类型
            
        Returns:
            是否成功切换
        """
        logger.debug_struct("切换帮助视图", view_type=view_type.value)
        
        try:
            self._view_type = view_type
            self._load_view(view_type)
            
            # 发布视图切换事件
            if self._event_bus:
                self._event_bus.publish("help.view.switched", {
                    "view_type": view_type.value,
                    "timestamp": time.time()
                })
            
            logger.debug_struct("帮助视图切换成功", view_type=view_type.value)
            return True
            
        except Exception as e:
            logger.error_struct("帮助视图切换失败", view_type=view_type.value, error=str(e))
            return False
    
    def get_current_view(self) -> HelpViewType:
        """获取当前视图类型"""
        return self._view_type
    
    def get_status(self) -> Dict[str, Any]:
        """获取帮助界面状态"""
        return {
            "widget_id": self._widget_id,
            "view_type": self._view_type.value,
            "help_section_count": sum(len(sections) for sections in self._help_sections.values())
        }


class HelpView:
    """
    帮助与支持视图
    
    集成帮助界面到主窗口视图框架中
    """
    
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化帮助视图
        
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
        self._help_interface = None
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("帮助视图初始化")
    
    def _initialize(self) -> None:
        """初始化帮助视图"""
        try:
            # 创建主框架
            self._main_frame = ctk.CTkFrame(self._parent)
            self._main_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            # 配置网格
            self._main_frame.grid_rowconfigure(0, weight=1)
            self._main_frame.grid_columnconfigure(0, weight=1)
            
            # 创建帮助界面
            self._help_interface = HelpInterface(
                self._main_frame,
                widget_id="help_system",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            help_widget = self._help_interface.get_widget()
            if help_widget:
                help_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # 订阅帮助相关事件
            self._subscribe_events()
            
            logger.info("帮助视图初始化完成")
            
        except Exception as e:
            logger.error("帮助视图初始化失败", exc_info=True)
            raise UIError(f"帮助视图初始化失败: {e}")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 帮助请求事件
        self._event_bus.subscribe("help.request", self._on_help_request)
    
    def _on_help_request(self, event) -> None:
        """处理帮助请求"""
        data = event.data
        topic = data.get("topic")
        
        logger.debug_struct("帮助请求", topic=topic)
        
        # 根据主题切换到相应视图
        if topic == "getting_started":
            self._help_interface.switch_view(HelpViewType.GETTING_STARTED)
        elif topic == "shortcuts":
            self._help_interface.switch_view(HelpViewType.SHORTCUTS)
        elif topic == "faq":
            self._help_interface.switch_view(HelpViewType.FAQ)
        elif topic == "system_info":
            self._help_interface.switch_view(HelpViewType.SYSTEM_INFO)
    
    def get_widget(self):
        """获取主框架"""
        return self._main_frame
    
    def get_help_interface(self) -> HelpInterface:
        """获取帮助界面"""
        return self._help_interface
    
    def get_status(self) -> Dict[str, Any]:
        """获取帮助视图状态"""
        if self._help_interface:
            return self._help_interface.get_status()
        return {"initialized": False}


# 导出
__all__ = [
    "HelpViewType",
    "HelpSection",
    "HelpCard",
    "HelpInterface",
    "HelpView"
]