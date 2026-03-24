#!/usr/bin/env python3
"""
LongMemEval 风格真实评测集
基于 LongMemEval 官方格式创建
问题类型: single-session, multi-session, temporal-reasoning, knowledge-update
"""

import sys
import os
import json

sys.path.insert(0, "/root/.openclaw/workspace")
sys.path.insert(0, "/root/.openclaw/workspace/memory")

from memory_system import FourLayerMemorySystem


# ==================== LongMemEval 风格测试集 ====================
# 参考: https://github.com/xiaowu0162/LongMemEval

# 测试集：模拟 LongMemEval 的 haystack + question 格式
TEST_DATASET = [

    # ========== single-session ==========
    {
        "id": "ss_001",
        "type": "single-session-user",
        "question": "What is the user's name?",
        "store": "My name is Zhang Wei.",
        "expected_keywords": ["Zhang Wei", "name"],
        "question_date": "2024-03-15"
    },
    {
        "id": "ss_002", 
        "type": "single-session-user",
        "question": "What city does the user live in?",
        "store": "I currently live in Shanghai.",
        "expected_keywords": ["Shanghai", "live"],
        "question_date": "2024-03-15"
    },
    {
        "id": "ss_003",
        "type": "single-session-user", 
        "question": "What is the user's favorite programming language?",
        "store": "My favorite language is Python, it's very elegant.",
        "expected_keywords": ["Python", "language"],
        "question_date": "2024-03-15"
    },
    {
        "id": "ss_004",
        "type": "single-session-user",
        "question": "What company does the user work at?",
        "store": "I work at BYD, in the new energy division.",
        "expected_keywords": ["BYD", "work"],
        "question_date": "2024-03-15"
    },
    {
        "id": "ss_005",
        "type": "single-session-user",
        "question": "What is the user's hobby?",
        "store": "I enjoy reading history books in my spare time.",
        "expected_keywords": ["reading", "history", "books"],
        "question_date": "2024-03-15"
    },
    
    # ========== multi-session ==========
    {
        "id": "ms_001",
        "type": "multi-session",
        "question": "What did the user say they wanted to learn?",
        "sessions": [
            {"role": "user", "content": "I want to learn machine learning."},
            {"role": "assistant", "content": "That's great! ML is very promising."},
            {"role": "user", "content": "What language should I start with?"},
            {"role": "assistant", "content": "I recommend Python, it has rich libraries."}
        ],
        "expected_keywords": ["machine learning", "ML", "learn"],
        "question_date": "2024-03-16"
    },
    {
        "id": "ms_002",
        "type": "multi-session",
        "question": "What investment advice did the assistant give?",
        "sessions": [
            {"role": "user", "content": "I want to start investing."},
            {"role": "assistant", "content": "Focus on long-term value investing, consider fundamental analysis."},
            {"role": "user", "content": "Any specific stocks?"},
            {"role": "assistant", "content": "Look at companies with strong moats like BYD in EV sector."}
        ],
        "expected_keywords": ["value investing", "fundamental", "BYD"],
        "question_date": "2024-03-16"
    },
    {
        "id": "ms_003",
        "type": "multi-session",
        "question": "What project is the user working on?",
        "sessions": [
            {"role": "user", "content": "I'm building a RAG system."},
            {"role": "assistant", "content": "Interesting! RAG combines retrieval with generation."},
            {"role": "user", "content": "What embedding model should I use?"},
            {"role": "assistant", "content": "For Chinese text, consider BGE or text2vec."}
        ],
        "expected_keywords": ["RAG", "embedding", "BGE"],
        "question_date": "2024-03-16"
    },
    
    # ========== temporal-reasoning ==========
    {
        "id": "tr_001",
        "type": "temporal-reasoning",
        "question": "When is the user's meeting scheduled?",
        "store": "The team meeting is at 3pm this Wednesday afternoon.",
        "expected_keywords": ["Wednesday", "3pm", "meeting"],
        "question_date": "2024-03-17"
    },
    {
        "id": "tr_002",
        "type": "temporal-reasoning",
        "question": "What is the deadline for the report?",
        "store": "The quarterly report needs to be submitted by this Friday.",
        "expected_keywords": ["Friday", "report", "quarterly"],
        "question_date": "2024-03-17"
    },
    {
        "id": "tr_003",
        "type": "temporal-reasoning",
        "question": "When does the user's business trip start?",
        "store": "I will depart for Shenzhen next Monday morning.",
        "expected_keywords": ["Monday", "Shenzhen", "business trip"],
        "question_date": "2024-03-17"
    },
    
    # ========== knowledge-update ==========
    {
        "id": "ku_001",
        "type": "knowledge-update",
        "old_content": "The user was using an iPhone 12.",
        "new_content": "The user just upgraded to iPhone 15 Pro Max.",
        "question": "What phone does the user currently use?",
        "expected_keywords": ["iPhone 15", "Pro Max", "upgraded"],
        "question_date": "2024-03-18"
    },
    {
        "id": "ku_002",
        "type": "knowledge-update",
        "old_content": "The user was working at Alibaba.",
        "new_content": "The user recently transferred to Tencent.",
        "question": "Where does the user work now?",
        "expected_keywords": ["Tencent", "transferred", "now"],
        "question_date": "2024-03-18"
    },
    
    # ========== preference ==========
    {
        "id": "pf_001",
        "type": "preference",
        "question": "What is the user's coffee preference?",
        "store": "I usually order a cup of oat milk latte, it's delicious.",
        "expected_keywords": ["oat milk latte", "latte", "coffee"],
        "question_date": "2024-03-19"
    },
    {
        "id": "pf_002",
        "type": "preference",
        "question": "How does the user prefer to study?",
        "store": "I like learning by doing projects, hands-on approach works best for me.",
        "expected_keywords": ["projects", "hands-on", "learning"],
        "question_date": "2024-03-19"
    },
]


