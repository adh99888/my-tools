"""
智能屏幕捕获模块
针对Windows环境优化，支持智能区域检测和变化跟踪
"""

import time
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
import threading
from dataclasses import dataclass

try:
    import pyautogui
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("警告: OpenCV未安装，部分功能受限")

@dataclass
class CaptureRegion:
    """捕获区域"""
    x: int
    y: int
    width: int
    height: int
    
    def to_tuple(self):
        return (self.x, self.y, self.width, self.height)
    
    def contains(self, x: int, y: int) -> bool:
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)

class SmartCapture:
    """智能屏幕捕获器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = config.get('mode', 'smart')  # smart/fixed/manual
        self.change_detection = config.get('change_detection', True)
        self.region_learning = config.get('region_learning', True)
        
        # 捕获区域
        default_region = config.get('default_region', [200, 200, 600, 400])
        self.current_region = CaptureRegion(*default_region)
        
        # 变化检测相关
        self.last_frame = None
        self.change_threshold = 0.1  # 变化阈值
        self.min_change_area = 100   # 最小变化区域面积
        
        # 区域学习相关
        self.learned_regions = []
        self.region_weights = {}  # 区域权重，使用频率高的区域权重高
        
        # 性能统计
        self.stats = {
            'total_captures': 0,
            'changed_captures': 0,
            'avg_capture_time': 0,
            'learned_regions_count': 0
        }
        
        print(f"智能捕获器初始化完成，模式: {self.mode}")
    
    def capture(self, region: Optional[CaptureRegion] = None, force: bool = False) -> Optional[np.ndarray]:
        """
        捕获屏幕图像
        
        Args:
            region: 指定捕获区域，None表示使用智能区域
            force: 强制捕获，忽略变化检测
            
        Returns:
            numpy数组表示的图像，失败返回None
        """
        start_time = time.time()
        
        try:
            # 确定捕获区域
            if region is None:
                region = self._get_optimal_region()
            
            # 捕获屏幕
            screenshot = pyautogui.screenshot(region=region.to_tuple())
            frame = np.array(screenshot)
            
            # 转换颜色空间（pyautogui返回RGB，OpenCV需要BGR）
            if len(frame.shape) == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # 变化检测（除非强制捕获）
            if self.change_detection and self.last_frame is not None and not force:
                if not self._has_significant_changes(frame):
                    # 没有显著变化，返回None
                    elapsed = time.time() - start_time
                    self._update_stats(elapsed, changed=False)
                    return None
            
            # 更新上一帧
            if self.change_detection and not force:
                self.last_frame = frame.copy()
            
            # 区域学习
            if self.region_learning:
                self._learn_region(region)
            
            # 更新统计
            elapsed = time.time() - start_time
            self._update_stats(elapsed, changed=True)
            
            return frame
            
        except Exception as e:
            print(f"屏幕捕获失败: {e}")
            return None
    
    def capture_with_mouse(self) -> Optional[np.ndarray]:
        """捕获鼠标所在区域的屏幕"""
        try:
            # 获取鼠标位置
            mouse_x, mouse_y = pyautogui.position()
            
            # 查找包含鼠标的学习区域
            for region in self.learned_regions:
                if region.contains(mouse_x, mouse_y):
                    return self.capture(region)
            
            # 如果没有学习区域，使用智能区域
            return self.capture()
            
        except Exception as e:
            print(f"鼠标区域捕获失败: {e}")
            return self.capture()
    
    def manual_select_region(self) -> Optional[CaptureRegion]:
        """手动选择区域（通过快捷键触发）"""
        try:
            print("请拖动鼠标选择捕获区域...")
            
            # 这里可以集成一个可视化区域选择工具
            # 暂时使用简单实现：返回当前区域
            return self.current_region
            
        except Exception as e:
            print(f"手动选择区域失败: {e}")
            return None
    
    def _get_optimal_region(self) -> CaptureRegion:
        """获取最优捕获区域"""
        if self.mode == 'fixed':
            return self.current_region
        
        elif self.mode == 'smart':
            # 智能模式：根据学习到的区域和当前活动窗口决定
            if self.learned_regions:
                # 使用权重最高的区域
                best_region = max(self.learned_regions, 
                                 key=lambda r: self.region_weights.get(id(r), 0))
                return best_region
            else:
                return self.current_region
        
        else:  # manual
            return self.current_region
    
    def _has_significant_changes(self, current_frame: np.ndarray) -> bool:
        """检测是否有显著变化"""
        if self.last_frame is None:
            return True
        
        try:
            # 转换为灰度图
            last_gray = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            # 计算差异
            diff = cv2.absdiff(last_gray, current_gray)
            
            # 二值化
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            
            # 计算变化面积
            change_area = np.sum(thresh > 0)
            
            # 判断是否超过阈值
            total_pixels = thresh.shape[0] * thresh.shape[1]
            change_ratio = change_area / total_pixels
            
            return change_ratio > self.change_threshold or change_area > self.min_change_area
            
        except Exception as e:
            print(f"变化检测失败: {e}")
            return True
    
    def _learn_region(self, region: CaptureRegion):
        """学习区域"""
        region_id = id(region)
        
        # 增加区域权重
        self.region_weights[region_id] = self.region_weights.get(region_id, 0) + 1
        
        # 如果是不在已学习列表中的新区域，添加到学习列表
        if region not in self.learned_regions:
            self.learned_regions.append(region)
            self.stats['learned_regions_count'] = len(self.learned_regions)
            
            # 限制学习区域数量
            if len(self.learned_regions) > 10:
                # 移除权重最低的区域
                to_remove = min(self.learned_regions, 
                               key=lambda r: self.region_weights.get(id(r), 0))
                self.learned_regions.remove(to_remove)
                del self.region_weights[id(to_remove)]
    
    def _update_stats(self, elapsed_time: float, changed: bool):
        """更新性能统计"""
        self.stats['total_captures'] += 1
        if changed:
            self.stats['changed_captures'] += 1
        
        # 更新平均捕获时间（指数移动平均）
        alpha = 0.1
        self.stats['avg_capture_time'] = (
            alpha * elapsed_time * 1000 +  # 转换为毫秒
            (1 - alpha) * self.stats['avg_capture_time']
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.stats.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        
        if 'mode' in new_config:
            self.mode = new_config['mode']
        
        if 'change_detection' in new_config:
            self.change_detection = new_config['change_detection']
        
        if 'region_learning' in new_config:
            self.region_learning = new_config['region_learning']
        
        print(f"捕获配置已更新: {new_config}")

# 快捷函数
def test_capture():
    """测试捕获功能"""
    config = {
        'mode': 'smart',
        'change_detection': True,
        'region_learning': True
    }
    
    capture = SmartCapture(config)
    
    print("测试屏幕捕获...")
    for i in range(3):
        frame = capture.capture()
        if frame is not None:
            print(f"第{i+1}次捕获: {frame.shape}")
        else:
            print(f"第{i+1}次捕获: 无变化")
        time.sleep(1)
    
    print(f"统计信息: {capture.get_stats()}")

if __name__ == "__main__":
    test_capture()