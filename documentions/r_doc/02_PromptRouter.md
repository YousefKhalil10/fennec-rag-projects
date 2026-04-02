# 📘 PromptRouter — موجّه الـ Prompt

## نظرة عامة

`PromptRouter` هو المكوّن المسؤول عن بناء الـ prompt المناسب لكل استعلام تلقائياً. يكشف لغة السؤال (عربي/إنجليزي) ونوعه (تعريفي، تحليلي، مقارن…) ثم يختار القالب الأنسب مع أمثلة few-shot اختيارية.

---

## الاستيراد

```python
from rag.core.prompt_router import PromptRouter, QuestionType
```

---

## `QuestionType` — أنواع الأسئلة

| القيمة | الوصف |
|---|---|
| `FACTUAL` | سؤال عن حقيقة محددة (من؟ متى؟ أين؟) |
| `ANALYTICAL` | سؤال تحليلي (لماذا؟ اشرح؟ وضّح؟) |
| `COMPARATIVE` | سؤال مقارن (الفرق بين؟ أيهما أفضل؟) |
| `PROCEDURAL` | سؤال إجرائي (كيف؟ خطوات؟ طريقة؟) |
| `DEFINITIONAL` | سؤال تعريفي (ما معنى؟ عرّف؟) |
| `EVALUATIVE` | سؤال تقييمي (قيّم؟ ما أفضل؟) |
| `CAUSAL` | سؤال سببي (سبب؟ نتيجة؟ أدى إلى؟) |
| `GENERAL` | عام — الحالة الافتراضية عند عدم التطابق |

---

## `__init__`

```python
PromptRouter(include_few_shot: bool = True)
```

| المعامل | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `include_few_shot` | `bool` | `True` | تضمين مثال توضيحي داخل الـ prompt |

---

## الدوال الرئيسية

### `detect_language`

```python
detect_language(text: str) -> str  # 'ar' | 'en'
```

يكشف لغة النص بحساب نسبة الأحرف العربية. إذا تجاوزت 25% يُعيد `'ar'`، وإلا `'en'`.

```python
router = PromptRouter()
print(router.detect_language("ما هو الذكاء الاصطناعي؟"))  # 'ar'
print(router.detect_language("What is AI?"))              # 'en'
```

---

### `detect_question_type`

```python
detect_question_type(query: str, language: Optional[str] = None) -> QuestionType
```

يصنّف نوع السؤال بمطابقة الأنماط. يكشف اللغة تلقائياً إذا لم تُحدَّد.

```python
qt = router.detect_question_type("ما الفرق بين Python وJava؟")
# → QuestionType.COMPARATIVE

qt = router.detect_question_type("How do I install pip?")
# → QuestionType.PROCEDURAL
```

---

### `build`

```python
build(
    query: str,
    context: str,
    language: Optional[str] = None,
    question_type: Optional[QuestionType] = None,
) -> str
```

الدالة الرئيسية: تبني الـ prompt الجاهز للإرسال إلى LLM.

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | استعلام المستخدم |
| `context` | `str` | السياق المسترجع من قاعدة البيانات |
| `language` | `str \| None` | `'ar'` أو `'en'` — يُكشف تلقائياً إذا لم يُحدَّد |
| `question_type` | `QuestionType \| None` | تجاوز التصنيف التلقائي |

**يُرجع:** `str` — prompt جاهز

```python
prompt = router.build(
    query="ما هو تعلم الآلة؟",
    context="تعلم الآلة هو فرع من الذكاء الاصطناعي...",
)
print(prompt)
```

---

## التكامل مع `RAGConfig`

`PromptRouter` يُفعَّل من خلال الإعدادات:

```python
config = RAGConfig(
    enable_prompt_routing=True,   # تفعيل الراوتر
    include_few_shot=True,        # تضمين الأمثلة
    prompt_language="ar",         # None = كشف تلقائي
)
```

عند تفعيل `enable_prompt_routing=True` يُنشئ `RAGSystem` كائن `PromptRouter` داخلياً ويستخدمه في كل استدعاء لـ `generate()`.

---

## مثال مستقل

```python
from rag.core.prompt_router import PromptRouter, QuestionType

router = PromptRouter(include_few_shot=True)

# كشف اللغة
lang = router.detect_language("How does RAG work?")
print(lang)  # 'en'

# كشف نوع السؤال
q_type = router.detect_question_type("How does RAG work?", lang)
print(q_type)  # QuestionType.PROCEDURAL

# بناء الـ prompt يدوياً
prompt = router.build(
    query="How does RAG work?",
    context="RAG stands for Retrieval-Augmented Generation...",
    language="en",
    question_type=QuestionType.PROCEDURAL,
)
print(prompt)
```

---

## ملاحظات

- أنماط الكشف مبنية على Regex — فعّالة وسريعة بدون نموذج لغة.
- يمكن تمرير `question_type` يدوياً لتجاوز الكشف التلقائي.
- القوالب الداخلية (`_build_arabic` / `_build_english`) تحتوي على تعليمات مخصصة لكل نوع سؤال.
