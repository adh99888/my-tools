#!/usr/bin/env python3
"""
结构化日志模块
宪法依据：宪法第3条，技术执行法典第4.1条
"""

import json
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union, cast
from enum import Enum

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogType(Enum):
    """日志类型"""
    HEARTBEAT = "heartbeat"
    PROTOCOL = "protocol"
    ERROR = "error"
    DIAGNOSIS = "diagnosis"
    EVOLUTION = "evolution"
    SYSTEM = "system"

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: LogLevel
    log_type: LogType
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, log_dir: str = "logs", max_entries: int = 1000):
        """
        初始化日志记录器
        
        Args:
            log_dir: 日志目录
            max_entries: 内存中保留的最大日志条目数
        """
        self.log_dir = log_dir
        self.max_entries = max_entries
        self.in_memory_logs: List[LogEntry] = []
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 当前日志文件路径
        self.current_log_file = self._get_current_log_file()
        
        # 加载现有日志
        self._load_recent_logs()
        
    def _get_current_log_file(self) -> str:
        """获取当前日志文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"log_{date_str}.json")
        
    def _load_recent_logs(self) -> None:
        """加载最近日志"""
        try:
            if os.path.exists(self.current_log_file):
                try:
                    with open(self.current_log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"警告：日志文件损坏，跳过加载。错误: {e}")
                    return
                    
                for entry in log_data[-100:]:  # 只加载最近100条
                    try:
                        log_entry = self._dict_to_log_entry(entry)
                        self.in_memory_logs.append(log_entry)
                    except (KeyError, ValueError) as e:
                        print(f"警告：跳过无效日志条目。错误: {e}")
                        continue
                    
        except Exception as e:
            print(f"加载日志失败: {e}")
            
    def _log_entry_to_dict(self, entry: LogEntry) -> Dict[str, Any]:
        """将LogEntry转换为可JSON序列化的字典"""
        return {
            "timestamp": entry.timestamp,
            "level": entry.level.value,  # 使用枚举值而不是枚举对象
            "log_type": entry.log_type.value,  # 使用枚举值而不是枚举对象
            "message": entry.message,
            "data": entry.data,
            "source": entry.source
        }
    
    def _dict_to_log_entry(self, data: Dict[str, Any]) -> LogEntry:
        """将字典转换为LogEntry对象"""
        return LogEntry(
            timestamp=data["timestamp"],
            level=LogLevel(data["level"]),  # 从字符串创建枚举
            log_type=LogType(data["log_type"]),  # 从字符串创建枚举
            message=data["message"],
            data=data.get("data", {}),
            source=data.get("source", "system")
        )
    
    def _save_log(self, entry: LogEntry) -> None:
        """保存日志到文件"""
        try:
            # 读取现有日志
            existing_logs = []
            if os.path.exists(self.current_log_file):
                try:
                    with open(self.current_log_file, 'r', encoding='utf-8') as f:
                        existing_logs = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"警告：日志文件损坏，创建新文件。错误: {e}")
                    # 文件损坏，创建空列表
                    existing_logs = []
                    
            # 添加新日志（使用可序列化的字典）
            existing_logs.append(self._log_entry_to_dict(entry))
            
            # 保持文件大小可控（最多10000条）
            if len(existing_logs) > 10000:
                existing_logs = existing_logs[-10000:]
                
            # 写入文件
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存日志失败: {e}")
            
    def _add_log(self, level: LogLevel, log_type: LogType, 
                message: str, data: Optional[Dict[str, Any]] = None, source: str = "system") -> None:
        """添加日志条目"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            log_type=log_type,
            message=message,
            data=data or {},
            source=source
        )
        
        # 添加到内存
        self.in_memory_logs.append(entry)
        
        # 限制内存中的日志数量
        if len(self.in_memory_logs) > self.max_entries:
            self.in_memory_logs = self.in_memory_logs[-self.max_entries:]
            
        # 保存到文件
        self._save_log(entry)
        
        # 打印到控制台（根据级别）
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            print(f"[{level.value}] {message}")
            
    # ========== 公共接口 ==========
    
    def log_heartbeat(self, heartbeat_data: Dict[str, Any]) -> None:
        """记录心跳日志"""
        self._add_log(
            level=LogLevel.INFO,
            log_type=LogType.HEARTBEAT,
            message="心跳记录",
            data=heartbeat_data,
            source="heartbeat"
        )
        
    def log_protocol(self, protocol_level: str, operation: str, 
                    result: Dict[str, Any], success: bool) -> None:
        """记录协议执行日志"""
        self._add_log(
            level=LogLevel.INFO if success else LogLevel.WARNING,
            log_type=LogType.PROTOCOL,
            message=f"协议执行: {protocol_level} - {operation}",
            data={
                "protocol_level": protocol_level,
                "operation": operation,
                "result": result,
                "success": success
            },
            source="protocol_engine"
        )
        
    def log_error(self, function_name: str, error_message: str, 
                  args: Optional[tuple] = None, kwargs: Optional[dict] = None) -> None:
        """记录错误日志"""
        self._add_log(
            level=LogLevel.ERROR,
            log_type=LogType.ERROR,
            message=f"函数错误: {function_name}",
            data={
                "function": function_name,
                "error": error_message,
                "args": str(args)[:200] if args else None,
                "kwargs": str(kwargs)[:200] if kwargs else None
            },
            source=function_name
        )
        
    def log_diagnosis(self, diagnosis_data: Dict[str, Any]) -> None:
        """记录诊断日志"""
        self._add_log(
            level=LogLevel.INFO,
            log_type=LogType.DIAGNOSIS,
            message="系统诊断完成",
            data=diagnosis_data,
            source="self_diagnosis"
        )
        
    def log_evolution(self, proposal: Dict[str, Any], result: Dict[str, Any]) -> None:
        """记录进化日志"""
        self._add_log(
            level=LogLevel.INFO,
            log_type=LogType.EVOLUTION,
            message=f"进化提案: {proposal.get('title', '未知')}",
            data={
                "proposal": proposal,
                "result": result
            },
            source="evolution"
        )
        
    def log_system(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """记录系统日志"""
        self._add_log(
            level=LogLevel.INFO,
            log_type=LogType.SYSTEM,
            message=message,
            data=data or {},
            source="system"
        )
        
    # ========== 查询功能 ==========
    
    def get_recent_logs(self, limit: int = 50, log_type: Optional[LogType] = None) -> List[Dict[str, Any]]:
        """获取最近日志"""
        logs: List[LogEntry] = self.in_memory_logs[-limit:] if self.in_memory_logs else []
        
        if log_type:
            logs = [log for log in logs if log.log_type == log_type]
            
        return [asdict(log) for log in logs]
        
    def get_logs_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """获取指定日期的日志"""
        log_file = os.path.join(self.log_dir, f"log_{date_str}.json")
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    return cast(List[Dict[str, Any]], json.load(f))
        except Exception as e:
            print(f"读取日志文件失败: {e}")
            
        return []
        
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        errors = []
        for log in self.in_memory_logs:
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                log_time = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
                if log_time >= cutoff_time:
                    errors.append(asdict(log))
                    
        return {
            "total_errors": len(errors),
            "errors_by_source": self._count_by_source(errors),
            "errors_by_type": self._count_by_type(errors),
            "recent_errors": errors[-10:] if errors else []
        }
        
    def _count_by_source(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """按来源统计"""
        counts: Dict[str, int] = {}
        for log in logs:
            source = log.get("source", "unknown")
            counts[source] = counts.get(source, 0) + 1
        return counts
        
    def _count_by_type(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """按类型统计"""
        counts: Dict[str, int] = {}
        for log in logs:
            log_type = log.get("log_type", "unknown")
            counts[log_type] = counts.get(log_type, 0) + 1
        return counts
        
    # ========== 维护功能 ==========
    
    def rotate_logs(self, days_to_keep: int = 30) -> None:
        """轮转日志，删除旧文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for filename in os.listdir(self.log_dir):
                if filename.startswith("log_") and filename.endswith(".json"):
                    date_str = filename[4:-5]  # 提取日期
                    try:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if file_date < cutoff_date:
                            filepath = os.path.join(self.log_dir, filename)
                            os.remove(filepath)
                            self.log_system(f"删除旧日志文件: {filename}")
                    except ValueError:
                        continue
                        
        except Exception as e:
            self.log_error("rotate_logs", str(e))
            
    def clear_memory_logs(self) -> None:
        """清空内存中的日志（保留文件）"""
        self.in_memory_logs = []
        self.log_system("清空内存日志")
        
    def export_logs(self, output_file: str = "logs_export.json") -> bool:
        """导出日志"""
        try:
            all_logs = []
            for filename in os.listdir(self.log_dir):
                if filename.startswith("log_") and filename.endswith(".json"):
                    filepath = os.path.join(self.log_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                        all_logs.extend(logs)
                        
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_logs, f, ensure_ascii=False, indent=2)
                
            self.log_system(f"日志已导出到: {output_file}")
            return True
        except Exception as e:
            self.log_error("export_logs", str(e))
            return False

def test_logger() -> None:
    """测试日志记录器"""
    print("=== 结构化日志模块测试 ===")
    import shutil
    
    # 创建测试日志目录
    test_dir = "test_logs"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    logger = StructuredLogger(log_dir=test_dir, max_entries=100)
    
    # 测试心跳日志
    print("\n1. 测试心跳日志:")
    heartbeat_data = {
        "timestamp": datetime.now().isoformat(),
        "interval_sec": 30.0,
        "system_status": "running",
        "trust_score": 50.0
    }
    logger.log_heartbeat(heartbeat_data)
    print("   心跳日志已记录")
    
    # 测试协议日志
    print("\n2. 测试协议日志:")
    logger.log_protocol(
        protocol_level="L2",
        operation="创建日志文件",
        result={"success": True, "file_size": 1024},
        success=True
    )
    print("   协议日志已记录")
    
    # 测试错误日志
    print("\n3. 测试错误日志:")
    logger.log_error(
        function_name="test_function",
        error_message="测试错误信息",
        args=(1, 2, 3),
        kwargs={"key": "value"}
    )
    print("   错误日志已记录")
    
    # 测试查询功能
    print("\n4. 测试查询功能:")
    recent_logs = logger.get_recent_logs(limit=5)
    print(f"   最近{len(recent_logs)}条日志:")
    for log in recent_logs:
        print(f"     - {log['timestamp']} [{log['level']}] {log['message'][:30]}...")
    
    # 测试错误摘要
    print("\n5. 测试错误摘要:")
    error_summary = logger.get_error_summary(hours=24)
    print(f"   总错误数: {error_summary['total_errors']}")
    
    # 清理测试目录
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_logger()