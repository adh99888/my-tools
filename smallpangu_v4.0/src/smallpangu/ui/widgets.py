"""
UI组件库

提供现代化、可扩展的UI组件，包括基础组件、布局组件、特殊组件。
支持主题动态更新、国际化、响应式布局。
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field

from ..core.events import EventBus
from ..config.manager import ConfigManager
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class WidgetState(str, Enum):
    """组件状态枚举"""
    NORMAL = "normal"
    DISABLED = "disabled"
    HOVER = "hover"
    ACTIVE = "active"
    FOCUS = "focus"
    READONLY = "readonly"


class Alignment(str, Enum):
    """对齐方式枚举"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    JUSTIFY = "justify"


@dataclass
class WidgetStyle:
    """组件样式数据类"""
    # 基础样式
    bg_color: Optional[str] = None
    fg_color: Optional[str] = None
    text_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[int] = None
    corner_radius: Optional[int] = None
    
    # 字体样式
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    font_weight: Optional[str] = None
    font_style: Optional[str] = None
    # 完整font元组支持（向后兼容）
    font: Optional[Union[str, Tuple[str, int], Tuple[str, int, str]]] = None
    
    # 布局样式
    padding: Optional[Union[int, Tuple[int, int], Tuple[int, int, int, int]]] = None
    margin: Optional[Union[int, Tuple[int, int], Tuple[int, int, int, int]]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    orientation: Optional[str] = None
    fill: Optional[str] = None
    expand: Optional[Union[bool, int]] = None
    wrap: Optional[bool] = None
    wraplength: Optional[int] = None
    justify: Optional[str] = None
    
    # 状态样式
    hover_color: Optional[str] = None
    active_color: Optional[str] = None
    disabled_color: Optional[str] = None
    
    def apply_to_widget(self, widget: ctk.CTkBaseClass) -> None:
        """
        将样式应用到组件
        
        Args:
            widget: 目标组件
        """
        style_dict = self.to_dict()
        
        # 特殊处理font属性
        if 'font' in style_dict:
            font_value = style_dict.pop('font')
            if isinstance(font_value, (tuple, list)):
                widget.configure(font=font_value)
        
        for attr, value in style_dict.items():
            if value is not None and hasattr(widget, attr):
                try:
                    widget.configure(**{attr: value})
                except Exception as e:
                    pass  # 静默处理样式应用失败
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for k, v in self.__dict__.items():
            if v is not None:
                result[k] = v
        return result
    
    @classmethod
    def from_dict(cls, style_dict: Dict[str, Any]) -> 'WidgetStyle':
        """从字典创建样式"""
        return cls(**{k: v for k, v in style_dict.items() if hasattr(cls, k)})
    
    def merge(self, other: 'WidgetStyle') -> 'WidgetStyle':
        """合并样式（other覆盖self）"""
        merged_dict = self.to_dict()
        merged_dict.update(other.to_dict())
        return self.from_dict(merged_dict)


class BaseWidget:
    """
    组件基类
    
    提供组件基础功能：
    1. 样式管理
    2. 状态管理
    3. 主题响应
    4. 事件处理
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[Union[WidgetStyle, Dict[str, Any]]] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None
    ):
        """
        初始化组件基类
        
        Args:
            parent: 父组件
            widget_id: 组件ID（用于事件和样式）
            style: 组件样式（可以是WidgetStyle对象或字典）
            config_manager: 配置管理器（可选）
            event_bus: 事件总线（可选）
        """
        self._parent = parent
        self._widget_id = widget_id or f"{self.__class__.__name__}_{id(self)}"
        self._config_manager = config_manager
        self._event_bus = event_bus
        
        # 样式管理 - 支持WidgetStyle对象或字典
        if style is None:
            self._base_style = WidgetStyle()
        elif isinstance(style, dict):
            self._base_style = WidgetStyle.from_dict(style)
        else:
            self._base_style = style
            
        self._current_style = self._base_style
        self._theme_styles: Dict[str, WidgetStyle] = {}
        
        # 子组件注册
        self._widgets: Dict[str, Any] = {}
        
        # 状态管理
        self._widget_state = WidgetState.NORMAL
        self._is_visible = True
        self._is_enabled = True
        
        # 事件监听器
        self._event_listeners: Dict[str, List[Callable]] = {}
        
        # 实际Tkinter组件（子类设置）
        self._widget: Optional[ctk.CTkBaseClass] = None
        
        logger.debug_struct("组件基类初始化", widget_id=self._widget_id)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """
        创建实际组件（子类实现）
        
        Returns:
            创建的组件
        """
        raise NotImplementedError("子类必须实现create_widget方法")
    
    def initialize(self) -> None:
        """初始化组件"""
        if self._widget is None:
            self._widget = self.create_widget()
            
            # 应用初始样式
            self._apply_style()
            
            # 订阅事件
            self._subscribe_events()
            
            logger.debug_struct("组件初始化完成", widget_id=self._widget_id)
    
    def _apply_style(self) -> None:
        """应用当前样式到组件"""
        if self._widget and self._current_style:
            self._current_style.apply_to_widget(self._widget)
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        if self._event_bus:
            # 主题切换事件
            self._event_bus.subscribe("theme.changed", self._on_theme_changed)
            
            # 语言切换事件
            self._event_bus.subscribe("language.changed", self._on_language_changed)
    
    def _on_theme_changed(self, event) -> None:
        """处理主题切换事件"""
        logger.debug_struct("处理主题切换事件", widget_id=self._widget_id, data=event.data)
        self.update_style_for_theme(event.data.get("theme", "dark"))
    
    def _on_language_changed(self, event) -> None:
        """处理语言切换事件"""
        logger.debug_struct("处理语言切换事件", widget_id=self._widget_id, data=event.data)
        self._update_text_for_language(event.data.get("language", "zh-CN"))
    
    def _update_text_for_language(self, language: str) -> None:
        """
        根据语言更新文本（子类可覆盖）
        
        Args:
            language: 语言代码
        """
        pass
    
    def set_style(self, style: WidgetStyle, apply_now: bool = True) -> None:
        """
        设置组件样式
        
        Args:
            style: 新样式
            apply_now: 是否立即应用
        """
        self._current_style = style
        
        if apply_now and self._widget:
            style.apply_to_widget(self._widget)
        
        logger.debug_struct("组件样式设置", widget_id=self._widget_id)
    
    def update_style(self, **style_kwargs) -> None:
        """
        更新组件样式
        
        Args:
            **style_kwargs: 样式参数
        """
        new_style = WidgetStyle(**style_kwargs)
        self._current_style = self._current_style.merge(new_style)
        
        if self._widget:
            new_style.apply_to_widget(self._widget)
        
        logger.debug_struct("组件样式更新", widget_id=self._widget_id, kwargs=style_kwargs)
    
    def set_theme_style(self, theme: str, style: WidgetStyle) -> None:
        """
        为主题设置特定样式
        
        Args:
            theme: 主题名称
            style: 主题样式
        """
        self._theme_styles[theme] = style
        logger.debug_struct("主题样式设置", widget_id=self._widget_id, theme=theme)
    
    def update_style_for_theme(self, theme: str) -> None:
        """
        根据主题更新样式
        
        Args:
            theme: 主题名称
        """
        if theme in self._theme_styles:
            theme_style = self._theme_styles[theme]
            self.set_style(theme_style)
        else:
            # 使用默认样式
            self.set_style(self._base_style)
    
    def set_state(self, state: WidgetState) -> None:
        """
        设置组件状态
        
        Args:
            state: 组件状态
        """
        self._widget_state = state
        
        if self._widget:
            if state == WidgetState.DISABLED:
                self._widget.configure(state="disabled")
                self._is_enabled = False
            elif state == WidgetState.READONLY:
                # 对于支持只读的组件
                if hasattr(self._widget, 'configure'):
                    try:
                        self._widget.configure(state="readonly")
                    except:
                        # 如果不支持readonly状态，使用disabled
                        self._widget.configure(state="disabled")
                self._is_enabled = False
            else:
                self._widget.configure(state="normal")
                self._is_enabled = True
        
        logger.debug_struct("组件状态设置", widget_id=self._widget_id, state=state)
    
    def show(self) -> None:
        """显示组件"""
        if self._widget and not self._is_visible:
            self._widget.pack()
            self._is_visible = True
            logger.debug_struct("组件显示", widget_id=self._widget_id)
    
    def hide(self) -> None:
        """隐藏组件"""
        if self._widget and self._is_visible:
            self._widget.pack_forget()
            self._is_visible = False
            logger.debug_struct("组件隐藏", widget_id=self._widget_id)
    
    def enable(self) -> None:
        """启用组件"""
        self.set_state(WidgetState.NORMAL)
    
    def disable(self) -> None:
        """禁用组件"""
        self.set_state(WidgetState.DISABLED)
    
    def set_readonly(self) -> None:
        """设置只读"""
        self.set_state(WidgetState.READONLY)
    
    def bind_event(self, event_type: str, handler: Callable) -> None:
        """
        绑定事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if self._widget:
            self._widget.bind(event_type, handler)
            
            # 存储监听器引用
            if event_type not in self._event_listeners:
                self._event_listeners[event_type] = []
            self._event_listeners[event_type].append(handler)
            
            logger.debug_struct("事件绑定", widget_id=self._widget_id, event_type=event_type)
    
    def unbind_event(self, event_type: str, handler: Optional[Callable] = None) -> None:
        """
        解绑事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器（为None时解绑所有）
        """
        if self._widget:
            if handler:
                self._widget.unbind(event_type, handler)
                if event_type in self._event_listeners and handler in self._event_listeners[event_type]:
                    self._event_listeners[event_type].remove(handler)
            else:
                self._widget.unbind_all(event_type)
                if event_type in self._event_listeners:
                    self._event_listeners[event_type].clear()
            
            logger.debug_struct("事件解绑", widget_id=self._widget_id, event_type=event_type)
    
    def get_widget(self) -> Optional[ctk.CTkBaseClass]:
        """获取实际组件"""
        return self._widget
    
    def register_widget(self, name: str, widget: Any) -> None:
        """注册子组件"""
        self._widgets[name] = widget
        logger.debug_struct("子组件注册", widget_id=self._widget_id, name=name)
    
    def get_registered_widget(self, name: str) -> Optional[Any]:
        """获取已注册的子组件"""
        return self._widgets.get(name)
    
    def destroy(self) -> None:
        """销毁组件"""
        if self._widget:
            self._widget.destroy()
            self._widget = None
            logger.debug_struct("组件销毁", widget_id=self._widget_id)
    
    # 属性访问
    @property
    def widget_id(self) -> str:
        """获取组件ID"""
        return self._widget_id
    
    @property
    def widget_state(self) -> WidgetState:
        """获取组件状态"""
        return self._widget_state
    
    @property
    def is_visible(self) -> bool:
        """组件是否可见"""
        return self._is_visible
    
    @property
    def is_enabled(self) -> bool:
        """组件是否启用"""
        return self._is_enabled
    
    @property
    def current_style(self) -> WidgetStyle:
        """获取当前样式"""
        return self._current_style
    
    def get_status(self) -> Dict[str, Any]:
        """获取组件状态"""
        return {
            "widget_id": self._widget_id,
            "widget_type": self.__class__.__name__,
            "widget_state": self._widget_state,
            "visible": self._is_visible,
            "enabled": self._is_enabled,
            "theme_style_count": len(self._theme_styles),
            "event_listener_count": sum(len(listeners) for listeners in self._event_listeners.values())
        }


# ============================================================================
# 布局组件
# ============================================================================

class Panel(BaseWidget):
    """面板组件 - 基础布局容器"""
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[Union[WidgetStyle, Dict[str, Any]]] = None,
        **kwargs
    ):
        """初始化面板"""
        super().__init__(parent, widget_id, style)
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建面板组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkFrame(self._parent, **config)
    
    def add_widget(self, child_widget: 'BaseWidget') -> None:
        """
        添加子组件到面板
        
        Args:
            child_widget: 子组件实例
        """
        if not self._widget:
            self.initialize()
        
        # 获取子组件的实际Tkinter组件
        child_tk_widget = child_widget.get_widget()
        if not child_tk_widget:
            child_widget.initialize()
            child_tk_widget = child_widget.get_widget()
        
        if not child_tk_widget:
            logger.error(f"无法获取子组件 {child_widget.widget_id} 的Tkinter组件")
            return
        
        # 获取布局参数
        style = self._current_style
        orientation = getattr(style, 'orientation', 'vertical')
        fill = getattr(style, 'fill', 'none')
        expand = getattr(style, 'expand', False)
        padding = getattr(style, 'padding', (0, 0))
        
        # 转换padding为元组
        if isinstance(padding, (list, tuple)):
            if len(padding) == 1:
                padx = pady = padding[0]
            elif len(padding) == 2:
                padx, pady = padding
            elif len(padding) == 4:
                padx = (padding[0], padding[2])
                pady = (padding[1], padding[3])
            else:
                padx = pady = 0
        else:
            padx = pady = padding
        
        # 根据方向布局
        if orientation == 'horizontal':
            side = 'left'
            fill_axis = 'y' if fill == 'both' or fill == 'y' else 'none'
            expand_bool = expand if isinstance(expand, bool) else False
            child_tk_widget.pack(side=side, fill=fill_axis, expand=expand_bool, padx=padx, pady=pady)
        else:  # vertical
            side = 'top'
            fill_axis = 'x' if fill == 'both' or fill == 'x' else 'none'
            expand_bool = expand if isinstance(expand, bool) else False
            child_tk_widget.pack(side=side, fill=fill_axis, expand=expand_bool, padx=padx, pady=pady)
        
        # 注册子组件
        self.register_widget(f"child_{child_widget.widget_id}", child_widget)
        logger.debug_struct("面板子组件添加", panel_id=self.widget_id, child_id=child_widget.widget_id)
    
    def remove_widget(self, child_widget: 'BaseWidget') -> None:
        """
        从面板移除子组件
        
        Args:
            child_widget: 子组件实例
        """
        child_tk_widget = child_widget.get_widget()
        if child_tk_widget and self._widget:
            child_tk_widget.pack_forget()
        
        # 注销子组件
        child_key = f"child_{child_widget.widget_id}"
        if child_key in self._widgets:
            del self._widgets[child_key]
        
        logger.debug_struct("面板子组件移除", panel_id=self.widget_id, child_id=child_widget.widget_id)

