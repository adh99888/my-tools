"""
国际化管理器

提供多语言支持，包括文本翻译、动态语言切换、语言包管理。
支持格式化字符串、复数形式、上下文相关翻译。
"""

import json
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import gettext
import locale

from ..core.events import EventBus
from ..config.manager import ConfigManager
from ..core.errors import UIError
from ..core.logging import get_logger

logger = get_logger(__name__)


class Language(str, Enum):
    """语言枚举（与配置模型保持一致）"""
    ZH_CN = "zh-CN"  # 简体中文
    EN_US = "en-US"  # 美式英语
    # 可以扩展更多语言


class TextDomain(str, Enum):
    """文本域枚举"""
    UI = "ui"          # UI界面文本
    ERROR = "error"    # 错误消息
    PLUGIN = "plugin"  # 插件文本
    SYSTEM = "system"  # 系统消息
    COMMON = "common"  # 通用文本


@dataclass
class Translation:
    """翻译数据类"""
    key: str
    text: str
    domain: TextDomain = TextDomain.COMMON
    context: Optional[str] = None
    plural_key: Optional[str] = None
    plural_texts: Optional[List[str]] = None
    
    def __post_init__(self):
        """数据验证"""
        if not self.key:
            raise ValueError("翻译键不能为空")
        if not self.text:
            raise ValueError("翻译文本不能为空")


