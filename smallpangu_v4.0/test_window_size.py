#!/usr/bin/env python3
"""
测试窗口尺寸问题
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_window_creation():
    """测试窗口创建和尺寸"""
    import customtkinter as ctk
    
    print("测试1: 直接创建customtkinter窗口")
    root = ctk.CTk()
    root.title("测试窗口")
    root.geometry("1280x720+100+100")
    root.minsize(800, 600)
    
    print(f"  几何设置后: {root.winfo_geometry()}")
    print(f"  宽度: {root.winfo_width()}, 高度: {root.winfo_height()}")
    
    # 添加一个标签以显示内容
    label = ctk.CTkLabel(root, text="测试窗口 - 应该显示")
    label.pack(padx=20, pady=20)
    
    print(f"  更新前: {root.winfo_geometry()}")
    root.update_idletasks()
    print(f"  更新后: {root.winfo_geometry()}")
    
    # 运行一小段时间
    root.after(2000, root.destroy)
    root.mainloop()
    
    print("\n测试2: 使用配置管理器")
    from smallpangu.config.manager import ConfigManager
    from smallpangu.ui.manager import UIManager
    
    config_manager = ConfigManager()
    print(f"  UI配置读取: 宽度={config_manager.config.ui.window_width}, 高度={config_manager.config.ui.window_height}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_window_creation()