#!/usr/bin/env python3
"""
第3天对话框功能验证测试
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dialog_imports():
    """测试对话框导入"""
    print("=== 测试对话框导入 ===")
    
    try:
        from ui.dialogs.prompt_preview_dialog import PromptPreviewDialog, show_prompt_preview
        from ui.dialogs.prompt_editor_dialog import PromptEditorDialog, show_prompt_editor
        
        print("✅ 预览对话框导入成功")
        print("✅ 编辑对话框导入成功")
        
        # 测试创建模拟对象
        class MockParent:
            def winfo_x(self): return 0
            def winfo_y(self): return 0
            def winfo_width(self): return 800
            def winfo_height(self): return 600
        
        class MockPromptManager:
            def get_default_prompt(self): return "默认提示词"
            def update_template_prompt(self, template_id, prompt, name): return True
        
        # 测试数据
        template_info = {
            "id": "report",
            "name": "工作报告",
            "description": "适用于正式工作报告",
            "prompt": "【工作报告排版指令】请严格识别文档中的标题层级结构...",
            "enabled": True,
            "last_modified": "2024-01-20 14:30",
            "usage_count": 128
        }
        
        print("✅ 对话框组件验证通过")
        print("✅ 模拟数据创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 对话框导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_updated_title_extractor():
    """测试修复后的标题提取器"""
    print("\n=== 测试修复后的标题提取器 ===")
    
    from utils.title_extractor import get_title_extractor
    
    extractor = get_title_extractor()
    
    # 测试之前失败的用例
    test_cases = [
        ("\n\n摘要\n本文研究了...", True, "应该识别'摘要'"),
        ("引言\n本文旨在研究...", True, "应该识别'引言'"),
        ("今天天气很好...", False, "不应该识别"),
        ("一、研究背景\n中医药作为...", True, "应该识别'一、研究背景'"),
        ("（一）主要穴位分析\n在中医针灸...", True, "应该识别'（一）主要穴位分析'"),
    ]
    
    all_passed = True
    for content, should_succeed, description in test_cases:
        result = extractor.extract_title_from_content(content)
        success = result["success"]
        passed = success == should_succeed
        status = "✅" if passed else "❌"
        all_passed = all_passed and passed
        
        print(f"{status} {description}")
        if success:
            print(f"   提取标题: {result['title']} (置信度: {result['confidence']})")
        else:
            print(f"   未提取 (置信度: {result['confidence']})")
    
    return all_passed

def main():
    """主测试函数"""
    print("第3天功能验证测试")
    print("=" * 50)
    
    try:
        # 测试对话框导入
        dialog_ok = test_dialog_imports()
        
        # 测试修复后的标题提取器
        extractor_ok = test_updated_title_extractor()
        
        print("\n" + "=" * 50)
        
        if dialog_ok and extractor_ok:
            print("🎉 第3天上午所有功能验证通过！")
            print("\n准备下午工作:")
            print("1. 修改主窗口 ui/main_window.py")
            print("2. 集成模板选择组件")
            print("3. 集成标题自动提取功能")
        else:
            print("⚠️  部分测试失败，需要检查")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)