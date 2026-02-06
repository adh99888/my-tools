#!/usr/bin/env python3
"""
进化提案生成模块
宪法依据：宪法第2条，进化伦理法案第3.2条
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from ..核心.protocol_engine import ProtocolLevel

class ChangeType(Enum):
    """变更类型枚举"""
    BUG_FIX = "bug_fix"
    ENHANCEMENT = "enhancement"
    ARCHITECTURE = "architecture"
    GENETIC = "genetic"

@dataclass
class EvolutionProposal:
    """进化提案数据结构"""
    title: str
    description: str
    change_type: str
    proposed_by: str
    timestamp: str
    current_trust_score: float
    required_trust_score: float
    sections: Dict[str, str]
    protocol_level: str

class EvolutionProposalGenerator:
    """进化提案生成器"""
    
    def generate(self, title: str, description: str, 
                change_type: str = "enhancement", 
                current_trust_score: float = 50.0) -> Dict[str, Any]:
        """
        生成进化提案
        
        Args:
            title: 提案标题
            description: 提案描述
            change_type: 变更类型 (bug_fix, enhancement, architecture, genetic)
            current_trust_score: 当前信任分
            
        Returns:
            进化提案字典
        """
        proposal = EvolutionProposal(
            title=title,
            description=description,
            change_type=change_type,
            proposed_by="evolution-proposal-gen-v0.1",
            timestamp=datetime.now().isoformat(),
            current_trust_score=current_trust_score,
            required_trust_score=self._get_required_trust_score(change_type),
            sections=self._create_proposal_sections(),
            protocol_level=self._map_change_to_protocol(change_type)
        )
        
        return asdict(proposal)
        
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
            "bug_fix": ProtocolLevel.L2_OPERATE.value,
            "enhancement": ProtocolLevel.L2_OPERATE.value,
            "architecture": ProtocolLevel.L3_CHANGE.value,
            "genetic": ProtocolLevel.L3_CHANGE.value
        }
        return mapping.get(change_type, ProtocolLevel.L3_CHANGE.value)
        
    def _create_proposal_sections(self) -> Dict[str, str]:
        """创建提案章节模板"""
        return {
            "problem_analysis": "待填写",
            "solution_design": "待填写",
            "risk_assessment": "待填写",
            "implementation_plan": "待填写",
            "expected_benefits": "待填写"
        }
        
    def create_detailed_proposal(self, title: str, description: str,
                                problem_analysis: str, solution_design: str,
                                risk_assessment: str, implementation_plan: str,
                                expected_benefits: str, change_type: str = "enhancement",
                                current_trust_score: float = 50.0) -> Dict[str, Any]:
        """创建详细进化提案"""
        proposal = self.generate(title, description, change_type, current_trust_score)
        proposal["sections"] = {
            "problem_analysis": problem_analysis,
            "solution_design": solution_design,
            "risk_assessment": risk_assessment,
            "implementation_plan": implementation_plan,
            "expected_benefits": expected_benefits
        }
        return proposal
        
    def validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """验证提案完整性"""
        required_fields = ["title", "description", "change_type", "timestamp", 
                          "current_trust_score", "required_trust_score", "protocol_level"]
        
        missing = [field for field in required_fields if field not in proposal]
        
        if missing:
            return {"valid": False, "missing_fields": missing}
            
        # 检查信任分是否足够
        if proposal["current_trust_score"] < proposal["required_trust_score"]:
            return {
                "valid": False,
                "reason": f"信任分不足: 当前{proposal['current_trust_score']:.1f}, 需要{proposal['required_trust_score']:.1f}"
            }
            
        # 检查章节完整性
        sections = proposal.get("sections", {})
        if not sections:
            return {"valid": False, "reason": "提案章节为空"}
            
        empty_sections = [name for name, content in sections.items() if not content or content == "待填写"]
        if empty_sections:
            return {"valid": True, "warning": f"以下章节为空: {empty_sections}"}
            
        return {"valid": True, "reason": "提案完整有效"}

def test_proposal_generator() -> None:
    """测试提案生成器"""
    print("=== 进化提案生成器测试 ===")
    
    generator = EvolutionProposalGenerator()
    
    # 测试基础提案生成
    print("\n1. 测试基础提案生成:")
    proposal = generator.generate(
        title="添加结构化日志系统",
        description="为创生种子添加JSON格式结构化日志，支持进化过程追踪",
        change_type="enhancement",
        current_trust_score=50.0
    )
    
    print(f"   提案标题: {proposal['title']}")
    print(f"   变更类型: {proposal['change_type']}")
    print(f"   所需协议: {proposal['protocol_level']}")
    print(f"   所需信任分: {proposal['required_trust_score']} (当前: {proposal['current_trust_score']})")
    
    # 测试提案验证
    print("\n2. 测试提案验证:")
    validation = generator.validate_proposal(proposal)
    print(f"   验证结果: {'有效' if validation['valid'] else '无效'}")
    if not validation['valid']:
        print(f"   原因: {validation.get('reason', '未知')}")
    elif 'warning' in validation:
        print(f"   警告: {validation['warning']}")
    
    # 测试详细提案
    print("\n3. 测试详细提案:")
    detailed = generator.create_detailed_proposal(
        title="重构创生种子架构",
        description="将种子拆分为模块化架构，提高可进化性",
        problem_analysis="当前种子670行严重超标，违反宪法第1条",
        solution_design="重构为≤180行核心种子 + 模块化架构",
        risk_assessment="重构过程中可能引入新bug，需要完整测试",
        implementation_plan="1. 分析现有代码 2. 设计模块结构 3. 逐步迁移功能",
        expected_benefits="符合宪法要求，提高可维护性和进化性",
        change_type="architecture",
        current_trust_score=50.0
    )
    
    print(f"   提案标题: {detailed['title']}")
    print(f"   问题分析: {detailed['sections']['problem_analysis'][:50]}...")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_proposal_generator()