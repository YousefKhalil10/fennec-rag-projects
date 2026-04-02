# Vector Database — توثيق المكتبة

## نظرة عامة

هذا المشروع يوفر **ثلاثة Wrappers جاهزة للإنتاج** لأشهر قواعد بيانات المتجهات، جميعها ترث من **`VectorDatabaseBase`** لضمان واجهة برمجية موحّدة تماماً. يمكنك التبديل بين المكتبات بدون تغيير أي كود في الـ RAGSystem.

### ما هي قاعدة بيانات المتجهات؟

قاعدة بيانات المتجهات تُخزِّن النصوص على شكل أرقام (Embeddings) وتسمح بالبحث عن النصوص الأقرب معنًى — مثلًا: البحث عن "الذكاء الاصطناعي" سيجلب نتائج عن "Machine Learning" و"Deep Learning" حتى لو لم تطابق الكلمات تمامًا.

---

## الـ Base Class المشترك: `VectorDatabaseBase`

> **جديد** — تمت إضافة هذا الـ class في آخر تحديث.

جميع الـ backends الثلاثة ترث من `VectorDatabaseBase`. هذا يضمن أن الـ RAGSystem يتعامل مع واجهة واحدة موحّدة بغض النظر عن الـ backend المستخدم.

```python
from vector_database import VectorDatabaseBase
```

### العقد الموحّد (Unified Contract)

| Method | Signature | الوصف |
|--------|-----------|-------|
| `add` | `(chunks, embeddings=None)` | إضافة `List[DocumentChunk]` |
| `search` | `(query, top_k, score_threshold, **kw)` | بحث — يُرجع دائماً `List[(DocumentChunk, float)]` |
| `remove_by_doc_id` | `(doc_id) -> int` | حذف مستند كامل — **اسم موحّد** |
| `get_stats` | `() -> Dict` | إحصائيات — **اسم موحّد** |
| `__len__` | `() -> int` | عدد المتجهات |

### الـ Helper المشترك: `sanitize_metadata`

> **جديد** — دالة مشتركة تُنظّف قيم الـ metadata تلقائياً قبل التخزين في أي backend.

```python
from vector_database import sanitize_metadata
```

تحوّل القيم غير المدعومة تلقائياً:

| نوع القيمة | النتيجة |
|---|---|
| `str`, `int`, `float`, `bool`, `None` | تُمرَّر كما هي |
| `list[str]` | تُمرَّر كما هي (صالحة لـ `$in` filtering) |
| `list` مختلطة مثل `['ar', 1]` | تُحوَّل لـ `"ar, 1"` |
| `dict` أو أي نوع آخر | تُحوَّل لـ JSON string |

---

## مقارنة بين المكتبات الثلاث

| الخاصية | ChromaDB | FAISS | Pinecone |
|---------|----------|-------|---------|
| **النوع** | محلي/سحابي | محلي فقط | سحابي فقط |
| **التثبيت** | `pip install chromadb` | `pip install faiss-cpu` | `pip install pinecone-client` |
| **API Key** | لا يحتاج | لا يحتاج | ✅ مطلوب |
| **التخزين الدائم** | ✅ مدعوم | ✅ مدعوم | ✅ تلقائي |
| **الحجم المناسب** | صغير-متوسط | أي حجم | كبير جداً |
| **السرعة** | جيدة | ممتازة | ممتازة |
| **Multi-tenancy** | ✅ (tenant_id) | ❌ | ✅ (namespace) |
| **Async** | ✅ | ✅ | ✅ |

---

## 1. ChromaVectorDatabase

### ما هو؟

Wrapper احترافي لـ **ChromaDB** — قاعدة بيانات مفتوحة المصدر مثالية للمشاريع المحلية والنماذج الأولية. تدعم التخزين الدائم على الديسك أو في الذاكرة فقط.

### التثبيت

```bash
pip install chromadb
```

---

### `__init__` — تهيئة قاعدة البيانات

