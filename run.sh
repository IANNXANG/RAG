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

# 显示帮助信息
show_help() {
    echo "RAG机器人运行脚本"
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help         显示帮助信息"
    echo "  -k, --keep-kb      保留现有知识库，不重新初始化 (默认: 不保留)"
    echo "  -c, --clear-db     强制清除现有数据库 (默认: 与知识库初始化选项一致)"
    echo "  -p, --preserve-db  强制保留现有数据库 (默认: 与知识库初始化选项一致)"
    echo "  -t, --no-tunnel    不建立SSH隧道，直接运行 (默认: 建立隧道)"
    echo "  -n, --top-k N      设置检索的相关文档数量 (默认: ${TOP_K})"
}

# 解析命令行参数
KEEP_KB=false
CLEAR_DB=false
NO_CLEAR_DB=false
NO_TUNNEL=false
TOP_K=2

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -k|--keep-kb)
            KEEP_KB=true
            shift
            ;;
        -c|--clear-db)
            CLEAR_DB=true
            shift
            ;;
        -p|--preserve-db)
            NO_CLEAR_DB=true
            shift
            ;;
        -t|--no-tunnel)
            NO_TUNNEL=true
            shift
            ;;
        -n|--top-k)
            if [[ $# -lt 2 ]] || [[ $2 =~ ^- ]]; then
                print_error "选项 --top-k 需要一个数值参数"
                exit 1
            fi
            TOP_K="$2"
            shift 2
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查端口8001是否被占用（即判断隧道是否已经建立）
check_port() {
    lsof -i:8001 > /dev/null 2>&1
    return $?
}

# 建立SSH隧道
setup_tunnel() {
    print_info "正在建立到远程服务的SSH隧道 (端口8001)..."
    # 在后台运行SSH隧道
    ssh -fN -L 8001:localhost:8001 -J zhouyang@10.61.190.11:18022 root@10.160.199.103 -p 30033
    
    # 检查SSH隧道是否成功建立
    if [ $? -eq 0 ]; then
        print_info "SSH隧道已成功建立，现在可以通过localhost:8001访问远程服务"
        # 等待1秒确保隧道完全建立
        sleep 1
        return 0
    else
        print_error "SSH隧道建立失败，请检查网络连接和SSH配置"
        return 1
    fi
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

# 如果不是NO_TUNNEL模式，检查端口8001是否被占用，如果没有则建立SSH隧道
if [ "${NO_TUNNEL}" = false ]; then
    if ! check_port; then
        print_info "端口8001未被占用，需要建立SSH隧道"
        setup_tunnel
        if [ $? -ne 0 ]; then
            print_error "无法建立SSH隧道，退出程序"
            exit 1
        fi
    else
        print_info "端口8001已被占用，假定SSH隧道已建立"
    fi
else
    print_info "跳过SSH隧道建立，直接运行程序"
fi

# 准备RAG_BOT命令行参数
RAG_ARGS=""
if [ "${KEEP_KB}" = true ]; then
    RAG_ARGS="${RAG_ARGS} --keep_kb"
fi
if [ "${CLEAR_DB}" = true ]; then
    RAG_ARGS="${RAG_ARGS} --clear_db"
fi
if [ "${NO_CLEAR_DB}" = true ]; then
    RAG_ARGS="${RAG_ARGS} --no_clear_db"
fi
RAG_ARGS="${RAG_ARGS} --top_k ${TOP_K}"

# 运行程序
print_info "开始运行RAG机器人..."
print_info "运行参数:"
print_info "  - 保留知识库: $([ "${KEEP_KB}" = true ] && echo "是" || echo "否") (--keep_kb)"
print_info "  - 强制清除数据库: $([ "${CLEAR_DB}" = true ] && echo "是" || echo "否") (--clear_db)"
print_info "  - 强制保留数据库: $([ "${NO_CLEAR_DB}" = true ] && echo "是" || echo "否") (--no_clear_db)"
print_info "  - 检索文档数: ${TOP_K} (--top_k)"
print_info "  - 跳过SSH隧道: $([ "${NO_TUNNEL}" = true ] && echo "是" || echo "否") (--no-tunnel)"
print_info "命令行: ${PYTHON_CMD} rag_bot.py ${RAG_ARGS}"

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
    ${PYTHON_CMD} rag_bot.py ${RAG_ARGS}
else
    print_info "使用系统Python"
    ${PYTHON_CMD} rag_bot.py ${RAG_ARGS}
fi

print_info "程序已退出。"

# 询问是否要关闭SSH隧道
if [ "${NO_TUNNEL}" = false ] && check_port; then
    read -p "是否要关闭SSH隧道? (y/n): " close_tunnel
    if [ "$close_tunnel" = "y" ] || [ "$close_tunnel" = "Y" ]; then
        print_info "正在关闭SSH隧道..."
        # 查找并关闭SSH隧道进程
        SSH_PID=$(lsof -ti:8001)
        if [ -n "$SSH_PID" ]; then
            kill $SSH_PID
            print_info "SSH隧道已关闭"
        else
            print_warning "未找到SSH隧道进程"
        fi
    else
        print_info "SSH隧道保持开启状态"
    fi
fi 