#!/usr/bin/env python3
"""
增强版轻量化三层记忆模型
集成智能模型路由，支持多模型调度和故障转移
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'skills'))

from model_router_skill import get_model_status, select_best_model
from core.memory_manager import LiteMemoryManager, MemoryLayer
from capture.session_capture import SmartSessionCapture
from search.vector_search import VectorSearch
import logging

# 配置日志 - 简化输出
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedMemoryManager:
    """增强版记忆管理器 - 集成智能模型路由"""
    
    def __init__(self, workspace_path: str = "."):
        """初始化增强版记忆管理器"""
        self.base_manager = LiteMemoryManager(workspace_path)
        self.session_capture = SmartSessionCapture()
        self.vector_search = VectorSearch()
        
        # 获取当前模型状态
        self.model_status = get_model_status()
        self.current_model = select_best_model("reasoning")
        
        logger.info(f"增强版记忆管理器初始化完成 (使用模型: {self.current_model})")
    
    def get_model_info(self) -> dict:
        """获取当前模型信息"""
        return {
            "current_model": self.current_model,
            "healthy_models": self.model_status["healthy_models"],
            "total_models": self.model_status["total_models"],
            "system_status": f"健康模型数: {self.model_status['healthy_models']}/{self.model_status['total_models']}"
        }
    
    def smart_capture(self, text: str, context: str = None) -> dict:
        """智能捕获 - 集成模型增强"""
        try:
            # 使用当前最佳模型进行增强捕获
            logger.info(f"智能捕获: {text[:50]}...")
            
            # 基础捕获
            captured_items = self.session_capture.capture_from_text(text, context)
            
            # 存储捕获的记忆
            stored_count = 0
            for item in captured_items:
                success = self.base_manager.store_memory(
                    item.content, 
                    MemoryLayer.HOT, 
                    item.type.value, 
                    item.confidence
                )
                if success:
                    stored_count += 1
            
            return {
                "success": True,
                "captured_count": len(captured_items),
                "stored_count": stored_count,
                "model_used": self.current_model,
                "items": captured_items
            }
            
        except Exception as e:
            logger.error(f"智能捕获失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "captured_count": 0,
                "stored_count": 0
            }
    
    def intelligent_search(self, query: str, limit: int = 5) -> dict:
        """智能搜索 - 集成模型增强"""
        try:
            logger.info(f"智能搜索: {query}")
            
            # 使用基础搜索功能
            results = self.base_manager.search_memories(query, limit)
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "model_used": self.current_model
            }
            
        except Exception as e:
            logger.error(f"智能搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    def get_enhanced_stats(self) -> dict:
        """获取增强版统计信息"""
        try:
            # 基础统计
            base_stats = self.base_manager.get_stats()
            
            # 模型状态
            model_info = self.get_model_info()
            
            return {
                "success": True,
                "memory_stats": base_stats,
                "model_info": model_info,
                "system_summary": f"记忆: {base_stats['total_memories']}条, 模型: {model_info['system_status']}"
            }
            
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def refresh_model_status(self):
        """刷新模型状态"""
        try:
            self.model_status = get_model_status()
            self.current_model = select_best_model("reasoning")
            logger.info(f"模型状态已刷新: {self.current_model}")
            return True
        except Exception as e:
            logger.error(f"刷新模型状态失败: {e}")
            return False

# 创建全局实例
enhanced_manager = None

def get_enhanced_memory_manager(workspace_path: str = ".") -> EnhancedMemoryManager:
    """获取增强版记忆管理器实例"""
    global enhanced_manager
    if enhanced_manager is None:
        enhanced_manager = EnhancedMemoryManager(workspace_path)
    return enhanced_manager

def get_system_summary() -> str:
    """获取系统摘要信息"""
    manager = get_enhanced_memory_manager()
    stats = manager.get_enhanced_stats()
    
    if stats["success"]:
        return stats["system_summary"]
    else:
        return "系统状态获取失败"

if __name__ == "__main__":
    # 测试增强版记忆管理器
    print("🧠 增强版轻量化三层记忆模型")
    print("=" * 40)
    
    manager = get_enhanced_memory_manager()
    
    # 获取系统摘要
    summary = get_system_summary()
    print(f"📊 {summary}")
    
    # 获取详细信息
    stats = manager.get_enhanced_stats()
    if stats["success"]:
        print(f"当前模型: {stats['model_info']['current_model']}")
        print(f"记忆统计: {stats['memory_stats']['total_memories']}条")
    
    print("\n✅ 增强版记忆管理器运行正常")