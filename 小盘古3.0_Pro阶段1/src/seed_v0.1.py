#!/usr/bin/env python3
"""
创生种子v0.1 - 小盘古3.0_Pro的初始生命单元

核心哲学：
1. 最小生命单元原则：功能简单但进化接口完备
2. 协议驱动进化原则：为L1-L4协议预留接口
3. 认知对齐优先原则：理解意图比功能增加更重要

设计约束：
- 总行数<200行
- 依赖最小化：仅requests, pydantic, dataclasses
- 心跳间隔：30秒
- 可进化性：为7个核心功能预留扩展接口

版本：seed-v0.1.0 (创生纪元起始版)
"""

import time
import json
import sys
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
import subprocess
import platform
from enum import Enum

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# ==================== 核心数据模型 ====================

class ProtocolLevel(Enum):
    """协议级别枚举"""
    L1_OBSERVE = "L1观察协议"
    L2_OPERATE = "L2操作协议" 
    L3_CHANGE = "L3变更协议"
    L4_ECOSYSTEM = "L4生态协议"

@dataclass
class HeartbeatRecord:
    """心跳记录"""
    timestamp: str
    interval_sec: float
    system_status: str
    trust_score: float = 50.0  # 初始信任分50
    
@dataclass
class ProtocolRequest:
    """协议请求"""
    level: ProtocolLevel
    operation: str
    params: Dict[str, Any] = field(default_factory=dict)
    justification: str = ""
    
@dataclass  
class SystemDiagnosis:
    """系统诊断报告"""
    timestamp: str
    overall_health: int  # 0-100
    components: Dict[str, Dict[str, Any]]
    recommendations: List[str]

# ==================== 创生种子核心类 ====================

