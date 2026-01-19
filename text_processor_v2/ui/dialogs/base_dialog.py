"""
对话框基类
提供对话框的通用功能和结构
"""

import tkinter as tk
from tkinter import ttk


class BaseDialog:
    """对话框基类，提供通用功能"""
    
    def __init__(self, parent, title, width=800, height=600):
        """
        初始化对话框基类
        
        Args:
            parent: 父窗口
            title: 对话框标题
            width: 对话框宽度
            height: 对话框高度
        """
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 设置窗口图标
        try:
            self.dialog.iconbitmap('icon.ico')
        except:
            pass
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.dialog, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建控件
        self.create_widgets()
        
        # 窗口居中
        self.center_window()
    
    def center_window(self):
        """窗口居中 - 通用方法"""
        self.dialog.update()
        window_width = self.dialog.winfo_width()
        window_height = self.dialog.winfo_height()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """创建控件 - 子类实现"""
        raise NotImplementedError("子类必须实现 create_widgets 方法")
    
    def run(self):
        """运行对话框"""
        self.parent.wait_window(self.dialog)
        return self.result if hasattr(self, 'result') else None