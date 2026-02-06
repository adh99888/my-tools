#!/usr/bin/env python3
"""
创生纪元演示：进化提案生成

展示功能：
1. 创生种子基础功能
2. 信任评分系统集成
3. 进化提案生成
4. 协议执行流程

这是小盘古3.0_Pro创生纪元的第一个演示。
"""

import sys
import os
import json

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("创生纪元演示：进化提案生成")
print("=" * 60)

# 1. 导入并初始化创生种子
print("\n1. 初始化创生种子v0.1")
from seed_v0_1 import GenesisSeed
seed = GenesisSeed()

# 启动心跳
seed.start_heartbeat()

print(f"   版本: {seed.version}")
print(f"   初始信任分: {seed.trust_score}")
print(f"   心跳间隔: {seed.heartbeat_interval}秒")

# 2. 系统诊断
print("\n2. 系统自我诊断")
diagnosis = seed._self_diagnose()
print(f"   总体健康度: {diagnosis['overall_health']}/100")
print(f"   组件状态:")
for comp_name, comp_data in diagnosis['components'].items():
    print(f"     - {comp_name}: {comp_data['status']} ({comp_data['score']}/100)")

if diagnosis['recommendations']:
    print(f"   改进建议:")
    for rec in diagnosis['recommendations']:
        print(f"     - {rec}")

# 3. 协议执行演示
print("\n3. 协议执行演示")

# L1观察协议
print("   a) L1观察协议：检查系统状态")
request = seed.parse_protocol_request("检查系统状态")
result = seed.execute_protocol(request)
print(f"      结果: {result['message']}")
if result['data']:
    print(f"      数据: {json.dumps(result['data'], ensure_ascii=False, indent=6)[:100]}...")

# L2操作协议
print("\n   b) L2操作协议：模拟文件创建")
request = seed.parse_protocol_request("创建测试文件")
result = seed.execute_protocol(request)
print(f"      结果: {result['message']}")
print(f"      信任分变化: {seed.trust_score:.1f} (+3.0)")

# 4. 信任评分系统演示
print("\n4. 信任评分系统演示")

try:
    from core.trust_system import TrustSystem
    
    # 创建信任系统（使用临时目录）
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        print(f"   当前信任分: {trust.current_score}")
        print(f"   当前阈值: {trust.get_current_threshold().level}")
        
        # 检查权限
        print("\n   权限检查:")
        for level in ["L1", "L2", "L3", "L4"]:
            allowed, reason = trust.can_perform_operation(level)
            print(f"     {level}: {'✓ 允许' if allowed else '✗ 禁止'} - {reason}")
        
        # 模拟协议执行
        print("\n   模拟协议执行结果:")
        
        # L2成功
        record = trust.apply_protocol_result(
            protocol_level="L2",
            success=True,
            operation_id="demo_l2_success",
            importance="medium",
            risk_level="low",
            clarity="good"
        )
        print(f"     L2成功: {record.old_score:.1f} → {record.new_score:.1f} (变化: {record.change_amount:+.1f})")
        
        # L3失败
        record = trust.apply_protocol_result(
            protocol_level="L3",
            success=False,
            operation_id="demo_l3_failure",
            importance="high",
            risk_level="high",
            clarity="poor"
        )
        print(f"     L3失败: {record.old_score:.1f} → {record.new_score:.1f} (变化: {record.change_amount:+.1f})")
        
        # 最终状态
        print(f"\n   最终信任分: {trust.current_score}")
        print(f"   最终阈值: {trust.get_current_threshold().level}")
        
except ImportError as e:
    print(f"   信任评分系统导入失败: {e}")
    print("   请确保已安装依赖: pip install pydantic")

# 5. 进化提案生成
print("\n5. 进化提案生成演示")

proposal = seed.generate_evolution_proposal(
    title="添加结构化日志系统",
    description="为创生种子添加JSON格式结构化日志，支持进化过程追踪和问题诊断。",
    change_type="enhancement"
)

print(f"   提案标题: {proposal['title']}")
print(f"   提案类型: {proposal['change_type']}")
print(f"   所需协议: {proposal['protocol_level']}")
print(f"   所需信任分: {proposal['required_trust_score']} (当前: {proposal['current_trust_score']})")

print("\n   提案章节:")
for section_name, section_content in proposal['sections'].items():
    print(f"     - {section_name}: {section_content}")

# 6. 系统摘要
print("\n6. 系统摘要")
summary = seed.get_summary()
print(f"   运行时间: {summary['system']['uptime_seconds']:.1f}秒")
print(f"   心跳状态: {'运行中' if summary['system']['heartbeat_running'] else '停止'}")
print(f"   进化日志数: {summary['system']['evolution_logs_count']}")
print(f"   协议日志数: {summary['system']['protocol_logs_count']}")

# 7. 进化准备建议
print("\n7. 进化准备建议")
print("   根据《创生纪元实施计划》，下一步应进行首次进化：")
print("   - 目标: 添加结构化日志系统 (L2操作协议)")
print("   - 所需信任分: ≥30分 (当前: 50分 ✓)")
print("   - 预计耗时: 1-2天")
print("   - 关键产出: 可追溯的进化日志，支持后续进化决策")

print("\n" + "=" * 60)
print("演示完成")
print("=" * 60)

# 停止心跳
seed.heartbeat_running = False
if seed.heartbeat_thread:
    seed.heartbeat_thread.join(timeout=2)
    
print("\n提示: 运行 'python tests/test_seed_basic.py' 进行完整功能测试")
print("提示: 运行 'python tests/test_trust_system.py' 进行信任系统测试")