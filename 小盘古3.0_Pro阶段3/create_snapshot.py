#!/usr/bin/env python3
"""
创建时光机快照脚本
用于L3死亡开关协议执行前的强制快照
宪法依据：技术执行法典第5.3条
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.工具.time_machine import TimeMachine
from datetime import datetime
import traceback

def main(description=None):
    """创建L3协议快照"""
    print("=== L3变更协议 - 时光机快照创建 ===")
    print("宪法依据：宪法第4条（L3+操作前强制创建时光机快照）")
    print("协议级别：L3变更协议")
    print("当前信任分：100.0分")
    print("")
    
    # 使用提供的描述或默认
    if description is None:
        if len(sys.argv) > 1:
            description = sys.argv[1]
        else:
            description = "L3变更协议实施前快照"
    
    print(f"快照描述: {description}")
    
    # 初始化时光机
    time_machine = TimeMachine(backup_dir="backups", max_snapshots=50)
    
    # 创建快照
    print("正在创建系统快照...")
    try:
        success, snapshot_id = time_machine.create_snapshot(
            description=description,
            protocol_level="L3",
            operation_id=f"L3-{datetime.now().strftime('%Y%m%d')}-001",
            trust_score=100.0,
            include_paths=None  # 包含默认所有路径
        )
    except Exception as e:
        print(f"[ERROR] 创建快照时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)
    
    if success:
        print(f"[SUCCESS] 快照创建成功: {snapshot_id}")
        
        # 验证快照
        print("正在验证快照完整性...")
        valid, message, details = time_machine.verify_snapshot(snapshot_id)
        if valid:
            print(f"[SUCCESS] 快照验证通过: {message}")
            print(f"   文件数量: {details.get('total_files', 0)}")
            print(f"   总大小: {details.get('snapshot_size', 0):,} 字节")
            
            # 获取元数据
            metadata = time_machine.get_snapshot_metadata(snapshot_id)
            if metadata:
                print(f"   快照描述: {metadata.description}")
                print(f"   协议级别: {metadata.protocol_level}")
                print(f"   创建时间: {metadata.timestamp}")
                print(f"   信任分（前）: {metadata.trust_score_before}")
            
            # 更新latest_snapshot.json
            print("[SUCCESS] 快照准备就绪，可以安全执行L3死亡开关协议")
            
            # 记录到日志
            snapshot_info = {
                "snapshot_id": snapshot_id,
                "timestamp": metadata.timestamp if metadata else "",
                "description": description,
                "protocol_level": "L3",
                "operation_id": "L3-20250204-001",
                "trust_score_before": 100.0
            }
            
            print(f"\n[INFO] 快照信息:")
            for key, value in snapshot_info.items():
                print(f"   {key}: {value}")
                
            return True, snapshot_id
        else:
            print(f"[ERROR] 快照验证失败: {message}")
            return False, snapshot_id
    else:
        print(f"[ERROR] 快照创建失败: {snapshot_id}")
        return False, snapshot_id

if __name__ == "__main__":
    # 传递命令行参数作为描述
    description = None
    if len(sys.argv) > 1:
        description = sys.argv[1]
    success, snapshot_id = main(description)
    if not success:
        sys.exit(1)