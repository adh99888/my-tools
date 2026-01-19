"""
配置管理模块
负责加载和管理所有配置文件
"""

import os
import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """统一的配置管理类"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            base_dir: 项目基础目录，默认为当前目录
        """
        # 如果 base_dir 为 None，则使用项目根目录
        if base_dir is None:
            # 从当前文件位置向上两级到项目根目录
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)
            
        self.config_dir = self.base_dir / "config"
        self.templates_dir = self.base_dir / "templates"
        
        # 配置数据
        self.api_config = {}
        self.model_configs = {}
        self.templates = {}
        
        # 确保目录存在
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
    def load_all_configs(self):
        """加载所有配置"""
        self.load_api_config()
        self.load_model_configs()
        self.load_templates()
        return self
    
    def load_api_config(self) -> Dict[str, Any]:
        """
        加载API配置
        
        Returns:
            字典格式的API配置
        """
        config_path = self.config_dir / "config.ini"
        
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            self.api_config = {
                "key": "",
                "api_base": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "max_retries": 3
            }
            return self.api_config
        
        try:
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            self.api_config = {
                "key": config.get('API', 'key', fallback='').strip(),
                "api_base": config.get('API', 'api_base', fallback='https://api.deepseek.com/v1').strip(),
                "model": config.get('API', 'model', fallback='deepseek-chat').strip(),
                "default_mode": config.get('Settings', 'default_mode', fallback='polish'),
                "keep_original_title": config.getboolean('Settings', 'keep_original_title', fallback=True),
                "auto_correct": config.getboolean('Settings', 'auto_correct', fallback=True),
                "max_retries": config.getint('Settings', 'max_retries', fallback=3)
            }
            
            # 多模型配置
            if config.has_section('MultiModel'):
                self.api_config.update({
                    "enable_multi_model": config.getboolean('MultiModel', 'enable_multi_model', fallback=False),
                    "default_model": config.get('MultiModel', 'default_model', fallback='deepseek-chat')
                })
            
            logger.info("API配置加载成功")
            return self.api_config
            
        except Exception as e:
            logger.error(f"加载API配置失败: {str(e)}")
            self.api_config = {}
            return {}
    
    def load_model_configs(self) -> Dict[str, Any]:
        """
        加载模型配置
        
        Returns:
            字典格式的模型配置
        """
        config_path = self.config_dir / "model_configs.json"
        
        if not config_path.exists():
            logger.warning(f"模型配置文件不存在: {config_path}")
            # 创建默认配置
            self.model_configs = {
                "deepseek": {
                    "name": "DeepSeek Chat",
                    "api_base": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "max_tokens": 8192,
                    "provider": "deepseek"
                }
            }
            self.save_model_configs()
            return self.model_configs
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.model_configs = json.load(f)
            
            logger.info(f"加载了 {len(self.model_configs)} 个模型配置")
            return self.model_configs
            
        except Exception as e:
            logger.error(f"加载模型配置失败: {str(e)}")
            self.model_configs = {}
            return {}
    
    def load_templates(self) -> Dict[str, Any]:
        """
        加载所有模板
        
        Returns:
            字典格式的模板配置
        """
        if not self.templates_dir.exists():
            logger.error(f"模板文件夹不存在: {self.templates_dir}")
            return {}
        
        template_files = list(self.templates_dir.glob("*.json"))
        if not template_files:
            logger.warning(f"模板文件夹为空: {self.templates_dir}")
            return {}
        
        loaded_count = 0
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    template_name = template_file.stem
                    self.templates[template_name] = template_data
                    loaded_count += 1
            except Exception as e:
                logger.error(f"加载模板失败 {template_file}: {str(e)}")
        
        logger.info(f"已加载 {loaded_count} 个模板")
        return self.templates
    
    def save_model_configs(self):
        """保存模型配置"""
        try:
            config_path = self.config_dir / "model_configs.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.model_configs, f, ensure_ascii=False, indent=2)
            logger.info("模型配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存模型配置失败: {str(e)}")
            return False
    
    def save_api_config(self):
        """保存API配置"""
        try:
            config_path = self.config_dir / "config.ini"
            config = configparser.ConfigParser()
            
            # API配置
            config['API'] = {
                'key': self.api_config.get('key', ''),
                'api_base': self.api_config.get('api_base', 'https://api.deepseek.com/v1'),
                'model': self.api_config.get('model', 'deepseek-chat')
            }
            
            # 设置
            config['Settings'] = {
                'default_mode': self.api_config.get('default_mode', 'polish'),
                'keep_original_title': 'yes' if self.api_config.get('keep_original_title', True) else 'no',
                'auto_correct': 'yes' if self.api_config.get('auto_correct', True) else 'no',
                'max_retries': str(self.api_config.get('max_retries', 3))
            }
            
            # 多模型配置
            if 'enable_multi_model' in self.api_config:
                config['MultiModel'] = {
                    'enable_multi_model': 'yes' if self.api_config.get('enable_multi_model', False) else 'no',
                    'default_model': self.api_config.get('default_model', 'deepseek-chat')
                }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            logger.info("API配置已保存")
            return True
            
        except Exception as e:
            logger.error(f"保存API配置失败: {str(e)}")
            return False
    
    def get_api_key(self, model_id: str = None) -> Optional[str]:
        """
        获取API密钥
        
        Args:
            model_id: 模型ID，如果为None则返回默认API密钥
            
        Returns:
            API密钥字符串或None
        """
        if model_id and model_id in self.model_configs:
            model_config = self.model_configs[model_id]
            api_key = model_config.get('api_key', '')
            if api_key:
                return api_key
        
        # 返回默认API密钥
        return self.api_config.get('key')
    
    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模型的配置
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型配置字典或None
        """
        return self.model_configs.get(model_id)
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模板的配置
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板配置字典或None
        """
        return self.templates.get(template_name)
    
    def update_model_config(self, model_id: str, config: Dict[str, Any]):
        """
        更新模型配置
        
        Args:
            model_id: 模型ID
            config: 新的配置字典
        """
        self.model_configs[model_id] = config
        self.save_model_configs()
    
    def update_api_config(self, key: str, value: Any):
        """
        更新API配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.api_config[key] = value
        self.save_api_config()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(base_dir: str = None) -> ConfigManager:
    """
    获取全局配置管理器实例（单例模式）
    
    Args:
        base_dir: 项目基础目录
        
    Returns:
        ConfigManager实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(base_dir)
        _config_manager.load_all_configs()
    return _config_manager