"""
模块注册服务

统一管理后台的核心组件，负责：
1. 自动发现和注册所有可配置模块
2. 管理模块元数据和配置定义
3. 提供模块查询和分类功能
4. 处理模块依赖关系
"""

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Type
from uuid import uuid4
from pathlib import Path

from ..core.logging import get_logger
from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..plugins.base import PluginMetadata
from ..plugins.registry import PluginRegistry

logger = get_logger(__name__)


class ReloadStrategy(str, Enum):
    """热重载策略枚举"""
    IMMEDIATE = "immediate"      # 立即生效（UI外观）
    REAL_TIME = "real_time"      # 实时生效（AI参数）
    RESTART_REQUIRED = "restart" # 重启生效（插件/系统）
    MANUAL = "manual"           # 手动生效（用户确认）


class ModuleCategory(str, Enum):
    """模块分类枚举"""
    AI = "ai"                    # AI相关模块
    PLUGIN = "plugin"           # 插件模块
    SYSTEM = "system"           # 系统模块
    UI = "ui"                   # UI模块
    DATA = "data"               # 数据模块
    SECURITY = "security"       # 安全模块
    MONITOR = "monitor"         # 监控模块
    DEVELOPER = "developer"     # 开发者工具
    CUSTOM = "custom"           # 自定义模块


