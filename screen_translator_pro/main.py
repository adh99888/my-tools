#!/usr/bin/env python3
"""
屏幕翻译助手增强版 - 主程序入口
针对Windows自用工具优化，简化配置，提升用户体验
"""

import sys
import os
import json
import yaml
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        # 创建默认配置
        create_default_config(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("配置加载成功")
        return config
    except Exception as e:
        print(f"配置加载失败: {e}")
        return {}

def create_default_config(config_path):
    """创建默认配置文件"""
    default_config = {
        'app': {
            'name': '屏幕翻译助手增强版',
            'theme': 'dark',
            'language': 'zh',
            'debug': False
        },
        'capture': {
            'mode': 'smart',
            'hotkey': 'Ctrl+Shift+T',
            'region_learning': True
        },
        'display': {
            'width': 'adaptive',
            'max_width': 800,
            'theme': 'dark'
        }
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        print(f"已创建默认配置文件: {config_path}")
    except Exception as e:
        print(f"创建默认配置文件失败: {e}")

def initialize_modules(config):
    """初始化各个模块"""
    modules = {}
    
    try:
        # 导入引擎模块
        from engines.capture.smart_capture import SmartCapture
        from engines.ocr.hybrid_ocr import HybridOCREngine
        from engines.translation.model_router import ModelRouter
        from ui.main_window import MainWindow
        
        print("开始初始化模块...")
        
        # 初始化捕获模块
        capture_config = config.get('capture', {})
        modules['capture'] = SmartCapture(capture_config)
        print("[OK] 捕获模块初始化完成")
        
        # 初始化OCR模块
        ocr_config = config.get('ocr', {})
        ocr_primary = ocr_config.get('primary', 'hybrid')
        
        if ocr_primary == 'vision':
            vision_config = ocr_config.get('vision', {})
            if vision_config.get('enabled', False):
                provider = vision_config.get('provider', 'qwen')
                
                if provider == 'qwen':
                    from engines.ocr.qwen_vision_ocr import QwenVisionOCR
                    # 合并API配置
                    qwen_api_config = config.get('apis', {}).get('qwen', {})
                    ocr_engine_config = {
                        'model': vision_config.get('model', 'qwen-vl-max'),
                        'api_key': qwen_api_config.get('api_key', ''),
                        'enable_translation': vision_config.get('enable_translation', True),
                        'target_language': config.get('translation', {}).get('target_language', 'zh'),
                        'max_image_size': vision_config.get('max_image_size', 2048)
                    }
                    modules['ocr'] = QwenVisionOCR(ocr_engine_config)
                    print(f"[OK] 视觉OCR模块初始化完成 (提供者: {provider})")
                elif provider == 'deepseek':
                    from engines.ocr.deepseek_vision_ocr import DeepSeekVisionOCR
                    # 合并API配置
                    deepseek_api_config = config.get('apis', {}).get('siliconflow', {})
                    ocr_engine_config = {
                        'model': vision_config.get('model', 'deepseek-ai/DeepSeek-OCR'),
                        'api_key': deepseek_api_config.get('api_key', ''),
                        'base_url': deepseek_api_config.get('base_url', ''),
                        'enable_translation': vision_config.get('enable_translation', True),
                        'target_language': config.get('translation', {}).get('target_language', 'zh'),
                        'max_image_size': vision_config.get('max_image_size', 2048)
                    }
                    modules['ocr'] = DeepSeekVisionOCR(ocr_engine_config)
                    print(f"[OK] 视觉OCR模块初始化完成 (提供者: {provider})")
                else:
                    print(f"[WARN] 不支持的视觉OCR提供者: {provider}，回退到混合OCR")
                    from engines.ocr.hybrid_ocr import HybridOCREngine
                    modules['ocr'] = HybridOCREngine(ocr_config)
            else:
                print("[WARN] 视觉OCR未启用，回退到混合OCR")
                from engines.ocr.hybrid_ocr import HybridOCREngine
                modules['ocr'] = HybridOCREngine(ocr_config)
        else:
            # 使用传统OCR（Tesseract/EasyOCR混合）
            from engines.ocr.hybrid_ocr import HybridOCREngine
            modules['ocr'] = HybridOCREngine(ocr_config)
            print(f"[OK] 传统OCR模块初始化完成 (模式: {ocr_primary})")
        
        # 初始化翻译模块
        translation_config = config.get('translation', {})
        api_config = config.get('apis', {})
        modules['translation'] = ModelRouter(translation_config, api_config)
        print("[OK] 翻译模块初始化完成")
        
        return modules
        
    except ImportError as e:
        print(f"模块导入失败: {e}")
        print("请确保所有依赖已安装，运行: pip install -r requirements.txt")
        return None
    except Exception as e:
        print(f"模块初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("屏幕翻译助手增强版 - 启动")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if not config:
        print("配置加载失败，退出")
        return 1
    
    # 初始化模块
    modules = initialize_modules(config)
    if not modules:
        print("模块初始化失败，退出")
        return 1
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("屏幕翻译助手增强版")
    
    # 创建主窗口
    try:
        from ui.main_window import MainWindow
        window = MainWindow(config, modules)
        window.show()
        
        print("应用程序启动成功")
        print(f"使用说明:")
        print(f"  1. 快捷键 {config.get('shortcuts', {}).get('capture', 'Ctrl+Shift+T')} 截屏翻译")
        print(f"  2. 快捷键 {config.get('shortcuts', {}).get('toggle_sidebar', 'Alt+T')} 显示/隐藏侧边栏")
        print(f"  3. 快捷键 {config.get('shortcuts', {}).get('settings', 'Ctrl+,')} 打开设置")
        
        return app.exec_()
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())