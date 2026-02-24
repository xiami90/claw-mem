#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量化三层记忆模型 - 核心内存管理器
负责管理三层记忆架构：快速记忆、智能搜索、长期存档
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryLayer(Enum):
    """记忆层级枚举"""
    HOT = "hot"      # 快速记忆层 (SESSION.md)
    WARM = "warm"    # 智能搜索层 (向量索引)
    COLD = "cold"    # 长期存档层 (MEMORY.md)


class MemoryCategory(Enum):
    """记忆分类枚举"""
    DECISION = "decision"      # 决策类
    PREFERENCE = "preference"  # 偏好类
    FACT = "fact"             # 事实类
    PLAN = "plan"             # 计划类
    LESSON = "lesson"         # 经验教训
    GENERAL = "general"       # 一般类


@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    layer: MemoryLayer
    category: str
    importance: float  # 0.0-1.0
    timestamp: datetime
    metadata: Dict[str, Any]
    tags: List[str]


@dataclass
class MemoryStats:
    """记忆统计信息"""
    total_memories: int
    hot_count: int
    warm_count: int
    cold_count: int
    storage_size_mb: float
    last_update: datetime


class LiteMemoryManager:
    """核心内存管理器 - 三层记忆模型的核心组件"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化内存管理器
        
        Args:
            base_path: 基础路径，默认为当前工作目录
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.memory_dir = self.base_path / "memory"
        self.config_file = self.memory_dir / "config.json"
        
        # 确保目录存在
        self.memory_dir.mkdir(exist_ok=True)
        
        # 各层存储文件
        self.hot_memory_file = self.memory_dir / "SESSION.md"
        self.cold_memory_file = self.memory_dir / "MEMORY.md"
        self.warm_index_file = self.memory_dir / "vector_index.json"
        self.metadata_file = self.memory_dir / "metadata.json"
        
        # 配置
        self.config = self._load_config()
        
        # 内存中的缓存
        self.hot_cache: List[MemoryItem] = []
        self.warm_cache: Dict[str, MemoryItem] = {}
        self.cold_cache: List[MemoryItem] = []
        
        # 初始化
        self._initialize_layers()
        
        logger.info(f"MemoryManager initialized at {self.base_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "max_hot_items": 50,
            "hot_retention_hours": 24,
            "auto_promote_threshold": 0.7,
            "auto_demote_threshold": 0.3,
            "vector_dimension": 384,
            "similarity_threshold": 0.75,
            "auto_backup": True,
            "backup_interval_hours": 24,
            "compression_enabled": True,
            "max_storage_mb": 100
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                    logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        return default_config
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _initialize_layers(self):
        """初始化各记忆层"""
        # 加载热记忆
        self._load_hot_memory()
        
        # 加载冷记忆
        self._load_cold_memory()
        
        # 初始化温记忆（向量索引将在搜索模块中处理）
        if self.warm_index_file.exists():
            logger.info("Warm layer index file found")
        else:
            logger.info("Warm layer index file not found, will be created when needed")
    
    def _load_hot_memory(self):
        """加载热记忆层（SESSION.md）"""
        if not self.hot_memory_file.exists():
            self._create_default_hot_memory()
            return
        
        try:
            with open(self.hot_memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 解析SESSION.md内容
                self._parse_hot_memory_content(content)
                logger.info(f"Hot memory loaded: {len(self.hot_cache)} items")
        except Exception as e:
            logger.error(f"Failed to load hot memory: {e}")
            self._create_default_hot_memory()
    
    def _create_default_hot_memory(self):
        """创建默认的热记忆文件"""
        default_content = """# 当前会话状态

## 🎯 当前任务
暂无活跃任务

## 💡 关键信息
- 系统初始化完成
- 记忆系统已启动

## ⚡ 下一步行动
- 开始新的对话或任务

