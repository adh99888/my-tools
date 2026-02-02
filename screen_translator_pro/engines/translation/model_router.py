"""
翻译模型路由器
管理多个翻译API，智能路由翻译请求，支持缓存和失败转移
"""

import time
import hashlib
import json
import sqlite3
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading

@dataclass
class TranslationRequest:
    """翻译请求"""
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    context: Optional[Dict[str, Any]] = None

@dataclass  
class TranslationResult:
    """翻译结果"""
    translated_text: str
    source_text: str
    source_lang: str
    target_lang: str
    confidence: Optional[float] = None
    model: str = ""
    response_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TranslationCache:
    """翻译缓存"""
    
    def __init__(self, cache_path: Optional[str] = None):
        if cache_path is None:
            cache_dir = Path(__file__).parent.parent.parent / "data"
            cache_dir.mkdir(exist_ok=True)
            cache_path = cache_dir / "translation_cache.db"
        
        self.cache_path = str(cache_path)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    hash TEXT PRIMARY KEY,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_lang TEXT,
                    target_lang TEXT,
                    model TEXT,
                    confidence REAL,
                    response_time REAL,
                    timestamp INTEGER,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON translations(timestamp)
            """)
    
    def get_cache_key(self, request: TranslationRequest) -> str:
        """生成缓存键"""
        key_data = {
            'text': request.text,
            'source_lang': request.source_lang,
            'target_lang': request.target_lang
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def get(self, request: TranslationRequest) -> Optional[TranslationResult]:
        """获取缓存"""
        cache_key = self.get_cache_key(request)
        
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM translations 
                WHERE hash = ? 
                LIMIT 1
            """, (cache_key,))
            
            row = cursor.fetchone()
            if row:
                # 更新访问计数
                conn.execute("""
                    UPDATE translations 
                    SET access_count = access_count + 1 
                    WHERE hash = ?
                """, (cache_key,))
                
                return TranslationResult(
                    translated_text=row[2],
                    source_text=row[1],
                    source_lang=row[3] or request.source_lang,
                    target_lang=row[4] or request.target_lang,
                    model=row[5],
                    confidence=row[6],
                    response_time=row[7],
                    metadata={'cached': True, 'access_count': row[9]}
                )
        
        return None
    
    def set(self, request: TranslationRequest, result: TranslationResult):
        """设置缓存"""
        cache_key = self.get_cache_key(request)
        
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO translations 
                (hash, source_text, translated_text, source_lang, target_lang, 
                 model, confidence, response_time, timestamp, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key,
                request.text,
                result.translated_text,
                request.source_lang,
                request.target_lang,
                result.model,
                result.confidence,
                result.response_time,
                int(time.time()),
                1
            ))
    
    def cleanup(self, max_age_days: int = 30, max_size: int = 10000):
        """清理缓存"""
        with sqlite3.connect(self.cache_path) as conn:
            # 删除过期缓存
            old_timestamp = int(time.time()) - max_age_days * 24 * 3600
            conn.execute("""
                DELETE FROM translations 
                WHERE timestamp < ?
            """, (old_timestamp,))
            
            # 如果仍然超过最大大小，删除访问最少的
            cursor = conn.execute("SELECT COUNT(*) FROM translations")
            count = cursor.fetchone()[0]
            
            if count > max_size:
                # 删除访问次数最少的一半缓存
                delete_count = count - max_size // 2
                conn.execute("""
                    DELETE FROM translations 
                    WHERE hash IN (
                        SELECT hash FROM translations 
                        ORDER BY access_count ASC, timestamp ASC 
                        LIMIT ?
                    )
                """, (delete_count,))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM translations")
            total = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT SUM(access_count) FROM translations")
            total_access = cursor.fetchone()[0] or 0
            
            cursor = conn.execute("SELECT AVG(response_time) FROM translations")
            avg_time = cursor.fetchone()[0] or 0
        
        return {
            'total_entries': total,
            'total_access': total_access,
            'avg_response_time': avg_time
        }

