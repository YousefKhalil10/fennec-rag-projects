# 🎯 DomainSpecificRAG — نظام RAG المتخصص بالمجال

## نظرة عامة

`DomainSpecificRAG` يُخصّص نظام RAG لمجال معين (طب، قانون، تقنية، طبخ...). يقيس **صلة السؤال بالمجال** ويرفض الأسئلة خارج نطاقه (في الوضع الصارم)، ويُعزّز استرجاع المستندات ذات الصلة بالمجال.

---

## هيكل المكونات



---

## التثبيت والاستيراد

```python
from rag.domain_rag import DomainSpecificRAG
from rag.domain_rag import DomainDefinition, PRESET_DOMAINS
```

---

## المجالات الجاهزة (Presets)

```python
print(list(PRESET_DOMAINS.keys()))
# ['medical', 'legal', 'technical', 'financial', 'academic']
```

| المجال | `display_name` | مثال على المصطلحات |
|---|---|---|
| `medical` | الطب والصحة | دواء، علاج، مرض، أعراض، تشخيص |
| `legal` | القانون والتشريع | قانون، حكم، محكمة، عقد، دعوى |
| `technical` | التقنية والبرمجة | كود، API، خوارزمية، قاعدة بيانات |
| `financial` | المال والاستثمار | سهم، بورصة، تداول، ربح، أصول |
| `academic` | الأبحاث والأكاديميا | بحث، نظرية، منهجية، فرضية، إحصاء |

> كل مجال جاهز يُنسَخ عند الاستخدام — التعديل عليه لا يؤثر على الـ preset الأصلي.

---

## `DomainDefinition` — تعريف مجال مخصص

### الحقول

| الحقل | النوع | الإلزامية | الوصف |
|---|---|---|---|
| `name` | `str` | ✅ | معرّف المجال e.g. `"nutrition"` |
| `terms` | `List[str]` | ✅ | المصطلحات الأساسية للمجال |
| `display_name` | `str` | ❌ | اسم عرض جميل — يُساوي `name` إن لم يُحدَّد |
| `language` | `str` | ❌ | لغة المصطلحات (افتراضي: `"ar"`) |
| `synonyms` | `Dict[str, List[str]]` | ❌ | مرادفات: `{"سعرات": ["كالوري", "طاقة"]}` |
| `system_prompt` | `str` | ❌ | تعليمات خاصة للنموذج عند الإجابة |
| `rejection_message` | `str` | ❌ | رسالة الرفض — تُولَّد تلقائياً إن لم تُحدَّد |
| `min_relevance` | `float` | ❌ | الحد الأدنى للصلة `0.0 → 1.0` (افتراضي: `0.10`) |
| `boost_weight` | `float` | ❌ | مضاعف تعزيز مصطلحات المجال (افتراضي: `1.5`) |
| `metadata` | `Dict[str, Any]` | ❌ | بيانات إضافية حرة يضيفها المستخدم |

### الخاصية `all_terms`

```python
domain.all_terms  # Set[str] — كل المصطلحات + المرادفات مُدمَجة
```

مُخزَّنة في cache تُعاد بناؤها تلقائياً عند إضافة مصطلحات أو مرادفات جديدة.

### دوال `DomainDefinition`

| الدالة | الوصف |
|---|---|
| `add_terms(*terms)` | إضافة مصطلحات جديدة في وقت التشغيل، تُعيد بناء الـ cache |
| `add_synonym(term, *synonyms)` | إضافة مرادفات لمصطلح، تُعيد بناء الـ cache |
| `to_dict()` | تسلسل إلى `dict` للحفظ في JSON |
| `from_dict(data)` | إنشاء كائن من `dict` (class method) |
| `save(path)` | حفظ المجال في ملف JSON |
| `load(path)` | تحميل المجال من ملف JSON (class method) |

### مثال

