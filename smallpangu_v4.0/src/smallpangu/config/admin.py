"""
管理后台配置模型

定义管理后台专用的配置模型，包括：
1. 模块注册配置
2. 界面布局配置
3. 热重载策略配置
4. 用户界面偏好
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, ConfigDict

from ..core.logging import get_logger

logger = get_logger(__name__)


class AdminLayout(str, Enum):
    """管理后台布局模式"""
    DASHBOARD = "dashboard"      # 仪表盘模式
    SIDEBAR = "sidebar"          # 侧边栏模式
    COMPACT = "compact"          # 紧凑模式
    EXPERT = "expert"            # 专家模式


class ModuleDisplayMode(str, Enum):
    """模块显示模式"""
    CARD = "card"                # 卡片模式
    LIST = "list"                # 列表模式
    TREE = "tree"                # 树形模式
    GRID = "grid"                # 网格模式


class ConfigValidationLevel(str, Enum):
    """配置验证级别"""
    NONE = "none"                # 不验证
    BASIC = "basic"              # 基本验证（类型检查）
    STRICT = "strict"            # 严格验证（Schema验证）
    EXTREME = "extreme"          # 极端验证（值域和依赖）


class AdminModuleConfig(BaseModel):
    """单个模块的管理配置"""
    
    module_id: str = Field(description="模块唯一标识符")
    display_name: str = Field(description="显示名称")
    category: str = Field(default="plugin", description="模块分类")
    
    # 显示配置
    icon: Optional[str] = Field(default=None, description="图标标识")
    priority: int = Field(default=100, ge=0, le=1000, description="显示优先级")
    visible: bool = Field(default=True, description="是否显示")
    collapsed: bool = Field(default=False, description="是否默认折叠")
    
    # 功能配置
    reload_strategy: str = Field(default="restart", description="热重载策略")
    config_editable: bool = Field(default=True, description="配置是否可编辑")
    requires_confirmation: bool = Field(default=False, description="是否需要确认")
    
    # 验证配置
    validation_level: ConfigValidationLevel = Field(
        default=ConfigValidationLevel.BASIC,
        description="配置验证级别"
    )
    
    # 权限配置（预留，用于未来扩展）
    permissions: List[str] = Field(default_factory=list, description="所需权限")
    
    @validator("reload_strategy")
    def validate_reload_strategy(cls, v):
        """验证热重载策略"""
        valid_strategies = ["immediate", "real_time", "restart", "manual"]
        if v not in valid_strategies:
            raise ValueError(f"热重载策略必须是: {', '.join(valid_strategies)}")
        return v
    
    @validator("category")
    def validate_category(cls, v):
        """验证模块分类"""
        valid_categories = [
            "ai", "plugin", "system", "ui", "data", 
            "security", "monitor", "developer", "custom"
        ]
        if v not in valid_categories:
            raise ValueError(f"模块分类必须是: {', '.join(valid_categories)}")
        return v


class AdminLayoutConfig(BaseModel):
    """管理后台布局配置"""
    
    layout_mode: AdminLayout = Field(default=AdminLayout.DASHBOARD, description="布局模式")
    module_display_mode: ModuleDisplayMode = Field(
        default=ModuleDisplayMode.CARD,
        description="模块显示模式"
    )
    
    # 界面配置
    show_category_tabs: bool = Field(default=True, description="显示分类标签页")
    show_search_bar: bool = Field(default=True, description="显示搜索栏")
    show_stats_panel: bool = Field(default=True, description="显示统计面板")
    show_quick_actions: bool = Field(default=True, description="显示快捷操作")
    show_recent_changes: bool = Field(default=True, description="显示最近变更")
    
    # 布局尺寸
    sidebar_width: int = Field(default=240, ge=150, le=500, description="侧边栏宽度")
    card_width: int = Field(default=300, ge=200, le=500, description="卡片宽度")
    card_height: int = Field(default=180, ge=120, le=400, description="卡片高度")
    
    # 响应式配置
    responsive_breakpoints: Dict[str, int] = Field(
        default_factory=lambda: {
            "mobile": 768,
            "tablet": 1024,
            "desktop": 1280,
            "wide": 1600
        },
        description="响应式断点"
    )
    
    @validator("sidebar_width", "card_width", "card_height")
    def validate_dimensions(cls, v, field):
        """验证尺寸参数"""
        if v <= 0:
            raise ValueError(f"{field.name} 必须大于0")
        return v


class AdminFeatureConfig(BaseModel):
    """管理后台功能配置"""
    
    # 配置管理功能
    enable_config_history: bool = Field(default=True, description="启用配置历史")
    max_history_entries: int = Field(default=50, ge=1, le=1000, description="最大历史记录数")
    enable_config_diff: bool = Field(default=True, description="启用配置差异对比")
    enable_config_export: bool = Field(default=True, description="启用配置导出")
    
    # 热重载功能
    enable_hot_reload: bool = Field(default=True, description="启用热重载")
    hot_reload_delay_ms: int = Field(default=500, ge=0, le=5000, description="热重载延迟（毫秒）")
    enable_auto_save: bool = Field(default=True, description="启用自动保存")
    auto_save_interval_s: int = Field(default=60, ge=5, le=3600, description="自动保存间隔（秒）")
    
    # 验证功能
    enable_live_validation: bool = Field(default=True, description="启用实时验证")
    validation_debounce_ms: int = Field(default=300, ge=0, le=2000, description="验证防抖时间（毫秒）")
    show_validation_errors: bool = Field(default=True, description="显示验证错误")
    
    # 开发者功能
    enable_developer_mode: bool = Field(default=False, description="启用开发者模式")
    show_internal_modules: bool = Field(default=False, description="显示内部模块")
    enable_performance_monitoring: bool = Field(default=False, description="启用性能监控")
    
    @validator("max_history_entries")
    def validate_history_entries(cls, v):
        """验证历史记录数量"""
        if v < 1:
            return 1
        return min(v, 1000)
    
    @validator("hot_reload_delay_ms")
    def validate_hot_reload_delay(cls, v):
        """验证热重载延迟"""
        if v < 0:
            return 0
        return min(v, 5000)
    
    @validator("auto_save_interval_s")
    def validate_auto_save_interval(cls, v):
        """验证自动保存间隔"""
        if v < 5:
            return 5
        return min(v, 3600)


class AdminUIConfig(BaseModel):
    """管理后台界面配置"""
    
    # 主题配置
    theme: str = Field(default="admin-dark", description="主题名称")
    accent_color: str = Field(default="#3b82f6", description="强调色")
    background_color: str = Field(default="#1e1e2e", description="背景色")
    text_color: str = Field(default="#ffffff", description="文字颜色")
    
    # 字体配置
    font_family: str = Field(default="'Microsoft YaHei', 'Segoe UI', sans-serif", description="字体家族")
    font_size_base: int = Field(default=14, ge=10, le=24, description="基础字体大小（px）")
    line_height: float = Field(default=1.5, ge=1.0, le=2.0, description="行高倍数")
    
    # 动画配置
    enable_animations: bool = Field(default=True, description="启用动画")
    animation_duration_ms: int = Field(default=200, ge=0, le=1000, description="动画持续时间（毫秒）")
    enable_transitions: bool = Field(default=True, description="启用过渡效果")
    
    # 交互配置
    hover_effect: bool = Field(default=True, description="启用悬停效果")
    focus_ring: bool = Field(default=True, description="启用焦点环")
    smooth_scrolling: bool = Field(default=True, description="启用平滑滚动")
    
    @validator("accent_color", "background_color", "text_color")
    def validate_color_format(cls, v):
        """验证颜色格式"""
        import re
        # 支持 HEX、RGB、RGBA、HSL、HSLA
        color_pattern = re.compile(
            r'^(#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})|'
            r'rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)|'
            r'rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*(0|1|0?\.\d+)\s*\)|'
            r'hsl\(\s*\d{1,3}\s*,\s*\d{1,3}%\s*,\s*\d{1,3}%\s*\)|'
            r'hsla\(\s*\d{1,3}\s*,\s*\d{1,3}%\s*,\s*\d{1,3}%\s*,\s*(0|1|0?\.\d+)\s*\))$'
        )
        if not color_pattern.match(v):
            raise ValueError(f"无效的颜色格式: {v}")
        return v
    
    @validator("font_size_base")
    def validate_font_size(cls, v):
        """验证字体大小"""
        if v < 10:
            return 10
        if v > 24:
            return 24
        return v


class AdminNotificationConfig(BaseModel):
    """管理后台通知配置"""
    
    # 通知类型
    enable_success_notifications: bool = Field(default=True, description="启用成功通知")
    enable_warning_notifications: bool = Field(default=True, description="启用警告通知")
    enable_error_notifications: bool = Field(default=True, description="启用错误通知")
    enable_info_notifications: bool = Field(default=True, description="启用信息通知")
    
    # 通知显示
    notification_duration_ms: int = Field(default=3000, ge=1000, le=10000, description="通知显示时长（毫秒）")
    notification_position: str = Field(default="top-right", description="通知位置")
    max_notifications: int = Field(default=3, ge=1, le=10, description="最大同时显示通知数")
    
    # 声音提醒
    enable_sound_effects: bool = Field(default=False, description="启用声音效果")
    sound_volume: float = Field(default=0.5, ge=0.0, le=1.0, description="音量")
    
    @validator("notification_position")
    def validate_notification_position(cls, v):
        """验证通知位置"""
        valid_positions = ["top-left", "top-center", "top-right", 
                          "bottom-left", "bottom-center", "bottom-right"]
        if v not in valid_positions:
            raise ValueError(f"通知位置必须是: {', '.join(valid_positions)}")
        return v


class AdminBackupConfig(BaseModel):
    """管理后台备份配置"""
    
    # 自动备份
    enable_auto_backup: bool = Field(default=True, description="启用自动备份")
    backup_interval_hours: int = Field(default=24, ge=1, le=168, description="备份间隔（小时）")
    max_backup_count: int = Field(default=10, ge=1, le=100, description="最大备份数量")
    
    # 备份内容
    backup_configurations: bool = Field(default=True, description="备份配置")
    backup_module_settings: bool = Field(default=True, description="备份模块设置")
    backup_ui_state: bool = Field(default=True, description="备份UI状态")
    backup_user_preferences: bool = Field(default=True, description="备份用户偏好")
    
    # 备份存储
    backup_location: str = Field(default="./backups/admin", description="备份存储位置")
    compression_enabled: bool = Field(default=True, description="启用压缩")
    encryption_enabled: bool = Field(default=False, description="启用加密")
    
    @validator("backup_location")
    def validate_backup_location(cls, v):
        """验证备份位置"""
        if not v:
            raise ValueError("备份位置不能为空")
        return v


class AdminConfig(BaseModel):
    """管理后台完整配置"""
    
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        json_schema_extra={
            "title": "小盘古管理后台配置",
            "description": "统一管理后台的完整配置定义"
        }
    )
    
    # 基本配置
    enabled: bool = Field(default=True, description="是否启用管理后台")
    version: str = Field(default="1.0.0", description="配置版本")
    
    # 模块配置
    modules: Dict[str, AdminModuleConfig] = Field(
        default_factory=dict,
        description="模块管理配置"
    )
    
    # 布局配置
    layout: AdminLayoutConfig = Field(
        default_factory=AdminLayoutConfig,
        description="布局配置"
    )
    
    # 功能配置
    features: AdminFeatureConfig = Field(
        default_factory=AdminFeatureConfig,
        description="功能配置"
    )
    
    # 界面配置
    ui: AdminUIConfig = Field(
        default_factory=AdminUIConfig,
        description="界面配置"
    )
    
    # 通知配置
    notifications: AdminNotificationConfig = Field(
        default_factory=AdminNotificationConfig,
        description="通知配置"
    )
    
    # 备份配置
    backup: AdminBackupConfig = Field(
        default_factory=AdminBackupConfig,
        description="备份配置"
    )
    
    def get_module_config(self, module_id: str) -> Optional[AdminModuleConfig]:
        """获取指定模块的配置"""
        return self.modules.get(module_id)
    
    def update_module_config(self, module_id: str, config: AdminModuleConfig) -> None:
        """更新模块配置"""
        self.modules[module_id] = config
    
    def remove_module_config(self, module_id: str) -> bool:
        """移除模块配置"""
        if module_id in self.modules:
            del self.modules[module_id]
            return True
        return False
    
    def validate_configuration(self) -> List[str]:
        """验证配置并返回错误列表"""
        errors = []
        
        # 验证模块配置
        for module_id, module_config in self.modules.items():
            try:
                # 重新验证模块配置
                module_config.model_validate(module_config.model_dump())
            except Exception as e:
                errors.append(f"模块 '{module_id}' 配置验证失败: {e}")
        
        return errors


# 默认配置
DEFAULT_ADMIN_CONFIG = AdminConfig()

# 配置模型导出
__all__ = [
    "AdminLayout",
    "ModuleDisplayMode",
    "ConfigValidationLevel",
    "AdminModuleConfig",
    "AdminLayoutConfig",
    "AdminFeatureConfig",
    "AdminUIConfig",
    "AdminNotificationConfig",
    "AdminBackupConfig",
    "AdminConfig",
    "DEFAULT_ADMIN_CONFIG"
]