# RAG 对话机器人

这是一个使用 LangChain 构建的简单 RAG（检索增强生成）对话机器人。该项目展示了如何使用 LangChain 框架实现基本的 RAG 功能。

## 功能特点

- 文档加载和分割
- 向量存储（使用 Chroma）
- 基于检索的问答系统
- 简单的命令行交互界面

## 安装步骤

1. 克隆项目并安装依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
创建 `.env` 文件并添加你的 OpenAI API 密钥：
```
OPENAI_API_KEY=你的API密钥
```

## 使用方法

1. 运行主程序：
```bash
python rag_bot.py
```

2. 程序会加载示例文档，然后你可以开始提问。

3. 输入 'quit' 退出程序。

## 项目结构

- `rag_bot.py`: 主要的 RAG 实现文件
- `requirements.txt`: 项目依赖文件
- `.env`: 环境变量配置文件（需要自行创建）
- `chroma_db/`: 向量数据库存储目录（自动创建）

## 自定义文档

你可以修改 `rag_bot.py` 中的 `sample_docs` 列表来添加你自己的文档。每个文档都会被分割成小块并存储在向量数据库中。

## 技术栈

- LangChain
- OpenAI API
- ChromaDB
- Python-dotenv 