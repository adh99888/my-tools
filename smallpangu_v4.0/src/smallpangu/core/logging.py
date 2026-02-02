"""
日志系统
提供结构化的日志记录功能
"""

import logging
import logging.config
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 默认日志格式
DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# 颜色支持（如果终端支持）
class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[0;36m',      # 青色
        'INFO': '\033[0;32m',       # 绿色
        'WARNING': '\033[0;33m',    # 黄色
        'ERROR': '\033[0;31m',      # 红色
        'CRITICAL': '\033[0;35m',   # 紫色
        'RESET': '\033[0m',         # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if sys.stdout.isatty() and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            record.msg = f"{self.COLORS[record.levelname]}{record.msg}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（适合机器解析）"""
    
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # 添加额外字段
        if hasattr(record, 'extra'):
            log_record.update(record.extra)
        
        # 添加异常信息
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # 添加文件位置
        log_record['file'] = f"{record.pathname}:{record.lineno}"
        log_record['function'] = record.funcName
        
        # 转换为JSON（简单实现）
        import json
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(
    config: Optional[Dict[str, Any]] = None,
    log_level: Union[str, int] = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True,
    structured: bool = False
) -> None:
    """
    设置日志系统
    
    Args:
        config: 日志配置字典（如果提供，则忽略其他参数）
        log_level: 日志级别
        log_file: 日志文件路径
        enable_console: 是否启用控制台输出
        enable_colors: 是否启用颜色（仅控制台）
        structured: 是否使用结构化日志格式
    """
    if config:
        # 使用提供的配置
        logging.config.dictConfig(config)
        return
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(_get_log_level(log_level))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    handlers = []
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if enable_colors and sys.stdout.isatty():
            formatter = ColoredFormatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
        elif structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
        
        console_handler.setFormatter(formatter)
        console_handler.setLevel(_get_log_level(log_level))
        handlers.append(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)
        
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # 文件记录更详细的日志
        handlers.append(file_handler)
    
    # 设置处理器
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # 设置常见库的日志级别
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def _get_log_level(level: Union[str, int]) -> int:
    """将日志级别转换为logging常量"""
    if isinstance(level, int):
        return level
    return LOG_LEVELS.get(level.upper(), logging.INFO)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称（None表示根日志器）
        
    Returns:
        logging.Logger实例
    """
    return logging.getLogger(name)


class Logger(logging.Logger):
    """
    增强的日志器类，支持结构化日志
    """
    
    def structured(self, level: int, message: str, **kwargs):
        """
        记录结构化日志
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外字段和特殊参数（exc_info, stack_info, stacklevel）
        """
        if self.isEnabledFor(level):
            # 分离特殊参数
            special_keys = {'exc_info', 'stack_info', 'stacklevel'}
            log_kwargs = {}
            extra = {}
            
            # LogRecord的保留字段（不能出现在extra中）
            reserved_keys = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process'
            }
            
            for key, value in kwargs.items():
                if key in special_keys:
                    log_kwargs[key] = value
                elif key in reserved_keys:
                    # 重命名保留字段以避免冲突
                    extra[f'_{key}'] = value
                else:
                    extra[key] = value
            
            # 使用LogRecord的extra属性存储额外字段
            self._log(level, message, (), extra=extra, **log_kwargs)
    
    def debug_struct(self, message: str, **kwargs):
        """记录DEBUG级别的结构化日志"""
        self.structured(logging.DEBUG, message, **kwargs)
    
    def info_struct(self, message: str, **kwargs):
        """记录INFO级别的结构化日志"""
        self.structured(logging.INFO, message, **kwargs)
    
    def warning_struct(self, message: str, **kwargs):
        """记录WARNING级别的结构化日志"""
        self.structured(logging.WARNING, message, **kwargs)
    
    def error_struct(self, message: str, **kwargs):
        """记录ERROR级别的结构化日志"""
        self.structured(logging.ERROR, message, **kwargs)
    
    def critical_struct(self, message: str, **kwargs):
        """记录CRITICAL级别的结构化日志"""
        self.structured(logging.CRITICAL, message, **kwargs)


# 替换logging.Logger为增强版本
logging.setLoggerClass(Logger)


def create_logger_config(
    log_level: str = "INFO",
    console_enabled: bool = True,
    file_enabled: bool = True,
    log_dir: str = "./logs",
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> Dict[str, Any]:
    """
    创建标准日志配置
    
    Returns:
        日志配置字典
    """
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': DEFAULT_FORMAT,
                'datefmt': DEFAULT_DATE_FORMAT,
            },
            'structured': {
                '()': StructuredFormatter,
            },
        },
        'handlers': {},
        'loggers': {
            '': {  # 根日志器
                'handlers': [],
                'level': log_level,
                'propagate': True,
            },
        },
    }
    
    handlers = []
    
    if console_enabled:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        }
        handlers.append('console')
    
    if file_enabled:
        # 主日志文件
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': str(log_dir_path / 'smallpangu.log'),
            'maxBytes': max_file_size_mb * 1024 * 1024,
            'backupCount': backup_count,
            'encoding': 'utf-8',
        }
        handlers.append('file')
        
        # 错误日志文件
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'filename': str(log_dir_path / 'error.log'),
            'maxBytes': max_file_size_mb * 1024 * 1024,
            'backupCount': backup_count,
            'encoding': 'utf-8',
        }
        handlers.append('error_file')
    
    config['loggers']['']['handlers'] = handlers
    
    return config


# 默认日志设置
def setup_default_logging():
    """设置默认日志配置"""
    # 检查是否在开发环境
    is_dev = os.getenv('SMALLPANGU_ENV', 'development') == 'development'
    
    config = create_logger_config(
        log_level='DEBUG' if is_dev else 'INFO',
        console_enabled=True,
        file_enabled=True,
        log_dir='./logs',
        max_file_size_mb=10,
        backup_count=5
    )
    
    setup_logging(config)


# 自动设置日志（如果未设置）
if not logging.getLogger().handlers:
    setup_default_logging()