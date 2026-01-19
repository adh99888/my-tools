"""
模型管理模块
负责管理多个AI模型的配置和切换
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

logger = logging.getLogger(__name__)


class ModelManager:
    """模型管理器类"""
    
    def __init__(self, config_manager):
        """
        初始化模型管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.model_configs = config_manager.model_configs
        self.current_model_id = config_manager.api_config.get('default_model', 'deepseek')
        
        # 验证当前模型是否存在
        if self.current_model_id not in self.model_configs:
            logger.warning(f"默认模型 '{self.current_model_id}' 不存在，使用第一个可用模型")
            if self.model_configs:
                self.current_model_id = next(iter(self.model_configs.keys()))
            else:
                self.current_model_id = None
    
    def get_current_model_config(self) -> Optional[Dict[str, Any]]:
        """
        获取当前模型配置
        
        Returns:
            当前模型配置字典或None
        """
        if self.current_model_id:
            return self.model_configs.get(self.current_model_id)
        return None
    
    def get_model_config(self, model_id: str):
        """
        获取指定模型的配置
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型配置字典或None
        """
        return self.model_configs.get(model_id)
    
    def get_model_list(self) -> List[str]:
        """
        获取模型ID列表
        
        Returns:
            模型ID列表
        """
        return list(self.model_configs.keys())
    
    def get_model_display_info(self) -> List[Dict[str, Any]]:
        """
        获取模型显示信息
        
        Returns:
            包含模型显示信息的字典列表
        """
        result = []
        for model_id, config in self.model_configs.items():
            result.append({
                'id': model_id,
                'name': config.get('name', model_id),
                'model': config.get('model', ''),
                'max_tokens': config.get('max_tokens', 8192),
                'provider': config.get('provider', 'custom'),
                'api_base': config.get('api_base', ''),
                'api_key': config.get('api_key', '')
            })
        return result
    
    def switch_model(self, model_id: str) -> bool:
        """
        切换当前模型
        
        Args:
            model_id: 要切换的模型ID
            
        Returns:
            切换是否成功
        """
        if model_id in self.model_configs:
            self.current_model_id = model_id
            logger.info(f"切换到模型: {model_id}")
            return True
        else:
            logger.error(f"模型不存在: {model_id}")
            return False
    
    def add_model(self, model_id: str, config: Dict[str, Any]) -> bool:
        """
        添加新模型
        
        Args:
            model_id: 模型ID
            config: 模型配置
            
        Returns:
            添加是否成功
        """
        if model_id in self.model_configs:
            logger.error(f"模型已存在: {model_id}")
            return False
        
        # 验证必填字段
        required_fields = ['name', 'api_base', 'model']
        for field in required_fields:
            if field not in config or not config[field]:
                logger.error(f"缺少必要字段: {field}")
                return False
        
        self.model_configs[model_id] = config
        self.config_manager.update_model_config(model_id, config)
        logger.info(f"添加模型成功: {model_id}")
        return True
    
    def update_model(self, model_id: str, config: Dict[str, Any]) -> bool:
        """
        更新模型配置
        
        Args:
            model_id: 模型ID
            config: 新的配置
            
        Returns:
            更新是否成功
        """
        if model_id not in self.model_configs:
            logger.error(f"模型不存在: {model_id}")
            return False
        
        # 保留必要的字段
        original_config = self.model_configs[model_id]
        updated_config = {**original_config, **config}
        
        self.model_configs[model_id] = updated_config
        self.config_manager.update_model_config(model_id, updated_config)
        logger.info(f"更新模型成功: {model_id}")
        return True
    
    def delete_model(self, model_id: str) -> bool:
        """
        删除模型
        
        Args:
            model_id: 要删除的模型ID
            
        Returns:
            删除是否成功
        """
        if model_id == 'deepseek':
            logger.error("不能删除默认的DeepSeek模型")
            return False
        
        if model_id not in self.model_configs:
            logger.error(f"模型不存在: {model_id}")
            return False
        
        del self.model_configs[model_id]
        self.config_manager.save_model_configs()
        logger.info(f"删除模型成功: {model_id}")
        return True
    
    def get_model_for_content(self, content: str) -> str:
        """
        根据内容长度推荐合适的模型
        
        Args:
            content: 文档内容
            
        Returns:
            推荐的模型ID
        """
        char_count = len(content)
        estimated_tokens = char_count // 3  # 粗略估计
        
        # 按最大token数排序模型
        sorted_models = sorted(
            self.model_configs.items(),
            key=lambda x: x[1].get('max_tokens', 8192),
            reverse=True
        )
        
        # 找到能容纳内容的模型
        for model_id, config in sorted_models:
            max_tokens = config.get('max_tokens', 8192)
            if estimated_tokens <= max_tokens * 0.7:  # 70%安全余量
                return model_id
        
        # 如果没有合适的模型，返回token最多的模型
        if sorted_models:
            return sorted_models[0][0]
        
        return self.current_model_id
    
    def validate_model_config(self, model_id: str) -> Dict[str, Any]:
        """
        验证模型配置是否完整
        
        Args:
            model_id: 模型ID
            
        Returns:
            验证结果字典 {status: bool, message: str, config: dict}
        """
        if model_id not in self.model_configs:
            return {
                'status': False,
                'message': f"模型 '{model_id}' 不存在",
                'config': None
            }
        
        config = self.model_configs[model_id]
        missing_fields = []
        
        # 检查必要字段
        required_fields = ['name', 'api_base', 'model']
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
        
        # 检查API密钥
        api_key = config.get('api_key', '')
        if not api_key and not self.config_manager.get_api_key():
            missing_fields.append('api_key')
        
        if missing_fields:
            return {
                'status': False,
                'message': f"缺少必要字段: {', '.join(missing_fields)}",
                'config': config
            }
        
        return {
            'status': True,
            'message': "配置验证通过",
            'config': config
        }


