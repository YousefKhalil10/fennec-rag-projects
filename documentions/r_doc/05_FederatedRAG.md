# 🌐 FederatedRAG — نظام RAG الموزّع

## نظرة عامة

`FederatedRAG` يُمكّنك من ربط **مصادر RAG متعددة** والاستعلام عنها في آنٍ واحد بشكل متوازٍ، ثم تجميع نتائجها باستخدام إحدى استراتيجيات التجميع. مفيد عندما تكون بياناتك موزّعة على قواعد بيانات مختلفة أو أنظمة منفصلة.

يتضمن أيضًا:
- **Circuit Breaker** لحماية المصادر الفاشلة تلقائياً
- **كاش TTL** آمن للـ multi-threading
- **Timeout** مستقل لكل مصدر
- **Streaming** متزامن وغير متزامن

---

## التثبيت والاستيراد

```python
from rag.federated_rag import FederatedRAG
from rag.federated_rag import AggregationMethod, StreamChunk
```

---

## المكونات الرئيسية

| المكوّن | النوع | الدور |
|---|---|---|
| `FederatedRAG` | class | المنسّق الرئيسي |
| `AggregationMethod` | Enum | استراتيجية تجميع النتائج |
| `StreamChunk` | dataclass | وحدة البث (chunk) |
| `FederatedSource` | dataclass | تمثيل مصدر مسجَّل (داخلي) |
| `CircuitBreaker` | dataclass | حماية المصادر الفاشلة |
| `TTLCache` | class | كاش ذكي بصلاحية زمنية |

---

## استراتيجيات التجميع — `AggregationMethod`

| الاستراتيجية | الوصف | سلوك الـ Streaming |
|---|---|---|
| `WEIGHTED` | إجابة المصدر ذي الوزن الأعلى | يبث من أعلى مصدر وزناً ينجح |
| `VOTING` | التصويت بالأغلبية | يجمع كل الإجابات أولاً ثم يبث chunk واحد |
| `RANKING` | ترتيب بـ `score × weight` | يسابق المصادر ثم يبث من الفائز |
| `SIMPLE` | أول مصدر ناجح | يبث من أول مصدر ينجح |
| `MERGE` | دمج كل الإجابات في نص واحد | يبث المصادر بالتسلسل مع prefix لكل مصدر |

---

## `StreamChunk`

وحدة البيانات التي تُرجعها دوال `stream()` و`astream()`.

```python
@dataclass
class StreamChunk:
    text:     str                        # جزء النص الوارد (فارغ في sentinel الختام)
    source:   str                        # اسم المصدر المُنتِج
    done:     bool = False               # True في آخر chunk لهذا المصدر
    metadata: Optional[Dict] = None      # score، latency_ms، weight ...
    error:    Optional[str]  = None      # رسالة الخطأ إن وُجد
```

**ملاحظات:**
- `str(chunk)` يُرجع `chunk.text` مباشرة — مناسب للطباعة.
- Chunks التي `done=True` و`text=""` هي sentinels (إشارة انتهاء) — لا تطبعها.
- إذا `error` ليس `None`، فشل المصدر في هذا الـ chunk.

**مثال على قراءة الـ metadata:**
```python
async for chunk in fed.astream("سؤال؟"):
    if chunk.done:
        latency = (chunk.metadata or {}).get("latency_ms")
        print(f"\n[{chunk.source}] انتهى في {latency}ms")
    elif not chunk.error:
        print(chunk.text, end="", flush=True)
```

---

## `FederatedRAG`

### `__init__`

```python
FederatedRAG(
    aggregation_method  = AggregationMethod.WEIGHTED,
    min_sources         = 1,
    cache_ttl           = 60.0,
    cache_max_size      = 256,
    stream_race_timeout = 2.0,
    pre_query_hook      = None,
    post_query_hook     = None,
)
```

