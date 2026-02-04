"""
模板项组件
自定义模板选择项，支持预览和编辑提示词
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class TemplateItemWidget(ttk.Frame):
    """模板项组件类"""
    
    def __init__(self, master, 
                 template_info: Dict[str, Any],
                 on_select: Optional[Callable] = None,
                 on_preview: Optional[Callable] = None,
                 on_edit: Optional[Callable] = None,
                 **kwargs):
        """
        初始化模板项组件
        
        Args:
            master: 父组件
            template_info: 模板信息字典
            on_select: 选择回调函数
            on_preview: 预览回调函数
            on_edit: 编辑回调函数
            **kwargs: 传递给Frame的其他参数
        """
        super().__init__(master, **kwargs)
        
        self.template_info = template_info
        self.on_select = on_select
        self.on_preview = on_preview
        self.on_edit = on_edit
        
        # 模板ID和名称
        self.template_id = template_info.get("id", "")
        self.template_name = template_info.get("name", self.template_id)
        self.description = template_info.get("description", "")
        
        # 是否启用自定义提示词
        self.has_custom_prompt = template_info.get("prompt_enabled", False)
        
        # 状态变量
        self.selected = False
        
        # 创建UI
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
    
    def _create_widgets(self):
        """创建子组件"""
        # 复选框 - 用于选择模板
        self.var_selected = tk.BooleanVar(value=False)
        self.checkbox = ttk.Checkbutton(
            self,
            variable=self.var_selected,
            command=self._on_checkbox_click
        )
        
        # 模板名称标签
        self.label_name = ttk.Label(
            self,
            text=self.template_name,
            font=("微软雅黑", 10)
        )
        
        # 描述标签（可选显示）
        if self.description:
            self.label_desc = ttk.Label(
                self,
                text=self.description,
                font=("微软雅黑", 8),
                foreground="gray"
            )
        else:
            self.label_desc = None
        
        # 预览按钮 👁️
        self.btn_preview = ttk.Button(
            self,
            text="👁️",
            width=3,
            style="Toolbutton.TButton"
        )
        
        # 编辑按钮 ⚙️
        self.btn_edit = ttk.Button(
            self,
            text="⚙️",
            width=3,
            style="Toolbutton.TButton"
        )
        
        # 自定义提示词指示器
        if self.has_custom_prompt:
            self.label_indicator = ttk.Label(
                self,
                text="✏️",
                font=("微软雅黑", 8),
                foreground="green"
            )
        else:
            self.label_indicator = None
    
    def _setup_layout(self):
        """设置布局"""
        # 配置网格权重
        self.columnconfigure(0, weight=0)  # 复选框
        self.columnconfigure(1, weight=1)  # 名称
        self.columnconfigure(2, weight=0)  # 指示器
        self.columnconfigure(3, weight=0)  # 预览按钮
        self.columnconfigure(4, weight=0)  # 编辑按钮
        
        # 放置组件
        self.checkbox.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")
        self.label_name.grid(row=0, column=1, padx=(0, 5), pady=2, sticky="w")
        
        col_index = 2
        
        # 指示器
        if self.label_indicator:
            self.label_indicator.grid(row=0, column=col_index, padx=(0, 5), pady=2, sticky="w")
            col_index += 1
        
        # 预览按钮
        self.btn_preview.grid(row=0, column=col_index, padx=(0, 2), pady=2, sticky="w")
        col_index += 1
        
        # 编辑按钮
        self.btn_edit.grid(row=0, column=col_index, padx=(0, 2), pady=2, sticky="w")
        
        # 描述标签（第二行）
        if self.label_desc:
            self.label_desc.grid(row=1, column=1, columnspan=4, padx=(0, 5), pady=(0, 2), sticky="w")
    
    def _bind_events(self):
        """绑定事件"""
        # 预览按钮事件
        self.btn_preview.bind("<Enter>", self._on_preview_enter)
        self.btn_preview.bind("<Leave>", self._on_button_leave)
        self.btn_preview.bind("<Button-1>", self._on_preview_click)
        
        # 编辑按钮事件
        self.btn_edit.bind("<Enter>", self._on_edit_enter)
        self.btn_edit.bind("<Leave>", self._on_button_leave)
        self.btn_edit.bind("<Button-1>", self._on_edit_click)
        
        # 名称标签也可点击选择
        self.label_name.bind("<Button-1>", self._on_name_click)
        if self.label_desc:
            self.label_desc.bind("<Button-1>", self._on_name_click)
    
    def _on_checkbox_click(self):
        """复选框点击事件"""
        self.selected = self.var_selected.get()
        
        # 更新视觉状态
        self._update_visual_state()
        
        # 调用回调函数
        if self.on_select:
            self.on_select(self.template_id, self.selected)
    
    def _on_name_click(self, event):
        """名称标签点击事件"""
        # 切换选择状态
        self.selected = not self.selected
        self.var_selected.set(self.selected)
        
        # 更新视觉状态
        self._update_visual_state()
        
        # 调用回调函数
        if self.on_select:
            self.on_select(self.template_id, self.selected)
    
    def _on_preview_enter(self, event):
        """预览按钮鼠标进入"""
        self.btn_preview.configure(style="Accent.TButton")
        
        # 显示Tooltip
        self.btn_preview.tooltip_text = "预览此模板的提示词"
        self._show_tooltip(event, "预览此模板的提示词")
    
    def _on_edit_enter(self, event):
        """编辑按钮鼠标进入"""
        self.btn_edit.configure(style="Accent.TButton")
        
        # 显示Tooltip
        self.btn_edit.tooltip_text = "编辑此模板的提示词"
        self._show_tooltip(event, "编辑此模板的提示词")
    
    def _on_button_leave(self, event):
        """按钮鼠标离开"""
        event.widget.configure(style="Toolbutton.TButton")
        self._hide_tooltip()
    
    def _on_preview_click(self, event):
        """预览按钮点击"""
        logger.info(f"预览模板: {self.template_name}")
        
        if self.on_preview:
            self.on_preview(self.template_id)
    
    def _on_edit_click(self, event):
        """编辑按钮点击"""
        logger.info(f"编辑模板: {self.template_name}")
        
        if self.on_edit:
            self.on_edit(self.template_id)
    
    def _show_tooltip(self, event, text: str):
        """显示Tooltip"""
        # 简单实现：在按钮上显示文本
        widget = event.widget
        widget.configure(text=f"{text[:10]}...")
    
    def _hide_tooltip(self):
        """隐藏Tooltip"""
        # 恢复按钮文本
        if self.btn_preview.cget("text") != "👁️":
            self.btn_preview.configure(text="👁️")
        
        if self.btn_edit.cget("text") != "⚙️":
            self.btn_edit.configure(text="⚙️")
    
    def _update_visual_state(self):
        """更新视觉状态"""
        if self.selected:
            self.configure(style="Selected.TFrame")
            self.label_name.configure(style="Selected.TLabel")
        else:
            self.configure(style="TFrame")
            self.label_name.configure(style="TLabel")
    
    def select(self, selected: bool = True):
        """
        选择或取消选择模板
        
        Args:
            selected: 是否选择
        """
        self.selected = selected
        self.var_selected.set(selected)
        self._update_visual_state()
    
    def is_selected(self) -> bool:
        """
        检查是否被选中
        
        Returns:
            是否选中
        """
        return self.selected
    
    def get_template_id(self) -> str:
        """
        获取模板ID
        
        Returns:
            模板ID
        """
        return self.template_id
    
    def get_template_name(self) -> str:
        """
        获取模板名称
        
        Returns:
            模板名称
        """
        return self.template_name
    
    def update_template_info(self, template_info: Dict[str, Any]):
        """
        更新模板信息
        
        Args:
            template_info: 新的模板信息
        """
        self.template_info = template_info
        self.template_name = template_info.get("name", self.template_id)
        self.description = template_info.get("description", "")
        
        # 更新名称标签
        self.label_name.configure(text=self.template_name)
        
        # 更新描述标签
        if hasattr(self, 'label_desc') and self.label_desc:
            if self.description:
                self.label_desc.configure(text=self.description)
            else:
                self.label_desc.grid_forget()
                self.label_desc = None
        elif self.description:
            # 创建新的描述标签
            self.label_desc = ttk.Label(
                self,
                text=self.description,
                font=("微软雅黑", 8),
                foreground="gray"
            )
            self.label_desc.grid(row=1, column=1, columnspan=4, padx=(0, 5), pady=(0, 2), sticky="w")
            self.label_desc.bind("<Button-1>", self._on_name_click)
        
        # 更新自定义提示词指示器
        has_custom_prompt = template_info.get("prompt_enabled", False)
        if has_custom_prompt != self.has_custom_prompt:
            self.has_custom_prompt = has_custom_prompt
            
            if has_custom_prompt:
                if not hasattr(self, 'label_indicator') or not self.label_indicator:
                    self.label_indicator = ttk.Label(
                        self,
                        text="✏️",
                        font=("微软雅黑", 8),
                        foreground="green"
                    )
                    # 重新布局
                    self._rearrange_layout()
            else:
                if hasattr(self, 'label_indicator') and self.label_indicator:
                    self.label_indicator.grid_forget()
                    self.label_indicator = None
                    # 重新布局
                    self._rearrange_layout()
    
    def _rearrange_layout(self):
        """重新排列布局"""
        # 移除所有组件
        for widget in self.grid_slaves():
            widget.grid_forget()
        
        # 重新放置
        self._setup_layout()
        
        # 重新绑定事件
        self._bind_events()
        
        # 更新视觉状态
        self._update_visual_state()
    
    def enable_preview_button(self, enabled: bool = True):
        """
        启用或禁用预览按钮
        
        Args:
            enabled: 是否启用
        """
        state = "normal" if enabled else "disabled"
        self.btn_preview.configure(state=state)
    
    def enable_edit_button(self, enabled: bool = True):
        """
        启用或禁用编辑按钮
        
        Args:
            enabled: 是否启用
        """
        state = "normal" if enabled else "disabled"
        self.btn_edit.configure(state=state)


# 样式配置函数
def configure_template_item_styles(root):
    """
    配置模板项组件的样式
    
    Args:
        root: Tk根窗口或样式对象
    """
    style = ttk.Style(root)
    
    # 选中状态的样式
    style.configure("Selected.TFrame", background="#e6f3ff")
    style.configure("Selected.TLabel", background="#e6f3ff")
    
    # 工具按钮样式
    style.configure("Toolbutton.TButton", padding=2)
    style.map("Toolbutton.TButton",
              background=[("active", "#e0e0e0")])
    
    # 强调按钮样式（悬停时）
    style.configure("Accent.TButton", padding=2, background="#4CAF50")
    style.map("Accent.TButton",
              background=[("active", "#45a049")])