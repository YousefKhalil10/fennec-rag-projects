# 🛡️ دليل التوثيق الشامل — Hallucination Guard
## طبقة الحماية من الهلوسة للـ LLMs

> **نظرة عامة**
>
> نظام يضيف طبقة حماية ذكية فوق أي نموذج لغوي كبير (LLM)
> للكشف عن الهلوسة (Hallucination) ومنعها قبل أن تصل إلى المستخدم.
> تشمل آليات متعددة للتحقق من المصادر والحقائق والتناقضات الداخلية،
> مع دعم لإعادة المحاولة التلقائية وإحصاءات مفصّلة.

---



---

## 🔍 ما هي الهلوسة في الـ LLMs؟

الهلوسة (Hallucination) هي ظاهرة تُنتج فيها نماذج اللغة معلومات تبدو صحيحة
لكنها مخترعة أو غير دقيقة. هذا النظام يكتشفها ويتعامل معها عبر ستة أنواع:

| النوع | الوصف |
|---|---|
| `FACTUAL_ERROR` | خطأ في الحقائق الموجودة في الإجابة |
| `MADE_UP_INFO` | معلومات مختلقة كلياً لا أساس لها |
| `CONFLICTING_INFO` | تناقض داخلي بين أجزاء الإجابة |
| `UNSUPPORTED_CLAIM` | ادعاءات لا تدعمها أي مصادر |
| `CONTEXT_DEVIATION` | إجابة تخرج عن سياق السؤال |
| `OVERCONFIDENCE` | ثقة زائدة في معلومات غير مؤكدة |

---

## 📦 متطلبات التثبيت

```bash
pip install numpy
```

---
---


**الوصف:**
يحتوي على كل منطق الكشف والتحليل: مقاييس التصنيف، بنى البيانات،
والكلاس الرئيسي `HallucinationGuard`.

---

## `HallucinationType` *(Enum)*

**الوصف:**
يُعرّف الأنواع الستة للهلوسة المحتملة في مخرجات الـ LLM.
يُستخدم في `HallucinationCheck.hallucination_type`.

| القيمة | الـ value | الوصف |
|---|---|---|
| `FACTUAL_ERROR` | `"factual_error"` | خطأ في الحقائق |
| `MADE_UP_INFO` | `"made_up_info"` | معلومات مختلقة |
| `CONFLICTING_INFO` | `"conflicting_info"` | معلومات متناقضة |
| `UNSUPPORTED_CLAIM` | `"unsupported_claim"` | ادعاءات غير مدعومة |
| `CONTEXT_DEVIATION` | `"context_deviation"` | خروج عن السياق |
| `OVERCONFIDENCE` | `"overconfidence"` | ثقة زائدة |

```python
from llm.hallucination import HallucinationType
print(HallucinationType.FACTUAL_ERROR.value)  # "factual_error"
print(HallucinationType.MADE_UP_INFO.value)   # "made_up_info"
```

---

## `ConfidenceLevel` *(Enum)*

**الوصف:**
يُعرّف خمسة مستويات للثقة في الإجابة. تُستخدم بواسطة
`get_confidence_level()` لتحويل النتيجة الرقمية إلى وصف مقروء.

| القيمة | النطاق | الوصف |
|---|---|---|
| `VERY_HIGH` | 90–100% | ثقة عالية جداً |
| `HIGH` | 75–89% | ثقة عالية |
| `MEDIUM` | 50–74% | ثقة متوسطة |
| `LOW` | 25–49% | ثقة منخفضة |
| `VERY_LOW` | 0–24% | ثقة منخفضة جداً |

```python
from llm.hallucination import ConfidenceLevel

guard = HallucinationGuard()
level = guard.get_confidence_level(0.85)
print(level)        # ConfidenceLevel.HIGH
print(level.value)  # "high"
```

---

## `HallucinationCheck` *(Dataclass)*

**الوصف:**
يحمل النتيجة الكاملة لعملية فحص هلوسة واحدة.
يُرجعه `HallucinationGuard.check_response()` في كل مرة.

**الحقول:**

| الحقل | النوع | الوصف |
|---|---|---|
| `is_hallucination` | `bool` | هل الإجابة تحتوي هلوسة؟ |
| `confidence_score` | `float` | النتيجة من 0 إلى 1 (كلما كانت أعلى = أكثر موثوقية) |
| `hallucination_type` | `Optional[HallucinationType]` | نوع الهلوسة، أو `None` إذا لم توجد |
| `evidence` | `List[str]` | قائمة الأدلة التي أثارت الشك |
| `recommendation` | `str` | توصية بالإجراء المناسب |
| `timestamp` | `datetime` | وقت إجراء الفحص (يُملأ تلقائياً) |

---

#### `to_dict()`

**الوصف:**
يُحوّل نتيجة الفحص إلى قاموس Python قابل للتسلسل (JSON-friendly).
مفيد للتسجيل أو الإرسال عبر API.

**Return:** `Dict`

```python
check = guard.check_response("The Eiffel Tower was built in 1989.")
result_dict = check.to_dict()

print(result_dict["is_hallucination"])    # True أو False
print(result_dict["confidence_score"])   # 0.65 مثلاً
print(result_dict["hallucination_type"]) # "factual_error"
print(result_dict["timestamp"])          # "2024-01-15T10:30:00.000000"
```

---

## `GroundingContext` *(Dataclass)*

**الوصف:**
يحمل السياق الموثوق الذي يُستخدم للتحقق من إجابة الـ LLM.
يُمرَّر لـ `check_response()` و`generate()` لتمكين التحقق من المصادر والحقائق.

**الحقول:**

| الحقل | النوع | الوصف |
|---|---|---|
| `sources` | `List[str]` | قائمة المصادر الموثوقة (URLs، أسماء كتب...) |
| `retrieved_facts` | `List[str]` | حقائق محددة مُسترجَعة من قاعدة المعرفة |
| `context_window` | `str` | النص الكامل للسياق المرجعي |
| `metadata` | `Dict[str, Any]` | بيانات إضافية اختيارية |

```python
from llm.hallucination import import GroundingContext

context = GroundingContext(
    sources=[
        "Wikipedia - Eiffel Tower",
        "Paris Official Tourism Guide 2023"
    ],
    retrieved_facts=[
        "The Eiffel Tower was built between 1887 and 1889.",
        "It stands 330 meters tall.",
        "It was designed by Gustave Eiffel."
    ],
    context_window="""
        The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars
        in Paris, France. It was constructed between 1887 and 1889 as the
        centerpiece of the 1889 World's Fair.
    """,
    metadata={"topic": "landmarks", "language": "en"}
)
```

---

