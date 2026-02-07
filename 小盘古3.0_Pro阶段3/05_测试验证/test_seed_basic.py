#!/usr/bin/env python3
"""
创生种子v0.1基础测试

测试目标：
1. 验证心跳功能正常
2. 验证自我诊断报告生成
3. 验证基础协议识别功能
4. 验证错误处理机制

测试原则：
- 最小依赖：不依赖外部服务
- 快速执行：每个测试<1秒
- 确定性：测试结果可重复
"""

import sys
import os
import time
import threading
import tempfile

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # 项目根目录 '小盘古3.0_Pro'
# 确保Python能够找到src目录下的模块
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.种子.seed_v0_1_1 import GenesisSeed
    from src.核心.protocol_engine import ProtocolLevel, ProtocolRequest
    from src.核心.heartbeat import HeartbeatRecord
    from src.进化.self_diagnosis import SystemDiagnosis
    from src.工具.logger import LogType
except ImportError as e:
    print(f"导入失败: {e}")
    print(f"sys.path: {sys.path}")
    print(f"project_root: {project_root}")
    raise

def test_heartbeat_mechanism():
    """测试心跳机制"""
    print("测试1: 心跳机制")
    
    seed = GenesisSeed()
    
    # 启动心跳
    seed.start_heartbeat()
    
    # 验证心跳线程已启动
    assert seed.heartbeat.running == True, "心跳应该正在运行"
    assert seed.heartbeat.thread is not None, "心跳线程应该存在"
    assert seed.heartbeat.thread.is_alive() == True, "心跳线程应该存活"
    
    # 短暂等待，让心跳线程有机会运行
    time.sleep(0.5)
    
    # 验证心跳相关状态
    assert seed.heartbeat.interval == 30.0, "心跳间隔应为30秒"
    
    # 停止心跳
    seed.heartbeat.stop()
    
    print("  [OK] 心跳机制测试通过")

def test_protocol_parsing():
    """测试协议解析"""
    print("测试2: 协议解析")
    
    seed = GenesisSeed()
    
    # 测试L1观察协议解析
    l1_request = seed.parse_protocol_request("检查系统状态")
    assert l1_request is not None, "L1请求不应为None"
    assert l1_request.level == ProtocolLevel.L1_OBSERVE
    assert "检查系统状态" in l1_request.operation
    
    # 测试L2操作协议解析
    l2_request = seed.parse_protocol_request("执行测试脚本")
    assert l2_request is not None, "L2请求不应为None"
    assert l2_request.level == ProtocolLevel.L2_OPERATE
    
    # 测试L3变更协议解析
    l3_request = seed.parse_protocol_request("修改核心架构")
    assert l3_request is not None, "L3请求不应为None"
    assert l3_request.level == ProtocolLevel.L3_CHANGE
    
    # 测试L4生态协议解析
    l4_request = seed.parse_protocol_request("申请长期生态授权")
    assert l4_request is not None, "L4请求不应为None"
    assert l4_request.level == ProtocolLevel.L4_ECOSYSTEM
    
    print("  [OK] 协议解析测试通过")

def test_protocol_execution():
    """测试协议执行"""
    print("测试3: 协议执行")
    
    seed = GenesisSeed()
    
    # 测试L1协议执行
    l1_request = ProtocolRequest(
        level=ProtocolLevel.L1_OBSERVE,
        operation="检查系统状态",
        justification="测试"
    )
    
    result = seed.execute_protocol(l1_request)
    assert result["success"] == True
    assert result["level"] == "L1观察协议"
    assert "data" in result
    
    # 测试L2协议执行（模拟审批通过）
    l2_request = ProtocolRequest(
        level=ProtocolLevel.L2_OPERATE,
        operation="创建测试文件",
        justification="测试"
    )
    
    initial_trust = seed.trust_score
    result = seed.execute_protocol(l2_request)
    assert result["success"] == True
    # L2成功信任分变化：基础3.0 * 重要性1.5 * 风险0.8 * 清晰度1.5 = 5.4
    expected = min(100.0, initial_trust + 5.4)  # 上限100
    assert seed.trust_score == expected
    
    # 验证协议日志
    assert len(seed.protocol_engine.execution_logs) == 2  # L1和L2两次执行
    
    print("  [OK] 协议执行测试通过")

