# 🤗 HuggingFaceEmbedder — نماذج HuggingFace

## نظرة عامة

`HuggingFaceEmbedder` يدعم تشغيل نماذج HuggingFace بوضعين: **API** (عبر HuggingFace Inference API) أو **محلي** (تحميل النموذج وتشغيله على جهازك). يدعم آلاف النماذج المتاحة على Hub.

---

## التثبيت

```bash
# للوضع المحلي (LOCAL)
pip install sentence-transformers torch

# للوضع API
pip install requests
```

```python
from embeddings import HuggingFaceEmbedder
```

---



## الدوال الرئيسية

### `__init__`

```python
HuggingFaceEmbedder(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    device=None,
    normalize_embeddings=True,
    batch_size=32,
    max_length=512,
    cache_embeddings=False,
    cache_ttl=3600,
    show_progress=False,
    timeout=30,
    max_retries=3,
    trust_remote_code=False
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `model_name` | `str` | اسم النموذج على HuggingFace Hub |
| `device` | `str` | `'cuda'`، `'cpu'`، `'mps'` — يُكشف تلقائياً |
| `normalize_embeddings` | `bool` | تطبيع المتجهات |
| `batch_size` | `int` | حجم الدفعة |
| `cache_ttl` | `int` | مدة صلاحية الكاش بالثواني (في وضع API) |
| `trust_remote_code` | `bool` | السماح بتنفيذ كود النموذج (لبعض النماذج المتقدمة) |

---

### `encode`

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True,
    normalize: bool = None,
    **kwargs
) -> np.ndarray
```

| المعامل | النوع | الوصف |
|---|---|---|
| `normalize` | `bool` | تجاوز إعداد التطبيع لهذا الاستدعاء فقط |

---

### `get_model_info`

```python
get_model_info() -> Dict[str, Any]
```

**Return:**
```python
{
    "full_name": info.full_name,
    "dimensions": info.dimensions,
    "max_tokens": info.max_tokens,
    "arabic_quality": info.arabic_quality.value,
    "size": info.size,
    "description": info.description,
}
```

---

### `get_stats` / `clear_cache`

```python
get_stats() -> Dict[str, Any]
clear_cache() -> None
```

---

## النماذج الموصى بها للعربية

| النموذج | الأبعاد | الوصف |
|---|---|---|
| `sentence-transformers/LaBSE` | 768 | أفضل للبحث متعدد اللغات عربي/إنجليزي |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | جودة عالية، متعدد اللغات |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | خفيف وسريع |
| `aubmindlab/bert-base-arabertv2` | 768 | متخصص للعربية |
| `CAMeL-Lab/bert-base-arabic-camelbert-msa` | 768 | العربية الفصحى |

---

## مثال عملي كامل

```python
import os
from embeddings import HuggingFaceEmbedder

# =====================================
# الوضع 1: تشغيل محلي (LOCAL)
# =====================================
print("=== الوضع المحلي ===")

local_emb = HuggingFaceEmbedder(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    device=None,                # كشف تلقائي (GPU إن وُجد)
    normalize_embeddings=True,
    batch_size=32,
    cache_embeddings=True,
    show_progress=True,
)

# التحقق من الاتصال
status = local_emb.validate_connection(detailed=True)
print(f"✅ {status['success']} | الأبعاد: {status['embedding_dim']} | الجهاز: {status['device']}")

# تحويل نصوص عربية
arabic_texts = [
    "الذكاء الاصطناعي يُغيّر العالم بشكل جذري.",
    "تعلم الآلة هو مستقبل التكنولوجيا.",
    "الشبكات العصبية تُحاكي الدماغ البشري.",
    "معالجة اللغة الطبيعية تربط الإنسان بالآلة.",
]

embeddings = local_emb.encode(arabic_texts)
print(f"📊 الشكل: {embeddings.shape}")   # (4, 768)

# حساب التشابه
query = "كيف يعمل الذكاء الاصطناعي؟"
results = local_emb.batch_similarity(query, arabic_texts, top_k=2)
print(f"\n🔍 أقرب نصان:")
for idx, score in results:
    print(f"  [{idx}] {score:.3f}: {arabic_texts[idx]}")


# =====================================
# نموذج متخصص للعربية (LaBSE)
# =====================================
print("\n=== LaBSE للبحث العربي-الإنجليزي ===")

labse = HuggingFaceEmbedder(
    model_name="sentence-transformers/LaBSE",
    mode="local",
    normalize_embeddings=True,
    batch_size=16,
)

en_texts = ["Artificial intelligence is the future.", "Machine learning enables automation."]
ar_texts = ["الذكاء الاصطناعي هو المستقبل.", "تعلم الآلة يُمكّن الأتمتة."]

en_emb = labse.encode(en_texts)
ar_emb = labse.encode(ar_texts)

# تشابه عبر اللغات
sim_1_1 = labse.similarity(en_emb[0], ar_emb[0])  # "AI is future" ↔ "الذكاء الاصطناعي"
sim_1_2 = labse.similarity(en_emb[0], ar_emb[1])  # "AI is future" ↔ "تعلم الآلة"
print(f"EN[0] ↔ AR[0]: {sim_1_1:.3f}  (يجب أن يكون عالياً)")
print(f"EN[0] ↔ AR[1]: {sim_1_2:.3f}  (يجب أن يكون منخفضاً)")

# =====================================
# نموذج يحتاج trust_remote_code
# =====================================
print("\n=== نموذج متقدم ===")
advanced_emb = HuggingFaceEmbedder(
    model_name="nomic-ai/nomic-embed-text-v1",
    mode="local",
    trust_remote_code=True,   # مطلوب لبعض النماذج
)

# =====================================
# الإحصائيات
# =====================================
print("\n📊 إحصائيات:")
stats = local_emb.get_stats()
print(f"  إجمالي التحويلات: {stats['total_encodings']}")
print(f"  إجمالي النصوص: {stats['total_texts']}")
print(f"  إصابات الكاش: {stats['cache_hits']}")

model_info = local_emb.get_model_info()
print(f"\n📋 معلومات النموذج:")
print(f"  الاسم: {model_info['full_name']}")
print(f"  الأبعاد: {model_info['dimensions']}")
print(f"  الوصف: {model_info['description']}")
```
