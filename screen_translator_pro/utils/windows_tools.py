"""
Windows专用工具模块
提供Windows特有的功能优化
"""

import os
import sys
import ctypes
from typing import Optional, Tuple, List, Dict
from ctypes import wintypes

# Windows API imports with fallbacks
try:
    import win32api
    import win32con
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    # 创建虚拟模块避免NameError
    class DummyWin32Module:
        def __getattr__(self, name):
            raise ImportError("pywin32未安装，Windows API功能不可用")
    
    win32api = DummyWin32Module()
    win32con = DummyWin32Module()
    win32gui = DummyWin32Module()
    win32process = DummyWin32Module()

class WindowsCapture:
    """Windows专用屏幕捕获（比pyautogui更高效）"""
    
    @staticmethod
    def get_screen_resolution() -> Tuple[int, int]:
        """获取屏幕分辨率"""
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    
    @staticmethod
    def get_active_window_rect() -> Optional[Tuple[int, int, int, int]]:
        """获取活动窗口的位置和大小"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                return rect  # (left, top, right, bottom)
        except:
            pass
        return None
    
    @staticmethod
    def get_window_title(hwnd: int) -> str:
        """获取窗口标题"""
        try:
            return win32gui.GetWindowText(hwnd)
        except:
            return ""
    
    @staticmethod
    def get_process_name(hwnd: int) -> str:
        """获取窗口对应的进程名"""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            exe_path = win32process.GetModuleFileNameEx(handle, 0)
            return os.path.basename(exe_path)
        except:
            return ""
    
    @staticmethod
    def is_terminal_window(hwnd: int) -> bool:
        """判断是否是终端窗口"""
        title = WindowsCapture.get_window_title(hwnd).lower()
        process = WindowsCapture.get_process_name(hwnd).lower()
        
        terminal_indicators = [
            'cmd.exe', 'powershell.exe', 'windows terminal', 
            'wt.exe', 'conhost.exe', 'mintty', 'cygwin'
        ]
        
        return any(indicator in process for indicator in terminal_indicators) or 'cmd' in title
    
    @staticmethod
    def is_browser_window(hwnd: int) -> bool:
        """判断是否是浏览器窗口"""
        process = WindowsCapture.get_process_name(hwnd).lower()
        
        browser_indicators = [
            'chrome.exe', 'firefox.exe', 'edge.exe', 'msedge.exe',
            'opera.exe', 'brave.exe', 'vivaldi.exe'
        ]
        
        return any(indicator in process for indicator in browser_indicators)
    
    @staticmethod
    def is_code_editor_window(hwnd: int) -> bool:
        """判断是否是代码编辑器窗口"""
        process = WindowsCapture.get_process_name(hwnd).lower()
        
        editor_indicators = [
            'code.exe', 'pycharm.exe', 'idea.exe', 'webstorm.exe',
            'sublime_text.exe', 'notepad++.exe', 'vim.exe', 'neovim.exe'
        ]
        
        return any(indicator in process for indicator in editor_indicators)

class WindowsHotkey:
    """Windows全局热键管理"""
    
    def __init__(self):
        self.hotkeys = {}
        self.next_id = 1
    
    def register_hotkey(self, key_combination: str, callback) -> bool:
        """注册全局热键"""
        try:
            import keyboard
            
            # 解析按键组合（如 "ctrl+shift+t"）
            keyboard.add_hotkey(key_combination, callback)
            
            hotkey_id = self.next_id
            self.hotkeys[hotkey_id] = {
                'combination': key_combination,
                'callback': callback
            }
            self.next_id += 1
            
            print(f"热键注册成功: {key_combination}")
            return True
            
        except ImportError:
            print("keyboard模块未安装，请运行: pip install keyboard")
            return False
        except Exception as e:
            print(f"热键注册失败: {e}")
            return False
    
    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """取消注册热键"""
        if hotkey_id in self.hotkeys:
            try:
                import keyboard
                keyboard.remove_hotkey(hotkey_id)
                del self.hotkeys[hotkey_id]
                return True
            except:
                pass
        return False
    
    def unregister_all(self):
        """取消所有热键"""
        for hotkey_id in list(self.hotkeys.keys()):
            self.unregister_hotkey(hotkey_id)

class WindowsTTS:
    """Windows文本转语音（使用系统TTS）"""
    
    def __init__(self):
        try:
            import comtypes.client
            self.speaker = comtypes.client.CreateObject("SAPI.SpVoice")
            self.available = True
        except:
            self.speaker = None
            self.available = False
            print("Windows TTS初始化失败")
    
    def speak(self, text: str, rate: int = 0):
        """朗读文本"""
        if not self.available or not self.speaker:
            return False
        
        try:
            # 设置语速 (-10 到 10)
            self.speaker.Rate = rate
            
            # 异步朗读
            self.speaker.Speak(text, 1)  # 1表示异步
            
            return True
        except Exception as e:
            print(f"TTS朗读失败: {e}")
            return False
    
    def stop(self):
        """停止朗读"""
        if self.available and self.speaker:
            try:
                self.speaker.Speak("", 3)  # 3表示停止所有
            except:
                pass

class WindowsUI:
    """Windows UI相关工具"""
    
    @staticmethod
    def set_window_on_top(hwnd: int, on_top: bool = True):
        """设置窗口置顶"""
        try:
            if on_top:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                     win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass
    
    @staticmethod
    def set_window_transparency(hwnd: int, opacity: float):
        """设置窗口透明度（0.0-1.0）"""
        try:
            # 转换为0-255的范围
            alpha = int(opacity * 255)
            
            # 设置窗口扩展样式
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style |= win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
            
            # 设置透明度
            win32gui.SetLayeredWindowAttributes(hwnd, 0, alpha, win32con.LWA_ALPHA)
        except:
            pass
    
    @staticmethod
    def flash_window(hwnd: int, count: int = 3, interval: int = 500):
        """闪烁窗口（吸引注意力）"""
        try:
            for _ in range(count):
                win32gui.FlashWindow(hwnd, True)
                import time
                time.sleep(interval / 1000.0)
        except:
            pass

class WindowsMonitor:
    """Windows系统监控"""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            print("psutil未安装，请运行: pip install psutil")
            return 0.0
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total / (1024 ** 3),  # GB
                'used': memory.used / (1024 ** 3),
                'percent': memory.percent
            }
        except ImportError:
            return {'total': 0, 'used': 0, 'percent': 0}
    
    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """获取磁盘使用情况"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total / (1024 ** 3),  # GB
                'used': disk.used / (1024 ** 3),
                'percent': disk.percent
            }
        except ImportError:
            return {'total': 0, 'used': 0, 'percent': 0}