| المعامل | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `aggregation_method` | `AggregationMethod` | `WEIGHTED` | استراتيجية تجميع النتائج |
| `min_sources` | `int` | `1` | الحد الأدنى للمصادر النشطة لقبول الاستعلام |
| `cache_ttl` | `float` | `60.0` | مدة صلاحية الكاش بالثواني |
| `cache_max_size` | `int` | `256` | أقصى عدد مدخلات في الكاش |
| `stream_race_timeout` | `float` | `2.0` | ثواني الانتظار في وضع `RANKING` لجمع أول chunk من كل مصدر قبل اختيار الفائز |
| `pre_query_hook` | `Callable[[str, Optional[Dict]], None]` | `None` | دالة تُستدعى قبل كل استعلام |
| `post_query_hook` | `Callable[[Dict], None]` | `None` | دالة تُستدعى بعد كل استعلام ناجح |

---

### إدارة المصادر

#### `add_source`

```python
add_source(
    name:       str,
    rag_system: Any,
    weight:     float = 1.0,
    timeout:    float = 10.0,
    metadata:   Optional[Dict] = None,
) -> FederatedRAG
```

تسجيل مصدر RAG جديد. يُرجع `self` للـ method chaining.

| المعامل | النوع | الوصف |
|---|---|---|
| `name` | `str` | معرّف فريد للمصدر |
| `rag_system` | `Any` | كائن يملك `generate()` وإن كان يدعم البث فـ `stream()` أو `astream()` |
| `weight` | `float` | وزن المصدر في التجميع — يجب أن يكون > 0 |
| `timeout` | `float` | أقصى وقت انتظار للمصدر بالثواني |
| `metadata` | `Dict` | بيانات وصفية حرة تُخزَّن مع المصدر |

**Backend streaming detection:** النظام يبحث تلقائياً عن `stream()` أو `astream()` أو `generate_stream()` في الـ `rag_system`. إن لم يجد أياً منها، يستدعي `generate()` ويبثّ الإجابة على شكل fragments صغيرة.

---

#### `remove_source`

```python
remove_source(name: str) -> None
```

إزالة مصدر نهائياً. يرفع `KeyError` إن لم يُوجد الاسم.

---

#### `enable_source`

```python
enable_source(name: str, enabled: bool = True) -> None
```

تفعيل أو تعطيل مصدر دون إزالته. المصدر المعطَّل لا يُستدعى في الاستعلامات.

```python
fed.enable_source("wiki", enabled=False)   # تعطيل
fed.enable_source("wiki", enabled=True)    # إعادة تفعيل
```

---

### الاستعلام المُجمَّع (Buffered)

#### `query`

```python
query(query: str, context: Optional[Dict] = None, top_k: int = 5) -> Dict[str, Any]
```

استعلام متزامن — آمن داخل وخارج event loop قائم (Jupyter، FastAPI، إلخ).

| المعامل | الوصف |
|---|---|
| `query` | نص السؤال |
| `context` | سياق إضافي يُمرَّر للمصادر التي تدعمه |
| `top_k` | عدد النتائج المطلوبة من كل مصدر (إن كان يدعمه) |

**الإجابة:**
```python
{
    "answer":             "الإجابة المجمّعة",
    "sources_used":       ["docs", "wiki"],
    "num_sources":        2,
    "aggregation_method": "weighted",
    "cached":             False,
    "primary_source":     "docs",       # في WEIGHTED / RANKING / SIMPLE
    "all_results":        [...],         # نتائج كل مصدر كاملة
    "ranked_results":     [...],         # في RANKING فقط
    "vote_counts":        {...},         # في VOTING فقط
}
```

**حالة الخطأ:**
```python
{
    "answer":      "رسالة الخطأ",
    "error":       "insufficient_sources" | "all_sources_failed",
    "sources_used": [],
    "num_sources":  0,
}
```

---

#### `query_async`

```python
await fed.query_async(query: str, context=None, top_k: int = 5) -> Dict[str, Any]
```

النسخة الأصلية غير المتزامنة من `query`. تُرجع نفس البنية تماماً.

---

#### `aquery`

```python
await fed.aquery(query: str, context=None, top_k: int = 5) -> Dict[str, Any]
```

اسم بديل لـ `query_async` متوافق مع اصطلاح تسمية المكتبات (`a` prefix).

---

### الاستعلام بالبث (Streaming)

#### `stream` — بث متزامن

