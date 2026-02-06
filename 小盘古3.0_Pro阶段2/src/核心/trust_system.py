#!/usr/bin/env python3
"""信任评分系统 - 兼容层

版本：trust-v0.1.1
修复历史：
- 修复v0.1.0拆分时缺少class TrustSystem:定义的语法错误
- 整合trust_system_manager和trust_system_data功能
- 简化架构（4个模块→2个模块）

宪法依据：
- 技术法典第4.1条：代码质量要求
- 生存保障法案第4条：核心功能保障
"""

from .trust_system_core import (
    TrustSystem,
    TrustChangeReason, 
    TrustChangeRecord,
    TrustThreshold,
    create_default_trust_system,
    test_trust_system
)

__version__ = "trust-v0.1.1"
# 版本历史: 
# v0.1.0(558行) -> v0.1.1(修复语法错误, 拆分为2个模块, 346行)
# 修复: trust_system_core.py第28行缺少class TrustSystem:定义
# 优化: 删除trust_system_manager和trust_system_data冗余文件
# 时间: 2025-02-03 21:30

__all__ = [
    "TrustSystem",
    "TrustChangeReason",
    "TrustChangeRecord", 
    "TrustThreshold",
    "create_default_trust_system",
    "test_trust_system"
]