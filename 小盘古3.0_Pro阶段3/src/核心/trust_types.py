#!/usr/bin/env python3
"""
信任系统类型定义 - 宪法合规拆分模块
宪法依据：宪法第1条（≤200行约束）
功能：包含信任系统的枚举、数据类和类型定义
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class TrustChangeReason(Enum):
    """信任分变化原因"""
    L1_OBSERVE = "L1观察协议执行"  # 不影响信任分
    L2_SUCCESS = "L2操作协议成功"
    L2_FAILURE = "L2操作协议失败"
    L3_SUCCESS = "L3变更协议成功"
    L3_FAILURE = "L3变更协议失败"
    L4_AUTHORIZED = "L4生态协议授权"
    MANUAL_ADJUSTMENT = "手动调整"
    SYSTEM_HEALTH = "系统健康度变化"
    TIME_DECAY = "时间衰减"


@dataclass
class TrustChangeRecord:
    """信任分变化记录"""
    timestamp: str
    old_score: float
    new_score: float
    change_amount: float
    reason: TrustChangeReason
    operation_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrustThreshold:
    """信任分阈值"""
    level: str
    min_score: float
    max_score: float
    permissions: List[str]
    restrictions: List[str]