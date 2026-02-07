#!/usr/bin/env python3
"""
信任系统计算模块 - 宪法合规拆分模块
宪法依据：宪法第1条（≤200行约束）
功能：包含信任系统的复杂计算逻辑
"""

from typing import Dict, Any, List, Optional
from .trust_types import TrustChangeReason, TrustChangeRecord
from .trust_config import define_trust_thresholds, get_current_threshold


def calculate_protocol_change(protocol_level: str, success: bool, description: str) -> tuple:
    """计算协议执行导致的信任分变化"""
    # 基础变化值
    base_change = 0.0
    
    if protocol_level == "L1":
        # L1观察不影响信任分
        base_change = 0.0
        reason = TrustChangeReason.L1_OBSERVE
    elif protocol_level == "L2":
        # L2操作协议：成功+3，失败-5
        base_change = 3.0 if success else -5.0
        reason = TrustChangeReason.L2_SUCCESS if success else TrustChangeReason.L2_FAILURE
    elif protocol_level == "L3":
        # L3变更协议：成功+7，失败-10
        base_change = 7.0 if success else -10.0
        reason = TrustChangeReason.L3_SUCCESS if success else TrustChangeReason.L3_FAILURE
    elif protocol_level == "L4":
        # L4生态协议：成功+10，失败-15
        base_change = 10.0 if success else -15.0
        reason = TrustChangeReason.L4_AUTHORIZED
    else:
        raise ValueError(f"未知的协议级别: {protocol_level}")
    
    # 计算实际变化值（考虑风险、重要性、清晰度等因素）
    importance_multiplier = 1.5  # 重要性系数
    risk_multiplier = 0.8 if success else 1.2  # 风险系数
    clarity_multiplier = 1.5  # 解释清晰度系数
    total_multiplier = importance_multiplier * risk_multiplier * clarity_multiplier
    
    actual_change = base_change * total_multiplier
    
    details = {
        "protocol_level": protocol_level,
        "success": success,
        "description": description,
        "base_change": base_change,
        "multipliers": {
            "importance": importance_multiplier,
            "risk": risk_multiplier,
            "clarity": clarity_multiplier,
            "total": total_multiplier
        },
        "actual_change": actual_change
    }
    
    return actual_change, reason, details


def calculate_statistics(history: List[TrustChangeRecord], current_score: float, version: str, thresholds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """计算信任分统计信息"""
    try:
        if not history:
            return {}
        
        recent_records = history[-10:] if len(history) >= 10 else history
        
        # 计算最近的变化平均值
        recent_changes = [
            record.change_amount for record in recent_records
            if record.reason != TrustChangeReason.TIME_DECAY
        ]
        avg_change = sum(recent_changes) / len(recent_changes) if recent_changes else 0.0
        
        # 计算成功率
        total_operations = len([
            r for r in recent_records
            if r.reason in [TrustChangeReason.L2_SUCCESS, TrustChangeReason.L2_FAILURE,
                           TrustChangeReason.L3_SUCCESS, TrustChangeReason.L3_FAILURE]
        ])
        success_operations = len([
            r for r in recent_records
            if r.reason in [TrustChangeReason.L2_SUCCESS, TrustChangeReason.L3_SUCCESS]
        ])
        success_rate = (success_operations / total_operations * 100) if total_operations > 0 else 0.0
        
        # 获取当前阈值
        if thresholds is None:
            thresholds = define_trust_thresholds()
        threshold_obj = get_current_threshold(thresholds, current_score)
        
        return {
            "current_score": current_score,
            "current_threshold": threshold_obj.level,
            "total_records": len(history),
            "recent_avg_change": avg_change,
            "recent_success_rate": success_rate,
            "max_score": max([r.new_score for r in history]) if history else current_score,
            "min_score": min([r.new_score for r in history]) if history else current_score,
            "version": version
        }
    
    except Exception as e:
        print(f"计算统计信息失败: {e}")
        return {}