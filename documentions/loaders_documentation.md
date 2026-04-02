
> **نظرة عامة | Overview**  
> هذه المكتبة توفر نظاماً متكاملاً لتحميل المستندات من مصادر متنوعة: ملفات نصية، PDF، Word، CSV، Excel، JSON، HTML، صفحات ويب، ومجلدات كاملة. تعتمد على نموذج بيانات موحّد (`LoadedDocument`) وواجهة مجردة مشتركة تتيح التوسع السهل.  
> This library provides a unified system for loading documents from diverse sources — plain text, PDF, Word, CSV, Excel, JSON, HTML, web pages, and entire directories — all returning a consistent `LoadedDocument` model.

---


---

## نموذج البيانات والفئات الأساسية

### `LoadedDocument`

**الوصف:** نموذج البيانات المركزي الذي يُنتجه كل محمّل. يمثل مستنداً واحداً محملاً بمحتواه النصي وبياناته الوصفية. يُولِّد معرّفاً فريداً تلقائياً إذا لم يُقدَّم.

**الحقول | Fields:**

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `page_content` | `str` | المحتوى النصي للمستند |
| `metadata` | `Dict[str, Any]` | بيانات وصفية (المصدر، نوع الملف، الصفحة...) |
| `doc_id` | `str` *(اختياري)* | معرّف فريد — يُولَّد تلقائياً إذا لم يُعطَ |

**المثال:**

```python
from document_loaders import LoadedDocument

doc = LoadedDocument(
    page_content="هذا محتوى المستند.",
    metadata={"source": "report.pdf", "page_number": 1}
)
print(doc.doc_id)     # doc_a3f2b1c4_1718000000 (auto-generated)
print(doc.to_dict())  # {'doc_id': ..., 'page_content': ..., 'metadata': ...}
```

#### `to_dict()`

**الوصف:** تحويل المستند إلى قاموس Python عادي — مفيد للتسلسل (JSON، قواعد البيانات).

**Return:** `Dict[str, Any]`

```python
data = doc.to_dict()
import json
print(json.dumps(data, ensure_ascii=False, indent=2))
```

---

### `BaseDocumentLoader` *(Abstract)*

**الوصف:** الفئة الأساسية المجردة التي يرث منها كل محمّل في المكتبة. تُعرّف الواجهة المشتركة وتوفر أدوات مساعدة.

#### `__init__(encoding)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `encoding` | `str` | `"utf-8"` | ترميز النص المستخدم عند قراءة الملفات |

---

#### `load()` *(abstract)*

**الوصف:** تحميل المستندات وإرجاعها كقائمة كاملة في الذاكرة. يجب تطبيقها في كل فئة فرعية.

**Return:** `List[LoadedDocument]`

---

#### `lazy_load()`

**الوصف:** تحميل المستندات بشكل كسول (Generator) — مثالي للملفات الكبيرة جداً لتوفير الذاكرة. الإعداد الافتراضي يستدعي `load()` ويُعيد النتائج واحدة تلو الأخرى؛ الفئات الفرعية يمكنها تجاوزه لتدفق حقيقي.

**Return:** `Iterator[LoadedDocument]`

```python
loader = CSVLoader("large_file.csv")
for doc in loader.lazy_load():
    process(doc)  # يعالج كل صف دون تحميل الكل في الذاكرة
```

---

#### `load_and_split(text_splitter)`

**الوصف:** تحميل المستندات ثم تقسيمها مباشرةً باستخدام أي `TextSplitter` من وحدة `chunks`. يضيف تلقائياً `chunk_index` و`total_chunks` و`original_doc_id` للبيانات الوصفية.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text_splitter` | `TextSplitter` *(اختياري)* | مقسّم النصوص — إذا كان `None` يُرجع المستندات كما هي |

**Return:** `List[LoadedDocument]`

**مثال:**

```python
from document_loaders import PDFLoader
from chunks import RecursiveCharacterTextSplitter

loader = PDFLoader("book.pdf", per_page=False)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = loader.load_and_split(splitter)

print(f"عدد القطع: {len(chunks)}")
print(chunks[0].metadata["chunk_index"])   # 0
print(chunks[0].metadata["total_chunks"])  # N
for i in chunks:                           # For Get Conent
    print(i.page_content)
```

---

### `BaseFileLoader` *(Abstract)*

**الوصف:** فئة وسيطة بين `BaseDocumentLoader` وجميع المحمّلات القائمة على ملفات. تتحقق من وجود الملف وامتداده، وتوفر بناء البيانات الوصفية المتعلقة بالملف.

#### `__init__(file_path, encoding)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | المسار الكامل للملف |
| `encoding` | `str` | `"utf-8"` | ترميز الملف |

> ⚠️ يُطلق `FileNotFoundError` إذا لم يوجد الملف، و`ValueError` إذا كان الامتداد غير مدعوم.

---

## ⚙️  الإعدادات المركزية

### `LoaderType` *(Enum)*

**الوصف:** تعداد يحدد جميع أنواع المحمّلات المدعومة. يُستخدم داخلياً بواسطة `AutoLoader` لتعيين نوع الملف للمحمّل الصحيح.

```python
from document_loaders import LoaderType

print(LoaderType.PDF.value)   # "pdf"
print(LoaderType.CSV.value)   # "csv"
print(LoaderType.WEB.value)   # "web"
```

---

### `EXTENSION_MAP`

