"""
模板管理模块
负责管理文档模板的加载和应用
"""

import json
import copy
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import logging

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.shared import qn


logger = logging.getLogger(__name__)


def load_prompt_config(config_path: str = None) -> dict:
    """
    加载提示词配置文件
    
    Args:
        config_path: 配置文件路径，默认为config/prompt_config.json
        
    Returns:
        dict: 配置字典，如果失败则返回空字典
    """
    # 默认配置
    default_config = {
        "enabled": False,
        "templates": {},
        "default_prompt": ""
    }
    
    # 确定配置文件路径
    if config_path is None:
        # 尝试在config目录下寻找
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(current_dir, "..", "config")
        config_path = os.path.join(config_dir, "prompt_config.json")
    
    # 确保路径存在
    config_path = os.path.abspath(config_path)
    
    if not os.path.exists(config_path):
        logger.warning(f"提示词配置文件不存在: {config_path}")
        return default_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证配置结构
        if not isinstance(config, dict):
            logger.error("提示词配置格式错误：不是有效的JSON对象")
            return default_config
        
        # 确保必要字段存在
        config.setdefault("enabled", False)
        config.setdefault("templates", {})
        config.setdefault("default_prompt", "")
        
        logger.info(f"提示词配置加载成功，启用状态: {config.get('enabled')}")
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"提示词配置文件JSON解析失败: {e}")
        return default_config
    except Exception as e:
        logger.error(f"读取提示词配置失败: {e}")
        return default_config


