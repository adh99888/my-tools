"""
DeepSeek翻译器
使用OpenAI兼容API，专门针对代码和技术内容优化
"""

import time
from typing import Dict, Any
from ..base_translator import BaseTranslator
from ..model_router import TranslationRequest, TranslationResult

class DeepSeekTranslator(BaseTranslator):
    """DeepSeek翻译器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "DeepSeek"
        self.max_tokens = config.get('max_tokens', 8192)  # DeepSeek标准上下文
    
    def initialize(self) -> bool:
        """初始化DeepSeek翻译器"""
        try:
            # 检查API密钥
            if not self.api_key:
                print("DeepSeek API密钥未配置")
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
                base_url=self.base_url if self.base_url else "https://api.deepseek.com/v1"
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
                print(f"DeepSeek翻译器初始化成功，模型: {self.model}")
                return True
            except Exception as e:
                print(f"DeepSeek API测试失败: {e}")
                return False
                
        except Exception as e:
            print(f"DeepSeek翻译器初始化失败: {e}")
            return False
    
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """翻译文本，特别针对代码和技术内容优化"""
        start_time = time.time()
        
        if not self.initialized or not self.client:
            return self._create_error_result(request, Exception("翻译器未初始化"))
        
        try:
            # 检查文本是否为代码/技术内容
            is_technical = self._is_technical_text(request.text)
            
            # 构建针对性的系统提示词
            system_prompt = self._build_system_prompt(request, is_technical)
            
            # 调用DeepSeek API
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
                confidence=0.95 if is_technical else 0.85,  # DeepSeek在技术内容上表现更好
                model=self.model,
                response_time=response_time,
                metadata={
                    'model': self.model,
                    'is_technical': is_technical,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                        'completion_tokens': response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                        'total_tokens': response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                    }
                }
            )
            
            content_type = "技术内容" if is_technical else "普通文本"
            print(f"DeepSeek翻译完成 ({content_type}): {len(request.text)}字符 -> {len(translated_text)}字符, "
                  f"耗时{response_time:.2f}ms")
            
            return result
            
        except Exception as e:
            print(f"DeepSeek翻译失败: {e}")
            return self._create_error_result(request, e)
    
    def _is_technical_text(self, text: str) -> bool:
        """判断文本是否为技术内容"""
        technical_indicators = [
            # 代码相关
            '{', '}', '(', ')', '[', ']', ';', '=', '==', '!=', '+=', '-=',
            'def ', 'class ', 'import ', 'from ', 'function ', 'var ', 'let ', 'const ',
            'if ', 'else ', 'for ', 'while ', 'return ', 'public ', 'private ', 'protected ',
            
            # 技术术语
            'error', 'exception', 'bug', 'debug', 'compile', 'runtime',
            'api', 'sdk', 'framework', 'library', 'module', 'package',
            'server', 'client', 'database', 'query', 'transaction',
            'algorithm', 'data structure', 'optimization', 'performance',
            
            # 命令行
            'command', 'terminal', 'shell', 'bash', 'powershell', 'cmd',
            'sudo', 'chmod', 'chown', 'git', 'clone', 'push', 'pull',
            
            # 文件路径
            '/home/', '/usr/', 'C:\\', 'D:\\', '.py', '.js', '.java', '.cpp'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in technical_indicators if indicator in text_lower)
        
        # 如果包含多个技术特征，认为是技术内容
        return indicator_count >= 3 or any(keyword in text_lower for keyword in ['error:', 'exception:', 'traceback'])
    
    def _build_system_prompt(self, request: TranslationRequest, is_technical: bool) -> str:
        """构建DeepSeek专用的系统提示词"""
        if is_technical:
            return f"""你是一个专业的翻译助手，专门处理技术文档、代码注释和命令行输出。
请将以下文本从{request.source_lang}翻译成{request.target_lang}。

重要要求（技术内容）：
1. 技术术语必须准确，使用行业标准译法
2. 代码部分不要翻译，保持原样
3. 注释需要翻译，但要保持简洁
4. 错误信息和日志保持技术准确性
5. 命令行指令和参数不要翻译
6. 文件路径和URL保持原样
7. 对于API文档，保持技术参数的准确性
8. 只输出翻译结果，不要添加额外说明

原文："""
        else:
            return f"""你是一个专业的翻译助手。
请将以下文本从{request.source_lang}翻译成{request.target_lang}。

要求：
1. 保持专业术语的准确性
2. 保持原文的格式和结构
3. 对于界面文本，保持简洁明了
4. 只输出翻译结果，不要添加额外说明

原文："""