**الوصف:** قاموس يربط امتداد كل ملف بنوع المحمّل المناسب. يُستخدم بواسطة `AutoLoader` و`DirectoryLoader`.

```python
from document_loaders import EXTENSION_MAP

print(EXTENSION_MAP[".pdf"])    # LoaderType.PDF
print(EXTENSION_MAP[".jsonl"])  # LoaderType.JSONL
print(sorted(EXTENSION_MAP.keys()))
# ['.csv', '.doc', '.docx', '.htm', '.html', '.json', '.jsonl', '.markdown',
#  '.md', '.ndjson', '.pdf', '.tsv', '.txt', '.xls', '.xlsx']
```

---

### إعدادات كل محمّل | Per-Loader Config Dataclasses

#### `TextLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `encoding` | `"utf-8"` | ترميز الملف |
| `autodetect_encoding` | `True` | استخدام chardet لاكتشاف الترميز |
| `errors` | `"replace"` | سلوك الأخطاء: `"strict"` / `"ignore"` / `"replace"` |

#### `PDFLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `per_page` | `True` | مستند واحد لكل صفحة |
| `password` | `None` | كلمة مرور للملفات المشفرة |
| `page_separator` | `"\n\n"` | الفاصل بين الصفحات في الوضع الكامل |
| `start_page` | `0` | رقم الصفحة الأولى (0-based) |
| `end_page` | `None` | رقم الصفحة الأخيرة (None = حتى النهاية) |
| `extract_images` | `False` | استخراج الصور |

#### `DocxLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `include_tables` | `True` | استخراج محتوى الجداول |
| `table_separator` | `"\n"` | الفاصل بين صفوف الجدول |
| `row_separator` | `" \| "` | الفاصل بين خلايا الصف الواحد |
| `include_headers` | `True` | استخراج الترويسات |
| `include_footers` | `True` | استخراج التذييلات |

#### `CSVLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `delimiter` | `","` | محدد الأعمدة |
| `encoding` | `"utf-8"` | ترميز الملف |
| `content_columns` | `None` | أعمدة المحتوى (None = كل الأعمدة) |
| `metadata_columns` | `None` | أعمدة البيانات الوصفية |
| `source_column` | `None` | العمود المستخدم كمصدر |
| `skip_rows` | `0` | عدد الصفوف للتخطي من البداية |
| `max_rows` | `None` | الحد الأقصى للصفوف |
| `row_joiner` | `"\n"` | طريقة دمج قيم الأعمدة |

#### `JSONLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `content_key` | `None` | المفتاح الحاوي للنص الرئيسي |
| `jq_schema` | `None` | تعبير مسار jq للتصفية |
| `metadata_func` | `None` | دالة `(record) → dict` لاستخراج البيانات الوصفية |
| `text_content` | `True` | إذا كان `False` يُحوّل الـ JSON كاملاً إلى نص |

#### `HTMLLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `parser` | `"html.parser"` | محلل HTML: `"html.parser"` / `"lxml"` / `"html5lib"` |
| `tags_to_remove` | `["script","style","nav","footer","header"]` | عناصر HTML للإزالة |
| `tags_to_extract` | `None` | عناصر محددة للاستخراج (None = نص الـ body) |
| `extract_links` | `False` | استخراج الروابط كبيانات وصفية |
| `extract_tables` | `True` | استخراج الجداول كمستندات منفصلة |

#### `WebLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `timeout` | `10` | مهلة الطلب بالثواني |
| `headers` | `{}` | رؤوس HTTP مخصصة |
| `verify_ssl` | `True` | التحقق من شهادة SSL |
| `max_retries` | `3` | عدد محاولات إعادة الاتصال |
| `retry_delay` | `1.0` | ثواني الانتظار بين المحاولات |
| `encoding` | `None` | None = اكتشاف تلقائي |

#### `DirectoryLoaderConfig`

| الحقل | الافتراضي | الوصف |
|-------|-----------|-------|
| `glob_pattern` | `"**/*"` | نمط Glob لتصفية الملفات |
| `exclude_patterns` | `["*.pyc", "__pycache__/*", ...]` | أنماط الاستبعاد |
| `recursive` | `True` | مسح المجلدات الفرعية |
| `silent_errors` | `False` | تخطي الملفات غير المقروءة |
| `show_progress` | `True` | طباعة شريط التقدم |
| `max_concurrency` | `4` | الحد الأقصى للخيوط المتزامنة |
| `use_multithreading` | `True` | تفعيل التحميل المتزامن |

---

## 🤖 المحمّل التلقائي

### `AutoLoader`

**الوصف:** نقطة الدخول الموصى بها للمكتبة. يكتشف نوع المصدر تلقائياً (URL، مجلد، ملف) ويختار المحمّل الصحيح دون أي إعداد مسبق. يدعم جميع أنواع الملفات والـ URLs والمجلدات.

---

#### `AutoLoader.load(source, **kwargs)` *(classmethod)*

**الوصف:** تحميل مستندات من أي مصدر بسطر واحد.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `source` | `str` | مسار ملف، أو URL، أو مسار مجلد |
| `**kwargs` | — | وسيطات إضافية تُمرَّر للمحمّل المحدد |

**Return:** `List[LoadedDocument]`

**مثال:**

