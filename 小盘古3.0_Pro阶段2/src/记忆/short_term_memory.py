#!/usr/bin/env python3
"""
短期记忆模块
宪法依据：宪法第3条（认知对齐优先）

功能：存储会话期间的重要信息，24-48小时有效期
设计约束：≤100行代码
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from .working_memory import MemoryItem, MemoryPriority

@dataclass
class ShortTermItem(MemoryItem):
    """短期记忆条目（继承自MemoryItem）"""
    access_count: int = 0
    last_accessed: str = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.last_accessed is None:
            self.last_accessed = datetime.now().isoformat()

class ShortTermMemory:
    """短期记忆管理器"""
    
    def __init__(self, max_items: int = 100, storage_file: str = "data/memory/short_term_memory.json"):
        """
        初始化短期记忆
        
        Args:
            max_items: 最大记忆条目数
            storage_file: 存储文件路径
        """
        self.max_items = max_items
        self.storage_file = storage_file
        self.items: List[ShortTermItem] = []
        
        storage_dir = os.path.dirname(storage_file)
        if not storage_dir:
            storage_dir = "."
        os.makedirs(storage_dir, exist_ok=True)
        self._load()
    
    def add(self, content: str, priority: MemoryPriority = MemoryPriority.MEDIUM,
            expires_hours: float = 24.0, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加记忆条目"""
        item_id = f"stm_{datetime.now().timestamp()}_{len(self.items)}"
        
        expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        item = ShortTermItem(
            id=item_id,
            content=content,
            priority=priority,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self.items.append(item)
        self._cleanup()
        self._save()
        
        return item_id
    
    def get(self, item_id: str) -> Optional[ShortTermItem]:
        """获取记忆条目"""
        for item in self.items:
            if item.id == item_id:
                item.access_count += 1
                item.last_accessed = datetime.now().isoformat()
                self._save()
                return item
        return None
    
    def clear(self) -> None:
        """清空记忆"""
        self.items = []
        self._save()
    
    def _cleanup(self) -> None:
        """清理过期和超出限制的记忆"""
        now = datetime.now()
        self.items = [
            item for item in self.items
            if datetime.fromisoformat(item.expires_at) > now
        ]
        
        if len(self.items) > self.max_items:
            # 按访问次数排序，保留最常访问的
            self.items.sort(key=lambda x: x.access_count, reverse=True)
            self.items = self.items[:self.max_items]
    
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
                ShortTermItem(**item) for item in data.get("items", [])
            ]
        except Exception:
            self.items = []
    
    def __len__(self) -> int:
        return len(self.items)