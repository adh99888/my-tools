"""
插件加载器 - 插件发现和加载机制
"""

import importlib
import importlib.util
import inspect
import logging
import os
import pkgutil
import sys
import warnings
from pathlib import Path
from typing import (
    Any, Dict, Iterator, List, Optional, Set, Tuple, Type, Union
)

from .base import (
    PluginMetadata,
    PluginType,
    Plugin,
    plugin as plugin_decorator,
    create_plugin_metadata
)
from ..core.errors import PluginError
from ..core.logging import get_logger

logger = get_logger(__name__)


class PluginLoader:
    """
    插件加载器
    
    负责：
    1. 从搜索路径发现插件模块
    2. 加载插件类和元数据
    3. 检查插件依赖和兼容性
    4. 验证插件配置
    """
    
    def __init__(
        self,
        search_paths: List[str],
        container: Optional[Any] = None
    ):
        """
        初始化插件加载器
        
        Args:
            search_paths: 插件搜索路径列表
            container: 依赖注入容器（可选）
        """
        self.search_paths = self._normalize_search_paths(search_paths)
        self.container = container
        
        # 缓存已发现的插件
        self._discovered_plugins: Dict[str, PluginMetadata] = {}
        self._loaded_modules: Set[str] = set()
        
        logger.debug_struct(
            "插件加载器初始化",
            search_paths=self.search_paths,
            search_path_count=len(self.search_paths)
        )
    
    def _normalize_search_paths(self, search_paths: List[str]) -> List[Path]:
        """标准化搜索路径（展开~，转换为绝对路径）"""
        normalized = []
        for path_str in search_paths:
            try:
                # 展开用户目录
                expanded = os.path.expanduser(path_str)
                # 转换为绝对路径
                path = Path(expanded).resolve()
                normalized.append(path)
            except Exception as e:
                logger.warning_struct(
                    "插件搜索路径处理失败",
                    path=path_str,
                    error=str(e)
                )
        
        return normalized
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """
        发现所有可用插件
        
        Returns:
            插件元数据列表
        """
        logger.info("开始发现插件")
        
        # 清空缓存
        self._discovered_plugins.clear()
        
        for search_path in self.search_paths:
            self._discover_plugins_in_path(search_path)
        
        plugins = list(self._discovered_plugins.values())
        logger.info_struct("插件发现完成", plugin_count=len(plugins))
        
        return plugins
    
    def _discover_plugins_in_path(self, search_path: Path):
        """在指定路径中发现插件"""
        if not search_path.exists():
            logger.debug_struct(
                "插件搜索路径不存在",
                path=str(search_path)
            )
            return
        
        logger.debug_struct(
            "在路径中搜索插件",
            path=str(search_path)
        )
        
        # 遍历目录
        if search_path.is_dir():
            # 检查是否为Python包（包含__init__.py）
            if (search_path / "__init__.py").exists():
                self._discover_plugins_in_package(search_path)
            else:
                # 普通目录，遍历所有.py文件
                self._discover_plugins_in_directory(search_path)
        elif search_path.is_file() and search_path.suffix == '.py':
            # 单个Python文件
            self._discover_plugins_in_file(search_path)
    
    def _discover_plugins_in_directory(self, directory: Path):
        """在目录中发现插件"""
        for item in directory.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                self._discover_plugins_in_package(item)
            elif item.is_file() and item.suffix == '.py':
                self._discover_plugins_in_file(item)
    
    def _discover_plugins_in_package(self, package_path: Path):
        """在Python包中发现插件"""
        package_name = package_path.name
        
        # 将包路径添加到Python路径
        package_parent = package_path.parent
        if str(package_parent) not in sys.path:
            sys.path.insert(0, str(package_parent))
        
        try:
            # 导入包
            package = importlib.import_module(package_name)
            
            # 遍历包中的所有模块
            for _, module_name, is_pkg in pkgutil.iter_modules(
                package.__path__,
                package.__name__ + '.'
            ):
                if is_pkg:
                    # 递归处理子包
                    subpackage_path = package_path / module_name.split('.')[-1]
                    self._discover_plugins_in_package(subpackage_path)
                else:
                    # 导入模块并查找插件
                    try:
                        module = importlib.import_module(module_name)
                        self._find_plugins_in_module(module, module_name)
                    except Exception as e:
                        logger.warning_struct(
                            "插件模块导入失败",
                            module=module_name,
                            error=str(e)
                        )
        
        except Exception as e:
            logger.warning_struct(
                "插件包导入失败",
                package=package_name,
                error=str(e)
            )
    
    def _discover_plugins_in_file(self, file_path: Path):
        """在Python文件中发现插件"""
        module_name = file_path.stem
        parent_path = file_path.parent
        
        # 将父路径添加到Python路径
        if str(parent_path) not in sys.path:
            sys.path.insert(0, str(parent_path))
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning_struct(
                    "插件文件无法加载",
                    file=str(file_path)
                )
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            self._find_plugins_in_module(module, module_name)
            
        except Exception as e:
            logger.warning_struct(
                "插件文件导入失败",
                file=str(file_path),
                error=str(e)
            )
    
    def _find_plugins_in_module(self, module, module_name: str):
        """在模块中查找插件类"""
        for name, obj in inspect.getmembers(module):
            # 检查是否为类且继承自Plugin
            if (inspect.isclass(obj) and 
                issubclass(obj, Plugin) and 
                obj is not Plugin):
                
                # 检查是否有metadata属性
                if hasattr(obj, 'metadata'):
                    metadata = obj.metadata
                    
                    # 设置模块路径
                    if not metadata.module_path:
                        metadata.module_path = module_name
                    
                    # 设置插件类
                    metadata.plugin_class = obj
                    
                    # 验证元数据
                    self._validate_plugin_metadata(metadata)
                    
                    # 添加到发现列表
                    if metadata.name in self._discovered_plugins:
                        logger.warning_struct(
                            "重复插件名称",
                            name=metadata.name,
                            existing_module=self._discovered_plugins[metadata.name].module_path,
                            new_module=module_name
                        )
                    else:
                        self._discovered_plugins[metadata.name] = metadata
                        logger.debug_struct(
                            "发现插件",
                            name=metadata.name,
                            type=metadata.plugin_type.value,
                            version=metadata.version,
                            module=module_name
                        )
    
    def _validate_plugin_metadata(self, metadata: PluginMetadata):
        """验证插件元数据"""
        errors = []
        
        # 检查必要字段
        if not metadata.name or not metadata.name.strip():
            errors.append("插件名称不能为空")
        
        if not metadata.display_name or not metadata.display_name.strip():
            errors.append("插件显示名称不能为空")
        
        if not metadata.version or not metadata.version.strip():
            errors.append("插件版本不能为空")
        
        if not metadata.description or not metadata.description.strip():
            errors.append("插件描述不能为空")
        
        if not metadata.author or not metadata.author.strip():
            errors.append("插件作者不能为空")
        
        # 检查版本格式（简单验证）
        import re
        version_pattern = r'^\d+\.\d+\.\d+(?:[-\.][a-zA-Z0-9]+)*$'
        if not re.match(version_pattern, metadata.version):
            errors.append(f"版本号格式无效: {metadata.version}")
        
        # 检查应用版本兼容性
        try:
            from .. import __version__ as app_version
            # 简单版本比较（实际可能需要更复杂的逻辑）
            if metadata.min_app_version != "*":
                min_required = metadata.min_app_version
                # 这里可以添加版本比较逻辑
                pass
        except ImportError:
            pass
        
        if errors:
            error_msg = f"插件元数据验证失败: {metadata.name}"
            details = {"errors": errors, "metadata": metadata.name}
            raise PluginError(error_msg, metadata.name, details)
    
    def load_plugin(self, plugin_name: str) -> Type[Plugin]:
        """
        加载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件类
        """
        logger.debug_struct("加载插件", plugin_name=plugin_name)
        
        # 检查是否已发现
        if plugin_name not in self._discovered_plugins:
            # 重新发现
            self.discover_plugins()
            
        if plugin_name not in self._discovered_plugins:
            raise PluginError(
                f"插件未找到: {plugin_name}",
                plugin_name,
                {"discovered_plugins": list(self._discovered_plugins.keys())}
            )
        
        metadata = self._discovered_plugins[plugin_name]
        
        if metadata.plugin_class is None:
            raise PluginError(
                f"插件类未设置: {plugin_name}",
                plugin_name,
                {"metadata": metadata}
            )
        
        # 检查Python依赖
        self._check_python_dependencies(metadata)
        
        logger.debug_struct(
            "插件加载成功",
            name=plugin_name,
            class_name=metadata.plugin_class.__name__
        )
        
        return metadata.plugin_class
    
    def _check_python_dependencies(self, metadata: PluginMetadata):
        """检查Python包依赖"""
        if not metadata.python_dependencies:
            return
        
        missing_deps = []
        for dep in metadata.python_dependencies:
            try:
                # 尝试导入依赖
                importlib.import_module(dep.split('>=')[0].split('==')[0].strip())
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            logger.warning_struct(
                "插件依赖缺失",
                plugin=metadata.name,
                missing_deps=missing_deps
            )
            
            # 根据配置决定是否抛出错误
            # 暂时只记录警告
    
    def create_plugin_instance(
        self,
        plugin_name: str,
        context: Any
    ) -> Plugin:
        """
        创建插件实例
        
        Args:
            plugin_name: 插件名称
            context: 插件上下文
            
        Returns:
            插件实例
        """
        plugin_class = self.load_plugin(plugin_name)
        
        try:
            instance = plugin_class(context)
            logger.debug_struct(
                "插件实例创建成功",
                name=plugin_name,
                instance_id=id(instance)
            )
            return instance
        except Exception as e:
            raise PluginError(
                f"插件实例创建失败: {plugin_name}",
                plugin_name,
                {"error": str(e)}
            ) from e
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """获取插件元数据"""
        if plugin_name in self._discovered_plugins:
            return self._discovered_plugins[plugin_name]
        
        # 尝试重新发现
        self.discover_plugins()
        return self._discovered_plugins.get(plugin_name)
    
    def get_all_plugin_metadata(self) -> List[PluginMetadata]:
        """获取所有插件元数据"""
        if not self._discovered_plugins:
            self.discover_plugins()
        
        return list(self._discovered_plugins.values())
    
    def clear_cache(self):
        """清除加载器缓存"""
        self._discovered_plugins.clear()
        self._loaded_modules.clear()
        logger.debug_struct("插件加载器缓存已清除")


# 便捷函数
def create_plugin_loader(
    search_paths: Optional[List[str]] = None,
    container: Optional[Any] = None
) -> PluginLoader:
    """
    创建插件加载器
    
    Args:
        search_paths: 插件搜索路径（None时使用默认路径）
        container: 依赖注入容器
        
    Returns:
        插件加载器实例
    """
    if search_paths is None:
        # 默认搜索路径
        search_paths = [
            "./plugins",
            "~/.smallpangu/plugins"
        ]
    
    return PluginLoader(search_paths, container)


__all__ = [
    "PluginLoader",
    "create_plugin_loader"
]