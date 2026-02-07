#!/usr/bin/env python3
"""
语义关联增强模块（极简版，≤100行）
宪法第3条：认知对齐优先，阶段三标准3
功能：同义词扩展和简单语义匹配
"""

from typing import List, Dict, Any, Tuple

class SemanticEnhancer:
    """语义增强器（字符串匹配版）"""
    
    def __init__(self):
        self.synonyms = {
            "代码": ["程序", "编程", "源码", "脚本"],
            "整理": ["清理", "优化", "重构", "调整"],
            "优化": ["改进", "提升", "增强", "完善"],
            "项目": ["工程", "任务", "工作", "计划"],
            "状态": ["情况", "状况", "进度", "进展"],
            "检查": ["查看", "审查", "验证", "测试"],
            "文件": ["文档", "资料", "记录", "档案"],
            "清理": ["删除", "清除", "整理", "移除"],
            "备份": ["副本", "拷贝", "复制", "存档"],
            "系统": ["平台", "框架", "架构", "环境"],
            "任务": ["工作", "作业", "事项", "活动"],
            "继续": ["恢复", "重启", "重新开始"],
            "查询": ["搜索", "查找", "检索", "寻找"]
        }
    
    def expand_query(self, query: str) -> List[str]:
        """扩展查询词的同义词"""
        expanded = [query]
        
        # 检查查询中包含哪些关键词
        for word, syns in self.synonyms.items():
            if word in query:
                # 为每个同义词创建变体
                for syn in syns:
                    # 简单替换：将word替换为syn
                    variant = query.replace(word, syn)
                    expanded.append(variant)
        
        return list(set(expanded))
    
    def semantic_search(self, query: str, contents: List[str], limit: int = 5) -> List[Tuple[str, float]]:
        """语义搜索：基于同义词扩展的匹配"""
        # 扩展查询
        expanded_queries = self.expand_query(query)
        
        results = []
        for content in contents:
            # 计算匹配度：检查content是否包含任何扩展查询
            max_score = 0
            for q in expanded_queries:
                # 简单匹配：计算共同词比例
                score = self._match_score(q, content)
                if score > max_score:
                    max_score = score
            
            if max_score > 0:
                results.append((content, max_score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _match_score(self, query: str, content: str) -> float:
        """计算匹配分数（简单实现）"""
        # 将查询和内容按非字母数字字符分割
        import re
        q_words = re.findall(r'[\u4e00-\u9fff]+|\w+', query.lower())
        c_words = re.findall(r'[\u4e00-\u9fff]+|\w+', content.lower())
        
        if not q_words:
            return 0.0
        
        # 计算共同词比例
        common = set(q_words) & set(c_words)
        return len(common) / len(q_words)
    
    def add_synonym(self, word: str, synonym: str) -> None:
        """添加同义词"""
        if word not in self.synonyms:
            self.synonyms[word] = []
        if synonym not in self.synonyms[word]:
            self.synonyms[word].append(synonym)
    
    def get_related(self, word: str) -> List[str]:
        """获取相关词（同义词）"""
        return self.synonyms.get(word, []).copy()
    
    def demo(self) -> None:
        """演示功能"""
        print("语义增强演示:")
        
        # 测试扩展
        tests = ["整理代码", "检查项目", "清理文件"]
        for t in tests:
            expanded = self.expand_query(t)
            print(f"'{t}' → {expanded}")
        
        # 测试搜索
        contents = [
            "需要优化程序代码",
            "项目进展情况良好", 
            "删除临时文档文件",
            "系统运行状态监控"
        ]
        
        results = self.semantic_search("整理代码", contents)
        print(f"\n搜索'整理代码':")
        for content, score in results:
            print(f"  {score:.2f}: {content}")

# 测试
if __name__ == "__main__":
    se = SemanticEnhancer()
    se.demo()