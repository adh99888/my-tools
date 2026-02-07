#!/usr/bin/env python3
"""
工作记忆模块
宪法依据：宪法第3条（认知对齐优先），技术法典第4.1条

功能：存储短期工作任务、上下文信息、用户偏好
设计约束：≤150行代码，支持优先级管理
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from .semantic_enhancer import SemanticEnhancer
from ..核心.event_system import EventType, publish_event

class MemoryPriority(Enum):
    """记忆优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class MemoryItem:
    """记忆条目"""
    id: str
    content: str
    priority: MemoryPriority
    created_at: str
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class WorkingMemory:
    """工作记忆管理器"""
    PRIORITY_ORDER = {MemoryPriority.HIGH: 0, MemoryPriority.MEDIUM: 1, MemoryPriority.LOW: 2}
    def __init__(self, max_items: int = 50, storage_file: str = "data/memory/working_memory.json"):
        """初始化工作记忆"""
        self.max_items = max_items
        self.storage_file = storage_file
        self.items: List[MemoryItem] = []
        
        # 确保存储目录存在
        storage_dir = os.path.dirname(storage_file)
        if not storage_dir:
            storage_dir = "."
        os.makedirs(storage_dir, exist_ok=True)
        
        # 加载已有记忆
        self._load()
    
    def add(self, content: str, priority: MemoryPriority = MemoryPriority.MEDIUM, 
            expires_hours: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加记忆条目并返回ID"""
        # 生成ID
        item_id = f"wm_{datetime.now().timestamp()}_{len(self.items)}"
        
        # 计算过期时间
        expires_at = None
        if expires_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        # 创建记忆条目
        item = MemoryItem(
            id=item_id,
            content=content,
            priority=priority,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # 添加到记忆
        self.items.append(item)
        
        # 如果超出最大数量，删除最低优先级的
        self._cleanup()
        
        # 保存到文件
        self._save()
        
        # 发布记忆更新事件
        publish_event(EventType.MEMORY_UPDATED, {
            "id": item_id,
            "content": content[:50] + "..." if len(content) > 50 else content,
            "priority": priority.value,
            "source": "working_memory"
        })
        
        return item_id
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """获取指定ID的记忆条目"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def get_recent(self, limit: int = 10, priority: Optional[MemoryPriority] = None) -> List[MemoryItem]:
        items = self.items.copy()
        if priority:
            items = [item for item in items if item.priority == priority]
        now = datetime.now()
        items = [item for item in items 
                if not item.expires_at or datetime.fromisoformat(item.expires_at) > now]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
    
    def search(self, keyword: str, limit: int = 5) -> List[MemoryItem]:
        keyword_lower = keyword.lower()
        matches = [
            item for item in self.items
            if keyword_lower in item.content.lower() or 
                (item.metadata and any(keyword_lower in str(v).lower() for v in item.metadata.values()))
        ]
        matches.sort(key=lambda x: self.PRIORITY_ORDER[x.priority])
        return matches[:limit]
    
    def semantic_search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """语义搜索：基于同义词扩展"""
        enhancer = SemanticEnhancer()
        contents = [item.content for item in self.items]
        results = enhancer.semantic_search(query, contents, limit)
        content_to_item = {item.content: item for item in self.items}
        return [content_to_item[content] for content, _ in results if content in content_to_item]
    
    def clear(self) -> None:
        """清空所有记忆"""
        self.items = []
        self._save()
    
    def _cleanup(self) -> None:
        now = datetime.now()
        self.items = [item for item in self.items
                      if not item.expires_at or datetime.fromisoformat(item.expires_at) > now]
        if len(self.items) > self.max_items:
            self.items.sort(key=lambda x: self.PRIORITY_ORDER[x.priority])
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
                MemoryItem(**item) for item in data.get("items", [])
            ]
        except Exception:
            self.items = []
    
    def __len__(self) -> int:
        """返回记忆数量"""
        return len(self.items)