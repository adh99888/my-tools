#!/usr/bin/env python3
"""
自我诊断模块
宪法依据：宪法第3条
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any

@dataclass
class SystemDiagnosis:
    """系统诊断报告"""
    timestamp: str
    overall_health: int  # 0-100
    components: Dict[str, Dict[str, Any]]
    recommendations: List[str]

class SelfDiagnosis:
    """自我诊断器"""
    
    def diagnose(self, seed: Any) -> Dict[str, Any]:
        """执行自我诊断"""
        diagnosis = SystemDiagnosis(
            timestamp=datetime.now().isoformat(),
            overall_health=self._calculate_health_score(seed),
            components=self._get_components_status(seed),
            recommendations=self._generate_recommendations(seed)
        )
        return asdict(diagnosis)
        
    def _calculate_health_score(self, seed: Any) -> int:
        """计算系统健康度"""
        score = 70  # 基础分
        
        # 检查心跳是否运行
        if hasattr(seed, 'heartbeat') and seed.heartbeat.running:
            score += 10
            
        # 检查信任分
        if hasattr(seed, 'trust_score') and seed.trust_score >= 40:
            score += 10
            
        # 检查依赖（简化）
        try:
            import requests
            import pydantic
            score += 10
        except ImportError:
            pass
            
        return min(score, 100)
        
    def _get_components_status(self, seed: Any) -> Dict[str, Dict[str, Any]]:
        """获取组件状态"""
        components = {}
        
        # 心跳组件
        heartbeat_running = False
        if hasattr(seed, 'heartbeat'):
            heartbeat_running = seed.heartbeat.running
        components["heartbeat"] = {
            "status": "正常" if heartbeat_running else "停止",
            "score": 95 if heartbeat_running else 30
        }
        
        # 协议引擎组件
        components["protocol_engine"] = {
            "status": "正常",
            "score": 85
        }
        
        # 信任系统组件
        trust_score = getattr(seed, 'trust_score', 50.0)
        components["trust_system"] = {
            "status": "正常" if trust_score >= 30 else "警告",
            "score": int(trust_score)
        }
        
        # 依赖组件
        deps_score = self._check_dependencies()
        components["dependencies"] = {
            "status": "检查中",
            "score": deps_score
        }
        
        return components
        
    def _check_dependencies(self) -> int:
        """检查依赖状态"""
        score = 0
        try:
            import requests
            score += 25
        except ImportError:
            pass
            
        try:
            import pydantic
            score += 25
        except ImportError:
            pass
            
        # 检查Python版本
        import sys
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            score += 50
            
        return score
        
    def _generate_recommendations(self, seed: Any) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 检查依赖
        try:
            import requests
        except ImportError:
            recommendations.append("安装requests库以启用LLM API功能")
            
        try:
            import pydantic
        except ImportError:
            recommendations.append("安装pydantic库以增强类型安全")
            
        # 检查信任分
        if hasattr(seed, 'trust_score') and seed.trust_score < 40:
            recommendations.append("通过成功执行L2/L3操作提升信任分")
            
        # 检查日志数量（简化）
        if hasattr(seed, 'evolution_logs'):
            logs = getattr(seed, 'evolution_logs', [])
            if len(logs) < 10:
                recommendations.append("积累更多运行日志以支持进化决策")
                
        return recommendations