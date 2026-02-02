"""
主窗口
整合所有功能，提供用户界面
"""

import sys
import time
import threading
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QSplitter, QScrollArea, QFrame, QSizePolicy, 
                             QDesktopWidget, QSystemTrayIcon, QMenu, QAction,
                             QMessageBox, QComboBox, QSpinBox, QCheckBox)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot, QObject, Qt
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

from engines.capture.smart_capture import SmartCapture, CaptureRegion
from engines.ocr.hybrid_ocr import HybridOCREngine, TextBlock
from engines.translation.model_router import ModelRouter, TranslationRequest, TranslationResult
from .smart_sidebar import SmartSidebar
from utils.windows_tools import WindowsHotkey

class CaptureWorker(QThread):
    """捕获工作线程"""
    capture_completed = pyqtSignal(object)  # 发送捕获的图像
    error_occurred = pyqtSignal(str)  # 发送错误信息
    
    def __init__(self, capture_engine, interval=3.0):
        super().__init__()
        self.capture_engine = capture_engine
        self.interval = interval
        self.running = False
        self.paused = False
    
    def run(self):
        """线程主循环"""
        self.running = True
        
        while self.running:
            if not self.paused:
                try:
                    # 捕获屏幕
                    image = self.capture_engine.capture()
                    if image is not None:
                        self.capture_completed.emit(image)
                    
                    # 等待间隔
                    self.msleep(int(self.interval * 1000))
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    self.msleep(1000)
            else:
                self.msleep(500)
    
    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()
    
    def pause(self):
        """暂停捕获"""
        self.paused = True
    
    def resume(self):
        """恢复捕获"""
        self.paused = False
    
    def update_interval(self, interval):
        """更新捕获间隔"""
        self.interval = interval

