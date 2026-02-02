"""
智谱GLM翻译器
使用智谱AI官方SDK
"""

import time
from typing import Dict, Any
from ..base_translator import BaseTranslator
from ..model_router import TranslationRequest, TranslationResult

class GLMTranslator(BaseTranslator):
    """智谱GLM翻译器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "智谱GLM"
        self.max_tokens = config.get('max_tokens', 2048)  # GLM标准上下文
    
    def initialize(self) -> bool:
        """初始化GLM翻译器"""
        try:
            # 检查API密钥
            if not self.api_key:
                print("智谱GLM API密钥未配置")
                return False
            
            # 尝试导入zhipuai
            try:
                import zhipuai
            except ImportError:
                print("ZhipuAI SDK未安装，请运行: pip install zhipuai")
                return False
            
            # 创建客户端
            self.client = zhipuai.ZhipuAI(api_key=self.api_key)
            
            # 测试连接
            try:
                # 简单测试API
                test_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                self.initialized = True
                print(f"GLM翻译器初始化成功，模型: {self.model}")
                return True
            except Exception as e:
                print(f"GLM API测试失败: {e}")
                return False
                
        except Exception as e:
            print(f"GLM翻译器初始化失败: {e}")
            return False
    
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """翻译文本（GLM响应速度快，适合短文本）"""
        start_time = time.time()
        
        if not self.initialized or not self.client:
            return self._create_error_result(request, Exception("翻译器未初始化"))
        
        try:
            # 构建系统提示词（GLM对提示词敏感，需要更精确）
            system_prompt = self._build_system_prompt(request)
            
            # 调用GLM API
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
                confidence=0.92,  # GLM翻译质量较高，响应速度快
                model=self.model,
                response_time=response_time,
                metadata={
                    'model': self.model,
                    'task_id': response.id if hasattr(response, 'id') else '',
                    'usage': {
                        'total_tokens': response.usage.total_tokens if hasattr(response, 'usage') else 0
                    }
                }
            )
            
            print(f"GLM翻译完成: {len(request.text)}字符 -> {len(translated_text)}字符, "
                  f"耗时{response_time:.2f}ms")
            
            return result
            
        except Exception as e:
            print(f"GLM翻译失败: {e}")
            return self._create_error_result(request, e)
    
    def _build_system_prompt(self, request: TranslationRequest) -> str:
        """构建GLM专用的系统提示词"""
        # GLM对提示词格式比较敏感，需要更明确的指令
        return f"""你是一个专业的翻译助手。你的任务是将文本从{request.source_lang}翻译成{request.target_lang}。
请严格遵守以下规则：
1. 只输出翻译结果，不要添加任何额外内容
2. 保持原文的格式和标点符号
3. 技术术语要准确翻译
4. 如果原文是界面文本（菜单、按钮、错误信息等），保持简洁
5. 如果原文包含代码，只翻译注释，不翻译代码

现在开始翻译，只输出翻译结果：

原文："""