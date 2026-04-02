> **نظرة عامة | Overview**  
> هذه المكتبة توفر نظاماً متكاملاً لتقسيم النصوص إلى قطع (chunks) مع دعم للغة العربية، ولغات أخرى، مع إمكانية التقسيم الدلالي (Semantic Chunking) باستخدام نماذج Hugging Face.  
> This library provides a complete system for splitting texts into chunks, supporting Arabic anothers languages with optional semantic chunking via Hugging Face models.

---


---



### `DocumentChunk` - نمازج البيانات

**الوصف:** يمثل قطعة نص واحدة ناتجة عن عملية التقسيم. يحتوي على النص والمعرّفات والبيانات الوصفية والـ embedding الاختياري.

**الحقول | Fields:**

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `chunk_id` | `str` | معرّف فريد للقطعة — مطلوب |
| `doc_id` | `str` | معرّف المستند الأصلي — مطلوب |
| `text` | `str` | محتوى النص — لا يمكن أن يكون فارغاً |
| `embedding` | `np.ndarray` *(اختياري)* | تمثيل متجهي للنص |
| `metadata` | `Dict` | بيانات وصفية إضافية (الحجم، اللغة، الجودة...) |

**مثال:**

```python
from chunks import DocumentChunk

chunk = DocumentChunk(
    chunk_id="doc1_chunk_0",
    doc_id="doc1",
    text="هذا النص هو محتوى القطعة الأولى."
)
print(chunk.text)
# هذا النص هو محتوى القطعة الأولى.
```

> ⚠️ `ValueError` إذا كان `chunk_id` أو `doc_id` فارغاً، أو إذا كان `text` فارغاً أو يحتوي على مسافات فقط.

---

### `Document`

**الوصف:** يمثل مستنداً كاملاً قبل التقسيم. يتكون من محتوى النص وبيانات وصفية.

**الحقول | Fields:**

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `page_content` | `str` | محتوى النص الكامل |
| `metadata` | `Dict` | بيانات وصفية (المصدر، التاريخ، ...) |

**مثال:**

```python
from chunks import Document

doc = Document(
    page_content="هذا مستند يحتوي على نصوص عربية مهمة.",
    metadata={"source": "article.pdf", "date": "2024-01-01"}
)
print(doc.metadata["source"])
# article.pdf
```

---



### `ChunkConfig` - الإعدادات المركزية

**الوصف:** `dataclass` يحتوي على جميع الإعدادات الافتراضية للمكتبة. يُستخدم كمرجع مركزي يمكن تعديله بسهولة دون تغيير الكود في أماكن متعددة.

**أهم الإعدادات:**

| الإعداد | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `chunk_size` | `512` | الحد الأقصى لحجم القطعة بالأحرف |
| `overlap` | `128` | عدد أحرف التداخل بين القطع المتتالية |
| `min_chunk_size` | `50` | الحد الأدنى لحجم القطعة |
| `use_semantic_chunking` | `False` | تفعيل التقسيم الدلالي |
| `preserve_formatting` | `True` | الحفاظ على تنسيق النص |
| `fix_spacing` | `True` | إصلاح المسافات تلقائياً |
| `strict_size_limit` | `True` | تطبيق حدود صارمة للحجم |
| `size_tolerance` | `0.05` | نسبة التسامح (5%) |
| `use_smart_overlap` | `True` | تفعيل التداخل الذكي |
| `smart_overlap_threshold` | `0.7` | عتبة التشابه للتداخل الذكي |
| `model_name` | `CAMeL-Lab/bert-base-arabic-camelbert-mix` | النموذج الافتراضي |

**مثال:**

```python
from chunks import ChunkConfig

config = ChunkConfig(chunk_size=256, overlap=64)
print(config.chunk_size)  # 256
print(config.arabic)      # CAMeL-Lab/bert-base-arabic-camelbert-mix
```

---



### `ChunkingStrategy` * (Abstract)* - الفئات الأساسية

