#!/usr/bin/env python3
"""
创新协调器演示模块
宪法依据：宪法第1条（≤200行约束）
功能：创新协调器的演示场景，从主模块分离以符合宪法
"""

import time
from datetime import datetime
from .event_system import EventType, publish_event
from .innovation_coordinator import get_innovation_coordinator


def demo_innovation_scenarios() -> None:
    """演示创新场景"""
    print("=== 创新协调器场景演示 ===")
    
    # 获取协调器
    coordinator = get_innovation_coordinator()
    
    print("1. 初始状态:")
    print(f"   安全模式: {coordinator.safety_mode.value}")
    
    print("\n2. 模拟心跳丢失场景:")
    # 模拟连续心跳丢失
    for i in range(1, 4):
        publish_event(EventType.HEARTBEAT_MISSED, {
            "reason": f"演示心跳丢失 #{i}",
            "source": "demo"
        })
        time.sleep(0.1)
        print(f"   心跳丢失 #{i}: 安全模式 -> {coordinator.safety_mode.value}")
    
    print("\n3. 模拟高优先级记忆更新:")
    publish_event(EventType.MEMORY_UPDATED, {
        "id": "demo_important_memory",
        "content": "这是非常重要的系统配置信息",
        "priority": "high",
        "source": "demo"
    })
    print("   高优先级记忆检测完成，应触发自动备份")
    
    print("\n4. 模拟错误累积:")
    errors = ["数据库连接失败", "内存不足警告", "网络延迟过高", 
              "API响应超时", "磁盘空间不足"]
    for i, error in enumerate(errors[:4], 1):
        publish_event(EventType.ERROR_OCCURRED, {
            "error": f"演示错误 #{i}: {error}",
            "severity": "warning",
            "source": "demo"
        })
        time.sleep(0.05)
        print(f"   错误 #{i}: 安全模式 -> {coordinator.safety_mode.value}")
    
    print("\n5. 显示最终状态:")
    status = coordinator.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n6. 重置协调器:")
    coordinator.reset()
    print(f"   重置后安全模式: {coordinator.safety_mode.value}")
    
    print("=== 演示完成 ===")


if __name__ == "__main__":
    demo_innovation_scenarios()