class Card(Panel):
    """卡片组件 - 带阴影和圆角的特殊面板"""
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[Union[WidgetStyle, Dict[str, Any]]] = None,
        shadow: bool = True,
        elevation: int = 2,
        **kwargs
    ):
        """初始化卡片"""
        # 卡片默认样式
        card_style = WidgetStyle(
            corner_radius=10,
            border_width=1,
            border_color=("gray70", "gray30"),
            fg_color=("gray95", "gray20")
        )
        
        if style:
            card_style = card_style.merge(style)
        
        self._shadow = shadow
        self._elevation = elevation
        self._kwargs = kwargs
        
        super().__init__(parent, widget_id, card_style, **kwargs)


class ScrollPanel(BaseWidget):
    """滚动面板组件 - 带滚动条的容器"""
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        scrollbar_width: int = 16,
        **kwargs
    ):
        """初始化滚动面板"""
        super().__init__(parent, widget_id, style)
        self._scrollbar_width = scrollbar_width
        self._kwargs = kwargs
        self._content_frame = None
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建滚动面板组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        scroll_frame = ctk.CTkScrollableFrame(self._parent, **config)
        scroll_frame._scrollbar.configure(width=self._scrollbar_width)
        
        # 保存内容框架引用
        self._content_frame = scroll_frame
        
        return scroll_frame
    
    def get_content_frame(self) -> Optional[ctk.CTkBaseClass]:
        """获取内容框架（用于添加子组件）"""
        return self._content_frame
    
    def add_widget(self, child_widget: 'BaseWidget') -> None:
        """
        添加子组件到滚动面板
        
        Args:
            child_widget: 子组件实例
        """
        if not self._content_frame:
            self.initialize()
            if not self._content_frame:
                logger.error("滚动面板内容框架未初始化")
                return
        
        # 获取子组件的实际Tkinter组件
        child_tk_widget = child_widget.get_widget()
        if not child_tk_widget:
            child_widget.initialize()
            child_tk_widget = child_widget.get_widget()
        
        if not child_tk_widget:
            logger.error(f"无法获取子组件 {child_widget.widget_id} 的Tkinter组件")
            return
        
        # 将子组件添加到内容框架
        child_tk_widget.pack(fill="x", padx=0, pady=2)
        
        # 注册子组件
        self.register_widget(f"child_{child_widget.widget_id}", child_widget)
        logger.debug_struct("滚动面子组件添加", panel_id=self.widget_id, child_id=child_widget.widget_id)
    
    def remove_widget(self, child_widget: 'BaseWidget') -> None:
        """
        从滚动面板移除子组件
        
        Args:
            child_widget: 子组件实例
        """
        child_tk_widget = child_widget.get_widget()
        if child_tk_widget:
            child_tk_widget.pack_forget()
        
        # 注销子组件
        child_key = f"child_{child_widget.widget_id}"
        if child_key in self._widgets:
            del self._widgets[child_key]
        
        logger.debug_struct("滚动面子组件移除", panel_id=self.widget_id, child_id=child_widget.widget_id)


