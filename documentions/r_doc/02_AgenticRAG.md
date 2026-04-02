
## نظرة عامة

`AgenticRAG` هو نظام RAG ذكي يعمل بشكل مستقل عبر **حلقة تكرارية** يقرر فيها بنفسه متى يسترجع، ومتى يحسّن، ومتى يتوقف ويُجيب.

```
User Query
    │
    ▼
┌───────────────────────────────────────────┐
│              حلقة القرار                  │
│  ┌─────────┐   ┌───────────┐   ┌────────┐│
│  │RETRIEVE │──▶│CHECK/REFINE│──▶│GENERATE││
│  └─────────┘   └───────────┘   └────────┘│
└───────────────────────────────────────────┘
    │
    ▼
AgenticResult (answer + docs + history + confidence)
```



---

## الاستثناءات

> ⚠️ **هذا القسم غائب تمامًا في التوثيق الأصلي.**

يرفع النظام استثناءات مخصصة بدلًا من الاستثناءات العامة، مما يُسهّل التعامل الدقيق مع الأخطاء.

```
AgenticRAGError          ← الاستثناء الأساسي لكل أخطاء النظام
    ├── RetrievalError       ← فشل في استرجاع المستندات من الـ backend
    ├── GenerationError      ← فشل في توليد الإجابة
    └── MaxIterationsExceeded ← تجاوز الحد الأقصى للتكرارات (مُعرَّف لكن لا يُرفع تلقائيًا)
```

### مثال للتعامل مع الاستثناءات

```python
from rag.agentic_rag import AgenticRAG, RetrievalError, GenerationError, AgenticRAGError

try:
    result = agent.query("ما هو الذكاء الاصطناعي؟")
except RetrievalError as e:
    print(f"فشل الاسترجاع: {e}")
except GenerationError as e:
    print(f"فشل التوليد: {e}")
except AgenticRAGError as e:
    print(f"خطأ عام في النظام: {e}")
```

### ملاحظات مهمة

- `RetrievalError` تُرفع داخليًا ويعيد النظام المحاولة تلقائيًا (`retry_attempts` مرات) قبل الاستسلام وإرجاع قائمة فارغة.
- `GenerationError` تُرفع داخليًا وعند استنفاد المحاولات تُعاد `_fallback_answer`.
- `MaxIterationsExceeded` معرَّفة لكن **لا يرفعها النظام تلقائيًا** — بل يسجّل تحذيرًا ويكمل.
- `ValueError` تُرفع إذا كان الاستعلام فارغًا (`query.strip() == ""`).

---

## الفئات المساعدة

### Document

```python
@dataclass
class Document:
    text: str                          # محتوى المستند النصي
    score: float = 0.0                 # درجة الصلة بالاستعلام [0.0, 1.0]
    metadata: Dict[str, Any] = {}      # بيانات وصفية إضافية
    source: str = ""                   # مصدر المستند (معرّف القطعة، اسم الملف)
```

#### الدوال

| الدالة | الوصف |
|--------|-------|
| `snippet(max_chars=300)` | إرجاع معاينة مقتطعة من النص. تُضاف `…` إذا كان النص أطول من `max_chars`. |

```python
doc = Document(text="نص طويل جدًا...", score=0.85, source="ai_history")
print(doc.snippet(50))  # "نص طويل جدًا…" (مقتطع عند 50 حرف)
```

---

### ActionStep

يُسجّل قرارًا واحدًا اتخذه الوكيل.

```python
@dataclass
class ActionStep:
    iteration: int                       # رقم التكرار الحالي
    action: AgentAction                  # نوع القرار (RETRIEVE, GENERATE, ...)
    query: str                           # الاستعلام المُستخدم في هذه الخطوة
    details: str = ""                    # تفاصيل إضافية (عدد الـ docs، نص الـ refinement)
    duration_ms: float = 0.0             # زمن تنفيذ القرار بالميلي ثانية
    confidence: float = 0.0             # درجة الثقة بعد هذه الخطوة
    refined_query: Optional[str] = None  # الاستعلام المحسَّن (إن وُجد تحسين)
```

---

### AgenticResult

