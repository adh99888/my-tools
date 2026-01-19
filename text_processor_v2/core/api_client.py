"""
API客户端模块
负责与各种AI模型API进行通信
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIClient:
    """统一的API客户端类"""
    
    def __init__(self, config_manager, model_manager):
        """
        初始化API客户端
        
        Args:
            config_manager: 配置管理器实例
            model_manager: 模型管理器实例
        """
        self.config_manager = config_manager
        self.model_manager = model_manager
        
        # 超时设置
        self.timeout = (30, 60)  # (连接超时, 读取超时)
        
        # 创建带重试的会话
        self.session = self._create_session()
    
    def _create_session(self):
        """创建带重试机制的HTTP会话"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def call_ai_api(self, content: str, model_id: str = None) -> Tuple[bool, str]:
        """
        调用AI API处理文档
        
        Args:
            content: 要处理的文档内容
            model_id: 模型ID，如果为None则使用当前模型
            
        Returns:
            (success: bool, result: str) 成功标志和处理结果
        """
        try:
            # 获取模型配置
            if model_id is None:
                model_id = self.model_manager.current_model_id
            
            validation = self.model_manager.validate_model_config(model_id)
            if not validation['status']:
                return False, f"模型配置验证失败: {validation['message']}"
            
            model_config = validation['config']
            
            # 获取API密钥
            api_key = self.model_manager.config_manager.get_api_key(model_id)
            if not api_key:
                return False, f"模型 '{model_id}' 的API密钥未配置"
            
            # 构建提示词
            prompt = self._build_prompt(content, model_config)
            
            # 准备请求数据
            api_url, headers, data = self._prepare_request(prompt, content, model_config, api_key)
            
            # 发送请求
            model_name = model_config.get('name', model_config.get('model', model_id))
            logger.info(f"正在与 {model_name} 通信...")
            
            response = self.session.post(
                api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 解析响应
            result = self._parse_response(response.json(), model_config.get('provider', 'deepseek'))
            
            if result:
                logger.info(f"API调用成功: {model_name}")
                return True, result
            else:
                return False, "API返回格式异常"
                
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "网络连接失败"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "API密钥无效"
            elif e.response.status_code == 429:
                return False, "请求过于频繁，请稍后再试"
            else:
                return False, f"HTTP错误: {e.response.status_code}"
        except Exception as e:
            return False, f"API调用失败: {str(e)}"
    
    def _build_prompt(self, content: str, model_config: Dict[str, Any]) -> str:
        """
        构建提示词
        
        Args:
            content: 文档内容
            model_config: 模型配置
            
        Returns:
            构建好的提示词
        """
        # 这里可以根据需要定制不同的提示词
        # 目前使用通用提示词
        prompt = """请对以下文档进行专业的排版优化：

具体要求：
1. 保持原文核心内容，不添加新信息
2. 修正错别字和语法错误
3. 根据原文的内容，重新优化段落结构，然后再继续之后的排版
4.优化段落结构，要使逻辑清晰
5. 对标题进行层级标记（不同的层级采用不同的字体大小）
6. 优化标点使用，保持专业性
7. 对列表内容使用-或*标记
8. 保持术语和专有名词不变
9. 重要要求：不要重复文档标题（文章排版完成，要注意检查，标题和下面的第一行不要重复）
10. 段落之间使用自然分隔，不要添加多余空行
11. 清理多余的Markdown标记符号（如孤立的#、*、.等）

请直接返回优化后的完整文档内容。"""
        
        return prompt
    
    def _prepare_request(self, prompt: str, content: str, model_config: Dict[str, Any], 
                         api_key: str) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        准备API请求
        
        Args:
            prompt: 提示词
            content: 文档内容
            model_config: 模型配置
            api_key: API密钥
            
        Returns:
            (api_url, headers, data) 元组
        """
        api_url = f"{model_config['api_base']}/chat/completions"
        
        # 根据不同提供商设置头部
        provider = model_config.get('provider', 'deepseek')
        
        if provider == 'dashscope':  # 阿里云
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        elif provider == 'moonshot':  # Kimi
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        else:  # DeepSeek, SiliconFlow, 百川等
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        
        # 根据不同提供商调整数据格式
        if provider == 'dashscope':
            data = {
                'model': model_config['model'],
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的文档编辑助手，擅长排版和润色。'},
                    {'role': 'user', 'content': prompt + "\n\n" + content}
                ],
                'temperature': 0.3,
                'max_tokens': min(model_config.get('max_tokens', 8192), 32768)
            }
        else:
            data = {
                'model': model_config['model'],
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的文档编辑助手，擅长排版和润色。'},
                    {'role': 'user', 'content': prompt + "\n\n" + content}
                ],
                'temperature': 0.3,
                'max_tokens': min(model_config.get('max_tokens', 8192), 32768),
                'stream': False
            }
        
        return api_url, headers, data
    
    def _parse_response(self, response_data: Dict[str, Any], provider: str) -> Optional[str]:
        """
        解析API响应
        
        Args:
            response_data: API响应数据
            provider: 提供商名称
            
        Returns:
            解析出的文本内容或None
        """
        try:
            if provider == 'dashscope':
                if 'output' in response_data and 'text' in response_data['output']:
                    return response_data['output']['text'].strip()
                elif 'choices' in response_data and len(response_data['choices']) > 0:
                    return response_data['choices'][0]['message']['content'].strip()
            else:
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    return response_data['choices'][0]['message']['content'].strip()
            
            return None
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}")
            return None
    
    def process_with_retry(self, content: str, max_retries: int = 3) -> Tuple[bool, str]:
        """
        带重试的文档处理
        
        Args:
            content: 文档内容
            max_retries: 最大重试次数
            
        Returns:
            (success: bool, result: str) 成功标志和处理结果
        """
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                logger.info(f"开始处理 (尝试 {retry_count + 1}/{max_retries + 1})...")
                success, result = self.call_ai_api(content)
                
                if success:
                    return True, result
                
            except Exception as e:
                logger.error(f"处理失败 (尝试 {retry_count + 1}): {str(e)}")
                retry_count += 1
                
                if retry_count <= max_retries:
                    logger.warning(f"第 {retry_count} 次尝试失败，3秒后重试...")
                    time.sleep(3)
                else:
                    return False, f"处理失败，已达到最大重试次数: {str(e)}"
        
        return False, "处理失败，未知错误"