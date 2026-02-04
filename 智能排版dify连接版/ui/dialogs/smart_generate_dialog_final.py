"""
智能生成对话框 - 最终版
防止重复回调，确保内容正常
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging

logger = logging.getLogger(__name__)


class SmartGenerateDialog:
    """智能生成对话框 - 最终版"""
    
    def __init__(self, parent, config_manager, template_manager, callback=None):
        self.parent = parent
        self.config_manager = config_manager
        self.template_manager = template_manager
        self.callback = callback
        self.generated_content = ""
        self._callback_called = False  # 防止重复回调
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🚀 智能内容生成器")
        self.dialog.geometry("950x700")
        self.dialog.resizable(False, False)
        
        # 设置为模态对话框
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 修复叉号关闭
        self.dialog.protocol("WM_DELETE_WINDOW", self._safe_destroy)
        
        # 创建界面
        self._create_ui()
        
        # 居中显示
        self._center_dialog()
        
        logger.info("智能生成对话框已打开")
    
    def _safe_destroy(self):
        """安全销毁对话框"""
        self.dialog.destroy()
    
    def _center_dialog(self):
        """居中对话框"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """创建界面"""
        # 主容器
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="🤖 智能内容生成器",
            font=('Microsoft YaHei', 16, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # 左右分栏
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：输入区
        left_frame = ttk.LabelFrame(content_frame, text="📝 输入需求", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 需求输入
        ttk.Label(left_frame, text="请输入您的需求:").pack(anchor=tk.W, pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(
            left_frame,
            height=12,
            wrap=tk.WORD,
            font=('Microsoft YaHei', 10)
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # 示例
        ttk.Label(
            left_frame,
            text="💡 示例：帮我写一篇关于艾灸与人文的讲座稿",
            font=('Microsoft YaHei', 9),
            foreground="blue"
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # 模板选择
        template_frame = ttk.Frame(left_frame)
        template_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(template_frame, text="选择模板:").pack(side=tk.LEFT)
        
        self.template_var = tk.StringVar()
        templates = self.template_manager.get_template_list()
        self.template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            values=templates,
            state="readonly",
            width=25
        )
        self.template_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        if templates:
            self.template_var.set(templates[0])
        
        # 右侧：控制区
        right_frame = ttk.LabelFrame(content_frame, text="⚙️ 生成控制", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 状态
        self.status_label = ttk.Label(
            right_frame,
            text="🔵 准备就绪",
            font=('Microsoft YaHei', 10)
        )
        self.status_label.pack(pady=(0, 15))
        
        # 按钮框架
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(pady=(0, 15))
        
        # 测试按钮
        self.test_btn = ttk.Button(
            button_frame,
            text="🔗 测试连接",
            command=self._test_connection,
            width=15
        )
        self.test_btn.pack(pady=(0, 10))
        
        # 生成按钮
        self.generate_btn = ttk.Button(
            button_frame,
            text="🚀 开始生成",
            command=self._start_generation,
            width=15
        )
        self.generate_btn.pack(pady=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(right_frame, mode='indeterminate', length=200)
        self.progress.pack(pady=(0, 15))
        
        # 预览区
        ttk.Label(right_frame, text="📋 生成预览:").pack(anchor=tk.W, pady=(0, 5))
        
        self.preview_text = scrolledtext.ScrolledText(
            right_frame,
            height=15,
            wrap=tk.WORD,
            font=('Microsoft YaHei', 9),
            state='disabled'
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮区
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 取消按钮
        ttk.Button(
            bottom_frame,
            text="❌ 取消",
            command=self._safe_destroy,
            width=12
        ).pack(side=tk.LEFT)
        
        # 中间选项
        middle_frame = ttk.Frame(bottom_frame)
        middle_frame.pack(side=tk.LEFT, expand=True, padx=20)
        
        self.auto_import_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(
            middle_frame,
            text="自动导入到排版系统",
            variable=self.auto_import_var
        )
        auto_check.pack()
        
        # 使用按钮
        self.use_btn = ttk.Button(
            bottom_frame,
            text="✅ 使用内容",
            command=self._use_content,
            width=12,
            state='disabled'
        )
        self.use_btn.pack(side=tk.RIGHT)
        
        # 初始焦点
        self.input_text.focus()
    
    def _test_connection(self):
        """测试连接"""
        self.test_btn.config(state='disabled', text="测试中...")
        self.status_label.config(text="🔄 测试连接...")
        
        thread = threading.Thread(target=self._do_test_connection)
        thread.daemon = True
        thread.start()
    
    def _do_test_connection(self):
        """执行测试"""
        try:
            from core.dify_client_final import get_dify_client
            
            client = get_dify_client(self.config_manager)
            success, message = client.test_connection()
            
            self.dialog.after(0, self._update_test_result, success, message)
            
        except Exception as e:
            self.dialog.after(0, self._update_test_result, False, str(e))
    
    def _update_test_result(self, success, message):
        """更新测试结果"""
        self.test_btn.config(state='normal', text="🔗 测试连接")
        
        if success:
            self.status_label.config(text="✅ 连接成功", foreground="green")
        else:
            self.status_label.config(text="❌ 连接失败", foreground="red")
    
    def _start_generation(self):
        """开始生成"""
        requirement = self.input_text.get('1.0', tk.END).strip()
        if not requirement:
            messagebox.showwarning("提示", "请输入需求描述！")
            return
        
        if not self.template_var.get():
            messagebox.showwarning("提示", "请选择模板！")
            return
        
        # 禁用按钮
        self.generate_btn.config(state='disabled', text="生成中...")
        self.test_btn.config(state='disabled')
        self.use_btn.config(state='disabled')
        self.status_label.config(text="🔄 正在生成...", foreground="orange")
        self.progress.start()
        
        # 清空预览
        self.preview_text.config(state='normal')
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', "正在生成内容，请稍候...\n")
        self.preview_text.config(state='disabled')
        
        # 在新线程中生成
        thread = threading.Thread(target=self._do_generation, args=(requirement,))
        thread.daemon = True
        thread.start()
    
    def _do_generation(self, requirement):
        """执行生成"""
        try:
            from core.dify_client_final import get_dify_client
            
            client = get_dify_client(self.config_manager)
            success, content = client.generate_content(requirement)
            
            self.dialog.after(0, self._update_generation_result, success, content)
            
        except Exception as e:
            self.dialog.after(0, self._update_generation_result, False, str(e))
    
    def _update_generation_result(self, success, content):
        """更新生成结果"""
        self.progress.stop()
        
        self.preview_text.config(state='normal')
        self.preview_text.delete('1.0', tk.END)
        
        if success:
            self.generated_content = content
            self.preview_text.insert('1.0', content)
            
            # 启用按钮
            self.generate_btn.config(state='normal', text="🚀 重新生成")
            self.test_btn.config(state='normal')
            self.use_btn.config(state='normal')
            
            char_count = len(content)
            self.status_label.config(text=f"✅ 生成完成 ({char_count}字符)", foreground="green")
            
            # 自动导入
            if self.auto_import_var.get():
                self.dialog.after(3000, self._auto_import)
        else:
            self.preview_text.insert('1.0', f"❌ 生成失败:\n{content}")
            self.generate_btn.config(state='normal', text="🚀 重新生成")
            self.test_btn.config(state='normal')
            self.status_label.config(text="❌ 生成失败", foreground="red")
        
        self.preview_text.config(state='disabled')
    
    def _auto_import(self):
        """自动导入"""
        if not self.generated_content or self._callback_called:
            return
        
        self._use_content()
    
    def _use_content(self):
        """使用内容"""
        if not self.generated_content or self._callback_called:
            return
        
        template_name = self.template_var.get()
        
        if self.callback:
            self._callback_called = True
            self.callback(self.generated_content, template_name)
        
        self._safe_destroy()