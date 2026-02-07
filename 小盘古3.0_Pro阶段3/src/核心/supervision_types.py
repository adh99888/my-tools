#!/usr/bin/env python3
"""
监督机制类型定义
宪法依据：宪法第2条（协议驱动），阶段二用户监督机制设计
设计约束：≤200行代码，包含所有监督相关数据结构
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import time

class ApprovalType(Enum):
    """审批点类型"""
    START_APPROVAL = "start_approval"
    CRITICAL_STEP_APPROVAL = "critical_step_approval"
    EXCEPTION_APPROVAL = "exception_approval"
    COMPLETION_CONFIRMATION = "completion_confirmation"

class ApprovalStatus(Enum):
    """审批状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    MODIFIED = "modified"

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"         # 计划内小偏差
    MEDIUM = "medium"   # 计划外但可控
    HIGH = "high"       # 可能影响系统稳定
    CRITICAL = "critical"  # 威胁系统生存

@dataclass
class TaskStep:
    """任务步骤"""
    step_id: str
    step_name: str
    description: str
    requires_approval: bool
    approval_type: Optional[ApprovalType]
    estimated_duration: float  # 分钟
    dependencies: List[str]  # 依赖的步骤ID

@dataclass
class SupervisedTask:
    """监督任务"""
    task_id: str
    user_id: str
    goal: str
    steps: List[TaskStep]
    current_step_index: int
    progress: float  # 0-100
    status: str  # pending, running, paused, completed, failed
    start_time: float
    estimated_completion_time: float
    trust_score: float  # 启动时的信任分
    supervision_level: str  # high, medium, low
    approval_pending: List[str]  # 待审批的审批点ID
    completion_confirmation_pending: bool

@dataclass
class ApprovalRequest:
    """审批请求"""
    approval_id: str
    task_id: str
    approval_type: ApprovalType
    request_time: float
    data: Dict[str, Any]
    status: ApprovalStatus
    user_decision: Optional[str]
    user_notes: Optional[str]
    response_time: Optional[float]

@dataclass
class SupervisionReport:
    """监督报告"""
    report_id: str
    task_id: str
    generation_time: float
    report_type: str  # progress, risk, completion, summary
    content: Dict[str, Any]
    recommendations: List[str]
    user_actions_required: bool

@dataclass
class SupervisionConfig:
    """监督配置"""
    trust_score: float
    approval_frequency: str  # each_step, critical_steps, milestones, final
    report_frequency: int  # 分钟
    autonomous_decision_range: str  # none, low_risk, medium_risk, most
    risk_handling_policy: Dict[RiskLevel, str]

def get_default_supervision_config(trust_score: float) -> SupervisionConfig:
    """根据信任分获取默认监督配置"""
    if trust_score < 30:
        return SupervisionConfig(
            trust_score=trust_score,
            approval_frequency="each_step",
            report_frequency=2,  # 每2分钟
            autonomous_decision_range="none",
            risk_handling_policy={
                RiskLevel.LOW: "log_and_continue",
                RiskLevel.MEDIUM: "pause_and_wait",
                RiskLevel.HIGH: "pause_and_wait",
                RiskLevel.CRITICAL: "auto_abort"
            }
        )
    elif trust_score < 60:
        return SupervisionConfig(
            trust_score=trust_score,
            approval_frequency="critical_steps",
            report_frequency=5,
            autonomous_decision_range="low_risk",
            risk_handling_policy={
                RiskLevel.LOW: "log_and_continue",
                RiskLevel.MEDIUM: "notify_and_optional",
                RiskLevel.HIGH: "pause_and_wait",
                RiskLevel.CRITICAL: "auto_abort"
            }
        )
    elif trust_score < 80:
        return SupervisionConfig(
            trust_score=trust_score,
            approval_frequency="milestones",
            report_frequency=15,
            autonomous_decision_range="medium_risk",
            risk_handling_policy={
                RiskLevel.LOW: "log_and_continue",
                RiskLevel.MEDIUM: "notify_and_optional",
                RiskLevel.HIGH: "pause_and_wait",
                RiskLevel.CRITICAL: "auto_abort"
            }
        )
    else:
        return SupervisionConfig(
            trust_score=trust_score,
            approval_frequency="final",
            report_frequency=30,
            autonomous_decision_range="most",
            risk_handling_policy={
                RiskLevel.LOW: "log_and_continue",
                RiskLevel.MEDIUM: "notify_and_optional",
                RiskLevel.HIGH: "pause_and_wait",
                RiskLevel.CRITICAL: "auto_abort"
            }
        )