## `HallucinationGuard`

**الوصف:**
الكلاس الرئيسي لكشف الهلوسة. يُشغّل سلسلة من الفحوصات على أي نص
ويُرجع تقييماً شاملاً مع النتيجة والأدلة والتوصية.

**الفحوصات التي يُجريها:**
1. التحقق من وجود مصادر للادعاءات
2. كشف التناقضات الداخلية
3. تحليل مؤشرات الثقة (عدم اليقين / الثقة الزائدة)
4. التحقق من الحقائق بالمقارنة مع السياق
5. فحص ملاءمة الإجابة للسؤال

---

#### `__init__(threshold, require_sources, fact_check_enabled, confidence_check_enabled, enable_logging)`

**الوصف:**
يُهيّئ طبقة الحماية مع إعدادات قابلة للتخصيص.
يُحمّل أنماط الكشف من `hallucination_pattern` خارجياً.

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `threshold` | `float` | `0.7` | الحد الأدنى للنتيجة لقبول الإجابة (0–1). نتيجة أقل = هلوسة |
| `require_sources` | `bool` | `True` | هل يُشترط وجود مصادر في السياق لقبول الإجابة؟ |
| `fact_check_enabled` | `bool` | `True` | تفعيل التحقق من الحقائق عند توفر `GroundingContext` |
| `confidence_check_enabled` | `bool` | `True` | تفعيل تحليل مؤشرات الثقة في النص |
| `enable_logging` | `bool` | `True` | حفظ نتائج الفحص في `check_history` |

```python
from llm.hallucination import HallucinationGuard

# إعداد افتراضي
guard = HallucinationGuard()

# إعداد صارم — يشترط نتيجة 90%+ وتحقق شامل
strict_guard = HallucinationGuard(
    threshold=0.9,
    require_sources=True,
    fact_check_enabled=True,
    confidence_check_enabled=True,
    enable_logging=True
)

# إعداد خفيف — بدون حفظ تاريخ
light_guard = HallucinationGuard(
    threshold=0.5,
    require_sources=False,
    enable_logging=False
)
```

---

### الدوال الرئيسية

---

#### `check_response(response, grounding_context, original_query)`

**الوصف:**
الدالة المحورية — تُجري فحصاً شاملاً على إجابة الـ LLM وتُرجع
تقييماً مفصّلاً. تُشغّل حتى خمسة فحوصات متوازية وتحسب متوسطاً
مرجّحاً لها (مع penalty 50% على أي فحص فاشل).

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `response` | `str` | — | نص الإجابة من الـ LLM |
| `grounding_context` | `Optional[GroundingContext]` | `None` | السياق والمصادر للتحقق منها |
| `original_query` | `Optional[str]` | `None` | السؤال الأصلي للتحقق من الملاءمة |

**Return:** `HallucinationCheck` — نتيجة الفحص الكاملة

**آلية الحساب:**
```
final_score = mean([score × (1.0 إذا نجح الفحص) أو (0.5 إذا فشل)])
is_hallucination = final_score < threshold
```

```python
from llm.hallucination import HallucinationGuard, GroundingContext

guard = HallucinationGuard(threshold=0.7)

# فحص بدون سياق
result = guard.check_response(
    response="Python was created by Guido van Rossum in 1991.",
    original_query="Who created Python?"
)
print(result.is_hallucination)   # False أو True
print(result.confidence_score)   # 0.0 - 1.0
print(result.recommendation)     # "Response appears reliable..."

# فحص مع سياق كامل
context = GroundingContext(
    sources=["Python.org - History"],
    retrieved_facts=["Python was released in 1991 by Guido van Rossum."],
    context_window="Python is a programming language created by Guido van Rossum."
)

result = guard.check_response(
    response="Python was created by Guido van Rossum in 1991.",
    grounding_context=context,
    original_query="Who created Python?"
)

print(result.is_hallucination)    # False
print(f"{result.confidence_score:.0%}")  # 85% مثلاً
print(result.hallucination_type)  # None
print(result.evidence)            # []
print(result.recommendation)      # "Response appears reliable. Minor verification recommended."

# فحص إجابة مشبوهة
result = guard.check_response(
    response="I am absolutely 100% certain that Python was invented in 1850.",
    grounding_context=context,
    original_query="When was Python created?"
)
print(result.is_hallucination)    # True
print(result.hallucination_type)  # HallucinationType.FACTUAL_ERROR
print(result.evidence)            # ["Unverified fact: ..."]
```

---

#### `get_confidence_level(score)`

**الوصف:**
يُحوّل نتيجة رقمية (0–1) إلى مستوى ثقة وصفي من `ConfidenceLevel`.
مفيد لعرض نتائج مقروءة للمستخدم.

| Parameter | النوع | الوصف |
|---|---|---|
| `score` | `float` | النتيجة من 0.0 إلى 1.0 |

**Return:** `ConfidenceLevel`

| النطاق | المستوى المُرجَع |
|---|---|
| `>= 0.90` | `VERY_HIGH` |
| `>= 0.75` | `HIGH` |
| `>= 0.50` | `MEDIUM` |
| `>= 0.25` | `LOW` |
| `< 0.25` | `VERY_LOW` |

```python
guard = HallucinationGuard()

print(guard.get_confidence_level(0.95).value)  # "very_high"
print(guard.get_confidence_level(0.80).value)  # "high"
print(guard.get_confidence_level(0.60).value)  # "medium"
print(guard.get_confidence_level(0.35).value)  # "low"
print(guard.get_confidence_level(0.10).value)  # "very_low"
```

---

#### `get_statistics()`

**الوصف:**
يُرجع إحصاءات شاملة عن جميع الفحوصات المحفوظة في `check_history`.
يتطلب `enable_logging=True` (الافتراضي).

**Return:** `Dict[str, Any]` يحتوي على:

| المفتاح | الوصف |
|---|---|
| `total_checks` | إجمالي عدد الفحوصات |
| `hallucinations_detected` | عدد الهلوسات المكتشفة |
| `hallucination_rate` | نسبة الهلوسة (0–1) |
| `average_confidence_score` | متوسط نتائج الثقة |
| `hallucination_types` | توزيع الأنواع المكتشفة |
| `last_check` | بيانات آخر فحص كـ dict |

```python
guard = HallucinationGuard()

# إجراء عدة فحوصات
guard.check_response("Python was created in 1991.")
guard.check_response("The moon is made of cheese.")
guard.check_response("Water boils at 100°C at sea level.")

stats = guard.get_statistics()
print(f"إجمالي الفحوصات: {stats['total_checks']}")         # 3
print(f"هلوسات مكتشفة: {stats['hallucinations_detected']}") # 1 أو 2
print(f"نسبة الهلوسة: {stats['hallucination_rate']:.0%}")   # 33% مثلاً
print(f"متوسط الثقة: {stats['average_confidence_score']:.2f}")
print(f"توزيع الأنواع: {stats['hallucination_types']}")
```

