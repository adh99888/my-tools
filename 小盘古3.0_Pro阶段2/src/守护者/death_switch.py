#!/usr/bin/env python3
"""
死亡开关守护进程
宪法依据：宪法第4条（生存优先原则），生存保障法案第3.1条

功能：监控系统心跳和主进程，30秒无心跳自动冻结系统
设计约束：≤180行代码，双重验证机制（文件+进程监控）
"""

import os
import sys
import json
import time
import signal
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

class DeathSwitch:
    """死亡开关守护进程"""
    
    def __init__(self, 
                 heartbeat_file: str = "data/heartbeat/last_beat.json",
                 pid_file: str = "data/pid/main.pid",
                 check_interval: int = 5,  # 检查间隔秒数
                 max_misses: int = 6,      # 30秒/5秒=6次
                 log_dir: str = "logs/guardian"):
        """
        初始化死亡开关
        
        Args:
            heartbeat_file: 心跳文件路径
            pid_file: 主进程PID文件路径
            check_interval: 检查间隔秒数
            max_misses: 最大连续丢失次数（检查间隔×最大次数=30秒）
            log_dir: 日志目录
        """
        self.heartbeat_file = heartbeat_file
        self.pid_file = pid_file
        self.check_interval = check_interval
        self.max_misses = max_misses
        self.log_dir = log_dir
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 监控状态
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.consecutive_misses = 0
        self.last_heartbeat_time: Optional[datetime] = None
        self.last_check_time: Optional[datetime] = None
        
        # 安全模式管理器
        self.safety_mode_enabled = False
        
        # 创建心跳文件目录
        heartbeat_dir = os.path.dirname(heartbeat_file)
        if heartbeat_dir:
            os.makedirs(heartbeat_dir, exist_ok=True)
    
    def start(self) -> bool:
        """启动死亡开关守护进程"""
        if self.running:
            self._log("死亡开关已经在运行")
            return False
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            daemon=True,
            name="DeathSwitchMonitor"
        )
        self.monitor_thread.start()
        
        self._log(f"死亡开关启动，检查间隔{self.check_interval}秒，最大丢失次数{self.max_misses}")
        return True
    
    def stop(self) -> None:
        """停止死亡开关守护进程"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
            self._log("死亡开关停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.running:
            try:
                self._check_system()
                time.sleep(self.check_interval)
            except Exception as e:
                self._log(f"监控循环异常: {e}", level="ERROR")
                time.sleep(self.check_interval)
    
    def _check_system(self) -> None:
        """检查系统健康状况"""
        self.last_check_time = datetime.now()
        
        # 双重验证：心跳文件 + 进程状态
        heartbeat_ok = self._check_heartbeat()
        process_ok = self._check_process()
        
        if heartbeat_ok and process_ok:
            # 系统正常
            if self.consecutive_misses > 0:
                self._log(f"系统恢复，连续丢失次数重置: {self.consecutive_misses} → 0")
                self.consecutive_misses = 0
            return
        
        # 至少一个检查失败
        self.consecutive_misses += 1
        self._log(f"系统检查失败: 心跳={heartbeat_ok}, 进程={process_ok}, 连续丢失={self.consecutive_misses}/{self.max_misses}")
        
        # 达到最大连续丢失次数
        if self.consecutive_misses >= self.max_misses:
            self._log(f"触发死亡开关: 连续{self.consecutive_misses}次检查失败，系统冻结", level="CRITICAL")
            self._activate_death_switch()
    
    def _check_heartbeat(self) -> bool:
        """检查心跳文件"""
        try:
            if not os.path.exists(self.heartbeat_file):
                self._log(f"心跳文件不存在: {self.heartbeat_file}", level="WARNING")
                return False
            
            with open(self.heartbeat_file, 'r', encoding='utf-8') as f:
                heartbeat_data = json.load(f)
            
            # 验证心跳数据
            timestamp_str = heartbeat_data.get('timestamp')
            if not timestamp_str:
                self._log("心跳文件缺少时间戳", level="WARNING")
                return False
            
            try:
                heartbeat_time = datetime.fromisoformat(timestamp_str)
                self.last_heartbeat_time = heartbeat_time
                
                # 检查是否在30秒内
                time_diff = (datetime.now() - heartbeat_time).total_seconds()
                if time_diff > 30:
                    self._log(f"心跳超时: {time_diff:.1f}秒 > 30秒", level="WARNING")
                    return False
                
                return True
                
            except ValueError as e:
                self._log(f"心跳时间戳格式错误: {e}", level="WARNING")
                return False
                
        except json.JSONDecodeError as e:
            self._log(f"心跳文件JSON解析错误: {e}", level="ERROR")
            return False
        except Exception as e:
            self._log(f"检查心跳异常: {e}", level="ERROR")
            return False
    
    def _check_process(self) -> bool:
        """检查主进程状态"""
        try:
            if not os.path.exists(self.pid_file):
                self._log(f"PID文件不存在: {self.pid_file}", level="WARNING")
                return False
            
            with open(self.pid_file, 'r', encoding='utf-8') as f:
                pid_str = f.read().strip()
            
            if not pid_str:
                self._log("PID文件为空", level="WARNING")
                return False
            
            pid = int(pid_str)
            
            # 检查进程是否存在
            try:
                os.kill(pid, 0)  # 发送信号0检查进程是否存在
                return True
            except OSError:
                self._log(f"进程不存在或无法访问: PID={pid}", level="WARNING")
                return False
                
        except ValueError as e:
            self._log(f"PID格式错误: {e}", level="ERROR")
            return False
        except Exception as e:
            self._log(f"检查进程异常: {e}", level="ERROR")
            return False
    
    def _activate_death_switch(self) -> None:
        """激活死亡开关（冻结系统）"""
        try:
            self._log("开始执行系统冻结流程...", level="CRITICAL")
            
            # 1. 发送SIGTERM信号给主进程
            self._terminate_main_process()
            
            # 2. 创建紧急快照
            self._create_emergency_snapshot()
            
            # 3. 进入安全模式
            self._enter_safety_mode()
            
            # 4. 记录冻结事件
            self._log_freeze_event()
            
            self._log("系统冻结完成，进入安全模式", level="CRITICAL")
            
        except Exception as e:
            self._log(f"激活死亡开关异常: {e}", level="CRITICAL")
    
    def _terminate_main_process(self) -> bool:
        """终止主进程"""
        try:
            if not os.path.exists(self.pid_file):
                self._log("PID文件不存在，无法终止进程", level="ERROR")
                return False
            
            with open(self.pid_file, 'r', encoding='utf-8') as f:
                pid = int(f.read().strip())
            
            self._log(f"发送SIGTERM信号到主进程: PID={pid}")
            os.kill(pid, signal.SIGTERM)
            
            # 等待5秒优雅关闭
            time.sleep(5)
            
            # 检查是否仍然存活
            try:
                os.kill(pid, 0)
                self._log(f"进程仍在运行，尝试强制终止: PID={pid}")
                # Windows不支持SIGKILL，使用其他方法
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                 capture_output=True, timeout=5)
                else:
                    os.kill(pid, signal.SIGKILL)
                self._log("进程已强制终止")
            except (OSError, subprocess.TimeoutExpired):
                self._log("进程已优雅终止")
            
            return True
            
        except Exception as e:
            self._log(f"终止进程异常: {e}", level="ERROR")
            return False
    
    def _create_emergency_snapshot(self) -> bool:
        """创建紧急快照"""
        try:
            from ..工具.time_machine import TimeMachine
            
            time_machine = TimeMachine(backup_dir="backups", max_snapshots=50)
            success, snapshot_id = time_machine.create_snapshot(
                description="死亡开关紧急快照 - 系统冻结前状态",
                protocol_level="L3",
                operation_id="death_switch_emergency",
                trust_score=100.0
            )
            
            if success:
                self._log(f"紧急快照创建成功: {snapshot_id}")
                return True
            else:
                self._log(f"紧急快照创建失败: {snapshot_id}", level="ERROR")
                return False
                
        except Exception as e:
            self._log(f"创建紧急快照异常: {e}", level="ERROR")
            return False
    
    def _enter_safety_mode(self) -> None:
        """进入安全模式"""
        self.safety_mode_enabled = True
        self._log("进入安全模式: 仅保留心跳监控和日志功能")
        
        # 在这里可以添加安全模式的具体逻辑
        # 例如：禁用L2-L4协议申请，冻结信任分更新等
    
    def _log_freeze_event(self) -> None:
        """记录冻结事件"""
        freeze_event = {
            "timestamp": datetime.now().isoformat(),
            "event": "death_switch_activated",
            "consecutive_misses": self.consecutive_misses,
            "last_heartbeat_time": self.last_heartbeat_time.isoformat() if self.last_heartbeat_time else None,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "safety_mode_enabled": self.safety_mode_enabled
        }
        
        log_file = os.path.join(self.log_dir, "freeze_events.json")
        try:
            # 读取现有事件
            events = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
            
            # 添加新事件
            events.append(freeze_event)
            
            # 写入文件
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            
            self._log(f"冻结事件记录到: {log_file}")
            
        except Exception as e:
            self._log(f"记录冻结事件异常: {e}", level="ERROR")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 控制台输出
        print(log_entry)
        
        # 文件日志
        log_file = os.path.join(self.log_dir, f"death_switch_{datetime.now().strftime('%Y%m%d')}.log")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"[ERROR] 写入日志文件失败: {e}")

def test_death_switch() -> None:
    """测试死亡开关"""
    print("=== 死亡开关测试 ===")
    
    # 创建测试心跳文件
    heartbeat_file = "test_heartbeat.json"
    heartbeat_data = {
        "pid": os.getpid(),
        "timestamp": datetime.now().isoformat(),
        "system_status": "normal",
        "trust_score": 100.0
    }
    
    with open(heartbeat_file, 'w', encoding='utf-8') as f:
        json.dump(heartbeat_data, f, indent=2)
    
    # 创建测试PID文件
    pid_file = "test_pid.pid"
    with open(pid_file, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    
    # 创建死亡开关实例
    death_switch = DeathSwitch(
        heartbeat_file=heartbeat_file,
        pid_file=pid_file,
        check_interval=2,  # 测试用2秒间隔
        max_misses=3       # 测试用3次丢失
    )
    
    # 启动死亡开关
    death_switch.start()
    print("死亡开关已启动，等待10秒...")
    time.sleep(10)
    
    # 停止死亡开关
    death_switch.stop()
    
    # 清理测试文件
    os.remove(heartbeat_file)
    os.remove(pid_file)
    
    print("死亡开关测试完成")

if __name__ == "__main__":
    test_death_switch()