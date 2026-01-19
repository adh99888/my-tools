"""
文档后处理模块
负责优化排版结果，清理多余字符
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class DocumentPostProcessor:
    """文档后处理器类"""
    
    @staticmethod
    def optimize_paragraph_spacing(content: str) -> str:
        """
        优化段落间距
        确保段落之间只有一个空行，移除连续多个空行
        
        Args:
            content: 原始内容
            
        Returns:
            优化后的内容
        """
        if not content:
            return content
        
        # 替换连续多个换行为两个换行（一个空行）
        # 先统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 替换3个及以上换行为2个换行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 处理标题与正文之间的间距
        lines = content.split('\n')
        optimized_lines = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 如果是标题行（以#开头）
            if line_stripped.startswith(('#', '##', '###')):
                # 确保标题前只有一个空行
                if i > 0 and lines[i-1].strip() == '':
                    # 已经有一个空行，保持
                    pass
                else:
                    # 确保标题前有一个空行（除非是第一个元素）
                    if i > 0 and optimized_lines and optimized_lines[-1].strip() != '':
                        optimized_lines.append('')
                
                optimized_lines.append(line)
                
                # 确保标题后有一个空行（如果不是最后一行）
                if i < len(lines) - 1 and lines[i+1].strip() != '':
                    optimized_lines.append('')
            else:
                optimized_lines.append(line)
        
        # 重新组合并再次处理连续空行
        result = '\n'.join(optimized_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # 移除开头和结尾的多余空行
        result = result.strip('\n')
        
        logger.info("段落间距优化完成")
        return result
    
    @staticmethod
    def clean_markdown_artifacts(content: str) -> str:
        """
        清理Markdown多余字符
        
        清理规则：
        1. 移除单独成行的"#"、"-"、"*"、"."
        2. 清理多余的标点符号
        3. 移除多余的空格
        4. 清理段落开头的多余标记
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        if not content:
            return content
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 清理行首行尾空格
            line = line.strip()
            
            if not line:
                cleaned_lines.append('')
                continue
            
            # 规则1：移除单独成行的特殊字符
            if line in ['#', '-', '*', '.', '##', '###']:
                continue
            
            # 规则2：清理多余的标点符号
            # 移除连续重复的标点（超过2个）
            line = re.sub(r'([!?.,;:])\1{2,}', r'\1\1', line)
            
            # 修正中文标点后的英文标点
            line = re.sub(r'([。！？，；：])([.,;:!?])', r'\1', line)
            
            # 规则3：移除多余的空格
            # 移除中文之间的空格（中文之间通常不需要空格）
            line = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', line)
            
            # 移除连续多个空格
            line = re.sub(r'\s{2,}', ' ', line)
            
            # 规则4：清理段落开头的多余标记
            # 移除段落开头多余的#、-、*等（但保留标题标记）
            if re.match(r'^[#-*.]+\s*$', line[:3]):
                line = re.sub(r'^[#-*.]+\s+', '', line)
            
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        # 最后整体清理
        # 移除连续的空白行
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        logger.info("Markdown字符清理完成")
        return result
    
    @classmethod
    def process(cls, content: str) -> str:
        """
        完整的后处理流程
        
        Args:
            content: 原始内容
            
        Returns:
            处理后内容
        """
        if not content:
            return content
        
        logger.info("开始文档后处理优化")
        
        # 第一步：清理多余字符
        cleaned = cls.clean_markdown_artifacts(content)
        
        # 第二步：优化段落间距
        optimized = cls.optimize_paragraph_spacing(cleaned)
        
        logger.info("文档后处理优化完成")
        return optimized