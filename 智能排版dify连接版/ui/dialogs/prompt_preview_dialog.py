"""
提示词预览对话框
显示模板提示词的只读预览
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class PromptPreviewDialog(tk.Toplevel):
    """提示词预览对话框"""
    
    def __init__(self, parent, 
                 template_id: str,
                 template_name: str,
                 prompt: str,
                 last_modified: str = None,
                 usage_count: int = 0,
                 on_copy: Optional[Callable] = None,
                 **kwargs):
        """
        初始化预览对话框
        
        Args:
            parent: 父窗口
            template_id: 模板ID
            template_name: 模板名称
            prompt: 提示词内容
            last_modified: 最后修改时间
            usage_count: 使用次数
            on_copy: 复制回调函数
            **kwargs: 传递给Toplevel的其他参数
        """
        super().__init__(parent, **kwargs)
        
        self.template_id = template_id
        self.template_name = template_name
        self.prompt = prompt
        self.last_modified = last_modified or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.usage_count = usage_count
        self.on_copy = on_copy
        
        # 窗口设置
        self.title(f"提示词预览 - {template_name}")
        self.geometry("600x500")
        self.resizable(True, True)
        
        # 设置窗口置顶
        self.transient(parent)
        self.grab_set()
        
        # 创建UI
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        # 居中显示
        self._center_window()
    
    def _create_widgets(self):
        """创建子组件"""
        # 标题框架
        self.frame_title = ttk.Frame(self)
        
        self.label_title = ttk.Label(
            self.frame_title,
            text=f"📝 提示词预览 - {self.template_name}",
            font=("微软雅黑", 12, "bold")
        )
        
        # 信息框架
        self.frame_info = ttk.LabelFrame(self, text="模板信息", padding=10)
        
        # 最后修改时间
        self.label_modified = ttk.Label(
            self.frame_info,
            text=f"📅 最后修改：{self.last_modified}",
            font=("微软雅黑", 9)
        )
        
        # 使用次数
        self.label_usage = ttk.Label(
            self.frame_info,
            text=f"📊 使用次数：{self.usage_count}次",
            font=("微软雅黑", 9)
        )
        
        # 内容框架
        self.frame_content = ttk.LabelFrame(self, text="提示词内容", padding=10)
        
        # 滚动文本框 - 只读显示
        self.text_prompt = scrolledtext.ScrolledText(
            self.frame_content,
            wrap=tk.WORD,
            width=70,
            height=15,
            font=("微软雅黑", 10),
            state="normal"  # 初始为normal以便插入文本
        )
        
        # 插入提示词内容
        self.text_prompt.insert("1.0", self.prompt)
        self.text_prompt.configure(state="disabled")  # 设为只读
        
        # 变量框架
        self.frame_variables = ttk.LabelFrame(self, text="可用变量", padding=10)
        
        variables_text = """• {document} - 文档内容
• {title} - 文档标题
• {requirements} - 额外要求
• {template} - 模板名称
• {date} - 当前日期"""
        
        self.label_variables = ttk.Label(
            self.frame_variables,
            text=variables_text,
            font=("微软雅黑", 9),
            justify=tk.LEFT
        )
        
        # 按钮框架
        self.frame_buttons = ttk.Frame(self)
        
        self.btn_copy = ttk.Button(
            self.frame_buttons,
            text="📋 复制到剪贴板",
            command=self._on_copy
        )
        
        self.btn_close = ttk.Button(
            self.frame_buttons,
            text="关闭",
            command=self.destroy
        )
        
        # 统计信息标签
        char_count = len(self.prompt)
        self.label_stats = ttk.Label(
            self.frame_content,
            text=f"字符数: {char_count}",
            font=("微软雅黑", 8),
            foreground="gray"
        )
    
    def _setup_layout(self):
        """设置布局"""
        # 标题框架
        self.frame_title.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.label_title.pack(pady=5)
        
        # 信息框架
        self.frame_info.pack(fill=tk.X, padx=10, pady=5)
        self.label_modified.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.label_usage.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.frame_info.columnconfigure(0, weight=1)
        self.frame_info.columnconfigure(1, weight=1)
        
        # 内容框架
        self.frame_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text_prompt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.label_stats.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 变量框架
        self.frame_variables.pack(fill=tk.X, padx=10, pady=5)
        self.label_variables.pack(padx=5, pady=2, anchor="w")
        
        # 按钮框架
        self.frame_buttons.pack(fill=tk.X, padx=10, pady=(5, 10))
        self.btn_close.pack(side=tk.RIGHT, padx=5)
        self.btn_copy.pack(side=tk.RIGHT, padx=5)
    
    def _bind_events(self):
        """绑定事件"""
        # 绑定关闭快捷键
        self.bind("<Escape>", lambda e: self.destroy())
        
        # 绑定复制快捷键
        self.bind("<Control-c>", lambda e: self._on_copy())
        
        # 窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.destroy)
    
    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        
        parent_x = self.winfo_parent().winfo_x()
        parent_y = self.winfo_parent().winfo_y()
        parent_width = self.winfo_parent().winfo_width()
        parent_height = self.winfo_parent().winfo_height()
        
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _on_copy(self):
        """复制到剪贴板"""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.prompt)
            
            # 临时改变按钮文本
            original_text = self.btn_copy.cget("text")
            self.btn_copy.configure(text="✅ 已复制")
            self.after(1000, lambda: self.btn_copy.configure(text=original_text))
            
            logger.info(f"复制提示词到剪贴板: {self.template_name}")
            
            if self.on_copy:
                self.on_copy(self.template_id)
                
        except Exception as e:
            logger.error(f"复制失败: {e}")
    
    def show(self):
        """显示对话框（模态）"""
        self.wait_window(self)
        return True


# 便捷函数
def show_prompt_preview(parent, template_id: str, template_name: str, prompt: str, 
                       last_modified: str = None, usage_count: int = 0) -> bool:
    """
    显示提示词预览对话框
    
    Args:
        parent: 父窗口
        template_id: 模板ID
        template_name: 模板名称
        prompt: 提示词内容
        last_modified: 最后修改时间
        usage_count: 使用次数
        
    Returns:
        是否成功显示
    """
    try:
        dialog = PromptPreviewDialog(
            parent, template_id, template_name, prompt, 
            last_modified, usage_count
        )
        dialog.show()
        return True
    except Exception as e:
        logger.error(f"显示预览对话框失败: {e}")
        return False