# ============================================================================
# 基础组件
# ============================================================================

class Button(BaseWidget):
    """按钮组件"""
    
    def __init__(
        self,
        parent,
        text: str = "按钮",
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        command: Optional[Callable] = None,
        **kwargs
    ):
        """初始化按钮"""
        super().__init__(parent, widget_id, style)
        self._text = text
        self._command = command
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建按钮组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkButton(self._parent, text=self._text, command=self._command, **config)
    
    def set_text(self, text: str) -> None:
        """设置按钮文本"""
        self._text = text
        if self._widget:
            self._widget.configure(text=text)
    
    def set_command(self, command: Callable) -> None:
        """设置按钮命令"""
        self._command = command
        if self._widget:
            self._widget.configure(command=command)
    
    def _update_text_for_language(self, language: str) -> None:
        """根据语言更新文本"""
        # 这里可以实现多语言文本更新逻辑
        pass


class Label(BaseWidget):
    """标签组件"""
    
    def __init__(
        self,
        parent,
        text: str = "",
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        **kwargs
    ):
        """初始化标签"""
        super().__init__(parent, widget_id, style)
        self._text = text
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建标签组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkLabel(self._parent, text=self._text, **config)
    
    def set_text(self, text: str) -> None:
        """设置标签文本"""
        self._text = text
        if self._widget:
            self._widget.configure(text=text)
    
    def _update_text_for_language(self, language: str) -> None:
        """根据语言更新文本"""
        # 这里可以实现多语言文本更新逻辑
        pass


