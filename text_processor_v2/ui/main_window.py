"""
主窗口模块
应用程序的主界面和控制器
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import logging
import threading
import queue
import os
import re
from pathlib import Path
from datetime import datetime

from ui.dialogs import ModelConfigDialog, TemplateEditorDialog

logger = logging.getLogger(__name__)


class MainWindow:
    """主窗口类"""
    
    def __init__(self, root, config_manager, model_manager, 
                 template_manager, document_processor):
        """
        初始化主窗口
        
        Args:
            root: Tkinter根窗口
            config_manager: 配置管理器实例
            model_manager: 模型管理器实例
            template_manager: 模板管理器实例
            document_processor: 文档处理器实例
        """
        self.root = root
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.template_manager = template_manager
        self.doc_processor = document_processor
        
        # 窗口设置
        self.root.title("专业文档智能排版系统 v2.0 - 多模型支持")
        self.root.geometry("1200x900")
        
        # 当前状态
        self.is_processing = False
        self.current_file = ""
        self.original_title = ""
        
        # 消息队列
        self.message_queue = queue.Queue()
        
        # 创建界面
        self.create_widgets()
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("🟢 就绪 - 专业文档智能排版系统 v2.0 (多模型支持)")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 定时检查消息队列
        self.root.after(100, self.process_message_queue)
        
        # 窗口居中
        self.center_window()
        
        logger.info("主窗口初始化完成")
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """创建界面控件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🤖 专业文档智能排版系统 v2.0", 
                               font=('Microsoft YaHei', 18, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="多模型AI智能润色 + 动态模板编辑 + 一键导出",
                                  font=('Microsoft YaHei', 11), foreground="#666")
        subtitle_label.pack()
        
        # 内容区域 - 使用Notebook实现标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 处理页面
        process_frame = ttk.Frame(notebook)
        notebook.add(process_frame, text="📄 文档处理")
        
        # 模板页面
        template_frame = ttk.Frame(notebook)
        notebook.add(template_frame, text="🎨 模板管理")
        
        # 模型管理页面
        model_frame = ttk.Frame(notebook)
        notebook.add(model_frame, text="🤖 模型管理")
        
        # 填充各页面
        self.create_process_widgets(process_frame)
        self.create_template_widgets(template_frame)
        self.create_model_widgets(model_frame)
    
    def create_process_widgets(self, parent):
        """创建处理页面的控件"""
        # 左右分栏
        left_panel = ttk.Frame(parent)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_panel = ttk.Frame(parent)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧：输入区
        input_frame = ttk.LabelFrame(left_panel, text="📥 文档输入", padding="15")
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="📂 选择文档", 
                  command=self.load_file, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="📋 粘贴文本", 
                  command=self.paste_text, width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        self.file_label = ttk.Label(file_frame, text="未选择文档", foreground="#0066cc")
        self.file_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 标题输入
        title_frame = ttk.Frame(input_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="文档标题:", 
                 font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, font=('Microsoft YaHei', 10))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 原文内容
        ttk.Label(input_frame, text="原文内容:", 
                 font=('Microsoft YaHei', 10, 'bold')).pack(anchor=tk.W)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame, 
            height=15, 
            wrap=tk.WORD, 
            font=('Consolas', 10),
            bg='#f8f9fa',
            relief=tk.SUNKEN
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 右侧：处理区
        control_frame = ttk.LabelFrame(right_panel, text="⚙️ 处理控制", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模型选择
        model_select_frame = ttk.Frame(control_frame)
        model_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(model_select_frame, text="AI模型:", 
                 font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar(value=self.model_manager.current_model_id)
        self.model_combo = ttk.Combobox(
            model_select_frame, 
            textvariable=self.model_var,
            values=self.model_manager.get_model_list(),
            state="readonly",
            width=20
        )
        self.model_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.model_combo.bind('<<ComboboxSelected>>', self.on_model_changed)
        
        # 模板选择
        template_select_frame = ttk.Frame(control_frame)
        template_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(template_select_frame, text="选择模板:", 
                 font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        
        self.template_var = tk.StringVar(value=self.template_manager.current_template)
        self.template_combo = ttk.Combobox(
            template_select_frame, 
            textvariable=self.template_var,
            values=self.template_manager.get_template_list(),
            state="readonly",
            width=20
        )
        self.template_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_changed)
        
        # 处理选项
        option_frame = ttk.Frame(control_frame)
        option_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_correct_var = tk.BooleanVar(value=True)
        self.keep_structure_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(option_frame, text="自动纠错", 
                       variable=self.auto_correct_var).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(option_frame, text="保持结构", 
                       variable=self.keep_structure_var).pack(side=tk.LEFT)
        
        # 操作按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(
            button_frame,
            text="🔄 刷新",
            command=self.refresh_all,
            width=12
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 处理按钮
        self.process_btn = ttk.Button(
            button_frame, 
            text="🚀 AI智能处理", 
            command=self.start_processing,
            width=12
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止按钮（默认禁用）
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹️ 停止",
            command=self.stop_processing,
            width=12,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存按钮
        self.save_btn = ttk.Button(
            button_frame, 
            text="💾 保存Word文档", 
            command=self.save_as_word,
            width=12,
            state='disabled'
        )
        self.save_btn.pack(side=tk.LEFT)
        
        # 进度显示
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(10, 0))
        
        # 模板预览
        preview_frame = ttk.LabelFrame(right_panel, text="📋 模板预览", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=5,
            wrap=tk.WORD,
            font=('Microsoft YaHei', 9),
            bg='#f5f5f5'
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 更新预览
        self.update_template_preview()
        
        # 处理结果
        result_frame = ttk.LabelFrame(right_panel, text="✨ 处理结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            result_frame, 
            height=20, 
            wrap=tk.WORD, 
            font=('Consolas', 10),
            bg='#f8f9fa'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 统计信息
        self.stats_label = ttk.Label(result_frame, text="", font=('Microsoft YaHei', 9))
        self.stats_label.pack(fill=tk.X, pady=(5, 0))
    
    def create_model_widgets(self, parent):
        """创建模型管理页面的控件"""
        # 主框架
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🤖 AI模型配置管理", 
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 说明文本
        info_text = """💡 功能介绍：
1. 支持多个国产AI模型切换
2. 可以根据文档长度选择合适的模型
3. 长文档建议使用硅基流动或通义千问
4. 短文档使用DeepSeek Chat更快速"""
        
        info_label = ttk.Label(main_frame, text=info_text, 
                              font=('Microsoft YaHei', 10),
                              background='#f0f8ff',
                              padding=10,
                              relief=tk.RIDGE,
                              wraplength=800,
                              justify=tk.LEFT)
        info_label.pack(fill=tk.X, pady=(0, 15))
        
        # 模型列表
        list_frame = ttk.LabelFrame(main_frame, text="📋 可用模型列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('id', 'name', 'model', 'max_tokens', 'provider')
        self.model_config_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # 设置列
        self.model_config_tree.heading('id', text='模型ID')
        self.model_config_tree.heading('name', text='显示名称')
        self.model_config_tree.heading('model', text='模型名称')
        self.model_config_tree.heading('max_tokens', text='最大长度')
        self.model_config_tree.heading('provider', text='提供商')
        
        self.model_config_tree.column('id', width=100)
        self.model_config_tree.column('name', width=150)
        self.model_config_tree.column('model', width=150)
        self.model_config_tree.column('max_tokens', width=80)
        self.model_config_tree.column('provider', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.model_config_tree.yview)
        self.model_config_tree.configure(yscroll=scrollbar.set)
        
        self.model_config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="⚙️ 配置模型", 
                  command=self.configure_models, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 刷新列表", 
                  command=self.refresh_model_list, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📊 查看API用量", 
                  command=self.show_api_usage, width=20).pack(side=tk.LEFT)
        
        # 加载模型列表
        self.refresh_model_list()
    
    def create_template_widgets(self, parent):
        """创建模板管理页面的控件"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎨 模板管理系统", 
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(button_frame, text="🆕 创建新模板", 
                  command=self.create_new_template, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="✏️ 编辑模板", 
                  command=self.edit_template, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="💾 另存为模板", 
                  command=self.save_as_template, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🗑️ 删除模板", 
                  command=self.delete_template, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 刷新列表", 
                  command=self.load_templates_to_tree, width=20).pack(side=tk.RIGHT)
        
        # 模板列表和详情
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模板列表
        list_frame = ttk.LabelFrame(content_frame, text="📁 可用模板", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        columns = ('name', 'description', 'font')
        self.template_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 设置列
        self.template_tree.heading('name', text='模板名称')
        self.template_tree.heading('description', text='描述')
        self.template_tree.heading('font', text='主要字体')
        
        self.template_tree.column('name', width=150)
        self.template_tree.column('description', width=250)
        self.template_tree.column('font', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.template_tree.yview)
        self.template_tree.configure(yscroll=scrollbar.set)
        
        self.template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.template_tree.bind('<<TreeviewSelect>>', self.on_template_selected)
        
        # 模板详情
        detail_frame = ttk.LabelFrame(content_frame, text="🔍 模板详情", padding="10")
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.template_detail = scrolledtext.ScrolledText(
            detail_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f5f5f5',
            height=20
        )
        self.template_detail.pack(fill=tk.BOTH, expand=True)
        
        # 加载模板到列表
        self.load_templates_to_tree()
    
    # ========== 新增的刷新和停止方法 ==========
    
    def refresh_all(self):
        """
        刷新功能：清空所有内容并重置状态
        """
        # 停止任何正在进行的处理
        if self.is_processing:
            self.stop_processing()
        
        # 清空输入框和输出框内容
        self.input_text.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)
        
        # 重置文件选择状态
        self.current_file = ""
        self.file_label.config(text="未选择文档", foreground="#0066cc")
        
        # 清空标题输入框
        self.title_entry.delete(0, tk.END)
        self.original_title = ""
        
        # 重置统计数据
        self.stats_label.config(text="")
        
        # 禁用保存按钮
        self.save_btn.config(state='disabled')
        
        # 重置按钮状态
        self.process_btn.config(state='normal', text="🚀 AI智能处理")
        self.stop_btn.config(state='disabled')
        self.refresh_btn.config(state='normal')
        
        # 停止进度条
        self.progress.stop()
        
        # 重置处理状态
        self.is_processing = False
        
        # 发送通知消息
        self.queue_message("success", "✅ 所有内容已刷新")
    
    def stop_processing(self):
        """
        停止功能：中断正在进行的处理
        """
        if not self.is_processing:
            return
        
        # 设置处理状态标志为False
        self.is_processing = False
        
        # 如果文档处理器有停止方法，调用它
        if hasattr(self.doc_processor, 'stop_processing'):
            self.doc_processor.stop_processing()
        
        # 禁用停止按钮，启用处理按钮
        self.stop_btn.config(state='disabled')
        self.process_btn.config(state='normal', text="🚀 AI智能处理")
        self.refresh_btn.config(state='normal')
        
        # 停止进度条动画
        self.progress.stop()
        
        # 发送停止通知消息
        self.queue_message("warning", "⏹️ 处理已停止")
    
    # ========== 事件处理方法 ==========
    
    def on_model_changed(self, event=None):
        """模型选择变化"""
        model_id = self.model_var.get()
        if model_id and model_id != self.model_manager.current_model_id:
            if self.model_manager.switch_model(model_id):
                model_config = self.model_manager.get_current_model_config()
                if model_config:
                    info = f"当前模型: {model_config.get('name', model_id)} "
                    info += f"(最大长度: {model_config.get('max_tokens', 8192)} tokens)"
                    self.queue_message("info", info)
    
    def on_template_changed(self, event=None):
        """模板选择变化时更新预览"""
        template_name = self.template_var.get()
        if template_name != self.template_manager.current_template:
            if self.template_manager.switch_template(template_name):
                self.update_template_preview()
    
    def update_template_preview(self):
        """更新模板预览"""
        template_name = self.template_var.get()
        template = self.template_manager.get_template(template_name)
        
        if template:
            preview = f"📋 {template.get('name', template_name)}\n"
            preview += f"📝 {template.get('description', '')}\n\n"
            
            if 'body' in template:
                body = template['body']
                preview += f"字体: {body.get('font_name_cn', '宋体')} / {body.get('font_name_en', 'Times New Roman')}\n"
                preview += f"字号: {body.get('font_size', '12')}pt\n"
                preview += f"行距: {body.get('line_spacing', '1.5')}\n"
            
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview)
    
    def load_file(self):
        """加载文件"""
        filetypes = [
            ('所有文档', '*.txt;*.docx;*.pdf'),
            ('文本文件', '*.txt'),
            ('Word文档', '*.docx'),
            ('PDF文件', '*.pdf')
        ]
        
        filename = filedialog.askopenfilename(
            title="选择文档",
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        self.current_file = filename
        self.file_label.config(text=f"📄 {os.path.basename(filename)}")
        
        try:
            # 加载文件
            success, content = self.doc_processor.load_file(filename)
            
            if success:
                # 提取标题
                title = self.doc_processor.extract_title(content)
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, title)
                self.original_title = title
                
                # 显示内容
                self.input_text.delete('1.0', tk.END)
                self.input_text.insert('1.0', content)
                
                # 更新统计
                char_count = len(content)
                self.stats_label.config(text=f"📊 原文: {char_count} 字符")
                self.queue_message("info", f"✅ 已加载文档: {os.path.basename(filename)}")
            else:
                self.queue_message("error", f"加载失败: {content}")
                
        except Exception as e:
            logger.error(f"加载文件失败: {str(e)}")
            self.queue_message("error", f"加载失败: {str(e)}")
    
    def paste_text(self):
        """粘贴文本内容"""
        try:
            text = self.root.clipboard_get()
            if text:
                self.input_text.delete('1.0', tk.END)
                self.input_text.insert('1.0', text)
                self.file_label.config(text="📋 已粘贴剪贴板内容")
                self.queue_message("info", "✅ 已粘贴剪贴板内容")
                
                # 自动提取标题
                title = self.doc_processor.extract_title(text)
                if title:
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.insert(0, title)
        except:
            self.queue_message("warning", "剪贴板为空或内容无法获取")
    
    def start_processing(self):
        """开始处理文档"""
        if self.is_processing:
            self.queue_message("warning", "正在处理中，请稍候...")
            return
        
        # 获取内容
        content = self.input_text.get('1.0', tk.END).strip()
        if not content:
            self.queue_message("warning", "请输入或加载要处理的文档内容")
            return
        
        # 检查模型配置
        model_id = self.model_var.get()
        validation = self.model_manager.validate_model_config(model_id)
        if not validation['status']:
            self.queue_message("error", f"模型配置验证失败: {validation['message']}")
            return
        
        # 设置处理状态
        self.is_processing = True
        
        # 按钮状态管理（根据集成点2）
        self.process_btn.config(state='disabled', text="处理中...")
        self.stop_btn.config(state='normal')  # 启用停止按钮
        self.refresh_btn.config(state='disabled')  # 禁用刷新按钮
        self.save_btn.config(state='disabled')  # 禁用保存按钮
        
        self.progress.start(10)
        
        # 在新线程中处理
        def processing_thread():
            try:
                success, result = self.doc_processor.process_document(content, model_id)
                
                # 在主线程中更新UI
                def update_result():
                    self.progress.stop()
                    self.is_processing = False
                    
                    # 按钮状态管理（正常结束）
                    self.process_btn.config(state='normal', text="🚀 AI智能处理")
                    self.stop_btn.config(state='disabled')  # 禁用停止按钮
                    self.refresh_btn.config(state='normal')  # 启用刷新按钮
                    self.save_btn.config(state='normal')  # 启用保存按钮（如果有结果）
                    
                    if success:
                        self.output_text.delete('1.0', tk.END)
                        self.output_text.insert('1.0', result)
                        
                        # 更新统计
                        stats = self.doc_processor.get_stats(content, result)
                        self.stats_label.config(
                            text=f"📊 统计: 原文{stats['original_length']}字 → 结果{stats['processed_length']}字 ({stats['change_rate']:+.1f}%)"
                        )
                        
                        model_config = self.model_manager.get_current_model_config()
                        model_name = model_config.get('name', model_id) if model_config else model_id
                        template_name = self.template_manager.current_template
                        
                        self.queue_message("success", 
                            f"✅ 处理完成！\n"
                            f"🤖 使用模型: {model_name}\n"
                            f"🎨 使用模板: {template_name}")
                    else:
                        self.queue_message("error", f"❌ {result}")
                
                self.root.after(0, update_result)
                
            except Exception as e:
                logger.error(f"处理线程异常: {str(e)}")
                
                def handle_error(error):
                    self.progress.stop()
                    self.is_processing = False
                    
                    # 按钮状态管理（错误情况）
                    self.process_btn.config(state='normal', text="🚀 AI智能处理")
                    self.stop_btn.config(state='disabled')  # 禁用停止按钮
                    self.refresh_btn.config(state='normal')  # 启用刷新按钮
                    self.save_btn.config(state='disabled')  # 禁用保存按钮
                    
                    self.queue_message("error", f"处理过程中发生错误: {str(error)}")
                
                self.root.after(0, handle_error, e)
        
        thread = threading.Thread(target=processing_thread)
        thread.daemon = True
        thread.start()
    
    def save_as_word(self):
        """保存为Word文档"""
        content = self.output_text.get('1.0', tk.END).strip()
        if not content:
            self.queue_message("warning", "没有可保存的内容，请先处理文档")
            return
        
        title = self.title_entry.get().strip() or self.original_title or "文档标题"
        template_name = self.template_var.get()
        
        # 选择保存位置
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"{safe_title}_{timestamp}.docx"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".docx",
            initialfile=default_name,
            filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")],
            title="保存Word文档"
        )
        
        if not filename:
            return
        
        try:
            # 保存文档
            success, file_path = self.doc_processor.save_as_word(content, title, template_name)
            
            if success:
                template = self.template_manager.get_template(template_name)
                template_display = template.get('name', template_name) if template else template_name
                model_config = self.model_manager.get_current_model_config()
                model_name = model_config.get('name', self.model_var.get()) if model_config else self.model_var.get()
                
                self.queue_message("success", 
                    f"✅ 文档保存成功！\n"
                    f"📁 文件: {os.path.basename(file_path)}\n"
                    f"🤖 模型: {model_name}\n"
                    f"🎨 模板: {template_display}\n"
                    f"📝 大小: {len(content)} 字符")
            else:
                self.queue_message("error", file_path)
                
        except Exception as e:
            logger.error(f"保存文档失败: {str(e)}")
            self.queue_message("error", f"保存失败: {str(e)}")
    
    def refresh_model_list(self):
        """刷新模型列表"""
        for item in self.model_config_tree.get_children():
            self.model_config_tree.delete(item)
        
        model_info = self.model_manager.get_model_display_info()
        for info in model_info:
            self.model_config_tree.insert('', 'end', 
                values=(info['id'],
                       info['name'],
                       info['model'],
                       info['max_tokens'],
                       info['provider']))
    
    def configure_models(self):
        """配置模型"""
        dialog = ModelConfigDialog(
            self.root, 
            self.model_manager.model_configs, 
            self.model_manager.current_model_id
        )
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # 更新模型配置
            for model_id, config in dialog.result.items():
                if model_id in self.model_manager.model_configs:
                    self.model_manager.model_configs[model_id] = config
            
            # 保存配置
            self.config_manager.save_model_configs()
            
            # 更新UI
            self.model_var.set(self.model_manager.current_model_id)
            self.model_combo['values'] = self.model_manager.get_model_list()
            
            # 刷新模型列表
            self.refresh_model_list()
            
            self.queue_message("success", "✅ 模型配置已更新")
    
    def show_api_usage(self):
        """显示API用量信息"""
        messagebox.showinfo("API用量提示", 
            "💡 API用量提示：\n\n"
            "1. DeepSeek: 每月免费额度，适合短文档\n"
            "2. Kimi (Moonshot): 免费试用额度\n"
            "3. 通义千问: 按量付费，支持长文本\n"
            "4. 硅基流动: 免费额度充足，支持多种模型\n"
            "5. 百川大模型: 免费体验，支持长文本\n"
            "6. 智谱GLM: 按量付费，性能稳定\n\n"
            "📌 建议：\n"
            "短文档(<4000字) → DeepSeek\n"
            "中长文档(4000-15000字) → 硅基流动\n"
            "超长文档(>15000字) → 通义千问/百川")
    
    def load_templates_to_tree(self):
        """加载模板到树形列表"""
        # 重新加载模板
        self.config_manager.load_templates()
        
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)
        
        template_info = self.template_manager.get_template_info()
        for info in template_info:
            self.template_tree.insert('', 'end', iid=info['id'],
                values=(info['name'],
                       info['description'],
                       info['body_font']))
        
        # 更新下拉框
        self.template_var.set(self.template_manager.current_template)
    
    def on_template_selected(self, event):
        """模板选择事件"""
        selection = self.template_tree.selection()
        if not selection:
            return
        
        template_name = selection[0]
        template_data = self.template_manager.get_template(template_name)
        
        # 显示详情
        detail_text = f"模板名称: {template_data.get('name', template_name)}\n"
        detail_text += f"模板ID: {template_name}\n"
        detail_text += f"描述: {template_data.get('description', '')}\n\n"
        
        detail_text += "页面设置:\n"
        if 'page_setup' in template_data:
            page = template_data['page_setup']
            detail_text += f"  纸张: {page.get('paper_size', 'A4')}\n"
            detail_text += f"  边距: 上{page.get('margin_top', 0)}pt, "
            detail_text += f"下{page.get('margin_bottom', 0)}pt, "
            detail_text += f"左{page.get('margin_left', 0)}pt, "
            detail_text += f"右{page.get('margin_right', 0)}pt\n\n"
        
        detail_text += "字体设置:\n"
        if 'body' in template_data:
            body = template_data['body']
            detail_text += f"  正文: 中文{body.get('font_name_cn', '')}, "
            detail_text += f"英文{body.get('font_name_en', '')}\n"
            detail_text += f"  字号: {body.get('font_size', '')}pt\n"
            detail_text += f"  行距: {body.get('line_spacing', '')}\n\n"
        
        detail_text += "标题设置:\n"
        for i in range(1, 4):
            heading_key = f'heading{i}'
            if heading_key in template_data:
                heading = template_data[heading_key]
                detail_text += f"  标题{i}: {heading.get('font_size', '')}pt, "
                detail_text += f"{heading.get('font_name_cn', '')}, "
                detail_text += f"{'加粗' if heading.get('bold', False) else '正常'}\n"
        
        self.template_detail.delete('1.0', tk.END)
        self.template_detail.insert('1.0', detail_text)
    
    def create_new_template(self):
        """创建新模板"""
        dialog = TemplateEditorDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # 保存模板
            template_name = dialog.result['name'].lower().replace(' ', '_')
            success = self.template_manager.create_template(dialog.result)
            
            if success:
                # 重新加载模板
                self.config_manager.load_templates()
                self.load_templates_to_tree()
                self.queue_message("success", f"✅ 模板 '{template_name}' 创建成功")
            else:
                self.queue_message("error", "❌ 创建模板失败")
    
    def edit_template(self):
        """编辑模板"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模板！")
            return
        
        template_name = selection[0]
        template_data = self.template_manager.get_template(template_name)
        
        if not template_data:
            messagebox.showerror("错误", f"模板 '{template_name}' 不存在！")
            return
        
        dialog = TemplateEditorDialog(self.root, template_data)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # 保存修改
            success = self.template_manager.update_template(template_name, dialog.result)
            
            if success:
                # 重新加载模板
                self.config_manager.load_templates()
                self.load_templates_to_tree()
                self.queue_message("success", f"✅ 模板 '{template_name}' 更新成功")
            else:
                self.queue_message("error", "❌ 更新模板失败")
    
    def save_as_template(self):
        """另存为模板"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模板！")
            return
        
        template_name = selection[0]
        new_name = simpledialog.askstring("另存为", "请输入新模板名称（英文）:", 
                                         initialvalue=f"{template_name}_copy")
        
        if not new_name:
            return
        
        # 复制模板数据
        template_data = self.template_manager.get_template(template_name)
        if not template_data:
            self.queue_message("error", f"❌ 模板 '{template_name}' 不存在")
            return
        
        import copy
        new_template_data = copy.deepcopy(template_data)
        new_template_data['name'] = new_name.replace('_', ' ').title()
        
        # 保存新模板
        success = self.template_manager.create_template(new_template_data)
        
        if success:
            # 重新加载模板
            self.config_manager.load_templates()
            self.load_templates_to_tree()
            self.queue_message("success", f"✅ 模板已另存为 '{new_name}'")
        else:
            self.queue_message("error", "❌ 保存模板失败")
    
    def delete_template(self):
        """删除模板"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模板！")
            return
        
        template_name = selection[0]
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除模板 '{template_name}' 吗？\n此操作不可恢复！"):
            return
        
        # 删除模板
        success = self.template_manager.delete_template(template_name)
        
        if success:
            # 重新加载模板
            self.config_manager.load_templates()
            self.load_templates_to_tree()
            self.queue_message("success", f"✅ 模板 '{template_name}' 已删除")
        else:
            self.queue_message("error", "❌ 删除模板失败")
    
    def queue_message(self, msg_type, message):
        """将消息加入队列"""
        self.message_queue.put((msg_type, message))
    
    def process_message_queue(self):
        """处理消息队列"""
        try:
            while True:
                msg_type, message = self.message_queue.get_nowait()
                
                if msg_type == "info":
                    self.status_var.set(f"ℹ️ {message}")
                elif msg_type == "success":
                    self.status_var.set(f"✅ {message}")
                elif msg_type == "warning":
                    self.status_var.set(f"⚠️ {message}")
                    messagebox.showwarning("提示", message)
                elif msg_type == "error":
                    self.status_var.set(f"❌ {message}")
                    messagebox.showerror("错误", message)
                
        except queue.Empty:
            pass
        
        # 继续检查队列
        self.root.after(100, self.process_message_queue)