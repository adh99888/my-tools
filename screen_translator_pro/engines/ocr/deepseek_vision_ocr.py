"""
DeepSeek视觉OCR引擎
使用DeepSeek视觉模型进行OCR识别
"""
import json
import re
from typing import Any, List, Dict
import numpy as np
from .vision_ocr import VisionOCREngine, VisionTextBlock

class DeepSeekVisionOCR(VisionOCREngine):
    """DeepSeek视觉OCR引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "DeepSeek视觉OCR"
        
        # DeepSeek特定配置
        self.model_name = config.get('model', 'deepseek-ai/DeepSeek-OCR')
        self.use_vision_model = True
    
    def initialize(self) -> bool:
        """初始化DeepSeek视觉OCR引擎"""
        try:
            # 检查API密钥
            if not self.api_key:
                print("DeepSeek API密钥未配置")
                return False
            
            # 尝试导入openai（用于调用API）
            try:
                from openai import OpenAI
            except ImportError:
                print("OpenAI SDK未安装，请运行: pip install openai")
                return False
            
            # 创建客户端
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            self.initialized = True
            print(f"DeepSeek视觉OCR引擎初始化成功，模型: {self.model_name}")
            return True
                
        except Exception as e:
            print(f"DeepSeek视觉OCR引擎初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _call_vision_api(self, image_base64: str, prompt: str, translate: bool) -> Any:
        """调用DeepSeek视觉API"""
        if not self.initialized:
            raise ValueError("引擎未初始化")
        
        try:
            print(f"调用DeepSeek视觉API，模型: {self.model_name}，翻译模式: {translate}")
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=2048  # 视觉识别需要更多token
            )
            
            return response
            
        except Exception as e:
            print(f"DeepSeek视觉API调用异常: {e}")
            raise
    
    def _parse_response(self, response: Any, translate: bool) -> List[VisionTextBlock]:
        """解析DeepSeek视觉API响应"""
        try:
            # 获取响应文本
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
            else:
                content = str(response)
            
            print(f"DeepSeek视觉API响应: {str(content)[:200]}...")
            
            # 解析响应文本
            text_blocks = self._extract_text_blocks(str(content), translate)
            
            # 如果没有提取到块，创建一个包含整个响应的块
            if not text_blocks and content and str(content).strip():
                content_str = str(content).strip()
                text_block = VisionTextBlock(
                    text=content_str,
                    confidence=0.9,
                    bbox=(0, 0, 100, 100),  # 未知位置
                    language="auto",
                    translated_text=content_str if translate else None
                )
                text_blocks.append(text_block)
            
            print(f"解析到 {len(text_blocks)} 个文本块")
            return text_blocks
            
        except Exception as e:
            print(f"解析DeepSeek响应失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_text_blocks(self, content: str, translate: bool) -> List[VisionTextBlock]:
        """从响应内容中提取文本块"""
        text_blocks = []
        
        try:
            # 尝试解析格式化的响应
            # 格式1: 【原文识别】...【翻译结果】...
            if translate:
                original_match = re.search(r'【原文识别】\s*(.*?)\s*【翻译结果】', content, re.DOTALL)
                translation_match = re.search(r'【翻译结果】\s*(.*?)$', content, re.DOTALL)
                
                if original_match and translation_match:
                    original_text = original_match.group(1).strip()
                    translated_text = translation_match.group(1).strip()
                    
                    # 分割为行
                    original_lines = [line.strip() for line in original_text.split('\n') if line.strip()]
                    translated_lines = [line.strip() for line in translated_text.split('\n') if line.strip()]
                    
                    # 创建对应的文本块
                    for i, (orig_line, trans_line) in enumerate(zip(original_lines, translated_lines)):
                        text_block = VisionTextBlock(
                            text=orig_line,
                            confidence=0.95,  # 视觉模型通常更准确
                            bbox=(0, i*20, 200, (i+1)*20),  # 估计位置
                            language="auto",
                            translated_text=trans_line
                        )
                        text_blocks.append(text_block)
                    
                    return text_blocks
            
            # 格式2: 只有识别结果
            result_match = re.search(r'【识别结果】\s*(.*?)$', content, re.DOTALL)
            if result_match:
                result_text = result_match.group(1).strip()
                lines = [line.strip() for line in result_text.split('\n') if line.strip()]
                
                for i, line in enumerate(lines):
                    text_block = VisionTextBlock(
                        text=line,
                        confidence=0.95,
                        bbox=(0, i*20, 200, (i+1)*20),
                        language="auto"
                    )
                    text_blocks.append(text_block)
                
                return text_blocks
            
            # 格式3: 自由格式响应
            # 尝试按行分割
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            # 过滤掉太短或可能是元信息的行
            filtered_lines = []
            for line in lines:
                # 跳过可能不是文本内容的行
                if len(line) < 2:
                    continue
                if line.startswith('注意:') or line.startswith('要求:') or line.startswith('格式:'):
                    continue
                if 'http://' in line or 'https://' in line:
                    continue
                
                filtered_lines.append(line)
            
            for i, line in enumerate(filtered_lines):
                text_block = VisionTextBlock(
                    text=line,
                    confidence=0.85,
                    bbox=(0, i*20, 200, (i+1)*20),
                    language="auto",
                    translated_text=line if translate else None
                )
                text_blocks.append(text_block)
            
            return text_blocks
            
        except Exception as e:
            print(f"提取文本块失败: {e}")
            return []

# 测试函数
def test_deepseek_vision_ocr():
    """测试DeepSeek视觉OCR"""
    import cv2
    import yaml
    import os
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 创建测试配置
    siliconflow_config = config.get('apis', {}).get('siliconflow', {})
    ocr_config = {
        'model': 'deepseek-ai/DeepSeek-OCR',
        'api_key': siliconflow_config.get('api_key', ''),
        'base_url': siliconflow_config.get('base_url', ''),
        'enable_translation': True,
        'target_language': 'zh'
    }
    
    # 创建测试图像
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    cv2.putText(img, 'Test DeepSeek OCR', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
    
    # 创建引擎
    ocr = DeepSeekVisionOCR(ocr_config)
    
    if ocr.initialize():
        print("引擎初始化成功")
        results = ocr.recognize(img, translate=True)
        
        if results:
            print(f"识别成功！找到 {len(results)} 个文本块:")
            for i, block in enumerate(results):
                print(f"  {i+1}. 原文: '{block.text}'")
                if block.translated_text:
                    print(f"     翻译: '{block.translated_text}'")
        
        stats = ocr.get_stats()
        print(f"统计: {stats}")
    else:
        print("引擎初始化失败")

if __name__ == "__main__":
    test_deepseek_vision_ocr()