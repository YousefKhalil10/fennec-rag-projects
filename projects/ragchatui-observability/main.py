
from __future__ import annotations
import logging
import random
import time
from typing import Dict, List, Optional, Tuple

# ── مكوّنات المكتبة ──────────────────────────────────────────────────────
from fennec.llm import MistralInterface
from fennec.embeddings import OllamaEmbedder
from fennec.chunks import MultilanguageTextChunker
from fennec.vector_database import FAISSVectorDatabase
from fennec.context import ContextManager
from fennec.rag.core import RAGSystem, RAGConfig
from fennec.document_loaders import TextLoader
from fennec.rag.streaming_rag import StreamingRAG, StreamConfig, EventType
from fennec.observability import (
    ObservabilityConfig,
    ObservabilitySystem,
    AnomalyConfig,
    MetricType,
    DashboardExporter,
)
from fennec.observability.dashboard import ConversationLogger

# ── Chat UI ───────────────────────────────────────────────────────────────
from fennec.rag.rag_ui import RagChatUI

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)-7s | %(name)s — %(message)s",
)

# ════════════════════════════════════════════════════════════════════════════
# ① الاعتمادات
# ════════════════════════════════════════════════════════════════════════════
loader=TextLoader("company_overview.txt").load()
llm      = MistralInterface(api_key=api)
embedder = OllamaEmbedder()
chunker  = MultilanguageTextChunker(chunk_size=200, overlap=50)
vd       = FAISSVectorDatabase(embedder=embedder)
context  = ContextManager()



# ════════════════════════════════════════════════════════════════════════════
# ③ RAGObservabilityWrapper — متوافق مع RagChatUI
# ════════════════════════════════════════════════════════════════════════════

