#!/usr/bin/env python3
"""
心跳监控器
宪法依据：生存保障法案第3.1条

功能：监控和管理心跳文件，提供心跳统计和告警
设计约束：≤120行代码
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from ..核心.event_system import EventType, publish_event

@dataclass
class HeartbeatStats:
    """心跳统计信息"""
    total_beats: int = 0
    last_beat_time: Optional[str] = None
    avg_interval_sec: float = 0.0
    min_interval_sec: float = float('inf')
    max_interval_sec: float = 0.0
    missed_beats: int = 0
    system_uptime_sec: float = 0.0

class HeartbeatMonitor:
    """心跳监控器"""
    
    def __init__(self, 
                 heartbeat_file: str = "data/heartbeat/last_beat.json",
                 stats_file: str = "data/heartbeat/stats.json",
                 max_age_sec: float = 30.0):
        """
        初始化心跳监控器
        
        Args:
            heartbeat_file: 心跳文件路径
            stats_file: 统计文件路径
            max_age_sec: 最大心跳年龄（秒）
        """
        self.heartbeat_file = heartbeat_file
        self.stats_file = stats_file
        self.max_age_sec = max_age_sec
        
        # 确保目录存在
        heartbeat_dir = os.path.dirname(heartbeat_file)
        if heartbeat_dir:
            os.makedirs(heartbeat_dir, exist_ok=True)
        
        stats_dir = os.path.dirname(stats_file)
        if stats_dir:
            os.makedirs(stats_dir, exist_ok=True)
        
        # 初始化统计
        self.stats = HeartbeatStats()
        self._load_stats()
        self.last_beat_timestamp: Optional[datetime] = None
    
    def write_heartbeat(self, 
                       pid: int,
                       system_status: str = "normal",
                       trust_score: float = 100.0,
                       additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        写入心跳文件
        
        Args:
            pid: 进程ID
            system_status: 系统状态
            trust_score: 信任分
            additional_data: 额外数据
            
        Returns:
            成功与否
        """
        try:
            heartbeat_data = {
                "pid": pid,
                "timestamp": datetime.now().isoformat(),
                "system_status": system_status,
                "trust_score": trust_score,
                "checksum": ""
            }
            
            if additional_data:
                heartbeat_data.update(additional_data)
            
            # 计算校验和（排除checksum字段本身）
            # 创建副本并移除checksum字段进行计算
            checksum_data = heartbeat_data.copy()
            checksum_data.pop('checksum', None)
            data_str = json.dumps(checksum_data, sort_keys=True, ensure_ascii=False)
            heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
            
            # 写入文件
            with open(self.heartbeat_file, 'w', encoding='utf-8') as f:
                json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
            
            # 更新统计
            self._update_stats()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 写入心跳文件失败: {e}")
            return False
    
    def check_heartbeat(self) -> Tuple[bool, Optional[str], float]:
        """
        检查心跳状态
        
        Returns:
            (是否正常, 错误信息, 年龄秒数)
        """
        try:
            if not os.path.exists(self.heartbeat_file):
                publish_event(EventType.HEARTBEAT_MISSED, {
                    "reason": "心跳文件不存在",
                    "source": "heartbeat_monitor"
                })
                return False, "心跳文件不存在", 0.0
            
            with open(self.heartbeat_file, 'r', encoding='utf-8') as f:
                heartbeat_data = json.load(f)
            
            # 验证校验和
            checksum = heartbeat_data.pop('checksum', '')
            data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
            expected_checksum = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
            
            if checksum != expected_checksum:
                publish_event(EventType.HEARTBEAT_MISSED, {
                    "reason": "心跳文件校验和错误",
                    "source": "heartbeat_monitor"
                })
                return False, "心跳文件校验和错误", 0.0
            
            # 检查时间戳
            timestamp_str = heartbeat_data.get('timestamp')
            if not timestamp_str:
                publish_event(EventType.HEARTBEAT_MISSED, {
                    "reason": "心跳文件缺少时间戳",
                    "source": "heartbeat_monitor"
                })
                return False, "心跳文件缺少时间戳", 0.0
            
            try:
                heartbeat_time = datetime.fromisoformat(timestamp_str)
                age_sec = (datetime.now() - heartbeat_time).total_seconds()
                
                if age_sec > self.max_age_sec:
                    publish_event(EventType.HEARTBEAT_MISSED, {
                        "reason": f"心跳超时 ({age_sec:.1f}秒 > {self.max_age_sec}秒)",
                        "age_sec": age_sec,
                        "max_age_sec": self.max_age_sec,
                        "source": "heartbeat_monitor"
                    })
                    return False, f"心跳超时 ({age_sec:.1f}秒 > {self.max_age_sec}秒)", age_sec
                
                self.last_beat_timestamp = heartbeat_time
                return True, None, age_sec
                
            except ValueError as e:
                publish_event(EventType.HEARTBEAT_MISSED, {
                    "reason": f"时间戳格式错误: {e}",
                    "source": "heartbeat_monitor"
                })
                return False, f"时间戳格式错误: {e}", 0.0
                
        except json.JSONDecodeError as e:
            publish_event(EventType.HEARTBEAT_MISSED, {
                "reason": f"JSON解析错误: {e}",
                "source": "heartbeat_monitor"
            })
            return False, f"JSON解析错误: {e}", 0.0
        except Exception as e:
            publish_event(EventType.HEARTBEAT_MISSED, {
                "reason": f"检查心跳异常: {e}",
                "source": "heartbeat_monitor"
            })
            return False, f"检查心跳异常: {e}", 0.0
    
    def get_stats(self) -> HeartbeatStats:
        """获取心跳统计"""
        return self.stats
    
    def reset_stats(self) -> None:
        """重置统计"""
        self.stats = HeartbeatStats()
        self._save_stats()
    
    def _update_stats(self) -> None:
        """更新统计信息"""
        current_time = datetime.now()
        
        if self.last_beat_timestamp:
            interval = (current_time - self.last_beat_timestamp).total_seconds()
            
            # 更新统计
            self.stats.total_beats += 1
            
            if self.stats.min_interval_sec > interval:
                self.stats.min_interval_sec = interval
            
            if self.stats.max_interval_sec < interval:
                self.stats.max_interval_sec = interval
            
            # 计算平均间隔
            if self.stats.total_beats > 1:
                total_time = self.stats.avg_interval_sec * (self.stats.total_beats - 1)
                self.stats.avg_interval_sec = (total_time + interval) / self.stats.total_beats
            else:
                self.stats.avg_interval_sec = interval
        
        self.last_beat_timestamp = current_time
        self.stats.last_beat_time = current_time.isoformat()
        
        # 保存统计
        self._save_stats()
    
    def _load_stats(self) -> None:
        """加载统计信息"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats_data = json.load(f)
                
                self.stats = HeartbeatStats(**stats_data)
        except Exception as e:
            print(f"[WARNING] 加载统计信息失败: {e}")
    
    def _save_stats(self) -> None:
        """保存统计信息"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] 保存统计信息失败: {e}")

