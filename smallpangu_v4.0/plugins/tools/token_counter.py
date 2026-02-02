"""
Token计数器插件

提供Token估算、使用量跟踪和限制管理功能。
继承自v3.1的TokenCounter，适配为v4.0插件架构。
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from smallpangu.plugins.base import plugin, PluginType, ToolPlugin, PluginContext

logger = logging.getLogger(__name__)


@dataclass
class ProviderUsage:
    """提供商使用数据"""
    total: int = 0
    daily: int = 0
    daily_limit: int = 100000
    operations: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        if self.operations is None:
            self.operations = {}


@plugin(
    name="tools.token_counter",
    display_name="Token计数器",
    version="1.0.0",
    description="计算文本的Token数量并提供使用量跟踪",
    author="小盘古项目组",
    plugin_type=PluginType.TOOL,
    python_dependencies=["tiktoken"],
    tags=["token", "counting", "monitoring", "analytics"],
    default_config={
        "daily_limit": 100000,
        "enable_tracking": True,
        "default_model": "gpt-3.5-turbo"
    }
)
class TokenCounterPlugin(ToolPlugin):
    """Token计数器插件 - 计算和监控Token使用量"""
    
    def __init__(self, context: PluginContext):
        super().__init__(context)
        self.model_token_limits = {
            "deepseek": {
                "max_tokens": 4096,
                "cost_per_1k": 0.00014,
                "models": ["deepseek-chat", "deepseek-coder"]
            },
            "zhipu": {
                "max_tokens": 4096,
                "cost_per_1k": 0.0001,
                "models": ["glm-4", "glm-3-turbo"]
            },
            "qwen": {
                "max_tokens": 6000,
                "cost_per_1k": 0.00012,
                "models": ["qwen-turbo", "qwen-plus"]
            },
            "kimi": {
                "max_tokens": 4096,
                "cost_per_1k": 0.00015,
                "models": ["moonshot-v1-8k"]
            },
            "siliconflow": {
                "max_tokens": 8192,
                "cost_per_1k": 0.00008,
                "models": ["deepseek-ai/DeepSeek-V3"]
            }
        }
        self.usage_history: Dict[str, ProviderUsage] = {}
        
        # 从配置加载设置
        self.daily_limit = self.config.get("daily_limit", 100000)
        self.enable_tracking = self.config.get("enable_tracking", True)
        self.default_model = self.config.get("default_model", "gpt-3.5-turbo")
        
        self.logger.debug(f"Token计数器插件初始化完成，配置: {self.config}")
    
    def on_initialize(self) -> None:
        """初始化钩子"""
        self.logger.info("Token计数器插件初始化")
        
        # 初始化使用历史（如果需要从持久化存储加载）
        # 这里可以添加从文件或数据库加载历史数据的逻辑
        
        # 注册服务到容器
        self.register_service(TokenCounterPlugin, self)
        self.logger.debug("Token计数器服务已注册到容器")
    
    def on_start(self) -> None:
        """启动钩子"""
        self.logger.info("Token计数器插件启动")
        
        # 订阅相关事件（例如：token_used, model_changed等）
        self.subscribe_event("token.used", self._handle_token_used_event)
        self.subscribe_event("model.selected", self._handle_model_selected_event)
        
        self.logger.debug("Token计数器插件事件订阅完成")
    
    def on_stop(self) -> None:
        """停止钩子"""
        self.logger.info("Token计数器插件停止")
        # 清理操作（如果有）
    
    def on_shutdown(self) -> None:
        """关闭钩子"""
        self.logger.info("Token计数器插件关闭")
        # 保存使用历史到持久化存储（如果需要）
        # 这里可以添加保存到文件或数据库的逻辑
    
    # ToolPlugin协议实现
    @property
    def tool_schema(self) -> Dict[str, Any]:
        """工具模式定义（OpenAI函数调用格式）"""
        return {
            "type": "function",
            "function": {
                "name": "token_counter",
                "description": "计算文本的Token数量，跟踪使用量，获取模型信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["estimate", "track", "get_info", "get_stats", "reset_daily"],
                            "description": "要执行的操作"
                        },
                        "text": {
                            "type": "string",
                            "description": "要估算Token的文本（仅estimate操作需要）"
                        },
                        "model": {
                            "type": "string",
                            "description": "模型名称（estimate和track操作需要）"
                        },
                        "tokens_used": {
                            "type": "integer",
                            "description": "已使用的Token数量（track操作需要）"
                        },
                        "operation_type": {
                            "type": "string",
                            "description": "操作类型（track操作需要）",
                            "default": "chat"
                        },
                        "provider": {
                            "type": "string",
                            "description": "提供商名称（get_stats和reset_daily操作需要）"
                        }
                    },
                    "required": ["action"]
                }
            }
        }
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具操作
        
        Args:
            input_data: 输入数据，包含action和其他参数
            
        Returns:
            操作结果
        """
        action = input_data.get("action", "estimate")
        
        try:
            if action == "estimate":
                return self._execute_estimate(input_data)
            elif action == "track":
                return self._execute_track(input_data)
            elif action == "get_info":
                return self._execute_get_info(input_data)
            elif action == "get_stats":
                return self._execute_get_stats(input_data)
            elif action == "reset_daily":
                return self._execute_reset_daily(input_data)
            else:
                return {
                    "success": False,
                    "error": f"未知操作: {action}",
                    "supported_actions": ["estimate", "track", "get_info", "get_stats", "reset_daily"]
                }
        except Exception as e:
            self.logger.error(f"执行操作 {action} 时出错: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    # 核心功能方法（从v3.1移植并适配）
    def estimate_tokens(self, text: str, model: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 要估算的文本
            model: 使用的模型
            
        Returns:
            估算的token数量
        """
        if not text:
            return 0
        
        try:
            import tiktoken
            try:
                enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
                tokens = enc.encode(text)
                return len(tokens)
            except:
                enc = tiktoken.get_encoding("cl100k_base")
                tokens = enc.encode(text)
                return len(tokens)
        except ImportError:
            # 回退到简单估算
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_chars = len(text) - chinese_chars
            estimated = english_chars * 0.25 + chinese_chars * 0.5
            return int(estimated)
        except Exception as e:
            self.logger.warning(f"Token估算失败，使用简单估算: {e}")
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_chars = len(text) - chinese_chars
            estimated = english_chars * 0.25 + chinese_chars * 0.5
            return int(estimated)
    
    def track_usage(self, model: str, tokens_used: int, operation_type: str = "chat") -> Dict[str, Any]:
        """
        跟踪使用量
        
        Args:
            model: 使用的模型
            tokens_used: 使用的token数量
            operation_type: 操作类型
            
        Returns:
            使用状态信息
        """
        if not self.enable_tracking:
            return {"status": "tracking_disabled", "message": "使用量跟踪已禁用"}
        
        provider = self._get_provider_from_model(model)
        
        if provider not in self.usage_history:
            self.usage_history[provider] = ProviderUsage(daily_limit=self.daily_limit)
        
        ops = self.usage_history[provider].operations
        if ops is None:
            self.usage_history[provider].operations = {}
            ops = self.usage_history[provider].operations
        
        if operation_type not in ops:
            ops[operation_type] = 0
        
        self.usage_history[provider].total += tokens_used
        self.usage_history[provider].daily += tokens_used
        ops[operation_type] += tokens_used
        
        self.logger.info(f"记录Token使用: {provider} {tokens_used} tokens, 操作: {operation_type}")
        
        # 发布使用事件
        self.publish_event("token.used", {
            "provider": provider,
            "model": model,
            "tokens": tokens_used,
            "operation_type": operation_type,
            "daily_total": self.usage_history[provider].daily
        })
        
        return self._check_limits(provider)
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        获取模型信息
        
        Args:
            model: 模型名称
            
        Returns:
            模型信息字典，如果模型不存在则返回None
        """
        provider = self._get_provider_from_model(model)
        if provider in self.model_token_limits:
            return {
                "provider": provider,
                "max_tokens": self.model_token_limits[provider]["max_tokens"],
                "cost_per_1k": self.model_token_limits[provider]["cost_per_1k"],
                "available_models": self.model_token_limits[provider]["models"]
            }
        return None
    
    def get_usage_statistics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        获取使用统计信息
        
        Args:
            provider: 指定提供商，如果为None则返回所有提供商的统计
            
        Returns:
            统计信息字典
        """
        if provider:
            if provider in self.usage_history:
                return {provider: self.usage_history[provider]}
            return {provider: ProviderUsage()}
        else:
            return dict(self.usage_history)
    
    def reset_daily_usage(self, provider: Optional[str] = None):
        """
        重置每日使用量
        
        Args:
            provider: 指定提供商，如果为None则重置所有提供商
        """
        if provider:
            if provider in self.usage_history:
                self.usage_history[provider].daily = 0
                self.logger.info(f"重置 {provider} 的每日使用量")
        else:
            for provider_data in self.usage_history.values():
                provider_data.daily = 0
            self.logger.info("重置所有提供商的每日使用量")
    
    def get_total_tokens(self) -> Dict[str, int]:
        """
        获取总Token使用量
        
        Returns:
            总token使用量，按提供商分组
        """
        total = {}
        for provider, data in self.usage_history.items():
            total[provider] = data.total
        return total
    
    def get_daily_tokens(self) -> Dict[str, int]:
        """
        获取每日Token使用量
        
        Returns:
            每日token使用量，按提供商分组
        """
        daily = {}
        for provider, data in self.usage_history.items():
            daily[provider] = data.daily
        return daily
    
    def get_context_token_limit(self, model: str) -> int:
        """
        获取模型的上下文Token限制
        
        Args:
            model: 模型名称
            
        Returns:
            上下文Token限制
        """
        provider = self._get_provider_from_model(model)
        if provider in self.model_token_limits:
            return self.model_token_limits[provider]["max_tokens"]
        return 4096  # 默认限制
    
    # 私有方法
    def _get_provider_from_model(self, model: str) -> str:
        """
        根据模型名称获取提供商
        
        Args:
            model: 模型名称
            
        Returns:
            提供商名称
        """
        for provider, info in self.model_token_limits.items():
            if model in info["models"]:
                return provider
        
        model_lower = model.lower()
        if "deepseek" in model_lower:
            return "deepseek"
        elif "glm" in model_lower or "zhipu" in model_lower:
            return "zhipu"
        elif "qwen" in model_lower:
            return "qwen"
        elif "moonshot" in model_lower or "kimi" in model_lower:
            return "kimi"
        elif "siliconflow" in model_lower:
            return "siliconflow"
        
        return "unknown"
    
    def _check_limits(self, provider: str) -> Dict[str, Any]:
        """
        检查是否接近限制
        
        Returns:
            状态信息字典
        """
        if provider not in self.usage_history:
            return {"status": "ok", "percentage": 0}
        
        usage = self.usage_history[provider]
        daily = usage.daily
        limit = usage.daily_limit
        percentage = (daily / limit) * 100 if limit > 0 else 0
        
        if percentage > 100:
            return {
                "status": "blocked",
                "percentage": percentage,
                "message": f"已达到每日限制 ({limit} tokens)"
            }
        elif percentage > 90:
            return {
                "status": "warning",
                "percentage": percentage,
                "message": f"使用量已达{percentage:.1f}%，接近每日限制"
            }
        elif percentage > 75:
            return {
                "status": "caution",
                "percentage": percentage,
                "message": f"使用量已达{percentage:.1f}%"
            }
        else:
            return {
                "status": "ok",
                "percentage": percentage,
                "message": f"使用量: {daily}/{limit} tokens"
            }
    
    # 事件处理器
    def _handle_token_used_event(self, event):
        """处理token使用事件"""
        data = event.data
        self.logger.debug(f"收到token使用事件: {data}")
        # 可以在这里添加额外的处理逻辑，如发送通知等
    
    def _handle_model_selected_event(self, event):
        """处理模型选择事件"""
        data = event.data
        self.logger.debug(f"收到模型选择事件: {data}")
        # 可以在这里更新默认模型或记录模型使用情况
    
    # 工具执行方法
    def _execute_estimate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行估算操作"""
        text = input_data.get("text", "")
        model = input_data.get("model", self.default_model)
        
        if not text:
            return {
                "success": False,
                "error": "需要提供text参数"
            }
        
        tokens = self.estimate_tokens(text, model)
        model_info = self.get_model_info(model)
        
        return {
            "success": True,
            "tokens": tokens,
            "text_length": len(text),
            "model": model,
            "model_info": model_info,
            "message": f"文本长度: {len(text)} 字符，估算Token: {tokens}"
        }
    
    def _execute_track(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行跟踪操作"""
        model = input_data.get("model", self.default_model)
        tokens_used = input_data.get("tokens_used", 0)
        operation_type = input_data.get("operation_type", "chat")
        
        if tokens_used <= 0:
            return {
                "success": False,
                "error": "tokens_used必须大于0"
            }
        
        result = self.track_usage(model, tokens_used, operation_type)
        
        return {
            "success": True,
            "tracking_result": result,
            "model": model,
            "tokens_used": tokens_used,
            "operation_type": operation_type
        }
    
    def _execute_get_info(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行获取信息操作"""
        model = input_data.get("model", self.default_model)
        model_info = self.get_model_info(model)
        
        if model_info:
            return {
                "success": True,
                "model": model,
                "model_info": model_info
            }
        else:
            return {
                "success": False,
                "error": f"未找到模型 {model} 的信息",
                "available_providers": list(self.model_token_limits.keys())
            }
    
    def _execute_get_stats(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行获取统计操作"""
        provider = input_data.get("provider")
        stats = self.get_usage_statistics(provider)
        
        return {
            "success": True,
            "provider": provider or "all",
            "statistics": stats,
            "total_tokens": self.get_total_tokens(),
            "daily_tokens": self.get_daily_tokens()
        }
    
    def _execute_reset_daily(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行重置每日使用量操作"""
        provider = input_data.get("provider")
        self.reset_daily_usage(provider)
        
        return {
            "success": True,
            "provider": provider or "all",
            "message": f"已重置 {provider or '所有提供商'} 的每日使用量"
        }


# 为向后兼容保留的快捷函数
def create_token_counter_plugin(context: PluginContext) -> TokenCounterPlugin:
    """创建Token计数器插件实例（工厂函数）"""
    return TokenCounterPlugin(context)