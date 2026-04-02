# 🟡 GeminiEmbedder — نماذج Google Gemini للتضمين

## نظرة عامة

`GeminiEmbedder` يوفر تكاملاً مع نماذج Google Gemini للتضمين عبر **SDK الجديد `google-genai`** (وليس `google-generativeai` القديم). يدعم أنواع مهام مختلفة (بحث، تصنيف، تجميع)، وتقليل الأبعاد (MRL)، ويدعم العربية و100+ لغة بجودة ممتازة.

> ⚠️ **مهم:** يستخدم `google-genai` (الجديد)، وليس `google-generativeai` (القديم المهمل).

---

## التثبيت

```bash
pip install google-genai
```

```python
from embeddings import GeminiEmbedder
```

---

## النماذج المدعومة

| النموذج | الأبعاد | الرموز | الحالة |
|---|---|---|---|
| `gemini-embedding-001` | 3072 | 8192 | ✅ نشط (الأحدث) |
| `text-embedding-004` | 768 | 2048 | ⚠️ مهمل (2026-01-14) |
| `embedding-001` | 768 | 2048 | ⚠️ مهمل (2025-08-14) |

---

## أنواع المهام — `task_type`

| النوع | متى تستخدمه |
|---|---|
| `RETRIEVAL_QUERY` | للأسئلة والاستعلامات في نظام RAG |
| `RETRIEVAL_DOCUMENT` | للمستندات التي ستُبحث فيها |
| `SEMANTIC_SIMILARITY` | لقياس التشابه بين النصوص |
| `CLASSIFICATION` | لتصنيف النصوص |
| `CLUSTERING` | لتجميع النصوص المتشابهة |

---

## الدوال الرئيسية

### `__init__`

```python
GeminiEmbedder(
    model_name="gemini-embedding-001",
    api_key=None,
    task_type=None,
    output_dimensionality=None,
    device=None,
    normalize_embeddings=True,
    batch_size=50,
    max_length=None,
    cache_embeddings=True,
    show_progress=False,
    timeout=60,
    max_retries=3,
    retry_delay=2.0,
    track_usage=True
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `model_name` | `str` | اسم نموذج Gemini |
| `api_key` | `str` | مفتاح API (أو `GOOGLE_API_KEY` / `GEMINI_API_KEY` من البيئة) |
| `task_type` | `str` | نوع المهمة (راجع الجدول أعلاه) — يحسّن جودة النتائج |
| `output_dimensionality` | `int` | تقليل الأبعاد (MRL) — `gemini-embedding-001` فقط |
| `batch_size` | `int` | حجم الدفعة (حد Gemini: 100) |
| `max_retries` | `int` | أقصى عدد محاولات |
| `retry_delay` | `float` | التأخير الأساسي بين المحاولات (بالثواني) |
| `track_usage` | `bool` | تتبع إحصائيات الاستخدام |

---

### `encode`

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True,
    task_type: Optional[str] = None,
    batch_size: Optional[int] = None,
    **kwargs
) -> np.ndarray
```

**الوصف:** تحويل النصوص إلى متجهات. يمكن تجاوز `task_type` لاستعلام واحد.

| المعامل | النوع | الوصف |
|---|---|---|
| `task_type` | `str` | تجاوز `task_type` الافتراضي لهذا الاستدعاء فقط |

---

### `get_usage_stats`

```python
get_usage_stats() -> Dict[str, Any]
```

**Return:**
```python
{
    "total_encodings": 5,
    "total_texts": 200,
    "cache_hit_rate": 0.3,
    "task_type": "RETRIEVAL_DOCUMENT",
    "api_usage": {
        "total_requests": 4,
        "total_texts": 140,
        "total_characters": 85000,
        "errors": 0,
        "success_rate": 1.0,
        "cache_hits": 60
    }
}
```

---

### `get_model_info`

```python
get_model_info() -> Dict[str, Any]
```

---

### `clear_cache`

```python
clear_cache() -> None
```

---

## الاستخدام كـ Context Manager

```python
with GeminiEmbedder(api_key="...") as emb:
    embeddings = emb.encode(texts)
# يطبع ملخص: الطلبات، النصوص، الأحرف، معدل النجاح
```

---

## مثال عملي كامل

