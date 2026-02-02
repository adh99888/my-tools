"""
硅基流动翻译器
使用OpenAI兼容API，支持DeepSeek等模型
"""

import time
from typing import Dict, Any
from ..base_translator import BaseTranslator
from ..model_router import TranslationRequest, TranslationResult

class SiliconFlowTranslator(BaseTranslator):
    """硅基流动翻译器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "硅基流动"
        self.max_tokens = config.get('max_tokens', 65536)  # 硅基流动支持长上下文
    
    def initialize(self) -> bool:
        """初始化硅基流动翻译器"""
        try:
            # 检查API密钥
            if not self.api_key:
                print("硅基流动 API密钥未配置")
                return False
            
            # 尝试导入openai
            try:
                from openai import OpenAI
            except ImportError:
                print("OpenAI SDK未安装，请运行: pip install openai")
                return False
            
            # 创建客户端
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else "https://api.siliconflow.cn/v1"
            )
            
            # 测试连接
            try:
                # 简单测试API
                test_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                self.initialized = True
                print(f"硅基流动翻译器初始化成功，模型: {self.model}")
                return True
            except Exception as e:
                print(f"硅基流动 API测试失败: {e}")
                return False
                
        except Exception as e:
            print(f"硅基流动翻译器初始化失败: {e}")
            return False
    
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """翻译文本"""
        start_time = time.time()
        
        if not self.initialized or not self.client:
            return self._create_error_result(request, Exception("翻译器未初始化"))
        
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(request)
            
            # 调用硅基流动 API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.text}
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,  # 低温度，保持准确性
                stream=False
            )
            
            # 提取翻译结果
            translated_text = response.choices[0].message.content.strip()
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000
            
            # 创建结果对象
            result = TranslationResult(
                translated_text=translated_text,
                source_text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                confidence=0.87,  # 硅基流动翻译质量良好
                model=self.model,
                response_time=response_time,
                metadata={
                    'model': self.model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                        'completion_tokens': response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                        'total_tokens': response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                    }
                }
            )
            
            print(f"硅基流动翻译完成: {len(request.text)}字符 -> {len(translated_text)}字符, "
                  f"耗时{response_time:.2f}ms")
            
            return result
            
        except Exception as e:
            print(f"硅基流动翻译失败: {e}")
            return self._create_error_result(request, e)
    
    def _build_system_prompt(self, request: TranslationRequest) -> str:
        """构建硅基流动专用的系统提示词"""
        # 硅基流动通常托管DeepSeek等模型，提示词可以更通用
        return f"""你是一个专业的翻译助手，专门处理屏幕文本和界面翻译。
请将以下文本从{request.source_lang}翻译成{request.target_lang}。

重要要求：
1. 保持专业术语的准确性
2. 保持原文的格式和结构
3. 对于界面文本（菜单、按钮、错误信息等），保持简洁
4. 对于代码和技术内容，使用专业的技术术语
5. 对于长文本，保持段落结构
6. 只输出翻译结果，不要添加额外说明

原文："""