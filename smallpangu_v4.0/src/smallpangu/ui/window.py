"""
主窗口模块

提供现代化、可扩展的主窗口和窗口基类，采用侧边导航布局。
支持主题切换、响应式布局、键盘快捷键。
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from .manager import UIManager
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class WindowState(str, Enum):
    """窗口状态枚举"""
    NORMAL = "normal"
    MAXIMIZED = "maximized"
    MINIMIZED = "minimized"
    FULLSCREEN = "fullscreen"


class NavigationItemType(str, Enum):
    """导航项类型枚举"""
    MENU = "menu"
    SEPARATOR = "separator"
    HEADER = "header"


@dataclass
class NavigationItem:
    """导航项数据类"""
    id: str
    label: str
    icon: Optional[str] = None
    item_type: NavigationItemType = NavigationItemType.MENU
    enabled: bool = True
    visible: bool = True
    order: int = 0
    children: List['NavigationItem'] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """数据验证"""
        if not self.id:
            raise ValueError("导航项ID不能为空")
        if self.item_type == NavigationItemType.MENU and not self.label:
            raise ValueError("菜单项标签不能为空")
    
    def add_child(self, child: 'NavigationItem') -> None:
        """添加子项"""
        self.children.append(child)
        # 按order排序
        self.children.sort(key=lambda x: x.order)


class BaseWindow:
    """
    窗口基类
    
    提供窗口基础功能：
    1. 生命周期管理
    2. 主题和语言响应
    3. 事件处理
    4. 基础布局框架
    """
    
    def __init__(
        self,
        root: ctk.CTk,
        ui_manager: UIManager,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化窗口基类
        
        Args:
            root: 根窗口
            ui_manager: UI管理器
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
        """
        self._root = root
        self._ui_manager = ui_manager
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._container = container
        self._ui_config = config_manager.config.ui
        
        # 窗口状态
        self._is_initialized = False
        self._is_showing = False
        self._window_state = WindowState.NORMAL
        
        # UI组件
        self._main_frame = None
        self._widgets: Dict[str, ctk.CTkBaseClass] = {}
        
        # 事件监听器ID
        self._event_listeners: List[str] = []
        
        logger.debug_struct("窗口基类初始化", window_type=self.__class__.__name__)
    
    def initialize(self) -> None:
        """初始化窗口"""
        if self._is_initialized:
            logger.warning("窗口已初始化，跳过重复初始化")
            return
        
        logger.debug("初始化窗口")
        
        try:
            # 1. 创建主框架
            self._create_main_frame()
            
            # 2. 构建窗口布局
            self._build_layout()
            
            # 3. 订阅事件
            self._subscribe_events()
            
            # 4. 应用当前主题和语言
            self._apply_theme()
            self._apply_language()
            
            self._is_initialized = True
            logger.debug("窗口初始化完成")
            
        except Exception as e:
            logger.error("窗口初始化失败", exc_info=True)
            raise UIError(f"窗口初始化失败: {e}")
    
    def _create_main_frame(self) -> None:
        """创建主框架"""
        self._main_frame = ctk.CTkFrame(self._root)
        self._main_frame.pack(fill="both", expand=True)
    
    def _build_layout(self) -> None:
        """构建窗口布局（子类实现）"""
        raise NotImplementedError("子类必须实现_build_layout方法")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 主题切换事件
        listener_id = self._event_bus.subscribe("theme.changed", self._on_theme_changed)
        self._event_listeners.append(listener_id)
        
        # 语言切换事件
        listener_id = self._event_bus.subscribe("language.changed", self._on_language_changed)
        self._event_listeners.append(listener_id)
        
        # 窗口事件
        listener_id = self._event_bus.subscribe("window.*", self._on_window_event)
        self._event_listeners.append(listener_id)
        
        logger.debug_struct("窗口事件订阅", listener_count=len(self._event_listeners))
    
    def _unsubscribe_events(self) -> None:
        """取消订阅事件"""
        for listener_id in self._event_listeners:
            self._event_bus.unsubscribe(listener_id)
        self._event_listeners.clear()
        logger.debug("窗口事件取消订阅")
    
    def _apply_theme(self) -> None:
        """应用当前主题"""
        # 子类可以实现具体主题应用逻辑
        pass
    
    def _apply_language(self) -> None:
        """应用当前语言"""
        # 子类可以实现具体语言应用逻辑
        pass
    
    def _on_theme_changed(self, event) -> None:
        """处理主题切换事件"""
        logger.debug_struct("处理主题切换事件", data=event.data)
        self._apply_theme()
    
    def _on_language_changed(self, event) -> None:
        """处理语言切换事件"""
        logger.debug_struct("处理语言切换事件", data=event.data)
        self._apply_language()
    
    def _on_window_event(self, event) -> None:
        """处理窗口事件"""
        logger.debug_struct("处理窗口事件", event_type=event.type, data=event.data)
    
    def show(self) -> None:
        """显示窗口"""
        if not self._is_initialized:
            self.initialize()
        
        if not self._is_showing:
            self._root.deiconify()
            self._root.lift()
            self._is_showing = True
            logger.debug("窗口显示")
    
    def hide(self) -> None:
        """隐藏窗口"""
        if self._is_showing:
            self._root.withdraw()
            self._is_showing = False
            logger.debug("窗口隐藏")
    
    def destroy(self) -> None:
        """销毁窗口"""
        logger.debug("销毁窗口")
        
        try:
            # 取消订阅事件
            self._unsubscribe_events()
            
            # 销毁组件
            if self._main_frame:
                self._main_frame.destroy()
            
            self._widgets.clear()
            self._is_initialized = False
            self._is_showing = False
            
            logger.debug("窗口销毁完成")
            
        except Exception as e:
            logger.error("窗口销毁失败", exc_info=True)
            raise UIError(f"窗口销毁失败: {e}")
    
    def register_widget(self, widget_id: str, widget: ctk.CTkBaseClass) -> None:
        """
        注册窗口组件
        
        Args:
            widget_id: 组件ID
            widget: 组件实例
        """
        if widget_id in self._widgets:
            logger.warning_struct("窗口组件重复注册", widget_id=widget_id)
            return
        
        self._widgets[widget_id] = widget
        logger.debug_struct("窗口组件注册", widget_id=widget_id)
    
    def get_widget(self, widget_id: str) -> Optional[ctk.CTkBaseClass]:
        """
        获取窗口组件
        
        Args:
            widget_id: 组件ID
            
        Returns:
            组件实例，如果未找到则返回None
        """
        return self._widgets.get(widget_id)
    
    def set_window_state(self, state: WindowState) -> bool:
        """
        设置窗口状态
        
        Args:
            state: 窗口状态
            
        Returns:
            是否成功设置
        """
        try:
            if state == WindowState.NORMAL:
                self._root.state("normal")
            elif state == WindowState.MAXIMIZED:
                self._root.state("zoomed")
            elif state == WindowState.MINIMIZED:
                self._root.state("iconic")
            elif state == WindowState.FULLSCREEN:
                self._root.attributes("-fullscreen", True)
            
            self._window_state = state
            logger.debug_struct("窗口状态设置", state=state)
            return True
            
        except Exception as e:
            logger.error_struct("窗口状态设置失败", state=state, error=str(e))
            return False
    
    def get_window_state(self) -> WindowState:
        """获取当前窗口状态"""
        return self._window_state
    
    def toggle_fullscreen(self) -> None:
        """切换全屏模式"""
        if self._window_state == WindowState.FULLSCREEN:
            self.set_window_state(WindowState.NORMAL)
        else:
            self.set_window_state(WindowState.FULLSCREEN)
    
    def update_title(self, title: str) -> None:
        """更新窗口标题"""
        self._root.title(title)
        logger.debug_struct("窗口标题更新", title=title)
    
    # 属性访问
    @property
    def root(self):
        """获取根窗口"""
        return self._root
    
    @property
    def main_frame(self):
        """获取主框架"""
        return self._main_frame
    
    @property
    def is_initialized(self) -> bool:
        """窗口是否已初始化"""
        return self._is_initialized
    
    @property
    def is_showing(self) -> bool:
        """窗口是否正在显示"""
        return self._is_showing
    
    @property
    def widget_count(self) -> int:
        """注册的窗口组件数量"""
        return len(self._widgets)
    
    def get_status(self) -> Dict[str, Any]:
        """获取窗口状态"""
        return {
            "initialized": self._is_initialized,
            "showing": self._is_showing,
            "window_state": self._window_state,
            "widget_count": self.widget_count,
            "window_size": f"{self._ui_config.window_width}x{self._ui_config.window_height}"
        }


