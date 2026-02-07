#!/usr/bin/env python3
"""
信任系统持久化模块 - 宪法合规拆分模块
宪法依据：宪法第1条（≤200行约束）
功能：处理信任系统的文件存储和历史记录管理
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from .trust_types import TrustChangeReason, TrustChangeRecord


def load_trust_history(history_file: str, data_dir: str) -> tuple[List[TrustChangeRecord], float]:
    """加载信任历史记录"""
    os.makedirs(data_dir, exist_ok=True)
    history: List[TrustChangeRecord] = []
    current_score = 50.0  # 默认初始分数
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
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
                history.append(record)
            
            # 设置当前分数为最后一条记录的new_score
            if history:
                current_score = history[-1].new_score
        
        except Exception as e:
            print(f"加载信任历史失败: {e}")
            # 使用默认初始分数
    
    return history, current_score


def save_trust_history(history: List[TrustChangeRecord], history_file: str) -> None:
    """保存信任历史记录"""
    try:
        history_data = []
        for record in history:
            history_data.append({
                "timestamp": record.timestamp,
                "old_score": record.old_score,
                "new_score": record.new_score,
                "change_amount": record.change_amount,
                "reason": record.reason.value,
                "operation_id": record.operation_id,
                "details": record.details
            })
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"保存信任历史失败: {e}")


def record_initial_state(history: List[TrustChangeRecord], current_score: float, 
                        history_file: str) -> List[TrustChangeRecord]:
    """记录初始状态"""
    if not history:  # 只有历史为空时才记录初始状态
        initial_record = TrustChangeRecord(
            timestamp=datetime.now().isoformat(),
            old_score=0.0,
            new_score=current_score,
            change_amount=current_score,
            reason=TrustChangeReason.SYSTEM_HEALTH,
            operation_id="INIT",
            details={"message": "系统初始化", "initial_score": current_score}
        )
        history.append(initial_record)
        save_trust_history(history, history_file)
    
    return history