#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信任评分系统 - 核心实现

核心功能：
1. 初始信任分：50分
2. 基础评分算法
3. 信任分历史记录
4. 阈值检查（<30分暂停L2+申请）

设计原则：
- 信任分反映系统可靠性和安全性记录
- 每次协议执行都更新信任分
- 信任分变化透明、可审计
- 阈值机制防止高风险操作

版本：trust-v0.1.1 (创生纪元修复版)
修复内容：
- 修复第28行后缺少class TrustSystem:定义的错误
- 整合trust_system_manager和trust_system_data功能
- 简化架构，消除循环导入风险
"""

import json
import time
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
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

class TrustSystem:
    """信任评分系统"""
    
    def __init__(self, data_dir: str = "data/trust"):
        """初始化信任评分系统"""
        self.version = "trust-v0.1.1"
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "trust_history.json")
        self.config_file = os.path.join(data_dir, "trust_config.json")
        
        # 初始信任分
        self.current_score = 50.0
        
        # 信任分历史记录
        self.history: List[TrustChangeRecord] = []
        
        # 阈值定义
        self.thresholds = self._define_thresholds()
        
        # 加载历史记录
        self._load_history()
        
        # 记录初始状态
        self._record_initial_state()
    
    def _define_thresholds(self) -> Dict[str, TrustThreshold]:
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
    
    def _load_history(self) -> None:
        """加载历史记录"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                for item in history_data:
                    record = TrustChangeRecord(
                        timestamp=item["timestamp"],
                        old_score=item["old_score"],
                        new_score=item["new_score"],
                        change_amount=item["change_amount"],
                        reason=TrustChangeReason(item["reason"]),
                        operation_id=item.get("operation_id"),
                        details=item.get("details", {})
                    )
                    self.history.append(record)
                
                # 设置当前分数为最后一条记录的new_score
                if self.history:
                    self.current_score = self.history[-1].new_score
            
            except Exception as e:
                print(f"加载信任历史失败: {e}")
                # 使用默认初始分数
    
    def _save_history(self) -> None:
        """保存历史记录"""
        try:
            history_data = []
            for record in self.history:
                history_data.append({
                    "timestamp": record.timestamp,
                    "old_score": record.old_score,
                    "new_score": record.new_score,
                    "change_amount": record.change_amount,
                    "reason": record.reason.value,
                    "operation_id": record.operation_id,
                    "details": record.details
                })
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"保存信任历史失败: {e}")
    
    def _record_initial_state(self) -> None:
        """记录初始状态"""
        if not self.history:  # 只有历史为空时才记录初始状态
            initial_record = TrustChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_score=0.0,
                new_score=self.current_score,
                change_amount=self.current_score,
                reason=TrustChangeReason.SYSTEM_HEALTH,
                operation_id="INIT",
                details={"message": "系统初始化", "initial_score": self.current_score}
            )
            self.history.append(initial_record)
            self._save_history()
    
    def get_current_score(self) -> float:
        """获取当前信任分"""
        return self.current_score
    
    def get_current_threshold(self) -> TrustThreshold:
        """获取当前阈值"""
        for threshold in self.thresholds.values():
            if threshold.min_score <= self.current_score <= threshold.max_score:
                return threshold
        return self.thresholds["critical"]
    
    def get_score_history(self, limit: Optional[int] = None) -> List[TrustChangeRecord]:
        """获取信任分历史"""
        if limit:
            return self.history[-limit:]
        return list(self.history)
    
    def update_score(self, change_amount: float, reason: TrustChangeReason,
                     operation_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> bool:
        """更新信任分"""
        try:
            old_score = self.current_score
            new_score = old_score + change_amount
            
            # 限制在0-100范围内
            new_score = max(0.0, min(100.0, new_score))
            
            # 创建变化记录
            record = TrustChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_score=old_score,
                new_score=new_score,
                change_amount=change_amount,
                reason=reason,
                operation_id=operation_id,
                details=details or {}
            )
            
            # 更新历史
            self.history.append(record)
            self.current_score = new_score
            
            # 保存到文件
            self._save_history()
            
            # 检查是否需要特殊处理（如低于阈值）
            threshold = self.get_current_threshold()
            if threshold.level == "critical":
                print(f"[警告] 信任分降至{self.current_score}，进入critical状态，暂停L2+权限")
            
            return True
        
        except Exception as e:
            print(f"更新信任分失败: {e}")
            return False
    
    def apply_protocol_result(self, protocol_level: str, success: bool, description: str,
                            operation_id: Optional[str] = None) -> bool:
        """应用协议执行结果到信任分"""
        try:
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
                print(f"未知的协议级别: {protocol_level}")
                return False
            
            # 计算实际变化值（考虑风险、重要性、清晰度等因素）
            importance_multiplier = 1.5  # 重要性系数
            risk_multiplier = 0.8 if success else 1.2  # 风险系数
            clarity_multiplier = 1.5  # 解释清晰度系数
            total_multiplier = importance_multiplier * risk_multiplier * clarity_multiplier
            
            actual_change = base_change * total_multiplier
            
            # 应用变化
            return self.update_score(
                change_amount=actual_change,
                reason=reason,
                operation_id=operation_id,
                details={
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
            )
        
        except Exception as e:
            print(f"应用协议结果失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取信任分统计信息"""
        try:
            if not self.history:
                return {}
            
            recent_records = self.get_score_history(limit=10)
            
            # 计算最近10次的变化平均值
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
            
            return {
                "current_score": self.current_score,
                "current_threshold": self.get_current_threshold().level,
                "total_records": len(self.history),
                "recent_avg_change": avg_change,
                "recent_success_rate": success_rate,
                "max_score": max([r.new_score for r in self.history]) if self.history else self.current_score,
                "min_score": min([r.new_score for r in self.history]) if self.history else self.current_score,
                "version": self.version
            }
        
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}


def create_default_trust_system() -> TrustSystem:
    """创建默认信任系统"""
    return TrustSystem(data_dir="data/trust")


def test_trust_system() -> bool:
    """测试信任系统"""
    try:
        # 创建信任系统
        trust_system = create_default_trust_system()
        
        print(f"[PASS] 信任系统创建成功")
        print(f"当前信任分: {trust_system.get_current_score()}")
        print(f"当前阈值: {trust_system.get_current_threshold().level}")
        
        # 测试更新
        success = trust_system.update_score(
            change_amount=5.0,
            reason=TrustChangeReason.L2_SUCCESS,
            operation_id="TEST_001",
            details={"test": True}
        )
        
        if success:
            print(f"[PASS] 信任分更新成功: {trust_system.get_current_score()}")
        else:
            print(f"[FAIL] 信任分更新失败")
            return False
        
        # 测试统计
        stats = trust_system.get_statistics()
        print(f"统计信息: {json.dumps(stats, indent=2)}")
        
        print(f"[PASS] 所有测试通过")
        return True
        
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("信任评分系统测试")
    print("=" * 60)
    
    success = test_trust_system()
    
    print("=" * 60)
    if success:
        print("[PASS] 所有测试通过！")
    else:
        print("[FAIL] 测试失败！")
    print("=" * 60)