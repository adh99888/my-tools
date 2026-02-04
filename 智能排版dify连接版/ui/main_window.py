"""
主窗口模块
应用程序的主界面和控制器
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog, Menu
import logging
import threading
import queue
import os
import re
from pathlib import Path
from datetime import datetime

from ui.widgets.template_item_widget import TemplateItemWidget
from ui.dialogs.prompt_preview_dialog import show_prompt_preview
from ui.dialogs.prompt_editor_dialog import show_prompt_editor
from core.prompt_manager import get_prompt_manager
from utils.title_extractor import get_title_extractor
from ui.dialogs import ModelConfigDialog, TemplateEditorDialog

logger = logging.getLogger(__name__)


class MainWindow:
    """主窗口类"""

    def __init__(
        self, root, config_manager, model_manager, template_manager, document_processor
    ):
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
        self.prompt_manager = get_prompt_manager()
        self.title_extractor = get_title_extractor()
        self.current_template_id = None

        # 窗口设置
        self.root.title("专业文档智能排版系统 v2.0 - 多模型支持")
        # 减小窗口高度，使按钮更容易访问
        self.root.geometry("1200x750")

        # 当前状态
        self.is_processing = False
        self.current_file = ""
        self.original_title = ""

        # 消息队列
        self.message_queue = queue.Queue()

        # 创建菜单栏
        self._create_menus()

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

    def _create_menus(self):
        """创建菜单栏"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开文档", command=self.load_file)
        file_menu.add_command(label="保存Word", command=self.save_as_word)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 功能设置菜单
        features_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="功能设置", menu=features_menu)

        # 创建功能开关变量
        self.prompt_ui_var = tk.BooleanVar(
            value=self.prompt_manager.is_feature_enabled("prompt_ui")
        )
        self.auto_title_var = tk.BooleanVar(
            value=self.prompt_manager.is_feature_enabled("auto_title")
        )
        self.complex_title_var = tk.BooleanVar(
            value=self.prompt_manager.is_feature_enabled("complex_title")
        )

        features_menu.add_checkbutton(
            label="启用提示词UI",
            variable=self.prompt_ui_var,
            command=self._toggle_prompt_ui,
        )

        features_menu.add_checkbutton(
            label="启用标题自动提取",
            variable=self.auto_title_var,
            command=self._toggle_auto_title,
        )

        features_menu.add_checkbutton(
            label="启用复杂标题提取",
            variable=self.complex_title_var,
            command=self._toggle_complex_title,
        )

        features_menu.add_separator()
        features_menu.add_command(label="打开配置文件", command=self._open_config_file)

    def _toggle_prompt_ui(self):
        """切换提示词UI功能"""
        current = self.prompt_manager.is_feature_enabled("prompt_ui")
        self.prompt_manager.config["features"]["prompt_ui"] = not current
        self.prompt_manager.save_config()

        # 更新UI
        self._load_template_widgets()

    def _toggle_auto_title(self):
        """切换标题自动提取功能"""
        current = self.prompt_manager.is_feature_enabled("auto_title")
        self.prompt_manager.config["features"]["auto_title"] = not current
        self.prompt_manager.save_config()

    def _toggle_complex_title(self):
        """切换复杂标题提取功能"""
        current = self.prompt_manager.is_feature_enabled("complex_title")
        self.prompt_manager.config["features"]["complex_title"] = not current
        self.prompt_manager.save_config()

    def _open_config_file(self):
        """打开配置文件"""
        config_path = self.prompt_manager.get_config_path()
        if os.path.exists(config_path):
            if os.name == "nt":  # Windows
                os.startfile(config_path)
            elif os.name == "posix":  # macOS or Linux
                import subprocess

                subprocess.call(["open", config_path])
        else:
            messagebox.showwarning("警告", f"配置文件不存在: {config_path}")

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

        title_label = ttk.Label(
            title_frame,
            text="🤖 专业文档智能排版系统 v2.0",
            font=("Microsoft YaHei", 18, "bold"),
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            title_frame,
            text="多模型AI智能润色 + 动态模板编辑 + 一键导出",
            font=("Microsoft YaHei", 11),
            foreground="#666",
        )
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

        ttk.Button(
            file_frame, text="📂 选择文档", command=self.load_file, width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            file_frame, text="📋 粘贴文本", command=self.paste_text, width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            file_frame,
            text="🚀 智能生成",
            command=self.open_smart_generate_dialog,
            width=12,
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.file_label = ttk.Label(file_frame, text="未选择文档", foreground="#0066cc")
        self.file_label.pack(side=tk.LEFT, padx=(10, 0))

        # 标题输入
        title_frame = ttk.Frame(input_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="文档标题:", font=("Microsoft YaHei", 10)).pack(
            side=tk.LEFT
        )
        self.title_entry = ttk.Entry(title_frame, font=("Microsoft YaHei", 10))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # 原文内容
        input_header_frame = ttk.Frame(input_frame)
        input_header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            input_header_frame, text="原文内容:", font=("Microsoft YaHei", 10, "bold")
        ).pack(side=tk.LEFT)

        # 输入字数统计标签
        self.input_char_count_label = ttk.Label(
            input_header_frame,
            text="字数: 0",
            font=("Microsoft YaHei", 9),
            foreground="#666",
        )
        self.input_char_count_label.pack(side=tk.RIGHT)

        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=12,  # 减小高度，使布局更紧凑
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8f9fa",
            relief=tk.SUNKEN,
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 绑定内容变化事件
        self.input_text.bind("<<Modified>>", self._on_content_modified)

        # 右侧：处理区 - 重新组织布局，使按钮更紧凑
        control_frame = ttk.LabelFrame(right_panel, text="⚙️ 处理控制", padding="10")
        control_frame.pack(fill=tk.BOTH, expand=True)

        # 创建垂直布局容器
        control_container = ttk.Frame(control_frame)
        control_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 第一行：模型选择和模板选择
        top_row_frame = ttk.Frame(control_container)
        top_row_frame.pack(fill=tk.X, pady=(0, 10))

        # 模型选择（左侧）
        model_frame = ttk.LabelFrame(top_row_frame, text="🤖 AI模型", padding="5")
        model_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.model_var = tk.StringVar(value=self.model_manager.current_model_id)
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=self.model_manager.get_model_list(),
            state="readonly",
            width=25,
        )
        self.model_combo.pack(fill=tk.X, padx=5, pady=2)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_changed)

        # 模板选择（右侧）- 简化版本
        template_frame = ttk.LabelFrame(top_row_frame, text="🎨 模板", padding="5")
        template_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.template_var = tk.StringVar()
        template_list = self.template_manager.get_template_list()
        self.template_combo = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            values=template_list,
            state="readonly",
            width=25,
        )
        self.template_combo.pack(fill=tk.X, padx=5, pady=2)
        self.template_combo.bind("<<ComboboxSelected>>", self.on_template_combo_changed)

        # 第二行：处理选项
        options_frame = ttk.LabelFrame(
            control_container, text="📝 处理选项", padding="5"
        )
        options_frame.pack(fill=tk.X, pady=(0, 10))

        options_inner_frame = ttk.Frame(options_frame)
        options_inner_frame.pack(fill=tk.X, padx=5, pady=2)

        self.auto_correct_var = tk.BooleanVar(value=True)
        self.keep_structure_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            options_inner_frame, text="自动纠错", variable=self.auto_correct_var
        ).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(
            options_inner_frame, text="保持结构", variable=self.keep_structure_var
        ).pack(side=tk.LEFT)

        # 第三行：主要操作按钮（两行布局）
        button_container = ttk.Frame(control_container)
        button_container.pack(fill=tk.X, pady=(0, 10))

        # 第一行按钮
        button_row1 = ttk.Frame(button_container)
        button_row1.pack(fill=tk.X, pady=(0, 5))

        self.refresh_btn = ttk.Button(
            button_row1, text="🔄 刷新", command=self.refresh_all, width=14
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.process_btn = ttk.Button(
            button_row1, text="🚀 AI智能处理", command=self.start_processing, width=14
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(
            button_row1,
            text="⏹️ 停止",
            command=self.stop_processing,
            width=14,
            state="disabled",
        )
        self.stop_btn.pack(side=tk.LEFT)

        # 第二行按钮
        button_row2 = ttk.Frame(button_container)
        button_row2.pack(fill=tk.X)

        self.save_btn = ttk.Button(
            button_row2,
            text="💾 保存Word文档",
            command=self.save_as_word,
            width=14,
            state="disabled",
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 智能生成按钮
        self.smart_gen_btn = ttk.Button(
            button_row2,
            text="✨ 智能生成",
            command=self.open_smart_generate_dialog,
            width=14,
        )
        self.smart_gen_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 模型配置按钮
        self.model_config_btn = ttk.Button(
            button_row2,
            text="⚙️ 模型配置",
            command=self.configure_models,
            width=14,
        )
        self.model_config_btn.pack(side=tk.LEFT)

        # 进度显示
        self.progress = ttk.Progressbar(control_container, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(5, 0))

        # 状态信息显示
        self.control_status_label = ttk.Label(
            control_container,
            text="就绪",
            font=("Microsoft YaHei", 9),
            foreground="#666",
        )
        self.control_status_label.pack(fill=tk.X, pady=(5, 0))

        # 处理结果
        result_frame = ttk.LabelFrame(right_panel, text="✨ 处理结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 输出区域头部
        output_header_frame = ttk.Frame(result_frame)
        output_header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            output_header_frame, text="排版结果:", font=("Microsoft YaHei", 10, "bold")
        ).pack(side=tk.LEFT)

        # 输出字数统计标签
        self.output_char_count_label = ttk.Label(
            output_header_frame,
            text="字数: 0",
            font=("Microsoft YaHei", 9),
            foreground="#666",
        )
        self.output_char_count_label.pack(side=tk.RIGHT)

        self.output_text = scrolledtext.ScrolledText(
            result_frame, height=20, wrap=tk.WORD, font=("Consolas", 10), bg="#f8f9fa"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # 统计信息
        self.stats_label = ttk.Label(result_frame, text="", font=("Microsoft YaHei", 9))
        self.stats_label.pack(fill=tk.X, pady=(5, 0))

        # 绑定输出内容变化事件
        self.output_text.bind("<<Modified>>", self._on_output_modified)

    def _create_template_selection_area(self, parent):
        """创建模板选择区域（使用新组件）"""
        # 创建框架
        template_frame = ttk.LabelFrame(parent, text="🎨 选择模板", padding="10")
        template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 滚动框架
        self.template_canvas = tk.Canvas(template_frame, height=150)
        self.template_scrollbar = ttk.Scrollbar(
            template_frame, orient="vertical", command=self.template_canvas.yview
        )
        self.template_scrollable_frame = ttk.Frame(self.template_canvas)

        # 配置滚动
        self.template_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.template_canvas.configure(
                scrollregion=self.template_canvas.bbox("all")
            ),
        )

        self.template_canvas.create_window(
            (0, 0), window=self.template_scrollable_frame, anchor="nw"
        )
        self.template_canvas.configure(yscrollcommand=self.template_scrollbar.set)

        # 加载模板
        self.template_widgets = {}
        self._load_template_widgets()

        # 布局
        self.template_canvas.pack(side="left", fill="both", expand=True)
        self.template_scrollbar.pack(side="right", fill="y")

    def _load_template_widgets(self):
        """加载模板组件"""
        # 清空现有组件
        for widget in self.template_scrollable_frame.winfo_children():
            widget.destroy()
        self.template_widgets.clear()

        # 获取所有模板
        template_list = self.template_manager.get_template_list()

        for i, template_id in enumerate(template_list):
            # 获取模板信息
            template_config = self.template_manager.get_template(template_id)
            template_info = {
                "id": template_id,
                "name": template_config.get("name", template_id),
                "description": template_config.get("description", ""),
                "prompt_enabled": False,  # 初始值，稍后更新
            }

            # 从提示词管理器获取更多信息
            prompt_info = self.prompt_manager.get_template_info(template_id)
            if prompt_info:
                template_info.update(
                    {
                        "prompt_enabled": prompt_info.get("enabled", False),
                        "last_modified": prompt_info.get("last_modified", ""),
                        "usage_count": prompt_info.get("usage_count", 0),
                    }
                )

            # 创建模板项组件
            widget = TemplateItemWidget(
                self.template_scrollable_frame,
                template_info,
                on_select=self._on_template_selected,
                on_preview=self._on_preview_prompt,
                on_edit=self._on_edit_prompt,
            )

            widget.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            self.template_widgets[template_id] = widget

        # 配置样式
        from ui.widgets.template_item_widget import configure_template_item_styles

        configure_template_item_styles(self.root)

    def _on_template_selected(self, template_id, selected):
        """模板选择回调"""
        if selected:
            # 取消选择其他模板
            for tid, widget in self.template_widgets.items():
                if tid != template_id and widget.is_selected():
                    widget.select(False)

            # 设置当前模板
            self.current_template_id = template_id
            self.template_manager.switch_template(template_id)

            # 更新UI
            self._update_template_parameters(template_id)

            # 触发标题自动提取（如果启用）
            if self.prompt_manager.is_auto_title_enabled():
                self._auto_extract_title()
        else:
            # 如果取消选择当前模板，清除当前模板
            if self.current_template_id == template_id:
                self.current_template_id = None

    def _on_preview_prompt(self, template_id):
        """预览提示词回调"""
        if not self.prompt_manager.is_feature_enabled("prompt_ui"):
            return

        # 获取提示词信息
        template_info = self.prompt_manager.get_template_info(template_id)
        if not template_info:
            return

        # 显示预览对话框
        show_prompt_preview(
            self.root,
            template_id,
            template_info.get("name", template_id),
            template_info.get("prompt", ""),
            template_info.get("last_modified", ""),
            template_info.get("usage_count", 0),
        )

    def _on_edit_prompt(self, template_id):
        """编辑提示词回调"""
        if not self.prompt_manager.is_feature_enabled("prompt_ui"):
            return

        # 获取模板信息
        template_info = self.prompt_manager.get_template_info(template_id)
        if not template_info:
            # 如果没有模板信息，创建基础信息
            template_config = self.template_manager.get_template(template_id)
            template_info = {
                "id": template_id,
                "name": template_config.get("name", template_id),
                "description": template_config.get("description", ""),
                "prompt": self.prompt_manager.get_default_prompt(),
                "enabled": False,
            }

        # 显示编辑对话框
        show_prompt_editor(
            self.root,
            template_id,
            template_info,
            self.prompt_manager,
            on_save=self._on_prompt_saved,
        )

    def _on_prompt_saved(self, template_id, new_prompt):
        """提示词保存回调"""
        # 更新对应组件的指示器
        if template_id in self.template_widgets:
            widget = self.template_widgets[template_id]
            template_info = self.prompt_manager.get_template_info(template_id)
            if template_info:
                widget.update_template_info(template_info)

        logger.info(f"提示词已保存: {template_id}")

    def _auto_extract_title(self):
        """自动提取标题"""
        if not self.prompt_manager.is_auto_title_enabled():
            return

        # 获取当前内容
        content = self.input_text.get("1.0", tk.END).strip()
        if not content:
            return

        # 检查标题框是否已有用户输入
        current_title = self.title_entry.get().strip()
        if current_title:  # 用户已手动输入，不自动覆盖
            return

        # 使用提取器提取标题
        use_complex = self.prompt_manager.is_complex_title_enabled()
        title = self.title_extractor.auto_extract_title(content, use_complex)

        if title:
            # 更新标题框
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, title)
            logger.info(f"自动提取标题: {title}")

    def _update_template_parameters(self, template_id):
        """更新模板参数设置"""
        # 清空当前参数设置
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        # 获取模板配置
        template_config = self.template_manager.get_template(template_id)
        if not template_config:
            no_params_label = ttk.Label(self.param_frame, text="此模板无额外参数")
            no_params_label.pack(pady=10)
            return

        row = 0

        # 添加字体选择
        if "body" in template_config and "font_name_cn" in template_config["body"]:
            font_label = ttk.Label(self.param_frame, text="字体:")
            font_label.grid(row=row, column=0, padx=5, pady=2, sticky="w")

            font_value = ttk.Label(
                self.param_frame, text=template_config["body"]["font_name_cn"]
            )
            font_value.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1

        # 添加字号选择
        if "body" in template_config and "font_size" in template_config["body"]:
            size_label = ttk.Label(self.param_frame, text="字号:")
            size_label.grid(row=row, column=0, padx=5, pady=2, sticky="w")

            size_value = ttk.Label(
                self.param_frame, text=str(template_config["body"]["font_size"])
            )
            size_value.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1

        # 添加行距设置
        if "body" in template_config and "line_spacing" in template_config["body"]:
            spacing_label = ttk.Label(self.param_frame, text="行距:")
            spacing_label.grid(row=row, column=0, padx=5, pady=2, sticky="w")

            spacing_value = ttk.Label(
                self.param_frame, text=str(template_config["body"]["line_spacing"])
            )
            spacing_value.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            row += 1

        # 如果没有参数，显示提示
        if row == 0:
            no_params_label = ttk.Label(self.param_frame, text="此模板无额外参数")
            no_params_label.grid(row=0, column=0, padx=5, pady=10, columnspan=2)

    def _on_content_modified(self, event=None):
        """文档内容变化事件"""
        # 更新输入字数统计
        content = self.input_text.get("1.0", tk.END).strip()
        char_count = len(content)
        self.input_char_count_label.config(text=f"字数: {char_count}")

        if self.prompt_manager.is_auto_title_enabled():
            self._auto_extract_title()
        # 重置修改标志
        self.input_text.edit_modified(False)

    def _on_output_modified(self, event=None):
        """输出内容变化事件"""
        # 更新输出字数统计
        content = self.output_text.get("1.0", tk.END).strip()
        char_count = len(content)
        self.output_char_count_label.config(text=f"字数: {char_count}")
        # 重置修改标志
        self.output_text.edit_modified(False)

    def get_current_content(self):
        """获取当前内容"""
        return self.input_text.get("1.0", tk.END).strip()

    def create_model_widgets(self, parent):
        """创建模型管理页面的控件"""
        # 主框架
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame, text="🤖 AI模型配置管理", font=("Microsoft YaHei", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))

        # 说明文本
        info_text = """💡 功能介绍：
1. 支持多个国产AI模型切换
2. 可以根据文档长度选择合适的模型
3. 长文档建议使用硅基流动或通义千问
4. 短文档使用DeepSeek Chat更快速"""

        info_label = ttk.Label(
            main_frame,
            text=info_text,
            font=("Microsoft YaHei", 10),
            background="#f0f8ff",
            padding=10,
            relief=tk.RIDGE,
            wraplength=800,
            justify=tk.LEFT,
        )
        info_label.pack(fill=tk.X, pady=(0, 15))

        # 模型列表
        list_frame = ttk.LabelFrame(main_frame, text="📋 可用模型列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "model", "max_tokens", "provider")
        self.model_config_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=12
        )

        # 设置列
        self.model_config_tree.heading("id", text="模型ID")
        self.model_config_tree.heading("name", text="显示名称")
        self.model_config_tree.heading("model", text="模型名称")
        self.model_config_tree.heading("max_tokens", text="最大长度")
        self.model_config_tree.heading("provider", text="提供商")

        self.model_config_tree.column("id", width=100)
        self.model_config_tree.column("name", width=150)
        self.model_config_tree.column("model", width=150)
        self.model_config_tree.column("max_tokens", width=80)
        self.model_config_tree.column("provider", width=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.model_config_tree.yview
        )
        self.model_config_tree.configure(yscroll=scrollbar.set)

        self.model_config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            button_frame, text="⚙️ 配置模型", command=self.configure_models, width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="🔄 刷新列表", command=self.refresh_model_list, width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="📊 查看API用量", command=self.show_api_usage, width=20
        ).pack(side=tk.LEFT)

        # 加载模型列表
        self.refresh_model_list()

    def create_template_widgets(self, parent):
        """创建模板管理页面的控件"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame, text="🎨 模板管理系统", font=("Microsoft YaHei", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(
            button_frame,
            text="🆕 创建新模板",
            command=self.create_new_template,
            width=20,
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="✏️ 编辑模板", command=self.edit_template, width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="💾 另存为模板", command=self.save_as_template, width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="🗑️ 删除模板", command=self.delete_template, width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame,
            text="🔄 刷新列表",
            command=self.load_templates_to_tree,
            width=20,
        ).pack(side=tk.RIGHT)

        # 模板列表和详情
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 模板列表
        list_frame = ttk.LabelFrame(content_frame, text="📁 可用模板", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        columns = ("name", "description", "font")
        self.template_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=15
        )

        # 设置列
        self.template_tree.heading("name", text="模板名称")
        self.template_tree.heading("description", text="描述")
        self.template_tree.heading("font", text="主要字体")

        self.template_tree.column("name", width=150)
        self.template_tree.column("description", width=250)
        self.template_tree.column("font", width=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.template_tree.yview
        )
        self.template_tree.configure(yscroll=scrollbar.set)

        self.template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.template_tree.bind("<<TreeviewSelect>>", self.on_template_selected)

        # 模板详情
        detail_frame = ttk.LabelFrame(content_frame, text="🔍 模板详情", padding="10")
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.template_detail = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#f5f5f5", height=20
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
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)

        # 重置文件选择状态
        self.current_file = ""
        self.file_label.config(text="未选择文档", foreground="#0066cc")

        # 清空标题输入框
        self.title_entry.delete(0, tk.END)
        self.original_title = ""

        # 重置统计数据
        self.stats_label.config(text="")

        # 禁用保存按钮
        self.save_btn.config(state="disabled")

        # 重置按钮状态
        self.process_btn.config(state="normal", text="🚀 AI智能处理")
        self.stop_btn.config(state="disabled")
        self.refresh_btn.config(state="normal")

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
        if hasattr(self.doc_processor, "stop_processing"):
            self.doc_processor.stop_processing()

        # 禁用停止按钮，启用处理按钮
        self.stop_btn.config(state="disabled")
        self.process_btn.config(state="normal", text="🚀 AI智能处理")
        self.refresh_btn.config(state="normal")

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
                    # 更新控制区域状态
                    self.control_status_label.config(
                        text=f"已选择模型: {model_config.get('name', model_id)}"
                    )

    def on_template_combo_changed(self, event=None):
        """模板选择框变化"""
        template_id = self.template_var.get()
        if template_id and template_id != self.current_template_id:
            self.current_template_id = template_id
            self.template_manager.switch_template(template_id)
            # 更新控制区域状态
            self.control_status_label.config(text=f"已选择模板: {template_id}")

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

            if "body" in template:
                body = template["body"]
                preview += f"字体: {body.get('font_name_cn', '宋体')} / {body.get('font_name_en', 'Times New Roman')}\n"
                preview += f"字号: {body.get('font_size', '12')}pt\n"
                preview += f"行距: {body.get('line_spacing', '1.5')}\n"

            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview)

    def load_file(self):
        """加载文件"""
        filetypes = [
            ("所有文档", "*.txt;*.docx;*.pdf"),
            ("文本文件", "*.txt"),
            ("Word文档", "*.docx"),
            ("PDF文件", "*.pdf"),
        ]

        filename = filedialog.askopenfilename(title="选择文档", filetypes=filetypes)

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
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", content)

                # 更新统计
                char_count = len(content)
                self.stats_label.config(text=f"📊 原文: {char_count} 字符")
                self.queue_message(
                    "info", f"✅ 已加载文档: {os.path.basename(filename)}"
                )
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
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", text)
                self.file_label.config(text="📋 已粘贴剪贴板内容")
                self.queue_message("info", "✅ 已粘贴剪贴板内容")

                # 自动提取标题
                title = self.doc_processor.extract_title(text)
                if title:
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.insert(0, title)
        except tk.TclError:
            self.queue_message("warning", "剪贴板为空或内容无法获取")

    def start_processing(self):
        """开始处理文档"""
        if self.is_processing:
            self.queue_message("warning", "正在处理中，请稍候...")
            return

        # 获取内容
        content = self.input_text.get("1.0", tk.END).strip()
        if not content:
            self.queue_message("warning", "请输入或加载要处理的文档内容")
            return

        # 检查模型配置
        model_id = self.model_var.get()
        validation = self.model_manager.validate_model_config(model_id)
        if not validation["status"]:
            self.queue_message("error", f"模型配置验证失败: {validation['message']}")
            return

        # 检查模板选择
        if not self.current_template_id:
            self.queue_message("warning", "请先选择一个模板")
            return

        # 设置处理状态
        self.is_processing = True

        # 按钮状态管理（根据集成点2）
        self.process_btn.config(state="disabled", text="处理中...")
        self.stop_btn.config(state="normal")  # 启用停止按钮
        self.refresh_btn.config(state="disabled")  # 禁用刷新按钮
        self.save_btn.config(state="disabled")  # 禁用保存按钮

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
                    self.process_btn.config(state="normal", text="🚀 AI智能处理")
                    self.stop_btn.config(state="disabled")  # 禁用停止按钮
                    self.refresh_btn.config(state="normal")  # 启用刷新按钮
                    self.save_btn.config(state="normal")  # 启用保存按钮（如果有结果）

                    if success:
                        self.output_text.delete("1.0", tk.END)
                        self.output_text.insert("1.0", result)

                        # 更新统计
                        stats = self.doc_processor.get_stats(content, result)
                        self.stats_label.config(
                            text=f"📊 统计: 原文{stats['original_length']}字 → 结果{stats['processed_length']}字 ({stats['change_rate']:+.1f}%)"
                        )

                        model_config = self.model_manager.get_current_model_config()
                        model_name = (
                            model_config.get("name", model_id)
                            if model_config
                            else model_id
                        )

                        self.queue_message(
                            "success",
                            f"✅ 处理完成！\n"
                            f"🤖 使用模型: {model_name}\n"
                            f"🎨 使用模板: {self.current_template_id}",
                        )
                    else:
                        self.queue_message("error", f"❌ {result}")

                self.root.after(0, update_result)

            except Exception as e:
                logger.error(f"处理线程异常: {str(e)}")

                def handle_error(error):
                    self.progress.stop()
                    self.is_processing = False

                    # 按钮状态管理（错误情况）
                    self.process_btn.config(state="normal", text="🚀 AI智能处理")
                    self.stop_btn.config(state="disabled")  # 禁用停止按钮
                    self.refresh_btn.config(state="normal")  # 启用刷新按钮
                    self.save_btn.config(state="disabled")  # 禁用保存按钮

                    self.queue_message("error", f"处理过程中发生错误: {str(error)}")

                self.root.after(0, handle_error, e)

        thread = threading.Thread(target=processing_thread)
        thread.daemon = True
        thread.start()

    def save_as_word(self):
        """保存为Word文档（修复路径问题）"""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            self.queue_message("warning", "没有可保存的内容，请先处理文档")
            return

        title = self.title_entry.get().strip() or self.original_title or "文档标题"

        if not self.current_template_id:
            self.queue_message("warning", "请先选择一个模板")
            return

        template_name = self.current_template_id

        # 选择保存位置
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{safe_title}_{timestamp}.docx"

        filename = filedialog.asksaveasfilename(
            defaultextension=".docx",
            initialfile=default_name,
            filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")],
            title="保存Word文档",
        )

        if not filename:
            return

        try:
            # 保存文档 - 传递用户选择的文件路径
            success, file_path = self.doc_processor.save_as_word(
                content,
                title,
                template_name,
                filename,  # 添加这个参数，传递用户选择的路径
            )

            if success:
                template = self.template_manager.get_template(template_name)
                template_display = (
                    template.get("name", template_name) if template else template_name
                )
                model_config = self.model_manager.get_current_model_config()
                model_name = (
                    model_config.get("name", self.model_var.get())
                    if model_config
                    else self.model_var.get()
                )

                # 显示文件保存位置
                file_size = (
                    os.path.getsize(file_path) if os.path.exists(file_path) else "未知"
                )
                file_dir = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)

                self.queue_message(
                    "success",
                    f"✅ 文档保存成功！\n"
                    f"📁 文件: {file_name}\n"
                    f"📂 位置: {file_dir}\n"
                    f"📏 大小: {file_size} 字节\n"
                    f"🤖 模型: {model_name}\n"
                    f"🎨 模板: {template_display}",
                )

                # 打开文件所在目录（可选）
                if messagebox.askyesno(
                    "保存成功", f"文档已保存到:\n{file_path}\n\n是否打开所在目录？"
                ):
                    try:
                        # Windows
                        if os.name == "nt":
                            os.startfile(file_dir)
                        # MacOS
                        elif os.name == "posix":
                            import subprocess

                            subprocess.call(["open", file_dir])
                    except:
                        pass
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
            self.model_config_tree.insert(
                "",
                "end",
                values=(
                    info["id"],
                    info["name"],
                    info["model"],
                    info["max_tokens"],
                    info["provider"],
                ),
            )

    def configure_models(self):
        """配置模型"""
        dialog = ModelConfigDialog(
            self.root,
            self.model_manager.model_configs,
            self.model_manager.current_model_id,
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
            self.model_combo["values"] = self.model_manager.get_model_list()

            # 刷新模型列表
            self.refresh_model_list()

            self.queue_message("success", "✅ 模型配置已更新")

    def show_api_usage(self):
        """显示API用量信息"""
        messagebox.showinfo(
            "API用量提示",
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
            "超长文档(>15000字) → 通义千问/百川",
        )

    def load_templates_to_tree(self):
        """加载模板到树形列表"""
        # 重新加载模板
        self.config_manager.load_templates()

        for item in self.template_tree.get_children():
            self.template_tree.delete(item)

        template_info = self.template_manager.get_template_info()
        for info in template_info:
            self.template_tree.insert(
                "",
                "end",
                iid=info["id"],
                values=(info["name"], info["description"], info["body_font"]),
            )

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
        if "page_setup" in template_data:
            page = template_data["page_setup"]
            detail_text += f"  纸张: {page.get('paper_size', 'A4')}\n"
            detail_text += f"  边距: 上{page.get('margin_top', 0)}pt, "
            detail_text += f"下{page.get('margin_bottom', 0)}pt, "
            detail_text += f"左{page.get('margin_left', 0)}pt, "
            detail_text += f"右{page.get('margin_right', 0)}pt\n\n"

        detail_text += "字体设置:\n"
        if "body" in template_data:
            body = template_data["body"]
            detail_text += f"  正文: 中文{body.get('font_name_cn', '')}, "
            detail_text += f"英文{body.get('font_name_en', '')}\n"
            detail_text += f"  字号: {body.get('font_size', '')}pt\n"
            detail_text += f"  行距: {body.get('line_spacing', '')}\n\n"

        detail_text += "标题设置:\n"
        for i in range(1, 4):
            heading_key = f"heading{i}"
            if heading_key in template_data:
                heading = template_data[heading_key]
                detail_text += f"  标题{i}: {heading.get('font_size', '')}pt, "
                detail_text += f"{heading.get('font_name_cn', '')}, "
                detail_text += f"{'加粗' if heading.get('bold', False) else '正常'}\n"

        self.template_detail.delete("1.0", tk.END)
        self.template_detail.insert("1.0", detail_text)

    def create_new_template(self):
        """创建新模板"""
        dialog = TemplateEditorDialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            # 保存模板
            template_name = dialog.result["name"].lower().replace(" ", "_")
            success = self.template_manager.create_template(dialog.result)

            if success:
                # 重新加载模板
                self.config_manager.load_templates()
                self.load_templates_to_tree()
                self._load_template_widgets()  # 重新加载模板选择区域
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
            success = self.template_manager.update_template(
                template_name, dialog.result
            )

            if success:
                # 重新加载模板
                self.config_manager.load_templates()
                self.load_templates_to_tree()
                self._load_template_widgets()  # 重新加载模板选择区域
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
        new_name = simpledialog.askstring(
            "另存为", "请输入新模板名称（英文）:", initialvalue=f"{template_name}_copy"
        )

        if not new_name:
            return

        # 复制模板数据
        template_data = self.template_manager.get_template(template_name)
        if not template_data:
            self.queue_message("error", f"❌ 模板 '{template_name}' 不存在")
            return

        import copy

        new_template_data = copy.deepcopy(template_data)
        new_template_data["name"] = new_name.replace("_", " ").title()

        # 保存新模板
        success = self.template_manager.create_template(new_template_data)

        if success:
            # 重新加载模板
            self.config_manager.load_templates()
            self.load_templates_to_tree()
            self._load_template_widgets()  # 重新加载模板选择区域
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
        if not messagebox.askyesno(
            "确认删除", f"确定要删除模板 '{template_name}' 吗？\n此操作不可恢复！"
        ):
            return

        # 删除模板
        success = self.template_manager.delete_template(template_name)

        if success:
            # 重新加载模板
            self.config_manager.load_templates()
            self.load_templates_to_tree()
            self._load_template_widgets()  # 重新加载模板选择区域

            # 如果删除的是当前选择的模板，清除当前选择
            if self.current_template_id == template_name:
                self.current_template_id = None

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

    def open_smart_generate_dialog(self):
        """打开智能生成对话框"""
        try:
            from ui.dialogs.smart_generate_dialog_final import SmartGenerateDialog

            dialog = SmartGenerateDialog(
                self.root,
                self.config_manager,
                self.template_manager,
                self.handle_generated_content,
            )

            # 等待对话框关闭
            self.root.wait_window(dialog.dialog)

        except Exception as e:
            logger.error(f"打开智能生成对话框失败: {str(e)}")
            self.queue_message("error", f"打开智能生成对话框失败: {str(e)}")

    def handle_generated_content(self, content: str, template_name: str):
        """
        处理智能生成的内容回调

        Args:
            content: 生成的文本内容
            template_name: 选择的模板名称
        """
        try:
            logger.info(f"接收智能生成内容: {len(content)}字符, 模板: {template_name}")

            # 填充到输入文本框
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", content)

            # 自动提取标题
            title = self.doc_processor.extract_title(content)
            if title:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, title)
                self.original_title = title

            # 设置选择的模板
            if template_name in self.template_manager.get_template_list():
                # 在模板选择区域中选中对应模板
                if template_name in self.template_widgets:
                    self.template_widgets[template_name].select(True)

            # 更新文件标签
            self.file_label.config(text="🚀 智能生成内容", foreground="#28a745")

            # 更新状态
            char_count = len(content)
            self.stats_label.config(text=f"📊 智能生成: {char_count} 字符")

            # 提示用户
            self.queue_message(
                "success",
                f"✅ 智能生成完成！\n"
                f"📝 生成内容: {char_count} 字符\n"
                f"🎨 使用模板: {template_name}\n"
                f"👉 请点击'AI智能处理'按钮进行排版",
            )

            logger.info(f"智能生成内容已填充到界面: {char_count}字符")

        except Exception as e:
            logger.error(f"处理生成内容失败: {str(e)}")
            self.queue_message("error", f"处理生成内容失败: {str(e)}")
