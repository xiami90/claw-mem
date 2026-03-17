#!/usr/bin/env python3
"""
OpenClaw 轻量化三层记忆模型 - 主程序入口
Main Entry Point for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
@description: 轻量化三层记忆模型的命令行界面和主要功能
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from core.memory_manager import LiteMemoryManager, MemoryCategory
from capture.session_capture import SmartSessionCapture, CaptureType
from search.vector_search import VectorSearch, SearchResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiteMemoryCLI:
    """轻量化记忆系统命令行界面"""
    
    def __init__(self, workspace_path: str = "."):
        """初始化CLI"""
        self.workspace = Path(workspace_path)
        self.memory_manager = LiteMemoryManager(workspace_path)
        self.session_capture = SmartSessionCapture()
        self.vector_search = VectorSearch()
        
        logger.info(f"🚀 LiteMemoryCLI 初始化完成 - 工作目录: {workspace_path}")
    
    def capture_session(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """捕获会话记忆"""
        logger.info(f"🎯 开始捕获会话记忆 - 文本长度: {len(text)}")
        
        try:
            # 使用智能捕获器捕获重要信息
            captured_items = self.session_capture.capture_from_text(text, context)
            
            # 存储捕获的记忆
            stored_count = 0
            for item in captured_items:
                from core.memory_manager import MemoryLayer
                success = self.memory_manager.store_memory(item.content, 'hot', item.type.value, item.confidence)
                if success:
                    stored_count += 1
            
            result = {
                "success": True,
                "captured_count": len(captured_items),
                "stored_count": stored_count,
                "items": [
                    {
                        "type": item.type.value,
                        "content": item.content,
                        "confidence": item.confidence,
                        "timestamp": item.timestamp.isoformat()
                    }
                    for item in captured_items
                ]
            }
            
            logger.info(f"✅ 会话捕获完成 - 捕获: {len(captured_items)}, 存储: {stored_count}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 会话捕获失败: {e}")
            return {"success": False, "error": str(e)}
    
    def search_memories(self, query: str, limit: int = 5, min_importance: float = 0.0) -> Dict[str, Any]:
        """搜索记忆"""
        logger.info(f"🔍 开始搜索记忆 - 查询: '{query}'")
        
        try:
            # 使用内存管理器的搜索功能
            results = self.memory_manager.search_memories(query, limit, min_importance)
            
            result = {
                "success": True,
                "query": query,
                "result_count": len(results),
                "results": results
            }
            
            logger.info(f"✅ 搜索完成 - 找到 {len(results)} 条相关记忆")
            return result
            
        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return {"success": False, "error": str(e)}
    
    def store_memory(self, content: str, category: str = "general", importance: float = 0.5) -> Dict[str, Any]:
        """存储单条记忆"""
        logger.info(f"💾 存储单条记忆 - 内容: {content[:50]}...")
        
        try:
            # 创建记忆项
            from core.memory_manager import MemoryItem, MemoryLayer
            
            memory_item = MemoryItem(
                id=f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                content=content,
                layer=MemoryLayer.HOT,
                category=MemoryCategory(category),
                importance=importance,
                timestamp=datetime.now(),
                metadata={"source": "manual_input"},
                tags=[category, "manual"]
            )
            
            # 存储记忆（直接存储内容，而不是MemoryItem对象）
            from core.memory_manager import MemoryLayer
            success = self.memory_manager.store_memory(
                content=content,
                layer=MemoryLayer.HOT,
                category=category,
                importance=importance,
                metadata={"source": "manual_input"},
                tags=[category, "manual"]
            )
            
            result = {
                "success": success,
                "memory_id": memory_item.id,
                "content": content,
                "category": category,
                "importance": importance
            }
            
            if success:
                logger.info(f"✅ 记忆存储成功: {memory_item.id}")
            else:
                logger.error(f"❌ 记忆存储失败: {memory_item.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 存储失败: {e}")
            return {"success": False, "error": str(e)}
    
    def show_session_state(self) -> Dict[str, Any]:
        """显示会话状态"""
        try:
            # 获取内存管理器的统计信息
            stats = self.memory_manager.get_stats()
            
            # 创建状态显示
            status_content = f"""# 🧠 轻量化三层记忆模型 - 系统状态

## 📊 记忆统计
- **总记忆数**: {stats.get('total_memories', 0)}
- **快速记忆**: {stats.get('hot_count', 0)} 条
- **智能搜索**: {stats.get('warm_count', 0)} 条  
- **长期存档**: {stats.get('cold_count', 0)} 条

## 💾 存储信息
- **总大小**: {stats.get('storage_size_mb', 0)} MB
- **最后更新**: {stats.get('last_update', '未知')}

