# 📡 StreamingRAG — توثيق تقني شامل



## نظرة عامة

`StreamingRAG` هو نظام RAG (Retrieval-Augmented Generation) يدعم **البث المباشر** للإجابات رمزاً بعد رمز على غرار ChatGPT. يُصدر أحداثاً مكتوبة (`StreamEvent`) تُتيح تتبع كل مرحلة من مراحل الاسترجاع والتوليد.

**المكتبات المطلوبة (stdlib فقط):** `asyncio`, `threading`, `queue`, `time`, `logging`, `inspect`

---


## `EventType` — أنواع الأحداث

```python
from enum import Enum

class EventType(str, Enum):
    RETRIEVAL_START  = "retrieval_start"   # بدأ الاسترجاع
    RETRIEVAL_DONE   = "retrieval_done"    # انتهى الاسترجاع
    GENERATION_START = "generation_start"  # بدأ التوليد
    GENERATION_DONE  = "generation_done"   # انتهى التوليد
    CHUNK            = "chunk"             # قطعة نص من الإجابة
    ERROR            = "error"             # خطأ في أي مرحلة
```

> `EventType` يرث من `str` — يمكن مقارنته مباشرةً بالسلاسل النصية.

---

## `StreamEvent` — كائن الحدث

```python
@dataclass(frozen=True)
class StreamEvent:
    type:    EventType
    data:    Any      = None   # نص للـ CHUNK، dict للباقي
    latency: float    = 0.0    # الثواني منذ بدء البث
```

**`frozen=True`** — الكائن غير قابل للتعديل بعد الإنشاء.

### حقل `data` حسب نوع الحدث

| `type` | محتوى `data` |
|---|---|
| `RETRIEVAL_START` | `{"query": str}` |
| `RETRIEVAL_DONE` | `{"num_docs": int, "docs": list}` |
| `GENERATION_START` | `{"prompt_chars": int}` |
| `CHUNK` | `str` — القطعة النصية مباشرةً |
| `GENERATION_DONE` | `{"total_latency": float}` |
| `ERROR` | `{"msg": str, "stage": "retrieval" | "generation"}` |

### الخاصية `is_chunk`

```python
@property
def is_chunk(self) -> bool:
    return self.type is EventType.CHUNK
```

### `__str__`

```python
def __str__(self) -> str:
    return self.data if self.is_chunk else ""
```

يُتيح استخدام `str(event)` مباشرةً في الطباعة — يُرجع النص للـ CHUNK وسلسلة فارغة لغيره.

---

## `StreamConfig` — الإعدادات

```python
@dataclass
class StreamConfig:
    chunk_size:          int   = 10     # عدد الكلمات في كل chunk (للمحاكاة فقط)
    sim_delay:           float = 0.04   # ثواني بين chunks المحاكاة
    max_context_docs:    int   = 5      # أقصى عدد مستندات في السياق
    max_doc_chars:       int   = 500    # أقصى أحرف لكل مستند
    emit_metadata:       bool  = True   # إصدار أحداث غير CHUNK (غير مُطبَّق داخلياً حالياً)
    retrieval_timeout:   float = 10.0   # مهلة مرحلة الاسترجاع بالثواني
    generation_timeout:  float = 60.0   # مهلة مرحلة التوليد بالثواني
    prompt_template:     str   = ...    # قالب البرومبت (يحتوي {context} و {query})
```

### قالب البرومبت الافتراضي

```
You are a precise RAG assistant.

Strict rules:
- Use ONLY the provided context.
- Do NOT guess.
- If missing info, say: 'لا توجد معلومات كافية في السياق'.
- The answer MUST be in the SAME language as the question.
- NEVER switch language.

Context:
{context}

Question: {query}

Final Answer:
```

> **ملاحظة:** القالب يدعم متغيّرَين فقط: `{context}` و `{query}`.

---

## البروتوكولات — `protocols.py`

جميع البروتوكولات مُعلَّمة بـ `@runtime_checkable` — يمكن استخدام `isinstance()` معها.

```python
class Retrievable(Protocol):
    def retrieve(self, query: str) -> Any: ...

class Queryable(Protocol):
    def query(self, query: str, context: Optional[Dict] = None) -> Any: ...

class SyncStreamableLLM(Protocol):
    def stream(self, prompt: str) -> Iterator[str]: ...

class AsyncStreamableLLM(Protocol):
    async def astream(self, prompt: str) -> AsyncIterator[str]: ...
```

