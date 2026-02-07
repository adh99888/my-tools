:''':''':''':''':''':'''
module_import_test.py
简单测试核心模块导入
'''

import sys
import os
import importlib

# 确保编码兼容性
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 设置项目根目录和src路径
root_path = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(root_path, 'src')

# 确保src路径在sys.path中
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 测试模块列表
modules_to_test = [
    '核心.trust_system_core',
    '核心.heartbeat',
    '核心.protocol_engine',
    '进化.self_diagnosis',
    '进化.proposal_gen',
    '工具.logger',
    '工具.time_machine'
]

def test_module_import(module_name):
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    print("=" + "="*59)
    print("核心模块导入测试")
    print("=" + "="*59)
    print(f"Python版本: {sys.version.split()[0]}")
    print(f"工作目录: {root_path}")
    print(f"src路径: {src_path}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print("=" + "="*59)
    
    failed = []
    
    for module in modules_to_test:
        print(f"\n测试: {module}")
        success, error = test_module_import(module)
        
        if success:
            print(f"  [OK]")
        else:
            print(f"  [FAIL] {error}")
            failed.append((module, error))
    
    print("\n" + "=" + "="*59)
    print("测试结果")
    print("=" + "="*59)
    total = len(modules_to_test)
    print(f"总计: {total}")
    print(f"通过: {total - len(failed)}")
    print(f"失败: {len(failed)}")
    
    if failed:
        print("\n失败详情:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        sys.exit(1)
    else:
        print("\n所有核心模块导入成功！")
        sys.exit(0)
