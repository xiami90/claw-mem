#!/usr/bin/env python3
"""
OpenClaw 轻量化三层记忆模型 - 测试套件
Test Suite for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.memory_manager import LiteMemoryManager, MemoryItem, MemoryCategory
from capture.session_capture import SmartSessionCapture, CapturedItem, CaptureType
from search.vector_search import VectorSearch, SearchResult


class TestLiteMemoryManager(unittest.TestCase):
    """测试 LiteMemoryManager 类"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_manager = LiteMemoryManager(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.memory_manager)
        self.assertEqual(self.memory_manager.workspace, Path(self.temp_dir))
        self.assertTrue(self.memory_manager.memory_dir.exists())
        self.assertTrue(self.memory_manager.session_file.exists())
    
    def test_capture_from_text_decision(self):
        """测试从文本捕获决策信息"""
        text = "我们决定使用React作为前端框架，而不是Vue。"
        memories = self.memory_manager.capture_from_text(text)
        
        self.assertGreater(len(memories), 0)
        self.assertEqual(memories[0].category, MemoryCategory.DECISION)
        self.assertIn("React", memories[0].content)
        self.assertGreater(memories[0].importance, 0.7)
    
    def test_capture_from_text_preference(self):
        """测试从文本捕获偏好信息"""
        text = "用户偏好深色主题界面，不喜欢过于复杂的设计。"
        memories = self.memory_manager.capture_from_text(text)
        
        self.assertGreater(len(memories), 0)
        self.assertEqual(memories[0].category, MemoryCategory.PREFERENCE)
        self.assertIn("深色主题", memories[0].content)
    
    def test_capture_from_text_plan(self):
        """测试从文本捕获计划信息"""
        text = "下一步计划完成API接口开发，目标是在下周完成。"
        memories = self.memory_manager.capture_from_text(text)
        
        self.assertGreater(len(memories), 0)
        self.assertEqual(memories[0].category, MemoryCategory.PLAN)
        self.assertIn("API接口开发", memories[0].content)
    
    def test_store_memory(self):
        """测试存储记忆"""
        memory_item = MemoryItem(
            id="test_001",
            content="测试记忆内容",
            category=MemoryCategory.FACT,
            importance=0.8,
            timestamp=datetime.now()
        )
        
        success = self.memory_manager.store_memory(memory_item)
        self.assertTrue(success)
    
    def test_search_memories(self):
        """测试搜索记忆"""
        # 先存储一些测试记忆
        test_memories = [
            MemoryItem("test_1", "React前端框架", MemoryCategory.DECISION, 0.8, datetime.now()),
            MemoryItem("test_2", "Vue.js技术栈", MemoryCategory.DECISION, 0.7, datetime.now()),
            MemoryItem("test_3", "Python后端开发", MemoryCategory.FACT, 0.6, datetime.now())
        ]
        
        for memory in test_memories:
            self.memory_manager.store_memory(memory)
        
        # 搜索相关记忆
        results = self.memory_manager.search_memories("前端框架", limit=3)
        self.assertGreater(len(results), 0)
        self.assertIn("React", results[0].content)
    
    def test_auto_maintenance(self):
        """测试自动维护"""
        # 存储一些测试记忆
        test_memory = MemoryItem(
            "test_maintenance",
            "测试维护功能",
            MemoryCategory.GENERAL,
            0.3,  # 低重要性
            datetime.now()
        )
        self.memory_manager.store_memory(test_memory)
        
        # 执行维护
        self.memory_manager.auto_maintenance()
        
        # 验证维护功能执行（这里主要测试不抛出异常）
        self.assertTrue(True)