---

#### `reset_history()`

**الوصف:**
يمسح جميع نتائج الفحص المحفوظة في `check_history`.
مفيد لبدء دورة تتبع جديدة أو تحرير الذاكرة.

```python
guard = HallucinationGuard()

guard.check_response("Some response here.")
print(len(guard.check_history))  # 1

guard.reset_history()
print(len(guard.check_history))  # 0
```

---

### الفحوصات الداخلية *(Internal Checks)*

---

#### `_check_sources(response, context)` *(internal)*

**الوصف:**
يستخرج الادعاءات من الإجابة ويتحقق من دعمها بالمصادر المتاحة.
يُحسب نسبة الادعاءات المدعومة. نسبة أعلى من 70% = نجاح.

| Parameter | النوع | الوصف |
|---|---|---|
| `response` | `str` | نص الإجابة |
| `context` | `GroundingContext` | السياق بالمصادر |

**Return:** `Tuple[bool, float, List[str]]` — `(passed, score, evidence)`

---

#### `_check_internal_contradictions(response)` *(internal)*

**الوصف:**
يُقسّم الإجابة إلى جمل ويفحص كل زوج منها عن تناقض.
يكشف التناقضات عبر تحليل كلمات النفي مع التشابه في الكلمات.

| Parameter | النوع | الوصف |
|---|---|---|
| `response` | `str` | نص الإجابة |

**Return:** `Tuple[bool, float, List[str]]` — `(no_contradictions, score, contradictions)`

**حساب النتيجة:**
```
score = 1.0 إذا لم توجد تناقضات
score = max(0.3, 1.0 - عدد_التناقضات × 0.2) إذا وُجدت
```

---

#### `_analyze_confidence_markers(response)` *(internal)*

**الوصف:**
يبحث في النص عن ثلاثة أنواع من المؤشرات:
1. **عدم اليقين** (مثل: "maybe", "I think") — penalty خفيفة
2. **الثقة الزائدة** (مثل: "absolutely certain") — penalty متوسطة
3. **مؤشرات الاختلاق** — penalty قوية

**المعادلة:**
```
penalty = (uncertainty × 0.05) + (overconfidence × 0.10) + (made_up × 0.20)
score   = max(0.0, 1.0 - penalty)
```

| Parameter | النوع | الوصف |
|---|---|---|
| `response` | `str` | نص الإجابة |

**Return:** `Tuple[bool, float, List[str]]`

---

#### `_verify_facts(response, context)` *(internal)*

**الوصف:**
يستخرج الجمل الحقيقية (التي تحتوي أرقاماً أو تواريخ أو نسباً مئوية)
من الإجابة ويقارنها بالحقائق في `context.retrieved_facts`.
نسبة تطابق فوق 70% = نجاح.

| Parameter | النوع | الوصف |
|---|---|---|
| `response` | `str` | نص الإجابة |
| `context` | `GroundingContext` | السياق بالحقائق المرجعية |

**Return:** `Tuple[bool, float, List[str]]`

---

#### `_check_context_relevance(response, query)` *(internal)*

**الوصف:**
يستخرج الكلمات المفتاحية من السؤال (بعد حذف stop words)
ويتحقق من وجودها في الإجابة.
نسبة تغطية فوق 30% = ملاءمة مقبولة.

| Parameter | النوع | الوصف |
|---|---|---|
| `response` | `str` | نص الإجابة |
| `query` | `str` | السؤال الأصلي |

**Return:** `Tuple[bool, float, List[str]]`

---

### الدوال المساعدة *(Helper Methods)*

---

#### `_extract_claims(text)` *(internal)*

**الوصف:**
يُقسّم النص إلى جمل ويُصفّي الأسئلة والجمل القصيرة جداً
(أقل من 5 كلمات)، ويُرجع ما تبقى كادعاءات.

**Return:** `List[str]`

---

#### `_is_claim_supported(claim, context)` *(internal)*

**الوصف:**
يتحقق من أن الادعاء مدعوم بالبحث في `sources` و`context_window`.
يُطابق الكلمات التي يزيد طولها عن 4 أحرف.

**Return:** `bool`

---

#### `_split_into_sentences(text)` *(internal)*

**الوصف:**
يُقسّم النص إلى جمل باستخدام `[.!?]+` كفاصل.

**Return:** `List[str]`

---

#### `_are_contradicting(sent1, sent2)` *(internal)*

**الوصف:**
يكشف التناقض بين جملتَين: إذا كانت إحداهما منفية والأخرى لا،
مع تشابه أكثر من 3 كلمات، تُعتبر متناقضتَين.
كلمات النفي المدعومة: `لا, ليس, not, no, never, none`.

**Return:** `bool`

---

#### `_extract_factual_statements(text)` *(internal)*

**الوصف:**
يستخرج الجمل التي تحتوي أرقاماً أو تواريخ أو نسباً مئوية (`\d+|في عام|\d{4}|%`).
يُستبعد الآراء ("أعتقد", "i think", "maybe"). يُرجع أول 3 جمل كحد أدنى.

**Return:** `List[str]`

---

#### `_facts_match(fact1, fact2)` *(internal)*

**الوصف:**
يُطابق حقيقتَين عبر مقارنة الأرقام المستخرجة أولاً،
ثم نسبة التداخل في الكلمات الطويلة (> 4 أحرف).
تطابق فوق 50% = تطابق إيجابي.

**Return:** `bool`

---

#### `_extract_keywords(text)` *(internal)*

**الوصف:**
يستخرج الكلمات الجوهرية بعد حذف stop words شائعة بالعربية والإنجليزية
وحذف الكلمات القصيرة (أقل من 4 أحرف).

**Return:** `List[str]`

---

#### `_determine_hallucination_type(checks, evidence)` *(internal)*

**الوصف:**
يُحدّد نوع الهلوسة بتحليل نص الأدلة المجمَّعة.
إذا لم يفشل أي فحص يُرجع `None`.

**منطق التحديد:**

| إذا وُجد في الأدلة | النوع المُرجَع |
|---|---|
| "no grounding sources" أو "unsupported" | `UNSUPPORTED_CLAIM` |
| "contradiction" | `CONFLICTING_INFO` |
| "overconfidence" | `OVERCONFIDENCE` |
| "made-up" | `MADE_UP_INFO` |
| "not relevant" | `CONTEXT_DEVIATION` |
| "unverified fact" | `FACTUAL_ERROR` |

