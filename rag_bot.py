import os
from typing import List
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import requests

# 加载环境变量
load_dotenv()

class RAGBot:
    def __init__(self):
        # 初始化本地 vLLM 模型
        self.llm = ChatOpenAI(
            model_name="ui-tars",
            openai_api_base="http://localhost:8001/v1",
            openai_api_key="not-needed",
            temperature=0
        )
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # 初始化向量存储
        self.vectorstore = None
        
    def load_documents(self, texts: List[str]):
        """加载文档并创建向量存储"""
        # 分割文本
        splits = self.text_splitter.create_documents(texts)
        
        # 创建向量存储
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        
    def setup_qa_chain(self):
        """设置问答链"""
        # 创建提示模板
        prompt_template = """使用以下上下文来回答问题。如果你不知道答案，就说你不知道，不要试图编造答案。

上下文: {context}

问题: {question}

答案:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # 创建检索链
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        return chain
    
    def ask(self, question: str) -> str:
        """向机器人提问"""
        if not self.vectorstore:
            return "请先加载一些文档！"
            
        chain = self.setup_qa_chain()
        response = chain.invoke({"query": question})
        return response["result"]

# 使用示例
if __name__ == "__main__":
    # 创建机器人实例
    bot = RAGBot()
    
    # 示例文档
    sample_docs = [
        "LangChain 是一个用于构建 LLM 应用的框架。它提供了许多工具和组件，使开发者能够更容易地构建复杂的 AI 应用。",
        "RAG (Retrieval-Augmented Generation) 是一种结合检索和生成的 AI 技术。它通过检索相关文档来增强 LLM 的回答能力。",
        "向量数据库是 RAG 系统中的重要组件，用于存储和检索文档的向量表示。"
    ]
    
    # 加载文档
    bot.load_documents(sample_docs)
    
    # 测试问答
    while True:
        question = input("\n请输入您的问题（输入 'quit' 退出）: ")
        if question.lower() == 'quit':
            break
            
        answer = bot.ask(question)
        print(f"\n回答: {answer}") 