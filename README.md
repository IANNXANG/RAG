# RAG 对话机器人

这是一个基于 LangChain 框架实现的 RAG（检索增强生成）对话机器人。该项目旨在展示如何构建一个能够基于本地文档回答问题的智能问答系统。

## 什么是 RAG？

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合检索系统和大型语言模型的技术。它的工作流程如下：

1. 将文档分割成小块并转换为向量表示
2. 将这些向量存储在向量数据库中
3. 当用户提出问题时，系统首先检索最相关的文档片段
4. 将检索到的文档作为上下文，连同用户问题一起发送给大语言模型
5. 大语言模型基于提供的上下文生成回答

这种方法能够显著提高模型回答的准确性，并减少"幻觉"（生成虚假信息）的可能性。

## 功能特点

- 基于本地 vLLM 服务的语言模型调用
- 使用中文文本向量模型（shibing624/text2vec-base-chinese）
- 文档分块与向量化存储
- 基于语义相似度的智能检索
- 简单的命令行交互界面

## 安装与环境配置

1. 创建 conda 环境（推荐 Python 3.10）：
```bash
conda create -n rag_env python=3.10 -y
conda activate rag_env
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 确保本地 vLLM 服务运行在 8001 端口（如需使用其他模型或服务，请修改代码中的配置）

## 使用方法

1. 激活环境并运行：
```bash
conda activate rag_env
python rag_bot.py
```

2. 程序会加载示例文档，然后您可以开始提问
   - 示例问题："什么是 RAG？"、"向量数据库有什么作用？"、"如何优化提示工程？"

3. 输入 'quit' 退出程序

## 项目结构

- `rag_bot.py`: 主要代码实现
- `requirements.txt`: 项目依赖
- `chroma_db/`: 向量数据库存储目录（自动创建）
- `.gitignore`: Git 忽略文件配置

## 自定义知识库

您可以修改 `rag_bot.py` 中的 `sample_docs` 列表来添加您自己的文档。每个文档会被自动分割并存储为向量。

## 技术栈

- LangChain: 用于构建 LLM 应用的框架
- HuggingFace Embeddings: 文本向量化模型
- ChromaDB: 向量数据库
- vLLM: 高性能语言模型服务 