class TemplateManager:
    """模板管理器类"""
    
    def __init__(self, config_manager):
        """
        初始化模板管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.templates = config_manager.templates
        self.templates_dir = config_manager.templates_dir
        self.current_template = 'article'  # 默认模板
        
        # 验证当前模板是否存在
        if self.current_template not in self.templates:
            if self.templates:
                self.current_template = next(iter(self.templates.keys()))
            else:
                self.current_template = None
    
    def get_template_list(self) -> List[str]:
        """
        获取模板名称列表
        
        Returns:
            模板名称列表
        """
        return list(self.templates.keys())
    
    def get_template_info(self) -> List[Dict[str, Any]]:
        """
        获取模板信息列表
        
        Returns:
            包含模板信息的字典列表
        """
        result = []
        for template_name, template_data in self.templates.items():
            result.append({
                'name': template_data.get('name', template_name),
                'id': template_name,
                'description': template_data.get('description', ''),
                'body_font': template_data.get('body', {}).get('font_name_cn', '未知')
            })
        return result
    
    def get_template(self, template_name: str = None) -> Optional[Dict[str, Any]]:
        """
        获取指定模板的配置
        
        Args:
            template_name: 模板名称，如果为None则返回当前模板
            
        Returns:
            模板配置字典或None
        """
        if template_name is None:
            template_name = self.current_template
        
        return self.templates.get(template_name)
    
    def switch_template(self, template_name: str) -> bool:
        """
        切换当前模板
        
        Args:
            template_name: 要切换的模板名称
            
        Returns:
            切换是否成功
        """
        if template_name in self.templates:
            self.current_template = template_name
            return True
        return False
    
    def create_template(self, template_data: Dict[str, Any]) -> bool:
        """
        创建新模板
        
        Args:
            template_data: 模板数据
            
        Returns:
            创建是否成功
        """
        template_name = template_data.get('name', '').lower().replace(' ', '_')
        if not template_name:
            return False
        
        # 保存模板文件
        template_file = self.templates_dir / f"{template_name}.json"
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            # 重新加载模板
            self.templates = self.config_manager.load_templates()
            return True
            
        except Exception as e:
            print(f"创建模板失败: {str(e)}")
            return False
    
    def update_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """
        更新模板
        
        Args:
            template_name: 模板名称
            template_data: 新的模板数据
            
        Returns:
            更新是否成功
        """
        if template_name not in self.templates:
            return False
        
        # 保存模板文件
        template_file = self.templates_dir / f"{template_name}.json"
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            # 重新加载模板
            self.templates = self.config_manager.load_templates()
            return True
            
        except Exception as e:
            print(f"更新模板失败: {str(e)}")
            return False
    
    def delete_template(self, template_name: str) -> bool:
        """
        删除模板
        
        Args:
            template_name: 要删除的模板名称
            
        Returns:
            删除是否成功
        """
        if template_name not in self.templates:
            return False
        
        # 删除模板文件
        template_file = self.templates_dir / f"{template_name}.json"
        try:
            import os
            os.remove(template_file)
            
            # 重新加载模板
            self.templates = self.config_manager.load_templates()
            
            # 如果删除的是当前模板，切换到另一个可用模板
            if template_name == self.current_template and self.templates:
                self.current_template = next(iter(self.templates.keys()))
            
            return True
            
        except Exception as e:
            print(f"删除模板失败: {str(e)}")
            return False
    
    def apply_document_styles(self, doc: Document, template_config: Dict[str, Any]) -> bool:
        """
        应用文档样式到Word文档
        
        Args:
            doc: Word文档对象
            template_config: 模板配置
            
        Returns:
            应用是否成功
        """
        try:
            # 1. 页面设置
            if 'page_setup' in template_config:
                page = template_config['page_setup']
                for section in doc.sections:
                    if 'margin_top' in page:
                        section.top_margin = Pt(page['margin_top'])
                    if 'margin_bottom' in page:
                        section.bottom_margin = Pt(page['margin_bottom'])
                    if 'margin_left' in page:
                        section.left_margin = Pt(page['margin_left'])
                    if 'margin_right' in page:
                        section.right_margin = Pt(page['margin_right'])
            
            # 2. 创建样式
            styles = doc.styles
            
            # 正文样式
            if 'body' in template_config:
                body = template_config['body']
                normal_style = styles['Normal']
                
                # 设置字体
                font_name_cn = body.get('font_name_cn', '宋体')
                font_name_en = body.get('font_name_en', 'Times New Roman')
                normal_style.font.name = font_name_en
                normal_style._element.rPr.rFonts.set(qn('w:eastAsia'), font_name_cn)
                
                # 设置字号
                if 'font_size' in body:
                    normal_style.font.size = Pt(body['font_size'])
                
                # 设置段落格式
                para_format = normal_style.paragraph_format
                para_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                
                if 'line_spacing' in body:
                    para_format.line_spacing = body['line_spacing']
                
                if 'first_line_indent' in body:
                    para_format.first_line_indent = Pt(body['first_line_indent'])
                
                if 'space_after' in body:
                    para_format.space_after = Pt(body['space_after'])
                
                # 对齐方式
                if 'alignment' in body:
                    alignment_map = {
                        'left': WD_ALIGN_PARAGRAPH.LEFT,
                        'center': WD_ALIGN_PARAGRAPH.CENTER,
                        'right': WD_ALIGN_PARAGRAPH.RIGHT,
                        'justify': WD_ALIGN_PARAGRAPH.JUSTIFY
                    }
                    if body['alignment'] in alignment_map:
                        normal_style.paragraph_format.alignment = alignment_map[body['alignment']]
            
            # 3. 标题样式
            for i in range(1, 4):
                heading_key = f'heading{i}'
                if heading_key in template_config:
                    heading_config = template_config[heading_key]
                    style_name = f'Heading {i}'
                    
                    if style_name in styles:
                        heading_style = styles[style_name]
                        
                        # 设置字体
                        font_name_cn = heading_config.get('font_name_cn', '黑体')
                        font_name_en = heading_config.get('font_name_en', 'Arial')
                        heading_style.font.name = font_name_en
                        heading_style._element.rPr.rFonts.set(qn('w:eastAsia'), font_name_cn)
                        
                        # 设置字号
                        if 'font_size' in heading_config:
                            heading_style.font.size = Pt(heading_config['font_size'])
                        
                        # 设置粗体
                        if 'bold' in heading_config:
                            heading_style.font.bold = heading_config['bold']
                        
                        # 设置段落格式
                        if 'space_before' in heading_config:
                            heading_style.paragraph_format.space_before = Pt(heading_config['space_before'])
                        if 'space_after' in heading_config:
                            heading_style.paragraph_format.space_after = Pt(heading_config['space_after'])
            
            return True
            
        except Exception as e:
            print(f"应用样式失败: {str(e)}")
            return False
    
    def format_content_with_template(self, content: str, template_config: Dict[str, Any]) -> str:
        """
        根据模板格式要求格式化内容（简单实现）
        
        Args:
            content: 原始内容
            template_config: 模板配置
            
        Returns:
            格式化后的内容
        """
        # 这里可以根据模板配置进行更复杂的内容格式化
        # 目前只返回原始内容，具体的格式化在保存为Word时处理
        return content