```python
from document_loaders import AutoLoader

# ملف PDF
docs = AutoLoader.load("report.pdf")

# ملف CSV مع تخصيص
docs = AutoLoader.load("data.csv", content_columns=["title", "body"])

# صفحة ويب
docs = AutoLoader.load("https://example.com/article")

# مجلد كامل
docs = AutoLoader.load("./my_documents/")

print(f"تم تحميل {len(docs)} مستند")
```

---

#### `AutoLoader.get_loader(source, **kwargs)` *(classmethod)*

**الوصف:** الحصول على كائن المحمّل المناسب **دون** تحميل المستندات — مفيد عند الحاجة لتكوين المحمّل أو الاطلاع على نوعه قبل التحميل.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `source` | `str` | مسار ملف، URL، أو مجلد |

**Return:** `BaseDocumentLoader`

**مثال:**

```python
loader = AutoLoader.get_loader("report.pdf", per_page=True)
print(type(loader).__name__)  # PDFLoader
docs = loader.load()
```

---

#### `AutoLoader.detect_type(source)` *(classmethod)*

**الوصف:** اكتشاف نوع المصدر كنص وصفي دون تحميل أي بيانات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `source` | `str` | المصدر المراد فحصه |

**Return:** `str` — مثل `"pdf"`, `"csv"`, `"web"`, `"directory"`, `"unknown"`

**مثال:**

```python
print(AutoLoader.detect_type("report.pdf"))          # "pdf"
print(AutoLoader.detect_type("https://example.com")) # "web"
print(AutoLoader.detect_type("./docs/"))             # "directory"
print(AutoLoader.detect_type("data.xyz"))            # "unknown"
```

---


#### `get_summary()`

**الوصف:** إرجاع ملخص عن المصادر ونوع كل منها دون تحميل أي بيانات.

**Return:** `dict` — `{"total_sources": N, "by_type": {"report.pdf": "pdf", ...}}`

```python
summary = loader.get_summary()
print(summary["total_sources"])  # 4
print(summary["by_type"])
```

---

## 📝 محمّل النصوص

### `TextLoader`

**الوصف:** يحمّل ملفات النص العادي (`.txt`, `.log`, `.rst`). يدعم اكتشاف الترميز تلقائياً عبر `chardet` والتعامل مع النصوص العربية.

#### `__init__(file_path, config, encoding, autodetect_encoding)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار الملف |
| `config` | `TextLoaderConfig` | `None` | إعدادات مخصصة |
| `encoding` | `str` | `"utf-8"` | الترميز المفضل |
| `autodetect_encoding` | `bool` | `True` | اكتشاف الترميز تلقائياً عند الفشل |

#### `load()`

**الوصف:** قراءة الملف النصي كاملاً وإرجاع مستند واحد. تشمل البيانات الوصفية: `encoding_used`, `char_count`, `line_count`.

**Return:** `List[LoadedDocument]` (دائماً قائمة بعنصر واحد)

**مثال:**

```python
from document_loaders import TextLoader

loader = TextLoader("article.txt", encoding="utf-8")
docs = loader.load()

print(docs[0].page_content[:200])
print(docs[0].metadata["char_count"])   # عدد الأحرف
print(docs[0].metadata["line_count"])   # عدد الأسطر
```

---

### `MarkdownLoader`

**الوصف:** يحمّل ملفات Markdown (`.md`, `.markdown`). يمكنه استخراج العنوان تلقائياً من أول عنوان H1، وإزالة صيغة Markdown للحصول على نص نظيف.

#### `__init__(file_path, encoding, strip_markdown, remove_code_blocks, autodetect_encoding)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار الملف |
| `encoding` | `str` | `"utf-8"` | ترميز الملف |
| `strip_markdown` | `bool` | `False` | إزالة صيغة Markdown (العناوين، التنسيق، الروابط) |
| `remove_code_blocks` | `bool` | `False` | إزالة كتل الكود المحاطة بـ ` ``` ` |
| `autodetect_encoding` | `bool` | `True` | اكتشاف الترميز تلقائياً |

#### `load()`

**الوصف:** تحميل ملف Markdown. تشمل البيانات الوصفية: `title` (من أول H1)، `char_count`، `has_code_blocks`، `heading_count`.

**مثال:**

```python
from document_loaders import MarkdownLoader

# الاحتفاظ بصيغة Markdown كما هي
loader = MarkdownLoader("README.md")
docs = loader.load()
print(docs[0].metadata["title"])        # العنوان من أول # H1

# نص نظيف بدون صيغة Markdown
loader = MarkdownLoader("README.md", strip_markdown=True, remove_code_blocks=True)
docs = loader.load()
print(docs[0].page_content[:300])
```

---

## 📄 محمّل PDF

### `PDFLoader`

**الوصف:** يحمّل مستندات PDF مع دعم ثلاث مكتبات (backend) تلقائياً. يجرب كل مكتبة بالترتيب حتى ينجح التحميل، مما يضمن العمل حتى لو لم تكن جميع المكتبات مثبتة.

**أولوية المكتبات:**
1. **PyMuPDF (`fitz`)** — الأسرع، أفضل دعم للعربية ✅ موصى به
2. **pdfplumber** — الأفضل لاستخراج الجداول
3. **pypdf** — Python خالص، يعمل دائماً كاحتياطي

#### `__init__(file_path, config, per_page, password)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف PDF |
| `config` | `PDFLoaderConfig` | `None` | إعدادات مخصصة |
| `per_page` | `bool` | `True` | إنشاء مستند منفصل لكل صفحة |
| `password` | `str` | `None` | كلمة مرور للملفات المشفرة |

