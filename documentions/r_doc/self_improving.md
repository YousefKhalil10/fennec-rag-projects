# 📚 توثيق نظام RAG المتقدم — الدليل الشامل

> يغطي هذا التوثيق جميع الوحدات: `SelfRAG` · `HyDERAG` · `RecursiveRAG` · الاستثناءات · الـ Dataclasses · الدوال المساعدة · الإعدادات


---

## الاستثناءات

تعريفها في `self_improving_rag.py` — جميعها ترث من `RAGSystemError`.

### `RAGSystemError`
القاعدة لجميع استثناءات النظام. لا تُرمى مباشرة.

```python
except RAGSystemError as e:
    # يصطاد أي خطأ من النظام
```

### `LLMCallError`
تُرمى عندما تفشل **جميع** محاولات استدعاء نموذج اللغة (بعد `llm_retries` محاولات).

```python
try:
    answer = _call_llm(llm, prompt, retries=2)
except LLMCallError as e:
    print(f"فشل نموذج اللغة نهائياً: {e}")
```

### `RetrievalError`
تُرمى عندما تفشل عملية استرجاع المستندات من `rag_system.retrieve()`.

```python
try:
    docs = _retrieve_safe(rag_system, query)
except RetrievalError as e:
    print(f"فشل الاسترجاع: {e}")
```

---

## الإعدادات

### `SelfRAGConfig`

إعدادات نظام `SelfRAG` — تعريفها في `self_config.py`.

```python
from rag.self_improving_rag import SelfRAGConfig

config = SelfRAGConfig(
    max_refinement_iterations=3,
    confidence_threshold=0.80,
    enable_answer_refinement=True,
    enable_retrieval_refinement=True,
    llm_retries=2,
    fast_mode=True,
    skip_refinement_on_high_confidence=True,
)
```

| المعامل | النوع | الافتراضي | الوصف |
|---------|-------|-----------|-------|
| `max_refinement_iterations` | `int` | `3` | الحد الأقصى لعدد دورات التحسين |
| `confidence_threshold` | `float` | `0.80` | عتبة الثقة للتوقف المبكر (0.0–1.0) |
| `enable_answer_refinement` | `bool` | `True` | تفعيل إعادة كتابة الإجابة في كل دورة |
| `enable_retrieval_refinement` | `bool` | `True` | تفعيل تعديل استعلام الاسترجاع بناءً على الاقتراحات |
| `llm_retries` | `int` | `2` | عدد إعادات المحاولة عند فشل نموذج اللغة |
| `fast_mode` | `bool` | `True` | دمج التوليد والتقييم في استدعاء LLM واحد (يوفر ~50% من الاستدعاءات) |
| `skip_refinement_on_high_confidence` | `bool` | `True` | التوقف فوراً إذا تجاوزت الإجابة الأولى العتبة |

---

### `RecursiveRAGConfig`

إعدادات نظام `RecursiveRAG` — تعريفها في `self_config.py`.

```python
from rag.self_improving_rag import RecursiveRAGConfig

config = RecursiveRAGConfig(
    max_depth=3,
    max_sub_questions=4,
    min_query_length=40,
    complexity_keywords=["أسباب", "نتائج", "مقارنة", "why", "how"],
    llm_retries=2,
)
```

| المعامل | النوع | الافتراضي | الوصف |
|---------|-------|-----------|-------|
| `max_depth` | `int` | `3` | الحد الأقصى لعمق التفكيك العودي |
| `max_sub_questions` | `int` | `4` | أقصى عدد أسئلة فرعية في كل تفكيك |
| `min_query_length` | `int` | `40` | الحد الأدنى لطول السؤال كي يُعتبر معقداً (بالأحرف) |
| `complexity_keywords` | `List[str]` | قائمة عربية/إنجليزية | الكلمات المفتاحية الدالة على التعقيد |
| `llm_retries` | `int` | `2` | عدد إعادات المحاولة عند فشل نموذج اللغة |

---

## Dataclasses

### `EvaluationResult`

نتيجة دورة تقييم ذاتي واحدة. تعريفها في `self_rag_dataclass.py`.

