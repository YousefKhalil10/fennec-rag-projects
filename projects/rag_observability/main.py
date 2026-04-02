import logging
import random
import time
from typing import Dict, List, Optional, Tuple

# ── مكوّنات المكتبة ──────────────────────────────────────────────────────
from fennec.document_loaders import TextLoader
from fennec.llm import GeminiInterface
from fennec.embeddings import GeminiEmbedder
from fennec.chunks import MultilanguageTextChunker
from fennec.vector_database import FAISSVectorDatabase
from fennec.context import ContextManager
from fennec.rag.core import RAGSystem, RAGConfig
from fennec.rag.streaming_rag import StreamingRAG, StreamConfig, EventType
from fennec.observability import (
    ObservabilityConfig,
    ObservabilitySystem,
    AnomalyConfig,
    MetricType,
    DashboardExporter,
)
from fennec.observability.dashboard import ConversationLogger   # ← Live Chat

# ── إعداد الـ logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)-7s | %(name)s — %(message)s",
)

company_overview_loader = TextLoader("company_overview.txt").load()


llm      = GeminiInterface(api_key=api)
embedder = GeminiEmbedder(api_key=api)
chunker  = MultilanguageTextChunker(chunk_size=200, overlap=50)
vd       = FAISSVectorDatabase(embedder=embedder)
context  = ContextManager()

# ════════════════════════════════════════════════════════════════════════════
# ② بيانات الـ Demo
# ════════════════════════════════════════════════════════════════════════════



DEMO_QUERIES = [
    "ما هو التعلم الآلي؟",
    "كيف يعمل التعلم العميق؟",
    "ما هو RAG وكيف يعمل؟",
    "ما الفرق بين قواعد البيانات المتجهية والعادية؟",
    "ما هي التضمينات وكيف تؤثر على RAG؟",
    "كيف يتم رصد أداء أنظمة الذكاء الاصطناعي؟",
]

# ════════════════════════════════════════════════════════════════════════════
# ③ RAGObservabilityWrapper — يجمع RAG + Observability + Live Chat
# ════════════════════════════════════════════════════════════════════════════