#### `load()`

**الوصف:** تحميل ملف PDF. البيانات الوصفية تشمل: `page_number`, `total_pages`, `pdf_title`, `pdf_author`, `backend` (المكتبة المستخدمة).

**Return:** `List[LoadedDocument]`

**مثال:**

```python
from document_loaders import PDFLoader
from document_loaders import PDFLoaderConfig

# تحميل صفحة بصفحة (الافتراضي)
loader = PDFLoader("book.pdf", per_page=True)
pages = loader.load()
print(f"عدد الصفحات: {len(pages)}")
print(pages[0].metadata["page_number"])  # 1
print(pages[0].metadata["backend"])      # "fitz" أو "pdfplumber" أو "pypdf"

# تحميل صفحات 5-10 فقط كمستند واحد
config = PDFLoaderConfig(start_page=4, end_page=10, per_page=False)
loader = PDFLoader("report.pdf", config=config)
docs = loader.load()
print(f"المستند الكامل: {len(docs[0].page_content)} حرف")

# ملف محمي بكلمة مرور
loader = PDFLoader("secure.pdf", password="mypassword")
docs = loader.load()
```

---

## 📝 محمّل Word

### `DocxLoader`

**الوصف:** يحمّل مستندات Microsoft Word (`.docx`). يستخرج الفقرات، العناوين، الجداول، الترويسات، والتذييلات مع الحفاظ على هيكل المستند. يدعم النصوص العربية وملفات `.doc` القديمة عبر `textract`.

#### `__init__(file_path, config)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف `.docx` أو `.doc` |
| `config` | `DocxLoaderConfig` | `None` | إعدادات مخصصة |

> ⚠️ يتطلب: `pip install python-docx`

#### `load()`

**الوصف:** تحميل مستند Word كاملاً كمستند واحد. تشمل البيانات الوصفية: `title`, `author`, `subject`, `created`, `modified`, `paragraph_count`, `table_count`.

**Return:** `List[LoadedDocument]` (دائماً قائمة بعنصر واحد)

**مثال:**

```python
from document_loaders import DocxLoader
from document_loaders import DocxLoaderConfig

# تحميل عادي
loader = DocxLoader("contract.docx")
docs = loader.load()
print(docs[0].metadata["author"])         # اسم المؤلف
print(docs[0].metadata["paragraph_count"])

# تخصيص — استخراج الجداول فقط بدون ترويسات
config = DocxLoaderConfig(
    include_tables=True,
    include_headers=False,
    include_footers=False,
    row_separator=" | "
)
loader = DocxLoader("report.docx", config=config)
docs = loader.load()
```

---

## 📊 محمّل CSV و Excel

### `CSVLoader`

**الوصف:** يحمّل ملفات CSV/TSV ويحوّل كل صف إلى مستند منفصل. يوفر تحكماً دقيقاً في اختيار أعمدة المحتوى والبيانات الوصفية.

#### `__init__(file_path, config, content_columns, metadata_columns, source_column, encoding, delimiter)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف CSV أو TSV |
| `content_columns` | `List[str]` | `None` | أعمدة تُدمج كمحتوى (None = كل الأعمدة) |
| `metadata_columns` | `List[str]` | `None` | أعمدة تُخزَّن كبيانات وصفية |
| `source_column` | `str` | `None` | عمود يُستخدم كمصدر المستند |
| `encoding` | `str` | `"utf-8"` | ترميز الملف |
| `delimiter` | `str` | `","` | محدد الأعمدة (`,` للـ CSV، `\t` للـ TSV) |

#### `load()` / `lazy_load()`

**الوصف:** `load()` يُرجع كل الصفوف كقائمة. `lazy_load()` يُنتج صفاً صفاً — مثالي للملفات الكبيرة.

**مثال:**

```python
from document_loaders import CSVLoader

# كل الأعمدة كمحتوى
loader = CSVLoader("products.csv")
docs = loader.load()
print(f"عدد الصفوف: {len(docs)}")

# أعمدة محددة للمحتوى وأخرى كبيانات وصفية
loader = CSVLoader(
    "articles.csv",
    content_columns=["title", "body"],
    metadata_columns=["id", "category", "date"],
    source_column="url"
)
docs = loader.load()
print(docs[0].page_content)      # title: ...\nbody: ...
print(docs[0].metadata["id"])    # قيمة عمود id

# تحميل كسول لملفات ضخمة
loader = CSVLoader("big_dataset.csv")
for doc in loader.lazy_load():
    process(doc)
```

---

### `ExcelLoader`

**الوصف:** يحمّل ملفات Excel (`.xlsx`, `.xls`). يدعم تحميل ورقة محددة أو جميع الأوراق. يحوّل كل صف إلى مستند منفصل.

#### `__init__(file_path, sheet_name, load_all_sheets, content_columns, metadata_columns, skip_rows, max_rows)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف Excel |
| `sheet_name` | `str` | `None` | اسم الورقة (None = الورقة الأولى) |
| `load_all_sheets` | `bool` | `False` | تحميل كل الأوراق |
| `content_columns` | `List[str]` | `None` | أعمدة المحتوى |
| `metadata_columns` | `List[str]` | `None` | أعمدة البيانات الوصفية |
| `skip_rows` | `int` | `0` | صفوف للتخطي بعد الرأس |
| `max_rows` | `int` | `None` | الحد الأقصى للصفوف |

