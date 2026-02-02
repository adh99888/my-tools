"""
配置管理器 - 配置的统一访问接口和热重载支持
"""

import os
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock, RLock

from .models import SmallPanguConfig
from .loader import load_config, reload_config, ConfigLoader
from ..core.events import EventBus, Event
from ..core.errors import ConfigError
from ..core.logging import get_logger
import yaml

logger = get_logger(__name__)


@dataclass
class ConfigWatchInfo:
    """配置监视信息"""
    file_path: Path
    last_modified: float
    last_size: int
    checksum: Optional[str] = None


class ConfigManager:
    """
    配置管理器
    
    提供统一的配置访问接口，支持：
    1. 配置加载和验证
    2. 环境变量覆盖
    3. 热重载
    4. 配置变更通知
    5. 配置订阅
    """
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        environment: Optional[str] = None,
        enable_hot_reload: bool = False,
        event_bus: Optional[EventBus] = None
    ):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径或目录
            environment: 运行环境
            enable_hot_reload: 是否启用热重载
            event_bus: 事件总线实例
        """
        self._config_path = Path(config_path) if config_path else None
        self._environment = environment
        self._enable_hot_reload = enable_hot_reload
        
        # 配置缓存
        self._config: Optional[SmallPanguConfig] = None
        self._config_lock = RLock()
        
        # 事件总线
        self._event_bus = event_bus
        
        # 热重载相关
        self._watched_files: Dict[str, ConfigWatchInfo] = {}
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_watching = threading.Event()
        self._watch_interval = 5.0  # 检查间隔（秒）
        self._watch_lock = Lock()
        
        # 配置变更回调
        self._callbacks: List[Callable[[SmallPanguConfig], None]] = []
        
        # 初始化配置
        self._initialize()
    
    def _initialize(self):
        """初始化配置"""
        with self._config_lock:
            try:
                # 加载配置
                self._config = load_config(self._config_path, self._environment)
                
                # 设置环境变量（用于后续配置验证）
                os.environ["SMALLPANGU_ENVIRONMENT"] = self._config.environment
                
                # 记录配置信息
                logger.info_struct(
                    "配置管理器初始化成功",
                    environment=self._config.environment,
                    config_path=str(self._config_path) if self._config_path else "default"
                )
                
                # 初始化热重载
                if self._enable_hot_reload and self._config.app.hot_reload:
                    self._start_watching()
                    
            except Exception as e:
                logger.error_struct("配置管理器初始化失败", exc_info=True)
                raise ConfigError(
                    "配置管理器初始化失败",
                    details={"error": str(e)}
                ) from e
    
    @property
    def config(self) -> SmallPanguConfig:
        """获取当前配置（线程安全）"""
        with self._config_lock:
            if self._config is None:
                raise ConfigError("配置未加载")
            return self._config
    
    @property
    def environment(self) -> str:
        """获取当前环境"""
        return self.config.environment
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）
        
        Args:
            key: 配置键，支持点号分隔（如 "app.log_level"）
            default: 默认值（如果键不存在）
            
        Returns:
            配置值
        """
        try:
            value = self.config
            for part in key.split("."):
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set_value(self, key: str, value: Any, persistent: bool = False) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔（如 "app.log_level"）
            value: 配置值
            persistent: 是否持久化到配置文件
            
        Returns:
            是否设置成功
        """
        with self._config_lock:
            try:
                # 获取当前配置对象
                config_obj = self._config
                parts = key.split(".")
                
                # 遍历到最后一个部分的前一个对象
                for i, part in enumerate(parts[:-1]):
                    if hasattr(config_obj, part):
                        config_obj = getattr(config_obj, part)
                    elif isinstance(config_obj, dict) and part in config_obj:
                        config_obj = config_obj[part]
                    else:
                        # 路径不存在，创建嵌套字典？（暂不支持）
                        logger.warning("配置路径不存在", key=key, part=part)
                        return False
                
                last_part = parts[-1]
                # 设置值
                if hasattr(config_obj, last_part):
                    setattr(config_obj, last_part, value)
                elif isinstance(config_obj, dict):
                    config_obj[last_part] = value
                else:
                    logger.warning("配置路径不可设置", key=key)
                    return False
                
                # 触发配置变更事件
                old_config = self._config
                self._on_config_changed(old_config, self._config)
                
                # 如果需要持久化，保存到文件
                if persistent:
                    self._save_to_file()
                
                logger.info("配置值设置成功", key=key, value=value, persistent=persistent)
                return True
                
            except Exception as e:
                logger.error("配置值设置失败", key=key, error=str(e))
                return False
    
    def _save_to_file(self) -> bool:
        """
        将当前配置保存到文件
        
        Returns:
            是否保存成功
        """
        try:
            config_dict = self._config.model_dump()
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
            logger.info("配置保存成功", config_path=str(self._config_path))
            return True
        except Exception as e:
            logger.error("配置保存失败", config_path=str(self._config_path), error=str(e))
            return False
    
    def reload(self, force: bool = False) -> bool:
        """
        重新加载配置
        
        Args:
            force: 是否强制重新加载（忽略缓存）
            
        Returns:
            是否重新加载成功
        """
        with self._config_lock:
            try:
                old_config = self._config
                
                if force:
                    self._config = reload_config(self._config_path, self._environment)
                else:
                    self._config = load_config(self._config_path, self._environment)
                
                # 触发配置变更事件
                self._on_config_changed(old_config, self._config)
                
                logger.info("配置重新加载成功")
                return True
                
            except Exception as e:
                logger.error("配置重新加载失败", exc_info=True)
                return False
    
    def subscribe(self, callback: Callable[[SmallPanguConfig], None]) -> str:
        """
        订阅配置变更
        
        Args:
            callback: 回调函数，接收新配置作为参数
            
        Returns:
            订阅ID
        """
        from uuid import uuid4
        callback_id = str(uuid4())
        
        # 使用装饰器包装回调以便追踪
        def wrapped_callback(new_config: SmallPanguConfig):
            try:
                callback(new_config)
            except Exception as e:
                logger.error("配置变更回调执行失败", callback_id=callback_id, exc_info=True)
        
        # 存储回调（实际实现使用包装版本）
        self._callbacks.append(wrapped_callback)
        logger.debug("配置变更订阅已添加", callback_id=callback_id)
        
        return callback_id
    
    def unsubscribe(self, callback_id: str) -> bool:
        """
        取消订阅配置变更
        
        Args:
            callback_id: 订阅ID
            
        Returns:
            是否取消成功
        """
        # TODO: 基于ID实现取消订阅
        logger.warning("配置变更取消订阅功能暂未完全实现", callback_id=callback_id)
        return False
    
    def _on_config_changed(self, old_config: SmallPanguConfig, new_config: SmallPanguConfig):
        """处理配置变更"""
        # 记录变更
        logger.info("配置已变更", environment=new_config.environment)
        
        # 触发事件总线事件
        if self._event_bus:
            event = Event(
                type="config.changed",
                data={
                    "old_config": old_config.dict() if old_config else None,
                    "new_config": new_config.dict(),
                    "environment": new_config.environment
                },
                timestamp=datetime.now().isoformat()
            )
            self._event_bus.publish(event)
        
        # 调用回调函数
        for callback in self._callbacks:
            try:
                callback(new_config)
            except Exception as e:
                logger.error("配置变更回调执行失败", exc_info=True)
    
    def _start_watching(self):
        """开始监视配置文件变更"""
        if self._watch_thread and self._watch_thread.is_alive():
            logger.warning("配置监视线程已在运行")
            return
        
        # 收集要监视的文件
        self._collect_watch_files()
        
        if not self._watched_files:
            logger.warning("没有配置文件可监视")
            return
        
        # 启动监视线程
        self._stop_watching.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            name="ConfigWatcher",
            daemon=True
        )
        self._watch_thread.start()
        
        logger.info("配置热重载监视已启动", files=list(self._watched_files.keys()))
    
    def _collect_watch_files(self):
        """收集要监视的配置文件"""
        with self._watch_lock:
            self._watched_files.clear()
            
            # 确定配置目录
            if self._config_path and self._config_path.is_dir():
                config_dir = self._config_path
            elif self._config_path and self._config_path.is_file():
                config_dir = self._config_path.parent
            else:
                config_dir = Path.cwd() / "configs"
            
            # 添加基础配置文件
            config_files = ["base.yaml", f"{self.environment}.yaml", "custom.yaml"]
            
            for config_file in config_files:
                file_path = config_dir / config_file
                if file_path.exists():
                    self._add_watch_file(file_path)
    
    def _add_watch_file(self, file_path: Path):
        """添加文件到监视列表"""
        try:
            stat = file_path.stat()
            watch_info = ConfigWatchInfo(
                file_path=file_path,
                last_modified=stat.st_mtime,
                last_size=stat.st_size
            )
            self._watched_files[str(file_path)] = watch_info
        except Exception as e:
            logger.error("添加配置文件监视失败", file=str(file_path), exc_info=True)
    
    def _watch_loop(self):
        """监视循环"""
        logger.debug("配置监视循环开始")
        
        while not self._stop_watching.is_set():
            try:
                time.sleep(self._watch_interval)
                
                # 检查文件变更
                changed_files = self._check_file_changes()
                
                if changed_files:
                    logger.info("检测到配置文件变更", files=changed_files)
                    
                    # 重新加载配置
                    success = self.reload(force=True)
                    
                    if success:
                        # 更新监视信息
                        self._collect_watch_files()
                    else:
                        logger.warning("配置文件变更但重新加载失败")
                        
            except Exception as e:
                logger.error("配置监视循环异常", exc_info=True)
                time.sleep(self._watch_interval * 2)  # 发生错误时等待更长时间
        
        logger.debug("配置监视循环结束")
    
    def _check_file_changes(self) -> List[str]:
        """检查文件变更"""
        changed_files = []
        
        with self._watch_lock:
            for file_path_str, watch_info in list(self._watched_files.items()):
                file_path = watch_info.file_path
                
                try:
                    if not file_path.exists():
                        logger.warning("监视的配置文件已删除", file=str(file_path))
                        self._watched_files.pop(file_path_str, None)
                        changed_files.append(str(file_path))
                        continue
                    
                    stat = file_path.stat()
                    current_mtime = stat.st_mtime
                    current_size = stat.st_size
                    
                    # 检查修改时间或大小是否变化
                    if (current_mtime != watch_info.last_modified or 
                        current_size != watch_info.last_size):
                        
                        # 更新监视信息
                        watch_info.last_modified = current_mtime
                        watch_info.last_size = current_size
                        
                        changed_files.append(str(file_path))
                        
                except Exception as e:
                    logger.error("检查配置文件变更失败", file=str(file_path), exc_info=True)
        
        return changed_files
    
    def stop_watching(self):
        """停止监视配置文件"""
        if self._watch_thread:
            self._stop_watching.set()
            self._watch_thread.join(timeout=3.0)
            
            if self._watch_thread.is_alive():
                logger.warning("配置监视线程未能正常停止")
            else:
                logger.info("配置监视已停止")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        if not self._config:
            return {}
        
        config_dict = self._config.dict()
        
        # 创建安全的摘要（排除敏感信息）
        summary = {
            "environment": self._config.environment,
            "app": {
                "name": self._config.app.name,
                "version": self._config.app.version,
                "log_level": self._config.app.log_level.value,
                "debug_mode": self._config.app.debug_mode
            },
            "plugins": {
                "enabled_count": len(self._config.plugins.enabled),
                "loading_strategy": self._config.plugins.loading_strategy
            },
            "ai": {
                "default_provider": self._config.ai.default_provider,
                "max_tokens": self._config.ai.max_tokens
            }
        }
        
        return summary
    
    def validate_current_config(self) -> List[str]:
        """
        验证当前配置
        
        Returns:
            验证错误列表（空列表表示验证通过）
        """
        errors = []
        
        if not self._config:
            errors.append("配置未加载")
            return errors
        
        # 检查必要的目录
        required_dirs = [
            ("数据目录", self._config.app.data_dir),
            ("缓存目录", self._config.app.cache_dir)
        ]
        
        for dir_name, dir_path in required_dirs:
            expanded_path = Path(dir_path).expanduser()
            try:
                expanded_path.mkdir(parents=True, exist_ok=True)
                
                # 测试写入权限
                test_file = expanded_path / ".write_test"
                test_file.touch()
                test_file.unlink()
                
            except Exception as e:
                errors.append(f"{dir_name} '{dir_path}' 不可写: {str(e)}")
        
        # 检查插件搜索路径
        for i, search_path in enumerate(self._config.plugins.search_paths):
            expanded_path = Path(search_path).expanduser()
            if not expanded_path.exists():
                logger.warning(f"插件搜索路径不存在: {search_path}")
        
        return errors
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_watching()
    
    def __del__(self):
        """析构函数"""
        self.stop_watching()


# 全局配置管理器实例
_global_manager = None
_global_manager_lock = threading.Lock()


def get_config_manager(
    config_path: Optional[Union[str, Path]] = None,
    environment: Optional[str] = None,
    enable_hot_reload: bool = False,
    event_bus: Optional[EventBus] = None
) -> ConfigManager:
    """
    获取全局配置管理器实例（单例）
    
    Args:
        config_path: 配置文件路径或目录
        environment: 运行环境
        enable_hot_reload: 是否启用热重载
        event_bus: 事件总线实例
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _global_manager
    
    with _global_manager_lock:
        if _global_manager is None:
            _global_manager = ConfigManager(
                config_path=config_path,
                environment=environment,
                enable_hot_reload=enable_hot_reload,
                event_bus=event_bus
            )
        elif (config_path or environment or enable_hot_reload):
            logger.warning_struct(
                "全局配置管理器已存在，新参数将被忽略",
                config_path=config_path,
                environment=environment
            )
        
        return _global_manager


def reset_config_manager():
    """重置全局配置管理器（主要用于测试）"""
    global _global_manager
    
    with _global_manager_lock:
        if _global_manager:
            _global_manager.stop_watching()
            _global_manager = None
        
        logger.debug("全局配置管理器已重置")


__all__ = [
    "ConfigManager",
    "get_config_manager",
    "reset_config_manager"
]