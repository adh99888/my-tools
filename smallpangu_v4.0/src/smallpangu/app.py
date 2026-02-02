"""
应用主类 - 小盘古应用的核心管理器
"""

import asyncio
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from .config.manager import ConfigManager, get_config_manager
from .core.events import EventBus
from .core.di import Container
from .core.logging import get_logger, setup_logging
from .core.errors import AppError

# 插件系统将延迟导入
PluginLoader = None
PluginRegistry = None

logger = get_logger(__name__)


class SmallPanguApp:
    """
    小盘古应用主类
    
    管理整个应用的生命周期，包括：
    1. 配置管理
    2. 事件总线
    3. 依赖注入容器
    4. 插件系统
    5. 应用状态
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化应用
        
        Args:
            config_path: 配置文件路径（可选）
        """
        self._config_path = config_path
        self._is_initialized = False
        self._is_running = False
        self._is_shutting_down = False
        
        # 核心组件
        self._config_manager: Optional[ConfigManager] = None
        self._event_bus: Optional[EventBus] = None
        self._container: Optional[Container] = None
        self._plugin_loader = None
        self._plugin_registry = None
        
        # 应用状态
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        
        # 信号处理
        self._setup_signal_handlers()
        
        logger.debug_struct("应用实例已创建", config_path=config_path)
    
    def _setup_signal_handlers(self):
        """设置信号处理"""
        try:
            signal.signal(signal.SIGINT, self._handle_shutdown_signal)
            signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        except (AttributeError, ValueError):
            # Windows可能不支持某些信号
            pass
    
    def _handle_shutdown_signal(self, signum, frame):
        """处理关闭信号"""
        logger.info(f"收到关闭信号 {signum}，开始优雅关闭")
        self.shutdown()
    
    def initialize(self, config_path: Optional[str] = None) -> None:
        """
        初始化应用
        
        Args:
            config_path: 配置文件路径（覆盖构造函数中的路径）
        """
        if self._is_initialized:
            logger.warning("应用已初始化，跳过重复初始化")
            return
        
        logger.info("开始初始化应用")
        start_time = time.time()
        
        try:
            # 确定配置路径
            final_config_path = config_path or self._config_path
            
            # 1. 初始化配置管理器
            self._initialize_config_manager(final_config_path)
            
            # 2. 设置日志系统（基于配置）
            self._setup_logging()
            
            # 3. 初始化事件总线
            self._initialize_event_bus()
            
            # 4. 初始化依赖注入容器
            self._initialize_container()
            
            # 5. 初始化插件系统
            self._initialize_plugin_system()
            
            # 6. 注册核心服务到容器
            self._register_core_services()
            
            self._is_initialized = True
            elapsed = time.time() - start_time
            logger.info(f"应用初始化完成，耗时 {elapsed:.2f} 秒")
            
        except Exception as e:
            logger.error("应用初始化失败", exc_info=True)
            raise AppError(f"应用初始化失败: {e}")
    
    def _initialize_config_manager(self, config_path: Optional[str]):
        """初始化配置管理器"""
        logger.debug("初始化配置管理器")
        
        # 启用热重载（根据环境配置决定）
        enable_hot_reload = False
        
        self._config_manager = get_config_manager(
            config_path=config_path,
            enable_hot_reload=enable_hot_reload,
            event_bus=None  # 此时事件总线还未创建
        )
        
        # 验证配置
        errors = self._config_manager.validate_current_config()
        if errors:
            for error in errors:
                logger.warning(f"配置验证警告: {error}")
        
        logger.info_struct(
            "配置管理器初始化成功",
            environment=self._config_manager.environment
        )
    
    def _setup_logging(self):
        """设置日志系统"""
        logger.debug("设置日志系统")
        
        # 从配置获取日志设置
        config = self._config_manager.config
        
        # 这里可以调用core.logging.setup_logging进行更详细的配置
        # 目前依赖自动设置
        
        logger.debug("日志系统已设置")
    
    def _initialize_event_bus(self):
        """初始化事件总线"""
        logger.debug("初始化事件总线")
        
        from .core.events import EventBus
        
        event_bus_config = self._config_manager.config.event_bus
        self._event_bus = EventBus(
            max_queue_size=event_bus_config.max_queue_size,
            worker_threads=event_bus_config.worker_threads,
            enable_debug_log=event_bus_config.enable_debug_log
        )
        
        logger.info_struct(
            "事件总线初始化成功",
            max_queue_size=event_bus_config.max_queue_size,
            worker_threads=event_bus_config.worker_threads
        )
    
    def _initialize_container(self):
        """初始化依赖注入容器"""
        logger.debug("初始化依赖注入容器")
        
        from .core.di import Container
        
        self._container = Container()
        
        # 注册核心实例到容器
        self._container.register_instance(ConfigManager, self._config_manager)
        self._container.register_instance(EventBus, self._event_bus)
        self._container.register_instance(Container, self._container)
        self._container.register_instance(SmallPanguApp, self)
        
        logger.info("依赖注入容器初始化成功")
    
    def _initialize_plugin_system(self):
        """初始化插件系统"""
        logger.debug("初始化插件系统")
        
        # 延迟导入插件模块
        try:
            from .plugins.loader import PluginLoader
            from .plugins.registry import PluginRegistry
            
            # 创建插件加载器和注册表
            plugin_config = self._config_manager.config.plugins
            
            self._plugin_loader = PluginLoader(
                search_paths=plugin_config.search_paths,
                container=self._container
            )
            
            self._plugin_registry = PluginRegistry(
                container=self._container,
                event_bus=self._event_bus,
                config_manager=self._config_manager
            )
            
            logger.info_struct(
                "插件系统初始化成功",
                search_paths=plugin_config.search_paths,
                loading_strategy=plugin_config.loading_strategy
            )
            
        except ImportError as e:
            logger.warning(f"插件系统模块未找到，跳过插件初始化: {e}")
            self._plugin_loader = None
            self._plugin_registry = None
    
    def _register_core_services(self):
        """注册核心服务到容器"""
        logger.debug("注册核心服务到容器")
        
        # 这里可以注册更多核心服务
        # 例如：AI服务管理器、工具管理器等
        
        logger.debug("核心服务注册完成")
    
    def load_plugins(self) -> None:
        """加载插件"""
        if not self._plugin_loader or not self._plugin_registry:
            logger.warning("插件系统未初始化，跳过插件加载")
            return
        
        logger.info("开始加载插件")
        
        try:
            # 从配置获取启用的插件列表
            enabled_plugins = self._config_manager.config.plugins.enabled
            
            # 发现插件
            discovered_plugins = self._plugin_loader.discover_plugins()
            logger.info(f"发现 {len(discovered_plugins)} 个插件")
            
            # 注册插件
            for plugin_metadata in discovered_plugins:
                if plugin_metadata.name in enabled_plugins:
                    self._plugin_registry.register_plugin(plugin_metadata)
                    logger.debug(f"插件已注册: {plugin_metadata.name}")
                else:
                    logger.debug(f"插件已禁用: {plugin_metadata.name}")
            
            logger.info("插件加载完成")
            
        except Exception as e:
            logger.error(f"插件加载失败: {e}", exc_info=True)
            raise AppError(f"插件加载失败: {e}")
    
    def start(self) -> None:
        """启动应用"""
        if not self._is_initialized:
            raise AppError("应用未初始化，请先调用initialize()")
        
        if self._is_running:
            logger.warning("应用已在运行中")
            return
        
        logger.info("启动应用")
        self._start_time = time.time()
        
        try:
            # 1. 启动事件总线
            if self._event_bus:
                self._event_bus.start()
                logger.debug("事件总线已启动")
            
            # 2. 加载插件
            self.load_plugins()
            
            # 3. 启动插件
            if self._plugin_registry:
                self._plugin_registry.start_all_plugins()
                logger.debug("插件已启动")
            
            self._is_running = True
            
            # 发布应用启动事件
            if self._event_bus:
                from .core.events import Event
                event = Event(
                    event_type="app.started",
                    data={
                        "start_time": self._start_time,
                        "environment": self._config_manager.environment
                    }
                )
                self._event_bus.publish(event.type, event.data, event.source)
            
            elapsed = time.time() - self._start_time
            logger.info(f"应用启动完成，耗时 {elapsed:.2f} 秒")
            
        except Exception as e:
            logger.error("应用启动失败", exc_info=True)
            raise AppError(f"应用启动失败: {e}")
    
    def run(self) -> None:
        """
        运行应用（阻塞调用）
        
        启动应用并进入主循环，直到收到停止信号
        """
        if not self._is_running:
            self.start()
        
        logger.info("应用进入主循环")
        
        try:
            # 简单的主循环 - 在实际应用中可能会更复杂
            while self._is_running and not self._is_shutting_down:
                # 检查事件总线状态
                if self._event_bus and self._event_bus.has_pending_events():
                    self._event_bus.process_events()
                
                # 短暂休眠以避免CPU占用过高
                time.sleep(0.1)
                
                # 检查停止条件
                # 在实际应用中，这里可能会有其他停止条件检查
        
        except KeyboardInterrupt:
            logger.info("收到键盘中断，开始关闭")
            self.shutdown()
        except Exception as e:
            logger.error("应用运行异常", exc_info=True)
            self.shutdown()
            raise
    
    def stop(self) -> None:
        """停止应用"""
        if not self._is_running:
            logger.warning("应用未运行，无需停止")
            return
        
        logger.info("停止应用")
        
        try:
            # 1. 停止插件
            if self._plugin_registry:
                self._plugin_registry.stop_all_plugins()
                logger.debug("插件已停止")
            
            # 2. 停止事件总线
            if self._event_bus:
                self._event_bus.stop()
                logger.debug("事件总线已停止")
            
            self._is_running = False
            self._stop_time = time.time()
            
            # 发布应用停止事件
            if self._event_bus:
                from .core.events import Event
                event = Event(
                    event_type="app.stopped",
                    data={
                        "stop_time": self._stop_time,
                        "uptime": self._stop_time - self._start_time
                    }
                )
                self._event_bus.publish(event.type, event.data, event.source)
            
            uptime = self._stop_time - self._start_time
            logger.info(f"应用已停止，运行时间 {uptime:.2f} 秒")
            
        except Exception as e:
            logger.error("应用停止失败", exc_info=True)
            raise AppError(f"应用停止失败: {e}")
    
    def shutdown(self) -> None:
        """关闭应用（完全清理）"""
        if self._is_shutting_down:
            logger.warning("应用已在关闭过程中")
            return
        
        logger.info("关闭应用")
        self._is_shutting_down = True
        
        try:
            # 1. 停止应用
            if self._is_running:
                self.stop()
            
            # 2. 清理插件
            if self._plugin_registry:
                self._plugin_registry.shutdown_all_plugins()
                logger.debug("插件已清理")
            
            # 3. 清理容器
            if self._container:
                self._container.clear()
                logger.debug("容器已清理")
            
            logger.info("应用关闭完成")
            
        except Exception as e:
            logger.error("应用关闭失败", exc_info=True)
            raise AppError(f"应用关闭失败: {e}")
        finally:
            self._is_shutting_down = False
    
    # 属性访问
    @property
    def config_manager(self) -> ConfigManager:
        """获取配置管理器"""
        if self._config_manager is None:
            raise AppError("配置管理器未初始化")
        return self._config_manager
    
    @property
    def event_bus(self) -> Optional[EventBus]:
        """获取事件总线"""
        return self._event_bus
    
    @property
    def container(self) -> Optional[Container]:
        """获取依赖注入容器"""
        return self._container
    
    @property
    def plugin_registry(self):
        """获取插件注册表"""
        return self._plugin_registry
    
    @property
    def is_initialized(self) -> bool:
        """应用是否已初始化"""
        return self._is_initialized
    
    @property
    def is_running(self) -> bool:
        """应用是否正在运行"""
        return self._is_running
    
    @property
    def uptime(self) -> Optional[float]:
        """应用运行时间（秒）"""
        if self._start_time is None:
            return None
        if self._is_running:
            return time.time() - self._start_time
        if self._stop_time is not None:
            return self._stop_time - self._start_time
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取应用状态"""
        status = {
            "initialized": self._is_initialized,
            "running": self._is_running,
            "shutting_down": self._is_shutting_down,
            "environment": self._config_manager.environment if self._config_manager else None,
            "start_time": self._start_time,
            "stop_time": self._stop_time,
            "uptime": self.uptime
        }
        
        # 添加组件状态
        if self._config_manager:
            status["config"] = {
                "environment": self._config_manager.environment,
                "app_name": self._config_manager.config.app.name,
                "app_version": self._config_manager.config.app.version
            }
        
        if self._event_bus:
            status["event_bus"] = {
                "queue_size": self._event_bus.queue_size,
                "worker_count": self._event_bus.worker_count
            }
        
        if self._plugin_registry:
            status["plugins"] = {
                "total": len(self._plugin_registry.get_all_plugins()),
                "running": len(self._plugin_registry.get_running_plugins())
            }
        
        return status
    
    def __enter__(self):
        """上下文管理器入口"""
        self.initialize()
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()
    
    def __del__(self):
        """析构函数"""
        if self._is_running:
            logger.warning("应用仍在运行时被销毁，强制关闭")
            try:
                self.shutdown()
            except Exception:
                pass


# 便捷函数
def create_app(config_path: Optional[str] = None) -> SmallPanguApp:
    """创建应用实例"""
    return SmallPanguApp(config_path)


def run_app(config_path: Optional[str] = None):
    """创建并运行应用"""
    app = create_app(config_path)
    app.initialize()
    app.run()


__all__ = [
    "SmallPanguApp",
    "create_app",
    "run_app"
]