class WindowsTools:
    """Windows工具集（外观模式，统一接口）"""
    
    @staticmethod
    def get_screen_resolution() -> Tuple[int, int]:
        """获取屏幕分辨率"""
        return WindowsCapture.get_screen_resolution()
    
    @staticmethod
    def get_active_window_rect() -> Optional[Tuple[int, int, int, int]]:
        """获取活动窗口位置和大小"""
        return WindowsCapture.get_active_window_rect()
    
    @staticmethod
    def set_window_on_top(hwnd: int, on_top: bool = True):
        """设置窗口置顶"""
        WindowsUI.set_window_on_top(hwnd, on_top)
    
    @staticmethod
    def speak_text(text: str, rate: int = 200, volume: float = 1.0):
        """语音朗读文本"""
        # WindowsTTS有speak方法，没有speak_text
        WindowsTTS.speak(text, rate, volume)
    
    @staticmethod
    def register_hotkey(hotkey: str, callback) -> bool:
        """注册全局热键"""
        hotkey_mgr = WindowsHotkey()
        return hotkey_mgr.register_hotkey(hotkey, callback)
    
    @staticmethod
    def unregister_hotkey(hotkey: str):
        """取消注册全局热键"""
        hotkey_mgr = WindowsHotkey()
        hotkey_mgr.unregister_hotkey(hotkey)
    
    @staticmethod
    def get_system_metrics() -> Dict[str, float]:
        """获取系统指标（CPU、内存、磁盘）"""
        return {
            'cpu': WindowsMonitor.get_cpu_usage(),
            'memory': WindowsMonitor.get_memory_usage(),
            'disk': WindowsMonitor.get_disk_usage()
        }


# 测试函数
def test_windows_tools():
    """测试Windows工具"""
    print("测试Windows工具...")
    
    # 测试屏幕分辨率
    width, height = WindowsCapture.get_screen_resolution()
    print(f"屏幕分辨率: {width}x{height}")
    
    # 测试活动窗口
    rect = WindowsCapture.get_active_window_rect()
    if rect:
        print(f"活动窗口位置: {rect}")
    
    # 测试热键（需要keyboard模块）
    hotkey_manager = WindowsHotkey()
    
    def test_callback():
        print("热键触发!")
    
    # 注册测试热键（注释掉，避免实际注册）
    # hotkey_manager.register("ctrl+shift+t", test_callback)
    # print("热键注册完成，按Ctrl+Shift+T测试")
    # print("按Ctrl+C退出")
    # 
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("\n测试结束")
    
    print("测试完成（部分功能需要实际运行）")

if __name__ == "__main__":
    test_windows_tools()