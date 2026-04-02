from fennec.document_loaders import HTMLStringLoader
# load documents
def read_text(file_path:str)->str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
company_overview = read_text('company_overview.txt')
company_overview_loader = HTMLStringLoader(company_overview).load()


from fennec.monitor import MetricsCollector
from fennec.llm import GeminiInterface
from fennec.embeddings import GeminiEmbedder
from fennec.vector_database import FAISSVectorDatabase
from fennec.chunks import MultilanguageTextChunker
from fennec.context import ContextManager
from fennec.rag.core import RAGSystem

embedder=GeminiEmbedder(api_key=api)
base_rag=RAGSystem(
        vector_db=FAISSVectorDatabase(embedder=embedder),
        llm=GeminiInterface(api_key=api),
        chunker=MultilanguageTextChunker(),
        context_manager=ContextManager(),)

collector = MetricsCollector(max_metrics=10_000)

base_rag.add_documents(company_overview_loader)
def monitored_rag_query(query: str) -> str:
    """تنفيذ استعلام RAG مع تسجيل كل المقاييس"""
    # ── قياس خطوة الاسترجاع ──────────────────────────────── #
    with collector.timer("rag.retrieval.latency"):
        retrieved = base_rag.retrieve(query)
    collector.increment("rag.queries.total")
    collector.gauge("rag.docs.retrieved", len(retrieved))
    if not retrieved:
        collector.increment("rag.retrieval.failures")
        return "❌ لم يتم العثور على معلومات."
    top_score = retrieved[0][1] if retrieved else 0
    collector.histogram("rag.retrieval.top_score", top_score)
    collector.increment("rag.retrieval.success")
    # ── قياس خطوة بناء السياق ────────────────────────────── #
    with collector.timer("rag.context.build_time"):
        context = base_rag.context_manager.build(query, retrieved)
    collector.gauge("rag.context.length_chars", len(context))
    # ── قياس خطوة التوليد ────────────────────────────────── #
    with collector.timer("rag.generation.latency"):
        answer = base_rag.llm.generate(
            base_rag._build_prompt(query, context, language_pr="ar")
        )
    collector.gauge("rag.answer.length_chars", len(answer))
    collector.histogram("rag.answer.length_hist", len(answer))
    collector.increment("rag.queries.successful")
    return answer

    # ── تشغيل استعلامات متعددة ────────────────────────────────── #
test_queries = [
    "ما هو الـ RAG؟",
    "كيف يعمل تعلم الآلة؟",

]
print(f"\n  🚀 تشغيل {len(test_queries)} استعلام مع المراقبة:\n")
for q in test_queries:
    answer = monitored_rag_query(q)
    print(f"  Q: {q}")
    print(f"  A: {answer[:70]}...\n")

print(collector.get_summary())
