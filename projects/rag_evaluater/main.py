from fennec.evaluator import RAGEvaluator,generate_dashboard
from fennec.document_loaders import TextLoader
from fennec.llm import GeminiInterface
from fennec.embeddings import GeminiEmbedder
from fennec.vector_database import FAISSVectorDatabase
from fennec.chunks import MultilanguageTextChunker
from fennec.context import ContextManager,ContextConfig
from fennec.rag.core import RAGSystem ,RAGConfig

company_overview_loader = TextLoader("company_overview.txt").load()
embedder=GeminiEmbedder(api_key=api)
vector_db=FAISSVectorDatabase(embedder=embedder)
llm=GeminiInterface(api_key=api)
chunker=MultilanguageTextChunker()
context_manager=ContextManager()
ctx_config = ContextConfig(
    max_context_length = 3000,
    include_scores     = True,
    template           = "english",
)
context_manager = ContextManager(config=ctx_config)
print("✅ ContextManager: max=3000 chars, include_scores=True")

# ── LLM ─────────────────────────────────────────────────────────────────

print("✅ LLM: OpenAI gpt-4o-mini")

# ── RAGConfig ────────────────────────────────────────────────────────────
rag_config = RAGConfig(
    chunk_size            = 500,
    overlap               = 80,
    top_k                 = 4,          # استرجع 4 قطع لكل سؤال
    min_score             = 0.20,       # تجاهل القطع أقل من 20% تشابه
    enable_reranking      = True,
    rerank_mode           = "heuristic",
    enable_prompt_routing = True,       # يكشف نوع السؤال تلقائياً
    prompt_language       = "en",
    include_few_shot      = True,
)
rag_config.validate()
print("✅ RAGConfig: top_k=4, reranking=heuristic, routing=True")

# ── RAGSystem ────────────────────────────────────────────────────────────
rag = RAGSystem(
    vector_db       = vector_db,
    llm             = llm,
    chunker         = chunker,
    context_manager = context_manager,
    config          = rag_config,
)
print(f"✅ RAGSystem ready → {rag}")


# ══════════════════════════════════════════════════════════════════════════
#  2. قاعدة المعرفة — 5 مستندات عن AI
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("2. إضافة قاعدة المعرفة")
print("─" * 60)


# إضافة المستندات
results = rag.add_documents(company_overview_loader)
for doc_id, num_chunks in results.items():
    print(f"  📄 {doc_id}: {num_chunks} chunks")

stats = rag.get_stats()
print(f"\n  إجمالي المستندات : {stats['total_documents']}")
print(f"  إجمالي القطع     : {stats['total_chunks']}")
print(f"  Vector DB size   : {stats['vector_db_size']}")


# ══════════════════════════════════════════════════════════════════════════
#  3. أسئلة مباشرة (بدون تقييم)
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("3. أسئلة مباشرة على النظام")
print("─" * 60)

DIRECT_QUESTIONS = [
    "What is Retrieval-Augmented Generation and how does it work?",
    "What are the main types of FAISS indexes and when to use each?",
    "Why do large language models hallucinate and how can RAG help?",
    "What embedding model should I use for Arabic text in a RAG system?",
    "What chunk size should I use for RAG?",
]

for i, q in enumerate(DIRECT_QUESTIONS, 1):
    print(f"\n  Q{i}: {q}")

    # استرجاع القطع
    retrieved = rag.retrieve(q, top_k=3)
    scores = [f"{score:.3f}" for _, score in retrieved]
    print(f"       ↳ استُرجع {len(retrieved)} قطع | أعلى درجات: {', '.join(scores)}")

    # توليد الإجابة
    answer = rag.generate(q, include_sources=False, language="en")
    print(f"       ↳ {answer[:200].strip()}{'...' if len(answer) > 200 else ''}")


# ══════════════════════════════════════════════════════════════════════════
#  4. التقييم الكامل بـ RAGEvaluator
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("4. التقييم الكامل بـ RAGEvaluator")
print("─" * 60)

# ── أسئلة التقييم مع إجابات مرجعية ────────────────────────────────────
EVAL_QUESTIONS = [
    "What is RAG and what are its main advantages?",
    "How does FAISS perform vector similarity search?",
]

REFERENCE_ANSWERS = [
    "RAG (Retrieval-Augmented Generation) enhances LLMs by combining generation "
    "with external knowledge retrieval. Advantages include reduced hallucinations, "
    "no retraining needed, source citations, and cost effectiveness.",

    "FAISS converts text into embedding vectors and performs similarity search "
    "using distance metrics like cosine similarity or L2 distance to find the "
    "k nearest vectors to a query embedding.",

    "HNSW builds a graph structure for fast approximate search and is best for "
    "speed-accuracy balance. IVF clusters vectors and only searches nearby clusters, "
    "trading some accuracy for speed on large datasets.",

    "The three phases are: Indexing (split documents, embed, store in vector DB), "
    "Retrieval (embed query, find nearest chunks), and Generation "
    "(inject retrieved chunks into LLM prompt with the question).",

    "Small chunks give precise retrieval but lack context; large chunks provide "
    "more context but dilute the signal. A common starting point is chunk_size=500 "
    "with overlap=100.",

    "Hallucination is when LLMs generate incorrect or fabricated content. RAG "
    "reduces it by anchoring answers to retrieved factual passages from the "
    "knowledge base.",

    "OpenAI text-embedding-3-large produces 3072-dimensional vectors.",

    "Semantic chunking groups semantically related sentences using embeddings, "
    "producing coherent variable-size chunks. Fixed-size chunking simply splits "
    "every N characters which can break sentences mid-way.",
]

