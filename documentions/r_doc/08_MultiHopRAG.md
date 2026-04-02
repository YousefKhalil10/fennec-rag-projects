# 🔗 MultiHopRAG — التوثيق الكامل

> نظام RAG متعدد القفزات للأسئلة المعقدة

---

## ١. نظرة عامة

`MultiHopRAG` مُصمَّم للأسئلة المعقدة التي تحتاج معلومات من مصادر متعددة ومترابطة. بدلاً من استرجاع واحد، يُنفّذ سلسلة قفزات (Hops) تُوجّه التفكير خطوة بخطوة، ويتوقف مبكراً إذا اكتملت الإجابة بثقة كافية.

| ⛓ قفزات موجّهة | 🛑 توقف مبكر ذكي | 🌐 عربي / إنجليزي | 🔒 إجابات من السياق فقط |
|:-:|:-:|:-:|:-:|

---

## ٢. التثبيت والاستيراد

> ⚠️ **تأكد من تثبيت stanza** إذا أردت استخراج الكيانات بدقة:
> ```bash
> pip install stanza && python -c "import stanza; stanza.download('ar')"
> ```

```python
# الاستيراد الصحيح — لاحظ: multi_hop (وليس multi_hub)
from rag.multi_hop import MultiHopRAG

# الوحدات المساعدة
from rag.multi_hop  import HopStrategy
from rag.multi_hop import HopResult, ReasoningState
from rag.multi_hop   import QueryDecomposer
```

---

## ٣. الكلاس الرئيسي — MultiHopRAG

### 3.1 `__init__`

```python
MultiHopRAG(
    rag_system,
    max_hops               = 3,
    min_score_threshold    = 0.3,
    enable_query_decomposition = True,
    use_stanza_ner         = True,
    language               = "ar",
    confidence_threshold   = 0.75
)
```

| المعامل | النوع | الافتراضي | الوصف |
|---------|-------|-----------|-------|
| `rag_system` | `Any` | — | نظام RAG الأساسي — إلزامي، يرفع `ValueError` إذا كان `None` |
| `max_hops` | `int` | `3` | أقصى عدد قفزات بحث قبل إرجاع الإجابة |
| `min_score_threshold` | `float` | `0.3` | الحد الأدنى لدرجة التشابه لقبول القطعة |
| `enable_query_decomposition` | `bool` | `True` | تفكيك السؤال المركب إلى استعلامات فرعية |
| `use_stanza_ner` | `bool` | `True` | استخدام Stanza NER لاستخراج الكيانات (يتراجع لـ Regex إن لم يتوفر) |
| `language` | `str` | `"ar"` | `"ar"` للعربية، `"en"` للإنجليزية — يُمرَّر لـ `QueryDecomposer` |
| `confidence_threshold` | `float` | `0.75` | نسبة الثقة (0–1) التي تُطلق التوقف المبكر وتوفير القفزات |

---

### 3.2 `query()`

```python
query(
    question:            str,
    hops:                Optional[int] = None,
    return_intermediate: bool          = False
) -> str | Dict
```

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `question` | `str` | السؤال المطلوب الإجابة عنه |
| `hops` | `int \| None` | تجاوز `max_hops` لهذا الاستعلام فقط؛ `None` يستخدم القيمة الافتراضية |
| `return_intermediate` | `bool` | `False` → يُرجع `str` (الإجابة فقط) — `True` → يُرجع `Dict` كامل |

#### Return `return_intermediate=True`

```python
{
    "answer":          str,            # الإجابة النهائية
    "reasoning_chain": List[str],      # خطوات التفكير المتراكمة
    "hops": [
        {
            "hop_number":    int,        # رقم القفزة (يبدأ من 1)
            "query":         str,        # الاستعلام المُستخدم في هذه القفزة
            "strategy":      str,        # استراتيجية القفزة (انظر §4)
            "reasoning_step":str,        # وصف ما اكتُشف في هذه الخطوة
            "gap_filled":    str | None, # الفجوة التي سدّتها (None إن لم تكن فجوة)
            "chunks_found":  int,        # عدد القطع المسترجعة
            "entities":      List[str],  # كيانات مُستخرجة من القطع
            "top_scores":    List[float] # درجات أعلى 3 قطع
        }
    ],
    "knowledge_state": {
        "known_facts":  List[str],     # الحقائق المكتشفة عبر جميع القفزات
        "missing_info": List[str],     # المعلومات الناقصة المتبقية
        "confidence":   float          # مستوى الثقة النهائي (0.0–1.0)
    },
    "total_chunks": int,               # إجمالي القطع المُجمَّعة
    "stats":        Dict               # إحصائيات الجلسة (انظر §3.4)
}
```