**الوصف:** فئة مجردة (Abstract Base Class) تعرّف الواجهة الأساسية لأي استراتيجية تقسيم. يجب على أي كلاس يرث منها تطبيق الدالة `chunk`.

#### `chunk(text, doc_id)`

**الوصف:** تقسيم نص كامل إلى قائمة من `DocumentChunk`.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد تقسيمه |
| `doc_id` | `str` | معرّف المستند |

**Return:** `List[DocumentChunk]`

---

### `TextSplitter` *(Abstract)*

**الوصف:** فئة مجردة توفر البنية الأساسية لمقسّمات النص. تتعامل مع منطق تقسيم المستندات المتعددة وإنشاء كائنات `Document`.

#### `__init__(chunk_size, chunk_overlap, length_function)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `chunk_size` | `int` | `1000` | الحد الأقصى لحجم كل قطعة |
| `chunk_overlap` | `int` | `200` | عدد الأحرف المشتركة بين القطع المتتالية |
| `length_function` | `Callable` | `len` | دالة لحساب طول النص (يمكن استبدالها بعداد tokens) |

---

#### `split_documents(documents)`

**الوصف:** تقسيم قائمة كاملة من كائنات `Document` دفعةً واحدة مع الحفاظ على البيانات الوصفية.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `documents` | `List[Document]` | قائمة المستندات المراد تقسيمها |

**Return:** `List[Document]`

**مثال:**

```python
from chunks import Document
from chunks import RecursiveCharacterTextSplitter

docs = [
    Document(page_content="نص طويل جداً...", metadata={"source": "file1.txt"}),
    Document(page_content="نص آخر...",       metadata={"source": "file2.txt"}),
]

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
chunks = splitter.split_documents(docs)

for c in chunks:
    print(c.metadata["source"], "→", len(c.page_content), "حرف")
```

---

#### `create_documents(texts, metadatas)`

**الوصف:** إنشاء قائمة من `Document` من قوائم نصوص وبيانات وصفية منفصلة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `texts` | `List[str]` | قائمة النصوص |
| `metadatas` | `List[Dict]` *(اختياري)* | قائمة البيانات الوصفية لكل نص |

**Return:** `List[Document]`

---



### `CharacterTextSplitter` - مقسم لنص بفاصل محدد

**الوصف:** يقسّم النص اعتماداً على فاصل محدد (مثل سطر فارغ)، ثم يدمج القطع الصغيرة للوصول إلى `chunk_size` المطلوب. مناسب للنصوص ذات البنية الواضحة.

#### `__init__(separator, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `separator` | `str` | `"\n\n"` | الفاصل المستخدم للتقسيم الأولي |
| `chunk_size` | `int` | `1000` | الحد الأقصى للقطعة |
| `chunk_overlap` | `int` | `200` | التداخل بين القطع |

#### `split_text(text)`

**الوصف:** تقسيم نص واحد إلى قطع.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد تقسيمه |

**ٌReturn:** `List[str]`

**مثال:**

```python
from chunks import CharacterTextSplitter
splitter = CharacterTextSplitter(separator="\n\n", chunk_size=300, chunk_overlap=50)
text = "الفقرة الأولى...\n\nالفقرة الثانية...\n\nالفقرة الثالثة..."
chunks = splitter.split_text(text)
print(f"عدد القطع: {len(chunks)}")
```

---

### `RecursiveCharacterTextSplitter` - التقسيم الهرمي

**الوصف:** المقسّم الأكثر تطوراً في هذا الملف. يحاول تقسيم النص باستخدام سلسلة من الفواصل بشكل هرمي (من الأكثر عمومية إلى الأكثر تفصيلاً). إذا فشل الفاصل الأول، يجرب الثاني، وهكذا — مما يضمن الحفاظ على السياق.

**تسلسل الفواصل الافتراضية:** `"\n\n"` ← `"\n"` ← `" "` ← `""`