**Return:** `Optional[HallucinationType]`

---

#### `_generate_recommendation(is_hallucination, score, hallucination_type, evidence)` *(internal)*

**الوصف:**
يُولّد توصية نصية مناسبة بناءً على نتيجة الفحص.
إذا لم تكن هلوسة يُرجع رسالة موجبة حسب مستوى الثقة.
إذا كانت هلوسة يُرجع توصية محددة لكل نوع.

| النوع | التوصية |
|---|---|
| `UNSUPPORTED_CLAIM` | اطلب مصادر وأدلة |
| `CONFLICTING_INFO` | أعد التوليد بمعلومات متسقة |
| `OVERCONFIDENCE` | اطلب صياغة أكثر تحفظاً |
| `MADE_UP_INFO` | ارفض الإجابة واستخدم مصادر موثقة |
| `CONTEXT_DEVIATION` | أعد التركيز على السؤال |
| `FACTUAL_ERROR` | تحقق من الحقائق وطلب تصحيحات |

**Return:** `str`

---

## `ProtectedLLMInterface`

**الوصف:**
يُغلّف أي `LLM interface` ويُضيف طبقة حماية تلقائية من الهلوسة.
يدعم إعادة المحاولة التلقائية مع تعديل الـ prompt وتخفيض الـ temperature،
ووضعاً صارماً يرفض أي إجابة مشبوهة، وإحصاءات تفصيلية.

---

#### `__init__(llm_interface, hallucination_guard, auto_retry, max_retries, request_sources, strict_mode, verbose)`

**الوصف:**
يُهيّئ الواجهة المحمية حول أي LLM.
إذا لم يُمرَّر `hallucination_guard` يُنشئ واحداً تلقائياً بإعدادات افتراضية.

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `llm_interface` | `Any` | — | واجهة الـ LLM الأصلية (يجب أن تدعم `.generate()`) |
| `hallucination_guard` | `Optional[HallucinationGuard]` | `None` | طبقة الحماية المخصصة؛ تُنشأ تلقائياً إذا لم تُحدَّد |
| `auto_retry` | `bool` | `True` | إعادة المحاولة تلقائياً عند كشف هلوسة |
| `max_retries` | `int` | `3` | أقصى عدد لإعادة المحاولة قبل قبول الإجابة |
| `request_sources` | `bool` | `True` | إضافة تعليمات "استشهد بمصادرك" تلقائياً للـ prompt |
| `strict_mode` | `bool` | `False` | الوضع الصارم — يرفض ويستبدل أي إجابة تُكشف كهلوسة |
| `verbose` | `bool` | `True` | طباعة ملخص الفحص في كل استدعاء |

```python
from llm.hallucination import ProtectedLLMInterface
from llm.hallucination import HallucinationGuard

# إنشاء بسيط (الحماية تُنشأ تلقائياً)
protected = ProtectedLLMInterface(
    llm_interface=my_llm,
    auto_retry=True,
    max_retries=3,
)

# مع حماية مخصصة
custom_guard = HallucinationGuard(threshold=0.85)
protected = ProtectedLLMInterface(
    llm_interface=my_llm,
    hallucination_guard=custom_guard,
    strict_mode=True,     # رفض أي هلوسة
    verbose=False,        # بدون طباعة
    max_retries=5
)
```

---

### الدوال الرئيسية

---

#### `generate(prompt, grounding_context, max_tokens, temperature, bypass_guard, **kwargs)`

**الوصف:**
الدالة المحورية — تُولّد نصاً محمياً من الهلوسة.
تُعزّز الـ prompt بتعليمات المصداقية، تُولّد الإجابة، تفحصها،
وتُعيد المحاولة إذا لزم مع تخفيض تدريجي للـ temperature.

**سلسلة التنفيذ:**
```
enhance_prompt → generate → check_response → [retry loop] → [strict_mode] → return
```

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `prompt` | `str` | — | السؤال أو الطلب الأصلي |
| `grounding_context` | `Optional[GroundingContext]` | `None` | السياق والمصادر للتحقق |
| `max_tokens` | `int` | `500` | الحد الأقصى لطول الإجابة |
| `temperature` | `float` | `0.7` | درجة الإبداعية (0=محافظ، 1=إبداعي) |
| `bypass_guard` | `bool` | `False` | تجاوز الحماية كلياً (للطوارئ فقط) |
| `**kwargs` | — | — | معاملات إضافية تُمرَّر للـ LLM |

**Return:** `Dict[str, Any]` يحتوي على:

| المفتاح | النوع | الوصف |
|---|---|---|
| `response` | `str` | نص الإجابة النهائية |
| `check_result` | `HallucinationCheck` | نتيجة آخر فحص |
| `retries` | `int` | عدد مرات إعادة المحاولة |
| `confidence_level` | `ConfidenceLevel` | مستوى الثقة الوصفي |
| `confidence_score` | `float` | نتيجة الثقة الرقمية |
| `is_hallucination` | `bool` | هل كانت الإجابة النهائية هلوسة؟ |
| `hallucination_type` | `str \| None` | نوع الهلوسة إن وُجد |
| `recommendation` | `str` | التوصية النهائية |
| `sources_used` | `List[str]` | المصادر المستخدمة في التحقق |

**آلية إعادة المحاولة:**
```
لكل محاولة إعادة:
  retry_temperature = max(0.3, temperature - retries × 0.1)
       retry_prompt = feedback + problems + original_prompt
```

```python
from llm.hallucination import ProtectedLLMInterface
from llm.hallucination import GroundingContext

protected = ProtectedLLMInterface(llm_interface=my_llm)

# استدعاء بسيط
result = protected.generate("What year was Python created?")

print(result["response"])          # نص الإجابة
print(result["is_hallucination"])  # False
print(result["confidence_score"])  # 0.85 مثلاً
print(result["retries"])           # 0

# مع سياق كامل
context = GroundingContext(
    sources=["Python.org", "Wikipedia - Python"],
    retrieved_facts=["Python was released in 1991."],
    context_window="Python 1.0 was released in January 1994 by Guido van Rossum."
)

result = protected.generate(
    prompt="When was Python first released?",
    grounding_context=context,
    max_tokens=200,
    temperature=0.5
)

print(result["response"])
print(f"ثقة: {result['confidence_score']:.0%}")
print(f"مستوى: {result['confidence_level'].value}")
print(f"مصادر: {result['sources_used']}")

# تجاوز الحماية (للطوارئ)
result = protected.generate(
    prompt="Tell me something creative",
    bypass_guard=True
)
print(result["warning"])  # "Hallucination guard was bypassed"
```

---