> ℹ️ **ملاحظة حول `gap_filled`:** تكون `None` في قفزات `entity_expansion` و`relation_bridging`. تحمل قيمة نصية فقط في قفزات `clarification` التي تسدّ فجوة معرفية محددة — مثل `"causal relationship"` أو `"specific date or time"`.

---

### 3.3 `aquery()` — الواجهة غير المتزامنة

```python
async aquery(
    question:            str,
    max_hops:            int  = None,
    return_intermediate: bool = False
) -> str | Dict
```

تُشغّل `query()` في thread pool منفصل (`asyncio.to_thread`) وتُرجع نفس النتيجة. المعاملات مطابقة لـ `query()` باستثناء أن المعامل الثاني هو `max_hops` وليس `hops`.

> ⚠️ **انتبه:** المعامل الثاني في `aquery` هو `max_hops` (وليس `hops` كما في `query`). تجنّب الخلط عند التمرير بالاسم.

```python
# استخدام بسيط
answer = await multi_hop.aquery("ما أهم إنجازات أينشتاين؟")

# مع معاملات
result = await multi_hop.aquery(
    "ما الفرق بين النسبية الخاصة والعامة؟",
    max_hops=4,
    return_intermediate=True
)

# Context Manager
async with MultiHopRAG(rag_system=base_rag) as mh:
    answer = await mh.aquery("سؤالك هنا")
```

---

### 3.4 `get_stats()`

```python
get_stats() -> Dict
```

```python
# مثال على القيمة المُرجَعة
{
    "total_queries":       int,   # إجمالي الاستعلامات منذ إنشاء الكائن
    "average_hops":        float, # متوسط عدد القفزات لكل استعلام
    "decomposed_queries":  int,   # الاستعلامات التي فُكِّكت لاستعلامات فرعية
    "entities_extracted":  int,   # إجمالي الكيانات المستخرجة
    "early_stops":         int,   # مرات التوقف المبكر (confidence >= threshold)
    "stanza_enabled":      bool,  # هل Stanza محمّل ونشط؟
    "max_hops":            int,   # القيمة المُعيَّنة عند الإنشاء
    "confidence_threshold":float, # القيمة المُعيَّنة عند الإنشاء
    "ner_method":          str,   # "Stanza" أو "Regex"
}
```

---

## ٤. HopStrategy — استراتيجيات القفزات

كل قفزة تعمل بإحدى الاستراتيجيات الأربع. القيمة تظهر في حقل `strategy` ضمن نتيجة `return_intermediate`.

| القيمة (`strategy`) | المعنى والمتى يُستخدم |
|---------------------|----------------------|
| `entity_expansion` | توسيع عبر كيانات مكتشفة — القفزة الافتراضية وفي الاستعلامات الفرعية المحددة مسبقاً |
| `relation_bridging` | ربط علاقات بين كيانين — يُستخدم في أسئلة المقارنة وقفزات الجسر |
| `clarification` | ملء فجوة معرفية محددة — يُطلق عند وجود `missing_info`؛ يعطى bonus وزن `+0.1` للقطع |
| `verification` | التحقق من معلومة — مُعرَّف في Enum ومتاح للتوسعة المستقبلية |

---

## ٥. الكشف التلقائي عن اللغة — `_detect_language()`

أُضيفت هذه الدالة في آخر تصحيح. **تعمل تلقائياً ولا تحتاج استدعاءً مباشراً.**

