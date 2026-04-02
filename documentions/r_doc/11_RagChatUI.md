# 🖥️ RagChatUI — واجهة محادثة احترافية

## نظرة عامة

`RagChatUI` يُحوّل **أي RAGSystem** إلى واجهة محادثة ويب احترافية تعمل في المتصفح. مبنية على Flask وتدعم: رفع الملفات، الجلسات المتعددة، البث المباشر للإجابات، والعمل البرمجي بدون واجهة.

---

## التثبيت والاستيراد

```python
from rag.rag_ui import RagChatUI
```

### المتطلبات الإضافية

```bash
pip install flask
```

---

## الدوال الرئيسية

### `__init__`

```python
RagChatUI(
    rag,
    title="RAG Chat",
    description="you can ask about anything in your documents",
    theme="dark",
    max_sessions=30,
    include_sources=True,
    language=None,  # الافضل تعملها None لو انت عايزه يجاوب بنفس لغه السوال
    allowed_extensions=None,
    on_upload=None
)
```

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---|---|---|---|
| `rag` | Any | — | RAGSystem (مطلوب) |
| `title` | `str` | `"RAG Chat"` | عنوان الواجهة في المتصفح |
| `description` | `str` | `"you can ask..."` | وصف في شاشة الترحيب |
| `theme` | `str` | `"dark"` | `"dark"` أو `"light"` |
| `max_sessions` | `int` | `30` | أقصى عدد جلسات في الذاكرة |
| `include_sources` | `bool` | `True` | إظهار مصادر الإجابة |
| `language` | `str` | `None` | تحديد لغة الإجابة |
| `allowed_extensions` | `set` | تلقائي | امتدادات الملفات المسموح برفعها |
| `on_upload` | `Callable` | `None` | معالج رفع مخصص `fn(path, doc_id) -> str` |

---

### `launch`

```python
launch(
    host: str = "0.0.0.0",
    port: int = 7860,
    open_browser: bool = True,
    debug: bool = False
) -> None
```

**الوصف:** تشغيل خادم الواجهة. يفتح المتصفح تلقائيًا.

| المعامل | النوع | الوصف |
|---|---|---|
| `host` | `str` | عنوان الاستماع |
| `port` | `int` | رقم المنفذ |
| `open_browser` | `bool` | فتح المتصفح تلقائيًا |
| `debug` | `bool` | وضع التشخيص في Flask |

---

### `ask`

```python
ask(query: str, session_id: Optional[str] = None) -> Dict[str, Any]
```

**الوصف:** إرسال سؤال برمجيًا (بدون واجهة).

**يُرجع:**
```python
{
    "session_id": "abc-123",
    "session_title": "جلسة 1",
    "answer": "الإجابة",
    "sources": [...],
    "latency_ms": 350.2,
    "msg_id": "msg-456"
}
```

---

### `create_session` / `get_session` / `delete_session`

```python
session = ui.create_session()       # إنشاء جلسة جديدة
session = ui.get_session(sid)       # الحصول على جلسة
ok = ui.delete_session(sid)         # حذف جلسة
```

---

### `get_stats`

```python
get_stats() -> Dict[str, Any]
```

**يُرجع:**
```python
{
    "sessions": 3,
    "total_messages": 42,
    "rag": {...}
}
```

---

## واجهة برمجة التطبيقات REST API

الواجهة تُوفّر هذه نقاط نهاية تلقائيًا:

| المسار | الطريقة | الوصف |
|---|---|---|
| `GET /` | GET | الصفحة الرئيسية |
| `GET /api/health` | GET | فحص الحالة |
| `POST /api/session/new` | POST | إنشاء جلسة جديدة |
| `GET /api/sessions` | GET | قائمة الجلسات |
| `GET /api/session/<sid>` | GET | تفاصيل جلسة |
| `DELETE /api/session/<sid>` | DELETE | حذف جلسة |
| `POST /api/session/<sid>/clear` | POST | مسح رسائل جلسة |
| `POST /api/chat` | POST | إرسال سؤال |
| `POST /api/chat/stream` | POST | إرسال سؤال مع بث SSE |
| `POST /api/upload` | POST | رفع ملف |
| `GET /api/stats` | GET | إحصائيات |

---

## مثال عملي كامل

