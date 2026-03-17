#!/usr/bin/env python3
"""
event_directories.py - 事件目录结构定义
借鉴 OpenViking 的 DirectoryDefinition 设计

功能：
1. 定义事件类型枚举
2. 预设目录树结构
3. 提供目录初始化功能
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path
import json
from datetime import datetime


class EventType(Enum):
    """事件类型枚举"""
    FINANCIAL = "financial"       # 金融日报
    MILITARY = "military"         # 军事课程
    IRONCLAW = "ironclaw"         # IronClaw 开发
    SYSTEM = "system"             # 系统配置
    TEMP = "temp"                 # 临时事件


@dataclass
class EventDirectory:
    """
    事件目录定义 - 借鉴 OpenViking DirectoryDefinition
    
    Attributes:
        path: 相对路径
        abstract: L0 摘要（用于快速定位）
        overview: L1 概述（用于详细描述）
        event_type: 事件类型
        children: 子目录列表
    """
    path: str
    abstract: str
    overview: str
    event_type: str
    children: List["EventDirectory"] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "path": self.path,
            "abstract": self.abstract,
            "overview": self.overview,
            "event_type": self.event_type,
            "children": [c.to_dict() for c in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EventDirectory":
        """从字典创建"""
        return cls(
            path=data["path"],
            abstract=data["abstract"],
            overview=data["overview"],
            event_type=data["event_type"],
            children=[cls.from_dict(c) for c in data.get("children", [])]
        )


# ==================== 预设目录树 ====================
# 借鉴 OpenViking 的 PRESET_DIRECTORIES 设计

PRESET_EVENT_DIRECTORIES: Dict[str, EventDirectory] = {
    "user": EventDirectory(
        path="",
        abstract="用户级记忆，跨会话持久化",
        overview="存储用户偏好、个人信息、学习进度等长期记忆",
        event_type="system",
        children=[
            # 金融日报事件
            EventDirectory(
                path="financial_report",
                abstract="金融日报事件记忆",
                overview="存储金融日报相关的预测、复盘、配置、准确率统计",
                event_type="financial",
                children=[
                    EventDirectory(
                        path="predictions",
                        abstract="预测记录",
                        overview="四维度预测（当日、一周、一月、一年）",
                        event_type="financial"
                    ),
                    EventDirectory(
                        path="reviews",
                        abstract="复盘记录",
                        overview="每日复盘、预测验证、策略调整",
                        event_type="financial"
                    ),
                    EventDirectory(
                        path="config",
                        abstract="配置信息",
                        overview="关注标的、报告时间、飞书配置",
                        event_type="financial"
                    ),
                    EventDirectory(
                        path="accuracy",
                        abstract="准确率统计",
                        overview="预测准确率、成功/失败模式",
                        event_type="financial"
                    ),
                ]
            ),
            # 军事课程事件
            EventDirectory(
                path="military_course",
                abstract="军事课程学习记忆",
                overview="孙子兵法、纪效新书学习进度和笔记",
                event_type="military",
                children=[
                    EventDirectory(
                        path="progress",
                        abstract="学习进度",
                        overview="课程进度、完成状态",
                        event_type="military"
                    ),
                    EventDirectory(
                        path="notes",
                        abstract="学习笔记",
                        overview="课程笔记、心得体会",
                        event_type="military"
                    ),
                    EventDirectory(
                        path="challenges",
                        abstract="挑战任务",
                        overview="课后挑战、练习记录",
                        event_type="military"
                    ),
                ]
            ),
            # IronClaw 开发事件
            EventDirectory(
                path="ironclaw_dev",
                abstract="IronClaw 开发记忆",
                overview="IronClaw 小弟系统的开发记录、配置、优化",
                event_type="ironclaw",
                children=[
                    EventDirectory(
                        path="sessions",
                        abstract="会话记录",
                        overview="与 IronClaw 的对话记录",
                        event_type="ironclaw"
                    ),
                    EventDirectory(
                        path="config",
                        abstract="配置信息",
                        overview="模型配置、API 密钥",
                        event_type="ironclaw"
                    ),
                ]
            ),
            # 系统级记忆
            EventDirectory(
                path="_system",
                abstract="系统级记忆",
                overview="用户偏好、全局配置、系统状态",
                event_type="system",
                children=[
                    EventDirectory(
                        path="preferences",
                        abstract="用户偏好",
                        overview="沟通风格、工作习惯、兴趣领域",
                        event_type="system"
                    ),
                    EventDirectory(
                        path="entities",
                        abstract="实体记忆",
                        overview="项目、人物、概念等实体信息",
                        event_type="system"
                    ),
                    EventDirectory(
                        path="events",
                        abstract="事件记录",
                        overview="重要事件、决策、里程碑",
                        event_type="system"
                    ),
                ]
            ),
            # 临时事件
            EventDirectory(
                path="_temp",
                abstract="临时记忆",
                overview="临时咨询、未分类内容，定期清理",
                event_type="temp"
            ),
        ]
    )
}


# ==================== 目录管理器 ====================

class DirectoryManager:
    """
    目录管理器 - 初始化和管理事件目录结构
    """
    
    BASE_PATH = Path("/root/.openclaw/workspace/memory/l2_memories")
    
    def __init__(self):
        self.base_path = self.BASE_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def initialize_directories(self) -> dict:
        """初始化预设目录结构"""
        results = {
            "created": [],
            "skipped": [],
            "errors": []
        }
        
        def create_directory(dir_def: EventDirectory, parent_path: Path):
            """递归创建目录"""
            dir_path = parent_path / dir_def.path if dir_def.path else parent_path
            
            try:
                # 创建目录
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # 创建目录元数据文件
                meta_file = dir_path / ".directory.json"
                if not meta_file.exists():
                    meta = {
                        "abstract": dir_def.abstract,
                        "overview": dir_def.overview,
                        "event_type": dir_def.event_type,
                        "created": datetime.now().isoformat()
                    }
                    with open(meta_file, 'w', encoding='utf-8') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                    results["created"].append(str(dir_path))
                else:
                    results["skipped"].append(str(dir_path))
                
                # 创建记忆存储文件
                memories_file = dir_path / "memories.json"
                if not memories_file.exists():
                    with open(memories_file, 'w', encoding='utf-8') as f:
                        json.dump({"memories": [], "last_updated": None}, f, ensure_ascii=False, indent=2)
                
                # 递归处理子目录
                for child in dir_def.children:
                    create_directory(child, dir_path)
                    
            except Exception as e:
                results["errors"].append({
                    "path": str(dir_path),
                    "error": str(e)
                })
        
        # 初始化所有预设目录
        for scope, dir_def in PRESET_EVENT_DIRECTORIES.items():
            create_directory(dir_def, self.base_path)
        
        return results
    
    def get_event_path(self, event_type: EventType) -> Path:
        """获取事件类型的目录路径"""
        path_map = {
            EventType.FINANCIAL: "financial_report",
            EventType.MILITARY: "military_course",
            EventType.IRONCLAW: "ironclaw_dev",
            EventType.SYSTEM: "_system",
            EventType.TEMP: "_temp"
        }
        return self.base_path / path_map[event_type]
    
    def list_directories(self) -> List[dict]:
        """列出所有目录及其元数据"""
        directories = []
        
        for meta_file in self.base_path.rglob(".directory.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                directories.append({
                    "path": str(meta_file.parent.relative_to(self.base_path)),
                    **meta
                })
            except:
                pass
        
        return directories


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("事件目录初始化测试")
    print("=" * 60)
    
    manager = DirectoryManager()
    results = manager.initialize_directories()
    
    print(f"\n✅ 创建目录: {len(results['created'])} 个")
    for p in results['created'][:5]:
        print(f"   {p}")
    
    print(f"\n⏭️ 跳过目录: {len(results['skipped'])} 个")
    
    if results['errors']:
        print(f"\n❌ 错误: {len(results['errors'])} 个")
        for e in results['errors']:
            print(f"   {e['path']}: {e['error']}")
    
    print("\n📂 目录列表:")
    for d in manager.list_directories():
        print(f"   [{d['event_type']}] {d['path']}")
        print(f"      {d['abstract']}")
