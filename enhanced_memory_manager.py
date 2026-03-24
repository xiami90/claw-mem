
import datetime
import json
import os
from typing import Dict, List, Optional, Any

class EnhancedThreeLayerMemoryManager:
    """增强版三层记忆管理器 - 解决上下文溢出问题"""
    
    def __init__(self):
        self.hot_ram = []  # 最近7天数据
        self.warm_store = []  # 7-30天数据，向量索引
        self.cold_store = []  # 30天+数据，压缩存储
        self.layer_config = {
            'hot_ram_days': 7,
            'warm_store_days': 30,
            'cold_store_days': 90,
            'max_hot_ram_size': 50,  # 限制Hot RAM大小
            'migration_batch_size': 10
        }
    
    def add_memory(self, content: str, category: str = "general") -> Dict[str, Any]:
        """添加记忆，自动分层存储"""
        memory = {
            'id': len(self.hot_ram) + len(self.warm_store) + len(self.cold_store) + 1,
            'content': content,
            'category': category,
            'timestamp': datetime.datetime.now().isoformat(),
            'vector': self._generate_vector(content),  # 用于Warm Store
            'compressed': False
        }
        
        # 添加到Hot RAM
        self.hot_ram.append(memory)
        
        # 检查是否需要迁移
        self._check_and_migrate()
        
        return {
            'success': True,
            'memory_id': memory['id'],
            'layer': 'hot_ram',
            'total_hot': len(self.hot_ram),
            'total_warm': len(self.warm_store),
            'total_cold': len(self.cold_store)
        }
    
    def _check_and_migrate(self):
        """检查并执行数据迁移"""
        current_time = datetime.datetime.now()
        
        # 迁移到Warm Store (超过7天)
        self._migrate_to_warm_store(current_time)
        
        # 迁移到Cold Store (超过30天)
        self._migrate_to_cold_store(current_time)
        
        # 清理Hot RAM (超过最大限制)
        self._cleanup_hot_ram()
    
    def _migrate_to_warm_store(self, current_time: datetime.datetime):
        """迁移到Warm Store"""
        cutoff_date = current_time - datetime.timedelta(days=self.layer_config['hot_ram_days'])
        
        memories_to_migrate = []
        remaining_hot = []
        
        for memory in self.hot_ram:
            memory_time = datetime.datetime.fromisoformat(memory['timestamp'])
            if memory_time < cutoff_date:
                memories_to_migrate.append(memory)
            else:
                remaining_hot.append(memory)
        
        if memories_to_migrate:
            self.warm_store.extend(memories_to_migrate)
            self.hot_ram = remaining_hot
            print(f'🔄 迁移 {len(memories_to_migrate)} 条记忆到 Warm Store')
    
    def _migrate_to_cold_store(self, current_time: datetime.datetime):
        """迁移到Cold Store"""
        cutoff_date = current_time - datetime.timedelta(days=self.layer_config['warm_store_days'])
        
        memories_to_migrate = []
        remaining_warm = []
        
        for memory in self.warm_store:
            memory_time = datetime.datetime.fromisoformat(memory['timestamp'])
            if memory_time < cutoff_date:
                # 压缩存储
                memory['compressed'] = True
                memory['content'] = self._compress_content(memory['content'])
                memories_to_migrate.append(memory)
            else:
                remaining_warm.append(memory)
        
        if memories_to_migrate:
            self.cold_store.extend(memories_to_migrate)
            self.warm_store = remaining_warm
            print(f'🗄️ 迁移 {len(memories_to_migrate)} 条记忆到 Cold Store')
    
    def _cleanup_hot_ram(self):
        """清理Hot RAM，保持合理大小"""
        if len(self.hot_ram) > self.layer_config['max_hot_ram_size']:
            # 保留最新的记录
            self.hot_ram = self.hot_ram[-self.layer_config['max_hot_ram_size']:]
            print(f'🧹 清理Hot RAM，保留最新 {len(self.hot_ram)} 条记录')
    
    def _generate_vector(self, content: str) -> List[float]:
        """生成内容向量"""
        # 简化的向量生成
        import hashlib
        hash_obj = hashlib.md5(content.encode())
        vector = [float(b) / 255.0 for b in hash_obj.digest()[:50]]
        return vector
    
    def _compress_content(self, content: str) -> str:
        """压缩内容"""
        # 简化的压缩 - 提取关键词
        words = content.split()
        if len(words) > 20:
            return ' '.join(words[:10] + ['...'] + words[-10:])
        return content
    
    def search_memories(self, query: str, layer: str = "all") -> List[Dict[str, Any]]:
        """搜索记忆，支持分层搜索"""
        results = []
        
        if layer in ["all", "hot_ram"]:
            results.extend(self._search_layer(self.hot_ram, query))
        
        if layer in ["all", "warm_store"]:
            results.extend(self._search_layer(self.warm_store, query))
        
        if layer in ["all", "cold_store"]:
            results.extend(self._search_layer(self.cold_store, query))
        
        return results
    
    def _search_layer(self, layer_data: List[Dict], query: str) -> List[Dict[str, Any]]:
        """在指定层搜索"""
        results = []
        query_lower = query.lower()
        
        for memory in layer_data:
            content = memory['content'].lower()
            if query_lower in content:
                results.append({
                    'id': memory['id'],
                    'content': memory['content'],
                    'category': memory['category'],
                    'timestamp': memory['timestamp'],
                    'layer': 'warm_store' if layer_data == self.warm_store else 
                            'cold_store' if layer_data == self.cold_store else 'hot_ram',
                    'relevance': content.count(query_lower) / len(content.split())
                })
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'hot_ram_count': len(self.hot_ram),
            'warm_store_count': len(self.warm_store),
            'cold_store_count': len(self.cold_store),
            'total_memories': len(self.hot_ram) + len(self.warm_store) + len(self.cold_store),
            'layer_config': self.layer_config,
            'memory_distribution': {
                'hot_ram': len(self.hot_ram),
                'warm_store': len(self.warm_store),
                'cold_store': len(self.cold_store)
            }
        }

# 创建全局实例
memory_manager = EnhancedThreeLayerMemoryManager()

# 测试函数
def test_enhanced_memory():
    """测试增强版记忆管理器"""
    print('🧪 测试增强版三层记忆管理器')
    print('=' * 40)
    
    # 添加测试数据
    test_memories = [
        '今天完成了智能模型路由系统开发',
        '语义可视化模块基本完成',
        '定时汇报机制已配置',
        '系统运行稳定，功能完整'
    ]
    
    for memory in test_memories:
        result = memory_manager.add_memory(memory, 'test')
        print(f'✅ 添加记忆: {result}')
    
    # 显示系统状态
    status = memory_manager.get_system_status()
    print(f'📊 系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}')
    
    # 搜索测试
    search_results = memory_manager.search_memories('系统')
    print(f'🔍 搜索结果: {len(search_results)} 条')
    for result in search_results:
        print(f'  - {result["content"]} (相关性: {result["relevance"]:.2f})')
    
    return status

if __name__ == "__main__":
    test_enhanced_memory()