```python
@dataclass
class EvaluationResult:
    relevance: float     # صلة الإجابة بالسؤال (0.0–1.0)
    accuracy: float      # دقة المعلومات (0.0–1.0)
    completeness: float  # اكتمال الإجابة (0.0–1.0)
    clarity: float       # وضوح الصياغة (0.0–1.0)
    issues: List[str]    # قائمة المشاكل المكتشفة
    suggestions: List[str] # اقتراحات للتحسين
```

**الخاصية المحسوبة `confidence`:**
```python
# المتوسط الهندسي للأبعاد الأربعة (أكثر صرامة من المتوسط الحسابي)
confidence = (relevance * accuracy * completeness * clarity) ** 0.25
```

> ملاحظة: إذا كان أحد الأبعاد قريباً من الصفر فإن `confidence` تنخفض بشكل ملحوظ — وهذا مقصود.

**الدوال:**
```python
result.to_dict()  # تحويل لقاموس مع تقريب الأرقام لـ 4 منازل عشرية
```

---

### `RefinementStep`

سجل تكرار واحد في دورة `SelfRAG`. تعريفها في `self_rag_dataclass.py`.

```python
@dataclass
class RefinementStep:
    iteration: int             # رقم التكرار (يبدأ من 1)
    answer: str                # الإجابة في هذا التكرار
    evaluation: EvaluationResult

    # خاصية محسوبة
    confidence: float          # = evaluation.confidence
```

---

### `SelfRAGResult`

النتيجة النهائية لنظام `SelfRAG`. تعريفها في `self_rag_dataclass.py`.

```python
result = self_rag.query("سؤال؟")

result.answer          # أفضل إجابة عبر جميع التكرارات
result.confidence      # درجة الثقة في أفضل إجابة
result.iterations      # عدد التكرارات الفعلية
result.history         # List[RefinementStep]

# خصائص إضافية
result.final_answer    # alias لـ answer
result.refinement_steps  # alias لـ iterations
result.initial_quality   # ثقة التكرار الأول
result.final_quality     # ثقة التكرار الأخير
result.steps           # قائمة مُحسَّنة مع .step, .action, .reason

result.to_dict()       # تحويل لقاموس كامل
```

---

### `HyDEResult`

نتيجة نظام `HyDERAG`. تعريفها في `self_rag_dataclass.py`.

```python
@dataclass
class HyDEResult:
    answer: str                    # الإجابة النهائية
    hypothetical_docs: List[str]   # المستندات الاصطناعية المُولَّدة
    num_retrieved: int             # عدد المستندات الفريدة المسترجعة
    num_ranked: int                # عدد المستندات بعد الترتيب النهائي

    to_dict() -> Dict              # تحويل لقاموس
```

---

### `RecursiveRAGResult`


```python
@dataclass
class RecursiveRAGResult:
    answer: str                   # الإجابة النهائية (مدمجة أو مباشرة)
    depth: int                    # عمق التفكيك الفعلي
    decomposed: bool              # هل جرى تفكيك السؤال؟
    sub_questions: List[str]      # الأسئلة الفرعية المُولَّدة
    sub_answers: List[SubAnswer]  # إجابات كل سؤال فرعي

    to_dict() -> Dict
```

---

### `SubAnswer`

إجابة سؤال فرعي واحد في `RecursiveRAG`. تعريفها في `self_rag_dataclass.py`.

```python
@dataclass
class SubAnswer:
    question: str   # نص السؤال الفرعي
    answer: str     # الإجابة عليه
    depth: int      # عمق العودية الذي أُجيب فيه
```

---

## SelfRAG


نظام RAG يحسّن إجاباته عبر حلقة: استرجاع → توليد → تقييم → تحسين.

### الإنشاء

```python
from rag.self_improving_rag import SelfRAG
from rag.self_improving_rag import SelfRAGConfig

self_rag = SelfRAG(
    rag_system=base_rag,   # Any — يجب أن يدعم .retrieve() و .add_document()
    llm=llm,               # Any — يجب أن يدعم .generate(prompt) -> str
    config=SelfRAGConfig(), # اختياري، يُستخدم الافتراضي إذا لم يُعطَ
)
```

