"""
依赖注入容器
提供轻量级的依赖管理功能
"""

import inspect
import threading
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, get_type_hints
from typing_extensions import Protocol

from .errors import DependencyError

T = TypeVar('T')

class ServiceProvider(Protocol):
    """服务提供者协议"""
    def get_service(self, service_type: Type[T]) -> T:
        """获取指定类型的服务实例"""
        ...


class Container:
    """
    依赖注入容器
    
    特性：
    - 支持接口到实现的注册
    - 支持单例和瞬态实例
    - 支持工厂函数
    - 自动依赖解析
    - 线程安全
    """
    
    def __init__(self):
        self._registrations: Dict[Type, Dict] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._logger = None  # 延迟初始化
    
    def _get_logger(self):
        """获取日志器（延迟初始化避免循环依赖）"""
        if self._logger is None:
            import logging
            self._logger = logging.getLogger(__name__)
        return self._logger
    
    def register(self, 
                interface: Type[T], 
                implementation: Optional[Type[T]] = None,
                factory: Optional[Callable[['Container'], T]] = None,
                singleton: bool = True) -> None:
        """
        注册服务
        
        Args:
            interface: 接口/抽象类型
            implementation: 实现类（如果为None，则使用interface作为实现）
            factory: 工厂函数（优先于implementation使用）
            singleton: 是否为单例
        """
        with self._lock:
            if implementation is None and factory is None:
                implementation = interface
            
            if interface in self._registrations:
                self._get_logger().warning(f"服务 {interface.__name__} 已注册，将被覆盖")
            
            self._registrations[interface] = {
                'implementation': implementation,
                'factory': factory,
                'singleton': singleton,
                'interface': interface
            }
            
            self._get_logger().debug(f"服务注册: {interface.__name__} -> "
                                   f"{implementation.__name__ if implementation else 'factory'} "
                                   f"(singleton: {singleton})")
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        注册服务实例
        
        Args:
            interface: 接口类型
            instance: 实例对象
        """
        with self._lock:
            self._singletons[interface] = instance
            
            # 也注册到registrations以便类型检查
            self._registrations[interface] = {
                'implementation': type(instance),
                'factory': None,
                'singleton': True,
                'interface': interface
            }
            
            self._get_logger().debug(f"服务实例注册: {interface.__name__} -> {type(instance).__name__}")
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
            
        Raises:
            DependencyError: 如果服务未注册或解析失败
        """
        with self._lock:
            # 首先检查是否已有单例实例
            if service_type in self._singletons:
                self._get_logger().debug(f"返回单例实例: {service_type.__name__}")
                return self._singletons[service_type]
            
            # 检查注册信息
            if service_type not in self._registrations:
                # 尝试自动注册（如果服务类型是具体类）
                if not inspect.isabstract(service_type) and service_type.__module__ != 'builtins':
                    self._get_logger().debug(f"自动注册具体类: {service_type.__name__}")
                    self.register(service_type, service_type, singleton=False)
                else:
                    raise DependencyError(
                        f"服务未注册: {service_type.__name__}",
                        service_name=service_type.__name__
                    )
            
            registration = self._registrations[service_type]
            
            try:
                # 创建实例
                if registration['factory'] is not None:
                    instance = registration['factory'](self)
                else:
                    implementation = registration['implementation']
                    if implementation is None:
                        raise DependencyError(
                            f"服务实现未指定: {service_type.__name__}",
                            service_name=service_type.__name__
                        )
                    
                    # 自动解析依赖并创建实例
                    instance = self._create_instance(implementation)
                
                # 如果是单例，保存实例
                if registration['singleton']:
                    self._singletons[service_type] = instance
                    self._get_logger().debug(f"创建单例实例: {service_type.__name__}")
                else:
                    self._get_logger().debug(f"创建瞬态实例: {service_type.__name__}")
                
                return instance
                
            except Exception as e:
                if isinstance(e, DependencyError):
                    raise e
                raise DependencyError(
                    f"服务解析失败: {service_type.__name__}",
                    service_name=service_type.__name__,
                    details=str(e)
                ) from e
    
    def _create_instance(self, cls: Type) -> Any:
        """
        创建类的实例，自动解析构造函数依赖
        
        Args:
            cls: 要实例化的类
            
        Returns:
            类的实例
        """
        # 获取构造函数的参数签名
        signature = inspect.signature(cls.__init__)
        parameters = signature.parameters
        
        # 准备参数
        args = {}
        
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue
            
            param_type = param.annotation
            
            # 跳过没有类型注解的参数
            if param_type == inspect.Parameter.empty:
                # 尝试从类型提示获取
                type_hints = get_type_hints(cls.__init__)
                if param_name in type_hints:
                    param_type = type_hints[param_name]
                else:
                    # 如果没有类型注解且没有默认值，使用None
                    if param.default == inspect.Parameter.empty:
                        args[param_name] = None
                    continue
            
            # 跳过可选参数
            if self._is_optional_type(param_type):
                # 提取实际类型
                import typing
                if hasattr(param_type, '__args__'):
                    inner_type = next((t for t in param_type.__args__ if t != type(None)), None)
                    if inner_type:
                        try:
                            args[param_name] = self.resolve(inner_type)
                        except DependencyError:
                            # 如果解析失败，使用None
                            args[param_name] = None
                    else:
                        args[param_name] = None
                else:
                    args[param_name] = None
                continue
            
            # 解析依赖
            try:
                args[param_name] = self.resolve(param_type)
            except DependencyError as e:
                # 如果有默认值，使用默认值
                if param.default != inspect.Parameter.empty:
                    args[param_name] = param.default
                else:
                    raise DependencyError(
                        f"无法解析依赖参数: {param_name}: {param_type.__name__}",
                        service_name=cls.__name__,
                        details=str(e)
                    )
        
        # 创建实例
        return cls(**args)
    
    def _is_optional_type(self, t: Any) -> bool:
        """检查是否为Optional类型"""
        import typing
        if hasattr(t, '__origin__') and t.__origin__ is Union:
            return type(None) in t.__args__
        return False
    
    def has_registration(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        with self._lock:
            return service_type in self._registrations
    
    def clear(self):
        """清除所有注册和单例实例"""
        with self._lock:
            self._registrations.clear()
            self._singletons.clear()
            self._get_logger().debug("容器已清除")
    
    def create_child(self) -> 'Container':
        """
        创建子容器
        
        Returns:
            子容器（继承父容器的注册但有自己的单例实例）
        """
        child = Container()
        
        with self._lock:
            # 复制注册信息（不复制单例实例）
            child._registrations = self._registrations.copy()
        
        child._get_logger().debug("创建子容器")
        return child
    
    def __contains__(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return self.has_registration(service_type)
    
    def __getitem__(self, service_type: Type[T]) -> T:
        """通过下标操作符解析服务"""
        return self.resolve(service_type)
    
    def __str__(self) -> str:
        """字符串表示"""
        with self._lock:
            service_count = len(self._registrations)
            singleton_count = len(self._singletons)
            return f"Container(services={service_count}, singletons={singleton_count})"


# 全局容器实例（可选）
_global_container: Optional[Container] = None

def get_global_container() -> Container:
    """获取全局容器实例（单例）"""
    global _global_container
    if _global_container is None:
        _global_container = Container()
    return _global_container

def set_global_container(container: Container) -> None:
    """设置全局容器实例"""
    global _global_container
    _global_container = container