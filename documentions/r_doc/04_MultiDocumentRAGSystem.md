# 📘 MultiDocumentRAGSystem — نظام RAG متعدد المستندات

## نظرة عامة

`MultiDocumentRAGSystem` هو نظام RAG مستقل (لا يرث من `BaseRAGSystem`) يُتيح إدارة مستندات متعددة بشكل منفصل. يوفر واجهة أكثر ثراءً من `RAGSystem` من حيث: تتبع كل مستند على حدة، دعم `metadata`، كشف اللغة تلقائياً، فلترة الاستعلامات بمستندات محددة، والتحديث الجزئي دون إعادة بناء كامل.

---

## الاستيراد

```python
from rag.core.multi_doc_rag import MultiDocumentRAGSystem
```

---

## `__init__`

```python
MultiDocumentRAGSystem(
    vector_db,
    llm,
    chunker,
    context_manager,
    config=None
)
```

نفس توقيع `RAGSystem` تماماً.

---

## إدارة المستندات

### `add_document`

```python
add_document(
    doc_id: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    chunk_independently: bool = True
) -> Dict[str, Any]
```

إضافة مستند واحد. يكشف اللغة تلقائياً إذا لم تُحدَّد. يرفض المستند إذا كان `doc_id` موجوداً مسبقاً ويطلب استخدام `update_document()` بدلاً منه.

**يُرجع:**
```python
# نجاح
{"success": True, "doc_id": "doc1", "num_chunks": 5, "language": "arabic", "metadata": {...}}

# فشل
{"success": False, "doc_id": "doc1", "error": "Document already exists. Use update_document()"}
```

**مثال:**
```python
result = rag.add_document(
    doc_id="policy_2024",
    text="نص السياسة الكاملة...",
    metadata={"source": "HR", "version": "2024"},
    language="arabic"
)
print(result["num_chunks"])  # 12
```

---

### `add_documents`

```python
add_documents(
    documents: Union[Dict[str, str], List[Dict[str, Any]]],
    global_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]
```

إضافة مستندات متعددة دفعة واحدة. يقبل صيغتين:

```python
# الصيغة البسيطة: Dict[doc_id, text]
rag.add_documents({"doc1": "نص...", "doc2": "نص..."})

# الصيغة الموسّعة: List مع metadata
rag.add_documents([
    {"doc_id": "doc1", "text": "نص...", "metadata": {"dept": "HR"}},
    {"doc_id": "doc2", "text": "نص...", "language": "english"},
])

# مع metadata مشتركة لجميع المستندات
rag.add_documents(docs, global_metadata={"project": "Q4"})
```

**يُرجع:** `Dict[doc_id, نتيجة_الإضافة]`

---

### `update_document`

```python
update_document(
    doc_id: str,
    new_text: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

يحذف المستند القديم ويُضيف النص الجديد محافظاً على `metadata` السابقة (مع دمج أي `metadata` جديدة).

```python
rag.update_document("policy_2024", new_text="النص المحدّث...")
```

---

### `remove_document`

```python
remove_document(doc_id: str) -> Dict[str, Any]
```

يحذف المستند وجميع chunks الخاصة به من قاعدة البيانات المتجهة.

```python
result = rag.remove_document("policy_2024")
print(result["chunks_removed"])  # عدد القطع المحذوفة
```

---

## الاستعلام

### `query`

```python
query(
    query: str,
    top_k: Optional[int] = None,
    filter_docs: Optional[List[str]] = None,
    include_sources: bool = True,
    language: str = "ar",
    **llm_kwargs
) -> Dict[str, Any]
```

يُختلف عن `RAGSystem.generate()` في أنه يُرجع قاموساً غنياً بالمعلومات بدلاً من نص مجرد.

| المعامل | الوصف |
|---|---|
| `filter_docs` | قائمة `doc_id` للبحث فيها فقط — `None` يبحث في الكل |
| `include_sources` | إضافة تفاصيل المصادر للنتيجة |
| `language` | لغة الـ prompt (`'ar'` أو `'en'`) |

**يُرجع:**
```python
{
    "success": True,
    "answer": "نص الإجابة...",
    "sources": [
        {
            "doc_id": "policy_2024",
            "score": 0.91,
            "language": "arabic",
            "metadata": {"dept": "HR"}
        }
    ],
    "num_results": 4
}
```

**مثال — بحث في مستندات محددة فقط:**
```python
result = rag.query(
    "ما هي سياسة الإجازات؟",
    filter_docs=["policy_2024", "policy_2023"],
    include_sources=True
)
if result["success"]:
    print(result["answer"])
    for src in result["sources"]:
        print(f"  ← {src['doc_id']} ({src['score']:.2f})")