**Return:** `ValueError` إذا كان `llm` فارغاً.

---

### `query`

```python
def query(
    query: str,
    context: Optional[Dict[str, Any]] = None,
) -> SelfRAGResult
```

تنفيذ حلقة التحسين الذاتي وإعادة أفضل إجابة.

**المعاملات:**
- `query` — السؤال بالنص الطبيعي
- `context` — سياق إضافي اختياري (محجوز للاستخدام المستقبلي)

**Return:** `SelfRAGResult` يحتوي على الإجابة وتاريخ كامل للتكرارات.

**منطق التوقف:** يتوقف مبكراً إذا تجاوزت `confidence >= confidence_threshold`، وإلا يكمل حتى `max_refinement_iterations`.

---

### `add_document`

```python
def add_document(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Any
```

يُمرِّر المستند مباشرة لـ `rag_system.add_document()`.

---

### `get_stats`

```python
def get_stats() -> Dict
```

يُعيد إعدادات النظام الحالية كقاموس:

```python
{
    "max_refinement_iterations": 3,
    "confidence_threshold": 0.80,
    "enable_answer_refinement": True,
    "enable_retrieval_refinement": True,
    "llm_retries": 2,
    "fast_mode": True,
}
```

---

### `aquery` (غير متزامن)

```python
async def aquery(
    query: str,
    context: Optional[Dict[str, Any]] = None,
) -> SelfRAGResult
```

غلاف غير متزامن حول `query()` باستخدام `asyncio.to_thread`.

```python
result = await self_rag.aquery("سؤال؟")

# أو كـ context manager
async with SelfRAG(rag, llm) as sr:
    result = await sr.aquery("سؤال؟")
```

---

## HyDERAG


نظام RAG يُولّد مستندات اصطناعية افتراضية لتوسيع الاسترجاع.

**الفكرة:** بدلاً من البحث بالسؤال مباشرة، يُولّد النظام عدة "إجابات افتراضية" ويبحث بكلٍّ منها — مما يُحسّن تغطية الاسترجاع الدلالي.

### الإنشاء

```python
from rag.self_improving_rag import HyDERAG

hyde = HyDERAG(
    rag_system=base_rag,
    llm=llm,
    num_hypothetical_docs=3,    # عدد المستندات الاصطناعية
    use_original_query=True,    # إضافة الاستعلام الأصلي للبحث أيضاً
    top_k=5,                    # نتائج لكل استعلام بحث
    max_final_docs=10,          # حد المستندات بعد التجميع والترتيب
    llm_retries=2,
    max_workers=4,              # خيوط التنفيذ المتوازي
)
```

**Return:** `ValueError` إذا كان `llm` فارغاً.

---

### `query`

```python
def query(
    query: str,
    context: Optional[Dict[str, Any]] = None,
) -> HyDEResult
```

تنفيذ خط أنابيب HyDE كاملاً:
1. توليد `num_hypothetical_docs` مستندات اصطناعية بالتوازي
2. البحث بكل مستند + الاستعلام الأصلي (إذا `use_original_query=True`)
3. إزالة التكرارات وإعادة الترتيب حسب الدرجة
4. توليد الإجابة النهائية من أفضل `max_final_docs` مستنداً

---

### `add_document`

```python
def add_document(text: str, metadata: Optional[Dict] = None) -> Any
```

---

## RecursiveRAG


نظام RAG يُفكك الأسئلة المعقدة إلى أسئلة فرعية أبسط ثم يدمج إجاباتها.

**الفكرة:** الأسئلة ذات الشقين ("ما أسباب X وكيف يمكن مواجهته؟") تُجاب بشكل أفضل عبر التفكيك بدلاً من الإجابة المباشرة.

### الإنشاء

```python
from rag.self_improving_rag import RecursiveRAG
from rag.self_improving_rag import RecursiveRAGConfig

recursive_rag = RecursiveRAG(
    rag_system=base_rag,
    llm=llm,
    config=RecursiveRAGConfig(max_depth=3),
)
```

**Return:** `ValueError` إذا كان `llm` فارغاً.

---

### `query`

