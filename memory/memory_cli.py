#!/usr/bin/env python3
"""
memory_cli.py - 四层记忆系统CLI
命令行工具接口
"""

import sys
import argparse
from pathlib import Path

# 导入记忆协议
sys.path.insert(0, "/root/.openclaw/workspace/memory")
from memory_protocol import memory_protocol

def main():
    parser = argparse.ArgumentParser(
        description="四层记忆系统命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 存储记忆
  python3 memory_cli.py store --topic "示例主题" --content "示例内容" --category "个人"
  
  # 搜索记忆
  python3 memory_cli.py search --query "生日" --limit 5
  
  # 更新引力值
  python3 memory_cli.py update --id 1 --delta 0.2
  
  # 删除记忆
  python3 memory_cli.py delete --id 1
  
  # 系统状态
  python3 memory_cli.py status
        """
    )
    
    parser.add_argument("command", choices=["store", "search", "update", "delete", "status", "help"], default="help")
    
    # 存储命令参数
    parser.add_argument("--topic", help="记忆主题")
    parser.add_argument("--content", help="记忆内容")
    parser.add_argument("--category", default="general", help="记忆类别")
    
    # 搜索命令参数
    parser.add_argument("--query", help="搜索关键词")
    parser.add_argument("--limit", type=int, default=5, help="返回结果数量")
    
    # 更新命令参数
    parser.add_argument("--id", type=int, help="记忆ID")
    parser.add_argument("--delta", type=float, default=0.2, help="引力值增量")
    
    args = parser.parse_args()
    
    if args.command == "help":
        parser.print_help()
        return
    
    if args.command == "store":
        if not args.topic or not args.content:
            print("❌ 错误: 需要提供 --topic 和 --content")
            return
        
        result = memory_protocol.store_memory(args.topic, args.content, args.category)
        print(f"✅ {result}")
        
    elif args.command == "search":
        if not args.query:
            print("❌ 错误: 需要提供 --query")
            return
        
        result = memory_protocol.search_memory(args.query, args.limit)
        print(f"✅ {result}")
        
    elif args.command == "update":
        if not args.id:
            print("❌ 错误: 需要提供 --id")
            return
        
        result = memory_protocol.update_gravity(args.id, args.delta)
        print(f"✅ {result}")
        
    elif args.command == "delete":
        if not args.id:
            print("❌ 错误: 需要提供 --id")
            return
        
        result = memory_protocol.delete_memory(args.id)
        print(f"✅ {result}")
        
    elif args.command == "status":
        result = memory_protocol.get_system_status()
        print(f"✅ {result}")

if __name__ == "__main__":
    main()