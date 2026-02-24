#!/usr/bin/env python3
"""
智能模型路由Skill
集成到轻量化三层记忆模型中，提供多模型调度和故障转移能力
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志 - 只显示重要信息
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    name: str
    provider: str
    base_url: str
    api_key: str
    model_id: str
    max_tokens: int = 8192
    temperature: float = 0.7
    timeout: int = 30
    priority: int = 1
    weight: float = 1.0
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["text", "chat", "code"]

class ModelStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ModelHealth:
    status: ModelStatus
    last_check: float
    response_time: float
    error_rate: float
    success_count: int
    failure_count: int

class ModelRouterSkill:
    """智能模型路由Skill - 简化版"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.health_status: Dict[str, ModelHealth] = {}
        self.failed_models: Dict[str, float] = {}
        self.max_failures = 3
        self.recovery_time = 60
        
        # 加载内置模型
        self._load_builtin_models()
    
    def _load_builtin_models(self):
        """加载内置模型配置"""
        # 当前使用的Kimi-K2模型
        self.add_model(ModelConfig(
            name="kimi-k2",
            provider="kimi",
            base_url="https://api.kimi.com/v1",
            api_key="sk-u2j6vGmiL",
            model_id="kimi-k2",
            priority=1,
            weight=1.0,
            capabilities=["text", "chat", "code", "reasoning"],
            max_tokens=200000
        ))
        
        # 火山方舟模型
        self.add_model(ModelConfig(
            name="volcengine-ark",
            provider="volcengine",
            base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
            api_key="eb2ca165-b533-4fdf-83fe-02196f7f5c9b",
            model_id="ark-code-latest",
            priority=2,
            weight=0.9,
            capabilities=["text", "code"],
            max_tokens=8192
        ))
    
    def add_model(self, config: ModelConfig):
        """添加模型配置"""
        self.models[config.name] = config
        self.health_status[config.name] = ModelHealth(
            status=ModelStatus.UNKNOWN,
            last_check=0,
            response_time=0,
            error_rate=0,
            success_count=0,
            failure_count=0
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态 - 简化版"""
        healthy_models = []
        for model_name, health in self.health_status.items():
            if health.status == ModelStatus.HEALTHY:
                healthy_models.append(model_name)
        
        return {
            "healthy_models": len(healthy_models),
            "total_models": len(self.models),
            "primary_model": healthy_models[0] if healthy_models else "none"
        }
    
    def select_model(self, task_type: str = "general") -> Optional[str]:
        """选择模型 - 简化版"""
        # 获取健康模型
        healthy_models = []
        for model_name, health in self.health_status.items():
            if health.status == ModelStatus.HEALTHY:
                healthy_models.append(model_name)
        
        if not healthy_models:
            # 如果没有健康模型，返回第一个可用模型
            available_models = list(self.models.keys())
            return available_models[0] if available_models else None
        
        # 根据任务类型选择
        for model_name in healthy_models:
            model = self.models[model_name]
            if task_type == "coding" and "code" in model.capabilities:
                return model_name
            elif task_type == "reasoning" and "reasoning" in model.capabilities:
                return model_name
            elif task_type == "chat" and "chat" in model.capabilities:
                return model_name
        
        # 默认返回第一个健康模型
        return healthy_models[0] if healthy_models else None

# 全局实例
model_router = ModelRouterSkill()

def get_model_status() -> Dict[str, Any]:
    """获取模型系统状态 - 对外接口"""
    return model_router.get_system_status()

def select_best_model(task_type: str = "general") -> Optional[str]:
    """选择最佳模型 - 对外接口"""
    return model_router.select_model(task_type)

if __name__ == "__main__":
    # 测试功能
    print("🧠 智能模型路由系统")
    
    # 获取系统状态
    status = get_model_status()
    print(f"系统状态: 健康模型数 {status['healthy_models']}/{status['total_models']}")
    
    # 选择模型
    best_model = select_best_model("coding")
    print(f"推荐模型: {best_model}")