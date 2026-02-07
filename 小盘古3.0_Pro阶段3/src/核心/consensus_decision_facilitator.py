#!/usr/bin/env python3
"""
共识决策促进器 - 阶段四能力前移（宪法合规版）
宪法依据：宪法第1条（≤200行约束），宪法第3条（认知对齐优先）
功能：通过协商达成共识，改善决策质量
设计约束：≤200行代码
"""

from typing import Dict, Any, List, Optional
from .consensus_decision_types import (
    DecisionType, DecisionStatus, DecisionOption,
    DecisionCriteria, DecisionRecord, ConsensusResult
)


class ConsensusDecisionFacilitator:
    """共识决策促进器 - 阶段四能力前移"""
    
    def __init__(self):
        self.decision_history: List[DecisionRecord] = []
        
    def facilitate_decision(self,
                          options: List[Dict[str, Any]],
                          criteria: List[str],
                          user_preferences: Dict[str, float],
                          decision_type: str = "tactical") -> ConsensusResult:
        """促进共识决策过程"""
        # 创建决策记录
        decision_id = f"decision_{len(self.decision_history) + 1}"
        
        # 转换数据结构
        option_objs = [
            DecisionOption(id=opt.get("id", f"opt_{i}"),
                         description=opt.get("description", ""),
                         metadata=opt.get("metadata", {}),
                         estimated_impact=opt.get("estimated_impact", 0.0))
            for i, opt in enumerate(options)
        ]
        
        criteria_objs = [
            DecisionCriteria(name=crit, weight=1.0/len(criteria), direction="max")
            for crit in criteria
        ]
        
        try:
            dec_type = DecisionType(decision_type)
        except ValueError:
            dec_type = DecisionType.TACTICAL
        
        record = DecisionRecord(
            id=decision_id,
            decision_type=dec_type,
            status=DecisionStatus.FACILITATING,
            options=option_objs,
            criteria=criteria_objs,
            user_preferences=user_preferences
        )
        
        # AI分析和推荐
        ai_recommendation = self._analyze_options(record)
        record.ai_recommendation = ai_recommendation
        
        # 计算共识程度
        consensus_score = self._calculate_consensus_score(record, user_preferences)
        record.consensus_score = consensus_score
        
        # 决定是否达成共识
        if consensus_score >= 0.7:
            best_option = self._select_best_option(record, user_preferences)
            record.final_decision = best_option.id
            record.status = DecisionStatus.CONSENSUS_REACHED
            
            result = ConsensusResult(
                decision_id=decision_id,
                consensus_reached=True,
                selected_option=best_option,
                consensus_score=consensus_score,
                rationale=f"基于用户偏好和AI分析，选择选项{best_option.id}",
                ai_confidence=ai_recommendation.get("confidence", 0.5)
            )
        else:
            record.status = DecisionStatus.PROPOSED
            result = ConsensusResult(
                decision_id=decision_id,
                consensus_reached=False,
                consensus_score=consensus_score,
                rationale="共识程度不足，需要进一步协商",
                ai_confidence=ai_recommendation.get("confidence", 0.5)
            )
        
        self.decision_history.append(record)
        return result
    
    def _analyze_options(self, record: DecisionRecord) -> Dict[str, Any]:
        """分析选项"""
        # 简单实现：基于元数据估算
        scores = {}
        for option in record.options:
            impact = option.estimated_impact
            scores[option.id] = impact
        
        best_id = max(scores.keys(), key=lambda k: scores[k])
        return {
            "best_option": best_id,
            "scores": scores,
            "confidence": 0.7
        }
    
    def _calculate_consensus_score(self, record: DecisionRecord,
                                 user_prefs: Dict[str, float]) -> float:
        """计算共识程度"""
        # 简单实现：基于用户偏好和AI推荐的匹配度
        if not record.ai_recommendation or not record.options:
            return 0.5
        
        ai_best = record.ai_recommendation.get("best_option")
        if not ai_best:
            return 0.5
        
        # 计算用户对AI推荐选项的支持度
        support = 0.0
        total = len(user_prefs)
        if total > 0:
            support = sum(user_prefs.values()) / total
        
        return min(1.0, support + 0.2)
    
    def _select_best_option(self, record: DecisionRecord,
                           user_prefs: Dict[str, float]) -> DecisionOption:
        """选择最佳选项"""
        # 简单实现：选择AI推荐的选项
        if not record.options:
            raise ValueError("No options available")
        
        if not record.ai_recommendation:
            return record.options[0]
        
        best_id = record.ai_recommendation.get("best_option")
        for option in record.options:
            if option.id == best_id:
                return option
        return record.options[0]
    
    def learn_from_decision_outcome(self,
                                   decision_id: str,
                                   outcome: Dict[str, Any],
                                   user_feedback: str) -> None:
        """从决策结果中学习"""
        # 查找决策记录
        for record in self.decision_history:
            if record.id == decision_id:
                # 简单实现：根据反馈调整偏好
                if "good" in user_feedback or "success" in user_feedback:
                    # 提升对类似决策的信任
                    pass
                break
    
    def get_decision_history(self) -> List[DecisionRecord]:
        """获取决策历史"""
        return self.decision_history.copy()
    
    def clear_history(self) -> None:
        """清空决策历史"""
        self.decision_history.clear()


_global_facilitator = None

def get_consensus_facilitator() -> ConsensusDecisionFacilitator:
    """获取全局共识决策促进器实例"""
    global _global_facilitator
    if _global_facilitator is None:
        _global_facilitator = ConsensusDecisionFacilitator()
    return _global_facilitator