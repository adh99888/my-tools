"""
翻译器基类
定义统一的翻译器接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .model_router import TranslationRequest, TranslationResult

class BaseTranslator(ABC):
    """翻译器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown Translator')
        self.model = config.get('model', '')
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')
        self.max_tokens = config.get('max_tokens', 2048)
        
        self.initialized = False
        self.client = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化翻译器"""
        pass
    
    @abstractmethod
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """翻译文本"""
        pass
    
    def shutdown(self):
        """关闭翻译器"""
        self.client = None
        self.initialized = False
    
    def _build_system_prompt(self, request: TranslationRequest) -> str:
        """构建系统提示词"""
        return f"""你是一个专业的翻译助手。请将以下文本从{request.source_lang}翻译成{request.target_lang}。
要求：
1. 保持专业术语的准确性
2. 保持原文的格式和结构
3. 如果原文是技术内容，请使用专业的技术术语
4. 只输出翻译结果，不要添加额外说明"""
    
    def _create_error_result(self, request: TranslationRequest, error: Exception) -> TranslationResult:
        """创建错误结果"""
        return TranslationResult(
            translated_text=f"[翻译错误: {str(error)[:100]}]",
            source_text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            confidence=0.0,
            model=self.model,
            response_time=0.0,
            metadata={'error': str(error), 'translator': self.name}
        )