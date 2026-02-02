"""
动态表单生成服务

基于JSON Schema自动生成配置表单，支持：
1. 多种表单控件类型
2. 实时验证和反馈
3. 条件显示逻辑
4. 嵌套对象和数组
5. 国际化支持
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Set
from pathlib import Path

from ..core.logging import get_logger
from ..core.events import EventBus

logger = get_logger(__name__)


class FormFieldType(str, Enum):
    """表单字段类型枚举"""
    TEXT = "text"                # 文本输入
    NUMBER = "number"            # 数字输入
    INTEGER = "integer"          # 整数输入
    BOOLEAN = "boolean"          # 布尔开关
    SELECT = "select"            # 下拉选择
    MULTISELECT = "multiselect"  # 多选
    SLIDER = "slider"            # 滑块
    COLOR = "color"              # 颜色选择器
    FILE = "file"                # 文件选择
    FOLDER = "folder"            # 文件夹选择
    TEXTAREA = "textarea"        # 多行文本
    CODE = "code"                # 代码编辑器
    DATE = "date"                # 日期选择
    TIME = "time"                # 时间选择
    DATETIME = "datetime"        # 日期时间选择
    OBJECT = "object"            # 嵌套对象
    ARRAY = "array"              # 数组列表
    GROUP = "group"              # 分组容器


class ValidationLevel(str, Enum):
    """验证级别枚举"""
    NONE = "none"                # 不验证
    BASIC = "basic"              # 基本验证（类型和必填）
    STRICT = "strict"            # 严格验证（所有约束）
    LIVE = "live"                # 实时验证（输入时验证）


class LayoutDirection(str, Enum):
    """布局方向枚举"""
    VERTICAL = "vertical"        # 垂直布局
    HORIZONTAL = "horizontal"    # 水平布局
    GRID = "grid"                # 网格布局
    INLINE = "inline"            # 内联布局


@dataclass
class FormFieldValidation:
    """表单字段验证规则"""
    
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    exclusive_minimum: Optional[Union[int, float]] = None
    exclusive_maximum: Optional[Union[int, float]] = None
    multiple_of: Optional[Union[int, float]] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    unique_items: Optional[bool] = None
    
    # 自定义验证函数
    custom_validator: Optional[Callable[[Any], Tuple[bool, str]]] = None
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """验证字段值"""
        # 必填验证
        if self.required and (value is None or value == ""):
            return False, "此字段是必填项"
        
        # 如果值为空且不是必填，直接通过
        if value is None or value == "":
            return True, None
        
        # 字符串长度验证
        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                return False, f"长度不能少于 {self.min_length} 个字符"
            if self.max_length is not None and len(value) > self.max_length:
                return False, f"长度不能超过 {self.max_length} 个字符"
            if self.pattern is not None:
                try:
                    if not re.match(self.pattern, value):
                        return False, "格式不符合要求"
                except re.error:
                    logger.warning(f"无效的正则表达式模式: {self.pattern}")
        
        # 数字范围验证
        if isinstance(value, (int, float)):
            if self.minimum is not None and value < self.minimum:
                return False, f"值不能小于 {self.minimum}"
            if self.maximum is not None and value > self.maximum:
                return False, f"值不能大于 {self.maximum}"
            if self.exclusive_minimum is not None and value <= self.exclusive_minimum:
                return False, f"值必须大于 {self.exclusive_minimum}"
            if self.exclusive_maximum is not None and value >= self.exclusive_maximum:
                return False, f"值必须小于 {self.exclusive_maximum}"
            if self.multiple_of is not None and value % self.multiple_of != 0:
                return False, f"值必须是 {self.multiple_of} 的倍数"
        
        # 数组验证
        if isinstance(value, list):
            if self.min_items is not None and len(value) < self.min_items:
                return False, f"至少需要 {self.min_items} 个项目"
            if self.max_items is not None and len(value) > self.max_items:
                return False, f"最多允许 {self.max_items} 个项目"
            if self.unique_items and len(value) != len(set(value)):
                return False, "所有项目必须是唯一的"
        
        # 自定义验证
        if self.custom_validator:
            try:
                return self.custom_validator(value)
            except Exception as e:
                logger.error(f"自定义验证器执行失败: {e}")
                return False, "验证失败"
        
        return True, None


@dataclass
class FormField:
    """表单字段定义"""
    
    id: str                      # 字段唯一标识
    name: str                    # 字段名称（用于显示）
    field_type: FormFieldType    # 字段类型
    
    # 值相关
    value: Any = None            # 当前值
    default_value: Any = None    # 默认值
    
    # 配置选项
    options: List[Any] = field(default_factory=list)  # 选择项（用于select/multiselect）
    placeholder: Optional[str] = None  # 占位符文本
    description: Optional[str] = None  # 描述文本
    tooltip: Optional[str] = None      # 工具提示
    
    # 布局配置
    width: Optional[int] = None        # 宽度（像素或百分比）
    height: Optional[int] = None       # 高度（像素或百分比）
    order: int = 0                     # 显示顺序
    colspan: int = 1                   # 网格列跨度
    rowspan: int = 1                   # 网格行跨度
    
    # 验证配置
    validation: FormFieldValidation = field(default_factory=FormFieldValidation)
    validation_level: ValidationLevel = ValidationLevel.BASIC
    
    # 条件显示
    depends_on: Optional[str] = None   # 依赖的字段ID
    condition: Optional[Dict[str, Any]] = None  # 显示条件
    
    # 状态
    enabled: bool = True               # 是否启用
    visible: bool = True               # 是否可见
    read_only: bool = False            # 是否只读
    
    # 样式
    css_class: Optional[str] = None    # CSS类名
    style: Optional[Dict[str, str]] = None  # 内联样式
    
    def __post_init__(self):
        """数据验证"""
        if not self.id:
            raise ValueError("字段ID不能为空")
        if not self.name:
            raise ValueError("字段名称不能为空")
        
        # 设置默认值
        if self.value is None and self.default_value is not None:
            self.value = self.default_value
    
    @property
    def is_valid(self) -> Tuple[bool, Optional[str]]:
        """检查字段值是否有效"""
        if self.validation_level == ValidationLevel.NONE:
            return True, None
        
        return self.validation.validate(self.value)
    
    @property
    def display_value(self) -> str:
        """获取显示值"""
        if self.value is None:
            return ""
        
        if isinstance(self.value, (list, dict)):
            return json.dumps(self.value, ensure_ascii=False, indent=2)
        
        return str(self.value)
    
    def update_value(self, new_value: Any) -> Tuple[bool, Optional[str]]:
        """
        更新字段值
        
        Returns:
            (是否成功, 错误信息)
        """
        # 类型转换
        converted_value = self._convert_value(new_value)
        
        # 验证
        is_valid, error = self.validation.validate(converted_value)
        if is_valid:
            self.value = converted_value
            return True, None
        else:
            return False, error
    
    def _convert_value(self, value: Any) -> Any:
        """根据字段类型转换值"""
        if value is None or value == "":
            return None
        
        try:
            if self.field_type == FormFieldType.INTEGER:
                return int(value)
            elif self.field_type == FormFieldType.NUMBER:
                return float(value)
            elif self.field_type == FormFieldType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    lower = value.lower()
                    return lower in ["true", "1", "yes", "on"]
                return bool(value)
            elif self.field_type == FormFieldType.TEXT:
                return str(value)
            elif self.field_type in [FormFieldType.TEXTAREA, FormFieldType.CODE]:
                return str(value)
            elif self.field_type == FormFieldType.SELECT:
                return str(value)
            elif self.field_type == FormFieldType.MULTISELECT:
                if isinstance(value, list):
                    return value
                if isinstance(value, str):
                    # 尝试解析JSON数组
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    # 逗号分隔的字符串
                    return [item.strip() for item in value.split(",") if item.strip()]
                return []
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning(f"值转换失败: {value} -> {self.field_type}: {e}")
            return value
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        config = {
            "id": self.id,
            "name": self.name,
            "type": self.field_type.value,
            "value": self.value,
            "default_value": self.default_value,
            "placeholder": self.placeholder or "",
            "description": self.description or "",
            "tooltip": self.tooltip or "",
            "order": self.order,
            "colspan": self.colspan,
            "rowspan": self.rowspan,
            "enabled": self.enabled,
            "visible": self.visible,
            "read_only": self.read_only,
            "css_class": self.css_class or "",
            "style": self.style or {},
            "validation": {
                "required": self.validation.required,
                "min_length": self.validation.min_length,
                "max_length": self.validation.max_length,
                "minimum": self.validation.minimum,
                "maximum": self.validation.maximum
            }
        }
        
        # 添加选项（如果有）
        if self.options:
            config["options"] = self.options
        
        # 添加条件显示（如果有）
        if self.depends_on or self.condition:
            config["conditional"] = {
                "depends_on": self.depends_on,
                "condition": self.condition
            }
        
        return config


@dataclass
class FormSection:
    """表单分区"""
    
    id: str                      # 分区唯一标识
    title: str                   # 分区标题
    description: Optional[str] = None  # 分区描述
    
    # 布局配置
    layout: LayoutDirection = LayoutDirection.VERTICAL
    columns: int = 1             # 网格列数（仅对GRID布局有效）
    collapsed: bool = False      # 是否默认折叠
    collapsible: bool = True     # 是否可折叠
    
    # 字段
    fields: List[FormField] = field(default_factory=list)
    
    # 样式
    css_class: Optional[str] = None
    style: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """数据验证"""
        if not self.id:
            raise ValueError("分区ID不能为空")
        if not self.title:
            raise ValueError("分区标题不能为空")
        
        # 按order排序字段
        self.fields.sort(key=lambda x: x.order)
    
    def add_field(self, field: FormField) -> None:
        """添加字段"""
        self.fields.append(field)
        self.fields.sort(key=lambda x: x.order)
    
    def remove_field(self, field_id: str) -> bool:
        """移除字段"""
        for i, field in enumerate(self.fields):
            if field.id == field_id:
                self.fields.pop(i)
                return True
        return False
    
    def get_field(self, field_id: str) -> Optional[FormField]:
        """获取字段"""
        for field in self.fields:
            if field.id == field_id:
                return field
        return None
    
    def validate_all(self) -> List[Tuple[str, str]]:
        """验证所有字段"""
        errors = []
        for field in self.fields:
            if field.visible and field.enabled:
                is_valid, error = field.is_valid
                if not is_valid:
                    errors.append((field.id, error or "验证失败"))
        return errors
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description or "",
            "layout": self.layout.value,
            "columns": self.columns,
            "collapsed": self.collapsed,
            "collapsible": self.collapsible,
            "fields": [field.get_ui_config() for field in self.fields],
            "css_class": self.css_class or "",
            "style": self.style or {}
        }


@dataclass
class FormConfig:
    """完整表单配置"""
    
    id: str                      # 表单唯一标识
    title: str                   # 表单标题
    description: Optional[str] = None  # 表单描述
    
    # 布局
    sections: List[FormSection] = field(default_factory=list)
    layout: LayoutDirection = LayoutDirection.VERTICAL
    
    # 验证配置
    validation_level: ValidationLevel = ValidationLevel.BASIC
    live_validation: bool = True  # 实时验证
    validation_debounce_ms: int = 300  # 验证防抖时间
    
    # 提交配置
    submit_text: str = "保存"
    cancel_text: str = "取消"
    show_reset: bool = True
    show_cancel: bool = True
    
    # 状态
    enabled: bool = True
    auto_save: bool = False
    auto_save_interval_s: int = 60
    
    def __post_init__(self):
        """数据验证"""
        if not self.id:
            raise ValueError("表单ID不能为空")
        if not self.title:
            raise ValueError("表单标题不能为空")
        
        # 按标题排序分区（如果需要的话）
        # self.sections.sort(key=lambda x: x.title)
    
    def add_section(self, section: FormSection) -> None:
        """添加分区"""
        self.sections.append(section)
    
    def remove_section(self, section_id: str) -> bool:
        """移除分区"""
        for i, section in enumerate(self.sections):
            if section.id == section_id:
                self.sections.pop(i)
                return True
        return False
    
    def get_section(self, section_id: str) -> Optional[FormSection]:
        """获取分区"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_field(self, field_id: str) -> Optional[FormField]:
        """获取字段（在所有分区中查找）"""
        for section in self.sections:
            field = section.get_field(field_id)
            if field:
                return field
        return None
    
    def validate_all(self) -> Dict[str, List[Tuple[str, str]]]:
        """验证所有分区和字段"""
        errors = {}
        for section in self.sections:
            section_errors = section.validate_all()
            if section_errors:
                errors[section.id] = section_errors
        return errors
    
    def get_values(self) -> Dict[str, Any]:
        """获取所有字段值"""
        values = {}
        for section in self.sections:
            for field in section.fields:
                if field.visible:
                    values[field.id] = field.value
        return values
    
    def set_values(self, values: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        设置字段值
        
        Returns:
            错误列表 [(字段ID, 错误信息), ...]
        """
        errors = []
        for section in self.sections:
            for field in section.fields:
                if field.id in values:
                    success, error = field.update_value(values[field.id])
                    if not success:
                        errors.append((field.id, error or "值设置失败"))
        return errors
    
    def reset_to_defaults(self) -> None:
        """重置所有字段为默认值"""
        for section in self.sections:
            for field in section.fields:
                field.value = field.default_value
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description or "",
            "layout": self.layout.value,
            "sections": [section.get_ui_config() for section in self.sections],
            "validation_level": self.validation_level.value,
            "live_validation": self.live_validation,
            "validation_debounce_ms": self.validation_debounce_ms,
            "submit_text": self.submit_text,
            "cancel_text": self.cancel_text,
            "show_reset": self.show_reset,
            "show_cancel": self.show_cancel,
            "enabled": self.enabled,
            "auto_save": self.auto_save,
            "auto_save_interval_s": self.auto_save_interval_s
        }


class ConfigFormService:
    """
    动态表单生成服务
    
    将JSON Schema转换为交互式表单配置，支持：
    1. 自动推断字段类型
    2. 生成验证规则
    3. 创建布局结构
    4. 处理嵌套对象和数组
    """
    
    # JSON Schema类型到表单字段类型的映射
    TYPE_MAPPINGS = {
        "string": FormFieldType.TEXT,
        "number": FormFieldType.NUMBER,
        "integer": FormFieldType.INTEGER,
        "boolean": FormFieldType.BOOLEAN,
        "array": FormFieldType.ARRAY,
        "object": FormFieldType.OBJECT
    }
    
    # 格式到字段类型的映射
    FORMAT_MAPPINGS = {
        "email": FormFieldType.TEXT,
        "uri": FormFieldType.TEXT,
        "url": FormFieldType.TEXT,
        "date": FormFieldType.DATE,
        "time": FormFieldType.TIME,
        "date-time": FormFieldType.DATETIME,
        "color": FormFieldType.COLOR,
        "textarea": FormFieldType.TEXTAREA,
        "code": FormFieldType.CODE,
        "file": FormFieldType.FILE,
        "folder": FormFieldType.FOLDER
    }
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        初始化表单生成服务
        
        Args:
            event_bus: 事件总线（可选）
        """
        self._event_bus = event_bus
        self._form_cache: Dict[str, FormConfig] = {}
        self._schema_cache: Dict[str, Dict] = {}
        
        logger.debug("动态表单生成服务初始化")
    
    def create_form_from_schema(
        self,
        schema_id: str,
        schema: Dict[str, Any],
        default_values: Optional[Dict[str, Any]] = None,
        form_title: Optional[str] = None,
        form_description: Optional[str] = None
    ) -> FormConfig:
        """
        从JSON Schema创建表单配置
        
        Args:
            schema_id: Schema唯一标识符
            schema: JSON Schema定义
            default_values: 默认值（可选）
            form_title: 表单标题（可选）
            form_description: 表单描述（可选）
            
        Returns:
            表单配置对象
        """
        logger.debug_struct("从Schema创建表单", schema_id=schema_id)
        
        # 检查缓存
        cache_key = f"{schema_id}_{json.dumps(schema, sort_keys=True)}"
        if cache_key in self._form_cache:
            logger.debug("使用缓存表单配置", schema_id=schema_id)
            return self._form_cache[cache_key]
        
        try:
            # 保存Schema到缓存
            self._schema_cache[schema_id] = schema
            
            # 确定表单标题和描述
            title = form_title or schema.get("title", "配置表单")
            description = form_description or schema.get("description", "")
            
            # 创建表单配置
            form_config = FormConfig(
                id=schema_id,
                title=title,
                description=description,
                layout=LayoutDirection.VERTICAL
            )
            
            # 处理Schema
            schema_type = schema.get("type", "object")
            
            if schema_type == "object":
                # 创建主分区
                main_section = FormSection(
                    id="main",
                    title="基本配置",
                    description=schema.get("description", "")
                )
                
                # 处理属性
                properties = schema.get("properties", {})
                required = set(schema.get("required", []))
                
                for prop_name, prop_schema in properties.items():
                    # 创建字段
                    field = self._create_field_from_schema(
                        field_id=prop_name,
                        schema=prop_schema,
                        is_required=prop_name in required
                    )
                    
                    if field:
                        main_section.add_field(field)
                
                form_config.add_section(main_section)
                
            elif schema_type == "array":
                # 对于数组类型，创建一个特殊的数组分区
                items_schema = schema.get("items", {})
                
                array_section = FormSection(
                    id="array_items",
                    title="项目列表",
                    description="配置列表项",
                    layout=LayoutDirection.VERTICAL
                )
                
                # 创建一个示例项字段
                sample_field = self._create_field_from_schema(
                    field_id="item_0",
                    schema=items_schema,
                    is_required=False
                )
                
                if sample_field:
                    sample_field.name = "示例项"
                    sample_field.description = "数组中的项目示例"
                    array_section.add_field(sample_field)
                
                form_config.add_section(array_section)
            
            else:
                # 简单类型，创建一个分区包含单个字段
                simple_section = FormSection(
                    id="simple",
                    title="配置",
                    description=""
                )
                
                field = self._create_field_from_schema(
                    field_id="value",
                    schema=schema,
                    is_required=True
                )
                
                if field:
                    simple_section.add_field(field)
                
                form_config.add_section(simple_section)
            
            # 应用默认值
            if default_values:
                errors = form_config.set_values(default_values)
                if errors:
                    logger.warning("应用默认值时出现错误", errors=errors)
            
            # 缓存表单配置
            self._form_cache[cache_key] = form_config
            
            # 发布表单创建事件
            if self._event_bus:
                self._event_bus.publish("form.created", {
                    "schema_id": schema_id,
                    "field_count": sum(len(s.fields) for s in form_config.sections),
                    "timestamp": "now"
                })
            
            logger.info_struct("表单创建成功",
                             schema_id=schema_id,
                             sections=len(form_config.sections),
                             fields=sum(len(s.fields) for s in form_config.sections))
            
            return form_config
            
        except Exception as e:
            logger.error("表单创建失败", schema_id=schema_id, error=str(e), exc_info=True)
            raise
    
    def _create_field_from_schema(
        self,
        field_id: str,
        schema: Dict[str, Any],
        is_required: bool = False
    ) -> Optional[FormField]:
        """从Schema创建字段"""
        try:
            # 获取字段类型
            schema_type = schema.get("type", "string")
            schema_format = schema.get("format")
            
            # 确定字段类型
            field_type = self._determine_field_type(schema_type, schema_format, schema)
            
            # 获取字段名称
            field_name = schema.get("title", field_id)
            
            # 创建验证规则
            validation = self._create_validation_from_schema(schema, is_required)
            
            # 获取默认值
            default_value = schema.get("default")
            
            # 获取枚举选项
            options = []
            enum_values = schema.get("enum")
            if enum_values:
                options = enum_values
            
            # 获取描述
            description = schema.get("description", "")
            
            # 创建字段
            field = FormField(
                id=field_id,
                name=field_name,
                field_type=field_type,
                default_value=default_value,
                options=options,
                description=description,
                validation=validation,
                order=schema.get("order", 0)
            )
            
            # 处理特殊配置
            self._apply_special_config(field, schema)
            
            return field
            
        except Exception as e:
            logger.warning("字段创建失败", field_id=field_id, error=str(e))
            return None
    
    def _determine_field_type(
        self,
        schema_type: str,
        schema_format: Optional[str],
        schema: Dict[str, Any]
    ) -> FormFieldType:
        """确定字段类型"""
        # 首先检查格式映射
        if schema_format and schema_format in self.FORMAT_MAPPINGS:
            return self.FORMAT_MAPPINGS[schema_format]
        
        # 检查特殊关键字
        if "enum" in schema:
            if schema.get("multipleOf") or schema.get("uniqueItems"):
                return FormFieldType.MULTISELECT
            return FormFieldType.SELECT
        
        # 检查UI提示
        ui_hint = schema.get("x-ui", {})
        if "widget" in ui_hint:
            widget_type = ui_hint["widget"]
            try:
                return FormFieldType(widget_type)
            except ValueError:
                pass
        
        # 使用类型映射
        if schema_type in self.TYPE_MAPPINGS:
            return self.TYPE_MAPPINGS[schema_type]
        
        # 默认为文本类型
        return FormFieldType.TEXT
    
    def _create_validation_from_schema(
        self,
        schema: Dict[str, Any],
        is_required: bool
    ) -> FormFieldValidation:
        """从Schema创建验证规则"""
        validation = FormFieldValidation(required=is_required)
        
        # 字符串验证
        if "minLength" in schema:
            validation.min_length = schema["minLength"]
        if "maxLength" in schema:
            validation.max_length = schema["maxLength"]
        if "pattern" in schema:
            validation.pattern = schema["pattern"]
        
        # 数字验证
        if "minimum" in schema:
            validation.minimum = schema["minimum"]
        if "maximum" in schema:
            validation.maximum = schema["maximum"]
        if "exclusiveMinimum" in schema:
            validation.exclusive_minimum = schema["exclusiveMinimum"]
        if "exclusiveMaximum" in schema:
            validation.exclusive_maximum = schema["exclusiveMaximum"]
        if "multipleOf" in schema:
            validation.multiple_of = schema["multipleOf"]
        
        # 数组验证
        if "minItems" in schema:
            validation.min_items = schema["minItems"]
        if "maxItems" in schema:
            validation.max_items = schema["maxItems"]
        if "uniqueItems" in schema:
            validation.unique_items = schema["uniqueItems"]
        
        return validation
    
    def _apply_special_config(self, field: FormField, schema: Dict[str, Any]) -> None:
        """应用特殊配置"""
        # UI提示
        ui_hint = schema.get("x-ui", {})
        
        if "placeholder" in ui_hint:
            field.placeholder = ui_hint["placeholder"]
        if "tooltip" in ui_hint:
            field.tooltip = ui_hint["tooltip"]
        if "readOnly" in ui_hint:
            field.read_only = ui_hint["readOnly"]
        if "enabled" in ui_hint:
            field.enabled = ui_hint["enabled"]
        if "visible" in ui_hint:
            field.visible = ui_hint["visible"]
        
        # 布局配置
        if "width" in ui_hint:
            field.width = ui_hint["width"]
        if "height" in ui_hint:
            field.height = ui_hint["height"]
        if "colspan" in ui_hint:
            field.colspan = ui_hint["colspan"]
        if "rowspan" in ui_hint:
            field.rowspan = ui_hint["rowspan"]
        
        # 条件显示
        if "dependsOn" in ui_hint:
            field.depends_on = ui_hint["dependsOn"]
        if "condition" in ui_hint:
            field.condition = ui_hint["condition"]
        
        # 样式
        if "cssClass" in ui_hint:
            field.css_class = ui_hint["cssClass"]
        if "style" in ui_hint:
            field.style = ui_hint["style"]
    
    def update_form_with_values(
        self,
        form_config: FormConfig,
        new_values: Dict[str, Any]
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        使用新值更新表单
        
        Returns:
            (是否全部成功, 错误列表)
        """
        errors = form_config.set_values(new_values)
        success = len(errors) == 0
        
        # 发布表单更新事件
        if self._event_bus and success:
            self._event_bus.publish("form.updated", {
                "form_id": form_config.id,
                "field_count": len(new_values),
                "timestamp": "now"
            })
        
        return success, errors
    
    def validate_form(self, form_config: FormConfig) -> Dict[str, List[Tuple[str, str]]]:
        """验证表单"""
        return form_config.validate_all()
    
    def get_form_values(self, form_config: FormConfig) -> Dict[str, Any]:
        """获取表单所有值"""
        return form_config.get_values()
    
    def reset_form(self, form_config: FormConfig) -> None:
        """重置表单为默认值"""
        form_config.reset_to_defaults()
        
        # 发布重置事件
        if self._event_bus:
            self._event_bus.publish("form.reset", {
                "form_id": form_config.id,
                "timestamp": "now"
            })
    
    def export_form_config(self, form_config: FormConfig, format: str = "json") -> str:
        """导出表单配置"""
        if format == "json":
            return json.dumps(form_config.get_ui_config(), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def import_form_config(self, config_str: str, format: str = "json") -> Optional[FormConfig]:
        """导入表单配置"""
        # TODO: 实现导入功能
        logger.warning("表单配置导入功能暂未实现")
        return None
    
    def clear_cache(self, schema_id: Optional[str] = None) -> None:
        """清除缓存"""
        if schema_id:
            # 清除指定Schema的缓存
            keys_to_remove = [k for k in self._form_cache.keys() if k.startswith(schema_id)]
            for key in keys_to_remove:
                del self._form_cache[key]
            
            if schema_id in self._schema_cache:
                del self._schema_cache[schema_id]
        else:
            # 清除所有缓存
            self._form_cache.clear()
            self._schema_cache.clear()
        
        logger.debug("表单缓存已清除", schema_id=schema_id or "all")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "cached_forms": len(self._form_cache),
            "cached_schemas": len(self._schema_cache),
            "event_bus_connected": self._event_bus is not None
        }