class I18nManager:
    """
    国际化管理器
    
    负责：
    1. 管理多语言文本
    2. 动态语言切换
    3. 语言包加载和管理
    4. 格式化字符串翻译
    5. 复数形式支持
    """
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        """
        初始化国际化管理器
        
        Args:
            config_manager: 配置管理器
            event_bus: 事件总线
        """
        self._config_manager = config_manager
        self._event_bus = event_bus
        
        # 语言配置
        self._ui_config = config_manager.config.ui
        self._current_language = Language(self._ui_config.language)
        self._fallback_language = Language.EN_US
        
        # 翻译数据存储
        self._translations: Dict[str, Dict[str, Translation]] = {}  # language -> {key: translation}
        self._text_domains: Dict[TextDomain, Dict[str, Dict[str, Translation]]] = {}  # domain -> {language: {key: translation}}
        
        # 语言监听器（用于实时更新UI文本）
        self._language_listeners: List[Callable] = []
        
        # Gettext翻译对象
        self._gettext_translations: Dict[str, gettext.GNUTranslations] = {}
        
        # 语言包路径
        self._language_dir = Path("i18n")  # 默认语言包目录
        
        logger.debug_struct("国际化管理器初始化", current_language=self._current_language)
    
    def initialize(self) -> None:
        """
        初始化国际化管理器
        """
        logger.debug("初始化国际化管理器")
        
        try:
            # 1. 设置系统语言环境
            self._setup_locale()
            
            # 2. 加载内置翻译
            self._load_builtin_translations()
            
            # 3. 加载语言包文件
            self._load_language_files()
            
            # 4. 初始化Gettext
            self._setup_gettext()
            
            # 5. 订阅语言相关事件
            self._subscribe_events()
            
            logger.info_struct("国际化管理器初始化完成", language=self._current_language)
            
        except Exception as e:
            logger.error("国际化管理器初始化失败", exc_info=True)
            raise UIError(f"国际化管理器初始化失败: {e}")
    
    def _setup_locale(self) -> None:
        """设置系统语言环境"""
        try:
            # 根据当前语言设置locale
            lang_code = self._current_language.value.replace("-", "_")
            locale.setlocale(locale.LC_ALL, f"{lang_code}.UTF-8")
            logger.debug_struct("语言环境设置", locale=lang_code)
        except locale.Error as e:
            logger.warning_struct("语言环境设置失败，使用默认", error=str(e))
            # 继续使用默认locale
    
    def _load_builtin_translations(self) -> None:
        """加载内置翻译"""
        logger.debug("加载内置翻译")
        
        # 初始化各文本域的存储结构
        for domain in TextDomain:
            if domain not in self._text_domains:
                self._text_domains[domain] = {}
        
        # 加载内置中文翻译
        self._load_builtin_language(Language.ZH_CN)
        
        # 加载内置英文翻译
        self._load_builtin_language(Language.EN_US)
        
        logger.debug_struct("内置翻译加载完成", language_count=len(self._translations))
    
    def _load_builtin_language(self, language: Language) -> None:
        """
        加载指定语言的内置翻译
        
        Args:
            language: 语言
        """
        if language == Language.ZH_CN:
            translations = self._get_builtin_zh_cn_translations()
        elif language == Language.EN_US:
            translations = self._get_builtin_en_us_translations()
        else:
            translations = []
        
        # 存储翻译
        self._translations[language.value] = {}
        for domain in TextDomain:
            self._text_domains[domain][language.value] = {}
        
        for trans in translations:
            self._add_translation(trans, language)
    
    def _get_builtin_zh_cn_translations(self) -> List[Translation]:
        """获取内置中文翻译"""
        return [
            # UI文本域
            Translation(key="app.title", text="小盘古 AI 助手", domain=TextDomain.UI),
            Translation(key="sidebar.chat", text="聊天", domain=TextDomain.UI),
            Translation(key="sidebar.plugins", text="插件", domain=TextDomain.UI),
            Translation(key="sidebar.config", text="配置", domain=TextDomain.UI),
            Translation(key="sidebar.monitor", text="监控", domain=TextDomain.UI),
            Translation(key="sidebar.help", text="帮助", domain=TextDomain.UI),
            Translation(key="sidebar.settings", text="设置", domain=TextDomain.UI),
            Translation(key="status.ready", text="就绪", domain=TextDomain.UI),
            Translation(key="button.send", text="发送", domain=TextDomain.UI),
            Translation(key="button.cancel", text="取消", domain=TextDomain.UI),
            Translation(key="button.save", text="保存", domain=TextDomain.UI),
            Translation(key="button.reset", text="重置", domain=TextDomain.UI),
            Translation(key="label.username", text="用户名", domain=TextDomain.UI),
            Translation(key="label.password", text="密码", domain=TextDomain.UI),
            Translation(key="label.api_key", text="API密钥", domain=TextDomain.UI),
            Translation(key="placeholder.input_message", text="输入消息...", domain=TextDomain.UI),
            Translation(key="placeholder.search", text="搜索...", domain=TextDomain.UI),
            
            # 错误文本域
            Translation(key="error.network", text="网络连接失败", domain=TextDomain.ERROR),
            Translation(key="error.auth", text="认证失败", domain=TextDomain.ERROR),
            Translation(key="error.permission", text="权限不足", domain=TextDomain.ERROR),
            Translation(key="error.not_found", text="未找到", domain=TextDomain.ERROR),
            Translation(key="error.timeout", text="请求超时", domain=TextDomain.ERROR),
            Translation(key="error.unknown", text="未知错误", domain=TextDomain.ERROR),
            
            # 系统文本域
            Translation(key="system.starting", text="系统启动中...", domain=TextDomain.SYSTEM),
            Translation(key="system.stopping", text="系统关闭中...", domain=TextDomain.SYSTEM),
            Translation(key="system.initialized", text="系统初始化完成", domain=TextDomain.SYSTEM),
            Translation(key="system.plugin_loaded", text="插件加载完成", domain=TextDomain.SYSTEM),
            
            # 通用文本域
            Translation(key="common.yes", text="是", domain=TextDomain.COMMON),
            Translation(key="common.no", text="否", domain=TextDomain.COMMON),
            Translation(key="common.ok", text="确定", domain=TextDomain.COMMON),
            Translation(key="common.close", text="关闭", domain=TextDomain.COMMON),
            Translation(key="common.back", text="返回", domain=TextDomain.COMMON),
            Translation(key="common.next", text="下一步", domain=TextDomain.COMMON),
            Translation(key="common.previous", text="上一步", domain=TextDomain.COMMON),
            Translation(key="common.loading", text="加载中...", domain=TextDomain.COMMON),
            Translation(key="common.success", text="成功", domain=TextDomain.COMMON),
            Translation(key="common.failed", text="失败", domain=TextDomain.COMMON),
        ]
    
    def _get_builtin_en_us_translations(self) -> List[Translation]:
        """获取内置英文翻译"""
        return [
            # UI domain
            Translation(key="app.title", text="SmallPangu AI Assistant", domain=TextDomain.UI),
            Translation(key="sidebar.chat", text="Chat", domain=TextDomain.UI),
            Translation(key="sidebar.plugins", text="Plugins", domain=TextDomain.UI),
            Translation(key="sidebar.config", text="Config", domain=TextDomain.UI),
            Translation(key="sidebar.monitor", text="Monitor", domain=TextDomain.UI),
            Translation(key="sidebar.help", text="Help", domain=TextDomain.UI),
            Translation(key="sidebar.settings", text="Settings", domain=TextDomain.UI),
            Translation(key="status.ready", text="Ready", domain=TextDomain.UI),
            Translation(key="button.send", text="Send", domain=TextDomain.UI),
            Translation(key="button.cancel", text="Cancel", domain=TextDomain.UI),
            Translation(key="button.save", text="Save", domain=TextDomain.UI),
            Translation(key="button.reset", text="Reset", domain=TextDomain.UI),
            Translation(key="label.username", text="Username", domain=TextDomain.UI),
            Translation(key="label.password", text="Password", domain=TextDomain.UI),
            Translation(key="label.api_key", text="API Key", domain=TextDomain.UI),
            Translation(key="placeholder.input_message", text="Type a message...", domain=TextDomain.UI),
            Translation(key="placeholder.search", text="Search...", domain=TextDomain.UI),
            
            # Error domain
            Translation(key="error.network", text="Network connection failed", domain=TextDomain.ERROR),
            Translation(key="error.auth", text="Authentication failed", domain=TextDomain.ERROR),
            Translation(key="error.permission", text="Insufficient permissions", domain=TextDomain.ERROR),
            Translation(key="error.not_found", text="Not found", domain=TextDomain.ERROR),
            Translation(key="error.timeout", text="Request timeout", domain=TextDomain.ERROR),
            Translation(key="error.unknown", text="Unknown error", domain=TextDomain.ERROR),
            
            # System domain
            Translation(key="system.starting", text="System starting...", domain=TextDomain.SYSTEM),
            Translation(key="system.stopping", text="System stopping...", domain=TextDomain.SYSTEM),
            Translation(key="system.initialized", text="System initialized", domain=TextDomain.SYSTEM),
            Translation(key="system.plugin_loaded", text="Plugin loaded", domain=TextDomain.SYSTEM),
            
            # Common domain
            Translation(key="common.yes", text="Yes", domain=TextDomain.COMMON),
            Translation(key="common.no", text="No", domain=TextDomain.COMMON),
            Translation(key="common.ok", text="OK", domain=TextDomain.COMMON),
            Translation(key="common.close", text="Close", domain=TextDomain.COMMON),
            Translation(key="common.back", text="Back", domain=TextDomain.COMMON),
            Translation(key="common.next", text="Next", domain=TextDomain.COMMON),
            Translation(key="common.previous", text="Previous", domain=TextDomain.COMMON),
            Translation(key="common.loading", text="Loading...", domain=TextDomain.COMMON),
            Translation(key="common.success", text="Success", domain=TextDomain.COMMON),
            Translation(key="common.failed", text="Failed", domain=TextDomain.COMMON),
        ]
    
    def _add_translation(self, translation: Translation, language: Language) -> None:
        """
        添加翻译
        
        Args:
            translation: 翻译对象
            language: 语言
        """
        # 存储到全局翻译表
        lang_key = language.value
        trans_key = self._make_translation_key(translation.domain, translation.key, translation.context)
        self._translations[lang_key][trans_key] = translation
        
        # 存储到文本域翻译表
        if translation.domain not in self._text_domains:
            self._text_domains[translation.domain] = {}
        
        if lang_key not in self._text_domains[translation.domain]:
            self._text_domains[translation.domain][lang_key] = {}
        
        self._text_domains[translation.domain][lang_key][trans_key] = translation
    
    def _make_translation_key(self, domain: TextDomain, key: str, context: Optional[str] = None) -> str:
        """
        创建翻译键
        
        Args:
            domain: 文本域
            key: 键名
            context: 上下文
            
        Returns:
            翻译键
        """
        if context:
            return f"{domain.value}:{context}:{key}"
        return f"{domain.value}:{key}"
    
    def _load_language_files(self) -> None:
        """加载语言包文件"""
        logger.debug("加载语言包文件")
        
        # 检查语言包目录是否存在
        if not self._language_dir.exists():
            logger.debug("语言包目录不存在，跳过文件加载")
            return
        
        # 遍历语言包目录
        for lang_file in self._language_dir.glob("*.json"):
            try:
                language_code = lang_file.stem  # 文件名作为语言代码
                self._load_language_file(lang_file, language_code)
            except Exception as e:
                logger.warning_struct("语言文件加载失败", file=str(lang_file), error=str(e))
    
    def _load_language_file(self, file_path: Path, language_code: str) -> None:
        """
        加载语言文件
        
        Args:
            file_path: 文件路径
            language_code: 语言代码
        """
        logger.debug_struct("加载语言文件", file=str(file_path), language=language_code)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析JSON数据
        for domain_str, domain_data in data.items():
            try:
                domain = TextDomain(domain_str)
            except ValueError:
                logger.warning_struct("未知文本域", domain=domain_str, file=str(file_path))
                continue
            
            for key, trans_data in domain_data.items():
                if isinstance(trans_data, str):
                    # 简单翻译
                    translation = Translation(
                        key=key,
                        text=trans_data,
                        domain=domain
                    )
                    self._add_translation(translation, Language(language_code))
                elif isinstance(trans_data, dict):
                    # 复杂翻译（带上下文、复数形式等）
                    text = trans_data.get("text", "")
                    context = trans_data.get("context")
                    plural_key = trans_data.get("plural_key")
                    plural_texts = trans_data.get("plural_texts")
                    
                    translation = Translation(
                        key=key,
                        text=text,
                        domain=domain,
                        context=context,
                        plural_key=plural_key,
                        plural_texts=plural_texts
                    )
                    self._add_translation(translation, Language(language_code))
        
        logger.debug_struct("语言文件加载完成", file=str(file_path), translation_count=len(data))
    
    def _setup_gettext(self) -> None:
        """设置Gettext翻译"""
        logger.debug("设置Gettext翻译")
        
        # 如果语言包目录存在，尝试加载Gettext翻译文件
        gettext_dir = self._language_dir / "gettext"
        if gettext_dir.exists():
            for lang_dir in gettext_dir.iterdir():
                if lang_dir.is_dir():
                    lang_code = lang_dir.name
                    mo_file = lang_dir / "LC_MESSAGES" / "smallpangu.mo"
                    
                    if mo_file.exists():
                        try:
                            with open(mo_file, 'rb') as f:
                                trans = gettext.GNUTranslations(f)
                                self._gettext_translations[lang_code] = trans
                                logger.debug_struct("Gettext翻译加载", language=lang_code)
                        except Exception as e:
                            logger.warning_struct("Gettext翻译加载失败", language=lang_code, error=str(e))
    
    def _subscribe_events(self) -> None:
        """订阅语言相关事件"""
        logger.debug("订阅语言相关事件")
        
        # 语言切换请求
        self._event_bus.subscribe("language.change_request", self._handle_language_change_request)
        
        # 配置更新
        self._event_bus.subscribe("config.updated", self._handle_config_updated)
        
        # 翻译更新请求
        self._event_bus.subscribe("translation.update_request", self._handle_translation_update_request)
        
        logger.debug("语言事件订阅完成")
    
    def _handle_language_change_request(self, event) -> None:
        """处理语言切换请求"""
        new_language = event.data.get("language")
        if new_language:
            logger.debug_struct("收到语言切换请求", new_language=new_language)
            self.set_language(new_language)
    
    def _handle_config_updated(self, event) -> None:
        """处理配置更新事件"""
        config_data = event.data.get("config", {})
        ui_config = config_data.get("ui", {})
        
        if "language" in ui_config:
            new_language = ui_config["language"]
            if new_language != self._current_language.value:
                logger.debug_struct("配置更新触发语言切换", new_language=new_language)
                self.set_language(new_language)
    
    def _handle_translation_update_request(self, event) -> None:
        """处理翻译更新请求"""
        translations = event.data.get("translations", [])
        domain = event.data.get("domain", TextDomain.COMMON)
        language = event.data.get("language", self._current_language.value)
        
        if translations:
            logger.debug_struct("收到翻译更新请求", domain=domain, language=language, count=len(translations))
            self.update_translations(translutions, TextDomain(domain), Language(language))
    
    def _notify_language_listeners(self) -> None:
        """通知语言监听器"""
        for listener in self._language_listeners:
            try:
                listener(self._current_language)
            except Exception as e:
                logger.warning_struct("语言监听器通知失败", error=str(e))
    
    # 公共API
    def set_language(self, language: Union[str, Language]) -> bool:
        """
        设置当前语言
        
        Args:
            language: 语言代码或Language枚举
            
        Returns:
            是否成功设置
        """
        if isinstance(language, str):
            try:
                language = Language(language)
            except ValueError:
                logger.warning_struct("无效的语言代码", language=language)
                return False
        
        if language not in [Language.ZH_CN, Language.EN_US]:
            logger.warning_struct("不支持的语言", language=language)
            return False
        
        try:
            # 更新当前语言
            old_language = self._current_language
            self._current_language = language
            
            # 更新配置
            self._ui_config.language = language.value
            self._config_manager.update_config({"ui": {"language": language.value}})
            
            # 更新locale
            self._setup_locale()
            
            # 通知监听器
            self._notify_language_listeners()
            
            # 发布语言已更改事件
            self._event_bus.publish("language.changed", {
                "language": language.value,
                "old_language": old_language.value,
                "language_name": self.get_language_name(language)
            })
            
            logger.info_struct("语言切换完成", old_language=old_language, new_language=language)
            return True
            
        except Exception as e:
            logger.error_struct("语言切换失败", language=language, error=str(e))
            return False
    
    def get(self, key: str, domain: TextDomain = TextDomain.COMMON, 
            context: Optional[str] = None, **kwargs) -> str:
        """
        获取翻译文本
        
        Args:
            key: 翻译键
            domain: 文本域
            context: 上下文
            **kwargs: 格式化参数
            
        Returns:
            翻译文本，如果未找到则返回键本身
        """
        return self.translate(key, domain, context, **kwargs)
    
    def translate(self, key: str, domain: TextDomain = TextDomain.COMMON,
                  context: Optional[str] = None, **kwargs) -> str:
        """
        翻译文本
        
        Args:
            key: 翻译键
            domain: 文本域
            context: 上下文
            **kwargs: 格式化参数
            
        Returns:
            翻译文本，如果未找到则返回键本身
        """
        # 尝试获取当前语言的翻译
        trans_key = self._make_translation_key(domain, key, context)
        translation = self._get_translation(trans_key, self._current_language)
        
        if translation:
            text = translation.text
        else:
            # 回退到备用语言
            translation = self._get_translation(trans_key, self._fallback_language)
            if translation:
                text = translation.text
            else:
                # 都未找到，返回键本身
                logger.debug_struct("翻译未找到", key=key, domain=domain, context=context)
                text = key
        
        # 格式化文本
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning_struct("文本格式化失败", text=text, kwargs=kwargs, error=str(e))
        
        return text
    
    def translate_plural(self, key: str, count: int, domain: TextDomain = TextDomain.COMMON,
                         context: Optional[str] = None, **kwargs) -> str:
        """
        翻译复数形式文本
        
        Args:
            key: 翻译键
            count: 数量
            domain: 文本域
            context: 上下文
            **kwargs: 格式化参数
            
        Returns:
            翻译文本
        """
        # 尝试获取当前语言的翻译
        trans_key = self._make_translation_key(domain, key, context)
        translation = self._get_translation(trans_key, self._current_language)
        
        if translation and translation.plural_texts:
            # 根据数量选择复数形式
            # 这里使用简单的规则：中文通常没有复数形式，英文根据count选择
            if self._current_language == Language.EN_US:
                if count == 1:
                    text_index = 0
                else:
                    text_index = 1 if len(translation.plural_texts) > 1 else 0
            else:
                # 中文和其他语言：通常使用单数形式或第一个复数形式
                text_index = 0
            
            if text_index < len(translation.plural_texts):
                text = translation.plural_texts[text_index]
            else:
                text = translation.text
        else:
            # 没有复数形式，使用普通翻译
            text = self.translate(key, domain, context)
        
        # 格式化文本（包含count参数）
        format_kwargs = {"count": count, **kwargs}
        if format_kwargs:
            try:
                text = text.format(**format_kwargs)
            except (KeyError, ValueError) as e:
                logger.warning_struct("复数文本格式化失败", text=text, kwargs=format_kwargs, error=str(e))
        
        return text
    
    def _get_translation(self, trans_key: str, language: Language) -> Optional[Translation]:
        """
        获取翻译
        
        Args:
            trans_key: 翻译键
            language: 语言
            
        Returns:
            翻译对象，如果未找到则返回None
        """
        lang_key = language.value
        
        # 首先在全局翻译表中查找
        if lang_key in self._translations and trans_key in self._translations[lang_key]:
            return self._translations[lang_key][trans_key]
        
        # 然后在文本域翻译表中查找
        for domain in TextDomain:
            if (domain.value in self._text_domains and 
                lang_key in self._text_domains[domain.value] and
                trans_key in self._text_domains[domain.value][lang_key]):
                return self._text_domains[domain.value][lang_key][trans_key]
        
        return None
    
    def update_translations(self, translations: List[Translation], 
                           domain: TextDomain, language: Language) -> None:
        """
        更新翻译
        
        Args:
            translations: 翻译列表
            domain: 文本域
            language: 语言
        """
        logger.debug_struct("更新翻译", domain=domain, language=language, count=len(translations))
        
        for translation in translations:
            # 确保翻译的文本域正确
            if translation.domain != domain:
                translation.domain = domain
            
            self._add_translation(translation, language)
        
        # 如果更新的是当前语言，通知监听器
        if language == self._current_language:
            self._notify_language_listeners()
        
        # 发布翻译更新事件
        self._event_bus.publish("translation.updated", {
            "domain": domain.value,
            "language": language.value,
            "translation_count": len(translations)
        })
    
    def register_language_listener(self, listener: Callable) -> None:
        """
        注册语言监听器
        
        Args:
            listener: 监听器函数，接收语言作为参数
        """
        if listener not in self._language_listeners:
            self._language_listeners.append(listener)
            logger.debug_struct("语言监听器注册", listener_count=len(self._language_listeners))
    
    def unregister_language_listener(self, listener: Callable) -> bool:
        """
        取消注册语言监听器
        
        Args:
            listener: 监听器函数
            
        Returns:
            是否成功取消注册
        """
        if listener in self._language_listeners:
            self._language_listeners.remove(listener)
            logger.debug_struct("语言监听器取消注册", listener_count=len(self._language_listeners))
            return True
        return False
    
    def get_available_languages(self) -> List[Language]:
        """获取可用语言列表"""
        return list(Language)
    
    def get_language_name(self, language: Optional[Language] = None) -> str:
        """
        获取语言名称
        
        Args:
            language: 语言（默认为当前语言）
            
        Returns:
            语言名称
        """
        if language is None:
            language = self._current_language
        
        language_names = {
            Language.ZH_CN: "简体中文",
            Language.EN_US: "English (US)"
        }
        
        return language_names.get(language, language.value)
    
    def get_language_info(self, language: Language) -> Dict[str, Any]:
        """
        获取语言信息
        
        Args:
            language: 语言
            
        Returns:
            语言信息字典
        """
        lang_key = language.value
        
        # 统计翻译数量
        translation_count = 0
        if lang_key in self._translations:
            translation_count = len(self._translations[lang_key])
        
        domain_counts = {}
        for domain in TextDomain:
            if (domain.value in self._text_domains and 
                lang_key in self._text_domains[domain.value]):
                domain_counts[domain.value] = len(self._text_domains[domain.value][lang_key])
        
        return {
            "code": language.value,
            "name": self.get_language_name(language),
            "translation_count": translation_count,
            "domain_counts": domain_counts,
            "has_gettext": lang_key in self._gettext_translations
        }
    
    def cycle_language(self) -> Language:
        """
        循环切换语言
        
        Returns:
            新的语言
        """
        languages = list(Language)
        current_index = languages.index(self._current_language)
        
        next_index = (current_index + 1) % len(languages)
        next_language = languages[next_index]
        
        self.set_language(next_language)
        return next_language
    
    def shutdown(self) -> None:
        """关闭国际化管理器"""
        logger.debug("关闭国际化管理器")
        
        # 清理监听器
        self._language_listeners.clear()
        
        # 清理翻译数据
        self._translations.clear()
        self._text_domains.clear()
        self._gettext_translations.clear()
        
        logger.debug("国际化管理器已关闭")
    
    # 属性访问
    @property
    def current_language(self) -> Language:
        """获取当前语言"""
        return self._current_language
    
    @property
    def fallback_language(self) -> Language:
        """获取备用语言"""
        return self._fallback_language
    
    @property
    def language_count(self) -> int:
        """获取支持的语言数量"""
        return len(self._translations)
    
    @property
    def translation_count(self) -> int:
        """获取总翻译数量"""
        total = 0
        for lang_trans in self._translations.values():
            total += len(lang_trans)
        return total
    
    @property
    def listener_count(self) -> int:
        """获取监听器数量"""
        return len(self._language_listeners)
    
    def get_status(self) -> Dict[str, Any]:
        """获取国际化管理器状态"""
        return {
            "current_language": self._current_language.value,
            "language_name": self.get_language_name(),
            "available_languages": [lang.value for lang in self.get_available_languages()],
            "translation_count": self.translation_count,
            "language_count": self.language_count,
            "listener_count": self.listener_count,
            "has_language_files": self._language_dir.exists()
        }