> ⚠️ يتطلب: `pip install openpyxl`

**مثال:**

```python
from document_loaders import ExcelLoader

# الورقة الأولى
loader = ExcelLoader("sales.xlsx")
docs = loader.load()

# ورقة محددة مع تحديد الأعمدة
loader = ExcelLoader(
    "report.xlsx",
    sheet_name="Q1_Data",
    content_columns=["Product", "Description"],
    metadata_columns=["SKU", "Price"],
    max_rows=1000
)
docs = loader.load()

# كل الأوراق
loader = ExcelLoader("workbook.xlsx", load_all_sheets=True)
docs = loader.load()
print(docs[0].metadata["sheet_name"])  # اسم الورقة
```

---

## 🔢 محمّل JSON

### `JSONLoader`

**الوصف:** يحمّل ملفات JSON (مصفوفات أو كائنات). يدعم استخراج مفتاح محتوى محدد، ودالة بيانات وصفية مخصصة، وتعبيرات `jq` للتصفية.

#### `__init__(file_path, config, content_key, metadata_func, jq_schema, encoding)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف JSON |
| `content_key` | `str` | `None` | مفتاح JSON الحاوي للنص الرئيسي |
| `metadata_func` | `Callable` | `None` | دالة `(record) → dict` لاستخراج البيانات الوصفية |
| `jq_schema` | `str` | `None` | تعبير jq للوصول لبيانات متداخلة (يتطلب `pip install jq`) |
| `encoding` | `str` | `"utf-8"` | ترميز الملف |

#### `load()`

**الوصف:** تحميل الملف وتحويل كل عنصر في المصفوفة (أو الكائن الكامل) إلى مستند.

**Return:** `List[LoadedDocument]`

**مثال:**

```python
from document_loaders import JSONLoader

# مصفوفة من الكائنات مع مفتاح نص محدد
loader = JSONLoader("articles.json", content_key="body")
docs = loader.load()

# مع استخراج بيانات وصفية مخصصة
loader = JSONLoader(
    "news.json",
    content_key="article_text",
    metadata_func=lambda rec: {
        "title": rec.get("title"),
        "author": rec.get("author"),
        "date": rec.get("published_at")
    }
)
docs = loader.load()
print(docs[0].metadata["title"])

# بيانات متداخلة باستخدام jq
loader = JSONLoader("complex.json", jq_schema=".data.articles[]")
docs = loader.load()
```

---

### `JSONLinesLoader`

**الوصف:** يحمّل ملفات JSONL/NDJSON (كائن JSON واحد في كل سطر). شائعة في مجموعات بيانات Hugging Face وOpenAI fine-tuning. يدعم التحميل الكسول والتخطي الآمن للأسطر التالفة.

#### `__init__(file_path, content_key, metadata_func, encoding, skip_invalid, max_records)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف JSONL |
| `content_key` | `str` | `None` | مفتاح النص الرئيسي |
| `metadata_func` | `Callable` | `None` | دالة استخراج البيانات الوصفية |
| `encoding` | `str` | `"utf-8"` | ترميز الملف |
| `skip_invalid` | `bool` | `True` | تخطي الأسطر التالفة |
| `max_records` | `int` | `None` | الحد الأقصى للسجلات |

**مثال:**

```python
from document_loaders import JSONLinesLoader

# مجموعة بيانات تدريب
loader = JSONLinesLoader(
    "dataset.jsonl",
    content_key="text",
    metadata_func=lambda r: {"label": r.get("label"), "id": r.get("id")},
    max_records=10000
)
docs = loader.load()

# تحميل كسول لملفات ضخمة
loader = JSONLinesLoader("huge.jsonl", content_key="content")
for doc in loader.lazy_load():
    process(doc)
```

---

## 🌐 محمّل HTML

### `HTMLLoader`

**الوصف:** يحمّل ملفات HTML ويستخرج المحتوى النصي النظيف باستخدام `BeautifulSoup`. يُزيل تلقائياً العناصر غير المرغوبة (scripts، styles، nav...)، ويستخرج البيانات الوصفية من وسوم `<meta>`.

> ⚠️ يتطلب: `pip install beautifulsoup4`

#### `__init__(file_path, config, encoding)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `file_path` | `str` | — | مسار ملف HTML |
| `config` | `HTMLLoaderConfig` | `None` | إعدادات مخصصة |
| `encoding` | `str` | `"utf-8"` | ترميز الملف |

#### `load()`

**الوصف:** تحليل الملف واستخراج النص. البيانات الوصفية تشمل: `title`, `description`, `language`, `og_title`, `og_description`, `char_count`. إذا كان `extract_tables=True` يُرجع مستندات إضافية للجداول.

**مثال:**

```python
from document_loaders import HTMLLoader
from document_loaders import HTMLLoaderConfig

# تحميل عادي
loader = HTMLLoader("page.html")
docs = loader.load()
print(docs[0].metadata["title"])
print(docs[0].metadata["language"])  # "ar" أو "en" إلخ

# استخراج عناصر محددة فقط
config = HTMLLoaderConfig(
    tags_to_extract=["article", "main", "section"],
    extract_links=True,
    extract_tables=False
)
loader = HTMLLoader("news.html", config=config)
docs = loader.load()
print(docs[0].metadata["links"])  # قائمة الروابط
```

---

### `HTMLStringLoader`

