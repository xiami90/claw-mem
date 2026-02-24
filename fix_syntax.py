#!/usr/bin/env python3
"""修复语法错误"""

with open('core/memory_manager.py', 'r') as f:
    content = f.read()

# 修复f-string转义问题
content = content.replace(
    'f"- {item.content} (重要性: {item.importance:.1f})\\n\\"',
    'f"- {item.content} (重要性: {item.importance:.1f})\\\\n\\\\n"'
)

content = content.replace(
    'f"  时间: {item.timestamp.strftime(\\\'%Y-%m-%d %H:%M\\\')}\\n\\"',
    'f"  时间: {item.timestamp.strftime(\\\'%Y-%m-%d %H:%M\\\')}\\\\n\\\\n"'
)

content = content.replace(
    'f"\\n---\\n*最后更新: {datetime.now().strftime(\\\'%Y-%m-%d %H:%M:%S\\\')}*\\"',
    'f"\\\\n---\\\\n*最后更新: {datetime.now().strftime(\\\'%Y-%m-%d %H:%M:%S\\\')}*"'
)

# 写回文件
with open('core/memory_manager.py', 'w') as f:
    f.write(content)

print('✅ 语法修复完成')

# 验证语法
import ast
try:
    ast.parse(content)
    print('✅ 语法验证通过')
except SyntaxError as e:
    print(f'❌ 语法错误: {e}')
    print(f'行号: {e.lineno}')
    print(f'文本: {e.text}')