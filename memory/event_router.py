#!/usr/bin/env python3
"""
event_router.py - 事件路由器
借鉴 OpenViking 的 IntentAnalyzer 和 TypedQuery

功能：
1. 识别事件类型
2. 智能路由检索
3. 分层降级策略
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum
import re
from datetime import datetime
import logging

from event_directories import EventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 数据类 ====================
# 借鉴 OpenViking 的 TypedQuery

@dataclass
class RoutedQuery:
    """
    路由查询 - 借鉴 OpenViking TypedQuery
    
    Attributes:
        query: 原始查询文本
        event_type: 识别的事件类型
        target_directories: 目标目录列表
        priority: 优先级 (1-5, 1最高)
        confidence: 置信度 (0.0-1.0)
        reasoning: 识别理由
    """
    query: str
    event_type: EventType
    target_directories: List[str]
    priority: int = 3
    confidence: float = 0.5
    reasoning: str = ""
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "event_type": self.event_type.value,
            "target_directories": self.target_directories,
            "priority": self.priority,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


# ==================== 事件关键词配置 ====================

EVENT_KEYWORDS: Dict[EventType, Dict[str, float]] = {
    EventType.FINANCIAL: {
        # 股票代码
        "002594": 0.9, "比亚迪": 0.9,
        "300124": 0.9, "汇川技术": 0.9,
        "600036": 0.9, "招商银行": 0.9,
        # 金融术语
        "股票": 0.7, "预测": 0.6, "复盘": 0.8,
        "金融": 0.7, "投资": 0.7, "涨停": 0.9,
        "跌停": 0.9, "收盘": 0.8, "开盘": 0.8,
        "大盘": 0.7, "板块": 0.6, "北向": 0.7,
        # 时间词
        "早盘": 0.8, "午间": 0.8, "收盘": 0.8,
    },
    EventType.MILITARY: {
        # 书名
        "孙子兵法": 0.95, "纪效新书": 0.95,
        # 军事术语
        "兵法": 0.8, "战术": 0.7, "战略": 0.7,
        "将军": 0.6, "军队": 0.6, "战争": 0.6,
        # 学习相关
        "课程": 0.6, "学习": 0.5, "笔记": 0.5,
        "始计篇": 0.9, "谋攻篇": 0.9, "军形篇": 0.9,
    },
    EventType.IRONCLAW: {
        # 命令
        "/ic": 1.0, "/IC": 1.0,
        # 名称
        "IronClaw": 0.9, "ironclaw": 0.9,
        "小弟": 0.7, "大哥": 0.6,
        # 功能
        "API": 0.5, "LLM": 0.5,
    },
    EventType.SYSTEM: {
        # 系统命令
        "HEARTBEAT": 0.95, "heartbeat": 0.95,
        "cron": 0.9, "定时": 0.7, "任务": 0.6,
        # 配置
        "配置": 0.6, "设置": 0.5, "更新": 0.5,
        # 维护
        "修复": 0.7, "bug": 0.7, "错误": 0.6,
        "日志": 0.6, "清理": 0.6,
    },
}

# 排除关键词（避免误判）
EXCLUSION_KEYWORDS: Dict[EventType, Set[str]] = {
    EventType.FINANCIAL: {"学习", "课程"},  # 金融学习应归军事课程
    EventType.MILITARY: {"股票", "投资"},    # 军事投资应归金融
}


# ==================== 事件路由器 ====================

class EventRouter:
    """
    事件路由器 - 借鉴 OpenViking IntentAnalyzer
    
    功能：
    1. 基于关键词的事件识别
    2. 置信度评分
    3. 多事件检测
    """
    
    def __init__(self):
        self.keywords = EVENT_KEYWORDS
        self.exclusions = EXCLUSION_KEYWORDS
    
    def detect_event(self, query: str) -> RoutedQuery:
        """
        检测事件类型
        
        Args:
            query: 查询文本
        
        Returns:
            RoutedQuery: 路由查询结果
        """
        scores: Dict[EventType, float] = {}
        matched_keywords: Dict[EventType, List[str]] = {}
        
        # 计算各事件类型得分
        for event_type, keywords in self.keywords.items():
            score = 0.0
            matched = []
            
            for keyword, weight in keywords.items():
                if keyword.lower() in query.lower():
                    # 检查排除词
                    if event_type in self.exclusions:
                        if any(ex in query for ex in self.exclusions[event_type]):
                            continue
                    
                    score += weight
                    matched.append(keyword)
            
            if score > 0:
                scores[event_type] = score
                matched_keywords[event_type] = matched
        
        # 选择最高分事件类型
        if not scores:
            return RoutedQuery(
                query=query,
                event_type=EventType.TEMP,
                target_directories=["_temp"],
                priority=5,
                confidence=0.0,
                reasoning="未识别到特定事件类型"
            )
        
        best_event = max(scores, key=scores.get)
        best_score = scores[best_event]
        
        # 计算置信度（归一化到 0-1）
        max_possible = sum(max(kw.values()) for kw in self.keywords.values()) / len(self.keywords)
        confidence = min(best_score / 3.0, 1.0)  # 简化计算
        
        # 确定优先级
        priority = 1 if confidence > 0.8 else 2 if confidence > 0.6 else 3
        
        # 确定目标目录
        target_dirs = self._get_target_directories(best_event, query)
        
        reasoning = f"匹配关键词: {', '.join(matched_keywords[best_event])}"
        
        logger.info(f"🎯 事件识别: {best_event.value} (置信度: {confidence:.2f})")
        
        return RoutedQuery(
            query=query,
            event_type=best_event,
            target_directories=target_dirs,
            priority=priority,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _get_target_directories(self, event_type: EventType, query: str) -> List[str]:
        """确定目标目录"""
        base_dir = {
            EventType.FINANCIAL: "financial_report",
            EventType.MILITARY: "military_course",
            EventType.IRONCLAW: "ironclaw_dev",
            EventType.SYSTEM: "_system",
            EventType.TEMP: "_temp"
        }.get(event_type, "_temp")
        
        # 细分目录
        if event_type == EventType.FINANCIAL:
            if "预测" in query:
                return [f"{base_dir}/predictions"]
            elif "复盘" in query:
                return [f"{base_dir}/reviews"]
            elif "准确率" in query:
                return [f"{base_dir}/accuracy"]
            elif "配置" in query:
                return [f"{base_dir}/config"]
        
        elif event_type == EventType.MILITARY:
            if "笔记" in query:
                return [f"{base_dir}/notes"]
            elif "进度" in query or "学习" in query:
                return [f"{base_dir}/progress"]
            elif "挑战" in query:
                return [f"{base_dir}/challenges"]
        
        return [base_dir]
    
    def route(self, query: str) -> RoutedQuery:
        """路由查询（主入口）"""
        return self.detect_event(query)
    
    def detect_multi_events(self, query: str) -> List[RoutedQuery]:
        """
        检测多事件查询
        
        用于处理跨事件查询场景
        """
        results = []
        
        for event_type in EventType:
            if event_type == EventType.TEMP:
                continue
            
            routed = self.detect_event(query)
            if routed.event_type != EventType.TEMP and routed.confidence > 0.3:
                results.append(routed)
        
        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results[:3]  # 最多返回3个事件


# ==================== 智能路由策略 ====================

class SmartRouter:
    """
    智能路由策略
    
    分层降级：
    1. 语义匹配（最高优先）
    2. 关键词匹配（中等优先）
    3. 默认路由（最低优先）
    """
    
    def __init__(self):
        self.event_router = EventRouter()
        self._fallback_count = 0
    
    def route(self, query: str) -> RoutedQuery:
        """
        智能路由
        
        Args:
            query: 查询文本
        
        Returns:
            RoutedQuery: 路由结果
        """
        # 1. 事件识别
        routed = self.event_router.route(query)
        
        # 2. 置信度检查
        if routed.confidence < 0.3:
            self._fallback_count += 1
            logger.warning(f"⚠️ 低置信度路由 ({routed.confidence:.2f})，使用默认策略")
        
        return routed
    
    def get_stats(self) -> dict:
        """获取路由统计"""
        return {
            "fallback_count": self._fallback_count
        }


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("事件路由器测试")
    print("=" * 60)
    
    router = EventRouter()
    
    test_queries = [
        "比亚迪今天的预测是什么？",
        "孙子兵法始计篇学完了",
        "/ic 你好",
        "HEARTBEAT 检查一下",
        "今天天气怎么样？",
        "复盘一下昨天的股票预测",
        "招商银行和比亚迪的预测",
    ]
    
    for query in test_queries:
        print(f"\n📝 查询: {query}")
        result = router.route(query)
        print(f"   事件: {result.event_type.value}")
        print(f"   目录: {result.target_directories}")
        print(f"   置信度: {result.confidence:.2f}")
        print(f"   理由: {result.reasoning}")
    
    print("\n✅ 测试完成")