class RAGObservabilityWrapper:
    """
    يلتف حول RAGSystem ويُضيف:
    - Observability كاملة (latency, docs, errors…)
    - تسجيل تلقائي في ConversationLogger لعرضه في Live Chat
    """

    def __init__(
        self,
        rag: RAGSystem,
        obs: ObservabilitySystem,
        conv_logger: ConversationLogger,
    ):
        self.rag         = rag
        self.obs         = obs
        self.conv_logger = conv_logger

    # ── مساعد تسجيل المقاييس ─────────────────────────────────────────
    def _rec(
        self,
        name: str,
        value: float,
        mtype: MetricType = MetricType.GAUGE,
        tags: Optional[Dict] = None,
    ) -> None:
        self.obs.record(name, value, mtype, tags or {})

    # ── فهرسة المستندات ──────────────────────────────────────────────
    def add_documents(self, docs: Dict[str, str]) -> Dict[str, int]:
        t0     = time.perf_counter()
        result = self.rag.add_documents(docs)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self._rec("rag.indexing_latency_ms",  elapsed_ms,          MetricType.TIMER)
        self._rec("rag.indexed_chunks_count", sum(result.values()), MetricType.COUNTER)
        return result

    # ── الاسترجاع ────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple]:
        t0      = time.perf_counter()
        results = self.rag.retrieve(query, top_k=top_k)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self._rec("rag.retrieval_latency_ms", elapsed_ms,   MetricType.TIMER)
        self._rec("rag.retrieved_docs_count", len(results))
        if results:
            avg_score = sum(s for _, s in results) / len(results)
            self._rec("rag.avg_similarity_score", avg_score)
        return results

    # ── الاستعلام الكامل (Query + Live Chat log) ──────────────────────
    def query(
        self,
        query: str,
        session_id: str = "default",
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        t_total = time.perf_counter()
        _tags   = tags or {}

        self._rec("rag.query_count", 1, MetricType.COUNTER, _tags)

        try:
            # مرحلة الاسترجاع
            t0 = time.perf_counter()
            retrieved = self.rag.retrieve(query)
            retrieval_ms = (time.perf_counter() - t0) * 1000
            self._rec("rag.retrieval_latency_ms", retrieval_ms, MetricType.TIMER, _tags)
            self._rec("rag.retrieved_docs_count", len(retrieved), tags=_tags)
            if retrieved:
                avg_score = sum(s for _, s in retrieved) / len(retrieved)
                self._rec("rag.avg_similarity_score", avg_score, tags=_tags)

            # مرحلة التوليد
            t0 = time.perf_counter()
            answer = self.rag.generate(query)
            generation_ms = (time.perf_counter() - t0) * 1000
            self._rec("rag.generation_latency_ms", generation_ms, MetricType.TIMER, _tags)
            self._rec("rag.answer_length_chars",   len(answer),   tags=_tags)

            total_ms = (time.perf_counter() - t_total) * 1000
            self._rec("rag.total_latency_ms", total_ms, MetricType.TIMER, _tags)

            # ✅ تسجيل المحادثة في Live Chat
            self.conv_logger.log(
                session_id    = session_id,
                query         = query,
                answer        = answer,
                latency_ms    = total_ms,
                sources_count = len(retrieved),
            )

            return answer

        except Exception as exc:
            self._rec("rag.error_count", 1, MetricType.COUNTER, _tags)
            raise

    # ── البث مع Observability + Live Chat ────────────────────────────
    def stream_query(
        self,
        streaming_rag: StreamingRAG,
        query: str,
        session_id: str = "default",
        print_tokens: bool = True,
    ) -> str:
        tokens: List[str] = []
        t_start            = time.perf_counter()
        retrieval_ms       = 0.0
        num_docs           = 0
        t_retrieval_start  = None

        for event in streaming_rag.stream_events(query):

            if event.type == EventType.RETRIEVAL_START:
                t_retrieval_start = time.perf_counter()

            elif event.type == EventType.RETRIEVAL_DONE:
                retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000
                num_docs     = event.data.get("num_docs", 0)
                self._rec("rag.retrieval_latency_ms", retrieval_ms, MetricType.TIMER)
                self._rec("rag.retrieved_docs_count", num_docs)
                if print_tokens:
                    print(f"\n  📂 استُرجع {num_docs} مستندات ({retrieval_ms:.0f}ms)")

            elif event.type == EventType.CHUNK:
                tokens.append(event.data)
                if print_tokens:
                    print(event.data, end="", flush=True)

            elif event.type == EventType.GENERATION_DONE:
                generation_ms = event.data.get("total_latency", 0) * 1000
                self._rec("rag.generation_latency_ms", generation_ms, MetricType.TIMER)

            elif event.type == EventType.ERROR:
                self._rec("rag.error_count", 1, MetricType.COUNTER)
                if print_tokens:
                    print(f"\n  ❌ خطأ: {event.data.get('msg')}")

        total_ms    = (time.perf_counter() - t_start) * 1000
        full_answer = "".join(tokens)

        self._rec("rag.total_latency_ms",    total_ms,          MetricType.TIMER)
        self._rec("rag.answer_length_chars", len(full_answer))
        self._rec("rag.query_count",         1,                 MetricType.COUNTER)

        # ✅ تسجيل المحادثة في Live Chat
        self.conv_logger.log(
            session_id    = session_id,
            query         = query,
            answer        = full_answer,
            latency_ms    = total_ms,
            sources_count = num_docs,
        )

        if print_tokens:
            print(f"\n  ⏱ الزمن الكلي: {total_ms:.0f}ms")

        return full_answer


# ════════════════════════════════════════════════════════════════════════════
# ④ بناء المكوّنات
# ════════════════════════════════════════════════════════════════════════════

def build_rag() -> RAGSystem:
    return RAGSystem(
        vector_db       = vd,
        llm             = llm,
        chunker         = chunker,
        context_manager = context,
        config          = RAGConfig(
            top_k                  = 3,
            min_score              = 0.0,
            enable_reranking       = False,
            enable_prompt_routing  = False,
        ),
    )


def build_observability() -> ObservabilitySystem:
    obs = ObservabilitySystem(
        config=ObservabilityConfig(
            environment           = "development",
            window_seconds        = 120.0,
            alert_cooldown_seconds= 15,
            anomaly               = AnomalyConfig(
                enabled           = True,
                algorithm         = "zscore",
                zscore_threshold  = 2.5,
                min_samples       = 5,
                window_seconds    = 120.0,
            ),
        )
    )

    obs.add_alert_rule(
        rule_id     = "slow_retrieval",
        metric_name = "rag.retrieval_latency_ms",
        condition   = lambda v: v > 500,
        message     = "زمن الاسترجاع تجاوز 500ms",
        severity    = "warning",
    )
    obs.add_alert_rule(
        rule_id     = "very_slow_total",
        metric_name = "rag.total_latency_ms",
        condition   = lambda v: v > 3000,
        message     = "الزمن الكلي تجاوز 3 ثوانٍ",
        severity    = "critical",
    )
    obs.add_alert_rule(
        rule_id     = "no_docs_retrieved",
        metric_name = "rag.retrieved_docs_count",
        condition   = lambda v: v < 1,
        message     = "لم يُسترجَع أي مستند",
        severity    = "critical",
    )
    obs.add_alert_rule(
        rule_id     = "low_similarity",
        metric_name = "rag.avg_similarity_score",
        condition   = lambda v: v < 0.3,
        message     = "درجة التشابه منخفضة جداً",
        severity    = "warning",
    )
    return obs


# ════════════════════════════════════════════════════════════════════════════
# ⑤ حلقة الطلبات
# ════════════════════════════════════════════════════════════════════════════

# أسماء جلسات وهمية لمحاكاة عدة مستخدمين
_SESSIONS = ["user-alpha", "user-beta", "user-gamma", "user-delta"]


def run_query_loop(
    wrapper:       RAGObservabilityWrapper,
    streaming_rag: StreamingRAG,
    iterations:    int = 20,
    delay_range:   Tuple[float, float] = (0.5, 2.0),
) -> None:
    print("\n" + "═" * 60)
    print(f"🚀 إرسال {iterations} طلب للـ RAG system...")
    print("📊 افتح المتصفح على http://localhost:8888 → تبويب 💬 Live Chat")
    print("═" * 60 + "\n")

    for i in range(iterations):
        query      = random.choice(DEMO_QUERIES)
        session_id = random.choice(_SESSIONS)
        streaming  = (i % 3 == 0)

        print(f"\n[{i+1}/{iterations}] {'🌊 Stream' if streaming else '📝 Query'}"
              f" | {session_id} | {query}")

        try:
            if streaming:
                print("  الإجابة: ", end="")
                wrapper.stream_query(streaming_rag, query,
                                     session_id=session_id, print_tokens=True)
            else:
                answer  = wrapper.query(query, session_id=session_id)
                preview = answer[:80] + "…" if len(answer) > 80 else answer
                print(f"  الإجابة: {preview}")

        except Exception as exc:
            print(f"  ❌ خطأ: {exc}")

        time.sleep(random.uniform(*delay_range))

    print("\n\n" + "═" * 60)
    print("✅ انتهت جميع الطلبات!")


# ════════════════════════════════════════════════════════════════════════════
# ⑥ إحصائيات نهائية
# ════════════════════════════════════════════════════════════════════════════

def print_final_stats(
    obs:         ObservabilitySystem,
    conv_logger: ConversationLogger,
) -> None:
    print("\n📊 ملخص الإحصائيات النهائية:")
    print("─" * 50)

    s = obs.get_system_stats()
    print(f"  إجمالي القياسات  : {s['total_recorded']}")
    print(f"  إجمالي التنبيهات : {s['total_alerts']}")
    print(f"  الشذوذات المكتشفة: {s['total_anomalies']}")
    print(f"  المقاييس الفريدة : {s['unique_metrics']}")

    chat_stats = conv_logger.get_stats()
    print(f"\n💬 إحصائيات Live Chat:")
    print(f"  إجمالي المحادثات : {chat_stats['total_logged']}")
    print(f"  جلسات مختلفة    : {chat_stats['unique_sessions']}")
    print(f"  متوسط الاستجابة  : {chat_stats['avg_latency_ms']} ms")

    print("\n📈 تفاصيل الزمن الكلي (rag.total_latency_ms):")
    summary = obs.get_metrics_summary("rag.total_latency_ms")
    if summary.get("count", 0) > 0:
        print(f"  عدد القياسات : {summary['count']}")
        print(f"  المتوسط      : {summary['mean']:.1f}ms")
        print(f"  الحد الأدنى  : {summary['min']:.1f}ms")
        print(f"  الحد الأقصى  : {summary['max']:.1f}ms")
        print(f"  p90          : {summary['p90']:.1f}ms")
        print(f"  p99          : {summary['p99']:.1f}ms")

    print("\n🔔 التنبيهات النشطة:")
    alerts = obs.get_active_alerts()
    if alerts:
        for a in alerts[-5:]:
            print(f"  [{a.severity.upper()}] {a.metric_name} — {a.message}")
    else:
        print("  ✅ لا توجد تنبيهات")


# ════════════════════════════════════════════════════════════════════════════
# ⑦ main
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   RAG + Observability + Live Chat Dashboard Demo     ║")
    print("╚═══════════════════════════════════════════════════════╝\n")

    # ── بناء المكوّنات ───────────────────────────────────────────────
    print("⚙️  بناء RAG system...")
    rag = build_rag()

    print("⚙️  بناء Observability system...")
    obs = build_observability()

    # ── ConversationLogger للـ Live Chat ─────────────────────────────
    conv_logger = ConversationLogger(max_turns=200)

    # ── Wrapper يجمع الثلاثة ─────────────────────────────────────────
    wrapper = RAGObservabilityWrapper(rag=rag, obs=obs, conv_logger=conv_logger)

    # ── Dashboard مع Live Chat ────────────────────────────────────────
    dashboard = DashboardExporter(
        obs,
        port                = 8888,
        refresh_seconds     = 2,
        conversation_logger = conv_logger,   # ← يفعّل تبويب Live Chat
    )
    dashboard.start()

    # ── فهرسة المستندات ──────────────────────────────────────────────
    print("\n📄 فهرسة المستندات...")
    result = wrapper.add_documents(company_overview_loader)
    for doc_id, n_chunks in result.items():
        print(f"  ✅ {doc_id}: {n_chunks} chunks")

    # ── StreamingRAG ─────────────────────────────────────────────────
    streaming_rag = StreamingRAG(
        rag_system = rag,
        llm        = rag.llm,
        config     = StreamConfig(
            chunk_size    = 4,
            sim_delay     = 0.015,
            max_context_docs = 3,
            max_doc_chars    = 400,
        ),
    )

    # ── حلقة الطلبات ─────────────────────────────────────────────────
    try:
        run_query_loop(
            wrapper       = wrapper,
            streaming_rag = streaming_rag,
            iterations    = 25,
            delay_range   = (0.3, 1.2),
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  توقف المستخدم")

    # ── الإحصائيات النهائية ──────────────────────────────────────────
    print_final_stats(obs, conv_logger)

    # ── إبقاء الـ Dashboard شغّال ────────────────────────────────────
    print(f"\n🌐 الـ Dashboard لا يزال يعمل على http://localhost:8888")
    print("   اضغط Ctrl+C للخروج\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 إيقاف النظام...")
    finally:
        obs.stop()
        dashboard.stop()
        print("✅ تم الإيقاف بشكل نظيف")


# ════════════════════════════════════════════════════════════════════════════
# دعم Jupyter Notebook
# ════════════════════════════════════════════════════════════════════════════

def jupyter_demo(iterations: int = 10, port: int = 8888):
    """
    من داخل Jupyter:
        from rag_demo import jupyter_demo
        wrapper, obs, conv_logger = jupyter_demo(iterations=10)
    """
    import nest_asyncio
    nest_asyncio.apply()

    rag         = build_rag()
    obs         = build_observability()
    conv_logger = ConversationLogger(max_turns=200)
    wrapper     = RAGObservabilityWrapper(rag=rag, obs=obs, conv_logger=conv_logger)

    DashboardExporter(obs, port=port, refresh_seconds=2,
                      conversation_logger=conv_logger).start()

    wrapper.add_documents(company_overview_loader)

    streaming_rag = StreamingRAG(
        rag_system=rag, llm=rag.llm,
        config=StreamConfig(chunk_size=4, sim_delay=0.01, max_context_docs=3),
    )

    run_query_loop(wrapper, streaming_rag,
                   iterations=iterations, delay_range=(0.2, 0.8))
    print_final_stats(obs, conv_logger)

    return wrapper, obs, conv_logger


if __name__ == "__main__":
    main()
