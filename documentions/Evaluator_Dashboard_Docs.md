
> نظام تقييم ذكي لأنظمة RAG — يقيس جودة الاسترجاع والتوليد، يكشف الهلوسة تلقائياً، ويُولّد لوحة تحكم HTML تفاعلية.

---


## 1. `RetrievalMetrics`

**النوع:** `@dataclass`  
**الوصف:** يحمل نتائج قياس جودة الاسترجاع لسؤال واحد. يُنشأ تلقائياً داخل `RAGEvaluator` ولا يحتاج إنشاءً يدوياً.

### الخصائص

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `query` | `str` | نص الاستعلام الذي جرى تقييمه |
| `num_chunks` | `int` | عدد القطع التي أرجعها نظام RAG |
| `top_score` | `float` | أعلى درجة تشابه من بين كل القطع (0.0 → 1.0) |
| `avg_score` | `float` | متوسط درجات التشابه لجميع القطع |
| `min_score` | `float` | أدنى درجة تشابه |
| `score_variance` | `float` | تباين الدرجات — يقيس مدى تجانس النتائج |
| `has_results` | `bool` | هل أرجع النظام أي قطع؟ |
| `latency_ms` | `float` | زمن استدعاء `retrieve()` بالمللي ثانية |

### الخصائص المحسوبة

#### `quality_label` → `str`

**الوصف:** يُحوّل `top_score` إلى تصنيف نصي للعرض.

| نطاق `top_score` | التصنيف |
|----------------|---------|
| `>= 0.80` | `"ممتاز"` |
| `>= 0.60` | `"جيد"` |
| `>= 0.40` | `"مقبول"` |
| `< 0.40` | `"ضعيف"` |

---
```python
# مثال
metrics = RetrievalMetrics(
    query="ما هو الذكاء الاصطناعي؟",
    num_chunks=5, top_score=0.85,
    avg_score=0.71, min_score=0.52,
    score_variance=0.018,
    has_results=True, latency_ms=120.5
)
print(metrics.quality_label)   # "ممتاز"
print(metrics.has_results)     # True
```

---

## 2. `GenerationMetrics`

**النوع:** `@dataclass`  
**الوصف:** يحمل نتائج قياس جودة التوليد لسؤال واحد — الدرجات الثلاث، نتيجة فحص الهلوسة، وزمن التوليد.

### الخصائص

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `query` | `str` | نص السؤال |
| `answer` | `str` | الإجابة التي ولّدها النظام |
| `answer_length` | `int` | طول الإجابة بالحروف |
| `latency_ms` | `float` | زمن استدعاء `generate()` بالمللي ثانية |
| `hallucination` | `HallucinationCheck` | نتيجة فحص `HallucinationGuard` |
| `faithfulness_score` | `float` | مدى التزام الإجابة بالسياق المسترجع (0→1) |
| `relevance_score` | `float` | مدى صلة الإجابة بالسؤال (0→1) |
| `completeness_score` | `float` | مدى اكتمال الإجابة (0→1) |

### الخصائص المحسوبة

#### `overall_score` → `float`

**الوصف:** الدرجة الإجمالية المُرجَّحة من الدرجات الثلاث.

**الصيغة:**
```
overall = faithfulness × 0.40 + relevance × 0.35 + completeness × 0.25
```

---

#### `grade` → `str`

**الوصف:** التقدير الحرفي بناءً على `overall_score`.

| نطاق `overall_score` | التقدير |
|--------------------|---------|
| `>= 0.85` | `"A"` |
| `>= 0.70` | `"B"` |
| `>= 0.55` | `"C"` |
| `>= 0.40` | `"D"` |
| `< 0.40` | `"F"` |

```python
# مثال
gen = GenerationMetrics(
    query="ما هو RAG؟",
    answer="RAG يجمع بين البحث والتوليد...",
    answer_length=250,
    latency_ms=450.0,
    hallucination=hall_check,
    faithfulness_score=0.88,
    relevance_score=0.75,
    completeness_score=0.70,
)
# overall = 0.40×0.88 + 0.35×0.75 + 0.25×0.70 = 0.789
print(gen.overall_score)   # 0.789
print(gen.grade)           # "B"
```

---

## 3. `EvalResult`

**النوع:** `@dataclass`  
**الوصف:** يجمع نتيجة تقييم سؤال واحد كاملاً — الاسترجاع والتوليد في كيان واحد.

### الخصائص

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `query` | `str` | السؤال المُقيَّم |
| `answer` | `str` | الإجابة المُولَّدة |
| `retrieval` | `RetrievalMetrics` | مقاييس الاسترجاع |
| `generation` | `GenerationMetrics` | مقاييس التوليد |
| `timestamp` | `str` | وقت التقييم بتنسيق ISO 8601 (يُعيَّن تلقائياً) |

### الدوال

#### `to_dict()` → `Dict`

**الوصف:** يُحوّل النتيجة إلى قاموس JSON-قابل للتسلسل. نص الإجابة مقطوع عند **300 حرف** في الإخراج.

**لا تأخذ باراميترات.**

**Return:**
```python
{
    "query":     "السؤال...",
    "answer":    "الإجابة (max 300 حرف)...",
    "timestamp": "2025-03-15T10:30:00.123456",
    "retrieval": {
        "num_chunks":  5,
        "top_score":   0.853,
        "avg_score":   0.712,
        "latency_ms":  120.1,
        "quality":     "ممتاز"
    },
    "generation": {
        "grade":              "B",
        "overall_score":      0.789,
        "faithfulness":       0.880,
        "relevance":          0.750,
        "completeness":       0.700,
        "latency_ms":         445.3,
        "is_hallucination":   False,
        "confidence":         0.912,
        "hallucination_type": None,
        "recommendation":     None
    }
}
```

