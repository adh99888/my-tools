"""
提示词编辑对话框
编辑和保存模板提示词
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class PromptEditorDialog(tk.Toplevel):
    """提示词编辑对话框"""
    
    def __init__(self, parent, 
                 template_id: str,
                 template_info: Dict[str, Any],
                 prompt_manager,
                 on_save: Optional[Callable] = None,
                 **kwargs):
        """
        初始化编辑对话框
        
        Args:
            parent: 父窗口
            template_id: 模板ID
            template_info: 模板信息
            prompt_manager: 提示词管理器实例
            on_save: 保存回调函数
            **kwargs: 传递给Toplevel的其他参数
        """
        super().__init__(parent, **kwargs)
        
        self.template_id = template_id
        self.template_info = template_info
        self.prompt_manager = prompt_manager
        self.on_save = on_save
        
        # 模板名称和当前提示词
        self.template_name = template_info.get("name", template_id)
        self.current_prompt = template_info.get("prompt", "")
        self.is_enabled = template_info.get("enabled", True)
        
        # 原始提示词（用于重置）
        self.original_prompt = self.current_prompt
        
        # 窗口设置
        self.title(f"提示词编辑 - {self.template_name}")
        self.geometry("700x600")
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
        
        # 初始化状态
        self._update_char_count()
    
    def _create_widgets(self):
        """创建子组件"""
        # 标题框架
        self.frame_title = ttk.Frame(self)
        
        self.label_title = ttk.Label(
            self.frame_title,
            text=f"⚙️ 提示词编辑 - {self.template_name}",
            font=("微软雅黑", 12, "bold")
        )
        
        # 状态框架
        self.frame_status = ttk.Frame(self)
        
        status_text = "✅ 已启用自定义提示词" if self.is_enabled else "❌ 自定义提示词已禁用"
        self.label_status = ttk.Label(
            self.frame_status,
            text=status_text,
            font=("微软雅黑", 10),
            foreground="green" if self.is_enabled else "red"
        )
        
        # 编辑框架
        self.frame_edit = ttk.LabelFrame(self, text="编辑区", padding=10)
        
        # 滚动文本框 - 可编辑
        self.text_prompt = scrolledtext.ScrolledText(
            self.frame_edit,
            wrap=tk.WORD,
            width=80,
            height=15,
            font=("微软雅黑", 10),
            undo=True
        )
        
        # 插入当前提示词
        self.text_prompt.insert("1.0", self.current_prompt)
        
        # 快捷操作框架
        self.frame_quick_actions = ttk.Frame(self)
        
        # 变量菜单
        self.variable_var = tk.StringVar(value="选择变量...")
        self.menu_variables = ttk.OptionMenu(
            self.frame_quick_actions,
            self.variable_var,
            "选择变量...",
            "{document}", "{title}", "{requirements}", "{template}", "{date}",
            command=self._insert_variable
        )
        self.menu_variables.configure(width=15)
        
        self.btn_insert = ttk.Button(
            self.frame_quick_actions,
            text="插入变量",
            command=lambda: self._insert_variable(self.variable_var.get()),
            width=12
        )
        
        self.btn_use_default = ttk.Button(
            self.frame_quick_actions,
            text="使用默认",
            command=self._use_default_prompt,
            width=12
        )
        
        self.btn_format = ttk.Button(
            self.frame_quick_actions,
            text="格式化",
            command=self._format_prompt,
            width=12
        )
        
        # 统计框架
        self.frame_stats = ttk.Frame(self)
        
        self.label_char_count = ttk.Label(
            self.frame_stats,
            text="字符数: 0/2000",
            font=("微软雅黑", 9)
        )
        
        self.label_ai_time = ttk.Label(
            self.frame_stats,
            text="预估AI用时: 0秒",
            font=("微软雅黑", 9),
            foreground="blue"
        )
        
        # 按钮框架
        self.frame_buttons = ttk.Frame(self)
        
        self.btn_save = ttk.Button(
            self.frame_buttons,
            text="💾 保存",
            command=self._on_save,
            style="Accent.TButton"
        )
        
        self.btn_cancel = ttk.Button(
            self.frame_buttons,
            text="取消",
            command=self.destroy
        )
        
        self.btn_reset = ttk.Button(
            self.frame_buttons,
            text="重置",
            command=self._reset_prompt
        )
        
        # 提示框架
        self.frame_tips = ttk.LabelFrame(self, text="编辑提示", padding=10)
        
        tips_text = """提示：
