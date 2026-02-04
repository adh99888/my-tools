"""
提示词管理器模块
负责提示词的加载、保存、验证和管理
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PromptManager:
    """提示词管理器类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化提示词管理器
        
        Args:
            config_path: 配置文件路径，默认为config/prompt_config.json
        """
        if config_path is None:
            # 默认配置文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(current_dir, "..", "config", "prompt_config.json")
        else:
            self.config_path = config_path
        
        # 默认配置
        self.default_config = {
            "version": "1.0",
            "enabled": False,
            "features": {
                "prompt_ui": False,
                "auto_title": False,
                "complex_title": False
            },
            "title_extraction": {
                "confidence_threshold": 70,
                "max_lines_to_scan": 5,
                "min_title_length": 5,
                "max_title_length": 100
            },
            "templates": {},
            "default_prompt": ""
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"提示词配置文件不存在: {self.config_path}")
            return self.default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置结构
            if not isinstance(config, dict):
                logger.error("提示词配置格式错误：不是有效的JSON对象")
                return self.default_config
            
            # 合并默认配置，确保所有字段都存在
            merged_config = self.default_config.copy()
            merged_config.update(config)
            
            # 确保嵌套字段也存在
            if "features" not in merged_config:
                merged_config["features"] = self.default_config["features"]
            else:
                for key in self.default_config["features"]:
                    if key not in merged_config["features"]:
                        merged_config["features"][key] = self.default_config["features"][key]
            
            if "title_extraction" not in merged_config:
                merged_config["title_extraction"] = self.default_config["title_extraction"]
            else:
                for key in self.default_config["title_extraction"]:
                    if key not in merged_config["title_extraction"]:
                        merged_config["title_extraction"][key] = self.default_config["title_extraction"][key]
            
            logger.info(f"提示词配置加载成功，版本: {merged_config.get('version')}")
            return merged_config
            
        except json.JSONDecodeError as e:
            logger.error(f"提示词配置文件JSON解析失败: {e}")
            return self.default_config
        except Exception as e:
            logger.error(f"读取提示词配置失败: {e}")
            return self.default_config
    
    def save_config(self) -> bool:
        """
        保存配置文件
        
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"提示词配置保存成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存提示词配置失败: {e}")
            return False
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        检查特定功能是否启用
        
        Args:
            feature_name: 功能名称，如 "prompt_ui", "auto_title", "complex_title"
            
        Returns:
            功能是否启用
        """
        if not self.config.get("enabled", False):
            return False
        
        features = self.config.get("features", {})
        return features.get(feature_name, False)
    
    def get_template_prompt(self, template_id: str) -> Optional[str]:
        """
        获取指定模板的提示词
        
        Args:
            template_id: 模板ID
            
        Returns:
            提示词内容，如果不存在则返回None
        """
        templates = self.config.get("templates", {})
        
        if template_id in templates:
            template_config = templates[template_id]
            if template_config.get("enabled", True):
                return template_config.get("prompt", "")
        
        return None
    
    def get_default_prompt(self) -> str:
        """
        获取默认提示词
        
        Returns:
            默认提示词内容
        """
        return self.config.get("default_prompt", "")
    
    def get_prompt(self, template_id: str) -> str:
        """
        获取提示词（优先使用模板专用提示词，否则使用默认提示词）
        
        Args:
            template_id: 模板ID
            
        Returns:
            提示词内容
        """
        template_prompt = self.get_template_prompt(template_id)
        if template_prompt:
            return template_prompt
        return self.get_default_prompt()
    
    def update_template_prompt(self, template_id: str, prompt: str, 
                              template_name: str = None, description: str = None) -> bool:
        """
        更新模板提示词
        
        Args:
            template_id: 模板ID
            prompt: 新的提示词内容
            template_name: 模板名称（可选）
            description: 模板描述（可选）
            
        Returns:
            更新是否成功
        """
        # 确保templates字段存在
        if "templates" not in self.config:
            self.config["templates"] = {}
        
        templates = self.config["templates"]
        
        # 创建或更新模板配置
        if template_id not in templates:
            templates[template_id] = {}
        
        template_config = templates[template_id]
        template_config["prompt"] = prompt
        template_config["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新使用次数
        template_config["usage_count"] = template_config.get("usage_count", 0) + 1
        
        # 可选字段更新
        if template_name is not None:
            template_config["name"] = template_name
        
        if description is not None:
            template_config["description"] = description
        
        # 确保enabled字段存在
        if "enabled" not in template_config:
            template_config["enabled"] = True
        
        logger.info(f"更新模板提示词: {template_id}")
        return self.save_config()
    
    def reset_template_prompt(self, template_id: str) -> bool:
        """
        重置模板提示词为默认提示词
        
        Args:
            template_id: 模板ID
            
        Returns:
            重置是否成功
        """
        default_prompt = self.get_default_prompt()
        return self.update_template_prompt(template_id, default_prompt)
    
    def enable_template_prompt(self, template_id: str, enabled: bool = True) -> bool:
        """
        启用或禁用模板提示词
        
        Args:
            template_id: 模板ID
            enabled: 是否启用
            
        Returns:
            操作是否成功
        """
        if "templates" not in self.config:
            return False
        
        templates = self.config["templates"]
        
        if template_id not in templates:
            return False
        
        templates[template_id]["enabled"] = enabled
        logger.info(f"{'启用' if enabled else '禁用'}模板提示词: {template_id}")
        return self.save_config()
    
    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模板信息
        
        Args:
            template_id: 模板ID
            
        Returns:
            模板信息字典
        """
        templates = self.config.get("templates", {})
        
        if template_id in templates:
            template_config = templates[template_id].copy()
            template_config["id"] = template_id
            return template_config
        
        return None
    
    def get_all_templates_info(self) -> List[Dict[str, Any]]:
        """
        获取所有模板信息
        
        Returns:
            模板信息列表
        """
        templates = self.config.get("templates", {})
        result = []
        
        for template_id, template_config in templates.items():
            info = template_config.copy()
            info["id"] = template_id
            result.append(info)
        
        return result
    
    def get_title_extraction_config(self) -> Dict[str, Any]:
        """
        获取标题提取配置
        
        Returns:
            标题提取配置字典
        """
        return self.config.get("title_extraction", {})
    
    def is_auto_title_enabled(self) -> bool:
        """
        检查自动标题提取是否启用
        
        Returns:
            是否启用
        """
        return self.is_feature_enabled("auto_title")
    
    def is_complex_title_enabled(self) -> bool:
        """
        检查复杂标题提取是否启用
        
        Returns:
            是否启用
        """
        return self.is_feature_enabled("complex_title")


# 全局实例
_prompt_manager_instance = None

def get_prompt_manager(config_path: str = None) -> PromptManager:
    """
    获取提示词管理器实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        PromptManager实例
    """
    global _prompt_manager_instance
    
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager(config_path)
    
    return _prompt_manager_instance