```python
ChromaVectorDatabase(
    embedder=None,
    collection_name="default_collection",
    persist_directory=None,
    distance_metric="cosine",
    tenant_id=None,
    batch_size=500,
    strict_mode=True
)
```

| Parameter | النوع | الافتراضي | الوصف |
|-----------|------|----------|-------|
| `embedder` | `Any` | `None` | نموذج التضمين (مثل SentenceTransformer). يجب أن يحتوي على دالة `.encode()` |
| `collection_name` | `str` | `"default_collection"` | اسم المجموعة في ChromaDB |
| `persist_directory` | `str` | `None` | مسار لحفظ البيانات على الديسك. إذا كان `None` فالبيانات تُخزَّن في الذاكرة فقط |
| `distance_metric` | `str` | `"cosine"` | طريقة حساب التشابه: `"cosine"`, `"l2"`, `"ip"` |
| `tenant_id` | `str` | `None` | معرّف المستأجر للعزل في تطبيقات Multi-tenant |
| `batch_size` | `int` | `500` | عدد المتجهات التي تُعالَج دفعة واحدة |
| `strict_mode` | `bool` | `True` | تفعيل التحقق الصارم من صحة المدخلات |

**مثال:**

```python
from embeddings import OllamaEmbedder

embedder = OllamaEmbedder()

# قاعدة بيانات دائمة محفوظة على الديسك
db = ChromaVectorDatabase(
    embedder=embedder,
    collection_name="my_documents",
    persist_directory="./chroma_db",
    distance_metric="cosine"
)

# قاعدة بيانات مؤقتة في الذاكرة
db_memory = ChromaVectorDatabase(
    embedder=embedder,
    collection_name="temp_collection"
)
```

---

### `add` — إضافة وثائق ⚠️ تم التعديل

> **تغيير مهم:** الدالة الآن تقبل أسلوبين للاستدعاء.

**الأسلوب الموحّد (مستخدم مع RAGSystem — الموصى به):**

```python
db.add(chunks: List[DocumentChunk], embeddings: Optional[np.ndarray] = None)
```

**الأسلوب القديم (لا يزال يعمل للتوافق مع الكود القديم):**

```python
db.add(
    ids: List[str],
    documents: List[str],
    metadatas: List[Dict],
    embeddings: Optional[np.ndarray] = None
)
```

| Parameter | النوع | الوصف |
|-----------|------|-------|
| `chunks` | `List[DocumentChunk]` | قائمة بقطع المستندات **(الأسلوب الجديد)** |
| `ids` | `List[str]` | قائمة بمعرّفات فريدة **(الأسلوب القديم)** |
| `documents` | `List[str]` | قائمة بنصوص الوثائق **(الأسلوب القديم)** |
| `metadatas` | `List[Dict]` | قائمة بالبيانات الوصفية **(الأسلوب القديم)** |
| `embeddings` | `np.ndarray` | متجهات التضمين الجاهزة (اختياري في كلا الأسلوبين) |

**ملاحظة:** يتم تطبيق `sanitize_metadata()` تلقائياً على جميع الـ metadata قبل التخزين.

**مثال (الأسلوب الموحّد — مع RAGSystem):**

```python
from chunks import DocumentChunk

chunks = [
    DocumentChunk(chunk_id="c1", doc_id="doc1", text="الذكاء الاصطناعي يغير العالم", metadata={"category": "AI"}),
    DocumentChunk(chunk_id="c2", doc_id="doc1", text="تعلم الآلة تقنية مذهلة", metadata={"category": "ML"}),
]
db.add(chunks)
```

**مثال (الأسلوب القديم — للتوافق):**

```python
db.add(
    ids=["doc1", "doc2"],
    documents=["الذكاء الاصطناعي يغير العالم", "تعلم الآلة تقنية مذهلة"],
    metadatas=[{"category": "AI"}, {"category": "ML"}]
)
```

---

### `search` — البحث بالتشابه الدلالي ⚠️ تم التعديل