```python
# مثال
result = evaluator.eval_single("ما هو RAG؟")
d = result.to_dict()
print(d["generation"]["grade"])     # "B"
print(d["retrieval"]["quality"])    # "ممتاز"
```

---

## 4. `EvalReport`

**النوع:** `@dataclass`  
**الوصف:** تقرير شامل لجلسة تقييم كاملة. يجمع كل نتائج `EvalResult` ويحسب الإحصائيات المجمّعة تلقائياً عبر properties.

### الخصائص

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `results` | `List[EvalResult]` | قائمة نتائج كل سؤال |
| `rag_stats` | `Dict` | إحصائيات نظام RAG المُقيَّم (من `rag.get_stats()`) |
| `created_at` | `str` | وقت إنشاء التقرير ISO 8601 (يُعيَّن تلقائياً) |

### الخصائص المحسوبة (Properties)

#### `total` → `int`
**الوصف:** عدد الأسئلة المُقيَّمة.
```python
print(report.total)  # 20
```

---

#### `avg_retrieval_score` → `float`
**الوصف:** متوسط `top_score` لجميع نتائج الاسترجاع.
```python
print(f"{report.avg_retrieval_score:.1%}")  # "78.3%"
```

---

#### `avg_generation_score` → `float`
**الوصف:** متوسط `overall_score` لجميع نتائج التوليد.
```python
print(f"{report.avg_generation_score:.1%}")  # "74.1%"
```

---

#### `hallucination_rate` → `float`
**الوصف:** نسبة الأسئلة التي اكتُشفت فيها هلوسة (0.0 → 1.0).
```python
print(f"{report.hallucination_rate:.1%}")  # "15.0%"
```

---

#### `avg_latency_ms` → `float`
**الوصف:** متوسط إجمالي زمن الاستجابة (استرجاع + توليد) بالمللي ثانية.
```python
print(f"{report.avg_latency_ms:.0f}ms")  # "580ms"
```

---

#### `grade_distribution` → `Dict[str, int]`
**الوصف:** توزيع التقديرات — كم سؤال حصل على كل تقدير.
```python
print(report.grade_distribution)
# {"A": 8, "B": 7, "C": 3, "D": 1, "F": 1}
```

---

#### `system_health` → `str`
**الوصف:** تقييم الصحة العامة للنظام بناءً على ثلاثة معايير مجتمعة.

| الحالة | المعايير |
|--------|---------|
| `"🟢 ممتاز"` | توليد ≥ 80% **و** هلوسة ≤ 10% **و** استرجاع ≥ 70% |
| `"🟡 جيد"` | توليد ≥ 65% **و** هلوسة ≤ 20% **و** استرجاع ≥ 55% |
| `"🟠 مقبول — يحتاج تحسين"` | توليد ≥ 50% **و** هلوسة ≤ 35% |
| `"🔴 ضعيف — يحتاج مراجعة"` | أقل من الشروط أعلاه |

```python
print(report.system_health)  # "🟢 ممتاز"
```

---

### الدوال

#### `to_dict()` → `Dict`

**الوصف:** يُحوّل التقرير الكامل إلى قاموس JSON-قابل للتسلسل.

**لا تأخذ باراميترات.**

**Return:**
```python
{
    "created_at":            "2025-03-15T10:30:00",
    "total_questions":       20,
    "system_health":         "🟢 ممتاز",
    "avg_retrieval_score":   0.783,
    "avg_generation_score":  0.741,
    "hallucination_rate":    0.150,
    "avg_latency_ms":        580.0,
    "grade_distribution":    {"A": 8, "B": 7, "C": 3, "D": 1, "F": 1},
    "rag_stats":             {...},
    "results":               [...]
}
```

---

#### `save(path="eval_report.json")`

**الوصف:** يحفظ التقرير كملف JSON مُنسَّق بمسافة بادئة.

| الباراميتر | النوع | الافتراضي | الوصف |
|-----------|------|-----------|-------|
| `path` | `str` | `"eval_report.json"` | مسار ملف الحفظ |

**Return:** `None`

```python
report.save("reports/eval_2025_03_15.json")
# 💾 تم حفظ التقرير في: reports/eval_2025_03_15.json
```

---

## 5. `RAGEvaluator`

**الوصف:** الكلاس الرئيسي للتقييم. يُشغّل كل سؤال عبر نظام RAG، يقيس جودة الاسترجاع والتوليد، يكشف الهلوسة بـ `HallucinationGuard`، ويسجّل المقاييس في `MetricsCollector`.

**المتطلبات من نظام RAG:**
- `rag.retrieve(question)` → `List[Tuple[chunk, float]]`
- `rag.generate(question)` → `str`
- `rag.get_stats()` → `Dict` *(اختياري)*

---

### `__init__(rag, hallucination_threshold=0.65, verbose=True)`

**الوصف:** يُهيئ المُقيّم ويُنشئ `HallucinationGuard` و`MetricsCollector` داخلياً.

| الباراميتر | النوع | الافتراضي | الوصف |
|-----------|------|-----------|-------|
| `rag` | `Any` | — | نظام RAG المُراد تقييمه **(مطلوب)** |
| `hallucination_threshold` | `float` | `0.65` | عتبة الثقة لاعتبار الإجابة هلوسة — كلما زادت كان الفحص أكثر صرامة |
| `verbose` | `bool` | `True` | طباعة تقدم التقييم أثناء التنفيذ |

