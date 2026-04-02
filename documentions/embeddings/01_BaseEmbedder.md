# 🧱 BaseEmbedder — الواجهة الأساسية

## نظرة عامة

`BaseEmbedder` هو الكلاس الأساسي المجرد (Abstract Base Class) الذي ترث منه **جميع** أنواع الـ Embedders في المكتبة. يوفر وظائف مشتركة جاهزة مثل: الكاش، قياس التشابه، الإحصائيات، وقياس الأداء — دون الحاجة لإعادة كتابتها في كل محوّل.

لا تستخدم `BaseEmbedder` مباشرة، بل استخدم أحد المحوّلات المشتقة منه.

---

## التثبيت والاستيراد

```python
from embeddings import BaseEmbedder
```

---

## الدوال المجردة (يجب تنفيذها)

### `encode` *(abstract)*

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True,
    **kwargs
) -> np.ndarray
```

**الوصف:** تحويل النصوص إلى متجهات. يجب على كل محوّل تنفيذ هذه الدالة.

---

### `embedding_dim` *(abstract property)*

```python
@property
embedding_dim -> int
```

**الوصف:** بُعد المتجهات الذي يُنتجه النموذج.

---

## الدوال الجاهزة (موروثة)

### `encode_with_cache`

```python
encode_with_cache(
    texts: Union[str, List[str]],
    **kwargs
) -> np.ndarray
```

**الوصف:** تحويل النصوص مع دعم التخزين المؤقت (Cache). يتحقق أولاً من الكاش قبل الاستدعاء الفعلي للنموذج.

| المعامل | النوع | الوصف |
|---|---|---|
| `texts` | `str` أو `List[str]` | النص أو قائمة النصوص |

> ملاحظة: يعمل فقط إذا كان `cache_embeddings=True` عند التهيئة.

---

### `similarity`

```python
similarity(
    text1: Union[str, np.ndarray],
    text2: Union[str, np.ndarray],
    metric: str = 'cosine'
) -> float
```

**الوصف:** حساب درجة التشابه بين نصين أو متجهين.

| المعامل | النوع | الوصف |
|---|---|---|
| `text1` | `str` أو `np.ndarray` | النص أو المتجه الأول |
| `text2` | `str` أو `np.ndarray` | النص أو المتجه الثاني |
| `metric` | `str` | نوع المقياس: `'cosine'`، `'dot'`، `'euclidean'` |

**Return:** `float` — درجة التشابه

**مثال:**
```python
score = embedder.similarity("الذكاء الاصطناعي", "تعلم الآلة")
print(f"التشابه: {score:.3f}")
```

---

### `batch_similarity`

```python
batch_similarity(
    query: Union[str, np.ndarray],
    texts: List[str],
    top_k: Optional[int] = None
) -> Union[np.ndarray, List[tuple]]
```

**الوصف:** حساب التشابه بين استعلام وقائمة نصوص دفعةً واحدة.

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` أو `np.ndarray` | الاستعلام |
| `texts` | `List[str]` | قائمة النصوص للمقارنة |
| `top_k` | `int` | إرجاع أفضل k نتيجة فقط (اختياري) |

**Retunr:**
- إذا `top_k=None`: مصفوفة numpy بكل درجات التشابه
- إذا `top_k=N`: قائمة من `(index, score)` للأفضل N نتيجة

**مثال:**
```python
docs = ["نص أول", "نص ثاني", "نص ثالث"]
results = embedder.batch_similarity("سؤال؟", docs, top_k=2)
for idx, score in results:
    print(f"  [{idx}] {docs[idx]} — {score:.3f}")
```

---

### `validate_connection`

```python
validate_connection(
    test_text: str = "مرحباً Hello",
    detailed: bool = False
) -> Dict[str, Any]
```

**الوصف:** التحقق من أن المحوّل يعمل بشكل صحيح.

| المعامل | النوع | الوصف |
|---|---|---|
| `test_text` | `str` | نص اختبار |
| `detailed` | `bool` | إرجاع معلومات تفصيلية |