class InputField(BaseWidget):
    """输入框组件"""
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        placeholder: str = "",
        **kwargs
    ):
        """初始化输入框"""
        super().__init__(parent, widget_id, style)
        self._placeholder = placeholder
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建输入框组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkEntry(self._parent, placeholder_text=self._placeholder, **config)
    
    def get_value(self) -> str:
        """获取输入值"""
        if self._widget:
            return self._widget.get()
        return ""
    
    def set_value(self, value: str) -> None:
        """设置输入值"""
        if self._widget:
            self._widget.delete(0, "end")
            self._widget.insert(0, value)
    
    def clear(self) -> None:
        """清空输入框"""
        self.set_value("")
    
    def set_placeholder(self, placeholder: str) -> None:
        """设置占位符文本"""
        self._placeholder = placeholder
        if self._widget:
            self._widget.configure(placeholder_text=placeholder)
    
    def _update_text_for_language(self, language: str) -> None:
        """根据语言更新占位符文本"""
        # 这里可以实现多语言占位符更新逻辑
        pass


class TextArea(BaseWidget):
    """文本区域组件"""
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        **kwargs
    ):
        """初始化文本区域"""
        super().__init__(parent, widget_id, style)
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建文本区域组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        # CustomTkinter没有专门的TextArea，使用CTkTextbox
        return ctk.CTkTextbox(self._parent, **config)
    
    def get_value(self) -> str:
        """获取文本值"""
        if self._widget:
            return self._widget.get("1.0", "end-1c")
        return ""
    
    def set_value(self, value: str) -> None:
        """设置文本值"""
        if self._widget:
            self._widget.delete("1.0", "end")
            self._widget.insert("1.0", value)
    
    def clear(self) -> None:
        """清空文本区域"""
        self.set_value("")
    
    def append_text(self, text: str) -> None:
        """追加文本"""
        if self._widget:
            self._widget.insert("end", text)
    
    def get_line_count(self) -> int:
        """获取行数"""
        if self._widget:
            return int(self._widget.index("end-1c").split(".")[0])
        return 0


