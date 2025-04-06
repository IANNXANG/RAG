#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 打印彩色消息函数
print_info() {
    echo -e "${GREEN}[信息]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查Python是否安装
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    print_error "未找到Python。请安装Python 3.8+后再运行此脚本。"
    exit 1
fi

# 确定Python命令
PYTHON_CMD="python"
if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# 检查rag_bot.py是否存在
if [ ! -f "rag_bot.py" ]; then
    print_error "未找到rag_bot.py文件。请确保脚本与rag_bot.py位于同一目录。"
    exit 1
fi

# 检查是否有Conda环境
CONDA_ENV="rag_env"
USE_CONDA=false

if command -v conda &> /dev/null; then
    # 检查是否存在rag_env环境
    if conda info --envs | grep -q "${CONDA_ENV}"; then
        print_info "找到Conda环境: ${CONDA_ENV}"
        USE_CONDA=true
    else
        print_warning "找到Conda但未找到${CONDA_ENV}环境。将使用系统Python。"
        
        # 询问是否要创建环境
        read -p "是否要创建一个名为${CONDA_ENV}的新Conda环境? (y/n): " create_env
        if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
            print_info "创建新的Conda环境: ${CONDA_ENV}..."
            conda create -n ${CONDA_ENV} python=3.10 -y
            conda activate ${CONDA_ENV}
            print_info "安装依赖..."
            pip install -r requirements.txt
            USE_CONDA=true
        fi
    fi
fi

# 检查依赖文件
if [ ! -f "requirements.txt" ] && [ "${USE_CONDA}" = false ]; then
    print_warning "未找到requirements.txt文件。可能缺少依赖项。"
fi

# 运行程序
print_info "开始运行RAG机器人..."

if [ "${USE_CONDA}" = true ]; then
    print_info "使用Conda环境: ${CONDA_ENV}"
    # 根据操作系统使用正确的Conda激活命令
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # macOS 或 Linux
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate ${CONDA_ENV}
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        eval "$(conda shell.bash hook)"
        conda activate ${CONDA_ENV}
    else
        print_warning "无法识别的操作系统，尝试通用激活方法"
        conda activate ${CONDA_ENV}
    fi
    ${PYTHON_CMD} rag_bot.py
else
    print_info "使用系统Python"
    ${PYTHON_CMD} rag_bot.py
fi

print_info "程序已退出。" 