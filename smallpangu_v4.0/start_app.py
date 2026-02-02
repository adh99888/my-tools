#!/usr/bin/env python3
"""
小盘古4.0 应用启动脚本
简单启动应用并测试核心功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """主函数"""
    print("=" * 60)
    print("小盘古 4.0 - 启动测试")
    print("=" * 60)
    
    try:
        # 导入应用
        from smallpangu.app import run_app
        
        # 简单测试配置
        config_path = None
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        
        print(f"配置路径: {config_path or '默认'}")
        
        # 运行应用（使用上下文管理器确保正确清理）
        with open("test_output.log", "w", encoding="utf-8") as f:
            import contextlib
            import io
            
            # 捕获输出
            captured_output = io.StringIO()
            
            with contextlib.redirect_stdout(captured_output), \
                 contextlib.redirect_stderr(captured_output):
                
                # 创建应用
                from smallpangu.app import create_app
                app = create_app(config_path)
                
                try:
                    # 初始化应用
                    print("正在初始化应用...")
                    app.initialize()
                    print("应用初始化成功")
                    
                    # 启动应用
                    print("正在启动应用...")
                    app.start()
                    print("应用启动成功")
                    
                    # 显示应用状态
                    status = app.get_status()
                    print(f"应用状态:")
                    print(f"  初始化: {status['initialized']}")
                    print(f"  运行中: {status['running']}")
                    print(f"  环境: {status.get('config', {}).get('environment', '未知')}")
                    print(f"  插件总数: {status.get('plugins', {}).get('total', 0)}")
                    
                    # 运行一小段时间
                    import time
                    print("应用将运行5秒...")
                    time.sleep(5)
                    
                    # 停止应用
                    print("正在停止应用...")
                    app.stop()
                    print("应用停止成功")
                    
                except KeyboardInterrupt:
                    print("\n收到中断信号，正在停止应用...")
                    app.stop()
                except Exception as e:
                    print(f"应用运行异常: {e}")
                    import traceback
                    traceback.print_exc()
                    return 1
                finally:
                    app.shutdown()
                
                # 保存输出
                f.write(captured_output.getvalue())
        
        print("\n" + "=" * 60)
        print("应用启动测试完成!")
        print("详细信息已保存到 test_output.log")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())