```python
def query(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    _depth: int = 0,            # داخلي — لا تضبطه يدوياً
) -> RecursiveRAGResult
```

**منطق التنفيذ:**

```
هل السؤال بسيط أو وصلنا max_depth؟
    نعم → أجب مباشرة (_answer_directly)
    لا  → فكّك إلى أسئلة فرعية
           ↓
        هل التفكيك أنتج ≤ سؤالاً؟
            نعم → أجب مباشرة
            لا  → اعمل query() عودي لكل سؤال فرعي
                    ↓
                 ادمج الإجابات (_merge)
```

**تحديد التعقيد:** سؤال يُعتبر معقداً إذا:
- طوله ≥ `min_query_length` أحرف، و
- يحتوي على ≥ كلمتين من `complexity_keywords`

---

### `add_document`

```python
def add_document(text: str, metadata: Optional[Dict] = None) -> Any
```

---

## الدوال المساعدة

تعريفها في `self_improving_rag.py` — مفيدة عند توسيع النظام أو كتابة أنظمة مخصصة.

### `_call_llm`

```python
def _call_llm(
    llm: Any,
    prompt: str,
    retries: int = 2,
    backoff: float = 0.5,
) -> str
```

يستدعي `llm.generate(prompt)` مع إعادة محاولة تلقائية بتأخير أسّي.

- التأخير بين المحاولات: `backoff * (2 ** attempt)` ثانية
- **Return:** `LLMCallError` إذا فشلت جميع المحاولات

```python
try:
    text = _call_llm(llm, "أجب على: ...", retries=3)
except LLMCallError:
    text = "fallback"
```

---

### `_retrieve_safe`

```python
def _retrieve_safe(
    rag_system: Any,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]
```

يسترجع المستندات ويُوحِّد أي تنسيق ناتج إلى `List[Dict]`.

يتعامل مع:
- `List[Tuple[DocumentChunk, float]]` ← FAISS
- `List[Dict]` ← مُوحَّد مسبقاً
- `{"results": [...]}` ← قاموس مُغلَّف

**كل مستند مُوحَّد يحتوي على:**
```python
{
    "text": str,
    "score": float,
    "source": str,
    "metadata": dict,
}
```

**Return:** `RetrievalError` عند فشل `rag_system.retrieve()`.

---

### `_deduplicate`

```python
def _deduplicate(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

يُزيل المستندات المكررة محتفظاً بأعلى درجة لكل مستند فريد.

يُحسب مفتاح كل مستند من أول 120 حرفاً من نصه عبر MD5.

```python
unique_docs = _deduplicate(all_retrieved_docs)
```

---

## مقارنة الأنظمة

| الميزة | SelfRAG | HyDERAG | RecursiveRAG |
|--------|---------|---------|--------------|
| **مناسب لـ** | أسئلة تحتاج دقة عالية | أسئلة تحتاج تغطية واسعة | أسئلة مركبة متعددة الأجزاء |
| **آلية التحسين** | تقييم ذاتي + إعادة كتابة | مستندات اصطناعية + استرجاع موسّع | تفكيك + دمج |
| **استدعاءات LLM** | 2–6 لكل سؤال (حسب التكرارات) | 3–5 لكل سؤال | تتزايد مع التعقيد |
| **استدعاءات Retrieval** | 1–3 | N+1 (N = عدد المستندات الاصطناعية) | بعدد الأسئلة الفرعية |
| **fast_mode** | ✅ متاح | ✖ غير متاح | ✖ غير متاح |
| **غير متزامن** | ✅ `aquery()` | ✖ | ✖ |
| **مثالي عند** | إجابات طبية/قانونية/دقيقة | استعلامات بحثية عامة | "ما أسباب X ونتائجه؟" |

---

## أمثلة متكاملة

### SelfRAG — الاستخدام الكامل

```python
from rag.core import RAGSystem
from rag.self_improving_rag import SelfRAG, LLMCallError, RetrievalError
from rag.self_improving_rag import SelfRAGConfig

config = SelfRAGConfig(
    max_refinement_iterations=3,
    confidence_threshold=0.85,
    fast_mode=True,
)
self_rag = SelfRAG(rag_system=base_rag, llm=llm, config=config)

