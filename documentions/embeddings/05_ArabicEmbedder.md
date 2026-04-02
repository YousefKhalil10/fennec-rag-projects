# 🌙 ArabicEmbedder — المحوّل المتخصص للعربية

## نظرة عامة

`ArabicEmbedder` محوّل مُصمَّم خصيصاً للنصوص العربية. يُضيف **معالجة مسبقة متقدمة** (تطبيع الهمزات، إزالة التشكيل، توحيد التاء المربوطة) قبل التضمين، مما يُحسّن جودة النتائج بشكل ملحوظ. يدعم نماذج متعددة محلية كلياً بدون API Key.

---

## التثبيت

```bash
pip install sentence-transformers torch
```

```python
from embeddings import ArabicEmbedder
```

---

## النماذج المدعومة

| المفتاح | النموذج الكامل | الأبعاد | الأفضل لـ |
|---|---|---|---|
| `multilingual` | `paraphrase-multilingual-mpnet-base-v2` | 768 | الجودة العالية العامة |
| `multilingual-mini` | `paraphrase-multilingual-MiniLM-L12-v2` | 384 | السرعة والكفاءة |
| `labse` | `sentence-transformers/LaBSE` | 768 | البحث عربي-إنجليزي |
| `arabert` | `aubmindlab/bert-base-arabertv2` | 768 | المهام العربية فقط |
| `camelbert` | `CAMeL-Lab/bert-base-arabic-camelbert-msa` | 768 | العربية الفصحى الرسمية |

---

## مستويات التطبيع — `normalization_level`

| المستوى | ما يُطبَّق |
|---|---|
| `'minimal'` | إزالة التشكيل فقط |
| `'standard'` | إزالة التشكيل + توحيد الهمزات + تطبيع الألف المقصورة والتاء المربوطة |
| `'aggressive'` | كل ما سبق + إزالة الكلمات المكررة والتطويل |

---

## الدوال الرئيسية

### `__init__`

```python
ArabicEmbedder(
    model_name=None,
    device=None,
    cache_dir=None,
    normalize_embeddings=True,
    batch_size=32,
    enable_preprocessing=True,
    max_seq_length=512,
    normalization_level='standard',
    track_processing_stats=True,
    auto_download=True,
    trust_remote_code=False
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `model_name` | `str` | مفتاح من الجدول أعلاه أو اسم نموذج كامل (افتراضي: `'multilingual'`) |
| `cache_dir` | `str` | مجلد تخزين النماذج المُحمَّلة |
| `enable_preprocessing` | `bool` | تفعيل التطبيع العربي قبل التضمين |
| `normalization_level` | `str` | مستوى التطبيع: `'minimal'`، `'standard'`، `'aggressive'` |
| `track_processing_stats` | `bool` | تتبع إحصائيات معالجة النصوص |
| `auto_download` | `bool` | تحميل النموذج تلقائياً إن لم يكن موجوداً |
| `trust_remote_code` | `bool` | السماح بتنفيذ كود النموذج |

---

### `encode`

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True,
    batch_size: Optional[int] = None,
    return_valid_indices: bool = False,
    skip_preprocessing: bool = False
) -> np.ndarray
```

| المعامل | النوع | الوصف |
|---|---|---|
| `return_valid_indices` | `bool` | إرجاع فهارس النصوص الصالحة (لتتبع النصوص المُهمَلة) |
| `skip_preprocessing` | `bool` | تخطي التطبيع العربي لهذا الاستدعاء |

---

### `save_embeddings` / `load_embeddings`

```python
save_embeddings(
    embeddings: np.ndarray,
    texts: List[str],
    save_path: str,
    metadata: Optional[Dict] = None
) -> None

load_embeddings(save_path: str) -> Tuple[np.ndarray, List[str], Dict]
```

**الوصف:** حفظ وتحميل المتجهات على القرص لإعادة الاستخدام.

---

### `compute_similarity`

```python
compute_similarity(
    text1: Union[str, np.ndarray],
    text2: Union[str, np.ndarray]
) -> float
```

**الوصف:** حساب التشابه الدلالي بين نصين.

---

### `find_most_similar`

```python
find_most_similar(
    query: str,
    texts: List[str],
    top_k: int = 5
) -> List[Tuple[int, str, float]]
```

**الوصف:** إيجاد أكثر النصوص شبهاً بالاستعلام.

**Return:** قائمة من `(index, text, score)`

---

### `benchmark`

```python
benchmark(
    num_texts: int = 100,
    text_length: int = 100
) -> Dict[str, Any]
```

**الوصف:** قياس أداء النموذج (الوقت + السرعة).

