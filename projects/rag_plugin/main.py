from fennec.llm import GeminiInterface
from fennec.document_loaders import HTMLStringLoader
from fennec.embeddings import GeminiEmbedder
from fennec.vector_database import FAISSVectorDatabase
from fennec.chunks import MultilanguageTextChunker
from fennec.context import ContextManager
from fennec.rag.core import RAGSystem


def read_text(file_path:str)->str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
    
company_overview = read_text('company_overview.txt')
company_overview_loader = HTMLStringLoader(company_overview).load()

embedder=GeminiEmbedder(api_key=api)
base_rag=RAGSystem(
        vector_db=FAISSVectorDatabase(embedder=embedder),
        llm=GeminiInterface(api_key=api),
        chunker=MultilanguageTextChunker(),
        context_manager=ContextManager(),)

from fennec.plugins import (
    Plugin, PluginManager, PluginConfig,
    PluginMetadata, PluginStatus, PluginPriority, PermissionType,
)

base_rag.add_documents(company_overview_loader)

# تعريف نظام RAG أولاً
rag_system=base_rag

class QueryCleanerPlugin(Plugin):
    async def initialize(self) -> bool:
        self.status = PluginStatus.ENABLED          # ← ACTIVE → ENABLED
        self.initialized_at = __import__("datetime").datetime.now()
        return True
    async def execute(self, query: str = "") -> str:
        import re
        clean = re.sub(r"\s+", " ", query).strip()
        clean = re.sub(r"[؟?!]+$", "؟", clean)
        return clean
    async def cleanup(self):
        self.status = PluginStatus.DISABLED

class RAGQueryPlugin(Plugin):
    def __init__(self, metadata, config, rag_system):
        super().__init__(metadata, config)
        self._rag = rag_system
    async def initialize(self) -> bool:
        self.status = PluginStatus.ENABLED
        self.initialized_at = __import__("datetime").datetime.now()
        return True
    async def execute(self, query: str = "") -> dict:
        retrieved = self._rag.retrieve(query)
        answer = self._rag.generate(query)
        return {
            "query": query,
            "answer": answer,
            "num_sources": len(retrieved),
            "top_score": retrieved[0][1] if retrieved else 0.0,
        }
    async def cleanup(self):
        self.status = PluginStatus.DISABLED

class AnswerValidatorPlugin(Plugin):
    async def initialize(self) -> bool:
        self.status = PluginStatus.ENABLED
        self.initialized_at = __import__("datetime").datetime.now()
        return True
    async def execute(self, result: dict = None) -> dict:
        if result is None:
            return {"valid": False, "reason": "no result"}
        answer = result.get("answer", "")
        is_valid = len(answer) > 20 and result.get("num_sources", 0) > 0
        result["is_valid"]   = is_valid
        result["word_count"] = len(answer.split())
        result["confidence"] = min(result.get("top_score", 0) * 1.2, 1.0)
        return result
    async def cleanup(self):
        self.status = PluginStatus.DISABLED

# ── إنشاء الإضافات بالمعاملات الصحيحة ──────────────────────── #
cfg = PluginConfig(enabled=True, timeout=15.0, max_retries=1)

cleaner_plugin = QueryCleanerPlugin(
    PluginMetadata(
        name="query_cleaner", version="1.0.0",          # ← "1.0" → "1.0.0"
        author="fennec-rag", description="تنظيف الاستعلام",
        permissions=[PermissionType.FILE_READ.value]    # ← القيمة الصحيحة
    ), cfg)

rag_plugin = RAGQueryPlugin(
    PluginMetadata(
        name="rag_executor", version="1.0.0",
        author="fennec-rag", description="تنفيذ RAG",
        permissions=[PermissionType.FILE_READ.value, PermissionType.FILE_WRITE.value]
    ), cfg, base_rag)

validator_plugin = AnswerValidatorPlugin(
    PluginMetadata(
        name="answer_validator", version="1.0.0",
        author="fennec-rag", description="تدقيق الإجابة",
        permissions=[PermissionType.FILE_READ.value]
    ), cfg)

# ── تسجيل الإضافات (بدون initialize() مسبق — المدير يفعل ذلك) ─ #
manager = PluginManager(plugins_dir="./plugins_dir", safe_mode=False,
                        system_version="1.0.0", auto_discover=False)

for plugin in [cleaner_plugin, rag_plugin, validator_plugin]:
    manager.grant_all_permissions(plugin.name)      # ← يجب قبل register
    await manager.register_plugin(plugin)

# ── تشغيل الـ Pipeline ───────────────────────────────────────── #
raw_queries = [
    "  ما هو الـ RAG   ؟؟؟ ",
    "كيف يعمل تعلم الآلة !!! ",
    "ما هي النماذج اللغوية الكبيرة؟",
]

print(f"\n🔌 تشغيل RAG Pipeline عبر 3 إضافات:\n")
for raw_q in raw_queries:
    print(f"━━━ استعلام: '{raw_q.strip()}' ━━━")
    clean_q    = await cleaner_plugin.safe_execute(query=raw_q)
    rag_result = await rag_plugin.safe_execute(query=clean_q)
    validated  = await validator_plugin.safe_execute(result=rag_result)
    print(f"  [Cleaner]   : '{clean_q}'")
    print(f"  [RAG]       : sources={rag_result['num_sources']}, score={rag_result['top_score']:.3f}")
    print(f"  [Validator] : valid={validated['is_valid']}, words={validated['word_count']}, conf={validated['confidence']:.2f}")
    print()

for plugin in [cleaner_plugin, rag_plugin, validator_plugin]:
    s = plugin.get_stats()
    print(f"📊 {plugin.name}: executions={s['execution_stats']['total_executions']}, "
          f"success={s['execution_stats']['success_rate']}, avg={s['timing_stats']['average_time']}")

for p in [cleaner_plugin, rag_plugin, validator_plugin]:
    await p.cleanup()
