#!/usr/bin/env python3
"""
意图识别模块（工作版，≤150行）
宪法第3条：认知对齐优先，阶段三核心能力
"""

from typing import List, Dict, Any

class IntentRecognizer:
    """意图识别器（字符串包含匹配）"""
    
    PATTERNS = [
        {"id": "code_cleanup", "kw": ["整理", "清理", "优化", "代码", "格式化"], 
         "actions": [{"t": "run_lint", "d": "代码检查"}, {"t": "format_code", "d": "格式化代码"}]},
        {"id": "system_check", "kw": ["状态", "检查", "健康", "看看", "查看"], 
         "actions": [{"t": "system_diagnosis", "d": "系统诊断"}, {"t": "generate_report", "d": "状态报告"}]},
        {"id": "task_resume", "kw": ["继续", "上次", "之前", "工作", "任务"], 
         "actions": [{"t": "resume_task", "d": "继续任务"}, {"t": "query_memory", "d": "查询记忆"}]},
        {"id": "file_cleanup", "kw": ["清理", "备份", "文件", "临时", "删除"], 
         "actions": [{"t": "clean_temp_files", "d": "清理临时文件"}, {"t": "create_backup", "d": "创建备份"}]},
        {"id": "info_query", "kw": ["什么", "如何", "怎么", "查询", "进度"], 
         "actions": [{"t": "query_info", "d": "查询信息"}, {"t": "show_progress", "d": "显示进度"}]}
    ]
    
    def __init__(self, memory=None):
        self.memory = memory
    
    def recognize(self, text: str, context=None) -> Dict[str, Any]:
        """识别意图"""
        matches = []
        
        for p in self.PATTERNS:
            score, common = self._match(text, p["kw"])
            if score >= 0.2:  # 阈值
                matches.append({
                    "id": p["id"], 
                    "score": score, 
                    "common": common, 
                    "actions": p["actions"]
                })
        
        if matches:
            # 按分数排序
            matches.sort(key=lambda x: x["score"], reverse=True)
            best = matches[0]
            
            # 生成动作
            actions = []
            for a in best["actions"]:
                actions.append({
                    "type": a["t"], 
                    "description": a["d"], 
                    "confidence": best["score"]
                })
            
            # 添加其他高分数匹配
            for m in matches[1:3]:
                if m["score"] > 0.4:
                    for a in m["actions"]:
                        if not any(x["type"] == a["t"] for x in actions):
                            actions.append({
                                "type": a["t"], 
                                "description": a["d"], 
                                "confidence": m["score"] * 0.8
                            })
            
            return {
                "success": True, 
                "intent": best["id"], 
                "confidence": best["score"],
                "suggested_actions": actions[:3],
                "matched_keywords": best["common"]
            }
        else:
            return {
                "success": False, 
                "intent": "unknown", 
                "confidence": 0.0,
                "suggested_actions": [{
                    "type": "clarify", 
                    "description": "请求用户澄清意图", 
                    "confidence": 1.0
                }]
            }
    
    def _match(self, text: str, keywords: List[str]) -> tuple:
        """匹配：检查文本包含哪些关键词"""
        if not text or not keywords:
            return 0.0, []
        
        common = [kw for kw in keywords if kw in text]
        if not common:
            return 0.0, []
        
        # 分数：包含的关键词数量 / 总关键词数量
        score = len(common) / len(keywords)
        return score, common
    
    def test_stage3(self) -> tuple:
        """测试阶段三标准1"""
        tests = [
            ("整理一下代码", "code_cleanup"),
            ("看看项目状态", "system_check"), 
            ("继续上次工作", "task_resume")
        ]
        
        results = []
        all_passed = True
        
        for text, expected in tests:
            r = self.recognize(text)
            passed = r["success"] and r["intent"] == expected
            results.append({
                "input": text,
                "expected": expected,
                "actual": r["intent"],
                "confidence": r["confidence"],
                "passed": passed
            })
            if not passed:
                all_passed = False
        
        return all_passed, results

# 演示和测试
if __name__ == "__main__":
    ir = IntentRecognizer()
    
    print("=== 意图识别模块 ===")
    print(f"行数检查: ≤150行目标")
    print(f"模式数量: {len(ir.PATTERNS)}")
    print()
    
    # 阶段三验证
    passed, details = ir.test_stage3()
    print(f"阶段三标准1验证（模糊指令理解）: {'通过' if passed else '失败'}")
    print()
    
    for d in details:
        status = "通过" if d["passed"] else "失败"
        print(f"{status} '{d['input']}'")
        print(f"  预期: {d['expected']}, 实际: {d['actual']}, 置信度: {d['confidence']:.2f}")
    print()
    
    # 额外测试
    test_cases = [
        "清理临时文件",
        "怎么优化代码", 
        "查询项目进度",
        "备份项目文件",
        "检查系统健康"
    ]
    
    print("=== 额外测试 ===")
    for text in test_cases:
        result = ir.recognize(text)
        status = "OK" if result["success"] else "NO"
        print(f"{status} '{text}' -> {result['intent']} ({result['confidence']:.2f})")
        if result["suggested_actions"]:
            print(f"  建议: {result['suggested_actions'][0]['description']}")