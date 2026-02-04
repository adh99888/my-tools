"""
Dify API客户端 - 最终版
只提取message事件的answer字段，强化内容过滤
"""

import requests
import json
import logging
import re
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def _filter_content(content: str) -> str:
    """
    过滤内容，只保留纯净的文本输出
    
    Args:
        content: 原始内容
        
    Returns:
        过滤后的纯净文本
    """
    if not content or not isinstance(content, str):
        return ""
    
    # 1. 移除JSON格式的代码块
    content = re.sub(r'\{[^}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\[[^\]]*\]', '', content, flags=re.DOTALL)
    
    # 2. 移除代码块（```language ... ```）
    content = re.sub(r'```[\s\S]*?```', '', content)
    
    # 3. 移除单行代码（`code`）
    content = re.sub(r'`[^`]*`', '', content)
    
    # 4. 移除HTML标签
    content = re.sub(r'<[^>]+>', '', content)
    
    # 5. 移除Markdown格式标记
    content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)  # 标题
    content = re.sub(r'^\*\s+', '', content, flags=re.MULTILINE)     # 无序列表
    content = re.sub(r'^\d+\.\s+', '', content, flags=re.MULTILINE)   # 有序列表
    content = re.sub(r'^\>\s+', '', content, flags=re.MULTILINE)     # 引用
    
    # 6. 移除多余的空白字符
    content = re.sub(r'\n\s*\n', '\n\n', content)  # 多个空行
    content = re.sub(r'[ \t]+', ' ', content)      # 多个空格/制表符
    
    # 7. 移除明显的代码片段（包含函数、变量等）
    code_patterns = [
        r'function\s+\w+\s*\(',           # JavaScript函数
        r'def\s+\w+\s*\(',                # Python函数
        r'var\s+\w+\s*=',                 # JavaScript变量
        r'let\s+\w+\s*=',                 # JavaScript let
        r'const\s+\w+\s*=',               # JavaScript const
        r'\w+\s*:\s*["\'\[\{]',           # 对象属性
        r'https?://[^\s]+',               # URL
        r'www\.[^\s]+',                   # www链接
    ]
    
    for pattern in code_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # 8. 移除特殊字符和符号（保留中文、英文、数字、基本标点）
    content = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()""''—-]', '', content)
    
    # 9. 清理首尾空白
    content = content.strip()
    
    # 10. 验证过滤结果
    if len(content) < 10:  # 过滤后内容太短
        logger.warning("内容过滤后过短，可能过滤过度")
        return ""
    
    # 检查是否包含足够的中文内容
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    if chinese_chars < len(content) * 0.1:  # 中文字符少于10%
        logger.warning("内容中中文字符比例过低，可能包含大量代码")
        return ""
    
    return content