> **تغييران مهمان:**
> 1. نوع القيمة المُرجَعة أصبح `List[Tuple[DocumentChunk, float]]` بدلاً من `List[Tuple[str, float, Dict]]`
> 2. أضيف parameter جديد `score_threshold`

```python
results = db.search(
    query: Union[str, np.ndarray],
    top_k: int = 5,
    score_threshold: Optional[float] = None,   # ← جديد
    filters: Optional[Dict] = None
)
```

| Parameter | النوع | الافتراضي | الوصف |
|-----------|------|----------|-------|
| `query` | `str` أو `np.ndarray` | — | نص الاستعلام أو متجه التضمين مباشرة |
| `top_k` | `int` | `5` | عدد النتائج المطلوبة |
| `score_threshold` | `float` | `None` | **جديد** — الحد الأدنى لدرجة التشابه (نتائج بدرجة أقل تُستبعَد) |
| `filters` | `Dict` | `None` | فلترة حسب البيانات الوصفية، مثل `{"category": "AI"}` |

**Return:** `List[Tuple[DocumentChunk, float]]`
قائمة من `(DocumentChunk, درجة_التشابه)` مرتّبة تنازليًا.

> ⚠️ **تغيير في الـ Return Type:** الكود القديم كان يُفكِّك النتائج هكذا:
> ```python
> for document, score, metadata in results:  # ← القديم — لن يعمل
> ```
> الكود الجديد:
> ```python
> for chunk, score in results:  # ← الجديد
>     print(chunk.text)
>     print(chunk.metadata)
> ```

**مثال:**

```python
# بحث بسيط
results = db.search("ما هو تعلم الآلة؟", top_k=3)

for chunk, score in results:
    print(f"التشابه: {score:.3f}")
    print(f"النص: {chunk.text[:60]}...")
    print(f"الكاتب: {chunk.metadata.get('author')}")
    print("---")

# بحث مع حد أدنى للتشابه وفلترة
results = db.search(
    query="الذكاء الاصطناعي",
    top_k=5,
    score_threshold=0.7,
    filters={"category": "AI"}
)
```

---

### `delete_by_ids` — حذف بالمعرّف

```python
count = db.delete_by_ids(ids: List[str])
```

**مثال:**

```python
deleted = db.delete_by_ids(["doc1", "doc3"])
print(f"تم حذف {deleted} وثيقة")
```

---

### `delete_by_filter` — حذف بالفلتر

```python
count = db.delete_by_filter(filters: Dict)
```

**مثال:**

```python
deleted = db.delete_by_filter({"category": "spam"})
print(f"تم حذف {deleted} وثيقة مصنّفة كـ spam")
```

---

### `remove_by_doc_id` — حذف وثيقة كاملة ⭐ جديد

> **جديد** — أضيف للتوافق مع الواجهة الموحّدة. يُفوِّض لـ `delete_by_filter({"doc_id": doc_id})`.

```python
count = db.remove_by_doc_id(doc_id: str)
```

**مثال:**

```python
removed = db.remove_by_doc_id("article_001")
print(f"تم حذف {removed} chunk من الوثيقة")
```

---

### `clear_collection` — مسح المجموعة بالكامل

```python
count = db.clear_collection()
```

---

### `clear` — مسح قاعدة البيانات ⭐ جديد (موحّد)

> **جديد** — اسم موحّد مع FAISS. يُفوِّض لـ `clear_collection()`.

```python
count = db.clear()
```

---

### `stats` — إحصائيات قاعدة البيانات

```python
info = db.stats()
```

**Return:**

```python
{
    "collection_name": "my_documents",
    "total_vectors": 150,
    "distance_metric": "cosine",
    "embedding_dimension": 384,
    "tenant_id": None,
    "batch_size": 500,
    "strict_mode": True
}
```

---

### `get_stats` — إحصائيات قاعدة البيانات ⭐ جديد (موحّد)

> **جديد** — اسم موحّد مع FAISS وPinecone. يُفوِّض لـ `stats()` مع إضافة مفاتيح إلزامية.

```python
info = db.get_stats()
```

---

### `get_by_ids` — استرجاع بالمعرّف

