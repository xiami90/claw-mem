#!/usr/bin/env python3
"""
memory_decay_daemon.py - 记忆衰减守护进程
定期调整记忆引力值，移除低价值记忆
"""

import time
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# 数据文件
DATA_DIR = Path("/root/.openclaw/workspace/memory")

class MemoryDecayDaemon:
    """记忆衰减守护进程"""
    
    def __init__(self, interval_hours: int = 24):
        self.interval_hours = interval_hours
        self.interval_seconds = interval_hours * 3600
        self.decay_factor = 0.99  # 每次衰减因子
        self.min_gravity = 0.1      # 最小引力值
        self.running = False
        self.thread = None
        
        # 导入L2管理器
        try:
            import sys
            sys.path.insert(0, str(DATA_DIR))
            from l2_manager import L2MemoryManager
            self.l2_manager = L2MemoryManager()
        except Exception as e:
            print(f"⚠️️ 导入L2管理器失败: {e}")
            self.l2_manager = None
    
    def start(self):
        """启动守护进程"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print(f"✅ 记忆衰减守护进程已启动，间隔：{self.interval_hours}小时")
    
    def stop(self):
        """停止守护进程"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print("⏹️️ 记忆衰减守护进程已停止")
    
    def _run(self):
        """守护进程主循环"""
        while self.running:
            try:
                # 执行衰减
                self.apply_decay()
                
                # 等待下一次执行
                time.sleep(self.interval_seconds)
                
            except Exception as e:
                print(f"⚠️️ 衰减守护进程错误: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    def apply_decay(self) -> Dict[str, Any]:
        """应用衰减"""
        if not self.l2_manager:
            return {
                'success': False,
                'message': 'L2管理器不可用'
            }
        
        timestamp = datetime.now().isoformat()
        initial_count = len(self.l2_manager.memories)
        
        # 应用衰减
        result = self.l2_manager.apply_decay(self.decay_factor)
        
        cleaned_count = result['cleaned_count']
        remaining_count = result['remaining_count']
        
        print(f"🔄 [{timestamp}] 记忆衰减完成: 清理{cleaned_count}条，剩余{remaining_count}条")
        
        # 保存衰减日志
        self._log_decay({
            'timestamp': timestamp,
            'initial_count': initial_count,
            'cleaned_count': cleaned_count,
            'remaining_count': remaining_count,
            'decay_factor': self.decay_factor
        })
        
        return {
            'success': True,
            'timestamp': timestamp,
            'initial_count': initial_count,
            'cleaned_count': cleaned_count,
            'remaining_count': remaining_count,
            'decay_factor': self.decay_factor
        }
    
    def _log_decay(self, log_entry: Dict[str, Any]):
        """记录衰减日志"""
        try:
            log_file = DATA_DIR / "decay_log.jsonl"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"⚠️️ 写入衰减日志失败: {e}")
    
    def get_decay_stats(self) -> Dict[str, Any]:
        """获取衰减统计"""
        try:
            log_file = DATA_DIR / "decay_log.jsonl"
            
            if not log_file.exists():
                return {
                    'total_decays': 0,
                    'last_decay': None,
                    'log_file': str(log_file)
                }
            
            # 读取日志
            logs = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
            
            if not logs:
                return {
                    'total_decays': 0,
                    'last_decay': None,
                    'log_file': str(log_file)
                }
            
            # 统计
            total_cleaned = sum(log['cleaned_count'] for log in logs)
            last_decay = logs[-1]
            
            return {
                'total_decays': len(logs),
                'total_cleaned': total_cleaned,
                'last_decay': last_decay,
                'log_file': str(log_file)
            }
            
        except Exception as e:
            return {
                'error': f'读取日志失败: {str(e)}'
            }
    
    def manual_decay(self) -> Dict[str, Any]:
        """手动触发衰减"""
        print("⚡ 手动触发记忆衰减...")
        return self.apply_decay()

# 创建全局实例
decay_daemon = MemoryDecayDaemon(interval_hours=24)

def test_decay_daemon():
    """测试衰减守护进程"""
    print("=" * 40)
    print("🧪 测试记忆衰减守护进程")
    print("=" * 40)
    
    # 测试1: 手动衰减
    print("\n测试1: 手动触发衰减")
    result = decay_daemon.manual_decay()
    print(f"✅ 衰减完成: 清理{result['cleaned_count']}条，剩余{result['remaining_count']}条")
    
    # 测试2: 获取统计
    print("\n测试2: 获取衰减统计")
    stats = decay_daemon.get_decay_stats()
    print(f"📊 总衰减次数: {stats['total_decays']}")
    print(f"   总清理数量: {stats.get('total_cleaned', 0)}")
    print(f"   最后衰减时间: {stats['last_decay']['timestamp'] if stats.get('last_decay') else '无'}")
    
    # 测试3: 启动守护进程
    print("\n测试3: 启动守护进程")
    print("⚠️️ 守护进程将每24小时运行一次，手动测试已跳过自动启动")
    print("💡 使用以下命令启动:")
    print("   decay_daemon.start()")
    print("   decay_daemon.stop()")
    
    print("\n✅ 衰减守护进程测试完成！")

if __name__ == "__main__":
    test_decay_daemon()