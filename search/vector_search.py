#!/usr/bin/env python3
"""
OpenClaw 轻量化三层记忆模型 - 向量搜索引擎
Vector Search Engine for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
@description: 基于向量的语义搜索和智能推荐系统
"""

import numpy as np
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import pickle
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    content: str
    score: float
    category: str
    timestamp: datetime
    metadata: Dict[str, Any]
    id: str


@dataclass
class SearchSuggestion:
    """搜索建议数据结构"""
    suggestion: str
    relevance: float
    category: str
    reason: str


class VectorSearch:
    """
    向量搜索引擎
    
    功能特性：
    - 基于向量的语义搜索
    - 智能相关性排序
    - 上下文感知推荐
    - 实时索引更新
    - 多维度相似度计算
    """
    
    def __init__(self, index_path: Optional[str] = None, dimension: int = 384):
        """
        初始化向量搜索引擎
        
        Args:
            index_path: 索引文件路径
            dimension: 向量维度
        """
        self.index_path = Path(index_path) if index_path else Path(".memory/vectors.index")
        self.dimension = dimension
        self.index = {}
        self.metadata = {}
        self.word_vectors = {}
        
        # 创建索引目录
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化搜索引擎
        self._init_search_engine()
        
        logger.info(f"✅ VectorSearch 初始化完成 - 维度: {dimension}, 索引路径: {self.index_path}")
    
    def _init_search_engine(self):
        """初始化搜索引擎"""
        # 加载或创建索引
        if self.index_path.exists():
            self._load_index()
        else:
            self._create_new_index()
        
        # 初始化词向量（简化版）
        self._init_word_vectors()
    
    def _create_new_index(self):
        """创建新索引"""
        logger.info("🆕 创建新的向量索引")
        self.index = {
            "version": "1.0.0",
            "dimension": self.dimension,
            "created_at": datetime.now().isoformat(),
            "vectors": {},
            "metadata": {},
            "statistics": {
                "total_vectors": 0,
                "categories": {},
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _load_index(self):
        """加载现有索引"""
        try:
            with open(self.index_path, 'rb') as f:
                self.index = pickle.load(f)
            
            logger.info(f"📂 向量索引加载成功 - 向量数: {self.index['statistics']['total_vectors']}")
            
        except Exception as e:
            logger.error(f"❌ 向量索引加载失败: {e}")
            self._create_new_index()
    
    def _save_index(self):
        """保存索引"""
        try:
            with open(self.index_path, 'wb') as f:
                pickle.dump(self.index, f)
            
            logger.info("💾 向量索引保存成功")
            
        except Exception as e:
            logger.error(f"❌ 向量索引保存失败: {e}")
    
    def _init_word_vectors(self):
        """初始化词向量（简化实现）"""
        # 这是一个简化的词向量实现
        # 在实际应用中，应该使用预训练的词向量模型
        
        # 基础词向量词典
        base_words = {
            # 技术词汇
            "技术": [0.8, 0.2, 0.1, 0.0] * 96,  # 384维
            "代码": [0.7, 0.3, 0.1, 0.0] * 96,
            "项目": [0.6, 0.4, 0.2, 0.1] * 96,
            "开发": [0.7, 0.2, 0.3, 0.0] * 96,
            "架构": [0.8, 0.1, 0.4, 0.2] * 96,
            
            # 决策词汇
            "决定": [0.9, 0.1, 0.8, 0.7] * 96,
            "选择": [0.8, 0.2, 0.7, 0.6] * 96,
            "确定": [0.9, 0.1, 0.9, 0.8] * 96,
            "采用": [0.7, 0.3, 0.6, 0.5] * 96,
            
            # 偏好词汇
            "偏好": [0.8, 0.6, 0.7, 0.3] * 96,
            "喜欢": [0.7, 0.7, 0.6, 0.2] * 96,
            "合适": [0.6, 0.8, 0.5, 0.4] * 96,
            "更好": [0.7, 0.6, 0.8, 0.5] * 96,
            
            # 重要性词汇
            "重要": [0.9, 0.2, 0.9, 0.9] * 96,
            "关键": [0.9, 0.1, 0.9, 0.8] * 96,
            "核心": [0.8, 0.2, 0.8, 0.7] * 96,
            "记住": [0.8, 0.3, 0.7, 0.8] * 96,
            
            # 时间词汇
            "计划": [0.7, 0.5, 0.8, 0.6] * 96,
            "目标": [0.8, 0.4, 0.9, 0.7] * 96,
            "下一步": [0.6, 0.6, 0.7, 0.5] * 96,
            "准备": [0.6, 0.5, 0.6, 0.4] * 96,
        }
        
        self.word_vectors = base_words
        logger.info(f"✅ 词向量初始化完成 - 词汇数: {len(base_words)}")
    
    def text_to_vector(self, text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        if not text or not text.strip():
            return np.zeros(self.dimension)
        
        # 简单的文本向量化实现
        words = self._tokenize(text)
        
        if not words:
            return np.zeros(self.dimension)
        
        # 基于词向量的平均池化
        vectors = []
        for word in words:
            if word in self.word_vectors:
                vectors.append(np.array(self.word_vectors[word]))
            else:
                # 为未知词生成随机向量
                np.random.seed(hash(word) % 2**32)
                random_vector = np.random.randn(self.dimension) * 0.1
                vectors.append(random_vector)
        
        if vectors:
            return np.mean(vectors, axis=0)
        else:
            return np.zeros(self.dimension)
    
    def _tokenize(self, text: str) -> List[str]:
        """简单的中文分词"""
        # 移除标点符号
        import re
        text = re.sub(r'[，。！？；：]', '', text)
        
        # 简单的分词：按空格和常见分隔符分割
        words = re.split(r'[\s\,\;\:]+', text)
        
        # 过滤空字符串和短词
        words = [word.strip() for word in words if word.strip() and len(word.strip()) > 1]
        
        return words
    
    def search(self, query: str, limit: int = 5, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        向量搜索
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            min_score: 最小相似度分数
            
        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"🔍 向量搜索 - 查询: '{query}', 限制: {limit}")
            
            if not self.index or not self.index['vectors']:
                logger.warning("向量索引为空")
                return []
            
            # 将查询转换为向量
            query_vector = self.text_to_vector(query)
            
            if np.all(query_vector == 0):
                logger.warning("查询向量为零，无法搜索")
                return []
            
            results = []
            
            # 计算与所有向量的相似度
            for vector_id, vector_data in self.index['vectors'].items():
                stored_vector = np.array(vector_data['vector'])
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(query_vector, stored_vector)
                
                if similarity >= min_score:
                    results.append({
                        "id": vector_id,
                        "content": vector_data['content'],
                        "score": float(similarity),
                        "metadata": vector_data.get('metadata', {}),
                        "timestamp": vector_data.get('timestamp', '')
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 限制结果数量
            final_results = results[:limit]
            
            logger.info(f"✅ 向量搜索完成 - 找到 {len(final_results)} 条相关记忆")
            return final_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def add_vector(self, vector_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        添加向量到索引
        
        Args:
            vector_id: 向量ID
            content: 内容文本
            metadata: 元数据
            
        Returns:
            是否成功添加
        """
        try:
            # 将内容转换为向量
            vector = self.text_to_vector(content)
            
            if np.all(vector == 0):
                logger.warning(f"内容 '{content}' 转换为零向量，跳过")
                return False
            
            # 添加到索引
            self.index['vectors'][vector_id] = {
                'vector': vector.tolist(),
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # 更新统计信息
            self.index['statistics']['total_vectors'] += 1
            
            logger.info(f"✅ 向量添加成功: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"向量添加失败: {e}")
            return False
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            # 计算点积
            dot_product = np.dot(vec1, vec2)
            
            # 计算范数
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 计算余弦相似度
            similarity = dot_product / (norm1 * norm2)
            
            # 确保在合理范围内
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"余弦相似度计算失败: {e}")
            return 0.0