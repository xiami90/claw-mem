#!/usr/bin/env python3
"""
embedding_engine.py - 统一的 Embedding 引擎
支持多种后端：
1. 火山引擎 ARK API
2. OpenAI API  
3. 本地关键词+BM25 回退
"""

import os
import re
import math
import hashlib
from typing import List, Dict, Any, Optional

# 配置
ARK_API_KEY = os.environ.get("ARK_API_KEY", "3afcac3d-2249-4463-9958-7c8b5de8155d")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"

class BM25:
    """BM25 关键词搜索算法 - 本地回退方案"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = {}
        self.doc_lens = []
        self.avgdl = 0
        self.N = 0
        self.corpus = []
    
    def index(self, corpus: List[str]):
        """建立索引"""
        self.corpus = corpus
        self.N = len(corpus)
        self.doc_freqs = {}
        self.doc_lens = []
        
        # 统计词频
        for doc in corpus:
            words = self._tokenize(doc)
            self.doc_lens.append(len(words))
            
            # 文档频率
            seen = set()
            for word in words:
                if word not in seen:
                    seen.add(word)
                    self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
        
        self.avgdl = sum(self.doc_lens) / self.N if self.N > 0 else 0
    
    def _tokenize(self, text: str) -> List[str]:
        """分词（简单中文分词）"""
        # 简单分词：按标点和空格分割，再按字符n-gram
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # 字符级n-gram（对中文更友好）
        result = []
        for word in words:
            if len(word) <= 3:
                result.append(word)
            else:
                # 生成2-gram和3-gram
                for i in range(len(word) - 1):
                    result.append(word[i:i+2])
                for i in range(len(word) - 2):
                    result.append(word[i:i+3])
        return result
    
    def score(self, query: str, doc_idx: int) -> float:
        """计算query对doc的BM25分数"""
        query_terms = self._tokenize(query.lower())
        doc = self.corpus[doc_idx]
        doc_words = self._tokenize(doc.lower())
        doc_len = self.doc_lens[doc_idx]
        
        score = 0.0
        for term in query_terms:
            if term in doc_words:
                tf = doc_words.count(term)
                df = self.doc_freqs.get(term, 0)
                if df == 0:
                    continue
                
                # IDF
                idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1)
                
                # TF normalization
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))
                
                score += idf * tf_norm
        
        return score


class EmbeddingEngine:
    """
    统一的 Embedding 引擎
    
    使用方式：
    engine = EmbeddingEngine()
    
    # 生成向量
    vector = engine.encode("文本内容")
    
    # 计算相似度
    similarity = engine.cosine_similarity(vec1, vec2)
    """
    
    def __init__(self, use_remote: bool = True):
        self.use_remote = use_remote
        self.bm25 = BM25()
        self.bm25_indexed = False
        self._init_bm25_index()
    
    def _init_bm25_index(self):
        """初始化 BM25 索引"""
        # 预定义一些常见的"记忆"关键词模式
        common_patterns = [
            "生日", "喜好", "工作", "学习", "投资", "预测", "分析",
            "用户", "上海", "北京", "公司", "比亚迪", "汇川",
            "孙子兵法", "纪效新书", "RAG", "Embedding"
        ]
        self.bm25.index(common_patterns)
        self.bm25_indexed = True
    
    def encode(self, text: str) -> List[float]:
        """
        生成文本的向量表示
        优先使用远程API，失败则使用本地embedding
        """
        if self.use_remote:
            # 尝试使用火山引擎API
            vector = self._encode_remote(text)
            if vector:
                return vector
        
        # 回退到本地（MD5 + n-gram 伪向量）
        return self._encode_local(text)
    
    def _encode_remote(self, text: str) -> Optional[List[float]]:
        """使用火山引擎 ARK API 生成向量"""
        import urllib.request
        import json
        
        try:
            url = f"{ARK_BASE_URL}/embeddings"
            data = json.dumps({
                "model": "doubao-embedding-text-240715",
                "input": text
            }).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ARK_API_KEY}"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                if "data" in result and len(result["data"]) > 0:
                    return result["data"][0]["embedding"]
        except Exception as e:
            print(f"⚠️ ARK API 调用失败: {e}")
        
        return None
    
    def _encode_local(self, text: str) -> List[float]:
        """
        本地伪向量生成
        使用字符n-gram + 关键词权重 + 时间实体增强
        """
        # 生成128维向量
        vector = [0.0] * 128
        
        # 1. 字符级n-gram（捕获局部相似性）
        text_lower = text.lower()
        for i in range(len(text_lower) - 1):
            ngram = text_lower[i:i+2]
            idx = hash(ngram) % 128
            vector[idx] += 0.3
        
        for i in range(len(text_lower) - 2):
            ngram = text_lower[i:i+3]
            idx = hash(ngram) % 128
            vector[idx] += 0.4
        
        # 2. 关键词检测（增强版）
        keywords = {
            # 基本实体
            "生日": 0.9, "工作": 0.8, "学习": 0.8, "投资": 0.8,
            "预测": 0.7, "分析": 0.7, "用户": 0.6, "喜欢": 0.8,
            "比亚迪": 0.9, "汇川": 0.9, "上海": 0.7, "北京": 0.7, "深圳": 0.7,
            "孙子兵法": 0.9, "纪效新书": 0.9, "RAG": 0.8, "Embedding": 0.8,
            "iPhone": 0.9, "苹果": 0.8, "小米": 0.8, "华为": 0.8,
            "茅台": 0.8, "股票": 0.8, "A股": 0.7,
            
            # 生活偏好
            "咖啡": 0.9, "拿铁": 0.9, "美式": 0.8, "偏好": 0.8,
            "城市": 0.7, "住在": 0.8, "居住": 0.8, "浦东": 0.7,
            "手机": 0.8, "电脑": 0.7, "平板": 0.6,
            
            # 时间相关关键词
            "周一": 1.0, "周二": 1.0, "周三": 1.0, "周四": 1.0, "周五": 1.0, "周六": 1.0, "周日": 1.0,
            "星期一": 1.0, "星期二": 1.0, "星期三": 1.0, "星期四": 1.0, "星期五": 1.0, "星期六": 1.0, "星期日": 1.0, "星期天": 1.0,
            "今天": 1.0, "明天": 1.0, "后天": 1.0, "昨天": 1.0, "前天": 1.0,
            "上午": 0.8, "下午": 0.8, "早上": 0.8, "晚上": 0.8, "中午": 0.8,
            "出差": 0.9, "开会": 0.9, "培训": 0.9, "发布": 0.8, "报告": 0.8,
            "会议": 0.9, "预约": 0.8, "日程": 0.8, "计划": 0.7,
            "季度": 0.8, "提交": 0.8,
            
            # 疑问词（帮助理解查询意图）
            "哪": 0.7, "什么": 0.6, "何时": 0.9, "什么时候": 0.9,
            "几点": 0.8, "哪天": 1.0, "几日": 0.9,
            "之前": 0.6, "现在": 0.7, "最近": 0.7, "以前": 0.6,
            
            # 学习相关
            "课程": 0.8, "技能": 0.8, "方法": 0.7, "效率": 0.7,
            "番茄钟": 0.9, "早起": 0.8, "复习": 0.7,
            "Python": 0.9, "编程": 0.8, "数据分析": 0.8,
        }
        
        for kw, weight in keywords.items():
            if kw in text:
                idx = hash(kw) % 128
                vector[idx] += weight
        
        # 3. 时间模式匹配增强
        import re
        time_patterns = [
            r'(\d+)年', r'(\d+)月', r'(\d+)日', r'(\d+)号',
            r'周([一二三四五六日])', r'星期([一二三四五六日天])',
            r'(上午|下午|早上|晚上|中午)',
            r'(今天|明天|后天|昨天|前天)'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                idx = hash('TIME_ENTITY') % 128
                vector[idx] += 0.8 * len(matches)
        
        # 4. 归一化
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot / (mag1 * mag2)
    
    def encode_and_score(self, query: str, texts: List[str]) -> List[Dict[str, Any]]:
        """
        对多个文本进行编码并计算与query的相似度
        
        Returns:
            List of dicts with 'text', 'score', 'vector' keys
        """
        query_vector = self.encode(query)
        
        results = []
        for text in texts:
            text_vector = self.encode(text)
            similarity = self.cosine_similarity(query_vector, text_vector)
            results.append({
                "text": text,
                "score": similarity,
                "vector": text_vector
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results


# 全局实例
embedding_engine = EmbeddingEngine()


def encode(text: str) -> List[float]:
    """快捷函数"""
    return embedding_engine.encode(text)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """快捷函数"""
    return embedding_engine.cosine_similarity(vec1, vec2)


if __name__ == "__main__":
    # 测试
    engine = EmbeddingEngine()
    
    print("=== Embedding 引擎测试 ===")
    
    # 测试本地向量
    texts = [
        "用户的生日是7月20日",
        "用户喜欢喝拿铁咖啡",
        "用户在比亚迪工作",
        "今天天气很好"
    ]
    
    query = "用户的生日是什么"
    
    results = engine.encode_and_score(query, texts)
    
    print(f"\n查询: {query}")
    print("\n相似度排序结果:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['score']:.4f}] {r['text']}")