#### `generate_async(prompt, grounding_context, max_tokens, temperature, bypass_guard, **kwargs)`

**الوصف:**
نسخة async كاملة من `generate` — نفس المنطق تماماً لكن تستدعي
`llm.generate_async()` وتدعم `await`.
مثالية للاستخدام في FastAPI وأي تطبيق async.

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `prompt` | `str` | — | السؤال أو الطلب الأصلي |
| `grounding_context` | `Optional[GroundingContext]` | `None` | السياق والمصادر |
| `max_tokens` | `int` | `500` | الحد الأقصى للطول |
| `temperature` | `float` | `0.7` | درجة الإبداعية |
| `bypass_guard` | `bool` | `False` | تجاوز الحماية |
| `**kwargs` | — | — | معاملات إضافية |

**Return:** `Dict[str, Any]` — نفس بنية `generate`

**ملاحظة:** يتطلب أن يدعم `llm_interface` دالة `generate_async`.

```python
import asyncio
from llm.hallucination import ProtectedLLMInterface

protected = ProtectedLLMInterface(llm_interface=my_async_llm)

async def main():
    result = await protected.generate_async(
        prompt="What is the capital of France?",
        max_tokens=100,
        temperature=0.3
    )
    print(result["response"])
    print(result["confidence_score"])

asyncio.run(main())

# معالجة متوازية لعدة أسئلة
async def process_batch(questions: list):
    tasks = [
        protected.generate_async(q, temperature=0.3)
        for q in questions
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

#### `get_statistics()`

**الوصف:**
يُرجع إحصاءات مدمجة من الواجهة المحمية والـ guard معاً.
يشمل: معدل الهلوسة، معدل النجاح، متوسط إعادات المحاولة.

**Return:** `Dict[str, Any]` يحتوي على:

| المفتاح | الوصف |
|---|---|
| `llm_stats` | إحصاءات الطلبات الكاملة (طلبات، هلوسات، إعادات...) |
| `guard_stats` | إحصاءات الـ guard (أنواع الهلوسة، متوسط الثقة...) |
| `hallucination_rate` | نسبة الطلبات التي انتهت بهلوسة |
| `success_rate` | نسبة الطلبات الناجحة |
| `avg_retries` | متوسط عدد إعادات المحاولة لكل طلب |

```python
protected = ProtectedLLMInterface(llm_interface=my_llm)

# بعد عدة طلبات
protected.generate("Question 1")
protected.generate("Question 2")
protected.generate("Question 3")

stats = protected.get_statistics()

print("=== إحصاءات الواجهة ===")
print(f"إجمالي الطلبات:    {stats['llm_stats']['total_requests']}")
print(f"هلوسات مكتشفة:    {stats['llm_stats']['hallucinations_detected']}")
print(f"إعادات المحاولة:  {stats['llm_stats']['retries_performed']}")
print(f"معدل الهلوسة:     {stats['hallucination_rate']:.1%}")
print(f"معدل النجاح:      {stats['success_rate']:.1%}")
print(f"متوسط الإعادات:  {stats['avg_retries']:.2f}")

print("\n=== إحصاءات الحماية ===")
guard_stats = stats['guard_stats']
print(f"أنواع الهلوسة: {guard_stats.get('hallucination_types', {})}")
```

---

#### `reset_statistics()`

**الوصف:**
يُعيد تعيين إحصاءات الواجهة (`self.stats`) وسجل الـ guard
(`check_history`) معاً في خطوة واحدة.

```python
protected = ProtectedLLMInterface(llm_interface=my_llm)

protected.generate("Some question")
print(protected.stats["total_requests"])  # 1

protected.reset_statistics()
print(protected.stats["total_requests"])  # 0
print(len(protected.guard.check_history)) # 0
```

---

#### `configure_guard(threshold, require_sources, fact_check_enabled, confidence_check_enabled)`

**الوصف:**
يُعدّل إعدادات الـ guard الداخلي في أي وقت بدون الحاجة لإعادة البناء.
فقط المعاملات التي تُمرَّر (غير `None`) تُحدَّث.

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `threshold` | `Optional[float]` | `None` | الحد الأدنى الجديد للثقة |
| `require_sources` | `Optional[bool]` | `None` | هل تشترط المصادر؟ |
| `fact_check_enabled` | `Optional[bool]` | `None` | تفعيل/تعطيل التحقق من الحقائق |
| `confidence_check_enabled` | `Optional[bool]` | `None` | تفعيل/تعطيل تحليل الثقة |

```python
protected = ProtectedLLMInterface(llm_interface=my_llm)

# رفع مستوى الحماية
protected.configure_guard(threshold=0.9)

# تخفيف الحماية مؤقتاً
protected.configure_guard(
    threshold=0.5,
    require_sources=False
)

# تعطيل التحقق من الحقائق فقط
protected.configure_guard(fact_check_enabled=False)
```

---

#### `set_strict_mode(enabled)`

**الوصف:**
يُفعّل أو يُعطّل الوضع الصارم.
في الوضع الصارم يُستبدَل رد الـ LLM المشبوه برسالة رفض رسمية
من `_generate_rejection_message()`.

| Parameter | النوع | الوصف |
|---|---|---|
| `enabled` | `bool` | `True` لتفعيل، `False` لتعطيل |

```python
protected = ProtectedLLMInterface(llm_interface=my_llm)

# تفعيل الوضع الصارم
protected.set_strict_mode(True)

result = protected.generate("Question with uncertain answer")
if result["is_hallucination"]:
    # الرد سيكون رسالة رفض بدلاً من الإجابة
    print(result["response"])  # "⚠️ Response Quality Check Failed..."

# إيقاف الوضع الصارم
protected.set_strict_mode(False)
```

---

#### `set_verbose(enabled)`

**الوصف:**
يُفعّل أو يُعطّل طباعة ملخص الفحص بعد كل استدعاء.
في `verbose=True` يُطبع جدول مفصّل بالنتيجة ومستوى الثقة والأدلة.

| Parameter | النوع | الوصف |
|---|---|---|
| `enabled` | `bool` | `True` لتفعيل، `False` لتعطيل |

```python
protected = ProtectedLLMInterface(llm_interface=my_llm, verbose=True)

# سيطبع ملخصاً مفصّلاً:
# ============================================================
# Hallucination Guard Check: ✅ PASS
# ============================================================
# Confidence Score: 85.00%
# Confidence Level: high
# Recommendation: Response appears reliable...
# ============================================================

