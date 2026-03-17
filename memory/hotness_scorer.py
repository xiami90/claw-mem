#!/usr/bin/env python3
"""
hotness_scorer.py - 热度评分模块
直接借鉴 OpenViking 的 hotness_score 实现

功能：
1. 计算记忆热度评分
2. 整合到现有衰减机制
3. 支持访问频率 + 时间衰减
"""

import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 热度评分 ====================
# 直接借鉴 OpenViking memory_lifecycle.py

DEFAULT_HALF_LIFE_DAYS: float = 7.0


def hotness_score(
    active_count: int,
    updated_at: Optional[datetime],
    now: Optional[datetime] = None,
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS
) -> float:
    """
    计算 0.0-1.0 热度评分 - 直接借鉴 OpenViking
    
    公式：
        score = sigmoid(log1p(active_count)) * time_decay(updated_at)
    
    * sigmoid 将 log1p(active_count) 映射到 (0, 1)
    * time_decay 是指数衰减，可配置半衰期
    
    Args:
        active_count: 访问次数
        updated_at: 最后更新时间
        now: 当前时间（用于测试）
        half_life_days: 半衰期（天）
    
    Returns:
        0.0-1.0 之间的热度评分
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    # --- 频率分量 ---
    # sigmoid(log1p(active_count))
    freq = 1.0 / (1.0 + math.exp(-math.log1p(active_count)))
    
    # --- 时间衰减分量 ---
    if updated_at is None:
        return 0.0
    
    # 标准化为 UTC 时区
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    
    age_days = max((now - updated_at).total_seconds() / 86400.0, 0.0)
    decay_rate = math.log(2) / half_life_days
    recency = math.exp(-decay_rate * age_days)
    
    return freq * recency


# ==================== 记忆重要性评分器 ====================

@dataclass
class ImportanceScore:
    """重要性评分结果"""
    hotness: float           # 热度评分 (0-1)
    priority_bonus: float    # 优先级加成
    total: float             # 总分
    level: str               # 等级 (critical/high/medium/low)
    
    def to_dict(self) -> dict:
        return {
            "hotness": self.hotness,
            "priority_bonus": self.priority_bonus,
            "total": self.total,
            "level": self.level
        }


class ImportanceScorer:
    """
    记忆重要性评分器
    
    整合：
    1. 热度评分（OpenViking）
    2. 优先级加成
    3. 自定义衰减
    """
    
    # 优先级加成配置
    PRIORITY_BONUS = {
        "critical": 0.3,   # 关键记忆
        "high": 0.2,       # 高优先
        "medium": 0.0,     # 中等
        "low": -0.1,       # 低优先
        "archive": -0.2    # 归档
    }
    
    # 半衰期配置（按记忆类型）
    HALF_LIFE_BY_CATEGORY = {
        "个人": 30.0,       # 个人信息长期保留
        "投资": 14.0,       # 投资相关中等保留
        "项目": 21.0,       # 项目信息
        "偏好": 60.0,       # 用户偏好长期保留
        "default": 7.0      # 默认
    }
    
    def __init__(self):
        pass
    
    def calculate_importance(
        self,
        active_count: int,
        updated_at: datetime,
        priority: str = "medium",
        category: str = "default"
    ) -> ImportanceScore:
        """
        计算记忆重要性
        
        Args:
            active_count: 访问次数
            updated_at: 最后更新时间
            priority: 优先级
            category: 分类
        
        Returns:
            ImportanceScore: 重要性评分
        """
        # 获取半衰期
        half_life = self.HALF_LIFE_BY_CATEGORY.get(category, self.HALF_LIFE_BY_CATEGORY["default"])
        
        # 计算热度
        hotness = hotness_score(active_count, updated_at, half_life_days=half_life)
        
        # 获取优先级加成
        priority_bonus = self.PRIORITY_BONUS.get(priority, 0.0)
        
        # 总分
        total = max(0.0, min(1.0, hotness + priority_bonus))
        
        # 确定等级
        if total >= 0.8:
            level = "critical"
        elif total >= 0.6:
            level = "high"
        elif total >= 0.3:
            level = "medium"
        else:
            level = "low"
        
        return ImportanceScore(
            hotness=hotness,
            priority_bonus=priority_bonus,
            total=total,
            level=level
        )
    
    def should_promote(self, score: ImportanceScore) -> bool:
        """判断是否应该提升优先级"""
        return score.total >= 0.7 and score.hotness >= 0.5
    
    def should_archive(self, score: ImportanceScore) -> bool:
        """判断是否应该归档"""
        return score.total < 0.1


# ==================== 记忆生命周期管理 ====================

class MemoryLifecycleManager:
    """
    记忆生命周期管理器
    
    借鉴 OpenViking 的冷热分层
    """
    
    def __init__(self, scorer: ImportanceScorer = None):
        self.scorer = scorer or ImportanceScorer()
    
    def classify_memories(self, memories: list) -> Dict[str, list]:
        """
        分类记忆
        
        Args:
            memories: 记忆列表，每个记忆需包含：
                - access_count: 访问次数
                - last_access: 最后访问时间
                - priority: 优先级
                - category: 分类
        
        Returns:
            分类结果：{"hot": [], "warm": [], "cold": []}
        """
        result = {
            "hot": [],      # 热记忆（高热度）
            "warm": [],     # 温记忆（中等）
            "cold": []      # 冷记忆（低热度）
        }
        
        for memory in memories:
            # 解析时间
            last_access = memory.get("last_access")
            if isinstance(last_access, str):
                last_access = datetime.fromisoformat(last_access)
            elif not isinstance(last_access, datetime):
                last_access = datetime.now()
            
            # 计算重要性
            score = self.scorer.calculate_importance(
                active_count=memory.get("access_count", 0),
                updated_at=last_access,
                priority=memory.get("priority", "medium"),
                category=memory.get("category", "default")
            )
            
            # 分类
            memory_with_score = {**memory, "importance": score.to_dict()}
            
            if score.total >= 0.6:
                result["hot"].append(memory_with_score)
            elif score.total >= 0.3:
                result["warm"].append(memory_with_score)
            else:
                result["cold"].append(memory_with_score)
        
        return result
    
    def get_archive_candidates(self, memories: list) -> list:
        """获取归档候选"""
        return [
            m for m in memories
            if self.scorer.should_archive(
                self.scorer.calculate_importance(
                    m.get("access_count", 0),
                    datetime.fromisoformat(m["last_access"]) if isinstance(m.get("last_access"), str) else datetime.now(),
                    m.get("priority", "medium"),
                    m.get("category", "default")
                )
            )
        ]


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("热度评分测试")
    print("=" * 60)
    
    # 测试热度评分
    print("\n📍 测试热度评分:")
    now = datetime.now(timezone.utc)
    
    # 新记忆（刚访问）
    score1 = hotness_score(active_count=1, updated_at=now, half_life_days=7)
    print(f"   新记忆(1次访问): {score1:.3f}")
    
    # 热门记忆（多次访问）
    score2 = hotness_score(active_count=10, updated_at=now, half_life_days=7)
    print(f"   热门记忆(10次访问): {score2:.3f}")
    
    # 旧记忆（7天前访问）
    from datetime import timedelta
    old_time = now - timedelta(days=7)
    score3 = hotness_score(active_count=10, updated_at=old_time, half_life_days=7)
    print(f"   旧记忆(10次访问, 7天前): {score3:.3f}")
    
    # 测试重要性评分器
    print("\n📍 测试重要性评分器:")
    scorer = ImportanceScorer()
    
    test_memories = [
        {"access_count": 5, "last_access": now, "priority": "high", "category": "投资"},
        {"access_count": 1, "last_access": old_time, "priority": "low", "category": "default"},
        {"access_count": 20, "last_access": now, "priority": "critical", "category": "个人"},
    ]
    
    for m in test_memories:
        score = scorer.calculate_importance(
            m["access_count"],
            m["last_access"],
            m["priority"],
            m["category"]
        )
        print(f"   访问{m['access_count']}次, {m['priority']}, {m['category']}: "
              f"热度={score.hotness:.3f}, 总分={score.total:.3f}, 等级={score.level}")
    
    # 测试生命周期管理
    print("\n📍 测试生命周期管理:")
    lifecycle = MemoryLifecycleManager()
    
    memories = [
        {"id": 1, "access_count": 20, "last_access": now, "priority": "high", "category": "投资"},
        {"id": 2, "access_count": 5, "last_access": now - timedelta(days=3), "priority": "medium", "category": "项目"},
        {"id": 3, "access_count": 0, "last_access": now - timedelta(days=30), "priority": "low", "category": "default"},
    ]
    
    classified = lifecycle.classify_memories(memories)
    print(f"   热记忆: {len(classified['hot'])}条")
    print(f"   温记忆: {len(classified['warm'])}条")
    print(f"   冷记忆: {len(classified['cold'])}条")
    
    archive_candidates = lifecycle.get_archive_candidates(memories)
    print(f"   归档候选: {len(archive_candidates)}条")
    
    print("\n✅ 测试完成")