class ProcessingWorker(QThread):
    """处理工作线程（OCR + 翻译）"""
    processing_completed = pyqtSignal(object)  # 发送翻译结果
    status_updated = pyqtSignal(str)  # 发送状态更新
    
    def __init__(self, ocr_engine, translation_router):
        super().__init__()
        self.ocr_engine = ocr_engine
        self.translation_router = translation_router
        self.running = False
        self.paused = False
        self.queue = []  # 图像队列
    
    def run(self):
        """线程主循环"""
        self.running = True
        
        while self.running:
            if not self.paused and self.queue:
                try:
                    # 获取下一个图像
                    image = self.queue.pop(0)
                    
                    # OCR识别
                    self.status_updated.emit("正在识别文本...")
                    text_blocks = self.ocr_engine.recognize(image)
                    
                    if text_blocks:
                        # 合并文本块
                        full_text = self._merge_text_blocks(text_blocks)
                        
                        # 翻译
                        self.status_updated.emit("正在翻译...")
                        request = TranslationRequest(
                            text=full_text,
                            source_lang="auto",
                            target_lang="zh"
                        )
                        result = self.translation_router.translate(request)
                        
                        # 发送结果
                        self.processing_completed.emit(result)
                        self.status_updated.emit("翻译完成")
                    else:
                        self.status_updated.emit("未识别到文本")
                        
                except Exception as e:
                    self.status_updated.emit(f"处理失败: {str(e)[:50]}")
                    print(f"处理失败: {e}")
            
            # 短暂休眠，避免CPU占用过高
            self.msleep(100)
    
    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()
    
    def add_image(self, image):
        """添加图像到处理队列"""
        self.queue.append(image)
    
    def clear_queue(self):
        """清空队列"""
        self.queue.clear()
    
    def _merge_text_blocks(self, text_blocks):
        """合并文本块"""
        # 按y坐标排序（从上到下）
        sorted_blocks = sorted(text_blocks, key=lambda tb: tb.bbox[1])
        
        # 合并文本
        lines = []
        current_line = ""
        current_y = -1
        line_height = 20  # 估计的行高
        
        for block in sorted_blocks:
            if current_y == -1:
                current_y = block.bbox[1]
                current_line = block.text
            elif abs(block.bbox[1] - current_y) < line_height:
                # 同一行
                current_line += " " + block.text
            else:
                # 新行
                lines.append(current_line)
                current_line = block.text
                current_y = block.bbox[1]
        
        if current_line:
            lines.append(current_line)
        
        return "\n".join(lines)

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, config: Dict[str, Any], modules: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.modules = modules
        
        # 初始化变量
        self.capture_engine = modules.get('capture')
        self.ocr_engine = modules.get('ocr')
        self.translation_router = modules.get('translation')
        
        self.capture_worker = None
        self.processing_worker = None
        
        self.sidebar = None
        
        # 系统托盘
        self.tray_icon = None
        
        # 热键管理器
        self.hotkey_manager = None
        
        # 初始化UI
        self.init_ui()
        
        # 初始化工作线程
        self.init_workers()
        
        # 初始化系统托盘
        self.init_system_tray()
        
        # 初始化热键
        self.init_hotkeys()
        
        # 应用样式
        self.apply_theme()
    
    def init_ui(self):
        """初始化用户界面"""
        # 窗口设置
        self.setWindowTitle("屏幕翻译助手增强版")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 标题栏
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        
        title_label = QLabel("🖥️ 屏幕翻译助手增强版")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 控制按钮
        btn_minimize = QPushButton("－")
        btn_minimize.setFixedSize(25, 25)
        btn_minimize.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("×")
        btn_close.setFixedSize(25, 25)
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(btn_minimize)
        title_layout.addWidget(btn_close)
        
        main_layout.addWidget(title_bar)
        
        # 状态面板
        status_panel = QWidget()
        status_layout = QHBoxLayout(status_panel)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        status_layout.addWidget(self.status_label)
        
        self.capture_status = QLabel("捕获: 停止")
        self.capture_status.setStyleSheet("color: #999; padding: 5px;")
        status_layout.addWidget(self.capture_status)
        
        self.translation_status = QLabel("翻译: 空闲")
        self.translation_status.setStyleSheet("color: #999; padding: 5px;")
        status_layout.addWidget(self.translation_status)
        
        status_layout.addStretch()
        
        main_layout.addWidget(status_panel)
        
        # 控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # 捕获控制
        capture_group = QWidget()
        capture_layout = QVBoxLayout(capture_group)
        
        capture_label = QLabel("屏幕捕获")
        capture_label.setStyleSheet("font-weight: bold;")
        capture_layout.addWidget(capture_label)
        
        capture_btn_layout = QHBoxLayout()
        
        self.btn_start_capture = QPushButton("开始捕获")
        self.btn_start_capture.clicked.connect(self.start_capture)
        capture_btn_layout.addWidget(self.btn_start_capture)
        
        self.btn_stop_capture = QPushButton("停止捕获")
        self.btn_stop_capture.clicked.connect(self.stop_capture)
        self.btn_stop_capture.setEnabled(False)
        capture_btn_layout.addWidget(self.btn_stop_capture)
        
        self.btn_single_capture = QPushButton("单次捕获")
        self.btn_single_capture.clicked.connect(self.single_capture)
        capture_btn_layout.addWidget(self.btn_single_capture)
        
        capture_layout.addLayout(capture_btn_layout)
        
        # 捕获间隔设置
        interval_layout = QHBoxLayout()
        interval_label = QLabel("间隔(秒):")
        interval_layout.addWidget(interval_label)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 30)
        self.interval_spin.setValue(int(self.config.get('capture', {}).get('interval', 3)))
        self.interval_spin.valueChanged.connect(self.update_capture_interval)
        interval_layout.addWidget(self.interval_spin)
        
        capture_layout.addLayout(interval_layout)
        
        control_layout.addWidget(capture_group)
        
        # OCR设置
        ocr_group = QWidget()
        ocr_layout = QVBoxLayout(ocr_group)
        
        ocr_label = QLabel("OCR设置")
        ocr_label.setStyleSheet("font-weight: bold;")
        ocr_layout.addWidget(ocr_label)
        
        self.ocr_engine_combo = QComboBox()
        self.ocr_engine_combo.addItems(["混合引擎", "Tesseract", "EasyOCR"])
        self.ocr_engine_combo.currentTextChanged.connect(self.change_ocr_engine)
        ocr_layout.addWidget(self.ocr_engine_combo)
        
        self.preprocess_check = QCheckBox("图像预处理")
        self.preprocess_check.setChecked(self.config.get('ocr', {}).get('preprocess', True))
        self.preprocess_check.stateChanged.connect(self.toggle_preprocess)
        ocr_layout.addWidget(self.preprocess_check)
        
        control_layout.addWidget(ocr_group)
        
        # 翻译设置
        translation_group = QWidget()
        translation_layout = QVBoxLayout(translation_group)
        
        translation_label = QLabel("翻译设置")
        translation_label.setStyleSheet("font-weight: bold;")
        translation_layout.addWidget(translation_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Kimi", "DeepSeek", "通义千问", "硅基流动", "智谱GLM"])
        self.model_combo.currentTextChanged.connect(self.change_translation_model)
        translation_layout.addWidget(self.model_combo)
        
        control_layout.addWidget(translation_group)
        
        # 显示控制
        display_group = QWidget()
        display_layout = QVBoxLayout(display_group)
        
        display_label = QLabel("显示设置")
        display_label.setStyleSheet("font-weight: bold;")
        display_layout.addWidget(display_label)
        
        self.btn_toggle_sidebar = QPushButton("显示侧边栏")
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        display_layout.addWidget(self.btn_toggle_sidebar)
        
        self.btn_clear_history = QPushButton("清空历史")
        self.btn_clear_history.clicked.connect(self.clear_history)
        display_layout.addWidget(self.btn_clear_history)
        
        control_layout.addWidget(display_group)
        
        main_layout.addWidget(control_panel)
        
        # 日志区域
        log_group = QWidget()
        log_layout = QVBoxLayout(log_group)
        
        log_label = QLabel("操作日志")
        log_label.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 5px;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # 底部状态栏
        self.statusBar().showMessage("就绪")
    
    def init_workers(self):
        """初始化工作线程"""
        # 捕获线程
        capture_interval = self.config.get('capture', {}).get('interval', 3.0)
        self.capture_worker = CaptureWorker(self.capture_engine, capture_interval)
        self.capture_worker.capture_completed.connect(self.on_capture_completed)
        self.capture_worker.error_occurred.connect(self.on_capture_error)
        
        # 处理线程
        self.processing_worker = ProcessingWorker(self.ocr_engine, self.translation_router)
        self.processing_worker.processing_completed.connect(self.on_translation_completed)
        self.processing_worker.status_updated.connect(self.update_status)
        self.processing_worker.start()  # 启动处理线程
    
    def init_system_tray(self):
        """初始化系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            show_action = QAction("显示主窗口", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("隐藏主窗口", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            capture_action = QAction("开始捕获", self)
            capture_action.triggered.connect(self.start_capture)
            tray_menu.addAction(capture_action)
            
            stop_action = QAction("停止捕获", self)
            stop_action.triggered.connect(self.stop_capture)
            tray_menu.addAction(stop_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # 设置托盘图标
            icon = QIcon()
            # 可以使用默认图标或自定义图标
            self.tray_icon.setIcon(icon)
            
            self.tray_icon.show()
    
    def init_hotkeys(self):
        """初始化热键"""
        import traceback
        print(f"[DEBUG] init_hotkeys called, hotkey_manager={self.hotkey_manager}")
        # 打印调用栈以调试重复调用问题
        stack = traceback.extract_stack()
        print(f"[DEBUG] Call stack (last 3):")
        for frame in stack[-4:-1]:
            print(f"  {frame.filename}:{frame.lineno} in {frame.name}")
        try:
            if self.hotkey_manager is not None:
                print("[WARN] hotkey_manager already exists, 跳过重复初始化")
                return
            self.hotkey_manager = WindowsHotkey()
            
            # 从配置获取热键设置
            shortcuts = self.config.get('shortcuts', {})
            capture_hotkey = shortcuts.get('capture', 'ctrl+shift+t')
            toggle_sidebar_hotkey = shortcuts.get('toggle_sidebar', 'alt+t')
            
            # 注册捕获热键
            if not self.hotkey_manager.register_hotkey(capture_hotkey, self.hotkey_capture):
                print(f"热键注册失败: {capture_hotkey}")
            
            # 注册侧边栏切换热键
            if not self.hotkey_manager.register_hotkey(toggle_sidebar_hotkey, self.hotkey_toggle_sidebar):
                print(f"热键注册失败: {toggle_sidebar_hotkey}")
                
        except Exception as e:
            print(f"热键初始化失败: {e}")
            self.hotkey_manager = None
    
    def hotkey_capture(self):
        """热键捕获回调"""
        # 在主线程中执行捕获
        self.single_capture()
    
    def hotkey_toggle_sidebar(self):
        """热键切换侧边栏回调"""
        # 在主线程中切换侧边栏
        self.toggle_sidebar()
    
    def apply_theme(self):
        """应用主题"""
        theme = self.config.get('app', {}).get('theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
                QComboBox, QSpinBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 3px;
                }
                QCheckBox {
                    color: #ffffff;
                }
            """)
        else:
            # 浅色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QPushButton {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
    
    def log_message(self, message: str):
        """记录日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 限制日志行数
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > 100:
            self.log_text.setPlainText('\n'.join(lines[-100:]))
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, status: str):
        """更新状态"""
        self.status_label.setText(status)
        self.statusBar().showMessage(status)
        self.log_message(status)
    
    @pyqtSlot(object)
    def on_capture_completed(self, image):
        """捕获完成回调"""
        self.capture_status.setText("捕获: 成功")
        
        # 记录图像信息
        if image is not None:
            height, width = image.shape[:2]
            self.log_message(f"捕获成功: 图像尺寸 {width}x{height}")
        
        # 添加到处理队列
        if self.processing_worker:
            self.processing_worker.add_image(image)
            self.translation_status.setText("翻译: 队列中")
    
    @pyqtSlot(str)
    def on_capture_error(self, error_msg: str):
        """捕获错误回调"""
        self.capture_status.setText("捕获: 错误")
        self.log_message(f"捕获错误: {error_msg}")
    
    @pyqtSlot(object)
    def on_translation_completed(self, result: TranslationResult):
        """翻译完成回调"""
        self.translation_status.setText("翻译: 完成")
        
        # 显示结果
        self.show_translation_result(result)
        
        # 记录日志
        self.log_message(f"翻译完成: {result.source_text[:50]}... -> {result.translated_text[:50]}...")
    
    def show_translation_result(self, result: TranslationResult):
        """显示翻译结果"""
        if self.sidebar is None:
            # 创建侧边栏
            self.sidebar = SmartSidebar(self.config)
            self.sidebar.show()
            self.btn_toggle_sidebar.setText("隐藏侧边栏")
        
        # 添加到侧边栏
        self.sidebar.add_translation(result)
    
    def start_capture(self):
        """开始捕获"""
        if self.capture_worker and not self.capture_worker.isRunning():
            self.capture_worker.start()
            self.btn_start_capture.setEnabled(False)
            self.btn_stop_capture.setEnabled(True)
            self.capture_status.setText("捕获: 运行中")
            self.update_status("开始屏幕捕获")
    
    def stop_capture(self):
        """停止捕获"""
        if self.capture_worker and self.capture_worker.isRunning():
            self.capture_worker.stop()
            self.btn_start_capture.setEnabled(True)
            self.btn_stop_capture.setEnabled(False)
            self.capture_status.setText("捕获: 停止")
            self.update_status("停止屏幕捕获")
    
    def single_capture(self):
        """单次捕获"""
        self.update_status("执行单次捕获")
        
        if self.capture_engine:
            # 尝试导入pyautogui获取屏幕尺寸
            try:
                import pyautogui
                screen_width, screen_height = pyautogui.size()
                
                # 使用屏幕中间80%的区域（避免边缘干扰）
                margin_x = int(screen_width * 0.1)
                margin_y = int(screen_height * 0.1)
                capture_width = screen_width - 2 * margin_x
                capture_height = screen_height - 2 * margin_y
                
                from engines.capture.smart_capture import CaptureRegion
                fullscreen_region = CaptureRegion(
                    x=margin_x, y=margin_y, 
                    width=capture_width, height=capture_height
                )
                
                # 强制捕获指定区域
                self.log_message(f"开始捕获，区域: ({margin_x},{margin_y}) {capture_width}x{capture_height}")
                image = self.capture_engine.capture(region=fullscreen_region, force=True)
                self.log_message(f"捕获区域: ({margin_x},{margin_y}) {capture_width}x{capture_height}")
                
            except Exception as e:
                # 如果获取屏幕尺寸失败，使用默认捕获
                self.log_message(f"获取屏幕尺寸失败: {e}，使用默认区域")
                image = self.capture_engine.capture(force=True)
            
            if image is not None:
                height, width = image.shape[:2]
                self.log_message(f"捕获成功，图像尺寸: {width}x{height}")
                self.on_capture_completed(image)
            else:
                self.update_status("捕获失败")
                self.log_message("捕获失败：未能获取屏幕图像，可能原因: 1) 变化检测阻止 2) 区域无效 3) 权限问题")
        else:
            self.update_status("捕获引擎未初始化")
            self.log_message("错误: 捕获引擎未初始化")
    
    def update_capture_interval(self, interval: int):
        """更新捕获间隔"""
        if self.capture_worker:
            self.capture_worker.update_interval(float(interval))
            self.update_status(f"捕获间隔更新为 {interval} 秒")
    
    def change_ocr_engine(self, engine_name: str):
        """更改OCR引擎"""
        engine_map = {
            "混合引擎": "hybrid",
            "Tesseract": "tesseract",
            "EasyOCR": "easyocr"
        }
        
        if engine_name in engine_map:
            new_config = {'primary': engine_map[engine_name]}
            self.ocr_engine.update_config(new_config)
            self.update_status(f"OCR引擎切换为 {engine_name}")
    
    def toggle_preprocess(self, state: int):
        """切换图像预处理"""
        enabled = state == Qt.Checked
        new_config = {'preprocess': enabled}
        self.ocr_engine.update_config(new_config)
        status = "启用" if enabled else "禁用"
        self.update_status(f"图像预处理{status}")
    
    def change_translation_model(self, model_name: str):
        """更改翻译模型"""
        model_map = {
            "Kimi": "kimi",
            "DeepSeek": "deepseek",
            "通义千问": "qwen",
            "硅基流动": "siliconflow",
            "智谱GLM": "glm"
        }
        
        if model_name in model_map:
            new_config = {'primary': model_map[model_name]}
            self.translation_router.update_config(new_config)
            self.update_status(f"翻译模型切换为 {model_name}")
    
    def toggle_sidebar(self):
        """切换侧边栏显示"""
        if self.sidebar is None:
            self.sidebar = SmartSidebar(self.config)
            self.sidebar.show()
            self.btn_toggle_sidebar.setText("隐藏侧边栏")
            self.update_status("显示侧边栏")
        else:
            if self.sidebar.isVisible():
                self.sidebar.hide()
                self.btn_toggle_sidebar.setText("显示侧边栏")
                self.update_status("隐藏侧边栏")
            else:
                self.sidebar.show()
                self.btn_toggle_sidebar.setText("隐藏侧边栏")
                self.update_status("显示侧边栏")
    
    def clear_history(self):
        """清空翻译历史"""
        if self.sidebar:
            self.sidebar.clear_history()
            self.update_status("已清空翻译历史")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止工作线程
        if self.capture_worker:
            self.capture_worker.stop()
        
        if self.processing_worker:
            self.processing_worker.stop()
        
        # 清理热键
        if self.hotkey_manager:
            self.hotkey_manager.unregister_all()
            self.hotkey_manager = None
        
        # 关闭侧边栏
        if self.sidebar:
            self.sidebar.close()
        
        # 确认退出
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出屏幕翻译助手吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 测试函数
def test_main_window():
    """测试主窗口"""
    app = QApplication(sys.argv)
    
    # 模拟配置和模块
    config = {
        'app': {'theme': 'dark'},
        'capture': {'interval': 3},
        'ocr': {'preprocess': True}
    }
    
    modules = {
        'capture': None,
        'ocr': None,
        'translation': None
    }
    
    window = MainWindow(config, modules)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_main_window()