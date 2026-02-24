#!/bin/bash
# OpenClaw 轻量化三层记忆模型 - 一键安装脚本
# One-click installer for OpenClaw Lite Memory System

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🧠 OpenClaw 轻量化三层记忆模型                    ║"
    echo "║                                                              ║"
    echo "║           Lite Memory System Installer                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# 检查系统要求
check_requirements() {
    print_info "检查系统要求..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        echo "请安装 Python 3.8 或更高版本"
        exit 1
    fi
    
    # 检查Python版本
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]]; then
        print_error "Python 版本过低 (需要 3.8+, 当前 $PYTHON_VERSION)"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION ✓"
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 未安装"
        echo "请安装 pip3"
        exit 1
    fi
    
    print_success "pip3 ✓"
    
    # 检查Git（可选）
    if command -v git &> /dev/null; then
        print_success "Git ✓"
    else
        print_warning "Git 未安装（可选，但推荐）"
    fi
}

# 创建虚拟环境
create_virtual_env() {
    print_info "创建虚拟环境..."
    
    VENV_DIR="$HOME/.openclaw/memory-env"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "虚拟环境已存在，将使用现有环境"
    else
        python3 -m venv "$VENV_DIR"
        print_success "虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级pip
    pip install --upgrade pip
    
    print_success "虚拟环境准备就绪"
}

# 安装依赖
install_dependencies() {
    print_info "安装依赖包..."
    
    # 基础依赖
    pip install numpy pyyaml loguru typer
    
    # 可选的高级依赖
    print_info "安装可选的高级依赖..."
    pip install lancedb sentence-transformers 2>/dev/null || print_warning "高级依赖安装失败，将使用基础功能"
    
    print_success "依赖包安装完成"
}

# 创建配置文件
create_config() {
    print_info "创建配置文件..."
    
    CONFIG_DIR="$HOME/.openclaw"
    mkdir -p "$CONFIG_DIR"
    
    cat > "$CONFIG_DIR/memory-config.yaml" << 'EOF'
# OpenClaw 轻量化三层记忆模型配置文件
version: "1.0.0"
name: "OpenClaw Lite Memory"

# 内存配置
memory:
  enabled: true
  auto_capture: true
  max_session_size: "50KB"
  importance_threshold: 0.6
  
  layers:
    hot_ram:
      enabled: true
      file: "SESSION-STATE.md"
      auto_update: true
      max_entries: 100
      
    warm_store:
      enabled: true
      provider: "vector_index"
      dimension: 384
      max_results: 10
      similarity_threshold: 0.7
      
    cold_store:
      enabled: true
      file: "MEMORY.md"
      git_enabled: true
      auto_archive: true

# 捕获配置
capture:
  enabled: true
  realtime_capture: true
  batch_processing: true
  min_confidence: 0.6
  max_context_size: 10

# 搜索配置
search:
  enabled: true
  vector_search: true
  keyword_search: true
  fuzzy_search: true
  
  parameters:
    max_results: 10
    similarity_threshold: 0.7
    fuzzy_threshold: 0.8

# 存储配置
storage:
  format: "json"
  compression: true
  backup_enabled: true
  backup_interval_days: 7

# 日志配置
logging:
  enabled: true
  level: "INFO"
  file: ".memory/memory.log"
EOF

    print_success "配置文件创建完成"
}

# 创建启动脚本
create_launcher() {
    print_info "创建启动脚本..."
    
    cat > "$HOME/.openclaw/memory-lite" << 'EOF'
#!/bin/bash
# OpenClaw 轻量化记忆模型启动器

# 激活虚拟环境
source "$HOME/.openclaw/memory-env/bin/activate"

# 设置工作目录
WORKSPACE="${1:-.}"

# 检查内存系统是否已安装
if [ -f "$HOME/.openclaw/memory-lite/main.py" ]; then
    python3 "$HOME/.openclaw/memory-lite/main.py" --workspace "$WORKSPACE" "${@:2}"
else
    echo "❌ 内存系统未安装，请先运行安装脚本"
    exit 1
fi
EOF

    chmod +x "$HOME/.openclaw/memory-lite"
    
    # 创建符号链接
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$HOME/.openclaw/memory-lite" /usr/local/bin/memory-lite
        print_success "已创建全局命令: memory-lite"
    else
        print_warning "无法创建全局命令，请手动添加 $HOME/.openclaw 到 PATH"
    fi
}