```python
import os
from embeddings import GeminiEmbedder

# --- 1. التهيئة لنظام RAG ---
# نحتاج نوعَي task لـ RAG: RETRIEVAL_DOCUMENT للمستندات، RETRIEVAL_QUERY للاستعلامات
doc_embedder = GeminiEmbedder(
    model_name="gemini-embedding-001",
    api_key=os.getenv("GOOGLE_API_KEY"),
    task_type="RETRIEVAL_DOCUMENT",    # للمستندات
    output_dimensionality=768,         # تقليل من 3072 → 768 (اختياري)
    batch_size=50,
    cache_embeddings=True,
    track_usage=True,
)

query_embedder = GeminiEmbedder(
    model_name="gemini-embedding-001",
    api_key=os.getenv("GOOGLE_API_KEY"),
    task_type="RETRIEVAL_QUERY",       # للاستعلامات
    output_dimensionality=768,
)

# --- 2. التحقق من الاتصال ---
status = doc_embedder.validate_connection(detailed=True)
print(f"✅ {status['success']} | الأبعاد: {status['embedding_dim']}")

# --- 3. تضمين المستندات ---
documents = [
    "الذكاء الاصطناعي هو محاكاة للذكاء البشري باستخدام الحاسوب.",
    "تعلم الآلة يُمكّن الأنظمة من التعلم من البيانات دون برمجة صريحة.",
    "الشبكات العصبية مستوحاة من طريقة عمل الدماغ البشري.",
    "معالجة اللغة الطبيعية تُتيح للآلات فهم وتوليد اللغة.",
    "الرؤية الحاسوبية تُمكّن الآلات من تحليل وفهم الصور.",
]

doc_embeddings = doc_embedder.encode(documents, show_progress_bar=True)
print(f"\n📄 متجهات المستندات: {doc_embeddings.shape}")

# --- 4. تضمين الاستعلامات ---
query = "ما هي تطبيقات الذكاء الاصطناعي في معالجة اللغة؟"
query_emb = query_embedder.encode(query)
print(f"🔍 متجه الاستعلام: {query_emb.shape}")

# --- 5. البحث بالتشابه ---
results = doc_embedder.batch_similarity(query_emb[0], documents, top_k=3)
print(f"\n📊 أقرب 3 مستندات:")
for idx, score in results:
    print(f"  [{idx}] score={score:.3f}: {documents[idx][:60]}...")

# --- 6. التضمين للتصنيف ---
classifier_emb = GeminiEmbedder(
    model_name="gemini-embedding-001",
    api_key=os.getenv("GOOGLE_API_KEY"),
    task_type="CLASSIFICATION",
)
texts_to_classify = ["هذا المنتج رائع جداً!", "لم أكن سعيداً بالخدمة."]
class_embeddings = classifier_emb.encode(texts_to_classify)
print(f"\n🏷️ متجهات التصنيف: {class_embeddings.shape}")

# --- 7. تجاوز task_type لاستدعاء واحد ---
# embedder افتراضي RETRIEVAL_DOCUMENT لكن نريد SEMANTIC_SIMILARITY هنا
similarity_emb = doc_embedder.encode(
    ["نص للمقارنة"],
    task_type="SEMANTIC_SIMILARITY"   # يتجاوز الافتراضي لهذا الاستدعاء فقط
)

# --- 8. تقليل الأبعاد (MRL) ---
# الأبعاد الموصى بها: 768, 1536, 3072
for dims in [768, 1536, 3072]:
    emb = GeminiEmbedder(
        model_name="gemini-embedding-001",
        api_key=os.getenv("GOOGLE_API_KEY"),
        output_dimensionality=dims,
    )
    test_emb = emb.encode("نص اختبار")
    print(f"  {dims} أبعاد → {test_emb.shape}")

# --- 9. الإحصائيات ---
stats = doc_embedder.get_usage_stats()
print(f"\n📊 الإحصائيات:")
print(f"  إجمالي النصوص: {stats['total_texts']}")
api = stats['api_usage']
print(f"  الطلبات: {api['total_requests']}")
print(f"  معدل النجاح: {api['success_rate']:.0%}")
print(f"  إصابات الكاش: {api['cache_hits']}")

# --- 10. Context Manager ---
with GeminiEmbedder(
    model_name="gemini-embedding-001",
    api_key=os.getenv("GOOGLE_API_KEY"),
    track_usage=True,
) as emb:
    embeddings = emb.encode(documents)
# يطبع ملخص الجلسة تلقائياً
```
