#!/usr/bin/env python3
"""
应用集成测试

测试整个小盘古应用架构，包括：
1. 应用初始化
2. 配置加载
3. 插件系统集成
4. 插件功能测试
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from smallpangu.app import create_app

def test_app_initialization():
    """测试应用初始化"""
    print("=== 应用初始化测试 ===")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp(prefix="smallpangu_test_")
    print(f"测试临时目录: {temp_dir}")
    
    try:
        # 复制配置文件到临时目录
        config_source = Path(__file__).parent / "configs" / "base.yaml"
        config_dest = Path(temp_dir) / "config.yaml"
        shutil.copy(config_source, config_dest)
        
        # 创建应用实例
        app = create_app(config_path=str(config_dest))
        
        # 测试应用属性
        assert not app.is_initialized, "应用初始状态应为未初始化"
        assert not app.is_running, "应用初始状态应为未运行"
        
        print("[OK] 应用实例创建成功")
        
        # 初始化应用
        app.initialize()
        
        assert app.is_initialized, "应用初始化后应标记为已初始化"
        assert app.config_manager is not None, "配置管理器应已初始化"
        assert app.event_bus is not None, "事件总线应已初始化"
        assert app.container is not None, "容器应已初始化"
        
        print("[OK] 应用初始化成功")
        print(f"    环境: {app.config_manager.environment}")
        print(f"    应用名称: {app.config_manager.config.app.name}")
        print(f"    应用版本: {app.config_manager.config.app.version}")
        
        # 获取应用状态
        status = app.get_status()
        print(f"[OK] 应用状态获取成功: {status['initialized']}")
        
        # 测试插件加载
        if app.plugin_registry:
            print("[OK] 插件注册表已初始化")
        else:
            print("[WARN] 插件注册表未初始化（可能插件系统未启用）")
        
        # 清理
        app.shutdown()
        
        print("[OK] 应用关闭成功")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 应用初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"临时目录已清理")

def test_plugin_loading():
    """测试插件加载"""
    print("\n=== 插件加载测试 ===")
    
    temp_dir = tempfile.mkdtemp(prefix="smallpangu_test_")
    
    try:
        # 复制配置文件
        config_source = Path(__file__).parent / "configs" / "base.yaml"
        config_dest = Path(temp_dir) / "config.yaml"
        shutil.copy(config_source, config_dest)
        
        # 创建应用并初始化
        app = create_app(config_path=str(config_dest))
        app.initialize()
        
        # 加载插件
        app.load_plugins()
        
        # 检查插件注册表
        if app.plugin_registry:
            all_plugins = app.plugin_registry.get_all_plugins()
            print(f"已注册插件数量: {len(all_plugins)}")
            
            # 查找token_counter插件
            token_counter_info = app.plugin_registry.get_plugin_info("tools.token_counter")
            if token_counter_info:
                print("[OK] Token计数器插件已注册")
                print(f"    状态: {token_counter_info.status.value}")
                print(f"    元数据: {token_counter_info.metadata.display_name}")
            else:
                print("[FAIL] Token计数器插件未找到")
                print(f"    已注册插件: {[p.name for p in all_plugins]}")
                return False
        else:
            print("[WARN] 插件注册表不可用，跳过插件加载测试")
            return True
        
        # 启动应用（启动插件）
        app.start()
        
        # 检查插件状态
        if app.plugin_registry:
            token_counter_info = app.plugin_registry.get_plugin_info("tools.token_counter")
            if token_counter_info.is_running:
                print("[OK] Token计数器插件正在运行")
            else:
                print("[WARN] Token计数器插件未运行")
        
        # 测试插件功能
        if app.plugin_registry:
            # 获取插件实例
            plugin_instance = token_counter_info.instance
            if plugin_instance:
                # 测试Token估算
                tokens = plugin_instance.estimate_tokens("测试文本", "gpt-3.5-turbo")
                print(f"[OK] Token估算测试: '测试文本' -> {tokens} tokens")
                
                # 测试工具执行
                result = plugin_instance.execute({
                    "action": "estimate",
                    "text": "Hello, world!",
                    "model": "gpt-3.5-turbo"
                })
                if result.get("success"):
                    print(f"[OK] 工具执行测试: {result['tokens']} tokens")
                else:
                    print(f"[FAIL] 工具执行失败: {result}")
                    return False
            else:
                print("[WARN] 插件实例不可用")
        
        # 停止应用
        app.stop()
        
        print("[OK] 应用停止成功")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 插件加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_app_lifecycle():
    """测试应用完整生命周期"""
    print("\n=== 应用完整生命周期测试 ===")
    
    try:
        # 使用上下文管理器测试生命周期
        with create_app() as app:
            print("[OK] 应用上下文管理器进入成功")
            
            # 验证应用状态
            assert app.is_initialized, "应用应已初始化"
            assert app.is_running, "应用应正在运行"
            
            print(f"[OK] 应用运行中，运行时间: {app.uptime:.2f} 秒")
            
            # 获取应用状态
            status = app.get_status()
            print(f"[OK] 应用状态: 初始化={status['initialized']}, 运行={status['running']}")
            
            # 测试插件功能（如果可用）
            if app.plugin_registry:
                plugins = app.plugin_registry.get_all_plugins()
                print(f"[OK] 已加载插件: {len(plugins)} 个")
        
        print("[OK] 应用上下文管理器退出成功（自动关闭）")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 应用生命周期测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("小盘古4.0应用集成测试")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # 测试1: 应用初始化
    if test_app_initialization():
        success_count += 1
    
    # 测试2: 插件加载
    if test_plugin_loading():
        success_count += 1
    
    # 测试3: 应用生命周期
    if test_app_lifecycle():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("[SUCCESS] 所有集成测试通过！应用架构工作正常。")
        return 0
    else:
        print("[FAIL] 部分集成测试失败，需要检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())