يستخدم `StreamingRAG` هذه البروتوكولات لاكتشاف قدرات الـ LLM تلقائياً واختيار استراتيجية التوليد المناسبة.

---

## `StreamingRAG` — الفئة الرئيسية

### الباني `__init__`

```python
def __init__(
    self,
    rag_system: Any,
    llm:        Any                          = None,
    config:     Optional[StreamConfig]       = None,
    *,
    chunk_size: Optional[int]                = None,
    on_chunk:   Optional[Callable[[str], None]]          = None,
    on_event:   Optional[Callable[[StreamEvent], None]]  = None,
)
```

| المعامل | الوصف |
|---|---|
| `rag_system` | أي كائن يمتلك `retrieve()` و/أو `generate()` |
| `llm` | كائن LLM يدعم `stream()` أو `astream()` — يُستنتج من `rag_system.llm` إن لم يُحدَّد |
| `config` | `StreamConfig` — **يُنسَخ** داخلياً لتجنب التعديل على النسخة المشتركة |
| `chunk_size` | اختصار لتعديل `config.chunk_size` — يُطبَّق بعد النسخ |
| `on_chunk` | callback يُستدعى لكل قطعة نص (`str`) فور إنتاجها |
| `on_event` | callback يُستدعى لكل حدث (`StreamEvent`) بما فيها غير CHUNK |

> **تنبيه:** `config` يُنسَخ بـ `copy.copy()` — أي تعديل على الـ config الأصلي لا يؤثر على النسخة الداخلية.

---

## الدوال العامة

### `stream` — بث متزامن (نص فقط)

```python
def stream(self, query: str, context: Optional[Dict] = None) -> Iterator[str]
```

مُولّد متزامن يُصدر النص المُولَّد قطعةً قطعة. الأحداث الوصفية تُستهلَك داخلياً (الـ callbacks تُنفَّذ لكنها لا تظهر للمستدعي).

```python
for token in rag.stream("ما هي النجوم؟"):
    print(token, end="", flush=True)
```

---

### `stream_events` — بث متزامن (بالأحداث)

```python
def stream_events(self, query: str, context: Optional[Dict] = None) -> Iterator[StreamEvent]
```

مُولّد متزامن يُصدر `StreamEvent`. يُشغِّل حلقة `asyncio` في **خيط منفصل** ويُمرِّر الأحداث عبر `stdlib.queue.Queue` (thread-safe).

```python
for event in rag.stream_events("اشرح الفضاء"):
    if event.type == EventType.RETRIEVAL_DONE:
        print(f"استُرجع {event.data['num_docs']} مستندات في {event.latency:.2f}s")
    elif event.is_chunk:
        print(event.data, end="", flush=True)
    elif event.type == EventType.ERROR:
        print(f"\nخطأ: {event.data['msg']} في مرحلة: {event.data['stage']}")
```

> **سبب استخدام `stdlib.queue.Queue` وليس `asyncio.Queue`:**  
> `asyncio.Queue` ليست thread-safe — استخدامها من الخيط الرئيسي بينما تعمل حلقة الأحداث في خيط آخر يُسبِّب data race وقد يُعطِّل البرنامج في Python 3.10+.

---

### `query` — استعلام كامل (بدون بث)

```python
def query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]
```

يجمع كل الأحداث ويُرجع:

```python
{
    "answer": str,            # الإجابة الكاملة مُجمَّعة
    "events": List[StreamEvent]  # جميع الأحداث بالترتيب
}
```

---

### `astream` — بث غير متزامن (نص فقط)

```python
async def astream(self, query: str, context: Optional[Dict] = None) -> AsyncIterator[str]
```

```python
async for token in rag.astream("ما هي المجرات؟"):
    print(token, end="", flush=True)
```

---

### `astream_events` — بث غير متزامن (بالأحداث) ⭐

```python
async def astream_events(self, query: str, context: Optional[Dict] = None) -> AsyncIterator[StreamEvent]
```

**هذه هي الدالة الجوهرية** — جميع الدوال الأخرى تُفوِّض إليها.

تنفِّذ ثلاث مراحل:
1. **الاسترجاع** (`_retrieve`) مع timeout
2. **بناء البرومبت** (`_build_context`)
3. **التوليد** (`_generate`) مع sliding deadline

