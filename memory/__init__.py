"""
memory - 四层记忆管理系统
L0 瞬时记忆 + L1 工作记忆 + L2 神经元记忆网 + L3 向量数据库
"""

from .l0_manager import L0MemoryManager, l0_manager
from .l2_manager import L2MemoryManager, l2_manager
from .vector_db import VectorDBManager, vector_db_manager
from .smart_compress import L1Compressor, l1_compressor

__version__ = "1.0.0"
__author__ = "DataBot"

# 全局实例
L0 = l0_manager
L1 = l1_compressor
L2 = l2_manager
L3 = vector_db_manager

__all__ = [
    'L0MemoryManager', 'l0_manager', 'L0',
    'L2MemoryManager', 'l2_manager', 'L2',
    'VectorDBManager', 'vector_db_manager', 'L3',
    'L1Compressor', 'l1_compressor', 'L1'
]