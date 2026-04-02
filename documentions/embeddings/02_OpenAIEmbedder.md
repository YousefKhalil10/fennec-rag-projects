# 🔵 OpenAIEmbedder — نماذج OpenAI للتضمين

## نظرة عامة

`OpenAIEmbedder` يوفر تكاملاً كاملاً مع نماذج تضمين OpenAI مع ميزات متقدمة: تحديد معدل الطلبات تلقائياً، عد الرموز الدقيق، تتبع التكلفة، وإعادة المحاولة الذكية. جميع النماذج تدعم العربية بجودة ممتازة.

---

## التثبيت

```bash
pip install openai tiktoken
```

```python
from embeddings import OpenAIEmbedder
```

---

## النماذج المدعومة

| النموذج | الأبعاد | الرموز | التكلفة/مليون | العربية |
|---|---|---|---|---|
| `text-embedding-3-large` | 3072 | 8191 | $0.13 | ممتاز |
| `text-embedding-3-small` | 1536 | 8191 | $0.02 | ممتاز |
| `text-embedding-ada-002` | 1536 | 8191 | $0.10 | جيد (قديم) |

---

## الدوال الرئيسية

### `__init__`

```python
OpenAIEmbedder(
    model_name="text-embedding-3-small",
    api_key=None,
    dimensions=None,
    device=None,
    normalize_embeddings=True,
    batch_size=100,
    max_length=None,
    cache_embeddings=True,
    show_progress=False,
    timeout=60,
    max_retries=3,
    retry_delay=1.0,
    enable_rate_limiting=True,
    max_requests_per_minute=3000,
    max_tokens_per_minute=1_000_000,
    track_costs=True
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `model_name` | `str` | اسم نموذج OpenAI |
| `api_key` | `str` | مفتاح API (أو `OPENAI_API_KEY` من البيئة) |
| `dimensions` | `int` | تقليل الأبعاد — يدعمها `text-embedding-3-*` فقط |
| `normalize_embeddings` | `bool` | تطبيع المتجهات |
| `batch_size` | `int` | حجم الدفعة (يدعم OpenAI حتى 2048) |
| `cache_embeddings` | `bool` | تخزين مؤقت بالنصوص كمفاتيح |
| `timeout` | `int` | مهلة الطلب بالثواني |
| `max_retries` | `int` | أقصى عدد محاولات عند الفشل |
| `retry_delay` | `float` | التأخير الأساسي بين المحاولات |
| `enable_rate_limiting` | `bool` | حماية تلقائية من تجاوز الحد |
| `track_costs` | `bool` | تتبع التكلفة والرموز المستهلكة |

---

### `encode`

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True,
    batch_size: Optional[int] = None,
    **kwargs
) -> np.ndarray
```

**الوصف:** تحويل النصوص إلى متجهات عبر OpenAI API.

| المعامل | النوع | الوصف |
|---|---|---|
| `texts` | `str` أو `List[str]` | نص واحد أو قائمة نصوص |
| `show_progress_bar` | `bool` | شريط التقدم (يتطلب `tqdm`) |
| `batch_size` | `int` | تجاوز حجم الدفعة الافتراضي |

**Return:** `np.ndarray` بشكل `(n, embedding_dim)`

---

### `estimate_cost`

```python
estimate_cost(texts: Union[str, List[str]]) -> Dict[str, Any]
```

**الوصف:** تقدير التكلفة **قبل** إرسال الطلب.

**Return:**
```python
{
    "texts_count": 100,
    "total_tokens": 5420,
    "avg_tokens_per_text": 54,
    "cost_per_1m_tokens_usd": 0.02,
    "estimated_cost_usd": 0.000108,
    "model": "text-embedding-3-small",
    "dimensions": 1536
}
```

---

### `get_usage_stats`

```python
get_usage_stats() -> Dict[str, Any]
```

**الوصف:** إحصائيات الاستخدام التفصيلية.

**Return:**
```python
{
    "total_encodings": 10,
    "total_texts": 500,
    "cache_hits": 120,
    "cache_hit_rate": 0.24,
    "cache_size": 380,
    "api_usage": {
        "total_tokens": 45000,
        "total_requests": 8,
        "total_cost_usd": 0.0009,
        "elapsed_time_seconds": 12.5
    }
}
```

---

### `get_model_info`

```python
get_model_info() -> Dict[str, Any]
```

**الوصف:** معلومات شاملة عن النموذج والإعدادات الحالية.

---