النتيجة الكاملة المُرجَعة من `agent.query()`.

```python
@dataclass
class AgenticResult:
    answer: str                         # الإجابة النصية النهائية
    retrieved_docs: List[Document]      # المستندات المُسترجَعة والمُصفّاة
    action_history: List[ActionStep]    # سجل كل القرارات المتخذة
    iterations: int                     # عدد التكرارات الفعلي
    reasoning: str                      # شرح نصي مُنسَّق لمسار التفكير
    confidence: float = 0.0            # درجة الثقة النهائية [0.0, 1.0]
    cached: bool = False                # هل الإجابة من الكاش؟
```

#### الدوال

```python
result.to_dict() -> Dict[str, Any]
```

يُرجع قاموسًا يحتوي على: `answer`, `docs_used`, `iterations`, `confidence`, `cached`, `reasoning`.

> ⚠️ **لا يتضمن `to_dict()` قائمة الـ docs الكاملة ولا `action_history`** — للوصول الكامل استخدم الخصائص مباشرة.

---

### TTLCache

> ⚠️ **هذه الفئة غائبة كليًا عن التوثيق الأصلي.**

كاش في الذاكرة بصلاحية زمنية (Time-To-Live) لنتائج الاسترجاع.

```python
class TTLCache:
    def __init__(self, ttl_seconds: int = 300)

    def get(self, query: str) -> Optional[List[Document]]
    # يُرجع الـ docs إذا كان المفتاح موجودًا وضمن الـ TTL، وإلا None

    def set(self, query: str, docs: List[Document]) -> None
    # يخزّن النتيجة مع timestamp

    def clear(self) -> None
    # يمسح كل الإدخالات
```

**خصائص مهمة:**
- المفاتيح: `SHA-256` لنص الاستعلام
- **غير آمنة للاستخدام المتزامن (thread-unsafe)** — مخصصة لعملية واحدة
- الانتهاء الزمني يُتحقق منه عند الـ `get`، لا بـ daemon thread

---

## AgenticConfig — الإعدادات الكاملة

```python
@dataclass
class AgenticConfig:
    max_iterations: int = 5
    # الحد الأقصى لعدد تكرارات الحلقة. عند بلوغه يُجبر النظام على GENERATE.

    min_confidence: float = 0.7
    # الحد الأدنى لمتوسط درجات الـ docs لاعتبار المعلومات كافية.

    min_docs_required: int = 2
    # الحد الأدنى لعدد الـ docs المطلوبة قبل اعتبار المعلومات كافية.

    enable_query_refinement: bool = True
    # تفعيل إعادة صياغة الاستعلام عند انخفاض الدرجات.

    enable_self_correction: bool = True
    # تفعيل مرور التصحيح الذاتي على الإجابة بعد توليدها.

    enable_sufficiency_check: bool = True
    # تفعيل سؤال الـ LLM عما إذا كانت المعلومات كافية.

    reasoning_depth: ReasoningDepth = ReasoningDepth.MEDIUM
    # يتحكم في تعقيد الـ prompt المُستخدم في تحسين الاستعلام (انظر قسم _refine_query).

    cache_ttl_seconds: int = 300
    # مدة صلاحية كاش الاسترجاع بالثواني. 0 = تعطيل الكاش.

    retry_attempts: int = 2
    # عدد مرات إعادة المحاولة عند فشل الاسترجاع أو التوليد.

    retry_backoff_base: float = 0.5
    # القاعدة الزمنية للتأخير الأسي بين المحاولات (ثانية).
    # المحاولة الأولى: 0.5s، الثانية: 1.0s، الثالثة: 2.0s ...
```

### ReasoningDepth

```python
class ReasoningDepth(str, Enum):
    SHALLOW = "shallow"   # إعادة صياغة مختصرة في جملة واحدة
    MEDIUM  = "medium"    # جملة واضحة مع إضافة تفاصيل (الافتراضي)
    DEEP    = "deep"      # توسيع النطاق وإضافة أسئلة فرعية إن لزم
```

---

## AgenticRAG — الفئة الرئيسية

### `__init__`