1. 提示词应清晰明确，指导AI进行文档排版
2. 可以使用变量 {document}、{title} 等
3. 字符数建议在500-2000之间
4. 避免使用过于复杂的指令"""
        
        self.label_tips = ttk.Label(
            self.frame_tips,
            text=tips_text,
            font=("微软雅黑", 9),
            justify=tk.LEFT,
            foreground="gray"
        )
    
    def _setup_layout(self):
        """设置布局"""
        # 标题框架
        self.frame_title.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.label_title.pack(pady=5)
        
        # 状态框架
        self.frame_status.pack(fill=tk.X, padx=10, pady=5)
        self.label_status.pack()
        
        # 编辑框架
        self.frame_edit.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text_prompt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 快捷操作框架
        self.frame_quick_actions.pack(fill=tk.X, padx=10, pady=5)
        self.menu_variables.pack(side=tk.LEFT, padx=2)
        self.btn_insert.pack(side=tk.LEFT, padx=2)
        self.btn_use_default.pack(side=tk.LEFT, padx=2)
        self.btn_format.pack(side=tk.LEFT, padx=2)
        
        # 统计框架
        self.frame_stats.pack(fill=tk.X, padx=10, pady=5)
        self.label_char_count.pack(side=tk.LEFT, padx=5)
        self.label_ai_time.pack(side=tk.LEFT, padx=5)
        
        # 提示框架
        self.frame_tips.pack(fill=tk.X, padx=10, pady=5)
        self.label_tips.pack(padx=5, pady=2, anchor="w")
        
        # 按钮框架
        self.frame_buttons.pack(fill=tk.X, padx=10, pady=(5, 10))
        self.btn_cancel.pack(side=tk.RIGHT, padx=5)
        self.btn_reset.pack(side=tk.RIGHT, padx=5)
        self.btn_save.pack(side=tk.RIGHT, padx=5)
    
    def _bind_events(self):
        """绑定事件"""
        # 绑定文本变化事件
        self.text_prompt.bind("<KeyRelease>", lambda e: self._update_char_count())
        
        # 绑定快捷键
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-s>", lambda e: self._on_save())
        self.bind("<Control-r>", lambda e: self._reset_prompt())
        
        # 窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self._confirm_close)
    
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
    
    def _update_char_count(self):
        """更新字符统计"""
        content = self.text_prompt.get("1.0", tk.END).strip()
        char_count = len(content)
        
        # 更新字符数
        self.label_char_count.configure(text=f"字符数: {char_count}/2000")
        
        # 更新AI用时预估（假设每秒处理100字符）
        ai_time = char_count / 100
        self.label_ai_time.configure(text=f"预估AI用时: {ai_time:.1f}秒")
        
        # 根据字符数改变颜色
        if char_count > 2000:
            self.label_char_count.configure(foreground="red")
        elif char_count > 1500:
            self.label_char_count.configure(foreground="orange")
        else:
            self.label_char_count.configure(foreground="black")
    
    def _insert_variable(self, variable: str):
        """插入变量"""
        if variable and variable != "选择变量...":
            self.text_prompt.insert(tk.INSERT, variable)
            self.text_prompt.focus_set()
    
    def _use_default_prompt(self):
        """使用默认提示词"""
        default_prompt = self.prompt_manager.get_default_prompt()
        
        if messagebox.askyesno("确认", "是否使用默认提示词？这将替换当前内容。"):
            self.text_prompt.delete("1.0", tk.END)
            self.text_prompt.insert("1.0", default_prompt)
            self._update_char_count()
    
    def _format_prompt(self):
        """格式化提示词"""
        content = self.text_prompt.get("1.0", tk.END).strip()
        
        # 简单的格式化：确保以【】包裹指令
        if not content.startswith("【"):
            content = f"【{self.template_name}排版指令】{content}"
        
        # 更新文本框
        self.text_prompt.delete("1.0", tk.END)
        self.text_prompt.insert("1.0", content)
        self._update_char_count()
    
    def _reset_prompt(self):
        """重置为原始提示词"""
        if self.current_prompt != self.original_prompt:
            if messagebox.askyesno("确认", "是否重置为原始提示词？"):
                self.text_prompt.delete("1.0", tk.END)
                self.text_prompt.insert("1.0", self.original_prompt)
                self._update_char_count()
    
    def _confirm_close(self):
        """确认关闭"""
        current_content = self.text_prompt.get("1.0", tk.END).strip()
        
        if current_content != self.current_prompt:
            if messagebox.askyesno("确认", "内容已修改，是否保存？"):
                self._on_save()
            else:
                self.destroy()
        else:
            self.destroy()
    
    def _on_save(self):
        """保存提示词"""
        content = self.text_prompt.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showerror("错误", "提示词不能为空")
            return
        
        if len(content) > 2000:
            if not messagebox.askyesno("确认", f"提示词过长 ({len(content)}字符)，建议不超过2000字符。是否继续保存？"):
                return
        
        try:
            # 更新提示词
            success = self.prompt_manager.update_template_prompt(
                self.template_id,
                content,
                self.template_name
            )
            
            if success:
                logger.info(f"保存模板提示词成功: {self.template_name}")
                
                # 更新状态
                self.current_prompt = content
                self.is_enabled = True
                status_text = "✅ 已启用自定义提示词"
                self.label_status.configure(text=status_text, foreground="green")
                
                # 调用回调
                if self.on_save:
                    self.on_save(self.template_id, content)
                
                # 显示成功消息
                messagebox.showinfo("成功", "提示词已保存")
                
                # 关闭窗口
                self.destroy()
                
            else:
                messagebox.showerror("错误", "保存失败")
                
        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def show(self):
        """显示对话框（模态）"""
        self.wait_window(self)
        return self.current_prompt != self.original_prompt


# 便捷函数
def show_prompt_editor(parent, template_id: str, template_info: Dict[str, Any], 
                      prompt_manager, on_save: Optional[Callable] = None) -> bool:
    """
    显示提示词编辑对话框
    
    Args:
        parent: 父窗口
        template_id: 模板ID
        template_info: 模板信息
        prompt_manager: 提示词管理器
        on_save: 保存回调函数
        
    Returns:
        是否成功显示
    """
    try:
        dialog = PromptEditorDialog(
            parent, template_id, template_info, prompt_manager, on_save
        )
        return dialog.show()
    except Exception as e:
        logger.error(f"显示编辑对话框失败: {e}")
        return False