```python
domain = DomainDefinition(
    name="cooking",
    display_name="الطبخ والمطبخ",
    language="ar",
    terms=["وصفة", "مكونات", "طبخ", "شوي", "قلي", "خبز"],
    synonyms={
        "وصفة": ["طريقة طبخ", "كيفية تحضير"],
        "مكونات": ["حاجات", "مقادير"],
    },
    system_prompt="أنت طاهٍ محترف تُجيب عن أسئلة الطبخ فقط.",
    min_relevance=0.2,
    boost_weight=1.5,
    rejection_message="عذرًا، أنا متخصص في الطبخ فقط.",
    metadata={"version": "1.0", "author": "team-a"},
)

# إضافة في وقت التشغيل
domain.add_terms("تتبيلة", "توابل")
domain.add_synonym("طبخ", "تحضير", "إعداد")

# عرض كل المصطلحات
print(domain.all_terms)

# حفظ وتحميل
domain.save("cooking_domain.json")
domain_loaded = DomainDefinition.load("cooking_domain.json")
```

---

## `DomainSpecificRAG`

### `__init__`

```python
DomainSpecificRAG(
    rag_system,
    domain: str | DomainDefinition,
    domain_terms: Optional[List[str]] = None,
    llm=None,
    strict_mode: bool = False,
    auto_expand_terms: bool = False,
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `rag_system` | Any | نظام RAG الأساسي **(مطلوب)** |
| `domain` | `str` أو `DomainDefinition` | اسم مجال جاهز أو كائن مجال مخصص |
| `domain_terms` | `List[str]` | مصطلحات إضافية تُضاف فوق المجال المحدد |
| `llm` | Any | نموذج لغة — يأخذ `rag_system.llm` تلقائياً إن وُجد، يُستخدم في `auto_expand_terms` |
| `strict_mode` | `bool` | رفض الأسئلة ذات صلة أقل من `min_relevance` (افتراضي: `False`) |
| `auto_expand_terms` | `bool` | توسيع المصطلحات تلقائياً عبر LLM عند الإنشاء — **يتطلب `llm` متاحاً** (افتراضي: `False`) |

> `auto_expand_terms=True` بدون `llm` لا يُسبّب خطأ — يُسجَّل تحذير ويُتجاهَل.

---

### `query`

```python
query(query: str, context: Optional[Dict] = None) -> Dict[str, Any]
```

استعلام متزامن متخصص بالمجال.

**Return:**
```python
{
    "answer": "الإجابة النصية",
    "domain": "medical",
    "domain_display": "الطب والصحة",
    "domain_relevance": 0.85,       # صلة السؤال بالمجال (0-1)
    "matched_terms": ["قلب", "ضغط"],
    "enhanced_query": "الاستعلام المُحسَّن بعد إضافة المرادفات",
    "docs_count": 5,
    "latency_ms": 230.5,
    "sources": [...],               # أول 5 مستندات مع النص والنقاط
    # يظهر فقط عند الرفض:
    "rejected": True,
}
```

> **الـ Schema موحّد** — سواء قُبل السؤال أو رُفض، الحقول نفسها دائماً موجودة. عند الرفض: `docs_count=0`, `matched_terms=[]`, `enhanced_query=""`, `latency_ms=0.0`.

---

### `aquery` (غير متزامن)

```python
await domain_rag.aquery(query: str, context: Optional[Dict] = None) -> Dict[str, Any]
```

نفس سلوك `query()` ونفس الـ return schema، لكن غير متزامن.

---

### `agenerate`

```python
await domain_rag.agenerate(query: str, **kwargs) -> str
```

يُشغّل `aquery()` ويُرجع حقل `"answer"` مباشرةً كـ `str` — مفيد عندما تحتاج النص فقط بدون باقي البيانات.

---

### `aretrieve`

```python
await domain_rag.aretrieve(query: str, **kwargs) -> List[Dict]
```

يُشغّل الاسترجاع فقط بدون توليد، ويُرجع قائمة المستندات الموحّدة الشكل:
```python
[
    {
        "text": "...",
        "score": 0.87,
        "metadata": {...},
        "domain_hits": 3,
        "domain_bonus": 0.12,
        "combined_score": 0.99,
    },
    ...
]
```

---

### `add_document`

```python
add_document(text: str, metadata: Optional[Dict] = None) -> Any
```

إضافة مستند مع وسم تلقائي بالمجال في الـ metadata:
```python
# يُضيف تلقائياً: {"domain": "medical", ...metadata الأصلي}
domain_rag.add_document("نص المستند", metadata={"source": "كتاب طبي"})
```

---

### `add_terms`

```python
add_terms(*terms: str) -> None
```

إضافة مصطلحات جديدة للمجال في وقت التشغيل.

```python
domain_rag.add_terms("ارتفاع ضغط الدم", "السكتة الدماغية", "قصور القلب")
```

---

### `add_synonym`

```python
add_synonym(term: str, *synonyms: str) -> None
```

إضافة مرادفات لمصطلح معين.

```python
domain_rag.add_synonym("علاج", "معالجة", "مداواة")
```

---

### `get_metrics`

```python
get_metrics() -> Dict[str, Any]
```

**Return:**
```python
{
    "domain": "medical",
    "total_queries": 50,
    "rejected": 3,
    "acceptance_rate": "94.0%",     # نسبة الأسئلة المقبولة
    "avg_relevance": 0.78,
    "avg_docs_per_query": 4.5,      # متوسط المستندات لكل استعلام
    "errors": 0,                    # عدد أخطاء الاسترجاع أو التوليد
    "total_terms": 120,             # إجمالي المصطلحات + المرادفات
}
```

---

### `save_domain`

```python
save_domain(path: str) -> None
```

حفظ تعريف المجال الحالي (بما يشمل المصطلحات المُضافة في وقت التشغيل) في ملف JSON.

---

### `__repr__`

```python
repr(domain_rag)
# DomainSpecificRAG(domain='medical', terms=18, strict=True, queries=5)
```

---

## الواجهة غير المتزامنة — ملخص

```python
# استعلام كامل مع جميع البيانات
result = await domain_rag.aquery("سؤالك هنا")