class ModelRouter:
    """模型路由器"""
    
    def __init__(self, config: Dict[str, Any], api_configs: Dict[str, Any]):
        self.config = config
        self.api_configs = api_configs
        
        # 主用和备用模型
        self.primary_model = config.get('primary', 'kimi')
        self.fallback_model = config.get('fallback', 'deepseek')
        self.auto_switch = config.get('auto_switch', True)
        
        # 初始化缓存
        cache_enabled = config.get('cache_enabled', True)
        if cache_enabled:
            self.cache = TranslationCache()
        else:
            self.cache = None
        
        # 模型状态跟踪
        self.model_stats = {}
        self._init_model_stats()
        
        # 模型实例（延迟加载）
        self.model_instances = {}
        
        print(f"翻译路由器初始化完成，主模型: {self.primary_model}")
    
    def _init_model_stats(self):
        """初始化模型统计"""
        for model_name in self.api_configs.keys():
            self.model_stats[model_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'last_error': None,
                'last_success': None
            }
    
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """翻译文本"""
        start_time = time.time()
        
        # 检查缓存
        if self.cache:
            cached_result = self.cache.get(request)
            if cached_result:
                cached_result.response_time = (time.time() - start_time) * 1000
                print(f"缓存命中: {request.text[:50]}...")
                return cached_result
        
        # 智能选择模型
        model_name = self._select_model(request)
        
        try:
            # 获取模型实例
            model = self._get_model_instance(model_name)
            if model is None:
                raise ValueError(f"模型 {model_name} 不可用")
            
            # 执行翻译
            result = model.translate(request)
            result.model = model_name
            result.response_time = (time.time() - start_time) * 1000
            
            # 更新统计
            self._update_model_stats(model_name, success=True, response_time=result.response_time)
            
            # 缓存结果
            if self.cache:
                self.cache.set(request, result)
            
            return result
            
        except Exception as e:
            print(f"模型 {model_name} 翻译失败: {e}")
            
            # 更新统计
            self._update_model_stats(model_name, success=False, error=str(e))
            
            # 失败转移
            if self.auto_switch and model_name != self.fallback_model:
                print(f"尝试切换到备用模型: {self.fallback_model}")
                fallback_request = TranslationRequest(
                    text=request.text,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang,
                    context={'fallback_from': model_name}
                )
                return self.translate(fallback_request)
            
            # 所有尝试都失败，返回错误结果
            return TranslationResult(
                translated_text=f"[翻译失败: {str(e)[:100]}]",
                source_text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                confidence=0.0,
                model="error",
                response_time=(time.time() - start_time) * 1000,
                metadata={'error': str(e), 'failed_models': [model_name]}
            )
    
    def _select_model(self, request: TranslationRequest) -> str:
        """智能选择模型"""
        # 简单实现：根据文本特征选择
        text = request.text
        
        # 检查文本长度
        if len(text) > 5000:
            # 长文本：使用支持长上下文的模型
            if self._is_model_available('kimi'):
                return 'kimi'
            elif self._is_model_available('siliconflow'):
                return 'siliconflow'
        
        # 检查是否包含代码/技术内容
        if self._looks_like_code(text):
            # 代码内容：使用DeepSeek（代码能力强）
            if self._is_model_available('deepseek'):
                return 'deepseek'
        
        # 默认使用主模型
        if self._is_model_available(self.primary_model):
            return self.primary_model
        
        # 主模型不可用，使用第一个可用的模型
        for model_name in self.api_configs.keys():
            if self._is_model_available(model_name):
                return model_name
        
        # 没有可用模型
        return self.primary_model
    
    def _is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""
        if model_name not in self.api_configs:
            return False
        
        # 检查API密钥
        api_config = self.api_configs[model_name]
        if not api_config.get('api_key'):
            return False
        
        # 检查模型状态（最近失败次数太多）
        stats = self.model_stats.get(model_name, {})
        if stats.get('failed_requests', 0) > 5:
            # 最近失败次数太多，暂时禁用
            return False
        
        return True
    
    def _looks_like_code(self, text: str) -> bool:
        """判断文本是否像代码"""
        code_indicators = [
            '{', '}', '(', ')', '[', ']',  # 括号
            ';', '=', '==', '!=', '+=', '-=',  # 操作符
            'def ', 'class ', 'import ', 'from ',  # Python关键词
            'function ', 'var ', 'let ', 'const ',  # JavaScript关键词
            'if ', 'else ', 'for ', 'while ',  # 控制流关键词
            'public ', 'private ', 'protected ',  # Java/C++关键词
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in code_indicators if indicator in text_lower)
        
        # 如果包含多个代码特征，认为是代码
        return indicator_count >= 3
    
    def _get_model_instance(self, model_name: str):
        """获取模型实例（延迟加载）"""
        if model_name in self.model_instances:
            return self.model_instances[model_name]
        
        if model_name not in self.api_configs:
            return None
        
        api_config = self.api_configs[model_name]
        
        try:
            if model_name == 'kimi':
                from .apis.kimi_translator import KimiTranslator
                model = KimiTranslator(api_config)
            elif model_name == 'deepseek':
                from .apis.deepseek_translator import DeepSeekTranslator
                model = DeepSeekTranslator(api_config)
            elif model_name == 'qwen':
                from .apis.qwen_translator import QwenTranslator
                model = QwenTranslator(api_config)
            elif model_name == 'siliconflow':
                from .apis.siliconflow_translator import SiliconFlowTranslator
                model = SiliconFlowTranslator(api_config)
            elif model_name == 'glm':
                from .apis.glm_translator import GLMTranslator
                model = GLMTranslator(api_config)
            else:
                print(f"未知模型: {model_name}")
                return None
            
            # 初始化模型
            if model.initialize():
                self.model_instances[model_name] = model
                print(f"模型 {model_name} 初始化成功")
                return model
            else:
                print(f"模型 {model_name} 初始化失败")
                return None
                
        except ImportError as e:
            print(f"导入模型 {model_name} 失败: {e}")
            print(f"请安装必要的依赖: pip install openai")
            return None
        except Exception as e:
            print(f"初始化模型 {model_name} 失败: {e}")
            return None
    
    def _update_model_stats(self, model_name: str, success: bool, 
                           response_time: float = 0.0, error: Optional[str] = None):
        """更新模型统计"""
        if model_name not in self.model_stats:
            self.model_stats[model_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'last_error': None,
                'last_success': None
            }
        
        stats = self.model_stats[model_name]
        stats['total_requests'] += 1
        
        if success:
            stats['successful_requests'] += 1
            stats['last_success'] = time.time()
            
            # 更新平均响应时间
            alpha = 0.1
            stats['avg_response_time'] = (
                alpha * response_time + 
                (1 - alpha) * stats['avg_response_time']
            )
        else:
            stats['failed_requests'] += 1
            stats['last_error'] = error
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self.cache.get_stats() if self.cache else {}
        
        return {
            'model_stats': self.model_stats,
            'cache_stats': cache_stats,
            'config': {
                'primary_model': self.primary_model,
                'fallback_model': self.fallback_model,
                'auto_switch': self.auto_switch
            }
        }
    
    def cleanup_cache(self):
        """清理缓存"""
        if self.cache:
            self.cache.cleanup()
            print("缓存已清理")
    
    def update_config(self, new_config: Dict[str, Any], new_api_configs: Optional[Dict[str, Any]] = None):
        """更新配置"""
        self.config.update(new_config)
        
        if 'primary' in new_config:
            self.primary_model = new_config['primary']
        
        if 'fallback' in new_config:
            self.fallback_model = new_config['fallback']
        
        if 'auto_switch' in new_config:
            self.auto_switch = new_config['auto_switch']
        
        if new_api_configs:
            self.api_configs.update(new_api_configs)
        
        print(f"翻译配置已更新")

# 测试函数
def test_translation():
    """测试翻译功能"""
    config = {
        'primary': 'kimi',
        'fallback': 'deepseek',
        'auto_switch': True,
        'cache_enabled': True
    }
    
    api_configs = {
        'kimi': {
            'api_key': 'sk-test-key',  # 测试用，实际使用时替换
            'model': 'kimi-k2-turbo-preview',
            'base_url': 'https://api.moonshot.cn/v1'
        }
    }
    
    router = ModelRouter(config, api_configs)
    
    # 测试请求
    request = TranslationRequest(
        text="Hello, this is a test translation.",
        source_lang="en",
        target_lang="zh"
    )
    
    print("测试翻译...")
    result = router.translate(request)
    
    print(f"原文: {result.source_text}")
    print(f"译文: {result.translated_text}")
    print(f"模型: {result.model}, 响应时间: {result.response_time:.2f}ms")
    
    print(f"统计信息: {router.get_stats()}")

if __name__ == "__main__":
    test_translation()