#### `__init__(separators, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `separators` | `List[str]` | `["\n\n", "\n", " ", ""]` | قائمة الفواصل مرتبة من العام إلى الخاص |
| `chunk_size` | `int` | `1000` | الحد الأقصى لكل قطعة |
| `chunk_overlap` | `int` | `200` | التداخل بين القطع |

**مثال:**

```python
from chunks import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

text = """
# مقدمة
هذا النص الأول في الفقرة الأولى.

هذا النص الثاني. وهو يحتوي على جمل متعددة مفصولة بنقطة.
"""
chunks = splitter.split_text(text)
for i, chunk in enumerate(chunks):
    print(f"القطعة {i}: {len(chunk)} حرف")
```

---

### `TokenTextSplitter` - تقسم بالكليمات

**الوصف:** يقسّم النص بناءً على عدد الـ tokens (وحدات النص) بدلاً من الأحرف، باستخدام مكتبة `tiktoken`. مفيد جداً عند العمل مع نماذج اللغة الكبيرة (LLMs) التي لها حد محدد بالـ tokens.

#### `__init__(encoding_name, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `encoding_name` | `str` | `"cl100k_base"` | اسم ترميز tiktoken (المستخدم في GPT-4) |
| `chunk_size` | `int` | `1000` | الحد الأقصى بعدد الـ tokens |
| `chunk_overlap` | `int` | `200` | التداخل بعدد الـ tokens |

> ⚠️ يتطلب تثبيت: `pip install tiktoken`

**مثال:**

```python
from chunks import TokenTextSplitter

splitter = TokenTextSplitter(encoding_name="cl100k_base", chunk_size=100, chunk_overlap=20)
text = "This is a long English text that needs to be split by token count..."
chunks = splitter.split_text(text)
print(f"Number of chunks: {len(chunks)}")
```

---


### `ArabicTextChunker` - مقسم خاص للغه العربيه

**الوصف:** المقسّم الأكثر تخصصاً للنصوص العربية. يدعم:
- 🔧 إصلاح المسافات تلقائياً
- 🧠 التقسيم الدلالي عبر نماذج BERT العربية
- 🔄 التداخل الذكي القائم على التشابه الدلالي
- 📏 حدود صارمة للحجم مع هامش تسامح
- 📊 إحصائيات تفصيلية عن جودة التقسيم

#### `__init__(...)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `chunk_size` | `int` | `512` | الحد الأقصى لحجم كل قطعة بالأحرف |
| `overlap` | `int` | `128` | عدد أحرف التداخل بين القطع |
| `min_chunk_size` | `int` | `50` | الحد الأدنى لقبول القطعة |
| `model_name` | `str` | `CAMeL-Lab/bert-base-arabic-camelbert-mix` | نموذج BERT للعربية |
| `use_semantic_chunking` | `bool` | `False` | تفعيل التقسيم الدلالي (يتطلب torch) |
| `device` | `str` | `None` | `"cuda"` أو `"cpu"` — يُكتشف تلقائياً |
| `preserve_formatting` | `bool` | `True` | الحفاظ على التنسيق الأصلي |
| `fix_spacing` | `bool` | `True` | إصلاح المسافات المفقودة |
| `strict_size_limit` | `bool` | `True` | رفض القطع التي تتجاوز الحد الأقصى |
| `size_tolerance` | `float` | `0.05` | نسبة تجاوز مسموح بها (5%) |
| `use_smart_overlap` | `bool` | `True` | تفعيل التداخل الذكي |
| `smart_overlap_threshold` | `float` | `0.7` | الحد الأدنى للتشابه لاختيار جملة تداخل |

---

#### `chunk(text, doc_id)`

**الوصف:** الدالة الرئيسية — تقسيم النص العربي إلى قائمة من `DocumentChunk`.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص العربي المراد تقسيمه |
| `doc_id` | `str` | معرّف المستند |

**Return:** `List[DocumentChunk]`