```python
from evaluator import RAGEvaluator

evaluator = RAGEvaluator(
    rag=my_rag_system,
    hallucination_threshold=0.70,  # أكثر صرامة
    verbose=True
)
```

---

### الدوال العامة

#### `evaluate(questions, reference_answers=None)` → `EvalReport`

**الوصف:** الدالة الرئيسية — تُقيّم نظام RAG على قائمة أسئلة كاملة وتُرجع تقريراً شاملاً.

لكل سؤال تُنفّذ ثلاث خطوات تلقائياً:
1. قياس الاسترجاع عبر `rag.retrieve()`
2. قياس التوليد عبر `rag.generate()` + `HallucinationGuard`
3. تسجيل المقاييس في `MetricsCollector`

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `questions` | `List[str]` | قائمة الأسئلة المراد تقييمها **(مطلوب)** |
| `reference_answers` | `Optional[List[str]]` | إجابات مرجعية اختيارية — إن وُجدت تُحسَب `completeness_score` بـ ROUGE-1 مبسط بدلاً من التقدير |

**⚠️ ملاحظة:** إن مُرِّرت `reference_answers` يجب أن يكون طولها مساوياً لطول `questions`.

**Return:** `EvalReport`

```python
questions = [
    "ما هو الذكاء الاصطناعي؟",
    "اشرح مفهوم RAG",
    "ما الفرق بين BM25 والبحث الدلالي؟"
]

# بدون مراجع
report = evaluator.evaluate(questions)

# مع مراجع — أدق في حساب completeness
references = [
    "الذكاء الاصطناعي هو محاكاة الذكاء البشري...",
    "RAG يجمع بين البحث وتوليد النصوص...",
    "BM25 يعتمد الكلمات بينما الدلالي يعتمد المعنى..."
]
report = evaluator.evaluate(questions, reference_answers=references)

print(report.system_health)           # "🟢 ممتاز"
print(f"{report.hallucination_rate:.0%}")  # "10%"
```

---

#### `eval_single(question, reference=None)` → `EvalResult`

**الوصف:** يُقيّم سؤالاً واحداً فقط — مفيد للاختبار السريع أو التكامل مع أنظمة خارجية.

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `question` | `str` | السؤال المراد تقييمه **(مطلوب)** |
| `reference` | `Optional[str]` | إجابة مرجعية اختيارية |

**Return:** `EvalResult`

```python
result = evaluator.eval_single(
    question="كيف يعمل نظام RAG؟",
    reference="RAG يسترجع المستندات ثم يولّد إجابة..."
)

print(result.generation.grade)               # "A"
print(result.retrieval.quality_label)        # "ممتاز"
print(result.generation.faithfulness_score)  # 0.88
```

---

#### `print_report(report)`

**الوصف:** يطبع تقريراً تفصيلياً كاملاً في الـ terminal — الإحصائيات المجمّعة + تفاصيل كل سؤال مع علامات الهلوسة.

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `report` | `EvalReport` | التقرير المُراد طباعته |

**Return:** `None`

```python
evaluator.print_report(report)
# ════════════════════════════════════════════════════════════
#   📊  تقرير التقييم الشامل
# ════════════════════════════════════════════════════════════
#   الصحة العامة      : 🟢 ممتاز
#   الأسئلة المُقيَّمة : 20
#   متوسط الاسترجاع   : 78.3%
#   متوسط التوليد     : 74.1%
#   نسبة الهلوسة      : 15.0%
#   متوسط الوقت       : 580 ms
#   ...
```

---

#### `print_summary(report)`

**الوصف:** يطبع ملخصاً مختصراً في سطرين فقط بدلاً من التقرير الكامل.

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `report` | `EvalReport` | التقرير |

**Return:** `None`

```python
evaluator.print_summary(report)
# ✅  اكتمل التقييم
# الصحة: 🟢 ممتاز
# التوليد: 74.1%  |  الاسترجاع: 78.3%  |  الهلوسة: 15.0%
```

---

#### `get_guard_statistics()` → `Dict`

**الوصف:** يُرجع إحصائيات `HallucinationGuard` — عدد الفحوصات، معدل الكشف، الأنواع الأكثر شيوعاً.

**لا تأخذ باراميترات.**

```python
stats = evaluator.get_guard_statistics()
print(stats)
# {"total_checks": 20, "hallucinations_found": 3, ...}
```

---

#### `get_metrics_summary()` → `Dict`

**الوصف:** يُرجع ملخص `MetricsCollector` — العدادات وآخر قيمة لكل مقياس مسجَّل.

**لا تأخذ باراميترات.**

**Return:**
```python
{
    "counters": {
        "eval.total_questions":         20,
        "eval.hallucinations_detected":  3
    },
    "gauges": {
        "eval.retrieval.top_score":       0.82,
        "eval.retrieval.num_chunks":      5.0,
        "eval.retrieval.latency_ms":      115.3,
        "eval.generation.faithfulness":   0.79,
        "eval.generation.relevance":      0.71,
        "eval.generation.overall":        0.74,
        "eval.generation.latency_ms":     460.2
    }
}
```

```python
metrics = evaluator.get_metrics_summary()
print(metrics["counters"]["eval.total_questions"])    # 20
print(metrics["gauges"]["eval.generation.overall"])   # 0.74
```

---

### الدوال الداخلية (Private)