**الوصف:** يحمّل HTML من سلسلة نصية مباشرة (وليس من ملف). مفيد لمعالجة HTML مُستقبَل من API أو قاعدة بيانات.

#### `__init__(html_content, source, config)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `html_content` | `str` | — | سلسلة HTML الخام |
| `source` | `str` | `"html_string"` | معرّف المصدر (يظهر في البيانات الوصفية) |
| `config` | `HTMLLoaderConfig` | `None` | إعدادات مخصصة |

**مثال:**

```python
from document_loaders import HTMLStringLoader

html = """
<html lang="ar">
  <head><title>مقال تجريبي</title></head>
  <body>
    <h1>عنوان المقال</h1>
    <p>محتوى المقال هنا.</p>
  </body>
</html>
"""
loader = HTMLStringLoader(html, source="https://example.com/article")
docs = loader.load()
print(docs[0].metadata["title"])   # "مقال تجريبي"
print(docs[0].page_content)
```

---

## 🌍  محمّل الويب

### `WebLoader`

**الوصف:** يجلب محتوى صفحات الويب عبر HTTP ويحلّله كـ HTML. يدعم إعادة المحاولة التلقائية بانتظار تدريجي (exponential backoff)، ورؤوس HTTP مخصصة، واكتشاف الترميز.

> ⚠️ يتطلب: `pip install requests beautifulsoup4`

#### `__init__(url, config, headers, timeout)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `url` | `str` | — | عنوان URL للصفحة |
| `config` | `WebLoaderConfig` | `None` | إعدادات مخصصة |
| `headers` | `Dict[str, str]` | `None` | رؤوس HTTP مخصصة |
| `timeout` | `int` | `10` | مهلة الطلب بالثواني |

#### `load()`

**الوصف:** جلب الصفحة وتحليلها. البيانات الوصفية تشمل: `url`, `source`, `title`, `description`, `language`, وسوم OG.

**مثال:**

```python
from document_loaders import WebLoader
from document_loaders import WebLoaderConfig

# تحميل عادي
loader = WebLoader("https://en.wikipedia.org/wiki/Python")
docs = loader.load()
print(docs[0].metadata["title"])

# مع إعدادات متقدمة
config = WebLoaderConfig(
    timeout=30,
    max_retries=5,
    headers={"User-Agent": "MyBot/1.0", "Accept-Language": "ar"},
    verify_ssl=True
)
loader = WebLoader("https://example.com", config=config)
docs = loader.load()
```

---

### `MultiURLLoader`

**الوصف:** يحمّل محتوى من قائمة URLs متعددة بشكل متزامن باستخدام خيوط متعددة (ThreadPoolExecutor). يوفر تحكماً في معدل الطلبات وإدارة الأخطاء.

#### `__init__(urls, config, max_workers, delay_between_requests, continue_on_error)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `urls` | `List[str]` | — | قائمة عناوين URL |
| `config` | `WebLoaderConfig` | `None` | إعدادات مشتركة |
| `max_workers` | `int` | `4` | الحد الأقصى للخيوط المتزامنة |
| `delay_between_requests` | `float` | `0.5` | ثواني الانتظار بين الطلبات (للتأدب مع الخوادم) |
| `continue_on_error` | `bool` | `True` | تخطي URLs الفاشلة |

**مثال:**

```python
from document_loaders import MultiURLLoader

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3",
]

loader = MultiURLLoader(
    urls,
    max_workers=3,
    delay_between_requests=1.0,
    continue_on_error=True
)
docs = loader.load()
print(f"تم تحميل {len(docs)} مستند من {len(urls)} صفحة")
```

---

## 📁 محمّل المجلدات

### `DirectoryLoader`

**الوصف:** يمسح مجلداً (بشكل تكراري أو غير تكراري) ويحمّل جميع الملفات ذات الامتدادات المدعومة. يستخدم التحميل المتزامن متعدد الخيوط تلقائياً لتسريع العملية، ويعرض شريط تقدم.

#### `__init__(path, config, glob_pattern, recursive, silent_errors, show_progress)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `path` | `str` | — | مسار المجلد |
| `config` | `DirectoryLoaderConfig` | `None` | إعدادات مخصصة |
| `glob_pattern` | `str` | `"**/*"` | نمط Glob لتصفية الملفات |
| `recursive` | `bool` | `True` | مسح المجلدات الفرعية |
| `silent_errors` | `bool` | `False` | تخطي الملفات غير المقروءة |
| `show_progress` | `bool` | `True` | طباعة شريط التقدم |

#### `load()` / `lazy_load()`

**الوصف:** `load()` يُرجع كل المستندات كقائمة. `lazy_load()` يُنتجها بشكل كسول للاستخدام الفعّال للذاكرة.

**مثال:**

```python
from document_loaders import DirectoryLoader
from document_loaders import DirectoryLoaderConfig

# تحميل كل الملفات المدعومة
loader = DirectoryLoader("./documents/")
docs = loader.load()
print(f"تم تحميل {len(docs)} مستند")

# تحميل PDFs فقط
loader = DirectoryLoader("./reports/", glob_pattern="**/*.pdf")
docs = loader.load()

# إعدادات متقدمة
config = DirectoryLoaderConfig(
    glob_pattern="**/*.{txt,md,pdf}",
    exclude_patterns=["draft/*", "*.tmp"],
    recursive=True,
    silent_errors=True,   # تخطي الملفات التالفة
    show_progress=True,
    max_concurrency=8
)
loader = DirectoryLoader("./data/", config=config)
docs = loader.load()
```

