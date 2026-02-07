#!/usr/bin/env python3
"""
协议引擎模块
宪法依据：宪法第2条
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

class ProtocolLevel(Enum):
    """协议级别枚举"""
    L1_OBSERVE = "L1观察协议"
    L2_OPERATE = "L2操作协议" 
    L3_CHANGE = "L3变更协议"
    L4_ECOSYSTEM = "L4生态协议"

@dataclass
class ProtocolRequest:
    """协议请求"""
    level: ProtocolLevel
    operation: str
    params: Dict[str, Any] = field(default_factory=dict)
    justification: str = ""

class ProtocolEngine:
    """协议引擎"""
    
    def __init__(self) -> None:
        self.execution_logs: List[Dict[str, Any]] = []
        
    def parse(self, request_text: str) -> ProtocolRequest:
        """解析协议请求文本"""
        text_lower = request_text.lower()
        
        if "观察" in text_lower or "查看" in text_lower or "检查" in text_lower:
            level = ProtocolLevel.L1_OBSERVE
        elif "操作" in text_lower or "执行" in text_lower or "运行" in text_lower:
            level = ProtocolLevel.L2_OPERATE
        elif "变更" in text_lower or "修改" in text_lower or "重构" in text_lower:
            level = ProtocolLevel.L3_CHANGE
        elif "生态" in text_lower or "授权" in text_lower or "长期" in text_lower:
            level = ProtocolLevel.L4_ECOSYSTEM
        else:
            level = ProtocolLevel.L1_OBSERVE
            
        return ProtocolRequest(
            level=level,
            operation=request_text[:50],
            params={"raw_text": request_text},
            justification="自动解析的协议请求"
        )
        
    def execute(self, request: ProtocolRequest, current_trust_score: float) -> Dict[str, Any]:
        """执行协议请求"""
        result: Dict[str, Any] = {
            "success": False,
            "level": request.level.value,
            "operation": request.operation,
            "timestamp": datetime.now().isoformat(),
            "message": "",
            "data": {}
        }
        
        try:
            if request.level == ProtocolLevel.L1_OBSERVE:
                result = self._execute_l1(request, result)
            elif request.level == ProtocolLevel.L2_OPERATE:
                result = self._execute_l2(request, result, current_trust_score)
            elif request.level == ProtocolLevel.L3_CHANGE:
                result = self._execute_l3(request, result, current_trust_score)
            elif request.level == ProtocolLevel.L4_ECOSYSTEM:
                result = self._execute_l4(request, result, current_trust_score)
        except Exception as e:
            result["success"] = False
            result["message"] = f"协议执行异常: {str(e)}"
            
        self._log_execution(request, result)
        return result
        
    def _execute_l1(self, request: ProtocolRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """执行L1观察协议"""
        result["success"] = True
        result["message"] = "L1观察协议执行成功"
        result["data"] = {"info": "L1观察操作执行完成"}
        return result
        
    def _execute_l2(self, request: ProtocolRequest, result: Dict[str, Any], 
                   trust_score: float) -> Dict[str, Any]:
        """执行L2操作协议"""
        result["success"] = True
        result["message"] = "L2操作协议执行成功（模拟审批通过）"
        result["data"] = {
            "trust_change": "+3.0",
            "note": "L2操作成功，信任分+3"
        }
        # 信任分变化由调用者处理
        return result
        
    def _execute_l3(self, request: ProtocolRequest, result: Dict[str, Any],
                   trust_score: float) -> Dict[str, Any]:
        """执行L3变更协议"""
        result["success"] = True
        result["message"] = "L3变更协议执行成功（模拟创建时光机快照）"
        result["data"] = {
            "trust_change": "+5.0",
            "snapshot_created": True,
            "note": "L3变更成功，信任分+5，时光机快照已创建"
        }
        return result
        
    def _execute_l4(self, request: ProtocolRequest, result: Dict[str, Any],
                   trust_score: float) -> Dict[str, Any]:
        """执行L4生态协议"""
        if trust_score < 70:
            result["success"] = False
            result["message"] = f"L4生态协议拒绝：信任分{trust_score:.1f}<70"
            return result
            
        result["success"] = True
        result["message"] = "L4生态协议执行成功（长期授权）"
        result["data"] = {
            "trust_change": "+0.0",
            "authorization_days": 30,
            "note": "L4生态协议生效，授予30天长期授权"
        }
        return result
        
    def _log_execution(self, request: ProtocolRequest, result: Dict[str, Any]) -> None:
        """记录协议执行日志"""
        log_entry = {
            "type": "protocol",
            "level": request.level.value,
            "operation": request.operation,
            "params": request.params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.execution_logs.append(log_entry)
        
        if len(self.execution_logs) > 50:
            self.execution_logs = self.execution_logs[-50:]