```python
async for event in rag.astream_events("اشرح النجوم"):
    match event.type:
        case EventType.RETRIEVAL_DONE:
            print(f"[{event.data['num_docs']} مستندات - {event.latency:.2f}s]")
        case EventType.CHUNK:
            print(event.data, end="", flush=True)
        case EventType.GENERATION_DONE:
            print(f"\n[انتهى في {event.data['total_latency']:.2f}s]")
        case EventType.ERROR:
            print(f"\n[خطأ: {event.data['msg']}]")
```

---

### `_sync_get` — **مهجورة** ⚠️

```python
def _sync_get(self, queue: Any) -> Optional[StreamEvent]:
    raise NotImplementedError("_sync_get is deprecated; ...")
```

Return `NotImplementedError` فوراً إن استُدعيت. موجودة فقط للتوافق مع الفئات الفرعية التي قد تُعيد تعريفها.

---

## استراتيجيات التوليد (الاختيار التلقائي)

الدالة `_generate` تختار استراتيجية من ثلاث تلقائياً:

```
AsyncStreamableLLM متاح؟
    ✅ → Strategy 1: astream() مباشرةً (الأفضل)
    ❌ ↓
SyncStreamableLLM متاح؟
    ✅ → Strategy 2: stream() في Executor + asyncio.Queue
    ❌ ↓
Strategy 3: rag_system.generate() + محاكاة الكلمات
```

### Strategy 1 — Native Async
```python
async for chunk in self.llm.astream(prompt):
    yield chunk
```

### Strategy 2 — Sync في Thread
- يُشغِّل `llm.stream(prompt)` في خيط منفصل
- يُمرِّر الـ chunks عبر `asyncio.Queue`
- الأخطاء في الخيط تُلتقَط وتُعاد رفعها في الـ async side
- يُرسَل sentinel واحد فقط في `finally` (ليس اثنين)

### Strategy 3 — Simulation
- يُنفِّذ `rag_system.generate(query, context)` في executor
- يُقسِّم الناتج إلى مجموعات من الكلمات بحجم `chunk_size`
- ينتظر `sim_delay` ثانية بين كل مجموعة
- يتطلب وجود `rag_system.generate()` وإلا يرفع `AttributeError` مع رسالة واضحة

---

## الدوال الداخلية

### `_retrieve`

```python
async def _retrieve(self, query: str) -> List[Dict]
```

تكتشف تلقائياً إذا كانت `rag_system.retrieve()` sync أو async:
- **async:** تستدعيها مباشرةً بـ `await`
- **sync:** تُشغِّلها في `loop.run_in_executor(None, ...)`

الناتج المُطبَّع:
- `dict` → يأخذ `results` key
- `list` → يُعيدها كما هي
- غير ذلك → قائمة فارغة

---

### `_build_context`

```python
def _build_context(self, docs: List[Dict]) -> str
```

يأخذ أول `max_context_docs` مستندات، يقتطع كل منها إلى `max_doc_chars` حرف، ويُنسِّقها:

```
[source_id]
نص المستند...

[source_id]
نص المستند...
```

يبحث في المستند عن المفاتيح بالترتيب: `text` → `content` → `str(doc)`  
ويبحث عن المصدر بالترتيب: `source` → `id` → `doc-{i}`

---

## خاصية `stats`

```python
@property
def stats(self) -> Dict[str, Any]
```

```python
{
    "total_streams":        int,    # عدد عمليات البث الكاملة
    "total_chunks":         int,    # إجمالي الـ chunks المُنتَجة
    "total_errors":         int,    # عدد الأخطاء
    "avg_stream_latency_s": float,  # متوسط زمن البث بالثواني
}
```

---

## `__repr__`

```python
StreamingRAG(llm=async, chunk_size=10)
StreamingRAG(llm=sync,  chunk_size=5)
StreamingRAG(llm=sim,   chunk_size=10)  # لا يوجد LLM — محاكاة
```

---

## مثال عملي شامل