```python
AgenticRAG(
    rag_system: Any,
    config: Optional[AgenticConfig] = None,
    llm: Optional[Any] = None,
    on_action: Optional[Callable[[ActionStep], None]] = None,
)
```

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `rag_system` | `Any` | النظام الأساسي. يجب أن يحتوي على `retrieve(query)` و `generate(query)` أو `query(query)`. |
| `config` | `AgenticConfig` | إعدادات الوكيل. الافتراضي: `AgenticConfig()` بقيمه الافتراضية. |
| `llm` | `Any` | نموذج اللغة. إذا لم يُحدَّد يُستخدم `rag_system.llm`. إذا لم يُوجد يتعطل القرار والـ refinement. |
| `on_action` | `Callable[[ActionStep], None]` | callback اختياري يُستدعى بعد كل خطوة. **الأخطاء داخله لا تُوقف الحلقة الرئيسية.** |

**خصائص داخلية تُهيَّأ في `__init__`:**

```python
self._cache        # TTLCache للاسترجاع (مفاتيح: query → List[Document])
self._result_cache # Dict[str, AgenticResult] كاش النتائج الكاملة (مفاتيح: SHA-256 للاستعلام)
```

---

## الواجهة العامة

### `query`

```python
query(query: str, context: Optional[Dict[str, Any]] = None) -> AgenticResult
```

