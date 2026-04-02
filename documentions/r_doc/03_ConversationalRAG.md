# 💬 ConversationalRAG — نظام RAG مع تاريخ المحادثة

## نظرة عامة

`ConversationalRAG` يُضيف **ذاكرة المحادثة** لنظام RAG. يتذكر الأسئلة والأجوبة السابقة ويستخدمها لفهم الأسئلة اللاحقة المرتبطة بالسياق، مثل: "ما رأيك في **هذا**؟" أو "وضّح **ذلك** أكثر".

كما يدعم الحفظ التلقائي في ملف JSON وتصدير تاريخ المحادثة.


---

## التثبيت والاستيراد

```python
from rag.conversational_rag import ConversationalRAG
```

---

## `RAGConfigConverstion`

الإعدادات الافتراضية للنظام — يمكن تجاوزها عند إنشاء `ConversationalRAG`.

| الخاصية | النوع | القيمة الافتراضية | الوصف |
|---|---|---|---|
| `max_history_turns` | `int` | `10` | أقصى عدد دورات محفوظة |
| `context_turns` | `int` | `3` | عدد دورات تُستخدم في السياق |
| `enable_context_compression` | `bool` | `False` | ضغط السياق للمحادثات الطويلة |
| `include_sources` | `bool` | `True` | إضافة المصادر للإجابة افتراضياً |
| `use_history` | `bool` | `True` | استخدام التاريخ افتراضياً |
| `auto_save_history` | `bool` | `True` | حفظ تلقائي بعد كل دورة |
| `history_save_path` | `str` | `"conversations"` | مجلد الحفظ الافتراضي |

---

## `ConversationTurn`

يمثل دورة واحدة من المحادثة (سؤال + جواب).

```python
@dataclass
class ConversationTurn:
    query: str
    answer: str
    timestamp: datetime
    chunks: Optional[List[str]] = None   # القطع المسترجعة
    retrieved_chunks: int = 0            # عدد القطع
```

### الدوال

| الدالة | الوصف |
|---|---|
| `__str__()` | تحويل إلى نص `"Question: ...\nAnswer: ..."` |
| `to_dict()` | تسلسل إلى dict للحفظ في JSON (يشمل chunks) |
| `from_dict(data)` | إنشاء كائن من dict محمّل من JSON |

---

## `ConversationHistory`

مدير التاريخ مع الحفظ المباشر (live) في JSON.

```python
ConversationHistory(
    max_turns: int = 10,
    history_file: Optional[str] = None   # None = اسم تلقائي بالتاريخ والوقت
)
```

### الدوال

| الدالة | الوصف |
|---|---|
| `add_turn(query, answer, chunks, retrieved_chunks)` | إضافة دورة وحفظ فوري في JSON |
| `get_recent_turns(n=3)` | آخر n دورات |
| `format_for_prompt(n=3, language='ar')` | تنسيق التاريخ لإدراجه في الـ prompt |
| `clear()` | مسح التاريخ من الذاكرة (لا يحذف ملف JSON) |
| `get_file_path()` | المسار الكامل لملف JSON |
| `__len__()` | عدد الدورات الحالية |

> **ملاحظة:** `clear()` تمسح الدورات من الذاكرة فقط، لكنها **لا تحذف** ملف JSON السابق ولا تكتب عليه.

---

## `ConversationalRAG`

### `__init__`

```python
ConversationalRAG(
    rag_system,
    max_history_turns: int = 10,
    context_turns: int = 3,
    enable_context_compression: bool = False,
    instructions: Optional[str] = None,
    lang: str = 'ar',
    history_file: Optional[str] = None,
    auto_save: bool = True
)
```

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---|---|---|---|
| `rag_system` | Any | — | نظام RAG الأساسي **(مطلوب)** |
| `max_history_turns` | `int` | `10` | أقصى عدد دورات في التاريخ |
| `context_turns` | `int` | `3` | عدد الدورات في سياق الـ prompt |
| `enable_context_compression` | `bool` | `False` | ضغط السياق (غير مُفعَّل حالياً) |
| `instructions` | `str` | `None` | تعليمات مخصصة — إن لم تُحدَّد تُختار تلقائياً حسب `lang` |
| `lang` | `str` | `'ar'` | لغة التعليمات الافتراضية: `'ar'`، `'en'`، أو أي لغة أخرى |
| `history_file` | `str` | `None` | مسار JSON للحفظ — يُنشئ تلقائياً إن لم يُحدَّد |
| `auto_save` | `bool` | `True` | حفظ تلقائي بعد كل سؤال |

