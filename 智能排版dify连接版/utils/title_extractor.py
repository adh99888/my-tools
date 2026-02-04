"""
复杂标题提取器模块
基于多维度分析和置信度评分的标题提取
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from .text_analyzer import get_text_analyzer

logger = logging.getLogger(__name__)


class TitleExtractor:
    """复杂标题提取器类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化标题提取器
        
        Args:
            config: 配置字典，包含提取参数
        """
        self.text_analyzer = get_text_analyzer()
        
        # 默认配置
        self.default_config = {
            "confidence_threshold": 70,
            "max_lines_to_scan": 5,
            "min_title_length": 5,
            "max_title_length": 100,
            "enable_complex_analysis": True
        }
        
        # 合并配置
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
    
    def extract_title_from_content(self, content: str) -> Dict[str, Any]:
        """
        从文档内容中提取标题
        
        Args:
            content: 文档内容
            
        Returns:
            提取结果字典，包含标题、置信度和详细分析
        """
        if not content or not content.strip():
            return self._create_empty_result()
        
        # 使用文本分析器提取候选标题
        max_lines = self.config.get("max_lines_to_scan", 5)
        threshold = self.config.get("confidence_threshold", 70)
        
        candidates = self.text_analyzer.extract_possible_title(content, max_lines)
        
        if not candidates:
            return self._create_empty_result()
        
        # 获取最佳候选
        best_candidate = candidates[0]
        
        result = {
            "success": best_candidate["total_score"] >= threshold,
            "candidates": candidates,
            "analysis": best_candidate.copy(),
            "config": self.config.copy()
        }
        
        if result["success"]:
            result["title"] = best_candidate["text"]
            result["confidence"] = best_candidate["total_score"]
            result["method"] = "complex_extraction"
            logger.info(f"标题提取成功: {best_candidate['text']} (置信度: {best_candidate['total_score']})")
        else:
            result["title"] = None
            result["confidence"] = best_candidate["total_score"]
            result["method"] = "below_threshold"
            logger.info(f"标题提取失败: 最佳候选 '{best_candidate['text']}' 置信度 {best_candidate['total_score']} < 阈值 {threshold}")
        
        return result
    
    def extract_title_simple(self, content: str) -> Optional[str]:
        """
        简单标题提取（向后兼容）
        
        Args:
            content: 文档内容
            
        Returns:
            提取的标题或None
        """
        if not content:
            return None
        
        lines = content.strip().split('\n')
        for line in lines[:3]:  # 只检查前3行
            line = line.strip()
            if line and len(line) < 100:
                # 基本检查：不是以特殊字符开头
                if not line.startswith((' ', '\t', '#', '-', '*', '•')):
                    return line
        
        return None
    
    def auto_extract_title(self, content: str, use_complex: bool = True) -> Optional[str]:
        """
        自动标题提取（根据配置选择简单或复杂方法）
        
        Args:
            content: 文档内容
            use_complex: 是否使用复杂方法
            
        Returns:
            提取的标题或None
        """
        if not use_complex or not self.config.get("enable_complex_analysis", True):
            # 使用简单方法
            return self.extract_title_simple(content)
        
        # 使用复杂方法
        result = self.extract_title_from_content(content)
        
        if result["success"]:
            return result["title"]
        
        # 复杂方法失败时回退到简单方法
        logger.debug("复杂标题提取失败，回退到简单方法")
        return self.extract_title_simple(content)
    
    def analyze_title_candidates(self, content: str) -> List[Dict[str, Any]]:
        """
        分析所有标题候选（用于调试和展示）
        
        Args:
            content: 文档内容
            
        Returns:
            候选标题分析列表
        """
        if not content:
            return []
        
        max_lines = self.config.get("max_lines_to_scan", 5)
        candidates = self.text_analyzer.extract_possible_title(content, max_lines)
        
        # 格式化结果，便于显示
        formatted_candidates = []
        for candidate in candidates:
            formatted = {
                "text": candidate["text"],
                "position": candidate["position"],
                "total_score": candidate["total_score"],
                "score_breakdown": {
                    "位置得分": candidate["position_score"],
                    "长度得分": candidate["length_score"],
                    "结构得分": candidate["structure_score"],
                    "格式得分": candidate["format_score"],
                    "语义得分": candidate["semantic_score"]
                },
                "pass_threshold": candidate["total_score"] >= self.config.get("confidence_threshold", 70),
                "length": len(candidate["text"])
            }
            formatted_candidates.append(formatted)
        
        return formatted_candidates
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """创建空的结果字典"""
        return {
            "success": False,
            "title": None,
            "confidence": 0,
            "method": "no_content",
            "candidates": [],
            "analysis": {},
            "config": self.config.copy()
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新提取器配置
        
        Args:
            new_config: 新配置字典
        """
        self.config.update(new_config)
        logger.info(f"标题提取器配置更新: {new_config}")


# 全局实例管理
_title_extractor_instances = {}

def get_title_extractor(config_key: str = "default", config: Dict[str, Any] = None) -> TitleExtractor:
    """
    获取标题提取器实例
    
    Args:
        config_key: 实例键名
        config: 配置字典
        
    Returns:
        TitleExtractor实例
    """
    if config_key not in _title_extractor_instances:
        _title_extractor_instances[config_key] = TitleExtractor(config)
    
    return _title_extractor_instances[config_key]


def extract_title_with_config(content: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    使用指定配置提取标题（便捷函数）
    
    Args:
        content: 文档内容
        config: 提取配置
        
    Returns:
        提取结果字典
    """
    extractor = TitleExtractor(config)
    return extractor.extract_title_from_content(content)


# 测试函数
if __name__ == "__main__":
    # 简单测试
    test_cases = [
        "第一章 中医理论基础\n中医理论是中国传统医学的核心...",
        "\n\n摘要\n本文研究了中医养生理论在现代社会的应用...",
        "关于2024年度中医药发展报告的通知\n各部门：\n为进一步促进...",
        "今天天气很好，我们去公园散步，看到了很多美丽的花朵...",
        "一、研究背景\n中医药作为中国传统医学的瑰宝...",
        "（一）主要穴位分析\n在中医针灸治疗中，穴位选择..."
    ]
    
    extractor = TitleExtractor()
    
    for i, content in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"内容: {content[:50]}...")
        
        result = extractor.extract_title_from_content(content)
        if result["success"]:
            print(f"✅ 提取成功: {result['title']} (置信度: {result['confidence']})")
        else:
            print(f"❌ 提取失败 (置信度: {result['confidence']})")
        
        # 显示候选分析
        candidates = extractor.analyze_title_candidates(content)
        if candidates:
            print("候选分析:")
            for cand in candidates[:2]:  # 只显示前2个
                status = "✅" if cand["pass_threshold"] else "❌"
                print(f"  {status} {cand['text']} (得分: {cand['total_score']})")