**مثال:**

```python
from chunks import ArabicTextChunker

chunker = ArabicTextChunker(chunk_size=300, overlap=60)
text = "الذكاء الاصطناعي هو محاكاة للذكاء البشري في الآلات. يشمل التعلم الآلي ومعالجة اللغة الطبيعية..."
chunks = chunker.chunk(text, doc_id="article_001")

for chunk in chunks:
    print(f"القطعة {chunk.chunk_id}: {len(chunk.text)} حرف")
```

---

#### `chunk_text(text, doc_id)`

**الوصف:** دالة بديلة لـ `chunk` للتوافق مع واجهات قديمة. تُنتج نفس النتيجة تماماً.

```python
chunks = chunker.chunk_text(text, doc_id="doc_001")
```

---

#### `analyze_text_quality(text)`

**الوصف:** تحليل جودة النص قبل التقسيم. يُرجع تقريراً يشمل عدد الكلمات، الجمل، مشاكل المسافات، ونقاط الجودة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد تحليله |

**Return:** `dict` يحتوي على:
- `original_length` / `fixed_length`: الطول قبل وبعد الإصلاح
- `spaces_added`: عدد المسافات المضافة
- `word_count_original` / `word_count_fixed`: عدد الكلمات
- `is_arabic`: هل النص عربي؟
- `sentence_count`: عدد الجمل
- `quality_score`: درجة الجودة (0.0 إلى 1.0)

**مثال:**

```python
report = chunker.analyze_text_quality("الذكاء الاصطناعي.معالجة اللغة")
print(f"درجة الجودة: {report['quality_score']}")
print(f"مسافات مُضافة: {report['spaces_added']}")
```

---

#### `get_chunking_stats(chunks)`

**الوصف:** تحليل إحصائي شامل لقائمة قطع ناتجة عن التقسيم.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `chunks` | `List[DocumentChunk]` | القطع المراد تحليلها |

**Return:** `dict` يحتوي على:
- `total_chunks`: العدد الإجمالي
- `size_stats`: (min, max, avg, median)
- `compliance`: نسبة الامتثال لحدود الحجم
- `smart_overlap`: إحصائيات التداخل الذكي
- `oversized_chunks`: القطع التي تجاوزت الحد

**مثال:**

```python
chunker = ArabicTextChunker(chunk_size=300)
chunks = chunker.chunk(long_text, "doc_01")
stats = chunker.get_chunking_stats(chunks)

print(f"عدد القطع: {stats['total_chunks']}")
print(f"متوسط الحجم: {stats['size_stats']['avg']:.0f} حرف")
print(f"نسبة الامتثال: {stats['compliance']['compliance_rate']:.1f}%")
```

---

#### `get_embeddings_batch(texts)`

**الوصف:** توليد متجهات تضمين (embeddings) لقائمة من النصوص دفعةً واحدة باستخدام نموذج BERT. يتطلب تفعيل `use_semantic_chunking=True`.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `texts` | `List[str]` | قائمة النصوص |

**Return:** `torch.Tensor` بشكل `(N, hidden_size)`

**مثال:**

```python
chunker = ArabicTextChunker(use_semantic_chunking=True)
embeddings = chunker.get_embeddings_batch(["نص أول", "نص ثاني", "نص ثالث"])
print(embeddings.shape)  # (3, 768)
```

---

#### `create_safely(**kwargs)` *(classmethod)*

**الوصف:** طريقة آمنة لإنشاء كائن `ArabicTextChunker` — تتجاهل تلقائياً أي `parameters` غير معروفة بدلاً من إطلاق خطأ.

**مثال:**

```python
chunker = ArabicTextChunker.create_safely(
    chunk_size=400,
    overlap=80,
    unsupported_param="value"  # سيتم تجاهله بدلاً من إطلاق خطأ
)
```

---

#### `get_available_parameters()` *(classmethod)*

**الوصف:** إرجاع قائمة بجميع الـ parameters المقبولة في `__init__`.

