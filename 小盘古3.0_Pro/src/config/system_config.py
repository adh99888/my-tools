#!/usr/bin/env python3
"""
系统配置模块
宪法依据：技术执行法典第7章
"""

import json
import os
import shutil
import sys
import toml
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List
from pathlib import Path

@dataclass
class HeartbeatConfig:
    """心跳配置"""
    interval_sec: float = 30.0
    max_misses: int = 3
    enable_health_check: bool = True

@dataclass
class ProtocolConfig:
    """协议配置"""
    l2_approval_required: bool = True
    l3_snapshot_required: bool = True
    l4_min_trust_score: float = 70.0
    max_protocol_logs: int = 50

@dataclass
class TrustSystemConfig:
    """信任系统配置"""
    initial_score: float = 50.0
    min_score: float = 0.0
    max_score: float = 100.0
    l2_success_bonus: float = 4.0
    l2_failure_penalty: float = -8.0
    l3_success_bonus: float = 7.0
    l3_failure_penalty: float = -15.0

@dataclass
class LoggingConfig:
    """日志配置"""
    log_dir: str = "logs"
    max_entries: int = 1000
    max_file_size_mb: int = 10
    retention_days: int = 30
    enable_console_output: bool = True

@dataclass
class SnapshotConfig:
    """快照配置"""
    backup_dir: str = "backups"
    max_snapshots: int = 50
    default_include_paths: List[str] = field(default_factory=lambda: [
        "src",
        "constitution",
        "protocols",
        "tests",
        "requirements.txt",
        "pyproject.toml"
    ])

