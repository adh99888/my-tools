#!/usr/bin/env python3
"""
长期记忆模块
宪法依据：宪法第3条（认知对齐优先）

功能：存储永久重要信息，用户习惯，项目知识
设计约束：≤100行代码
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from .working_memory import MemoryItem, MemoryPriority

@dataclass
class LongTermItem(MemoryItem):
    """长期记忆条目（继承自MemoryItem）"""
    category: str = "general"
    importance: float = 0.5  # 0.0-1.0
    
    def __post_init__(self):
        super().__post_init__()
        # 长期记忆不设置过期时间
        self.expires_at = None

class LongTermMemory:
    """长期记忆管理器"""
    
    def __init__(self, storage_file: str = "data/memory/long_term_memory.json"):
        """
        初始化长期记忆
        
        Args:
            storage_file: 存储文件路径
        """
        self.storage_file = storage_file
        self.items: List[LongTermItem] = []
        
        storage_dir = os.path.dirname(storage_file)
        if not storage_dir:
            storage_dir = "."
        os.makedirs(storage_dir, exist_ok=True)
        self._load()
    
    def add(self, content: str, category: str = "general",
            importance: float = 0.5, priority: MemoryPriority = MemoryPriority.MEDIUM,
            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加记忆条目
        
        Args:
            content: 记忆内容
            category: 记忆类别
            importance: 重要性(0.0-1.0)
            priority: 优先级
            metadata: 附加元数据
        """
        item_id = f"ltm_{datetime.now().timestamp()}_{len(self.items)}"
        
        item = LongTermItem(
            id=item_id,
            content=content,
            priority=priority,
            created_at=datetime.now().isoformat(),
            category=category,
            importance=importance,
            metadata=metadata or {}
        )
        
        self.items.append(item)
        self._save()
        
        return item_id
    
    def get_by_category(self, category: str) -> List[LongTermItem]:
        """按类别获取记忆"""
        return [item for item in self.items if item.category == category]
    
    def get(self, item_id: str) -> Optional[LongTermItem]:
        """获取记忆条目"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def clear(self) -> None:
        """清空记忆"""
        self.items = []
        self._save()
    
    def _save(self) -> None:
        """保存到文件"""
        try:
            data = {
                "items": [asdict(item) for item in self.items],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def _load(self) -> None:
        """从文件加载"""
        if not os.path.exists(self.storage_file):
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.items = [
                LongTermItem(**item) for item in data.get("items", [])
            ]
        except Exception:
            self.items = []
    
    def __len__(self) -> int:
        return len(self.items)