"""
系统监控界面

提供实时的系统监控和性能指标展示，包括：
1. 系统资源监控（CPU、内存、磁盘、网络）
2. 插件状态监控
3. Token使用统计
4. 性能指标展示
5. 实时图表和警报
"""

import customtkinter as ctk
import logging
import time
import threading
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("psutil not available, system monitoring will be limited")
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from ..core.events import EventBus
from ..core.di import Container
from ..config.manager import ConfigManager
from ..plugins.registry import PluginRegistry
from ..plugins.base import PluginStatus, PluginInfo
from .manager import UIManager
from .widgets import BaseWidget, Panel, ScrollPanel, Card, Button, Label, Switch, TextArea, ProgressBar
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class MonitorViewType(str, Enum):
    """监控视图类型枚举"""
    OVERVIEW = "overview"      # 概览视图
    RESOURCES = "resources"    # 资源视图
    PLUGINS = "plugins"        # 插件监控视图
    PERFORMANCE = "performance"  # 性能视图
    LOGS = "logs"              # 日志视图


class MetricType(str, Enum):
    """指标类型枚举"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    TOKEN_COUNT = "token_count"
    PLUGIN_COUNT = "plugin_count"
    ERROR_COUNT = "error_count"
    RESPONSE_TIME = "response_time"


@dataclass
class MetricData:
    """指标数据类"""
    metric_type: MetricType
    value: float
    unit: str
    timestamp: float
    label: str
    description: str = ""
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    trend: Optional[float] = None  # 趋势（正负百分比）
    
    def get_status_color(self) -> str:
        """根据阈值获取状态颜色"""
        if self.threshold_critical is not None and self.value >= self.threshold_critical:
            return "critical"
        elif self.threshold_warning is not None and self.value >= self.threshold_warning:
            return "warning"
        else:
            return "normal"
    
    def get_display_value(self) -> str:
        """获取显示值"""
        if self.metric_type == MetricType.CPU_USAGE:
            return f"{self.value:.1f}{self.unit}"
        elif self.metric_type == MetricType.MEMORY_USAGE:
            if self.value >= 1024:
                return f"{self.value/1024:.1f} GB"
            else:
                return f"{self.value:.0f} MB"
        else:
            return f"{self.value}{self.unit}"


class MetricCard(BaseWidget):
    """指标卡片组件"""
    
    def __init__(
        self,
        parent,
        metric_data: MetricData,
        widget_id: Optional[str] = None,
        **kwargs
    ):
        """
        初始化指标卡片
        
        Args:
            parent: 父组件
            metric_data: 指标数据
            widget_id: 组件ID
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None)
        self._metric_data = metric_data
        self._kwargs = kwargs
        
        # UI组件
        self._card = None
        self._title_label = None
        self._value_label = None
        self._progress_bar = None
        self._trend_label = None
        
        self.initialize()
        
        logger.debug_struct("指标卡片初始化", metric_type=metric_data.metric_type.value)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建指标卡片组件"""
        # 根据状态确定卡片样式
        status_color = self._metric_data.get_status_color()
        if status_color == "critical":
            card_style = {
                "fg_color": ("#ffebee", "#3a1c1c"),
                "border_color": ("#ef9a9a", "#7b3f3f"),
                "border_width": 2
            }
        elif status_color == "warning":
            card_style = {
                "fg_color": ("#fff3e0", "#332d1c"),
                "border_color": ("#ff9800", "#8a5b00"),
                "border_width": 2
            }
        else:
            card_style = {
                "fg_color": ("white", "gray20"),
                "border_color": ("gray70", "gray40"),
                "border_width": 1
            }
        
        # 创建卡片
        self._card = Card(self._parent, style=card_style)
        card_widget = self._card.get_widget()
        
        # 配置卡片网格
        card_widget.grid_columnconfigure(0, weight=1)
        card_widget.grid_rowconfigure(1, weight=1)
        
        # 内容区域
        content_frame = ctk.CTkFrame(card_widget, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        
        # 标题和值
        self._create_title_area(content_frame)
        
        # 进度条（如果适用）
        self._create_progress_area(content_frame)
        
        # 元数据
        self._create_metadata_area(content_frame)
        
        return card_widget
    
    def _create_title_area(self, parent) -> None:
        """创建标题区域"""
        # 标题框架
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=0, pady=(0, 5))
        
        # 指标标题
        self._title_label = ctk.CTkLabel(
            title_frame,
            text=self._metric_data.label,
            font=("Microsoft YaHei", 12, "bold"),
            anchor="w"
        )
        self._title_label.pack(side="left", fill="x", expand=True)
        
        # 指标值
        self._value_label = ctk.CTkLabel(
            title_frame,
            text=self._metric_data.get_display_value(),
            font=("Microsoft YaHei", 14, "bold"),
            anchor="e"
        )
        self._value_label.pack(side="right", padx=(10, 0))
        
        # 注册组件
        self.register_widget("title_frame", title_frame)
    
    def _create_progress_area(self, parent) -> None:
        """创建进度条区域"""
        # 只有百分比类型的指标显示进度条
        if self._metric_data.metric_type in [MetricType.CPU_USAGE, MetricType.MEMORY_USAGE, MetricType.DISK_USAGE]:
            # 进度条框架
            progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
            progress_frame.pack(fill="x", padx=0, pady=(5, 0))
            
            # 创建进度条
            self._progress_bar = ProgressBar(
                progress_frame,
                widget_id=f"{self._widget_id}_progress"
            )
            progress_widget = self._progress_bar.get_widget()
            progress_widget.pack(fill="x", padx=0, pady=0)
            
            # 设置进度值
            if self._metric_data.metric_type == MetricType.CPU_USAGE:
                progress_value = self._metric_data.value / 100.0
            elif self._metric_data.metric_type == MetricType.MEMORY_USAGE:
                # 假设内存以MB为单位，需要知道总内存
                if PSUTIL_AVAILABLE:
                    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
                else:
                    total_memory = 1024.0  # 默认1GB
                progress_value = self._metric_data.value / total_memory if total_memory > 0 else 0
            else:
                progress_value = self._metric_data.value / 100.0  # 默认百分比
            
            self._progress_bar.set_value(progress_value)
            
            # 根据状态设置颜色
            status_color = self._metric_data.get_status_color()
            if status_color == "critical":
                progress_widget.configure(progress_color=("red", "#ff6666"))
            elif status_color == "warning":
                progress_widget.configure(progress_color=("orange", "#ff9900"))
            
            # 注册组件
            self.register_widget("progress_frame", progress_frame)
    
    def _create_metadata_area(self, parent) -> None:
        """创建元数据区域"""
        meta_frame = ctk.CTkFrame(parent, fg_color="transparent")
        meta_frame.pack(fill="x", padx=0, pady=(5, 0))
        
        # 时间戳
        timestamp = datetime.fromtimestamp(self._metric_data.timestamp)
        time_str = timestamp.strftime("%H:%M:%S")
        
        time_label = ctk.CTkLabel(
            meta_frame,
            text=f"更新: {time_str}",
            font=("Microsoft YaHei", 9),
            text_color=("gray50", "gray60")
        )
        time_label.pack(side="left")
        
        # 趋势（如果有）
        if self._metric_data.trend is not None:
            trend_icon = "↗️" if self._metric_data.trend > 0 else "↘️" if self._metric_data.trend < 0 else "➡️"
            trend_text = f"{trend_icon} {abs(self._metric_data.trend):.1f}%"
            
            self._trend_label = ctk.CTkLabel(
                meta_frame,
                text=trend_text,
                font=("Microsoft YaHei", 9),
                text_color=("green" if self._metric_data.trend < 0 else "red" if self._metric_data.trend > 0 else "gray")
            )
            self._trend_label.pack(side="right", padx=(10, 0))
            self.register_widget("trend_label", self._trend_label)
        
        # 阈值提示（如果有）
        if self._metric_data.threshold_warning is not None:
            threshold_label = ctk.CTkLabel(
                meta_frame,
                text=f"警告: {self._metric_data.threshold_warning}{self._metric_data.unit}",
                font=("Microsoft YaHei", 9),
                text_color=("orange", "#ff9900")
            )
            threshold_label.pack(side="right", padx=(10, 0))
            self.register_widget("threshold_label", threshold_label)
        
        self.register_widget("meta_frame", meta_frame)
        self.register_widget("time_label", time_label)
    
    def update_metric_data(self, metric_data: MetricData) -> None:
        """
        更新指标数据
        
        Args:
            metric_data: 新的指标数据
        """
        self._metric_data = metric_data
        
        # 更新卡片样式
        if self._card and self._card.get_widget():
            card_widget = self._card.get_widget()
            
            status_color = metric_data.get_status_color()
            if status_color == "critical":
                card_widget.configure(
                    fg_color=("#ffebee", "#3a1c1c"),
                    border_color=("#ef9a9a", "#7b3f3f")
                )
            elif status_color == "warning":
                card_widget.configure(
                    fg_color=("#fff3e0", "#332d1c"),
                    border_color=("#ff9800", "#8a5b00")
                )
            else:
                card_widget.configure(
                    fg_color=("white", "gray20"),
                    border_color=("gray70", "gray40")
                )
        
        # 更新值标签
        if self._value_label:
            self._value_label.configure(text=metric_data.get_display_value())
        
        # 更新进度条
        if self._progress_bar and metric_data.metric_type in [MetricType.CPU_USAGE, MetricType.MEMORY_USAGE, MetricType.DISK_USAGE]:
            progress_widget = self._progress_bar.get_widget()
            
            # 计算进度值
            if metric_data.metric_type == MetricType.CPU_USAGE:
                progress_value = metric_data.value / 100.0
            elif metric_data.metric_type == MetricType.MEMORY_USAGE:
                if PSUTIL_AVAILABLE:
                    total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
                else:
                    total_memory = 1024.0  # 默认1GB
                progress_value = metric_data.value / total_memory if total_memory > 0 else 0
            else:
                progress_value = metric_data.value / 100.0
            
            self._progress_bar.set_value(progress_value)
            
            # 更新进度条颜色
            if status_color == "critical":
                progress_widget.configure(progress_color=("red", "#ff6666"))
            elif status_color == "warning":
                progress_widget.configure(progress_color=("orange", "#ff9900"))
            else:
                progress_widget.configure(progress_color=("green", "green"))
        
        # 更新趋势标签
        if self._trend_label and metric_data.trend is not None:
            trend_icon = "↗️" if metric_data.trend > 0 else "↘️" if metric_data.trend < 0 else "➡️"
            trend_text = f"{trend_icon} {abs(metric_data.trend):.1f}%"
            trend_color = "green" if metric_data.trend < 0 else "red" if metric_data.trend > 0 else "gray"
            
            self._trend_label.configure(text=trend_text, text_color=trend_color)
        
        logger.debug_struct("指标卡片更新", metric_type=metric_data.metric_type.value)


class MonitorInterface(BaseWidget):
    """
    系统监控界面
    
    实时系统监控界面，支持：
    1. 系统资源监控（CPU、内存、磁盘、网络）
    2. 插件状态监控
    3. Token使用统计
    4. 性能指标展示
    5. 实时图表和警报
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        container: Optional[Container] = None,
        plugin_registry: Optional[PluginRegistry] = None,
        **kwargs
    ):
        """
        初始化系统监控界面
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            plugin_registry: 插件注册表
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, None, config_manager, event_bus)
        self._container = container
        self._plugin_registry = plugin_registry
        
        # 视图状态
        self._view_type = MonitorViewType.OVERVIEW
        self._is_monitoring = False
        self._update_interval = 2.0  # 更新间隔（秒）
        
        # 指标数据
        self._metrics: Dict[str, MetricData] = {}
        self._metric_cards: Dict[str, MetricCard] = {}
        
        # 监控线程
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # UI组件
        self._main_panel = None
        self._control_panel = None
        self._metrics_panel = None
        
        # 初始化
        self.initialize()
        
        logger.debug_struct("系统监控界面初始化", widget_id=self._widget_id)
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建系统监控界面组件"""
        # 创建主面板
        self._main_panel = Panel(self._parent)
        main_widget = self._main_panel.get_widget()
        
        # 配置网格布局
        main_widget.grid_rowconfigure(1, weight=1)  # 指标区域
        main_widget.grid_columnconfigure(0, weight=1)
        
        # 1. 创建控制面板
        self._create_control_panel(main_widget)
        
        # 2. 创建指标显示面板
        self._create_metrics_panel(main_widget)
        
        # 3. 初始化指标数据
        self._initialize_metrics()
        
        # 4. 开始监控
        self.start_monitoring()
        
        # 注册主面板
        self.register_widget("main_panel", main_widget)
        
        return main_widget
    
    def _create_control_panel(self, parent) -> None:
        """创建控制面板"""
        logger.debug("创建控制面板")
        
        # 控制面板
        control_style = {
            "fg_color": ("gray90", "gray20"),
            "corner_radius": 0,
            "border_width": 1,
            "border_color": ("gray70", "gray30"),
            "height": 50
        }
        
        self._control_panel = Panel(parent, style=control_style)
        control_widget = self._control_panel.get_widget()
        control_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        control_widget.grid_propagate(False)
        
        # 配置控制面板网格
        control_widget.grid_columnconfigure(0, weight=1)  # 标题
        control_widget.grid_columnconfigure(1, weight=0)  # 视图切换
        control_widget.grid_columnconfigure(2, weight=0)  # 控制按钮
        
        # 标题
        title_label = ctk.CTkLabel(
            control_widget,
            text="系统监控",
            font=("Microsoft YaHei", 16, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=0)
        
        # 视图切换
        view_frame = ctk.CTkFrame(control_widget, fg_color="transparent")
        view_frame.grid(row=0, column=1, sticky="e", padx=10, pady=0)
        
        view_label = ctk.CTkLabel(
            view_frame,
            text="视图:",
            font=("Microsoft YaHei", 11)
        )
        view_label.pack(side="left", padx=(0, 5))
        
        view_options = [t.value for t in MonitorViewType]
        view_combo = ctk.CTkComboBox(
            view_frame,
            values=view_options,
            width=120,
            command=self._on_view_type_changed
        )
        view_combo.set(self._view_type.value)
        view_combo.pack(side="left")
        
        # 控制按钮
        button_frame = ctk.CTkFrame(control_widget, fg_color="transparent")
        button_frame.grid(row=0, column=2, sticky="e", padx=10, pady=0)
        
        # 开始/停止监控按钮
        self._monitor_button = Button(
            button_frame,
            text="停止监控" if self._is_monitoring else "开始监控",
            widget_id="toggle_monitoring",
            width=100,
            command=self.toggle_monitoring
        )
        monitor_widget = self._monitor_button.get_widget()
        monitor_widget.pack(side="left", padx=5)
        
        # 刷新按钮
        refresh_button = Button(
            button_frame,
            text="刷新",
            widget_id="refresh_metrics",
            width=80,
            command=self.refresh_metrics
        )
        refresh_widget = refresh_button.get_widget()
        refresh_widget.pack(side="left", padx=5)
        
        # 注册组件
        self.register_widget("control_panel", control_widget)
        self.register_widget("title_label", title_label)
        self.register_widget("view_combo", view_combo)
        self.register_widget("monitor_button", monitor_widget)
        self.register_widget("refresh_button", refresh_widget)
    
    def _on_view_type_changed(self, choice: str) -> None:
        """
        处理视图类型变化
        
        Args:
            choice: 选择的视图类型
        """
        try:
            self._view_type = MonitorViewType(choice)
            logger.debug_struct("监控视图类型变更", view_type=self._view_type.value)
            # TODO: 实现视图切换
        except ValueError:
            logger.warning_struct("无效的视图类型", choice=choice)
    
    def _create_metrics_panel(self, parent) -> None:
        """创建指标显示面板"""
        logger.debug("创建指标显示面板")
        
        # 指标面板
        metrics_style = {
            "fg_color": ("gray95", "gray15"),
            "corner_radius": 0,
            "border_width": 0
        }
        
        self._metrics_panel = ScrollPanel(parent, style=metrics_style)
        metrics_widget = self._metrics_panel.get_widget()
        metrics_widget.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # 配置滚动面板内部框架
        content_frame = self._metrics_panel.get_content_frame()
        if content_frame:
            content_frame.grid_columnconfigure(0, weight=1)
        
        # 注册组件
        self.register_widget("metrics_panel", metrics_widget)
        self.register_widget("metrics_content_frame", content_frame)
    
    def _initialize_metrics(self) -> None:
        """初始化指标数据"""
        logger.debug("初始化指标数据")
        
        # 系统资源指标
        self._metrics[MetricType.CPU_USAGE.value] = MetricData(
            metric_type=MetricType.CPU_USAGE,
            value=0.0,
            unit="%",
            timestamp=time.time(),
            label="CPU使用率",
            description="中央处理器使用率",
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        
        # 内存指标（以MB为单位）
        if PSUTIL_AVAILABLE:
            memory_info = psutil.virtual_memory()
            memory_used = memory_info.used / (1024 * 1024)  # MB
            memory_total = memory_info.total / (1024 * 1024)  # MB
            threshold_warning = memory_total * 0.8
            threshold_critical = memory_total * 0.95
        else:
            memory_used = 0.0
            memory_total = 1024.0  # 默认1GB
            threshold_warning = memory_total * 0.8
            threshold_critical = memory_total * 0.95
        
        self._metrics[MetricType.MEMORY_USAGE.value] = MetricData(
            metric_type=MetricType.MEMORY_USAGE,
            value=memory_used,
            unit="MB",
            timestamp=time.time(),
            label="内存使用",
            description="系统内存使用量",
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical
        )
        
        # 磁盘指标
        if PSUTIL_AVAILABLE:
            try:
                disk_info = psutil.disk_usage('/')
                self._metrics[MetricType.DISK_USAGE.value] = MetricData(
                    metric_type=MetricType.DISK_USAGE,
                    value=disk_info.percent,
                    unit="%",
                    timestamp=time.time(),
                    label="磁盘使用率",
                    description="主磁盘使用率",
                    threshold_warning=80.0,
                    threshold_critical=95.0
                )
            except Exception:
                # 磁盘信息可能不可用
                pass
        
        # 插件计数指标
        plugin_count = 0
        if self._plugin_registry:
            plugin_count = len(self._plugin_registry.get_all_plugins())
        
        self._metrics[MetricType.PLUGIN_COUNT.value] = MetricData(
            metric_type=MetricType.PLUGIN_COUNT,
            value=plugin_count,
            unit="个",
            timestamp=time.time(),
            label="插件数量",
            description="已加载的插件数量"
        )
        
        # 创建指标卡片
        self._create_metric_cards()
        
        logger.debug_struct("指标数据初始化完成", metric_count=len(self._metrics))
    
    def _create_metric_cards(self) -> None:
        """创建指标卡片"""
        # 清理现有卡片
        for card in self._metric_cards.values():
            card.destroy()
        self._metric_cards.clear()
        
        # 获取内容框架
        content_frame = self._metrics_panel.get_content_frame()
        if not content_frame:
            return
        
        # 配置网格（两列布局）
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # 创建卡片
        metric_items = list(self._metrics.values())
        for i, metric_data in enumerate(metric_items):
            try:
                metric_card = MetricCard(
                    content_frame,
                    metric_data=metric_data,
                    widget_id=f"metric_card_{metric_data.metric_type.value}"
                )
                
                card_widget = metric_card.get_widget()
                if card_widget:
                    # 两列布局
                    column = i % 2
                    row = i // 2
                    card_widget.grid(row=row, column=column, sticky="nsew", padx=10, pady=5)
                
                # 存储卡片引用
                self._metric_cards[metric_data.metric_type.value] = metric_card
                
                logger.debug_struct("指标卡片创建", metric_type=metric_data.metric_type.value)
                
            except Exception as e:
                logger.error_struct("指标卡片创建失败", 
                                   metric_type=metric_data.metric_type.value, 
                                   error=str(e))
    
    def _update_metrics(self) -> None:
        """更新指标数据"""
        try:
            # CPU使用率
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=None)
            else:
                cpu_percent = 0.0  # 模拟值
            
            cpu_metric = self._metrics.get(MetricType.CPU_USAGE.value)
            if cpu_metric:
                old_value = cpu_metric.value
                cpu_metric.value = cpu_percent
                cpu_metric.timestamp = time.time()
                cpu_metric.trend = (cpu_percent - old_value) if old_value > 0 else None
            
            # 内存使用
            if PSUTIL_AVAILABLE:
                memory_info = psutil.virtual_memory()
                memory_used = memory_info.used / (1024 * 1024)  # MB
            else:
                memory_used = 512.0  # 模拟值 512MB
            
            memory_metric = self._metrics.get(MetricType.MEMORY_USAGE.value)
            if memory_metric:
                old_value = memory_metric.value
                memory_metric.value = memory_used
                memory_metric.timestamp = time.time()
                memory_metric.trend = ((memory_metric.value - old_value) / old_value * 100) if old_value > 0 else None
            
            # 磁盘使用率
            disk_metric = self._metrics.get(MetricType.DISK_USAGE.value)
            if disk_metric:
                if PSUTIL_AVAILABLE:
                    try:
                        disk_info = psutil.disk_usage('/')
                        old_value = disk_metric.value
                        disk_metric.value = disk_info.percent
                        disk_metric.timestamp = time.time()
                        disk_metric.trend = (disk_info.percent - old_value) if old_value > 0 else None
                    except Exception:
                        pass
            
            # 插件计数
            plugin_metric = self._metrics.get(MetricType.PLUGIN_COUNT.value)
            if plugin_metric and self._plugin_registry:
                plugin_count = len(self._plugin_registry.get_all_plugins())
                old_value = plugin_metric.value
                plugin_metric.value = plugin_count
                plugin_metric.timestamp = time.time()
                plugin_metric.trend = ((plugin_count - old_value) / old_value * 100) if old_value > 0 else None
            
            # 更新卡片
            for metric_type, metric_data in self._metrics.items():
                if metric_type in self._metric_cards:
                    self._metric_cards[metric_type].update_metric_data(metric_data)
            
        except Exception as e:
            logger.error_struct("指标更新失败", error=str(e))
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        logger.debug("监控循环开始")
        
        while not self._stop_monitoring.is_set():
            try:
                self._update_metrics()
                time.sleep(self._update_interval)
            except Exception as e:
                logger.error_struct("监控循环错误", error=str(e))
                time.sleep(self._update_interval)
        
        logger.debug("监控循环结束")
    
    def start_monitoring(self) -> bool:
        """开始监控"""
        if self._is_monitoring:
            logger.warning("监控已在运行中")
            return False
        
        logger.debug("开始系统监控")
        
        try:
            self._stop_monitoring.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="SystemMonitor",
                daemon=True
            )
            self._monitor_thread.start()
            self._is_monitoring = True
            
            # 更新按钮文本
            if self._monitor_button:
                self._monitor_button.get_widget().configure(text="停止监控")
            
            logger.debug("系统监控已启动")
            return True
            
        except Exception as e:
            logger.error_struct("监控启动失败", error=str(e))
            return False
    
    def stop_monitoring(self) -> bool:
        """停止监控"""
        if not self._is_monitoring:
            logger.warning("监控未在运行中")
            return False
        
        logger.debug("停止系统监控")
        
        try:
            self._stop_monitoring.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)
            
            self._is_monitoring = False
            
            # 更新按钮文本
            if self._monitor_button:
                self._monitor_button.get_widget().configure(text="开始监控")
            
            logger.debug("系统监控已停止")
            return True
            
        except Exception as e:
            logger.error_struct("监控停止失败", error=str(e))
            return False
    
    def toggle_monitoring(self) -> None:
        """切换监控状态"""
        if self._is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def refresh_metrics(self) -> None:
        """手动刷新指标"""
        logger.debug("手动刷新指标")
        self._update_metrics()
    
    def set_update_interval(self, interval: float) -> None:
        """
        设置更新间隔
        
        Args:
            interval: 更新间隔（秒）
        """
        if interval < 0.5:
            logger.warning("更新间隔过短，使用最小值0.5秒")
            interval = 0.5
        
        self._update_interval = interval
        logger.debug_struct("更新间隔设置", interval=interval)
    
    def destroy(self) -> None:
        """销毁监控界面"""
        logger.debug("销毁监控界面")
        
        # 停止监控
        if self._is_monitoring:
            self.stop_monitoring()
        
        # 调用父类销毁方法
        super().destroy()
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控界面状态"""
        return {
            "widget_id": self._widget_id,
            "view_type": self._view_type.value,
            "is_monitoring": self._is_monitoring,
            "update_interval": self._update_interval,
            "metric_count": len(self._metrics),
            "has_plugin_registry": self._plugin_registry is not None
        }


class MonitorView:
    """
    系统监控视图
    
    集成系统监控界面到主窗口视图框架中
    """
    
    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        event_bus: EventBus,
        container: Container
    ):
        """
        初始化系统监控视图
        
        Args:
            parent: 父组件
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
        """
        self._parent = parent
        self._config_manager = config_manager
        self._event_bus = event_bus
        self._container = container
        
        # 主框架
        self._main_frame = None
        self._monitor_interface = None
        
        # 插件注册表（从容器获取）
        self._plugin_registry = None
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("系统监控视图初始化")
    
    def _initialize(self) -> None:
        """初始化系统监控视图"""
        try:
            # 创建主框架
            self._main_frame = ctk.CTkFrame(self._parent)
            self._main_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            # 配置网格
            self._main_frame.grid_rowconfigure(0, weight=1)
            self._main_frame.grid_columnconfigure(0, weight=1)
            
            # 尝试从容器获取插件注册表
            try:
                from ..plugins.registry import PluginRegistry
                self._plugin_registry = self._container.resolve(PluginRegistry)
            except Exception:
                logger.warning("无法从容器获取插件注册表")
            
            # 创建系统监控界面
            self._monitor_interface = MonitorInterface(
                self._main_frame,
                widget_id="system_monitoring",
                config_manager=self._config_manager,
                event_bus=self._event_bus,
                container=self._container,
                plugin_registry=self._plugin_registry
            )
            
            monitor_widget = self._monitor_interface.get_widget()
            if monitor_widget:
                monitor_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # 订阅监控相关事件
            self._subscribe_events()
            
            logger.info("系统监控视图初始化完成")
            
        except Exception as e:
            logger.error("系统监控视图初始化失败", exc_info=True)
            raise UIError(f"系统监控视图初始化失败: {e}")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 插件状态更新事件
        self._event_bus.subscribe("plugin.status.updated", self._on_plugin_status_updated)
        
        # 系统资源警报事件
        self._event_bus.subscribe("system.alert", self._on_system_alert)
    
    def _on_plugin_status_updated(self, event) -> None:
        """处理插件状态更新"""
        data = event.data
        plugin_name = data.get("plugin_name")
        new_status = data.get("status")
        
        logger.debug_struct("插件状态更新", plugin_name=plugin_name, status=new_status)
        
        # 刷新监控界面
        if self._monitor_interface:
            self._monitor_interface.refresh_metrics()
    
    def _on_system_alert(self, event) -> None:
        """处理系统警报"""
        data = event.data
        alert_type = data.get("alert_type")
        message = data.get("message")
        severity = data.get("severity")
        
        logger.debug_struct("系统警报", alert_type=alert_type, severity=severity, message=message)
        
        # 这里可以添加警报显示逻辑
        # 例如：在界面上显示警告消息
    
    def get_widget(self):
        """获取主框架"""
        return self._main_frame
    
    def get_monitor_interface(self) -> MonitorInterface:
        """获取系统监控界面"""
        return self._monitor_interface
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统监控视图状态"""
        if self._monitor_interface:
            return self._monitor_interface.get_status()
        return {"initialized": False}


