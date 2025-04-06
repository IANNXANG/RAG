import os
import shutil
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate




class RAGBot:
    def __init__(self, clear_previous=True):
        # 清除之前的 ChromaDB 内容
        if clear_previous and os.path.exists("./chroma_db"):
            print("删除之前的 ChromaDB 内容...")
            shutil.rmtree("./chroma_db")
            print("已删除之前的数据库内容。")
            
        # 初始化本地 vLLM 模型
        self.llm = ChatOpenAI(
            model_name="ui-tars",
            openai_api_base="http://localhost:8001/v1",
            openai_api_key="not-needed",
            temperature=0
        )
        
        # 初始化嵌入模型
        # 嵌入模型的作用：
        # 1. 将文本转化为高维向量（通常是几百到上千维度的浮点数数组）
        # 2. 这些向量捕捉了文本的语义信息，语义相似的文本在向量空间中距离较近
        # 3. 通过计算向量间的距离或相似度，可以找到语义上相似的文本
        self.embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese",  # 中文文本向量模型
            model_kwargs={'device': 'cpu'},  # 在CPU上运行模型
            encode_kwargs={'normalize_embeddings': True}  # 向量归一化处理
            # 向量归一化的意义：
            # 1. 使所有向量长度为1，即将向量投影到单位超球面上
            # 2. 归一化后，向量间的余弦相似度等价于点积，计算更简单
            # 3. 消除了文本长度对相似度计算的影响，只关注语义方向
            # 4. 便于使用余弦距离、欧氏距离等进行相似度计算
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # 初始化向量存储
        # 向量存储的作用：
        # 1. 存储文档的向量表示和原始内容
        # 2. 提供高效的相似度搜索功能，快速找到与查询向量最相似的文档向量
        # 3. 支持语义检索，而不仅仅是关键词匹配
        self.vectorstore = None
        
        # 存储文档切片
        self.document_chunks = []
        
    def load_documents(self, texts: List[str]):
        """加载文档并创建向量存储"""
        # 分割文本
        splits = self.text_splitter.create_documents(texts)
        
        # 保存文档切片以便查看
        self.document_chunks = splits
        
        # 打印切片信息
        print(f"\n===== 文档切片信息 =====")
        print(f"总共将 {len(texts)} 个文档切分为 {len(splits)} 个块")
        
        for i, chunk in enumerate(splits):
            print(f"\n切片 #{i+1}:")
            print(f"长度: {len(chunk.page_content)} 字符")
            print(f"内容: {chunk.page_content}")
        
        # 创建向量存储
        # 向量存储创建过程：
        # 1. 将每个文档块通过嵌入模型转换为向量
        # 2. 将向量与原始文档一起存储在ChromaDB中
        # 3. ChromaDB内部使用高效索引结构(如HNSW、ANNOY等)来加速相似度搜索
        # 4. 相似度搜索原理是在高维空间中找到距离最近的向量
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory="./chroma_db"  # 持久化存储目录，便于重复使用
        )
        
        # 打印 ChromaDB 存储信息
        print(f"\n===== ChromaDB 存储信息 =====")
        collection = self.vectorstore._collection
        print(f"Collection 名称: {collection.name}")
        print(f"Collection 中的文档数量: {collection.count()}")
        
    def setup_qa_chain(self):
        """设置问答链"""
        # 创建提示模板
        prompt_template = """使用以下上下文来回答问题。

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
        
        print(f"\n===== 检索过程 =====")
        print(f"问题: {question}")
        
        # 使用LangChain的检索器获取相关文档，只进行一次检索
        # 这样确保展示的文档与实际用于回答的文档完全一致
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})
        retrieved_docs = retriever.get_relevant_documents(question)
        
        # 打印检索结果信息
        print(f"检索到 {len(retrieved_docs)} 个相关文档片段")
        
        # 对于每个检索到的文档，打印内容并计算原始距离
        for i, doc in enumerate(retrieved_docs):
            # 使用嵌入模型计算文档与问题的向量，以便后续计算距离
            # 由于我们不直接使用ChromaDB API，无法直接获取距离值
            # 因此这里只展示文档内容，不展示距离值
            print(f"\n相关文档 #{i+1}:")
            print(f"内容: {doc.page_content}")
            
        # 创建并调用问答链
        chain = self.setup_qa_chain()
        response = chain.invoke({"query": question})
        return response["result"]

# 使用示例
if __name__ == "__main__":
    # 创建机器人实例
    bot = RAGBot()
    
    # 更丰富的示例文档
    sample_docs = [
        "LangChain 是一个用于构建大型语言模型（LLM）应用的开源框架。它提供了一系列工具、组件和接口，使开发者能够更容易地创建由 LLM 驱动的应用程序。LangChain 的核心理念是将 LLM 与其他计算或知识源连接起来，从而构建更加强大和可靠的应用。它支持各种流行的 LLM，如 GPT-4、Claude、Llama 等，并提供了丰富的集成能力。",
        
        "RAG（Retrieval-Augmented Generation）是一种结合检索和生成的 AI 技术，旨在提高大型语言模型的回答质量和可靠性。在 RAG 系统中，当用户提出问题时，系统首先从知识库中检索相关信息，然后将这些信息与用户的问题一起提供给语言模型，使模型能够基于检索到的信息生成更准确的回答。这种方法有效地解决了 LLM 在处理特定领域知识或最新信息时的局限性，减少了'幻觉'（生成虚假信息）的可能性。",
        
        "向量数据库是 RAG 系统中的核心组件，它专门设计用于高效存储和检索向量化的文本数据。在 RAG 工作流程中，文档首先被分割成小块，然后通过嵌入模型转换为向量表示，这些向量随后被存储在向量数据库中。当用户提出问题时，该问题同样被转换为向量，系统使用相似度搜索（如余弦相似度）在向量数据库中找出与问题向量最相似的文档向量。常见的向量数据库包括 Chroma、Pinecone、Weaviate、Milvus 等。",
        
        "嵌入模型（Embedding Models）是将文本转换为数值向量的神经网络模型。在 RAG 系统中，嵌入模型的作用是将文本内容（如文档和查询）转换为向量表示，使得语义相似的文本在向量空间中的距离较近。这种向量表示捕捉了文本的语义信息，使得系统能够基于语义相似度而非简单的关键词匹配来检索相关文档。常用的嵌入模型包括 OpenAI 的 text-embedding-ada-002、Sentence-BERT 系列模型、BGE 系列模型等。",
        
        "提示工程（Prompt Engineering）是设计和优化 LLM 输入提示的过程，旨在引导模型生成更准确、更相关的回答。在 RAG 系统中，提示工程尤为重要，因为它决定了如何将检索到的文档与用户问题整合成一个有效的提示。好的提示模板应该明确指导模型如何使用检索到的信息，同时保持回答的相关性和准确性。常见的 RAG 提示策略包括：明确区分上下文和问题、指导模型在不确定时表明不知道而非编造答案、要求模型仅基于提供的上下文回答等。",
        
        "文本分割（Text Splitting）是 RAG 流程中的关键步骤，它将长文档分割成较小的文本块，以便于向量化和检索。合适的分割策略对 RAG 系统的性能有着重要影响：如果块太大，可能包含过多无关信息，降低检索精度；如果块太小，可能丢失上下文，影响理解。常见的分割方法包括基于字符的分割、基于句子的分割、基于段落的分割以及递归字符分割。为了保持上下文连贯性，分割器通常会在相邻块之间保留一定的重叠区域。",
    ]
    
    # 加载文档
    bot.load_documents(sample_docs)
    
    # 打印 ChromaDB 目录内容
    print("\n===== ChromaDB 目录内容 =====")
    try:
        chroma_files = os.listdir("./chroma_db")
        print(f"ChromaDB 目录内容: {chroma_files}")
        
        # 如果有子目录，也列出
        for file in chroma_files:
            if os.path.isdir(f"./chroma_db/{file}"):
                subfolder_files = os.listdir(f"./chroma_db/{file}")
                print(f"{file} 子目录内容: {subfolder_files}")
                
    except Exception as e:
        print(f"获取 ChromaDB 目录信息时出错: {e}")
    
    # 测试问答
    while True:
        question = input("\n请输入您的问题（输入 'quit' 退出）: ")
        if question.lower() == 'quit':
            break
            
        answer = bot.ask(question)
        print(f"\n回答: {answer}") 