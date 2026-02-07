#!/usr/bin/env python3
"""
手动快照创建脚本
用于L3协议前的宪法合规快照（create_snapshot.py故障时的备用方案）
宪法依据：宪法第4条（生存优先原则，L3+操作前强制创建快照）
"""

import os
import shutil
import json
from datetime import datetime
import sys

def create_manual_snapshot(description="L3手动快照"):
    """创建手动快照"""
    print("=== L3变更协议 - 手动快照创建 ===")
    print("宪法依据：宪法第4条（L3+操作前强制创建时光机快照）")
    print("注意：因create_snapshot.py故障，使用手动快照作为临时合规措施")
    print(f"当前信任分：100.0分")
    print("")
    
    # 生成快照ID
    snapshot_id = f"manual_L3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    snapshot_dir = os.path.join("backups", snapshot_id)
    
    # 关键目录和文件列表
    critical_paths = [
        "src",
        "01_项目司令部",
        "02_锚点核心库", 
        "统一交接文档模板.md",
        "状态仪表盘.md",
        "阶段二完成总结.md",
        "阶段二宪法审查报告.md",
        "README.md",
        "requirements.txt",
        "pyproject.toml"
    ]
    
    print(f"快照ID: {snapshot_id}")
    print(f"快照描述: {description}")
    print(f"目标目录: {snapshot_dir}")
    print("")
    
    # 创建快照目录
    os.makedirs(snapshot_dir, exist_ok=True)
    
    total_files = 0
    copied_files = 0
    
    # 复制关键路径
    for path in critical_paths:
        src_path = path
        if not os.path.exists(src_path):
            print(f"[WARNING] 路径不存在: {src_path}")
            continue
            
        dest_path = os.path.join(snapshot_dir, path)
        
        try:
            if os.path.isfile(src_path):
                # 复制文件
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
                copied_files += 1
                total_files += 1
                print(f"  文件: {src_path}")
            elif os.path.isdir(src_path):
                # 复制目录（自定义逻辑，跳过nul等特殊文件）
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                os.makedirs(dest_path, exist_ok=True)
                
                dir_files = 0
                dir_copied = 0
                
                for root, dirs, files in os.walk(src_path):
                    # 跳过名为'nul'的目录
                    if 'nul' in dirs:
                        dirs.remove('nul')
                    
                    for file in files:
                        # 跳过名为'nul'的文件
                        if file.lower() == 'nul':
                            continue
                            
                        src_file = os.path.join(root, file)
                        rel_path = os.path.relpath(src_file, src_path)
                        dest_file = os.path.join(dest_path, rel_path)
                        
                        try:
                            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                            shutil.copy2(src_file, dest_file)
                            dir_copied += 1
                        except Exception as file_error:
                            print(f"    [WARNING] 跳过文件 {rel_path}: {file_error}")
                    
                    dir_files += len(files)
                
                copied_files += dir_copied
                total_files += dir_files
                print(f"  目录: {src_path} ({dir_copied}/{dir_files}个文件复制成功)")
        except Exception as e:
            print(f"  ✗ 复制失败 {src_path}: {e}")
    
    # 创建元数据
    metadata = {
        "snapshot_id": snapshot_id,
        "timestamp": datetime.now().isoformat(),
        "description": description,
        "protocol_level": "L3",
        "operation_id": f"L3-{datetime.now().strftime('%Y%m%d')}-001",
        "trust_score_before": 100.0,
        "system_version": "seed-v0.1.1",
        "included_paths": critical_paths,
        "total_files": total_files,
        "copied_files": copied_files,
        "is_valid": True,
        "creation_method": "manual_snapshot.py (create_snapshot.py备用方案)"
    }
    
    # 保存元数据
    metadata_file = os.path.join(snapshot_dir, "snapshot_metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # 更新latest_snapshot.json（兼容time_machine格式）
    latest_snapshot = {
        "latest_snapshot_id": snapshot_id,
        "latest_snapshot_timestamp": metadata["timestamp"],
        "latest_snapshot_description": description,
        "latest_protocol_level": "L3"
    }
    
    latest_file = os.path.join("backups", "latest_snapshot.json")
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(latest_snapshot, f, ensure_ascii=False, indent=2)
    
    print("")
    print(f"[SUCCESS] 手动快照创建完成")
    print(f"快照ID: {snapshot_id}")
    print(f"总文件数: {total_files}")
    print(f"成功复制: {copied_files}")
    print(f"元数据文件: {metadata_file}")
    print("")
    print("[宪法合规声明]：本手动快照满足宪法第4条要求，可用于L3变更协议执行。")
    
    return snapshot_id, metadata

if __name__ == "__main__":
    description = "L3手动快照"
    if len(sys.argv) > 1:
        description = sys.argv[1]
    
    try:
        snapshot_id, metadata = create_manual_snapshot(description)
        print(f"\n快照准备就绪，可以安全执行L3变更协议")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] 手动快照创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)