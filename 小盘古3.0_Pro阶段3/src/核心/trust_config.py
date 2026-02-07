#!/usr/bin/env python3
"""
信任系统配置模块 - 宪法合规拆分模块
宪法依据：宪法第1条（≤200行约束）
功能：包含信任系统的阈值配置和配置管理
"""

from typing import Dict
from .trust_types import TrustThreshold


def define_trust_thresholds() -> Dict[str, TrustThreshold]:
    """定义信任分阈值"""
    return {
        "critical": TrustThreshold(
            level="critical",
            min_score=0.0,
            max_score=29.9,
            permissions=["L1观察协议"],
            restrictions=["暂停所有L2/L3/L4协议申请", "需要紧急修复"]
        ),
        "low": TrustThreshold(
            level="low",
            min_score=30.0,
            max_score=49.9,
            permissions=["L1观察协议", "L2操作协议"],
            restrictions=["L3变更协议需要特别批准", "L4生态协议不可申请"]
        ),
        "medium": TrustThreshold(
            level="medium",
            min_score=50.0,
            max_score=69.9,
            permissions=["L1观察协议", "L2操作协议", "L3变更协议"],
            restrictions=["L4生态协议需要≥70分"]
        ),
        "high": TrustThreshold(
            level="high",
            min_score=70.0,
            max_score=89.9,
            permissions=["L1观察协议", "L2操作协议", "L3变更协议", "L4生态协议申请资格"],
            restrictions=["需要稳定30天才能获得长期授权"]
        ),
        "excellent": TrustThreshold(
            level="excellent",
            min_score=90.0,
            max_score=100.0,
            permissions=["所有协议权限", "长期授权资格", "简化审批流程"],
            restrictions=["无"]
        )
    }


def get_current_threshold(thresholds: Dict[str, TrustThreshold], current_score: float) -> TrustThreshold:
    """获取当前阈值"""
    for threshold in thresholds.values():
        if threshold.min_score <= current_score <= threshold.max_score:
            return threshold
    return thresholds["critical"]