class ModelConfigDialog:
    """模型配置对话框（UI部分）"""
    
    def __init__(self, parent, model_manager, current_model_id):
        self.parent = parent
        self.model_manager = model_manager
        self.current_model_id = current_model_id
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI模型配置")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 设置窗口图标
        try:
            self.dialog.iconbitmap('icon.ico')
        except:
            pass
        
        self.create_widgets()
        self.center_window()
        
    def center_window(self):
        """窗口居中"""
        self.dialog.update()
        window_width = self.dialog.winfo_width()
        window_height = self.dialog.winfo_height()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """创建界面控件"""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🤖 AI模型配置管理", 
                               font=('Microsoft YaHei', 14, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 模型列表
        list_frame = ttk.LabelFrame(main_frame, text="可用模型", padding="10")
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
        detail_frame = ttk.LabelFrame(main_frame, text="模型配置", padding="10")
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
        button_frame = ttk.Frame(main_frame)
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
        
        for model_id, config in self.model_manager.model_configs.items():
            self.model_tree.insert('', 'end', iid=model_id,
                values=(config.get('name', model_id),
                       config.get('model', ''),
                       config.get('max_tokens', ''),
                       config.get('provider', '')))
        
        # 选中当前模型
        if self.current_model_id in self.model_tree.get_children():
            self.model_tree.selection_set(self.current_model_id)
            self.on_model_selected(None)
    
    def on_model_selected(self, event):
        """模型选择事件"""
        selection = self.model_tree.selection()
        if not selection:
            return
        
        model_id = selection[0]
        config = self.model_manager.model_configs.get(model_id, {})
        
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
        
        if name in self.model_manager.model_configs:
            messagebox.showerror("错误", f"模型标识符 '{name}' 已存在！")
            return
        
        # 默认配置
        config = {
            'name': name,
            'api_base': 'https://api.example.com/v1',
            'model': 'model-name',
            'max_tokens': 8192,
            'provider': 'custom'
        }
        
        if self.model_manager.add_model(name, config):
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
        config = {
            'name': self.name_entry.get().strip(),
            'api_base': self.base_entry.get().strip(),
            'model': self.model_entry.get().strip(),
            'api_key': self.key_entry.get().strip(),
            'max_tokens': int(self.token_var.get()),
            'provider': self.provider_var.get()
        }
        
        if self.model_manager.update_model(model_id, config):
            self.load_models_to_tree()
            messagebox.showinfo("成功", "模型配置已更新！")
    
    def delete_model(self):
        """删除模型"""
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模型！")
            return
        
        model_id = selection[0]
        
        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除模型 '{model_id}' 吗？"):
            if self.model_manager.delete_model(model_id):
                self.load_models_to_tree()
                messagebox.showinfo("成功", "模型已删除！")
    
    def save_and_close(self):
        """保存并关闭"""
        self.result = self.model_manager.model_configs
        self.dialog.destroy()