```python
results = db.get_by_ids(ids: List[str])
# Return: List[Tuple[str, Dict]]
```

---

### `batch_operation` — عمليات دُفعية

```python
with db.batch_operation():
    db.add(chunks_1)
    db.add(chunks_2)
```

---

### `asearch` و `aadd` — الواجهة غير المتزامنة

```python
# Async search — يُرجع List[(DocumentChunk, float)]
results = await db.asearch("استعلامي", top_k=5)

# Async add — يقبل List[DocumentChunk]
await db.aadd(chunks)

# Context Manager
async with ChromaVectorDatabase(embedder=embedder) as db:
    await db.aadd(chunks)
    results = await db.asearch("query")
```

---

---

## 2. FAISSVectorDatabase

### ما هو؟

Wrapper لـ **FAISS** (Facebook AI Similarity Search) — المكتبة الأسرع والأكثر كفاءة للبحث عن المتجهات محليًا.

### التثبيت

```bash
pip install faiss-cpu   # للـ CPU
pip install faiss-gpu   # للـ GPU
```

---

### `__init__` — تهيئة قاعدة البيانات

```python
FAISSVectorDatabase(
    embedder=None,
    embedding_dim=None,
    index_type='flat',
    distance_metric='cosine',
    ivf_clusters=None,
    hnsw_m=None
)
```

| Parameter | النوع | الافتراضي | الوصف |
|-----------|------|----------|-------|
| `embedder` | `Any` | `None` | نموذج التضمين بدالة `.encode()` |
| `embedding_dim` | `int` | `None` | أبعاد التضمين (مطلوب إذا لم يُقدَّم `embedder`) |
| `index_type` | `str` | `'flat'` | نوع الفهرس: `'flat'`, `'ivf'`, `'hnsw'` |
| `distance_metric` | `str` | `'cosine'` | مقياس التشابه: `'cosine'`, `'l2'`, `'ip'` |
| `ivf_clusters` | `int` | `100` | عدد مجموعات IVF |
| `hnsw_m` | `int` | `32` | عدد الاتصالات في كل طبقة HNSW |

**مثال:**

```python
from embeddings import GeminiEmbedder

embedder = GeminiEmbedder()
db = FAISSVectorDatabase(embedder=embedder, index_type='flat', distance_metric='cosine')
```

---

### `add_chunk` — إضافة chunk واحد

```python
db.add_chunk(chunk: DocumentChunk)
```

---

### `add` — إضافة عدة chunks ⚠️ ملاحظة

> الـ metadata لكل chunk يمر تلقائياً عبر `sanitize_metadata()` قبل التخزين في الفهرس.

```python
db.add(
    chunks: List[DocumentChunk],
    embeddings: Optional[np.ndarray] = None
)
```

**مثال:**

```python
chunks = [
    DocumentChunk(chunk_id="c1", doc_id="d1", text="مقدمة في البرمجة"),
    DocumentChunk(chunk_id="c2", doc_id="d1", text="المتغيرات في Python"),
]
db.add(chunks)
print(f"المجموع: {len(db)} متجه")
```

---

### `search` — البحث بالتشابه

```python
results = db.search(
    query: Union[str, np.ndarray],
    top_k: int = 5,
    score_threshold: Optional[float] = None,
    doc_id_filter: Optional[Union[str, List[str]]] = None
)
```

**Return:** `List[Tuple[DocumentChunk, float]]`

**مثال:**

```python
results = db.search("ما هو الذكاء الاصطناعي؟", top_k=5, score_threshold=0.6)
for chunk, score in results:
    print(f"التشابه: {score:.3f} | النص: {chunk.text[:50]}")
```

---

### `remove_by_doc_id` — حذف وثيقة كاملة

```python
count = db.remove_by_doc_id(doc_id: str)
```

---

### `remove_by_chunk_id` — حذف chunk بالمعرّف

```python
success = db.remove_by_chunk_id(chunk_id: str)
```

---

### `search_by_doc_id` — بحث تشابه بين الوثائق

