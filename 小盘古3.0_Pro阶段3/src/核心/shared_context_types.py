#!/usr/bin/env python3
"""
共享上下文类型定义 - 阶段四能力前移
宪法依据：宪法第1条（≤200行约束）
功能：定义共享上下文管理器使用的数据类
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List


@dataclass
class InteractionRecord:
    """交互记录"""
    timestamp: str
    user_input: str
    ai_response: str
    extracted_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# 共享上下文数据结构类型定义
SharedContextData = Dict[str, List]  # 简化定义