```python
from llm import MistralInterface
from embeddings import MistralEmbedder
from chunks import MultilanguageTextChunker
from rag.core import RAGSystem
from vector_database import FAISSVectorDatabase
from context import ContextManager
import asyncio
import logging
import nest_asyncio
nest_asyncio.apply()
llm=MistralInterface(api_key=api)
embedder=MistralEmbedder(api_key=api)
chunker=MultilanguageTextChunker(chunk_size=200,overlap=50)
vd=FAISSVectorDatabase(embedder=embedder)
context=ContextManager()

rag_base=RAGSystem(vector_db=vd,
                   chunker=chunker,
                   llm=llm,
                   context_manager=context)
rag_base.add_documents({
    "guide": """
        دليل الشركة: تأسست شركتنا عام 2020 وتعمل في مجال التقنية.
        ساعات العمل من 9 صباحًا حتى 5 مساءً. العطل الرسمية يوم الجمعة.
    """,
    "products": """
        منتجاتنا: نظام إدارة المشاريع، منصة التحليلات، أدوات الذكاء الاصطناعي.
        الأسعار تبدأ من 99 دولارًا شهريًا مع تجربة مجانية 30 يومًا.
    """,
    "support": """
        للدعم التقني: support@company.com أو الاتصال على 800-1234.
        الدعم متاح 24 ساعة للعملاء بالباقة المتميزة.
    """,
})


from rag.streaming_rag import StreamingRAG, StreamConfig, EventType

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# الإعداد
# ─────────────────────────────────────────────
config = StreamConfig(
    chunk_size=3,
    sim_delay=0.05,
    retrieval_timeout=15.0,
    generation_timeout=90.0,
    max_context_docs=5,
    max_doc_chars=800,
)

# ✅ on_chunk للجانب الخفي فقط (WebSocket, DB, logging ...)
#    لا تطبع هنا إذا كنت ستطبع في الـ loop أيضاً
def on_chunk_side_effect(token: str):
    # مثال: إرسال عبر WebSocket
    # websocket.send(token)
    pass  # ← لا طباعة هنا

def on_event_side_effect(event):
    if event.type == EventType.ERROR:
        logger.error("خطأ في %s: %s", event.data["stage"], event.data["msg"])

rag = StreamingRAG(
    rag_system=rag_base,
    llm=llm,
    config=config,
    on_chunk=on_chunk_side_effect,   # جانب خفي فقط
    on_event=on_event_side_effect,
)

# ─────────────────────────────────────────────
# 1. بث متزامن — نص فقط
#    الطباعة هنا فقط، on_chunk لا يطبع
# ─────────────────────────────────────────────
print("=== بث متزامن ===")
for token in rag.stream("ما هي منتجاتكم"):
    print(token, end="", flush=True)   # ← مكان الطباعة الوحيد
print()

# ─────────────────────────────────────────────
# 2. استعلام كامل — بدون بث
# ─────────────────────────────────────────────
print("\n=== استعلام كامل ===")
result = rag.query("ما هي منتجاتكم")
print(result["answer"])
print(f"عدد الأحداث: {len(result['events'])}")

# ─────────────────────────────────────────────
# 3. بث غير متزامن — بالأحداث
# ─────────────────────────────────────────────
async def main():
    print("\n=== بث غير متزامن ===")
    async for event in rag.astream_events("ما هي منتجاتكم"):
        if event.type == EventType.RETRIEVAL_DONE:
            print(f"\n[استُرجع {event.data['num_docs']} مستندات]")
        elif event.is_chunk:
            print(event.data, end="", flush=True)   # ← مكان الطباعة الوحيد
        elif event.type == EventType.GENERATION_DONE:
            print(f"\n[اكتمل في {event.data['total_latency']:.2f}s]")
        elif event.type == EventType.ERROR:
            print(f"\n[خطأ في {event.data['stage']}: {event.data['msg']}]")

asyncio.run(main())

# ─────────────────────────────────────────────
# 4. الإحصائيات
# ─────────────────────────────────────────────
print(f"\n📊 {rag.stats}")
print(repr(rag))


# ═════════════════════════════════════════════
# بديل: استخدام on_chunk للطباعة فقط — بدون for loop
# ═════════════════════════════════════════════

def on_chunk_print(token: str):
    print(token, end="", flush=True)   # الطباعة هنا

rag_print = StreamingRAG(
    rag_system=rag_base,
    llm=llm,
    config=config,
    on_chunk=on_chunk_print,  # ← يتولى الطباعة
)

print("\n=== بث عبر on_chunk فقط ===")
# استهلك الـ generator لتشغيل الـ callbacks لكن لا تطبع شيئاً
for _ in rag_print.stream("ما هي منتجاتكم"):
    pass   # ← لا طباعة هنا، on_chunk يتولى الأمر
print()
```

