"""
事件总线系统
提供轻量级的发布-订阅机制，用于组件间解耦通信
"""

import asyncio
import threading
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from .logging import get_logger

logger = get_logger(__name__)

# 事件类
@dataclass
class Event:
    """事件对象"""
    type: str  # 事件类型
    data: Any  # 事件数据
    timestamp: datetime  # 事件时间戳
    source: Optional[str] = None  # 事件源
    
    def __init__(self, event_type: str, data: Any = None, source: Optional[str] = None):
        self.type = event_type
        self.data = data
        self.timestamp = datetime.now()
        self.source = source

# 事件回调类型
EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], Any]

class EventBus:
    """
    事件总线 - 轻量级发布订阅系统
    
    特性：
    - 支持同步和异步事件处理
    - 线程安全
    - 支持一次性订阅
    - 支持通配符事件类型
    - 事件历史记录（可选）
    """
    
    def __init__(self, max_queue_size: int = 1000, worker_threads: int = 2, 
                 enable_debug_log: bool = False, max_history: int = 100, 
                 enable_async: bool = True):
        """
        初始化事件总线
        
        Args:
            max_queue_size: 最大事件队列大小（保留参数，当前未使用）
            worker_threads: 事件处理工作线程数（保留参数，当前未使用）
            enable_debug_log: 是否启用事件调试日志（保留参数，当前未使用）
            max_history: 最大事件历史记录数（0表示不记录）
            enable_async: 是否启用异步支持
        """
        self.max_queue_size = max_queue_size
        self.worker_threads = worker_threads
        self.enable_debug_log = enable_debug_log
        
        self._subscribers: Dict[str, List[Dict]] = {}
        self._history: List[Event] = []
        self._max_history = max_history
        self._enable_async = enable_async
        self._lock = threading.RLock()
        
        # 异步事件循环（惰性初始化）
        self._loop = None
        
        logger.debug_struct("事件总线初始化完成", max_queue_size=max_queue_size, 
                          worker_threads=worker_threads, max_history=max_history)
    
    def subscribe(self, event_type: str, handler: Union[EventHandler, AsyncEventHandler], 
                  once: bool = False, priority: int = 0) -> Callable:
        """
        订阅事件
        
        Args:
            event_type: 事件类型（支持通配符，如 "chat.*"）
            handler: 事件处理函数（同步或异步）
            once: 是否只处理一次
            priority: 优先级（数值越小优先级越高）
            
        Returns:
            取消订阅的函数
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            handler_info = {
                'handler': handler,
                'once': once,
                'priority': priority,
                'is_async': asyncio.iscoroutinefunction(handler)
            }
            
            # 按优先级插入
            subscribers = self._subscribers[event_type]
            subscribers.append(handler_info)
            subscribers.sort(key=lambda x: x['priority'])
            
            logger.debug(f"事件订阅: {event_type} -> {handler.__name__} (priority: {priority})")
            
            # 返回取消订阅函数
            def unsubscribe():
                self._unsubscribe(event_type, handler_info)
            
            return unsubscribe
    
    def _unsubscribe(self, event_type: str, handler_info: Dict):
        """取消订阅（内部方法）"""
        with self._lock:
            if event_type in self._subscribers:
                subscribers = self._subscribers[event_type]
                if handler_info in subscribers:
                    subscribers.remove(handler_info)
                    logger.debug(f"事件取消订阅: {event_type}")
    
    def publish(self, event_type: str, data: Any = None, source: Optional[str] = None) -> None:
        """
        发布事件（同步）
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源标识
        """
        event = Event(event_type, data, source)
        
        # 记录历史
        if self._max_history > 0:
            with self._lock:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
        
        # 查找匹配的订阅者（包括通配符）
        matching_subscribers = []
        with self._lock:
            for pattern, subscribers in self._subscribers.items():
                if self._match_event_type(event_type, pattern):
                    matching_subscribers.extend(subscribers.copy())
        
        # 处理事件
        handlers_to_remove = []
        
        for handler_info in matching_subscribers:
            handler = handler_info['handler']
            is_async = handler_info['is_async']
            once = handler_info['once']
            
            try:
                if is_async and self._enable_async:
                    # 异步处理（在当前线程中同步调用）
                    asyncio.create_task(self._async_wrapper(handler, event))
                else:
                    # 同步处理
                    handler(event)
                
                if once:
                    handlers_to_remove.append((pattern, handler_info))
                    
            except Exception as e:
                logger.error(f"事件处理失败 [{event_type}]: {e}", exc_info=True)
        
        # 移除一次性处理函数
        for pattern, handler_info in handlers_to_remove:
            self._unsubscribe(pattern, handler_info)
        
        logger.debug(f"事件发布: {event_type} (数据: {type(data).__name__})")
    
    async def publish_async(self, event_type: str, data: Any = None, 
                           source: Optional[str] = None) -> None:
        """
        异步发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源标识
        """
        event = Event(event_type, data, source)
        
        # 记录历史
        if self._max_history > 0:
            with self._lock:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
        
        # 查找匹配的订阅者
        matching_subscribers = []
        with self._lock:
            for pattern, subscribers in self._subscribers.items():
                if self._match_event_type(event_type, pattern):
                    matching_subscribers.extend(subscribers.copy())
        
        # 异步处理事件
        tasks = []
        handlers_to_remove = []
        
        for handler_info in matching_subscribers:
            handler = handler_info['handler']
            is_async = handler_info['is_async']
            once = handler_info['once']
            
            try:
                if is_async:
                    # 异步处理函数
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                else:
                    # 同步处理函数在线程池中执行
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(None, handler, event)
                    tasks.append(task)
                
                if once:
                    handlers_to_remove.append((pattern, handler_info))
                    
            except Exception as e:
                logger.error(f"事件处理失败 [{event_type}]: {e}", exc_info=True)
        
        # 等待所有任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 移除一次性处理函数
        for pattern, handler_info in handlers_to_remove:
            self._unsubscribe(pattern, handler_info)
        
        logger.debug(f"异步事件发布: {event_type}")
    
    async def _async_wrapper(self, handler: AsyncEventHandler, event: Event):
        """异步处理包装器"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"异步事件处理失败: {e}", exc_info=True)
    
    def _match_event_type(self, event_type: str, pattern: str) -> bool:
        """检查事件类型是否匹配模式（支持通配符）"""
        if pattern == event_type:
            return True
        
        # 简单通配符匹配：chat.* 匹配 chat.message, chat.error 等
        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + '.')
        
        return False
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 10) -> List[Event]:
        """
        获取事件历史
        
        Args:
            event_type: 过滤事件类型（None表示所有类型）
            limit: 返回的最大事件数
            
        Returns:
            事件历史列表
        """
        with self._lock:
            if event_type:
                history = [e for e in self._history if e.type == event_type]
            else:
                history = self._history.copy()
            
            return history[-limit:] if limit > 0 else history
    
    def clear_history(self):
        """清除事件历史"""
        with self._lock:
            self._history.clear()
            logger.debug("事件历史已清除")
    
    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """
        获取订阅者数量
        
        Args:
            event_type: 事件类型（None表示所有类型）
            
        Returns:
            订阅者数量
        """
        with self._lock:
            if event_type:
                return len(self._subscribers.get(event_type, []))
            else:
                return sum(len(subs) for subs in self._subscribers.values())
    
    def __str__(self) -> str:
        """字符串表示"""
        count = self.get_subscriber_count()
        history_len = len(self._history)
        return f"EventBus(subscribers={count}, history={history_len})"

    def start(self):
        """启动事件总线（保留方法，用于兼容性）"""
        logger.debug("事件总线启动")

    def stop(self):
        """停止事件总线（保留方法，用于兼容性）"""
        logger.debug("事件总线停止")

    def has_pending_events(self) -> bool:
        """检查是否有待处理的事件（保留方法，用于兼容性）"""
        return False

    def process_events(self):
        """处理事件队列（保留方法，用于兼容性）"""
        pass
    
    @property
    def queue_size(self) -> int:
        """获取事件队列大小（当前未实现队列，返回0）"""
        return 0
    
    @property
    def worker_count(self) -> int:
        """获取工作线程数量"""
        return self.worker_threads