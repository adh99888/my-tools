"""
错误处理框架
定义应用程序级别的异常类
"""

from typing import Any, Optional


class AppError(Exception):
    """应用程序基础异常"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", 
                 details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)
    
    def __str__(self) -> str:
        details_str = f" (details: {self.details})" if self.details else ""
        return f"[{self.code}] {self.message}{details_str}"


class PluginError(AppError):
    """插件相关异常"""
    
    def __init__(self, message: str, plugin_name: Optional[str] = None, 
                 details: Optional[Any] = None):
        code = f"PLUGIN_ERROR.{plugin_name}" if plugin_name else "PLUGIN_ERROR"
        super().__init__(message, code, details)
        self.plugin_name = plugin_name


class ConfigError(AppError):
    """配置相关异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None,
                 details: Optional[Any] = None):
        code = f"CONFIG_ERROR.{config_path}" if config_path else "CONFIG_ERROR"
        super().__init__(message, code, details)
        self.config_path = config_path


class ValidationError(AppError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None, details: Optional[Any] = None):
        code = f"VALIDATION_ERROR.{field}" if field else "VALIDATION_ERROR"
        super().__init__(message, code, details)
        self.field = field
        self.value = value


class DependencyError(AppError):
    """依赖注入异常"""
    
    def __init__(self, message: str, service_name: Optional[str] = None,
                 details: Optional[Any] = None):
        code = f"DEPENDENCY_ERROR.{service_name}" if service_name else "DEPENDENCY_ERROR"
        super().__init__(message, code, details)
        self.service_name = service_name


class SecurityError(AppError):
    """安全相关异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 severity: str = "MEDIUM", details: Optional[Any] = None):
        code = f"SECURITY_ERROR.{operation}" if operation else "SECURITY_ERROR"
        super().__init__(message, code, details)
        self.operation = operation
        self.severity = severity


class AIError(AppError):
    """AI服务异常"""
    
    def __init__(self, message: str, provider: Optional[str] = None,
                 model: Optional[str] = None, details: Optional[Any] = None):
        code_parts = ["AI_ERROR"]
        if provider:
            code_parts.append(provider)
        if model:
            code_parts.append(model)
        code = ".".join(code_parts)
        
        super().__init__(message, code, details)
        self.provider = provider
        self.model = model


class NetworkError(AppError):
    """网络相关异常"""
    
    def __init__(self, message: str, url: Optional[str] = None,
                 status_code: Optional[int] = None, details: Optional[Any] = None):
        code = "NETWORK_ERROR"
        if status_code:
            code = f"NETWORK_ERROR.{status_code}"
        
        super().__init__(message, code, details)
        self.url = url
        self.status_code = status_code


class TimeoutError(AppError):
    """超时异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 timeout_seconds: Optional[float] = None, details: Optional[Any] = None):
        code = f"TIMEOUT_ERROR.{operation}" if operation else "TIMEOUT_ERROR"
        super().__init__(message, code, details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class ResourceError(AppError):
    """资源相关异常（内存、磁盘、CPU等）"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None,
                 limit: Optional[Any] = None, current: Optional[Any] = None,
                 details: Optional[Any] = None):
        code = f"RESOURCE_ERROR.{resource_type}" if resource_type else "RESOURCE_ERROR"
        super().__init__(message, code, details)
        self.resource_type = resource_type
        self.limit = limit
        self.current = current


class StateError(AppError):
    """状态相关异常（非法状态转换等）"""
    
    def __init__(self, message: str, current_state: Optional[str] = None,
                 target_state: Optional[str] = None, details: Optional[Any] = None):
        code = "STATE_ERROR"
        if current_state and target_state:
            code = f"STATE_ERROR.{current_state}.{target_state}"
        
        super().__init__(message, code, details)
        self.current_state = current_state
        self.target_state = target_state


class UIError(AppError):
    """UI相关异常"""
    
    def __init__(self, message: str, widget_id: Optional[str] = None,
                 component: Optional[str] = None, details: Optional[Any] = None):
        code = "UI_ERROR"
        if widget_id:
            code = f"UI_ERROR.{widget_id}"
        elif component:
            code = f"UI_ERROR.{component}"
        
        super().__init__(message, code, details)
        self.widget_id = widget_id
        self.component = component


# 便捷错误检查函数
def ensure(condition: bool, error_class: type, *args, **kwargs):
    """
    条件检查，如果不满足条件则抛出指定异常
    
    Args:
        condition: 检查条件
        error_class: 异常类
        *args, **kwargs: 传递给异常构造函数的参数
    """
    if not condition:
        raise error_class(*args, **kwargs)


def require_not_none(value: Any, name: str = "value") -> Any:
    """
    检查值是否为None，如果是则抛出ValidationError
    
    Args:
        value: 要检查的值
        name: 值的名称（用于错误信息）
        
    Returns:
        原值（如果非None）
    """
    if value is None:
        raise ValidationError(f"{name}不能为None", field=name)
    return value


def require_type(value: Any, expected_type: type, name: str = "value") -> Any:
    """
    检查值的类型，如果不匹配则抛出ValidationError
    
    Args:
        value: 要检查的值
        expected_type: 期望的类型
        name: 值的名称（用于错误信息）
        
    Returns:
        原值（如果类型匹配）
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"{name}的类型应为{expected_type.__name__}，实际为{type(value).__name__}",
            field=name,
            value=value
        )
    return value


# 导出所有异常类
__all__ = [
    "AppError",
    "PluginError",
    "ConfigError",
    "ValidationError",
    "DependencyError",
    "SecurityError",
    "AIError",
    "NetworkError",
    "TimeoutError",
    "ResourceError",
    "StateError",
    "UIError",
    "ensure",
    "require_not_none",
    "require_type"
]