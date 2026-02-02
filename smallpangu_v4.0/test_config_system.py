#!/usr/bin/env python3
"""
配置系统验证脚本
测试配置加载、验证和管理的核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from smallpangu.config import (
    SmallPanguConfig,
    load_config,
    get_config_manager,
    LogLevel,
    Theme
)


def test_basic_config():
    """测试基础配置加载"""
    print("=" * 60)
    print("测试1: 基础配置加载")
    print("=" * 60)
    
    try:
        # 加载默认配置
        config = load_config()
        
        print(f"✓ 配置加载成功")
        print(f"  环境: {config.environment}")
        print(f"  应用名称: {config.app.name}")
        print(f"  版本: {config.app.version}")
        print(f"  日志级别: {config.app.log_level}")
        print(f"  UI主题: {config.ui.theme}")
        print(f"  AI默认提供商: {config.ai.default_provider}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False


def test_config_manager():
    """测试配置管理器"""
    print("\n" + "=" * 60)
    print("测试2: 配置管理器")
    print("=" * 60)
    
    try:
        # 获取配置管理器
        manager = get_config_manager()
        
        print(f"✓ 配置管理器获取成功")
        print(f"  当前环境: {manager.environment}")
        
        # 获取配置值
        app_name = manager.get_value("app.name", "未知")
        log_level = manager.get_value("app.log_level", LogLevel.INFO)
        
        print(f"  应用名称: {app_name}")
        print(f"  日志级别: {log_level}")
        
        # 获取配置摘要
        summary = manager.get_config_summary()
        print(f"  配置摘要:")
        print(f"    插件启用数: {summary['plugins']['enabled_count']}")
        print(f"    AI最大token: {summary['ai']['max_tokens']}")
        
        # 验证配置
        errors = manager.validate_current_config()
        if errors:
            print(f"  ⚠ 配置验证警告:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✓ 配置验证通过")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_override():
    """测试环境变量覆盖"""
    print("\n" + "=" * 60)
    print("测试3: 环境变量覆盖")
    print("=" * 60)
    
    try:
        # 设置环境变量
        os.environ["SMALLPANGU_ENVIRONMENT"] = "development"
        os.environ["SMALLPANGU_APP__LOG_LEVEL"] = "DEBUG"
        os.environ["SMALLPANGU_UI__THEME"] = "light"
        
        # 重新加载配置
        from smallpangu.config import reload_config
        config = reload_config()
        
        print(f"✓ 环境变量覆盖测试")
        print(f"  环境: {config.environment} (应为: development)")
        print(f"  日志级别: {config.app.log_level} (应为: DEBUG)")
        print(f"  UI主题: {config.ui.theme} (应为: light)")
        
        # 验证
        success = True
        if config.environment != "development":
            print(f"  ✗ 环境变量覆盖失败: environment")
            success = False
        if config.app.log_level != LogLevel.DEBUG:
            print(f"  ✗ 环境变量覆盖失败: app.log_level")
            success = False
        if config.ui.theme != Theme.LIGHT:
            print(f"  ✗ 环境变量覆盖失败: ui.theme")
            success = False
            
        if success:
            print(f"  ✓ 所有环境变量覆盖成功")
        
        # 清理环境变量
        os.environ.pop("SMALLPANGU_ENVIRONMENT", None)
        os.environ.pop("SMALLPANGU_APP__LOG_LEVEL", None)
        os.environ.pop("SMALLPANGU_UI__THEME", None)
        
        return success
        
    except Exception as e:
        print(f"✗ 环境变量覆盖测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_models():
    """测试配置模型"""
    print("\n" + "=" * 60)
    print("测试4: 配置模型验证")
    print("=" * 60)
    
    try:
        # 创建最小配置
        config_dict = {
            "environment": "testing",
            "app": {
                "name": "测试应用",
                "version": "1.0.0",
                "log_level": "INFO"
            }
        }
        
        config = SmallPanguConfig(**config_dict)
        
        print(f"✓ 最小配置创建成功")
        print(f"  应用名称: {config.app.name}")
        print(f"  版本: {config.app.version}")
        
        # 测试默认值
        print(f"  默认AI提供商: {config.ai.default_provider}")
        print(f"  默认温度: {config.ai.temperature}")
        
        # 测试无效值验证
        print(f"\n  测试无效值验证...")
        try:
            invalid_config = SmallPanguConfig(
                environment="invalid_env",
                app={"log_level": "INVALID_LEVEL"}
            )
            print(f"  ✗ 无效值验证失败: 应抛出异常")
            return False
        except Exception as e:
            print(f"  ✓ 无效值验证成功: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置模型测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("小盘古4.0 - 配置系统验证")
    print("=" * 60)
    
    tests = [
        test_basic_config,
        test_config_manager,
        test_environment_override,
        test_config_models
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    print(f"失败: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())