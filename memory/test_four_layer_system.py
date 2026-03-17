#!/usr/bin/env python3
"""
test_four_layer_system.py - 四层记忆系统完整测试
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/root/.openclaw/workspace/memory")

from l0_manager import L0MemoryManager
from l2_manager import L2MemoryManager
from vector_db import VectorDBManager
from smart_compress import L1Compressor
from priority_manager import PriorityManager
from result_filter import ResultFilter
from memory_protocol import MemoryProtocol
from memory_decay_daemon import MemoryDecayDaemon
from offline_strategy import OfflineStrategy

def run_all_tests():
    """运行所有测试"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'summary': {}
    }
    
    print("=" * 60)
    print("🧪 四层记忆系统完整测试")
    print("=" * 60)
    print()
    
    # 测试L0
    test_l0(results)
    
    # 测试L1
    test_l1(results)
    
    # 测试L2
    test_l2(results)
    
    # 测试L3
    test_l3(results)
    
    # 测试优先级
    test_priority(results)
    
    # 测试过滤
    test_filter(results)
    
    # 测试协议
    test_protocol(results)
    
    # 测试离线策略
    test_offline(results)
    
    # 测试衰减
    test_decay(results)
    
    # 生成报告
    generate_report(results)

def test_l0(results):
    """测试L0"""
    print("🧪 测试 L0 瞬时记忆")
    print("-" * 40)
    try:
        manager = L0MemoryManager()
        result = manager.add_memory("测试内容", "test")
        manager.stop_cleanup_thread()
        
        results['tests']['L0'] = {
            'status': 'PASS',
            'message': 'L0测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['L0'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_l1(results):
    """测试L1"""
    print("🧪 测试 L1 工作记忆")
    print("-" * 40)
    try:
        compressor = L1Compressor()
        result = compressor.trigger_compress()
        
        results['tests']['L1'] = {
            'status': 'PASS',
            'message': 'L1测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['L1'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_l2(results):
    """测试L2"""
    print("🧪 测试 L2 神经元记忆网")
    print("-" * 40)
    try:
        manager = L2MemoryManager()
        result = manager.add_memory("测试主题", "测试内容", "test")
        
        results['tests']['L2'] = {
            'status': 'PASS',
            'message': 'L2测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['L2'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_l3(results):
    """测试L3"""
    print("🧪 测试 L3 向量数据库")
    print("-" * 40)
    try:
        manager = VectorDBManager()
        
        if not manager.chromadb_available:
            results['tests']['L3'] = {
                'status': 'SKIP',
                'message': 'ChromaDB不可用'
            }
            print("⚠️️ SKIP\n")
            return
        
        result = manager.add_memory("测试内容")
        
        results['tests']['L3'] = {
            'status': 'PASS',
            'message': 'L3测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['L3'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_priority(results):
    """测试优先级"""
    print("🧪 测试优先级判断")
    print("-" * 40)
    try:
        manager = PriorityManager()
        result = manager.determine_priority("记住生日", "personal")
        
        results['tests']['Priority'] = {
            'status': 'PASS',
            'message': '优先级测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['Priority'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_filter(results):
    """测试过滤"""
    print("🧪 测试结果过滤")
    print("-" * 40)
    try:
        filter_obj = ResultFilter()
        test_results = [
            {'id': '1', 'similarity': 0.9, 'gravity': 1.5},
            {'id': '2', 'similarity': 0.2, 'gravity': 0.5}
        ]
        filtered = filter_obj.filter_results(test_results, limit=1)
        
        results['tests']['Filter'] = {
            'status': 'PASS',
            'message': '过滤测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['Filter'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_protocol(results):
    """测试协议"""
    print("🧪 测试记忆协议")
    print("-" * 40)
    try:
        protocol = MemoryProtocol()
        result = protocol.store_memory("测试主题", "测试内容", "test")
        
        results['tests']['Protocol'] = {
            'status': 'PASS',
            'message': '协议测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['Protocol'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_offline(results):
    """测试离线策略"""
    print("🧪 测试离线回退策略")
    print("-" * 40)
    try:
        strategy = OfflineStrategy()
        result = strategy.search_with_fallback("测试", limit=3)
        
        results['tests']['Offline'] = {
            'status': 'PASS',
            'message': '离线策略测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['Offline'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def test_decay(results):
    """测试衰减"""
    print("🧪 测试记忆衰减守护")
    print("-" * 40)
    try:
        daemon = MemoryDecayDaemon(interval_hours=24)
        result = daemon.manual_decay()
        
        results['tests']['Decay'] = {
            'status': 'PASS',
            'message': '衰减守护测试通过'
        }
        print("✅ PASS\n")
    except Exception as e:
        results['tests']['Decay'] = {
            'status': 'FAIL',
            'message': str(e)
        }
        print(f"❌ FAIL: {e}\n")

def generate_report(results):
    """生成报告"""
    print("=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    print()
    
    total = len(results['tests'])
    passed = sum(1 for t in results['tests'].values() if t['status'] == 'PASS')
    failed = sum(1 for t in results['tests'].values() if t['status'] == 'FAIL')
    skipped = sum(1 for t in results['tests'].values() if t['status'] == 'SKIP')
    
    pass_rate = (passed / (total - skipped) * 100) if (total - skipped) > 0 else 0
    
    results['summary'] = {
        'total': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'pass_rate': pass_rate
    }
    
    print(f"总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⚠️️ 跳过: {skipped}")
    print(f"📊 通过率: {pass_rate:.1f}%")
    print()
    
    for test_name, result in results['tests'].items():
        emoji = {'PASS': '✅', 'FAIL': '❌', 'SKIP': '⚠️️'}.get(result['status'], '?')
        print(f"{emoji} {test_name}: {result['message']}")
    
    # 保存报告
    report_file = Path("/root/.openclaw/workspace/memory/test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"📄 测试报告已保存: {report_file}")

if __name__ == "__main__":
    run_all_tests()