| الشرط | النتيجة |
|-------|---------|
| نسبة الحروف العربية > 20% | الـ prompt يكون عربياً — الرد بالعربية |
| نسبة الحروف العربية ≤ 20% | الـ prompt يكون إنجليزياً — الرد بالإنجليزية |

> 🔒 **Grounding صارم:** كلا الـ prompts يتضمنان قاعدة: *"أجب فقط من السياق المقدم. إذا لم تجد المعلومة، قل صراحةً إنها غير متوفرة."* — هذا يمنع الهلوسة واستحضار معلومات خارج قاعدة البيانات.

---

## ٦. مثال عملي كامل

```python
import asyncio
from rag.core                import RAGSystem
from rag.multi_hop           import MultiHopRAG       # ✓ multi_hop وليس multi_hub
from vector_database   import FAISSVectorDatabase
from embeddings import OpenAIEmbedder
from llm    import OpenAIInterface
from chunks    import TextSplitter
from context import ContextManager

# ── 1. إعداد النظام الأساسي ───────────────────────────────────────────────────
embedder  = OpenAIEmbedder(api_key="sk-...")
vector_db = FAISSVectorDatabase(embedder=embedder)
llm       = OpenAIInterface(api_key="sk-...")
base_rag  = RAGSystem(
    vector_db=vector_db, llm=llm,
    chunker=TextSplitter(chunk_size=400),
    context_manager=ContextManager(),
)


base_rag.add_documents({
    "einstein": """
        ألبرت أينشتاين فيزيائي ألماني ولد عام 1879.
        درس في جامعة زيوريخ وحصل على الدكتوراه عام 1905.
    """,
    "relativity": """
        نظرية النسبية الخاصة نشرها أينشتاين عام 1905.
        تقول إن سرعة الضوء ثابتة في جميع الإطارات المرجعية.
        معادلة E=mc² تصف تحول الكتلة لطاقة.
    """,
    "general_relativity": """
        النسبية العامة (1915) وصفت الجاذبية كانحناء في الزمكان.
        أثبتتها تجربة خسوف 1919 برصد انحراف الضوء قرب الشمس.
    """,
    "quantum": """
        ميكانيكا الكم وصفت السلوك الغريب للجسيمات دون الذرية.
        أسهم فيها بور وهايزنبرج وشرودنغر وأينشتاين أيضاً.
    """,
    "nobel": """
        حصل أينشتاين على جائزة نوبل عام 1921 ليس لنظرية النسبية
        بل لشرحه ظاهرة التأثير الكهروضوئي.
    """,
})
# ── 2. إنشاء MultiHopRAG ──────────────────────────────────────────────────────
multi_hop = MultiHopRAG(
    rag_system=base_rag,
    max_hops=3,
    confidence_threshold=0.75,
    language="ar",
)

# ── 3. سؤال بسيط (يُرجع str) ─────────────────────────────────────────────────
answer = multi_hop.query("متى وُلد أينشتاين؟")
print(answer)

# ── 4. سؤال معقد مع تفاصيل ───────────────────────────────────────────────────
result = multi_hop.query(
    "ما علاقة أينشتاين بميكانيكا الكم وعلى ماذا حصل جائزة نوبل؟",
    return_intermediate=True
)
print(result["answer"])
for step in result["reasoning_chain"]:
    print("•", step)

# ── 5. سؤال بالإنجليزية (يرد بالإنجليزية تلقائياً) ──────────────────────────
answer_en = multi_hop.query("What did Einstein win the Nobel Prize for?")

# ── 6. async ──────────────────────────────────────────────────────────────────
async def main():
    async with MultiHopRAG(rag_system=base_rag) as mh:
        answer = await mh.aquery(
            "ما أهم إنجازات أينشتاين؟",
            max_hops=4,
            return_intermediate=False
        )
        print(answer)

asyncio.run(main())

# ── 7. إحصائيات ───────────────────────────────────────────────────────────────
stats = multi_hop.get_stats()
print(f"متوسط القفزات:    {stats['average_hops']:.1f}")
print(f"التوقفات المبكرة: {stats['early_stops']}")
print(f"طريقة NER:        {stats['ner_method']}")
```