class MetricHistory:
    """
    指标历史数据管理器
    
    负责：
    1. 存储历史指标数据
    2. 数据持久化到文件
    3. 查询历史数据
    4. 数据清理和归档
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        max_history_hours: int = 24,
        max_data_points: int = 1000
    ):
        """
        初始化指标历史管理器
        
        Args:
            storage_path: 数据存储路径，默认为None（内存存储）
            max_history_hours: 最大历史小时数
            max_data_points: 每个指标最大数据点数
        """
        self._storage_path = storage_path
        self._max_history_hours = max_history_hours
        self._max_data_points = max_data_points
        
        # 历史数据存储: metric_type -> list of (timestamp, value)
        self._history: Dict[str, List[tuple[float, float]]] = {}
        
        # 指标元数据
        self._metric_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 加载现有数据
        if storage_path:
            self._load_from_storage()
        
        logger.debug_struct("指标历史管理器初始化", 
                          storage_path=storage_path, 
                          max_history_hours=max_history_hours)
    
    def add_metric_data(self, metric_data: MetricData) -> None:
        """
        添加指标数据到历史
        
        Args:
            metric_data: 指标数据
        """
        metric_type = metric_data.metric_type.value
        
        # 初始化历史列表
        if metric_type not in self._history:
            self._history[metric_type] = []
        
        # 添加新数据点
        self._history[metric_type].append((metric_data.timestamp, metric_data.value))
        
        # 更新元数据
        self._update_metadata(metric_type, metric_data)
        
        # 清理旧数据
        self._cleanup_old_data(metric_type)
        
        # 自动保存（如果配置了存储路径）
        if self._storage_path and len(self._history[metric_type]) % 10 == 0:
            self._save_to_storage()
    
    def _update_metadata(self, metric_type: str, metric_data: MetricData) -> None:
        """更新指标元数据"""
        if metric_type not in self._metric_metadata:
            self._metric_metadata[metric_type] = {
                "label": metric_data.label,
                "unit": metric_data.unit,
                "description": metric_data.description,
                "threshold_warning": metric_data.threshold_warning,
                "threshold_critical": metric_data.threshold_critical,
                "min_value": metric_data.value,
                "max_value": metric_data.value,
                "avg_value": metric_data.value,
                "last_updated": metric_data.timestamp
            }
        else:
            meta = self._metric_metadata[metric_type]
            meta["min_value"] = min(meta["min_value"], metric_data.value)
            meta["max_value"] = max(meta["max_value"], metric_data.value)
            
            # 更新平均值
            history = self._history.get(metric_type, [])
            if history:
                total = sum(value for _, value in history)
                meta["avg_value"] = total / len(history)
            
            meta["last_updated"] = metric_data.timestamp
    
    def _cleanup_old_data(self, metric_type: str) -> None:
        """清理旧数据"""
        if metric_type not in self._history:
            return
        
        history = self._history[metric_type]
        if not history:
            return
        
        # 基于时间清理
        cutoff_time = time.time() - (self._max_history_hours * 3600)
        self._history[metric_type] = [
            (ts, val) for ts, val in history if ts >= cutoff_time
        ]
        
        # 基于数量清理
        if len(self._history[metric_type]) > self._max_data_points:
            # 保留最新的数据点
            self._history[metric_type] = self._history[metric_type][-self._max_data_points:]
    
    def get_history(
        self, 
        metric_type: str, 
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        max_points: Optional[int] = None
    ) -> List[tuple[float, float]]:
        """
        获取指标历史数据
        
        Args:
            metric_type: 指标类型
            start_time: 开始时间（时间戳）
            end_time: 结束时间（时间戳）
            max_points: 最大返回点数
            
        Returns:
            时间戳-值对的列表
        """
        if metric_type not in self._history:
            return []
        
        history = self._history[metric_type]
        
        # 时间范围过滤
        if start_time is not None:
            history = [(ts, val) for ts, val in history if ts >= start_time]
        if end_time is not None:
            history = [(ts, val) for ts, val in history if ts <= end_time]
        
        # 数量限制
        if max_points is not None and len(history) > max_points:
            # 均匀采样
            step = len(history) // max_points
            history = history[::step][:max_points]
        
        return history
    
    def get_statistics(self, metric_type: str) -> Dict[str, Any]:
        """
        获取指标统计信息
        
        Args:
            metric_type: 指标类型
            
        Returns:
            统计信息字典
        """
        if metric_type not in self._metric_metadata:
            return {}
        
        meta = self._metric_metadata[metric_type].copy()
        history = self._history.get(metric_type, [])
        
        if history:
            values = [val for _, val in history]
            meta.update({
                "current_value": values[-1] if values else 0,
                "data_point_count": len(values),
                "time_range_hours": (history[-1][0] - history[0][0]) / 3600 if len(history) > 1 else 0,
                "recent_trend": self._calculate_trend(metric_type)
            })
        
        return meta
    
    def _calculate_trend(self, metric_type: str, window_minutes: int = 30) -> Optional[float]:
        """计算趋势（最近window_minutes内的变化百分比）"""
        if metric_type not in self._history:
            return None
        
        history = self._history[metric_type]
        if len(history) < 2:
            return None
        
        cutoff_time = time.time() - (window_minutes * 60)
        recent_values = [val for ts, val in history if ts >= cutoff_time]
        
        if len(recent_values) < 2:
            return None
        
        start_val = recent_values[0]
        end_val = recent_values[-1]
        
        if start_val == 0:
            return None
        
        return ((end_val - start_val) / start_val) * 100
    
    def _save_to_storage(self) -> bool:
        """保存数据到存储"""
        if not self._storage_path:
            return False
        
        try:
            import json
            import os
            
            # 准备数据
            data = {
                "history": self._history,
                "metadata": self._metric_metadata,
                "max_history_hours": self._max_history_hours,
                "max_data_points": self._max_data_points,
                "saved_at": time.time()
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            
            # 写入文件
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug_struct("指标历史数据保存", path=self._storage_path)
            return True
            
        except Exception as e:
            logger.error_struct("指标历史数据保存失败", path=self._storage_path, error=str(e))
            return False
    
    def _load_from_storage(self) -> bool:
        """从存储加载数据"""
        if not self._storage_path:
            return False
        
        try:
            import json
            import os
            
            if not os.path.exists(self._storage_path):
                logger.debug("指标历史数据文件不存在，跳过加载")
                return False
            
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载数据
            self._history = data.get("history", {})
            self._metric_metadata = data.get("metadata", {})
            
            # 清理过期数据
            for metric_type in list(self._history.keys()):
                self._cleanup_old_data(metric_type)
            
            logger.debug_struct("指标历史数据加载", 
                              path=self._storage_path, 
                              metric_count=len(self._history))
            return True
            
        except Exception as e:
            logger.error_struct("指标历史数据加载失败", path=self._storage_path, error=str(e))
            return False
    
    def export_report(
        self, 
        output_path: str, 
        metric_types: Optional[List[str]] = None,
        format: str = "json"
    ) -> bool:
        """
        导出监控报告
        
        Args:
            output_path: 输出路径
            metric_types: 要导出的指标类型列表，None表示全部
            format: 导出格式，支持"json"、"csv"
            
        Returns:
            是否成功导出
        """
        try:
            import os
            
            if format == "json":
                return self._export_json_report(output_path, metric_types)
            elif format == "csv":
                return self._export_csv_report(output_path, metric_types)
            else:
                logger.warning_struct("不支持的导出格式", format=format)
                return False
                
        except Exception as e:
            logger.error_struct("监控报告导出失败", output_path=output_path, error=str(e))
            return False
    
    def _export_json_report(self, output_path: str, metric_types: Optional[List[str]]) -> bool:
        """导出JSON格式报告"""
        import json
        
        report_data = {}
        
        # 确定要导出的指标类型
        if metric_types is None:
            metric_types = list(self._history.keys())
        
        for metric_type in metric_types:
            if metric_type in self._history:
                report_data[metric_type] = {
                    "statistics": self.get_statistics(metric_type),
                    "history": self.get_history(metric_type, max_points=100)  # 限制历史点数
                }
        
        # 添加汇总信息
        report_data["_summary"] = {
            "exported_at": time.time(),
            "metric_count": len(report_data),
            "time_range": f"{self._max_history_hours}小时"
        }
        
        # 写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.debug_struct("JSON监控报告导出", output_path=output_path)
        return True
    
    def _export_csv_report(self, output_path: str, metric_types: Optional[List[str]]) -> bool:
        """导出CSV格式报告"""
        import csv
        
        if metric_types is None:
            metric_types = list(self._history.keys())
        
        # 写入CSV文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow(["timestamp", "metric_type", "value", "unit", "label"])
            
            # 写入数据
            for metric_type in metric_types:
                if metric_type in self._history:
                    meta = self._metric_metadata.get(metric_type, {})
                    for timestamp, value in self._history[metric_type]:
                        # 时间戳转换为可读格式
                        from datetime import datetime
                        time_str = datetime.fromtimestamp(timestamp).isoformat()
                        writer.writerow([
                            time_str,
                            metric_type,
                            value,
                            meta.get("unit", ""),
                            meta.get("label", "")
                        ])
        
        logger.debug_struct("CSV监控报告导出", output_path=output_path)
        return True
    
    def clear_history(self, metric_type: Optional[str] = None) -> None:
        """
        清空历史数据
        
        Args:
            metric_type: 要清空的指标类型，None表示全部
        """
        if metric_type is None:
            self._history.clear()
            self._metric_metadata.clear()
        elif metric_type in self._history:
            del self._history[metric_type]
            if metric_type in self._metric_metadata:
                del self._metric_metadata[metric_type]
        
        logger.debug_struct("指标历史数据清空", metric_type=metric_type)
    
    def get_metric_types(self) -> List[str]:
        """获取所有指标类型"""
        return list(self._history.keys())
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        return {
            "total_metric_types": len(self._history),
            "total_data_points": sum(len(data) for data in self._history.values()),
            "storage_path": self._storage_path,
            "max_history_hours": self._max_history_hours,
            "max_data_points": self._max_data_points
        }


class ChartCanvas:
    """
    图表画布组件
    
    使用tkinter Canvas绘制简单折线图
    """
    
    def __init__(
        self,
        parent,
        width: int = 400,
        height: int = 200,
        widget_id: Optional[str] = None,
        **kwargs
    ):
        """
        初始化图表画布
        
        Args:
            parent: 父组件
            width: 画布宽度
            height: 画布高度
            widget_id: 组件ID
            **kwargs: 其他参数
        """
        self._parent = parent
        self._width = width
        self._height = height
        self._widget_id = widget_id or f"chart_{id(self)}"
        self._kwargs = kwargs
        
        # 画布组件
        self._canvas = None
        self._chart_items = []
        
        # 图表配置
        self._margin = {"top": 20, "right": 20, "bottom": 40, "left": 50}
        self._chart_width = width - self._margin["left"] - self._margin["right"]
        self._chart_height = height - self._margin["top"] - self._margin["bottom"]
        
        # 数据
        self._data: List[tuple[float, float]] = []  # (x, y) 数据点
        self._x_range = (0, 1)  # x轴范围
        self._y_range = (0, 1)  # y轴范围
        
        # 样式
        self._style = {
            "bg_color": ("white", "gray10"),
            "grid_color": ("gray80", "gray40"),
            "axis_color": ("gray50", "gray60"),
            "line_color": ("blue", "lightblue"),
            "point_color": ("red", "orange"),
            "text_color": ("gray30", "gray70")
        }
        
        # 初始化
        self._initialize()
        
        logger.debug_struct("图表画布初始化", widget_id=self._widget_id, size=f"{width}x{height}")
    
    def _initialize(self) -> None:
        """初始化画布"""
        # 创建画布
        self._canvas = ctk.CTkCanvas(
            self._parent,
            width=self._width,
            height=self._height,
            highlightthickness=0
        )
        
        # 应用初始样式
        self._apply_style()
    
    def _apply_style(self) -> None:
        """应用样式到画布"""
        if not self._canvas:
            return
        
        # 设置背景色
        bg_color = self._get_color(self._style["bg_color"])
        self._canvas.configure(bg=bg_color)
    
    def _get_color(self, color_spec: Union[str, tuple]) -> str:
        """
        获取颜色值
        
        Args:
            color_spec: 颜色规格，可以是颜色元组(light_mode, dark_mode)或颜色字符串
            
        Returns:
            颜色字符串
        """
        if isinstance(color_spec, tuple) and len(color_spec) == 2:
            # 根据当前主题选择颜色
            try:
                # 检查当前主题
                appearance_mode = ctk.get_appearance_mode()
                if appearance_mode == "Dark":
                    return color_spec[1]
                else:
                    return color_spec[0]
            except:
                return color_spec[0]
        return color_spec
    
    def set_data(self, data: List[tuple[float, float]]) -> None:
        """
        设置图表数据
        
        Args:
            data: 数据点列表，每个点是(x, y)元组
        """
        self._data = data.copy() if data else []
        
        # 计算坐标轴范围
        self._calculate_ranges()
        
        # 重绘图表
        self._draw_chart()
    
    def set_time_series_data(self, time_series: List[tuple[float, float]]) -> None:
        """
        设置时间序列数据
        
        Args:
            time_series: 时间序列数据，每个点是(时间戳, 值)
        """
        if not time_series:
            self.set_data([])
            return
        
        # 将时间戳转换为相对时间（从最早的时间戳开始）
        timestamps = [ts for ts, _ in time_series]
        values = [val for _, val in time_series]
        
        if not timestamps:
            self.set_data([])
            return
        
        min_time = min(timestamps)
        relative_times = [(ts - min_time) / 60.0 for ts in timestamps]  # 转换为分钟
        
        # 创建数据点
        data = list(zip(relative_times, values))
        self.set_data(data)
    
    def _calculate_ranges(self) -> None:
        """计算坐标轴范围"""
        if not self._data:
            self._x_range = (0, 1)
            self._y_range = (0, 1)
            return
        
        x_values = [x for x, _ in self._data]
        y_values = [y for _, y in self._data]
        
        if x_values:
            x_min = min(x_values)
            x_max = max(x_values)
            # 添加一些边距
            x_range = x_max - x_min
            self._x_range = (x_min - x_range * 0.05, x_max + x_range * 0.05) if x_range > 0 else (x_min - 0.5, x_max + 0.5)
        else:
            self._x_range = (0, 1)
        
        if y_values:
            y_min = min(y_values)
            y_max = max(y_values)
            # 添加一些边距
            y_range = y_max - y_min
            self._y_range = (y_min - y_range * 0.1, y_max + y_range * 0.1) if y_range > 0 else (y_min - 0.5, y_max + 0.5)
        else:
            self._y_range = (0, 1)
    
    def _draw_chart(self) -> None:
        """绘制图表"""
        if not self._canvas:
            return
        
        # 清除现有图形
        self._canvas.delete("all")
        self._chart_items.clear()
        
        # 绘制背景
        self._draw_background()
        
        # 绘制网格
        self._draw_grid()
        
        # 绘制坐标轴
        self._draw_axes()
        
        # 绘制数据
        if self._data:
            self._draw_data()
        
        # 绘制标题和标签
        self._draw_labels()
    
    def _draw_background(self) -> None:
        """绘制背景"""
        bg_color = self._get_color(self._style["bg_color"])
        
        # 绘制整个背景
        bg_item = self._canvas.create_rectangle(
            0, 0, self._width, self._height,
            fill=bg_color, outline=bg_color
        )
        self._chart_items.append(bg_item)
        
        # 绘制图表区域背景
        chart_bg_color = self._get_color(("white", "gray15"))
        chart_bg_item = self._canvas.create_rectangle(
            self._margin["left"], self._margin["top"],
            self._width - self._margin["right"], self._height - self._margin["bottom"],
            fill=chart_bg_color, outline=chart_bg_color
        )
        self._chart_items.append(chart_bg_item)
    
    def _draw_grid(self) -> None:
        """绘制网格线"""
        grid_color = self._get_color(self._style["grid_color"])
        
        # 垂直网格线（5条）
        for i in range(6):
            x = self._margin["left"] + (self._chart_width * i / 5)
            
            # 主网格线
            grid_item = self._canvas.create_line(
                x, self._margin["top"],
                x, self._height - self._margin["bottom"],
                fill=grid_color, width=1
            )
            self._chart_items.append(grid_item)
        
        # 水平网格线（5条）
        for i in range(6):
            y = self._margin["top"] + (self._chart_height * i / 5)
            
            # 主网格线
            grid_item = self._canvas.create_line(
                self._margin["left"], y,
                self._width - self._margin["right"], y,
                fill=grid_color, width=1
            )
            self._chart_items.append(grid_item)
    
    def _draw_axes(self) -> None:
        """绘制坐标轴"""
        axis_color = self._get_color(self._style["axis_color"])
        
        # X轴
        x_axis_item = self._canvas.create_line(
            self._margin["left"], self._height - self._margin["bottom"],
            self._width - self._margin["right"], self._height - self._margin["bottom"],
            fill=axis_color, width=2
        )
        self._chart_items.append(x_axis_item)
        
        # Y轴
        y_axis_item = self._canvas.create_line(
            self._margin["left"], self._margin["top"],
            self._margin["left"], self._height - self._margin["bottom"],
            fill=axis_color, width=2
        )
        self._chart_items.append(y_axis_item)
    
    def _draw_data(self) -> None:
        """绘制数据"""
        if len(self._data) < 2:
            # 只有一个数据点，绘制点
            self._draw_single_point()
        else:
            # 绘制折线
            self._draw_line()
    
    def _draw_single_point(self) -> None:
        """绘制单个数据点"""
        point_color = self._get_color(self._style["point_color"])
        
        for x, y in self._data:
            canvas_x = self._data_to_canvas_x(x)
            canvas_y = self._data_to_canvas_y(y)
            
            point_item = self._canvas.create_oval(
                canvas_x - 4, canvas_y - 4,
                canvas_x + 4, canvas_y + 4,
                fill=point_color, outline=point_color
            )
            self._chart_items.append(point_item)
    
    def _draw_line(self) -> None:
        """绘制折线图"""
        line_color = self._get_color(self._style["line_color"])
        point_color = self._get_color(self._style["point_color"])
        
        # 绘制折线
        points = []
        for x, y in self._data:
            canvas_x = self._data_to_canvas_x(x)
            canvas_y = self._data_to_canvas_y(y)
            points.extend([canvas_x, canvas_y])
        
        if len(points) >= 4:
            line_item = self._canvas.create_line(
                *points,
                fill=line_color, width=2, smooth=True
            )
            self._chart_items.append(line_item)
        
        # 绘制数据点
        for x, y in self._data:
            canvas_x = self._data_to_canvas_x(x)
            canvas_y = self._data_to_canvas_y(y)
            
            point_item = self._canvas.create_oval(
                canvas_x - 3, canvas_y - 3,
                canvas_x + 3, canvas_y + 3,
                fill=point_color, outline=point_color
            )
            self._chart_items.append(point_item)
    
    def _draw_labels(self) -> None:
        """绘制标签"""
        text_color = self._get_color(self._style["text_color"])
        
        # X轴标签（5个刻度）
        for i in range(6):
            x = self._margin["left"] + (self._chart_width * i / 5)
            value = self._x_range[0] + (self._x_range[1] - self._x_range[0]) * i / 5
            
            # 刻度线
            tick_item = self._canvas.create_line(
                x, self._height - self._margin["bottom"],
                x, self._height - self._margin["bottom"] + 5,
                fill=text_color, width=1
            )
            self._chart_items.append(tick_item)
            
            # 刻度标签
            label_text = f"{value:.1f}"
            if self._x_range[1] - self._x_range[0] > 100:
                label_text = f"{value:.0f}"
            
            label_item = self._canvas.create_text(
                x, self._height - self._margin["bottom"] + 15,
                text=label_text,
                fill=text_color,
                font=("Microsoft YaHei", 9),
                anchor="n"
            )
            self._chart_items.append(label_item)
        
        # Y轴标签（5个刻度）
        for i in range(6):
            y = self._margin["top"] + (self._chart_height * i / 5)
            value = self._y_range[1] - (self._y_range[1] - self._y_range[0]) * i / 5
            
            # 刻度线
            tick_item = self._canvas.create_line(
                self._margin["left"] - 5, y,
                self._margin["left"], y,
                fill=text_color, width=1
            )
            self._chart_items.append(tick_item)
            
            # 刻度标签
            label_text = f"{value:.1f}"
            if self._y_range[1] - self._y_range[0] > 100:
                label_text = f"{value:.0f}"
            
            label_item = self._canvas.create_text(
                self._margin["left"] - 10, y,
                text=label_text,
                fill=text_color,
                font=("Microsoft YaHei", 9),
                anchor="e"
            )
            self._chart_items.append(label_item)
    
    def _data_to_canvas_x(self, x: float) -> float:
        """将数据x坐标转换为画布x坐标"""
        x_min, x_max = self._x_range
        if x_max == x_min:
            return self._margin["left"] + self._chart_width / 2
        
        normalized_x = (x - x_min) / (x_max - x_min)
        return self._margin["left"] + (normalized_x * self._chart_width)
    
    def _data_to_canvas_y(self, y: float) -> float:
        """将数据y坐标转换为画布y坐标"""
        y_min, y_max = self._y_range
        if y_max == y_min:
            return self._margin["top"] + self._chart_height / 2
        
        normalized_y = (y - y_min) / (y_max - y_min)
        # 注意：画布y坐标从上到下增加，所以需要反转
        return self._height - self._margin["bottom"] - (normalized_y * self._chart_height)
    
    def set_style(self, style: Dict[str, Any]) -> None:
        """
        设置图表样式
        
        Args:
            style: 样式字典
        """
        self._style.update(style)
        self._apply_style()
        if self._data:
            self._draw_chart()
    
    def get_widget(self) -> ctk.CTkCanvas:
        """获取画布组件"""
        return self._canvas
    
    def resize(self, width: int, height: int) -> None:
        """
        调整画布大小
        
        Args:
            width: 新宽度
            height: 新高度
        """
        self._width = width
        self._height = height
        self._chart_width = width - self._margin["left"] - self._margin["right"]
        self._chart_height = height - self._margin["top"] - self._margin["bottom"]
        
        if self._canvas:
            self._canvas.configure(width=width, height=height)
            self._draw_chart()


class EnhancedMonitorInterface(MonitorInterface):
    """
    增强版系统监控界面
    
    在基础监控界面基础上增加：
    1. 历史数据存储
    2. 图表显示
    3. 警报系统
    4. 报告导出
    """
    
    def __init__(
        self,
        parent,
        widget_id: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        event_bus: Optional[EventBus] = None,
        container: Optional[Container] = None,
        plugin_registry: Optional[PluginRegistry] = None,
        storage_path: Optional[str] = None,
        **kwargs
    ):
        """
        初始化增强版系统监控界面
        
        Args:
            parent: 父组件
            widget_id: 组件ID
            config_manager: 配置管理器
            event_bus: 事件总线
            container: 依赖注入容器
            plugin_registry: 插件注册表
            storage_path: 数据存储路径
            **kwargs: 其他参数
        """
        super().__init__(parent, widget_id, config_manager, event_bus, container, plugin_registry, **kwargs)
        
        # 历史数据管理器
        self._metric_history = MetricHistory(storage_path=storage_path)
        
        # 图表组件
        self._chart_frame = None
        self._chart_canvas = None
        
        # 警报系统
        self._alerts: List[Dict[str, Any]] = []
        self._alert_thresholds: Dict[str, Dict[str, float]] = {}
        
        # 初始化警报阈值
        self._initialize_alert_thresholds()
        
        logger.debug_struct("增强版系统监控界面初始化", 
                          widget_id=self._widget_id,
                          storage_path=storage_path)
    
    def _initialize_alert_thresholds(self) -> None:
        """初始化警报阈值"""
        # 默认阈值配置
        self._alert_thresholds = {
            MetricType.CPU_USAGE.value: {
                "warning": 80.0,
                "critical": 95.0
            },
            MetricType.MEMORY_USAGE.value: {
                "warning": 80.0,  # 百分比
                "critical": 95.0
            },
            MetricType.DISK_USAGE.value: {
                "warning": 80.0,
                "critical": 95.0
            }
        }
    
    def create_widget(self) -> ctk.CTkBaseClass:
        """创建增强版系统监控界面组件"""
        # 调用父类方法创建基础组件
        main_widget = super().create_widget()
        
        if not main_widget:
            return main_widget
        
        # 添加图表区域
        self._create_chart_area(main_widget)
        
        # 添加警报区域
        self._create_alert_area(main_widget)
        
        # 添加导出控制
        self._create_export_controls(main_widget)
        
        return main_widget
    
    def _create_chart_area(self, parent) -> None:
        """创建图表区域"""
        logger.debug("创建图表区域")
        
        # 图表框架
        chart_frame = ctk.CTkFrame(parent)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=(5, 0))
        
        # 配置图表框架网格
        chart_frame.grid_rowconfigure(1, weight=1)  # 图表区域
        chart_frame.grid_columnconfigure(0, weight=1)
        
        # 图表控制面板
        chart_control_frame = ctk.CTkFrame(chart_frame, fg_color="transparent", height=40)
        chart_control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        chart_control_frame.grid_propagate(False)
        
        # 图表标题
        chart_title = ctk.CTkLabel(
            chart_control_frame,
            text="性能趋势图表",
            font=("Microsoft YaHei", 12, "bold"),
            anchor="w"
        )
        chart_title.pack(side="left", fill="y", padx=(0, 20))
        
        # 指标选择
        metric_options = list(self._metrics.keys())
        if metric_options:
            self._chart_metric_var = ctk.StringVar(value=metric_options[0])
            metric_combo = ctk.CTkComboBox(
                chart_control_frame,
                values=metric_options,
                variable=self._chart_metric_var,
                width=150,
                command=self._on_chart_metric_changed
            )
            metric_combo.pack(side="left", padx=(0, 10))
        
        # 时间范围选择
        time_options = ["1小时", "6小时", "12小时", "24小时"]
        self._chart_time_var = ctk.StringVar(value="6小时")
        time_combo = ctk.CTkComboBox(
            chart_control_frame,
            values=time_options,
            variable=self._chart_time_var,
            width=100,
            command=self._on_chart_time_changed
        )
        time_combo.pack(side="left", padx=(0, 10))
        
        # 刷新图表按钮
        refresh_chart_btn = ctk.CTkButton(
            chart_control_frame,
            text="刷新图表",
            width=80,
            command=self._refresh_chart
        )
        refresh_chart_btn.pack(side="left")
        
        # 图表画布
        chart_canvas_frame = ctk.CTkFrame(chart_frame)
        chart_canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # 创建图表画布
        self._chart_canvas = ChartCanvas(
            chart_canvas_frame,
            width=600,
            height=250
        )
        chart_widget = self._chart_canvas.get_widget()
        if chart_widget:
            chart_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 注册组件
        self.register_widget("chart_frame", chart_frame)
        self.register_widget("chart_canvas_frame", chart_canvas_frame)
        self._chart_frame = chart_frame
        
        # 初始图表数据
        self._refresh_chart()
    
    def _create_alert_area(self, parent) -> None:
        """创建警报区域"""
        logger.debug("创建警报区域")
        
        # 警报框架
        alert_frame = ctk.CTkFrame(parent)
        alert_frame.grid(row=3, column=0, sticky="nsew", padx=0, pady=(5, 0))
        
        # 警报标题
        alert_title = ctk.CTkLabel(
            alert_frame,
            text="系统警报",
            font=("Microsoft YaHei", 12, "bold"),
            anchor="w"
        )
        alert_title.pack(fill="x", padx=10, pady=5)
        
        # 警报列表框架
        alert_list_frame = ctk.CTkScrollableFrame(alert_frame, height=100)
        alert_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 初始无警报消息
        no_alerts_label = ctk.CTkLabel(
            alert_list_frame,
            text="暂无警报",
            font=("Microsoft YaHei", 10),
            text_color=("gray50", "gray60")
        )
        no_alerts_label.pack(pady=20)
        
        # 存储引用
        self._alert_frame = alert_frame
        self._alert_list_frame = alert_list_frame
        self._no_alerts_label = no_alerts_label
        
        # 注册组件
        self.register_widget("alert_frame", alert_frame)
        self.register_widget("alert_list_frame", alert_list_frame)
    
    def _create_export_controls(self, parent) -> None:
        """创建导出控制"""
        logger.debug("创建导出控制")
        
        # 导出框架
        export_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        export_frame.grid(row=4, column=0, sticky="nsew", padx=0, pady=(5, 5))
        export_frame.grid_propagate(False)
        
        # 导出按钮
        export_json_btn = ctk.CTkButton(
            export_frame,
            text="导出JSON报告",
            width=120,
            command=lambda: self._export_report("json")
        )
        export_json_btn.pack(side="left", padx=5)
        
        export_csv_btn = ctk.CTkButton(
            export_frame,
            text="导出CSV数据",
            width=120,
            command=lambda: self._export_report("csv")
        )
        export_csv_btn.pack(side="left", padx=5)
        
        clear_history_btn = ctk.CTkButton(
            export_frame,
            text="清空历史数据",
            width=120,
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray30"),
            command=self._clear_history
        )
        clear_history_btn.pack(side="left", padx=5)
        
        # 注册组件
        self.register_widget("export_frame", export_frame)
    
    def _on_chart_metric_changed(self, choice: str) -> None:
        """处理图表指标变化"""
        logger.debug_struct("图表指标变更", metric_type=choice)
        self._refresh_chart()
    
    def _on_chart_time_changed(self, choice: str) -> None:
        """处理图表时间范围变化"""
        logger.debug_struct("图表时间范围变更", time_range=choice)
        self._refresh_chart()
    
    def _refresh_chart(self) -> None:
        """刷新图表"""
        if not self._chart_canvas:
            return
        
        # 获取选中的指标
        metric_type = getattr(self, '_chart_metric_var', None)
        if metric_type:
            selected_metric = metric_type.get()
        else:
            # 默认选择第一个指标
            metric_types = list(self._metrics.keys())
            if not metric_types:
                return
            selected_metric = metric_types[0]
        
        # 获取时间范围
        time_range_str = getattr(self, '_chart_time_var', "6小时")
        if isinstance(time_range_str, ctk.StringVar):
            time_range_str = time_range_str.get()
        
        # 计算时间范围（秒）
        time_ranges = {
            "1小时": 3600,
            "6小时": 21600,
            "12小时": 43200,
            "24小时": 86400
        }
        time_range_seconds = time_ranges.get(time_range_str, 21600)
        
        # 获取历史数据
        start_time = time.time() - time_range_seconds
        history_data = self._metric_history.get_history(
            selected_metric,
            start_time=start_time,
            max_points=100
        )
        
        # 更新图表
        if history_data:
            self._chart_canvas.set_time_series_data(history_data)
    
    def _export_report(self, format: str) -> None:
        """导出报告"""
        import tkinter.filedialog as fd
        import os
        
        # 选择文件路径
        file_ext = ".json" if format == "json" else ".csv"
        default_name = f"monitor_report_{time.strftime('%Y%m%d_%H%M%S')}{file_ext}"
        
        file_path = fd.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=[(f"{format.upper()}文件", f"*{file_ext}")],
            initialfile=default_name
        )
        
        if not file_path:
            return  # 用户取消
        
        # 导出报告
        success = self._metric_history.export_report(file_path, format=format)
        
        if success:
            # 显示成功消息
            success_label = ctk.CTkLabel(
                self._export_frame,
                text=f"报告已导出: {os.path.basename(file_path)}",
                text_color="green",
                font=("Microsoft YaHei", 9)
            )
            success_label.pack(side="left", padx=10)
            
            # 3秒后移除消息
            def remove_success_label():
                success_label.destroy()
            
            self._parent.after(3000, remove_success_label)
    
    def _clear_history(self) -> None:
        """清空历史数据"""
        # 确认对话框
        import tkinter.messagebox as mb
        
        result = mb.askyesno(
            "确认清空",
            "确定要清空所有历史监控数据吗？此操作不可恢复。"
        )
        
        if result:
            self._metric_history.clear_history()
            logger.info("监控历史数据已清空")
            
            # 刷新图表
            self._refresh_chart()
    
    def _update_metrics(self) -> None:
        """更新指标数据（覆盖父类方法）"""
        # 调用父类方法更新基础指标
        super()._update_metrics()
        
        # 将指标数据保存到历史
        for metric_data in self._metrics.values():
            self._metric_history.add_metric_data(metric_data)
            
            # 检查警报阈值
            self._check_alert_thresholds(metric_data)
        
        # 定期刷新图表
        if hasattr(self, '_last_chart_refresh'):
            if time.time() - self._last_chart_refresh > 30:  # 每30秒刷新一次图表
                self._refresh_chart()
                self._last_chart_refresh = time.time()
        else:
            self._last_chart_refresh = time.time()
    
    def _check_alert_thresholds(self, metric_data: MetricData) -> None:
        """检查警报阈值"""
        metric_type = metric_data.metric_type.value
        
        if metric_type not in self._alert_thresholds:
            return
        
        thresholds = self._alert_thresholds[metric_type]
        warning_threshold = thresholds.get("warning")
        critical_threshold = thresholds.get("critical")
        
        if critical_threshold is not None and metric_data.value >= critical_threshold:
            self._add_alert(
                level="critical",
                metric_type=metric_type,
                message=f"{metric_data.label} 已达到临界值: {metric_data.get_display_value()}",
                value=metric_data.value,
                threshold=critical_threshold
            )
        elif warning_threshold is not None and metric_data.value >= warning_threshold:
            self._add_alert(
                level="warning",
                metric_type=metric_type,
                message=f"{metric_data.label} 已达到警告值: {metric_data.get_display_value()}",
                value=metric_data.value,
                threshold=warning_threshold
            )
    
    def _add_alert(self, level: str, metric_type: str, message: str, value: float, threshold: float) -> None:
        """添加警报"""
        alert_id = f"alert_{len(self._alerts)}_{int(time.time())}"
        
        alert = {
            "id": alert_id,
            "level": level,
            "metric_type": metric_type,
            "message": message,
            "value": value,
            "threshold": threshold,
            "timestamp": time.time(),
            "acknowledged": False
        }
        
        # 避免重复警报（相同指标类型和级别在5分钟内）
        recent_alerts = [
            a for a in self._alerts 
            if a["metric_type"] == metric_type and 
               a["level"] == level and
               time.time() - a["timestamp"] < 300  # 5分钟
        ]
        
        if not recent_alerts:
            self._alerts.append(alert)
            self._update_alert_display()
            
            # 发布警报事件
            if self._event_bus:
                self._event_bus.publish("monitor.alert", alert)
            
            logger.warning_struct("系统警报触发", 
                                metric_type=metric_type,
                                level=level,
                                value=value,
                                threshold=threshold)
    
    def _update_alert_display(self) -> None:
        """更新警报显示"""
        if not hasattr(self, '_alert_list_frame'):
            return
        
        # 清除现有警报显示
        for widget in self._alert_list_frame.winfo_children():
            widget.destroy()
        
        # 显示警报
        if not self._alerts:
            # 显示无警报消息
            no_alerts_label = ctk.CTkLabel(
                self._alert_list_frame,
                text="暂无警报",
                font=("Microsoft YaHei", 10),
                text_color=("gray50", "gray60")
            )
            no_alerts_label.pack(pady=20)
            return
        
        # 显示警报列表
        for alert in self._alerts[-10:]:  # 显示最近10条警报
            self._create_alert_item(alert)
    
    def _create_alert_item(self, alert: Dict[str, Any]) -> None:
        """创建警报项"""
        # 警报卡片框架
        alert_color = "red" if alert["level"] == "critical" else "orange"
        
        alert_frame = ctk.CTkFrame(
            self._alert_list_frame,
            fg_color=(f"#{alert_color}20", f"#{alert_color}20"),
            border_color=alert_color,
            border_width=1,
            corner_radius=5
        )
        alert_frame.pack(fill="x", padx=5, pady=2)
        
        # 警报内容
        time_str = time.strftime("%H:%M:%S", time.localtime(alert["timestamp"]))
        
        alert_text = f"[{time_str}] {alert['message']}"
        alert_label = ctk.CTkLabel(
            alert_frame,
            text=alert_text,
            font=("Microsoft YaHei", 9),
            text_color=alert_color,
            anchor="w",
            justify="left"
        )
        alert_label.pack(fill="x", padx=10, pady=5)
        
        # 确认按钮（如果未确认）
        if not alert["acknowledged"]:
            def acknowledge_alert(alert_id=alert["id"]):
                self._acknowledge_alert(alert_id)
            
            ack_button = ctk.CTkButton(
                alert_frame,
                text="确认",
                width=50,
                height=20,
                font=("Microsoft YaHei", 8),
                command=acknowledge_alert
            )
            ack_button.pack(side="right", padx=(0, 10), pady=5)
    
    def _acknowledge_alert(self, alert_id: str) -> None:
        """确认警报"""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                break
        
        self._update_alert_display()
    
    def get_metric_history(self) -> MetricHistory:
        """获取指标历史管理器"""
        return self._metric_history
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取当前警报列表"""
        return self._alerts.copy()
    
    def clear_alerts(self) -> None:
        """清空警报"""
        self._alerts.clear()
        self._update_alert_display()
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """获取增强版状态信息"""
        base_status = super().get_status()
        history_summary = self._metric_history.get_data_summary()
        
        enhanced_status = {
            **base_status,
            "history_summary": history_summary,
            "alert_count": len(self._alerts),
            "unacknowledged_alerts": len([a for a in self._alerts if not a["acknowledged"]]),
            "has_chart": self._chart_canvas is not None
        }
        
        return enhanced_status


# 导出
__all__ = [
    "MonitorViewType",
    "MetricType",
    "MetricData",
    "MetricCard",
    "MonitorInterface",
    "MonitorView",
    "MetricHistory",
    "ChartCanvas",
    "EnhancedMonitorInterface"
]