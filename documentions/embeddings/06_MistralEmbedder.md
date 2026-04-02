# 🟠 MistralEmbedder — نماذج Mistral AI للتضمين

## نظرة عامة

`MistralEmbedder` يوفر تكاملاً مع نماذج تضمين Mistral AI عبر API. يدعم تتبع التكلفة، تحديد معدل الطلبات، وكاشاً ذكياً مع LRU Cache.

---

## التثبيت

```bash
pip install mistralai
```

```python
from embeddings import MistralEmbedder
```

---

## النماذج المدعومة

| النموذج | الأبعاد | دعم العربية |
|---|---|---|
| `mistral-embed` | 1024 | جيد |

---

## الدوال الرئيسية

### `__init__`

```python
MistralEmbedder(
    model_name="mistral-embed",
    api_key=None,
    base_url="https://api.mistral.ai/v1",
    normalize_embeddings=True,
    batch_size=32,
    max_length=None,
    cache_embeddings=False,
    cache_size=10000,
    show_progress=False,
    timeout=60,
    max_retries=3,
    retry_delay=1.0,
    enable_rate_limiting=True,
    max_requests_per_second=5,
    track_costs=True
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `api_key` | `str` | مفتاح API (أو `MISTRAL_API_KEY` من البيئة) |
| `base_url` | `str` | عنوان API (مفيد للخوادم المخصصة) |
| `cache_size` | `int` | حجم LRU Cache (عدد المدخلات) |
| `max_requests_per_second` | `int` | حد معدل الطلبات في الثانية |
| `track_costs` | `bool` | تتبع التكلفة |

---

### `encode`

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True,
    batch_size: Optional[int] = None
) -> np.ndarray
```

---

### `estimate_cost`

```python
estimate_cost(texts: Union[str, List[str]]) -> Dict[str, Any]
```

**Return:**
```python
{
    "texts_count": 50,
    "estimated_tokens": 2500,
    "estimated_cost_usd": 0.000025,
    "model": "mistral-embed"
}
```

---

### `get_usage_stats` / `get_model_info` / `clear_cache`

---

## مثال عملي

```python
import os
from embeddings import MistralEmbedder

embedder = MistralEmbedder(
    model_name="mistral-embed",
    api_key=os.getenv("MISTRAL_API_KEY"),
    batch_size=32,
    cache_embeddings=True,
    cache_size=5000,
    enable_rate_limiting=True,
    max_requests_per_second=5,
    track_costs=True,
)

# التحقق
status = embedder.validate_connection(detailed=True)
print(f"✅ {status['success']} | الأبعاد: {status['embedding_dim']}")

texts = [
    "الذكاء الاصطناعي يُحوّل صناعات بأكملها.",
    "تعلم الآلة يعتمد على البيانات والخوارزميات.",
    "معالجة اللغة الطبيعية تُتيح التواصل مع الحواسيب.",
]

# تقدير التكلفة
cost = embedder.estimate_cost(texts)
print(f"💰 التكلفة المتوقعة: ${cost['estimated_cost_usd']:.6f}")

# التحويل
embeddings = embedder.encode(texts)
print(f"📊 الشكل: {embeddings.shape}")   # (3, 1024)

# التشابه
sim = embedder.similarity(texts[0], texts[1])
print(f"↔️ التشابه: {sim:.3f}")

# البحث
results = embedder.batch_similarity("كيف تعمل خوارزميات ML؟", texts, top_k=2)
for idx, score in results:
    print(f"  [{idx}] {score:.3f}: {texts[idx][:50]}")

# الإحصائيات
stats = embedder.get_usage_stats()
print(f"\n📊 الإحصائيات:")
if 'api_usage' in stats:
    print(f"  التكلفة الإجمالية: ${stats['api_usage']['total_cost_usd']:.6f}")
    print(f"  الرموز: {stats['api_usage']['total_tokens']:,}")

with MistralEmbedder(api_key=os.getenv("MISTRAL_API_KEY")) as emb:
    result = emb.encode("اختبار")
    print(f"\n[Context] {result.shape}")
```

---
