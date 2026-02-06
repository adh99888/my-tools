#!/usr/bin/env python3
"""
基础行动器模块
宪法依据：宪法第2条，技术执行法典第3.2条
"""

import os
import subprocess
from typing import Dict, Any

class BasicActionExecutor:
    """基础行动执行器"""
    
    def __init__(self) -> None:
        self.project_root = self._get_project_root()
        
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        # 假设模块位于 src/core/，项目根目录是 src 的父目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(current_dir))
        
    def execute(self, action_type: str, **kwargs: Any) -> Dict[str, Any]:
        """执行基础行动"""
        result = {"success": False, "action": action_type, "details": {}}
        
        try:
            if action_type == "read_file":
                result = self._action_read_file(**kwargs)
            elif action_type == "write_file":
                result = self._action_write_file(**kwargs)
            elif action_type == "run_command":
                result = self._action_run_command(**kwargs)
            elif action_type == "create_dir":
                result = self._action_create_dir(**kwargs)
            else:
                result["error"] = f"未知操作类型: {action_type}"
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    def _action_read_file(self, path: str) -> Dict[str, Any]:
        """读取文件（受限）"""
        abs_path = os.path.abspath(path)
        
        if not abs_path.startswith(self.project_root):
            return {"success": False, "error": "文件路径超出允许范围"}
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content[:1000]}  # 限制长度
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _action_write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件（受限）"""
        abs_path = os.path.abspath(path)
        
        if not abs_path.startswith(self.project_root):
            return {"success": False, "error": "文件路径超出允许范围"}
            
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _action_run_command(self, command: str) -> Dict[str, Any]:
        """运行命令（受限）"""
        dangerous = ["rm -rf", "format", "del /", "shutdown", "halt"]
        if any(d in command.lower() for d in dangerous):
            return {"success": False, "error": "命令被安全策略阻止"}
            
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30  # 30秒超时
            )
            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout[:500],
                "stderr": result.stderr[:500]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "命令执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _action_create_dir(self, path: str) -> Dict[str, Any]:
        """创建目录（受限）"""
        abs_path = os.path.abspath(path)
        
        if not abs_path.startswith(self.project_root):
            return {"success": False, "error": "目录路径超出允许范围"}
            
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "created": not os.path.exists(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}