# النص فقط
answer = await domain_rag.agenerate("سؤالك هنا")

# الاسترجاع فقط (بدون توليد)
docs = await domain_rag.aretrieve("سؤالك هنا")

# Context Manager
async with DomainSpecificRAG(base_rag, domain="medical") as rag:
    result = await rag.aquery("سؤال طبي")
```

---

## آلية قياس الصلة

النظام يقيس الصلة بطبقتين:

**طبقة 1 — تطابق مباشر** (وزن 1.0): كلمات السؤال موجودة حرفياً في مصطلحات المجال.

**طبقة 2 — تطابق جزئي** (وزن 0.5): مصطلح المجال موجود كجزء من كلمة في السؤال أو العكس.

```
score = (direct_matches × 1.0 + partial_matches × 0.5) / len(query_words)
score = min(score × boost_weight, 1.0)
```

---

## مثال عملي كامل

```python
from rag.core import RAGSystem
from rag.domain_rag import DomainSpecificRAG
from rag.domain_rag import DomainDefinition
import asyncio

# --- 1. إعداد النظام الأساسي ---
base_rag = RAGSystem(
    vector_db=vector_db, llm=llm,
    chunker=chunker, context_manager=ctx_manager,
)
base_rag.add_documents({
    "heart": """
        القلب هو العضو المركزي في الجهاز الدوري. يضخ الدم عبر الشرايين والأوردة.
        أمراض القلب تشمل: ارتفاع الضغط، الذبحة الصدرية، قصور القلب الاحتقاني.
    """,
    "diabetes": """
        السكري مرض مزمن يؤثر على كيفية معالجة الجسم للسكر.
        النوع الأول يعتمد على الأنسولين، والنوع الثاني يرتبط بمقاومة الأنسولين.
    """,
})

# --- 2. طريقة 1: مجال جاهز ---
medical_rag = DomainSpecificRAG(
    rag_system=base_rag,
    domain="medical",
    strict_mode=True,
)