class DifyClient:
    """Dify工作流客户端 - 最终版"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key else 'app-IjlgOV9kIbI7p5u1ZxYdZMT4'
        self.base_url = "https://ai.tuluoai.com/v1"
    
    def generate_content(self, query: str, debug: bool = False) -> Tuple[bool, str]:
        """生成内容 - 只提取message事件中的answer
        
        Args:
            query: 查询内容
            debug: 是否启用调试模式，记录原始数据
        """
        url = f'{self.base_url}/chat-messages'
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            "inputs": {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "abc-123",
            "files": [
                {
                    "type": "image",
                    "transfer_method": "remote_url",
                    "url": "https://cloud.dify.ai/logo/logo-site.png"
                }
            ]
        }
        
        logger.info(f"生成内容: {query[:50]}...")
        
        try:
            response = requests.post(url, headers=headers, json=data, stream=True, timeout=120)
            
            if response.status_code == 200:
                answer_parts = []
                message_count = 0
                raw_data_log = []
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8', errors='ignore').strip()
                        
                        # 跳过空行
                        if not line_str:
                            continue
                        
                        # 调试模式记录原始数据
                        if debug and len(raw_data_log) < 10:  # 只记录前10行
                            raw_data_log.append(line_str)
                        
                        # 处理SSE格式
                        if line_str.startswith('data: '):
                            try:
                                data_obj = json.loads(line_str[6:])  # 移除"data: "前缀
                                
                                # 只处理message事件
                                if isinstance(data_obj, dict) and data_obj.get('event') == 'message':
                                    message_count += 1
                                    
                                    # 提取answer字段
                                    if 'answer' in data_obj and isinstance(data_obj['answer'], str):
                                        answer = data_obj['answer'].strip()
                                        if answer and answer != '':
                                            answer_parts.append(answer)
                                            
                                            # 调试：记录前几个
                                            if message_count <= 3:
                                                logger.debug(f"提取message {message_count}: {answer[:100]}...")
                                
                                # 调试模式：记录其他事件类型
                                elif debug and isinstance(data_obj, dict) and 'event' in data_obj:
                                    event_type = data_obj.get('event')
                                    if event_type != 'message':
                                        logger.debug(f"跳过非message事件: {event_type}")
                            
                            except json.JSONDecodeError:
                                # 不是JSON，跳过
                                continue
                
                # 调试模式输出原始数据
                if debug and raw_data_log:
                    logger.debug("=== 原始数据样本 ===")
                    for i, log_line in enumerate(raw_data_log[:5]):
                        logger.debug(f"原始数据{i+1}: {log_line}")
                
                # 合并所有answer
                if answer_parts:
                    raw_content = ''.join(answer_parts)
                    logger.info(f"原始内容: {message_count}个message，{len(raw_content)}字符")
                    
                    # 应用内容过滤
                    filtered_content = _filter_content(raw_content)
                    
                    if not filtered_content:
                        logger.warning("内容过滤后为空，可能包含大量代码")
                        return False, "生成内容包含过多代码，请调整工作流设置"
                    
                    # 验证过滤后内容长度
                    if len(filtered_content) > 50000:  # 超过5万字符
                        logger.warning(f"过滤后内容仍过长 {len(filtered_content)}字符，截断为3万字符")
                        filtered_content = filtered_content[:30000] + "\n\n【内容过长，已自动截断】"
                    
                    # 记录过滤效果
                    filter_ratio = len(filtered_content) / len(raw_content) if raw_content else 0
                    logger.info(f"过滤完成: 原始{len(raw_content)}字符 -> 过滤后{len(filtered_content)}字符 (比例: {filter_ratio:.1%})")
                    
                    return True, filtered_content
                else:
                    logger.warning("未提取到有效内容")
                    return False, "未提取到有效内容"
            else:
                logger.error(f"API错误 {response.status_code}")
                return False, f"Dify API错误: {response.status_code}"
                
        except Exception as e:
            logger.error(f"请求失败: {str(e)}")
            return False, f"请求失败: {str(e)}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试连接"""
        try:
            # 简单测试
            success, content = self.generate_content("测试连接，请回复'连接成功'")
            
            if success and "连接成功" in content:
                return True, "✅ Dify API连接正常"
            else:
                return False, "❌ Dify连接测试失败"
                
        except Exception as e:
            return False, f"❌ 连接测试异常: {str(e)}"


# 全局实例
_dify_instance = None

def get_dify_client(config_manager=None):
    """获取Dify客户端实例"""
    global _dify_instance
    
    if _dify_instance is None:
        try:
            api_key = None
            if config_manager:
                # 尝试从不同位置获取API密钥
                if hasattr(config_manager, 'api_config'):
                    api_key = config_manager.api_config.get('dify_api_key', '')
                elif hasattr(config_manager, 'get'):
                    api_key = config_manager.get('Dify', 'api_key', fallback='')
            
            _dify_instance = DifyClient(api_key if api_key else None)
            logger.info("Dify客户端初始化成功")
            
        except Exception as e:
            logger.error(f"初始化Dify客户端失败: {str(e)}")
            _dify_instance = DifyClient()
    
    return _dify_instance