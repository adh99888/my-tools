"""
智能侧边栏
自适应布局，优化阅读体验，解决侧边栏狭小问题
"""

import time
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QLabel, QScrollArea,
                             QFrame, QSplitter, QComboBox, QCheckBox,
                             QLineEdit, QListWidget, QListWidgetItem, 
                             QTabWidget, QToolButton, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCursor, QIcon

from engines.translation.model_router import TranslationResult

class TranslationItemWidget(QFrame):
    """单个翻译项部件"""
    
    def __init__(self, result: TranslationResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 220);
                border-radius: 5px;
                margin: 5px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 标题栏（显示时间和模型）
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        
        time_label = QLabel(time.strftime("%H:%M:%S"))
        time_label.setStyleSheet("color: #666; font-size: 9pt;")
        title_layout.addWidget(time_label)
        
        model_label = QLabel(f"模型: {self.result.model}")
        model_label.setStyleSheet("color: #888; font-size: 9pt;")
        title_layout.addWidget(model_label)
        
        title_layout.addStretch()
        
        # 复制按钮
        copy_btn = QToolButton()
        copy_btn.setText("📋")
        copy_btn.setToolTip("复制译文")
        copy_btn.clicked.connect(self.copy_translation)
        title_layout.addWidget(copy_btn)
        
        layout.addWidget(title_bar)
        
        # 原文区域
        source_group = QWidget()
        source_layout = QVBoxLayout(source_group)
        
        source_label = QLabel("原文:")
        source_label.setStyleSheet("font-weight: bold; color: #333; font-size: 10pt;")
        source_layout.addWidget(source_label)
        
        self.source_text = QTextEdit()
        self.source_text.setPlainText(self.result.source_text)
        self.source_text.setReadOnly(True)
        self.source_text.setMaximumHeight(80)
        self.source_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                padding: 3px;
                background-color: #f9f9f9;
                font-size: 10pt;
            }
        """)
        source_layout.addWidget(self.source_text)
        
        layout.addWidget(source_group)
        
        # 翻译区域
        trans_group = QWidget()
        trans_layout = QVBoxLayout(trans_group)
        
        trans_label = QLabel("译文:")
        trans_label.setStyleSheet("font-weight: bold; color: #0066cc; font-size: 11pt;")
        trans_layout.addWidget(trans_label)
        
        self.trans_text = QTextEdit()
        self.trans_text.setPlainText(self.result.translated_text)
        self.trans_text.setReadOnly(True)
        self.trans_text.setMinimumHeight(60)
        self.trans_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cce5ff;
                border-radius: 3px;
                padding: 5px;
                background-color: #f0f7ff;
                font-size: 11pt;
            }
        """)
        trans_layout.addWidget(self.trans_text)
        
        layout.addWidget(trans_group)
        
        # 状态栏（显示语言和置信度）
        status_bar = QWidget()
        status_layout = QHBoxLayout(status_bar)
        
        lang_label = QLabel(f"{self.result.source_lang} → {self.result.target_lang}")
        lang_label.setStyleSheet("color: #666; font-size: 9pt;")
        status_layout.addWidget(lang_label)
        
        if self.result.confidence is not None:
            confidence_label = QLabel(f"置信度: {self.result.confidence:.2f}")
            confidence_label.setStyleSheet("color: #888; font-size: 9pt;")
            status_layout.addWidget(confidence_label)
        
        status_layout.addStretch()
        
        # 响应时间
        time_label = QLabel(f"耗时: {self.result.response_time:.0f}ms")
        time_label.setStyleSheet("color: #999; font-size: 8pt;")
        status_layout.addWidget(time_label)
        
        layout.addWidget(status_bar)
        
        self.setLayout(layout)
    
    def copy_translation(self):
        """复制译文到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result.translated_text)
        
        # 显示反馈
        self.trans_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #4CAF50;
                border-radius: 3px;
                padding: 5px;
                background-color: #f0f7ff;
                font-size: 11pt;
            }
        """)
        QTimer.singleShot(500, self.reset_style)
    
    def reset_style(self):
        """重置样式"""
        self.trans_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cce5ff;
                border-radius: 3px;
                padding: 5px;
                background-color: #f0f7ff;
                font-size: 11pt;
            }
        """)

class SmartSidebar(QMainWindow):
    """智能侧边栏窗口"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
        # 显示配置
        self.width_mode = config.get('display', {}).get('width', 'adaptive')
        self.max_width = config.get('display', {}).get('max_width', 800)
        self.min_width = config.get('display', {}).get('min_width', 400)
        self.font_size = config.get('display', {}).get('font_size', 12)
        self.theme = config.get('display', {}).get('theme', 'dark')
        
        # 数据
        self.translation_history = []
        self.max_history_items = 50
        
        # 当前布局模式
        self.current_layout = 'compact'  # compact/balanced/expanded/dual
        
        # 初始化UI
        self.init_ui()
        
        # 应用主题
        self.apply_theme()
        
        # 设置窗口属性
        self.set_window_properties()
    
    def init_ui(self):
        """初始化用户界面"""
        # 窗口设置
        self.setWindowTitle("翻译结果")
        
        # 计算初始大小
        self.adjust_window_size()
        
        # 设置窗口属性：置顶、无边框
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏（可拖动）
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        # 标题
        title_label = QLabel("📖 实时翻译")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # 布局模式选择
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["紧凑模式", "平衡模式", "扩展模式", "双栏模式"])
        self.layout_combo.currentTextChanged.connect(self.change_layout_mode)
        self.layout_combo.setMaximumWidth(100)
        title_layout.addWidget(self.layout_combo)
        
        title_layout.addStretch()
        
        # 控制按钮
        btn_minimize = QPushButton("－")
        btn_minimize.setFixedSize(20, 20)
        btn_minimize.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("×")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(btn_minimize)
        title_layout.addWidget(btn_close)
        
        main_layout.addWidget(self.title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 搜索和过滤
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索翻译历史...")
        self.search_box.textChanged.connect(self.filter_history)
        filter_layout.addWidget(self.search_box)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_history)
        filter_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_history)
        filter_layout.addWidget(self.export_btn)
        
        self.content_layout.addWidget(filter_widget)
        
        # 主显示区域
        self.main_display = QTabWidget()
        
        # 翻译历史标签页
        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.scroll_content)
        history_layout.addWidget(self.scroll_area)
        
        self.main_display.addTab(self.history_tab, "历史记录")
        
        # 统计标签页（可扩展）
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        stats_label = QLabel("翻译统计")
        stats_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(stats_label)
        
        self.main_display.addTab(stats_tab, "统计")
        
        self.content_layout.addWidget(self.main_display)
        
        main_layout.addWidget(content_widget)
        
        # 底部状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; padding: 3px; font-size: 9pt;")
        main_layout.addWidget(self.status_label)
    
    def set_window_properties(self):
        """设置窗口属性"""
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        
        # 计算初始位置（右侧中央）
        x = screen.width() - self.width()
        y = (screen.height() - self.height()) // 2
        
        self.move(x, y)
        
        # 设置鼠标跟踪，支持拖动
        self.setMouseTracking(True)
        self.title_bar.setMouseTracking(True)
    
    def adjust_window_size(self):
        """调整窗口大小"""
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        
        if self.width_mode == 'adaptive':
            # 自适应宽度：根据内容调整
            base_width = self.min_width
            
            if len(self.translation_history) > 0:
                # 根据内容长度调整宽度
                avg_length = sum(len(item.source_text) for item in self.translation_history[-5:]) / 5
                if avg_length > 200:
                    base_width = min(self.max_width, int(base_width * 1.5))
                elif avg_length > 100:
                    base_width = min(self.max_width, int(base_width * 1.2))
            
            width = base_width
        else:
            # 固定宽度
            width = self.min_width
        
        # 高度：屏幕高度的70%
        height = int(screen.height() * 0.7)
        
        self.resize(width, height)
    
    def apply_theme(self):
        """应用主题"""
        if self.theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QWidget#titleBar {
                    background-color: #3c3c3c;
                    border-bottom: 1px solid #555555;
                }
                QWidget#contentWidget {
                    background-color: #323232;
                }
                QLabel {
                    color: #ffffff;
                }
                QLineEdit, QComboBox, QPushButton {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #323232;
                }
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    padding: 5px 10px;
                }
                QTabBar::tab:selected {
                    background-color: #505050;
                }
                QScrollArea {
                    border: none;
                    background-color: #323232;
                }
            """)
        else:
            # 浅色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                }
                QWidget#titleBar {
                    background-color: #f0f0f0;
                    border-bottom: 1px solid #cccccc;
                }
                QWidget#contentWidget {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #333333;
                }
                QLineEdit, QComboBox, QPushButton {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: #333333;
                    padding: 5px 10px;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                }
                QScrollArea {
                    border: none;
                    background-color: #ffffff;
                }
            """)
    
    def add_translation(self, result: TranslationResult):
        """添加翻译结果"""
        # 添加到历史
        self.translation_history.append(result)
        
        # 限制历史记录数量
        if len(self.translation_history) > self.max_history_items:
            self.translation_history = self.translation_history[-self.max_history_items:]
        
        # 创建并添加部件
        item_widget = TranslationItemWidget(result)
        self.scroll_layout.addWidget(item_widget)
        
        # 更新状态
        self.status_label.setText(f"已添加翻译 ({len(self.translation_history)} 条)")
        
        # 自动滚动到底部
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 根据内容调整窗口大小
        self.adjust_window_size_if_needed(result)
    
    def adjust_window_size_if_needed(self, result: TranslationResult):
        """根据内容调整窗口大小"""
        if self.width_mode == 'adaptive':
            # 检查文本长度
            text_length = len(result.source_text)
            
            if text_length > 300 and self.width() < self.max_width:
                # 长文本，增加宽度
                new_width = min(self.width() + 50, self.max_width)
                self.resize(new_width, self.height())
            elif text_length < 100 and self.width() > self.min_width + 100:
                # 短文本，减小宽度
                new_width = max(self.width() - 30, self.min_width)
                self.resize(new_width, self.height())
    
    def clear_history(self):
        """清空历史记录"""
        # 移除所有部件
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 清空历史列表
        self.translation_history.clear()
        
        # 更新状态
        self.status_label.setText("历史记录已清空")
        
        # 恢复默认大小
        self.resize(self.min_width, self.height())
    
    def filter_history(self, search_text: str):
        """过滤历史记录"""
        search_text = search_text.lower()
        
        # 遍历所有项目，显示/隐藏匹配的项目
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                widget = item.widget()
                if isinstance(widget, TranslationItemWidget):
                    source_text = widget.result.source_text.lower()
                    trans_text = widget.result.translated_text.lower()
                    
                    # 检查是否匹配
                    if search_text in source_text or search_text in trans_text:
                        widget.show()
                    else:
                        widget.hide()
        
        self.status_label.setText(f"搜索: {search_text}")
    
    def export_history(self):
        """导出历史记录"""
        # 这里可以实现导出功能
        # 例如：导出为文本文件、JSON等
        self.status_label.setText("导出功能开发中...")
    
    def change_layout_mode(self, mode_name: str):
        """更改布局模式"""
        mode_map = {
            "紧凑模式": "compact",
            "平衡模式": "balanced", 
            "扩展模式": "expanded",
            "双栏模式": "dual"
        }
        
        if mode_name in mode_map:
            self.current_layout = mode_map[mode_name]
            self.apply_layout_mode()
    
    def apply_layout_mode(self):
        """应用布局模式"""
        # 更新所有翻译项的样式
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), TranslationItemWidget):
                widget = item.widget()
                
                if self.current_layout == 'compact':
                    widget.setMaximumHeight(150)
                    widget.source_text.setMaximumHeight(40)
                    widget.trans_text.setMaximumHeight(60)
                elif self.current_layout == 'balanced':
                    widget.setMaximumHeight(200)
                    widget.source_text.setMaximumHeight(60)
                    widget.trans_text.setMaximumHeight(80)
                elif self.current_layout == 'expanded':
                    widget.setMaximumHeight(300)
                    widget.source_text.setMaximumHeight(80)
                    widget.trans_text.setMaximumHeight(120)
                else:  # dual
                    # 双栏模式需要更复杂的布局
                    pass
        
        self.status_label.setText(f"布局模式: {self.current_layout}")
    
    # 鼠标事件支持拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """双击标题栏切换最大化/正常状态"""
        if event.button() == Qt.LeftButton:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
            event.accept()

# 全局QApplication引用
import sys
from PyQt5.QtWidgets import QApplication

# 测试函数
def test_sidebar():
    """测试侧边栏"""
    app = QApplication(sys.argv)
    
    config = {
        'display': {
            'width': 'adaptive',
            'max_width': 800,
            'min_width': 400,
            'font_size': 12,
            'theme': 'dark'
        }
    }
    
    sidebar = SmartSidebar(config)
    
    # 添加测试数据
    test_results = [
        TranslationResult(
            translated_text="这是一个测试翻译",
            source_text="This is a test translation",
            source_lang="en",
            target_lang="zh",
            confidence=0.95,
            model="test",
            response_time=150.0
        ),
        TranslationResult(
            translated_text="你好，世界！",
            source_text="Hello, World!",
            source_lang="en", 
            target_lang="zh",
            confidence=0.98,
            model="test",
            response_time=120.0
        )
    ]
    
    for result in test_results:
        sidebar.add_translation(result)
    
    sidebar.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_sidebar()