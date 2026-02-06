"""
DeepSeek OCR一体化识别翻译引擎
使用本地部署的DeepSeek-OCR模型进行OCR识别和翻译一体化处理
"""

import os
import ssl
import time
import hashlib
import tempfile
from typing import Any, List, Dict, Optional, Tuple
from pathlib import Path
from functools import lru_cache

import numpy as np
from PIL import Image
import torch

# ===== 必须在导入任何HuggingFace库之前设置环境变量 =====
# 修复Windows SSL证书问题
ssl._create_default_https_context = ssl._create_unverified_context

# 设置环境变量
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["SSL_CERT_FILE"] = ""
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"  # 离线模式
os.environ["TRANSFORMERS_OFFLINE"] = "1"  # transformers离线模式

import urllib3
from transformers import AutoModel, AutoTokenizer

# 禁用urllib3警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .vision_ocr import VisionOCREngine, VisionTextBlock


class LRUCache:
    """简单的LRU缓存实现"""
    def __init__(self, maxsize=50):
        self.maxsize = maxsize
        self.cache = {}
        self.order = []
    
    def get(self, key):
        """获取缓存值"""
        if key in self.cache:
            # 更新访问顺序
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        """设置缓存值"""
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.maxsize:
            # 移除最久未使用的
            oldest = self.order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = value
        self.order.append(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.order.clear()


class DeepSeekOCRTranslator(VisionOCREngine):
    """DeepSeek OCR一体化识别翻译引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        # 先设置name属性，然后再调用父类的__init__
        self.name = "DeepSeek OCR翻译器"
        
        # 模型配置
        self.model_path = config.get('local_model_path', config.get('model_path', './deepseek-ocr-local'))
        self.device = config.get('device', 'auto')
        self.use_half_precision = config.get('use_half_precision', True)
        
        # 分辨率配置
        self.base_size = config.get('base_size', 1024)
        self.image_size = config.get('image_size', 640)
        self.crop_mode = config.get('crop_mode', True)
        self.max_image_size = config.get('max_image_size', 2048)
        
        # 翻译配置
        self.enable_translation = config.get('enable_translation', True)
        self.target_language = config.get('target_language', 'zh')
        self.source_language = config.get('source_language', 'auto')
        
        # 缓存配置
        self.cache_enabled = config.get('cache_enabled', True)
        self.cache_size = config.get('cache_size', 50)
        self.max_retries = config.get('max_retries', 3)
        
        # 模型和tokenizer
        self.model = None
        self.tokenizer = None
        
        # 缓存系统
        self.image_cache = LRUCache(maxsize=self.cache_size)
        self.prompt_cache = {}
        
        # 现在调用父类的__init__
        super().__init__(config)
        
        # 性能统计扩展
        self.stats.update({
            "cache_hits": 0,
            "cache_misses": 0,
            "retry_count": 0,
            "gpu_inferences": 0,
            "cpu_inferences": 0,
            "avg_gpu_time": 0.0,
            "avg_cpu_time": 0.0
        })
        
        # 使用本地模型，不需要API密钥
        self.use_vision_model = True
        self.requires_api_key = False
        
        print(f"[{self.name}] 初始化一体化OCR翻译引擎")
        print(f"[{self.name}] 模型路径: {self.model_path}")
        print(f"[{self.name}] 设备: {self.device}")
        print(f"[{self.name}] 翻译启用: {self.enable_translation}")
        print(f"[{self.name}] 目标语言: {self.target_language}")
    
    def _setup_device(self):
        """设置设备并优化GPU配置"""
        if self.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                gpu_free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
                gpu_free_memory_gb = gpu_free_memory / (1024**3)
                
                print(f"[{self.name}] 使用GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                print(f"[{self.name}] GPU可用显存: {gpu_free_memory_gb:.1f}GB")
                
                # 设置CUDA优化参数
                torch.backends.cudnn.benchmark = True  # 启用cuDNN自动优化
                torch.backends.cuda.matmul.allow_tf32 = True  # 允许TF32计算
                torch.backends.cudnn.allow_tf32 = True
                
                # 根据显存大小调整配置
                if gpu_memory < 8:  # 小于8GB显存
                    print(f"[{self.name}] 检测到小显存GPU，启用内存优化模式")
                    self.use_half_precision = True
                    self.base_size = 768  # 降低基础分辨率
                    self.image_size = 512
                else:
                    print(f"[{self.name}] 检测到大显存GPU，启用高性能模式")
            else:
                self.device = "cpu"
                print(f"[{self.name}] 使用CPU")
        elif self.device == "cuda" and not torch.cuda.is_available():
            print(f"[{self.name}] CUDA不可用，回退到CPU")
            self.device = "cpu"
        
        print(f"[{self.name}] 设备设置为: {self.device}")
        print(f"[{self.name}] 混合精度: {self.use_half_precision}")
    
    def initialize(self) -> bool:
        """初始化DeepSeek OCR翻译引擎（优化版本）"""
        try:
            print(f"[{self.name}] 初始化一体化OCR翻译引擎（优化版本）...")
            
            # 检查模型路径是否存在
            if not os.path.exists(self.model_path):
                print(f"[{self.name}] 错误: 模型路径不存在: {self.model_path}")
                print(f"[{self.name}] 请确保模型已下载到: {self.model_path}")
                return False
            
            # 设置设备
            self._setup_device()
            
            start_time = time.time()
            
            # 加载tokenizer
            print(f"[{self.name}] 加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # 加载模型（优化版本）
            print(f"[{self.name}] 加载模型（优化配置）...")
            torch_dtype = torch.float16 if self.use_half_precision else torch.float32
            
            # 根据设备类型选择加载策略
            if self.device == "cuda":
                # GPU加载优化
                print(f"[{self.name}] 使用GPU优化加载策略...")
                
                # 检查显存情况
                free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
                free_memory_gb = free_memory / (1024**3)
                print(f"[{self.name}] 加载前可用显存: {free_memory_gb:.1f}GB")
                
                # 使用device_map自动分配
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    torch_dtype=torch_dtype,
                    device_map="auto",
                    low_cpu_mem_usage=True,  # 减少CPU内存使用
                    offload_folder="./offload" if free_memory_gb < 10 else None  # 小显存时启用offload
                )
                
                # 启用梯度检查点以减少显存使用
                if hasattr(self.model, "gradient_checkpointing_enable"):
                    self.model.gradient_checkpointing_enable()
                    print(f"[{self.name}] 已启用梯度检查点")
            else:
                # CPU加载优化
                print(f"[{self.name}] 使用CPU优化加载策略...")
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    torch_dtype=torch_dtype,
                    low_cpu_mem_usage=True
                )
                self.model.to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            load_time = time.time() - start_time
            print(f"[{self.name}] 模型加载完成，耗时: {load_time:.2f}秒")
            print(f"[{self.name}] 模型参数数量: {sum(p.numel() for p in self.model.parameters()):,}")
            print(f"[{self.name}] 模型设备: {self.model.device}")
            print(f"[{self.name}] 模型精度: {self.model.dtype}")
            
            # 模型预热（提高首次推理速度）
            if load_time > 5.0:  # 如果加载时间较长，进行预热
                print(f"[{self.name}] 执行模型预热...")
                self._warmup_model()
            
            # 记录显存使用情况
            if self.device == "cuda":
                allocated = torch.cuda.memory_allocated(0) / (1024**3)
                reserved = torch.cuda.memory_reserved(0) / (1024**3)
                print(f"[{self.name}] GPU显存使用: 已分配 {allocated:.1f}GB, 已保留 {reserved:.1f}GB")
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"[{self.name}] 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _warmup_model(self):
        """模型预热：执行一次小规模推理以加速后续推理"""
        temp_path = None
        temp_output_dir = None
        
        try:
            print(f"[{self.name}] 开始模型预热...")
            warmup_start = time.time()
            
            # 创建一个小测试图像（纯色）
            from PIL import Image
            test_image = Image.new('RGB', (100, 100), color='white')
            
            # 构建简单提示词
            test_prompt = "<image>\n请识别这张图片中的文本。"
            
            # 保存临时图像
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"warmup_{int(time.time())}.jpg")
            test_image.save(temp_path, 'JPEG', quality=90)
            
            # 创建临时输出目录
            temp_output_dir = tempfile.mkdtemp(prefix="deepseek_warmup_")
            
            # 执行预热推理
            with torch.no_grad():
                if hasattr(self.model, 'infer'):
                    # 使用小参数进行预热
                    result = self.model.infer(
                        self.tokenizer,
                        prompt=test_prompt,
                        image_file=temp_path,
                        output_path=temp_output_dir,  # 提供有效的输出路径
                        base_size=256,  # 小分辨率
                        image_size=128,
                        crop_mode=False,
                        save_results=False,
                        test_compress=False
                    )
                    print(f"[{self.name}] 预热推理完成，结果长度: {len(str(result))}")
            
            warmup_time = time.time() - warmup_start
            print(f"[{self.name}] 模型预热完成，耗时: {warmup_time:.2f}秒")
            
        except Exception as e:
            print(f"[{self.name}] 模型预热失败（不影响正常使用）: {e}")
        finally:
            # 清理临时文件
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
            # 清理临时输出目录
            if temp_output_dir and os.path.exists(temp_output_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_output_dir)
                except Exception as e:
                    print(f"[{self.name}] 清理预热输出目录失败: {e}")
            
            # 清理显存
            if self.device == "cuda":
                torch.cuda.empty_cache()
    
    def _calculate_image_hash(self, image: np.ndarray) -> str:
        """计算图像哈希值用于缓存"""
        # 将图像转换为字节并计算MD5
        if isinstance(image, np.ndarray):
            # 对于numpy数组，使用tobytes
            image_bytes = image.tobytes()
        else:
            # 对于PIL图像，转换为字节
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()
        
        return hashlib.md5(image_bytes).hexdigest()
    
    def _adaptive_resolution(self, image: Image.Image) -> Tuple[int, int]:
        """智能自适应调整分辨率（优化版本）"""
        width, height = image.size
        
        # 计算图像复杂度（基于颜色变化）
        try:
            # 转换为灰度图并计算标准差
            gray_image = image.convert('L')
            import numpy as np
            gray_array = np.array(gray_image)
            complexity = np.std(gray_array) / 255.0  # 0-1之间的复杂度
            
            # 根据复杂度调整最大尺寸
            if complexity < 0.1:  # 简单图像（如纯色背景）
                effective_max_size = min(self.max_image_size, 1024)
            elif complexity < 0.3:  # 中等复杂度
                effective_max_size = min(self.max_image_size, 1536)
            else:  # 高复杂度（如截图、文档）
                effective_max_size = self.max_image_size
                
            print(f"[{self.name}] 图像复杂度: {complexity:.2f}, 有效最大尺寸: {effective_max_size}")
        except Exception as e:
            print(f"[{self.name}] 复杂度计算失败: {e}")
            effective_max_size = self.max_image_size
        
        # 根据设备能力调整
        if self.device == "cpu":
            # CPU模式下使用更小的分辨率
            effective_max_size = min(effective_max_size, 1024)
        
        # 如果图像太大，调整大小
        if max(width, height) > effective_max_size:
            scale = effective_max_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            print(f"[{self.name}] 图像从 {width}x{height} 调整到 {new_width}x{new_height}")
            return new_width, new_height
        
        # 如果图像太小，适当放大（但不超过原始尺寸的2倍）
        min_size = 256  # 最小处理尺寸
        if max(width, height) < min_size:
            scale = min_size / max(width, height)
            # 限制放大倍数
            scale = min(scale, 2.0)
            new_width = int(width * scale)
            new_height = int(height * scale)
            print(f"[{self.name}] 图像从 {width}x{height} 放大到 {new_width}x{new_height}")
            return new_width, new_height
        
        return width, height
    
    def _optimize_image_quality(self, image: Image.Image) -> Image.Image:
        """优化图像质量以提高OCR准确率"""
        try:
            # 检查图像模式
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            # 增强对比度（对于低对比度图像）
            from PIL import ImageEnhance
            
            # 转换为灰度图检查对比度
            gray_image = image.convert('L')
            import numpy as np
            gray_array = np.array(gray_image)
            
            # 计算对比度指标
            min_val = np.min(gray_array)
            max_val = np.max(gray_array)
            contrast_ratio = (max_val - min_val) / 255.0
            
            # 如果对比度过低，增强对比度
            if contrast_ratio < 0.3:
                print(f"[{self.name}] 检测到低对比度图像 ({contrast_ratio:.2f})，增强对比度")
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)  # 增强50%
            
            # 锐化图像（对于模糊图像）
            if contrast_ratio > 0.7:  # 高对比度图像可能受益于锐化
                print(f"[{self.name}] 应用轻度锐化")
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.2)  # 轻微锐化
            
            return image
            
        except Exception as e:
            print(f"[{self.name}] 图像质量优化失败: {e}")
            return image
    
    def _build_prompt(self, translate: bool = True) -> str:
        """构建一体化识别翻译提示词"""
        cache_key = f"prompt_{translate}_{self.target_language}"
        
        if cache_key in self.prompt_cache:
            return self.prompt_cache[cache_key]
        
        if translate:
            prompt = f"""<image>
请仔细识别这张图片中的所有文本内容，并完成以下任务：

【任务要求】
1. 识别图片中的每一段文本（包括标题、正文、注释、代码等）
2. 将非{self.target_language}文本翻译成{self.target_language}
3. {self.target_language}文本保持原样
4. 保持原文的格式、布局和结构
5. 对于代码、命令行等技术内容：
   - 代码部分不要翻译
   - 注释需要翻译
   - 保留代码格式
6. 对于表格、列表等结构化内容，保持原有结构

【输出格式】
请按照以下格式输出：
═══════════════════════════════════════
【原文识别】
[列出所有识别到的文本，保持原格式]

【翻译结果】
[翻译后的文本，保持相同格式]
═══════════════════════════════════════

请确保识别准确完整，翻译自然流畅。"""
        else:
            prompt = """<image>
请识别这张图片中的所有文本内容，保持原文的格式和布局。"""
        
        self.prompt_cache[cache_key] = prompt
        return prompt
    
    def _save_temp_image(self, image: Image.Image) -> str:
        """保存临时图像文件（优化版本）"""
        # 创建临时目录
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"deepseek_ocr_temp_{int(time.time())}.jpg")
        
        # 优化图像质量
        image = self._optimize_image_quality(image)
        
        # 智能调整分辨率
        width, height = self._adaptive_resolution(image)
        if (width, height) != image.size:
            print(f"[{self.name}] 调整图像大小: {image.size} -> {width}x{height}")
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # 根据图像内容选择最佳压缩质量
        try:
            # 检查图像类型
            import numpy as np
            gray_image = image.convert('L')
            gray_array = np.array(gray_image)
            
            # 计算图像复杂度
            complexity = np.std(gray_array) / 255.0
            
            # 根据复杂度选择压缩质量
            if complexity < 0.1:  # 简单图像
                quality = 75  # 较低质量，文件更小
            elif complexity < 0.3:  # 中等复杂度
                quality = 85
            else:  # 高复杂度（文档、截图）
                quality = 95  # 高质量，保持文本清晰
            
            print(f"[{self.name}] 图像复杂度: {complexity:.2f}, 使用JPEG质量: {quality}")
            
            # 保存为JPEG
            image.save(temp_path, 'JPEG', quality=quality, optimize=True)
            
        except Exception as e:
            print(f"[{self.name}] 智能压缩失败，使用默认质量: {e}")
            image.save(temp_path, 'JPEG', quality=90)
        
        # 记录文件大小
        file_size = os.path.getsize(temp_path) / 1024  # KB
        print(f"[{self.name}] 临时文件大小: {file_size:.1f}KB")
        
        return temp_path
    
    def _cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[{self.name}] 清理临时文件失败: {e}")
    
    def _call_model(self, prompt: str, image: Image.Image) -> Any:
        """调用DeepSeek OCR模型进行一体化处理（混合精度优化版本）"""
        temp_image_path = None
        temp_output_dir = None
        
        try:
            # 保存临时图像文件
            temp_image_path = self._save_temp_image(image)
            
            # 创建临时输出目录（DeepSeek OCR的infer方法需要有效的output_path）
            import tempfile
            temp_output_dir = tempfile.mkdtemp(prefix="deepseek_ocr_output_")
            
            # 调用infer方法（官方推荐方式）
            print(f"[{self.name}] 执行OCR推理（混合精度优化）...")
            print(f"[{self.name}] 临时输出目录: {temp_output_dir}")
            start_infer = time.time()
            
            # 根据设备类型选择推理策略
            if self.device == "cuda" and torch.cuda.is_available() and self.use_half_precision:
                # GPU + 混合精度推理（仅在CUDA可用时）
                print(f"[{self.name}] 使用GPU混合精度推理...")
                
                # 启用自动混合精度
                with torch.autocast(device_type='cuda', dtype=torch.float16):
                    result = self.model.infer(
                        self.tokenizer,
                        prompt=prompt,
                        image_file=temp_image_path,
                        output_path=temp_output_dir,  # 提供有效的输出路径
                        base_size=self.base_size,
                        image_size=self.image_size,
                        crop_mode=self.crop_mode,
                        save_results=False,  # 不保存结果文件
                        test_compress=False
                    )
            else:
                # CPU或FP32推理
                print(f"[{self.name}] 使用CPU标准精度推理...")
                # 确保模型在CPU上
                if hasattr(self.model, 'to'):
                    self.model.to('cpu')
                
                result = self.model.infer(
                    self.tokenizer,
                    prompt=prompt,
                    image_file=temp_image_path,
                    output_path=temp_output_dir,  # 提供有效的输出路径
                    base_size=self.base_size,
                    image_size=self.image_size,
                    crop_mode=self.crop_mode,
                    save_results=False,  # 不保存结果文件
                    test_compress=False
                )
            
            infer_time = time.time() - start_infer
            
            # 更新性能统计
            if self.device == "cuda":
                self.stats["gpu_inferences"] += 1
                self.stats["avg_gpu_time"] = (
                    self.stats["avg_gpu_time"] * (self.stats["gpu_inferences"] - 1) + infer_time
                ) / self.stats["gpu_inferences"]
                
                # 记录显存使用情况
                if infer_time > 1.0:  # 只有推理时间较长时才记录
                    allocated = torch.cuda.memory_allocated(0) / (1024**3)
                    peak_allocated = torch.cuda.max_memory_allocated(0) / (1024**3)
                    print(f"[{self.name}] 推理后显存: {allocated:.1f}GB, 峰值: {peak_allocated:.1f}GB")
            else:
                self.stats["cpu_inferences"] += 1
                self.stats["avg_cpu_time"] = (
                    self.stats["avg_cpu_time"] * (self.stats["cpu_inferences"] - 1) + infer_time
                ) / self.stats["cpu_inferences"]
            
            print(f"[{self.name}] OCR推理完成，耗时: {infer_time:.2f}秒")
            
            # 清理显存（如果推理时间较长）
            if self.device == "cuda" and infer_time > 5.0:
                torch.cuda.empty_cache()
                print(f"[{self.name}] 已清理显存缓存")
            
            return result
            
        except Exception as e:
            print(f"[{self.name}] 模型调用失败: {e}")
            raise
        finally:
            # 清理临时文件
            if temp_image_path:
                self._cleanup_temp_file(temp_image_path)
            
            # 清理临时输出目录
            if temp_output_dir and os.path.exists(temp_output_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_output_dir)
                    print(f"[{self.name}] 已清理临时输出目录: {temp_output_dir}")
                except Exception as e:
                    print(f"[{self.name}] 清理临时输出目录失败: {e}")
    
    def _parse_combined_output(self, result: str) -> List[VisionTextBlock]:
        """解析一体化输出（包含原文和翻译）"""
        text_blocks = []
        
        try:
            # 分割原文和翻译部分
            if "【原文识别】" in result and "【翻译结果】" in result:
                # 提取原文部分
                original_start = result.find("【原文识别】") + len("【原文识别】")
                translation_start = result.find("【翻译结果】")
                original_text = result[original_start:translation_start].strip()
                
                # 提取翻译部分
                translation_text = result[translation_start + len("【翻译结果】"):].strip()
                
                # 创建原文文本块
                if original_text:
                    original_block = VisionTextBlock(
                        text=original_text,
                        confidence=0.95,  # DeepSeek OCR置信度较高
                        bbox=[0, 0, 100, 100],  # 占位符，实际应用中需要更精确
                        language=self.source_language,
                        translated_text=translation_text if translation_text else None
                    )
                    text_blocks.append(original_block)
                
                # 如果翻译文本不同，也创建一个翻译文本块
                if translation_text and translation_text != original_text:
                    translation_block = VisionTextBlock(
                        text=translation_text,
                        confidence=0.90,  # 翻译置信度稍低
                        bbox=[0, 0, 100, 100],
                        language=self.target_language
                    )
                    text_blocks.append(translation_block)
            else:
                # 如果没有找到分隔符，将整个结果作为原文
                text_block = VisionTextBlock(
                    text=result.strip(),
                    confidence=0.95,
                    bbox=[0, 0, 100, 100],
                    language="auto"
                )
                text_blocks.append(text_block)
                
        except Exception as e:
            print(f"[{self.name}] 解析输出失败: {e}")
            # 创建默认文本块
            text_block = VisionTextBlock(
                text=str(result)[:500],  # 限制长度
                confidence=0.8,
                bbox=[0, 0, 100, 100],
                language="auto"
            )
            text_blocks.append(text_block)
        
        return text_blocks
    
    def recognize(self, image: np.ndarray, translate: bool = True) -> List[VisionTextBlock]:
        """
        识别图像中的文本（一体化OCR+翻译）
        
        Args:
            image: OpenCV格式的图像 (BGR)
            translate: 是否同时进行翻译
            
        Returns:
            文本块列表，包含识别和翻译结果
        """
        start_time = time.time()
        
        if not self.initialized:
            print(f"[{self.name}] 引擎未初始化")
            return []
        
        try:
            # 转换图像格式
            from PIL import Image
            import cv2
            
            # OpenCV BGR 转 RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)
            else:
                pil_image = Image.fromarray(image)
            
            # 检查缓存
            image_hash = self._calculate_image_hash(image)
            cache_key = f"{image_hash}_{translate}_{self.target_language}"
            
            if self.cache_enabled:
                cached_result = self.image_cache.get(cache_key)
                if cached_result is not None:
                    self.stats["cache_hits"] += 1
                    print(f"[{self.name}] 缓存命中，使用缓存结果")
                    return cached_result
            
            self.stats["cache_misses"] += 1
            
            # 构建提示词
            prompt = self._build_prompt(translate and self.enable_translation)
            
            # 调用模型
            result = self._call_model(prompt, pil_image)
            
            # 解析结果
            text_blocks = self._parse_combined_output(str(result))
            
            # 更新缓存
            if self.cache_enabled and text_blocks:
                self.image_cache.set(cache_key, text_blocks)
            
            # 更新统计
            elapsed = time.time() - start_time
            self._update_stats(elapsed, success=True)
            self.stats['total_recognitions'] += 1
            
            print(f"[{self.name}] 识别完成，找到 {len(text_blocks)} 个文本块")
            if text_blocks and len(text_blocks) > 0:
                sample_text = text_blocks[0].text[:100] + "..." if len(text_blocks[0].text) > 100 else text_blocks[0].text
                print(f"[{self.name}] 示例文本: {sample_text}")
            
            return text_blocks
            
        except Exception as e:
            print(f"[{self.name}] 识别失败: {e}")
            import traceback
            traceback.print_exc()
            
            elapsed = time.time() - start_time
            self._update_stats(elapsed, success=False)
            
            return []
    
    def batch_process(self, images: List[np.ndarray], translate: bool = True) -> List[List[VisionTextBlock]]:
        """批量处理图像"""
        results = []
        
        for i, image in enumerate(images):
            print(f"[{self.name}] 处理图像 {i+1}/{len(images)}")
            result = self.recognize(image, translate)
            results.append(result)
            
            # 清理显存
            if self.device == "cuda" and (i + 1) % 5 == 0:
                torch.cuda.empty_cache()
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """引擎健康状态检查"""
        checks = {
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "initialized": self.initialized,
            "gpu_available": torch.cuda.is_available() if self.device == "cuda" else True,
            "model_path_exists": os.path.exists(self.model_path),
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.image_cache.cache)
        }
        
        # 计算成功率
        total = self.stats['success_count'] + self.stats['fail_count']
        success_rate = self.stats['success_count'] / total if total > 0 else 0
        
        status = "healthy" if all(checks.values()) and success_rate > 0.8 else "degraded"
        
        return {
            "status": status,
            "checks": checks,
            "success_rate": success_rate,
            "stats": self.get_stats(),
            "recommendation": self._generate_recommendation(checks, success_rate)
        }
    
    def _generate_recommendation(self, checks: Dict[str, bool], success_rate: float) -> str:
        """生成优化建议"""
        recommendations = []
        
        if not checks["model_loaded"]:
            recommendations.append("模型未加载，请检查模型路径和权限")
        
        if checks["gpu_available"] and self.device == "cpu":
            recommendations.append("检测到GPU可用，建议切换到GPU模式以获得更好性能")
        
        if success_rate < 0.8:
            recommendations.append(f"成功率较低 ({success_rate:.1%})，建议检查图像质量和模型配置")
        
        if self.stats['avg_processing_time'] > 30.0:
            recommendations.append(f"平均处理时间较长 ({self.stats['avg_processing_time']:.1f}秒)，建议降低图像分辨率")
        
        return "; ".join(recommendations) if recommendations else "系统运行正常"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = super().get_stats()
        stats.update({
            "model_path": self.model_path,
            "device": self.device,
            "use_half_precision": self.use_half_precision,
            "base_size": self.base_size,
            "image_size": self.image_size,
            "crop_mode": self.crop_mode,
            "enable_translation": self.enable_translation,
            "target_language": self.target_language,
            "cache_enabled": self.cache_enabled,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_rate": self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"]),
            "gpu_inferences": self.stats["gpu_inferences"],
            "cpu_inferences": self.stats["cpu_inferences"],
            "avg_gpu_time": self.stats["avg_gpu_time"],
            "avg_cpu_time": self.stats["avg_cpu_time"],
            "initialized": self.initialized
        })
        return stats
    
    def cleanup(self):
        """清理资源"""
        if self.model is not None:
            del self.model
            self.model = None
            
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        # 清空缓存
        self.image_cache.clear()
        self.prompt_cache.clear()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        print(f"[{self.name}] 资源已清理")
        self.initialized = False
    
    # ===== 异步处理功能 =====
    
    def recognize_async(self, image: np.ndarray, translate: bool = True, callback=None):
        """
        异步识别图像中的文本
        
        Args:
            image: OpenCV格式的图像 (BGR)
            translate: 是否同时进行翻译
            callback: 回调函数，接收识别结果
        
        Returns:
            threading.Thread: 异步线程对象
        """
        import threading
        
        def async_task():
            try:
                result = self.recognize(image, translate)
                if callback:
                    callback(result)
            except Exception as e:
                print(f"[{self.name}] 异步识别失败: {e}")
                if callback:
                    callback([])
        
        thread = threading.Thread(target=async_task, daemon=True)
        thread.start()
        return thread
    
    def batch_process_async(self, images: List[np.ndarray], translate: bool = True,
                           max_workers: int = 2, callback=None):
        """
        异步批量处理图像
        
        Args:
            images: 图像列表
            translate: 是否同时进行翻译
            max_workers: 最大并发数
            callback: 每张图像处理完成后的回调函数
        
        Returns:
            List[threading.Thread]: 线程列表
        """
        import threading
        from queue import Queue
        
        results = []
        threads = []
        image_queue = Queue()
        
        # 将图像放入队列
        for i, image in enumerate(images):
            image_queue.put((i, image))
        
        # 工作线程函数
        def worker(worker_id):
            while not image_queue.empty():
                try:
                    idx, image = image_queue.get_nowait()
                    print(f"[{self.name}] 工作线程 {worker_id} 处理图像 {idx+1}/{len(images)}")
                    
                    result = self.recognize(image, translate)
                    results.append((idx, result))
                    
                    if callback:
                        callback(idx, result)
                    
                    image_queue.task_done()
                    
                except Exception as e:
                    print(f"[{self.name}] 工作线程 {worker_id} 处理失败: {e}")
                    results.append((idx, []))
                    image_queue.task_done()
        
        # 创建工作线程
        for i in range(min(max_workers, len(images))):
            thread = threading.Thread(target=worker, args=(i+1,), daemon=True)
            thread.start()
            threads.append(thread)
        
        return threads, results
    
    def get_async_stats(self) -> Dict[str, Any]:
        """获取异步处理统计信息"""
        stats = self.get_stats()
        stats.update({
            "async_capable": True,
            "max_async_workers": 4,  # 建议的最大工作线程数
            "recommended_batch_size": 10 if self.device == "cuda" else 5,
            "async_processing_tips": [
                "使用recognize_async进行单张图像异步处理",
                "使用batch_process_async进行批量异步处理",
                "GPU模式下可增加max_workers以提高吞吐量",
                "注意监控GPU显存使用情况"
            ]
        })
        return stats


# 工厂函数
def create_engine(config: Dict[str, Any]) -> DeepSeekOCRTranslator:
    """创建DeepSeek OCR翻译引擎"""
    return DeepSeekOCRTranslator(config)