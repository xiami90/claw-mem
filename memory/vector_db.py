#!/usr/bin/env python3
"""
vector_db.py - L3向量数据库管理器
ChromaDB持久化，高性能语义搜索
"""

import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

# 数据目录
DATA_DIR = Path("/root/.openclaw/workspace/memory/vectordb")

class VectorDBManager:
    """L3向量数据库管理器 - ChromaDB持久化"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.chromadb_available = False
        self.chroma_client = None
        self.collection = None
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试初始化ChromaDB
        self._init_chromadb()
    
    def _init_chromadb(self):
        """初始化ChromaDB"""
        try:
            import chromadb
            
            # 创建持久化客户端
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.data_dir)
            )
            
            # 获取或创建集合
            self.collection = self.chroma_client.get_or_create_collection(
                name="memories",
                metadata={"description": "记忆向量数据库"}
            )
            
            self.chromadb_available = True
            print("✅ ChromaDB初始化成功")
            
        except ImportError:
            print("⚠️️ ChromaDB未安装，将使用回退方案")
            self.chromadb_available = False
        except Exception as e:
            print(f"⚠️️ ChromaDB初始化失败: {e}")
            self.chromadb_available = False
    
    def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """添加记忆到向量数据库"""
        if not self.chromadb_available:
            return {
                'success': False,
                'message': 'ChromaDB不可用，请检查安装',
                'fallback': True
            }
        
        try:
            # 生成唯一ID
            memory_id = str(uuid.uuid4())
            
            # 准备元数据
            metadatas = metadata or {}
            metadatas.update({
                'timestamp': str(datetime.datetime.now().isoformat())
            })
            
            # 添加到集合
            self.collection.add(
                documents=[content],
                metadatas=[metadatas],
                ids=[memory_id]
            )
            
            return {
                'success': True,
                'memory_id': memory_id,
                'layer': 'L3',
                'storage': 'chromadb'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'添加失败: {str(e)}'
            }
    
    def search_memory(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """向量语义搜索"""
        if not self.chromadb_available:
            print("⚠️️ ChromaDB不可用，回退到L2语义检索")
            return []  # 返回空，让上层回退
        
        try:
            # 执行向量搜索
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # 格式化结果
            formatted_results = []
            
            if results and results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    if i < len(results['documents'][0]):
                        formatted_results.append({
                            'id': memory_id,
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                            'layer': 'L3',
                            'source': 'chromadb'
                        })
            
            return formatted_results
            
        except Exception as e:
            print(f"⚠️️ 搜索失败: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """删除记忆"""
        if not self.chromadb_available:
            return {
                'success': False,
                'message': 'ChromaDB不可用'
            }
        
        try:
            self.collection.delete(ids=[memory_id])
            
            return {
                'success': True,
                'memory_id': memory_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'删除失败: {str(e)}'
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.chromadb_available:
            return {
                'available': False,
                'message': 'ChromaDB不可用',
                'data_directory': str(self.data_dir)
            }
        
        try:
            # 获取集合数量
            count = self.collection.count()
            
            return {
                'available': True,
                'total_memories': count,
                'data_directory': str(self.data_dir),
                'collection_name': self.collection.name
            }
            
        except Exception as e:
            return {
                'available': False,
                'message': f'获取统计失败: {str(e)}'
            }

# 创建全局实例
vector_db_manager = VectorDBManager()

def test_vector_db():
    """测试向量数据库"""
    print("=" * 40)
    print("🧪 测试L3向量数据库管理器")
    print("=" * 40)
    
    if not vector_db_manager.chromadb_available:
        print("⚠️️ ChromaDB不可用，跳过测试")
        return
    
    # 测试添加记忆
    print("\n测试1: 添加记忆")
    test_memories = [
        "用户喜欢在早上处理重要工作，下午学习AI技术",
        "坚持长期价值投资，关注基本面优秀的公司",
        "TradingAgents-CN项目正在部署中，需要配置API密钥",
        "用户偏好已记录"
    ]
    
    added_ids = []
    for content in test_memories:
        result = vector_db_manager.add_memory(
            content,
            metadata={'category': 'test'}
        )
        if result['success']:
            added_ids.append(result['memory_id'])
            print(f"✅ 添加成功: ID={result['memory_id'][:8]}...")
        else:
            print(f"❌ 添加失败: {result['message']}")
    
    # 测试搜索
    print("\n测试2: 语义搜索")
    query = "投资"
    results = vector_db_manager.search_memory(query, n_results=3)
    print(f"🔍 搜索'{query}': 找到{len(results)}条结果")
    for r in results:
        print(f"   - {r['content'][:40]}...")
    
    # 测试统计
    print("\n测试3: 统计信息")
    stats = vector_db_manager.get_stats()
    print(f"📊 总记忆数: {stats['total_memories']}")
    print(f"   数据目录: {stats['data_directory']}")
    print(f"   集合名称: {stats['collection_name']}")
    
    print("\n✅ 向量数据库测试完成！")

if __name__ == "__main__":
    import datetime  # 需要导入datetime
    test_vector_db()