```python
params = ArabicTextChunker.get_available_parameters()
print(params)
# ['chunk_size', 'overlap', 'min_chunk_size', 'model_name', ...]
```

---



### `MultilanguageTextChunker` - متعدد اللغات

**الوصف:** نسخة موسّعة تدعم أكثر من  لغة مع اكتشاف تلقائي للغة، واختيار تلقائي للنموذج المناسب. يرث نفس فلسفة التقسيم الذكي والتداخل من المقسّم العربي مع إضافات للغات المتعددة.

**اللغات المدعومة صراحةً:**  
`arabic` • `english` • `french` • `spanish` • `german` • `chinese` • `japanese` • `korean` • `russian` • `portuguese` • `italian` • `dutch` • `polish` • `turkish` • `vietnamese` • `hindi` • `multilingual`

#### `__init__(...)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `chunk_size` | `int` | `512` | الحد الأقصى لحجم القطعة |
| `overlap` | `int` | `128` | عدد أحرف التداخل |
| `min_chunk_size` | `int` | `50` | الحد الأدنى |
| `model_name` | `str` | `None` | يُختار تلقائياً إذا كان `None` |
| `language` | `str` | `"auto"` | اللغة (`"auto"` للكشف التلقائي) |
| `use_semantic_chunking` | `bool` | `False` | التقسيم الدلالي |
| `device` | `str` | `None` | `"cuda"` أو `"cpu"` |
| `use_smart_overlap` | `bool` | `True` | التداخل الذكي |
| `smart_overlap_threshold` | `float` | `0.7` | عتبة التشابه |
| `strict_size_limit` | `bool` | `True` | حدود صارمة |
| `size_tolerance` | `float` | `0.05` | هامش التسامح (5%) |

---

#### `chunk(text, doc_id)`

**الوصف:** الدالة الرئيسية للتقسيم. تكتشف اللغة تلقائياً وتختار الاستراتيجية المناسبة.

**مثال — نص عربي:**

```python
from chunks import MultilanguageTextChunker
chunker = MultilanguageTextChunker(language="auto", chunk_size=400)
text = "الذكاء الاصطناعي يتطور بسرعة كبيرة في عالمنا المعاصر..."
chunks = chunker.chunk(text, doc_id="ar_doc_01")

for chunk in chunks:
    print(chunk.metadata["languages"])  # ['arabic']
```

**مثال — نص متعدد اللغات:**

```python
chunker = MultilanguageTextChunker(language="auto")
mixed_text = "This is English text. هذا نص عربي. C'est du texte français."
chunks = chunker.chunk(mixed_text, doc_id="mixed_01")
print(chunks[0].metadata["languages"])
```

---

#### `get_chunking_stats(chunks)`

**الوصف:** نفس إحصائيات `ArabicTextChunker` مع إضافة `detected_languages` — قائمة بجميع اللغات المكتشفة في مجموع القطع.

**مثال:**

```python
stats = chunker.get_chunking_stats(chunks)
print("اللغات المكتشفة:", stats["detected_languages"])
print("نسبة الامتثال:", stats["compliance"]["compliance_rate"])
```

---

#### `get_embeddings_batch(texts)`

**الوصف:** توليد embeddings لمجموعة نصوص. يعمل مع أي لغة مدعومة.

```python
chunker = MultilanguageTextChunker(use_semantic_chunking=True, language="english")
embeddings = chunker.get_embeddings_batch(["Hello world", "AI is great"])
print(embeddings.shape)  # (2, 768)
```

---

#### `get_supported_languages()` *(classmethod)*

**الوصف:** إرجاع قائمة بجميع اللغات المدعومة صراحةً.

```python
langs = MultilanguageTextChunker.get_supported_languages()
print(langs)
# ['multilingual', 'english', 'arabic', 'chinese', ...]
```

---

#### `get_recommended_model(language)` *(classmethod)*