#### `_eval_single(question, reference)` → `EvalResult`
**الوصف:** المحرك الداخلي — يُنسّق استدعاء `_measure_retrieval` ثم `_measure_generation` ثم `_record_metrics`.

---

#### `_measure_retrieval(question)` → `RetrievalMetrics`
**الوصف:** يستدعي `rag.retrieve()` ويقيس الوقت والدرجات ويُنشئ `RetrievalMetrics`.

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `question` | `str` | نص السؤال |

---

#### `_measure_generation(question, ret, reference)` → `GenerationMetrics`
**الوصف:** يستدعي `rag.generate()` ثم يبني `GroundingContext` ويُشغّل `HallucinationGuard` ويحسب الدرجات الثلاث.

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `question` | `str` | نص السؤال |
| `ret` | `RetrievalMetrics` | مقاييس الاسترجاع (محجوزة للتوسع) |
| `reference` | `Optional[str]` | إجابة مرجعية اختيارية |

---

#### `_score_faithfulness(answer, context_chunks)` → `float`

**الوصف:** يقيس مدى التزام الإجابة بالسياق المسترجع.

**الخوارزمية:**
```
تداخل_الكلمات = |كلمات_الإجابة ∩ كلمات_السياق| / |كلمات_الإجابة|
score = min(1.0, تداخل_الكلمات × 1.4)
```
- تُستثنى الكلمات بطول ≤ 3 حروف
- معامل `1.4` يُطبّع المنحنى للتقليل من عقوبة الكلمات غير الموجودة في السياق

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `answer` | `str` | نص الإجابة |
| `context_chunks` | `List[str]` | قائمة نصوص القطع المسترجعة |

**يُرجع:** `float` (0.0 → 1.0) — يُرجع `0.5` إذا كانت المدخلات فارغة

---

#### `_score_relevance(answer, question)` → `float`

**الوصف:** يقيس مدى صلة الإجابة بالسؤال.

**الخوارزمية:**
```
تطابق   = |كلمات_السؤال ∩ كلمات_الإجابة| / |كلمات_السؤال|
طول     = min(1.0, len(answer) / 80)
score   = تطابق × 0.65 + طول × 0.35
```
- عقوبة الطول تُعاقب الإجابات القصيرة جداً (< 80 حرف)

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `answer` | `str` | نص الإجابة |
| `question` | `str` | نص السؤال |

**Return:** `float` (0.0 → 1.0)

---

#### `_score_completeness(answer, question, reference)` → `float`

**الوصف:** يقيس مدى اكتمال الإجابة بطريقتين:

**مع مرجع (ROUGE-1 مبسط):**
```
score = |كلمات_الإجابة ∩ كلمات_المرجع| / |كلمات_المرجع|
```

**بدون مرجع (تقدير):**
```
طول      = min(1.0, عدد_الكلمات / 60)
تنوع     = min(1.0, كلمات_فريدة / مجموع_الكلمات × 2)
score    = طول × 0.60 + تنوع × 0.40
```

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `answer` | `str` | نص الإجابة |
| `question` | `str` | نص السؤال (محجوز للتوسع) |
| `reference` | `Optional[str]` | إجابة مرجعية — إن وُجدت تُعطي دقة أعلى |

**Return:** `float` (0.0 → 1.0)

---

#### `_record_metrics(q, ret, gen)`

**الوصف:** يسجّل جميع المقاييس في `MetricsCollector`.

**المقاييس المسجَّلة:**

| المقياس | النوع | الوصف |
|---------|------|-------|
| `eval.total_questions` | counter | يزيد بـ 1 مع كل سؤال |
| `eval.retrieval.top_score` | gauge | أعلى درجة استرجاع |
| `eval.retrieval.num_chunks` | gauge | عدد القطع |
| `eval.retrieval.latency_ms` | gauge | زمن الاسترجاع |
| `eval.generation.faithfulness` | gauge | درجة الأمانة |
| `eval.generation.relevance` | gauge | درجة الصلة |
| `eval.generation.overall` | gauge | الدرجة الإجمالية |
| `eval.generation.latency_ms` | gauge | زمن التوليد |
| `eval.hallucinations_detected` | counter | يزيد فقط عند اكتشاف هلوسة |

---

#### `_print_single_line(r)`
**الوصف:** يطبع سطراً واحداً موجزاً لنتيجة سؤال أثناء تقدم `evaluate()`.

```
✅  Grade=B  Faith=0.88  Rel=0.75  Hall=0.91  Ret=0.85  ⏱570ms
```

---

#### `_variance(values)` → `float` *(static)*

**الوصف:** يحسب التباين لقائمة أرقام.

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `values` | `List[float]` | قائمة الأرقام |

**Return:** `float` — التباين، أو `0.0` إذا كانت القائمة أقل من عنصرين

```python
var = RAGEvaluator._variance([0.8, 0.7, 0.9, 0.75])
print(var)  # 0.00563
```

---

## 6. `generate_dashboard()`

**الوصف:** يُولّد ملف HTML تفاعلي كامل من `EvalReport` — لوحة تحكم احترافية بتصميم داكن تعرض KPIs وتوزيع الدرجات وجدولاً تفصيلياً لكل سؤال.

### `generate_dashboard(report, output_path="rag_dashboard.html")` → `str`

| الباراميتر | النوع | الافتراضي | الوصف |
|-----------|------|-----------|-------|
| `report` | `EvalReport` | — | التقرير المُراد عرضه **(مطلوب)** |
| `output_path` | `str` | `"rag_dashboard.html"` | مسار حفظ ملف HTML |

