#!/usr/bin/env python3
"""
priority_manager.py - 优先级判断系统
根据内容自动判断记忆优先级
"""

from typing import Dict, Any, List

class PriorityManager:
    """优先级判断系统"""
    
    def __init__(self):
        # 优先级关键词
        self.keywords = {
            "high": [
                "生日", "年龄", "性别",  # 个人身份
                "联系方式", "电话", "邮箱", "地址",
                "决策", "决定", "架构", "架构设计",
                "记住", "记住是", "一定要记住",  # 明确要求
                "重要", "关键", "核心", "非常重要"
            ],
            "medium": [
                "偏好", "喜欢", "习惯",  # 用户偏好
                "项目", "任务", "计划",  # 项目信息
                "团队", "同事", "工具", "软件", "框架",
                "会议", "讨论", "会议记录"  # 重要会议
            ],
            "low": [
                "临时", "待办", "想法",  # 临时信息
                "建议",  # 一般性对话
                "可以", "可能", "也许"  # 不确定性内容
            ]
        }
        
        # 引力值范围
        self.gravity_ranges = {
            "high": (1.5, 2.0),
            "medium": (1.0, 1.5),
            "low": (0.5, 1.0)
        }
    
    def determine_priority(self, content: str, category: str = "") -> Dict[str, Any]:
        """
        判断记忆优先级
        """
        content_lower = content.lower()
        category_lower = category.lower()
        
        # 检查优先级
        priority, confidence = self._check_priority(content_lower, category_lower)
        
        # 计算引力值
        gravity = self._calculate_gravity(priority)
        
        return {
            "priority": priority,
            "gravity": gravity,
            "confidence": confidence,
            "gravity_range": self.gravity_ranges[priority]
        }
    
    def _check_priority(self, content: str, category: str) -> tuple:
        """
        检查内容优先级
        返回：(
优先级, 置信度）
        """
        # 先检查高优先级
        if self._matches_keywords(content, category, self.keywords["high"]):
            return ("high", 0.9)
        
        # 检查中优先级
        if self._matches_keywords(content, category, self.keywords["medium"]):
            return ("medium", 0.8)
        
        # 检查低优先级
        if self._matches_keywords(content, category, self.keywords["low"]):
            return ("low", 0.7)
        
        # 默认中优先级
        return ("medium", 0.5)
    
    def _matches_keywords(self, content: str, category: str, keywords: List[str]) -> bool:
        """
        检查内容是否匹配关键词
        """
        # 在内容中查找
        for keyword in keywords:
            if keyword.lower() in content:
                return True
        
        # 在类别中查找
        for keyword in keywords:
            if keyword.lower() in category:
                return True
        
        return False
    
    def _calculate_gravity(self, priority: str) -> float:
        """
        根据优先级计算引力值
        """
        min_gravity, max_gravity = self.gravity_ranges[priority]
        
        # 在范围内随机选择一个值（简化为中间值）
        return (min_gravity + max_gravity) / 2
    
    def manual_set_priority(self, content: str, priority: str, gravity: float = None) -> Dict[str, Any]:
        """
        手动设置优先级
        """
        # 验证优先级
        if priority not in ["high", "medium", "low"]:
            return {
                "success": False,
                "message": f"无效的优先级: {priority}，必须是 high/medium/low"
            }
        
        # 验证引力值
        if gravity is None:
            gravity = self._calculate_gravity(priority)
        else:
            min_gravity, max_gravity = self.gravity_ranges[priority]
            if gravity < min_gravity or gravity > max_gravity:
                return {
                    "success": False,
                    "message": f"引力值超出范围[{min_gravity}, {max_gravity}]"
                }
        
        return {
            "success": True,
            "priority": priority,
            "gravity": gravity
        }

# 创建全局实例
priority_manager = PriorityManager()

def test_priority_manager():
    """测试优先级判断系统"""
    print("=" * 40)
    print("🧪 测试优先级判断系统")
    print("=" * 40)
    
    # 测试自动判断
    print("\n测试1: 自动优先级判断")
    test_cases = [
        ("用户生日是7月20日，一定要记住", "个人信息"),
        ("我的工作偏好是早上处理重要任务", "工作"),
        ("这是一个临时想法，待会再确认", "临时"),
        ("项目架构设计决定了系统性能", "技术决策"),
        ("明天有个项目会议需要参加", "工作")
    ]
    
    for content, category in test_cases:
        result = priority_manager.determine_priority(content, category)
        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        print(f"{priority_emoji[result['priority']]} [{result['priority'].upper()}] 引力={result['gravity']:.2f}")
        print(f"   {content[:40]}...")
    
    # 测试手动设置
    print("\n测试2: 手动设置优先级")
    result = priority_manager.manual_set_priority("重要决策", "high", 1.8)
    if result['success']:
        print(f"✅ 手动设置成功: 优先级={result['priority']}, 引力={result['gravity']}")
    else:
        print(f"❌ 设置失败: {result['message']}")
    
    print("\n✅ 优先级判断系统测试完成！")

if __name__ == "__main__":
    test_priority_manager()