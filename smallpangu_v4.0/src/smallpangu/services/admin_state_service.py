"""
管理后台状态持久化服务

统一管理后台的用户界面偏好、操作历史、模块状态等持久化数据，支持：
1. 用户界面偏好保存/恢复
2. 最近操作历史记录
3. 模块折叠/展开状态
4. 搜索和过滤条件
5. 备份和恢复机制
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from uuid import uuid4

from ..core.logging import get_logger
from ..core.events import EventBus
from ..config.manager import ConfigManager

logger = get_logger(__name__)


class StateCategory(str, Enum):
    """状态分类枚举"""
    UI_PREFERENCES = "ui_preferences"      # 用户界面偏好
    MODULE_STATES = "module_states"       # 模块状态（折叠/展开等）
    OPERATION_HISTORY = "operation_history" # 操作历史记录
    SEARCH_FILTERS = "search_filters"     # 搜索和过滤条件
    BACKUP_SNAPSHOTS = "backup_snapshots" # 备份快照


class OperationType(str, Enum):
    """操作类型枚举"""
    CONFIG_CHANGE = "config_change"        # 配置变更
    MODULE_ENABLE = "module_enable"        # 模块启用
    MODULE_DISABLE = "module_disable"      # 模块禁用
    MODULE_RELOAD = "module_reload"        # 模块重载
    UI_PREFERENCE_CHANGE = "ui_preference_change"  # 界面偏好变更
    SEARCH_FILTER_CHANGE = "search_filter_change"  # 搜索过滤变更
    BACKUP_CREATED = "backup_created"      # 备份创建
    RESTORE_PERFORMED = "restore_performed"  # 恢复操作


@dataclass
class UITheme:
    """界面主题配置"""
    name: str = "default"
    primary_color: str = "#3f51b5"
    secondary_color: str = "#f50057"
    background_color: str = "#ffffff"
    text_color: str = "#333333"
    font_family: str = "Arial, sans-serif"
    font_size: int = 14
    spacing_unit: int = 8
    rounded_corners: bool = True
    animations_enabled: bool = True


@dataclass
class UIPreferences:
    """用户界面偏好"""
    theme: UITheme = field(default_factory=UITheme)
    sidebar_width: int = 240
    sidebar_collapsed: bool = False
    module_view_mode: str = "cards"  # cards, list, table
    show_descriptions: bool = True
    show_icons: bool = True
    show_categories: bool = True
    auto_save_enabled: bool = True
    auto_save_interval: int = 30  # 秒
    confirm_before_reload: bool = True
    confirm_before_restart: bool = True
    language: str = "zh_CN"
    timezone: str = "Asia/Shanghai"


@dataclass
class ModuleUIState:
    """模块界面状态"""
    module_id: str
    expanded: bool = True
    pinned: bool = False
    favorite: bool = False
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    custom_order: Optional[int] = None
    hidden: bool = False


@dataclass
class OperationRecord:
    """操作记录"""
    operation_type: OperationType
    operation_id: str = field(default_factory=lambda: str(uuid4()))
    module_id: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user: str = "admin"  # 固定为管理员，专人专用
    successful: bool = True
    duration_ms: Optional[int] = None


@dataclass
class SearchFilter:
    """搜索过滤条件"""
    filter_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    query: str = ""
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled_only: bool = True
    has_config_only: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0


@dataclass
class BackupSnapshot:
    """备份快照"""
    snapshot_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    state_data: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0
    included_categories: List[StateCategory] = field(default_factory=list)


@dataclass
class AdminState:
    """管理后台完整状态"""
    version: int = 1
    ui_preferences: UIPreferences = field(default_factory=UIPreferences)
    module_states: Dict[str, ModuleUIState] = field(default_factory=dict)
    operation_history: List[OperationRecord] = field(default_factory=list)
    search_filters: Dict[str, SearchFilter] = field(default_factory=dict)
    backup_snapshots: Dict[str, BackupSnapshot] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)


class AdminStateService:
    """
    管理后台状态服务
    
    统一管理后台的所有持久化状态，提供：
    1. 自动保存和加载状态
    2. 状态变更跟踪
    3. 备份和恢复功能
    4. 操作历史记录
    """
    
    DEFAULT_STATE_FILE = "admin_state.json"
    MAX_HISTORY_ENTRIES = 1000
    MAX_BACKUP_SNAPSHOTS = 50
    
    def __init__(
        self,
        config_manager: ConfigManager,
        event_bus: Optional[EventBus] = None,
        state_file_path: Optional[str] = None
    ):
        """
        初始化状态服务
        
        Args:
            config_manager: 配置管理器
            event_bus: 事件总线（可选）
            state_file_path: 状态文件路径（可选）
        """
        self._config_manager = config_manager
        self._event_bus = event_bus
        
        # 确定状态文件路径
        if state_file_path:
            self._state_file = Path(state_file_path)
        else:
            # 使用默认配置目录
            config_dir = Path.cwd() / "configs"
            self._state_file = config_dir / self.DEFAULT_STATE_FILE
        
        # 状态存储
        self._state: Optional[AdminState] = None
        self._state_lock = threading.RLock()
        
        # 自动保存
        self._auto_save_enabled = True
        self._auto_save_timer: Optional[threading.Timer] = None
        self._auto_save_interval = 30  # 秒
        self._pending_save = False
        
        # 初始化日志
        logger.debug(
            f"管理后台状态服务初始化: state_file={self._state_file}, "
            f"config_manager={config_manager is not None}, "
            f"event_bus={event_bus is not None}"
        )
    
    def initialize(self) -> None:
        """初始化状态服务"""
        with self._state_lock:
            if self._state is not None:
                logger.warning("状态服务已初始化，跳过重复初始化")
                return
            
            logger.info("初始化管理后台状态服务")
            
            # 尝试加载现有状态
            try:
                self._state = self._load_state()
                logger.info(f"状态加载成功，版本: {self._state.version}")
            except Exception as e:
                logger.warning(f"状态加载失败，创建新状态: {e}")
                self._state = AdminState()
            
            # 启动自动保存定时器
            if self._auto_save_enabled:
                self._start_auto_save_timer()
            
            # 发布初始化完成事件
            if self._event_bus:
                self._event_bus.publish(
                    "admin_state.initialized",
                    {"state_file": str(self._state_file)}
                )
            
            logger.info("管理后台状态服务初始化完成")
    
    def shutdown(self) -> None:
        """关闭状态服务"""
        with self._state_lock:
            logger.info("关闭管理后台状态服务")
            
            # 停止自动保存定时器
            if self._auto_save_timer:
                self._auto_save_timer.cancel()
                self._auto_save_timer = None
            
            # 确保保存所有未保存的更改
            if self._pending_save:
                self._save_state()
            
            logger.info("管理后台状态服务已关闭")
    
    def _load_state(self) -> AdminState:
        """从文件加载状态"""
        if not self._state_file.exists():
            logger.debug("状态文件不存在，返回默认状态")
            return AdminState()
        
        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 基本验证
            if not isinstance(data, dict):
                raise ValueError("状态文件格式无效")
            
            # 这里可以添加更复杂的反序列化逻辑
            # 目前使用简单转换
            state = AdminState(**data)
            
            # 状态迁移（处理旧版本）
            state = self._migrate_state(state)
            
            logger.debug(f"状态加载成功，文件大小: {self._state_file.stat().st_size} 字节，版本: {state.version}")
            return state
            
        except Exception as e:
            logger.error(f"状态文件加载失败: {e}", exc_info=True)
            # 备份损坏的文件
            self._backup_corrupted_file()
            raise
    
    def _save_state(self) -> None:
        """保存状态到文件"""
        if self._state is None:
            logger.warning("状态未初始化，跳过保存")
            return
        
        try:
            # 更新修改时间
            self._state.last_modified = datetime.now()
            
            # 转换为可序列化的字典
            state_dict = asdict(self._state)
            
            # 确保目录存在
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件（原子操作）
            temp_file = self._state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
            # 替换原文件
            temp_file.replace(self._state_file)
            
            self._pending_save = False
            logger.debug(f"状态保存成功，文件: {self._state_file}")
            
            # 发布保存完成事件
            if self._event_bus:
                self._event_bus.publish(
                    "admin_state.saved",
                    {"state_file": str(self._state_file)}
                )
                
        except Exception as e:
            logger.error(f"状态保存失败: {e}", exc_info=True)
            raise
    
    def _json_serializer(self, obj):
        """JSON序列化辅助函数"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"无法序列化类型: {type(obj)}")
    
    def _backup_corrupted_file(self) -> None:
        """备份损坏的状态文件"""
        if not self._state_file.exists():
            return
        
        try:
            backup_file = self._state_file.with_suffix(f'.corrupted.{int(time.time())}.bak')
            self._state_file.rename(backup_file)
            logger.warning(f"损坏的状态文件已备份到: {backup_file}")
        except Exception as e:
            logger.error(f"备份损坏文件失败: {e}")
    
    def _migrate_state(self, state: AdminState) -> AdminState:
        """
        状态迁移
        
        确保旧版本状态数据能够迁移到当前版本
        """
        current_version = 1
        
        # 如果版本相同，直接返回
        if state.version >= current_version:
            return state
        
        logger.info(f"开始状态迁移: 版本 {state.version} -> {current_version}")
        
        # 版本1迁移逻辑（目前版本1是初始版本，无需迁移）
        # 这里可以添加未来版本的迁移逻辑
        
        # 更新版本号
        state.version = current_version
        
        logger.info(f"状态迁移完成，当前版本: {state.version}")
        return state
    
    def _start_auto_save_timer(self) -> None:
        """启动自动保存定时器"""
        if not self._auto_save_enabled:
            return
        
        def auto_save_task():
            try:
                with self._state_lock:
                    if self._pending_save:
                        self._save_state()
            except Exception as e:
                logger.error(f"自动保存失败: {e}")
            finally:
                # 重新安排定时器
                if self._auto_save_enabled:
                    self._auto_save_timer = threading.Timer(
                        self._auto_save_interval,
                        auto_save_task
                    )
                    self._auto_save_timer.daemon = True
                    self._auto_save_timer.start()
        
        self._auto_save_timer = threading.Timer(
            self._auto_save_interval,
            auto_save_task
        )
        self._auto_save_timer.daemon = True
        self._auto_save_timer.start()
        
        logger.debug(f"自动保存定时器已启动，间隔: {self._auto_save_interval}秒")
    
    def mark_state_dirty(self) -> None:
        """标记状态为脏（需要保存）"""
        with self._state_lock:
            self._pending_save = True
            logger.debug("状态标记为需要保存")
    
    # ========== 公共API方法 ==========
    
    def get_state(self) -> AdminState:
        """获取完整状态"""
        with self._state_lock:
            if self._state is None:
                raise RuntimeError("状态服务未初始化")
            return self._state
    
    def get_ui_preferences(self) -> UIPreferences:
        """获取用户界面偏好"""
        return self.get_state().ui_preferences
    
    def update_ui_preferences(self, preferences: UIPreferences) -> None:
        """更新用户界面偏好"""
        with self._state_lock:
            self._state.ui_preferences = preferences
            self.mark_state_dirty()
            
            # 记录操作历史
            self._add_operation_record(
                OperationType.UI_PREFERENCE_CHANGE,
                description="更新界面偏好设置"
            )
    
    def update_theme(self, theme: UITheme) -> None:
        """更新主题设置"""
        with self._state_lock:
            preferences = self._state.ui_preferences
            preferences.theme = theme
            self._state.ui_preferences = preferences
            self.mark_state_dirty()
            
            self._add_operation_record(
                OperationType.UI_PREFERENCE_CHANGE,
                description="更新主题设置"
            )
    
    def update_preference(self, key: str, value: Any) -> bool:
        """
        更新单个偏好设置
        
        Args:
            key: 偏好键名（支持点号路径，如 "theme.primary_color"）
            value: 新的值
            
        Returns:
            是否成功更新
        """
        try:
            with self._state_lock:
                preferences = self._state.ui_preferences
                
                # 支持嵌套路径
                keys = key.split('.')
                obj = preferences
                
                # 遍历到最后一个键的父对象
                for k in keys[:-1]:
                    if not hasattr(obj, k):
                        return False
                    obj = getattr(obj, k)
                
                # 设置值
                final_key = keys[-1]
                if not hasattr(obj, final_key):
                    return False
                
                setattr(obj, final_key, value)
                self._state.ui_preferences = preferences
                self.mark_state_dirty()
                
                self._add_operation_record(
                    OperationType.UI_PREFERENCE_CHANGE,
                    description=f"更新偏好设置: {key}"
                )
                
                return True
                
        except Exception as e:
            logger.error(f"更新偏好设置失败: {e}", exc_info=True)
            return False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        获取单个偏好设置
        
        Args:
            key: 偏好键名（支持点号路径，如 "theme.primary_color"）
            default: 默认值（如果键不存在）
            
        Returns:
            偏好值或默认值
        """
        try:
            preferences = self.get_ui_preferences()
            
            # 支持嵌套路径
            keys = key.split('.')
            obj = preferences
            
            for k in keys:
                if not hasattr(obj, k):
                    return default
                obj = getattr(obj, k)
            
            return obj
            
        except Exception as e:
            logger.error(f"获取偏好设置失败: {e}", exc_info=True)
            return default
    
    def get_module_state(self, module_id: str) -> Optional[ModuleUIState]:
        """获取模块界面状态"""
        return self.get_state().module_states.get(module_id)
    
    def update_module_state(self, module_state: ModuleUIState) -> None:
        """更新模块界面状态"""
        with self._state_lock:
            self._state.module_states[module_state.module_id] = module_state
            self.mark_state_dirty()
    
    def record_operation(self, operation_record: OperationRecord) -> None:
        """记录操作历史"""
        with self._state_lock:
            # 添加到历史记录
            self._state.operation_history.append(operation_record)
            
            # 保持历史记录大小限制
            if len(self._state.operation_history) > self.MAX_HISTORY_ENTRIES:
                self._state.operation_history = self._state.operation_history[-self.MAX_HISTORY_ENTRIES:]
            
            self.mark_state_dirty()
    
    def _add_operation_record(
        self,
        operation_type: OperationType,
        module_id: Optional[str] = None,
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
        successful: bool = True,
        duration_ms: Optional[int] = None
    ) -> OperationRecord:
        """添加操作记录（辅助方法）"""
        operation_record = OperationRecord(
            operation_type=operation_type,
            module_id=module_id,
            description=description,
            details=details or {},
            successful=successful,
            duration_ms=duration_ms
        )
        
        self.record_operation(operation_record)
        return operation_record
    
    def create_backup_snapshot(self, name: str, description: str = "") -> BackupSnapshot:
        """创建备份快照"""
        with self._state_lock:
            # 创建快照
            snapshot = BackupSnapshot(
                name=name,
                description=description,
                state_data=asdict(self._state),
                size_bytes=0  # 将在后面计算
            )
            
            # 添加到快照列表
            self._state.backup_snapshots[snapshot.snapshot_id] = snapshot
            
            # 保持快照数量限制
            if len(self._state.backup_snapshots) > self.MAX_BACKUP_SNAPSHOTS:
                # 删除最旧的快照
                oldest_id = min(
                    self._state.backup_snapshots.keys(),
                    key=lambda k: self._state.backup_snapshots[k].timestamp
                )
                del self._state.backup_snapshots[oldest_id]
            
            self.mark_state_dirty()
            
            # 记录操作
            self._add_operation_record(
                OperationType.BACKUP_CREATED,
                description=f"创建备份快照: {name}",
                details={"snapshot_id": snapshot.snapshot_id}
            )
            
            return snapshot
    
    def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """从快照恢复状态"""
        with self._state_lock:
            snapshot = self._state.backup_snapshots.get(snapshot_id)
            if not snapshot:
                logger.error(f"快照不存在: {snapshot_id}")
                return False
            
            try:
                # 恢复状态
                self._state = AdminState(**snapshot.state_data)
                
                # 记录操作
                self._add_operation_record(
                    OperationType.RESTORE_PERFORMED,
                    description=f"从快照恢复: {snapshot.name}",
                    details={"snapshot_id": snapshot_id}
                )
                
                # 立即保存
                self._save_state()
                
                logger.info(f"状态从快照恢复成功: {snapshot.name}")
                return True
                
            except Exception as e:
                logger.error(f"快照恢复失败: {e}", exc_info=True)
                return False
    
    # ========== 实用方法 ==========
    
    def get_recent_operations(self, limit: int = 50) -> List[OperationRecord]:
        """获取最近的操作记录"""
        with self._state_lock:
            history = self.get_state().operation_history
            return history[-limit:] if history else []
    
    def clear_operation_history(self) -> None:
        """清空操作历史"""
        with self._state_lock:
            self._state.operation_history.clear()
            self.mark_state_dirty()
            logger.info("操作历史已清空")
    
    def get_all_module_states(self) -> Dict[str, ModuleUIState]:
        """获取所有模块状态"""
        return self.get_state().module_states.copy()
    
    def reset_ui_preferences(self) -> None:
        """重置界面偏好为默认值"""
        with self._state_lock:
            self._state.ui_preferences = UIPreferences()
            self.mark_state_dirty()
            logger.info("界面偏好已重置为默认值")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取状态统计信息"""
        with self._state_lock:
            state = self.get_state()
            return {
                "version": state.version,
                "module_count": len(state.module_states),
                "operation_count": len(state.operation_history),
                "filter_count": len(state.search_filters),
                "backup_count": len(state.backup_snapshots),
                "created_at": state.created_at,
                "last_modified": state.last_modified,
                "state_file_size": self._state_file.stat().st_size if self._state_file.exists() else 0
            }