class MainWindow(BaseWindow):
    """
    主窗口
    
    现代化主窗口布局：
    1. 侧边导航栏（左侧）
    2. 主工作区（右侧）
    3. 状态栏（底部）
    4. 标题栏（顶部）
    """
    
    def __init__(
        self,
        root: ctk.CTk,
        ui_manager: UIManager,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """初始化主窗口"""
        super().__init__(root, ui_manager, config_manager, event_bus, container)
        
        # 主窗口特定状态
        self._current_view = "chat"  # 默认视图：聊天
        self._navigation_items: List[NavigationItem] = []
        
        # 布局组件
        self._sidebar_frame = None
        self._content_frame = None
        self._status_bar = None
        self._title_bar = None
        
        # 视图缓存
        self._view_cache: Dict[str, ctk.CTkBaseClass] = {}
        
        # 视图引用
        self._chat_view = None
        self._plugins_view = None
        self._config_view = None
        self._admin_view = None
        self._monitor_view = None
        self._help_view = None
        
        logger.debug_struct("主窗口初始化")
    
    def _create_main_frame(self) -> None:
        """创建主框架（覆盖基类方法）"""
        super()._create_main_frame()
        
        # 设置网格布局权重
        self._main_frame.grid_rowconfigure(1, weight=1)
        self._main_frame.grid_columnconfigure(1, weight=1)
    
    def _build_layout(self) -> None:
        """构建主窗口布局"""
        logger.debug("构建主窗口布局")
        
        try:
            # 0. 设置窗口标题
            app_name = self._config_manager.config.app.name
            app_version = self._config_manager.config.app.version
            self.update_title(f"{app_name} v{app_version}")
            
            # 1. 创建标题栏（第0行）
            self._create_title_bar()
            
            # 2. 创建侧边栏（第1行，第0列）
            self._create_sidebar()
            
            # 3. 创建内容区域（第1行，第1列）
            self._create_content_area()
            
            # 4. 创建状态栏（第2行）
            self._create_status_bar()
            
            # 5. 加载默认视图
            self._load_default_view()
            
            logger.debug("主窗口布局构建完成")
            
        except Exception as e:
            logger.error("主窗口布局构建失败", exc_info=True)
            raise UIError(f"主窗口布局构建失败: {e}")
    
    def _create_title_bar(self) -> None:
        """创建标题栏"""
        logger.debug("创建标题栏")
        
        # 标题栏框架
        self._title_bar = ctk.CTkFrame(
            self._main_frame,
            height=40,
            corner_radius=0
        )
        self._title_bar.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
        self._title_bar.grid_propagate(False)
        
        # 标题栏网格配置
        self._title_bar.grid_columnconfigure(0, weight=1)  # 标题区域
        self._title_bar.grid_columnconfigure(1, weight=0)  # 控制按钮区域
        
        # 应用标题
        app_name = self._config_manager.config.app.name
        title_label = ctk.CTkLabel(
            self._title_bar,
            text=app_name,
            font=("Segoe UI", 14, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=0)
        
        # 窗口控制按钮（最小化、最大化/还原、关闭）
        button_frame = ctk.CTkFrame(self._title_bar, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="e", padx=5, pady=0)
        
        # 最小化按钮
        minimize_btn = ctk.CTkButton(
            button_frame,
            text="─",
            width=30,
            height=30,
            command=lambda: self.set_window_state(WindowState.MINIMIZED)
        )
        minimize_btn.grid(row=0, column=0, padx=2, pady=0)
        
        # 最大化/还原按钮
        def toggle_maximize():
            if self._window_state == WindowState.MAXIMIZED:
                self.set_window_state(WindowState.NORMAL)
            else:
                self.set_window_state(WindowState.MAXIMIZED)
        
        maximize_btn = ctk.CTkButton(
            button_frame,
            text="□",
            width=30,
            height=30,
            command=toggle_maximize
        )
        maximize_btn.grid(row=0, column=1, padx=2, pady=0)
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            button_frame,
            text="×",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#D32F2F",
            text_color=("gray10", "gray90"),
            command=self._root.destroy
        )
        close_btn.grid(row=0, column=2, padx=2, pady=0)
        
        # 注册组件
        self.register_widget("title_bar", self._title_bar)
        self.register_widget("title_label", title_label)
        self.register_widget("minimize_btn", minimize_btn)
        self.register_widget("maximize_btn", maximize_btn)
        self.register_widget("close_btn", close_btn)
        
        logger.debug("标题栏创建完成")
    
    def _create_sidebar(self) -> None:
        """创建侧边栏"""
        logger.debug("创建侧边栏")
        
        # 侧边栏框架
        sidebar_width = 240
        self._sidebar_frame = ctk.CTkFrame(
            self._main_frame,
            width=sidebar_width,
            corner_radius=0
        )
        self._sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._sidebar_frame.grid_propagate(False)
        self._sidebar_frame.grid_rowconfigure(1, weight=1)  # 导航区域
        
        # 侧边栏网格配置
        self._sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # Logo区域（顶部）
        logo_frame = ctk.CTkFrame(self._sidebar_frame, fg_color="transparent", height=80)
        logo_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        logo_frame.grid_propagate(False)
        
        # Logo文本（暂时用文本代替图标）
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="小盘古",
            font=("Microsoft YaHei", 20, "bold"),
            anchor="center"
        )
        logo_label.pack(expand=True, fill="both", padx=20, pady=10)
        
        # 导航区域（中间）
        nav_frame = ctk.CTkScrollableFrame(self._sidebar_frame, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 初始化导航项
        self._initialize_navigation_items()
        
        # 创建导航按钮
        self._nav_buttons: Dict[str, ctk.CTkButton] = {}
        for nav_item in self._navigation_items:
            if nav_item.visible:
                self._create_nav_button(nav_frame, nav_item)
        
        # 设置区域（底部）
        settings_frame = ctk.CTkFrame(self._sidebar_frame, fg_color="transparent", height=60)
        settings_frame.grid(row=2, column=0, sticky="sew", padx=0, pady=0)
        settings_frame.grid_propagate(False)
        
        # 设置按钮
        settings_btn = ctk.CTkButton(
            settings_frame,
            text="设置",
            width=40,
            height=40,
            corner_radius=20,
            command=lambda: self.switch_view("settings")
        )
        settings_btn.place(relx=0.5, rely=0.5, anchor="center")
        
        # 注册组件
        self.register_widget("sidebar_frame", self._sidebar_frame)
        self.register_widget("logo_frame", logo_frame)
        self.register_widget("logo_label", logo_label)
        self.register_widget("nav_frame", nav_frame)
        self.register_widget("settings_frame", settings_frame)
        self.register_widget("settings_btn", settings_btn)
        
        logger.debug("侧边栏创建完成")
    
    def _initialize_navigation_items(self) -> None:
        """初始化导航项"""
        logger.debug("初始化导航项")
        
        # 默认导航项
        self._navigation_items = [
            NavigationItem(
                id="chat",
                label="聊天",
                icon="💬",
                order=100,
                data={"view": "chat"}
            ),
            NavigationItem(
                id="plugins",
                label="插件",
                icon="🔌",
                order=200,
                data={"view": "plugins"}
            ),
            NavigationItem(
                id="config",
                label="配置",
                icon="⚙️",
                order=300,
                data={"view": "config"}
            ),
            NavigationItem(
                id="admin",
                label="管理",
                icon="🚀",
                order=350,
                data={"view": "admin"}
            ),
            NavigationItem(
                id="monitor",
                label="监控",
                icon="📊",
                order=400,
                data={"view": "monitor"}
            ),
            NavigationItem(
                id="help",
                label="帮助",
                icon="❓",
                order=500,
                data={"view": "help"}
            )
        ]
        
        logger.debug_struct("导航项初始化完成", item_count=len(self._navigation_items))
    
    def _create_nav_button(self, parent, nav_item: NavigationItem) -> None:
        """
        创建导航按钮
        
        Args:
            parent: 父组件
            nav_item: 导航项
        """
        if nav_item.item_type != NavigationItemType.MENU:
            return
        
        # 按钮文本
        button_text = f"  {nav_item.label}"
        if nav_item.icon:
            button_text = f"{nav_item.icon}{button_text}"
        
        # 创建按钮
        button = ctk.CTkButton(
            parent,
            text=button_text,
            anchor="w",
            height=40,
            corner_radius=10,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda item=nav_item: self._on_nav_button_click(item)
        )
        button.pack(fill="x", padx=10, pady=2)
        
        # 存储按钮引用
        self._nav_buttons[nav_item.id] = button
        
        # 注册组件
        self.register_widget(f"nav_btn_{nav_item.id}", button)
    
    def _on_nav_button_click(self, nav_item: NavigationItem) -> None:
        """
        处理导航按钮点击
        
        Args:
            nav_item: 导航项
        """
        logger.debug_struct("导航按钮点击", nav_id=nav_item.id)
        
        # 切换视图
        view = nav_item.data.get("view", nav_item.id)
        self.switch_view(view)
        
        # 更新按钮状态（高亮当前选中项）
        self._update_nav_button_states(nav_item.id)
    
    def _update_nav_button_states(self, selected_id: str) -> None:
        """
        更新导航按钮状态
        
        Args:
            selected_id: 选中的导航项ID
        """
        for nav_id, button in self._nav_buttons.items():
            if nav_id == selected_id:
                # 选中状态
                button.configure(fg_color=("gray75", "gray25"))
            else:
                # 默认状态
                button.configure(fg_color="transparent")
    
    def _create_content_area(self) -> None:
        """创建内容区域"""
        logger.debug("创建内容区域")
        
        # 内容区域框架
        self._content_frame = ctk.CTkFrame(self._main_frame)
        self._content_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        
        # 内容区域网格配置
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)
        
        # 创建视图容器
        self._view_container = ctk.CTkFrame(self._content_frame)
        self._view_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # 视图容器网格配置
        self._view_container.grid_rowconfigure(0, weight=1)
        self._view_container.grid_columnconfigure(0, weight=1)
        
        # 注册组件
        self.register_widget("content_frame", self._content_frame)
        self.register_widget("view_container", self._view_container)
        
        logger.debug("内容区域创建完成")
    
    def _create_status_bar(self) -> None:
        """创建状态栏"""
        logger.debug("创建状态栏")
        
        # 状态栏框架
        self._status_bar = ctk.CTkFrame(
            self._main_frame,
            height=30,
            corner_radius=0
        )
        self._status_bar.grid(row=2, column=0, columnspan=2, sticky="sew", padx=0, pady=0)
        self._status_bar.grid_propagate(False)
        
        # 状态栏网格配置
        self._status_bar.grid_columnconfigure(0, weight=1)  # 状态信息区域
        self._status_bar.grid_columnconfigure(1, weight=0)  # 系统信息区域
        
        # 状态信息（左侧）
        status_label = ctk.CTkLabel(
            self._status_bar,
            text="就绪",
            anchor="w"
        )
        status_label.grid(row=0, column=0, sticky="w", padx=10, pady=0)
        
        # 系统信息（右侧）
        sys_info_frame = ctk.CTkFrame(self._status_bar, fg_color="transparent")
        sys_info_frame.grid(row=0, column=1, sticky="e", padx=10, pady=0)
        
        # 主题切换按钮
        def toggle_theme():
            theme_manager = self._ui_manager.theme_manager
            if theme_manager:
                theme_manager.cycle_theme()
        
        theme_btn = ctk.CTkButton(
            sys_info_frame,
            text="🌓",
            width=30,
            height=20,
            font=("Segoe UI", 12),
            command=toggle_theme
        )
        theme_btn.pack(side="left", padx=2)
        
        # 时间显示
        time_label = ctk.CTkLabel(
            sys_info_frame,
            text="00:00",
            width=50,
            anchor="center"
        )
        time_label.pack(side="left", padx=2)
        
        # 注册组件
        self.register_widget("status_bar", self._status_bar)
        self.register_widget("status_label", status_label)
        self.register_widget("theme_btn", theme_btn)
        self.register_widget("time_label", time_label)
        
        logger.debug("状态栏创建完成")
    
    def _load_default_view(self) -> None:
        """加载默认视图"""
        logger.debug("加载默认视图")
        
        # 加载聊天视图
        self.switch_view("chat")
        
        # 高亮聊天按钮
        self._update_nav_button_states("chat")
        
        logger.debug("默认视图加载完成")
    
    def switch_view(self, view_name: str) -> bool:
        """
        切换视图
        
        Args:
            view_name: 视图名称
            
        Returns:
            是否成功切换
        """
        logger.debug_struct("切换视图", view_name=view_name)
        
        try:
            # 清理当前视图
            self._clear_current_view()
            
            # 加载新视图
            view = self._load_view(view_name)
            if view:
                # 显示视图
                view.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
                self._current_view = view_name
                
                # 发布视图切换事件
                self._event_bus.publish("view.switched", {
                    "view_name": view_name,
                    "timestamp": "now"  # 这里应该使用实际时间戳
                })
                
                logger.debug_struct("视图切换成功", view_name=view_name)
                return True
            else:
                logger.warning_struct("视图加载失败", view_name=view_name)
                return False
                
        except Exception as e:
            logger.error_struct("视图切换失败", view_name=view_name, error=str(e))
            return False
    
    def _clear_current_view(self) -> None:
        """清理当前视图"""
        # 隐藏所有子组件
        for child in self._view_container.winfo_children():
            child.grid_forget()
    
    def _load_view(self, view_name: str) -> Optional[ctk.CTkBaseClass]:
        """
        加载视图
        
        Args:
            view_name: 视图名称
            
        Returns:
            视图组件，如果加载失败则返回None
        """
        # 检查缓存
        if view_name in self._view_cache:
            logger.debug_struct("从缓存加载视图", view_name=view_name)
            return self._view_cache[view_name]
        
        # 创建新视图
        view = self._create_view(view_name)
        if view:
            # 缓存视图
            self._view_cache[view_name] = view
            logger.debug_struct("视图创建并缓存", view_name=view_name)
        
        return view
    
    def _create_view(self, view_name: str) -> Optional[ctk.CTkBaseClass]:
        """
        创建视图
        
        Args:
            view_name: 视图名称
            
        Returns:
            视图组件，如果创建失败则返回None
        """
        try:
            logger.debug_struct("创建视图", view_name=view_name)
            
            if view_name == "chat":
                return self._create_chat_view()
            elif view_name == "plugins":
                return self._create_plugins_view()
            elif view_name == "config":
                return self._create_config_view()
            elif view_name == "monitor":
                return self._create_monitor_view()
            elif view_name == "help":
                return self._create_help_view()
            elif view_name == "settings":
                return self._create_settings_view()
            elif view_name == "admin":
                return self._create_admin_view()
            else:
                logger.warning_struct("未知视图", view_name=view_name)
                return None
                
        except Exception as e:
            logger.error_struct("视图创建失败", view_name=view_name, error=str(e))
            return None
    
    def _create_chat_view(self) -> ctk.CTkBaseClass:
        """创建聊天视图"""
        logger.debug("创建聊天视图")
        
        try:
            # 导入ChatView（延迟导入以避免循环依赖）
            from .chat_interface import ChatView
            
            # 创建聊天视图
            chat_view = ChatView(
                parent=self._view_container,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            # 获取主框架
            chat_frame = chat_view.get_widget()
            
            if not chat_frame:
                raise UIError("聊天视图框架创建失败")
            
            # 注册组件
            self.register_widget("chat_frame", chat_frame)
            self.register_widget("chat_view", chat_view)
            
            # 存储聊天视图引用，以便后续访问
            self._chat_view = chat_view
            
            logger.debug("聊天视图创建完成")
            return chat_frame
            
        except Exception as e:
            logger.error("聊天视图创建失败", exc_info=True)
            # 回退到简单视图
            return self._create_simple_chat_view()
    
    def _create_simple_chat_view(self) -> ctk.CTkBaseClass:
        """创建简单的聊天视图（回退方案）"""
        logger.debug("创建简单聊天视图")
        
        # 创建聊天视图框架
        chat_frame = ctk.CTkFrame(self._view_container)
        
        # 标题
        title_label = ctk.CTkLabel(
            chat_frame,
            text="聊天助手",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 提示文本
        hint_label = ctk.CTkLabel(
            chat_frame,
            text="聊天功能正在开发中...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        # 注册组件
        self.register_widget("chat_frame_simple", chat_frame)
        self.register_widget("chat_title_label_simple", title_label)
        self.register_widget("chat_hint_label_simple", hint_label)
        
        return chat_frame
    
    def _create_plugins_view(self) -> ctk.CTkBaseClass:
        """创建插件视图"""
        logger.debug("创建插件视图")
        
        try:
            # 导入PluginView（延迟导入以避免循环依赖）
            from .plugin_interface import PluginView
            
            # 创建插件视图
            plugins_view = PluginView(
                parent=self._view_container,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            # 获取主框架
            plugins_frame = plugins_view.get_widget()
            
            if not plugins_frame:
                raise UIError("插件视图框架创建失败")
            
            # 注册组件
            self.register_widget("plugins_frame", plugins_frame)
            self.register_widget("plugins_view", plugins_view)
            
            # 存储插件视图引用，以便后续访问
            self._plugins_view = plugins_view
            
            logger.debug("插件视图创建完成")
            return plugins_frame
            
        except Exception as e:
            logger.error("插件视图创建失败", exc_info=True)
            # 回退到简单视图
            return self._create_simple_plugins_view()
    
    def _create_simple_plugins_view(self) -> ctk.CTkBaseClass:
        """创建简单的插件视图（回退方案）"""
        logger.debug("创建简单插件视图")
        
        # 创建插件视图框架
        plugins_frame = ctk.CTkFrame(self._view_container)
        
        # 标题
        title_label = ctk.CTkLabel(
            plugins_frame,
            text="插件管理",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 提示文本
        hint_label = ctk.CTkLabel(
            plugins_frame,
            text="插件管理功能加载失败，正在使用简化视图...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        # 注册组件
        self.register_widget("plugins_frame_simple", plugins_frame)
        self.register_widget("plugins_title_label_simple", title_label)
        self.register_widget("plugins_hint_label_simple", hint_label)
        
        return plugins_frame
    
    def _create_config_view(self) -> ctk.CTkBaseClass:
        """创建配置视图"""
        logger.debug("创建配置视图")
        
        try:
            # 导入ConfigView（延迟导入以避免循环依赖）
            from .config_interface import ConfigView
            
            # 创建配置视图
            config_view = ConfigView(
                parent=self._view_container,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            # 获取主框架
            config_frame = config_view.get_widget()
            
            if not config_frame:
                raise UIError("配置视图框架创建失败")
            
            # 注册组件
            self.register_widget("config_frame", config_frame)
            self.register_widget("config_view", config_view)
            
            # 存储配置视图引用，以便后续访问
            self._config_view = config_view
            
            logger.debug("配置视图创建完成")
            return config_frame
            
        except Exception as e:
            logger.error("配置视图创建失败", exc_info=True)
            # 回退到简单视图
            return self._create_simple_config_view()
    
    def _create_simple_config_view(self) -> ctk.CTkBaseClass:
        """创建简单的配置视图（回退方案）"""
        logger.debug("创建简单配置视图")
        
        # 创建配置视图框架
        config_frame = ctk.CTkFrame(self._view_container)
        
        # 标题
        title_label = ctk.CTkLabel(
            config_frame,
            text="配置管理",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 提示文本
        hint_label = ctk.CTkLabel(
            config_frame,
            text="配置管理功能加载失败，正在使用简化视图...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        # 注册组件
        self.register_widget("config_frame_simple", config_frame)
        self.register_widget("config_title_label_simple", title_label)
        self.register_widget("config_hint_label_simple", hint_label)
        
        return config_frame
    
    def _create_monitor_view(self) -> ctk.CTkBaseClass:
        """创建监控视图"""
        logger.debug("创建监控视图")
        
        try:
            # 导入MonitorView（延迟导入以避免循环依赖）
            from .monitor_interface import MonitorView
            
            # 创建监控视图
            monitor_view = MonitorView(
                parent=self._view_container,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            # 获取主框架
            monitor_frame = monitor_view.get_widget()
            
            if not monitor_frame:
                raise UIError("监控视图框架创建失败")
            
            # 注册组件
            self.register_widget("monitor_frame", monitor_frame)
            self.register_widget("monitor_view", monitor_view)
            
            # 存储监控视图引用，以便后续访问
            self._monitor_view = monitor_view
            
            logger.debug("监控视图创建完成")
            return monitor_frame
            
        except Exception as e:
            logger.error("监控视图创建失败", exc_info=True)
            # 回退到简单视图
            return self._create_simple_monitor_view()
    
    def _create_simple_monitor_view(self) -> ctk.CTkBaseClass:
        """创建简单的监控视图（回退方案）"""
        logger.debug("创建简单监控视图")
        
        # 创建监控视图框架
        monitor_frame = ctk.CTkFrame(self._view_container)
        
        # 标题
        title_label = ctk.CTkLabel(
            monitor_frame,
            text="系统监控",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 提示文本
        hint_label = ctk.CTkLabel(
            monitor_frame,
            text="监控功能加载失败，正在使用简化视图...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        # 注册组件
        self.register_widget("monitor_frame_simple", monitor_frame)
        self.register_widget("monitor_title_label_simple", title_label)
        self.register_widget("monitor_hint_label_simple", hint_label)
        
        return monitor_frame
    
    def _create_help_view(self) -> ctk.CTkBaseClass:
        """创建帮助视图"""
        logger.debug("创建帮助视图")
        
        try:
            # 导入HelpView（延迟导入以避免循环依赖）
            from .help_interface import HelpView
            
            # 创建帮助视图
            help_view = HelpView(
                parent=self._view_container,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container
            )
            
            # 获取主框架
            help_frame = help_view.get_widget()
            
            if not help_frame:
                raise UIError("帮助视图框架创建失败")
            
            # 注册组件
            self.register_widget("help_frame", help_frame)
            self.register_widget("help_view", help_view)
            
            # 存储帮助视图引用，以便后续访问
            self._help_view = help_view
            
            logger.debug("帮助视图创建完成")
            return help_frame
            
        except Exception as e:
            logger.error("帮助视图创建失败", exc_info=True)
            # 回退到简单视图
            return self._create_simple_help_view()
    
    def _create_simple_help_view(self) -> ctk.CTkBaseClass:
        """创建简单的帮助视图（回退方案）"""
        logger.debug("创建简单帮助视图")
        
        help_frame = ctk.CTkFrame(self._view_container)
        
        title_label = ctk.CTkLabel(
            help_frame,
            text="帮助与支持",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        hint_label = ctk.CTkLabel(
            help_frame,
            text="帮助功能正在开发中...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        self.register_widget("help_frame_simple", help_frame)
        self.register_widget("help_title_label_simple", title_label)
        self.register_widget("help_hint_label_simple", hint_label)
        
        return help_frame
    
    def _create_settings_view(self) -> ctk.CTkBaseClass:
        """创建设置视图（临时实现）"""
        logger.debug("创建设置视图")
        
        settings_frame = ctk.CTkFrame(self._view_container)
        
        title_label = ctk.CTkLabel(
            settings_frame,
            text="设置",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        hint_label = ctk.CTkLabel(
            settings_frame,
            text="设置功能正在开发中...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        self.register_widget("settings_frame", settings_frame)
        self.register_widget("settings_title_label", title_label)
        self.register_widget("settings_hint_label", hint_label)
        
        return settings_frame
    
    def _create_admin_view(self) -> ctk.CTkBaseClass:
        """创建管理后台视图"""
        logger.debug("创建管理后台视图")
        
        try:
            # 导入AdminInterface（延迟导入以避免循环依赖）
            from .admin_interface import AdminInterface
            
            # 从容器获取所需服务
            module_registry = None
            config_form_service = None
            hot_reload_orchestrator = None
            admin_state_service = None
            
            if self._container:
                try:
                    module_registry = self._container.get("module_registry")
                except:
                    logger.warning("无法从容器获取module_registry服务")
                
                try:
                    config_form_service = self._container.get("config_form_service")
                except:
                    logger.warning("无法从容器获取config_form_service服务")
                
                try:
                    hot_reload_orchestrator = self._container.get("hot_reload_orchestrator")
                except:
                    logger.warning("无法从容器获取hot_reload_orchestrator服务")
                
                try:
                    admin_state_service = self._container.get("admin_state_service")
                except:
                    logger.warning("无法从容器获取admin_state_service服务")
            
            # 创建管理后台界面
            admin_view = AdminInterface(
                parent=self._view_container,
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container,
                module_registry=module_registry,
                config_form_service=config_form_service,
                hot_reload_orchestrator=hot_reload_orchestrator,
                admin_state_service=admin_state_service
            )
            
            # 获取主框架
            admin_frame = admin_view.get_widget()
            
            if not admin_frame:
                raise UIError("管理后台视图框架创建失败")
            
            # 注册组件
            self.register_widget("admin_frame", admin_frame)
            self.register_widget("admin_view", admin_view)
            
            # 存储管理视图引用，以便后续访问
            self._admin_view = admin_view
            
            logger.debug("管理后台视图创建完成")
            return admin_frame
            
        except Exception as e:
            logger.error("管理后台视图创建失败", exc_info=True)
            # 回退到简单视图
            return self._create_simple_admin_view()
    
    def _create_simple_admin_view(self) -> ctk.CTkBaseClass:
        """创建简单的管理后台视图（回退方案）"""
        logger.debug("创建简单管理后台视图")
        
        # 创建管理后台视图框架
        admin_frame = ctk.CTkFrame(self._view_container)
        
        # 标题
        title_label = ctk.CTkLabel(
            admin_frame,
            text="统一管理后台",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 提示文本
        hint_label = ctk.CTkLabel(
            admin_frame,
            text="管理后台功能正在开发中...",
            font=("Microsoft YaHei", 12)
        )
        hint_label.pack(pady=10)
        
        # 注册组件
        self.register_widget("admin_frame_simple", admin_frame)
        self.register_widget("admin_title_label_simple", title_label)
        self.register_widget("admin_hint_label_simple", hint_label)
        
        return admin_frame
    
    def _apply_theme(self) -> None:
        """应用当前主题（覆盖基类方法）"""
        super()._apply_theme()
        
        # 这里可以添加主窗口特定的主题应用逻辑
        logger.debug("主窗口主题应用")
    
    def _apply_language(self) -> None:
        """应用当前语言（覆盖基类方法）"""
        super()._apply_language()
        
        # 这里可以添加主窗口特定的语言应用逻辑
        logger.debug("主窗口语言应用")
    
    # 公共API
    def add_navigation_item(self, nav_item: NavigationItem) -> None:
        """
        添加导航项
        
        Args:
            nav_item: 导航项
        """
        self._navigation_items.append(nav_item)
        self._navigation_items.sort(key=lambda x: x.order)
        
        logger.debug_struct("导航项添加", nav_id=nav_item.id)
        
        # 如果UI已初始化，更新导航栏
        if self._is_initialized:
            self._refresh_navigation()
    
    def remove_navigation_item(self, nav_id: str) -> bool:
        """
        移除导航项
        
        Args:
            nav_id: 导航项ID
            
        Returns:
            是否成功移除
        """
        for i, item in enumerate(self._navigation_items):
            if item.id == nav_id:
                self._navigation_items.pop(i)
                logger.debug_struct("导航项移除", nav_id=nav_id)
                
                # 如果UI已初始化，更新导航栏
                if self._is_initialized:
                    self._refresh_navigation()
                
                return True
        
        logger.warning_struct("导航项未找到", nav_id=nav_id)
        return False
    
    def _refresh_navigation(self) -> None:
        """刷新导航栏"""
        logger.debug("刷新导航栏")
        
        # 这里可以实现导航栏的动态刷新逻辑
        # 目前需要重新创建侧边栏，更复杂的实现可以只更新变化的部分
        pass
    
    def update_status(self, message: str) -> None:
        """
        更新状态栏信息
        
        Args:
            message: 状态消息
        """
        status_label = self.get_widget("status_label")
        if status_label:
            status_label.configure(text=message)
            logger.debug_struct("状态栏更新", message=message)
    
    def get_current_view(self) -> str:
        """获取当前视图名称"""
        return self._current_view
    
    def clear_view_cache(self) -> None:
        """清空视图缓存"""
        self._view_cache.clear()
        logger.debug("视图缓存已清空")
    
    # 属性访问
    @property
    def sidebar_frame(self):
        """获取侧边栏框架"""
        return self._sidebar_frame
    
    @property
    def content_frame(self):
        """获取内容区域框架"""
        return self._content_frame
    
    @property
    def status_bar(self):
        """获取状态栏"""
        return self._status_bar
    
    @property
    def title_bar(self):
        """获取标题栏"""
        return self._title_bar
    
    @property
    def navigation_items(self) -> List[NavigationItem]:
        """获取导航项列表（只读）"""
        return self._navigation_items.copy()
    
    @property
    def view_count(self) -> int:
        """缓存的视图数量"""
        return len(self._view_cache)
    
    def get_full_status(self) -> Dict[str, Any]:
        """获取完整窗口状态（包含基类状态）"""
        base_status = super().get_status()
        main_status = {
            "current_view": self._current_view,
            "navigation_item_count": len(self._navigation_items),
            "view_count": self.view_count,
            "nav_button_count": len(self._nav_buttons)
        }
        return {**base_status, **main_status}


# 导出
__all__ = [
    "WindowState",
    "NavigationItemType",
    "NavigationItem",
    "BaseWindow",
    "MainWindow"
]