```python
from rag.core import RAGSystem
from rag.rag_ui import RagChatUI
from vector_database import FAISSVectorDatabase
from vector_database import ChromaVectorDatabase
from embeddings import OpenAIEmbedder
from llm import OpenAIInterface
from chunks import TextSplitter
from context import ContextManager

# --- 1. إعداد نظام RAG ---
embedder = OpenAIEmbedder(api_key="sk-...")
vector_db = FAISSVectorDatabase(embedder=embedder)
llm = OpenAIInterface(api_key="sk-...")
chunker = TextSplitter(chunk_size=500, overlap=100)
ctx_manager = ContextManager()


system = RAGSystem(
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
)

# --- 2. إضافة مستندات عبر add_documents() ---
system.add_documents({
    "guide": """
        دليل الشركة: تأسست شركتنا عام 2020 وتعمل في مجال التقنية.
        ساعات العمل من 9 صباحًا حتى 5 مساءً. العطل الرسمية يوم الجمعة.
    """,
    "products": """
        منتجاتنا: نظام إدارة المشاريع، منصة التحليلات، أدوات الذكاء الاصطناعي.
        الأسعار تبدأ من 99 دولارًا شهريًا مع تجربة مجانية 30 يومًا.
    """,
    "support": """
        للدعم التقني: support@company.com أو الاتصال على 800-1234.
        الدعم متاح 24 ساعة للعملاء بالباقة المتميزة.
    """,
})

# --- 3. معالج رفع مخصص (اختياري) ---
def custom_upload_handler(file_path: str, doc_id: str) -> str:
    import PyPDF2
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = "\n".join(p.extract_text() for p in reader.pages)
    system.add_documents({doc_id: text})
    return f"✅ تم رفع PDF وإضافته ({len(text)} حرف)"

# --- 4. إنشاء الواجهة ---
ui = RagChatUI(
    rag=system,
    title="مساعد الشركة الذكي",
    description="اسألني عن أي شيء متعلق بالشركة، المنتجات، أو الدعم التقني",
    theme="dark",
    max_sessions=50,
    include_sources=True,
    allowed_extensions={".pdf", ".txt", ".docx"},
    on_upload=custom_upload_handler,
)

# --- 5. الاستخدام البرمجي (بدون واجهة) ---
print("=== الاستخدام البرمجي ===")

# إنشاء جلسة
session = ui.create_session()
sid = session.session_id
print(f"🆕 جلسة جديدة: {sid}")

# سؤال أول
result1 = ui.ask("ما هي ساعات العمل؟", session_id=sid)
print(f"\n❓ ما هي ساعات العمل؟")
print(f"✅ {result1['answer']}")
print(f"📚 المصادر: {result1['sources']}")   # ← تُستخرج من retrieve()
print(f"⚡ {result1['latency_ms']:.0f}ms")

# سؤال ثانٍ في نفس الجلسة
result2 = ui.ask("وما هو سعر منتجاتكم؟", session_id=sid)
print(f"\n❓ وما هو سعر منتجاتكم؟")
print(f"✅ {result2['answer']}")

# سؤال في جلسة جديدة (تُنشأ تلقائيًا)
result3 = ui.ask("كيف أتواصل مع الدعم التقني؟")
new_sid = result3["session_id"]
print(f"\n❓ كيف أتواصل مع الدعم؟")
print(f"✅ {result3['answer']}")
print(f"🆕 جلسة جديدة تلقائيًا: {new_sid}")

# تفاصيل الجلسة
session_data = ui.get_session(sid)
if session_data:
    print(f"\n📋 تفاصيل الجلسة {sid}:")
    print(f"  العنوان    : {session_data.title}")
    print(f"  عدد الرسائل: {session_data.message_count}")

# الإحصائيات
stats = ui.get_stats()
print(f"\n📊 إحصائيات:")
print(f"  الجلسات        : {stats['sessions']}")
print(f"  إجمالي الرسائل : {stats['total_messages']}")
print(f"  RAG stats      : {stats['rag']}")

# حذف جلسة
#ui.delete_session(new_sid)
#print(f"\n🗑️ تم حذف الجلسة {new_sid}")

# --- 6. تشغيل الواجهة ---
ui.launch(port=7860, open_browser=True)
```