#### `get_stats()`

**الوصف:** إرجاع إحصائيات عن الملفات في المجلد دون تحميلها — مفيد للاستطلاع الأولي.

**Return:** `dict` يحتوي على:
- `total_files`: العدد الإجمالي للملفات
- `by_type`: عدد الملفات وحجمها لكل نوع
- `total_size_bytes` / `total_size_mb`: الحجم الكلي

**مثال:**

```python
loader = DirectoryLoader("./documents/")
stats = loader.get_stats()

print(f"إجمالي الملفات: {stats['total_files']}")
print(f"الحجم الكلي: {stats['total_size_mb']} MB")
for file_type, info in stats["by_type"].items():
    print(f"  {file_type}: {info['count']} ملف")
```

---

## 🚀 أمثلة متكاملة

### مثال 1: خط أنابيب متكامل — تحميل وتقسيم

```python
from document_loaders import AutoLoader
from chunks import RecursiveCharacterTextSplitter

# تحميل وتقسيم في خطوتين
loader = AutoLoader.get_loader("research_paper.pdf", per_page=False)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = loader.load_and_split(splitter)

for chunk in chunks:
    print(f"[صفحة {chunk.metadata.get('page_number', '?')}] "
          f"القطعة {chunk.metadata['chunk_index']}: "
          f"{len(chunk.page_content)} حرف")
```

---


---

### مثال 2: تحميل مجلد مع إحصاءات

```python
from document_loaders import DirectoryLoader

loader = DirectoryLoader("./knowledge_base/", show_progress=True)

# إحصاءات أولاً
stats = loader.get_stats()
print(f"سيتم تحميل {stats['total_files']} ملف ({stats['total_size_mb']} MB)")

# التحميل
docs = loader.load()

# تصفية حسب نوع الملف
pdf_docs = [d for d in docs if d.metadata.get("file_type") == ".pdf"]
print(f"مستندات PDF: {len(pdf_docs)}")
```

---

### مثال 3: تحميل ويب متعدد مع إعادة المحاولة

```python
from document_loaders import MultiURLLoader
from document_loaders import WebLoaderConfig

urls = [f"https://news.example.com/article/{i}" for i in range(1, 21)]

config = WebLoaderConfig(
    timeout=15,
    max_retries=3,
    retry_delay=2.0
)

loader = MultiURLLoader(
    urls,
    config=config,
    max_workers=5,
    delay_between_requests=0.5
)
docs = loader.load()
print(f"تم تحميل {len(docs)} مقال")
```
---

