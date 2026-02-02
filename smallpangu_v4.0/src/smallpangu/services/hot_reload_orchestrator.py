"""
热重载协调器

实现分级热重载策略，支持：
1. 立即生效（UI外观）
2. 实时生效（AI参数）
3. 重启生效（插件/系统）
4. 手动生效（用户确认）
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from queue import Queue, Empty

from ..core.logging import get_logger
from ..core.events import EventBus
from ..config.manager import ConfigManager
from .module_registry import ModuleRegistry, ReloadStrategy

logger = get_logger(__name__)


class ReloadPriority(str, Enum):
    """重载优先级枚举"""
    LOW = "low"          # 低优先级（UI外观）
    MEDIUM = "medium"    # 中优先级（AI参数）
    HIGH = "high"        # 高优先级（插件配置）
    CRITICAL = "critical"  # 关键优先级（系统参数）


class ReloadStatus(str, Enum):
    """重载状态枚举"""
    PENDING = "pending"      # 等待重载
    IN_PROGRESS = "in_progress"  # 重载中
    SUCCESS = "success"      # 重载成功
    FAILED = "failed"        # 重载失败
    CANCELLED = "cancelled"  # 已取消
    SKIPPED = "skipped"      # 已跳过


@dataclass
class ReloadRequest:
    """重载请求"""
    
    request_id: str                    # 请求ID
    module_id: str                     # 模块ID
    reload_strategy: ReloadStrategy    # 重载策略
    priority: ReloadPriority           # 优先级
    
    # 请求数据
    old_config: Dict[str, Any]         # 旧配置
    new_config: Dict[str, Any]         # 新配置
    changes: Dict[str, Any]            # 变更内容
    source: str                        # 请求来源
    
    # 时间戳
    created_at: float                  # 创建时间
    started_at: Optional[float] = None # 开始时间
    completed_at: Optional[float] = None  # 完成时间
    
    # 状态
    status: ReloadStatus = ReloadStatus.PENDING
    error_message: Optional[str] = None  # 错误信息
    
    # 回调
    on_success: Optional[Callable[[], None]] = None
    on_failure: Optional[Callable[[str], None]] = None
    on_complete: Optional[Callable[[ReloadStatus], None]] = None
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """计算耗时"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return time.time() - self.started_at
        return None
    
    @property
    def waiting_time(self) -> float:
        """计算等待时间"""
        if self.started_at:
            return self.started_at - self.created_at
        return time.time() - self.created_at


@dataclass
class ReloadResult:
    """重载结果"""
    
    request_id: str
    module_id: str
    status: ReloadStatus
    elapsed_time: Optional[float]
    error_message: Optional[str] = None
    affected_modules: List[str] = field(default_factory=list)  # 受影响的模块