**الوصف:** إرجاع اسم النموذج الموصى به للغة المحددة. إذا لم تكن اللغة مدعومة صراحةً، يُرجع النموذج متعدد اللغات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `language` | `str` | اسم اللغة بالإنجليزية |

**مثال:**

```python
model = MultilanguageTextChunker.get_recommended_model("arabic")
print(model)  # CAMeL-Lab/bert-base-arabic-camelbert-mix

model = MultilanguageTextChunker.get_recommended_model("swahili")
print(model)  # xlm-roberta-base (fallback)
```

---

## 🚀 أمثلة متكاملة

### تهيئه Documents

```python
from chunks import DocumentChunk, Document

chunk = DocumentChunk(
    chunk_id="doc1_chunk_0",
    doc_id="doc1",
    text="الذكاء الاصطناعي يُحدث ثورة في معالجة اللغات الطبيعية.",
    metadata={"source": "article_ai.pdf", "page": 1}
)
print(f"chunk_id : {chunk.chunk_id}")
print(f"text     : {chunk.text}")

doc = Document(
    page_content="هذا مستند تجريبي يحتوي على نصوص متعددة.",
    metadata={"author": "محمد", "lang": "ar"}
)
```


### مثال 1: استخدام CharacterTextSplitter

```python
from chunks import CharacterTextSplitter, Document
text = "الفصل الأول: مقدمة في الذكاء الاصطناعي.الذكاء الاصطناعي هو محاكاة الذكاء البشري في الآلات.الفصل الثاني: تطبيقات الذكاء الاصطناعي.تشمل التطبيقات: التعرف على الصوت، ومعالجة اللغات الطبيعية."
splitter = CharacterTextSplitter(separator=".", chunk_size=120, chunk_overlap=30)
chunks = splitter.split_text(text)

print(f"عدد القطع: {len(chunks)}")
for i, ch in enumerate(chunks):
    print(f"  [{i}] ({len(ch)} chars) → {ch[:60]}…")

# split_documents
docs = [Document(page_content=text, metadata={"source": "chapter.txt"})]
doc_chunks = splitter.split_documents(docs)
print(f"مستندات بعد التقسيم: {len(doc_chunks)}")
```

---

### مثال 2: استخدام RecursiveCharacterTextSplitter

```python
from chunks import RecursiveCharacterTextSplitter
english_text = """
    Machine learning is a branch of artificial intelligence.
    It allows computers to learn from data
    Deep learning uses neural networks with many layers.
    It models complex patterns in data.
    """
splitter = RecursiveCharacterTextSplitter(
    separators=["\n"],
    chunk_size=150,
    chunk_overlap=20
)
chunks = splitter.split_text(english_text)
for i, ch in enumerate(chunks):
    print(f"  [{i}] ({len(ch):3d} chars) {ch[:80]}…")
```

---

### مثال 3: باستخدام TokenTextSplitter 

```python
from chunks import TokenTextSplitter

splitter = TokenTextSplitter(
    encoding_name="cl100k_base",
    chunk_size=10,
    chunk_overlap=0
)

text = (
    "Artificial Intelligence is transforming industries worldwide. "
    "From healthcare to finance, AI-powered solutions are automating tasks."
)

chunks = splitter.split_text(text)
for i, ch in enumerate(chunks):
    print(f"  [{i}] ({len(ch):3d} chars) {ch}")
```
--

### مثال 4: استخدام ArabicTextChunker