```python
import tempfile
import json
from document_loaders import (
        TextLoader, MarkdownLoader, JSONLoader,
        CSVLoader, HTMLStringLoader, AutoLoader,
        TextLoaderConfig, CSVLoaderConfig,
    )
from pathlib import Path
from llm import MistralInterface
from embeddings import MistralEmbedder
from vector_database import FAISSVectorDatabase
from chunks import MultilanguageTextChunker
from context import ContextManager
from rag.core import RAGSystem
from chunks import Document 
embedder=MistralEmbedder(api_key=api)
base_rag=RAGSystem(
        vector_db=FAISSVectorDatabase(embedder=embedder),
        llm=MistralInterface(api_key=api),
        chunker=MultilanguageTextChunker(),
        context_manager=ContextManager(),)
    # ── إنشاء ملفات مؤقتة تمثل قاعدة معرفة ──────────────────── #
tmp = Path(tempfile.mkdtemp())

(tmp / "ai_intro.txt").write_text(
        "الذكاء الاصطناعي هو محاكاة الذكاء البشري في الحواسيب.\n"
        "يشمل تعلم الآلة والشبكات العصبية ومعالجة اللغة الطبيعية.\n"
        "يُطبَّق في الطب والتعليم والصناعة والمركبات ذاتية القيادة.",
        encoding="utf-8"
    )

(tmp / "rag_guide.md").write_text(
    "# دليل RAG\n\n"
    "## ما هو RAG؟\nRAG هو Retrieval-Augmented Generation.\n\n"
    "## كيف يعمل؟\n"
    "1. يستقبل الاستعلام\n2. يبحث في قاعدة المعرفة\n3. يُنتج إجابة دقيقة\n\n"
    "## مزاياه\n- يُقلّل الهلوسة\n- يُحدّث المعلومات باستمرار\n- يشرح مصادره",
    encoding="utf-8"
)

(tmp / "models.json").write_text(json.dumps([
    {"id": "gpt4",   "name": "GPT-4",   "company": "OpenAI",    "desc": "نموذج متقدم يدعم النصوص والصور."},
    {"id": "claude", "name": "Claude",  "company": "Anthropic", "desc": "نموذج مُحاذَى للسلامة من Anthropic."},
    {"id": "gemini", "name": "Gemini",  "company": "Google",    "desc": "نموذج متعدد الوسائط من Google DeepMind."},
], ensure_ascii=False), encoding="utf-8")
(tmp / "qa_pairs.csv").write_text(
    "question,answer\n"
    "ما هو GPT؟,GPT هو Generative Pre-trained Transformer من OpenAI.\n"
    "ما هو BERT؟,BERT هو Bidirectional Encoder Representations من Google.\n"
    "ما هو T5؟,T5 هو Text-To-Text Transfer Transformer من Google.\n",
    encoding="utf-8"
)
# ── تحميل المستندات من كل مصدر ───────────────────────────── #
print("\n  📂 تحميل المستندات من مصادر متعددة:\n")
all_docs = {}
# TextLoader
txt_docs = TextLoader(config=TextLoaderConfig(encoding="utf-8"),file_path=str(tmp / "ai_intro.txt")).load()
for i, doc in enumerate(txt_docs):
    all_docs[f"txt_doc_{i}"] = doc.page_content
print(f"  ✅ TextLoader     : {len(txt_docs)} مستند(ات)")
# MarkdownLoader
md_docs = MarkdownLoader(file_path=str(tmp / "rag_guide.md")).load()
for i, doc in enumerate(md_docs):
    all_docs[f"md_doc_{i}"] = doc.page_content
print(f"  ✅ MarkdownLoader : {len(md_docs)} مستند(ات)")

# CSVLoader
csv_docs = CSVLoader(config=CSVLoaderConfig(
    content_columns=["answer"], metadata_columns=["question"]
),file_path=str(tmp / "qa_pairs.csv")).load()
for doc in csv_docs:
    q = doc.metadata.get("question", "q")
    all_docs[f"qa_{q[:10]}"] = f"السؤال: {q} | الإجابة: {doc.page_content}"
print(f"  ✅ CSVLoader      : {len(csv_docs)} مستند(ات)")
# HTMLStringLoader

html_content="""
    <html><body><h1>Transformers</h1>
    <p>معمارية Transformer هي أساس نماذج NLP الحديثة. 
    تعتمد على آلية الانتباه (Attention) بدلاً من RNN.</p></body></html>

"""
html_loader = HTMLStringLoader(html_content=html_content)
html_docs = html_loader.load()
for i, doc in enumerate(html_docs):
    all_docs[f"html_doc_{i}"] = doc.page_content
print(f"  ✅ HTMLLoader     : {len(html_docs)} مستند(ات)")
print(f"\n  📦 إجمالي المستندات المحملة: {len(all_docs)}")
# ── بناء RAG وإدخال المستندات ─────────────────────────────── #
rag = base_rag

print("\n  📥 إدخال المستندات في الـ RAG:")
chunk_counts = rag.add_documents(all_docs)
total_chunks = sum(chunk_counts.values())
print(f"  ✅ {len(all_docs)} مستند → {total_chunks} chunk مُفهرَس\n")
# ── استعلامات على المستندات المحملة ──────────────────────── #
test_queries = [
    "ما هو GPT-4 وما شركته؟",
    "كيف يعمل RAG وما مزاياه؟",
    "ما هي معمارية Transformer؟",
]
print("  🔍 استعلامات على المعرفة المحملة:\n")
for q in test_queries:
    answer   = rag.generate(q)
    retrieved = rag.retrieve(q)
    sources  = list({c.doc_id for c, _ in retrieved})
    print(f"  Q: {q}")
    print(f"  A: {answer[:80]}...")
    print(f"  📌 Sources: {sources}\n")

```
---

## ⚠️ متطلبات التثبيت

```bash
# متطلبات أساسية (إلزامية)
pip install requests beautifulsoup4

# محمّلات اختيارية — ثبّت ما تحتاجه فقط
pip install PyMuPDF          # PDF (الأسرع والأفضل)
pip install pdfplumber        # PDF (أفضل لاستخراج الجداول)
pip install pypdf             # PDF (احتياطي خالص Python)
pip install python-docx       # ملفات Word .docx
pip install openpyxl          # ملفات Excel .xlsx
pip install chardet           # اكتشاف الترميز تلقائياً
pip install jq                # تعبيرات jq لملفات JSON
pip install textract          # ملفات .doc القديمة
```

---

## 🔑 ملخص مقارنة المحمّلات

| المحمّل | الامتدادات | الاستخدام الأمثل |
|---------|-----------|-----------------|
| `AutoLoader` | الكل | نقطة دخول موحدة لأي مصدر |
| `MultiSourceLoader` | الكل | مصادر متعددة بأنواع مختلطة |
| `TextLoader` | `.txt` `.log` `.rst` | ملفات نصية عادية |
| `MarkdownLoader` | `.md` `.markdown` | ملفات Markdown مع خيار تنظيف الصيغة |
| `PDFLoader` | `.pdf` | كتب ومقالات وتقارير PDF |
| `DocxLoader` | `.docx` `.doc` | مستندات Word مع جداول وترويسات |
| `CSVLoader` | `.csv` `.tsv` | جداول بيانات، مجموعات بيانات صفوف |
| `ExcelLoader` | `.xlsx` `.xls` | جداول بيانات Excel متعددة الأوراق |
| `JSONLoader` | `.json` | بيانات JSON منظّمة |
| `JSONLinesLoader` | `.jsonl` `.ndjson` | مجموعات بيانات تدريب وملفات ضخمة |
| `HTMLLoader` | `.html` `.htm` | صفحات HTML محلية |
| `HTMLStringLoader` | — (سلسلة نصية) | HTML من APIs أو قواعد البيانات |
| `WebLoader` | URLs | صفحات ويب بالجلب المباشر |
| `MultiURLLoader` | URLs متعددة | زحف مواقع، تحميل متزامن |
| `DirectoryLoader` | مجلد | استيراد كامل لمستودع مستندات |
