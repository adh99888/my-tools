#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信任评分系统 - 核心实现（宪法合规版）
宪法依据：宪法第1条（≤200行约束）

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

版本：trust-v0.1.2（宪法合规拆分版）
修复内容：
- 类型定义拆分到trust_types.py
- 持久化逻辑拆分到trust_persistence.py
- 配置管理拆分到trust_config.py
- 计算逻辑拆分到trust_calculations.py
- 辅助函数拆分到trust_helpers.py
- 主类保持≤200行，符合宪法第1条
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from .trust_types import TrustChangeReason, TrustChangeRecord, TrustThreshold
from .trust_persistence import load_trust_history, save_trust_history, record_initial_state
from .trust_config import define_trust_thresholds, get_current_threshold
from .trust_calculations import calculate_protocol_change, calculate_statistics


class TrustSystem:
    """信任评分系统（宪法合规版）"""
    
    def __init__(self, data_dir: str = "data/trust"):
        """初始化信任评分系统"""
        self.version = "trust-v0.1.2"
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "trust_history.json")
        self.config_file = os.path.join(data_dir, "trust_config.json")
        
        # 阈值定义
        self.thresholds = define_trust_thresholds()
        
        # 加载历史记录
        self.history, self.current_score = load_trust_history(self.history_file, data_dir)
        
        # 记录初始状态（如果需要）
        self.history = record_initial_state(self.history, self.current_score, self.history_file)
    
    def get_current_score(self) -> float:
        """获取当前信任分"""
        return self.current_score
    
    def get_current_threshold(self) -> TrustThreshold:
        """获取当前阈值"""
        return get_current_threshold(self.thresholds, self.current_score)
    
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
            save_trust_history(self.history, self.history_file)
            
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
            # 使用计算模块
            actual_change, reason, details = calculate_protocol_change(
                protocol_level, success, description
            )
            
            # 应用变化
            return self.update_score(
                change_amount=actual_change,
                reason=reason,
                operation_id=operation_id,
                details=details
            )
        
        except Exception as e:
            print(f"应用协议结果失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取信任分统计信息"""
        return calculate_statistics(self.history, self.current_score, self.version, self.thresholds)


# 向后兼容性：导出辅助函数
from .trust_helpers import create_default_trust_system, test_trust_system

__all__ = [
    "TrustSystem",
    "TrustChangeReason", 
    "TrustChangeRecord",
    "TrustThreshold",
    "create_default_trust_system",
    "test_trust_system"
]