> إذا كان `lang` غير `'ar'` أو `'en'`، تُستخدم تعليمات إنجليزية افتراضية عامة.

---

### `ask`

```python
ask(
    query: str,
    include_sources: bool = True,   # من config.include_sources
    use_history: bool = True        # من config.use_history
) -> str
```

**الوصف:** طرح سؤال مع مراعاة سياق المحادثة السابقة.

**آلية العمل:**
1. تعزيز الاستعلام بالسياق إن وُجدت إشارات مرجعية (`هذا`، `ذلك`، `this`، `it`...)
2. استرجاع القطع ذات الصلة عبر `rag.retrieve()`
3. بناء الـ prompt مع التاريخ والسياق والتعليمات
4. توليد الجواب عبر `rag.llm.generate()`
5. إضافة المصادر إن طُلبت
6. حفظ الدورة في التاريخ

**Return:** `str` — الإجابة (وتشمل المصادر إن كان `include_sources=True`)

---

### `reset_conversation`

```python
reset_conversation() -> None
```

مسح جميع دورات التاريخ من الذاكرة. لا يحذف ملف JSON الحالي.

---

### `get_conversation_summary`

```python
get_conversation_summary() -> dict
```

**Return:**
```python
{
    "total_turns": 5,
    "total_queries": 5,
    "context_used_count": 3,
    "total_chunks_retrieved": 15,
    "avg_chunks_per_query": 3.0,
    "history_file": "/path/to/conversation_20240101_120000.json",
    "recent_topics": ["ما هو الذكاء الاصطناعي؟", ...]
}
```

---

### `export_conversation`

```python
export_conversation(
    format: str = 'json',
    output_file: Optional[str] = None
) -> str
```

| المعامل | الوصف |
|---|---|
| `format` | `'json'` أو `'text'` — أي قيمة أخرى ترفع `ValueError` |
| `output_file` | مسار لحفظ المحتوى (اختياري) |

**Return:** `str` — محتوى المحادثة بالصيغة المطلوبة

---

### `load_conversation_from_file`

```python
load_conversation_from_file(file_path: str) -> None
```

تحميل تاريخ محادثة سابقة من ملف JSON. يدعم صيغتين:
- ملف به `session_info` + `turns` (ناتج عن `ConversationHistory`)
- مصفوفة مباشرة من الدورات (ناتج عن `export_conversation`)

---

### `get_history_file_path`

```python
get_history_file_path() -> str
```

المسار الكامل لملف JSON الذي يحفظ فيه التاريخ تلقائياً.

---

### `__repr__`

```python
repr(conv_rag)
# ConversationalRAG(turns=3, queries=3, file=conversation_20240101_120000.json)
```

---

## الواجهة غير المتزامنة

### `aask`

```python
await conv_rag.aask(
    query: str,
    include_sources: bool = True,
    use_history: bool = True
) -> str
```

نفس سلوك `ask()` لكن غير متزامن عبر `asyncio.to_thread`.

### `astream`

```python
async for token in conv_rag.astream(query, use_history=True):
    print(token, end="", flush=True)
```

- إن كان `rag_system` يدعم `astream()` → يُستخدم مباشرة
- إن لا → يُوزَّع الجواب كلمة كلمة

### Context Manager

```python
async with ConversationalRAG(rag_system=base_rag) as conv_rag:
    answer = await conv_rag.aask("سؤالك هنا")
```

---

## تعزيز الاستعلام بالسياق

النظام يكتشف تلقائياً الإشارات المرجعية ويُضيف السياق:

**كلمات مدمجة:** `هذا`، `ذلك`، `نفسه`، `أيضاً`، `كذلك`، `بالإضافة`، `this`، `that`، `it`، `also`، `too`، `as well`

**إضافة كلمات مخصصة:** ضع ملف `context_indicators.txt` بجانب النظام، كل كلمة في سطر.

```
هو
هي
they
them
```

---

## مثال عملي كامل