**يُرجع:**
```python
# أساسي
{"success": True, "reason": "✅ ...", "embedding_dim": 768, "encoding_time": "0.123s"}

# تفصيلي (detailed=True)
{"success": True, "model_name": "...", "device": "cuda",
 "embedding_shape": (1, 768), "embedding_norm": 1.0, ...}
```

---

### `get_model_info`

```python
get_model_info() -> Dict[str, Any]
```

**الوصف:** معلومات تفصيلية عن النموذج الحالي.

**يُرجع:**
```python
{
    "model_name": "text-embedding-3-small",
    "model_class": "OpenAIEmbedder",
    "embedding_dim": 1536,
    "device": "cpu",
    "normalize_embeddings": True,
    "batch_size": 100,
    "max_length": None,
    "cache_enabled": True
}
```

---

### `get_stats`

```python
get_stats() -> Dict[str, Any]
```

**الوصف:** إحصائيات الأداء التراكمية.

**يُرجع:**
```python
{
    "total_encodings": 50,
    "total_texts": 500,
    "cache_hits": 120,
    "total_time": 45.3,
    "avg_time_per_text": 0.091,
    "cache_hit_rate": 0.24,   # فقط إذا cache_embeddings=True
    "cache_size": 380
}
```

---

### `reset_stats`

```python
reset_stats() -> None
```

**الوصف:** إعادة تعيين جميع إحصائيات الأداء إلى الصفر.

---

### `clear_cache`

```python
clear_cache() -> None
```

**الوصف:** مسح الكاش بالكامل.

---

### `cleanup`

```python
cleanup() -> None
```

**الوصف:** تنظيف الموارد (مسح الكاش + تحرير ذاكرة GPU إن وُجدت). يُستدعى تلقائياً عند الحذف.

---

### `timing` *(context manager)*

```python
with embedder.timing("batch_encoding"):
    embeddings = embedder.encode(texts)
```

**الوصف:** سياق لقياس وطباعة وقت تنفيذ عملية معينة.

---

## معاملات التهيئة المشتركة

كل Embedder يرث هذه المعاملات من `BaseEmbedder`:

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---|---|---|---|
| `model_name` | `str` | — | اسم النموذج |
| `device` | `str` | تلقائي | `'cuda'`، `'cpu'`، `'mps'` — يُكشف تلقائياً |
| `normalize_embeddings` | `bool` | `True` | تطبيع المتجهات لوحدة القياس |
| `batch_size` | `int` | `32` | حجم الدفعة للمعالجة |
| `max_length` | `int` | `512` | أقصى طول للنص بالرموز |
| `cache_embeddings` | `bool` | `False` | تخزين المتجهات مؤقتاً |
| `show_progress` | `bool` | `False` | شريط التقدم |

---

## الواجهة غير المتزامنة (Async API)

| الدالة | الوصف |
|---|---|
| `aencode(texts, ...)` | تحويل نصوص غير متزامن |
| `aencode_with_cache(texts)` | تحويل مع كاش غير متزامن |
| `abatch_similarity(query, candidates)` | تشابه دفعي غير متزامن |

---
```python
# مثال async
async def example():
    embeddings = await embedder.aencode(["نص أول", "نص ثاني"])
    results = await embedder.abatch_similarity("سؤال؟", candidates, top_k=5)
```

---

## استخدام كـ Context Manager

```python
async with embedder as e:
    embeddings = await e.aencode(texts)
# cleanup() يُستدعى تلقائياً
```

---

## مثال: بناء محوّل مخصص

```python
from embeddings import BaseEmbedder
import numpy as np

class MyEmbedder(BaseEmbedder):
    def __init__(self):
        super().__init__(
            model_name="my-model",
            normalize_embeddings=True,
            batch_size=64,
            cache_embeddings=True,
        )
        # تهيئة النموذج هنا

    @property
    def embedding_dim(self) -> int:
        return 512

    def encode(self, texts, show_progress_bar=False,
               convert_to_numpy=True, **kwargs) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        # منطق التحويل هنا
        return np.random.randn(len(texts), self.embedding_dim).astype(np.float32)

# الاستخدام
embedder = MyEmbedder()
result = embedder.validate_connection(detailed=True)
print(result)
```