**Return:** `str` — المسار الكامل للملف المحفوظ

**ما تعرضه اللوحة:**

| القسم | الوصف |
|-------|-------|
| **Health Banner** | شريط ملوّن يُبيّن صحة النظام (🟢/🟡/🟠/🔴) |
| **5 بطاقات KPI** | أسئلة مُقيَّمة · متوسط التوليد · متوسط الاسترجاع · نسبة الهلوسة · متوسط الوقت |
| **Grade Pills** | توزيع A→F بشكل بصري مع عدد الأسئلة |
| **Results Table** | جدول تفصيلي لكل سؤال بأشرطة تقدم ملوّنة وزر "عرض الإجابة" |

```python
from evaluator import RAGEvaluator
from evaluator import generate_dashboard

# 1. تقييم النظام
evaluator = RAGEvaluator(rag=my_rag)
report = evaluator.evaluate(questions)

# 2. توليد اللوحة
path = generate_dashboard(report, output_path="my_eval.html")
# 🌐 Dashboard محفوظ في: my_eval.html

# 3. فتح في المتصفح
import webbrowser
webbrowser.open(path)
```

---

## 7. `_bar()`

**الوصف:** دالة داخلية تُولّد HTML لشريط تقدم مُلوَّن مع نسبة مئوية.

### `_bar(score, color)` → `str`

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `score` | `float` | الدرجة من 0.0 إلى 1.0 |
| `color` | `str` | اسم اللون: `"green"` · `"blue"` · `"amber"` · `"red"` |

**يُرجع:** `str` — HTML snippet يحتوي شريط التقدم والنسبة

```python
# مثال داخلي (لا تُستدعى مباشرة)
html = _bar(0.85, "green")
# ينتج: <div class="score-bar-wrap">...<span>85%</span></div>
```

---

## 8. `_tag_hall()`

**الوصف:** دالة داخلية تُولّد تاج HTML مُلوَّن يُبيّن نتيجة فحص الهلوسة.

### `_tag_hall(is_hall, conf)` → `str`

| الباراميتر | النوع | الوصف |
|-----------|------|-------|
| `is_hall` | `bool` | هل اكتُشفت هلوسة؟ |
| `conf` | `float` | درجة الثقة (0.0 → 1.0) |

**Return:** `str` — HTML `<span>` مُلوَّن

| الحالة | التاج المُولَّد |
|--------|---------------|
| `is_hall=True` | 🚨 هلوسة 85% (أحمر) |
| `is_hall=False` و `conf >= 0.80` | ✅ سليم 91% (أخضر) |
| `is_hall=False` و `conf < 0.80` | ⚠️ 72% (أصفر) |

---

## 9. تدفق البيانات الكامل

```
أسئلة مُدخَلة
      │
      ▼
RAGEvaluator.evaluate()
      │
      ├──► _measure_retrieval()
      │         └── rag.retrieve()
      │              └── RetrievalMetrics
      │
      ├──► _measure_generation()
      │         ├── rag.generate()
      │         ├── HallucinationGuard.check_response()
      │         └── _score_faithfulness / _score_relevance / _score_completeness
      │              └── GenerationMetrics
      │
      ├──► _record_metrics()
      │         └── MetricsCollector (counters + gauges)
      │
      └──► EvalResult
               └── EvalReport
                        │
               ┌────────┴────────┐
               ▼                 ▼
         report.save()   generate_dashboard()
           (JSON)           (HTML تفاعلي)
```

---

## 10. مثال شامل من البداية للنهاية

```python
from evaluator import RAGEvaluator
from evaluator import generate_dashboard

# ── 1. إنشاء المُقيّم ─────────────────────────────────────────────────
evaluator = RAGEvaluator(
    rag=my_rag_pipeline,
    hallucination_threshold=0.65,
    verbose=True
)

# ── 2. تعريف الأسئلة والمراجع ─────────────────────────────────────────
questions = [
    "ما هو الذكاء الاصطناعي؟",
    "اشرح مفهوم Retrieval-Augmented Generation",
    "ما الفرق بين BM25 والبحث الدلالي؟",
    "كيف يعمل نظام RAG خطوة بخطوة؟",
    "ما هي مزايا استخدام Vector Database؟"
]

references = [
    "الذكاء الاصطناعي هو محاكاة الذكاء البشري في الآلات...",
    "RAG يجمع بين استرجاع المعلومات من قاعدة معرفة وتوليد نصوص...",
    "BM25 يعتمد تكرار الكلمات بينما البحث الدلالي يستخدم embeddings...",
    "خطوات RAG: تقسيم النص، توليد embeddings، البحث، بناء السياق، التوليد...",
    "Vector Database تتيح البحث بالمعنى وليس بالكلمات المفتاحية فقط..."
]

# ── 3. تشغيل التقييم ──────────────────────────────────────────────────
report = evaluator.evaluate(questions, reference_answers=references)

# ── 4. عرض الملخص في الـ terminal ─────────────────────────────────────
evaluator.print_summary(report)

# ── 5. تقرير تفصيلي كامل ─────────────────────────────────────────────
evaluator.print_report(report)

# ── 6. حفظ التقرير كـ JSON ────────────────────────────────────────────
report.save("reports/eval_session_1.json")

# ── 7. توليد لوحة التحكم HTML ─────────────────────────────────────────
path = generate_dashboard(report, "dashboard/eval_session_1.html")

# ── 8. إحصائيات إضافية ────────────────────────────────────────────────
guard_stats = evaluator.get_guard_statistics()
print(f"هلوسات مكتشفة: {guard_stats.get('hallucinations_found', 0)}")

metrics = evaluator.get_metrics_summary()
print(f"متوسط الأمانة: {metrics['gauges']['eval.generation.faithfulness']:.2f}")
print(f"إجمالي الأسئلة: {metrics['counters']['eval.total_questions']}")

# ── 9. تقييم سؤال واحد (للاختبار السريع) ─────────────────────────────
single = evaluator.eval_single("ما هو embedding؟")
print(f"Grade: {single.generation.grade}")
print(f"Hallucination: {single.generation.hallucination.is_hallucination}")
d = single.to_dict()
print(d["generation"]["faithfulness"])
```
---

