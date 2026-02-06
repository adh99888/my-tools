#!/usr/bin/env python3
"""
心跳机制模块
宪法依据：生存保障法案第3.1条
"""

import time
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Tuple

@dataclass
class HeartbeatRecord:
    """心跳记录"""
    timestamp: str
    interval_sec: float
    system_status: str
    trust_score: float = 50.0

class HeartbeatManager:
    """心跳管理器"""
    
    def __init__(self, interval_sec: float = 30.0):
        self.interval = interval_sec
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.log_callback: Optional[Callable[[HeartbeatRecord], None]] = None  # 日志回调函数
        self.status_callback: Optional[Callable[[], Tuple[str, float]]] = None  # 状态回调函数
        
    def set_log_callback(self, callback: Callable[[HeartbeatRecord], None]) -> None:
        """设置日志回调函数"""
        self.log_callback = callback
        
    def set_status_callback(self, callback: Callable[[], Tuple[str, float]]) -> None:
        """设置状态回调函数"""
        self.status_callback = callback
        
    def start(self) -> None:
        """启动心跳线程"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        print(f"心跳机制启动 ({self.interval}秒间隔)")
        
    def stop(self) -> None:
        """停止心跳线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            
    def _heartbeat_loop(self) -> None:
        """心跳循环"""
        last_beat = time.time()
        
        while self.running:
            current_time = time.time()
            if current_time - last_beat >= self.interval:
                self._perform_heartbeat()
                last_beat = current_time
                
            time.sleep(1)  # 每秒检查一次
            
    def _perform_heartbeat(self) -> None:
        """执行单次心跳"""
        # 获取当前状态
        system_status = "unknown"
        trust_score = 50.0
        if self.status_callback:
            system_status, trust_score = self.status_callback()
            
        heartbeat = HeartbeatRecord(
            timestamp=datetime.now().isoformat(),
            interval_sec=self.interval,
            system_status=system_status,
            trust_score=trust_score
        )
        
        # 记录心跳
        if self.log_callback:
            self.log_callback(heartbeat)
            
        # 状态报告
        status_msg = (
            f"[心跳] {heartbeat.timestamp} | "
            f"状态: {system_status} | "
            f"信任分: {trust_score:.1f}"
        )
        print(status_msg)
        
    def get_record_dict(self, record: HeartbeatRecord) -> Dict[str, Any]:
        """将心跳记录转换为字典"""
        return asdict(record)