# إيقاف الطباعة للإنتاج
protected.set_verbose(False)
```

---

### الدوال المساعدة الداخلية

---

#### `_enhance_prompt(prompt)` *(internal)*

**الوصف:**
يُضيف تعليمات مصداقية ثابتة لنهاية الـ prompt لتوجيه الـ LLM نحو إجابات
أكثر موثوقية. يُستخدم تلقائياً عندما `request_sources=True`.

**التعليمات المُضافة:**
- الاعتماد فقط على حقائق قابلة للتحقق
- الاستشهاد بالمصادر
- الإشارة الصريحة لعدم اليقين
- عدم اختلاق معلومات
- الإقرار بعدم المعرفة

**Return:** `str` — الـ prompt المُعزَّز

---

#### `_create_retry_prompt(original_prompt, check_result, grounding_context)` *(internal)*

**الوصف:**
يبني prompt معدّل للمحاولات التالية يتضمن: نوع المشكلة المكتشفة،
أول 3 أدلة، تعليمات التصحيح، والمصادر المتاحة (حتى 5 مصادر).
يُضاف هذا كـ prefix قبل الـ prompt الأصلي.

| Parameter | النوع | الوصف |
|---|---|---|
| `original_prompt` | `str` | الـ prompt الأصلي المُعزَّز |
| `check_result` | `HallucinationCheck` | نتيجة الفحص الفاشل |
| `grounding_context` | `Optional[GroundingContext]` | السياق لإضافة المصادر |

**Return:** `str` — prompt إعادة المحاولة الكامل

---

#### `_generate_rejection_message(check_result)` *(internal)*

**الوصف:**
يُولّد رسالة رفض رسمية منسّقة للوضع الصارم تشمل:
نوع المشكلة، نتيجة الثقة، قائمة الأدلة، والتوصية،
مع إرشادات للمستخدم لإعادة المحاولة.

| Parameter | النوع | الوصف |
|---|---|---|
| `check_result` | `HallucinationCheck` | نتيجة الفحص |

**Return:** `str` — رسالة الرفض المُنسَّقة

---

#### `_print_check_summary(check_result, retries)` *(internal)*

**الوصف:**
يطبع جدول ملخص مُنسَّق بعد كل فحص. يُستدعى تلقائياً عند `verbose=True`.
يعرض: حالة النجاح/الفشل، النتيجة الرقمية، مستوى الثقة، نوع المشكلة،
أول 5 أدلة، عدد الإعادات، والتوصية.

| Parameter | النوع | الوصف |
|---|---|---|
| `check_result` | `HallucinationCheck` | نتيجة الفحص |
| `retries` | `int` | عدد إعادات المحاولة |

---
---

#  أمثلة متكاملة

---

### مثال 1: استخدام أساسي لـ `HallucinationGuard`

```python
from llm.hallucination import HallucinationGuard, GroundingContext

guard = HallucinationGuard(threshold=0.7)

# بناء السياق
context = GroundingContext(
    sources=["Wikipedia - Eiffel Tower", "Paris Tourism Board"],
    retrieved_facts=[
        "The Eiffel Tower was constructed between 1887 and 1889.",
        "It stands 330 meters tall.",
        "It is located on the Champ de Mars in Paris."
    ],
    context_window="""
        The Eiffel Tower is an iron lattice tower built for the 1889 World's Fair.
        Construction began in 1887 and was completed in 1889.
    """
)

# فحص إجابة صحيحة
good_response = "The Eiffel Tower was built between 1887 and 1889 for the World's Fair."
result = guard.check_response(
    response=good_response,
    grounding_context=context,
    original_query="When was the Eiffel Tower built?"
)

print(f"هلوسة؟ {result.is_hallucination}")        # False
print(f"الثقة: {result.confidence_score:.0%}")     # 85%
print(f"التوصية: {result.recommendation}")

# فحص إجابة خاطئة
bad_response = "The Eiffel Tower was built in 1950. I am absolutely certain of this!"
result = guard.check_response(
    response=bad_response,
    grounding_context=context,
    original_query="When was the Eiffel Tower built?"
)

print(f"\nهلوسة؟ {result.is_hallucination}")       # True
print(f"النوع: {result.hallucination_type.value}") # "factual_error"
print(f"الأدلة: {result.evidence}")
print(f"التوصية: {result.recommendation}")
```

---

### مثال 2: واجهة محمية مع إعادة المحاولة التلقائية

```python
from llm.hallucination import ProtectedLLMInterface
from llm.hallucination import HallucinationGuard
from llm import MistralInterface

llm=MistralInterface(api_key="XXXXXXXXXXXXXXXXXXXX")

guard = HallucinationGuard(threshold=0.7, enable_logging=True)
protected = ProtectedLLMInterface(
    llm_interface=llm,
    hallucination_guard=guard,
    verbose=False
)

# تشغيل دفعة من الأسئلة
test_questions = [
    "What is 2+2?",
        "Who wrote Hamlet?",
    "What is the speed of light?",
    "Who was the 47th US president?",
    "What is the capital of Germany?",
]


for q in test_questions:
    protected.generate(q, max_tokens=100)

# تحليل الإحصاءات
stats = protected.get_statistics()

print("=" * 50)
print("📊 تقرير أداء نظام الحماية")
print("=" * 50)
print(f"إجمالي الطلبات:    {stats['llm_stats']['total_requests']}")
print(f"طلبات ناجحة:      {stats['llm_stats']['successful_responses']}")
print(f"طلبات فاشلة:      {stats['llm_stats']['failed_responses']}")
print(f"إجمالي الإعادات:  {stats['llm_stats']['retries_performed']}")
print(f"معدل الهلوسة:     {stats['hallucination_rate']:.1%}")
print(f"معدل النجاح:      {stats['success_rate']:.1%}")
print(f"متوسط الإعادات:  {stats['avg_retries']:.2f} لكل طلب")

if stats['guard_stats'].get('hallucination_types'):
    print("\n📋 توزيع أنواع الهلوسة:")
    for h_type, count in stats['guard_stats']['hallucination_types'].items():
        print(f"  • {h_type}: {count}")

# إعادة الضبط لجولة جديدة
protected.reset_statistics()
print("\n🔄 تم إعادة ضبط الإحصاءات")
```

---

### مثال 3: الوضع الصارم مع ترتيب إعادة الضبط

```python
from llm.hallucination import ProtectedLLMInterface
from llm.hallucination import HallucinationGuard

# حماية صارمة جداً
guard = HallucinationGuard(threshold=0.9, require_sources=True)
protected = ProtectedLLMInterface(
    llm_interface=my_llm,
    hallucination_guard=guard,
    strict_mode=True,   # يرفض أي إجابة لا تجتاز الفحص
    max_retries=5,
    verbose=False
)

result = protected.generate("What is the GDP of France in 2023?")