```python
results = db.search_by_doc_id(doc_id: str, top_k: int = 5, exclude_same_doc: bool = True)
```

---

### `save` و `load` — حفظ وتحميل

```python
db.save("./my_faiss_database")
db_loaded = FAISSVectorDatabase.load("./my_faiss_database", embedder=embedder)
```

---

### `get_stats` — إحصائيات تفصيلية

```python
stats = db.get_stats()
# {
#     'total_chunks': 500,
#     'unique_docs': 25,
#     'embedding_dim': 384,
#     'index_type': 'flat',
#     'distance_metric': 'cosine',
#     'is_trained': True,
#     'has_embedder': True
# }
```

---

### `get_chunk_by_id` و `get_chunks_by_doc_id`

```python
chunk = db.get_chunk_by_id("c001")
chunks = db.get_chunks_by_doc_id("document_1")
```

---

### `clear` — مسح قاعدة البيانات

```python
count = db.clear()
```

---

### الواجهة غير المتزامنة (Async)

```python
results = await db.asearch("استعلامي", top_k=5, score_threshold=0.5)
await db.aadd(chunks)
await db.aremove_by_doc_id("doc_id")
await db.asave("./database_path")

async with FAISSVectorDatabase(embedder=embedder) as db:
    await db.aadd(chunks)
```

---

---

## 3. PineconeVectorDatabase

### ما هو؟

Wrapper لـ **Pinecone** — أشهر قاعدة بيانات متجهات سحابية مُدارة بالكامل.

### التثبيت

```bash
pip install pinecone-client
```

---

### `__init__` — تهيئة الاتصال

```python
PineconeVectorDatabase(
    embedder=None,
    index_name="default-index",
    embedding_dim=None,
    api_key=None,
    environment="us-east-1",
    distance_metric="cosine",
    cloud="aws",
    pod_type=None,
    namespace=None,
    cache_chunks=True
)
```

| Parameter | النوع | الافتراضي | الوصف |
|-----------|------|----------|-------|
| `embedder` | `Any` | `None` | نموذج التضمين |
| `index_name` | `str` | `"default-index"` | اسم الفهرس في Pinecone |
| `embedding_dim` | `int` | `None` | أبعاد التضمين |
| `api_key` | `str` | `None` | مفتاح Pinecone API (أو من `PINECONE_API_KEY` env) |
| `environment` | `str` | `"us-east-1"` | المنطقة الجغرافية |
| `distance_metric` | `str` | `"cosine"` | مقياس التشابه: `"cosine"`, `"euclidean"`, `"dotproduct"` |
| `cloud` | `str` | `"aws"` | مزود السحابة: `"aws"`, `"gcp"`, `"azure"` |
| `pod_type` | `str` | `None` | نوع Pod (`None` للـ Serverless) |
| `namespace` | `str` | `None` | Namespace للعزل في Multi-tenant |
| `cache_chunks` | `bool` | `True` | تخزين الـ chunks محليًا لتسريع العمليات |

---

### `add` — إضافة عدة chunks ⚠️ تم الإصلاح

> **إصلاح مهم:** الـ metadata لم تعد تُسبِّب خطأ عند احتوائها على قيم `list` مثل `['arabic']`. يتم تمرير كل القيم عبر `sanitize_metadata()` تلقائياً.

```python
db.add(
    chunks: List[DocumentChunk],
    embeddings: Optional[np.ndarray] = None,
    namespace: Optional[str] = None
)
```

**مثال:**

```python
# هذا كان يُسبِّب خطأ قبل الإصلاح — الآن يعمل بشكل صحيح
chunk = DocumentChunk(
    chunk_id="c1", doc_id="d1", text="نص عربي",
    metadata={"languages": ["arabic", "english"]}  # ← list كانت تُسبِّب خطأ
)
db.add([chunk])  # ✅ يعمل الآن
```

---

### `add_chunk` — إضافة chunk واحد

```python
db.add_chunk(chunk: DocumentChunk)
```

---

### `search` — البحث المتقدم

