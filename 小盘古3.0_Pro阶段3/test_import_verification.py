# -*- coding: utf-8 -*-

# 移除错误的setdefaultencoding调用
import sys
import os

# 添加项目src路径到sys.path（临时解决方案）
pc = os.path.dirname(__file__)
if pc not in sys.path:
    sys.path.insert(0, pc)

print(f"sys.path已更新: {sys.path[0]}")

# 测试导入列表
modules_to_test = [
    '种子.seed_v0_1_1',
    '核心.trust_system_core',
    '核心.heartbeat',
    '核心.protocol_engine',
    '进化.self_diagnosis',
    '进化.proposal_gen',
    '工具.logger',
    '工具.time_machine'
]

def test_import(module_name):
    """测试单个模块导入"""
    try:
        __import__(module_name)
        return True, None
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    # 打印测试开始信息
    print("=" * 60)
    print("模块导入测试开始")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    
    failed_modules = []
    
    # 逐个测试模块导入
    for module in modules_to_test:
        print(f"\n测试: {module}")
        success, error = test_import(module)
        
        if success:
            print(f"  [OK] 成功导入")
        else:
            print(f"  [FAIL] 导入失败: {error}")
            failed_modules.append((module, error))
    
    # 测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    total = len(modules_to_test)
    passed = total - len(failed_modules)
    
    print(f"总计: {total} 个模块")
    print(f"通过: {passed} 个")
    print(f"失败: {len(failed_modules)} 个")
    
    if failed_modules:
        print("\n失败的模块:")
        for module, error in failed_modules:
            print(f"  - {module}: {error}")
        sys.exit(1)
    else:
        print("\n[+] 所有模块导入测试通过！")
        sys.exit(0)
