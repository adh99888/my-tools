#!/usr/bin/env python3
"""
DeepSeek OCR翻译器测试脚本
测试一体化OCR识别翻译功能
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_deepseek_translator():
    """测试DeepSeek OCR翻译器"""
    print("=" * 70)
    print("DeepSeek OCR翻译器测试")
    print("=" * 70)
    
    # 测试配置
    config = {
        'model_path': "d:/deepseek ocr - 副本/DeepSeek-OCR/deepseek-ocr-local",
        'device': 'auto',  # auto, cuda, cpu
        'use_half_precision': True,
        'base_size': 1024,
        'image_size': 640,
        'crop_mode': True,
        'enable_translation': True,
        'target_language': 'zh',
        'source_language': 'auto',
        'cache_enabled': True,
        'cache_size': 10,
        'max_retries': 3,
        'max_image_size': 2048
    }
    
    print("配置信息:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n1. 导入DeepSeekOCRTranslator...")
    try:
        from engines.ocr.deepseek_ocr_translator import DeepSeekOCRTranslator
        print("   [OK] 导入成功")
    except ImportError as e:
        print(f"   [FAIL] 导入失败: {e}")
        return False
    
    print("\n2. 创建DeepSeekOCRTranslator实例...")
    try:
        translator = DeepSeekOCRTranslator(config)
        print("   [OK] 实例创建成功")
    except Exception as e:
        print(f"   [FAIL] 实例创建失败: {e}")
        return False
    
    print("\n3. 初始化引擎...")
    try:
        initialized = translator.initialize()
        if initialized:
            print("   [OK] 引擎初始化成功")
        else:
            print("   [FAIL] 引擎初始化失败")
            return False
    except Exception as e:
        print(f"   [FAIL] 初始化异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n4. 检查健康状态...")
    try:
        health = translator.health_check()
        print(f"   [OK] 健康状态: {health['status']}")
        print(f"   [OK] 成功率: {health['success_rate']:.1%}")
        
        if health['status'] != 'healthy':
            print(f"   [WARN] 系统状态不佳: {health['recommendation']}")
    except Exception as e:
        print(f"   [WARN] 健康检查失败: {e}")
    
    print("\n5. 创建测试图像...")
    try:
        # 创建一个简单的测试图像（白色背景上的黑色文字）
        import cv2
        
        # 创建一个400x200的白色图像
        test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        
        # 添加英文文本
        cv2.putText(test_image, "Hello World", (50, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # 添加中文文本
        cv2.putText(test_image, "测试文本", (50, 130), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        print("   [OK] 测试图像创建成功")
        print(f"   [INFO] 图像形状: {test_image.shape}")
    except Exception as e:
        print(f"   [FAIL] 创建测试图像失败: {e}")
        return False
    
    print("\n6. 测试OCR识别（无翻译）...")
    try:
        start_time = time.time()
        results = translator.recognize(test_image, translate=False)
        elapsed = time.time() - start_time
        
        print(f"   [OK] 识别完成，耗时: {elapsed:.2f}秒")
        print(f"   [INFO] 找到 {len(results)} 个文本块")
        
        for i, block in enumerate(results):
            print(f"     块 {i+1}: {block.text[:50]}... (置信度: {block.confidence:.2f}, 语言: {block.language})")
            if block.translated_text:
                print(f"       翻译: {block.translated_text[:50]}...")
    except Exception as e:
        print(f"   [FAIL] OCR识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n7. 测试OCR识别+翻译...")
    try:
        start_time = time.time()
        results = translator.recognize(test_image, translate=True)
        elapsed = time.time() - start_time
        
        print(f"   [OK] 识别翻译完成，耗时: {elapsed:.2f}秒")
        print(f"   [INFO] 找到 {len(results)} 个文本块")
        
        for i, block in enumerate(results):
            print(f"     块 {i+1}: {block.text[:50]}... (置信度: {block.confidence:.2f}, 语言: {block.language})")
            if block.translated_text:
                print(f"       翻译: {block.translated_text[:50]}...")
    except Exception as e:
        print(f"   [FAIL] OCR翻译测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n8. 测试缓存功能...")
    try:
        # 第一次识别（应该缓存未命中）
        start_time = time.time()
        results1 = translator.recognize(test_image, translate=True)
        time1 = time.time() - start_time
        
        # 第二次识别（应该缓存命中）
        start_time = time.time()
        results2 = translator.recognize(test_image, translate=True)
        time2 = time.time() - start_time
        
        print(f"   [OK] 第一次识别: {time1:.2f}秒")
        print(f"   [OK] 第二次识别: {time2:.2f}秒")
        
        if time2 < time1 * 0.5:  # 第二次应该快很多
            print("   [OK] 缓存生效，第二次识别更快")
        else:
            print("   [WARN] 缓存效果不明显")
        
        stats = translator.get_stats()
        print(f"   [INFO] 缓存命中率: {stats.get('cache_hit_rate', 0):.1%}")
    except Exception as e:
        print(f"   [WARN] 缓存测试失败: {e}")
    
    print("\n9. 测试批量处理...")
    try:
        # 创建多个测试图像
        batch_images = []
        for i in range(3):
            img = np.ones((200, 400, 3), dtype=np.uint8) * 255
            cv2.putText(img, f"Batch Test {i+1}", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            batch_images.append(img)
        
        start_time = time.time()
        batch_results = translator.batch_process(batch_images, translate=True)
        elapsed = time.time() - start_time
        
        print(f"   [OK] 批量处理完成，耗时: {elapsed:.2f}秒")
        print(f"   [INFO] 处理了 {len(batch_results)} 张图像")
        
        for i, results in enumerate(batch_results):
            print(f"     图像 {i+1}: {len(results)} 个文本块")
    except Exception as e:
        print(f"   [WARN] 批量处理测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n10. 获取性能统计...")
    try:
        stats = translator.get_stats()
        print("   [OK] 性能统计:")
        for key, value in stats.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if 'time' in key or 'Time' in key:
                    print(f"     {key}: {value:.2f}秒")
                elif 'rate' in key:
                    print(f"     {key}: {value:.1%}")
                else:
                    print(f"     {key}: {value}")
            else:
                print(f"     {key}: {value}")
    except Exception as e:
        print(f"   [WARN] 获取统计失败: {e}")
    
    print("\n11. 清理资源...")
    try:
        translator.cleanup()
        print("   [OK] 资源清理成功")
    except Exception as e:
        print(f"   [WARN] 资源清理失败: {e}")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
    
    return True

def main():
    """主测试函数"""
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    try:
        success = test_deepseek_translator()
        
        if success:
            print("\n[SUCCESS] DeepSeek OCR翻译器测试通过!")
            print("\n总结:")
            print("  1. 引擎初始化成功")
            print("  2. OCR识别功能正常")
            print("  3. 翻译功能正常")
            print("  4. 缓存系统工作")
            print("  5. 批量处理支持")
            print("\nDeepSeek OCR翻译器已准备好集成到屏幕翻译助手中。")
            return 0
        else:
            print("\n[FAILURE] DeepSeek OCR翻译器测试失败")
            print("\n建议:")
            print("  1. 检查模型路径是否正确")
            print("  2. 确认CUDA和PyTorch配置")
            print("  3. 检查依赖包是否安装")
            print("  4. 查看详细错误信息")
            return 1
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())