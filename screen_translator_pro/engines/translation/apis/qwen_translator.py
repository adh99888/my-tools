"""
通义千问翻译器
使用阿里云Dashscope API
"""

import time
from typing import Dict, Any
from ..base_translator import BaseTranslator
from ..model_router import TranslationRequest, TranslationResult

class QwenTranslator(BaseTranslator):
    """通义千问翻译器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "通义千问"
        self.max_tokens = min(config.get('max_tokens', 8192), 8192)  # 通义千问最大8192
    
    def initialize(self) -> bool:
        """初始化通义千问翻译器"""
        try:
            # 检查API密钥
            if not self.api_key:
                print("通义千问 API密钥未配置")
                return False
            
            # 尝试导入dashscope
            try:
                import dashscope
            except ImportError:
                print("Dashscope SDK未安装，请运行: pip install dashscope")
                return False
            
            # 设置API密钥
            dashscope.api_key = self.api_key
            
            # 测试连接
            try:
                # 简单测试API（使用较短的prompt）
                from dashscope import Generation
                test_response = Generation.call(
                    model=self.model,
                    prompt="test",
                    max_tokens=10
                )
                
                if test_response.status_code == 200:
                    self.initialized = True
                    print(f"通义千问翻译器初始化成功，模型: {self.model}")
                    return True
                else:
                    print(f"通义千问 API测试失败: {test_response.message}")
                    return False
                    
            except Exception as e:
                print(f"通义千问 API测试失败: {e}")
                return False
                
        except Exception as e:
            print(f"通义千问翻译器初始化失败: {e}")
            return False
    
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """翻译文本"""
        start_time = time.time()
        
        if not self.initialized:
            return self._create_error_result(request, Exception("翻译器未初始化"))
        
        try:
            import dashscope
            from dashscope import Generation
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt(request)
            
            # 构建完整的prompt
            full_prompt = f"{system_prompt}\n\n原文：{request.text}"
            
            # 调用通义千问 API
            response = Generation.call(
                model=self.model,
                prompt=full_prompt,
                max_tokens=min(self.max_tokens, 8192),
                temperature=0.1,  # 低温度，保持准确性
                stream=False
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API错误: {response.message}"
                print(f"通义千问翻译失败: {error_msg}")
                return self._create_error_result(request, Exception(error_msg))
            
            # 提取翻译结果
            translated_text = response.output.text.strip()
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000
            
            # 创建结果对象
            result = TranslationResult(
                translated_text=translated_text,
                source_text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                confidence=0.88,  # 通义千问翻译质量良好
                model=self.model,
                response_time=response_time,
                metadata={
                    'model': self.model,
                    'request_id': response.request_id,
                    'usage': {
                        'total_tokens': response.usage.total_tokens if hasattr(response, 'usage') else 0
                    }
                }
            )
            
            print(f"通义千问翻译完成: {len(request.text)}字符 -> {len(translated_text)}字符, "
                  f"耗时{response_time:.2f}ms")
            
            return result
            
        except Exception as e:
            print(f"通义千问翻译失败: {e}")
            return self._create_error_result(request, e)
    
    def _build_system_prompt(self, request: TranslationRequest) -> str:
        """构建通义千问专用的系统提示词"""
        return f"""你是一个专业的翻译助手，专门处理中文和英文之间的翻译。
请将以下文本从{request.source_lang}翻译成{request.target_lang}。

重要要求：
1. 保持专业术语的准确性，特别是技术术语
2. 保持原文的格式和结构
3. 对于中文翻译，使用地道的中文表达
4. 对于界面文本，保持简洁明了
5. 对于技术内容，使用专业的技术术语
6. 只输出翻译结果，不要添加额外说明"""