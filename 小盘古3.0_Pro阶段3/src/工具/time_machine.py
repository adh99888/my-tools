#!/usr/bin/env python3
"""
时光机快照模块
宪法依据：生存保障法案第4条，技术执行法典第5.3条
"""

import json
import os
import shutil
import hashlib
import zipfile
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

@dataclass
class SnapshotMetadata:
    """快照元数据"""
    snapshot_id: str
    timestamp: str
    description: str
    protocol_level: str
    operation_id: Optional[str] = None
    trust_score_before: float = 50.0
    trust_score_after: Optional[float] = None
    system_version: str = "seed-v0.1.1"
    checksums: Dict[str, str] = field(default_factory=dict)
    included_paths: List[str] = field(default_factory=list)
    total_size_bytes: int = 0
    is_valid: bool = True

@dataclass
class SnapshotInfo:
    """快照信息"""
    snapshot_id: str
    timestamp: str
    description: str
    protocol_level: str
    size_bytes: int
    is_valid: bool

class TimeMachine:
    """时光机快照管理器"""
    
    def __init__(self, backup_dir: str = "backups", max_snapshots: int = 50):
        """
        初始化时光机
        
        Args:
            backup_dir: 备份目录
            max_snapshots: 最大快照数量
        """
        self.backup_dir = backup_dir
        self.max_snapshots = max_snapshots
        
        # 确保备份目录存在
        os.makedirs(backup_dir, exist_ok=True)
        
        # 快照元数据目录
        self.metadata_dir = os.path.join(backup_dir, "metadata")
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # 快照数据目录
        self.snapshot_dir = os.path.join(backup_dir, "snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
    def create_snapshot(self, description: str, protocol_level: str = "L3",
                       operation_id: Optional[str] = None,
                       trust_score: float = 50.0,
                       include_paths: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        创建系统快照
        
        Args:
            description: 快照描述
            protocol_level: 协议级别
            operation_id: 操作ID
            trust_score: 当前信任分
            include_paths: 包含的路径列表，None表示包含整个项目
            
        Returns:
            (成功与否, 快照ID或错误信息)
        """
        try:
            # 生成快照ID
            snapshot_id = self._generate_snapshot_id(description)
            
            # 确定要包含的路径
            if include_paths is None:
                include_paths = self._get_default_include_paths()
                
            # 创建快照目录
            snapshot_path = os.path.join(self.snapshot_dir, snapshot_id)
            os.makedirs(snapshot_path, exist_ok=True)
            
            # 复制文件
            total_size = 0
            checksums = {}
            
            for path in include_paths:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        size, checksum = self._copy_file_to_snapshot(path, snapshot_path)
                        total_size += size
                        checksums[path] = checksum
                    elif os.path.isdir(path):
                        size, dir_checksums = self._copy_dir_to_snapshot(path, snapshot_path)
                        total_size += size
                        checksums.update(dir_checksums)
                        
            # 创建元数据
            metadata = SnapshotMetadata(
                snapshot_id=snapshot_id,
                timestamp=datetime.now().isoformat(),
                description=description,
                protocol_level=protocol_level,
                operation_id=operation_id,
                trust_score_before=trust_score,
                system_version=self._get_system_version(),
                checksums=checksums,
                included_paths=include_paths,
                total_size_bytes=total_size,
                is_valid=True
            )
            
            # 保存元数据
            metadata_file = os.path.join(self.metadata_dir, f"{snapshot_id}.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
                
            # 更新最新快照引用
            self._update_latest_snapshot(snapshot_id, metadata)
            
            # 清理旧快照
            self._cleanup_old_snapshots()
            
            return True, snapshot_id
            
        except Exception as e:
            return False, f"创建快照失败: {str(e)}"
            
    def restore_snapshot(self, snapshot_id: str, target_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        恢复快照
        
        Args:
            snapshot_id: 快照ID
            target_dir: 目标目录，None表示恢复到原始位置
            
        Returns:
            (成功与否, 结果信息)
        """
        try:
            # 检查快照是否存在
            metadata = self.get_snapshot_metadata(snapshot_id)
            if not metadata:
                return False, f"快照不存在: {snapshot_id}"
                
            if not metadata.is_valid:
                return False, f"快照无效: {snapshot_id}"
                
            # 快照路径
            snapshot_path = os.path.join(self.snapshot_dir, snapshot_id)
            
            # 如果未指定目标目录，使用原始路径
            if target_dir is None:
                # 从元数据中获取原始路径
                for path in metadata.included_paths:
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            # 恢复文件
                            snapshot_file = os.path.join(snapshot_path, self._get_relative_path(path))
                            if os.path.exists(snapshot_file):
                                shutil.copy2(snapshot_file, path)
                        elif os.path.isdir(path):
                            # 恢复目录
                            snapshot_subdir = os.path.join(snapshot_path, self._get_relative_path(path))
                            if os.path.exists(snapshot_subdir):
                                if os.path.exists(path):
                                    shutil.rmtree(path)
                                shutil.copytree(snapshot_subdir, path)
            else:
                # 恢复到指定目录
                target_path = target_dir
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(snapshot_path, target_path)
                
            return True, f"快照 {snapshot_id} 恢复成功"
            
        except Exception as e:
            return False, f"恢复快照失败: {str(e)}"
            
    def verify_snapshot(self, snapshot_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证快照完整性
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            (是否有效, 消息, 详细信息)
        """
        try:
            metadata = self.get_snapshot_metadata(snapshot_id)
            if not metadata:
                return False, "快照不存在", {}
                
            snapshot_path = os.path.join(self.snapshot_dir, snapshot_id)
            
            if not os.path.exists(snapshot_path):
                return False, "快照数据不存在", {}
                
            # 验证文件完整性
            missing_files = []
            checksum_mismatch = []
            
            for path, expected_checksum in metadata.checksums.items():
                relative_path = self._get_relative_path(path)
                snapshot_file = os.path.join(snapshot_path, relative_path)
                
                if not os.path.exists(snapshot_file):
                    missing_files.append(path)
                    continue
                    
                actual_checksum = self._calculate_file_checksum(snapshot_file)
                if actual_checksum != expected_checksum:
                    checksum_mismatch.append(path)
                    
            is_valid = len(missing_files) == 0 and len(checksum_mismatch) == 0
            
            details = {
                "missing_files": missing_files,
                "checksum_mismatch": checksum_mismatch,
                "total_files": len(metadata.checksums),
                "snapshot_size": metadata.total_size_bytes
            }
            
            if is_valid:
                return True, "快照完整有效", details
            else:
                return False, "快照不完整", details
                
        except Exception as e:
            return False, f"验证失败: {str(e)}", {}
            
    def get_snapshot_metadata(self, snapshot_id: str) -> Optional[SnapshotMetadata]:
        """获取快照元数据"""
        metadata_file = os.path.join(self.metadata_dir, f"{snapshot_id}.json")
        
        try:
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                return SnapshotMetadata(**data)
        except Exception:
            pass
            
        return None
        
    def list_snapshots(self) -> List[SnapshotInfo]:
        """列出所有快照"""
        snapshots = []
        
        for filename in os.listdir(self.metadata_dir):
            if filename.endswith(".json"):
                snapshot_id = filename[:-5]
                metadata = self.get_snapshot_metadata(snapshot_id)
                
                if metadata:
                    info = SnapshotInfo(
                        snapshot_id=snapshot_id,
                        timestamp=metadata.timestamp,
                        description=metadata.description,
                        protocol_level=metadata.protocol_level,
                        size_bytes=metadata.total_size_bytes,
                        is_valid=metadata.is_valid
                    )
                    snapshots.append(info)
                    
        # 按时间倒序排序
        snapshots.sort(key=lambda x: x.timestamp, reverse=True)
        return snapshots
        
    def delete_snapshot(self, snapshot_id: str) -> Tuple[bool, str]:
        """删除快照"""
        try:
            # 删除元数据
            metadata_file = os.path.join(self.metadata_dir, f"{snapshot_id}.json")
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
                
            # 删除快照数据
            snapshot_path = os.path.join(self.snapshot_dir, snapshot_id)
            if os.path.exists(snapshot_path):
                shutil.rmtree(snapshot_path)
                
            return True, f"快照 {snapshot_id} 已删除"
        except Exception as e:
            return False, f"删除快照失败: {str(e)}"
            
    # ========== 私有方法 ==========
    
    def _generate_snapshot_id(self, description: str) -> str:
        """生成快照ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desc_hash = hashlib.md5(description.encode()).hexdigest()[:8]
        return f"snapshot_{timestamp}_{desc_hash}"
        
    def _get_default_include_paths(self) -> List[str]:
        """获取默认包含的路径"""
        project_root = self._get_project_root()
        
        include_paths = [
            os.path.join(project_root, "src"),
            os.path.join(project_root, "constitution"),
            os.path.join(project_root, "protocols"),
            os.path.join(project_root, "tests"),
            os.path.join(project_root, "requirements.txt"),
            os.path.join(project_root, "pyproject.toml")
        ]
        
        # 只保留存在的路径
        return [p for p in include_paths if os.path.exists(p)]
        
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        # 假设模块位于 src/utils/，项目根目录是 src 的父目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(current_dir))
        
    def _get_system_version(self) -> str:
        """获取系统版本"""
        version_file = os.path.join(self._get_project_root(), "src", "seed_v0.1.1.py")
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "version" in line.lower() and "=" in line:
                        # 简单提取版本
                        return line.split("=")[1].strip().strip('"').strip("'")
        except Exception:
            pass
            
        return "seed-v0.1.1"
        
    def _copy_file_to_snapshot(self, src_path: str, snapshot_path: str) -> Tuple[int, str]:
        """复制文件到快照目录"""
        relative_path = self._get_relative_path(src_path)
        dest_path = os.path.join(snapshot_path, relative_path)
        
        # 创建目标目录
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # 复制文件
        shutil.copy2(src_path, dest_path)
        
        # 计算大小和校验和
        size = os.path.getsize(src_path)
        checksum = self._calculate_file_checksum(src_path)
        
        return size, checksum
        
    def _copy_dir_to_snapshot(self, src_dir: str, snapshot_path: str) -> Tuple[int, Dict[str, str]]:
        """复制目录到快照目录"""
        total_size = 0
        checksums = {}
        
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                file_path = os.path.join(root, file)
                size, checksum = self._copy_file_to_snapshot(file_path, snapshot_path)
                total_size += size
                checksums[file_path] = checksum
                
        return total_size, checksums
        
    def _get_relative_path(self, path: str) -> str:
        """获取相对于项目根目录的路径"""
        project_root = self._get_project_root()
        abs_path = os.path.abspath(path)
        
        if abs_path.startswith(project_root):
            return os.path.relpath(abs_path, project_root)
        else:
            # 如果不在项目根目录下，保留完整路径但替换分隔符
            return abs_path.replace(os.sep, "_")
            
    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception:
            return "error"
            
        return hash_md5.hexdigest()
        
    def _update_latest_snapshot(self, snapshot_id: str, metadata: SnapshotMetadata) -> None:
        """更新最新快照引用"""
        latest_file = os.path.join(self.backup_dir, "latest_snapshot.json")
        
        latest_info = {
            "snapshot_id": snapshot_id,
            "timestamp": metadata.timestamp,
            "description": metadata.description,
            "protocol_level": metadata.protocol_level,
            "metadata_file": os.path.join("metadata", f"{snapshot_id}.json"),
            "snapshot_path": os.path.join("snapshots", snapshot_id)
        }
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(latest_info, f, ensure_ascii=False, indent=2)
            
    def _cleanup_old_snapshots(self) -> None:
        """清理旧快照"""
        snapshots = self.list_snapshots()
        
        if len(snapshots) > self.max_snapshots:
            # 按时间排序，删除最旧的
            snapshots.sort(key=lambda x: x.timestamp)  # 升序，最旧的在前面
            
            to_delete = snapshots[:len(snapshots) - self.max_snapshots]
            
            for snapshot in to_delete:
                self.delete_snapshot(snapshot.snapshot_id)

def test_time_machine() -> None:
    """测试时光机快照模块"""
    print("=== 时光机快照模块测试 ===")
    
    # 创建测试备份目录
    test_dir = "test_backups"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    time_machine = TimeMachine(backup_dir=test_dir, max_snapshots=5)
    
    # 测试创建快照
    print("\n1. 测试创建快照:")
    success, snapshot_id = time_machine.create_snapshot(
        description="测试快照",
        protocol_level="L3",
        operation_id="test_op_001",
        trust_score=50.0,
        include_paths=["src/core/heartbeat.py"]  # 只包含一个文件以加快测试
    )
    
    if success:
        print(f"   快照创建成功: {snapshot_id}")
    else:
        print(f"   快照创建失败: {snapshot_id}")
        return
        
    # 测试列出快照
    print("\n2. 测试列出快照:")
    snapshots = time_machine.list_snapshots()
    print(f"   共找到 {len(snapshots)} 个快照:")
    for snapshot in snapshots:
        print(f"     - {snapshot.snapshot_id}: {snapshot.description}")
    
    # 测试验证快照
    print("\n3. 测试验证快照:")
    valid, message, details = time_machine.verify_snapshot(snapshot_id)
    print(f"   验证结果: {'有效' if valid else '无效'}")
    print(f"   消息: {message}")
    print(f"   文件数: {details.get('total_files', 0)}")
    
    # 测试获取元数据
    print("\n4. 测试获取元数据:")
    metadata = time_machine.get_snapshot_metadata(snapshot_id)
    if metadata:
        print(f"   快照描述: {metadata.description}")
        print(f"   协议级别: {metadata.protocol_level}")
        print(f"   创建时间: {metadata.timestamp}")
        print(f"   总大小: {metadata.total_size_bytes} 字节")
    
    # 测试删除快照
    print("\n5. 测试删除快照:")
    success, message = time_machine.delete_snapshot(snapshot_id)
    print(f"   删除结果: {message}")
    
    # 清理测试目录
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_time_machine()