# ============================================================================
# 特殊组件
# ============================================================================

class ProgressBar(BaseWidget):
    """进度条组件"""
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        mode: str = "determinate",
        **kwargs
    ):
        """初始化进度条"""
        super().__init__(parent, widget_id, style)
        self._mode = mode
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建进度条组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkProgressBar(self._parent, mode=self._mode, **config)
    
    def set_value(self, value: float) -> None:
        """设置进度值（0.0-1.0）"""
        if self._widget and 0.0 <= value <= 1.0:
            self._widget.set(value)
    
    def get_value(self) -> float:
        """获取当前进度值"""
        if self._widget:
            return self._widget.get()
        return 0.0
    
    def start(self, interval: int = 100) -> None:
        """开始不确定模式动画"""
        if self._widget and self._mode == "indeterminate":
            self._widget.start()
    
    def stop(self) -> None:
        """停止不确定模式动画"""
        if self._widget and self._mode == "indeterminate":
            self._widget.stop()


class Switch(BaseWidget):
    """开关组件"""
    
    def __init__(
        self,
        parent,
        text: str = "",
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        **kwargs
    ):
        """初始化开关"""
        super().__init__(parent, widget_id, style)
        self._text = text
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建开关组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkSwitch(self._parent, text=self._text, **config)
    
    def get_value(self) -> bool:
        """获取开关状态"""
        if self._widget:
            return bool(self._widget.get())
        return False
    
    def set_value(self, value: bool) -> None:
        """设置开关状态"""
        if self._widget:
            self._widget.select() if value else self._widget.deselect()
    
    def toggle(self) -> bool:
        """切换开关状态"""
        if self._widget:
            self._widget.toggle()
            return self.get_value()
        return False
    
    def set_text(self, text: str) -> None:
        """设置开关文本"""
        self._text = text
        if self._widget:
            self._widget.configure(text=text)
    
    def _update_text_for_language(self, language: str) -> None:
        """根据语言更新文本"""
        # 这里可以实现多语言文本更新逻辑
        pass


