"""
插件基类和协议定义
"""

import abc
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Callable, ClassVar, Dict, List, Optional, Set, Type, Union,
    TYPE_CHECKING
)
from uuid import uuid4

if TYPE_CHECKING:
    from ..config.manager import ConfigManager
    from ..core.events import EventBus, Event
    from ..core.di import Container


class PluginType(str, Enum):
    """插件类型枚举"""
    TOOL = "tool"           # 工具插件（提供具体功能）
    AI_PROVIDER = "ai_provider"  # AI提供商插件
    UI_COMPONENT = "ui_component"  # UI组件插件
    INTEGRATION = "integration"  # 集成插件（第三方服务）
    STORAGE = "storage"     # 存储插件
    ANALYTICS = "analytics"  # 分析插件
    CUSTOM = "custom"       # 自定义插件


class PluginStatus(str, Enum):
    """插件状态枚举"""
    REGISTERED = "registered"  # 已注册但未初始化
    INITIALIZED = "initialized"  # 已初始化
    STARTED = "started"      # 已启动（运行中）
    STOPPED = "stopped"      # 已停止
    ERROR = "error"          # 错误状态
    DISABLED = "disabled"    # 已禁用


@dataclass
class PluginMetadata:
    """插件元数据"""
    
    # 基本信息（无默认值字段必须在前）
    name: str                       # 插件名称（唯一标识）
    display_name: str               # 显示名称
    version: str                    # 版本号
    description: str                # 插件描述
    author: str                     # 作者
    plugin_type: PluginType         # 插件类型
    
    # 基本信息（有默认值）
    license: str = "MIT"            # 许可证
    tags: List[str] = field(default_factory=list)  # 标签
    
    # 依赖信息
    dependencies: List[str] = field(default_factory=list)  # 依赖的插件名称
    python_dependencies: List[str] = field(default_factory=list)  # Python包依赖
    
    # 兼容性信息
    min_app_version: str = "4.0.0"  # 最小应用版本
    max_app_version: str = "*"      # 最大应用版本
    
    # 配置信息
    config_schema: Optional[Dict[str, Any]] = None  # 配置模式（JSON Schema）
    default_config: Optional[Dict[str, Any]] = None  # 默认配置
    admin_config: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "category": "plugin",
        "icon": None,
        "priority": 100,
        "reload_strategy": "restart",
        "show_in_admin": True
    })  # 管理后台配置
    
    # 运行时信息
    plugin_class: Optional[Type["Plugin"]] = None  # 插件类
    module_path: Optional[str] = None  # 模块路径


@dataclass
class PluginInfo:
    """插件运行时信息"""
    
    metadata: PluginMetadata         # 插件元数据
    status: PluginStatus            # 当前状态
    instance: Optional["Plugin"] = None  # 插件实例
    error: Optional[str] = None     # 错误信息
    
    # 运行时数据
    startup_time: Optional[float] = None  # 启动时间戳
    stop_time: Optional[float] = None    # 停止时间戳
    
    @property
    def name(self) -> str:
        """插件名称"""
        return self.metadata.name
    
    @property
    def is_enabled(self) -> bool:
        """插件是否启用"""
        return self.status != PluginStatus.DISABLED
    
    @property
    def is_running(self) -> bool:
        """插件是否正在运行"""
        return self.status == PluginStatus.STARTED
    
    @property
    def has_error(self) -> bool:
        """插件是否有错误"""
        return self.status == PluginStatus.ERROR


