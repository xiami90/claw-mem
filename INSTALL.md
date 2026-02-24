# 🚀 一键安装指南

## 快速开始（推荐）

```bash
# 一键安装脚本
curl -sSL https://raw.githubusercontent.com/xiami90/claw-mem/master/install.sh | bash

# 或者手动安装
git clone https://github.com/xiami90/claw-mem.git
cd claw-mem
pip install -e .
```

## 详细安装步骤

### 1. 环境要求
- Python 3.8+
- Git
- 网络连接

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 验证安装
```bash
python -c "from memory_lite import LiteMemoryManager; print('✅ 安装成功')"
```

### 4. 首次运行
```bash
# 启动记忆系统
python main.py status

# 测试捕获
python main.py capture --text "这是一个测试记忆"

# 搜索测试
python main.py search --query "测试"
```

## 集成到OpenClaw

```bash
# 复制到OpenClaw技能目录
cp -r memory-lite ~/.openclaw/skills/

# 启用技能
openclaw skills enable memory-lite
```

## 故障排除

### 常见问题
1. **权限问题**: `chmod +x install.sh`
2. **依赖冲突**: 使用虚拟环境 `python -m venv venv`
3. **网络问题**: 手动下载依赖包

### 获取帮助
- 查看日志: `tail -f memory.log`
- 运行诊断: `python main.py diagnose`
- 提交Issue: https://github.com/xiami90/claw-mem/issues