def test_self_diagnosis():
    """测试自我诊断"""
    print("测试4: 自我诊断")
    
    seed = GenesisSeed()
    
    diagnosis = seed.self_diagnose()
    
    # 验证诊断结构
    assert isinstance(diagnosis, dict)
    assert "timestamp" in diagnosis
    assert "overall_health" in diagnosis
    assert isinstance(diagnosis["overall_health"], int)
    assert 0 <= diagnosis["overall_health"] <= 100
    
    # 验证组件状态
    assert "components" in diagnosis
    required_components = ["heartbeat", "protocol_engine", "trust_system", "dependencies"]
    for comp in required_components:
        assert comp in diagnosis["components"]
        assert "status" in diagnosis["components"][comp]
        assert "score" in diagnosis["components"][comp]
    
    # 验证建议
    assert "recommendations" in diagnosis
    assert isinstance(diagnosis["recommendations"], list)
    
    print("  [OK] 自我诊断测试通过")

def test_basic_actions():
    """测试基础行动器"""
    print("测试5: 基础行动器")
    
    seed = GenesisSeed()
    
    # 创建临时目录进行测试
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        
        # 测试文件写入（受限环境外，应失败）
        result = seed.execute_basic_action("write_file", path=test_file, content="测试内容")
        # 由于路径不在项目目录内，应该失败
        assert result["success"] == False
        assert "超出允许范围" in result.get("error", "")
        
        # 测试命令执行（安全命令）
        if sys.platform != "win32":
            result = seed.execute_basic_action("run_command", command="echo hello")
            # 由于命令在受限环境外执行，可能失败或被限制
            # 我们不断言成功，只验证不崩溃
        
        # 测试目录创建（受限环境外，应失败）
        test_dir = os.path.join(tmpdir, "subdir")
        result = seed.execute_basic_action("create_dir", path=test_dir)
        assert result["success"] == False
    
    print("  [OK] 基础行动器测试通过")

def test_error_handling():
    """测试错误处理"""
    print("测试6: 错误处理")
    
    seed = GenesisSeed()
    
    # 测试安全执行函数
    def problematic_function(x, y):
        return x / y
    
    # 正常执行
    result = seed.safe_execute(problematic_function, 10, 2)
    assert result == 5.0
    
    # 异常执行
    result = seed.safe_execute(problematic_function, 10, 0)
    assert result is None
    
    # 验证错误被记录
    error_logs = seed.logger.get_recent_logs(log_type=LogType.ERROR)
    assert len(error_logs) >= 1
    
    print("  [OK] 错误处理测试通过")

def test_evolution_proposal():
    """测试进化提案生成"""
    print("测试7: 进化提案生成")
    
    seed = GenesisSeed()
    
    proposal = seed.generate_evolution_proposal(
        title="测试进化提案",
        description="这是一个测试进化提案",
        change_type="enhancement"
    )
    
    # 验证提案结构
    assert proposal["title"] == "测试进化提案"
    assert proposal["description"] == "这是一个测试进化提案"
    assert proposal["change_type"] == "enhancement"
    assert proposal["proposed_by"] == "evolution-proposal-gen-v0.1"
    assert "timestamp" in proposal
    assert proposal["current_trust_score"] == seed.trust_score
    assert proposal["required_trust_score"] == 40.0  # enhancement需要40分
    assert proposal["protocol_level"] == "L2操作协议"
    
    # 验证提案章节
    assert "sections" in proposal
    sections = proposal["sections"]
    required_sections = [
        "problem_analysis",
        "solution_design", 
        "risk_assessment",
        "implementation_plan",
        "expected_benefits"
    ]
    for section in required_sections:
        assert section in sections
        assert isinstance(sections[section], str)
    
    print("  [OK] 进化提案生成测试通过")

def test_system_summary():
    """测试系统摘要"""
    print("测试8: 系统摘要")
    
    seed = GenesisSeed()
    
    summary = seed.get_summary()
    
    # 验证摘要结构
    assert "version" in summary
    assert "uptime" in summary
    assert "trust_score" in summary
    assert "status" in summary
    assert "heartbeat_running" in summary
    
    # 验证系统状态
    assert summary["version"] == "seed-v0.1.1"
    assert isinstance(summary["trust_score"], float)
    assert 0 <= summary["trust_score"] <= 100
    assert summary["heartbeat_running"] == False
    
    print("  [OK] 系统摘要测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=== 创生种子v0.1基础测试开始 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 40)
    
    tests = [
        test_heartbeat_mechanism,
        test_protocol_parsing,
        test_protocol_execution,
        test_self_diagnosis,
        test_basic_actions,
        test_error_handling,
        test_evolution_proposal,
        test_system_summary
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test_func.__name__} 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] {test_func.__name__} 异常: {type(e).__name__}: {e}")
            failed += 1
    
    print("=" * 40)
    print(f"测试完成: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有测试通过！创生种子v0.1基础功能正常。")
        return 0
    else:
        print("[FAIL] 部分测试失败，请检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())