```python
stream(query: str, context: Optional[Dict] = None, top_k: int = 5) -> Generator[StreamChunk, None, None]
```

يُنتج `StreamChunk` objects بالتسلسل. يعمل داخل وخارج event loop قائم.

```python
for chunk in fed.stream("اشرح الذكاء الاصطناعي"):
    if not chunk.done and not chunk.error:
        print(chunk.text, end="", flush=True)
```

---

#### `astream` — بث غير متزامن

```python
async def astream(query: str, context: Optional[Dict] = None, top_k: int = 5) -> AsyncGenerator[StreamChunk, None]
```

يُنتج `StreamChunk` objects فور وصولها. الأسرع والأنسب داخل `async` context.

```python
async for chunk in fed.astream("اشرح الذكاء الاصطناعي"):
    if not chunk.done and not chunk.error:
        print(chunk.text, end="", flush=True)
```

**سلوك كل استراتيجية عند البث:**

| الاستراتيجية | السلوك |
|---|---|
| `WEIGHTED` / `SIMPLE` | يجرّب المصادر بترتيب الوزن — يبث من أول مصدر ينجح |
| `RANKING` | يسابق كل المصادر لـ `stream_race_timeout` ثانية — يبث من الأعلى `score × weight` |
| `MERGE` | يبث المصادر بالتسلسل (الأعلى وزناً أولاً) — يُضيف `[اسم_المصدر] ` كـ prefix |
| `VOTING` | يجمع الإجابات كاملةً أولاً ثم يرسل chunk واحداً |

**معالجة الأخطاء في البث:**
```python
async for chunk in fed.astream("سؤال؟"):
    if chunk.error:
        print(f"خطأ في {chunk.source}: {chunk.error}")
    elif chunk.done:
        pass   # sentinel — تجاهل
    else:
        print(chunk.text, end="", flush=True)
```

---

### الإحصائيات

#### `get_stats`

```python
get_stats() -> Dict[str, Dict]
```

إحصائيات لكل مصدر مسجَّل.

```python
{
    "docs_source": {
        "total_queries":  20,
        "total_errors":   1,
        "avg_latency_ms": 230.0,
        "error_rate":     0.05,
        "circuit_state":  "closed",   # closed | open | half_open
    },
    "wiki_source": { ... }
}
```

---

### Context Manager

يدعم `FederatedRAG` الاستخدام كـ async context manager:

```python
async with FederatedRAG() as fed:
    fed.add_source("docs", rag1)
    result = await fed.query_async("سؤال؟")
```

---

### Dunder Methods

| الدالة | الوصف | مثال |
|---|---|---|
| `__len__` | عدد المصادر المسجَّلة | `len(fed)` → `3` |
| `__repr__` | تمثيل نصي للكائن | `repr(fed)` → `FederatedRAG(sources=['docs', 'wiki'], ...)` |

---

## `CircuitBreaker`

يحمي كل مصدر من الاستدعاء المتكرر عند الفشل.

### انتقالات الحالة

```
CLOSED ──(3 فشل متتالي)──► OPEN ──(30 ثانية)──► HALF_OPEN
  ▲                                                    │
  └─────────────(نجاح)──────────────────────────────────┘
                                    │
                           (فشل) ──► OPEN
```

| الحالة | المعنى | الاستعلامات |
|---|---|---|
| `closed` | وضع طبيعي | تمر |
| `open` | المصدر فاشل | محجوبة |
| `half_open` | فترة تجربة | تمر (واحدة فقط) |

### المعاملات الافتراضية

| المعامل | القيمة | الوصف |
|---|---|---|
| `failure_threshold` | `3` | عدد الفشل المتتالي قبل فتح الدائرة |
| `recovery_timeout` | `30.0` ثانية | وقت الانتظار قبل الانتقال لـ `HALF_OPEN` |

تُخصَّص عبر `CircuitBreaker` مباشرة في `FederatedSource`:

```python
from rag.federated_rag import CircuitBreaker

cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
source = FederatedSource(name="docs", rag_system=rag1, circuit_breaker=cb)
```

> حالة الـ circuit لكل مصدر متاحة في `get_stats()` عبر حقل `"circuit_state"`.

---

