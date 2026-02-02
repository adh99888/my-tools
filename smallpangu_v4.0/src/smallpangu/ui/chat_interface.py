"""
聊天界面组件

提供现代化的聊天界面，包括：
1. 消息列表（可滚动，支持Markdown渲染）
2. 消息输入区域
3. 发送按钮和功能
4. 消息历史管理
5. 用户和助手消息的不同样式
"""

import customtkinter as ctk
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from .manager import UIManager
from .widgets import BaseWidget, Panel, ScrollPanel, TextArea, Button, MessageCard
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class MessageStatus(str, Enum):
    """消息状态枚举"""
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ERROR = "error"


@dataclass
class ChatMessage:
    """聊天消息数据类"""
    id: str
    role: MessageRole
    content: str
    timestamp: float
    status: MessageStatus = MessageStatus.SENT
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """数据验证"""
        if not self.id:
            raise ValueError("消息ID不能为空")
        if not self.content:
            raise ValueError("消息内容不能为空")
    
    @property
    def formatted_time(self) -> str:
        """获取格式化的时间字符串"""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%H:%M:%S")
    
    @property
    def formatted_date(self) -> str:
        """获取格式化的日期字符串"""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class ChatInterface(BaseWidget):
    """
    聊天界面组件
    
    现代化聊天界面，支持：
    1. 消息列表显示和滚动
    2. 消息输入和发送
    3. Markdown渲染
    4. 消息历史管理
    5. 实时状态更新
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        container: Optional[Container] = None,
        max_history: int = 100,
        enable_markdown: bool = True,
        auto_scroll: bool = True,
        **kwargs
    ):
        """
        初始化聊天界面
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            max_history: 最大历史消息数
            enable_markdown: 是否启用Markdown渲染
            auto_scroll: 是否自动滚动到最新消息
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None, config_manager, event_bus)
        self._container = container
        
        # 配置
        self._max_history = max_history
        self._enable_markdown = enable_markdown
        self._auto_scroll = auto_scroll
        
        # 消息管理
        self._messages: List[ChatMessage] = []
        self._message_widgets: Dict[str, MessageCard] = {}
        self._current_input = ""
        
        # UI组件
        self._main_panel = None
        self._message_panel = None
        self._input_panel = None
        self._input_text = None
        self._send_button = None
        
        # 事件回调
        self._on_send_message: Optional[Callable] = None
        self._on_message_click: Optional[Callable] = None
        
        # 初始化
        self.initialize()
        
        logger.debug_struct("聊天界面初始化", widget_id=self._widget_id, max_history=max_history)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建聊天界面组件"""
        # 创建主面板
        self._main_panel = Panel(self._parent)
        main_widget = self._main_panel.get_widget()
        
        # 配置网格布局
        main_widget.grid_rowconfigure(0, weight=1)  # 消息区域
        main_widget.grid_rowconfigure(1, weight=0)  # 输入区域
        main_widget.grid_columnconfigure(0, weight=1)
        
        # 1. 创建消息区域（可滚动）
        self._create_message_area(main_widget)
        
        # 2. 创建输入区域
        self._create_input_area(main_widget)
        
        # 注册主面板
        self.register_widget("main_panel", main_widget)
        
        return main_widget
    
    def _create_message_area(self, parent) -> None:
        """创建消息显示区域"""
        logger.debug("创建消息区域")
        
        # 创建滚动面板
        message_style = {
            "fg_color": ("gray95", "gray15"),
            "corner_radius": 0,
            "border_width": 0
        }
        
        self._message_panel = ScrollPanel(
            parent,
            widget_id=f"{self._widget_id}_message_panel",
            style=message_style
        )
        message_widget = self._message_panel.get_widget()
        message_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # 配置滚动面板内部框架
        content_frame = self._message_panel.get_content_frame()
        if content_frame:
            content_frame.grid_columnconfigure(0, weight=1)
        
        # 注册组件
        self.register_widget("message_panel", message_widget)
        self.register_widget("message_content_frame", content_frame)
        
        # 欢迎消息
        self._add_welcome_message()
    
    def _add_welcome_message(self) -> None:
        """添加欢迎消息"""
        welcome_message = ChatMessage(
            id=f"welcome_{int(time.time())}",
            role=MessageRole.SYSTEM,
            content="欢迎使用小盘古 AI 助手！\n\n我是您的智能助手，可以帮您处理各种问题。\n请在下方的输入框中输入您的问题。",
            timestamp=time.time()
        )
        
        self.add_message(welcome_message, scroll_to_bottom=False)
    
    def _create_input_area(self, parent) -> None:
        """创建消息输入区域"""
        logger.debug("创建输入区域")
        
        # 输入区域框架
        input_style = {
            "fg_color": ("gray90", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray70", "gray30")
        }
        
        self._input_panel = Panel(parent, style=input_style)
        input_widget = self._input_panel.get_widget()
        input_widget.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 配置输入区域网格
        input_widget.grid_columnconfigure(0, weight=1)
        input_widget.grid_columnconfigure(1, weight=0)
        input_widget.grid_rowconfigure(0, weight=1)
        
        # 创建文本输入区域
        input_text_style = {
            "fg_color": ("white", "gray25"),
            "border_color": ("gray70", "gray40"),
            "border_width": 1,
            "corner_radius": 5,
            "font": ("Microsoft YaHei", 11),
            "height": 80
        }
        
        self._input_text = TextArea(
            input_widget,
            widget_id=f"{self._widget_id}_input_text",
            style=input_text_style
        )
        input_text_widget = self._input_text.get_widget()
        input_text_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 绑定回车键发送消息（Ctrl+Enter换行）
        input_text_widget.bind("<Return>", self._on_input_return_key)
        input_text_widget.bind("<Control-Return>", self._on_input_ctrl_return)
        
        # 创建发送按钮
        button_style = {
            "fg_color": ("#2b5b84", "#3a7ebf"),
            "hover_color": ("#1e3a5f", "#2b5b84"),
            "text_color": "white",
            "corner_radius": 5,
            "font": ("Microsoft YaHei", 11, "bold"),
            "width": 80,
            "height": 40
        }
        
        self._send_button = Button(
            input_widget,
            text="发送",
            widget_id=f"{self._widget_id}_send_button",
            style=button_style,
            command=self._on_send_button_click
        )
        send_button_widget = self._send_button.get_widget()
        send_button_widget.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        
        # 注册组件
        self.register_widget("input_panel", input_widget)
        self.register_widget("input_text", input_text_widget)
        self.register_widget("send_button", send_button_widget)
        
        # 设置输入框焦点
        input_text_widget.focus_set()
    
    def _on_input_return_key(self, event) -> str:
        """
        处理回车键事件
        
        Args:
            event: 键盘事件
            
        Returns:
            事件处理结果
        """
        # Ctrl+Enter是换行，单独的Enter是发送
        if event.state & 0x4:  # Ctrl键
            # 插入换行符
            widget = self._input_text.get_widget()
            if widget:
                widget.insert("insert", "\n")
            return "break"
        else:
            # 发送消息
            self._send_current_message()
            return "break"
    
    def _on_input_ctrl_return(self, event) -> str:
        """处理Ctrl+Enter事件（插入换行）"""
        # 这个事件由_on_input_return_key处理
        return "break"
    
    def _on_send_button_click(self) -> None:
        """处理发送按钮点击"""
        self._send_current_message()
    
    def _send_current_message(self) -> None:
        """发送当前输入的消息"""
        if not self._input_text:
            return
        
        # 获取输入文本
        message_text = self._input_text.get_value().strip()
        if not message_text:
            logger.debug("消息为空，不发送")
            return
        
        logger.debug_struct("发送消息", text_length=len(message_text))
        
        # 创建用户消息
        user_message = ChatMessage(
            id=f"user_{int(time.time() * 1000)}",
            role=MessageRole.USER,
            content=message_text,
            timestamp=time.time()
        )
        
        # 添加到消息列表
        self.add_message(user_message)
        
        # 清空输入框
        self._input_text.clear()
        
        # 触发发送回调
        if self._on_send_message:
            try:
                self._on_send_message(message_text, user_message)
            except Exception as e:
                logger.error_struct("发送回调执行失败", error=str(e))
        
        # 发布消息发送事件
        if self._event_bus:
            self._event_bus.publish("chat.message.sent", {
                "message_id": user_message.id,
                "role": user_message.role.value,
                "content": message_text,
                "timestamp": user_message.timestamp
            })
    
    def add_message(self, message: ChatMessage, scroll_to_bottom: bool = True) -> None:
        """
        添加消息到聊天界面
        
        Args:
            message: 消息对象
            scroll_to_bottom: 是否滚动到底部
        """
        logger.debug_struct("添加消息", message_id=message.id, role=message.role)
        
        # 添加到消息列表
        self._messages.append(message)
        
        # 限制历史消息数量
        if len(self._messages) > self._max_history:
            removed = self._messages.pop(0)
            if removed.id in self._message_widgets:
                removed_widget = self._message_widgets.pop(removed.id)
                removed_widget.destroy()
        
        # 创建消息组件
        message_widget = self._create_message_widget(message)
        if message_widget:
            self._message_widgets[message.id] = message_widget
            
            # 添加到消息面板
            content_frame = self._message_panel.get_content_frame()
            if content_frame:
                widget = message_widget.get_widget()
                if widget:
                    widget.pack(fill="x", padx=10, pady=5, anchor="w")
            
            # 自动滚动到底部
            if scroll_to_bottom and self._auto_scroll:
                self._scroll_to_bottom()
        
        # 发布消息添加事件
        if self._event_bus:
            self._event_bus.publish("chat.message.added", {
                "message_id": message.id,
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.timestamp,
                "status": message.status.value,
                "total_messages": len(self._messages)
            })
    
    def _create_message_widget(self, message: ChatMessage) -> Optional[MessageCard]:
        """
        创建消息组件
        
        Args:
            message: 消息对象
            
        Returns:
            消息卡片组件
        """
        try:
            content_frame = self._message_panel.get_content_frame()
            if not content_frame:
                return None
            
            # 根据消息角色确定发送者显示
            sender = "user" if message.role == MessageRole.USER else "assistant"
            
            # 特殊处理系统消息和错误消息
            if message.role == MessageRole.SYSTEM:
                sender = "system"
            elif message.role == MessageRole.ERROR:
                sender = "error"
            
            # 创建消息卡片
            message_widget = MessageCard(
                content_frame,
                message=message.content,
                sender=sender,
                timestamp=message.formatted_time,
                widget_id=f"message_{message.id}"
            )
            
            # 绑定点击事件
            widget = message_widget.get_widget()
            if widget and self._on_message_click:
                widget.bind("<Button-1>", lambda e, msg=message: self._on_message_click(msg))
            
            return message_widget
            
        except Exception as e:
            logger.error_struct("消息组件创建失败", message_id=message.id, error=str(e))
            return None
    
    def update_message_status(self, message_id: str, status: MessageStatus) -> bool:
        """
        更新消息状态
        
        Args:
            message_id: 消息ID
            status: 新状态
            
        Returns:
            是否成功更新
        """
        # 找到消息
        message = next((msg for msg in self._messages if msg.id == message_id), None)
        if not message:
            logger.warning_struct("消息未找到", message_id=message_id)
            return False
        
        # 更新状态
        old_status = message.status
        message.status = status
        
        logger.debug_struct("消息状态更新", 
                          message_id=message_id, 
                          old_status=old_status, 
                          new_status=status)
        
        # 这里可以添加UI状态更新逻辑，比如更新消息卡片的样式
        
        return True
    
    def add_assistant_response(self, content: str, message_id: Optional[str] = None) -> str:
        """
        添加助手响应
        
        Args:
            content: 响应内容
            message_id: 消息ID（如果为None则自动生成）
            
        Returns:
            创建的消息ID
        """
        message = ChatMessage(
            id=message_id or f"assistant_{int(time.time() * 1000)}",
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=time.time(),
            status=MessageStatus.SENT
        )
        
        self.add_message(message)
        return message.id
    
    def add_error_message(self, error_text: str) -> str:
        """
        添加错误消息
        
        Args:
            error_text: 错误文本
            
        Returns:
            创建的消息ID
        """
        message = ChatMessage(
            id=f"error_{int(time.time() * 1000)}",
            role=MessageRole.ERROR,
            content=f"❌ {error_text}",
            timestamp=time.time(),
            status=MessageStatus.ERROR
        )
        
        self.add_message(message)
        return message.id
    
    def _scroll_to_bottom(self) -> None:
        """滚动到消息列表底部"""
        if not self._message_panel:
            return
        
        widget = self._message_panel.get_widget()
        if widget:
            # CustomTkinter的ScrollableFrame需要更新后才能滚动
            widget.update()
            # 尝试滚动到底部
            try:
                # 这里使用after确保在UI更新后执行滚动
                widget.after(100, lambda: widget._parent_canvas.yview_moveto(1.0))
            except Exception as e:
                logger.debug_struct("滚动失败", error=str(e))
    
    def clear_messages(self) -> None:
        """清空所有消息"""
        logger.debug("清空所有消息")
        
        # 销毁所有消息组件
        for widget in self._message_widgets.values():
            widget.destroy()
        
        # 清空数据结构
        self._messages.clear()
        self._message_widgets.clear()
        
        # 添加欢迎消息
        self._add_welcome_message()
        
        # 发布清空事件
        if self._event_bus:
            self._event_bus.publish("chat.messages.cleared", {
                "timestamp": time.time(),
                "total_cleared": len(self._messages)
            })
    
    def get_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """
        获取消息列表
        
        Args:
            limit: 限制返回的消息数量（None表示全部）
            
        Returns:
            消息列表
        """
        if limit and limit > 0:
            return self._messages[-limit:]
        return self._messages.copy()
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self._messages)
    
    def set_on_send_message(self, callback: Callable) -> None:
        """
        设置消息发送回调
        
        Args:
            callback: 回调函数，接收(message_text, message_object)参数
        """
        self._on_send_message = callback
        logger.debug_struct("设置发送回调", has_callback=callback is not None)
    
    def set_on_message_click(self, callback: Callable) -> None:
        """
        设置消息点击回调
        
        Args:
            callback: 回调函数，接收message_object参数
        """
        self._on_message_click = callback
        logger.debug_struct("设置消息点击回调", has_callback=callback is not None)
    
    def set_input_focus(self) -> None:
        """设置输入框焦点"""
        if self._input_text:
            widget = self._input_text.get_widget()
            if widget:
                widget.focus_set()
    
    def enable_input(self) -> None:
        """启用输入"""
        if self._input_text:
            self._input_text.enable()
        if self._send_button:
            self._send_button.enable()
        
        logger.debug("聊天输入已启用")
    
    def disable_input(self) -> None:
        """禁用输入（例如在助手响应期间）"""
        if self._input_text:
            self._input_text.disable()
        if self._send_button:
            self._send_button.disable()
        
        logger.debug("聊天输入已禁用")
    
    def set_input_text(self, text: str) -> None:
        """
        设置输入框文本
        
        Args:
            text: 文本内容
        """
        if self._input_text:
            self._input_text.set_value(text)
    
    def get_input_text(self) -> str:
        """获取输入框文本"""
        if self._input_text:
            return self._input_text.get_value()
        return ""
    
    def clear_input(self) -> None:
        """清空输入框"""
        if self._input_text:
            self._input_text.clear()
    
    # 属性访问
    @property
    def max_history(self) -> int:
        """获取最大历史消息数"""
        return self._max_history
    
    @max_history.setter
    def max_history(self, value: int) -> None:
        """设置最大历史消息数"""
        if value < 1:
            raise ValueError("最大历史消息数必须大于0")
        self._max_history = value
        
        # 如果当前消息数超过新限制，移除旧消息
        while len(self._messages) > self._max_history:
            removed = self._messages.pop(0)
            if removed.id in self._message_widgets:
                removed_widget = self._message_widgets.pop(removed.id)
                removed_widget.destroy()
    
    @property
    def enable_markdown(self) -> bool:
        """是否启用Markdown渲染"""
        return self._enable_markdown
    
    @enable_markdown.setter
    def enable_markdown(self, value: bool) -> None:
        """设置是否启用Markdown渲染"""
        self._enable_markdown = value
        # TODO: 实现Markdown渲染的切换
    
    @property
    def auto_scroll(self) -> bool:
        """是否自动滚动"""
        return self._auto_scroll
    
    @auto_scroll.setter
    def auto_scroll(self, value: bool) -> None:
        """设置是否自动滚动"""
        self._auto_scroll = value
    
    def get_status(self) -> Dict[str, Any]:
        """获取聊天界面状态"""
        return {
            "widget_id": self._widget_id,
            "message_count": len(self._messages),
            "max_history": self._max_history,
            "enable_markdown": self._enable_markdown,
            "auto_scroll": self._auto_scroll,
            "input_enabled": self._input_text.is_enabled if self._input_text else False,
            "has_send_callback": self._on_send_message is not None,
            "has_message_click_callback": self._on_message_click is not None
        }


class ChatView:
    """
    聊天视图
    
    集成聊天界面到主窗口视图框架中
    """
    
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化聊天视图
        
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
        
        # UI配置
        self._ui_config = config_manager.config.ui
        
        # 主框架
        self._main_frame = None
        self._chat_interface = None
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("聊天视图初始化")
    
    def _initialize(self) -> None:
        """初始化聊天视图"""
        try:
            # 创建主框架
            self._main_frame = ctk.CTkFrame(self._parent)
            self._main_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            # 配置网格
            self._main_frame.grid_rowconfigure(0, weight=1)
            self._main_frame.grid_columnconfigure(0, weight=1)
            
            # 创建聊天界面
            self._chat_interface = ChatInterface(
                self._main_frame,
                widget_id="main_chat",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container,
                max_history=self._ui_config.chat_history_limit,
                enable_markdown=self._ui_config.markdown_render,
                auto_scroll=self._ui_config.auto_scroll
            )
            
            chat_widget = self._chat_interface.get_widget()
            if chat_widget:
                chat_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # 设置消息发送回调
            self._chat_interface.set_on_send_message(self._on_message_sent)
            
            # 订阅相关事件
            self._subscribe_events()
            
            logger.info("聊天视图初始化完成")
            
        except Exception as e:
            logger.error("聊天视图初始化失败", exc_info=True)
            raise UIError(f"聊天视图初始化失败: {e}")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # AI响应事件
        self._event_bus.subscribe("ai.response", self._on_ai_response)
        
        # AI错误事件
        self._event_bus.subscribe("ai.error", self._on_ai_error)
        
        # 配置更新事件
        self._event_bus.subscribe("config.updated", self._on_config_updated)
    
    def _on_message_sent(self, message_text: str, message: ChatMessage) -> None:
        """
        处理消息发送
        
        Args:
            message_text: 消息文本
            message: 消息对象
        """
        logger.debug_struct("处理消息发送", message_id=message.id, text_length=len(message_text))
        
        # 禁用输入（等待AI响应）
        self._chat_interface.disable_input()
        
        # 发布AI请求事件
        self._event_bus.publish("ai.request", {
            "message_id": message.id,
            "content": message_text,
            "timestamp": message.timestamp,
            "require_response": True
        })
    
    def _on_ai_response(self, event) -> None:
        """处理AI响应"""
        data = event.data
        content = data.get("content", "")
        request_id = data.get("request_id")
        
        logger.debug_struct("处理AI响应", request_id=request_id, content_length=len(content))
        
        # 添加助手响应
        self._chat_interface.add_assistant_response(content)
        
        # 重新启用输入
        self._chat_interface.enable_input()
        self._chat_interface.set_input_focus()
    
    def _on_ai_error(self, event) -> None:
        """处理AI错误"""
        data = event.data
        error_message = data.get("error", "未知错误")
        request_id = data.get("request_id")
        
        logger.warning_struct("处理AI错误", request_id=request_id, error=error_message)
        
        # 添加错误消息
        self._chat_interface.add_error_message(error_message)
        
        # 重新启用输入
        self._chat_interface.enable_input()
        self._chat_interface.set_input_focus()
    
    def _on_config_updated(self, event) -> None:
        """处理配置更新"""
        config_data = event.data.get("config", {})
        ui_config = config_data.get("ui", {})
        
        if "chat_history_limit" in ui_config:
            new_limit = ui_config["chat_history_limit"]
            self._chat_interface.max_history = new_limit
        
        if "markdown_render" in ui_config:
            self._chat_interface.enable_markdown = ui_config["markdown_render"]
        
        if "auto_scroll" in ui_config:
            self._chat_interface.auto_scroll = ui_config["auto_scroll"]
    
    def get_widget(self):
        """获取主框架"""
        return self._main_frame
    
    def get_chat_interface(self) -> ChatInterface:
        """获取聊天界面"""
        return self._chat_interface
    
    def get_status(self) -> Dict[str, Any]:
        """获取聊天视图状态"""
        if self._chat_interface:
            return self._chat_interface.get_status()
        return {"initialized": False}


# 导出
__all__ = [
    "MessageRole",
    "MessageStatus",
    "ChatMessage",
    "ChatInterface",
    "ChatView"
]