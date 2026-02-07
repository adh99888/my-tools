#!/usr/bin/env python3
"""
安全模式定义 - 创新协调器子模块
宪法依据：宪法第1条（≤200行约束）
功能：安全模式枚举和基础转换逻辑
"""

from enum import Enum
from datetime import datetime
import time
from .event_system import EventType, publish_event


class SafetyMode(Enum):
    """安全模式级别"""
    NORMAL = "normal"
    DEGRADED = "degraded"  # 降级模式：减少非核心功能
    SAFE = "safe"          # 安全模式：只保留核心功能
    EMERGENCY = "emergency" # 紧急模式：准备关闭


def create_safety_mode_change_event(old_mode: SafetyMode, new_mode: SafetyMode) -> dict:
    """创建安全模式变更事件数据"""
    return {
        "id": f"safety_mode_change_{int(time.time())}",
        "content": f"安全模式变更: {old_mode.value} -> {new_mode.value}",
        "priority": "high",
        "source": "innovation_coordinator",
        "metadata": {
            "old_mode": old_mode.value,
            "new_mode": new_mode.value,
            "timestamp": datetime.now().isoformat()
        }
    }


def publish_safety_mode_change(old_mode: SafetyMode, new_mode: SafetyMode) -> None:
    """发布安全模式变更事件"""
    if old_mode != new_mode:
        event_data = create_safety_mode_change_event(old_mode, new_mode)
        publish_event(EventType.MEMORY_UPDATED, event_data)