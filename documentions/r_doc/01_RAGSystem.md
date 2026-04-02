# 📘 RAGSystem — النظام الأساسي

## نظرة عامة

`RAGSystem` هو النظام الجوهري في المكتبة. يعمل كطبقة تنسيق (Orchestration Layer) نقية تربط كل المكونات معًا: قاعدة البيانات المتجهة، نموذج اللغة، المقطّع، ومدير السياق. كل هذه المكونات تُحقن من الخارج مما يجعل النظام مرنًا جدًا وقابلًا للتكوين.

---

## التثبيت والاستيراد

```python
from rag.core import RAGSystem, RAGConfig
```

---

## الإعدادات — `RAGConfig`

```python
config = RAGConfig(
    top_k=5,                      # عدد القطع المسترجعة
    min_score=0.0,                # الحد الأدنى للدرجة
    prompt_language="ar",         # لغة الـ prompt ('ar' أو 'en')
    enable_reranking=False,       # تفعيل إعادة الترتيب
    enable_prompt_routing=False,  # تفعيل توجيه الـ prompt
)
```

---

## الدوال الرئيسية

### `__init__`

```python
RAGSystem(
    vector_db,
    llm,
    chunker,
    context_manager,
    config=None
)
```

**الوصف:** تهيئة نظام RAG الأساسي.

| المعامل | النوع | الوصف |
|---|---|---|
| `vector_db` | Any | قاعدة بيانات متجهة تحتوي على: `add`, `search`, `remove_by_doc_id`, `save`, `load` |
| `llm` | Any | نموذج اللغة يحتوي على: `generate` |
| `chunker` | Any | مقطّع النصوص يحتوي على: `chunk_text` أو `chunk` |
| `context_manager` | Any | مدير السياق يحتوي على: `build` |
| `config` | RAGConfig | إعدادات النظام (اختياري) |

---

### `add_documents`

```python
add_documents(docs: Dict[str, str]) -> Dict[str, int]
```

**الوصف:** إضافة مستندات إلى النظام، يقوم بتقطيعها وإضافتها لقاعدة البيانات.

| المعامل | النوع | الوصف |
|---|---|---|
| `docs` | `Dict[str, str]` | قاموس من `{doc_id: نص_المستند}` |

**Return:** `Dict[str, int]` — قاموس `{doc_id: عدد_القطع}`

**مثال:**
```python
results = rag.add_documents({
    "doc1": "الذكاء الاصطناعي هو محاكاة للذكاء البشري...",
    "doc2": "تعلم الآلة هو فرع من الذكاء الاصطناعي...",
})
print(results)  # {'doc1': 3, 'doc2': 2}
```

---

### `retrieve`

```python
retrieve(query: str, top_k: Optional[int] = None) -> List[Tuple[Any, float]]
```

**الوصف:** استرجاع القطع الأكثر صلة بالاستعلام من قاعدة البيانات، مع دعم إعادة الترتيب تلقائيًا إن كانت مفعّلة.

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | استعلام المستخدم |
| `top_k` | `int` | تجاوز العدد الافتراضي للنتائج (اختياري) |

**Return:** `List[Tuple[chunk, score]]`

**مثال:**
```python
results = rag.retrieve("ما هو الذكاء الاصطناعي؟")
for chunk, score in results:
    print(f"Score: {score:.2f} | {chunk.text[:100]}")
```

---

### `generate`

```python
generate(
    query: str,
    include_sources: bool = False,
    language: Optional[str] = None,
    **llm_kwargs
) -> str
```

**الوصف:** توليد إجابة كاملة للاستعلام (استرجاع + بناء سياق + توليد).

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | استعلام المستخدم |
| `include_sources` | `bool` | إضافة المصادر للإجابة |
| `language` | `str` | `'ar'` أو `'en'`، يُكشف تلقائيًا إن لم يُحدَّد |
| `**llm_kwargs` | `Any` | معاملات إضافية لنموذج اللغة |

**يُرجع:** `str` — نص الإجابة

**مثال:**
```python
answer = rag.generate("ما هو الذكاء الاصطناعي؟", include_sources=True)
print(answer)
```

