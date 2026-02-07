#!/usr/bin/env python3
"""
创新协调器助手模块 - 宪法合规拆分
宪法依据：宪法第1条（≤200行约束）
功能：包含创新协调器的辅助方法，从主模块分离
"""

from datetime import datetime
from typing import Dict, Any
import json
import os
import time
from .event_system import EventType, publish_event


def set_safety_mode(old_mode, new_mode, coordinator) -> None:
    """设置安全模式并发布事件"""
    if old_mode != new_mode:
        coordinator.safety_mode = new_mode
        print(f"[创新协调器] 安全模式变更: {old_mode.value} -> {new_mode.value}")
        
        # 发布安全模式变更事件
        publish_event(EventType.MEMORY_UPDATED, {
            "id": f"safety_mode_change_{int(time.time())}",
            "content": f"安全模式变更: {old_mode.value} -> {new_mode.value}",
            "priority": "high",
            "source": "innovation_coordinator",
            "metadata": {
                "old_mode": old_mode.value,
                "new_mode": new_mode.value,
                "timestamp": datetime.now().isoformat()
            }
        })


def backup_high_priority_memory(backup_dir: str, memory_id: str, data: Dict[str, Any], coordinator) -> None:
    """备份高优先级记忆到文件"""
    try:
        backup_file = os.path.join(backup_dir, f"memory_backup_{memory_id}_{int(time.time())}.json")
        
        backup_data = {
            "memory_id": memory_id,
            "data": data,
            "backup_time": datetime.now().isoformat(),
            "reason": "high_priority_auto_backup"
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        coordinator.last_backup_time = datetime.now()
        print(f"[创新协调器] 高优先级记忆已备份到: {backup_file}")
        
    except Exception as e:
        print(f"[创新协调器] 备份失败: {e}")


def get_status(coordinator) -> Dict[str, Any]:
    """获取协调器状态"""
    return {
        "safety_mode": coordinator.safety_mode.value,
        "consecutive_heartbeat_misses": coordinator.consecutive_heartbeat_misses,
        "error_count": coordinator.error_count,
        "last_backup_time": coordinator.last_backup_time.isoformat() if coordinator.last_backup_time else None,
        "active_retries": len(coordinator.retry_count)
    }


def reset_coordinator(coordinator, default_safety_mode) -> None:
    """重置协调器状态"""
    coordinator.consecutive_heartbeat_misses = 0
    coordinator.error_count = 0
    coordinator.retry_count.clear()
    coordinator.safety_mode = default_safety_mode
    print(f"[创新协调器] 状态已重置")