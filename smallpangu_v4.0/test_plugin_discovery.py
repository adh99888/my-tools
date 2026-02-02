#!/usr/bin/env python3
"""
插件发现测试脚本

测试插件加载器是否能正确发现token_counter插件。
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from smallpangu.plugins.loader import create_plugin_loader

def test_plugin_discovery():
    """测试插件发现"""
    print("=== 插件发现测试 ===")
    
    # 创建插件加载器（使用默认搜索路径）
    loader = create_plugin_loader(search_paths=["./plugins"])
    
    # 发现插件
    plugins = loader.discover_plugins()
    
    print(f"发现 {len(plugins)} 个插件:")
    for plugin in plugins:
        print(f"  - {plugin.name} ({plugin.display_name}) v{plugin.version}")
        print(f"    类型: {plugin.plugin_type.value}")
        print(f"    描述: {plugin.description}")
        print(f"    作者: {plugin.author}")
        if plugin.python_dependencies:
            print(f"    依赖: {plugin.python_dependencies}")
        print()
    
    # 检查token_counter插件是否存在
    token_counter_plugin = loader.get_plugin_metadata("tools.token_counter")
    if token_counter_plugin:
        print("[OK] Token计数器插件发现成功!")
        print(f"   显示名称: {token_counter_plugin.display_name}")
        print(f"   版本: {token_counter_plugin.version}")
        print(f"   插件类: {token_counter_plugin.plugin_class}")
    else:
        print("[FAIL] Token计数器插件未发现!")
        print("已发现的插件名称:", [p.name for p in plugins])
        return False
    
    # 尝试加载插件类
    try:
        plugin_class = loader.load_plugin("tools.token_counter")
        print(f"[OK] 插件加载成功: {plugin_class.__name__}")
        
        # 检查是否为ToolPlugin
        from smallpangu.plugins.base import ToolPlugin
        if issubclass(plugin_class, ToolPlugin):
            print("[OK] 插件类型正确（ToolPlugin）")
        else:
            print("[WARN]  插件类型非ToolPlugin")
            
    except Exception as e:
        print(f"[FAIL] 插件加载失败: {e}")
        return False
    
    return True

def test_plugin_instantiation():
    """测试插件实例化（需要模拟上下文）"""
    print("\n=== 插件实例化测试 ===")
    
    # 创建插件加载器
    loader = create_plugin_loader(search_paths=["./plugins"])
    
    # 创建模拟上下文
    from unittest.mock import Mock
    mock_context = Mock()
    mock_context.logger = Mock()
    mock_context.config = {"daily_limit": 50000, "enable_tracking": True, "default_model": "gpt-3.5-turbo"}
    mock_context.plugin_name = "tools.token_counter"
    
    try:
        # 创建插件实例
        plugin_instance = loader.create_plugin_instance("tools.token_counter", mock_context)
        print(f"[OK] 插件实例创建成功: {plugin_instance}")
        
        # 测试插件方法
        tokens = plugin_instance.estimate_tokens("Hello, world!", "gpt-3.5-turbo")
        print(f"[OK] Token估算测试: 'Hello, world!' -> {tokens} tokens")
        
        # 测试工具执行
        result = plugin_instance.execute({"action": "estimate", "text": "测试文本", "model": "gpt-3.5-turbo"})
        print(f"[OK] 工具执行测试: {result}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 插件实例化或执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_schema():
    """测试工具模式"""
    print("\n=== 工具模式测试 ===")
    
    loader = create_plugin_loader(search_paths=["./plugins"])
    plugin_class = loader.load_plugin("tools.token_counter")
    
    # 创建模拟上下文
    from unittest.mock import Mock
    mock_context = Mock()
    mock_context.config = {}
    mock_context.plugin_name = "tools.token_counter"
    
    plugin_instance = plugin_class(mock_context)
    
    # 检查tool_schema属性
    schema = plugin_instance.tool_schema
    if schema:
        print("[OK] 工具模式获取成功:")
        print(f"   名称: {schema['function']['name']}")
        print(f"   描述: {schema['function']['description']}")
        print(f"   参数: {list(schema['function']['parameters']['properties'].keys())}")
    else:
        print("[FAIL] 工具模式为空")
        return False
    
    return True

def main():
    """主测试函数"""
    print("小盘古4.0插件系统集成测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 测试1: 插件发现
    if test_plugin_discovery():
        success_count += 1
    
    # 测试2: 插件实例化
    if test_plugin_instantiation():
        success_count += 1
    
    # 测试3: 工具模式
    if test_tool_schema():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("[SUCCESS] 所有测试通过！插件系统工作正常。")
        return 0
    else:
        print("[FAIL] 部分测试失败，需要检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())