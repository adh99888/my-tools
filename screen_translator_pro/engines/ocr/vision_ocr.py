"""
视觉OCR引擎
使用大模型视觉能力进行OCR识别，支持直接翻译
"""
import time
import base64
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class VisionTextBlock:
    """视觉识别的文本块"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    language: str = "auto"
    translated_text: Optional[str] = None  # 可选的翻译结果

class VisionOCREngine:
    """视觉OCR引擎基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('model', '')
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', '')
        
        # 识别参数
        self.detail_level = config.get('detail_level', 'high')  # low, high
        self.enable_translation = config.get('enable_translation', True)
        self.target_language = config.get('target_language', 'zh')
        
        # 性能统计
        self.stats = {
            'total_recognitions': 0,
            'avg_processing_time': 0.0,
            'success_count': 0,
            'fail_count': 0
        }
        
        # 初始化状态
        self.initialized = False
        self.client = None
        
        print(f"视觉OCR引擎初始化，模型: {self.model_name}")
        
        # 自动初始化
        self.initialize()
    
    def initialize(self) -> bool:
        """初始化引擎"""
        raise NotImplementedError("子类必须实现initialize方法")
    
    def recognize(self, image: np.ndarray, translate: bool = True) -> List[VisionTextBlock]:
        """
        识别图像中的文本
        
        Args:
            image: OpenCV格式的图像 (BGR)
            translate: 是否同时进行翻译
            
        Returns:
            文本块列表，包含识别和翻译结果
        """
        start_time = time.time()
        
        try:
            # 预处理图像
            processed_image = self._preprocess_image(image)
            
            # 转换为base64
            image_base64 = self._image_to_base64(processed_image)
            
            # 构建提示词
            prompt = self._build_ocr_prompt(translate)
            
            # 调用API
            response = self._call_vision_api(image_base64, prompt, translate)
            
            # 解析响应
            text_blocks = self._parse_response(response, translate)
            
            # 更新统计
            elapsed = time.time() - start_time
            self._update_stats(elapsed, success=True)
            
            return text_blocks
            
        except Exception as e:
            print(f"视觉OCR识别失败: {e}")
            import traceback
            traceback.print_exc()
            
            elapsed = time.time() - start_time
            self._update_stats(elapsed, success=False)
            
            return []
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        # 视觉模型通常能处理原始图像，但可以进行一些优化
        processed = image.copy()
        
        # 如果图像太大，可以调整大小（但会损失细节）
        max_size = self.config.get('max_image_size', 2048)
        h, w = processed.shape[:2]
        
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            
            import cv2
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_AREA)
            print(f"图像从 {w}x{h} 调整到 {new_w}x{new_h}")
        
        return processed
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """将OpenCV图像转换为base64字符串"""
        import cv2
        
        # 将BGR转换为RGB（大多数API期望RGB）
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # 编码为JPEG（压缩率更高）
        success, encoded_image = cv2.imencode('.jpg', rgb_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success:
            raise ValueError("图像编码失败")
        
        image_bytes = encoded_image.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        return image_base64
    
    def _build_ocr_prompt(self, translate: bool) -> str:
        """构建OCR提示词"""
        if translate:
            return f"""请仔细识别这张图片中的所有文本内容。

要求：
1. 识别图片中的每一段文本
2. 将非中文文本翻译成中文
3. 中文文本保持原样
4. 保持原文的格式和布局
5. 对于代码、命令行等技术内容，代码部分不要翻译，注释需要翻译
6. 按照以下格式输出：
【原文识别】
[列出所有识别到的文本，保持原格式]
【翻译结果】
[翻译后的文本，保持相同格式]

请确保识别准确，翻译自然流畅。"""
        else:
            return """请仔细识别这张图片中的所有文本内容。

要求：
1. 识别图片中的每一段文本
2. 保持原文的格式和布局
3. 对于代码、命令行等技术内容，保持原样
4. 按照以下格式输出：
【识别结果】
[列出所有识别到的文本，保持原格式]

请确保识别准确完整。"""
    
    def _call_vision_api(self, image_base64: str, prompt: str, translate: bool) -> Any:
        """调用视觉API"""
        raise NotImplementedError("子类必须实现_call_vision_api方法")
    
    def _parse_response(self, response: Any, translate: bool) -> List[VisionTextBlock]:
        """解析API响应"""
        raise NotImplementedError("子类必须实现_parse_response方法")
    
    def _update_stats(self, elapsed_time: float, success: bool):
        """更新性能统计"""
        self.stats['total_recognitions'] += 1
        
        if success:
            self.stats['success_count'] += 1
        else:
            self.stats['fail_count'] += 1
        
        # 更新平均处理时间（指数移动平均）
        alpha = 0.1
        new_avg = alpha * elapsed_time * 1000 + (1 - alpha) * self.stats['avg_processing_time']
        self.stats['avg_processing_time'] = float(new_avg)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.stats.copy()
    
    def get_combined_text(self, text_blocks: List[VisionTextBlock], include_translation: bool = True) -> str:
        """获取合并的文本"""
        if not text_blocks:
            return ""
        
        if include_translation and any(block.translated_text for block in text_blocks):
            # 使用翻译后的文本
            texts = [block.translated_text if block.translated_text else block.text 
                    for block in text_blocks]
        else:
            # 使用原始文本
            texts = [block.text for block in text_blocks]
        
        # 合并文本，保持原有顺序
        return '\n'.join(texts)
    
    def shutdown(self):
        """关闭引擎"""
        self.client = None
        self.initialized = False