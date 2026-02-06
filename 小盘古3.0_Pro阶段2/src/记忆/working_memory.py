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
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

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
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class WorkingMemory:
    """工作记忆管理器"""
    
    def __init__(self, max_items: int = 50, storage_file: str = "data/memory/working_memory.json"):
        """
        初始化工作记忆
        
        Args:
            max_items: 最大记忆条目数
            storage_file: 存储文件路径
        """
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
        """
        添加记忆条目
        
        Args:
            content: 记忆内容
            priority: 优先级
            expires_hours: 过期时间（小时）
            metadata: 附加元数据
            
        Returns:
            记忆ID
        """
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
        
        return item_id
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        获取指定ID的记忆条目
        
        Args:
            item_id: 记忆ID
            
        Returns:
            记忆条目或None
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def get_recent(self, limit: int = 10, priority: Optional[MemoryPriority] = None) -> List[MemoryItem]:
        """
        获取最近记忆
        
        Args:
            limit: 返回数量限制
            priority: 过滤优先级
            
        Returns:
            记忆列表（按创建时间降序）
        """
        items = self.items.copy()
        
        # 按优先级过滤
        if priority:
            items = [item for item in items if item.priority == priority]
        
        # 删除过期条目
        now = datetime.now()
        items = [
            item for item in items 
            if not item.expires_at or datetime.fromisoformat(item.expires_at) > now
        ]
        
        # 按创建时间排序
        items.sort(key=lambda x: x.created_at, reverse=True)
        
        return items[:limit]
    
    def search(self, keyword: str, limit: int = 5) -> List[MemoryItem]:
        """
        搜索记忆
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            匹配的记忆列表
        """
        keyword_lower = keyword.lower()
        matches = [
            item for item in self.items
            if keyword_lower in item.content.lower() or 
               any(keyword_lower in str(v).lower() for v in item.metadata.values())
        ]
        
        # 优先返回高优先级的
        priority_order = {MemoryPriority.HIGH: 0, MemoryPriority.MEDIUM: 1, MemoryPriority.LOW: 2}
        matches.sort(key=lambda x: priority_order[x.priority])
        
        return matches[:limit]
    
    def clear(self) -> None:
        """清空所有记忆"""
        self.items = []
        self._save()
    
    def _cleanup(self) -> None:
        """清理过期记忆和超出限制的记忆"""
        # 删除过期条目
        now = datetime.now()
        self.items = [
            item for item in self.items
            if not item.expires_at or datetime.fromisoformat(item.expires_at) > now
        ]
        
        # 如果超出最大数量，删除最低优先级的
        if len(self.items) > self.max_items:
            priority_order = {MemoryPriority.HIGH: 0, MemoryPriority.MEDIUM: 1, MemoryPriority.LOW: 2}
            self.items.sort(key=lambda x: priority_order[x.priority])
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