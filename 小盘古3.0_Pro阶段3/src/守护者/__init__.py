"""
死亡开关守护进程模块
宪法依据：宪法第4条（生存优先原则），生存保障法案第3.1条

核心功能：
1. 死亡开关监控：30秒无心跳自动冻结系统
2. 心跳监控：监控系统心跳文件
3. 安全模式：系统异常时进入最小化安全运行模式
"""

from .death_switch import DeathSwitch
from .heartbeat_monitor import HeartbeatMonitor
from .safety_mode import SafetyModeManager

__all__ = ["DeathSwitch", "HeartbeatMonitor", "SafetyModeManager"]