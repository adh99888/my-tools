"""
DeepSeek 本地OCR引擎
使用本地部署的DeepSeek-OCR模型进行OCR识别
"""

import os
import ssl
import time
from typing import Any, List, Dict
import numpy as np
from .vision_ocr import VisionOCREngine, VisionTextBlock

# ===== 必须在导入任何HuggingFace库之前设置环境变量 =====
# 修复Windows SSL证书问题
ssl._create_default_https_context = ssl._create_unverified_context

# 设置环境变量
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = ""
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"  # 离线模式

import torch
import urllib3
from transformers import AutoModel, AutoTokenizer
from PIL import Image

# 禁用urllib3警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DeepSeekLocalOCR(VisionOCREngine):
    """DeepSeek本地OCR引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "DeepSeek本地OCR"
        
        # 本地模型配置
        self.model_path = config.get('local_model_path', './deepseek-ocr-local')
        self.device = config.get('device', 'auto')
        self.use_half_precision = config.get('use_half_precision', True)
        self.max_length = config.get('max_length', 512)
        
        # 模型和tokenizer
        self.model = None
        self.tokenizer = None
        
        # 性能统计
        self.stats = {
            "total_inferences": 0,
            "total_time": 0.0,
            "avg_time": 0.0
        }
        
        # 使用本地模型，不需要API密钥
        self.use_vision_model = True
        self.requires_api_key = False
        
    def _setup_device(self):
        """设置设备"""
        if self.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
                print(f"[DeepSeekLocalOCR] 使用GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                print("[DeepSeekLocalOCR] 使用CPU")
        elif self.device == "cuda" and not torch.cuda.is_available():
            print("[DeepSeekLocalOCR] CUDA不可用，回退到CPU")
            self.device = "cpu"
            
        print(f"[DeepSeekLocalOCR] 设备设置为: {self.device}")
        
    def initialize(self) -> bool:
        """初始化DeepSeek本地OCR引擎"""
        try:
            print(f"[DeepSeekLocalOCR] 初始化本地OCR引擎，模型路径: {self.model_path}")
            
            # 检查模型路径是否存在
            if not os.path.exists(self.model_path):
                print(f"[DeepSeekLocalOCR] 错误: 模型路径不存在: {self.model_path}")
                print(f"[DeepSeekLocalOCR] 请确保模型已下载到: {self.model_path}")
                return False
            
            # 设置设备
            self._setup_device()
            
            start_time = time.time()
            
            # 加载tokenizer
            print("[DeepSeekLocalOCR] 加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # 加载模型
            print("[DeepSeekLocalOCR] 加载模型...")
            torch_dtype = torch.float16 if self.use_half_precision else torch.float32
            
            if self.device == "cuda":
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    torch_dtype=torch_dtype,
                    device_map="auto" if torch.cuda.is_available() else None
                )
            else:
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    torch_dtype=torch_dtype
                )
                self.model.to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            load_time = time.time() - start_time
            print(f"[DeepSeekLocalOCR] 模型加载完成，耗时: {load_time:.2f}秒")
            print(f"[DeepSeekLocalOCR] 模型参数数量: {sum(p.numel() for p in self.model.parameters()):,}")
            print(f"[DeepSeekLocalOCR] 模型设备: {self.model.device}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"[DeepSeekLocalOCR] 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        预处理图像
        
        Args:
            image: PIL图像
            
        Returns:
            预处理后的PIL图像
        """
        # 转换为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 这里可以添加更多的图像预处理逻辑
        # 例如：调整大小、归一化等
        
        return image
    
    def recognize_text(self, image: Image.Image, **kwargs) -> List[VisionTextBlock]:
        """
        识别图像中的文本
        
        Args:
            image: PIL图像
            **kwargs: 其他参数
            
        Returns:
            文本块列表
        """
        if not self.initialized:
            print("[DeepSeekLocalOCR] 引擎未初始化")
            return []
        
        start_time = time.time()
        
        try:
            # 预处理图像
            processed_image = self.preprocess_image(image)
            
            # 准备提示词
            prompt = kwargs.get('prompt', "<image>\nFree OCR.")
            temperature = kwargs.get('temperature', 0.1)
            top_p = kwargs.get('top_p', 0.9)
            
            # 准备输入
            inputs = self.tokenizer(
                prompt,
                images=[processed_image],
                return_tensors="pt"
            )
            
            # 移动到设备
            if self.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 生成文本
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True
                )
            
            # 解码结果
            result_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 计算处理时间
            inference_time = time.time() - start_time
            
            # 更新统计信息
            self.stats["total_inferences"] += 1
            self.stats["total_time"] += inference_time
            self.stats["avg_time"] = self.stats["total_time"] / max(1, self.stats["total_inferences"])
            
            # 创建文本块
            text_block = VisionTextBlock(
                text=result_text,
                confidence=1.0,  # 本地模型不提供置信度
                bbox=[0, 0, image.width, image.height],  # 整个图像
                language="auto"
            )
            
            print(f"[DeepSeekLocalOCR] OCR完成，耗时: {inference_time:.2f}秒")
            print(f"[DeepSeekLocalOCR] 识别结果: {result_text[:100]}...")
            
            return [text_block]
            
        except Exception as e:
            print(f"[DeepSeekLocalOCR] 识别失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            **self.stats,
            "model_path": self.model_path,
            "device": self.device,
            "use_half_precision": self.use_half_precision,
            "initialized": self.initialized
        }
    
    def cleanup(self):
        """清理资源"""
        if self.model is not None:
            del self.model
            self.model = None
            
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        print("[DeepSeekLocalOCR] 资源已清理")
        self.initialized = False


# 工厂函数
def create_engine(config: Dict[str, Any]) -> DeepSeekLocalOCR:
    """创建DeepSeek本地OCR引擎"""
    return DeepSeekLocalOCR(config)