### Example With Rag System

```python
from evaluator import RAGEvaluator,generate_dashboard
from llm import MistralInterface
from embeddings import MistralEmbedder
from vector_database import FAISSVectorDatabase
from chunks import MultilanguageTextChunker
from context import ContextManager,ContextConfig
from rag.core import RAGSystem ,RAGConfig
embedder=MistralEmbedder(api_key=api)
vector_db=FAISSVectorDatabase(embedder=embedder)
llm=MistralInterface(api_key=api)
chunker=MultilanguageTextChunker()
context_manager=ContextManager()
ctx_config = ContextConfig(
    max_context_length = 3000,
    include_scores     = True,
    template           = "english",
)
context_manager = ContextManager(config=ctx_config)
print("✅ ContextManager: max=3000 chars, include_scores=True")

# ── LLM ─────────────────────────────────────────────────────────────────

print("✅ LLM: OpenAI gpt-4o-mini")

# ── RAGConfig ────────────────────────────────────────────────────────────
rag_config = RAGConfig(
    chunk_size            = 500,
    overlap               = 80,
    top_k                 = 4,          # استرجع 4 قطع لكل سؤال
    min_score             = 0.20,       # تجاهل القطع أقل من 20% تشابه
    enable_reranking      = True,
    rerank_mode           = "heuristic",
    enable_prompt_routing = True,       # يكشف نوع السؤال تلقائياً
    prompt_language       = "en",
    include_few_shot      = True,
)
rag_config.validate()
print("✅ RAGConfig: top_k=4, reranking=heuristic, routing=True")

# ── RAGSystem ────────────────────────────────────────────────────────────
rag = RAGSystem(
    vector_db       = vector_db,
    llm             = llm,
    chunker         = chunker,
    context_manager = context_manager,
    config          = rag_config,
)
print(f"✅ RAGSystem ready → {rag}")


# ══════════════════════════════════════════════════════════════════════════
#  2. قاعدة المعرفة — 5 مستندات عن AI
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("2. إضافة قاعدة المعرفة")
print("─" * 60)

KNOWLEDGE_BASE = {

    "rag_overview": """
Retrieval-Augmented Generation (RAG) is an AI framework that enhances large language
models by combining them with external knowledge retrieval. Instead of relying solely
on knowledge baked into model weights during training, RAG systems retrieve relevant
documents from an external knowledge base at inference time, then pass those documents
as context to the LLM along with the user's query.

RAG was introduced in a 2020 paper by Lewis et al. at Meta AI. The architecture has
three main phases: (1) Indexing — documents are split into chunks, converted into
vector embeddings, and stored in a vector database; (2) Retrieval — at query time,
the query is embedded and nearest neighbors are fetched from the vector store;
(3) Generation — the retrieved chunks are injected into the LLM prompt alongside
the question, and the model generates a grounded answer.

Key advantages of RAG: it reduces hallucinations because answers are grounded in
retrieved facts; it allows knowledge updates without retraining the model; it provides
source citations; and it is cost-effective compared to fine-tuning for every new domain.
""",

    "vector_databases": """
Vector databases are specialized storage systems designed to hold and search
high-dimensional embedding vectors efficiently. Unlike traditional databases that
search by exact value match, vector databases perform similarity search — finding
the k nearest vectors to a query vector using distance metrics such as cosine
similarity, Euclidean distance (L2), or dot product.

Popular vector databases include: FAISS (Facebook AI Similarity Search) — a
highly optimized open-source library that runs in-process; Chroma — a simple
embedded database popular in prototyping; Pinecone — a fully managed cloud service;
Weaviate and Qdrant — production-ready open-source options with filtering support.

FAISS supports several index types. The Flat index performs exact brute-force search
and is accurate but slow for large datasets. The IVF (Inverted File) index clusters
vectors and only searches nearby clusters, trading some accuracy for speed. HNSW
(Hierarchical Navigable Small World) builds a graph structure enabling very fast
approximate search and is often the best balance of speed and accuracy in practice.

Choosing an index depends on dataset size, latency requirements, and whether
approximate answers are acceptable. For datasets under one million vectors, Flat or
HNSW are common choices.
""",

    "embeddings_guide": """
Embeddings are dense numerical representations of text (or other data) in a
continuous vector space. Semantically similar texts map to nearby points in this
space, enabling semantic search instead of keyword-only matching.

Embedding models are trained to project text into a space where distance reflects
meaning. Common models include: sentence-transformers (open-source, runs locally),
OpenAI text-embedding-3-small and text-embedding-3-large (API-based, high quality),
Google Gecko, and Cohere Embed.

The dimensionality of embeddings varies. OpenAI's text-embedding-3-large produces
3072-dimensional vectors. Sentence-Transformers' all-MiniLM-L6-v2 produces 384
dimensions — compact and fast. Higher dimensionality can capture more nuance but
requires more memory and compute.

For multilingual or Arabic text, models like multilingual-e5-large or intfloat/e5-
mistral-7b-instruct are preferred because they are explicitly trained on diverse
language data. Embedding quality is critical to RAG performance: poor embeddings
lead to low-quality retrieval regardless of how good the LLM is.
""",

    "chunking_strategies": """
Chunking is the process of dividing documents into smaller pieces before embedding
and indexing. Chunk size and overlap are among the most impactful hyperparameters in
a RAG pipeline.

Common chunking strategies: (1) Fixed-size character chunking — split every N
characters with optional overlap. Simple but can break sentences mid-way. (2)
Recursive character splitting — tries to split on natural boundaries like paragraphs,
then sentences, then words, then characters. Produces more coherent chunks.
(3) Semantic chunking — uses sentence embeddings to group semantically related
sentences into the same chunk, maximizing coherence at the cost of variable chunk sizes.
(4) Token-based splitting — splits by token count, which matches LLM context windows
precisely.

Chunk size trade-offs: small chunks (100-200 tokens) give precise retrieval but may
lack context; large chunks (800-1500 tokens) provide more context but dilute the
signal. Chunk overlap (typically 10-20% of chunk size) preserves continuity across
boundaries. A common starting point is chunk_size=500, overlap=100.
""",

    "hallucination_guide": """
Hallucination in large language models refers to the generation of content that is
factually incorrect, ungrounded, or fabricated — yet stated with confidence. LLMs
hallucinate because they generate text based on statistical patterns learned from
training data, not by accessing verified facts.

Types of hallucinations: (1) Factual hallucination — stating incorrect facts (e.g.,
wrong dates, people, statistics); (2) Context hallucination — generating information
not supported by the provided context; (3) Source hallucination — citing non-existent
papers, URLs, or references.

RAG significantly reduces hallucinations because the model's answer is anchored to
retrieved passages. However, RAG does not eliminate hallucinations completely —
models can still ignore retrieved context or misinterpret it.

Mitigation strategies: faithfulness scoring (measuring how much the answer is
supported by context), confidence thresholding, self-consistency checks, and
HallucinationGuard systems that flag suspect responses. In production, monitoring
hallucination rate as a key metric is essential for maintaining answer quality.
"""
}

# إضافة المستندات
results = rag.add_documents(KNOWLEDGE_BASE)
for doc_id, num_chunks in results.items():
    print(f"  📄 {doc_id}: {num_chunks} chunks")

stats = rag.get_stats()
print(f"\n  إجمالي المستندات : {stats['total_documents']}")
print(f"  إجمالي القطع     : {stats['total_chunks']}")
print(f"  Vector DB size   : {stats['vector_db_size']}")


# ══════════════════════════════════════════════════════════════════════════
#  3. أسئلة مباشرة (بدون تقييم)
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("3. أسئلة مباشرة على النظام")
print("─" * 60)

DIRECT_QUESTIONS = [
    "What is Retrieval-Augmented Generation and how does it work?",
    "What are the main types of FAISS indexes and when to use each?",
    "Why do large language models hallucinate and how can RAG help?",
    "What embedding model should I use for Arabic text in a RAG system?",
    "What chunk size should I use for RAG?",
]

for i, q in enumerate(DIRECT_QUESTIONS, 1):
    print(f"\n  Q{i}: {q}")

    # استرجاع القطع
    retrieved = rag.retrieve(q, top_k=3)
    scores = [f"{score:.3f}" for _, score in retrieved]
    print(f"       ↳ استُرجع {len(retrieved)} قطع | أعلى درجات: {', '.join(scores)}")

    # توليد الإجابة
    answer = rag.generate(q, include_sources=False, language="en")
    print(f"       ↳ {answer[:200].strip()}{'...' if len(answer) > 200 else ''}")


# ══════════════════════════════════════════════════════════════════════════
#  4. التقييم الكامل بـ RAGEvaluator
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("4. التقييم الكامل بـ RAGEvaluator")
print("─" * 60)

# ── أسئلة التقييم مع إجابات مرجعية ────────────────────────────────────
EVAL_QUESTIONS = [
    "What is RAG and what are its main advantages?",
    "How does FAISS perform vector similarity search?",
]

REFERENCE_ANSWERS = [
    "RAG (Retrieval-Augmented Generation) enhances LLMs by combining generation "
    "with external knowledge retrieval. Advantages include reduced hallucinations, "
    "no retraining needed, source citations, and cost effectiveness.",

    "FAISS converts text into embedding vectors and performs similarity search "
    "using distance metrics like cosine similarity or L2 distance to find the "
    "k nearest vectors to a query embedding.",

    "HNSW builds a graph structure for fast approximate search and is best for "
    "speed-accuracy balance. IVF clusters vectors and only searches nearby clusters, "
    "trading some accuracy for speed on large datasets.",

    "The three phases are: Indexing (split documents, embed, store in vector DB), "
    "Retrieval (embed query, find nearest chunks), and Generation "
    "(inject retrieved chunks into LLM prompt with the question).",

    "Small chunks give precise retrieval but lack context; large chunks provide "
    "more context but dilute the signal. A common starting point is chunk_size=500 "
    "with overlap=100.",

    "Hallucination is when LLMs generate incorrect or fabricated content. RAG "
    "reduces it by anchoring answers to retrieved factual passages from the "
    "knowledge base.",

    "OpenAI text-embedding-3-large produces 3072-dimensional vectors.",

    "Semantic chunking groups semantically related sentences using embeddings, "
    "producing coherent variable-size chunks. Fixed-size chunking simply splits "
    "every N characters which can break sentences mid-way.",
]

# ── تهيئة المُقيّم ───────────────────────────────────────────────────────
evaluator = RAGEvaluator(
    rag                     = rag,
    hallucination_threshold = 0.65,
    verbose                 = True,
)

# ── تشغيل التقييم ────────────────────────────────────────────────────────
report = evaluator.evaluate(
    questions         = EVAL_QUESTIONS,
    reference_answers = REFERENCE_ANSWERS,
)


# ══════════════════════════════════════════════════════════════════════════
#  5. طباعة التقرير الكامل
# ══════════════════════════════════════════════════════════════════════════

evaluator.print_report(report)


# ══════════════════════════════════════════════════════════════════════════
#  6. تفاصيل كل سؤال
# ══════════════════════════════════════════════════════════════════════════

print("─" * 60)
print("6. تفاصيل إضافية لكل سؤال")
print("─" * 60)

for i, result in enumerate(report.results, 1):
    r   = result.retrieval
    g   = result.generation
    hall_icon = "🚨" if g.hallucination.is_hallucination else "✅"

    print(f"\n  [{i}] {result.query[:65]}")
    print(f"       Grade        : {g.grade} ({g.overall_score:.1%})")
    print(f"       Faithfulness : {g.faithfulness_score:.1%}")
    print(f"       Relevance    : {g.relevance_score:.1%}")
    print(f"       Completeness : {g.completeness_score:.1%}")
    print(f"       Retrieval    : top={r.top_score:.3f}  avg={r.avg_score:.3f}  "
          f"chunks={r.num_chunks}  ({r.quality_label})")
    print(f"       Latency      : ret={r.latency_ms:.0f}ms  gen={g.latency_ms:.0f}ms  "
          f"total={r.latency_ms+g.latency_ms:.0f}ms")
    print(f"       Hallucination: {hall_icon} conf={g.hallucination.confidence_score:.3f}")
    if g.hallucination.is_hallucination and g.hallucination.recommendation:
        print(f"       ⚠️  Tip: {g.hallucination.recommendation[:80]}")


# ══════════════════════════════════════════════════════════════════════════
#  7. توزيع الدرجات
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("7. توزيع الدرجات")
print("─" * 60)

dist = report.grade_distribution
total = sum(dist.values())

for grade, count in dist.items():
    bar = "█" * count + "░" * (total - count)
    pct = count / total * 100 if total else 0
    print(f"  {grade}  {bar}  {count}/{total} ({pct:.0f}%)")

print(f"\n  صحة النظام : {report.system_health}")
print(f"  متوسط الوقت: {report.avg_latency_ms:.0f}ms")


# ══════════════════════════════════════════════════════════════════════════
#  8. إحصائيات HallucinationGuard
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("8. إحصائيات HallucinationGuard")
print("─" * 60)

guard_stats = evaluator.get_guard_statistics()
for k, v in guard_stats.items():
    print(f"  {k}: {v}")


# ══════════════════════════════════════════════════════════════════════════
#  9. إحصائيات MetricsCollector
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("9. إحصائيات MetricsCollector")
print("─" * 60)

metrics = evaluator.get_metrics_summary()
print("  Counters:")
for k, v in metrics["counters"].items():
    print(f"    {k}: {v}")

print("  Gauges (last value):")
for k, v in metrics["gauges"].items():
    print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")


# ══════════════════════════════════════════════════════════════════════════
#  10. حفظ التقرير وتوليد Dashboard
# ══════════════════════════════════════════════════════════════════════════
import os
print("\n" + "─" * 60)
print("10. الحفظ والتصدير")
print("─" * 60)

# حفظ كـ JSON
OUTPUT_DIR = "./dashbord_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)



# توليد Dashboard HTML
html_path = os.path.join(OUTPUT_DIR, "eval_dashboard.html")
generate_dashboard(report, output_path=html_path)

print(f"  📁 ملفات الإخراج في: {OUTPUT_DIR}/")
print(f"  🌐 HTML  : {html_path}")
print(f"      افتح rag_output/eval_dashboard.html في المتصفح!")


# ══════════════════════════════════════════════════════════════════════════
#  11. إحصائيات RAGSystem النهائية
# ══════════════════════════════════════════════════════════════════════════

print("\n" + "─" * 60)
print("11. إحصائيات RAGSystem")
print("─" * 60)

final_stats = rag.get_stats()
print(f"  total_documents  : {final_stats['total_documents']}")
print(f"  total_chunks     : {final_stats['total_chunks']}")
print(f"  total_queries    : {final_stats['total_queries']}")
print(f"  successful       : {final_stats['successful_queries']}")
print(f"  failed           : {final_stats['failed_queries']}")
print(f"  vector_db_size   : {final_stats['vector_db_size']}")
print(f"  chunker_type     : {final_stats['chunker_type']}")

```
---

## ملخص صيغ حساب الدرجات

| المقياس | الصيغة |
|---------|--------|
| **Faithfulness** | `min(1.0, تداخل_كلمات × 1.4)` |
| **Relevance** | `(تطابق × 0.65) + (min(1, طول÷80) × 0.35)` |
| **Completeness (مع مرجع)** | `تداخل_مع_المرجع ÷ كلمات_المرجع` |
| **Completeness (بدون مرجع)** | `(min(1, كلمات÷60) × 0.60) + (تنوع × 0.40)` |
| **Overall Score** | `Faith×0.40 + Relevance×0.35 + Completeness×0.25` |

---

