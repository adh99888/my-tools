#!/usr/bin/env python3
"""
配置向导
首次运行时引导用户完成基本配置
"""

import sys
import os
import yaml
from pathlib import Path

def check_config():
    """检查配置文件，返回缺失的配置项"""
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        return {"config_file": False, "missing_apis": ["kimi", "deepseek", "qwen", "siliconflow"]}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    missing = []
    apis_config = config.get('apis', {})
    
    # 检查至少一个API密钥
    has_valid_api = False
    for api_name in ['kimi', 'deepseek', 'qwen', 'siliconflow', 'glm']:
        if api_name in apis_config:
            api_key = apis_config[api_name].get('api_key', '')
            if api_key and api_key.strip() and not api_key.startswith('sk-'):
                missing.append(f"{api_name}_invalid")
            elif api_key and api_key.strip():
                has_valid_api = True
    
    if not has_valid_api:
        missing.append("no_valid_api")
    
    return {"config_file": True, "missing": missing, "has_valid_api": has_valid_api}

def run_wizard():
    """运行配置向导"""
    print("=" * 60)
    print("屏幕翻译助手 - 配置向导")
    print("=" * 60)
    print()
    
    config_status = check_config()
    
    if not config_status["config_file"]:
        print("首次运行，需要创建配置文件...")
        create_default_config()
        config_status = check_config()
    
    if not config_status.get("has_valid_api", False):
        print("检测到没有有效的API密钥，需要配置至少一个翻译API。")
        print()
        
        print("支持的翻译API:")
        print("1. Kimi (月之暗面) - 适合长文本，上下文128K")
        print("2. DeepSeek - 免费额度，适合代码和技术内容")
        print("3. 通义千问 (阿里云) - 稳定，支持多种模型")
        print("4. 硅基流动 - 支持DeepSeek等开源模型")
        print("5. 智谱GLM - 国内快速响应")
        print()
        
        print("请选择要配置的API (输入数字，多个用逗号分隔，如 1,3):")
        choices_input = input("> ").strip()
        
        choices = []
        for choice in choices_input.split(','):
            choice = choice.strip()
            if choice.isdigit():
                choices.append(int(choice))
        
        apis_to_configure = []
        for choice in choices:
            if choice == 1:
                apis_to_configure.append("kimi")
            elif choice == 2:
                apis_to_configure.append("deepseek")
            elif choice == 3:
                apis_to_configure.append("qwen")
            elif choice == 4:
                apis_to_configure.append("siliconflow")
            elif choice == 5:
                apis_to_configure.append("glm")
        
        if not apis_to_configure:
            print("未选择任何API，将使用默认配置（功能受限）")
            return
        
        print()
        print("请按照提示输入API密钥:")
        print("（密钥通常以'sk-'开头，可以在对应平台申请）")
        print()
        
        # 加载现有配置
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'apis' not in config:
            config['apis'] = {}
        
        for api_name in apis_to_configure:
            print()
            print(f"配置 {api_name.upper()} API:")
            print(f"  获取地址: {get_api_url(api_name)}")
            api_key = input(f"  请输入API密钥: ").strip()
            
            if api_name not in config['apis']:
                config['apis'][api_name] = {}
            
            config['apis'][api_name]['api_key'] = api_key
            
            # 设置默认模型
            if api_name == 'kimi':
                config['apis'][api_name]['model'] = 'kimi-k2-turbo-preview'
                config['apis'][api_name]['base_url'] = 'https://api.moonshot.cn/v1'
            elif api_name == 'deepseek':
                config['apis'][api_name]['model'] = 'deepseek-chat'
                config['apis'][api_name]['base_url'] = 'https://api.deepseek.com/v1'
            elif api_name == 'qwen':
                config['apis'][api_name]['model'] = 'qwen-max'
                config['apis'][api_name]['base_url'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
            elif api_name == 'siliconflow':
                config['apis'][api_name]['model'] = 'deepseek-ai/DeepSeek-V3.1'
                config['apis'][api_name]['base_url'] = 'https://api.siliconflow.cn/v1'
            elif api_name == 'glm':
                config['apis'][api_name]['model'] = 'glm-4-flash'
                config['apis'][api_name]['base_url'] = 'https://open.bigmodel.cn/api/paas/v4'
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print()
        print("配置已保存！")
        
        # 测试API连接
        print("是否测试API连接? (y/n): ")
        test_choice = input("> ").lower().strip()
        
        if test_choice == 'y':
            test_apis(apis_to_configure)
    
    else:
        print("配置文件检查完成，所有必需配置已存在。")
        print("如果需要修改配置，请直接编辑 config.yaml 文件。")
    
    print()
    print("配置向导完成。启动程序命令: python main.py")

def get_api_url(api_name):
    """获取API申请地址"""
    urls = {
        'kimi': 'https://platform.moonshot.cn/console/api-keys',
        'deepseek': 'https://platform.deepseek.com/api_keys',
        'qwen': 'https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key',
        'siliconflow': 'https://cloud.siliconflow.cn/apikeys',
        'glm': 'https://open.bigmodel.cn/usercenter/apikeys'
    }
    return urls.get(api_name, "请访问对应官网")

def create_default_config():
    """创建默认配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    
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
            'region_learning': True,
            'change_detection': True,
            'default_region': [200, 200, 600, 400]
        },
        'ocr': {
            'primary': 'hybrid',
            'auto_language': True,
            'preprocess': True,
            'languages': ['en', 'zh']
        },
        'translation': {
            'primary': 'kimi',
            'fallback': 'deepseek',
            'auto_switch': True,
            'cache_enabled': True,
            'cache_size': 100,
            'target_language': 'zh'
        },
        'display': {
            'width': 'adaptive',
            'max_width': 800,
            'min_width': 400,
            'font_size': 12,
            'theme': 'dark',
            'remember_position': True,
            'auto_hide': False
        },
        'shortcuts': {
            'capture': 'Ctrl+Shift+T',
            'toggle_sidebar': 'Alt+T',
            'pause': 'Ctrl+P',
            'clear': 'Ctrl+L',
            'settings': 'Ctrl+,'
        },
        'apis': {
            'kimi': {'api_key': '', 'model': 'kimi-k2-turbo-preview', 'base_url': 'https://api.moonshot.cn/v1'},
            'deepseek': {'api_key': '', 'model': 'deepseek-chat', 'base_url': 'https://api.deepseek.com/v1'},
            'qwen': {'api_key': '', 'model': 'qwen-max', 'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'},
            'siliconflow': {'api_key': '', 'model': 'deepseek-ai/DeepSeek-V3.1', 'base_url': 'https://api.siliconflow.cn/v1'},
            'glm': {'api_key': '', 'model': 'glm-4-flash', 'base_url': 'https://open.bigmodel.cn/api/paas/v4'}
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/app.log',
            'max_size_mb': 10
        }
    }
    
    # 创建目录
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"已创建默认配置文件: {config_path}")

def test_apis(apis_to_test):
    """测试API连接"""
    print()
    print("测试API连接...")
    
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    for api_name in apis_to_test:
        print(f"\n测试 {api_name} API...")
        try:
            if api_name == 'kimi':
                from engines.translation.apis.kimi_translator import KimiTranslator
                translator_class = KimiTranslator
            elif api_name == 'deepseek':
                from engines.translation.apis.deepseek_translator import DeepSeekTranslator
                translator_class = DeepSeekTranslator
            elif api_name == 'qwen':
                from engines.translation.apis.qwen_translator import QwenTranslator
                translator_class = QwenTranslator
            elif api_name == 'siliconflow':
                from engines.translation.apis.siliconflow_translator import SiliconFlowTranslator
                translator_class = SiliconFlowTranslator
            elif api_name == 'glm':
                from engines.translation.apis.glm_translator import GLMTranslator
                translator_class = GLMTranslator
            else:
                print(f"  未知API: {api_name}")
                continue
            
            # 加载配置
            config_path = Path(__file__).parent / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            api_config = config['apis'][api_name]
            
            translator = translator_class(api_config)
            
            if translator.initialize():
                print(f"  [OK] {api_name} 连接成功")
            else:
                print(f"  [FAIL] {api_name} 连接失败")
                
        except ImportError as e:
            print(f"  [FAIL] 模块导入失败: {e}")
        except Exception as e:
            print(f"  [FAIL] 测试失败: {e}")
    
    print()
    print("API测试完成。")

def main():
    """主函数"""
    try:
        run_wizard()
        return 0
    except KeyboardInterrupt:
        print("\n\n配置向导已取消。")
        return 1
    except Exception as e:
        print(f"\n配置向导出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())