if result["is_hallucination"]:
    # في الوضع الصارم الرد سيكون رسالة رفض
    print("❌ تم رفض الإجابة:")
    print(result["response"])  # رسالة ⚠️ Response Quality Check Failed
else:
    print("✅ الإجابة موثوقة:")
    print(result["response"])

# تعديل إعدادات الحماية بدون إعادة بناء
protected.configure_guard(threshold=0.8)
protected.set_strict_mode(False)  # قبول إجابات أقل موثوقية

result2 = protected.generate("What is the GDP of France in 2023?")
print(f"\nمع إعدادات مخففة — هلوسة؟ {result2['is_hallucination']}")
```

---

### مثال 4: معالجة متوازية async لعدة أسئلة

```python
import asyncio
from llm.hallucination import ProtectedLLMInterface
from llm.hallucination import GroundingContext

protected = ProtectedLLMInterface(
    llm_interface=my_async_llm,
    auto_retry=True,
    max_retries=2,
    verbose=False
)

questions = [
    ("What year was Python created?", "Python released in 1991."),
    ("Who invented the telephone?",   "Alexander Bell in 1876."),
    ("When did WW2 end?",             "WW2 ended in 1945."),
]

async def process_all():
    tasks = []
    for question, fact in questions:
        ctx = GroundingContext(
            sources=["Wikipedia"],
            retrieved_facts=[fact],
            context_window=fact
        )
        tasks.append(protected.generate_async(question, grounding_context=ctx))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for (question, _), result in zip(questions, results):
        if isinstance(result, Exception):
            print(f"❌ خطأ: {result}")
        else:
            status = "✅" if not result["is_hallucination"] else "⚠️"
            print(f"{status} {question}")
            print(f"   الثقة: {result['confidence_score']:.0%} | إعادات: {result['retries']}")

asyncio.run(process_all())
```

---

### مثال 5: تتبع الإحصاءات وتحليل الأداء

```python
from llm.hallucination import ProtectedLLMInterface
from llm.hallucination import HallucinationGuard

guard = HallucinationGuard(threshold=0.7, enable_logging=True)
protected = ProtectedLLMInterface(
    llm_interface=my_llm,
    hallucination_guard=guard,
    verbose=False
)

# تشغيل دفعة من الأسئلة
test_questions = [
    "What is 2+2?",
    "Who wrote Hamlet?",
    "What is the speed of light?",
    "Who was the 47th US president?",
    "What is the capital of Germany?",
]

for q in test_questions:
    protected.generate(q, max_tokens=100)

# تحليل الإحصاءات
stats = protected.get_statistics()

print("=" * 50)
print("📊 تقرير أداء نظام الحماية")
print("=" * 50)
print(f"إجمالي الطلبات:    {stats['llm_stats']['total_requests']}")
print(f"طلبات ناجحة:      {stats['llm_stats']['successful_responses']}")
print(f"طلبات فاشلة:      {stats['llm_stats']['failed_responses']}")
print(f"إجمالي الإعادات:  {stats['llm_stats']['retries_performed']}")
print(f"معدل الهلوسة:     {stats['hallucination_rate']:.1%}")
print(f"معدل النجاح:      {stats['success_rate']:.1%}")
print(f"متوسط الإعادات:  {stats['avg_retries']:.2f} لكل طلب")

if stats['guard_stats'].get('hallucination_types'):
    print("\n📋 توزيع أنواع الهلوسة:")
    for h_type, count in stats['guard_stats']['hallucination_types'].items():
        print(f"  • {h_type}: {count}")

# إعادة الضبط لجولة جديدة
protected.reset_statistics()
print("\n🔄 تم إعادة ضبط الإحصاءات")
```
--
### مثال توضيحي 

```python
"""
مثال توضيحي لفكرة Hallucination Detection
==========================================
نستخدم HallucinationGuard مباشرة بدون LLM حقيقي
لنوضح كيف يكتشف النظام أنواع مختلفة من الهلوسة
"""

from llm.hallucination import (
    HallucinationGuard,
    GroundingContext,
    HallucinationType,
)

print("=" * 65)
print("   🧠 Hallucination Detection - مثال توضيحي")
print("=" * 65)

# إنشاء الـ Guard
guard = HallucinationGuard(
    threshold=0.8,
    require_sources=True,
    fact_check_enabled=True,
    confidence_check_enabled=True,
)

# ─────────────────────────────────────────────────────────────
# مثال 1: إجابة موثوقة مع سياق صحيح
# ─────────────────────────────────────────────────────────────
print("\n📌 مثال 1: إجابة موثوقة (مدعومة بمصادر)")
print("-" * 50)

context_1 = GroundingContext(
    sources=[
        "Wikipedia: Python was created by Guido van Rossum in 1991",
        "Python.org: Python 3.0 was released in 2008",
    ],
    retrieved_facts=[
        "Python was created in 1991 by Guido van Rossum",
        "Python 3.0 released in 2008",
    ],
    context_window="Python history and facts"
)

response_1 = (
    "Python was created by Guido van Rossum in 1991. "
    "Python 3.0 was released in 2008 as a major revision."
)

result_1 = guard.check_response(
    response=response_1,
    grounding_context=context_1,
    original_query="Who created Python and when?"
)

status = "✅ موثوقة" if not result_1.is_hallucination else "❌ هلوسة"
print(f"الإجابة : {response_1}")
print(f"النتيجة : {status}")
print(f"درجة الثقة : {result_1.confidence_score:.0%}")
print(f"التوصية : {result_1.recommendation}")


# ─────────────────────────────────────────────────────────────
# مثال 2: هلوسة - معلومات مختلقة (Overconfidence)
# ─────────────────────────────────────────────────────────────
print("\n📌 مثال 2: هلوسة - ثقة زائدة بدون دليل (Overconfidence)")
print("-" * 50)

response_2 = (
    "Python is absolutely the fastest programming language ever created. "
    "It is definitely and certainly 100% better than every other language. "
    "There is no doubt that Python always outperforms C++ in all benchmarks."
)

result_2 = guard.check_response(
    response=response_2,
    grounding_context=None,   # لا يوجد سياق
    original_query="Is Python fast?"
)

status = "✅ موثوقة" if not result_2.is_hallucination else "❌ هلوسة"
print(f"الإجابة : {response_2[:80]}...")
print(f"النتيجة : {status}")
print(f"درجة الثقة : {result_2.confidence_score:.0%}")
if result_2.hallucination_type:
    print(f"نوع الهلوسة : {result_2.hallucination_type.value}")
if result_2.evidence:
    for e in result_2.evidence:
        print(f"  ⚠️  {e}")
print(f"التوصية : {result_2.recommendation}")