## 🏷️ 分类统计
"""
            
            # 添加分类统计
            category_stats = stats.get('categories', {})
            if category_stats:
                for category, count in category_stats.items():
                    status_content += f"- **{category}**: {count} 条\n"
            else:
                status_content += "- 暂无分类数据\n"
            
            status_content += f"\n---\n*状态生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            # 保存到会话状态文件
            session_state_file = self.workspace / "SESSION-STATE.md"
            with open(session_state_file, 'w', encoding='utf-8') as f:
                f.write(status_content)
            
            return {
                "success": True,
                "file_exists": True,
                "content": status_content,
                "file_size": len(status_content),
                "last_modified": datetime.now().isoformat(),
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"❌ 生成会话状态失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_exists": False,
                "message": f"生成会话状态失败: {str(e)}"
            }
        """显示会话状态"""
        try:
            session_file = self.workspace / "SESSION-STATE.md"
            
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "file_exists": True,
                    "content": content,
                    "file_size": len(content),
                    "last_modified": datetime.fromtimestamp(session_file.stat().st_mtime).isoformat()
                }
            else:
                return {
                    "success": True,
                    "file_exists": False,
                    "message": "会话状态文件不存在"
                }
                
        except Exception as e:
            logger.error(f"❌ 读取会话状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def export_memories(self, format: str = "json") -> Dict[str, Any]:
        """导出所有记忆"""
        logger.info(f"📤 开始导出记忆 - 格式: {format}")
        
        try:
            # 获取所有记忆
            all_memories = self.memory_manager.export_memories(format)
            
            result = {
                "success": True,
                "format": format,
                "export_time": datetime.now().isoformat(),
                "data": all_memories,
                "size": len(all_memories)
            }
            
            logger.info(f"✅ 导出完成 - 大小: {len(all_memories)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"❌ 导出失败: {e}")
            return {"success": False, "error": str(e)}
    
    def auto_maintenance(self) -> Dict[str, Any]:
        """自动维护"""
        logger.info("🔧 开始自动维护")
        
        try:
            # 执行自动维护
            self.memory_manager.auto_maintenance()
            
            result = {
                "success": True,
                "maintenance_time": datetime.now().isoformat(),
                "message": "自动维护完成"
            }
            
            logger.info("✅ 自动维护完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ 维护失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OpenClaw 轻量化三层记忆模型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 捕获会话记忆
  python main.py capture --text "决定使用React作为前端框架"
  
  # 搜索记忆
  python main.py search --query "前端框架"
  
  # 存储单条记忆
  python main.py store --content "示例偏好内容" --category preference
  
  # 显示会话状态
  python main.py status
  
  # 导出所有记忆
  python main.py export --format json
  
  # 自动维护
  python main.py maintain
        """
    )
    
    # 全局参数
    parser.add_argument("--workspace", "-w", default=".", help="工作目录路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 捕获命令
    capture_parser = subparsers.add_parser("capture", help="捕获会话记忆")
    capture_parser.add_argument("--text", "-t", required=True, help="要捕获的文本")
    capture_parser.add_argument("--context", "-c", help="上下文信息")
    
    # 搜索命令
    search_parser = subparsers.add_parser("search", help="搜索记忆")
    search_parser.add_argument("--query", "-q", required=True, help="搜索查询")
    search_parser.add_argument("--limit", "-l", type=int, default=5, help="结果数量限制")
    search_parser.add_argument("--min-importance", "-m", type=float, default=0.0, help="最小重要性")
    
    # 存储命令
    store_parser = subparsers.add_parser("store", help="存储单条记忆")
    store_parser.add_argument("--content", required=True, help="记忆内容")
    store_parser.add_argument("--category", "-c", default="general", choices=["decision", "preference", "fact", "plan", "lesson", "general"], help="记忆分类")
    store_parser.add_argument("--importance", "-i", type=float, default=0.5, help="重要性评分 (0.0-1.0)")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="显示会话状态")
    
    # 导出命令
    export_parser = subparsers.add_parser("export", help="导出所有记忆")
    export_parser.add_argument("--format", "-f", default="json", choices=["json", "csv", "text"], help="导出格式")
    
    # 维护命令
    maintain_parser = subparsers.add_parser("maintain", help="自动维护")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建CLI实例
    cli = LiteMemoryCLI(args.workspace)
    
    # 执行命令
    if args.command == "capture":
        result = cli.capture_session(args.text, args.context)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif args.command == "search":
        result = cli.search_memories(args.query, args.limit, args.min_importance)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif args.command == "store":
        result = cli.store_memory(args.content, args.category, args.importance)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif args.command == "status":
        result = cli.show_session_state()
        if result["file_exists"]:
            print(result["content"])
        else:
            print("会话状态文件不存在")
            
    elif args.command == "export":
        result = cli.export_memories(args.format)
        print(result["data"])
        
    elif args.command == "maintain":
        result = cli.auto_maintenance()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()