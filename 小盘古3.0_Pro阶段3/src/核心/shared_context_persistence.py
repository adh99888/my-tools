#!/usr/bin/env python3
"""
共享上下文持久化模块 - 阶段四能力前移
宪法依据：宪法第1条（≤200行约束）
功能：处理共享上下文的文件存储和加载
"""

import json
import os
from typing import Dict, Any, List, Tuple
from .shared_context_types import InteractionRecord, SharedContextData


def load_persisted_data(context_file: str, history_file: str, data_dir: str
                       ) -> Tuple[SharedContextData, List[InteractionRecord]]:
    """加载持久化数据"""
    os.makedirs(data_dir, exist_ok=True)
    
    # 共享上下文
    shared_context: SharedContextData = {
        "goals": [],
        "constraints": [],
        "preferences": [],
        "history": [],
        "mental_models": []
    }
    
    if os.path.exists(context_file):
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                shared_context.update(loaded)
        except Exception as e:
            print(f"加载共享上下文失败: {e}")
    
    # 交互历史
    interaction_history: List[InteractionRecord] = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                interaction_history = [
                    InteractionRecord(**record) for record in history_data
                ]
        except Exception as e:
            print(f"加载交互历史失败: {e}")
    
    return shared_context, interaction_history


def save_persisted_data(shared_context: SharedContextData,
                       interaction_history: List[InteractionRecord],
                       context_file: str,
                       history_file: str) -> None:
    """保存持久化数据"""
    try:
        # 保存共享上下文
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(shared_context, f, ensure_ascii=False, indent=2)
        
        # 保存交互历史
        history_data = [record.to_dict() for record in interaction_history]
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"保存共享上下文数据失败: {e}")