---

### `remove_document`

```python
remove_document(doc_id: str) -> int
```

**الوصف:** حذف مستند بالكامل من النظام.

| المعامل | النوع | الوصف |
|---|---|---|
| `doc_id` | `str` | معرّف المستند |

**يُرجع:** `int` — عدد القطع المحذوفة

---

### `save` / `load`

```python
save(path: str) -> None
load(path, vector_db, llm, chunker, context_manager, config=None) -> RAGSystem
```

**الوصف:** حفظ وتحميل النظام من القرص.

---

### `get_stats`

```python
get_stats() -> Dict[str, Any]
```

**الوصف:** الحصول على إحصائيات النظام.

**Return:**
```python
{
    "total_documents": 10,
    "total_chunks": 45,
    "total_queries": 100,
    "successful_queries": 98,
    "failed_queries": 2,
    "vector_db_size": 45,
    "llm_available": True,
    "chunker_type": "TextSplitter"
}
```

---

### `cleanup`

```python
cleanup() -> None
```

**الوصف:** تنظيف الموارد وإغلاق الاتصالات.

---

## الواجهة غير المتزامنة (Async API)

| الدالة | الوصف |
|---|---|
| `aadd_documents(docs)` | إضافة مستندات بشكل غير متزامن (متوازٍ) |
| `aretrieve(query, top_k)` | استرجاع غير متزامن |
| `agenerate(query, ...)` | توليد غير متزامن |
| `astream(query, ...)` | بث الإجابة رمزًا بعد رمز |

---

## مثال عملي كامل

```python
from rag.core import RAGSystem, RAGConfig
from vector_database import FAISSVectorDatabase
from embeddings import OpenAIEmbedder
from llm import OpenAIInterface
from chunks import TextSplitter
from context import Conte
# --- 1. إعداد المكونات ---
embedder = OpenAIEmbedder(api_key="sk-...")
vector_db = FAISSVectorDatabase(embedder=embedder)
llm = OpenAIInterface(api_key="sk-...")
chunker = TextSplitter(chunk_size=500, overlap=50)
ctx_manager = ContextManager()

# --- 2. إنشاء النظام ---
config = RAGConfig(top_k=5, prompt_language="ar")
rag = RAGSystem(
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
    config=config,
)

# --- 3. إضافة المستندات ---
docs = {
    "ai_intro": """
        الذكاء الاصطناعي هو مجال علوم الحاسوب الذي يهدف إلى بناء أنظمة
        قادرة على أداء مهام تتطلب عادةً ذكاءً بشريًا، مثل التعلم والاستدلال
        وحل المشكلات والفهم اللغوي.
    """,
    "ml_intro": """
        تعلم الآلة هو فرع من الذكاء الاصطناعي يتيح للأنظمة التعلم التلقائي
        من البيانات وتحسين أدائها دون برمجة صريحة.
    """,
}
results = rag.add_documents(docs)
print(f"تم إضافة: {results}")

# --- 4. الاستعلام ---
answer = rag.generate(
    "ما الفرق بين الذكاء الاصطناعي وتعلم الآلة؟",
    include_sources=True,
    language="ar",
)
print(answer)

# --- 5. الإحصائيات ---
print(rag.get_stats())

# --- 6. الحفظ والتحميل ---
rag.save("./my_rag_system")
rag_loaded = RAGSystem.load(
    "./my_rag_system",
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
)

# --- 7. استخدام context manager ---
with RAGSystem(vector_db, llm, chunker, ctx_manager) as rag:
    rag.add_documents({"doc": "محتوى..."})
    print(rag.generate("سؤال؟"))
# يتم تنظيف الموارد تلقائيًا

# --- 8. الاستخدام غير المتزامن ---
import asyncio

async def async_example():
    await rag.aadd_documents({"doc": "محتوى..."})
    answer = await rag.agenerate("ما هو الذكاء الاصطناعي؟")
    print(answer)

    # بث الإجابة
    async for token in rag.astream("اشرح تعلم الآلة"):
        print(token, end="", flush=True)

asyncio.run(async_example())
```
