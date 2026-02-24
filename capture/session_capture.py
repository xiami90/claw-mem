#!/usr/bin/env python3
"""
OpenClaw 轻量化三层记忆模型 - 智能会话捕获器
Smart Session Capture for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
@description: 智能识别和捕获会话中的重要信息
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CaptureType(Enum):
    """捕获类型枚举"""
    DECISION = "decision"
    PREFERENCE = "preference" 
    FACT = "fact"
    PLAN = "plan"
    LESSON = "lesson"
    WARNING = "warning"
    CONTACT = "contact"
    GENERAL = "general"


@dataclass
class CapturedItem:
    """捕获项数据结构"""
    type: CaptureType
    content: str
    confidence: float
    timestamp: datetime
    context: str
    metadata: Dict[str, Any]


class SmartSessionCapture:
    """
    智能会话捕获器
    
    功能特性：
    - 多模式重要信息识别
    - 上下文感知的智能提取
    - 置信度评估和过滤
    - 实时捕获和批处理
    - 可扩展的模式匹配
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能捕获器
        
        Args:
            config: 配置字典
        """
        self.config = config or self._get_default_config()
        self.capture_patterns = self._load_capture_patterns()
        self.context_window = []
        self.max_context_size = self.config.get("max_context_size", 10)
        self.min_confidence = self.config.get("min_confidence", 0.6)
        
        logger.info("✅ SmartSessionCapture 初始化完成")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "max_context_size": 10,
            "min_confidence": 0.6,
            "enable_realtime_capture": True,
            "enable_batch_processing": True,
            "patterns": {
                "decision": {"weight": 0.9, "min_confidence": 0.7},
                "preference": {"weight": 0.8, "min_confidence": 0.6},
                "fact": {"weight": 0.7, "min_confidence": 0.5},
                "plan": {"weight": 0.8, "min_confidence": 0.6},
                "lesson": {"weight": 0.85, "min_confidence": 0.65}
            }
        }
    
    def _load_capture_patterns(self) -> Dict[CaptureType, List[Tuple[str, float, Dict[str, Any]]]]:
        """加载捕获模式"""
        patterns = {
            CaptureType.DECISION: [
                # 中文决策模式
                (r"(?:决定|决策|选择|确定|采用|使用|应用)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.9, {"language": "zh", "formality": "high"}),
                (r"(?:我们|我)\s*(?:决定|选择)\s*(.+?)(?:[。！？\n]|$)", 0.85, {"language": "zh", "speaker": "inclusive"}),
                (r"(?:确定|敲定)\s*(?:了|要)\s*(.+?)(?:[。！？\n]|$)", 0.8, {"language": "zh", "certainty": "high"}),
                
                # 技术决策
                (r"(?:技术栈|框架|工具|方案)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"domain": "tech", "type": "stack"}),
                (r"(?:用|使用)\s*(.+?)\s*(?:做|开发|实现)", 0.8, {"domain": "tech", "type": "implementation"}),
                (r"(?:架构|设计)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"domain": "tech", "type": "architecture"}),
            ],
            
            CaptureType.PREFERENCE: [
                # 偏好表达
                (r"(?:偏好|喜欢|偏爱|倾向于|更喜欢)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.9, {"type": "positive_preference"}),
                (r"(?:不喜欢|讨厌|反感|不想|不要)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "negative_preference"}),
                (r"(?:我觉得|我认为|对我而言)\s*(.+?)\s*(?:更好|更合适|更喜欢)", 0.8, {"speaker": "personal", "type": "opinion"}),
                (r"(?:用户|我们)\s*(?:偏好|喜欢)\s*(.+?)(?:[。！？\n]|$)", 0.85, {"speaker": "collective", "type": "preference"}),
            ],
            
            CaptureType.FACT: [
                # 重要事实
                (r"(?:重要|关键|核心|主要)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"importance": "high"}),
                (r"(?:记住|牢记|备忘|记录)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.9, {"action": "remember", "importance": "critical"}),
                (r"(?:事实是|实际上是|其实是)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.8, {"type": "fact_statement", "certainty": "high"}),
                (r"(?:确认|证实|验证)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "confirmation", "reliability": "high"}),
                
                # 技术事实
                (r"(?:版本|型号|规格|配置)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.8, {"domain": "tech", "type": "specification"}),
                (r"(?:API|接口|端点)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"domain": "tech", "type": "api_info"}),
            ],
            
            CaptureType.PLAN: [
                # 计划和目标
                (r"(?:计划|打算|准备|将要|下一步)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "plan", "timeframe": "future"}),
                (r"(?:目标|目的|要达成|要完成)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "goal", "timeframe": "future"}),
                (r"(?:明天|后天|下周|下个月)\s*(.+?)(?:[。！？\n]|$)", 0.8, {"type": "scheduled", "timeframe": "specific"}),
                (r"(?:第一步|第二步|第三阶段)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "step", "structure": "sequential"}),
            ],
            
            CaptureType.LESSON: [
                # 经验教训
                (r"(?:经验|教训|学到|总结|反思)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "lesson_learned"}),
                (r"(?:应该|不应该|要|不要)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.8, {"type": "advice", "recommendation": "prescriptive"}),
                (r"(?:注意|小心|警惕)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "warning", "urgency": "high"}),
                (r"(?:错误|失误|问题)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.8, {"type": "mistake", "sentiment": "negative"}),
            ],
            
            CaptureType.WARNING: [
                # 警告和风险
                (r"(?:警告|风险|危险|注意)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.9, {"type": "warning", "severity": "high"}),
                (r"(?:可能|也许|大概)\s*(?:会|要)\s*(.+?)(?:[。！？\n]|$)", 0.7, {"type": "possibility", "certainty": "medium"}),
                (r"(?:如果|假如|倘若)\s*(.+?)(?:[。！？\n]|$)", 0.75, {"type": "condition", "structure": "hypothetical"}),
            ],
            
            CaptureType.CONTACT: [
                # 联系信息
                (r"(?:联系人|联系方式|邮箱|电话)[：:]\s*(.+?)(?:[。！？\n]|$)", 0.85, {"type": "contact_info"}),
                (r"(?:@|联系)\s*(\w+?)(?:[。！？\n]|$)", 0.8, {"type": "mention", "platform": "generic"}),
            ]
        }
        
        return patterns
    
    def capture_from_text(self, text: str, context: Optional[str] = None) -> List[CapturedItem]:
        """
        从文本中捕获重要信息
        
        Args:
            text: 输入文本
            context: 上下文信息
            
        Returns:
            捕获项列表
        """
        if not text or not text.strip():
            return []
        
        logger.info(f"🎯 开始智能捕获 - 文本长度: {len(text)}, 上下文: {context}")
        
        # 更新上下文窗口
        self._update_context(text, context)
        
        captured_items = []
        
        # 使用模式匹配捕获
        for capture_type, patterns in self.capture_patterns.items():
            for pattern, base_confidence, metadata in patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple):
                        content = match[0] if match[0] else match[1] if len(match) > 1 else str(match)
                    else:
                        content = str(match)
                    
                    content = content.strip()
                    
                    # 过滤太短或太长的内容
                    if len(content) < 10 or len(content) > 500:
                        continue
                    
                    # 计算置信度
                    confidence = self._calculate_confidence(content, capture_type, base_confidence, text)
                    
                    if confidence >= self.min_confidence:
                        captured_item = CapturedItem(
                            type=capture_type,
                            content=content,
                            confidence=confidence,
                            timestamp=datetime.now(),
                            context=self._get_current_context(),
                            metadata={**metadata, "capture_method": "pattern_matching", "pattern": pattern}
                        )
                        
                        captured_items.append(captured_item)
                        logger.info(f"✅ 捕获成功: [{capture_type.value}] {content[:50]}... (置信度: {confidence:.2f})")
        
        # 如果没有捕获到足够的内容，使用智能提取
        if len(captured_items) < 2:
            smart_items = self._smart_extract(text, context)
            captured_items.extend(smart_items)
        
        # 去重和合并
        captured_items = self._deduplicate_items(captured_items)
        
        logger.info(f"🎯 捕获完成 - 共捕获 {len(captured_items)} 条重要信息")
        return captured_items
    
    def _update_context(self, text: str, context: Optional[str] = None):
        """更新上下文窗口"""
        context_entry = {
            "text": text[:200],  # 只保留前200字符
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "length": len(text)
        }
        
        self.context_window.append(context_entry)
        
        # 保持上下文窗口大小
        if len(self.context_window) > self.max_context_size:
            self.context_window.pop(0)
    
    def _get_current_context(self) -> str:
        """获取当前上下文"""
        if not self.context_window:
            return ""
        
        # 返回最近几条上下文的摘要
        recent_contexts = self.context_window[-3:]  # 最近3条
        context_summary = []
        
        for i, ctx in enumerate(recent_contexts):
            text_preview = ctx["text"][:50] + "..." if len(ctx["text"]) > 50 else ctx["text"]
            context_summary.append(f"{i+1}. {text_preview}")
        
        return "\n".join(context_summary)
    
    def _calculate_confidence(self, content: str, capture_type: CaptureType, base_confidence: float, full_text: str) -> float:
        """计算捕获置信度"""
        confidence = base_confidence
        
        # 长度因子
        content_length = len(content)
        if 20 <= content_length <= 100:
            confidence += 0.05
        elif content_length > 200:
            confidence -= 0.1
        elif content_length < 15:
            confidence -= 0.15
        
        # 关键词密度因子
        important_words = {
            CaptureType.DECISION: ["决定", "选择", "确定", "采用", "使用"],
            CaptureType.PREFERENCE: ["偏好", "喜欢", "更合适", "更好"],
            CaptureType.FACT: ["重要", "关键", "记住", "事实", "确认"],
            CaptureType.PLAN: ["计划", "目标", "下一步", "准备"],
            CaptureType.LESSON: ["经验", "教训", "学到", "总结", "应该"]
        }
        
        if capture_type in important_words:
            keyword_count = sum(1 for word in important_words[capture_type] if word in content)
            confidence += min(keyword_count * 0.03, 0.15)
        
        # 上下文一致性因子
        if self._check_context_consistency(content, capture_type):
            confidence += 0.1
        
        # 位置因子（开头和结尾的内容通常更重要）
        position_ratio = full_text.find(content) / len(full_text) if full_text else 0.5
        if position_ratio < 0.2 or position_ratio > 0.8:  # 开头或结尾
            confidence += 0.05
        
        # 确保置信度在合理范围内
        return max(0.1, min(1.0, confidence))
    
    def _check_context_consistency(self, content: str, capture_type: CaptureType) -> bool:
        """检查上下文一致性"""
        if not self.context_window:
            return False
        
        # 检查最近几条上下文是否与当前捕获类型一致
        recent_types = []
        for ctx in self.context_window[-3:]:
            # 简单的类型推断
            if "决定" in ctx["text"] or "选择" in ctx["text"]:
                recent_types.append(CaptureType.DECISION)
            elif "偏好" in ctx["text"] or "喜欢" in ctx["text"]:
                recent_types.append(CaptureType.PREFERENCE)
            elif "计划" in ctx["text"] or "目标" in ctx["text"]:
                recent_types.append(CaptureType.PLAN)
        
        # 如果最近上下文与当前捕获类型一致，返回True
        return capture_type in recent_types[-2:] if len(recent_types) >= 2 else False
    
    def _smart_extract(self, text: str, context: Optional[str] = None) -> List[CapturedItem]:
        """智能提取重要信息"""
        # 当模式匹配没有找到足够内容时的备用提取方法
        
        sentences = re.split(r'[。！？\n]+', text)
        extracted_items = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 简单的关键词匹配
            important_keywords = {
                "重要": CaptureType.FACT,
                "决定": CaptureType.DECISION,
                "计划": CaptureType.PLAN,
                "偏好": CaptureType.PREFERENCE,
                "经验": CaptureType.LESSON,
                "应该": CaptureType.LESSON
            }
            
            for keyword, capture_type in important_keywords.items():
                if keyword in sentence:
                    confidence = 0.6  # 基础置信度
                    
                    # 位置权重
                    if i == 0 or i == len(sentences) - 1:  # 开头或结尾
                        confidence += 0.1
                    
                    captured_item = CapturedItem(
                        type=capture_type,
                        content=sentence,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        context=self._get_current_context(),
                        metadata={"capture_method": "smart_extraction", "sentence_index": i}
                    )
                    
                    extracted_items.append(captured_item)
                    logger.info(f"✅ 智能提取: [{capture_type.value}] {sentence[:50]}... (置信度: {confidence:.2f})")
                    break
        
        return extracted_items
    
    def _deduplicate_items(self, items: List[CapturedItem]) -> List[CapturedItem]:
        """去重捕获项"""
        if not items:
            return []
        
        unique_items = []
        seen_content = set()
        
        # 按置信度排序，保留高置信度的
        items.sort(key=lambda x: x.confidence, reverse=True)
        
        for item in items:
            # 创建内容指纹（简化版本）
            content_fingerprint = self._create_content_fingerprint(item.content)
            
            if content_fingerprint not in seen_content:
                seen_content.add(content_fingerprint)
                unique_items.append(item)
            else:
                logger.info(f"🔄 去重: 跳过重复内容 - {item.content[:50]}...")
        
        return unique_items
    
    def _create_content_fingerprint(self, content: str) -> str:
        """创建内容指纹用于去重"""
        # 移除标点符号和空格，转换为小写
        import re
        clean_content = re.sub(r'[^\w]', '', content.lower())
        
        # 如果内容太短，返回原文
        if len(clean_content) < 10:
            return content
        
        # 返回前20个字符作为指纹（可以根据需要调整）
        return clean_content[:20]