**Return:**
```python
{
    "num_texts": 100,
    "total_time": 2.3,
    "texts_per_second": 43.5,
    "ms_per_text": 23.0,
    "embedding_dim": 768
}
```

---

### `get_processing_stats`

```python
get_processing_stats() -> Dict[str, Any]
```

**الوصف:** إحصائيات تطبيع النصوص العربية.

**Return:**
```python
{
    "total_texts": 500,
    "normalized_texts": 480,
    "normalization_rate": 0.96,
    "avg_normalization_time_ms": 0.8,
    "removed_diacritics": 320,
    "normalized_hamzas": 145
}
```

---

### `list_recommended_models`

```python
list_recommended_models() -> None
```

**الوصف:** طباعة جدول بجميع النماذج الموصى بها ومواصفاتها.

---

### `reset_stats`

```python
reset_stats() -> None
```

---

## مثال عملي كامل

```python
from embeddings import ArabicEmbedder

# ============================================================
# 1. عرض النماذج المتاحة
# ============================================================
print("📋 النماذج المتاحة:")
models = ArabicEmbedder.list_recommended_models()
for key, info in models.items():
    print(f"  [{key}] {info['name']} — {info['description_ar']}")


# ============================================================
# 2. إنشاء محوّل بالنموذج متعدد اللغات
# ============================================================
embedder = ArabicEmbedder(
    model_name="multilingual",        # أفضل للاستخدام العام
    enable_preprocessing=True,
    normalization_level="standard",   # تطبيع الهمزات والتشكيل
    batch_size=32,
    track_processing_stats=True,
    cache_dir="./models_cache",       # حفظ النماذج محلياً
)


# ============================================================
# 3. التحقق من الاتصال
# ============================================================
status = embedder.validate_connection(detailed=True)
print(f"\n✅ النموذج : {status['model_name']}")
print(f"   الأبعاد  : {status['embedding_dim']}")
print(f"   الجهاز   : {status['device']}")
print(f"   الوقت    : {status['encoding_time']}")


# ============================================================
# 4. تأثير التطبيع — مُشكَّل مقابل غير مُشكَّل
# ============================================================
texts_diacritics = [
    "الذَّكاءُ الاصطناعيُّ يُغيِّرُ العالَمَ",   # مُشكَّل
    "الذكاء الاصطناعي يغير العالم",               # بدون تشكيل
    "إنَّ الإِنسانَ لَفِي خُسرٍ",                # قرآني مشكول
    "ان الانسان لفي خسر",                         # بدون تشكيل
]

embeddings_d = embedder.encode(texts_diacritics)
print(f"\n📊 شكل المتجهات: {embeddings_d.shape}")

sim_01 = embedder.compute_similarity(texts_diacritics[0], texts_diacritics[1])
sim_23 = embedder.compute_similarity(texts_diacritics[2], texts_diacritics[3])
print(f"  تشابه (مشكول/غير مشكول) 0,1 : {sim_01:.3f}")
print(f"  تشابه (مشكول/غير مشكول) 2,3 : {sim_23:.3f}")


# ============================================================
# 5. تضمين نصوص الذكاء الاصطناعي
# ============================================================
ai_texts = [
    "الذكاء الاصطناعي مجال علمي يسعى لمحاكاة الذكاء البشري في الحاسوب.",
    "تعلم الآلة يُمكّن الأنظمة من التعلم التلقائي من البيانات دون برمجة صريحة.",
    "الشبكات العصبية العميقة مستوحاة من تركيب الدماغ البشري وطريقة عمله.",
    "معالجة اللغة الطبيعية تُتيح للآلات فهم النصوص والكلام البشري وتوليدهما.",
    "الرؤية الحاسوبية تُمكّن الحواسيب من تحليل الصور والفيديو وفهم محتواها.",
]

ai_embeddings = embedder.encode(ai_texts, show_progress_bar=True)
print(f"\n✅ شكل متجهات الذكاء الاصطناعي: {ai_embeddings.shape}")


# ============================================================
# 6. البحث عن الأكثر تشابهاً
# ============================================================
query = "كيف يتعلم الكمبيوتر من البيانات؟"
similar = embedder.find_most_similar(query, ai_texts, top_k=3)

print(f"\n🔍 أقرب 3 نصوص لـ: '{query}'")
for idx, text, score in similar:
    print(f"  [{idx}] {score:.3f}: {text[:60]}...")


# ============================================================
# 7. حفظ وتحميل المتجهات
#    save_embeddings(texts, filepath) — بتعمل encode داخلياً
# ============================================================
embedder.save_embeddings(
    texts=ai_texts,
    filepath="./arabic_embeddings",   # .npz بتتضاف تلقائياً
    save_texts=True,
    save_metadata=True,
)
print("\n💾 تم الحفظ في: arabic_embeddings.npz")

# تحميل الـ embeddings فقط
loaded_embeddings = embedder.load_embeddings("./arabic_embeddings")
print(f"📂 embeddings فقط  : {loaded_embeddings.shape}")

# تحميل الـ embeddings + النصوص
loaded_embeddings, loaded_texts = embedder.load_embeddings(
    "./arabic_embeddings",
    load_texts=True,
)
print(f"📂 مع النصوص       : {loaded_embeddings.shape} | {len(loaded_texts)} نص")

# تحميل الكل — embeddings + نصوص + metadata
loaded_embeddings, loaded_texts, metadata = embedder.load_embeddings(
    "./arabic_embeddings",
    load_texts=True,
    load_metadata=True,
)
print(f"📂 مع الـ metadata  : نموذج={metadata['model_name']} | تاريخ={metadata['timestamp']}")


# ============================================================
# 8. مستويات التطبيع المختلفة
# ============================================================
test_text = "إنَّ الإِنسَانَ لَفِي خُسرٍ"
print(f"\n🔬 مستويات التطبيع على: '{test_text}'")

for level in ['minimal', 'standard', 'aggressive']:
    mini_embedder = ArabicEmbedder(
        model_name="multilingual-mini",
        normalization_level=level,
    )
    emb = mini_embedder.encode(test_text)
    print(f"  [{level:10s}]: shape={emb.shape}")


# ============================================================
# 9. تخطي المعالجة المسبقة
# ============================================================
raw_embeddings = embedder.encode(
    ai_texts,
    skip_preprocessing=True,   # تضمين مباشر بدون تطبيع عربي
)
print(f"\n⚡ بدون معالجة مسبقة: {raw_embeddings.shape}")


# ============================================================
# 10. قياس الأداء — benchmark
#     sample_texts: النصوص التجريبية (اختياري)
#     num_iterations: عدد مرات التكرار
#     warmup_iterations: تكرارات الإحماء
# ============================================================
print("\n⏱️  قياس الأداء...")
benchmark = embedder.benchmark(
    sample_texts=ai_texts,   # لو None بيستخدم نصوص افتراضية داخلياً
    num_iterations=5,
    warmup_iterations=1,
)
print(f"  نصوص/ثانية  : {benchmark['texts_per_second']:.1f}")
print(f"  متوسط الوقت : {benchmark['avg_time']:.4f}s")
print(f"  أقل وقت     : {benchmark['min_time']:.4f}s")
print(f"  أعلى وقت    : {benchmark['max_time']:.4f}s")
print(f"  الجهاز      : {benchmark['device']}")


# ============================================================
# 11. إحصائيات المعالجة العربية
# ============================================================
proc_stats = embedder.get_processing_stats()
print(f"\n📊 إحصائيات التطبيع:")
print(f"  نصوص مُعالجة   : {proc_stats['normalized_texts']}/{proc_stats['total_texts']}")
print(f"  همزات مُطبَّعة  : {proc_stats['normalized_hamzas']}")
print(f"  تشكيل مُزال    : {proc_stats['removed_diacritics']}")
print(f"  متوسط وقت/نص  : {proc_stats['avg_normalization_time_ms']:.2f}ms")


# ============================================================
# 12. نموذج متخصص للعربية الفصحى
# ============================================================
formal_embedder = ArabicEmbedder(
    model_name="camelbert",           # مصمم للعربية الفصحى
    normalization_level="aggressive",
    enable_preprocessing=True,
)

formal_texts = [
    "إن الله لا يخفى عليه شيء في الأرض ولا في السماء",
    "يَا أَيُّهَا النَّاسُ اتَّقُوا رَبَّكُمُ",
]
formal_emb = formal_embedder.encode(formal_texts)
print(f"\n📜 نصوص فصيحة: {formal_emb.shape}")

sim_formal = formal_embedder.compute_similarity(formal_texts[0], formal_texts[1])
print(f"   تشابه النصين  : {sim_formal:.3f}")


# ============================================================
# 13. استخدام context manager للتنظيف التلقائي
# ============================================================
print("\n🔄 مثال بـ context manager:")
with ArabicEmbedder(model_name="multilingual-mini") as ctx_embedder:
    emb = ctx_embedder.encode("الذكاء الاصطناعي")
    print(f"  shape: {emb.shape}")
# الموارد بتتنظف تلقائياً عند الخروج
```
