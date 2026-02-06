#!/usr/bin/env python3
"""
调试脚本：检查DeepSeek OCR翻译引擎的问题
"""

import os
import sys
import numpy as np
from PIL import Image, ImageDraw

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.ocr.deepseek_ocr_translator import DeepSeekOCRTranslator

def test_image_saving():
    """测试图像保存功能"""
    print("测试图像保存功能...")
    
    # 创建一个测试图像
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "测试图像", fill='black')
    
    # 创建引擎实例
    config = {
        'model_path': "d:/deepseek ocr - 副本/DeepSeek-OCR/deepseek-ocr-local",
        'device': 'cpu',
        'use_half_precision': False
    }
    
    engine = DeepSeekOCRTranslator(config)
    
    # 测试_save_temp_image方法
    print("调用_save_temp_image方法...")
    try:
        temp_path = engine._save_temp_image(img)
        print(f"临时文件路径: {temp_path}")
        print(f"文件是否存在: {os.path.exists(temp_path)}")
        
        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print(f"文件大小: {file_size}字节")
            
            # 清理临时文件
            engine._cleanup_temp_file(temp_path)
            print(f"清理后文件是否存在: {os.path.exists(temp_path)}")
        else:
            print("错误: 临时文件未创建")
            
    except Exception as e:
        print(f"保存图像时发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_model_infer():
    """测试模型推理功能"""
    print("\n测试模型推理功能...")
    
    config = {
        'model_path': "d:/deepseek ocr - 副本/DeepSeek-OCR/deepseek-ocr-local",
        'device': 'cpu',
        'use_half_precision': False
    }
    
    engine = DeepSeekOCRTranslator(config)
    
    # 初始化引擎
    print("初始化引擎...")
    success = engine.initialize()
    print(f"初始化结果: {success}")
    
    if success:
        # 创建测试图像
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "测试OCR识别", fill='black')
        
        # 转换为OpenCV格式
        import cv2
        cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # 测试识别
        print("测试图像识别...")
        try:
            result = engine.recognize(cv_image, translate=False)
            print(f"识别结果: {len(result)} 个文本块")
            if result:
                print(f"示例文本: {result[0].text[:100]}")
        except Exception as e:
            print(f"识别时发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 清理资源
    engine.cleanup()

def main():
    """主函数"""
    print("=" * 80)
    print("DeepSeek OCR翻译引擎调试脚本")
    print("=" * 80)
    
    # 测试1: 图像保存
    test_image_saving()
    
    # 测试2: 模型推理
    test_model_infer()
    
    print("\n调试完成!")

if __name__ == "__main__":
    main()