```python
from rag.core import RAGSystem, RAGConfig
from rag.conversational_rag import ConversationalRAG
from vector_database import FAISSVectorDatabase
from embeddings import OpenAIEmbedder
from llm import OpenAIInterface
from chunks import TextSplitter
from context import ContextManager

# --- 1. إعداد النظام الأساسي ---
embedder = OpenAIEmbedder(api_key="sk-...")
vector_db = FAISSVectorDatabase(embedder=embedder)
llm = OpenAIInterface(api_key="sk-...")
chunker = TextSplitter(chunk_size=500)
ctx_manager = ContextManager()

base_rag = RAGSystem(
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
)

# إضافة مستندات
base_rag.add_documents({
    "python_doc": """
        بايثون لغة برمجة عالية المستوى تتميز بوضوح الكود وسهولة التعلم.
        تُستخدم في علم البيانات، تطوير الويب، والذكاء الاصطناعي.
        أنشأها غيدو فان روسم عام 1991.
    """,
    "libraries": """
        أشهر مكتبات بايثون: NumPy للحسابات العددية، Pandas لمعالجة البيانات،
        TensorFlow وPyTorch للتعلم العميق، Flask وDjango لتطوير الويب،
        وScikit-learn للتعلم الآلي.
    """,
})

# --- 2. إنشاء نظام المحادثة ---
conv_rag = ConversationalRAG(
    rag_system=base_rag,
    max_history_turns=10,
    context_turns=3,
    lang="ar",
    history_file="my_conversation.json",
    auto_save=True,
)

print(f"📁 ملف التاريخ: {conv_rag.get_history_file_path()}")

# --- 3. محادثة متسلسلة ---
print("\n" + "="*50)
print("🤖 بدء المحادثة")
print("="*50)

q1 = "ما هي لغة بايثون؟"
print(f"\n👤 {q1}")
a1 = conv_rag.ask(q1, include_sources=True)
print(f"🤖 {a1}")

# السؤال الثاني — "أنشأها" يُشير لبايثون فيُعزَّز الاستعلام تلقائياً
q2 = "من أنشأها وفي أي سنة؟"
print(f"\n👤 {q2}")
a2 = conv_rag.ask(q2)
print(f"🤖 {a2}")

q3 = "ما أشهر مكتباتها؟"
print(f"\n👤 {q3}")
a3 = conv_rag.ask(q3)
print(f"🤖 {a3}")

# --- 4. ملخص المحادثة ---
print("\n📊 ملخص المحادثة:")
summary = conv_rag.get_conversation_summary()
for key, value in summary.items():
    print(f"  {key}: {value}")

# --- 5. تصدير المحادثة ---
json_export = conv_rag.export_conversation(format='json', output_file='chat_export.json')
print(f"\n💾 تم التصدير بصيغة JSON")

text_export = conv_rag.export_conversation(format='text')
print(f"\n📄 المحادثة كنص:\n{text_export[:200]}...")

# --- 6. تحميل محادثة سابقة ---
conv_rag2 = ConversationalRAG(rag_system=base_rag)
conv_rag2.load_conversation_from_file("my_conversation.json")
print(f"\n✅ تم تحميل {len(conv_rag2.history.turns)} أدوار من الملف")

# --- 7. إعادة تعيين المحادثة ---
conv_rag.reset_conversation()
print("\n🔄 تم مسح تاريخ المحادثة")

# --- 8. الاستخدام غير المتزامن ---
import asyncio

async def async_conversation():
    answer = await conv_rag.aask("ما هو بايثون؟", use_history=True)
    print(f"\n[Async] {answer[:100]}...")

    print("\n[Stream] ", end="")
    async for token in conv_rag.astream("ما أشهر مكتبات بايثون؟"):
        print(token, end="", flush=True)

asyncio.run(async_conversation())

# --- 9. Context Manager غير المتزامن ---
async def with_context_manager():
    async with ConversationalRAG(rag_system=base_rag, lang="en") as rag:
        answer = await rag.aask("What is Python?")
        print(answer)

asyncio.run(with_context_manager())
```

---

## ملاحظات مهمة

| الموضوع | التفصيل |
|---|---|
| **الحفظ التلقائي** | يحدث فور كل `add_turn()` — لا يحتاج استدعاء يدوي |
| **مسح التاريخ** | `reset_conversation()` يمسح الذاكرة فقط، ملف JSON يبقى |
| **`export` مقابل الحفظ التلقائي** | الحفظ التلقائي بصيغة `ConversationHistory`، أما `export` فيُنتج مصفوفة مباشرة |
| **تعزيز الاستعلام** | يعمل على آخر دورتين فقط للحد من الضوضاء |
| **`enable_context_compression`** | معامل محجوز للمستقبل، لا يؤثر حالياً على السلوك |