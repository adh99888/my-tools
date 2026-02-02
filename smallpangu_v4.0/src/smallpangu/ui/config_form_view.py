"""
配置表单视图组件

基于ConfigFormService生成的FormConfig动态渲染配置表单。
支持多种字段类型、实时验证、条件显示等高级功能。
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional, List, Tuple, Callable, Union
from dataclasses import dataclass

from .widgets import BaseWidget, Panel, ScrollPanel, Label, InputField, Switch, Dropdown, TextArea, Button, WidgetStyle
from ..services.config_form_service import FormConfig, FormSection, FormField, FormFieldType, ValidationLevel
from ..core.events import EventBus
from ..config.manager import ConfigManager
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FieldValidationResult:
    """字段验证结果"""
    field_id: str
    is_valid: bool
    message: Optional[str] = None


@dataclass
class FormValidationResult:
    """表单验证结果"""
    is_valid: bool
    errors: List[FieldValidationResult]
    values: Dict[str, Any]


class FieldRenderer:
    """字段渲染器 - 将FormField转换为UI组件"""
    
    def __init__(self, parent, config_manager: Optional[ConfigManager] = None):
        self._parent = parent
        self._config_manager = config_manager
        self._widget_cache: Dict[str, BaseWidget] = {}
        
    def render_field(self, field: FormField) -> Optional[BaseWidget]:
        """渲染字段为UI组件"""
        try:
            widget_id = f"field_{field.id}"
            
            # 检查缓存
            if widget_id in self._widget_cache:
                return self._widget_cache[widget_id]
            
            widget = None
            
            # 根据字段类型创建对应的UI组件
            if field.field_type == FormFieldType.TEXT:
                widget = self._create_text_field(field, widget_id)
            elif field.field_type == FormFieldType.TEXTAREA:
                widget = self._create_textarea_field(field, widget_id)
            elif field.field_type == FormFieldType.CODE:
                widget = self._create_code_field(field, widget_id)
            elif field.field_type == FormFieldType.NUMBER:
                widget = self._create_number_field(field, widget_id)
            elif field.field_type == FormFieldType.INTEGER:
                widget = self._create_integer_field(field, widget_id)
            elif field.field_type == FormFieldType.BOOLEAN:
                widget = self._create_boolean_field(field, widget_id)
            elif field.field_type == FormFieldType.SELECT:
                widget = self._create_select_field(field, widget_id)
            elif field.field_type == FormFieldType.MULTISELECT:
                widget = self._create_multiselect_field(field, widget_id)
            elif field.field_type == FormFieldType.SLIDER:
                widget = self._create_slider_field(field, widget_id)
            elif field.field_type == FormFieldType.COLOR:
                widget = self._create_color_field(field, widget_id)
            else:
                # 默认使用文本字段
                widget = self._create_text_field(field, widget_id)
                logger.warning(f"不支持的字段类型: {field.field_type}, 使用文本字段替代")
            
            if widget:
                self._widget_cache[widget_id] = widget
                self._apply_field_styling(widget, field)
            
            return widget
            
        except Exception as e:
            logger.error(f"字段渲染失败: {field.id} - {e}", exc_info=True)
            return None
    
    def _create_text_field(self, field: FormField, widget_id: str) -> InputField:
        """创建文本输入字段"""
        return InputField(
            self._parent,
            widget_id=widget_id,
            placeholder=field.placeholder or "",
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _create_textarea_field(self, field: FormField, widget_id: str) -> TextArea:
        """创建多行文本字段"""
        return TextArea(
            self._parent,
            widget_id=widget_id,
            style={
                "font": ("Consolas", 10),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "height": 120
            }
        )
    
    def _create_code_field(self, field: FormField, widget_id: str) -> TextArea:
        """创建代码编辑字段（暂时使用TextArea）"""
        return TextArea(
            self._parent,
            widget_id=widget_id,
            style={
                "font": ("Consolas", 10),
                "bg_color": "#f8f9fa",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "height": 180
            }
        )
    
    def _create_number_field(self, field: FormField, widget_id: str) -> InputField:
        """创建数字输入字段"""
        return InputField(
            self._parent,
            widget_id=widget_id,
            placeholder=field.placeholder or "",
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _create_integer_field(self, field: FormField, widget_id: str) -> InputField:
        """创建整数输入字段"""
        return InputField(
            self._parent,
            widget_id=widget_id,
            placeholder=field.placeholder or "",
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _create_boolean_field(self, field: FormField, widget_id: str) -> Switch:
        """创建布尔开关字段"""
        return Switch(
            self._parent,
            text=field.name,
            widget_id=widget_id,
            style={
                "font": ("Segoe UI", 11),
                "text_color": "#212529",
                "padding": (0, 8)
            }
        )
    
    def _create_select_field(self, field: FormField, widget_id: str) -> Dropdown:
        """创建下拉选择字段"""
        options = [str(opt) for opt in field.options] if field.options else []
        return Dropdown(
            self._parent,
            options=options,
            widget_id=widget_id,
            default_value=str(field.default_value) if field.default_value else None,
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _create_multiselect_field(self, field: FormField, widget_id: str) -> Dropdown:
        """创建多选字段（暂时使用Dropdown，未来需要实现多选）"""
        options = [str(opt) for opt in field.options] if field.options else []
        return Dropdown(
            self._parent,
            options=options,
            widget_id=widget_id,
            default_value=str(field.default_value) if field.default_value else None,
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _create_slider_field(self, field: FormField, widget_id: str) -> InputField:
        """创建滑块字段（暂时使用InputField）"""
        return InputField(
            self._parent,
            widget_id=widget_id,
            placeholder=field.placeholder or "输入数值",
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _create_color_field(self, field: FormField, widget_id: str) -> InputField:
        """创建颜色选择字段（暂时使用InputField）"""
        return InputField(
            self._parent,
            widget_id=widget_id,
            placeholder="#RRGGBB 或颜色名称",
            style={
                "font": ("Segoe UI", 11),
                "bg_color": "#ffffff",
                "border_color": "#ced4da",
                "border_width": 1,
                "corner_radius": 4,
                "padding": (8, 8)
            }
        )
    
    def _apply_field_styling(self, widget: BaseWidget, field: FormField) -> None:
        """应用字段样式"""
        # 设置字段值
        if hasattr(widget, 'set_value'):
            try:
                widget.set_value(field.value if field.value is not None else "")
            except Exception as e:
                logger.warning(f"设置字段值失败 {field.id}: {e}")
        
        # 禁用状态
        if not field.enabled or field.read_only:
            widget.set_state("disabled")
        
        # 应用自定义样式（如果支持）
        if field.style and hasattr(widget, 'update_style'):
            try:
                widget.update_style(**field.style)
            except Exception as e:
                logger.warning(f"应用自定义样式失败 {field.id}: {e}")
    
    def get_field_value(self, widget: BaseWidget, field_type: FormFieldType) -> Any:
        """从UI组件获取字段值"""
        if not hasattr(widget, 'get_value'):
            return None
        
        try:
            raw_value = widget.get_value()
            
            # 根据字段类型转换值
            if field_type == FormFieldType.TEXT:
                return str(raw_value) if raw_value else ""
            elif field_type == FormFieldType.TEXTAREA:
                return str(raw_value) if raw_value else ""
            elif field_type == FormFieldType.CODE:
                return str(raw_value) if raw_value else ""
            elif field_type == FormFieldType.NUMBER:
                try:
                    return float(raw_value) if raw_value else None
                except (ValueError, TypeError):
                    return None
            elif field_type == FormFieldType.INTEGER:
                try:
                    return int(raw_value) if raw_value else None
                except (ValueError, TypeError):
                    return None
            elif field_type == FormFieldType.BOOLEAN:
                return bool(raw_value)
            elif field_type == FormFieldType.SELECT:
                return str(raw_value) if raw_value else None
            elif field_type == FormFieldType.MULTISELECT:
                # TODO: 实现真正的多选值获取
                return [str(raw_value)] if raw_value else []
            elif field_type == FormFieldType.SLIDER:
                try:
                    return float(raw_value) if raw_value else None
                except (ValueError, TypeError):
                    return None
            elif field_type == FormFieldType.COLOR:
                return str(raw_value) if raw_value else ""
            else:
                return raw_value
                
        except Exception as e:
            logger.error(f"获取字段值失败: {e}", exc_info=True)
            return None
    
    def clear_cache(self) -> None:
        """清除组件缓存"""
        self._widget_cache.clear()


class ConfigFormView(BaseWidget):
    """
    配置表单视图
    
    动态渲染FormConfig为交互式表单，支持：
    1. 多种字段类型渲染
    2. 实时验证和错误显示
    3. 条件字段显示/隐藏
    4. 表单提交和取消
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        style: Optional[Union[WidgetStyle, Dict[str, Any]]] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        form_config: Optional[FormConfig] = None,
        on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        """
        初始化配置表单视图
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            style: 组件样式
            config_manager: 配置管理器
            event_bus: 事件总线
            form_config: 表单配置
            on_submit: 提交回调函数
            on_cancel: 取消回调函数
        """
        super().__init__(parent, widget_id, style, config_manager, event_bus)
        
        self._form_config = form_config
        self._on_submit = on_submit
        self._on_cancel = on_cancel
        
        # 字段渲染器
        self._field_renderer = FieldRenderer(parent, config_manager)
        
        # UI组件
        self._main_panel: Optional[Panel] = None
        self._scroll_panel: Optional[ScrollPanel] = None
        self._sections_panel: Optional[Panel] = None
        self._button_panel: Optional[Panel] = None
        
        # 字段映射: field_id -> (UI组件, FormField实例)
        self._field_widgets: Dict[str, Tuple[BaseWidget, FormField]] = {}
        
        # 验证状态
        self._validation_errors: Dict[str, str] = {}
        
        # 初始化
        self.initialize()
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建表单视图主组件"""
        # 主面板
        self._main_panel = Panel(
            self._parent,
            widget_id=f"{self.widget_id}_main",
            style={"orientation": "vertical", "fill": "both", "expand": True, "padding": (0, 0)}
        )
        
        # 滚动面板（用于长表单）
        self._scroll_panel = ScrollPanel(
            self._main_panel,
            widget_id=f"{self.widget_id}_scroll",
            style={"orientation": "vertical", "fill": "both", "expand": True}
        )
        
        # 分区容器
        self._sections_panel = Panel(
            self._scroll_panel,
            widget_id=f"{self.widget_id}_sections",
            style={"orientation": "vertical", "padding": (16, 16)}
        )
        
        # 按钮面板
        self._button_panel = Panel(
            self._main_panel,
            widget_id=f"{self.widget_id}_buttons",
            style={"orientation": "horizontal", "padding": (16, 16, 16, 16)}
        )
        
        # 渲染表单（如果有配置）
        if self._form_config:
            self._render_form()
        
        return self._main_panel.get_widget()
    
    def set_form_config(self, form_config: FormConfig) -> None:
        """设置表单配置并重新渲染"""
        self._form_config = form_config
        self._field_widgets.clear()
        self._validation_errors.clear()
        
        # 清除现有内容
        if self._sections_panel and hasattr(self._sections_panel, 'remove_widget'):
            # 移除所有子组件
            for child_id, (widget, _) in list(self._field_widgets.items()):
                self._sections_panel.remove_widget(widget)
        
        # 重新渲染
        self._render_form()
    
    def _render_form(self) -> None:
        """渲染表单"""
        if not self._form_config or not self._sections_panel:
            return
        
        try:
            logger.info(f"渲染表单: {self._form_config.title}")
            
            # 渲染标题
            title_label = Label(
                self._sections_panel,
                text=self._form_config.title,
                widget_id=f"{self.widget_id}_title",
                style={
                    "font": ("Segoe UI", 18, "bold"),
                    "text_color": "#212529",
                    "padding": (0, 0, 0, 16)
                }
            )
            self._sections_panel.add_widget(title_label)
            
            # 渲染描述
            if self._form_config.description:
                desc_label = Label(
                    self._sections_panel,
                    text=self._form_config.description,
                    widget_id=f"{self.widget_id}_description",
                    style={
                        "font": ("Segoe UI", 12),
                        "text_color": "#6c757d",
                        "wraplength": 600,
                        "padding": (0, 0, 0, 24)
                    }
                )
                self._sections_panel.add_widget(desc_label)
            
            # 渲染所有分区
            for section in self._form_config.sections:
                self._render_section(section)
            
            # 渲染按钮
            self._render_buttons()
            
        except Exception as e:
            logger.error(f"表单渲染失败: {e}", exc_info=True)
    
    def _render_section(self, section: FormSection) -> None:
        """渲染表单分区"""
        try:
            # 分区标题
            section_title = Label(
                self._sections_panel,
                text=section.title,
                widget_id=f"{self.widget_id}_section_{section.id}_title",
                style={
                    "font": ("Segoe UI", 14, "bold"),
                    "text_color": "#495057",
                    "padding": (0, 16, 0, 12)
                }
            )
            self._sections_panel.add_widget(section_title)
            
            # 分区描述
            if section.description:
                section_desc = Label(
                    self._sections_panel,
                    text=section.description,
                    widget_id=f"{self.widget_id}_section_{section.id}_desc",
                    style={
                        "font": ("Segoe UI", 11),
                        "text_color": "#6c757d",
                        "wraplength": 600,
                        "padding": (0, 0, 0, 12)
                    }
                )
                self._sections_panel.add_widget(section_desc)
            
            # 创建分区内容面板
            section_panel = Panel(
                self._sections_panel,
                widget_id=f"{self.widget_id}_section_{section.id}_content",
                style={
                    "orientation": section.layout.value,
                    "padding": (0, 0, 0, 24)
                }
            )
            self._sections_panel.add_widget(section_panel)
            
            # 渲染分区内的字段
            for field in section.fields:
                if field.visible:
                    self._render_field(field, section_panel)
            
        except Exception as e:
            logger.error(f"分区渲染失败 {section.id}: {e}", exc_info=True)
    
    def _render_field(self, field: FormField, parent_panel: Panel) -> None:
        """渲染单个字段"""
        try:
            # 创建字段标签
            field_label = Label(
                parent_panel,
                text=f"{field.name}:",
                widget_id=f"{self.widget_id}_field_{field.id}_label",
                style={
                    "font": ("Segoe UI", 11),
                    "text_color": "#495057",
                    "padding": (0, 8, 0, 4)
                }
            )
            parent_panel.add_widget(field_label)
            
            # 渲染字段控件
            field_widget = self._field_renderer.render_field(field)
            if field_widget:
                parent_panel.add_widget(field_widget)
                self._field_widgets[field.id] = (field_widget, field)
                
                # 添加字段描述（如果有）
                if field.description:
                    desc_label = Label(
                        parent_panel,
                        text=field.description,
                        widget_id=f"{self.widget_id}_field_{field.id}_desc",
                        style={
                            "font": ("Segoe UI", 10),
                            "text_color": "#6c757d",
                            "padding": (0, 2, 0, 8)
                        }
                    )
                    parent_panel.add_widget(desc_label)
            
        except Exception as e:
            logger.error(f"字段渲染失败 {field.id}: {e}", exc_info=True)
    
    def _render_buttons(self) -> None:
        """渲染表单按钮"""
        if not self._button_panel:
            return
        
        # 弹性空间
        spacer = Panel(
            self._button_panel,
            widget_id=f"{self.widget_id}_spacer",
            style={"fill": "both", "expand": True}
        )
        self._button_panel.add_widget(spacer)
        
        # 重置按钮（如果启用）
        if self._form_config and self._form_config.show_reset:
            reset_btn = Button(
                self._button_panel,
                text="重置",
                widget_id=f"{self.widget_id}_reset_btn",
                style={
                    "font": ("Segoe UI", 11),
                    "bg_color": "#6c757d",
                    "hover_color": "#545b62",
                    "fg_color": "#ffffff",
                    "corner_radius": 6,
                    "padding": (12, 8),
                    "margin": (0, 0, 8, 0)
                },
                command=self._on_reset_click
            )
            self._button_panel.add_widget(reset_btn)
        
        # 取消按钮（如果启用）
        if self._form_config and self._form_config.show_cancel:
            cancel_btn = Button(
                self._button_panel,
                text=self._form_config.cancel_text or "取消",
                widget_id=f"{self.widget_id}_cancel_btn",
                style={
                    "font": ("Segoe UI", 11),
                    "bg_color": "#6c757d",
                    "hover_color": "#545b62",
                    "fg_color": "#ffffff",
                    "corner_radius": 6,
                    "padding": (12, 8),
                    "margin": (0, 0, 8, 0)
                },
                command=self._on_cancel_click
            )
            self._button_panel.add_widget(cancel_btn)
        
        # 提交按钮
        submit_text = self._form_config.submit_text if self._form_config else "保存"
        submit_btn = Button(
            self._button_panel,
            text=submit_text,
            widget_id=f"{self.widget_id}_submit_btn",
            style={
                "font": ("Segoe UI", 11, "bold"),
                "bg_color": "#007bff",
                "hover_color": "#0056b3",
                "fg_color": "#ffffff",
                "corner_radius": 6,
                "padding": (12, 8)
            },
            command=self._on_submit_click
        )
        self._button_panel.add_widget(submit_btn)
    
    def validate_form(self) -> FormValidationResult:
        """验证整个表单"""
        errors = []
        values = {}
        
        if not self._form_config:
            return FormValidationResult(
                is_valid=False,
                errors=[FieldValidationResult("form", False, "表单配置为空")],
                values={}
            )
        
        # 收集所有字段值
        for field_id, (widget, field) in self._field_widgets.items():
            # 获取UI组件的值
            value = self._field_renderer.get_field_value(widget, field.field_type)
            values[field_id] = value
            
            # 验证字段
            if field.visible and field.enabled:
                # 更新字段值（用于验证）
                success, error_msg = field.update_value(value)
                if not success:
                    errors.append(FieldValidationResult(field_id, False, error_msg))
        
        # 执行表单级别的验证
        if self._form_config.validation_level != ValidationLevel.NONE:
            form_errors = self._form_config.validate_all()
            for section_id, section_errors in form_errors.items():
                for field_id, error_msg in section_errors:
                    errors.append(FieldValidationResult(field_id, False, error_msg))
        
        return FormValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            values=values
        )
    
    def get_form_values(self) -> Dict[str, Any]:
        """获取表单所有值（不验证）"""
        values = {}
        
        for field_id, (widget, field) in self._field_widgets.items():
            value = self._field_renderer.get_field_value(widget, field.field_type)
            values[field_id] = value
        
        return values
    
    def reset_form(self) -> None:
        """重置表单为默认值"""
        if not self._form_config:
            return
        
        try:
            # 重置表单配置
            self._form_config.reset_to_defaults()
            
            # 更新UI组件
            for field_id, (widget, field) in self._field_widgets.items():
                if hasattr(widget, 'set_value'):
                    widget.set_value(field.value if field.value is not None else "")
            
            logger.info(f"表单已重置: {self._form_config.title}")
            
        except Exception as e:
            logger.error(f"表单重置失败: {e}", exc_info=True)
    
    def _on_submit_click(self) -> None:
        """提交按钮点击事件"""
        try:
            # 验证表单
            validation_result = self.validate_form()
            
            if validation_result.is_valid:
                logger.info(f"表单验证通过: {self._form_config.title if self._form_config else 'unknown'}")
                
                # 调用提交回调
                if self._on_submit:
                    self._on_submit(validation_result.values)
                
                # 发布事件
                if self._event_bus and self._form_config:
                    self._event_bus.publish("form.submitted", {
                        "form_id": self._form_config.id,
                        "field_count": len(validation_result.values),
                        "valid": True
                    })
            else:
                logger.warning(f"表单验证失败: {len(validation_result.errors)} 个错误")
                
                # 显示错误信息（TODO: 实现错误UI显示）
                for error in validation_result.errors:
                    logger.warning(f"字段错误: {error.field_id} - {error.message}")
                
                # 发布验证失败事件
                if self._event_bus and self._form_config:
                    self._event_bus.publish("form.validation_failed", {
                        "form_id": self._form_config.id,
                        "error_count": len(validation_result.errors),
                        "errors": [(e.field_id, e.message or "") for e in validation_result.errors]
                    })
            
        except Exception as e:
            logger.error(f"表单提交失败: {e}", exc_info=True)
    
    def _on_cancel_click(self) -> None:
        """取消按钮点击事件"""
        logger.info("表单取消")
        
        if self._on_cancel:
            self._on_cancel()
    
    def _on_reset_click(self) -> None:
        """重置按钮点击事件"""
        self.reset_form()
        
        # 发布事件
        if self._event_bus and self._form_config:
            self._event_bus.publish("form.reset", {
                "form_id": self._form_config.id,
                "timestamp": "now"
            })
    
    # 公共API
    def update_field_value(self, field_id: str, value: Any) -> bool:
        """更新特定字段的值"""
        if field_id not in self._field_widgets:
            return False
        
        widget, field = self._field_widgets[field_id]
        
        try:
            if hasattr(widget, 'set_value'):
                widget.set_value(value)
                
                # 更新字段对象的值
                success, error = field.update_value(value)
                return success
            else:
                return False
                
        except Exception as e:
            logger.error(f"更新字段值失败 {field_id}: {e}", exc_info=True)
            return False
    
    def show_field(self, field_id: str, show: bool = True) -> bool:
        """显示或隐藏字段"""
        # TODO: 实现字段显示/隐藏逻辑
        logger.warning(f"字段显示/隐藏功能暂未实现: {field_id}")
        return False
    
    def enable_field(self, field_id: str, enable: bool = True) -> bool:
        """启用或禁用字段"""
        if field_id not in self._field_widgets:
            return False
        
        widget, field = self._field_widgets[field_id]
        
        try:
            state = "normal" if enable else "disabled"
            widget.set_state(state)
            field.enabled = enable
            return True
            
        except Exception as e:
            logger.error(f"设置字段启用状态失败 {field_id}: {e}", exc_info=True)
            return False
    
    def get_form_config(self) -> Optional[FormConfig]:
        """获取表单配置"""
        return self._form_config
    
    def destroy(self) -> None:
        """销毁组件"""
        self._field_renderer.clear_cache()
        self._field_widgets.clear()
        super().destroy()


# 导出
__all__ = [
    "ConfigFormView",
    "FieldValidationResult", 
    "FormValidationResult"
]