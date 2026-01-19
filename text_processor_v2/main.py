#!/usr/bin/env python3
"""
AI文档智能排版系统 v2.0 - 主入口点
模块化重构版本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_application():
    """创建应用程序实例"""
    try:
        # 导入模块
        from config import get_config_manager
        from core.model_manager import ModelManager
        from core.template_manager import TemplateManager
        from core.api_client import APIClient
        from core.document_processor import DocumentProcessor
        
        print("🚀 正在初始化应用程序...")
        
        # 初始化配置管理器
        config_manager = get_config_manager()
        print(f"✅ 配置管理器: 加载了 {len(config_manager.model_configs)} 个模型, {len(config_manager.templates)} 个模板")
        
        # 初始化模型管理器
        model_manager = ModelManager(config_manager)
        print(f"✅ 模型管理器: 当前模型 '{model_manager.current_model_id}'")
        
        # 初始化模板管理器
        template_manager = TemplateManager(config_manager)
        print(f"✅ 模板管理器: 当前模板 '{template_manager.current_template}'")
        
        # 初始化API客户端
        api_client = APIClient(config_manager, model_manager)
        print("✅ API客户端: 初始化成功")
        
        # 初始化文档处理器
        doc_processor = DocumentProcessor(config_manager, model_manager, template_manager, api_client)
        print("✅ 文档处理器: 初始化成功")
        
        return {
            'config_manager': config_manager,
            'model_manager': model_manager,
            'template_manager': template_manager,
            'api_client': api_client,
            'doc_processor': doc_processor
        }
        
    except Exception as e:
        logger.error(f"应用程序初始化失败: {str(e)}")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("  AI文档智能排版系统 v2.0 - 模块化重构版本")
    print("=" * 60)
    
    # 创建应用程序实例
    app_components = create_application()
    if not app_components:
        print("❌ 应用程序初始化失败，程序退出")
        return 1
    
    print("\n✅ 所有核心模块初始化成功!")
    print("💡 正在启动GUI界面...")
    
    try:
        # 导入tkinter
        import tkinter as tk
        
        # 创建主窗口
        root = tk.Tk()
        
        # 设置窗口图标
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
        except:
            pass
        
        # 设置窗口最小大小
        root.minsize(1100, 800)
        
        # 创建主窗口
        from ui import MainWindow
        app = MainWindow(
            root,
            app_components['config_manager'],
            app_components['model_manager'],
            app_components['template_manager'],
            app_components['doc_processor']
        )
        
        # 绑定关闭事件
        def on_closing():
            if app.is_processing:
                import tkinter.messagebox as messagebox
                if messagebox.askyesno("确认", "正在处理中，确定要退出吗？"):
                    root.destroy()
            else:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 启动主循环
        print("✅ GUI界面启动成功!")
        print("=" * 60)
        root.mainloop()
        
        return 0
        
    except ImportError as e:
        logger.error(f"GUI模块导入失败: {str(e)}")
        print("❌ GUI模块导入失败，请确保tkinter已安装")
        print("💡 对于Windows系统，tkinter通常随Python一起安装")
        print("💡 对于Linux系统，可能需要安装: sudo apt-get install python3-tk")
        return 1
    except Exception as e:
        logger.error(f"GUI启动失败: {str(e)}")
        print(f"❌ GUI启动失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())