def load_dataset():
    """加载测试数据集"""
    return TEST_DATASET


def run_evaluation():
    """运行评测"""
    print("\n" + "="*60)
    print("📊 LongMemEval 风格真实评测")
    print("="*60)
    print(f"测试题数量: {len(TEST_DATASET)}")
    print()
    
    memory = FourLayerMemorySystem()
    
    # 按类型分组统计
    type_stats = {}
    
    for item in TEST_DATASET:
        # 清理记忆
        l2_file = "/root/.openclaw/workspace/memory/l2_memories.json"
        if os.path.exists(l2_file):
            os.remove(l2_file)
        memory = FourLayerMemorySystem()
        
        qtype = item["type"]
        if qtype not in type_stats:
            type_stats[qtype] = {"correct": 0, "total": 0}
        type_stats[qtype]["total"] += 1
        
        # 存储记忆
        if "sessions" in item:
            for session in item["sessions"]:
                memory.store_memory(
                    f"[{session['role']}]",
                    session["content"],
                    "session",
                    "medium"
                )
        elif "sessions" not in item and "old_content" in item:
            # knowledge-update 类型
            memory.store_memory("old_info", item["old_content"], "fact", "low")
            import time
            time.sleep(0.05)
            memory.store_memory("new_info", item["new_content"], "fact", "high")
        else:
            memory.store_memory("fact", item["store"], "fact", "high")
        
        # 搜索
        result = memory.search_memory(item["question"])
        results = result.get("results", [])
        answer = results[0].get("content", "") if results else ""
        
        # 检查是否匹配
        matched = False
        if answer:
            answer_lower = answer.lower()
            for kw in item["expected_keywords"]:
                if kw.lower() in answer_lower:
                    matched = True
                    break
        
        if matched:
            type_stats[qtype]["correct"] += 1
            print(f"  ✅ {item['id']} ({qtype})")
        else:
            print(f"  ❌ {item['id']} ({qtype})")
            if answer:
                print(f"      得到: {answer[:50]}...")
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 分类型结果")
    print("="*60)
    
    total_correct = 0
    total_count = 0
    
    type_mapping = {
        "single-session-user": "Single",
        "multi-session": "Multi",
        "temporal-reasoning": "Temp",
        "knowledge-update": "Update",
        "preference": "Preference"
    }
    
    for qtype, stats in type_stats.items():
        acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        name = type_mapping.get(qtype, qtype)
        bar = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
        print(f"  {name:12s} {bar} {stats['correct']}/{stats['total']} ({acc:.0f}%)")
        total_correct += stats["correct"]
        total_count += stats["total"]
    
    overall = total_correct / total_count * 100 if total_count > 0 else 0
    print("-"*60)
    bar = "█" * int(overall / 10) + "░" * (10 - int(overall / 10))
    print(f"  {'Overall':12s} {bar} {total_correct}/{total_count} ({overall:.0f}%)")
    print("="*60)
    
    return {
        "type_stats": type_stats,
        "overall": overall,
        "total_correct": total_correct,
        "total_count": total_count
    }


if __name__ == "__main__":
    results = run_evaluation()
    
    # 保存
    output = "/root/.openclaw/workspace/longmemeval_style_results.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {output}")
