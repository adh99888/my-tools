#!/usr/bin/env python3
"""
意图识别器 - 认知对齐核心模块
宪法依据：宪法第3条（认知对齐优先），阶段三标准1
功能：识别用户意图（对话/执行/澄清/建议），支持模糊指令理解
设计约束：≤200行代码，符合宪法第1条
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re
from ..核心.event_system import publish_event, EventType

class IntentType(Enum):
    """意图类型"""
    DIALOGUE = "dialogue"       # 纯对话
    EXECUTE = "execute"         # 执行任务
    CLARIFY = "clarify"         # 需要澄清
    SUGGEST = "suggest"         # 提供建议

@dataclass
class IntentResult:
    """意图识别结果"""
    intent_type: IntentType
    confidence: float
    task_description: Optional[str]
    reasoning: str
    suggested_questions: List[str]

class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self):
        # 简化关键词集合
        self.execute_keywords = [
            "我来", "让我", "开始", "执行", "读取", "查看", 
            "打开", "列出", "分析", "检查", "创建", "运行"
        ]
        self.clarify_keywords = [
            "请问", "哪个", "具体", "确认", "不明白"
        ]
        self.suggest_keywords = [
            "建议", "推荐", "考虑", "可以", "我认为"
        ]
    
    def recognize(self, user_message: str, ai_response: str) -> IntentResult:
        """识别意图"""
        # 计算各类型得分
        scores = {
            IntentType.EXECUTE: self._score_execute(ai_response, user_message),
            IntentType.CLARIFY: self._score_clarify(ai_response),
            IntentType.SUGGEST: self._score_suggest(ai_response),
        }
        
        # 找到最高分意图
        max_intent = max(scores.items(), key=lambda x: x[1])
        intent_type = max_intent[0]
        confidence = max_intent[1]
        
        # 如果所有得分都较低，默认为对话
        if confidence < 0.2:
            intent_type = IntentType.DIALOGUE
        
        # 提取任务描述（如果是执行意图）
        task_desc = None
        if intent_type == IntentType.EXECUTE and confidence > 0.5:
            task_desc = self._extract_task(user_message)
        
        # 生成推理说明
        reasoning = f"识别为{intent_type.value}，置信度{confidence:.2f}"
        
        # 提取建议问题（如果是澄清意图）
        questions = []
        if intent_type == IntentType.CLARIFY:
            questions = self._extract_questions(ai_response)
        
        # 发布交互记录事件
        publish_event(EventType.INTERACTION_RECORDED, {
            "user_input": user_message,
            "ai_response": ai_response,
            "intent_type": intent_type.value,
            "confidence": confidence
        }, source="intent_recognizer")
        
        return IntentResult(intent_type, confidence, task_desc, reasoning, questions)
    
    def _score_execute(self, ai_response: str, user_message: str) -> float:
        """执行意图得分"""
        score = 0.0
        
        # AI响应关键词
        for kw in self.execute_keywords:
            if kw in ai_response:
                score += 0.15
        
        # 用户消息动作词
        action_words = ["帮我", "请", "分析", "读取", "查看", "列出", "运行", "执行", "打开", "创建"]
        for word in action_words:
            if word in user_message:
                score += 0.15
                break
        
        # 对象词（文件、目录、项目等）
        object_words = ["文件", "目录", "项目", "代码", "脚本", "数据", "文档"]
        if any(word in ai_response or word in user_message for word in object_words):
            score += 0.15
        
        # 文件扩展名检测（.txt, .py, .md, .json等）
        if re.search(r'\.(txt|py|md|json|yml|yaml|csv|xml)\b', user_message):
            score += 0.20
        
        # 路径模式检测（包含/或\的路径）
        if '/' in user_message or '\\' in user_message:
            score += 0.15
        
        # AI响应包含明确执行短语
        if any(phrase in ai_response for phrase in ["我来", "让我来", "开始执行", "立即执行"]):
            score += 0.20
        
        return min(score, 1.0)
    
    def _score_clarify(self, ai_response: str) -> float:
        """澄清意图得分"""
        score = sum(0.20 for kw in self.clarify_keywords if kw in ai_response)
        if '?' in ai_response or '？' in ai_response:
            score += 0.20
        return min(score, 1.0)
    
    def _score_suggest(self, ai_response: str) -> float:
        """建议意图得分"""
        score = sum(0.20 for kw in self.suggest_keywords if kw in ai_response)
        if ai_response.strip().startswith(("建议", "我建议")):
            score += 0.30
        return min(score, 1.0)
    
    def _extract_task(self, message: str) -> Optional[str]:
        """提取任务描述"""
        msg = message.strip()
        
        # 短消息直接返回（但尝试提取核心部分）
        if len(msg) < 30:
            # 尝试提取动作+对象
            patterns = [
                r'(?:帮我|请|帮我请)(.+?)(?:[。？！]|$)',
                r'(?:分析|读取|查看|列出|运行|执行|打开|创建|修改|删除)(.+?)(?:[。？！]|$)',
                r'(?:要|想|需要)(.+?)(?:[。？！]|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, msg, re.IGNORECASE)
                if match:
                    task = match.group(0).strip()
                    if len(task) > 2:
                        return task
            
            # 如果没有匹配模式，返回原消息
            return msg
        
        # 长消息：提取动作短语
        patterns = [
            r'(?:帮我|请|帮我请)(.+?)(?:[。？！]|$)',
            r'(?:分析|读取|查看|列出|运行|执行|打开|创建|修改|删除)(.+?)(?:[。？！]|$)',
            r'(?:要|想|需要)(.+?)(?:[。？！]|$)',
            r'(?:对于|关于)(.+?)(?:[。？！]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                task = match.group(0).strip()
                if len(task) > 3:
                    return task
        
        # 返回前40个字符作为摘要
        return msg[:40]
    
    def _extract_questions(self, text: str) -> List[str]:
        """提取问题"""
        questions = []
        sentences = re.split(r'[。！？?!]', text)
        
        for sent in sentences:
            sent = sent.strip()
            if any(kw in sent for kw in ["请问", "什么", "哪个", "如何"]):
                questions.append(sent[:50])
        
        return questions[:2]

# 全局实例
_global_recognizer = None

def get_intent_recognizer() -> IntentRecognizer:
    """获取全局识别器实例"""
    global _global_recognizer
    if _global_recognizer is None:
        _global_recognizer = IntentRecognizer()
    return _global_recognizer