class RAGObservabilityWrapper:
    """
    يلتف حول RAGSystem ويُضيف Observability كاملة مع دعم RagChatUI.

    التوافق مع RagChatUI:
    ─────────────────────
    الـ RAGAdapter داخل RagChatUI يبحث بالترتيب عن:
      1. generate(query, include_sources)   ← نستخدمها
      2. query(query)
      3. ask(query, ...)

    كذلك يستدعي لإضافة المستندات:
      rag.ingest({doc_id: text})            ← نوفّرها

    ولحذف المستندات:
      rag.delete(doc_id)                    ← نوفّرها (اختياري)

    ولإحصائيات الـ health:
      rag.get_stats()                       ← نوفّرها
    """

    def __init__(
        self,
        rag:         RAGSystem,
        obs:         ObservabilitySystem,
        conv_logger: ConversationLogger,
    ):
        self.rag         = rag
        self.obs         = obs
        self.conv_logger = conv_logger
        self._query_count = 0

    # ── مساعد تسجيل المقاييس ──────────────────────────────────────────────
    def _rec(
        self,
        name:  str,
        value: float,
        mtype: MetricType = MetricType.GAUGE,
        tags:  Optional[Dict] = None,
    ) -> None:
        self.obs.record(name, value, mtype, tags or {})

    # ── generate() ← الدالة التي تستدعيها RagChatUI عبر RAGAdapter ──────────
    def generate(self, query: str, include_sources: bool = True) -> str:
        """
        الدالة الرئيسية للاستعلام — يستدعيها RAGAdapter تلقائياً.
        تُعيد str فقط (لا tuple) حتى يعالجها _extract_answer_and_sources بشكل صحيح.
        """
        t_total = time.perf_counter()
        self._query_count += 1

        self._rec("rag.query_count", 1, MetricType.COUNTER)

        try:
            # ── Retrieval ────────────────────────────────────────────────
            t0        = time.perf_counter()
            retrieved = self.rag.retrieve(query)
            retrieval_ms = (time.perf_counter() - t0) * 1000

            self._rec("rag.retrieval_latency_ms", retrieval_ms, MetricType.TIMER)
            self._rec("rag.retrieved_docs_count", len(retrieved))

            if retrieved:
                avg_score = sum(s for _, s in retrieved) / len(retrieved)
                self._rec("rag.avg_similarity_score", avg_score)

            # ── Generation ───────────────────────────────────────────────
            t0     = time.perf_counter()
            answer = self.rag.generate(query, include_sources=include_sources)
            generation_ms = (time.perf_counter() - t0) * 1000

            self._rec("rag.generation_latency_ms", generation_ms, MetricType.TIMER)
            self._rec("rag.answer_length_chars",   len(answer))

            total_ms = (time.perf_counter() - t_total) * 1000
            self._rec("rag.total_latency_ms", total_ms, MetricType.TIMER)

            # ── Live Chat Log ────────────────────────────────────────────
            self.conv_logger.log(
                session_id    = "chat_ui",
                query         = query,
                answer        = answer,
                latency_ms    = total_ms,
                sources_count = len(retrieved),
            )

            return answer

        except Exception:
            self._rec("rag.error_count", 1, MetricType.COUNTER)
            raise

    # ── ingest() ← يستدعيها RAGAdapter عند رفع ملف من الـ UI ─────────────────
    def ingest(self, docs: Dict[str, str]) -> Dict[str, int]:
        """
        يُحوِّل dict {doc_id: text} للـ RAGSystem.
        الـ RAGAdapter يستدعيها بالصيغة: rag.ingest({doc_id: text})
        """
        t0     = time.perf_counter()
        result = self.rag.add_documents(docs)          # RAGSystem.ingest()
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self._rec("rag.indexing_latency_ms",  elapsed_ms,
                  MetricType.TIMER)
        self._rec("rag.indexed_chunks_count", sum(result.values()),
                  MetricType.COUNTER)
        return result

    # ── add_documents() ← للاستخدام المباشر من الكود (خارج UI) ──────────────
    def add_documents(self, docs: Dict[str, str]) -> Dict[str, int]:
        return self.ingest(docs)

    # ── delete() ← يستدعيها RAGAdapter عند حذف مستند من الـ UI ──────────────
    def delete(self, doc_id: str) -> bool:
        """تمرير طلب الحذف للـ RAGSystem إن كان يدعمه."""
        for method in ("delete", "delete_document", "remove", "remove_document"):
            fn = getattr(self.rag, method, None)
            if fn:
                try:
                    fn(doc_id)
                    return True
                except Exception:
                    pass
        return False

    # ── get_stats() ← يستدعيها RAGAdapter لعرض إحصائيات الـ health ──────────
    def get_stats(self) -> Dict:
        alerts   = self.obs.get_active_alerts()
        chat     = self.conv_logger.get_stats()
        summary  = self.obs.get_metrics_summary("rag.total_latency_ms")
        return {
            "total_queries":      self._query_count,
            "active_alerts":      len(alerts),
            "avg_latency_ms":     summary.get("mean", 0),
            "p90_latency_ms":     summary.get("p90", 0),
            "chat_sessions":      chat.get("unique_sessions", 0),
            "total_logged":       chat.get("total_logged", 0),
        }

    # ── retrieve() ← للاستخدام المباشر من الكود ──────────────────────────────
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple]:
        t0      = time.perf_counter()
        results = self.rag.retrieve(query, top_k=top_k)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._rec("rag.retrieval_latency_ms", elapsed_ms, MetricType.TIMER)
        self._rec("rag.retrieved_docs_count", len(results))
        return results


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
            top_k                 = 3,
            min_score             = 0.0,
            enable_reranking      = False,
            enable_prompt_routing = False,
        ),
    )


