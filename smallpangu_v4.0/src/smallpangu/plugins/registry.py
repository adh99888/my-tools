"""
插件注册表 - 插件管理和生命周期
"""

import threading
import time
from collections import defaultdict, deque
from typing import (
    Any, Dict, List, Optional, Set, Tuple, Type, Union
)

from .base import (
    PluginMetadata,
    PluginInfo,
    PluginStatus,
    PluginContext,
    Plugin
)
from .loader import PluginLoader
from ..core.errors import PluginError
from ..core.logging import get_logger

logger = get_logger(__name__)


class PluginRegistry:
    """
    插件注册表
    
    负责：
    1. 插件注册和注销
    2. 插件生命周期管理
    3. 插件依赖关系处理
    4. 插件状态跟踪
    5. 插件配置管理
    """
    
    def __init__(
        self,
        container: Any,
        event_bus: Any,
        config_manager: Any,
        plugin_loader: Optional[PluginLoader] = None
    ):
        """
        初始化插件注册表
        
        Args:
            container: 依赖注入容器
            event_bus: 事件总线
            config_manager: 配置管理器
            plugin_loader: 插件加载器（可选）
        """
        self.container = container
        self.event_bus = event_bus
        self.config_manager = config_manager
        
        # 插件加载器
        if plugin_loader is None:
            from .loader import create_plugin_loader
            plugin_loader = create_plugin_loader()
        self.plugin_loader = plugin_loader
        
        # 插件存储
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_contexts: Dict[str, PluginContext] = {}
        
        # 依赖关系
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)  # 插件 -> 依赖的插件
        self._dependents: Dict[str, Set[str]] = defaultdict(set)    # 插件 -> 被哪些插件依赖
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.debug_struct("插件注册表初始化")
    
    def register_plugin(self, metadata: PluginMetadata) -> PluginInfo:
        """
        注册插件
        
        Args:
            metadata: 插件元数据
            
        Returns:
            插件信息
        """
        with self._lock:
            plugin_name = metadata.name
            
            # 检查是否已注册
            if plugin_name in self._plugins:
                logger.debug_struct(
                    "插件已注册，跳过",
                    name=plugin_name
                )
                return self._plugins[plugin_name]
            
            logger.debug_struct(
                "注册插件",
                name=plugin_name,
                type=metadata.plugin_type.value,
                version=metadata.version
            )
            
            # 创建插件信息
            plugin_info = PluginInfo(
                metadata=metadata,
                status=PluginStatus.REGISTERED
            )
            
            # 存储插件信息
            self._plugins[plugin_name] = plugin_info
            
            # 更新依赖关系
            self._update_dependencies(plugin_name, metadata.dependencies)
            
            # 创建插件上下文
            context = self._create_plugin_context(plugin_name, metadata)
            self._plugin_contexts[plugin_name] = context
            
            # 发布插件注册事件
            self._publish_plugin_event(
                "plugin.registered",
                plugin_name,
                {"metadata": metadata}
            )
            
            logger.info_struct(
                "插件注册成功",
                name=plugin_name,
                display_name=metadata.display_name
            )
            
            return plugin_info
    
    def _update_dependencies(self, plugin_name: str, dependencies: List[str]):
        """更新依赖关系"""
        # 清除旧的依赖关系
        old_deps = self._dependencies.get(plugin_name, set())
        for dep in old_deps:
            if dep in self._dependents:
                self._dependents[dep].discard(plugin_name)
        
        # 设置新的依赖关系
        self._dependencies[plugin_name] = set(dependencies)
        for dep in dependencies:
            self._dependents[dep].add(plugin_name)
    
    def _create_plugin_context(
        self,
        plugin_name: str,
        metadata: PluginMetadata
    ) -> PluginContext:
        """创建插件上下文"""
        # 获取插件配置
        plugin_config = self._get_plugin_config(plugin_name, metadata)
        
        # 创建上下文
        context = PluginContext(
            plugin_name=plugin_name,
            config_manager=self.config_manager,
            event_bus=self.event_bus,
            container=self.container,
            plugin_config=plugin_config
        )
        
        return context
    
    def _get_plugin_config(
        self,
        plugin_name: str,
        metadata: PluginMetadata
    ) -> Dict[str, Any]:
        """获取插件配置"""
        # 从配置管理器获取插件配置
        config_key = f"plugins.{plugin_name}"
        config = self.config_manager.get_value(config_key, {})
        
        # 合并默认配置
        if metadata.default_config:
            default_config = metadata.default_config.copy()
            default_config.update(config)
            config = default_config
        
        return config
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if plugin_name not in self._plugins:
                logger.warning_struct(
                    "插件未注册，无法注销",
                    name=plugin_name
                )
                return False
            
            plugin_info = self._plugins[plugin_name]
            
            # 检查插件状态
            if plugin_info.status == PluginStatus.STARTED:
                logger.warning_struct(
                    "插件正在运行，请先停止",
                    name=plugin_name,
                    status=plugin_info.status.value
                )
                return False
            
            # 清理依赖关系
            if plugin_name in self._dependencies:
                deps = self._dependencies[plugin_name]
                for dep in deps:
                    if dep in self._dependents:
                        self._dependents[dep].discard(plugin_name)
                del self._dependencies[plugin_name]
            
            if plugin_name in self._dependents:
                dependents = self._dependents[plugin_name]
                for dependent in dependents:
                    if dependent in self._dependencies:
                        self._dependencies[dependent].discard(plugin_name)
                del self._dependents[plugin_name]
            
            # 清理上下文
            if plugin_name in self._plugin_contexts:
                del self._plugin_contexts[plugin_name]
            
            # 移除插件信息
            del self._plugins[plugin_name]
            
            # 发布插件注销事件
            self._publish_plugin_event(
                "plugin.unregistered",
                plugin_name,
                {"plugin_name": plugin_name}
            )
            
            logger.info_struct(
                "插件注销成功",
                name=plugin_name
            )
            
            return True
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        with self._lock:
            return self._plugins.get(plugin_name)
    
    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件信息"""
        with self._lock:
            return list(self._plugins.values())
    
    def get_running_plugins(self) -> List[PluginInfo]:
        """获取正在运行的插件"""
        with self._lock:
            return [
                plugin for plugin in self._plugins.values()
                if plugin.status == PluginStatus.STARTED
            ]
    
    def get_plugin_context(self, plugin_name: str) -> Optional[PluginContext]:
        """获取插件上下文"""
        with self._lock:
            return self._plugin_contexts.get(plugin_name)
    
    def initialize_plugin(self, plugin_name: str) -> bool:
        """
        初始化插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功初始化
        """
        with self._lock:
            plugin_info = self._get_plugin_for_operation(plugin_name, "initialize")
            if plugin_info is None:
                return False
            
            if plugin_info.status != PluginStatus.REGISTERED:
                logger.warning_struct(
                    "插件状态不适合初始化",
                    name=plugin_name,
                    current_status=plugin_info.status.value,
                    expected_status=PluginStatus.REGISTERED.value
                )
                return False
            
            try:
                # 检查依赖
                missing_deps = self._check_dependencies(plugin_name)
                if missing_deps:
                    logger.error_struct(
                        "插件依赖缺失",
                        name=plugin_name,
                        missing_dependencies=missing_deps
                    )
                    return False
                
                # 创建插件实例
                context = self._plugin_contexts[plugin_name]
                plugin_instance = self.plugin_loader.create_plugin_instance(
                    plugin_name,
                    context
                )
                plugin_info.instance = plugin_instance
                
                # 初始化插件
                plugin_instance.initialize()
                plugin_info.status = PluginStatus.INITIALIZED
                
                # 发布插件初始化事件
                self._publish_plugin_event(
                    "plugin.initialized",
                    plugin_name,
                    {"plugin_name": plugin_name}
                )
                
                logger.info_struct(
                    "插件初始化成功",
                    name=plugin_name
                )
                
                return True
                
            except Exception as e:
                self._handle_plugin_error(plugin_info, e, "初始化")
                return False
    
    def start_plugin(self, plugin_name: str) -> bool:
        """
        启动插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功启动
        """
        with self._lock:
            plugin_info = self._get_plugin_for_operation(plugin_name, "start")
            if plugin_info is None:
                return False
            
            if plugin_info.status != PluginStatus.INITIALIZED:
                logger.warning_struct(
                    "插件状态不适合启动",
                    name=plugin_name,
                    current_status=plugin_info.status.value,
                    expected_status=PluginStatus.INITIALIZED.value
                )
                return False
            
            try:
                # 检查依赖插件是否已启动
                unstarted_deps = self._check_dependency_status(
                    plugin_name,
                    PluginStatus.STARTED
                )
                if unstarted_deps:
                    logger.warning_struct(
                        "插件依赖未启动",
                        name=plugin_name,
                        unstarted_dependencies=unstarted_deps
                    )
                    # 可以尝试自动启动依赖，这里暂时返回失败
                    return False
                
                # 启动插件
                plugin_info.instance.start()
                plugin_info.status = PluginStatus.STARTED
                plugin_info.startup_time = time.time()
                plugin_info.stop_time = None
                
                # 发布插件启动事件
                self._publish_plugin_event(
                    "plugin.started",
                    plugin_name,
                    {"plugin_name": plugin_name}
                )
                
                logger.info_struct(
                    "插件启动成功",
                    name=plugin_name
                )
                
                return True
                
            except Exception as e:
                self._handle_plugin_error(plugin_info, e, "启动")
                return False
    
    def stop_plugin(self, plugin_name: str) -> bool:
        """
        停止插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功停止
        """
        with self._lock:
            plugin_info = self._get_plugin_for_operation(plugin_name, "stop")
            if plugin_info is None:
                return False
            
            if plugin_info.status != PluginStatus.STARTED:
                logger.warning_struct(
                    "插件未运行，无需停止",
                    name=plugin_name,
                    current_status=plugin_info.status.value
                )
                return True  # 已经停止，返回成功
            
            try:
                # 检查是否有其他插件依赖此插件
                blocking_dependents = self._check_dependents_status(
                    plugin_name,
                    PluginStatus.STARTED
                )
                if blocking_dependents:
                    logger.warning_struct(
                        "有插件依赖此插件，无法停止",
                        name=plugin_name,
                        blocking_dependents=blocking_dependents
                    )
                    return False
                
                # 停止插件
                plugin_info.instance.stop()
                plugin_info.status = PluginStatus.STOPPED
                plugin_info.stop_time = time.time()
                
                # 发布插件停止事件
                self._publish_plugin_event(
                    "plugin.stopped",
                    plugin_name,
                    {"plugin_name": plugin_name}
                )
                
                logger.info_struct(
                    "插件停止成功",
                    name=plugin_name
                )
                
                return True
                
            except Exception as e:
                self._handle_plugin_error(plugin_info, e, "停止")
                return False
    
    def shutdown_plugin(self, plugin_name: str) -> bool:
        """
        关闭插件（完全清理）
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否成功关闭
        """
        with self._lock:
            plugin_info = self._get_plugin_for_operation(plugin_name, "shutdown")
            if plugin_info is None:
                return False
            
            try:
                # 如果插件正在运行，先停止
                if plugin_info.status == PluginStatus.STARTED:
                    self.stop_plugin(plugin_name)
                
                # 关闭插件
                if plugin_info.instance:
                    plugin_info.instance.shutdown()
                
                # 重置状态
                plugin_info.status = PluginStatus.REGISTERED
                plugin_info.instance = None
                plugin_info.error = None
                plugin_info.startup_time = None
                plugin_info.stop_time = None
                
                # 发布插件关闭事件
                self._publish_plugin_event(
                    "plugin.shutdown",
                    plugin_name,
                    {"plugin_name": plugin_name}
                )
                
                logger.info_struct(
                    "插件关闭成功",
                    name=plugin_name
                )
                
                return True
                
            except Exception as e:
                self._handle_plugin_error(plugin_info, e, "关闭")
                return False
    
    def start_all_plugins(self) -> Dict[str, bool]:
        """
        启动所有已注册的插件
        
        Returns:
            插件启动结果字典
        """
        with self._lock:
            # 拓扑排序，按依赖顺序启动
            sorted_plugins = self._topological_sort()
            
            results = {}
            for plugin_name in sorted_plugins:
                if plugin_name in self._plugins:
                    success = self.start_plugin(plugin_name)
                    results[plugin_name] = success
            
            logger.info_struct(
                "所有插件启动完成",
                total_count=len(results),
                success_count=sum(1 for r in results.values() if r),
                failure_count=sum(1 for r in results.values() if not r)
            )
            
            return results
    
    def stop_all_plugins(self) -> Dict[str, bool]:
        """
        停止所有插件
        
        Returns:
            插件停止结果字典
        """
        with self._lock:
            # 逆拓扑排序，先停止依赖其他插件的插件
            sorted_plugins = self._topological_sort(reverse=True)
            
            results = {}
            for plugin_name in sorted_plugins:
                if plugin_name in self._plugins:
                    success = self.stop_plugin(plugin_name)
                    results[plugin_name] = success
            
            logger.info_struct(
                "所有插件停止完成",
                total_count=len(results),
                success_count=sum(1 for r in results.values() if r),
                failure_count=sum(1 for r in results.values() if not r)
            )
            
            return results
    
    def shutdown_all_plugins(self) -> Dict[str, bool]:
        """
        关闭所有插件
        
        Returns:
            插件关闭结果字典
        """
        with self._lock:
            results = {}
            for plugin_name in list(self._plugins.keys()):
                success = self.shutdown_plugin(plugin_name)
                results[plugin_name] = success
            
            logger.info_struct(
                "所有插件关闭完成",
                total_count=len(results),
                success_count=sum(1 for r in results.values() if r),
                failure_count=sum(1 for r in results.values() if not r)
            )
            
            return results
    
    def _topological_sort(self, reverse: bool = False) -> List[str]:
        """拓扑排序插件（考虑依赖关系）"""
        # Kahn's algorithm
        indegree = {}
        graph = defaultdict(list)
        
        # 构建图
        for plugin_name in self._plugins:
            indegree[plugin_name] = 0
        
        for plugin_name, deps in self._dependencies.items():
            if plugin_name in self._plugins:
                for dep in deps:
                    if dep in self._plugins:
                        graph[dep].append(plugin_name)
                        indegree[plugin_name] += 1
        
        # 找到入度为0的节点
        queue = deque([p for p, d in indegree.items() if d == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有环
        if len(result) != len(self._plugins):
            logger.warning_struct(
                "插件依赖关系可能存在环",
                sorted_count=len(result),
                total_count=len(self._plugins)
            )
            # 返回所有插件（不保证顺序）
            result = list(self._plugins.keys())
        
        if reverse:
            result.reverse()
        
        return result
    
    def _check_dependencies(self, plugin_name: str) -> List[str]:
        """检查插件依赖是否满足"""
        dependencies = self._dependencies.get(plugin_name, set())
        missing = []
        
        for dep in dependencies:
            if dep not in self._plugins:
                missing.append(dep)
        
        return missing
    
    def _check_dependency_status(
        self,
        plugin_name: str,
        required_status: PluginStatus
    ) -> List[str]:
        """检查依赖插件的状态"""
        dependencies = self._dependencies.get(plugin_name, set())
        unready = []
        
        for dep in dependencies:
            if dep in self._plugins:
                plugin_info = self._plugins[dep]
                if plugin_info.status != required_status:
                    unready.append(f"{dep}({plugin_info.status.value})")
        
        return unready
    
    def _check_dependents_status(
        self,
        plugin_name: str,
        blocking_status: PluginStatus
    ) -> List[str]:
        """检查依赖此插件的插件状态"""
        dependents = self._dependents.get(plugin_name, set())
        blocking = []
        
        for dep in dependents:
            if dep in self._plugins:
                plugin_info = self._plugins[dep]
                if plugin_info.status == blocking_status:
                    blocking.append(f"{dep}({plugin_info.status.value})")
        
        return blocking
    
    def _get_plugin_for_operation(
        self,
        plugin_name: str,
        operation: str
    ) -> Optional[PluginInfo]:
        """获取插件信息并进行基本检查"""
        if plugin_name not in self._plugins:
            logger.error_struct(
                f"插件{operation}失败：插件未注册",
                name=plugin_name
            )
            return None
        
        plugin_info = self._plugins[plugin_name]
        
        if plugin_info.status == PluginStatus.ERROR:
            logger.warning_struct(
                f"插件{operation}失败：插件处于错误状态",
                name=plugin_name,
                error=plugin_info.error
            )
            return None
        
        return plugin_info
    
    def _handle_plugin_error(
        self,
        plugin_info: PluginInfo,
        error: Exception,
        operation: str
    ):
        """处理插件错误"""
        plugin_name = plugin_info.name
        error_msg = str(error)
        
        plugin_info.status = PluginStatus.ERROR
        plugin_info.error = error_msg
        
        logger.error_struct(
            f"插件{operation}失败",
            name=plugin_name,
            error=error_msg,
            exc_info=True
        )
        
        # 发布插件错误事件
        self._publish_plugin_event(
            "plugin.error",
            plugin_name,
            {
                "plugin_name": plugin_name,
                "operation": operation,
                "error": error_msg
            }
        )
    
    def _publish_plugin_event(
        self,
        event_type: str,
        plugin_name: str,
        data: Dict[str, Any]
    ):
        """发布插件事件"""
        if self.event_bus:
            from ..core.events import Event
            event = Event(
                event_type=event_type,
                data={
                    "plugin": plugin_name,
                    "timestamp": time.time(),
                    **data
                },
                source=f"plugin_registry.{plugin_name}"
            )
            self.event_bus.publish(event.type, event.data, event.source)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取插件注册表状态摘要"""
        with self._lock:
            total = len(self._plugins)
            status_counts = defaultdict(int)
            
            for plugin_info in self._plugins.values():
                status_counts[plugin_info.status.value] += 1
            
            return {
                "total_plugins": total,
                "status_counts": dict(status_counts),
                "running_plugins": len(self.get_running_plugins()),
                "plugin_names": list(self._plugins.keys())
            }
    
    def clear(self):
        """清空注册表（用于测试）"""
        with self._lock:
            self._plugins.clear()
            self._plugin_contexts.clear()
            self._dependencies.clear()
            self._dependents.clear()
            logger.debug_struct("插件注册表已清空")


# 便捷函数
def create_plugin_registry(
    container: Any,
    event_bus: Any,
    config_manager: Any,
    plugin_loader: Optional[PluginLoader] = None
) -> PluginRegistry:
    """
    创建插件注册表
    
    Args:
        container: 依赖注入容器
        event_bus: 事件总线
        config_manager: 配置管理器
        plugin_loader: 插件加载器
        
    Returns:
        插件注册表实例
    """
    return PluginRegistry(
        container=container,
        event_bus=event_bus,
        config_manager=config_manager,
        plugin_loader=plugin_loader
    )


__all__ = [
    "PluginRegistry",
    "create_plugin_registry"
]