class PluginContext:
    """
    插件上下文
    
    提供插件运行时需要的所有资源和接口
    """
    
    def __init__(
        self,
        plugin_name: str,
        config_manager: "ConfigManager",
        event_bus: "EventBus",
        container: "Container",
        plugin_config: Optional[Dict[str, Any]] = None
    ):
        self.plugin_name = plugin_name
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.container = container
        self.plugin_config = plugin_config or {}
        
        # 插件特定资源
        self._resources: Dict[str, Any] = {}
        self._logger = logging.getLogger(f"plugin.{plugin_name}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self.plugin_config.copy()
    
    @property
    def logger(self) -> logging.Logger:
        """获取插件专用日志器"""
        return self._logger
    
    def get_resource(self, key: str, default: Any = None) -> Any:
        """获取插件资源"""
        return self._resources.get(key, default)
    
    def set_resource(self, key: str, value: Any):
        """设置插件资源"""
        self._resources[key] = value
    
    def remove_resource(self, key: str) -> bool:
        """移除插件资源"""
        if key in self._resources:
            del self._resources[key]
            return True
        return False
    
    def get_app_config(self, key: str, default: Any = None) -> Any:
        """获取应用配置值"""
        return self.config_manager.get_value(key, default)
    
    def publish_event(self, event_type: str, data: Dict[str, Any] = None):
        """发布事件"""
        from ..core.events import Event
        event = Event(
            type=event_type,
            data=data or {},
            source=self.plugin_name
        )
        self.event_bus.publish(event)
    
    def subscribe_event(
        self,
        event_pattern: str,
        handler: Callable[["Event"], None],
        priority: int = 0
    ) -> str:
        """订阅事件"""
        return self.event_bus.subscribe(event_pattern, handler, priority)
    
    def unsubscribe_event(self, subscription_id: str) -> bool:
        """取消订阅事件"""
        return self.event_bus.unsubscribe(subscription_id)
    
    def resolve_dependency(self, service_type: Type) -> Any:
        """解析依赖（从容器中获取服务实例）"""
        return self.container.resolve(service_type)
    
    def register_service(
        self,
        service_type: Type,
        implementation: Any,
        singleton: bool = True
    ):
        """注册服务到容器"""
        self.container.register(service_type, implementation, singleton)
    
    def __str__(self) -> str:
        return f"PluginContext({self.plugin_name})"


class Plugin(ABC):
    """
    插件基类
    
    所有插件必须继承此类并实现必要的方法
    """
    
    # 类属性 - 由子类定义
    metadata: ClassVar[PluginMetadata]
    
    def __init__(self, context: PluginContext):
        self.context = context
        self._subscriptions: List[str] = []
        self._is_initialized = False
        self._is_started = False
        
        # 自动设置插件名称
        if not hasattr(self, 'name'):
            self.name = self.metadata.name
    
    @property
    def logger(self) -> logging.Logger:
        """获取插件日志器"""
        return self.context.logger
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self.context.config
    
    @property
    def is_initialized(self) -> bool:
        """插件是否已初始化"""
        return self._is_initialized
    
    @property
    def is_started(self) -> bool:
        """插件是否已启动"""
        return self._is_started
    
    def initialize(self) -> None:
        """
        初始化插件
        
        在此方法中执行一次性初始化操作，如：
        - 解析配置
        - 注册服务到容器
        - 准备资源
        """
        if self._is_initialized:
            self.logger.warning("插件已初始化，跳过重复初始化")
            return
        
        try:
            self.logger.debug("开始初始化插件")
            self.on_initialize()
            self._is_initialized = True
            self.logger.info("插件初始化完成")
        except Exception as e:
            self.logger.error(f"插件初始化失败: {e}", exc_info=True)
            raise
    
    def start(self) -> None:
        """
        启动插件
        
        在此方法中执行启动操作，如：
        - 启动后台任务
        - 订阅事件
        - 连接外部服务
        """
        if not self._is_initialized:
            raise RuntimeError("插件未初始化，无法启动")
        
        if self._is_started:
            self.logger.warning("插件已启动，跳过重复启动")
            return
        
        try:
            self.logger.debug("开始启动插件")
            self.on_start()
            self._is_started = True
            self.logger.info("插件启动完成")
        except Exception as e:
            self.logger.error(f"插件启动失败: {e}", exc_info=True)
            raise
    
    def stop(self) -> None:
        """
        停止插件
        
        在此方法中执行清理操作，如：
        - 停止后台任务
        - 取消事件订阅
        - 断开外部连接
        """
        if not self._is_started:
            self.logger.warning("插件未启动，无需停止")
            return
        
        try:
            self.logger.debug("开始停止插件")
            self.on_stop()
            self._cleanup_subscriptions()
            self._is_started = False
            self.logger.info("插件停止完成")
        except Exception as e:
            self.logger.error(f"插件停止失败: {e}", exc_info=True)
            raise
    
    def shutdown(self) -> None:
        """
        关闭插件（完全清理）
        
        在此方法中执行最终清理操作
        """
        try:
            if self._is_started:
                self.stop()
            
            self.logger.debug("开始关闭插件")
            self.on_shutdown()
            self._is_initialized = False
            self.logger.info("插件关闭完成")
        except Exception as e:
            self.logger.error(f"插件关闭失败: {e}", exc_info=True)
            raise
    
    # 生命周期钩子方法（子类可重写）
    def on_initialize(self) -> None:
        """初始化钩子（可选）"""
        pass
    
    def on_start(self) -> None:
        """启动钩子（必需）"""
        raise NotImplementedError("插件必须实现on_start方法")
    
    def on_stop(self) -> None:
        """停止钩子（可选）"""
        pass
    
    def on_shutdown(self) -> None:
        """关闭钩子（可选）"""
        pass
    
    # 工具方法
    def get_app_config(self, key: str, default: Any = None) -> Any:
        """获取应用配置值"""
        return self.context.get_app_config(key, default)
    
    def publish_event(self, event_type: str, data: Dict[str, Any] = None):
        """发布事件"""
        self.context.publish_event(event_type, data)
    
    def subscribe_event(
        self,
        event_pattern: str,
        handler: Callable[["Event"], None],
        priority: int = 0
    ) -> str:
        """订阅事件并记录订阅ID"""
        subscription_id = self.context.subscribe_event(event_pattern, handler, priority)
        self._subscriptions.append(subscription_id)
        return subscription_id
    
    def unsubscribe_event(self, subscription_id: str) -> bool:
        """取消订阅事件"""
        success = self.context.unsubscribe_event(subscription_id)
        if success and subscription_id in self._subscriptions:
            self._subscriptions.remove(subscription_id)
        return success
    
    def resolve_dependency(self, service_type: Type) -> Any:
        """解析依赖"""
        return self.context.resolve_dependency(service_type)
    
    def register_service(
        self,
        service_type: Type,
        implementation: Any,
        singleton: bool = True
    ):
        """注册服务"""
        self.context.register_service(service_type, implementation, singleton)
    
    def _cleanup_subscriptions(self):
        """清理所有事件订阅"""
        for subscription_id in self._subscriptions[:]:
            self.context.unsubscribe_event(subscription_id)
        self._subscriptions.clear()
    
    def __str__(self) -> str:
        return f"Plugin({self.name})"


# 插件协议定义（用于类型检查和静态分析）
class ToolPlugin(Plugin):
    """工具插件协议"""
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具操作"""
        pass
    
    @property
    @abstractmethod
    def tool_schema(self) -> Dict[str, Any]:
        """工具模式定义（OpenAI函数调用格式）"""
        pass


class AIProviderPlugin(Plugin):
    """AI提供商插件协议"""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """生成AI响应"""
        pass
    
    @property
    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        """模型信息"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """支持的 capabilities"""
        pass


class UIPlugin(Plugin):
    """UI插件协议"""
    
    @abstractmethod
    def create_widget(self, parent, **kwargs) -> Any:
        """创建UI组件"""
        pass
    
    @abstractmethod
    def update_widget(self, widget, data: Dict[str, Any]):
        """更新UI组件"""
        pass


# 插件工厂函数
def create_plugin_metadata(
    name: str,
    display_name: str,
    version: str,
    description: str,
    author: str,
    plugin_type: PluginType,
    **kwargs
) -> PluginMetadata:
    """创建插件元数据"""
    return PluginMetadata(
        name=name,
        display_name=display_name,
        version=version,
        description=description,
        author=author,
        plugin_type=plugin_type,
        **kwargs
    )


# 插件装饰器（用于简化插件定义）
def plugin(
    name: str,
    display_name: str,
    version: str,
    description: str,
    author: str,
    plugin_type: PluginType,
    **metadata_kwargs
):
    """
    插件类装饰器
    
    用法：
    @plugin(
        name="my_plugin",
        display_name="我的插件",
        version="1.0.0",
        description="插件描述",
        author="作者",
        plugin_type=PluginType.TOOL
    )
    class MyPlugin(Plugin):
        ...
    """
    def decorator(cls: Type[Plugin]) -> Type[Plugin]:
        metadata = create_plugin_metadata(
            name=name,
            display_name=display_name,
            version=version,
            description=description,
            author=author,
            plugin_type=plugin_type,
            **metadata_kwargs
        )
        metadata.plugin_class = cls
        cls.metadata = metadata
        return cls
    return decorator


__all__ = [
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginInfo",
    "PluginContext",
    "Plugin",
    "ToolPlugin",
    "AIProviderPlugin",
    "UIPlugin",
    "create_plugin_metadata",
    "plugin"
]