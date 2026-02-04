"""
模板编辑器对话框
负责模板的创建和编辑界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from datetime import datetime
from pathlib import Path
from .base_dialog import BaseDialog


class TemplateEditorDialog(BaseDialog):
    """模板编辑器对话框"""
    
    def __init__(self, parent, template_data=None):
        """
        初始化模板编辑器对话框
        
        Args:
            parent: 父窗口
            template_data: 模板数据，如果为None则创建新模板
        """
        self.template_data = template_data if template_data else {}
        self.result = None
        
        super().__init__(parent, "模板编辑器", 1000, 700)
        
        # 加载数据
        if self.template_data:
            self.load_template_data()
    
    def create_widgets(self):
        """创建界面控件"""
        # 标题
        title_label = ttk.Label(self.main_frame, text="📝 模板编辑器", 
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 基本信息
        basic_frame = ttk.LabelFrame(self.main_frame, text="基本信息", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 模板名称
        name_frame = ttk.Frame(basic_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(name_frame, text="模板名称:", width=12).pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 模板描述
        desc_frame = ttk.Frame(basic_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(desc_frame, text="模板描述:", width=12).pack(side=tk.LEFT)
        self.desc_entry = ttk.Entry(desc_frame)
        self.desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 页面设置
        page_frame = ttk.LabelFrame(self.main_frame, text="页面设置", padding="10")
        page_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 使用网格布局
        page_grid = ttk.Frame(page_frame)
        page_grid.pack(fill=tk.X)
        
        ttk.Label(page_grid, text="上边距(pt):").grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.margin_top = ttk.Entry(page_grid, width=10)
        self.margin_top.insert(0, "72")
        self.margin_top.grid(row=0, column=1, padx=(0, 15), pady=5)
        
        ttk.Label(page_grid, text="下边距(pt):").grid(row=0, column=2, padx=(0, 5), pady=5, sticky=tk.W)
        self.margin_bottom = ttk.Entry(page_grid, width=10)
        self.margin_bottom.insert(0, "72")
        self.margin_bottom.grid(row=0, column=3, padx=(0, 15), pady=5)
        
        ttk.Label(page_grid, text="左边距(pt):").grid(row=1, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.margin_left = ttk.Entry(page_grid, width=10)
        self.margin_left.insert(0, "90")
        self.margin_left.grid(row=1, column=1, padx=(0, 15), pady=5)
        
        ttk.Label(page_grid, text="右边距(pt):").grid(row=1, column=2, padx=(0, 5), pady=5, sticky=tk.W)
        self.margin_right = ttk.Entry(page_grid, width=10)
        self.margin_right.insert(0, "90")
        self.margin_right.grid(row=1, column=3, padx=(0, 15), pady=5)
        
        ttk.Label(page_grid, text="纸张大小:").grid(row=2, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.paper_size = ttk.Combobox(page_grid, width=12, 
                                      values=["A4", "A3", "Letter", "Legal"])
        self.paper_size.set("A4")
        self.paper_size.grid(row=2, column=1, padx=(0, 15), pady=5)
        
        # 字体设置
        font_frame = ttk.LabelFrame(self.main_frame, text="字体设置", padding="10")
        font_frame.pack(fill=tk.X, pady=(0, 15))
        
        font_grid = ttk.Frame(font_frame)
        font_grid.pack(fill=tk.X)
        
        ttk.Label(font_grid, text="中文字体:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.font_cn = ttk.Combobox(font_grid, width=15, 
                                   values=["宋体", "黑体", "微软雅黑", "楷体", "仿宋", "方正小标宋简体"])
        self.font_cn.set("宋体")
        self.font_cn.grid(row=0, column=1, padx=(0, 15), pady=5)
        
        ttk.Label(font_grid, text="英文字体:").grid(row=0, column=2, padx=(0, 5), pady=5, sticky=tk.W)
        self.font_en = ttk.Combobox(font_grid, width=15,
                                   values=["Times New Roman", "Arial", "Calibri", "Georgia", "Segoe UI"])
        self.font_en.set("Times New Roman")
        self.font_en.grid(row=0, column=3, padx=(0, 15), pady=5)
        
        ttk.Label(font_grid, text="正文字号(pt):").grid(row=1, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.font_size = ttk.Entry(font_grid, width=10)
        self.font_size.insert(0, "12")
        self.font_size.grid(row=1, column=1, padx=(0, 15), pady=5)
        
        ttk.Label(font_grid, text="行距:").grid(row=1, column=2, padx=(0, 5), pady=5, sticky=tk.W)
        self.line_spacing = ttk.Entry(font_grid, width=10)
        self.line_spacing.insert(0, "1.5")
        self.line_spacing.grid(row=1, column=3, padx=(0, 15), pady=5)
        
        ttk.Label(font_grid, text="首行缩进(pt):").grid(row=2, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.first_indent = ttk.Entry(font_grid, width=10)
        self.first_indent.insert(0, "28")
        self.first_indent.grid(row=2, column=1, padx=(0, 15), pady=5)
        
        # 标题设置
        heading_frame = ttk.LabelFrame(self.main_frame, text="标题设置", padding="10")
        heading_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 标题1
        h1_frame = ttk.Frame(heading_frame)
        h1_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(h1_frame, text="标题1 字号:", width=12).pack(side=tk.LEFT)
        self.h1_size = ttk.Entry(h1_frame, width=8)
        self.h1_size.insert(0, "18")
        self.h1_size.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(h1_frame, text="字体:").pack(side=tk.LEFT)
        self.h1_font = ttk.Combobox(h1_frame, width=12, values=["黑体", "微软雅黑", "宋体", "楷体"])
        self.h1_font.set("黑体")
        self.h1_font.pack(side=tk.LEFT, padx=(0, 10))
        
        self.h1_bold = tk.BooleanVar(value=True)
        ttk.Checkbutton(h1_frame, text="加粗", variable=self.h1_bold).pack(side=tk.LEFT, padx=(0, 10))
        
        # 标题2
        h2_frame = ttk.Frame(heading_frame)
        h2_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(h2_frame, text="标题2 字号:", width=12).pack(side=tk.LEFT)
        self.h2_size = ttk.Entry(h2_frame, width=8)
        self.h2_size.insert(0, "16")
        self.h2_size.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(h2_frame, text="字体:").pack(side=tk.LEFT)
        self.h2_font = ttk.Combobox(h2_frame, width=12, values=["黑体", "微软雅黑", "宋体", "楷体"])
        self.h2_font.set("黑体")
        self.h2_font.pack(side=tk.LEFT, padx=(0, 10))
        
        self.h2_bold = tk.BooleanVar(value=False)
        ttk.Checkbutton(h2_frame, text="加粗", variable=self.h2_bold).pack(side=tk.LEFT, padx=(0, 10))
        
        # 按钮区域
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="✅ 保存模板", 
                  command=self.save_template, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="💾 另存为...", 
                  command=self.save_as_template, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ 取消", 
                  command=self.dialog.destroy, width=15).pack(side=tk.RIGHT)
    
    def load_template_data(self):
        """加载模板数据"""
        if 'name' in self.template_data:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self.template_data['name'])
        
        if 'description' in self.template_data:
            self.desc_entry.delete(0, tk.END)
            self.desc_entry.insert(0, self.template_data['description'])
        
        # 页面设置
        if 'page_setup' in self.template_data:
            page = self.template_data['page_setup']
            self.margin_top.delete(0, tk.END)
            self.margin_top.insert(0, str(page.get('margin_top', 72)))
            
            self.margin_bottom.delete(0, tk.END)
            self.margin_bottom.insert(0, str(page.get('margin_bottom', 72)))
            
            self.margin_left.delete(0, tk.END)
            self.margin_left.insert(0, str(page.get('margin_left', 90)))
            
            self.margin_right.delete(0, tk.END)
            self.margin_right.insert(0, str(page.get('margin_right', 90)))
            
            self.paper_size.set(page.get('paper_size', 'A4'))
        
        # 字体设置
        if 'body' in self.template_data:
            body = self.template_data['body']
            self.font_cn.set(body.get('font_name_cn', '宋体'))
            self.font_en.set(body.get('font_name_en', 'Times New Roman'))
            self.font_size.delete(0, tk.END)
            self.font_size.insert(0, str(body.get('font_size', 12)))
            self.line_spacing.delete(0, tk.END)
            self.line_spacing.insert(0, str(body.get('line_spacing', 1.5)))
            self.first_indent.delete(0, tk.END)
            self.first_indent.insert(0, str(body.get('first_line_indent', 28)))
        
        # 标题设置
        if 'heading1' in self.template_data:
            h1 = self.template_data['heading1']
            self.h1_size.delete(0, tk.END)
            self.h1_size.insert(0, str(h1.get('font_size', 18)))
            self.h1_font.set(h1.get('font_name_cn', '黑体'))
            self.h1_bold.set(h1.get('bold', True))
        
        if 'heading2' in self.template_data:
            h2 = self.template_data['heading2']
            self.h2_size.delete(0, tk.END)
            self.h2_size.insert(0, str(h2.get('font_size', 16)))
            self.h2_font.set(h2.get('font_name_cn', '黑体'))
            self.h2_bold.set(h2.get('bold', False))
    
    def build_template_data(self):
        """构建模板数据"""
        template_data = {
            'name': self.name_entry.get().strip(),
            'description': self.desc_entry.get().strip(),
            'page_setup': {
                'margin_top': int(self.margin_top.get()),
                'margin_bottom': int(self.margin_bottom.get()),
                'margin_left': int(self.margin_left.get()),
                'margin_right': int(self.margin_right.get()),
                'paper_size': self.paper_size.get()
            },
            'body': {
                'font_name_cn': self.font_cn.get(),
                'font_name_en': self.font_en.get(),
                'font_size': float(self.font_size.get()),
                'line_spacing': float(self.line_spacing.get()),
                'first_line_indent': float(self.first_indent.get()),
                'alignment': 'justify'
            },
            'heading1': {
                'font_name_cn': self.h1_font.get(),
                'font_name_en': 'Arial',
                'font_size': float(self.h1_size.get()),
                'bold': self.h1_bold.get(),
                'alignment': 'left'
            },
            'heading2': {
                'font_name_cn': self.h2_font.get(),
                'font_name_en': 'Arial',
                'font_size': float(self.h2_size.get()),
                'bold': self.h2_bold.get(),
                'alignment': 'left'
            },
            'metadata': {
                'author': '用户自定义',
                'version': '1.0',
                'create_date': datetime.now().strftime('%Y-%m-%d')
            }
        }
        
        return template_data
    
    def save_template(self):
        """保存模板"""
        if not self.name_entry.get().strip():
            messagebox.showerror("错误", "模板名称不能为空！")
            return
        
        self.result = self.build_template_data()
        messagebox.showinfo("成功", f"模板 '{self.name_entry.get()}' 已保存！")
        self.dialog.destroy()
    
    def save_as_template(self):
        """另存为模板"""
        template_name = simpledialog.askstring("另存为", "请输入新模板名称（英文）:")
        if not template_name:
            return
        
        template_data = self.build_template_data()
        template_data['name'] = template_name
        
        self.result = template_data
        messagebox.showinfo("成功", f"模板已构建为 '{template_name}'")
        self.dialog.destroy()