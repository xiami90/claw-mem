#!/usr/bin/env python3
"""
OpenClaw 轻量化三层记忆模型 - 工具函数
Utility functions for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def generate_memory_id(content: str, timestamp: datetime) -> str:
    """
    生成记忆ID
    
    Args:
        content: 记忆内容
        timestamp: 时间戳
        
    Returns:
        记忆ID字符串
    """
    # 使用内容哈希和时间戳生成唯一ID
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
    time_str = timestamp.strftime('%Y%m%d_%H%M%S')
    return f"mem_{time_str}_{content_hash}"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename.strip()


def ensure_directory(path: Path) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        是否成功创建
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {path} - {e}")
        return False


def load_json_file(filepath: Path, default: Optional[Dict] = None) -> Dict:
    """
    安全加载JSON文件
    
    Args:
        filepath: JSON文件路径
        default: 默认值
        
    Returns:
        解析后的JSON数据
    """
    default = default or {}
    
    if not filepath.exists():
        return default
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {filepath} - {e}")
        return default
    except Exception as e:
        logger.error(f"加载JSON文件失败: {filepath} - {e}")
        return default


def save_json_file(filepath: Path, data: Dict, indent: int = 2) -> bool:
    """
    安全保存JSON文件
    
    Args:
        filepath: 保存路径
        data: 要保存的数据
        indent: JSON缩进
        
    Returns:
        是否成功保存
    """
    try:
        # 确保父目录存在
        ensure_directory(filepath.parent)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {filepath} - {e}")
        return False


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算文本相似度（简单实现）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度分数 (0.0 - 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    # 转换为小写并分词
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    # 计算交集和并集
    intersection = words1 & words2
    union = words1 | words2
    
    # Jaccard相似度
    jaccard_similarity = len(intersection) / len(union) if union else 0.0
    
    return jaccard_similarity


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """
    提取关键词
    
    Args:
        text: 输入文本
        min_length: 最小词长
        
    Returns:
        关键词列表
    """
    if not text:
        return []
    
    # 简单的关键词提取
    import re
    
    # 移除标点符号
    text = re.sub(r'[^\w\s]', '', text)
    
    # 分词
    words = text.split()
    
    # 过滤短词和常见词
    stop_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '里', '些', '只', '下', '可', '过', '她', '他', '它', '们',
        '与', '或', '但', '而', '因为', '所以', '如果', '虽然', '然而', '因此', '于是',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'among', 'throughout', 'despite', 'towards'
    }
    
    keywords = []
    for word in words:
        if len(word) >= min_length and word.lower() not in stop_words:
            keywords.append(word)
    
    # 去重并保持顺序
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word.lower() not in seen:
            seen.add(word.lower())
            unique_keywords.append(word)
    
    return unique_keywords


def format_timestamp(dt: datetime) -> str:
    """
    格式化时间戳
    
    Args:
        dt: datetime对象
        
    Returns:
        格式化的时间字符串
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    解析时间戳字符串
    
    Args:
        timestamp_str: 时间戳字符串
        
    Returns:
        datetime对象或None
    """
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y%m%d_%H%M%S',
        '%Y%m%d_%H%M',
        '%Y%m%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S.%f+00:00'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"无法解析时间戳: {timestamp_str}")
    return None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀字符串
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    # 尝试在单词边界截断
    truncated = text[:max_length - len(suffix)]
    
    # 找到最后一个空格
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:  # 如果空格在合理位置
        truncated = truncated[:last_space]
    
    return truncated + suffix


def validate_importance(importance: float) -> float:
    """
    验证并规范化重要性分数
    
    Args:
        importance: 原始重要性分数
        
    Returns:
        规范化后的重要性分数 (0.0 - 1.0)
    """
    if not isinstance(importance, (int, float)):
        return 0.5
    
    # 限制在0.0-1.0范围内
    return max(0.0, min(1.0, float(importance)))


def get_file_size(filepath: Path) -> str:
    """
    获取文件大小（人类可读格式）
    
    Args:
        filepath: 文件路径
        
    Returns:
        格式化的文件大小字符串
    """
    if not filepath.exists():
        return "0 B"
    
    size_bytes = filepath.stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"


def is_valid_memory_content(content: str) -> bool:
    """
    验证记忆内容是否有效
    
    Args:
        content: 记忆内容
        
    Returns:
        是否有效
    """
    if not content or not content.strip():
        return False
    
    content = content.strip()
    
    # 检查最小长度
    if len(content) < 5:
        return False
    
    # 检查是否只有标点符号或特殊字符
    import string
    if all(c in string.punctuation + string.whitespace for c in content):
        return False
    
    # 检查是否包含有效字符
    has_letter = any(c.isalpha() for c in content)
    has_digit = any(c.isdigit() for c in content)
    
    return has_letter or has_digit


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    生成文本摘要（简单实现）
    
    Args:
        text: 原始文本
        max_sentences: 最大句子数
        
    Returns:
        文本摘要
    """
    if not text:
        return ""
    
    import re
    
    # 分割句子
    sentences = re.split(r'[。！？\n]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return ""
    
    # 选择前几个句子作为摘要
    summary_sentences = sentences[:max_sentences]
    
    # 连接句子
    summary = ' '.join(summary_sentences)
    
    # 如果文本很长，添加省略号
    if len(sentences) > max_sentences:
        summary += "..."
    
    return summary


# 工具函数测试
if __name__ == "__main__":
    # 测试函数
    print("测试工具函数...")
    
    # 测试文本相似度
    text1 = "我喜欢使用React进行前端开发"
    text2 = "React是我最喜欢的前端框架"
    similarity = calculate_text_similarity(text1, text2)
    print(f"文本相似度: {similarity:.2f}")
    
    # 测试关键词提取
    keywords = extract_keywords(text1)
    print(f"关键词: {keywords}")
    
    # 测试时间戳
    now = datetime.now()
    formatted = format_timestamp(now)
    print(f"格式化时间: {formatted}")
    
    # 测试文本截断
    long_text = "这是一个很长的文本，用于测试文本截断功能。这个功能非常有用，可以帮助我们处理过长的内容。"
    truncated = truncate_text(long_text, 30)
    print(f"截断文本: {truncated}")
    
    # 测试重要性验证
    importance = validate_importance(1.5)
    print(f"验证重要性: {importance}")
    
    # 测试记忆内容验证
    valid_content = "这是一个有效的记忆内容"
    is_valid = is_valid_memory_content(valid_content)
    print(f"内容有效性: {is_valid}")
    
    # 测试摘要生成
    summary = generate_summary(long_text, max_sentences=2)
    print(f"文本摘要: {summary}")
    
    print("工具函数测试完成！")