## `TTLCache`

كاش داخلي آمن للـ multi-threading يُستخدم تلقائياً من `FederatedRAG`.

### السلوك
- المفتاح: SHA-256 لـ `(query + context)`.
- عند امتلاء الكاش يُحذف أقدم مدخل (LRU بسيط).
- آمن للاستخدام من threads متعددة.

### مسح الكاش يدوياً

```python
fed._cache.invalidate()   # يمسح جميع المدخلات فوراً
```

مفيد عند تحديث بيانات المصادر وتريد نتائج طازجة فوراً.

---

## مثال عملي كامل

```python
import asyncio
from rag.federated_rag import FederatedRAG
from rag.federated_rag.federat import AggregationMethod  # ✅ الاستيراد الصحيح
from chunks import MultilanguageTextChunker
from embeddings import MistralEmbedder
from llm import MistralInterface
from vector_database import FAISSVectorDatabase
from context import ContextManager
from rag.core import RAGSystem
import nest_asyncio



embedder    = MistralEmbedder(api_key=api)
llm         = MistralInterface(api_key=api)
    # chunk_size=300 يستوعب الجمل العربية الطويلة (max = 300 × 1.05 = 315 حرف)
chunker     = MultilanguageTextChunker(chunk_size=300, overlap=50)
ctx_manager = ContextManager()
 
    # ── مصدر 1: الوثائق التقنية ──────────────────────────────────────────────
vdb1     = FAISSVectorDatabase(embedder=embedder)
rag_tech = RAGSystem(vector_db=vdb1, llm=llm, chunker=chunker, context_manager=ctx_manager)
rag_tech.add_documents({
        "python": (
            "بايثون لغة برمجة عالية المستوى متعددة الاستخدامات، صُمِّمت لتكون سهلة القراءة والكتابة. "
            "تدعم البرمجة الإجرائية والكائنية والوظيفية. تُستخدم على نطاق واسع في علم البيانات، "
            "والذكاء الاصطناعي، وتطوير الويب، وأتمتة المهام. تتميز بمكتبة قياسية ضخمة ومجتمع "
            "نشط يوفر آلاف الحزم الجاهزة عبر PyPI."
        ),
        "ai": (
            "الذكاء الاصطناعي مجال من علوم الحاسوب يهدف إلى بناء أنظمة قادرة على أداء مهام "
            "تتطلب عادةً ذكاءً بشرياً. يشمل تعلم الآلة، والشبكات العصبية العميقة، ومعالجة اللغة "
            "الطبيعية، والرؤية الحاسوبية. تُستخدم تطبيقاته في التعرف على الصور والكلام، والترجمة "
            "الآلية، وأنظمة التوصية، والسيارات ذاتية القيادة."
        ),
        "deep_learning": (
            "التعلم العميق فرع من تعلم الآلة يعتمد على شبكات عصبية اصطناعية متعددة الطبقات. "
            "يتميز بقدرته على تعلم التمثيلات الهرمية للبيانات تلقائياً دون الحاجة لاستخراج "
            "الميزات يدوياً. يُستخدم في نماذج مثل CNN للصور، وRNN وTransformer للنصوص. "
            "يتطلب كميات كبيرة من البيانات وقدرة حوسبة عالية، غالباً باستخدام GPU أو TPU."
        ),
        "nlp": (
            "معالجة اللغة الطبيعية (NLP) فرع من الذكاء الاصطناعي يُعنى بتمكين الحاسوب من "
            "فهم اللغة البشرية وتوليدها. تشمل مهامها: تصنيف النصوص، واستخراج الكيانات، "
            "والترجمة، والإجابة على الأسئلة. ثورة الـ Transformer ونماذج BERT وGPT "
            "غيّرت هذا المجال جذرياً منذ عام 2017."
        ),
        "rag": (
            "الاسترجاع المعزَّز بالتوليد (RAG) تقنية تجمع بين نماذج اللغة الكبيرة وقواعد البيانات "
            "الخارجية. تعمل بخطوتين: استرجاع الوثائق ذات الصلة، ثم تغذيتها للنموذج لتوليد إجابة. "
            "تُقلّل من الهلوسة وتُحدِّث معرفة النموذج دون إعادة التدريب."
        ),
        "vector_db": (
            "قواعد البيانات المتجهة مخصصة لتخزين والبحث في التضمينات عالية الأبعاد بكفاءة. "
            "تعتمد على خوارزميات البحث التقريبي مثل HNSW وIVF. من أبرز الأمثلة: "
            "FAISS من Meta، وPinecone، وWeaviate. تُستخدم في RAG والبحث الدلالي."
        ),
    })
 
    # ── مصدر 2: ويكيبيديا ────────────────────────────────────────────────────
vdb2     = FAISSVectorDatabase(embedder=embedder)
rag_wiki = RAGSystem(vector_db=vdb2, llm=llm, chunker=chunker, context_manager=ctx_manager)
rag_wiki.add_documents({
        "wiki_ai_history": (
            "بدأت بحوث الذكاء الاصطناعي رسمياً في مؤتمر دارتموث عام 1956. "
            "مرّ المجال بفترتين من شتاء الذكاء الاصطناعي بسبب توقف التمويل. "
            "انتعش مجدداً مطلع الألفية الثالثة بفضل البيانات الضخمة والقدرة الحوسبية، "
            "ثم شهد طفرة مع ظهور نماذج اللغة الكبيرة."
        ),
        "wiki_ml": (
            "تعلم الآلة فرع من الذكاء الاصطناعي يُمكِّن الأنظمة من التعلم من البيانات. "
            "ينقسم إلى: التعلم الخاضع للإشراف على بيانات مُصنَّفة، والتعلم غير الخاضع "
            "للإشراف الذي يكتشف الأنماط تلقائياً، والتعلم المعزَّز من التفاعل مع البيئة."
        ),
        "wiki_transformer": (
            "معمارية Transformer قدّمها Google عام 2017 في ورقة Attention is All You Need. "
            "تعتمد على آلية الانتباه الذاتي لمعالجة التسلسلات بالتوازي. "
            "أصبحت الأساس لنماذج GPT وBERT وT5، وامتدت لمعالجة الصور والصوت."
        ),
        "wiki_llm": (
            "نماذج اللغة الكبيرة (LLMs) نماذج عصبية ضخمة تُدرَّب على نصوص هائلة. "
            "أبرز الأمثلة: GPT-4 من OpenAI، وClaude من Anthropic، وGemini من Google. "
            "تتميز بقدرتها على الفهم والتوليد والاستدلال."
        ),
        "wiki_embeddings": (
            "التضمينات تمثيلات رقمية متجهية للنصوص تُلتقط العلاقات الدلالية. "
            "الكيانات المتشابهة تكون قريبة في الفضاء المتجهي. "
            "تُنتَج بنماذج مثل Word2Vec وSentence-BERT، وتُعدّ أساس البحث الدلالي وRAG."
        ),
    })
 
    # ── مصدر 3: المعرفة الداخلية للشركة ──────────────────────────────────────
vdb3         = FAISSVectorDatabase(embedder=embedder)
rag_internal = RAGSystem(vector_db=vdb3, llm=llm, chunker=chunker, context_manager=ctx_manager)
rag_internal.add_documents({
        "company_overview": (
            "شركتنا TechAI Solutions تأسست عام 2020 وتتخصص في حلول الذكاء الاصطناعي. "
            "نخدم أكثر من 150 عميلاً في قطاعات المال والصحة والتجزئة. "
            "يضم فريقنا 80 موظفاً منهم 45 مهندساً وباحثاً."
        ),
        "company_products": (
            "نقدم ثلاثة منتجات: SmartSearch محرك بحث دلالي على RAG، "
            "وAutoReport لتوليد التقارير التلقائية، وChatAssist منصة chatbot "
            "تدعم العربية والإنجليزية. متاحة كـ SaaS أو on-premise."
        ),
        "company_tech_stack": (
            "نعتمد Python وFastAPI للخدمات الخلفية، وReact للواجهات. "
            "نستخدم FAISS وPinecone للمتجهات، وMistral وOpenAI كنماذج لغوية. "
            "البنية على AWS مع Kubernetes، والمراقبة عبر Prometheus وGrafana."
        ),
        "company_policy_ai": (
            "سياستنا تُلزم بمراجعة بشرية للمخرجات في القرارات الحساسة. "
            "نلتزم بمبادئ الذكاء الاصطناعي المسؤول: الشفافية والعدالة والتفسيرية. "
            "كل نموذج يجتاز تقييم المخاطر ومراجعة الخصوصية وفق GDPR."
        ),
        "company_clients": (
            "من عملائنا: بنك الخليج للتحليل الائتماني، ومجموعة صحة للتشخيص المساعد. "
            "حقق SmartSearch لدى بنك الخليج تخفيضاً 40% في وقت المعالجة "
            "وزيادة 35% في رضا العملاء خلال 6 أشهر."
        ),
    })
 

fed = FederatedRAG(
        aggregation_method  = AggregationMethod.WEIGHTED,
        min_sources         = 1,
        cache_ttl           = 120.0,
        stream_race_timeout = 3.0,
    )
fed.add_source("tech_docs", rag_tech,     weight=2.0, timeout=15.0) \
       .add_source("wikipedia", rag_wiki,     weight=1.0, timeout=10.0) \
       .add_source("internal",  rag_internal, weight=1.5, timeout=8.0)
 
print(f"عدد المصادر: {len(fed)}")
print(repr(fed))

# --- الاستعلام المتزامن ---
result = fed.query("ما هو الذكاء الاصطناعي؟", top_k=5)
print(result["answer"])
print(f"المصادر: {result['sources_used']} | كاش: {result['cached']}")


    # --- إدارة المصادر ---
# --- Context Manager ---

import nest_asyncio
nest_asyncio.apply()
async def main():
        # --- الاستعلام غير المتزامن ---
    result = await fed.query_async("ما هو الذكاء الاصطناعي؟")
    result = await fed.aquery("ما هو الذكاء الاصطناعي؟")
    print(result["answer"])
asyncio.run(main())

async with FederatedRAG(aggregation_method=AggregationMethod.MERGE) as fed2:
    fed2.add_source("tech", rag_tech).add_source("wiki", rag_wiki)
    async for chunk in fed2.astream("ما هو تعلم الآلة؟"):
        if not chunk.done and not chunk.error:
            print(chunk.text, end="", flush=True)

async for chunk in fed.astream("ما  هو تعلم الآلة؟", top_k=3):
    if chunk.error:
        print(f"\nخطأ [{chunk.source}]: {chunk.error}")
    elif chunk.done:
        latency = (chunk.metadata or {}).get("latency_ms", "?")
        print(f"\n✓ {chunk.source} ({latency}ms)")
    else:
        print(chunk.text, end="", flush=True)

async with FederatedRAG(aggregation_method=AggregationMethod.MERGE) as fed2:
    fed2.add_source("tech", rag_tech).add_source("wiki", rag_wiki)
    async for chunk in fed2.astream("ما هو تعلم الآلة؟"):
        if not chunk.done and not chunk.error:
            print(chunk.text, end="", flush=True)

fed.enable_source("wikipedia", enabled=False)
result = fed.query("ما هو تعلم الآلة")
print(f"بدون ويكيبيديا: {result['sources_used']}")
fed.enable_source("wikipedia", enabled=True)
 
fed.remove_source("tech_docs")
print(f"بعد الحذف: {len(fed)} مصادر")
 
# --- الإحصائيات ---
stats = fed.get_stats()
for name, s in stats.items():
    print(f"{name}: latency={s['avg_latency_ms']}ms | "
          f"errors={s['total_errors']} | circuit={s['circuit_state']}")
 
# --- مسح الكاش ---
fed._cache.invalidate()
 
# --- الـ Hooks ---
def before_query(query, ctx):
    print(f"استعلام: {query[:50]}")
 
def after_query(result):
    print(f"انتهى | {result['num_sources']} مصادر | كاش: {result['cached']}")
 
fed_hooked = FederatedRAG(pre_query_hook=before_query, post_query_hook=after_query)
fed_hooked.add_source("tech", rag_tech)
fed_hooked.query("ما هو تعلم الآلة")
```