class HotReloadOrchestrator:
    """
    热重载协调器
    
    管理配置变更的热重载过程，实现分级策略：
    1. 立即生效：UI外观设置（优先级低）
    2. 实时生效：AI模型参数（优先级中）
    3. 重启生效：插件和系统配置（优先级高）
    4. 手动生效：需要用户确认的变更（优先级关键）
    """
    
    # 策略到优先级的映射
    STRATEGY_PRIORITY_MAP = {
        ReloadStrategy.IMMEDIATE: ReloadPriority.LOW,
        ReloadStrategy.REAL_TIME: ReloadPriority.MEDIUM,
        ReloadStrategy.RESTART_REQUIRED: ReloadPriority.HIGH,
        ReloadStrategy.MANUAL: ReloadPriority.CRITICAL
    }
    
    # 策略到处理方法的映射
    STRATEGY_HANDLERS = {
        ReloadStrategy.IMMEDIATE: "_handle_immediate_reload",
        ReloadStrategy.REAL_TIME: "_handle_real_time_reload",
        ReloadStrategy.RESTART_REQUIRED: "_handle_restart_reload",
        ReloadStrategy.MANUAL: "_handle_manual_reload"
    }
    
    def __init__(
        self,
        config_manager: ConfigManager,
        event_bus: EventBus,
        module_registry: ModuleRegistry,
        max_queue_size: int = 100,
        worker_count: int = 2
    ):
        """
        初始化热重载协调器
        
        Args:
            config_manager: 配置管理器
            event_bus: 事件总线
            module_registry: 模块注册表
            max_queue_size: 最大队列大小
            worker_count: 工作线程数量
        """
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._module_registry = module_registry
        
        # 队列管理
        self._request_queue = Queue(maxsize=max_queue_size)
        self._pending_requests: Dict[str, ReloadRequest] = {}
        self._completed_requests: Dict[str, ReloadResult] = {}
        
        # 工作线程
        self._worker_count = worker_count
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "cancelled": 0,
            "skipped": 0,
            "average_time": 0.0
        }
        
        # 订阅事件
        self._subscribe_events()
        
        logger.debug_struct("热重载协调器初始化",
                          max_queue_size=max_queue_size,
                          worker_count=worker_count)
    
    def _subscribe_events(self) -> None:
        """订阅相关事件"""
        # 模块配置变更事件
        self._event_bus.subscribe("module.config.changed", self._on_module_config_changed)
        
        # 系统配置变更事件
        self._event_bus.subscribe("config.changed", self._on_config_changed)
        
        # 插件状态变更事件
        self._event_bus.subscribe("plugin.enabled", self._on_plugin_state_changed)
        self._event_bus.subscribe("plugin.disabled", self._on_plugin_state_changed)
        
        logger.debug("热重载协调器事件订阅完成")
    
    def _on_module_config_changed(self, event) -> None:
        """处理模块配置变更事件"""
        data = event.data
        module_id = data.get("module_id")
        old_config = data.get("old_config", {})
        new_config = data.get("new_config", {})
        reload_strategy = data.get("reload_strategy")
        
        if not module_id or not reload_strategy:
            logger.warning("模块配置变更事件数据不完整", data=data)
            return
        
        # 计算变更内容
        changes = self._calculate_changes(old_config, new_config)
        
        # 如果没有实际变更，跳过
        if not changes:
            logger.debug("配置无实际变更，跳过重载", module_id=module_id)
            return
        
        # 创建重载请求
        request_id = self._generate_request_id()
        priority = self.STRATEGY_PRIORITY_MAP.get(
            ReloadStrategy(reload_strategy), 
            ReloadPriority.MEDIUM
        )
        
        request = ReloadRequest(
            request_id=request_id,
            module_id=module_id,
            reload_strategy=ReloadStrategy(reload_strategy),
            priority=priority,
            old_config=old_config,
            new_config=new_config,
            changes=changes,
            source="module_config_change",
            created_at=time.time()
        )
        
        # 提交请求
        self.submit_request(request)
        
        logger.debug_struct("模块配置变更触发重载请求",
                          module_id=module_id,
                          request_id=request_id,
                          strategy=reload_strategy,
                          changes_count=len(changes))
    
    def _on_config_changed(self, event) -> None:
        """处理系统配置变更事件"""
        data = event.data
        config_key = data.get("key", "")
        
        # 检查是否是系统级配置变更
        if config_key.startswith("system."):
            # 计算变更
            old_value = data.get("old_value")
            new_value = data.get("new_value")
            
            if old_value != new_value:
                # 创建系统重载请求
                request_id = self._generate_request_id()
                
                request = ReloadRequest(
                    request_id=request_id,
                    module_id="system.config",
                    reload_strategy=ReloadStrategy.RESTART_REQUIRED,
                    priority=ReloadPriority.HIGH,
                    old_config={config_key: old_value},
                    new_config={config_key: new_value},
                    changes={config_key: {"old": old_value, "new": new_value}},
                    source="system_config_change",
                    created_at=time.time()
                )
                
                self.submit_request(request)
                
                logger.debug_struct("系统配置变更触发重载请求",
                                  config_key=config_key,
                                  request_id=request_id)
    
    def _on_plugin_state_changed(self, event) -> None:
        """处理插件状态变更事件"""
        data = event.data
        plugin_name = data.get("plugin_name")
        enabled = "enabled" in event.type  # plugin.enabled 或 plugin.disabled
        
        if plugin_name:
            # 创建插件重载请求（插件状态变更需要重启）
            request_id = self._generate_request_id()
            
            request = ReloadRequest(
                request_id=request_id,
                module_id=f"plugin.{plugin_name}",
                reload_strategy=ReloadStrategy.RESTART_REQUIRED,
                priority=ReloadPriority.HIGH,
                old_config={"enabled": not enabled},
                new_config={"enabled": enabled},
                changes={"enabled": {"old": not enabled, "new": enabled}},
                source="plugin_state_change",
                created_at=time.time()
            )
            
            self.submit_request(request)
            
            logger.debug_struct("插件状态变更触发重载请求",
                              plugin_name=plugin_name,
                              enabled=enabled,
                              request_id=request_id)
    
    def _calculate_changes(self, old_config: Dict, new_config: Dict) -> Dict[str, Any]:
        """计算配置变更"""
        changes = {}
        
        # 检查新增和修改的键
        all_keys = set(old_config.keys()) | set(new_config.keys())
        
        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)
            
            # 检查值是否不同
            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value,
                    "type": self._get_change_type(old_value, new_value)
                }
        
        return changes
    
    def _get_change_type(self, old_value, new_value) -> str:
        """获取变更类型"""
        if old_value is None:
            return "added"
        elif new_value is None:
            return "removed"
        else:
            return "modified"
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())
    
    def start(self) -> None:
        """启动热重载协调器"""
        with self._lock:
            if self._workers:
                logger.warning("热重载协调器已在运行")
                return
            
            logger.info("启动热重载协调器")
            
            # 创建工作线程
            for i in range(self._worker_count):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"HotReloadWorker-{i}",
                    daemon=True
                )
                worker.start()
                self._workers.append(worker)
            
            logger.info_struct("热重载协调器启动完成", worker_count=self._worker_count)
    
    def stop(self) -> None:
        """停止热重载协调器"""
        with self._lock:
            if not self._workers:
                return
            
            logger.info("停止热重载协调器")
            
            # 设置停止标志
            self._stop_event.set()
            
            # 等待工作线程结束
            for worker in self._workers:
                try:
                    worker.join(timeout=5.0)
                except Exception as e:
                    logger.warning(f"工作线程停止异常: {e}")
            
            self._workers.clear()
            self._stop_event.clear()
            
            # 清空队列
            while not self._request_queue.empty():
                try:
                    self._request_queue.get_nowait()
                except Empty:
                    break
            
            logger.info("热重载协调器已停止")
    
    def _worker_loop(self) -> None:
        """工作线程循环"""
        logger.debug(f"热重载工作线程启动: {threading.current_thread().name}")
        
        while not self._stop_event.is_set():
            try:
                # 从队列获取请求（阻塞，但会定期检查停止标志）
                try:
                    request = self._request_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # 处理请求
                self._process_request(request)
                
                # 标记任务完成
                self._request_queue.task_done()
                
            except Exception as e:
                logger.error(f"热重载工作线程异常: {e}", exc_info=True)
        
        logger.debug(f"热重载工作线程停止: {threading.current_thread().name}")
    
    def _process_request(self, request: ReloadRequest) -> None:
        """处理重载请求"""
        request_id = request.request_id
        
        with self._lock:
            # 更新请求状态
            request.started_at = time.time()
            request.status = ReloadStatus.IN_PROGRESS
            self._pending_requests[request_id] = request
        
        logger.debug_struct("开始处理重载请求",
                          request_id=request_id,
                          module_id=request.module_id,
                          strategy=request.reload_strategy.value)
        
        try:
            # 根据策略选择处理方法
            handler_name = self.STRATEGY_HANDLERS.get(request.reload_strategy)
            if not handler_name:
                raise ValueError(f"未知的重载策略: {request.reload_strategy}")
            
            handler = getattr(self, handler_name)
            
            # 执行重载
            success, error_message, affected_modules = handler(request)
            
            # 更新请求状态
            with self._lock:
                request.completed_at = time.time()
                request.status = ReloadStatus.SUCCESS if success else ReloadStatus.FAILED
                request.error_message = error_message
                
                # 从待处理列表中移除
                if request_id in self._pending_requests:
                    del self._pending_requests[request_id]
                
                # 记录结果
                result = ReloadResult(
                    request_id=request_id,
                    module_id=request.module_id,
                    status=request.status,
                    elapsed_time=request.elapsed_time,
                    error_message=error_message,
                    affected_modules=affected_modules
                )
                self._completed_requests[request_id] = result
                
                # 更新统计信息
                self._update_stats(result)
            
            # 发布事件
            event_data = {
                "request_id": request_id,
                "module_id": request.module_id,
                "status": request.status.value,
                "success": success,
                "elapsed_time": request.elapsed_time,
                "affected_modules": affected_modules,
                "source": request.source
            }
            
            if success:
                self._event_bus.publish("hot_reload.completed", event_data)
                logger.info_struct("重载请求处理完成",
                                 request_id=request_id,
                                 module_id=request.module_id,
                                 status="success",
                                 elapsed_time=request.elapsed_time)
            else:
                self._event_bus.publish("hot_reload.failed", event_data)
                logger.error_struct("重载请求处理失败",
                                  request_id=request_id,
                                  module_id=request.module_id,
                                  error=error_message)
            
            # 执行回调
            if success and request.on_success:
                try:
                    request.on_success()
                except Exception as e:
                    logger.error("重载成功回调执行失败", error=str(e))
            elif not success and request.on_failure:
                try:
                    request.on_failure(error_message or "未知错误")
                except Exception as e:
                    logger.error("重载失败回调执行失败", error=str(e))
            
            if request.on_complete:
                try:
                    request.on_complete(request.status)
                except Exception as e:
                    logger.error("重载完成回调执行失败", error=str(e))
        
        except Exception as e:
            # 处理过程中出现异常
            with self._lock:
                request.completed_at = time.time()
                request.status = ReloadStatus.FAILED
                request.error_message = str(e)
                
                if request_id in self._pending_requests:
                    del self._pending_requests[request_id]
                
                result = ReloadResult(
                    request_id=request_id,
                    module_id=request.module_id,
                    status=ReloadStatus.FAILED,
                    elapsed_time=request.elapsed_time,
                    error_message=str(e)
                )
                self._completed_requests[request_id] = result
                self._update_stats(result)
            
            self._event_bus.publish("hot_reload.failed", {
                "request_id": request_id,
                "module_id": request.module_id,
                "error": str(e)
            })
            
            logger.error("重载请求处理异常", exc_info=True)
    
    def _handle_immediate_reload(self, request: ReloadRequest) -> Tuple[bool, Optional[str], List[str]]:
        """处理立即重载（UI外观）"""
        try:
            # 立即重载通常是UI相关的配置
            # 这里可以触发UI更新事件
            self._event_bus.publish("ui.config.updated", {
                "module_id": request.module_id,
                "changes": request.changes,
                "new_config": request.new_config
            })
            
            # 模拟处理时间
            time.sleep(0.01)
            
            return True, None, [request.module_id]
            
        except Exception as e:
            return False, str(e), []
    
    def _handle_real_time_reload(self, request: ReloadRequest) -> Tuple[bool, Optional[str], List[str]]:
        """处理实时重载（AI参数）"""
        try:
            # 实时重载通常是AI模型参数
            # 这里可以触发AI服务更新事件
            self._event_bus.publish("ai.config.updated", {
                "module_id": request.module_id,
                "changes": request.changes,
                "new_config": request.new_config
            })
            
            # 模拟处理时间（略长于立即重载）
            time.sleep(0.05)
            
            return True, None, [request.module_id]
            
        except Exception as e:
            return False, str(e), []
    
    def _handle_restart_reload(self, request: ReloadRequest) -> Tuple[bool, Optional[str], List[str]]:
        """处理重启重载（插件/系统）"""
        try:
            # 重启重载需要更复杂的处理
            # 这里可以触发重启准备事件
            self._event_bus.publish("restart.required", {
                "module_id": request.module_id,
                "changes": request.changes,
                "reason": "配置变更需要重启"
            })
            
            # 模拟处理时间
            time.sleep(0.1)
            
            # 获取依赖模块
            affected_modules = self._get_affected_modules(request.module_id)
            
            return True, None, affected_modules
            
        except Exception as e:
            return False, str(e), []
    
    def _handle_manual_reload(self, request: ReloadRequest) -> Tuple[bool, Optional[str], List[str]]:
        """处理手动重载（需要用户确认）"""
        try:
            # 手动重载需要用户确认
            # 这里触发用户确认事件
            self._event_bus.publish("reload.confirmation.required", {
                "request_id": request.request_id,
                "module_id": request.module_id,
                "changes": request.changes,
                "description": "此变更需要用户确认"
            })
            
            # 等待用户确认（在实际实现中，这里应该是异步的）
            # 这里我们模拟用户已确认
            time.sleep(0.2)
            
            # 用户确认后，按照重启重载处理
            return self._handle_restart_reload(request)
            
        except Exception as e:
            return False, str(e), []
    
    def _get_affected_modules(self, module_id: str) -> List[str]:
        """获取受影响的模块（包括依赖模块）"""
        affected = [module_id]
        
        # 获取依赖此模块的模块
        try:
            dependents = self._module_registry.get_dependent_modules(module_id)
            affected.extend(dependents)
        except Exception as e:
            logger.warning("获取依赖模块失败", module_id=module_id, error=str(e))
        
        return list(set(affected))  # 去重
    
    def _update_stats(self, result: ReloadResult) -> None:
        """更新统计信息"""
        self._stats["total_requests"] += 1
        
        if result.status == ReloadStatus.SUCCESS:
            self._stats["successful"] += 1
        elif result.status == ReloadStatus.FAILED:
            self._stats["failed"] += 1
        elif result.status == ReloadStatus.CANCELLED:
            self._stats["cancelled"] += 1
        elif result.status == ReloadStatus.SKIPPED:
            self._stats["skipped"] += 1
        
        # 更新平均时间
        if result.elapsed_time:
            total_time = self._stats["average_time"] * (self._stats["total_requests"] - 1)
            total_time += result.elapsed_time
            self._stats["average_time"] = total_time / self._stats["total_requests"]
    
    def submit_request(self, request: ReloadRequest) -> bool:
        """提交重载请求"""
        try:
            # 检查队列是否已满
            if self._request_queue.full():
                logger.warning("重载队列已满，无法提交新请求", request_id=request.request_id)
                return False
            
            # 添加到队列
            self._request_queue.put(request)
            
            # 记录到待处理列表
            with self._lock:
                self._pending_requests[request.request_id] = request
            
            logger.debug_struct("重载请求已提交",
                              request_id=request.request_id,
                              module_id=request.module_id,
                              priority=request.priority.value)
            
            return True
            
        except Exception as e:
            logger.error("提交重载请求失败", request_id=request.request_id, error=str(e))
            return False
    
    def cancel_request(self, request_id: str) -> bool:
        """取消重载请求"""
        with self._lock:
            if request_id in self._pending_requests:
                request = self._pending_requests[request_id]
                request.status = ReloadStatus.CANCELLED
                request.completed_at = time.time()
                
                # 从队列中移除（如果还在队列中）
                # 注意：这需要遍历队列，效率较低，但请求数量通常不多
                temp_queue = Queue()
                cancelled = False
                
                while not self._request_queue.empty():
                    try:
                        item = self._request_queue.get_nowait()
                        if item.request_id == request_id:
                            cancelled = True
                        else:
                            temp_queue.put(item)
                    except Empty:
                        break
                
                # 恢复队列
                while not temp_queue.empty():
                    try:
                        self._request_queue.put(temp_queue.get_nowait())
                    except Empty:
                        break
                
                if cancelled:
                    logger.debug("重载请求已从队列中取消", request_id=request_id)
                
                # 记录结果
                result = ReloadResult(
                    request_id=request_id,
                    module_id=request.module_id,
                    status=ReloadStatus.CANCELLED,
                    elapsed_time=request.elapsed_time,
                    error_message="用户取消"
                )
                self._completed_requests[request_id] = result
                self._update_stats(result)
                
                # 发布事件
                self._event_bus.publish("hot_reload.cancelled", {
                    "request_id": request_id,
                    "module_id": request.module_id
                })
                
                logger.info_struct("重载请求已取消",
                                 request_id=request_id,
                                 module_id=request.module_id)
                
                return True
        
        logger.warning("重载请求不存在或已完成", request_id=request_id)
        return False
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """获取请求状态"""
        with self._lock:
            # 检查待处理请求
            if request_id in self._pending_requests:
                request = self._pending_requests[request_id]
                return self._request_to_dict(request)
            
            # 检查已完成请求
            if request_id in self._completed_requests:
                result = self._completed_requests[request_id]
                return self._result_to_dict(result)
        
        return None
    
    def _request_to_dict(self, request: ReloadRequest) -> Dict[str, Any]:
        """转换请求为字典"""
        return {
            "request_id": request.request_id,
            "module_id": request.module_id,
            "reload_strategy": request.reload_strategy.value,
            "priority": request.priority.value,
            "status": request.status.value,
            "created_at": request.created_at,
            "started_at": request.started_at,
            "completed_at": request.completed_at,
            "elapsed_time": request.elapsed_time,
            "waiting_time": request.waiting_time,
            "source": request.source,
            "changes_count": len(request.changes)
        }
    
    def _result_to_dict(self, result: ReloadResult) -> Dict[str, Any]:
        """转换结果为字典"""
        return {
            "request_id": result.request_id,
            "module_id": result.module_id,
            "status": result.status.value,
            "elapsed_time": result.elapsed_time,
            "error_message": result.error_message,
            "affected_modules": result.affected_modules
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self._lock:
            queue_size = self._request_queue.qsize()
            pending_count = len(self._pending_requests)
            completed_count = len(self._completed_requests)
            
            # 按优先级统计
            priority_stats = {p.value: 0 for p in ReloadPriority}
            for request in self._pending_requests.values():
                priority_stats[request.priority.value] += 1
            
            # 按策略统计
            strategy_stats = {s.value: 0 for s in ReloadStrategy}
            for request in self._pending_requests.values():
                strategy_stats[request.reload_strategy.value] += 1
            
            return {
                "queue_size": queue_size,
                "pending_count": pending_count,
                "completed_count": completed_count,
                "priority_stats": priority_stats,
                "strategy_stats": strategy_stats,
                "worker_count": self._worker_count,
                "is_running": bool(self._workers)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats.update(self.get_queue_status())
            return stats
    
    def clear_completed(self, older_than_hours: Optional[float] = None) -> int:
        """清理已完成请求"""
        with self._lock:
            current_time = time.time()
            removed_count = 0
            
            # 确定要移除的请求ID
            to_remove = []
            for request_id, result in self._completed_requests.items():
                # 如果指定了时间限制，只移除旧请求
                if older_than_hours is not None:
                    request = None
                    # 尝试从结果中获取时间信息
                    # 这里需要根据实际情况调整
                    pass
                
                # 暂时移除所有已完成请求
                to_remove.append(request_id)
            
            # 移除请求
            for request_id in to_remove:
                del self._completed_requests[request_id]
                removed_count += 1
            
            if removed_count > 0:
                logger.debug(f"清理了 {removed_count} 个已完成的重载请求")
            
            return removed_count
    
    def wait_for_completion(self, request_id: str, timeout: float = 30.0) -> bool:
        """等待请求完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_request_status(request_id)
            if status:
                if status["status"] in ["success", "failed", "cancelled", "skipped"]:
                    return True
            time.sleep(0.1)
        
        return False