---
*最后更新: {timestamp}*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        try:
            with open(self.hot_memory_file, 'w', encoding='utf-8') as f:
                f.write(default_content)
                logger.info("Default hot memory file created")
        except Exception as e:
            logger.error(f"Failed to create default hot memory: {e}")
    
    def _parse_hot_memory_content(self, content: str):
        """解析热记忆内容"""
        # 这里实现简单的解析逻辑
        # 在实际实现中，可以根据具体格式进行更复杂的解析
        lines = content.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                current_section = line[3:].strip()
            elif line.startswith('- ') and current_section:
                item_content = line[2:].strip()
                if item_content and item_content != "暂无":
                    memory_item = MemoryItem(
                        id=f"hot_{len(self.hot_cache)}",
                        content=item_content,
                        layer=MemoryLayer.HOT,
                        category=self._categorize_content(item_content),
                        importance=0.5,
                        timestamp=datetime.now(),
                        metadata={"section": current_section},
                        tags=self._extract_tags(item_content)
                    )
                    self.hot_cache.append(memory_item)
    
    def _load_cold_memory(self):
        """加载冷记忆层（MEMORY.md）"""
        if not self.cold_memory_file.exists():
            self._create_default_cold_memory()
            return
        
        try:
            with open(self.cold_memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self._parse_cold_memory_content(content)
                logger.info(f"Cold memory loaded: {len(self.cold_cache)} items")
        except Exception as e:
            logger.error(f"Failed to load cold memory: {e}")
            self._create_default_cold_memory()
    
    def _create_default_cold_memory(self):
        """创建默认的冷记忆文件"""
        default_content = """# 长期记忆库

## 📚 重要决策
*暂无重要决策记录*

## 🎯 项目经验
*暂无项目经验*

## 💡 技能积累
*暂无技能记录*

## 📝 个人偏好
*暂无个人偏好*

---
*最后更新: {timestamp}*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        try:
            with open(self.cold_memory_file, 'w', encoding='utf-8') as f:
                f.write(default_content)
                logger.info("Default cold memory file created")
        except Exception as e:
            logger.error(f"Failed to create default cold memory: {e}")
    
    def _parse_cold_memory_content(self, content: str):
        """解析冷记忆内容"""
        lines = content.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                current_section = line[3:].strip()
            elif line.startswith('- ') and current_section:
                item_content = line[2:].strip()
                if item_content and not item_content.startswith('*暂无'):
                    memory_item = MemoryItem(
                        id=f"cold_{len(self.cold_cache)}",
                        content=item_content,
                        layer=MemoryLayer.COLD,
                        category=self._categorize_content(item_content),
                        importance=0.8,  # 冷记忆通常更重要
                        timestamp=datetime.now(),
                        metadata={"section": current_section},
                        tags=self._extract_tags(item_content)
                    )
                    self.cold_cache.append(memory_item)
    
    def store_memory(self, content: str, layer: MemoryLayer = MemoryLayer.HOT,
                    category: str = "general", importance: float = 0.5,
                    metadata: Optional[Dict] = None, tags: Optional[List[str]] = None) -> bool:
        """
        存储记忆项
        
        Args:
            content: 记忆内容
            layer: 目标层级
            category: 分类
            importance: 重要性 (0.0-1.0)
            metadata: 元数据
            tags: 标签列表
            
        Returns:
            是否成功存储
        """
        try:
            # 验证内容
            if not self._validate_content(content):
                logger.warning(f"Invalid content, not storing: {content[:50]}...")
                return False
            
            # 检查重复
            if self._is_duplicate(content):
                logger.info("Duplicate content detected, updating existing")
                return self._update_existing(content)
            
            # 创建记忆项
            memory_item = MemoryItem(
                id=self._generate_id(),
                content=content,
                layer=layer,
                category=category,
                importance=importance,
                timestamp=datetime.now(),
                metadata=metadata or {},
                tags=tags or self._extract_tags(content)
            )
            
            # 存储到对应层级
            success = self._store_to_layer(memory_item)
            
            if success:
                logger.info(f"Memory stored successfully: {memory_item.id} in layer {layer.value}")
                # 更新统计信息
                self._update_stats()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    def _validate_content(self, content: str) -> bool:
        """验证内容有效性"""
        if not content or len(content.strip()) < 3:
            return False
        
        # 检查是否是无意义的重复内容
        if len(set(content)) < 3:  # 字符种类太少
            return False
        
        return True
    
    def _is_duplicate(self, content: str) -> bool:
        """检查内容是否重复"""
        # 简单的重复检查，实际实现中可以更复杂
        content_lower = content.lower().strip()
        
        # 检查热记忆
        for item in self.hot_cache:
            if item.content.lower().strip() == content_lower:
                return True
        
        # 检查冷记忆
        for item in self.cold_cache:
            if item.content.lower().strip() == content_lower:
                return True
        
        return False
    
    def _update_existing(self, content: str) -> bool:
        """更新已存在的记忆项"""
        # 找到并更新已存在的项
        content_lower = content.lower().strip()
        
        for cache in [self.hot_cache, self.cold_cache]:
            for item in cache:
                if item.content.lower().strip() == content_lower:
                    item.timestamp = datetime.now()
                    item.importance = min(1.0, item.importance + 0.1)  # 增加重要性
                    logger.info(f"Updated existing memory: {item.id}")
                    return True
        
        return False
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        timestamp = int(time.time() * 1000)
        return f"mem_{timestamp}"
    
    def _categorize_content(self, content: str) -> str:
        """自动分类内容"""
        content_lower = content.lower()
        
        # 简单的关键词分类
        if any(word in content_lower for word in ['项目', '任务', '工作', '进度']):
            return 'project'
        elif any(word in content_lower for word in ['学习', '技能', '知识', '技术']):
            return 'learning'
        elif any(word in content_lower for word in ['决定', '选择', '方案', '策略']):
            return 'decision'
        elif any(word in content_lower for word in ['偏好', '习惯', '喜欢', '讨厌']):
            return 'preference'
        else:
            return 'general'
    
    def _extract_tags(self, content: str) -> List[str]:
        """提取标签"""
        # 简单的标签提取，实际实现中可以更复杂
        tags = []
        words = content.split()
        
        # 提取重要词汇作为标签
        for word in words:
            word = word.strip('.,!?;:')
            if len(word) > 2 and word.isalnum():
                tags.append(word.lower())
        
        return tags[:5]  # 最多5个标签
    
    def _store_to_layer(self, memory_item: MemoryItem) -> bool:
        """存储到指定层级"""
        try:
            if memory_item.layer == MemoryLayer.HOT:
                self.hot_cache.append(memory_item)
                self._update_hot_memory_file()
                
            elif memory_item.layer == MemoryLayer.COLD:
                self.cold_cache.append(memory_item)
                self._update_cold_memory_file()
                
            elif memory_item.layer == MemoryLayer.WARM:
                self.warm_cache[memory_item.id] = memory_item
                # 温记忆的文件更新由搜索模块处理
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to store to layer {memory_item.layer.value}: {e}")
            return False
    
    def _update_hot_memory_file(self):
        """更新热记忆文件"""
        try:
            content = "# 当前会话状态\n\n"
            
            # 按类别分组
            categories = {}
            for item in self.hot_cache:
                if item.category not in categories:
                    categories[item.category] = []
                categories[item.category].append(item)
            
            # 生成内容
            for category, items in categories.items():
                section_title = self._get_section_title(category)
                content += f"## {section_title}\n"
                
                if not items:
                    content += "*暂无相关记录*\n"
                else:
                    # 只显示最新的几个项目
                    recent_items = sorted(items, key=lambda x: x.timestamp, reverse=True)[:10]
                    for item in recent_items:
                        content += f"- {item.content}\n"
                
                content += "\n"
            
            content += f"---\n*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            with open(self.hot_memory_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logger.error(f"Failed to update hot memory file: {e}")
    
    def _update_cold_memory_file(self):
        """更新冷记忆文件"""
        try:
            content = "# 长期记忆库\n\n"
            
            # 按类别分组
            categories = {}
            for item in self.cold_cache:
                if item.category not in categories:
                    categories[item.category] = []
                categories[item.category].append(item)
            
            # 生成内容
            for category, items in categories.items():
                section_title = self._get_section_title(category)
                content += f"## {section_title}\n\n"
                # 写入文件内容
                for item in items:
                    content += f"- {item.content} (重要性: {item.importance:.1f})\n"
                    content += f"  时间: {item.timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            # 添加统计信息
            content += f"\n---\n*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            # 写入文件
            with open(self.cold_memory_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info("✅ 冷记忆文件更新完成")
            
        except Exception as e:
            logger.error(f"更新冷记忆文件失败: {e}")
    
    def _get_section_title(self, category: MemoryCategory) -> str:
        """获取分类标题"""
        titles = {
            MemoryCategory.DECISION: "重要决策",
            MemoryCategory.PREFERENCE: "用户偏好",
            MemoryCategory.FACT: "重要事实",
            MemoryCategory.PLAN: "计划目标",
            MemoryCategory.LESSON: "经验教训",
            MemoryCategory.GENERAL: "一般信息"
        }
        return titles.get(category, "其他信息")