class GenesisSeed:
    """创生种子v0.1核心类"""
    
    def __init__(self) -> None:
        self.version = "seed-v0.1.0"
        self.start_time = datetime.now()
        self.trust_score = 50.0  # 初始信任分50
        self.heartbeat_interval = 30.0  # 30秒心跳
        
        # 进化日志
        self.evolution_logs: List[Dict[str, Any]] = []
        
        # 协议执行记录
        self.protocol_logs: List[Dict[str, Any]] = []
        
        # 心跳线程控制
        self.heartbeat_running = False
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        # 系统状态
        self.system_status = "initializing"
        
        print(f"=== 创生种子v0.1启动 ===")
        print(f"版本: {self.version}")
        print(f"启动时间: {self.start_time}")
        print(f"初始信任分: {self.trust_score}")
        print("=" * 40)
        
    # ========== 功能1: 心跳机制 ==========
    
    def start_heartbeat(self) -> None:
        """启动心跳线程"""
        if self.heartbeat_running:
            return
            
        self.heartbeat_running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        print("心跳机制启动 (30秒间隔)")
        
    def _heartbeat_loop(self) -> None:
        """心跳循环"""
        last_beat = time.time()
        
        while self.heartbeat_running:
            current_time = time.time()
            if current_time - last_beat >= self.heartbeat_interval:
                self._perform_heartbeat()
                last_beat = current_time
                
            time.sleep(1)  # 每秒检查一次
            
    def _perform_heartbeat(self) -> None:
        """执行单次心跳"""
        heartbeat = HeartbeatRecord(
            timestamp=datetime.now().isoformat(),
            interval_sec=self.heartbeat_interval,
            system_status=self.system_status,
            trust_score=self.trust_score
        )
        
        # 记录心跳
        self._log_heartbeat(heartbeat)
        
        # 简单状态报告
        status_msg = (
            f"[心跳] {heartbeat.timestamp} | "
            f"状态: {self.system_status} | "
            f"信任分: {self.trust_score:.1f}"
        )
        print(status_msg)
        
    def _log_heartbeat(self, heartbeat: HeartbeatRecord) -> None:
        """记录心跳到日志"""
        log_entry = {
            "type": "heartbeat",
            "data": asdict(heartbeat),
            "timestamp": datetime.now().isoformat()
        }
        self.evolution_logs.append(log_entry)
        
        # 保持日志不超过100条
        if len(self.evolution_logs) > 100:
            self.evolution_logs = self.evolution_logs[-100:]
            
    # ========== 功能2: 协议解析器 ==========
    
    def parse_protocol_request(self, request_text: str) -> Optional[ProtocolRequest]:
        """解析协议请求文本"""
        # 简化解析：识别L1-L4关键词
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
            # 默认L1观察
            level = ProtocolLevel.L1_OBSERVE
            
        return ProtocolRequest(
            level=level,
            operation=request_text[:50],  # 截断前50字符
            params={"raw_text": request_text},
            justification="自动解析的协议请求"
        )
        
    def execute_protocol(self, request: ProtocolRequest) -> Dict[str, Any]:
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
                result = self._execute_l2(request, result)
            elif request.level == ProtocolLevel.L3_CHANGE:
                result = self._execute_l3(request, result)
            elif request.level == ProtocolLevel.L4_ECOSYSTEM:
                result = self._execute_l4(request, result)
        except Exception as e:
            result["success"] = False
            result["message"] = f"协议执行异常: {str(e)}"
            
        # 记录协议执行
        self._log_protocol_execution(request, result)
        
        return result
        
    def _execute_l1(self, request: ProtocolRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """执行L1观察协议"""
        # L1操作：只读，不影响信任分
        result["success"] = True
        result["message"] = "L1观察协议执行成功"
        
        # 根据操作类型返回不同数据
        op_text = request.operation.lower()
        if "状态" in op_text or "status" in op_text:
            result["data"] = self._get_system_status()
        elif "诊断" in op_text or "diagnose" in op_text:
            result["data"] = self._self_diagnose()
        elif "环境" in op_text or "environment" in op_text:
            result["data"] = self._check_environment()
        else:
            result["data"] = {"info": "L1观察操作执行完成"}
            
        return result
        
    def _execute_l2(self, request: ProtocolRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """执行L2操作协议"""
        # L2操作：需要用户审批，这里模拟已批准
        result["success"] = True
        result["message"] = "L2操作协议执行成功（模拟审批通过）"
        result["data"] = {
            "trust_change": "+3.0",
            "note": "L2操作成功，信任分+3"
        }
        
        # 模拟信任分变化
        self.trust_score += 3.0
        
        return result
        
    def _execute_l3(self, request: ProtocolRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """执行L3变更协议"""
        # L3操作：高风险，需要详细论证和时光机快照
        result["success"] = True
        result["message"] = "L3变更协议执行成功（模拟创建时光机快照）"
        result["data"] = {
            "trust_change": "+5.0",
            "snapshot_created": True,
            "note": "L3变更成功，信任分+5，时光机快照已创建"
        }
        
        # 模拟信任分变化
        self.trust_score += 5.0
        
        return result
        
    def _execute_l4(self, request: ProtocolRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """执行L4生态协议"""
        # L4操作：长期授权，需要高信任度
        if self.trust_score < 70:
            result["success"] = False
            result["message"] = f"L4生态协议拒绝：信任分{self.trust_score:.1f}<70"
            return result
            
        result["success"] = True
        result["message"] = "L4生态协议执行成功（长期授权）"
        result["data"] = {
            "trust_change": "+0.0",  # L4不直接影响信任分
            "authorization_days": 30,
            "note": "L4生态协议生效，授予30天长期授权"
        }
        
        return result
        
    def _log_protocol_execution(self, request: ProtocolRequest, result: Dict[str, Any]) -> None:
        """记录协议执行日志"""
        log_entry = {
            "type": "protocol",
            "level": request.level.value,
            "operation": request.operation,
            "params": request.params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.protocol_logs.append(log_entry)
        
        # 保持日志不超过50条
        if len(self.protocol_logs) > 50:
            self.protocol_logs = self.protocol_logs[-50:]
            
    # ========== 功能3: LLM接口 ==========
    
    def call_llm_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """调用LLM API（硅基流动）"""
        if not REQUESTS_AVAILABLE:
            return {"error": "requests库未安装", "fallback": self._local_fallback(prompt)}
            
        # 简化实现：模拟API调用
        # 实际实现需要配置API密钥和端点
        
        # 模拟响应
        return {
            "success": True,
            "provider": "硅基流动（模拟）",
            "response": f"收到请求: {prompt[:50]}...",
            "cost_estimate": 0.001,
            "usage": {"prompt_tokens": len(prompt), "completion_tokens": 20}
        }
        
    def _local_fallback(self, prompt: str) -> Dict[str, Any]:
        """LLM API不可用时的本地回退"""
        return {
            "success": False,
            "provider": "本地回退",
            "response": f"LLM API不可用，请求已记录: {prompt[:30]}...",
            "note": "请安装requests库并配置API密钥"
        }
        
    # ========== 功能4: 基础行动器 ==========
    
    def execute_basic_action(self, action_type: str, **kwargs: Any) -> Dict[str, Any]:
        """执行基础行动（受限文件操作等）"""
        result = {"success": False, "action": action_type, "details": {}}
        
        try:
            if action_type == "read_file":
                result = self._action_read_file(**kwargs)
            elif action_type == "write_file":
                result = self._action_write_file(**kwargs)
            elif action_type == "run_command":
                result = self._action_run_command(**kwargs)
            elif action_type == "create_dir":
                result = self._action_create_dir(**kwargs)
            else:
                result["error"] = f"未知操作类型: {action_type}"
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    def _action_read_file(self, path: str) -> Dict[str, Any]:
        """读取文件（受限）"""
        # 安全限制：只能读取项目目录下的文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.abspath(path)
        
        if not abs_path.startswith(project_root):
            return {"success": False, "error": "文件路径超出允许范围"}
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content[:1000]}  # 限制长度
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _action_write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件（受限）"""
        # 安全限制：只能写入项目目录下的文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.abspath(path)
        
        if not abs_path.startswith(project_root):
            return {"success": False, "error": "文件路径超出允许范围"}
            
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _action_run_command(self, command: str) -> Dict[str, Any]:
        """运行命令（受限）"""
        # 安全限制：禁止危险命令
        dangerous = ["rm -rf", "format", "del /", "shutdown", "halt"]
        if any(d in command.lower() for d in dangerous):
            return {"success": False, "error": "命令被安全策略阻止"}
            
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30  # 30秒超时
            )
            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout[:500],  # 限制输出长度
                "stderr": result.stderr[:500]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "命令执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _action_create_dir(self, path: str) -> Dict[str, Any]:
        """创建目录（受限）"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.abspath(path)
        
        if not abs_path.startswith(project_root):
            return {"success": False, "error": "目录路径超出允许范围"}
            
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "created": not os.path.exists(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    # ========== 功能5: 自我诊断 ==========
    
    def _self_diagnose(self) -> Dict[str, Any]:
        """执行自我诊断"""
        diagnosis = SystemDiagnosis(
            timestamp=datetime.now().isoformat(),
            overall_health=self._calculate_health_score(),
            components={
                "heartbeat": {
                    "status": "正常" if self.heartbeat_running else "停止",
                    "score": 95 if self.heartbeat_running else 30
                },
                "protocol_engine": {
                    "status": "正常",
                    "score": 85
                },
                "trust_system": {
                    "status": "正常" if self.trust_score >= 30 else "警告",
                    "score": self.trust_score
                },
                "dependencies": {
                    "status": "检查中",
                    "score": self._check_dependencies()
                }
            },
            recommendations=self._generate_recommendations()
        )
        
        return asdict(diagnosis)
        
    def _calculate_health_score(self) -> int:
        """计算系统健康度"""
        score = 70  # 基础分
        
        if self.heartbeat_running:
            score += 10
            
        if self.trust_score >= 40:
            score += 10
            
        if REQUESTS_AVAILABLE and PYDANTIC_AVAILABLE:
            score += 10
            
        return min(score, 100)
        
    def _check_dependencies(self) -> int:
        """检查依赖状态"""
        score = 0
        if REQUESTS_AVAILABLE:
            score += 25
        if PYDANTIC_AVAILABLE:
            score += 25
            
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            score += 50
            
        return score
        
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if not REQUESTS_AVAILABLE:
            recommendations.append("安装requests库以启用LLM API功能")
        if not PYDANTIC_AVAILABLE:
            recommendations.append("安装pydantic库以增强类型安全")
        if self.trust_score < 40:
            recommendations.append("通过成功执行L2/L3操作提升信任分")
        if len(self.evolution_logs) < 10:
            recommendations.append("积累更多运行日志以支持进化决策")
            
        return recommendations
        
    # ========== 功能6: 错误处理 ==========
    
    def safe_execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """安全执行函数，捕获异常"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "function": func.__name__,
                "error": str(e),
                "args": str(args),
                "kwargs": str(kwargs)
            }
            
            # 记录错误
            self.evolution_logs.append({
                "type": "error",
                "data": error_info,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"[错误] {func.__name__}: {str(e)}")
            return None
            
    # ========== 功能7: 进化申请接口 ==========
    
    def generate_evolution_proposal(self, 
                                   title: str, 
                                   description: str,
                                   change_type: str = "enhancement") -> Dict[str, Any]:
        """生成进化提案模板"""
        proposal = {
            "title": title,
            "description": description,
            "change_type": change_type,
            "proposed_by": self.version,
            "timestamp": datetime.now().isoformat(),
            "current_trust_score": self.trust_score,
            "required_trust_score": self._get_required_trust_score(change_type),
            "sections": {
                "problem_analysis": "待填写",
                "solution_design": "待填写", 
                "risk_assessment": "待填写",
                "implementation_plan": "待填写",
                "expected_benefits": "待填写"
            },
            "protocol_level": self._map_change_to_protocol(change_type)
        }
        
        return proposal
        
    def _get_required_trust_score(self, change_type: str) -> float:
        """获取所需信任分"""
        if change_type == "bug_fix":
            return 30.0
        elif change_type == "enhancement":
            return 40.0
        elif change_type == "architecture":
            return 50.0
        elif change_type == "genetic":
            return 60.0
        else:
            return 50.0
            
    def _map_change_to_protocol(self, change_type: str) -> str:
        """映射变更类型到协议级别"""
        mapping = {
            "bug_fix": "L2操作协议",
            "enhancement": "L2操作协议",
            "architecture": "L3变更协议",
            "genetic": "L3变更协议"
        }
        return mapping.get(change_type, "L3变更协议")
        
    # ========== 辅助功能 ==========
    
    def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "version": self.version,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "trust_score": self.trust_score,
            "heartbeat_running": self.heartbeat_running,
            "evolution_logs_count": len(self.evolution_logs),
            "protocol_logs_count": len(self.protocol_logs),
            "system_status": self.system_status
        }
        
    def _check_environment(self) -> Dict[str, Any]:
        """检查运行环境"""
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "dependencies": {
                "requests": REQUESTS_AVAILABLE,
                "pydantic": PYDANTIC_AVAILABLE
            },
            "working_directory": os.getcwd(),
            "script_directory": os.path.dirname(os.path.abspath(__file__))
        }
        
    def get_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        return {
            "system": self._get_system_status(),
            "environment": self._check_environment(),
            "health": self._self_diagnose()
        }
        
# ==================== 主函数 ====================

def main() -> None:
    """主函数：演示创生种子功能"""
    seed = GenesisSeed()
    
    # 启动心跳
    seed.start_heartbeat()
    
    print("\n=== 创生种子v0.1功能演示 ===")
    
    # 演示1: 系统状态
    print("\n1. 系统状态检查:")
    status = seed._get_system_status()
    print(f"   版本: {status['version']}")
    print(f"   运行时间: {status['uptime_seconds']:.1f}秒")
    print(f"   信任分: {status['trust_score']}")
    
    # 演示2: 协议解析和执行
    print("\n2. 协议解析演示:")
    test_request = "检查系统健康状况"
    parsed = seed.parse_protocol_request(test_request)
    print(f"   请求: '{test_request}'")
    assert parsed is not None
    print(f"   解析为: {parsed.level.value}")
    
    result = seed.execute_protocol(parsed)
    print(f"   执行结果: {result['message']}")
    
    # 演示3: 自我诊断
    print("\n3. 自我诊断报告:")
    diagnosis = seed._self_diagnose()
    print(f"   总体健康度: {diagnosis['overall_health']}/100")
    for comp_name, comp_data in diagnosis['components'].items():
        print(f"   {comp_name}: {comp_data['status']} ({comp_data['score']}/100)")
    
    # 演示4: 进化提案生成
    print("\n4. 进化提案生成:")
    proposal = seed.generate_evolution_proposal(
        title="添加结构化日志系统",
        description="为创生种子添加JSON格式结构化日志，支持进化过程追踪",
        change_type="enhancement"
    )
    print(f"   提案标题: {proposal['title']}")
    print(f"   所需协议: {proposal['protocol_level']}")
    print(f"   所需信任分: {proposal['required_trust_score']} (当前: {proposal['current_trust_score']})")
    
    print("\n=== 演示完成 ===")
    print("创生种子正在运行中...")
    print("按Ctrl+C退出")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n=== 创生种子停止 ===")
        seed.heartbeat_running = False
        if seed.heartbeat_thread:
            seed.heartbeat_thread.join(timeout=2)
            
if __name__ == "__main__":
    main()