#!/usr/bin/env python3
"""
安全模式管理器
宪法依据：宪法第4条（生存优先原则）

功能：系统异常时进入最小化安全运行模式，仅保留核心功能
设计约束：≤100行代码
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class SafetyModeLevel(Enum):
    """安全模式级别"""
    NORMAL = "正常模式"
    DEGRADED = "降级模式"  # 部分功能受限
    SAFE = "安全模式"      # 仅核心功能
    LOCKDOWN = "锁定模式"  # 完全锁定，等待人工干预

@dataclass
class SafetyModeConfig:
    """安全模式配置"""
    level: SafetyModeLevel = SafetyModeLevel.NORMAL
    enabled_features: List[str] = None  # type: ignore
    disabled_features: List[str] = None  # type: ignore
    entered_at: Optional[str] = None
    exit_conditions: Dict[str, Any] = None  # type: ignore
    
    def __post_init__(self):
        if self.enabled_features is None:
            self.enabled_features = ["heartbeat", "logging", "constitution"]
        if self.disabled_features is None:
            self.disabled_features = ["protocol_l2", "protocol_l3", "protocol_l4", "trust_updates"]
        if self.exit_conditions is None:
            self.exit_conditions = {
                "manual_intervention_required": True,
                "min_trust_score": 70.0,
                "timeout_sec": 3600  # 1小时后自动尝试恢复
            }

class SafetyModeManager:
    """安全模式管理器"""
    
    def __init__(self, config_file: str = "data/safety_mode/config.json"):
        """
        初始化安全模式管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = SafetyModeConfig()
        
        # 确保目录存在
        config_dir = os.path.dirname(config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        
        # 加载配置
        self._load_config()
    
    def enter_safety_mode(self, level: SafetyModeLevel = SafetyModeLevel.SAFE) -> bool:
        """
        进入安全模式
        
        Args:
            level: 安全模式级别
            
        Returns:
            成功与否
        """
        try:
            self.config.level = level
            self.config.entered_at = datetime.now().isoformat()
            
            self._log(f"进入安全模式: {level.value}")
            self._apply_safety_restrictions()
            self._save_config()
            
            return True
            
        except Exception as e:
            self._log(f"进入安全模式失败: {e}", level="ERROR")
            return False
    
    def exit_safety_mode(self) -> bool:
        """退出安全模式"""
        try:
            if self.config.level == SafetyModeLevel.NORMAL:
                self._log("系统已在正常模式")
                return True
            
            self._log(f"退出安全模式: {self.config.level.value} → {SafetyModeLevel.NORMAL.value}")
            self.config.level = SafetyModeLevel.NORMAL
            self.config.entered_at = None
            
            self._remove_safety_restrictions()
            self._save_config()
            
            return True
            
        except Exception as e:
            self._log(f"退出安全模式失败: {e}", level="ERROR")
            return False
    
    def is_in_safety_mode(self) -> bool:
        """检查是否在安全模式"""
        return self.config.level != SafetyModeLevel.NORMAL
    
    def get_enabled_features(self) -> List[str]:
        """获取启用的功能列表"""
        return self.config.enabled_features.copy()
    
    def get_disabled_features(self) -> List[str]:
        """获取禁用的功能列表"""
        return self.config.disabled_features.copy()
    
    def add_enabled_feature(self, feature: str) -> None:
        """添加启用的功能"""
        if feature not in self.config.enabled_features:
            self.config.enabled_features.append(feature)
            self._save_config()
    
    def add_disabled_feature(self, feature: str) -> None:
        """添加禁用的功能"""
        if feature not in self.config.disabled_features:
            self.config.disabled_features.append(feature)
            self._save_config()
    
    def check_feature_allowed(self, feature: str) -> bool:
        """检查功能是否允许"""
        if self.config.level == SafetyModeLevel.NORMAL:
            return True
        
        if feature in self.config.disabled_features:
            self._log(f"功能被安全模式禁用: {feature}", level="WARNING")
            return False
        
        return feature in self.config.enabled_features
    
    def _apply_safety_restrictions(self) -> None:
        """应用安全限制"""
        restrictions = {
            SafetyModeLevel.DEGRADED: {
                "message": "系统降级运行，非核心功能受限",
                "actions": ["限制L3/L4协议", "降低信任分更新频率"]
            },
            SafetyModeLevel.SAFE: {
                "message": "安全模式运行，仅核心功能可用",
                "actions": ["禁用所有协议申请", "冻结信任分", "仅保留心跳和日志"]
            },
            SafetyModeLevel.LOCKDOWN: {
                "message": "系统锁定，等待人工干预",
                "actions": ["完全停止进化", "创建紧急快照", "等待用户指令"]
            }
        }
        
        if self.config.level in restrictions:
            restriction = restrictions[self.config.level]
            self._log(f"应用安全限制: {restriction['message']}")
            for action in restriction["actions"]:
                self._log(f"  - {action}")
    
    def _remove_safety_restrictions(self) -> None:
        """移除安全限制"""
        self._log("移除所有安全限制，恢复正常运行")
    
    def _load_config(self) -> None:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 转换level字符串为枚举
                if "level" in config_data:
                    level_str = config_data["level"]
                    if isinstance(level_str, str):
                        # 尝试从值查找枚举
                        for level in SafetyModeLevel:
                            if level.value == level_str:
                                config_data["level"] = level
                                break
                        else:
                            # 默认为NORMAL
                            config_data["level"] = SafetyModeLevel.NORMAL
                
                self.config = SafetyModeConfig(**config_data)
        except Exception as e:
            self._log(f"加载安全模式配置失败: {e}", level="WARNING")
    
    def _save_config(self) -> None:
        """保存配置"""
        try:
            config_dict = asdict(self.config)
            # 转换枚举为字符串值
            config_dict["level"] = self.config.level.value
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"保存安全模式配置失败: {e}", level="ERROR")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [SAFETY_MODE] [{level}] {message}"
        print(log_entry)

def test_safety_mode() -> None:
    """测试安全模式管理器"""
    print("=== 安全模式管理器测试 ===")
    
    # 创建管理器
    manager = SafetyModeManager(config_file="test_safety_config.json")
    
    # 测试进入安全模式
    print("1. 进入安全模式...")
    success = manager.enter_safety_mode(SafetyModeLevel.SAFE)
    print(f"   结果: {'成功' if success else '失败'}")
    print(f"   当前模式: {manager.config.level.value}")
    print(f"   启用的功能: {manager.get_enabled_features()}")
    print(f"   禁用的功能: {manager.get_disabled_features()}")
    
    # 测试功能检查
    print("\n2. 测试功能检查...")
    test_features = ["heartbeat", "protocol_l3", "trust_updates"]
    for feature in test_features:
        allowed = manager.check_feature_allowed(feature)
        print(f"   功能 '{feature}': {'允许' if allowed else '禁止'}")
    
    # 测试退出安全模式
    print("\n3. 退出安全模式...")
    success = manager.exit_safety_mode()
    print(f"   结果: {'成功' if success else '失败'}")
    print(f"   当前模式: {manager.config.level.value}")
    
    # 清理
    if os.path.exists("test_safety_config.json"):
        os.remove("test_safety_config.json")
    
    print("\n安全模式管理器测试完成")

if __name__ == "__main__":
    test_safety_mode()