# ── تهيئة المُقيّم ───────────────────────────────────────────────────────
evaluator = RAGEvaluator(
    rag                     = rag,
    hallucination_threshold = 0.65,
    verbose                 = True,
)

# ── تشغيل التقييم ────────────────────────────────────────────────────────
report = evaluator.evaluate(
    questions         = EVAL_QUESTIONS,
    reference_answers = REFERENCE_ANSWERS,
)


# ══════════════════════════════════════════════════════════════════════════
#  5. طباعة التقرير الكامل
# ══════════════════════════════════════════════════════════════════════════

evaluator.print_report(report)


# ══════════════════════════════════════════════════════════════════════════
#  6. تفاصيل كل سؤال
# ══════════════════════════════════════════════════════════════════════════

print("─" * 60)
print("6. تفاصيل إضافية لكل سؤال")
print("─" * 60)

for i, result in enumerate(report.results, 1):
    r   = result.retrieval
    g   = result.generation
    hall_icon = "🚨" if g.hallucination.is_hallucination else "✅"

    print(f"\n  [{i}] {result.query[:65]}")
    print(f"       Grade        : {g.grade} ({g.overall_score:.1%})")
    print(f"       Faithfulness : {g.faithfulness_score:.1%}")
    print(f"       Relevance    : {g.relevance_score:.1%}")
    print(f"       Completeness : {g.completeness_score:.1%}")
    print(f"       Retrieval    : top={r.top_score:.3f}  avg={r.avg_score:.3f}  "
          f"chunks={r.num_chunks}  ({r.quality_label})")
    print(f"       Latency      : ret={r.latency_ms:.0f}ms  gen={g.latency_ms:.0f}ms  "
          f"total={r.latency_ms+g.latency_ms:.0f}ms")
    print(f"       Hallucination: {hall_icon} conf={g.hallucination.confidence_score:.3f}")
    if g.hallucination.is_hallucination and g.hallucination.recommendation:
        print(f"       ⚠️  Tip: {g.hallucination.recommendation[:80]}")


# ══════════════════════════════════════════════════════════════════════════
#  7. توزيع الدرجات
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("7. توزيع الدرجات")
print("─" * 60)

dist = report.grade_distribution
total = sum(dist.values())

for grade, count in dist.items():
    bar = "█" * count + "░" * (total - count)
    pct = count / total * 100 if total else 0
    print(f"  {grade}  {bar}  {count}/{total} ({pct:.0f}%)")

print(f"\n  صحة النظام : {report.system_health}")
print(f"  متوسط الوقت: {report.avg_latency_ms:.0f}ms")


# ══════════════════════════════════════════════════════════════════════════
#  8. إحصائيات HallucinationGuard
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("8. إحصائيات HallucinationGuard")
print("─" * 60)

guard_stats = evaluator.get_guard_statistics()
for k, v in guard_stats.items():
    print(f"  {k}: {v}")


# ══════════════════════════════════════════════════════════════════════════
#  9. إحصائيات MetricsCollector
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("9. إحصائيات MetricsCollector")
print("─" * 60)

metrics = evaluator.get_metrics_summary()
print("  Counters:")
for k, v in metrics["counters"].items():
    print(f"    {k}: {v}")

print("  Gauges (last value):")
for k, v in metrics["gauges"].items():
    print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")


# ══════════════════════════════════════════════════════════════════════════
#  10. حفظ التقرير وتوليد Dashboard
# ══════════════════════════════════════════════════════════════════════════
import os
print("\n" + "─" * 60)
print("10. الحفظ والتصدير")
print("─" * 60)

# حفظ كـ JSON
OUTPUT_DIR = "./dashbord_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)



# توليد Dashboard HTML
html_path = os.path.join(OUTPUT_DIR, "eval_dashboard.html")
generate_dashboard(report, output_path=html_path)

print(f"  📁 ملفات الإخراج في: {OUTPUT_DIR}/")
print(f"  🌐 HTML  : {html_path}")
print(f"      افتح rag_output/eval_dashboard.html في المتصفح!")


# ══════════════════════════════════════════════════════════════════════════
#  11. إحصائيات RAGSystem النهائية
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("11. إحصائيات RAGSystem")
print("─" * 60)

final_stats = rag.get_stats()
print(f"  total_documents  : {final_stats['total_documents']}")
print(f"  total_chunks     : {final_stats['total_chunks']}")
print(f"  total_queries    : {final_stats['total_queries']}")
print(f"  successful       : {final_stats['successful_queries']}")
print(f"  failed           : {final_stats['failed_queries']}")
print(f"  vector_db_size   : {final_stats['vector_db_size']}")
print(f"  chunker_type     : {final_stats['chunker_type']}")
