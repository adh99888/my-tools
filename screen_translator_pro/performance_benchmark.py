#!/usr/bin/env python3
"""
DeepSeek OCR翻译引擎性能测试和基准对比脚本
测试优化后的性能提升效果
"""

import os
import sys
import time
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.ocr.deepseek_ocr_translator import DeepSeekOCRTranslator


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化基准测试"""
        self.config = self._load_config(config_path)
        self.results = []
        self.test_images = []
        
        # 创建测试图像
        self._create_test_images()
        
        print("=" * 80)
        print("DeepSeek OCR翻译引擎性能基准测试")
        print("=" * 80)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        import yaml
        
        if not os.path.exists(config_path):
            print(f"警告: 配置文件不存在: {config_path}")
            return {
                'ocr': {
                    'vision': {
                        'deepseek_translator': {
                            'enabled': True,
                            'model_path': "d:/deepseek ocr - 副本/DeepSeek-OCR/deepseek-ocr-local",
                            'device': 'auto',
                            'use_half_precision': True,
                            'cache_enabled': True
                        }
                    }
                }
            }
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _create_test_images(self):
        """创建测试图像"""
        from PIL import Image, ImageDraw, ImageFont
        import cv2
        
        print("创建测试图像...")
        
        # 测试图像1: 简单文本
        img1 = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img1)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), "性能测试: DeepSeek OCR翻译引擎", fill='black', font=font)
        draw.text((50, 100), "This is a test image for OCR performance benchmarking.", fill='black', font=font)
        draw.text((50, 150), "这是一个用于OCR性能基准测试的图像。", fill='black', font=font)
        draw.text((50, 200), "测试多语言文本识别和翻译性能。", fill='black', font=font)
        
        # 测试图像2: 复杂文档
        img2 = Image.new('RGB', (1024, 768), color='white')
        draw = ImageDraw.Draw(img2)
        
        # 模拟文档内容
        lines = [
            "文档标题: 性能测试报告",
            "日期: 2026年2月5日",
            "测试项目: DeepSeek OCR翻译引擎",
            "",
            "1. 测试目标",
            "   - 评估OCR识别准确率",
            "   - 测量翻译处理速度",
            "   - 验证GPU加速效果",
            "",
            "2. 测试方法",
            "   - 使用标准测试图像集",
            "   - 记录处理时间和内存使用",
            "   - 对比优化前后性能",
            "",
            "3. 预期结果",
            "   - 识别准确率 > 95%",
            "   - 处理时间 < 30秒",
            "   - GPU加速效果明显"
        ]
        
        y_pos = 50
        for line in lines:
            draw.text((50, y_pos), line, fill='black', font=font)
            y_pos += 30
        
        # 转换为OpenCV格式
        self.test_images = [
            (cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR), "简单文本"),
            (cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR), "复杂文档")
        ]
        
        print(f"创建了 {len(self.test_images)} 个测试图像")
    
    def test_model_loading(self, engine: DeepSeekOCRTranslator) -> Dict[str, Any]:
        """测试模型加载性能"""
        print("\n" + "=" * 60)
        print("测试1: 模型加载性能")
        print("=" * 60)
        
        start_time = time.time()
        success = engine.initialize()
        load_time = time.time() - start_time
        
        result = {
            "test_name": "模型加载",
            "success": success,
            "load_time": load_time,
            "device": engine.device,
            "model_loaded": engine.model is not None,
            "tokenizer_loaded": engine.tokenizer is not None
        }
        
        print(f"模型加载结果: {'成功' if success else '失败'}")
        print(f"加载时间: {load_time:.2f}秒")
        print(f"设备: {engine.device}")
        
        return result
    
    def test_single_image_recognition(self, engine: DeepSeekOCRTranslator) -> Dict[str, Any]:
        """测试单张图像识别性能"""
        print("\n" + "=" * 60)
        print("测试2: 单张图像识别性能")
        print("=" * 60)
        
        if not engine.initialized:
            print("引擎未初始化，跳过测试")
            return {"test_name": "单张图像识别", "skipped": True}
        
        results = []
        
        for i, (image, description) in enumerate(self.test_images):
            print(f"\n处理图像 {i+1}: {description}")
            
            # 第一次识别（可能包含缓存预热）
            start_time = time.time()
            text_blocks = engine.recognize(image, translate=True)
            first_time = time.time() - start_time
            
            # 第二次识别（测试缓存效果）
            start_time = time.time()
            text_blocks2 = engine.recognize(image, translate=True)
            second_time = time.time() - start_time
            
            result = {
                "image_type": description,
                "first_recognition_time": first_time,
                "second_recognition_time": second_time,
                "cache_speedup": first_time / second_time if second_time > 0 else 0,
                "text_blocks_found": len(text_blocks),
                "sample_text": text_blocks[0].text[:100] + "..." if text_blocks else ""
            }
            
            results.append(result)
            
            print(f"  第一次识别时间: {first_time:.2f}秒")
            print(f"  第二次识别时间: {second_time:.2f}秒")
            print(f"  缓存加速比: {result['cache_speedup']:.2f}x")
            print(f"  找到文本块: {len(text_blocks)}个")
        
        return {
            "test_name": "单张图像识别",
            "results": results,
            "avg_first_time": np.mean([r["first_recognition_time"] for r in results]),
            "avg_second_time": np.mean([r["second_recognition_time"] for r in results])
        }
    
    def test_batch_processing(self, engine: DeepSeekOCRTranslator) -> Dict[str, Any]:
        """测试批量处理性能"""
        print("\n" + "=" * 60)
        print("测试3: 批量处理性能")
        print("=" * 60)
        
        if not engine.initialized:
            print("引擎未初始化，跳过测试")
            return {"test_name": "批量处理", "skipped": True}
        
        # 创建批量测试图像（重复使用测试图像）
        batch_images = [img for img, _ in self.test_images * 3]  # 6张图像
        
        print(f"批量处理 {len(batch_images)} 张图像...")
        
        # 顺序处理
        start_time = time.time()
        sequential_results = engine.batch_process(batch_images, translate=True)
        sequential_time = time.time() - start_time
        
        # 获取统计信息
        stats = engine.get_stats()
        
        result = {
            "test_name": "批量处理",
            "batch_size": len(batch_images),
            "sequential_time": sequential_time,
            "avg_time_per_image": sequential_time / len(batch_images),
            "gpu_inferences": stats.get("gpu_inferences", 0),
            "cpu_inferences": stats.get("cpu_inferences", 0),
            "cache_hit_rate": stats.get("cache_hit_rate", 0),
            "avg_gpu_time": stats.get("avg_gpu_time", 0),
            "avg_cpu_time": stats.get("avg_cpu_time", 0)
        }
        
        print(f"批量处理时间: {sequential_time:.2f}秒")
        print(f"平均每张图像: {result['avg_time_per_image']:.2f}秒")
        print(f"GPU推理次数: {result['gpu_inferences']}")
        print(f"缓存命中率: {result['cache_hit_rate']:.2%}")
        
        return result
    
    def test_memory_usage(self, engine: DeepSeekOCRTranslator) -> Dict[str, Any]:
        """测试内存使用情况"""
        print("\n" + "=" * 60)
        print("测试4: 内存使用情况")
        print("=" * 60)
        
        import psutil
        import torch
        
        process = psutil.Process()
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行一些推理以观察内存变化
        if engine.initialized:
            for i, (image, description) in enumerate(self.test_images[:2]):
                engine.recognize(image, translate=True)
        
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # GPU内存使用
        gpu_memory = {}
        if torch.cuda.is_available():
            gpu_memory = {
                "allocated_mb": torch.cuda.memory_allocated() / 1024 / 1024,
                "reserved_mb": torch.cuda.memory_reserved() / 1024 / 1024,
                "max_allocated_mb": torch.cuda.max_memory_allocated() / 1024 / 1024
            }
        
        result = {
            "test_name": "内存使用",
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "gpu_memory": gpu_memory
        }
        
        print(f"初始内存: {initial_memory:.1f}MB")
        print(f"最终内存: {final_memory:.1f}MB")
        print(f"内存增加: {result['memory_increase_mb']:.1f}MB")
        
        if gpu_memory:
            print(f"GPU已分配内存: {gpu_memory['allocated_mb']:.1f}MB")
            print(f"GPU峰值内存: {gpu_memory['max_allocated_mb']:.1f}MB")
        
        return result
    
    def test_async_processing(self, engine: DeepSeekOCRTranslator) -> Dict[str, Any]:
        """测试异步处理性能"""
        print("\n" + "=" * 60)
        print("测试5: 异步处理性能")
        print("=" * 60)
        
        if not engine.initialized:
            print("引擎未初始化，跳过测试")
            return {"test_name": "异步处理", "skipped": True}
        
        # 测试异步单张图像处理
        import threading
        
        test_image, _ = self.test_images[0]
        results = []
        
        def callback(result):
            results.append(result)
        
        print("测试异步单张图像处理...")
        start_time = time.time()
        thread = engine.recognize_async(test_image, translate=True, callback=callback)
        thread.join()
        async_time = time.time() - start_time
        
        # 测试同步处理对比
        start_time = time.time()
        sync_result = engine.recognize(test_image, translate=True)
        sync_time = time.time() - start_time
        
        result = {
            "test_name": "异步处理",
            "async_time": async_time,
            "sync_time": sync_time,
            "async_overhead": async_time - sync_time,
            "results_received": len(results)
        }
        
        print(f"异步处理时间: {async_time:.2f}秒")
        print(f"同步处理时间: {sync_time:.2f}秒")
        print(f"异步开销: {result['async_overhead']:.2f}秒")
        
        return result
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有性能测试"""
        print("\n" + "=" * 80)
        print("开始全面性能测试")
        print("=" * 80)
        
        # 创建引擎实例
        engine_config = self.config.get('ocr', {}).get('vision', {}).get('deepseek_translator', {})
        engine = DeepSeekOCRTranslator(engine_config)
        
        all_results = []
        
        try:
            # 测试1: 模型加载
            result1 = self.test_model_loading(engine)
            all_results.append(result1)
            
            if result1["success"]:
                # 测试2: 单张图像识别
                result2 = self.test_single_image_recognition(engine)
                all_results.append(result2)
                
                # 测试3: 批量处理
                result3 = self.test_batch_processing(engine)
                all_results.append(result3)
                
                # 测试4: 内存使用
                result4 = self.test_memory_usage(engine)
                all_results.append(result4)
                
                # 测试5: 异步处理
                result5 = self.test_async_processing(engine)
                all_results.append(result5)
            
            # 生成测试报告
            self._generate_report(all_results, engine)
            
        finally:
            # 清理资源
            engine.cleanup()
        
        return all_results
    
    def _generate_report(self, results: List[Dict[str, Any]], engine: DeepSeekOCRTranslator):
        """生成性能测试报告"""
        print("\n" + "=" * 80)
        print("性能测试报告")
        print("=" * 80)
        
        # 收集关键指标
        key_metrics = {}
        
        for result in results:
            test_name = result.get("test_name", "未知测试")
            
            if test_name == "模型加载":
                key_metrics["model_load_time"] = result.get("load_time", 0)
                key_metrics["model_load_success"] = result.get("success", False)
            
            elif test_name == "单张图像识别":
                if "avg_first_time" in result:
                    key_metrics["avg_first_recognition_time"] = result["avg_first_time"]
                    key_metrics["avg_second_recognition_time"] = result["avg_second_time"]
                    key_metrics["cache_speedup"] = result["avg_first_time"] / result["avg_second_time"] if result["avg_second_time"] > 0 else 0
            
            elif test_name == "批量处理":
                key_metrics["batch_processing_time"] = result.get("sequential_time", 0)
                key_metrics["avg_time_per_image"] = result.get("avg_time_per_image", 0)
                key_metrics["cache_hit_rate"] = result.get("cache_hit_rate", 0)
            
            elif test_name == "内存使用":
                key_metrics["memory_increase_mb"] = result.get("memory_increase_mb", 0)
                if "gpu_memory" in result and result["gpu_memory"]:
                    key_metrics["gpu_allocated_mb"] = result["gpu_memory"].get("allocated_mb", 0)
                    key_metrics["gpu_peak_mb"] = result["gpu_memory"].get("max_allocated_mb", 0)
        
        # 获取引擎统计信息
        stats = engine.get_stats()
        
        # 打印报告（使用ASCII字符避免编码问题）
        print("\n[关键性能指标]:")
        print("-" * 40)
        
        if "model_load_time" in key_metrics:
            print(f"[OK] 模型加载时间: {key_metrics['model_load_time']:.2f}秒")
        
        if "avg_first_recognition_time" in key_metrics:
            print(f"[OK] 首次识别平均时间: {key_metrics['avg_first_recognition_time']:.2f}秒")
            print(f"[OK] 缓存后识别平均时间: {key_metrics['avg_second_recognition_time']:.2f}秒")
            print(f"[OK] 缓存加速比: {key_metrics['cache_speedup']:.2f}x")
        
        if "avg_time_per_image" in key_metrics:
            print(f"[OK] 批量处理平均时间: {key_metrics['avg_time_per_image']:.2f}秒/图像")
            print(f"[OK] 缓存命中率: {key_metrics['cache_hit_rate']:.2%}")
        
        if "memory_increase_mb" in key_metrics:
            print(f"[OK] 内存增加: {key_metrics['memory_increase_mb']:.1f}MB")
        
        if "gpu_allocated_mb" in key_metrics:
            print(f"[OK] GPU显存使用: {key_metrics['gpu_allocated_mb']:.1f}MB")
            print(f"[OK] GPU峰值显存: {key_metrics['gpu_peak_mb']:.1f}MB")
        
        print("\n[引擎配置]:")
        print("-" * 40)
        print(f"设备: {stats.get('device', '未知')}")
        print(f"混合精度: {stats.get('use_half_precision', False)}")
        print(f"基础分辨率: {stats.get('base_size', 0)}")
        print(f"图像尺寸: {stats.get('image_size', 0)}")
        print(f"缓存启用: {stats.get('cache_enabled', False)}")
        
        print("\n[性能评估]:")
        print("-" * 40)
        
        # 性能评估
        if key_metrics.get("avg_first_recognition_time", 100) < 30:
            print("[OK] 识别速度: 优秀 (<30秒)")
        elif key_metrics.get("avg_first_recognition_time", 100) < 60:
            print("[WARN] 识别速度: 良好 (30-60秒)")
        else:
            print("[ERROR] 识别速度: 较慢 (>60秒)")
        
        if key_metrics.get("cache_speedup", 1) > 1.5:
            print("[OK] 缓存效果: 优秀 (>1.5x加速)")
        elif key_metrics.get("cache_speedup", 1) > 1.1:
            print("[WARN] 缓存效果: 良好 (1.1-1.5x加速)")
        else:
            print("[ERROR] 缓存效果: 不明显")
        
        if key_metrics.get("memory_increase_mb", 1000) < 500:
            print("[OK] 内存效率: 优秀 (<500MB增加)")
        elif key_metrics.get("memory_increase_mb", 1000) < 1000:
            print("[WARN] 内存效率: 良好 (500-1000MB增加)")
        else:
            print("[ERROR] 内存效率: 较高 (>1000MB增加)")
        
        print("\n[优化建议]:")
        print("-" * 40)
        
        suggestions = []
        
        if key_metrics.get("avg_first_recognition_time", 100) > 30:
            suggestions.append("降低图像分辨率以提高识别速度")
        
        if key_metrics.get("cache_speedup", 1) < 1.2:
            suggestions.append("增加缓存大小以提高缓存命中率")
        
        if key_metrics.get("memory_increase_mb", 1000) > 800:
            suggestions.append("启用更激进的内存优化策略")
        
        if not suggestions:
            suggestions.append("当前配置性能良好，无需额外优化")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
        
        # 保存报告到文件
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "key_metrics": key_metrics,
            "engine_stats": stats,
            "all_results": results,
            "suggestions": suggestions
        }
        
        report_file = "performance_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n[报告] 详细报告已保存到: {report_file}")
        print("=" * 80)


def main():
    """主函数"""
    try:
        benchmark = PerformanceBenchmark()
        results = benchmark.run_all_tests()
        
        print("\n[完成] 性能测试完成!")
        print("使用以下命令查看详细报告:")
        print("python performance_benchmark.py")
        
    except Exception as e:
        print(f"[错误] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())