```

---

## المعلومات والإحصائيات

### `get_document_info`

```python
get_document_info(doc_id: str) -> Optional[Dict[str, Any]]
```

يُرجع تفاصيل مستند واحد: النص الأصلي، قائمة chunk IDs، عدد القطع، metadata، تاريخ الإضافة، اللغة، والحالة.

---

### `list_documents`

```python
list_documents() -> List[Dict[str, Any]]
```

يُرجع ملخصاً لجميع المستندات (بدون النصوص الكاملة).

```python
for doc in rag.list_documents():
    print(f"{doc['doc_id']}: {doc['num_chunks']} chunks | {doc['language']}")
```

---

### `get_stats`

```python
get_stats() -> Dict[str, Any]
```

**يُرجع:**
```python
{
    "total_documents": 5,
    "total_chunks": 47,
    "total_queries": 20,
    "successful_queries": 19,
    "failed_queries": 1,
    "documents": {
        "doc1": {"num_chunks": 10, "language": "arabic"},
        "doc2": {"num_chunks": 8, "language": "english"}
    }
}
```

---

### `get_document_stats_summary`

```python
get_document_stats_summary() -> Dict[str, Any]
```

```python
{
    "total_documents": 5,
    "total_chunks": 47,
    "languages": {"arabic": 3, "english": 2},
    "avg_chunks_per_doc": 9.4
}
```

---

## الحفظ والتحميل

```python
# حفظ
rag.save("./my_multi_rag")

# تحميل
rag = MultiDocumentRAGSystem.load(
    "./my_multi_rag",
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
)
```

يحفظ النظام: قاعدة البيانات المتجهة، معلومات جميع المستندات (`documents.json`)، والإحصائيات (`stats.json`).

---

## الواجهة غير المتزامنة (Async)

| الدالة | الوصف |
|---|---|
| `agenerate(query, **kwargs)` | توليد إجابة بشكل غير متزامن |
| `aretrieve(query, **kwargs)` | استرجاع غير متزامن |

---

## الفرق بين `RAGSystem` و`MultiDocumentRAGSystem`

| الميزة | `RAGSystem` | `MultiDocumentRAGSystem` |
|---|---|---|
| تتبع المستندات | إحصائيات فقط | تفاصيل كاملة لكل مستند |
| `metadata` | ❌ | ✅ |
| كشف اللغة | ✅ | ✅ (مع دعم الصينية) |
| فلترة بمستندات محددة | ❌ | ✅ عبر `filter_docs` |
| تحديث مستند بدون إعادة بناء | ❌ | ✅ `update_document()` |
| يرث من `BaseRAGSystem` | ✅ | ❌ |
| Prompt Router / Reranker | ✅ | ❌ (prompt مدمج) |

---

## مثال عملي كامل

```python
from rag.core.multi_doc_rag import MultiDocumentRAGSystem

rag = MultiDocumentRAGSystem(
    vector_db=vector_db, llm=llm,
    chunker=chunker, context_manager=ctx_manager
)

# إضافة مستندات
rag.add_documents([
    {"doc_id": "hr_policy", "text": "...", "metadata": {"dept": "HR"}},
    {"doc_id": "tech_guide", "text": "...", "metadata": {"dept": "Tech"}},
])

# استعلام مع فلتر
res = rag.query("ما إجراءات الإجازة؟", filter_docs=["hr_policy"])
print(res["answer"])

# تحديث مستند
rag.update_document("hr_policy", new_text="النسخة المحدّثة...")

# إحصائيات
summary = rag.get_document_stats_summary()
print(summary)

# الحفظ
rag.save("./rag_backup")
```