class Dropdown(BaseWidget):
    """下拉选择组件"""
    
    def __init__(
        self,
        parent,
        options: List[str],
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        default_value: Optional[str] = None,
        **kwargs
    ):
        """初始化下拉选择"""
        super().__init__(parent, widget_id, style)
        self._options = options
        self._default_value = default_value or (options[0] if options else "")
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建下拉选择组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        return ctk.CTkComboBox(self._parent, values=self._options, **config)
    
    def get_value(self) -> str:
        """获取选中值"""
        if self._widget:
            return self._widget.get()
        return ""
    
    def set_value(self, value: str) -> None:
        """设置选中值"""
        if self._widget and value in self._options:
            self._widget.set(value)
    
    def set_options(self, options: List[str], default_value: Optional[str] = None) -> None:
        """设置选项列表"""
        self._options = options
        if self._widget:
            self._widget.configure(values=options)
            
            # 更新默认值
            new_default = default_value or (options[0] if options else "")
            if new_default in options:
                self._default_value = new_default
                self._widget.set(new_default)


class TabView(BaseWidget):
    """标签页组件"""
    
    def __init__(
        self,
        parent,
        tabs: List[str],
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        **kwargs
    ):
        """初始化标签页"""
        super().__init__(parent, widget_id, style)
        self._tabs = tabs
        self._tab_frames: Dict[str, ctk.CTkFrame] = {}
        self._kwargs = kwargs
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建标签页组件"""
        style_dict = self._current_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        tab_view = ctk.CTkTabview(self._parent, **config)
        
        # 创建标签页
        for tab_name in self._tabs:
            tab_frame = tab_view.add(tab_name)
            self._tab_frames[tab_name] = tab_frame
        
        return tab_view
    
    def get_tab_frame(self, tab_name: str) -> Optional[ctk.CTkFrame]:
        """获取标签页框架"""
        return self._tab_frames.get(tab_name)
    
    def get_current_tab(self) -> str:
        """获取当前选中的标签页"""
        if self._widget:
            return self._widget.get()
        return ""
    
    def set_current_tab(self, tab_name: str) -> None:
        """设置当前标签页"""
        if self._widget and tab_name in self._tabs:
            self._widget.set(tab_name)
    
    def add_tab(self, tab_name: str) -> Optional[ctk.CTkFrame]:
        """添加新标签页"""
        if self._widget and tab_name not in self._tabs:
            tab_frame = self._widget.add(tab_name)
            self._tabs.append(tab_name)
            self._tab_frames[tab_name] = tab_frame
            return tab_frame
        return None
    
    def remove_tab(self, tab_name: str) -> bool:
        """移除标签页"""
        if self._widget and tab_name in self._tabs:
            # CustomTkinter的CTkTabview没有直接的remove方法
            # 这里需要重新创建Tabview或者使用其他方法
            logger.warning_struct("标签页移除功能受限", tab_name=tab_name)
            return False
        return False


# ============================================================================
# 复合组件
# ============================================================================

class MessageCard(BaseWidget):
    """消息卡片组件（用于聊天界面）"""
    
    def __init__(
        self,
        parent,
        message: str,
        sender: str = "user",
        timestamp: str = "",
        widget_id: Optional[str] = None,
        style: Optional[WidgetStyle] = None,
        **kwargs
    ):
        """初始化消息卡片"""
        super().__init__(parent, widget_id, style)
        self._message = message
        self._sender = sender  # "user" 或 "assistant"
        self._timestamp = timestamp
        self._kwargs = kwargs
        
        # 子组件
        self._sender_label = None
        self._message_label = None
        self._time_label = None
        
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建消息卡片组件"""
        # 创建主卡片
        card_style = WidgetStyle(
            corner_radius=10,
            border_width=1,
            border_color=("gray70", "gray30"),
            fg_color=("gray95", "gray20") if self._sender == "user" else ("gray85", "gray25")
        )
        
        if self._current_style:
            card_style = card_style.merge(self._current_style)
        
        style_dict = card_style.to_dict()
        config = {**style_dict, **self._kwargs}
        
        card = ctk.CTkFrame(self._parent, **config)
        
        # 配置网格布局
        card.grid_columnconfigure(0, weight=1)
        
        # 发送者标签
        sender_text = "你" if self._sender == "user" else "助手"
        self._sender_label = ctk.CTkLabel(
            card,
            text=sender_text,
            font=("Microsoft YaHei", 11, "bold"),
            anchor="w"
        )
        self._sender_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        
        # 时间标签
        if self._timestamp:
            self._time_label = ctk.CTkLabel(
                card,
                text=self._timestamp,
                font=("Microsoft YaHei", 9),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            self._time_label.grid(row=0, column=1, sticky="e", padx=10, pady=(8, 2))
        
        # 消息标签
        self._message_label = ctk.CTkLabel(
            card,
            text=self._message,
            font=("Microsoft YaHei", 11),
            wraplength=400,
            justify="left",
            anchor="w"
        )
        self._message_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 8))
        
        return card
    
    def set_message(self, message: str) -> None:
        """更新消息内容"""
        self._message = message
        if self._message_label:
            self._message_label.configure(text=message)
    
    def set_sender(self, sender: str) -> None:
        """更新发送者"""
        self._sender = sender
        if self._sender_label:
            sender_text = "你" if self._sender == "user" else "助手"
            self._sender_label.configure(text=sender_text)
        
        # 更新卡片背景颜色
        if self._widget:
            new_color = ("gray95", "gray20") if sender == "user" else ("gray85", "gray25")
            self._widget.configure(fg_color=new_color)
    
    def set_timestamp(self, timestamp: str) -> None:
        """更新时间戳"""
        self._timestamp = timestamp
        if self._time_label:
            self._time_label.configure(text=timestamp)
        elif timestamp and self._widget:
            # 如果之前没有时间标签，现在创建
            self._time_label = ctk.CTkLabel(
                self._widget,
                text=timestamp,
                font=("Microsoft YaHei", 9),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            self._time_label.grid(row=0, column=1, sticky="e", padx=10, pady=(8, 2))


# ============================================================================
# 快捷创建函数
# ============================================================================

def create_button(
    parent,
    text: str,
    command: Optional[Callable] = None,
    **kwargs
) -> Button:
    """快捷创建按钮"""
    return Button(parent, text=text, command=command, **kwargs)


def create_label(
    parent,
    text: str = "",
    **kwargs
) -> Label:
    """快捷创建标签"""
    return Label(parent, text=text, **kwargs)


def create_input(
    parent,
    placeholder: str = "",
    **kwargs
) -> InputField:
    """快捷创建输入框"""
    return InputField(parent, placeholder=placeholder, **kwargs)


def create_panel(
    parent,
    **kwargs
) -> Panel:
    """快捷创建面板"""
    return Panel(parent, **kwargs)


def create_card(
    parent,
    **kwargs
) -> Card:
    """快捷创建卡片"""
    return Card(parent, **kwargs)


def create_scroll_panel(
    parent,
    **kwargs
) -> ScrollPanel:
    """快捷创建滚动面板"""
    return ScrollPanel(parent, **kwargs)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 枚举和数据结构
    "WidgetState",
    "Alignment",
    "WidgetStyle",
    
    # 基类
    "BaseWidget",
    
    # 布局组件
    "Panel",
    "Card",
    "ScrollPanel",
    
    # 基础组件
    "Button",
    "Label",
    "InputField",
    "TextArea",
    
    # 特殊组件
    "ProgressBar",
    "Switch",
    "Dropdown",
    "TabView",
    
    # 复合组件
    "MessageCard",
    
    # 快捷函数
    "create_button",
    "create_label",
    "create_input",
    "create_panel",
    "create_card",
    "create_scroll_panel"
]