def test_heartbeat_monitor() -> None:
    """测试心跳监控器"""
    print("=== 心跳监控器测试 ===")
    
    # 创建监控器
    monitor = HeartbeatMonitor(
        heartbeat_file="test_heartbeat.json",
        stats_file="test_stats.json",
        max_age_sec=5.0
    )
    
    # 写入心跳
    success = monitor.write_heartbeat(
        pid=os.getpid(),
        system_status="testing",
        trust_score=95.5,
        additional_data={"test": True}
    )
    
    print(f"写入心跳: {'成功' if success else '失败'}")
    
    # 检查心跳
    ok, error, age = monitor.check_heartbeat()
    print(f"检查心跳: {'正常' if ok else '异常'} (年龄: {age:.1f}秒)")
    if error:
        print(f"错误信息: {error}")
    
    # 获取统计
    stats = monitor.get_stats()
    print(f"心跳统计: 总次数={stats.total_beats}, 平均间隔={stats.avg_interval_sec:.1f}秒")
    
    # 清理
    if os.path.exists("test_heartbeat.json"):
        os.remove("test_heartbeat.json")
    if os.path.exists("test_stats.json"):
        os.remove("test_stats.json")
    
    print("心跳监控器测试完成")

if __name__ == "__main__":
    test_heartbeat_monitor()