# ─────────────────────────────────────────────────────────────
# مثال 3: هلوسة - تناقض داخلي (Conflicting Info)
# ─────────────────────────────────────────────────────────────
print("\n📌 مثال 3: هلوسة - تناقض داخلي (Conflicting Info)")
print("-" * 50)

response_3 = (
    "The Earth is not round. "
    "Scientists have no doubt confirmed the Earth is perfectly round and spherical. "
    "The Earth is not a sphere according to modern research."
)

result_3 = guard.check_response(
    response=response_3,
    grounding_context=None,
    original_query="What is the shape of the Earth?"
)

status = "✅ موثوقة" if not result_3.is_hallucination else "❌ هلوسة"
print(f"الإجابة : {response_3}")
print(f"النتيجة : {status}")
print(f"درجة الثقة : {result_3.confidence_score:.0%}")
if result_3.hallucination_type:
    print(f"نوع الهلوسة : {result_3.hallucination_type.value}")
if result_3.evidence:
    for e in result_3.evidence:
        print(f"  ⚠️  {e}")
print(f"التوصية : {result_3.recommendation}")


# ─────────────────────────────────────────────────────────────
# إحصائيات الجلسة
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("📊 إحصائيات الجلسة")
print("=" * 65)
stats = guard.get_statistics()
print(f"  إجمالي الفحوصات    : {stats['total_checks']}")
print(f"  هلوسة مكتشفة      : {stats['hallucinations_detected']}")
print(f"  نسبة الهلوسة       : {stats['hallucination_rate']:.0%}")
print(f"  متوسط درجة الثقة  : {stats['average_confidence_score']:.0%}")
if stats['hallucination_types']:
    print(f"  أنواع الهلوسة      : {stats['hallucination_types']}")
print("=" * 65)
```
---

## 📊 ملخص مقارنة الكلاسَين

| الميزة | `HallucinationGuard` | `ProtectedLLMInterface` |
|---|---|---|
| **الوظيفة الأساسية** | كشف وتقييم الهلوسة | تغليف الـ LLM بالحماية |
| **المدخل** | نص إجابة جاهزة | prompt مباشر للـ LLM |
| **إعادة المحاولة** | ✗ | ✓ تلقائياً |
| **تعزيز الـ prompt** | ✗ | ✓ تلقائياً |
| **الوضع الصارم** | ✗ | ✓ |
| **دعم async** | عبر `async_parse` الموروثة | ✓ `generate_async` |
| **الإحصاءات** | `get_statistics()` للفحوصات | `get_statistics()` مدمجة |
| **التخصيص** | إعدادات في `__init__` | `configure_guard()` ديناميكي |
| **يُستخدم وحده** | ✓ | يحتاج LLM interface |

---

## 🔑 نقاط جوهرية

- **درجة الثقة** هي قيمة من 0–1 تُمثّل موثوقية الإجابة؛ أي قيمة **أقل من `threshold`** تُعدّ هلوسة
- **`GroundingContext`** هو مفتاح الفحص الجيد — بدونه تُجرى فحوصات أقل (فقط التناقضات وعلامات الثقة)
- **الـ penalty** في الفحوصات الفاشلة يُخفّض نتيجتها بنسبة 50% وليس يُلغيها، مما يُعطي تقييماً أكثر مرونة
- **`AutoRetry`** يُخفّض الـ temperature تدريجياً في كل إعادة محاولة: `max(0.3, temp - retries × 0.1)`
- **الوضع الصارم** لا يوقف التوليد، بل يُبدّل الإجابة برسالة رفض — الـ LLM يعمل دائماً
- **`configure_guard()`** يسمح بتغيير إعدادات الحماية ديناميكياً بين الطلبات بدون إعادة بناء الكائن


# 🚨 خطأ Gemini 429 RESOURCE_EXHAUSTED

## 📌 نظرة عامة
يظهر هذا الخطأ عند استخدام `ProtectedLLMInterface` مع واجهة Gemini، حيث تفشل الطلبات بالرسالة التالية:


---

## ❗ وصف المشكلة

عند تنفيذ عدة استعلامات باستخدام نظام يحتوي على **حماية من الهلوسة (Hallucination Guard)**، يحدث:

- تجاوز لحدود عدد الطلبات (Rate Limit)
- استهلاك سريع للكوتا (Quota)
- إعادة محاولات (Retries) تزيد المشكلة سوءًا

---

## 🧠 السبب الجذري

المشكلة ليست في الكود نفسه، بل في **طريقة استهلاك API**.

### 🔍 الأسباب الرئيسية:

### 1. تعدد الطلبات بشكل غير مباشر
كل استدعاء:
```python
protected.generate(q)
```
قد يؤدي داخليًا إلى:

توليد الإجابة

تحليل الهلوسة

إعادة الطلب (Retry)

👉 النتيجة:

سؤال واحد ≈ من 2 إلى 5 طلبات API
2. قيود صارمة في Gemini

واجهة Gemini تفرض:

حد أقصى لعدد الطلبات في الدقيقة

حد لاستهلاك التوكنز

حساسية عالية للطلبات المتتالية (Burst)

3. تضخيم الطلبات بسبب إعادة المحاولة

عند اكتشاف هلوسة:

يتم إعادة إرسال الطلب تلقائيًا

مما يؤدي إلى زيادة الضغط على API بشكل كبير

⚖️ مقارنة مهمة
الخاصية	Gemini API	نماذج أخرى (مثل Mistral)
صرامة القيود	عالية 🔴	متوسطة 🟢
تحمل إعادة المحاولة	ضعيف	أعلى
التعامل مع الضغط	حساس	أكثر مرونة

✅ الحلول
🥇 الحل الأساسي (الأهم)

تعطيل إعادة المحاولة:
```python
protected = ProtectedLLMInterface(
    llm_interface=gemi,
    hallucination_guard=guard,
    max_retries=0
)
```
🥈 تقليل حساسية اكتشاف الهلوسة

```python
guard = HallucinationGuard(
    threshold=0.9,
    enable_logging=True
)
```
🥉 إضافة تأخير بين الطلبات
```python
import time
for q in test_questions:
    protected.generate(q)
    time.sleep(2)
```
🚀 أفضل تصميم للنظام
بدلاً من إعادة الطلب داخل الحماية:
❌ تجنب:
LLM → Guard → Retry → LLM
✅ استخدم:
LLM → Guard (تحليل فقط) → طبقة اتخاذ القرار

💡 استراتيجية موصى بها
استخدم Gemini في:
الطلبات الفردية عالية الجودة
تجنب:
الأنظمة التي تعتمد على إعادة المحاولة بكثرة
الحلقات الثقيلة (Heavy Loops)