```python
results = db.search(
    query: Union[str, np.ndarray],
    top_k: int = 5,
    score_threshold: Optional[float] = None,
    filter_dict: Optional[Dict] = None,
    namespace: Optional[str] = None,
    include_metadata: bool = True,
    include_values: bool = False
)
```

**Return:** `List[Tuple[DocumentChunk, float]]`

**مثال:**

```python
results = db.search(
    query="تعلم الآلة",
    top_k=10,
    score_threshold=0.75,
    filter_dict={"language": "ar", "category": {"$in": ["AI", "ML"]}},
    namespace="arabic_content"
)

for chunk, score in results:
    print(f"[{score:.3f}] {chunk.text[:80]}")
```

---

### `remove_by_doc_id` — حذف وثيقة كاملة ⭐ جديد (موحّد)

> **جديد** — اسم موحّد مع FAISS وChroma. يُفوِّض لـ `delete_by_doc_id()`.

```python
count = db.remove_by_doc_id(doc_id: str)
```

---

### `delete_by_doc_id` — حذف وثيقة كاملة (الاسم الأصلي)

```python
count = db.delete_by_doc_id(doc_id: str, namespace: Optional[str] = None)
```

---

### `delete_by_ids` — حذف بالمعرّفات

```python
count = db.delete_by_ids(chunk_ids: List[str], namespace: Optional[str] = None)
```

---

### `delete_by_filter` — حذف بالفلتر

```python
db.delete_by_filter(filter_dict: Dict, namespace: Optional[str] = None)
```

---

### `delete_all` — مسح namespace

```python
db.delete_all(namespace: Optional[str] = None)
```

---

### `clear` — مسح قاعدة البيانات ⭐ جديد (موحّد)

> **جديد** — اسم موحّد مع FAISS وChroma. يُفوِّض لـ `delete_all()`.

```python
db.clear()
```

---

### `get_stats` — إحصائيات الفهرس

```python
stats = db.get_stats(namespace: Optional[str] = None)
# {
#     'index_name': 'my-index',
#     'total_vector_count': 1500000,
#     'embedding_dim': 384,
#     'distance_metric': 'cosine',
#     'has_embedder': True,
#     'cache_enabled': True,
#     ...
# }
```

---

### `fetch_by_ids` — جلب بالمعرّفات

```python
chunks = db.fetch_by_ids(chunk_ids: List[str], namespace: Optional[str] = None)
```

---

### `search_by_id` — بحث تشابه بالمعرّف

```python
results = db.search_by_id(chunk_id: str, top_k: int = 5, exclude_self: bool = True)
```

---

### `list_namespaces` و `batch_operation`

```python
namespaces = db.list_namespaces()

with db.batch_operation(namespace="arabic_content"):
    db.add(arabic_chunks_1)
    db.add(arabic_chunks_2)
```

---

### الواجهة غير المتزامنة (Async)

```python
results = await db.asearch("استعلامي", top_k=5)
await db.aadd(chunks)
await db.aremove_by_doc_id("doc_id")

async with PineconeVectorDatabase(embedder=embedder, api_key="key") as db:
    await db.aadd(chunks)
    results = await db.asearch("query")
```

---

---

## الكلاس المشترك: `DocumentChunk`

يُستخدم مع الثلاث backends.

```python
from chunks import DocumentChunk

chunk = DocumentChunk(
    chunk_id="article_5_page_3",   # معرّف فريد للـ chunk
    doc_id="article_5",            # معرّف الوثيقة الأم
    text="نص المقتطف هنا...",
    metadata={
        "page": 3,
        "author": "محمد أحمد",
        "languages": ["ar", "en"]  # ✅ list مقبولة — sanitize_metadata تعالجها تلقائياً
    }
)
```

---

## ملخص التغييرات (Changelog)

### تغييرات تؤثر على الكود الموجود ⚠️