@dataclass
class ModuleRegistration:
    """模块注册信息"""
    
    module_id: str                    # 唯一标识符
    display_name: str                 # 显示名称
    category: ModuleCategory          # 分类
    config_schema: Dict[str, Any]     # JSON Schema配置定义
    default_config: Dict[str, Any]    # 默认配置
    reload_strategy: ReloadStrategy   # 热重载策略
    
    # 可选信息
    icon: Optional[str] = None        # 图标标识（支持emoji或图标名称）
    description: Optional[str] = None  # 详细描述
    version: str = "1.0.0"           # 模块版本
    author: Optional[str] = None      # 作者
    priority: int = 100               # 显示优先级（数值越小优先级越高）
    tags: List[str] = field(default_factory=list)  # 标签
    dependencies: List[str] = field(default_factory=list)  # 依赖的模块ID
    
    # 运行时信息
    enabled: bool = True              # 是否启用
    is_initialized: bool = False      # 是否已初始化
    last_modified: float = 0.0        # 最后修改时间戳
    source: Optional[str] = None      # 模块来源（plugin, system, custom）
    
    # 回调函数
    on_config_changed: Optional[Callable[[Dict[str, Any]], None]] = None
    on_reload_required: Optional[Callable[[], bool]] = None
    
    def __post_init__(self):
        """数据验证"""
        if not self.module_id:
            raise ValueError("模块ID不能为空")
        if not self.display_name:
            raise ValueError("显示名称不能为空")
        if not isinstance(self.config_schema, dict):
            raise ValueError("配置模式必须是字典类型")
        if not isinstance(self.default_config, dict):
            raise ValueError("默认配置必须是字典类型")
    
    @property
    def has_dependencies(self) -> bool:
        """是否有依赖"""
        return bool(self.dependencies)
    
    @property
    def can_reload_immediately(self) -> bool:
        """是否可以立即重载"""
        return self.reload_strategy in [ReloadStrategy.IMMEDIATE, ReloadStrategy.REAL_TIME]
    
    @property
    def requires_restart(self) -> bool:
        """是否需要重启"""
        return self.reload_strategy == ReloadStrategy.RESTART_REQUIRED
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取显示信息"""
        return {
            "id": self.module_id,
            "name": self.display_name,
            "category": self.category.value,
            "icon": self.icon or self._get_default_icon(),
            "description": self.description or "",
            "version": self.version,
            "enabled": self.enabled,
            "priority": self.priority,
            "tags": self.tags,
            "reload_strategy": self.reload_strategy.value,
            "has_config": bool(self.config_schema),
            "has_dependencies": self.has_dependencies,
            "can_reload_immediately": self.can_reload_immediately,
            "requires_restart": self.requires_restart,
            "source": self.source or "unknown"
        }
    
    def _get_default_icon(self) -> str:
        """获取默认图标"""
        icon_map = {
            ModuleCategory.AI: "🤖",
            ModuleCategory.PLUGIN: "🧩",
            ModuleCategory.SYSTEM: "⚙️",
            ModuleCategory.UI: "🎨",
            ModuleCategory.DATA: "💾",
            ModuleCategory.SECURITY: "🔒",
            ModuleCategory.MONITOR: "📊",
            ModuleCategory.DEVELOPER: "🔧",
            ModuleCategory.CUSTOM: "📦"
        }
        return icon_map.get(self.category, "📦")


class ModuleRegistry:
    """
    模块注册表
    
    统一管理所有可配置模块，支持：
    1. 自动发现插件模块
    2. 手动注册系统模块
    3. 模块分类和过滤
    4. 依赖关系管理
    5. 配置变更跟踪
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container,
        plugin_registry: Optional[PluginRegistry] = None
    ):
        """
        初始化模块注册表
        
        Args:
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            plugin_registry: 插件注册表（可选）
        """
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._container = container
        self._plugin_registry = plugin_registry
        
        # 模块存储
        self._modules: Dict[str, ModuleRegistration] = {}
        self._categories: Dict[ModuleCategory, List[str]] = {}
        self._dependencies: Dict[str, Set[str]] = {}  # 模块ID -> 依赖的模块ID集合
        
        # 状态管理
        self._is_initialized = False
        self._lock = threading.RLock()
        
        # 初始化分类字典
        for category in ModuleCategory:
            self._categories[category] = []
        
        logger.debug_struct("模块注册表初始化", 
                          config_manager=config_manager is not None,
                          event_bus=event_bus is not None,
                          plugin_registry=plugin_registry is not None)
    
    def initialize(self) -> None:
        """初始化模块注册表"""
        with self._lock:
            if self._is_initialized:
                logger.warning("模块注册表已初始化，跳过重复初始化")
                return
            
            logger.info("初始化模块注册表")
            
            try:
                # 1. 自动发现插件模块
                if self._plugin_registry:
                    self._discover_plugin_modules()
                
                # 2. 注册内置系统模块
                self._register_builtin_modules()
                
                # 3. 订阅配置变更事件
                self._subscribe_events()
                
                # 4. 验证依赖关系
                self._validate_dependencies()
                
                self._is_initialized = True
                
                total_modules = len(self._modules)
                logger.info_struct("模块注册表初始化完成",
                                 total_modules=total_modules,
                                 categories=self._get_category_stats())
                
                # 发布初始化完成事件
                self._event_bus.publish("module_registry.initialized", {
                    "total_modules": total_modules,
                    "timestamp": "now"
                })
                
            except Exception as e:
                logger.error("模块注册表初始化失败", exc_info=True)
                raise
    
    def _discover_plugin_modules(self) -> None:
        """自动发现插件模块"""
        if not self._plugin_registry:
            return
        
        try:
            all_plugins = self._plugin_registry.get_all_plugins()
            plugin_count = 0
            
            for plugin_info in all_plugins:
                metadata = plugin_info.metadata
                
                # 只有有配置模式的插件才注册为可配置模块
                if metadata.config_schema:
                    # 从admin_config获取管理配置，如果没有则使用默认值
                    admin_config = getattr(metadata, 'admin_config', {}) or {}
                    
                    # 确定分类（优先使用admin_config中的分类）
                    category_str = admin_config.get('category', 'plugin')
                    try:
                        category = ModuleCategory(category_str)
                    except ValueError:
                        # 如果不是有效分类，根据插件类型推断
                        if metadata.plugin_type.value == "ai_provider":
                            category = ModuleCategory.AI
                        elif metadata.plugin_type.value == "tool":
                            category = ModuleCategory.SYSTEM
                        else:
                            category = ModuleCategory.PLUGIN
                    
                    # 确定热重载策略
                    reload_strategy_str = admin_config.get('reload_strategy', 'restart')
                    try:
                        reload_strategy = ReloadStrategy(reload_strategy_str)
                    except ValueError:
                        reload_strategy = ReloadStrategy.RESTART_REQUIRED
                    
                    # 创建模块注册信息
                    module_id = f"plugin.{metadata.name}"
                    module = ModuleRegistration(
                        module_id=module_id,
                        display_name=metadata.display_name,
                        category=category,
                        config_schema=metadata.config_schema,
                        default_config=metadata.default_config or {},
                        reload_strategy=reload_strategy,
                        icon=admin_config.get('icon'),
                        description=metadata.description,
                        version=metadata.version,
                        author=metadata.author,
                        priority=admin_config.get('priority', 100),
                        tags=metadata.tags,
                        dependencies=metadata.dependencies,
                        source="plugin",
                        enabled=plugin_info.is_enabled
                    )
                    
                    # 注册模块
                    self._register_module_internal(module)
                    plugin_count += 1
                    logger.debug_struct("插件模块已注册",
                                      module_id=module_id,
                                      plugin_name=metadata.name)
            
            logger.info_struct("插件模块发现完成", count=plugin_count)
            
        except Exception as e:
            logger.error("插件模块发现失败", exc_info=True)
    
    def _register_builtin_modules(self) -> None:
        """注册内置系统模块"""
        logger.debug("注册内置系统模块")
        
        # AI配置模块
        ai_module = ModuleRegistration(
            module_id="system.ai_config",
            display_name="AI模型配置",
            category=ModuleCategory.AI,
            config_schema=self._get_ai_config_schema(),
            default_config=self._get_ai_default_config(),
            reload_strategy=ReloadStrategy.REAL_TIME,
            icon="🤖",
            description="配置AI模型的参数、提示词和切换策略",
            version="4.0.0",
            author="小盘古项目组",
            priority=10,
            tags=["ai", "model", "configuration"],
            source="system"
        )
        self._register_module_internal(ai_module)
        
        # UI配置模块
        ui_module = ModuleRegistration(
            module_id="system.ui_config",
            display_name="界面设置",
            category=ModuleCategory.UI,
            config_schema=self._get_ui_config_schema(),
            default_config=self._get_ui_default_config(),
            reload_strategy=ReloadStrategy.IMMEDIATE,
            icon="🎨",
            description="配置界面主题、语言和布局设置",
            version="4.0.0",
            author="小盘古项目组",
            priority=20,
            tags=["ui", "theme", "layout"],
            source="system"
        )
        self._register_module_internal(ui_module)
        
        # 系统设置模块
        system_module = ModuleRegistration(
            module_id="system.settings",
            display_name="系统设置",
            category=ModuleCategory.SYSTEM,
            config_schema=self._get_system_config_schema(),
            default_config=self._get_system_default_config(),
            reload_strategy=ReloadStrategy.RESTART_REQUIRED,
            icon="⚙️",
            description="配置系统日志、存储和安全设置",
            version="4.0.0",
            author="小盘古项目组",
            priority=30,
            tags=["system", "security", "storage"],
            source="system"
        )
        self._register_module_internal(system_module)
        
        # 插件管理模块
        plugin_module = ModuleRegistration(
            module_id="system.plugin_management",
            display_name="插件管理",
            category=ModuleCategory.PLUGIN,
            config_schema=self._get_plugin_config_schema(),
            default_config=self._get_plugin_default_config(),
            reload_strategy=ReloadStrategy.RESTART_REQUIRED,
            icon="🧩",
            description="管理插件的启用、禁用和配置",
            version="4.0.0",
            author="小盘古项目组",
            priority=40,
            tags=["plugin", "management"],
            source="system"
        )
        self._register_module_internal(plugin_module)
        
        logger.info_struct("内置系统模块注册完成", count=4)
    
    def _get_ai_config_schema(self) -> Dict[str, Any]:
        """获取AI配置的JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "default_provider": {
                    "type": "string",
                    "title": "默认AI提供商",
                    "description": "默认使用的AI服务提供商",
                    "enum": ["deepseek", "openai", "claude", "gemini", "custom"],
                    "default": "deepseek"
                },
                "max_tokens": {
                    "type": "integer",
                    "title": "最大Token数",
                    "description": "单次请求允许的最大Token数量",
                    "minimum": 100,
                    "maximum": 100000,
                    "default": 4000
                },
                "temperature": {
                    "type": "number",
                    "title": "温度参数",
                    "description": "控制回答的随机性（0-2之间）",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.7
                },
                "top_p": {
                    "type": "number",
                    "title": "Top-P参数",
                    "description": "核采样概率（0-1之间）",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.9
                },
                "prompt_templates": {
                    "type": "object",
                    "title": "提示词模板",
                    "description": "不同场景下的提示词模板",
                    "additionalProperties": {
                        "type": "string"
                    },
                    "default": {
                        "default": "你是一个有帮助的AI助手。",
                        "creative": "请发挥创造力，提供新颖的想法。",
                        "technical": "请提供详细的技术分析和解释。"
                    }
                }
            },
            "required": ["default_provider", "max_tokens", "temperature", "top_p"]
        }
    
    def _get_ai_default_config(self) -> Dict[str, Any]:
        """获取AI默认配置"""
        return {
            "default_provider": "deepseek",
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9,
            "prompt_templates": {
                "default": "你是一个有帮助的AI助手。",
                "creative": "请发挥创造力，提供新颖的想法。",
                "technical": "请提供详细的技术分析和解释。"
            }
        }
    
    def _get_ui_config_schema(self) -> Dict[str, Any]:
        """获取UI配置的JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "title": "界面主题",
                    "description": "选择界面主题风格",
                    "enum": ["dark", "light", "system"],
                    "default": "dark"
                },
                "language": {
                    "type": "string",
                    "title": "界面语言",
                    "description": "选择界面显示语言",
                    "enum": ["zh-CN", "en-US"],
                    "default": "zh-CN"
                },
                "font_size": {
                    "type": "integer",
                    "title": "字体大小",
                    "description": "界面字体大小（像素）",
                    "minimum": 8,
                    "maximum": 72,
                    "default": 12
                },
                "auto_scroll": {
                    "type": "boolean",
                    "title": "自动滚动",
                    "description": "是否自动滚动到最新内容",
                    "default": True
                },
                "markdown_render": {
                    "type": "boolean",
                    "title": "Markdown渲染",
                    "description": "是否渲染Markdown格式",
                    "default": True
                }
            },
            "required": ["theme", "language", "font_size"]
        }
    
    def _get_ui_default_config(self) -> Dict[str, Any]:
        """获取UI默认配置"""
        return {
            "theme": "dark",
            "language": "zh-CN",
            "font_size": 12,
            "auto_scroll": True,
            "markdown_render": True
        }
    
    def _get_system_config_schema(self) -> Dict[str, Any]:
        """获取系统配置的JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "string",
                    "title": "日志级别",
                    "description": "系统日志记录级别",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "default": "INFO"
                },
                "enable_hot_reload": {
                    "type": "boolean",
                    "title": "启用热重载",
                    "description": "是否启用配置热重载功能",
                    "default": True
                },
                "data_retention_days": {
                    "type": "integer",
                    "title": "数据保留天数",
                    "description": "保留历史数据的天数",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 30
                },
                "backup_enabled": {
                    "type": "boolean",
                    "title": "启用自动备份",
                    "description": "是否启用自动数据备份",
                    "default": True
                },
                "backup_interval_hours": {
                    "type": "integer",
                    "title": "备份间隔（小时）",
                    "description": "自动备份的时间间隔",
                    "minimum": 1,
                    "maximum": 168,
                    "default": 24
                }
            },
            "required": ["log_level", "enable_hot_reload"]
        }
    
    def _get_system_default_config(self) -> Dict[str, Any]:
        """获取系统默认配置"""
        return {
            "log_level": "INFO",
            "enable_hot_reload": True,
            "data_retention_days": 30,
            "backup_enabled": True,
            "backup_interval_hours": 24
        }
    
    def _get_plugin_config_schema(self) -> Dict[str, Any]:
        """获取插件配置的JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "auto_discovery": {
                    "type": "boolean",
                    "title": "自动发现",
                    "description": "是否自动发现新安装的插件",
                    "default": True
                },
                "sandbox_mode": {
                    "type": "boolean",
                    "title": "沙箱模式",
                    "description": "是否在沙箱环境中运行插件",
                    "default": True
                },
                "loading_strategy": {
                    "type": "string",
                    "title": "加载策略",
                    "description": "插件加载策略",
                    "enum": ["eager", "lazy"],
                    "default": "lazy"
                },
                "max_plugin_memory_mb": {
                    "type": "integer",
                    "title": "最大内存限制（MB）",
                    "description": "单个插件允许使用的最大内存",
                    "minimum": 10,
                    "maximum": 1024,
                    "default": 100
                }
            },
            "required": ["auto_discovery", "sandbox_mode"]
        }
    
    def _get_plugin_default_config(self) -> Dict[str, Any]:
        """获取插件默认配置"""
        return {
            "auto_discovery": True,
            "sandbox_mode": True,
            "loading_strategy": "lazy",
            "max_plugin_memory_mb": 100
        }
    
    def _register_module_internal(self, module: ModuleRegistration) -> None:
        """内部模块注册方法"""
        module_id = module.module_id
        
        with self._lock:
            # 检查模块是否已存在
            if module_id in self._modules:
                logger.warning_struct("模块已存在，跳过注册", module_id=module_id)
                return
            
            # 添加模块
            self._modules[module_id] = module
            
            # 添加到分类
            category = module.category
            if module_id not in self._categories[category]:
                self._categories[category].append(module_id)
            
            # 记录依赖关系
            if module.dependencies:
                self._dependencies[module_id] = set(module.dependencies)
            
            # 设置最后修改时间
            module.last_modified = threading.time()
            
            logger.debug_struct("模块已注册",
                              module_id=module_id,
                              display_name=module.display_name,
                              category=module.category.value)
    
    def _subscribe_events(self) -> None:
        """订阅相关事件"""
        # 配置变更事件
        self._event_bus.subscribe("config.changed", self._on_config_changed)
        
        # 插件变更事件
        self._event_bus.subscribe("plugin.registered", self._on_plugin_registered)
        self._event_bus.subscribe("plugin.unregistered", self._on_plugin_unregistered)
        self._event_bus.subscribe("plugin.enabled", self._on_plugin_enabled)
        self._event_bus.subscribe("plugin.disabled", self._on_plugin_disabled)
        
        logger.debug("模块注册表事件订阅完成")
    
    def _on_config_changed(self, event) -> None:
        """处理配置变更事件"""
        data = event.data
        config_key = data.get("key", "")
        
        # 检查是否是模块配置变更
        if config_key.startswith("module."):
            module_id = config_key.split(".")[1] if "." in config_key else None
            if module_id and module_id in self._modules:
                module = self._modules[module_id]
                if module.on_config_changed:
                    try:
                        new_config = data.get("new_value", {})
                        module.on_config_changed(new_config)
                        logger.debug_struct("模块配置变更处理",
                                          module_id=module_id,
                                          config_key=config_key)
                    except Exception as e:
                        logger.error("模块配置变更回调执行失败",
                                   module_id=module_id,
                                   error=str(e))
    
    def _on_plugin_registered(self, event) -> None:
        """处理插件注册事件"""
        # TODO: 重新发现插件模块
        pass
    
    def _on_plugin_unregistered(self, event) -> None:
        """处理插件注销事件"""
        # TODO: 移除对应的模块
        pass
    
    def _on_plugin_enabled(self, event) -> None:
        """处理插件启用事件"""
        data = event.data
        plugin_name = data.get("plugin_name")
        
        if plugin_name:
            module_id = f"plugin.{plugin_name}"
            if module_id in self._modules:
                self._modules[module_id].enabled = True
                logger.debug_struct("模块启用状态更新",
                                  module_id=module_id,
                                  enabled=True)
    
    def _on_plugin_disabled(self, event) -> None:
        """处理插件禁用事件"""
        data = event.data
        plugin_name = data.get("plugin_name")
        
        if plugin_name:
            module_id = f"plugin.{plugin_name}"
            if module_id in self._modules:
                self._modules[module_id].enabled = False
                logger.debug_struct("模块启用状态更新",
                                  module_id=module_id,
                                  enabled=False)
    
    def _validate_dependencies(self) -> None:
        """验证模块依赖关系"""
        with self._lock:
            unresolved = []
            
            for module_id, deps in self._dependencies.items():
                for dep_id in deps:
                    if dep_id not in self._modules:
                        unresolved.append((module_id, dep_id))
                        logger.warning_struct("依赖未找到",
                                            module_id=module_id,
                                            dependency_id=dep_id)
            
            if unresolved:
                logger.warning_struct("存在未解决的依赖",
                                    unresolved_count=len(unresolved))
    
    def _get_category_stats(self) -> Dict[str, int]:
        """获取分类统计信息"""
        stats = {}
        for category, module_ids in self._categories.items():
            enabled_count = 0
            for module_id in module_ids:
                if module_id in self._modules and self._modules[module_id].enabled:
                    enabled_count += 1
            stats[category.value] = enabled_count
        return stats
    
    def register_module(self, module: ModuleRegistration) -> bool:
        """
        注册新模块
        
        Args:
            module: 模块注册信息
            
        Returns:
            是否注册成功
        """
        try:
            self._register_module_internal(module)
            
            # 发布模块注册事件
            self._event_bus.publish("module.registered", {
                "module_id": module.module_id,
                "display_name": module.display_name,
                "category": module.category.value,
                "timestamp": "now"
            })
            
            return True
            
        except Exception as e:
            logger.error("模块注册失败",
                       module_id=module.module_id,
                       error=str(e))
            return False
    
    def unregister_module(self, module_id: str) -> bool:
        """
        注销模块
        
        Args:
            module_id: 模块ID
            
        Returns:
            是否注销成功
        """
        with self._lock:
            if module_id not in self._modules:
                logger.warning_struct("模块不存在，无法注销", module_id=module_id)
                return False
            
            module = self._modules[module_id]
            
            # 从分类中移除
            category = module.category
            if module_id in self._categories[category]:
                self._categories[category].remove(module_id)
            
            # 从依赖关系中移除
            if module_id in self._dependencies:
                del self._dependencies[module_id]
            
            # 移除模块
            del self._modules[module_id]
            
            # 发布模块注销事件
            self._event_bus.publish("module.unregistered", {
                "module_id": module_id,
                "display_name": module.display_name,
                "timestamp": "now"
            })
            
            logger.debug_struct("模块已注销", module_id=module_id)
            return True
    
    def get_module(self, module_id: str) -> Optional[ModuleRegistration]:
        """获取模块信息"""
        with self._lock:
            return self._modules.get(module_id)
    
    def get_modules_by_category(self, category: ModuleCategory, 
                               enabled_only: bool = False) -> List[ModuleRegistration]:
        """获取指定分类的模块"""
        with self._lock:
            result = []
            for module_id in self._categories[category]:
                if module_id in self._modules:
                    module = self._modules[module_id]
                    if not enabled_only or module.enabled:
                        result.append(module)
            
            # 按优先级排序
            result.sort(key=lambda x: x.priority)
            return result
    
    def get_all_modules(self, enabled_only: bool = False) -> List[ModuleRegistration]:
        """获取所有模块"""
        with self._lock:
            modules = list(self._modules.values())
            if enabled_only:
                modules = [m for m in modules if m.enabled]
            
            # 按分类和优先级排序
            modules.sort(key=lambda x: (x.category.value, x.priority))
            return modules
    
    def get_module_config(self, module_id: str) -> Optional[Dict[str, Any]]:
        """获取模块当前配置"""
        module = self.get_module(module_id)
        if not module:
            return None
        
        # 从配置管理器获取配置
        config_key = f"module.{module_id}"
        config = self._config_manager.get_value(config_key, {})
        
        # 合并默认配置
        merged = module.default_config.copy()
        merged.update(config)
        return merged
    
    def update_module_config(self, module_id: str, new_config: Dict[str, Any],
                           persistent: bool = True) -> bool:
        """
        更新模块配置
        
        Args:
            module_id: 模块ID
            new_config: 新配置
            persistent: 是否持久化到配置文件
            
        Returns:
            是否更新成功
        """
        module = self.get_module(module_id)
        if not module:
            logger.warning_struct("模块不存在，无法更新配置", module_id=module_id)
            return False
        
        try:
            # 验证配置（简单验证，后续可添加JSON Schema验证）
            if not isinstance(new_config, dict):
                logger.error("配置必须是字典类型", module_id=module_id)
                return False
            
            # 保存到配置管理器
            config_key = f"module.{module_id}"
            success = self._config_manager.set_value(config_key, new_config, persistent)
            
            if success:
                # 发布配置变更事件
                self._event_bus.publish("module.config.changed", {
                    "module_id": module_id,
                    "old_config": self.get_module_config(module_id),
                    "new_config": new_config,
                    "reload_strategy": module.reload_strategy.value,
                    "timestamp": "now"
                })
                
                # 更新模块最后修改时间
                module.last_modified = threading.time()
                
                logger.info_struct("模块配置已更新",
                                 module_id=module_id,
                                 persistent=persistent,
                                 reload_strategy=module.reload_strategy.value)
                
                # 如果是立即生效的策略，触发重载
                if module.can_reload_immediately and module.on_reload_required:
                    try:
                        module.on_reload_required()
                        logger.debug_struct("模块热重载已触发", module_id=module_id)
                    except Exception as e:
                        logger.error("模块热重载失败", module_id=module_id, error=str(e))
            
            return success
            
        except Exception as e:
            logger.error("模块配置更新失败", module_id=module_id, error=str(e))
            return False
    
    def get_dependent_modules(self, module_id: str) -> List[str]:
        """获取依赖于指定模块的所有模块"""
        with self._lock:
            dependents = []
            for dep_module_id, deps in self._dependencies.items():
                if module_id in deps:
                    dependents.append(dep_module_id)
            return dependents
    
    def get_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        with self._lock:
            total = len(self._modules)
            enabled = sum(1 for m in self._modules.values() if m.enabled)
            
            category_stats = {}
            for category in ModuleCategory:
                modules = self.get_modules_by_category(category)
                category_stats[category.value] = {
                    "total": len(modules),
                    "enabled": sum(1 for m in modules if m.enabled)
                }
            
            return {
                "total_modules": total,
                "enabled_modules": enabled,
                "disabled_modules": total - enabled,
                "categories": category_stats,
                "has_dependencies": len(self._dependencies),
                "is_initialized": self._is_initialized
            }
    
    def clear(self) -> None:
        """清空所有模块"""
        with self._lock:
            self._modules.clear()
            for category in self._categories:
                self._categories[category].clear()
            self._dependencies.clear()
            logger.info("模块注册表已清空")