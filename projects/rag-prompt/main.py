# -- Prompt Components
from fennec.prompt.core import PromptTemplate
from fennec.prompt.core import FewShotPromptTemplate
# -- Text Splitter (Chunking)
from fennec.chunks import MultilanguageTextChunker
# -- Vector Database
from fennec.vector_database import ChromaVectorDatabase
# -- Embeddings
from fennec.embeddings import OllamaEmbedder
# -- Context Manager
from fennec.context import ContextManager
from fennec.context import ContextConfig
# -- RAG Core
from fennec.rag.core import RAGConfig
from fennec.rag.core import RAGSystem
from fennec.document_loaders import TextLoader
# -- LLM Interface
from fennec.llm import GeminiInterface

template_str = """أنت مساعد ذكاء اصطناعي متخصص في الإجابة عن الأسئلة التقنية.
المعلومات المتاحة من قاعدة المعرفة:
{context}
السؤال: {question}
تعليمات:
- أجب بناءً على المعلومات المقدمة فقط
- كن دقيقاً ومختصراً
- إذا لم تجد معلومات كافية، قل "لا توجد معلومات كافية"
- اجب بنفس لغة السؤال
الإجابة:"""

prompt = PromptTemplate(
        template=template_str,
        input_variables=["context", "question"],
        template_format="f-string"
    )

example_template = PromptTemplate(
        template="سؤال: {question}\nإجابة: {answer}",
        input_variables=["question", "answer"]
    )

    # أمثلة تدريبية | Training examples
examples = [
        {
            "question": "ما هو RAG؟",
            "answer": "RAG هو Retrieval-Augmented Generation، نظام يجمع بين استرجاع المعلومات وتوليد الإجابات باستخدام LLM."
        },
        {
            "question": "ما هي مميزات استخدام FAISS؟",
            "answer": "FAISS سريع جداً في البحث، يدعم millions of vectors، ومناسب للـ production."
        },
        {
            "question": "ما الفرق بين chunking و embedding؟",
            "answer": "Chunking هو تقسيم النص لقطع صغيرة، بينما Embedding هو تحويل النص لأرقام (vectors) للبحث."
        }
    ]

few_shot = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_template,
        prefix="أنت مساعد تقني. هذه أمثلة على إجابات جيدة:\n",
        suffix="\n\nالمعلومات: {context}\n\nسؤال: {question}\nإجابة:",
        input_variables=["context", "question"],
        example_separator="\n---\n",
        max_examples=3
    )

llm=GeminiInterface(api_key=api)
embedder=OllamaEmbedder()
chunker=MultilanguageTextChunker(chunk_size=500, overlap=50)
vector_db=ChromaVectorDatabase(embedder=embedder)
config = ContextConfig(
        max_context_length=3000,
        include_scores=False,
        include_metadata=False,
        separator="\n---\n",
        template="arabic"
    )
manager = ContextManager(config=config)
config = RAGConfig(
        chunk_size=300,
        overlap=50,
        top_k=4,
        min_score=0.0,
        enable_reranking=True,
        rerank_mode="heuristic",
        rerank_top_k=3,
        enable_prompt_routing=True,   # يُفعّل فقط لو مفيش custom prompt
        include_few_shot=True,
        context_max_length=3000
    )

rag = RAGSystem(
        vector_db=vector_db,
        llm=llm,
        chunker=chunker,
        context_manager=manager,
        config=config,
        prompt=prompt
    )

loader=TextLoader("company_overview.txt").load()
rag.add_documents(loader)

queries = [
        "ما هو RAG وكيف يعمل؟",
        "ما هي مكونات نظام RAG الأساسية؟",
    ]

for i, query in enumerate(queries, 1):
    # -- استرجاع بدون توليد | Retrieve only
    # -- توليد الإجابة الكاملة | Full generation
    answer = rag.generate(
        query=query,
        include_sources=True,
        language=None   # None = كشف تلقائي للغة
        )
    print(f"\n{'='*60}")
    print(f"السؤال {i}: {query}")
    print(f"الإجابة: {answer}")

rag.set_prompt(few_shot)
answer = rag.generate("اشرح Embedding بإيجاز")
print(f"\n💬 FewShot Answer:\n{answer}")