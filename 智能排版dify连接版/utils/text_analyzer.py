"""
文本分析工具模块
提供基础的文本分析功能
"""

import re
from typing import List, Dict, Any, Optional, Tuple


class TextAnalyzer:
    """文本分析工具类"""

    # 常见标题关键词库
    TITLE_KEYWORDS = [
        "第一章",
        "第二章",
        "第三章",
        "第四章",
        "第五章",
        "第六章",
        "第七章",
        "第八章",
        "第九章",
        "第十章",
        "第1章",
        "第2章",
        "第3章",
        "第4章",
        "第5章",
        "第6章",
        "第7章",
        "第8章",
        "第9章",
        "第10章",
        "一、",
        "二、",
        "三、",
        "四、",
        "五、",
        "六、",
        "七、",
        "八、",
        "九、",
        "十、",
        "摘要",
        "引言",
        "目录",
        "前言",
        "序言",
        "正文",
        "结论",
        "总结",
        "参考文献",
        "致谢",
        "附录",
        "关于",
        "报告",
        "通知",
        "决定",
        "方案",
        "计划",
        "建议",
        "意见",
        "办法",
        "第一部分",
        "第二部分",
        "第三部分",
        "第四部分",
        "第五部分",
        "第一节",
        "第二节",
        "第三节",
        "第四节",
        "第五节",
        "（一）",
        "（二）",
        "（三）",
        "（四）",
        "（五）",
        "1.",
        "2.",
        "3.",
        "4.",
        "5.",
        "1、",
        "2、",
        "3、",
        "4、",
        "5、",
    ]

    # 段落起始词黑名单
    PARAGRAPH_START_WORDS = [
        "然后",
        "但是",
        "因为",
        "所以",
        "然而",
        "首先",
        "其次",
        "最后",
        "接着",
        "此外",
        "今天",
        "昨天",
        "明天",
        "今年",
        "去年",
        "我们",
        "你们",
        "他们",
        "咱们",
        "大家",
        "这个",
        "那个",
        "这些",
        "那些",
        "这种",
        "总之",
        "总而言之",
        "综上所述",
        "因此",
        "因而",
        "例如",
        "比如",
        "譬如",
        "比方说",
        "举个例子",
    ]

    # 常见标题结束词
    TITLE_END_WORDS = [
        "报告",
        "通知",
        "方案",
        "计划",
        "意见",
        "办法",
        "规定",
        "条例",
        "章程",
    ]

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本，去除多余空格和空行

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 替换全角空格为半角空格
        text = text.replace("　", " ")

        # 去除首尾空白
        text = text.strip()

        # 合并多个空白字符为单个空格
        text = re.sub(r"\s+", " ", text)

        return text

    @staticmethod
    def split_into_lines(text: str) -> List[str]:
        """
        将文本分割为行

        Args:
            text: 文本

        Returns:
            行列表
        """
        if not text:
            return []

        lines = text.split("\n")
        # 清理每行并过滤空行
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line:
                cleaned_lines.append(cleaned_line)

        return cleaned_lines

    @staticmethod
    def get_first_n_lines(text: str, n: int = 5) -> List[str]:
        """
        获取文本的前N行（非空行）

        Args:
            text: 文本
            n: 需要获取的行数

        Returns:
            前N行列表
        """
        lines = TextAnalyzer.split_into_lines(text)
        return lines[:n]

    @staticmethod
    def contains_title_keywords(text: str) -> bool:
        """
        检查文本是否包含标题关键词

        Args:
            text: 文本

        Returns:
            是否包含标题关键词
        """
        if not text:
            return False

        for keyword in TextAnalyzer.TITLE_KEYWORDS:
            if keyword in text:
                return True

        return False

    @staticmethod
    def starts_with_paragraph_word(text: str) -> bool:
        """
        检查文本是否以段落起始词开头

        Args:
            text: 文本

        Returns:
            是否以段落起始词开头
        """
        if not text:
            return False

        text = text.strip()
        for word in TextAnalyzer.PARAGRAPH_START_WORDS:
            if text.startswith(word):
                return True

        return False

    @staticmethod
    def has_title_format(text: str) -> bool:
        """
        检查文本是否具有标题格式

        Args:
            text: 文本

        Returns:
            是否具有标题格式
        """
        if not text:
            return False

        patterns = [
            r"^第[一二三四五六七八九十0-9]+[章节部分]",  # 第一章、第一部分
            r"^[一二三四五六七八九十]+[、.]",  # 一、 一.
            r"^（[一二三四五六七八九十]+）",  # （一）
            r"^[0-9]+[、.]",  # 1、 1.
            r"^[0-9]+\.[0-9]+",  # 1.1
        ]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    @staticmethod
    def calculate_length_score(
        text: str, min_length: int = 5, max_length: int = 100
    ) -> int:
        """
        计算文本长度得分

        Args:
            text: 文本
            min_length: 最小长度（改为2）
            max_length: 最大长度

        Returns:
            长度得分 (0-20分)
        """
        length = len(text)
        # 特殊情况：短标题关键词给高分
        short_titles = ["摘要", "引言", "目录", "前言", "结论", "致谢", "附录"]
        if text in TextAnalyzer.TITLE_KEYWORDS and length < 5:
            return 15  # 短关键词给15分

        if min_length <= length <= 50:
            return 20
        elif 50 < length <= max_length:
            return 10
        else:
            return 0

    @staticmethod
    def calculate_structure_score(text: str) -> int:
        """
        计算文本结构得分

        Args:
            text: 文本

        Returns:
            结构得分 (0-25分)
        """
        score = 0

        # 包含标题标识
        if TextAnalyzer.has_title_format(text):
            score += 15

        # 以常见标题关键词开头
        for keyword in TextAnalyzer.TITLE_KEYWORDS:
            if text.startswith(keyword):
                score += 10
                # 如果是完全匹配的短标题，额外加分
                if text == keyword and len(text) <= 5:
                    score += 5
                break

        return min(score, 25)  # 不超过25分

    @staticmethod
    def calculate_format_score(text: str) -> int:
        """
        计算文本格式得分

        Args:
            text: 文本

        Returns:
            格式得分 (0-15分)
        """
        score = 0

        # 检查句尾标点
        if not text.endswith(("。", "！", "？", ".", "!", "?")):
            score += 10

        # 检查空格数量
        if text.count(" ") <= 3:  # 不超过3个空格
            score += 5

        return min(score, 15)  # 不超过15分

    @staticmethod
    def calculate_semantic_score(text: str) -> int:
        """
        计算文本语义得分

        Args:
            text: 文本

        Returns:
            语义得分 (0-10分)
        """
        # 不以段落起始词开头
        if not TextAnalyzer.starts_with_paragraph_word(text):
            return 10

        return 0

    @staticmethod
    def extract_possible_title(text: str, max_lines: int = 5) -> List[Dict[str, Any]]:
        """
        从文本中提取可能的标题

        Args:
            text: 文本
            max_lines: 最大扫描行数

        Returns:
            可能的标题列表，包含文本和得分
        """
        lines = TextAnalyzer.get_first_n_lines(text, max_lines)
        results = []

        for i, line in enumerate(lines):
            # 跳过明显不是标题的行
            if len(line) < 2 or len(line) > 200:
                continue

            # 计算各项得分
            position_score = max(30 - i * 5, 0)  # 第一行30分，依次递减
            length_score = TextAnalyzer.calculate_length_score(line)
            structure_score = TextAnalyzer.calculate_structure_score(line)
            format_score = TextAnalyzer.calculate_format_score(line)
            semantic_score = TextAnalyzer.calculate_semantic_score(line)

            total_score = (
                position_score
                + length_score
                + structure_score
                + format_score
                + semantic_score
            )

            results.append(
                {
                    "text": line,
                    "position": i + 1,
                    "position_score": position_score,
                    "length_score": length_score,
                    "structure_score": structure_score,
                    "format_score": format_score,
                    "semantic_score": semantic_score,
                    "total_score": total_score,
                }
            )

        # 按总分降序排序
        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results

    @staticmethod
    def find_best_title(
        text: str, max_lines: int = 5, threshold: int = 70
    ) -> Optional[str]:
        """
        查找最佳标题

        Args:
            text: 文本
            max_lines: 最大扫描行数
            threshold: 置信度阈值

        Returns:
            最佳标题文本，如果无达标标题则返回None
        """
        candidates = TextAnalyzer.extract_possible_title(text, max_lines)

        if not candidates:
            return None

        best_candidate = candidates[0]

        if best_candidate["total_score"] >= threshold:
            return best_candidate["text"]

        return None


# 全局实例
_text_analyzer_instance = None


def get_text_analyzer() -> TextAnalyzer:
    """
    获取文本分析器实例（单例模式）

    Returns:
        TextAnalyzer实例
    """
    global _text_analyzer_instance

    if _text_analyzer_instance is None:
        _text_analyzer_instance = TextAnalyzer()

    return _text_analyzer_instance