# 便捷函数
def get_i18n_manager(
    config_manager: ConfigManager,
    event_bus: EventBus
) -> I18nManager:
    """创建国际化管理器实例"""
    return I18nManager(config_manager, event_bus)


def t(key: str, domain: TextDomain = TextDomain.COMMON, 
      context: Optional[str] = None, **kwargs) -> str:
    """
    翻译快捷函数（全局函数）
    
    Args:
        key: 翻译键
        domain: 文本域
        context: 上下文
        **kwargs: 格式化参数
        
    Returns:
        翻译文本
    """
    # 注意：这个函数需要全局的I18nManager实例
    # 目前返回键本身，实际使用时需要设置全局管理器
    logger.warning_struct("全局翻译函数未初始化，返回键本身", key=key)
    return key


def pt(key: str, count: int, domain: TextDomain = TextDomain.COMMON,
       context: Optional[str] = None, **kwargs) -> str:
    """
    复数翻译快捷函数（全局函数）
    
    Args:
        key: 翻译键
        count: 数量
        domain: 文本域
        context: 上下文
        **kwargs: 格式化参数
        
    Returns:
        翻译文本
    """
    # 注意：这个函数需要全局的I18nManager实例
    logger.warning_struct("全局复数翻译函数未初始化，返回键本身", key=key, count=count)
    return key


# 导出
__all__ = [
    "Language",
    "TextDomain",
    "Translation",
    "I18nManager",
    "get_i18n_manager",
    "t",
    "pt"
]