class TestSmartSessionCapture(unittest.TestCase):
    """测试 SmartSessionCapture 类"""
    
    def setUp(self):
        """测试前设置"""
        self.capture = SmartSessionCapture()
    
    def test_capture_decision(self):
        """测试捕获决策"""
        text = "我决定使用Django作为后端框架，因为它更适合快速开发。"
        items = self.capture.capture_from_text(text)
        
        decision_items = [item for item in items if item.type == CaptureType.DECISION]
        self.assertGreater(len(decision_items), 0)
        self.assertIn("Django", decision_items[0].content)
    
    def test_capture_preference(self):
        """测试捕获偏好"""
        text = "我更喜欢简洁的代码风格，不喜欢过度工程化。"
        items = self.capture.capture_from_text(text)
        
        preference_items = [item for item in items if item.type == CaptureType.PREFERENCE]
        self.assertGreater(len(preference_items), 0)
        self.assertIn("简洁", preference_items[0].content)
    
    def test_capture_fact(self):
        """测试捕获事实"""
        text = "重要：API接口需要在本周五之前完成开发。"
        items = self.capture.capture_from_text(text)
        
        fact_items = [item for item in items if item.type == CaptureType.FACT]
        self.assertGreater(len(fact_items), 0)
        self.assertIn("API接口", fact_items[0].content)
    
    def test_capture_plan(self):
        """测试捕获计划"""
        text = "下一步计划完成数据库设计，然后开始后端开发。"
        items = self.capture.capture_from_text(text)
        
        plan_items = [item for item in items if item.type == CaptureType.PLAN]
        self.assertGreater(len(plan_items), 0)
        self.assertIn("数据库设计", plan_items[0].content)
    
    def test_confidence_calculation(self):
        """测试置信度计算"""
        text = "我决定使用Python作为主要开发语言。"
        items = self.capture.capture_from_text(text)
        
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertGreaterEqual(item.confidence, 0.6)  # 最小置信度
            self.assertLessEqual(item.confidence, 1.0)     # 最大置信度
    
    def test_context_awareness(self):
        """测试上下文感知"""
        # 提供上下文信息
        context = "正在讨论前端技术选型"
        text = "我们决定使用React，因为它有更好的生态系统。"
        
        items = self.capture.capture_from_text(text, context)
        
        self.assertGreater(len(items), 0)
        # 验证捕获到了相关内容
        relevant_items = [item for item in items if "React" in item.content]
        self.assertGreater(len(relevant_items), 0)


class TestVectorSearch(unittest.TestCase):
    """测试 VectorSearch 类"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.search_engine = VectorSearch(index_path=f"{self.temp_dir}/test.index")
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_text_to_vector(self):
        """测试文本向量化"""
        text = "React前端开发框架"
        vector = self.search_engine.text_to_vector(text)
        
        self.assertEqual(len(vector), 384)  # 默认维度
        self.assertFalse(all(v == 0 for v in vector))  # 不是零向量
    
    def test_add_vector(self):
        """测试添加向量"""
        content = "React是用于构建用户界面的JavaScript库"
        vector_id = "test_vector_1"
        category = "tech"
        metadata = {"type": "framework", "language": "javascript"}
        
        success = self.search_engine.add_vector(vector_id, content, category, metadata)
        self.assertTrue(success)
    
    def test_search_similar(self):
        """测试相似度搜索"""
        # 添加测试向量
        test_data = [
            ("vec_1", "React前端框架", "frontend"),
            ("vec_2", "Vue.js技术栈", "frontend"),
            ("vec_3", "Python后端开发", "backend"),
            ("vec_4", "Django Web框架", "backend")
        ]
        
        for vec_id, content, category in test_data:
            self.search_engine.add_vector(vec_id, content, category)
        
        # 搜索相关向量
        query = "前端开发框架"
        results = self.search_engine.search_similar(query, limit=3)
        
        self.assertGreater(len(results), 0)
        self.assertIn("React", results[0].content)
    
    def test_search_by_category(self):
        """测试按分类搜索"""
        # 添加不同分类的向量
        self.search_engine.add_vector("tech_1", "React开发", "technology")
        self.search_engine.add_vector("business_1", "项目管理", "business")
        
        # 按分类搜索
        results = self.search_engine.search_by_category("technology", limit=5)
        
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].category, "technology")
    
    def test_get_suggestions(self):
        """测试获取搜索建议"""
        # 添加一些向量
        self.search_engine.add_vector("sug_1", "前端开发最佳实践", "best_practice")
        self.search_engine.add_vector("sug_2", "前端框架对比分析", "analysis")
        
        # 获取搜索建议
        query = "前端"
        suggestions = self.search_engine.get_suggestions(query, limit=3)
        
        self.assertGreater(len(suggestions), 0)
        for suggestion in suggestions:
            self.assertGreater(suggestion.relevance, 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_manager = LiteMemoryManager(self.temp_dir)
        self.capture = SmartSessionCapture()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 捕获会话
        conversation = """
        用户：我们决定使用React作为前端框架，因为它有更好的生态系统。
        助手：好的，React确实是个不错的选择。还有其他偏好吗？
        用户：我偏好简洁的代码风格，记住这一点很重要。
        助手：明白了，我会记住您偏好简洁的代码风格。
        """
        
        # 2. 智能捕获
        captured_items = self.capture.capture_from_text(conversation)
        self.assertGreater(len(captured_items), 0)
        
        # 3. 存储记忆
        stored_count = 0
        for item in captured_items:
            success = self.memory_manager.store_memory(item)
            if success:
                stored_count += 1
        
        self.assertGreater(stored_count, 0)
        
        # 4. 搜索记忆
        search_results = self.memory_manager.search_memories("React框架")
        self.assertGreater(len(search_results), 0)
        
        # 5. 验证搜索结果
        react_results = [r for r in search_results if "React" in r.content]
        self.assertGreater(len(react_results), 0)


if __name__ == '__main__':
    # 设置测试日志级别
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)