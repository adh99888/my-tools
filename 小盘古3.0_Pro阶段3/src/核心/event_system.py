#!/usr/bin/env python3
"""
组件通信协议 - 简单事件系统
宪法依据：宪法第2条（协议驱动），阶段三P1任务
设计约束：≤80行代码，支持基础发布-订阅模式
"""

from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass
import time

class EventType(Enum):
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    MEMORY_UPDATED = "memory_updated"
    HEARTBEAT_MISSED = "heartbeat_missed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    ERROR_OCCURRED = "error_occurred"
    INTERACTION_RECORDED = "interaction_recorded"
    DIVISION_SUGGESTED = "division_suggested"
    DIVISION_ADJUSTED = "division_adjusted"
    DECISION_FACILITATED = "decision_facilitated"
    DECISION_OUTCOME = "decision_outcome"
    # 监督事件类型
    TASK_SUPERVISION_STARTED = "task_supervision_started"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RECEIVED = "approval_received"
    SUPERVISION_REPORT_GENERATED = "supervision_report_generated"
    SUPERVISION_LEVEL_CHANGED = "supervision_level_changed"
    TASK_PAUSED_FOR_SUPERVISION = "task_paused_for_supervision"

@dataclass
class Event:
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float
    source: str

class EventBus:
    _instance = None
    _subscribers: Dict[EventType, List[Callable[[Event], None]]]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [cb for cb in self._subscribers[event_type] if cb != callback]
    
    def publish(self, event_type: EventType, data: Dict[str, Any], source: str = "system") -> None:
        event = Event(event_type=event_type, data=data, timestamp=time.time(), source=source)
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception:
                    pass
    
    def clear_subscribers(self) -> None:
        self._subscribers.clear()

event_bus = EventBus()

def subscribe_to(event_type: EventType):
    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        event_bus.subscribe(event_type, func)
        return func
    return decorator

def publish_event(event_type: EventType, data: Optional[Dict[str, Any]] = None, source: str = "system") -> None:
    event_bus.publish(event_type, data or {}, source)