# --- 3. طريقة 2: مجال مخصص كامل ---
medical_domain = DomainDefinition(
    name="medical",
    display_name="الطب والصحة",
    terms=["قلب", "ضغط", "سكري", "جراحة", "أنسولين", "شرايين",
           "أوردة", "دم", "علاج", "دواء", "مستشفى", "طبيب"],
    system_prompt="أنت طبيب متخصص تُجيب بدقة علمية عالية.",
    min_relevance=0.15,
    boost_weight=1.5,
    rejection_message="عذرًا، تخصصي في الطب فقط.",
    synonyms={
        "قلب": ["فؤاد", "عضلة القلب"],
        "ضغط": ["ضغط الدم", "hypertension"],
    },
    metadata={"version": "2.0", "reviewed_by": "dr-ahmed"},
)

custom_rag = DomainSpecificRAG(
    rag_system=base_rag,
    domain=medical_domain,
    strict_mode=True,
)

custom_rag.add_terms("نبضات القلب", "الأوعية الدموية")
custom_rag.add_synonym("علاج", "معالجة", "مداواة")

# --- 4. الاستعلام المتزامن ---
q1 = "ما هو علاج ارتفاع ضغط الدم؟"
result1 = custom_rag.query(q1)
print(f"❓ {q1}")
print(f"🎯 الصلة: {result1['domain_relevance']:.2%}")
print(f"🔍 المصطلحات: {result1['matched_terms']}")
print(f"📝 الإجابة: {result1['answer'][:200]}")

# سؤال خارج المجال — سيُرفض في strict_mode
q2 = "ما أفضل برنامج لتعلم البرمجة؟"
result2 = custom_rag.query(q2)
print(f"\n❓ {q2}")
print(f"❌ مرفوض: {result2.get('rejected', False)}")
print(f"💬 {result2['answer']}")

# --- 5. الإحصائيات ---
metrics = custom_rag.get_metrics()
print("\n📊 إحصائيات المجال:")
for k, v in metrics.items():
    print(f"  {k}: {v}")

# --- 6. حفظ المجال وتحميله ---
custom_rag.save_domain("medical_domain.json")
domain_from_file = DomainDefinition.load("medical_domain.json")
rag_from_file = DomainSpecificRAG(rag_system=base_rag, domain=domain_from_file)

# --- 7. الاستخدام غير المتزامن ---
async def async_examples():
    # استعلام كامل
    result = await custom_rag.aquery("ما أسباب السكري؟")
    print(f"\n[aquery] {result['answer'][:100]}")

    # النص فقط
    answer = await custom_rag.agenerate("ما أعراض ارتفاع الضغط؟")
    print(f"[agenerate] {answer[:100]}")

    # الاسترجاع فقط
    docs = await custom_rag.aretrieve("علاج السكري")
    print(f"[aretrieve] {len(docs)} مستند")

    # Context Manager
    async with DomainSpecificRAG(base_rag, domain="medical") as rag:
        result = await rag.aquery("ما هو القلب؟")
        print(f"[context manager] {result['answer'][:100]}")

asyncio.run(async_examples())

# --- 8. repr ---
print(repr(custom_rag))
# DomainSpecificRAG(domain='medical', terms=20, strict=True, queries=2)
```

### 'astream'  token by token

```python
print(f"\n⚡ astream (بث فوري):")
print("🤖 ", end="", flush=True)
async for token in custom_rag.astream("ماهو القلب"):
    print(token, end="", flush=True)
print()
```

---

## ملاحظات مهمة

| الموضوع | التفصيل |
|---|---|
| **الـ Schema موحّد** | `query()` و `aquery()` يُرجعان نفس الحقول دائماً — سواء قُبل السؤال أو رُفض |
| **auto_expand_terms** | يتطلب `llm` متاحاً — بدونه يُسجَّل تحذير ويُتجاهَل بدون خطأ |
| **strict_mode والترتيب** | في `strict_mode`: المستندات التي `domain_hits=0` تُحذف حتى لو كانت `rag_score` عالية |
| **نسخ الـ Presets** | المجالات الجاهزة تُنسَخ عند الاستخدام — التعديل لا يغيّر `PRESET_DOMAINS` |
| **cache الـ all_terms** | يُعاد بناؤه تلقائياً عند `add_terms()` أو `add_synonym()` — لا تدخّل يدوي |
| **`agenerate` مقابل `aquery`** | `agenerate` يُرجع `str` فقط — استخدم `aquery` إن احتجت الصلة والمصادر والإحصائيات |