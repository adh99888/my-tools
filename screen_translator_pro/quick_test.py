#!/usr/bin/env python3
"""
快速测试脚本 - 验证DeepSeek OCR翻译器集成
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    print("测试导入...")
    
    try:
        from engines.ocr.deepseek_ocr_translator import DeepSeekOCRTranslator
        print("  [OK] DeepSeekOCRTranslator 导入成功")
        
        from engines.ocr.deepseek_ocr_translator import LRUCache
        print("  [OK] LRUCache 导入成功")
        
        return True
    except ImportError as e:
        print(f"  [FAIL] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """测试配置"""
    print("\n测试配置...")
    
    try:
        import yaml
        
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查OCR配置
        ocr_config = config.get('ocr', {})
        primary = ocr_config.get('primary', '')
        
        if primary == 'deepseek_translator':
            print(f"  [OK] 主OCR引擎配置为: {primary}")
        else:
            print(f"  [WARN] 主OCR引擎不是deepseek_translator: {primary}")
            print("  建议修改config.yaml中的ocr.primary为deepseek_translator")
        
        # 检查DeepSeek翻译器配置
        vision_config = ocr_config.get('vision', {})
        translator_config = vision_config.get('deepseek_translator', {})
        
        if translator_config:
            print("  [OK] DeepSeek翻译器配置存在")
            model_path = translator_config.get('model_path', '')
            if model_path and os.path.exists(model_path):
                print(f"  [OK] 模型路径存在: {model_path}")
            else:
                print(f"  [WARN] 模型路径可能不存在: {model_path}")
        else:
            print("  [WARN] DeepSeek翻译器配置不存在")
        
        return True
    except Exception as e:
        print(f"  [FAIL] 配置测试失败: {e}")
        return False

def test_main_integration():
    """测试主程序集成"""
    print("\n测试主程序集成...")
    
    try:
        # 检查main.py中是否有DeepSeekOCRTranslator的导入
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'deepseek_ocr_translator' in content:
            print("  [OK] main.py中包含deepseek_ocr_translator引用")
        else:
            print("  [WARN] main.py中未找到deepseek_ocr_translator引用")
        
        if 'DeepSeekOCRTranslator' in content:
            print("  [OK] main.py中包含DeepSeekOCRTranslator类名")
        else:
            print("  [WARN] main.py中未找到DeepSeekOCRTranslator类名")
        
        # 检查配置选项
        if 'deepseek_translator' in content:
            print("  [OK] main.py中包含deepseek_translator配置选项")
        else:
            print("  [WARN] main.py中未找到deepseek_translator配置选项")
        
        return True
    except Exception as e:
        print(f"  [FAIL] 主程序集成测试失败: {e}")
        return False

def test_engine_creation():
    """测试引擎创建"""
    print("\n测试引擎创建...")
    
    try:
        from engines.ocr.deepseek_ocr_translator import DeepSeekOCRTranslator
        
        # 使用最小配置
        config = {
            'model_path': "d:/deepseek ocr - 副本/DeepSeek-OCR/deepseek-ocr-local",
            'device': 'cpu',  # 使用CPU避免GPU问题
            'use_half_precision': False,
            'enable_translation': True,
            'target_language': 'zh',
            'cache_enabled': False  # 禁用缓存以简化测试
        }
        
        print("  创建DeepSeekOCRTranslator实例...")
        translator = DeepSeekOCRTranslator(config)
        
        print("  检查实例属性...")
        assert translator.name == "DeepSeek OCR翻译器", f"名称错误: {translator.name}"
        assert translator.model_path == config['model_path'], f"模型路径错误"
        assert translator.device == 'cpu', f"设备错误: {translator.device}"
        
        print("  [OK] 引擎创建测试通过")
        return True
    except Exception as e:
        print(f"  [FAIL] 引擎创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 70)
    print("DeepSeek OCR翻译器快速测试")
    print("=" * 70)
    
    tests = [
        ("导入测试", test_imports),
        ("配置测试", test_config),
        ("主程序集成测试", test_main_integration),
        ("引擎创建测试", test_engine_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  [ERROR] 测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "通过" if success else "失败"
        print(f"  {test_name:20} [{status}]")
    
    print(f"\n总体: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过!")
        print("\nDeepSeek OCR翻译器集成完成，可以开始使用。")
        print("\n使用说明:")
        print("  1. 确保模型路径正确: d:/deepseek ocr - 副本/DeepSeek-OCR/deepseek-ocr-local")
        print("  2. 运行主程序: python main.py")
        print("  3. 使用快捷键 Ctrl+Shift+T 进行截图翻译")
        print("  4. 系统将自动使用DeepSeek OCR进行一体化识别翻译")
        return 0
    elif passed >= total // 2:
        print("\n[WARNING] 部分测试通过，基本功能可用")
        print("\n建议:")
        print("  1. 检查模型路径和配置文件")
        print("  2. 确保所有依赖已安装")
        print("  3. 可以尝试运行完整测试: python test_deepseek_translator.py")
        return 1
    else:
        print("\n[FAILURE] 多数测试失败")
        print("\n需要检查的问题:")
        print("  1. 模型文件是否存在")
        print("  2. 配置文件是否正确")
        print("  3. Python依赖是否完整")
        print("  4. 系统环境是否支持")
        return 1

if __name__ == "__main__":
    sys.exit(main())