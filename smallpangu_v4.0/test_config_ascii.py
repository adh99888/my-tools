#!/usr/bin/env python3
"""
简单配置系统测试 - ASCII版本
"""

import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 直接导入config模块
from smallpangu.config.models import SmallPanguConfig, LogLevel, Theme
from smallpangu.config.loader import load_config
from smallpangu.config.manager import ConfigManager


def test_basic_models():
    """测试基础模型"""
    print("测试基础模型...")
    
    # 创建最小配置
    config = SmallPanguConfig(
        environment="testing",
        app={"name": "测试", "version": "1.0.0"}
    )
    
    assert config.environment == "testing"
    assert config.app.name == "测试"
    assert config.app.version == "1.0.0"
    assert config.ai.default_provider == "deepseek"  # 默认值
    
    print("  [OK] 基础模型测试通过")
    return True


def test_config_loading():
    """测试配置加载"""
    print("\n测试配置加载...")
    
    try:
        # 加载配置
        config = load_config()
        
        print(f"  [OK] 配置加载成功")
        print(f"    环境: {config.environment}")
        print(f"    应用: {config.app.name} v{config.app.version}")
        print(f"    日志级别: {config.app.log_level}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")
    
    try:
        # 创建配置管理器
        manager = ConfigManager()
        
        print(f"  [OK] 配置管理器创建成功")
        print(f"    当前环境: {manager.environment}")
        
        # 获取配置值
        value = manager.get_value("app.name", "默认值")
        print(f"    应用名称: {value}")
        
        # 验证配置
        errors = manager.validate_current_config()
        if errors:
            print(f"  [WARN] 配置验证警告:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  [OK] 配置验证通过")
        
        return True
    except Exception as e:
        print(f"  [FAIL] 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_variables():
    """测试环境变量"""
    print("\n测试环境变量...")
    
    try:
        # 设置环境变量
        os.environ["SMALLPANGU_ENVIRONMENT"] = "development"
        os.environ["SMALLPANGU_APP__LOG_LEVEL"] = "DEBUG"
        
        # 重新加载配置
        from smallpangu.config.loader import reload_config
        config = reload_config()
        
        print(f"  [OK] 环境变量测试")
        print(f"    环境: {config.environment} (应为: development)")
        print(f"    日志级别: {config.app.log_level} (应为: DEBUG)")
        
        success = True
        if config.environment != "development":
            print(f"    [FAIL] 环境变量覆盖失败: environment")
            success = False
        if config.app.log_level != LogLevel.DEBUG:
            print(f"    [FAIL] 环境变量覆盖失败: app.log_level")
            success = False
            
        if success:
            print(f"    [OK] 环境变量覆盖成功")
        
        # 清理
        os.environ.pop("SMALLPANGU_ENVIRONMENT", None)
        os.environ.pop("SMALLPANGU_APP__LOG_LEVEL", None)
        
        return success
    except Exception as e:
        print(f"  [FAIL] 环境变量测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("小盘古4.0配置系统测试")
    print("=" * 60)
    
    tests = [
        test_basic_models,
        test_config_loading,
        test_config_manager,
        test_environment_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("所有测试通过!")
        return 0
    else:
        print("部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())