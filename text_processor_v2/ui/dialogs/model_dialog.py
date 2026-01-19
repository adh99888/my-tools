"""
模型配置对话框
负责模型配置的管理界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .base_dialog import BaseDialog


class ModelConfigDialog(BaseDialog):
    """模型配置对话框"""
    
    def __init__(self, parent, model_configs, current_model):
        """
        初始化模型配置对话框
        
        Args:
            parent: 父窗口
            model_configs: 模型配置字典
            current_model: 当前模型ID
        """
        self.model_configs = model_configs.copy()  # 使用副本
        self.current_model = current_model
        self.result = None
        
        super().__init__(parent, "AI模型配置", 800, 600)
    
    def create_widgets(self):
        """创建界面控件"""
        # 标题
        title_label = ttk.Label(self.main_frame, text="🤖 AI模型配置管理", 
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 模型列表
        list_frame = ttk.LabelFrame(self.main_frame, text="可用模型", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        columns = ('name', 'model', 'max_tokens', 'provider')
        self.model_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # 设置列
        self.model_tree.heading('name', text='模型名称')
        self.model_tree.heading('model', text='模型ID')
        self.model_tree.heading('max_tokens', text='最大长度')
        self.model_tree.heading('provider', text='提供商')
        
        self.model_tree.column('name', width=150)
        self.model_tree.column('model', width=150)
        self.model_tree.column('max_tokens', width=100)
        self.model_tree.column('provider', width=120)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.model_tree.yview)
        self.model_tree.configure(yscroll=scrollbar.set)
        
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.model_tree.bind('<<TreeviewSelect>>', self.on_model_selected)
        
        # 详情编辑区
        detail_frame = ttk.LabelFrame(self.main_frame, text="模型配置", padding="10")
        detail_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 模型名称
        name_frame = ttk.Frame(detail_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(name_frame, text="显示名称:", width=12).pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # API基础URL
        base_frame = ttk.Frame(detail_frame)
        base_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(base_frame, text="API基础URL:", width=12).pack(side=tk.LEFT)
        self.base_entry = ttk.Entry(base_frame)
        self.base_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 模型ID
        model_frame = ttk.Frame(detail_frame)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(model_frame, text="模型ID:", width=12).pack(side=tk.LEFT)
        self.model_entry = ttk.Entry(model_frame)
        self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # API密钥
        key_frame = ttk.Frame(detail_frame)
        key_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(key_frame, text="API密钥:", width=12).pack(side=tk.LEFT)
        self.key_entry = ttk.Entry(key_frame, show="*")
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 最大token数
        token_frame = ttk.Frame(detail_frame)
        token_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(token_frame, text="最大Token:", width=12).pack(side=tk.LEFT)
        self.token_var = tk.StringVar(value="8192")
        token_combo = ttk.Combobox(token_frame, textvariable=self.token_var, 
                                  values=["4096", "8192", "16384", "32768", "65536"])
        token_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 提供商
        provider_frame = ttk.Frame(detail_frame)
        provider_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(provider_frame, text="提供商:", width=12).pack(side=tk.LEFT)
        self.provider_var = tk.StringVar()
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.provider_var,
                                     values=["deepseek", "moonshot", "dashscope", "siliconflow", "baichuan", "glm", "custom"])
        provider_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="➕ 添加新模型", 
                  command=self.add_model, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="✏️ 更新模型", 
                  command=self.update_model, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🗑️ 删除模型", 
                  command=self.delete_model, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="✅ 保存并关闭", 
                  command=self.save_and_close, width=15).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="❌ 取消", 
                  command=self.dialog.destroy, width=15).pack(side=tk.RIGHT, padx=(0, 10))
        
        # 加载数据
        self.load_models_to_tree()
    
    def load_models_to_tree(self):
        """加载模型到树形列表"""
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
        
        for model_id, config in self.model_configs.items():
            self.model_tree.insert('', 'end', iid=model_id,
                values=(config.get('name', model_id),
                       config.get('model', ''),
                       config.get('max_tokens', ''),
                       config.get('provider', '')))
        
        # 选中当前模型
        if self.current_model in self.model_tree.get_children():
            self.model_tree.selection_set(self.current_model)
            self.on_model_selected(None)
    
    def on_model_selected(self, event):
        """模型选择事件"""
        selection = self.model_tree.selection()
        if not selection:
            return
        
        model_id = selection[0]
        config = self.model_configs.get(model_id, {})
        
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, config.get('name', ''))
        
        self.base_entry.delete(0, tk.END)
        self.base_entry.insert(0, config.get('api_base', ''))
        
        self.model_entry.delete(0, tk.END)
        self.model_entry.insert(0, config.get('model', ''))
        
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, config.get('api_key', ''))
        
        self.token_var.set(str(config.get('max_tokens', 8192)))
        self.provider_var.set(config.get('provider', 'custom'))
    
    def add_model(self):
        """添加新模型"""
        name = simpledialog.askstring("新模型", "请输入新模型的唯一标识符（英文）:")
        if not name:
            return
        
        if name in self.model_configs:
            messagebox.showerror("错误", f"模型标识符 '{name}' 已存在！")
            return
        
        # 默认配置
        self.model_configs[name] = {
            'name': name,
            'api_base': 'https://api.example.com/v1',
            'model': 'model-name',
            'max_tokens': 8192,
            'provider': 'custom'
        }
        
        # 添加到列表
        self.load_models_to_tree()
        self.model_tree.selection_set(name)
        self.on_model_selected(None)
        
        messagebox.showinfo("成功", f"已添加新模型 '{name}'，请配置其详细信息。")
    
    def update_model(self):
        """更新模型配置"""
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模型！")
            return
        
        model_id = selection[0]
        
        # 验证必填项
        if not self.name_entry.get().strip():
            messagebox.showerror("错误", "模型名称不能为空！")
            return
        
        if not self.base_entry.get().strip():
            messagebox.showerror("错误", "API基础URL不能为空！")
            return
        
        if not self.model_entry.get().strip():
            messagebox.showerror("错误", "模型ID不能为空！")
            return
        
        # 更新配置
        self.model_configs[model_id] = {
            'name': self.name_entry.get().strip(),
            'api_base': self.base_entry.get().strip(),
            'model': self.model_entry.get().strip(),
            'api_key': self.key_entry.get().strip(),
            'max_tokens': int(self.token_var.get()),
            'provider': self.provider_var.get()
        }
        
        # 刷新列表
        self.load_models_to_tree()
        messagebox.showinfo("成功", "模型配置已更新！")
    
    def delete_model(self):
        """删除模型"""
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模型！")
            return
        
        model_id = selection[0]
        
        # 不能删除默认模型
        if model_id == 'deepseek':
            messagebox.showerror("错误", "不能删除默认的DeepSeek模型！")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除模型 '{model_id}' 吗？"):
            del self.model_configs[model_id]
            self.load_models_to_tree()
            messagebox.showinfo("成功", "模型已删除！")
    
    def save_and_close(self):
        """保存并关闭"""
        self.result = self.model_configs
        self.dialog.destroy()