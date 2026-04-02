# 📘 Reranker — مُعيد الترتيب

## نظرة عامة

`Reranker` يأخذ قائمة النتائج الأولية `(chunk, score)` القادمة من قاعدة البيانات المتجهة ويُعيد ترتيبها باستخدام درجة مركّبة تجمع بين: الدرجة الأصلية، تقييم نموذج اللغة، مكافأة الطول الأمثل، ومكافأة التنوع. كما يُزيل تلقائياً القطع المتشابهة نصياً قبل أي معالجة.

---

## الاستيراد

```python
from rag.core.reranker import Reranker
from rag.core.rag_config import RerankerConfig, RerankMode
```

---

## `RerankMode` — أوضاع إعادة الترتيب

| الوضع | الوصف |
|---|---|
| `HEURISTIC` | سريع، لا يحتاج LLM — يعتمد على التداخل النصي والطول والتنوع |
| `LLM` | دقيق، يستدعي LLM لتقييم كل قطعة (الاستدعاءات تتم بالتوازي) |
| `HYBRID` | مزيج: الأوزان الهيوريستية + تقييم LLM معاً |

---

## `RerankerConfig` — الإعدادات

```python
config = RerankerConfig(
    mode=RerankMode.HEURISTIC,   # الوضع الافتراضي
    top_k=None,                  # None = نفس عدد المدخلات
    original_score_weight=0.40,  # وزن الدرجة الأصلية
    llm_score_weight=0.40,       # وزن تقييم LLM
    diversity_weight=0.10,       # وزن مكافأة التنوع
    length_weight=0.10,          # وزن مكافأة الطول
    llm_eval_language="ar",      # لغة prompt التقييم ('ar' | 'en')
    ideal_min_words=30,          # الحد الأدنى للطول الأمثل (بالكلمات)
    ideal_max_words=300,         # الحد الأقصى للطول الأمثل
    dedup_enabled=True,          # تفعيل إزالة التكرار
    dedup_threshold=0.85,        # نسبة Jaccard فوقها تُعدّ القطعة مكررة
)
```

> **تنبيه:** مجموع الأوزان الأربعة يجب أن يساوي `1.0` وإلا يُرفع `ValueError`.

---

## `__init__`

```python
Reranker(
    config: Optional[RerankerConfig] = None,
    llm: Any = None
)
```

| المعامل | الوصف |
|---|---|
| `config` | إعدادات المُعيد (اختياري، يستخدم الافتراضي إذا لم يُحدَّد) |
| `llm` | نموذج اللغة (مطلوب فقط في وضعي `LLM` و`HYBRID`) |

> إذا طُلب وضع `LLM` أو `HYBRID` دون تمرير `llm`، يتراجع النظام تلقائياً إلى `HEURISTIC` مع تحذير في السجلات.

---

## الدوال الرئيسية

### `rerank`

```python
rerank(
    query: str,
    chunks: List[Tuple[Any, float]]
) -> List[Tuple[Any, float]]
```

الدالة الرئيسية لإعادة الترتيب.

| المعامل | الوصف |
|---|---|
| `query` | استعلام المستخدم |
| `chunks` | قائمة `(chunk, score)` من قاعدة البيانات |

**يُرجع:** نفس القائمة مُعاد ترتيبها تنازلياً حسب الدرجة المركّبة، مُقتطعة بـ `top_k` إذا حُدِّد.

```python
reranker = Reranker(config=RerankerConfig(mode=RerankMode.HEURISTIC))
ranked = reranker.rerank(query="ما هو تعلم الآلة؟", chunks=results)
for chunk, score in ranked:
    print(f"{score:.3f} | {chunk.text[:80]}")
```

---

### `clear_cache`

```python
clear_cache() -> None
```

يمسح ذاكرة التخزين المؤقت لنتائج LLM (`lru_cache`). مفيد عند تغيير المستندات أو الاستعلامات.

```python
reranker.clear_cache()
```

---

## آلية إزالة التكرار (Deduplication)

قبل إعادة الترتيب، يُحسب معامل **Jaccard** بين كل قطعتين. إذا تجاوزت النسبة `dedup_threshold` (الافتراضي 0.85)، تُحذف القطعة ذات الدرجة الأدنى. يُحافظ هذا على تنوع النتائج ويمنع تكرار المعلومات في السياق.

---

## كيفية حساب درجة الطول

تُعطي مكافأة الطول `1.0` للقطع التي يقع عدد كلماتها بين `ideal_min_words` و`ideal_max_words`. تنخفض المكافأة تدريجياً خارج هذا النطاق وصولاً إلى `0.0`.

---

## التكامل مع `RAGConfig`

```python
config = RAGConfig(
    enable_reranking=True,
    rerank_mode="hybrid",           # 'heuristic' | 'llm' | 'hybrid'
    rerank_top_k=3,                 # None = نفس top_k
    rerank_original_weight=0.40,
    rerank_llm_weight=0.40,
    rerank_diversity_weight=0.10,
    rerank_length_weight=0.10,
)
```

`RAGSystem` ينشئ `Reranker` داخلياً من هذه الإعدادات ويستدعيه تلقائياً داخل `retrieve()`.

---

## مثال مكتمل

```python
from rag.core.reranker import Reranker
from rag.core.rag_config import RerankerConfig, RerankMode

# إعداد المُعيد في الوضع الهيوريستي
config = RerankerConfig(
    mode=RerankMode.HEURISTIC,
    top_k=3,
    dedup_enabled=True,
    dedup_threshold=0.85,
)
reranker = Reranker(config=config)

# إعادة الترتيب
ranked = reranker.rerank(query="سؤال المستخدم", chunks=raw_results)
print(ranked[0])  # أعلى نتيجة بعد إعادة الترتيب

# مع LLM (وضع hybrid)
from my_llm import MyLLM
llm = MyLLM()
config_hybrid = RerankerConfig(mode=RerankMode.HYBRID)
reranker_hybrid = Reranker(config=config_hybrid, llm=llm)
ranked_hybrid = reranker_hybrid.rerank("سؤال المستخدم", raw_results)
```

---

## ملاحظات أداء

- في وضع `LLM` و`HYBRID` تُستدعى نتائج LLM بالتوازي (حتى 6 خيوط) لتسريع المعالجة.
- نتائج LLM مُخزَّنة مؤقتاً بـ `lru_cache(maxsize=512)` — نفس زوج `(query, text)` لا يُستدعى مرتين.
- يقتطع النصوص إلى 150 كلمة قبل إرسالها لـ LLM للحد من التكلفة والزمن.