@dataclass
class SystemConfig:
    """系统配置"""
    version: str = "seed-v0.1.1"
    project_root: str = ""
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)
    protocol: ProtocolConfig = field(default_factory=ProtocolConfig)
    trust_system: TrustSystemConfig = field(default_factory=TrustSystemConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    snapshot: SnapshotConfig = field(default_factory=SnapshotConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "project_root": self.project_root,
            "heartbeat": asdict(self.heartbeat),
            "protocol": asdict(self.protocol),
            "trust_system": asdict(self.trust_system),
            "logging": asdict(self.logging),
            "snapshot": asdict(self.snapshot)
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建配置"""
        config = cls(
            version=data.get("version", "seed-v0.1.1"),
            project_root=data.get("project_root", "")
        )
        
        if "heartbeat" in data:
            config.heartbeat = HeartbeatConfig(**data["heartbeat"])
            
        if "protocol" in data:
            config.protocol = ProtocolConfig(**data["protocol"])
            
        if "trust_system" in data:
            config.trust_system = TrustSystemConfig(**data["trust_system"])
            
        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])
            
        if "snapshot" in data:
            snapshot_data = data["snapshot"]
            # 处理default_include_paths
            if "default_include_paths" in snapshot_data:
                config.snapshot = SnapshotConfig(**snapshot_data)
            else:
                config.snapshot = SnapshotConfig()
                
        return config

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "system_config.json")
        self.default_config_file = os.path.join(config_dir, "system_config.default.json")
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
    def _load_config(self) -> SystemConfig:
        """加载配置"""
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(self.config_file):
            default_config = self._create_default_config()
            self._save_config(default_config)
            return default_config
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            config = SystemConfig.from_dict(data)
            
            # 设置项目根目录（如果未设置）
            if not config.project_root:
                config.project_root = self._get_project_root()
                
            return config
            
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
            return self._create_default_config()
            
    def _save_config(self, config: SystemConfig) -> None:
        """保存配置"""
        try:
            # 保存主配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
                
            # 保存默认配置（如果不存在）
            if not os.path.exists(self.default_config_file):
                default_config = self._create_default_config()
                with open(self.default_config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config.to_dict(), f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            
    def _create_default_config(self) -> SystemConfig:
        """创建默认配置"""
        config = SystemConfig()
        config.project_root = self._get_project_root()
        return config
        
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        # 假设模块位于 src/config/，项目根目录是 src 的父目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(current_dir))
        
    def get_config(self) -> SystemConfig:
        """获取当前配置"""
        return self.config
        
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            updates: 更新数据，格式为 {"section.key": value} 或嵌套字典
            
        Returns:
            是否成功
        """
        try:
            config_dict = self.config.to_dict()
            
            # 处理扁平键
            for key, value in updates.items():
                if "." in key:
                    # 嵌套键，如 "heartbeat.interval_sec"
                    parts = key.split(".")
                    current = config_dict
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    # 顶级键
                    config_dict[key] = value
                    
            # 重新创建配置对象
            self.config = SystemConfig.from_dict(config_dict)
            
            # 保存配置
            self._save_config(self.config)
            
            return True
            
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
            
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            self.config = self._create_default_config()
            self._save_config(self.config)
            return True
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
            
    def export_config(self, output_file: str = "system_config.export.json") -> bool:
        """导出配置"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
            
    def validate_config(self) -> Dict[str, Any]:
        """验证配置"""
        issues = []
        
        # 检查心跳间隔
        if self.config.heartbeat.interval_sec < 1.0:
            issues.append("心跳间隔太短，建议≥1.0秒")
            
        if self.config.heartbeat.interval_sec > 300.0:
            issues.append("心跳间隔太长，建议≤300.0秒")
            
        # 检查信任分范围
        if self.config.trust_system.initial_score < 0 or self.config.trust_system.initial_score > 100:
            issues.append("初始信任分应在0-100范围内")
            
        # 检查日志目录是否可写
        log_dir = self.config.logging.log_dir
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                issues.append(f"日志目录无法创建: {log_dir}")
                
        # 检查备份目录是否可写
        backup_dir = self.config.snapshot.backup_dir
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir, exist_ok=True)
            except Exception:
                issues.append(f"备份目录无法创建: {backup_dir}")
                
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config_summary": {
                "heartbeat_interval": self.config.heartbeat.interval_sec,
                "initial_trust_score": self.config.trust_system.initial_score,
                "log_dir": self.config.logging.log_dir,
                "backup_dir": self.config.snapshot.backup_dir
            }
        }

def test_config_manager() -> None:
    """测试配置管理器"""
    print("=== 系统配置模块测试 ===")
    
    # 创建测试配置目录
    test_dir = "test_config"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    manager = ConfigManager(config_dir=test_dir)
    
    # 测试获取配置
    print("\n1. 测试获取配置:")
    config = manager.get_config()
    print(f"   系统版本: {config.version}")
    print(f"   心跳间隔: {config.heartbeat.interval_sec}秒")
    print(f"   初始信任分: {config.trust_system.initial_score}")
    
    # 测试验证配置
    print("\n2. 测试验证配置:")
    validation = manager.validate_config()
    print(f"   配置验证: {'通过' if validation['valid'] else '未通过'}")
    if validation['issues']:
        print(f"   问题: {validation['issues']}")
    
    # 测试更新配置
    print("\n3. 测试更新配置:")
    success = manager.update_config({
        "heartbeat.interval_sec": 45.0,
        "trust_system.initial_score": 60.0
    })
    print(f"   更新结果: {'成功' if success else '失败'}")
    
    if success:
        updated_config = manager.get_config()
        print(f"   更新后心跳间隔: {updated_config.heartbeat.interval_sec}秒")
        print(f"   更新后初始信任分: {updated_config.trust_system.initial_score}")
    
    # 测试重置配置
    print("\n4. 测试重置配置:")
    success = manager.reset_to_defaults()
    print(f"   重置结果: {'成功' if success else '失败'}")
    
    if success:
        reset_config = manager.get_config()
        print(f"   重置后心跳间隔: {reset_config.heartbeat.interval_sec}秒")
        print(f"   重置后初始信任分: {reset_config.trust_system.initial_score}")
    
    # 清理测试目录
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_config_manager()