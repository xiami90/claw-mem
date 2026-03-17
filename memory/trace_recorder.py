#!/usr/bin/env python3
"""
trace_recorder.py - 检索轨迹记录器
借鉴 OpenViking 的 QueryResult 设计

功能：
1. 记录检索路径
2. 可视化输出
3. 轨迹持久化
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 数据类 ====================

@dataclass
class TraceStep:
    """
    检索轨迹步骤
    
    Attributes:
        layer: 记忆层 (L0/L1/L2/L3)
        action: 操作类型 (vector_search/semantic_search/keyword_match)
        target: 目标位置
        found: 找到数量
        duration_ms: 耗时(毫秒)
        timestamp: 时间戳
    """
    layer: str
    action: str
    target: str
    found: int = 0
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "action": self.action,
            "target": self.target,
            "found": self.found,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }


@dataclass
class RetrievalTrace:
    """
    完整检索轨迹 - 借鉴 OpenViking QueryResult
    
    Attributes:
        query: 查询文本
        event_type: 事件类型
        steps: 检索步骤列表
        total_found: 总找到数量
        duration_ms: 总耗时
        results: 检索结果摘要
    """
    query: str
    event_type: str = "unknown"
    steps: List[TraceStep] = field(default_factory=list)
    total_found: int = 0
    duration_ms: float = 0.0
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_step(self, step: TraceStep):
        """添加步骤"""
        self.steps.append(step)
        self.total_found += step.found
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "event_type": self.event_type,
            "steps": [s.to_dict() for s in self.steps],
            "total_found": self.total_found,
            "duration_ms": self.duration_ms,
            "results": self.results
        }
    
    def render(self, detailed: bool = False) -> str:
        """
        渲染可视化输出
        
        Args:
            detailed: 是否显示详细信息
        """
        lines = [
            f"📍 检索轨迹: {self.query}",
            f"   事件类型: {self.event_type}",
            ""
        ]
        
        # 渲染步骤
        for i, step in enumerate(self.steps):
            prefix = "├──" if i < len(self.steps) - 1 else "└──"
            found_str = f"{step.found}条" if step.found >= 0 else "失败"
            lines.append(
                f"   {prefix} [{step.layer}] {step.action} → {step.target} ({found_str}, {step.duration_ms:.1f}ms)"
            )
        
        # 总结
        lines.extend([
            "",
            f"   ✅ 总计: {self.total_found}条结果 ({self.duration_ms:.1f}ms)"
        ])
        
        # 详细结果
        if detailed and self.results:
            lines.append("")
            lines.append("   📄 结果预览:")
            for i, r in enumerate(self.results[:3]):
                lines.append(f"      {i+1}. {r.get('topic', 'N/A')}: {r.get('content', '')[:50]}...")
        
        return "\n".join(lines)


# ==================== 轨迹记录器 ====================

class TraceRecorder:
    """
    检索轨迹记录器
    
    功能：
    1. 记录每次检索的完整轨迹
    2. 持久化存储
    3. 支持回放和分析
    """
    
    def __init__(self, trace_dir: str = "/root/.openclaw/workspace/memory/traces"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self._current_trace: Optional[RetrievalTrace] = None
        self._start_time: Optional[float] = None
    
    def start_trace(self, query: str, event_type: str = "unknown") -> RetrievalTrace:
        """开始新轨迹"""
        self._current_trace = RetrievalTrace(
            query=query,
            event_type=event_type
        )
        self._start_time = time.monotonic()
        
        logger.debug(f"🔍 开始轨迹: {query}")
        return self._current_trace
    
    def record_step(
        self,
        layer: str,
        action: str,
        target: str,
        found: int = 0,
        duration_ms: float = 0.0
    ):
        """记录步骤"""
        if not self._current_trace:
            logger.warning("⚠️ 没有活动的轨迹")
            return
        
        step = TraceStep(
            layer=layer,
            action=action,
            target=target,
            found=found,
            duration_ms=duration_ms
        )
        
        self._current_trace.add_step(step)
        logger.debug(f"   └── [{layer}] {action} → {found}条")
    
    def end_trace(self, results: List[Dict] = None) -> RetrievalTrace:
        """结束轨迹"""
        if not self._current_trace:
            raise ValueError("没有活动的轨迹")
        
        # 计算总耗时
        self._current_trace.duration_ms = (time.monotonic() - self._start_time) * 1000
        
        # 记录结果
        if results:
            self._current_trace.results = results
        
        # 保存轨迹
        self._save_trace(self._current_trace)
        
        trace = self._current_trace
        self._current_trace = None
        
        logger.info(f"✅ 轨迹完成: {trace.total_found}条结果 ({trace.duration_ms:.1f}ms)")
        return trace
    
    def _save_trace(self, trace: RetrievalTrace):
        """保存轨迹到文件"""
        date_str = datetime.now().strftime("%Y%m%d")
        trace_file = self.trace_dir / f"trace_{date_str}.jsonl"
        
        try:
            with open(trace_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"⚠️ 保存轨迹失败: {e}")
    
    def get_traces(self, date: str = None, limit: int = 10) -> List[RetrievalTrace]:
        """
        获取历史轨迹
        
        Args:
            date: 日期 (YYYYMMDD)，默认今天
            limit: 最大数量
        """
        date = date or datetime.now().strftime("%Y%m%d")
        trace_file = self.trace_dir / f"trace_{date}.jsonl"
        
        traces = []
        if trace_file.exists():
            with open(trace_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        traces.append(RetrievalTrace(
                            query=data["query"],
                            event_type=data.get("event_type", "unknown"),
                            steps=[TraceStep(**s) for s in data.get("steps", [])],
                            total_found=data.get("total_found", 0),
                            duration_ms=data.get("duration_ms", 0),
                            results=data.get("results", [])
                        ))
                        if len(traces) >= limit:
                            break
                    except:
                        pass
        
        return traces
    
    def get_stats(self, date: str = None) -> Dict:
        """获取轨迹统计"""
        traces = self.get_traces(date, limit=1000)
        
        if not traces:
            return {"total_traces": 0}
        
        total_duration = sum(t.duration_ms for t in traces)
        total_found = sum(t.total_found for t in traces)
        
        # 按事件类型统计
        by_event = {}
        for t in traces:
            by_event[t.event_type] = by_event.get(t.event_type, 0) + 1
        
        # 按层级统计
        by_layer = {}
        for t in traces:
            for step in t.steps:
                by_layer[step.layer] = by_layer.get(step.layer, 0) + 1
        
        return {
            "total_traces": len(traces),
            "total_found": total_found,
            "avg_found": total_found / len(traces),
            "avg_duration_ms": total_duration / len(traces),
            "by_event": by_event,
            "by_layer": by_layer
        }


# ==================== 上下文管理器 ====================

class TraceContext:
    """轨迹记录上下文管理器"""
    
    def __init__(self, recorder: TraceRecorder, query: str, event_type: str = "unknown"):
        self.recorder = recorder
        self.query = query
        self.event_type = event_type
        self.trace = None
    
    def __enter__(self):
        self.trace = self.recorder.start_trace(self.query, self.event_type)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.recorder.record_step("error", "exception", str(exc_val))
        self.recorder.end_trace()
        return False
    
    def step(self, layer: str, action: str, target: str, found: int = 0, duration_ms: float = 0.0):
        """记录步骤"""
        self.recorder.record_step(layer, action, target, found, duration_ms)


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("检索轨迹记录器测试")
    print("=" * 60)
    
    recorder = TraceRecorder()
    
    # 测试轨迹记录
    print("\n📍 测试轨迹记录:")
    
    with TraceContext(recorder, "比亚迪预测", "financial") as trace:
        # 模拟 L3 检索
        trace.step("L3", "vector_search", "chromadb", found=3, duration_ms=15.5)
        
        # 模拟 L2 检索
        trace.step("L2", "semantic_search", "financial_report/predictions", found=2, duration_ms=8.2)
        
        # 模拟 L0 检索
        trace.step("L0", "keyword_match", "instant_memory", found=1, duration_ms=0.5)
    
    # 获取统计
    print("\n📊 轨迹统计:")
    stats = recorder.get_stats()
    print(f"   总轨迹数: {stats['total_traces']}")
    print(f"   平均找到: {stats['avg_found']:.1f}条")
    print(f"   平均耗时: {stats['avg_duration_ms']:.1f}ms")
    print(f"   按事件: {stats['by_event']}")
    print(f"   按层级: {stats['by_layer']}")
    
    # 获取历史轨迹
    print("\n📜 历史轨迹:")
    traces = recorder.get_traces(limit=3)
    for t in traces:
        print(t.render())
    
    print("\n✅ 测试完成")