```python
from chunks import ArabicTextChunker

arabic_text = """
تُعدّ معالجة اللغة العربية من أصعب مجالات الذكاء الاصطناعي نظراً لتعقيد بنية اللغة.
تحتوي اللغة العربية على نظام صرفي ثري يختلف جذرياً عن اللغات الأوروبية.
أسفر التطور السريع لنماذج اللغة الكبيرة عن تحسينات ملموسة في فهم النصوص العربية.
"""*30

chunker = ArabicTextChunker(
    chunk_size=100,
    overlap=30,
    fix_spacing=False,
    use_smart_overlap=True,
    strict_size_limit=False,
)

chunks = chunker.chunk(arabic_text.strip(), doc_id="arabic_doc_1")
print(f"عدد القطع: {len(chunks)}")

for chunk in chunks:
    print(f"chunk_id  : {chunk.chunk_id}")
    print(f"  length    : {chunk.metadata['length']} حرف")
    print(f"  quality   : {chunk.metadata['quality_score']:.2f}")
    print(f"  text      : {chunk.text[:80]}…")

# إحصائيات التقسيم
stats = chunker.get_chunking_stats(chunks)
print(stats)

# تحليل جودة النص
quality = chunker.analyze_text_quality(arabic_text.strip())
print(f"جودة النص     : {quality['quality_score']:.2f}")
print(f"مشاكل مسافات  : {quality['has_spacing_issues']}")
```
---

### مثال 5: استخدام MultilanguageTextChunker
--
```python
from chunks import MultilanguageTextChunker

samples = {
    "Arabic": "التعلم الآلي هو فرع من فروع الذكاء الاصطناعي. يُستخدم في تطبيقات متعددة.",
    "English": "Machine learning is a branch of AI. It is used in many applications.",
    "French": "L'apprentissage automatique est une branche de l'IA. Il est utilisé dans de nombreuses applications.",
}

for lang_name, text in samples.items():
    chunker = MultilanguageTextChunker(chunk_size=200, overlap=40, language="auto")
    chunks = chunker.chunk(text, doc_id=f"{lang_name.lower()}_doc")

    print(f"── {lang_name} ──")
    print(f"  اللغة المكتشفة : {chunks[0].metadata.get('languages', [])}")
    print(f"  النموذج        : {chunks[0].metadata.get('model_used', 'N/A')}")
    print(f"  عدد القطع      : {len(chunks)}")
```
## ⚠️ متطلبات التثبيت

```bash
# متطلبات أساسية
pip install numpy

# للتقسيم الدلالي
pip install torch transformers

# لمقسّم الـ Tokens
pip install tiktoken
```

---

## 🔑 ملخص مقارنة الكلاسات

| الكلاس | اللغة | التقسيم الدلالي | التداخل الذكي | الأنسب لـ |
|--------|-------|----------------|--------------|-----------|
| `CharacterTextSplitter` | أي | ❌ | ❌ | نصوص بسيطة بفواصل واضحة |
| `RecursiveCharacterTextSplitter` | أي | ❌ | ❌ | نصوص عامة بدون بنية ثابتة |
| `TokenTextSplitter` | أي | ❌ | ❌ | العمل مع نماذج LLM مثل GPT |
| `ArabicTextChunker` | عربي | ✅ | ✅ | النصوص العربية المتخصصة |
| `MultilanguageTextChunker` | متعدد | ✅ | ✅ | النصوص متعددة اللغات |

## ⚠️ ملاحظات مهمة
--
| الموضوع | الملاحظة |
|--------|----------|
| التقسيم الدلالي | يتطلب تحميل نموذج (~400MB+) — ابدأ بـ False ثم فعّله عند الحاجة |
| GPU | يُحمَّل تلقائياً عند توفر CUDA — مرر `device="cpu"` لإلزام المعالج |
| Fallback | عند فشل تحميل النموذج، يتراجع النظام تلقائياً للتقسيم التقليدي |
| overlap | يجب أن يكون أقل من `chunk_size` دائماً |
| min_chunk_size | يجب أن يكون > 0 وأقل من `chunk_size` |
| النصوص المختلطة | استخدم `MultilanguageTextChunker` مع `language="auto"` |
| get_embeddings_batch | يستهلك ذاكرة أكبر مع النصوص الطويلة — قسّمها لـ batches |
| create_safely | الطريقة الأأمن في الإنتاج — تتجنب الأعطال من المعاملات غير المتوقعة |