| التغيير | قبل | بعد |
|---------|-----|-----|
| **Chroma `add`** | `add(ids, docs, metas)` فقط | `add(chunks)` أو `add(ids, docs, metas)` |
| **Chroma `search` Return Type** | `(str, float, dict)` | `(DocumentChunk, float)` |
| **Chroma `search`** | لا يدعم `score_threshold` | يدعم `score_threshold` |

### إضافات جديدة لا تكسر الكود الموجود ✅

| الإضافة | Chroma | FAISS | Pinecone |
|---------|--------|-------|---------|
| `remove_by_doc_id()` | ⭐ جديد | موجود | ⭐ جديد (alias) |
| `get_stats()` | ⭐ جديد (alias لـ `stats()`) | موجود | موجود |
| `clear()` | ⭐ جديد (alias لـ `clear_collection()`) | موجود | ⭐ جديد (alias لـ `delete_all()`) |
| `sanitize_metadata` تلقائي | ✅ | ✅ | ✅ (إصلاح bug الـ list) |

---

## مثال شامل متكامل

```python
from embeddings import GeminiEmbedder
from chunks import DocumentChunk

embedder = GeminiEmbedder()

# ---- ChromaDB ----
from vector_database import ChromaVectorDatabase

chroma_db = ChromaVectorDatabase(embedder=embedder, collection_name="articles")

chunks = [
    DocumentChunk("c1", "doc1", "مقال عن الذكاء الاصطناعي", {"tag": "AI"}),
    DocumentChunk("c2", "doc2", "مقال عن تعلم الآلة", {"tag": "ML"}),
]

# الأسلوب الموحّد الجديد
chroma_db.add(chunks)

# search — الآن يُرجع (DocumentChunk, float)
results = chroma_db.search("التعلم العميق", top_k=2, score_threshold=0.5)
for chunk, score in results:
    print(f"{score:.3f} — {chunk.text}")

# ---- FAISS ----
from vector_database import FAISSVectorDatabase

faiss_db = FAISSVectorDatabase(embedder=embedder, index_type='flat')
faiss_db.add(chunks)
faiss_db.save("./faiss_backup")

results = faiss_db.search("كود Python", top_k=3, score_threshold=0.5)
for chunk, score in results:
    print(f"{score:.3f} — {chunk.text}")

# ---- Pinecone ----
from vector_database import PineconeVectorDatabase

pinecone_db = PineconeVectorDatabase(
    embedder=embedder,
    index_name="production-index",
    api_key="YOUR_API_KEY"
)

# metadata مع list — لم تعد تُسبِّب خطأ
chunk = DocumentChunk("p1", "doc1", "محتوى سحابي", {"languages": ["ar", "en"]})
pinecone_db.add([chunk])

results = pinecone_db.search("بحث في السحابة", top_k=5, filter_dict={"region": "ME"})
for chunk, score in results:
    print(f"{score:.3f} — {chunk.text}")

# ---- الواجهة الموحّدة — نفس الكود مع أي backend ----
def add_and_search(db: VectorDatabaseBase, query: str):
    db.add(chunks)
    results = db.search(query, top_k=3)
    stats = db.get_stats()          # اسم موحّد
    db.remove_by_doc_id("doc1")     # اسم موحّد
    return results
```

---

## دليل الاختيار

### اختر **ChromaDB** إذا:
- مشروعك صغير أو نموذج أولي
- تريد بدء العمل بسرعة بدون إعداد معقد
- تحتاج تخزينًا محليًا مع دعم فلترة Metadata
- تريد دعمًا لـ Multi-tenancy عبر `tenant_id`

### اختر **FAISS** إذا:
- تحتاج أعلى سرعة ممكنة
- البيانات حساسة ولا تريد إرسالها للسحابة
- تعمل على بيئة بدون إنترنت
- تريد التحكم الكامل في نوع الفهرس (Flat/IVF/HNSW)

### اختر **Pinecone** إذا:
- التطبيق في الإنتاج ويحتاج ملايين المتجهات
- تحتاج ضمانات توفر عالٍ (High Availability)
- تحتاج فلترة Metadata متقدمة وسريعة
- تعمل بنموذج Multi-tenant مع namespaces