**السلوك:**
1. يتحقق من الكاش أولًا (بمستوييه). إذا وُجدت نتيجة يُرجعها فورًا مع `cached=True`.
2. يُشغّل حلقة القرار (انظر [منطق القرار الداخلي](#منطق-القرار-الداخلي)).
3. يُزيل الـ docs المكررة.
4. يُولّد الإجابة مع retry.
5. إذا كان `enable_self_correction=True` يمرر الإجابة على `_self_correct`.
6. يحسب الثقة النهائية ويبني `AgenticResult`.
7. يخزّن النتيجة في `_result_cache`.

**Return:**
- `ValueError` إذا كان الاستعلام فارغًا.

---

### `add_document`

```python
add_document(text: str, metadata: Optional[Dict] = None) -> Any
```

يُضيف مستندًا واحدًا للنظام الأساسي. يمرر العملية كاملةً لـ `rag_system.add_document`.

---

### `add_documents`

```python
add_documents(documents: List[str], metadatas: Optional[List[Dict]] = None) -> Any
```

يُضيف مجموعة مستندات دفعةً واحدة. يمرر العملية لـ `rag_system.add_documents`.

---

### `clear_cache`

```python
clear_cache() -> None
```

يمسح **مستويَي الكاش معًا**: كاش الاسترجاع (`TTLCache`) وكاش النتائج الكاملة (`_result_cache`). ينبغي استدعاؤه بعد تحديث قاعدة البيانات.

---

## الواجهة غير المتزامنة

### `aquery`

```python
async def aquery(query: str, **kwargs) -> AgenticResult
```

يُشغّل نفس منطق `query()` داخل thread منفصل عبر `asyncio.to_thread`، مما يجعله آمنًا للاستخدام في event loop.

```python
# استعلام واحد
result = await agent.aquery("ما هو الذكاء الاصطناعي؟")

# استعلامات متوازية
results = await asyncio.gather(
    agent.aquery("سؤال 1"),
    agent.aquery("سؤال 2"),
    agent.aquery("سؤال 3"),
)
```

---

### `astream_query`

```python
async def astream_query(query: str) -> AsyncGenerator[str, None]
```

يُشغّل حلقة القرار كاملةً ثم يَبُثّ الإجابة النهائية **token بـ token** فور وصولها.

> ⚠️ **شرط مهم:** يتطلب أن يمتلك الـ `llm` دالة `astream(prompt)` غير متزامنة. إذا لم تكن موجودة يُرجع رسالة خطأ مباشرةً:
> ```
> ❌ نموذج اللغة لا يدعم الـ streaming.
> ```

**الاستخدام:**

```python
async for token in agent.astream_query("كيف تطور الذكاء الاصطناعي؟"):
    print(token, end="", flush=True)
print()
```

**الفرق عن `aquery`:**

| | `aquery` | `astream_query` |
|--|----------|-----------------|
| يُرجع | `AgenticResult` كامل | tokens نصية واحدة تلو الأخرى |
| يدعم الكاش | ✅ نعم | ❌ لا (حلقة مستقلة) |
| يتطلب `llm.astream` | ❌ لا | ✅ نعم |
| يدعم `enable_self_correction` | ✅ نعم | ❌ لا |
| مفيد لـ | نتيجة كاملة، معالجة دفعية | واجهات المستخدم التفاعلية |

---

## Context Manager

يدعم النظام بروتوكول `async context manager`:

```python
async with AgenticRAG(rag_system, config=config) as agent:
    result = await agent.aquery("ما هو الذكاء الاصطناعي؟")
    print(result.answer)
```

> **ملاحظة:** `__aexit__` يُرجع `False` فقط ولا يُجري أي تنظيف خاص — لا يُغلق اتصالات ولا يمسح الكاش تلقائيًا.

---

## منطق القرار الداخلي

> ⚠️ **هذا القسم غائب في التوثيق الأصلي.**

الدالة `_decide_action(query, retrieved_docs, iteration)` تتبع **ترتيبًا صارمًا للأولويات**:

```
الأولوية 1: iteration == 1  أو  لا توجد docs
    → RETRIEVE  (دائمًا نبدأ بالاسترجاع)

الأولوية 2: iteration >= max_iterations
    → GENERATE  (ضمان الإجابة دائمًا)

الأولوية 3: enable_sufficiency_check == True  AND  iteration % 2 == 0
    → CHECK_SUFFICIENCY  (في التكرارات الزوجية: 2، 4، ...)

الأولوية 4: enable_query_refinement == True  AND  iteration < 4
         AND  avg_score(docs) < min_confidence
    → REFINE_QUERY

الافتراضي:
    → GENERATE
```

**جدول مسارات القرار النموذجية (max_iterations=5):**

| التكرار | docs موجودة؟ | avg_score | القرار |
|---------|-------------|-----------|--------|
| 1 | لا يهم | - | RETRIEVE |
| 2 | نعم | < 0.7 | CHECK_SUFFICIENCY (زوجي) |
| 3 | نعم | < 0.7 | REFINE_QUERY (إذا < 4) |
| 4 | نعم | أي قيمة | CHECK_SUFFICIENCY (زوجي) |
| 5 | نعم | أي قيمة | GENERATE (بلغ max) |

**سلوك REFINE_QUERY عند عدم التغيير:**

إذا أرجع الـ LLM نفس الاستعلام (أو رفض التحسين)، يُجبر النظام على استدعاء `RETRIEVE` مجددًا بدلًا من الدوران في حلقة.

---

## نظام الكاش بمستوييه

> ⚠️ **التوثيق الأصلي يذكر الكاش لكن لا يُفصّل مستوييه.**

يعمل النظام بـ **مستويَين مستقلَّين من الكاش**:

```
المستوى 1: TTLCache (self._cache)
    المفتاح : SHA-256 للاستعلام
    القيمة  : List[Document]
    الصلاحية: cache_ttl_seconds (افتراضي 300 ثانية)
    الغرض   : تجنب الاستدعاء المتكرر لقاعدة البيانات بنفس الاستعلام

المستوى 2: Result Cache (self._result_cache)
    المفتاح : SHA-256 لـ query.lower().strip()
    القيمة  : AgenticResult كامل
    الصلاحية: لا تنتهي (طوال حياة الـ object)
    الغرض   : إرجاع نتيجة كاملة فورية لاستعلامات متطابقة
```

**ترتيب التحقق عند `query()`:**

```
1. ابحث في _result_cache
   → وُجد: أرجع النتيجة فورًا (cached=True) ← أسرع
   → لم يوجد: تابع

2. أثناء حلقة القرار عند كل RETRIEVE:
   → ابحث في TTLCache (self._cache)
      → وُجد وضمن TTL: استخدم الـ docs المخزّنة
      → لم يوجد أو انتهت الصلاحية: استدعِ backend واخزّن
```

**مخطط الـ caching:**

```
query("X")
    │
    ├─▶ _result_cache["X"]? ──▶ YES ──▶ return cached AgenticResult
    │
    NO
    │
    ▼
حلقة القرار
    │
    ├─▶ RETRIEVE "X"
    │       │
    │       ├─▶ TTLCache["X"]? ──▶ YES ──▶ return cached docs
    │       │
    │       NO
    │       │
    │       └─▶ backend.retrieve("X") ──▶ normalise ──▶ TTLCache.set("X", docs)
    │
    ▼
generate answer
    │
    ▼
_result_cache["X"] = AgenticResult
    │
    ▼
return AgenticResult
```

---

## دعم الـ Backends المختلفة

> ⚠️ **هذا القسم غائب تمامًا في التوثيق الأصلي.**

الدالة `_normalise_docs(raw)` تحوّل أي مخرجات من الـ backend إلى `List[Document]`.

**الأنواع المدعومة:**

### 1. `Document` مباشرة

```python
# Backend يُرجع Document objects مباشرة
[Document(text="...", score=0.9)]
```

### 2. `Tuple[chunk, float]` — صيغة FAISS

```python
# شائعة في FAISS وبعض قواعد البيانات المتجهية
[(DocumentChunk_object, 0.87), (DocumentChunk_object, 0.65)]
```

الـ `chunk` يُفحص عن: `text` أو `page_content` أو `content` (بالترتيب).  
المصدر يُستخرج من: `chunk_id` أو `doc_id` أو `id`.

### 3. `Dict` مع مفاتيح نصية

```python
[
    {"text": "...", "score": 0.8, "metadata": {}, "source": "doc1"},
    {"content": "...", "relevance": 0.75}  # أسماء مفاتيح بديلة مدعومة
]
```

المفاتيح البديلة المدعومة: `content` بدل `text`، `relevance` بدل `score`، `id` بدل `source`.

### 4. `{"results": [...]}` — صيغة ملفوفة

```python
# بعض الـ backends تُرجع dict مع مفتاح "results"
{"results": [{"text": "...", "score": 0.9}]}
```

يُفكّ الغلاف تلقائيًا قبل المعالجة.

---

## آلية حساب الثقة

> ⚠️ **التوثيق الأصلي يذكر "درجة الثقة" لكن لا يشرح كيف تُحسب.**

الدالة `_compute_confidence(docs)` تستخدم **متوسطًا موزونًا تنازليًا** — الـ docs الأعلى درجةً تحظى بوزن أكبر.

**الخوارزمية:**

```python
# 1. ترتيب الـ docs تنازليًا حسب الدرجة
sorted_docs = sorted(docs, key=lambda d: d.score, reverse=True)

# 2. حساب الأوزان: الأول يأخذ 1، الثاني 0.5، الثالث 0.33، ...
weights = [1/(i+1) for i in range(len(sorted_docs))]

# 3. المتوسط الموزون
confidence = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)

# 4. تحديد بـ [0, 1]
confidence = min(confidence, 1.0)
```

**مثال:**

```
docs = [score=0.9, score=0.5, score=0.3]
weights = [1.0, 0.5, 0.333]
total_weight = 1.833

confidence = (0.9×1.0 + 0.5×0.5 + 0.3×0.333) / 1.833
           = (0.9 + 0.25 + 0.1) / 1.833
           = 0.682
```

> هذا يعني أن **doc واحد بدرجة عالية** يرفع الثقة أكثر من عدة docs بدرجات متوسطة.

---

## تحسين الاستعلام

الدالة `_refine_query(query, retrieved_docs)` تطلب من الـ LLM إعادة صياغة الاستعلام عند انخفاض الدرجات.

**المدخلات للـ prompt:**
- الاستعلام الأصلي
- مقتطفات من أول 3 docs (200 حرف لكل doc)

**تأثير `reasoning_depth` على الـ prompt:**

| القيمة | التوجيه المُضاف للـ LLM |
|--------|------------------------|
| `SHALLOW` | "in one concise sentence" |
| `MEDIUM`  | "in one clear sentence, adding specificity" |
| `DEEP`    | "expanding scope and adding sub-questions if needed" |

**حالات العودة للاستعلام الأصلي (Fallback):**
- الـ LLM غير متاح
- لا توجد docs بعد
- النتيجة مطابقة للاستعلام الأصلي
- النتيجة أقصر من 5 أحرف
- رُفع استثناء أثناء الاستدعاء

---

## فحص كفاية المعلومات

> ⚠️ **التوثيق الأصلي يذكر وجود الفحص لكن لا يُفصّل منطقه الثلاثي المستويات.**

الدالة `_is_information_sufficient(query, retrieved_docs)` تتبع **منطقًا ثلاثي المستويات** — اقتصاديًا في استخدام الـ LLM:

```
المستوى 1: الفحص السريع (بدون LLM)
    ├── len(docs) < min_docs_required  →  False (أقل من الحد الأدنى)
    ├── avg_score >= min_confidence    →  True  (جودة عالية واضحة)
    └── avg_score < 0.3               →  False (جودة منخفضة واضحة)

المستوى 2: الحالة الحدية (0.3 ≤ avg_score < min_confidence)
    ├── لا يوجد LLM  →  True إذا len(docs) >= 3
    └── يوجد LLM    →  اسأل الـ LLM ("yes" / "no")
                       فشل الاستدعاء → True إذا len(docs) >= 3
```

---

## التصحيح الذاتي

الدالة `_self_correct(query, answer, retrieved_docs)` تطلب من الـ LLM مراجعة الإجابة.

**الـ prompt يحتوي على:**
- الاستعلام الأصلي
- مقتطفات من أول 4 docs (300 حرف لكل doc)
- الإجابة المسودة

**يطلب من الـ LLM:** إرجاع الإجابة كما هي إذا كانت صحيحة، أو نسخة مصحَّحة إذا كانت بها أخطاء.

**حالات الرجوع للإجابة الأصلية:**
- لا يوجد `llm`
- الإجابة فارغة
- النتيجة المُصحَّحة أقصر من 10 أحرف
- رُفع استثناء

---

## إزالة التكرار

> ⚠️ **غائب من التوثيق الأصلي.**

الدالة `_deduplicate(docs)` تُزيل الـ docs المكررة **بعد** اكتمال حلقة القرار وقبل التوليد.

**الخوارزمية:**
- المفتاح: `MD5(doc.text.encode())`
- عند وجود doc مكرر يُحتفظ **بالأعلى درجةً** منهما

```python
# مثال: doc نفسه مُسترجَع مرتين بدرجات مختلفة
[Document(text="A", score=0.9), Document(text="A", score=0.6)]
# بعد التصفية:
[Document(text="A", score=0.9)]  # الأعلى درجة فقط
```

---

## الاسترجاع مع إعادة المحاولة

> ⚠️ **التوثيق الأصلي يذكر `retry_attempts` لكن لا يشرح آلية الـ backoff.**

`_retrieve_with_retry` و `_generate_answer_with_retry` يتبعان نفس النمط:

```
محاولة 0: فشل → انتظر retry_backoff_base * (2^0) ثانية
محاولة 1: فشل → انتظر retry_backoff_base * (2^1) ثانية
...
محاولة retry_attempts: فشل → استسلم

مثال (retry_attempts=2, retry_backoff_base=0.5):
    المحاولة 0 فشلت → انتظر 0.5s
    المحاولة 1 فشلت → انتظر 1.0s
    المحاولة 2 فشلت → أرجع [] (للاسترجاع) أو fallback_answer (للتوليد)
```

---

## الإجابة الاحتياطية

> ⚠️ **غائب من التوثيق الأصلي.**

`_fallback_answer(docs)` تُستدعى عند استنفاد كل محاولات التوليد.

```python
# إذا لا توجد docs:
return "i cant find anything for you"

# إذا توجد docs:
return "based on the following snippets:\n\n• [snippet 1]\n\n• [snippet 2]\n\n• [snippet 3]"
# (أول 3 docs، 400 حرف لكل منها)
```

> **ملاحظة:** الرسائل الاحتياطية بالإنجليزية في الكود الحالي حتى عند استخدام الـ prompts العربية. يُنصح بتخصيصها عند النشر.

---

## مثال عملي كامل

```python
from chunks import MultilanguageTextChunker
from embeddings import MistralEmbedder
from llm import MistralInterface
from vector_database import FAISSVectorDatabase
from context import ContextManager
from rag.core import RAGSystem, RAGConfig
from rag.agentic_rag import AgenticRAG
from rag.agentic_rag import AgenticConfig, ReasoningDepth
from rag.core import RAGSystem , RAGConfig
embedder = MistralEmbedder(api_key=api)
vector_db = FAISSVectorDatabase(embedder=embedder)
llm = MistralInterface(api_key=api)
chunker = MultilanguageTextChunker(chunk_size=500, overlap=50)
ctx_manager = ContextManager()


# ─────────────────────────────────────────────────────────────────────────────
# 3. إنشاء RAG System الأساسي | Create base RAG system
# ─────────────────────────────────────────────────────────────────────────────
rag_config = RAGConfig(top_k=5, prompt_language="ar")

base_rag = RAGSystem(
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
    config=rag_config,
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. إضافة المستندات | Add documents
# ─────────────────────────────────────────────────────────────────────────────
print("📄 جاري إضافة المستندات...")

docs = {
    "ai_history": """
        نشأ الذكاء الاصطناعي في خمسينيات القرن العشرين على يد علماء
        أمثال آلان تورينج وجون مكارثي. أول مؤتمر للذكاء الاصطناعي
        أُقيم عام 1956 في دارتموث. كان الهدف الأول بناء آلات تفكر
        مثل البشر، لكن القيود التقنية أبطأت التقدم لعقود.
    """,
    "ml_revolution": """
        في العقد الثاني من الألفية الثالثة، أحدث التعلم العميق ثورة
        في مجال الذكاء الاصطناعي. ظهرت نماذج ضخمة مثل GPT وBERT
        غيّرت كيفية معالجة اللغة الطبيعية. شبكات الخصوم التوليدية
        (GANs) مكّنت من توليد صور واقعية بشكل مذهل.
    """,
    "ai_applications": """
        تطبيقات الذكاء الاصطناعي تشمل: التعرف على الصور، ترجمة اللغات،
        القيادة الذاتية، التشخيص الطبي، توصيات المحتوى، والمساعدين الذكيين.
        تستخدم شركات مثل Google وMeta وAmazon الذكاء الاصطناعي في معظم
        منتجاتها الأساسية.
    """,
    "llm_overview": """
        نماذج اللغة الكبيرة (LLMs) هي أنظمة ذكاء اصطناعي مدرّبة على
        كميات ضخمة من النصوص. تشمل أبرزها: GPT-4 من OpenAI،
        Claude من Anthropic، وGemini من Google. تتميز بقدرتها على
        فهم السياق وتوليد نصوص متماسكة بلغات متعددة.
    """,
    "future_ai": """
        مستقبل الذكاء الاصطناعي يتجه نحو الأنظمة متعددة الوسائط التي
        تجمع النصوص والصور والصوت. يُتوقع أن يصل الذكاء الاصطناعي العام
        (AGI) خلال العقود القادمة. التحديات الأخلاقية والأمان تُعدّ
        من أبرز القضايا التي تشغل الباحثين حالياً.
    """,
}

results = base_rag.add_documents(docs)
for doc_id, chunk_count in results.items():
    print(f"  ✅ {doc_id}: {chunk_count} قطعة")

# ─────────────────────────────────────────────────────────────────────────────
# 5. إعداد AgenticRAG | Setup AgenticRAG
# ─────────────────────────────────────────────────────────────────────────────

# callback لمتابعة خطوات الوكيل في الوقت الفعلي
def on_action(step):
    icons = {
        "retrieve":           "📥",
        "generate":           "✍️",
        "refine_query":       "🔄",
        "check_sufficiency":  "🔍",
        "stop":               "🛑",
    }
    icon = icons.get(step.action.value, "▶️")
    print(
        f"  {icon} [{step.iteration}] {step.action.value:<22} "
        f"| ثقة: {step.confidence:.2f} "
        f"| {step.duration_ms:.0f}ms"
        + (f" | {step.details}" if step.details else "")
    )


agentic_config = AgenticConfig(
    max_iterations=5,
    min_confidence=0.65,
    min_docs_required=2,
    enable_query_refinement=True,
    enable_sufficiency_check=True,
    enable_self_correction=True,
    reasoning_depth=ReasoningDepth.MEDIUM,
    cache_ttl_seconds=300,
    retry_attempts=2,
)

agent = AgenticRAG(
    rag_system=base_rag,
    config=agentic_config,
    on_action=on_action,
)

# 6. استعلام مفصّل | Detailed query
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("🤔 الاستعلام الأول: تاريخ وتطور الذكاء الاصطناعي")
print("="*60)

result = agent.query("كيف تطور الذكاء الاصطناعي من الخمسينيات حتى اليوم؟")

print(f"\n✅ الإجابة:\n{result.answer}")
print(f"\n📊 إحصائيات:")
print(f"  • التكرارات المستخدمة : {result.iterations}")
print(f"  • درجة الثقة          : {result.confidence:.2%}")
print(f"  • المستندات المسترجعة : {len(result.retrieved_docs)}")
print(f"  • من الكاش            : {result.cached}")
print(f"\n🧠 سلسلة التفكير:\n{result.reasoning}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. اختبار الكاش | Cache test
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("⚡ اختبار الكاش — نفس الاستعلام مرة ثانية")
print("="*60)

result_cached = agent.query("كيف تطور الذكاء الاصطناعي من الخمسينيات حتى اليوم؟")
print(f"  من الكاش: {result_cached.cached}  ✅" if result_cached.cached else "  ❌ لم يُسترجع من الكاش")

# ─────────────────────────────────────────────────────────────────────────────
# 8. استعلام ثانٍ مختلف | Second different query
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("🤔 الاستعلام الثاني: تطبيقات الذكاء الاصطناعي")
print("="*60)

result2 = agent.query("ما هي أبرز تطبيقات الذكاء الاصطناعي في حياتنا اليومية؟")
print(f"\n✅ الإجابة:\n{result2.answer}")
print(f"\n📊 ثقة: {result2.confidence:.2%} | تكرارات: {result2.iterations}")

# ─────────────────────────────────────────────────────────────────────────────
# 9. مسح الكاش | Clear cache
# ─────────────────────────────────────────────────────────────────────────────
print("\n🗑️  مسح الكاش...")
agent.clear_cache()
print("  ✅ تم مسح الكاش")

# ─────────────────────────────────────────────────────────────────────────────
# 10. الاستخدام غير المتزامن | Async usage
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("🔁 الاستخدام غير المتزامن (Async)")
print("="*60)

import asyncio

async def async_example():
    # استعلام async واحد
    print("\n🤔 استعلام async: مستقبل الذكاء الاصطناعي")
    result = await agent.aquery("ما هو مستقبل الذكاء الاصطناعي؟")
    print(f"\n✅ الإجابة:\n{result.answer}")
    print(f"📊 ثقة: {result.confidence:.2%} | تكرارات: {result.iterations}")

    # استعلامات متوازية
    print("\n\n🚀 استعلامات متوازية (3 في وقت واحد)...")
    queries = [
        "ما هي نماذج اللغة الكبيرة؟",
        "من هو آلان تورينج؟",
        "ما الفرق بين التعلم العميق والذكاء الاصطناعي؟",
    ]
    results = await asyncio.gather(*[agent.aquery(q) for q in queries])
    for q, r in zip(queries, results):
        print(f"\n  ❓ {q}")
        print(f"  💬 {r.answer[:150]}{'...' if len(r.answer) > 150 else ''}")
        print(f"  📊 ثقة: {r.confidence:.2%}")


asyncio.run(async_example())

# ─────────────────────────────────────────────────────────────────────────────
# 11. عرض نتيجة كـ dict | Result as dict
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("📋 النتيجة كـ dictionary")
print("="*60)
import json
print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

print("\n✅ الإجابة:")
async for token in agent.astream_query("كيف تطور الذكاء الاصطناعي؟"):
    print(token, end="", flush=True)
print()  # سطر جديد في النهاية
# يمسح TTLCache و _result_cache معًا
```

