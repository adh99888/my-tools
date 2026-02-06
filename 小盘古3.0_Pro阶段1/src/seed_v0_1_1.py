#!/usr/bin/env python3
"""
创生种子v0.1.1 - 宪法合规版（≤180行）
核心哲学：最小生命单元原则，协议驱动进化，生存优先
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import asdict

# 导入模块
from src.core.heartbeat import HeartbeatManager, HeartbeatRecord
from src.core.protocol_engine import ProtocolEngine, ProtocolRequest, ProtocolLevel
from src.core.basic_actions import BasicActionExecutor
from src.core.trust_system import TrustSystem
from src.evolution.self_diagnosis import SelfDiagnosis
from src.evolution.proposal_gen import EvolutionProposalGenerator
from src.utils.logger import StructuredLogger
from src.utils.time_machine import TimeMachine

class GenesisSeed:
    """创生种子v0.1.1核心类"""
    
    def __init__(self) -> None:
        self.version = "seed-v0.1.1"
        self.start_time = datetime.now()
        self.system_status = "initializing"
        
        # 初始化模块
        self.heartbeat = HeartbeatManager(interval_sec=30.0)
        self.protocol_engine = ProtocolEngine()
        self.actions = BasicActionExecutor()
        self.trust_system = TrustSystem()
        self.diagnosis = SelfDiagnosis()
        self.proposal_gen = EvolutionProposalGenerator()
        self.logger = StructuredLogger()
        self.time_machine = TimeMachine()
        
        # 设置回调
        self.heartbeat.set_log_callback(self._log_heartbeat)
        self.heartbeat.set_status_callback(self._get_system_status_tuple)
        
        # 初始信任分 (信任系统已初始化)
        # self.trust_score = 50.0  # 使用信任系统管理
        
        print(f"=== 创生种子v0.1.1启动 ===")
        print(f"版本: {self.version}")
        print(f"启动时间: {self.start_time}")
        print(f"初始信任分: {self.trust_score}")
        print("=" * 40)
        
    def _log_heartbeat(self, record: HeartbeatRecord) -> None:
        """记录心跳回调"""
        self.logger.log_heartbeat(asdict(record))
        
    def _get_system_status_tuple(self) -> Tuple[str, float]:
        """获取系统状态回调"""
        return self.system_status, self.trust_score
        
    def start_heartbeat(self) -> None:
        """启动心跳机制"""
        self.heartbeat.start()
        
    def parse_protocol_request(self, request_text: str) -> Optional[ProtocolRequest]:
        """解析协议请求"""
        return self.protocol_engine.parse(request_text)
        
    def execute_protocol(self, request: ProtocolRequest) -> Dict[str, Any]:
        """执行协议请求"""
        result = self.protocol_engine.execute(request, self.trust_score)
        if result.get("success"):
            level_str = request.level.value[:2]
            self.trust_system.apply_protocol_result(
                protocol_level=level_str,
                success=True,
                description=request.operation,
                operation_id=f"protocol_{request.level.value}"
            )
        return result
        
    def call_llm_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """调用LLM API"""
        # 暂时使用模拟实现
        return {"response": f"收到请求: {prompt[:50]}..."}
        
    def execute_basic_action(self, action_type: str, **kwargs: Any) -> Dict[str, Any]:
        """执行基础行动"""
        return self.actions.execute(action_type, **kwargs)
        
    def self_diagnose(self) -> Dict[str, Any]:
        """执行自我诊断"""
        return self.diagnosis.diagnose(self)
        
    def generate_evolution_proposal(self, title: str, description: str,
                                   change_type: str = "enhancement") -> Dict[str, Any]:
        """生成进化提案"""
        return self.proposal_gen.generate(title, description, change_type, self.trust_score)
        
    def safe_execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.log_error(func.__name__, str(e), args, kwargs)
            return None
        
    @property
    def trust_score(self) -> float:
        """获取当前信任分"""
        return self.trust_system.get_current_score()    
    def get_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        return {
            "version": self.version,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "trust_score": self.trust_score,
            "status": self.system_status,
            "heartbeat_running": self.heartbeat.running
        }

def main() -> None:
    """主函数：演示创生种子功能"""
    seed = GenesisSeed()
    seed.start_heartbeat()
    
    print("\n=== 创生种子v0.1.1功能演示 ===")
    print("1. 系统状态检查:")
    summary = seed.get_summary()
    print(f"   版本: {summary['version']}")
    print(f"   运行时间: {summary['uptime']:.1f}秒")
    print(f"   信任分: {summary['trust_score']}")
    
    print("\n2. 协议解析演示:")
    test_request = "检查系统健康状况"
    parsed = seed.parse_protocol_request(test_request)
    if parsed:
        print(f"   请求: '{test_request}'")
        print(f"   解析为: {parsed.level.value}")
        result = seed.execute_protocol(parsed)
        print(f"   执行结果: {result.get('message', '未知')}")
    
    print("\n3. 自我诊断演示:")
    diagnosis = seed.self_diagnose()
    print(f"   总体健康度: {diagnosis.get('overall_health', 0)}/100")
    
    print("\n=== 演示完成 ===")
    print("创生种子正在运行中...")
    print("按Ctrl+C退出")
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n=== 创生种子停止 ===")
        seed.heartbeat.stop()

if __name__ == "__main__":
    main()