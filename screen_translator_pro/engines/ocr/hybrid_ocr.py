"""
混合OCR引擎
结合Tesseract（英文优势）和EasyOCR（中文优势），提供最优识别效果
针对屏幕文本进行优化处理
"""

import time
import numpy as np
import os
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import cv2

@dataclass
class TextBlock:
    """文本块"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    language: str = "en"

class HybridOCREngine:
    """混合OCR引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.primary = config.get('primary', 'hybrid')
        self.auto_language = config.get('auto_language', True)
        self.preprocess = config.get('preprocess', True)
        self.languages = config.get('languages', ['en', 'zh'])
        
        # Tesseract语言映射 (配置代码 -> Tesseract代码)
        self.tesseract_lang_map = {
            'en': 'eng',
            'zh': 'chi_sim',
            'zhs': 'chi_sim',  # 简体中文
            'zht': 'chi_tra',  # 繁体中文
            'ja': 'jpn',
            'ko': 'kor',
            'fr': 'fra',
            'de': 'deu',
            'es': 'spa',
            'ru': 'rus'
        }
        
        # Tesseract数据目录
        self.tessdata_dir = None
        
        # 初始化引擎
        self.tesseract_available = False
        self.easyocr_available = False
        
        self._init_engines()
        
        # 性能统计
        self.stats = {
            'total_recognitions': 0,
            'avg_processing_time': 0.0,
            'tesseract_usage': 0,
            'easyocr_usage': 0,
            'hybrid_usage': 0
        }
        
        # 调试
        self.debug_fail_count = 0
        self.debug_save_failed_images = True  # 设置为True以保存失败图像用于调试
        
        print(f"混合OCR引擎初始化完成，主引擎: {self.primary}")
    
    def _init_engines(self):
        """初始化OCR引擎"""
        # 初始化Tesseract
        try:
            import pytesseract
            from PIL import Image, ImageOps
            
            # 自动查找Tesseract路径
            tesseract_path = self._find_tesseract_path()
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"[OK] Tesseract路径已配置: {tesseract_path}")
            else:
                print("[WARN] 未找到Tesseract可执行文件，Tesseract OCR将不可用")
                print("  提示: Tesseract已安装但路径未知，尝试添加到PATH或配置tesseract_path")
                self.tesseract_available = False
                print("[INFO] Tesseract OCR标记为不可用")
            
            if tesseract_path:
                self.tesseract_available = True
                print("[OK] Tesseract OCR可用")
                # 设置tessdata目录
                import os
                tesseract_dir = os.path.dirname(tesseract_path)
                self.tessdata_dir = os.path.join(tesseract_dir, 'tessdata')
                print(f"[INFO] Tesseract tessdata目录: {self.tessdata_dir}")
        except (ImportError, OSError, RuntimeError) as e:
            print(f"[FAIL] Tesseract OCR初始化失败: {e}")
            print("  请安装: pip install pytesseract Pillow")
            self.tesseract_available = False
        
        # 初始化EasyOCR
        try:
            import easyocr
            # 延迟初始化，第一次使用时才创建reader
            self.easyocr_reader = None
            self.easyocr_available = True
            print("[OK] EasyOCR可用")
        except (ImportError, OSError, RuntimeError) as e:
            # 检查是否为WinError 1114 (DLL初始化失败)
            if isinstance(e, OSError) and '1114' in str(e):
                print(f"[FAIL] EasyOCR初始化遇到DLL问题: {e}")
                print("  PyTorch DLL加载失败，EasyOCR将不可用")
                print("  可能的解决方案:")
                print("  1. 重启计算机")
                print("  2. 重新安装PyTorch CPU版本:")
                print("     pip install torch==2.9.0 torchvision==0.24.0 --index-url https://download.pytorch.org/whl/cpu --force-reinstall")
                print("  3. 使用Tesseract作为主引擎")
                self.easyocr_available = False
                self.easyocr_reader = None
            else:
                print(f"[FAIL] EasyOCR初始化失败: {e}")
                print("  请安装: pip install easyocr")
                print("  如果遇到PyTorch DLL错误，尝试重新安装PyTorch CPU版本:")
                print("  pip install torch --index-url https://download.pytorch.org/whl/cpu")
                self.easyocr_available = False
        
        if not self.tesseract_available and not self.easyocr_available:
            print("警告: 没有可用的OCR引擎，OCR功能将无法使用")
    
    def _find_tesseract_path(self) -> Optional[str]:
        """查找Tesseract可执行文件路径"""
        # 策略1: 从配置读取
        if 'tesseract_path' in self.config:
            custom_path = self.config['tesseract_path']
            if custom_path and os.path.exists(custom_path):
                return custom_path
        
        # 策略2: 尝试从PATH查找
        try:
            result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True, shell=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        # 策略3: 检查常见安装位置
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\LQJ\AppData\Local\Tesseract-OCR\tesseract.exe",
            r"C:\tesseract\tesseract.exe",
            r"D:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 策略4: 尝试Windows搜索 (可能需要管理员权限)
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-ChildItem -Path C:\\ -Filter tesseract.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1'],
                capture_output=True, text=True, shell=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                for line in lines:
                    if line.endswith('.exe'):
                        return line
        except:
            pass
        
        return None

    def recognize(self, image: np.ndarray, context: Optional[Dict] = None) -> List[TextBlock]:
        """
        识别图像中的文本
        
        Args:
            image: OpenCV格式的图像 (BGR)
            context: 上下文信息，如界面类型、语言偏好等
            
        Returns:
            文本块列表
        """
        start_time = time.time()
        
        processed_image = None
        try:
            # 图像预处理
            if self.preprocess:
                processed_image = self._preprocess_image(image)
            else:
                processed_image = image.copy()
            
            # 确定识别策略
            strategy = self._choose_strategy(context)
            print(f"[OCR调试] 识别策略: {strategy}, Tesseract可用: {self.tesseract_available}, EasyOCR可用: {self.easyocr_available}")
            
            # 执行识别
            if strategy == 'tesseract_only':
                text_blocks = self._recognize_tesseract(processed_image)
                self.stats['tesseract_usage'] += 1
                
            elif strategy == 'easyocr_only':
                text_blocks = self._recognize_easyocr(processed_image)
                self.stats['easyocr_usage'] += 1
                
            else:  # hybrid
                # 优先尝试EasyOCR（中文识别更好）
                easyocr_results = self._recognize_easyocr(processed_image)
                
                if not easyocr_results and self.tesseract_available:
                    print("[混合模式] EasyOCR无结果，尝试Tesseract...")
                    tesseract_results = self._recognize_tesseract(processed_image)
                    text_blocks = tesseract_results
                elif easyocr_results:
                    # 如果EasyOCR成功，尝试用Tesseract补充
                    tesseract_results = self._recognize_tesseract(processed_image)
                    text_blocks = self._merge_results(tesseract_results, easyocr_results)
                else:
                    text_blocks = []
                
                self.stats['hybrid_usage'] += 1
            
            # 后处理
            text_blocks = self._postprocess(text_blocks)
            
            # 更新统计
            elapsed = time.time() - start_time
            self._update_stats(elapsed)
            self.stats['total_recognitions'] += 1
            
            # 调试：保存失败图像
            if not text_blocks and self.debug_save_failed_images:
                self._save_failed_images(image, processed_image, strategy)
            
            return text_blocks
            
        except Exception as e:
            print(f"OCR识别失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 调试：保存失败图像
            if self.debug_save_failed_images:
                try:
                    self._save_failed_images(image, processed_image, 'error')
                except:
                    pass
            
            return []
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        processed = image.copy()
        
        # 转换为灰度图
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # 自适应二值化（对屏幕文本效果更好）
        processed = cv2.adaptiveThreshold(
            processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 去噪
        processed = cv2.medianBlur(processed, 3)
        
        # 边缘增强
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        processed = cv2.filter2D(processed, -1, kernel)
        
        return processed
    
    def _choose_strategy(self, context: Optional[Dict]) -> str:
        """选择识别策略"""
        if self.primary in ['tesseract', 'tesseract_only'] and self.tesseract_available:
            return 'tesseract_only'
        elif self.primary in ['easyocr', 'easyocr_only'] and self.easyocr_available:
            return 'easyocr_only'
        
        # 混合模式：根据上下文选择
        if context:
            ui_type = context.get('ui_type', '')
            languages = context.get('languages', [])
            
            # 命令行界面：英文为主，优先Tesseract
            if ui_type == 'terminal':
                return 'tesseract_only'
            
            # 中文为主的界面：优先EasyOCR
            if languages and 'zh' in languages and 'en' not in languages:
                return 'easyocr_only'
        
        # 默认使用混合模式或回退
        if self.tesseract_available and self.easyocr_available:
            return 'hybrid'
        elif self.easyocr_available:
            return 'easyocr_only'
        elif self.tesseract_available:
            return 'tesseract_only'
        else:
            return 'hybrid'  # 两者都不可用，但应该不会发生，因为前面有检查
    
    def _get_tesseract_lang_param(self) -> str:
        """获取Tesseract语言参数，映射配置代码到Tesseract代码，只返回存在的语言包"""
        import os
        
        if not self.languages or not self.tessdata_dir:
            return 'eng'
        
        available_langs = []
        for lang in self.languages:
            tesseract_lang = self.tesseract_lang_map.get(lang, lang)
            
            # 检查语言包文件是否存在
            lang_file = os.path.join(self.tessdata_dir, f"{tesseract_lang}.traineddata")
            if os.path.exists(lang_file):
                available_langs.append(tesseract_lang)
            else:
                print(f"[WARN] Tesseract语言包 '{tesseract_lang}' 不存在，跳过")
                print(f"  文件路径: {lang_file}")
        
        # 去重
        unique_langs = list(dict.fromkeys(available_langs))
        
        if not unique_langs:
            print("[INFO] 没有可用的Tesseract语言包，使用默认 'eng'")
            # 检查英文包是否存在，如果不存在则Tesseract完全不可用
            eng_file = os.path.join(self.tessdata_dir, "eng.traineddata")
            if os.path.exists(eng_file):
                return 'eng'
            else:
                print("[WARN] 英文语言包也不存在，Tesseract将无法使用")
                self.tesseract_available = False
                return ''
        
        return '+'.join(unique_langs)
    
    def _recognize_tesseract(self, image: np.ndarray) -> List[TextBlock]:
        """使用Tesseract识别"""
        if not self.tesseract_available:
            return []
        
        try:
            import pytesseract
            from PIL import Image
            
            # 转换为PIL图像
            pil_image = Image.fromarray(image)
            
            # 设置语言
            lang_param = self._get_tesseract_lang_param()
            print(f"[OCR调试] Tesseract语言参数: {lang_param}")
            
            # 检查是否有可用的语言包
            if not lang_param:
                print("[WARN] 没有可用的Tesseract语言包，跳过识别")
                return []
            
            # 获取详细数据
            data = pytesseract.image_to_data(
                pil_image, 
                lang=lang_param,
                output_type=pytesseract.Output.DICT
            )
            
            text_blocks = []
            n_boxes = len(data['level'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:
                    continue
                
                # 过滤低置信度结果
                confidence = float(data['conf'][i]) / 100.0
                if confidence < 0.1:
                    continue
                
                text_block = TextBlock(
                    text=text,
                    confidence=confidence,
                    bbox=(
                        data['left'][i],
                        data['top'][i],
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    ),
                    language=self._detect_language(text)
                )
                text_blocks.append(text_block)
            
            return text_blocks
            
        except Exception as e:
            import traceback
            print(f"Tesseract识别失败: {e}")
            
            # 检查是否为语言包缺失错误，如果是则标记Tesseract不可用
            error_str = str(e)
            if 'Could not initialize tesseract' in error_str or 'Error opening data file' in error_str:
                print("[WARN] Tesseract语言包缺失，将Tesseract标记为不可用")
                self.tesseract_available = False
                # 清除路径配置，避免后续尝试
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = None
                except:
                    pass
            
            traceback.print_exc()
            
            # 提供有用的调试信息
            try:
                import pytesseract
                print(f"Tesseract路径配置: {pytesseract.pytesseract.tesseract_cmd}")
            except:
                print("无法获取Tesseract路径配置")
            
            return []
    
    def _recognize_easyocr(self, image: np.ndarray) -> List[TextBlock]:
        """使用EasyOCR识别"""
        if not self.easyocr_available:
            return []
        
        try:
            import easyocr
            
            # 延迟初始化reader
            if self.easyocr_reader is None:
                print("正在初始化EasyOCR Reader...")
                self.easyocr_reader = easyocr.Reader(
                    ['ch_sim', 'en'],
                    gpu=False  # 自用工具，默认不使用GPU
                )
            
            # 执行识别
            results = self.easyocr_reader.readtext(
                image,
                paragraph=False,
                detail=1
            )
            
            text_blocks = []
            for result in results:
                bbox, text, confidence = result
                
                # 转换bbox格式
                x1 = int(min([p[0] for p in bbox]))
                y1 = int(min([p[1] for p in bbox]))
                x2 = int(max([p[0] for p in bbox]))
                y2 = int(max([p[1] for p in bbox]))
                
                text_block = TextBlock(
                    text=text.strip(),
                    confidence=float(confidence),
                    bbox=(x1, y1, x2, y2),
                    language=self._detect_language(text)
                )
                text_blocks.append(text_block)
            
            print(f"[OCR调试] EasyOCR识别到 {len(text_blocks)} 个文本块")
            return text_blocks
            
        except Exception as e:
            print(f"EasyOCR识别失败: {e}")
            
            # 检查是否为DLL错误，如果是则禁用EasyOCR
            error_str = str(e)
            if '1114' in error_str or 'DLL' in error_str or '动态链接库' in error_str:
                print("[WARN] EasyOCR遇到DLL错误，将EasyOCR标记为不可用")
                self.easyocr_available = False
                self.easyocr_reader = None
            
            # 降级逻辑：如果Tesseract可用，自动切换
            if self.tesseract_available:
                print("[OCR降级] EasyOCR失败，自动切换到Tesseract...")
                return self._recognize_tesseract(image)
            
            return []
    
    def _merge_results(self, tesseract_results: List[TextBlock], 
                      easyocr_results: List[TextBlock]) -> List[TextBlock]:
        """合并Tesseract和EasyOCR的结果"""
        merged = []
        
        # 按bbox位置分组
        all_results = tesseract_results + easyocr_results
        
        # 简单去重：如果两个结果的bbox重叠且文本相似，取置信度高的
        for i, result1 in enumerate(all_results):
            keep = True
            
            for j, result2 in enumerate(all_results):
                if i == j:
                    continue
                
                # 检查bbox重叠
                if self._bbox_overlap(result1.bbox, result2.bbox, threshold=0.5):
                    # 文本相似度
                    if self._text_similar(result1.text, result2.text, threshold=0.8):
                        # 取置信度高的
                        if result2.confidence > result1.confidence:
                            keep = False
                            break
            
            if keep:
                merged.append(result1)
        
        return merged
    
    def _bbox_overlap(self, bbox1: Tuple, bbox2: Tuple, threshold: float = 0.5) -> bool:
        """检查两个bbox是否重叠"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # 计算交集面积
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return False
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        # 计算重叠比例
        overlap_ratio = intersection_area / min(area1, area2)
        return overlap_ratio > threshold
    
    def _text_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """检查文本相似度"""
        # 简单实现：编辑距离
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity > threshold
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言（简单实现）"""
        # 检查是否包含中文字符
        import re
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'zh'
        else:
            return 'en'
    
    def _postprocess(self, text_blocks: List[TextBlock]) -> List[TextBlock]:
        """后处理：过滤、合并等"""
        if not text_blocks:
            return []
        
        # 按y坐标排序（从上到下）
        text_blocks.sort(key=lambda tb: tb.bbox[1])
        
        # 过滤过短的文本
        filtered = [tb for tb in text_blocks if len(tb.text.strip()) > 1]
        
        return filtered
    
    def _update_stats(self, elapsed_time: float):
        """更新性能统计"""
        alpha = 0.1
        new_avg = alpha * elapsed_time * 1000 + (1 - alpha) * self.stats['avg_processing_time']
        self.stats['avg_processing_time'] = float(new_avg)
    
    def _save_failed_images(self, original_image, processed_image, strategy):
        """保存失败的图像用于调试"""
        try:
            import cv2
            import os
            
            self.debug_fail_count += 1
            if self.debug_fail_count % 5 == 1:  # 每5次失败保存一次，避免太多文件
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                base_name = f"ocr_fail_{timestamp}_{self.debug_fail_count}"
                
                # 保存原始图像
                if original_image is not None:
                    original_path = f"{base_name}_original.png"
                    cv2.imwrite(original_path, original_image)
                    print(f"[OCR调试] 保存失败原始图像: {original_path}")
                
                # 保存预处理图像
                if processed_image is not None and original_image is not processed_image:
                    processed_path = f"{base_name}_processed.png"
                    cv2.imwrite(processed_path, processed_image)
                    print(f"[OCR调试] 保存失败预处理图像: {processed_path}")
                
                print(f"[OCR调试] 识别策略: {strategy}, 图像形状: {original_image.shape if original_image is not None else 'N/A'}")
        except Exception as e:
            print(f"[OCR调试] 保存失败图像时出错: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.stats.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        
        if 'primary' in new_config:
            self.primary = new_config['primary']
        
        if 'auto_language' in new_config:
            self.auto_language = new_config['auto_language']
        
        if 'preprocess' in new_config:
            self.preprocess = new_config['preprocess']
        
        if 'languages' in new_config:
            self.languages = new_config['languages']
        
        print(f"OCR配置已更新: {new_config}")

# 测试函数
def test_ocr():
    """测试OCR功能"""
    config = {
        'primary': 'hybrid',
        'auto_language': True,
        'preprocess': True,
        'languages': ['en', 'zh']
    }
    
    ocr = HybridOCREngine(config)
    
    # 创建一个测试图像（白色背景上的黑色文字）
    test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
    cv2.putText(test_image, "Hello World", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(test_image, "你好世界", (50, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    print("测试OCR识别...")
    results = ocr.recognize(test_image)
    
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.text} (置信度: {result.confidence:.2f}, 语言: {result.language})")
    
    print(f"统计信息: {ocr.get_stats()}")

if __name__ == "__main__":
    test_ocr()