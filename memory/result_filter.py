#!/usr/bin/env python3
"""
result_filter.py - 结果过滤系统
按（相似度 × 引力值）排序，过滤低相关性结果
"""

from typing import List, Dict, Any

class ResultFilter:
    """结果过滤系统"""
    
    def __init__(self):
        self.similarity_threshold = 0.3  # 相似度阈值
        self.score_threshold = 0.3        # 综合评分阈值
    
    def filter_results(self, results: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """
        过滤和排序结果
        """
        if not results:
            return []
        
        # 1. 计算综合评分
        filtered_results = self._calculate_scores(results)
        
        # 2. 过滤低相似度
        filtered_results = self._filter_by_similarity(filtered_results)
        
        # 3. 过滤低综合评分
        filtered_results = self._filter_by_score(filtered_results)
        
        # 4. 按综合评分排序
        filtered_results = self._sort_by_score(filtered_results)
        
        # 5. 限制数量
        filtered_results = filtered_results[:limit]
        
        return filtered_results
    
    def _calculate_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算综合评分（相似度 × 引力值）
        """
        for result in results:
            similarity = result.get('similarity', 0.0)
            gravity = result.get('gravity', 1.0)
            
            # 综合评分
            result['score'] = similarity * gravity
        
        return results
    
    def _filter_by_similarity(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤低相似度结果
        """
        return [
            r for r in results 
            if r.get('similarity', 0.0) > self.similarity_threshold
        ]
    
    def _filter_by_score(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤低综合评分结果
        """
        return [
            r for r in results 
            if r.get('score', 0.0) > self.score_threshold
        ]
    
    def _sort_by_score(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按综合评分降序排序
        """
        return sorted(results, key=lambda x: x.get('score', 0.0), reverse=True)
    
    def deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重（基于记忆ID）
        """
        unique_results = []
        seen_ids = set()
        
        for result in results:
            result_id = result.get('id', '')
            
            # 如果ID不存在，使用content作为标识
            if not result_id:
                result_id = result.get('content', '')[:50]
            
            if result_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result_id)
        
        return unique_results
    
    def set_thresholds(self, similarity_threshold: float = None, score_threshold: float = None):
        """
        设置阈值
        """
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
        
        if score_threshold is not None:
            self.score_threshold = score_threshold

# 创建全局实例
result_filter = ResultFilter()

def test_result_filter():
    """测试结果过滤系统"""
    print("=" * 40)
    print("🧪 测试结果过滤系统")
    print("=" * 40)
    
    # 创建测试结果
    test_results = [
        {'id': '1', 'content': '示例记忆内容', 'similarity': 0.9, 'gravity': 1.5},
        {'id': '2', 'content': '项目架构设计', 'similarity': 0.8, 'gravity': 1.2},
        {'id': '3', 'content': '临时想法', 'similarity': 0.2, 'gravity': 0.5},
        {'id': '4', 'content': '重要决策', 'similarity': 0.85, 'gravity': 1.0},
        {'id': '5', 'content': '低相关内容', 'similarity': 0.1, 'gravity': 0.8},
        {'id': '6', 'content': '工作偏好', 'similarity': 0.7, 'gravity': 1.0}
    ]
    
    # 测试1: 计算评分
    print("\n测试1: 计算综合评分")
    result_filter._calculate_scores(test_results)
    for r in test_results:
        print(f"  ID:{r['id']} 相似度:{r['similarity']:.2f} 引力:{r['gravity']:.2f} 评分:{r['score']:.2f}")
    
    # 测试2: 过滤和排序
    print("\n测试2: 过滤和排序（限制5条）")
    filtered = result_filter.filter_results(test_results, limit=5)
    print(f"✅ 过滤后剩余{len(filtered)}条结果")
    for i, r in enumerate(filtered, 1):
        print(f"  {i}. [{r['id']}] {r['content'][:30]}... (评分:{r['score']:.2f})")
    
    # 测试3: 去重
    print("\n测试3: 去重测试")
    duplicate_results = test_results + [
        {'id': '1', 'content': '重复内容', 'similarity': 0.9, 'gravity': 1.5},  # 重复ID
        {'id': '7', 'content': '新增内容', 'similarity': 0.6, 'gravity': 0.9}
    ]
    print(f"去重前: {len(duplicate_results)}条")
    unique = result_filter.deduplicate_results(duplicate_results)
    print(f"去重后: {len(unique)}条")
    
    # 测试4: 设置阈值
    print("\n测试4: 设置阈值")
    result_filter.set_thresholds(similarity_threshold=0.5, score_threshold=0.5)
    filtered = result_filter.filter_results(test_results, limit=10)
    print(f"✅ 更高阈值后剩余{len(filtered)}条结果")
    for r in filtered:
        print(f"  [{r['id']}] {r['content'][:30]}... (评分:{r['score']:.2f})")
    
    print("\n✅ 结果过滤系统测试完成！")

if __name__ == "__main__":
    test_result_filter()