# 创建示例文件
create_examples() {
    print_info "创建示例文件..."
    
    EXAMPLES_DIR="$HOME/.openclaw/memory-examples"
    mkdir -p "$EXAMPLES_DIR"
    
    # 创建使用示例
    cat > "$EXAMPLES_DIR/usage-examples.sh" << 'EOF'
#!/bin/bash
# OpenClaw 轻量化记忆模型使用示例

echo "🧠 OpenClaw 轻量化记忆模型 - 使用示例"
echo "========================================"
echo ""

echo "1. 捕获会话记忆:"
echo "   memory-lite capture --text '决定使用React作为前端框架'"
echo ""

echo "2. 搜索相关记忆:"
echo "   memory-lite search --query '前端框架选择'"
echo ""

echo "3. 存储重要信息:"
echo "   memory-lite store --content '用户偏好深色主题' --category preference"
echo ""

echo "4. 查看会话状态:"
echo "   memory-lite status"
echo ""

echo "5. 导出所有记忆:"
echo "   memory-lite export --format json"
echo ""

echo "6. 自动维护:"
echo "   memory-lite maintain"
echo ""

echo "更多帮助: memory-lite --help"
EOF

    chmod +x "$EXAMPLES_DIR/usage-examples.sh"
    
    # 创建集成示例
    cat > "$EXAMPLES_DIR/integration-example.py" << 'EOF'
#!/usr/bin/env python3
"""
OpenClaw 轻量化记忆模型 - Python集成示例
"""

import sys
sys.path.append('/path/to/memory-lite')

from core.memory_manager import LiteMemoryManager
from capture.session_capture import SmartSessionCapture
from search.vector_search import VectorSearch

def main():
    # 初始化内存系统
    manager = LiteMemoryManager("./my-project")
    capture = SmartSessionCapture()
    
    # 示例对话
    conversation = """
    用户：我们决定使用Vue3作为前端框架，因为它有更好的性能。
    助手：好的选择！Vue3确实在性能方面有显著提升。
    用户：记住，API接口需要在下周完成。
    助手：已记录，API接口deadline是下周。
    """
    
    # 捕获重要信息
    captured_items = capture.capture_from_text(conversation)
    
    # 存储记忆
    for item in captured_items:
        manager.store_memory(item)
    
    # 搜索相关记忆
    results = manager.search_memories("前端框架")
    
    # 输出结果
    print(f"捕获了 {len(captured_items)} 条重要信息")
    print(f"搜索到 {len(results)} 条相关记忆")
    
    for result in results:
        print(f"- {result.content} (相关度: {result.score:.2f})")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$EXAMPLES_DIR/integration-example.py"
    
    print_success "示例文件创建完成"
}

# 安装完成提示
show_completion_message() {
    echo ""
    print_success "🎉 安装完成！"
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║           🧠 轻量化三层记忆模型已安装完成！                   ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo "📖 快速开始："
    echo ""
    echo "1. 测试安装："
    echo "   memory-lite status"
    echo ""
    echo "2. 捕获第一条记忆："
    echo "   memory-lite capture --text '决定使用React作为前端框架'"
    echo ""
    echo "3. 搜索相关记忆："
    echo "   memory-lite search --query '前端框架'"
    echo ""
    echo "4. 查看使用示例："
    echo "   $HOME/.openclaw/memory-examples/usage-examples.sh"
    echo ""
    echo "📚 更多帮助："
    echo "   memory-lite --help"
    echo ""
    echo "🔧 配置文件位置："
    echo "   $HOME/.openclaw/memory-config.yaml"
    echo ""
    
    # 激活虚拟环境提示
    echo "💡 提示：首次使用前请激活虚拟环境："
    echo "   source $HOME/.openclaw/memory-env/bin/activate"
    echo ""
}

# 主安装流程
main() {
    print_header
    
    echo "开始安装 OpenClaw 轻量化三层记忆模型..."
    echo ""
    
    # 检查要求
    check_requirements
    echo ""
    
    # 创建虚拟环境
    create_virtual_env
    echo ""
    
    # 安装依赖
    install_dependencies
    echo ""
    
    # 创建配置
    create_config
    echo ""
    
    # 创建启动器
    create_launcher
    echo ""
    
    # 创建示例
    create_examples
    echo ""
    
    # 完成提示
    show_completion_message
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi