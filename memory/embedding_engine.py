#!/usr/bin/env python3
"""
embedding_engine.py - 专业向量引擎
借鉴 OpenViking 的 EmbedResult 设计

功能：
1. 集成火山引擎 Embedding API
2. 支持批量向量化
3. 向量缓存机制
4. 离线回退能力
"""

import requests
import hashlib
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 数据类 ====================
# 借鉴 OpenViking 的 EmbedResult

@dataclass
class EmbedResult:
    """
    向量嵌入结果 - 借鉴 OpenViking
    
    Attributes:
        dense_vector: 稠密向量（主要检索用）
        sparse_vector: 稀疏向量（可选，关键词增强）
        model: 使用的模型名称
        dimension: 向量维度
    """
    dense_vector: List[float]
    sparse_vector: Optional[Dict[str, float]] = None
    model: str = ""
    dimension: int = 0
    
    def __post_init__(self):
        if not self.dimension:
            self.dimension = len(self.dense_vector) if self.dense_vector else 0
        if not self.model:
            self.model = "unknown"


# ==================== 向量引擎基类 ====================

class BaseEmbedder:
    """向量引擎基类"""
    
    def embed(self, text: str) -> EmbedResult:
        raise NotImplementedError
    
    def embed_batch(self, texts: List[str]) -> List[EmbedResult]:
        return [self.embed(t) for t in texts]


# ==================== 火山引擎 Embedding ====================

class VolcengineEmbedder(BaseEmbedder):
    """
    火山引擎向量引擎
    
    支持模型：
    - doubao-embedding-vision-250615 (1024维)
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "doubao-embedding-vision-250615",
        api_base: str = "https://ark.cn-beijing.volces.com/api/v3",
        dimension: int = 1024,
        cache_file: str = None
    ):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.dimension = dimension
        self.cache_file = Path(cache_file) if cache_file else None
        
        # 向量缓存
        self._cache: Dict[str, EmbedResult] = {}
        
        # 加载缓存
        if self.cache_file and self.cache_file.exists():
            self._load_cache()
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _load_cache(self):
        """加载向量缓存"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, item in data.get("cache", {}).items():
                    self._cache[key] = EmbedResult(
                        dense_vector=item["dense_vector"],
                        model=item.get("model", self.model),
                        dimension=item.get("dimension", self.dimension)
                    )
            logger.info(f"✅ 加载向量缓存: {len(self._cache)} 条")
        except Exception as e:
            logger.warning(f"⚠️ 加载缓存失败: {e}")
    
    def _save_cache(self):
        """保存向量缓存"""
        if not self.cache_file:
            return
        
        try:
            data = {
                "cache": {
                    key: {
                        "dense_vector": result.dense_vector,
                        "model": result.model,
                        "dimension": result.dimension
                    }
                    for key, result in self._cache.items()
                },
                "last_saved": datetime.now().isoformat()
            }
            
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"💾 保存向量缓存: {len(self._cache)} 条")
        except Exception as e:
            logger.warning(f"⚠️ 保存缓存失败: {e}")
    
    def embed(self, text: str) -> EmbedResult:
        """
        生成向量嵌入
        
        Args:
            text: 输入文本
        
        Returns:
            EmbedResult: 嵌入结果
        """
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            logger.debug(f"🎯 命中缓存: {text[:30]}...")
            return self._cache[cache_key]
        
        # 调用 API
        try:
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                dense_vector = data["data"][0]["embedding"]
                
                result = EmbedResult(
                    dense_vector=dense_vector,
                    model=self.model,
                    dimension=len(dense_vector)
                )
                
                # 缓存结果
                self._cache[cache_key] = result
                self._save_cache()
                
                logger.info(f"✅ 生成向量: {text[:30]}... (维度: {len(dense_vector)})")
                return result
            else:
                logger.error(f"❌ API 错误: {response.status_code} - {response.text}")
                raise Exception(f"API 错误: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 向量生成失败: {e}")
            raise


# ==================== 本地回退引擎 ====================

class LocalEmbedder(BaseEmbedder):
    """
    本地向量引擎（回退方案）
    
    使用 MD5 哈希生成简化向量
    维度：50
    """
    
    def __init__(self, dimension: int = 50):
        self.dimension = dimension
    
    def embed(self, text: str) -> EmbedResult:
        """生成本地向量"""
        # 使用 MD5 哈希生成向量
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # 转换为浮点数向量
        vector = [float(b) / 255.0 for b in hash_bytes]
        
        # 补齐到指定维度
        while len(vector) < self.dimension:
            vector.append(0.0)
        
        return EmbedResult(
            dense_vector=vector[:self.dimension],
            model="local-md5",
            dimension=self.dimension
        )


# ==================== 智能向量引擎 ====================

class SmartEmbedder(BaseEmbedder):
    """
    智能向量引擎
    
    自动选择最优引擎：
    1. 优先使用火山引擎 API
    2. 失败时回退到本地引擎
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "doubao-embedding-vision-250615",
        api_base: str = "https://ark.cn-beijing.volces.com/api/v3",
        cache_file: str = "/root/.openclaw/workspace/memory/embedding_cache.json"
    ):
        self.cache_file = cache_file
        self._api_available = False
        
        # 初始化 API 引擎
        if api_key:
            try:
                self.api_embedder = VolcengineEmbedder(
                    api_key=api_key,
                    model=model,
                    api_base=api_base,
                    cache_file=cache_file
                )
                self._api_available = True
                logger.info("✅ 火山引擎 Embedding API 可用")
            except Exception as e:
                logger.warning(f"⚠️ 火山引擎不可用: {e}")
        else:
            logger.warning("⚠️ 未配置火山引擎 API Key")
        
        # 本地回退引擎
        self.local_embedder = LocalEmbedder()
    
    def embed(self, text: str) -> EmbedResult:
        """生成向量嵌入（智能选择引擎）"""
        if self._api_available:
            try:
                return self.api_embedder.embed(text)
            except Exception as e:
                logger.warning(f"⚠️ API 失败，回退到本地引擎: {e}")
                self._api_available = False
        
        return self.local_embedder.embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[EmbedResult]:
        """批量向量化"""
        return [self.embed(t) for t in texts]


# ==================== 工厂函数 ====================

def create_embedder(config: dict = None) -> BaseEmbedder:
    """
    创建向量引擎
    
    Args:
        config: 配置字典，包含 api_key, model, api_base
    
    Returns:
        向量引擎实例
    """
    if config is None:
        # 从配置文件读取
        config_path = Path("/root/.openclaw/workspace/memory/embedding_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
    
    api_key = config.get("api_key", "")
    model = config.get("model", "doubao-embedding-vision-250615")
    api_base = config.get("api_base", "https://ark.cn-beijing.volces.com/api/v3")
    
    return SmartEmbedder(
        api_key=api_key,
        model=model,
        api_base=api_base
    )


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("向量引擎测试")
    print("=" * 60)
    
    # 测试本地引擎
    print("\n📍 测试本地引擎:")
    local = LocalEmbedder()
    result = local.embed("测试文本")
    print(f"   维度: {result.dimension}")
    print(f"   向量前5位: {result.dense_vector[:5]}")
    
    # 测试智能引擎（无 API Key）
    print("\n📍 测试智能引擎（无 API Key，应回退到本地）:")
    smart = SmartEmbedder(api_key="")
    result = smart.embed("测试文本")
    print(f"   模型: {result.model}")
    print(f"   维度: {result.dimension}")
    
    # 测试缓存
    print("\n📍 测试缓存:")
    result2 = smart.embed("测试文本")
    print(f"   （应该命中缓存）模型: {result2.model}")
    
    print("\n✅ 测试完成")