def build_observability() -> ObservabilitySystem:
    obs = ObservabilitySystem(
        config=ObservabilityConfig(
            environment            = "development",
            window_seconds         = 120.0,
            alert_cooldown_seconds = 15,
            anomaly                = AnomalyConfig(
                enabled          = True,
                algorithm        = "zscore",
                zscore_threshold = 2.5,
                min_samples      = 5,
                window_seconds   = 120.0,
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
# ⑤ إحصائيات نهائية (للاستخدام من الكود، ليس من الـ UI)
# ════════════════════════════════════════════════════════════════════════════

def print_final_stats(obs: ObservabilitySystem, conv_logger: ConversationLogger) -> None:
    print("\n📊 ملخص الإحصائيات النهائية:")
    print("─" * 50)

    s = obs.get_system_stats()
    print(f"  إجمالي القياسات  : {s['total_recorded']}")
    print(f"  إجمالي التنبيهات : {s['total_alerts']}")
    print(f"  الشذوذات المكتشفة: {s['total_anomalies']}")

    chat_stats = conv_logger.get_stats()
    print(f"\n💬 Live Chat:")
    print(f"  إجمالي المحادثات : {chat_stats['total_logged']}")
    print(f"  جلسات مختلفة    : {chat_stats['unique_sessions']}")
    print(f"  متوسط الاستجابة  : {chat_stats['avg_latency_ms']} ms")

    summary = obs.get_metrics_summary("rag.total_latency_ms")
    if summary.get("count", 0) > 0:
        print(f"\n📈 rag.total_latency_ms:")
        print(f"  عدد    : {summary['count']}")
        print(f"  متوسط  : {summary['mean']:.1f}ms")
        print(f"  p90    : {summary['p90']:.1f}ms")
        print(f"  p99    : {summary['p99']:.1f}ms")

    alerts = obs.get_active_alerts()
    print(f"\n🔔 التنبيهات النشطة: {len(alerts)}")
    for a in alerts[-5:]:
        print(f"  [{a.severity.upper()}] {a.metric_name} — {a.message}")


# ════════════════════════════════════════════════════════════════════════════
# ⑥ main
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   RAG + Observability + RagChatUI Demo                  ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # ── بناء المكوّنات ────────────────────────────────────────────────────
    print("⚙️  بناء RAG system...")
    rag = build_rag()

    print("⚙️  بناء Observability system...")
    obs = build_observability()

    conv_logger = ConversationLogger(max_turns=500)

    # ── Wrapper يجمع الثلاثة ──────────────────────────────────────────────
    wrapper = RAGObservabilityWrapper(rag=rag, obs=obs, conv_logger=conv_logger)

    # ── Observability Dashboard على port 8888 (في thread منفصل) ──────────
    dashboard = DashboardExporter(
        obs,
        port                = 8888,
        refresh_seconds     = 2,
        conversation_logger = conv_logger,
    )
    dashboard.start()
    print("📊 Observability Dashboard → http://localhost:8888")

    # ── فهرسة المستندات ───────────────────────────────────────────────────
    print("\n📄 فهرسة المستندات...")
    result = wrapper.add_documents(loader)
    for doc_id, n_chunks in result.items():
        print(f"  ✅ {doc_id}: {n_chunks} chunks")

    # ── Chat UI على port 7860 ─────────────────────────────────────────────
    ui = RagChatUI(
        rag             = wrapper,          # ← الـ wrapper مباشرة
        title           = "🤖 RAG Demo مع Observability",
        description     = "اسألني عن التعلم الآلي والذكاء الاصطناعي وأنظمة RAG",
        theme           = "dark",
        language        = "ar",
        include_sources = True,
        max_sessions    = 50,
        persist_path    = "./sessions.json",
    )

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  🚀 Chat UI       → http://localhost:7860               ║")
    print("║  📊 Observability → http://localhost:8888               ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    try:
        ui.launch(
            host         = "0.0.0.0",
            port         = 7860,
            open_browser = True,
            debug        = False,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  توقف المستخدم")
    finally:
        print_final_stats(obs, conv_logger)
        obs.stop()
        dashboard.stop()
        print("✅ تم الإيقاف بشكل نظيف")


if __name__ == "__main__":
    main()