# الاستعلام
result = self_rag.query("ما أسباب التغير المناخي؟")

print(f"الإجابة: {result.answer}")
print(f"الثقة: {result.confidence:.2%}")
print(f"التكرارات: {result.iterations}")
print(f"الجودة الأولى: {result.initial_quality:.2%}")
print(f"الجودة الأخيرة: {result.final_quality:.2%}")

for step in result.history:
    eval_ = step.evaluation
    print(
        f"  تكرار {step.iteration}: "
        f"ثقة={step.confidence:.2%} | "
        f"مشاكل: {'; '.join(eval_.issues) or 'لا يوجد'}"
    )

# الإحصائيات
print(self_rag.get_stats())
```

---

### HyDERAG — الاستخدام الكامل

```python
from rag.hyde import HyDERAG

hyde = HyDERAG(
    rag_system=base_rag,
    llm=llm,
    num_hypothetical_docs=4,
    use_original_query=True,
    top_k=5,
    max_final_docs=12,
)

result = hyde.query("ما فوائد الطاقة الشمسية؟")

print(f"الإجابة: {result.answer}")
print(f"مستندات اصطناعية مُولَّدة: {len(result.hypothetical_docs)}")
print(f"مستندات مسترجعة فريدة: {result.num_retrieved}")
print(f"مستندات استُخدمت نهائياً: {result.num_ranked}")

# عرض المستندات الاصطناعية
for i, doc in enumerate(result.hypothetical_docs, 1):
    print(f"\n[مستند اصطناعي {i}]\n{doc[:200]}...")
```

---

### RecursiveRAG — الاستخدام الكامل

```python
from rag.recursive import RecursiveRAG
from rag.self_config import RecursiveRAGConfig

config = RecursiveRAGConfig(
    max_depth=3,
    max_sub_questions=4,
    min_query_length=40,
)
recursive_rag = RecursiveRAG(rag_system=base_rag, llm=llm, config=config)

result = recursive_rag.query(
    "ما هي أسباب الثورة الصناعية ونتائجها على المجتمع والاقتصاد؟"
)

print(f"الإجابة النهائية:\n{result.answer}")
print(f"\nجرى التفكيك: {'نعم' if result.decomposed else 'لا'}")
print(f"العمق الفعلي: {result.depth}")

if result.decomposed:
    print("\nالأسئلة الفرعية:")
    for i, sq in enumerate(result.sub_questions, 1):
        print(f"  {i}. {sq}")

    print("\nإجابات الأسئلة الفرعية:")
    for sa in result.sub_answers:
        print(f"\n  [سؤال] {sa.question}")
        print(f"  [إجابة] {sa.answer[:150]}...")
```

---

### معالجة الاستثناءات

```python
from rag.self_improving_rag import SelfRAG, LLMCallError, RetrievalError, RAGSystemError

try:
    result = self_rag.query("سؤال؟")
except LLMCallError as e:
    # نموذج اللغة فشل بعد جميع المحاولات
    print(f"فشل LLM: {e}")
except RetrievalError as e:
    # فشل استرجاع المستندات
    print(f"فشل الاسترجاع: {e}")
except RAGSystemError as e:
    # أي خطأ آخر في النظام
    print(f"خطأ عام في RAG: {e}")
```

---

### الاستخدام غير المتزامن مع SelfRAG

```python
import asyncio
from rag.self_improving_rag import SelfRAG

async def main():
    async with SelfRAG(base_rag, llm) as sr:
        # استعلام واحد
        result = await sr.aquery("ما هو الذكاء الاصطناعي؟")
        print(result.answer)

        # استعلامات متعددة بالتوازي
        questions = [
            "ما هو التعلم الآلي؟",
            "ما هو التعلم العميق؟",
            "ما الفرق بين AI و ML؟",
        ]
        results = await asyncio.gather(*[sr.aquery(q) for q in questions])
        for q, r in zip(questions, results):
            print(f"\nسؤال: {q}")
            print(f"إجابة: {r.answer[:100]}...")

asyncio.run(main())
```

---