### `clear_cache`

```python
clear_cache() -> None
```

**الوصف:** مسح الكاش بالكامل.

---

## الاستخدام كـ Context Manager

عند الخروج، يطبع ملخص الجلسة (الرموز، الطلبات، التكلفة):

```python
with OpenAIEmbedder(model_name="text-embedding-3-small", api_key="sk-...") as emb:
    embeddings = emb.encode(texts)
# 📊 Session Summary: tokens=..., cost=$...
```

---

## مثال عملي كامل

```python
import os
import numpy as np
from embeddings import OpenAIEmbedder

# --- 1. التهيئة ---
embedder = OpenAIEmbedder(
    model_name="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),   # أو مباشرة: api_key="sk-..."
    dimensions=768,                         # تقليل من 1536 → 768 (اختياري)
    batch_size=100,
    cache_embeddings=True,
    track_costs=True,
)

# --- 2. التحقق من الاتصال ---
status = embedder.validate_connection(detailed=True)
print(f"✅ الاتصال: {status['success']}")
print(f"   الأبعاد: {status['embedding_dim']}")
print(f"   وقت التحويل: {status['encoding_time']}")

# --- 3. تقدير التكلفة مسبقاً ---
texts = [
    "الذكاء الاصطناعي هو محاكاة للذكاء البشري في الآلات.",
    "تعلم الآلة يُمكّن الأنظمة من التعلم التلقائي من البيانات.",
    "معالجة اللغة الطبيعية تُتيح للآلات فهم اللغة البشرية.",
    "الشبكات العصبية العميقة مستوحاة من بنية الدماغ البشري.",
    "الرؤية الحاسوبية تُمكّن الآلات من تفسير الصور والفيديو.",
]

cost_estimate = embedder.estimate_cost(texts)
print(f"\n💰 تقدير التكلفة:")
print(f"   النصوص: {cost_estimate['texts_count']}")
print(f"   الرموز: {cost_estimate['total_tokens']:,}")
print(f"   التكلفة المتوقعة: ${cost_estimate['estimated_cost_usd']:.6f}")

# --- 4. تحويل نص واحد ---
single_emb = embedder.encode("ما هو الذكاء الاصطناعي؟")
print(f"\n📊 متجه نص واحد: {single_emb.shape}")

# --- 5. تحويل قائمة نصوص ---
embeddings = embedder.encode(texts, show_progress_bar=True)
print(f"📊 متجهات: {embeddings.shape}")   # (5, 768)

# --- 6. حساب التشابه ---
query = "ما هي تطبيقات الذكاء الاصطناعي؟"
results = embedder.batch_similarity(query, texts, top_k=3)
print(f"\n🔍 أقرب 3 نصوص للاستعلام:")
for idx, score in results:
    print(f"  [{idx}] {texts[idx][:50]}... → {score:.3f}")

# --- 7. التشابه المباشر ---
sim = embedder.similarity(
    "الذكاء الاصطناعي يُحاكي الذكاء البشري",
    "AI simulates human intelligence",
    metric='cosine'
)
print(f"\n↔️ التشابه عربي↔إنجليزي: {sim:.3f}")

# --- 8. الكاش ---
# الاستدعاء الثاني أسرع بكثير (من الكاش)
embeddings_cached = embedder.encode(texts)
stats = embedder.get_usage_stats()
print(f"\n💾 معدل إصابة الكاش: {stats['cache_hit_rate']:.0%}")

# --- 9. الإحصائيات الكاملة ---
info = embedder.get_model_info()
print(f"\n📋 معلومات النموذج:")
print(f"   النموذج: {info['model_name']}")
print(f"   الأبعاد: {info['configured_dimensions']}")
print(f"   التكلفة الإجمالية: ${info['usage_stats']['total_cost_usd']:.6f}")

# --- 10. تقليل الأبعاد (للنماذج الجديدة فقط) ---
embedder_reduced = OpenAIEmbedder(
    model_name="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY"),
    dimensions=256,          # تقليل من 3072 → 256
)
reduced_emb = embedder_reduced.encode("نص تجريبي")
print(f"\n📉 متجه مُقلَّص: {reduced_emb.shape}")   # (1, 256)

# --- 11. Context Manager مع ملخص تلقائي ---
with OpenAIEmbedder(
    model_name="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
) as emb:
    result = emb.encode("اختبار نهائي")
    print(f"\n[Context] متجه: {result.shape}")
# يطبع ملخص الجلسة عند الخروج
```
