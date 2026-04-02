from fennec.llm import GeminiInterface
from fennec.embeddings import GeminiEmbedder
from fennec.vector_database import FAISSVectorDatabase
from fennec.chunks import MultilanguageTextChunker
from fennec.context import ContextManager
from fennec.rag.core import RAGSystem
from fennec.document_loaders import TextLoader
embedder=GeminiEmbedder(api_key=api)
base_rag=RAGSystem(
        vector_db=FAISSVectorDatabase(embedder=embedder),
        llm=GeminiInterface(api_key=api),
        chunker=MultilanguageTextChunker(),
        context_manager=ContextManager(),)
from fennec.cache import MultiLevelCache, CacheConfig, CacheStrategy
from typing import Tuple
import time

load=TextLoader("company_overview.txt").load()

cache_config = CacheConfig(
    l1_max_items=100,
    l2_max_items=500,
    default_ttl=600,          # نتيجة صالحة لـ 10 دقائق
    enable_stats=True,
)
cache = MultiLevelCache(strategy=CacheStrategy.LRU, config=cache_config)

base_rag.add_documents(load)
def cached_rag_query(query: str) -> Tuple[str, bool]:
    """استعلام RAG مع Cache — يُرجع (answer, from_cache)"""
    cache_key = f"rag:query:{query.strip().lower()}"
    # 1) تحقق من الـ Cache أولاً
    cached = cache.get(cache_key)
    if cached:
        return cached, True
    # 2) تنفيذ الـ RAG الحقيقي
    answer = base_rag.generate(query)
    # 3) حفظ النتيجة في الـ Cache
    cache.set(cache_key, answer)
    return answer, False
    # ── اختبار الـ Cache ──────────────────────────────────────── #
queries = [
    "ما هو الـ RAG وكيف يعمل؟",
    "ما هو الذكاء الاصطناعي؟",
    "ما هو الـ RAG وكيف يعمل؟",    # ← سيُجاب من الـ Cache
    "ما هو الذكاء الاصطناعي؟",     # ← سيُجاب من الـ Cache
    "كيف تعمل النماذج اللغوية الكبيرة؟",
]
print(f"\n  🔍 تشغيل {len(queries)} استعلام على الـ RAG:\n")
for q in queries:
    t0 = time.perf_counter()
    answer, from_cache = cached_rag_query(q)
    elapsed = (time.perf_counter() - t0) * 1000
    source = "⚡ Cache" if from_cache else "🔄 RAG"
    print(f"  {source} ({elapsed:.1f}ms)")
    print(f"  Q: {q}")
    print(f"  A: {answer[:80]}...")
    print()
# ── إحصائيات الـ Cache ────────────────────────────────────── #
stats = cache.get_stats()
print(f"  📊 Cache Stats:")
print(f"     L1 items : {stats.get('l1_items', 0)}")
print(f"     hits     : {stats.get('hits', 0)}")
print(f"     misses   : {stats.get('misses', 0)}")
hit_rate = stats.get("hits", 0) / max(stats.get("hits", 0) + stats.get("misses", 0), 1)
print(f"     hit rate : {hit_rate:.0%}")

