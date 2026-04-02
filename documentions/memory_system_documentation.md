## 🌐 نظرة عامة

نظام **Memory Management** هو طبقة إدارة ذاكرة متكاملة لتطبيقات الذكاء الاصطناعي. يحل مشكلة جوهرية: **نماذج اللغة لا تتذكر المحادثات السابقة** بطبيعتها، فيأتي هذا النظام ليضيف طبقة ذاكرة تُزوِّد النموذج بالسياق المناسب عند كل استدعاء.

يدعم النظام **أربعة أنواع متخصصة** من الذاكرة تحت واجهة برمجية موحَّدة، مما يُتيح التبديل بينها بتغيير سطر واحد فقط.



## 🏗 البنية المعمارية

```
┌──────────────────────────────────────────────────────────┐
│                     Memory System                        │
│                                                          │
│  ┌─────────────────────────────────────────────────┐     │
│  │           BaseMemory  (Abstract Class)          │     │
│  │  save_context() | load_memory_variables()       │     │
│  │  clear()        | get_memory_stats()            │     │
│  │  asave_context()| aload_memory_variables()      │     │
│  └───────────────────────┬─────────────────────────┘     │
│                          │  ترث منه / inherited by       │
│         ┌────────────────┼─────────────────────┐         │
│         │                │                     │         │
│  ┌──────┴──────┐  ┌──────┴───────┐  ┌──────────┴──────┐  │
│  │   Buffer    │◄─│    Window    │  │    Summary      │  │
│  │   Memory    │  │    Memory    │  │    Memory       │  │
│  │  (كل شيء)  │  │   (آخر K)   │  │  (تلخيص تلقائي)│  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐     │
│  │          Entity Memory  (كيانات)                │     │
│  └─────────────────────────────────────────────────┘     │
│                                                          │
│  ┌─────────────────────────────────────────────────┐     │
│  │         نماذج البيانات / Data Models            │     │
│  │  MemoryEntry | MemoryType | ChatMessage | Entity │     │
│  └─────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

---

## ⚖️ مقارنة أنواع الذاكرة

| النوع | ما يحفظه | الحد الأقصى | يحتاج LLM؟ | الأنسب لـ |
|------|---------|-----------|-----------|----------|
| `BufferMemory` | كل المحادثة من أولها | غير محدود | ❌ لا | محادثات قصيرة، سياق كامل |
| `WindowMemory` | آخر K رسالة فقط | K رسالة | ❌ لا | محادثات طويلة مستمرة |
| `SummaryMemory` | ملخص تراكمي + رسائل حديثة | حد التوكنز | ✅ نعم | محادثات طويلة جداً |
| `EntityMemory` | معلومات الكيانات المذكورة | غير محدود | ✅ نعم | محادثات متعددة الأشخاص والأماكن |

---


---

## 1. `MemoryConfig` — إعدادات النظام

>
> **الوصف:** `dataclass` مركزي يضم جميع إعدادات نظام الذاكرة القابلة للتخصيص. يُنشئ تلقائياً كائن `memory_config` (Singleton) يُستخدم كقيم افتراضية في جميع أجزاء النظام، ويمكنك استيراده والاستخدام مباشرة دون إنشاء كائن جديد.

### الخصائص | Attributes

#### حدود الذاكرة | Memory Limits

| الخاصية | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `max_short_term` | `int` | `1000` | الحد الأقصى لذاكرة قصيرة المدى |
| `max_long_term` | `int` | `1000` | الحد الأقصى لذاكرة طويلة المدى |
| `max_working` | `int` | `1000` | الحد الأقصى لذاكرة العمل النشطة |
| `max_episodic` | `int` | `1000` | الحد الأقصى للذاكرة الزمنية |
| `max_semantic` | `int` | `1000` | الحد الأقصى للذاكرة الدلالية |
| `max_procedral` | `int` | `1000` | الحد الأقصى للذاكرة الإجرائية |

#### إعدادات الاسترجاع | Retrieval Settings

| الخاصية | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `importance_threshold` | `float` | `0.7` | عتبة الأهمية للترقية لذاكرة طويلة المدى (0–1) |
| `similarity_threshold` | `float` | `0.85` | عتبة التشابه لدمج الذكريات المتشابهة (0–1) |
| `retrieval_limit` | `int` | `10` | الحد الافتراضي لعدد الذكريات المُسترجعة |

#### إعدادات التضمين | Embedding Settings

| الخاصية | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `embedding_model` | `str` | `"all-MiniLM-L6-v2"` | نموذج التضمين المستخدم |
| `embedding_batch_size` | `int` | `32` | حجم الدفعة لتوليد التضمينات |
| `embedding_cache_size` | `int` | `1000` | حجم كاش التضمينات |

#### إعدادات المحادثة | Conversation Settings

| الخاصية | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `return_messages` | `bool` | `False` | `True` = كائنات قاموس، `False` = نص مدمج |
| `input_key` | `str` | `"input"` | المفتاح الافتراضي لرسالة المستخدم |
| `output_key` | `str` | `"output"` | المفتاح الافتراضي لرد النظام |
| `memory_key` | `str` | `"history"` | مفتاح الذاكرة في القاموس المُرجَع |
| `max_token_limit` | `int` | `2000` | الحد الأقصى للتوكنز قبل تفعيل التلخيص |
| `window_size` | `int` | `5` | حجم نافذة `WindowMemory` الافتراضي |
| `max_tokens` | `int` | `2000` | الحد الأقصى لتوكنز إخراج نموذج اللغة |

#### إعدادات التلاشي والحفظ | Decay & Persistence Settings

| الخاصية | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `enable_decay` | `bool` | `True` | تفعيل تلاشي الذكريات بمرور الوقت |
| `decay_rate` | `float` | `0.1` | معدل التلاشي اليومي (10%) |
| `min_importance` | `float` | `0.1` | الحد الأدنى للأهمية قبل حذف الذكرى |
| `enable_persistence` | `bool` | `True` | تفعيل الحفظ التلقائي على القرص |
| `persistence_path` | `str` | `"./memory_storage"` | مسار مجلد حفظ الذكريات |
| `auto_save_interval` | `int` | `300` | الفترة بين الحفظ التلقائي بالثواني (5 دقائق) |
| `normalize_text` | `bool` | `False` | تحويل النص لأحرف صغيرة قبل الحفظ |
| `preserve_case` | `bool` | `True` | الحفاظ على حالة الأحرف الأصلية |
| `remove_duplicates` | `bool` | `True` | إزالة الذكريات المكررة تلقائياً |
| `enable_consolidation` | `bool` | `True` | تفعيل دمج الذكريات المتشابهة |

---

### `from_env()` — Class Method

**الوصف:** يُنشئ كائن `MemoryConfig` من متغيرات البيئة بدلاً من القيم الثابتة في الكود. مفيد في بيئات Docker أو الإنتاج حيث تتغير الإعدادات بين البيئات المختلفة.

**لا يأخذ معاملات** — يقرأ مباشرة من `os.environ`.

**متغيرات البيئة المدعومة:**

| المتغير | القيمة الافتراضية | يقابل |
|---------|-----------------|------|
| `MEMORY_MAX_SHORT_TERM` | `100` | `max_short_term` |
| `MEMORY_MAX_LONG_TERM` | `1000` | `max_long_term` |
| `MEMORY_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | `embedding_model` |
| `MEMORY_PERSISTENCE_PATH` | `./memory_storage` | `persistence_path` |
| `MEMORY_ENABLE_PERSISTENCE` | `true` | `enable_persistence` |

**Return:** `MemoryConfig`

```python
import os
from memory import MemoryConfig

os.environ['MEMORY_MAX_SHORT_TERM'] = '500'
os.environ['MEMORY_PERSISTENCE_PATH'] = '/var/app/memory'
os.environ['MEMORY_ENABLE_PERSISTENCE'] = 'true'

config = MemoryConfig.from_env()
print(config.max_short_term)    # 500
print(config.persistence_path)  # /var/app/memory
print(config.enable_persistence)# True
```

---

### `to_dict()`

**الوصف:** يُحوِّل الإعدادات الرئيسية إلى `dict`. مفيد لتسجيل الإعدادات المستخدمة أو حفظها.

**لا يأخذ معاملات.**

**Return:** `dict`

```python
from memory import MemoryConfig

config = MemoryConfig(max_short_term=200, enable_decay=False)
d = config.to_dict()

print(d['max_short_term'])   # 200
print(d['enable_decay'])     # False
print(d['embedding_model'])  # all-MiniLM-L6-v2
```

---

### مثال — إنشاء إعدادات مخصصة

```python
from memory import MemoryConfig

# استخدام الـ Singleton الجاهز (مستورد مباشرة)
print(MemoryConfig.max_token_limit)  # 2000
print(MemoryConfig.window_size)      # 5

# إنشاء إعدادات مخصصة
custom_config = MemoryConfig(
    max_token_limit=4000,
    window_size=10,
    enable_persistence=True,
    persistence_path="./my_app/memory",
    decay_rate=0.05           # تلاشٍ بطيء (5% يومياً)
)
```

---

## 2. `MemoryType` — أنواع الذاكرة

>
> **الوصف:** `Enum` يُعرِّف الأنواع الستة للذاكرة مستوحاةً من علم النفس المعرفي. يُستخدم لتصنيف كل `MemoryEntry` عند إنشائه وتحديد سعته الافتراضية.

### القيم | Values

| القيمة | الوصف |
|--------|-------|
| `SHORT_TERM` | ذاكرة مؤقتة ومحدودة السعة |
| `LONG_TERM` | ذاكرة دائمة وواسعة السعة |
| `WORKING` | ذاكرة المعالجة النشطة الحالية |
| `EPISODIC` | ذاكرة الأحداث والتجارب الشخصية |
| `SEMANTIC` | ذاكرة الحقائق والمعرفة العامة |
| `PROCEDURAL` | ذاكرة المهارات والإجراءات |

---

### `from_string(type_str)` — Class Method

**الوصف:** يُحوِّل نصاً إلى `MemoryType`. مفيد عند تحميل البيانات من ملفات JSON أو قواعد البيانات حيث تُخزَّن الأنواع كنصوص. يقبل الاسم الكامل أو اختصارات متعددة، ويُعيد `SHORT_TERM` افتراضياً إذا لم يُطابق أي قيمة.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `type_str` | `str` | نص يمثل نوع الذاكرة، غير حساس لحالة الأحرف |

**الاختصارات المقبولة:**

| الاختصارات | النتيجة |
|-----------|--------|
| `'short_term'`, `'short'`, `'st'` | `SHORT_TERM` |
| `'long_term'`, `'long'`, `'lt'` | `LONG_TERM` |
| `'working'`, `'work'`, `'wm'` | `WORKING` |
| `'episodic'`, `'episode'`, `'ep'` | `EPISODIC` |
| `'semantic'`, `'sem'` | `SEMANTIC` |
| `'procedural'`, `'proc'` | `PROCEDURAL` |

**Return:** `MemoryType`

```python
from memory import MemoryType

t1 = MemoryType.from_string('short_term')  # MemoryType.SHORT_TERM
t2 = MemoryType.from_string('st')          # MemoryType.SHORT_TERM (اختصار)
t3 = MemoryType.from_string('episodic')    # MemoryType.EPISODIC
t4 = MemoryType.from_string('EP')          # MemoryType.EPISODIC (غير حساس لحالة الأحرف)
t5 = MemoryType.from_string('xyz')         # MemoryType.SHORT_TERM (افتراضي)

print(t1.value)   # "short_term"
print(t3.name)    # "EPISODIC"
print(str(t1))    # "short_term"
print(repr(t3))   # "MemoryType.EPISODIC"
```

---

### `description` — Property

**الوصف:** يُعيد وصفاً نصياً بالإنجليزية لنوع الذاكرة.

**لا يأخذ معاملات.** | **Return:** `str`

```python
print(MemoryType.SHORT_TERM.description)
# "Temporary storage with limited capacity"

print(MemoryType.EPISODIC.description)
# "Personal experiences and events"

print(MemoryType.PROCEDURAL.description)
# "Skills and procedures"
```

---

### `default_capacity` — Property

**الوصف:** يُعيد الحد الأقصى الافتراضي لهذا النوع مأخوذاً مباشرة من `memory_config`.

**لا يأخذ معاملات.** | **Return:** `int`

```python
print(MemoryType.SHORT_TERM.default_capacity)  # 1000
print(MemoryType.LONG_TERM.default_capacity)   # 1000
```

---

## 3. `MemoryPriority` — أولويات الذاكرة

>
> **الوصف:** `Enum` يُعرِّف خمسة مستويات أولوية للذكريات بناءً على درجة أهميتها. يُحسب تلقائياً من `effective_importance` عبر خاصية `MemoryEntry.priority`.

### القيم | Values

| القيمة | الرقم | عتبة الأهمية |
|--------|------|-------------|
| `CRITICAL` | `1.0` | ≥ 0.9 |
| `HIGH` | `0.8` | ≥ 0.7 |
| `MEDIUM` | `0.5` | ≥ 0.5 |
| `LOW` | `0.3` | ≥ 0.3 |
| `MINIMAL` | `0.1` | < 0.3 |

---

### `from_importance(importance)` — Class Method

**الوصف:** يُحوِّل درجة أهمية رقمية (0.0 – 1.0) إلى مستوى أولوية مقابل. يُستخدم داخلياً في `MemoryEntry.priority`.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `importance` | `float` | درجة الأهمية بين `0.0` و `1.0` |

**Return:** `MemoryPriority`

```python
from memory import MemoryPriority

p1 = MemoryPriority.from_importance(0.95)  # CRITICAL
p2 = MemoryPriority.from_importance(0.75)  # HIGH
p3 = MemoryPriority.from_importance(0.55)  # MEDIUM
p4 = MemoryPriority.from_importance(0.35)  # LOW
p5 = MemoryPriority.from_importance(0.15)  # MINIMAL

print(p1.name)   # "CRITICAL"
print(p1.value)  # 1.0
print(p3.name)   # "MEDIUM"
```

---

## 4. `MemoryEntry` — وحدة الذاكرة

>
> **الوصف:** `dataclass` يُمثِّل ذكرى واحدة في النظام. يحتوي على المحتوى مع كل البيانات الوصفية: درجة الأهمية، عدد الوصولات، التلاشي الزمني، والوسوم. يولِّد معرِّفاً فريداً تلقائياً عبر MD5 عند الإنشاء.

### الخصائص | Attributes

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `content` | `Any` | محتوى الذاكرة (نص، قاموس، أي نوع بيانات) |
| `timestamp` | `float` | وقت الإنشاء (Unix timestamp) |
| `memory_type` | `MemoryType` | نوع الذاكرة |
| `importance` | `float` | درجة الأهمية الحالية (0–1) — افتراضي: `0.5` |
| `access_count` | `int` | عدد مرات الوصول — افتراضي: `0` |
| `tags` | `List[str]` | وسوم للتصنيف والبحث |
| `metadata` | `Dict[str, Any]` | بيانات وصفية إضافية (يُحفظ فيها `id` تلقائياً) |
| `embedding` | `List[float] \| None` | متجه التضمين — افتراضي: `None` |
| `last_access` | `float` | وقت آخر وصول — يُضبط تلقائياً |
| `decay_factor` | `float` | معامل التلاشي الحالي (0.1 – 1.0) — افتراضي: `1.0` |
| `original_importance` | `float \| None` | الأهمية الأصلية قبل أي تلاشٍ |

### الخصائص المحسوبة | Computed Properties

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `id` | `str` | معرِّف فريد (16 حرف من MD5) |
| `age_seconds` | `float` | عمر الذاكرة بالثواني |
| `age_days` | `float` | عمر الذاكرة بالأيام |
| `time_since_access_seconds` | `float` | الوقت بالثواني منذ آخر وصول |
| `effective_importance` | `float` | الأهمية الفعلية = `importance × decay_factor` |
| `priority` | `MemoryPriority` | مستوى الأولوية المحسوب تلقائياً |
| `has_embedding` | `bool` | هل تملك متجه تضمين غير فارغ؟ |

---

### `access()`

**الوصف:** يُسجِّل وصولاً للذاكرة. يزيد `access_count` بمقدار 1، يُحدِّث `last_access`، ويرفع `importance` قليلاً بصيغة تناقصية (كلما اقتربت الأهمية من 1.0 قل الارتفاع).

**لا يأخذ معاملات.** | **Return:** `None`

```python
from memory import MemoryEntry
from memory import MemoryType
import time

entry = MemoryEntry(
    content="اسم المستخدم هو أحمد",
    timestamp=time.time(),
    memory_type=MemoryType.SHORT_TERM,
    importance=0.6
)

print(entry.access_count)         # 0
print(f"{entry.importance:.2f}")  # 0.60

entry.access()
print(entry.access_count)         # 1
print(f"{entry.importance:.2f}")  # 0.62 (ارتفع بـ 0.05 × (1 - 0.6))
```

---

### `apply_decay(decay_rate=0.1)`

**الوصف:** يُطبِّق التلاشي الزمني على الأهمية بناءً على الوقت المنقضي منذ آخر وصول. كلما طال الوقت دون وصول انخفضت الأهمية. لن تنخفض أبداً عن `0.1`.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `decay_rate` | `float` | `0.1` | معدل التلاشي اليومي (0.1 = 10% في اليوم) |

**Return:** `None`

```python
import time

# ذاكرة لم يُصَل إليها منذ يومين
entry = MemoryEntry(
    content="معلومة قديمة",
    timestamp=time.time() - (2 * 86400),
    memory_type=MemoryType.SHORT_TERM,
    importance=0.8,
    last_access=time.time() - (2 * 86400)
)

print(f"قبل:  importance={entry.importance:.2f}")  # 0.80

entry.apply_decay(decay_rate=0.1)

print(f"بعد:  importance={entry.importance:.2f}")     # ~0.64 (80% × 80%)
print(f"      decay_factor={entry.decay_factor:.2f}") # ~0.80
```

---

### `add_tag(tag)` | `add_tags(tags)` | `has_tag(tag)`

**الوصف:** إدارة الوسوم (Tags) للتصنيف والبحث اللاحق. تُحوَّل الوسوم تلقائياً لأحرف صغيرة ولا تُضاف مكرراً.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `tag` | `str` | الوسم المراد إضافته أو البحث عنه |
| `tags` | `List[str]` | قائمة وسوم مراد إضافتها دفعةً واحدة |

**Return:** `None` (لـ add) / `bool` (لـ has)

```python
entry = MemoryEntry(
    content="باريس عاصمة فرنسا",
    timestamp=time.time(),
    memory_type=MemoryType.SEMANTIC
)

entry.add_tag("جغرافيا")
entry.add_tags(["أوروبا", "عواصم", "فرنسا"])
entry.add_tag("أوروبا")  # لن تُضاف مكرراً

print(entry.tags)               # ['جغرافيا', 'أوروبا', 'عواصم', 'فرنسا']
print(entry.has_tag("أوروبا"))  # True
print(entry.has_tag("آسيا"))    # False
```

---

### `update_metadata(key, value)` | `merge_metadata(metadata)`

**الوصف:** تحديث حقل واحد أو دمج قاموس كامل من البيانات الوصفية بالذاكرة. مفيد لتخزين معلومات إضافية كمصدر البيانات أو معرِّف الجلسة.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح البيانات الوصفية |
| `value` | `Any` | القيمة المراد تخزينها |
| `metadata` | `Dict[str, Any]` | قاموس يُدمَج مع البيانات الموجودة |

**Return:** `None`

```python
entry = MemoryEntry(
    content="نص مهم",
    timestamp=time.time(),
    memory_type=MemoryType.LONG_TERM
)

entry.update_metadata("source", "user_conversation")
entry.merge_metadata({"language": "ar", "verified": True})

print(entry.metadata)
# {'id': 'abc123...', 'source': 'user_conversation',
#  'language': 'ar', 'verified': True}
```

---

### `to_dict(include_embedding=False)` | `to_json(include_embedding=False)`

**الوصف:** يُحوِّل الذاكرة إلى `dict` أو نص JSON شامل لكل الخصائص. مفيد للحفظ في ملفات أو قواعد البيانات.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `include_embedding` | `bool` | `False` | تضمين متجه التضمين في النتيجة |

**Return:** `dict` / `str`

```python
d = entry.to_dict()
print(list(d.keys()))
# ['id', 'content', 'timestamp', 'memory_type', 'importance',
#  'effective_importance', 'access_count', 'tags', 'metadata',
#  'last_access', 'decay_factor', 'age_seconds', 'priority']

json_str = entry.to_json()          # نص JSON جاهز للحفظ
json_with_emb = entry.to_json(include_embedding=True)
```

---

### `from_dict(data)` | `from_json(json_str)` — Class Methods

**الوصف:** يُنشئ `MemoryEntry` من `dict` أو نص JSON. مفيد لاستعادة الذكريات المحفوظة على القرص أو في قاعدة البيانات. يُحوِّل `memory_type` من نص إلى Enum تلقائياً.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `data` | `Dict[str, Any]` | قاموس يحتوي على بيانات الذاكرة |
| `json_str` | `str` | نص JSON يحتوي على بيانات الذاكرة |

**Return:** `MemoryEntry`

--

```python
# حفظ ثم استعادة
json_str = entry.to_json()
restored = MemoryEntry.from_json(json_str)

print(restored.content)         # نفس المحتوى الأصلي
print(restored.id == entry.id)  # True

# من قاموس مباشرة
data = {
    'content': 'المستخدم يفضل الرد بالعربية',
    'timestamp': 1700000000.0,
    'memory_type': 'long_term',  # نص يُحوَّل تلقائياً
    'importance': 0.8,
    'tags': ['تفضيلات']
}
entry2 = MemoryEntry.from_dict(data)
print(entry2.memory_type)    # MemoryType.LONG_TERM
print(entry2.priority.name)  # HIGH
```

---

## 5. `ChatMessage` — رسالة المحادثة

>
> **الوصف:** `dataclass` يُمثِّل وحدة المحادثة الأساسية — تبادل واحد بين المستخدم والنظام. يُستخدم داخلياً في أنواع الذاكرة المختلفة لتخزين الرسائل بشكل موحَّد.

### الخصائص | Attributes

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `input` | `str` | نص رسالة المستخدم |
| `output` | `str` | نص رد النظام / المساعد |
| `timestamp` | `float` | وقت الإنشاء — يُضبط تلقائياً |
| `metadata` | `Dict[str, Any]` | بيانات إضافية اختيارية |

---

### `to_dict()`

**الوصف:** يُحوِّل الرسالة إلى `dict` يحتوي على جميع الخصائص.

**لا يأخذ معاملات.** | **Return:** `Dict[str, Any]`

---

### `to_text()`

**الوصف:** يُحوِّل الرسالة إلى نص منسَّق بصيغة `user: ...\n assistant: ...` جاهز للتمرير لنموذج اللغة.

**لا يأخذ معاملات.** | **Return:** `str`


```python
from memory import ChatMessage

msg = ChatMessage(
    input="ما هي عاصمة السعودية؟",
    output="عاصمة المملكة العربية السعودية هي مدينة الرياض.",
    metadata={"session": "chat_001", "model": "gpt-4o"}
)

print(msg.to_text())
# user: ما هي عاصمة السعودية؟
#  assistant: عاصمة المملكة العربية السعودية هي مدينة الرياض.

d = msg.to_dict()
print(d['input'])     # ما هي عاصمة السعودية؟
print(d['metadata'])  # {'session': 'chat_001', 'model': 'gpt-4o'}
```

---

## 6. `Entity` — الكيان

>
> **الوصف:** `dataclass` يُمثِّل كياناً (شخصاً، مكاناً، منظمةً، منتجاً...) مُستخرَجاً من المحادثة. يتراكم فيه تاريخ ظهور الكيان وسياقاته عبر الجلسة كلها. يُستخدم حصراً داخل `ConversationEntityMemory`.

### الخصائص | Attributes

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `name` | `str` | اسم الكيان |
| `entity_type` | `str` | نوع الكيان: `person`, `place`, `organization`... |
| `contexts` | `List[str]` | قائمة تراكمية للسياقات التي ظهر فيها |
| `first_seen` | `float` | Unix timestamp لأول ذكر — يُضبط تلقائياً |
| `last_seen` | `float` | Unix timestamp لآخر ذكر — يُحدَّث عند كل إضافة |

---

### `add_context(context)`

**الوصف:** يُضيف سياقاً نصياً جديداً لقائمة سياقات الكيان ويُحدِّث `last_seen` تلقائياً.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `context` | `str` | النص الذي ظهر فيه الكيان |

**Return:** `None`

---

### `get_recent_contexts(limit=3)`

**الوصف:** يُعيد آخر N سياقات حُفظت للكيان (الأحدث أولاً في آخر القائمة).

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `limit` | `int` | `3` | عدد السياقات المُعادة |

**Return:** `List[str]`

```python
from memory import Entity

entity = Entity(name="أحمد", entity_type="person")

entity.add_context("أحمد يعمل مهندساً في شركة تقنية بالرياض.")
entity.add_context("ذكر أحمد أنه متخصص في الذكاء الاصطناعي.")
entity.add_context("أحمد حاصل على ماجستير من جامعة الملك عبدالله.")

print(len(entity.contexts))  # 3

recent = entity.get_recent_contexts(limit=2)
print(recent)
# ['ذكر أحمد أنه متخصص في الذكاء الاصطناعي.',
#  'أحمد حاصل على ماجستير من جامعة الملك عبدالله.']
```

---

## 7. `BaseMemory` — الواجهة الأساسية

>
> **الوصف:** كلاس مجرد (ABC) يُعرِّف الواجهة الإلزامية لكل نوع ذاكرة في النظام. يضمن أن جميع الأنواع الأربعة توفر نفس الدوال الأساسية، مما يُتيح التبديل بينها بشفافية تامة في أي جزء من التطبيق.

### الدوال المجردة — يجب تطبيقها في كل نوع

---

### `save_context(inputs, outputs)` ← مجردة

**الوصف:** يحفظ تبادلاً واحداً في الذاكرة. كل نوع ذاكرة يُعالج هذا التبادل بطريقته الخاصة (الـ Buffer يُضيفه مباشرة، الـ Summary قد يُطلق التلخيص، الـ Entity يستخرج الكيانات...).

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | قاموس يجب أن يحتوي على مفتاح `input_key` برسالة المستخدم |
| `outputs` | `Dict[str, Any]` | قاموس يجب أن يحتوي على مفتاح `output_key` برد النظام |

**Return:** `None`

---

### `load_memory_variables(inputs)` ← مجردة

**الوصف:** يُحمِّل السياق من الذاكرة لتمريره لنموذج اللغة. يُعيد قاموساً يحتوي على مفتاح `memory_key` بقيمة نصية أو كائن.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | المدخلات الحالية (تُستخدم في `EntityMemory` لاستخراج الكيانات من السؤال الحالي) |

**Return:** `Dict[str, Any]` — مثال: `{"history": "نص المحادثة..."}`

---

### `clear()` ← مجردة

**الوصف:** يمسح جميع محتويات الذاكرة بشكل كامل ونهائي.

**لا يأخذ معاملات.** | **المُعيدات:** `None`

---

### `get_memory_stats()`

**الوصف:** يُعيد إحصائيات عامة عن حالة الذاكرة. الدالة الأساسية تُعيد نوع الكلاس والحجم، وكل نوع يُوسِّعها بإحصائياته الخاصة.

**لا يأخذ معاملات.** | **Return:** `dict`

---

### `asave_context(inputs, outputs)` | `aload_memory_variables(inputs)` — Async

**الوصف:** نسخ `async` من الدوالّ الرئيسية تعمل عبر `asyncio.to_thread`. مناسبة لـ FastAPI أو أي إطار غير متزامن دون حجب حلقة الأحداث.

```python
import asyncio
from memory import ConversationBufferMemory

async def async_turn(user_input: str, system_response: str):
    memory = ConversationBufferMemory()

    await memory.asave_context(
        {"input": user_input},
        {"output": system_response}
    )
    context = await memory.aload_memory_variables({})
    return context["history"]

result = asyncio.run(async_turn("مرحباً", "أهلاً!"))
print(result)
```

---

### `async with` — Async Context Manager

**الوصف:** يدعم `BaseMemory` الاستخدام كـ `async context manager`. يُنادى `clear()` تلقائياً عند الخروج من الـ `with` block، مما يضمن تنظيف الذاكرة بعد انتهاء الجلسة.

```python
async def session():
    async with ConversationBufferMemory() as mem:
        await mem.asave_context({"input": "مرحبا"}, {"output": "أهلاً"})
        ctx = await mem.aload_memory_variables({})
        print(ctx["history"])
    # ← يُنادى clear() تلقائياً هنا

asyncio.run(session())
```


## 9. `BaseRetriever` — واجهة الاسترجاع

>
> **الوصف:** كلاس مجرد يُعرِّف واجهة أنظمة الاسترجاع المتجهي. يُستخدم مع الذاكرة الدلالية للبحث عن ذكريات ذات صلة بالاستعلام.

### `add_documents(documents)` ← مجردة

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `documents` | `List[Any]` | قائمة المستندات المراد فهرستها |

---

### `get_relevant_documents(query, k=3)` ← مجردة

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `query` | `str` | مطلوب | نص الاستعلام |
| `k` | `int` | `3` | عدد المستندات الأكثر صلةً المُعادة |

**المُعيدات:** `List[Any]`

---

## 10. `ConversationBufferMemory` — ذاكرة المحادثة الكاملة

>
> **الوصف:** أبسط أنواع الذاكرة وأكثرها مباشرةً. تحفظ **المحادثة بأكملها** منذ بدايتها دون حذف أي شيء. كل رسالة جديدة تُضاف للنهاية مع طابع زمني تلقائي.
>
> ⚠️ **تنبيه:** حجم السياق يكبر مع كل رسالة. في المحادثات الطويلة جداً قد يتجاوز نافذة سياق النموذج.

### `__init__()` — المعاملات

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `return_messages` | `bool` | `False` | `True` = يُعيد `List[Dict]`، `False` = يُعيد نصاً مدمجاً |
| `input_key` | `str` | `"input"` | المفتاح المستخدم للبحث عن رسالة المستخدم في `inputs` |
| `output_key` | `str` | `"output"` | المفتاح المستخدم للبحث عن رد النظام في `outputs` |
| `memory_key` | `str` | `"history"` | المفتاح المستخدم في القاموس المُرجَع من `load_memory_variables` |

```python
from memory import ConversationBufferMemory

# إرجاع نص مدمج (افتراضي)
memory = ConversationBufferMemory()

# إرجاع قائمة كائنات قاموس
memory_obj = ConversationBufferMemory(return_messages=True)

# مفاتيح مخصصة لتطبيق بمفاتيح مختلفة
memory_custom = ConversationBufferMemory(
    input_key="question",
    output_key="answer",
    memory_key="chat_history"
)
```

---

### `save_context(inputs, outputs)`

**الوصف:** يُضيف تبادلاً جديداً للذاكرة. يبحث عن رسالة المستخدم باستخدام `input_key` وعن رد النظام باستخدام `output_key`، ويحفظهما مع الطابع الزمني.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `input_key` |
| `outputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `output_key` |

**Return:** `None`

```python
memory = ConversationBufferMemory()

memory.save_context(
    inputs={"input": "ما هو الذكاء الاصطناعي؟"},
    outputs={"output": "الذكاء الاصطناعي هو محاكاة الذكاء البشري بالحواسيب."}
)
memory.save_context(
    inputs={"input": "هل يمكنه فهم العربية؟"},
    outputs={"output": "نعم، النماذج الحديثة تدعم العربية بشكل ممتاز."}
)

print(len(memory.chat_memory))  # 2
```

---

### `load_memory_variables(inputs)`

**الوصف:** يُعيد تاريخ المحادثة الكامل. إذا كان `return_messages=False` يُعيد نصاً بصيغة "المستخدم: ...\nالمساعد: ..."، وإذا كان `True` يُعيد القائمة الأصلية من القواميس.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | المدخلات الحالية — غير مستخدمة في هذا النوع |

**Return:** `Dict[str, Any]`

```python
context = memory.load_memory_variables({})
print(context["history"])
# المستخدم: ما هو الذكاء الاصطناعي؟
# المساعد: الذكاء الاصطناعي هو محاكاة الذكاء البشري بالحواسيب.
# المستخدم: هل يمكنه فهم العربية؟
# المساعد: نعم، النماذج الحديثة تدعم العربية بشكل ممتاز.
```

---

### `clear()`

**الوصف:** يمسح جميع الرسائل المحفوظة من `chat_memory`.

**لا يأخذ معاملات.** | **Return:** `None`

```python
memory.clear()
print(len(memory.chat_memory))  # 0
```

---

### `get_memory_stats()`

**الوصف:** يُعيد إحصائيات عن عدد الرسائل وحجمها التقريبي.

**لا يأخذ معاملات.** | **المُعيدات:** `dict`

```python
stats = memory.get_memory_stats()
print(stats)
# {
#   'type': 'ConversationBufferMemory',
#   'message_count': 2,
#   'total_characters': 175,
#   'estimated_tokens': 43   # تقدير: total_chars ÷ 4
# }
```

---

### `get_messages(limit=None)`

**الوصف:** يُعيد قائمة الرسائل المحفوظة مع إمكانية تحديد آخر N رسالة. إذا كان `limit=None` يُعيد نسخة من القائمة كاملة.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `limit` | `int \| None` | `None` | عدد آخر الرسائل المطلوبة. `None` يُعيد الكل |

**Return:** `List[Dict[str, Any]]`

--

```python
# كل الرسائل
all_msgs = memory.get_messages()

# آخر رسالتين فقط
recent = memory.get_messages(limit=2)
print(recent[-1]['input'])    # آخر رسالة مستخدم
print(recent[-1]['output'])   # آخر رد نظام
print(recent[-1]['timestamp'])# الطابع الزمني
```

---

## 11. `ConversationBufferWindowMemory` — ذاكرة النافذة

>
> **الوصف:** تمتد من `ConversationBufferMemory` بإضافة **نافذة منزلقة** بحد أقصى `k` رسالة. تستخدم `collections.deque(maxlen=k)` داخلياً، لذلك عند إضافة رسالة جديدة تتجاوز الحد تُحذف أقدم رسالة **تلقائياً** دون أي تدخل.
>
> ✅ **مناسبة للمحادثات الطويلة** حيث يكفي السياق الأخير فقط لإعطاء إجابات صحيحة.

### `__init__()` — المعاملات

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `k` | `int` | `5` | عدد الرسائل الأخيرة المحفوظة. يجب أن يكون > 0 وإلا يرفع `ValueError` |
| `**kwargs` | — | — | تُمرَّر لـ `ConversationBufferMemory`: `return_messages`, `input_key`, `output_key`, `memory_key` |

```python
from memory import ConversationBufferWindowMemory

# آخر 5 رسائل (افتراضي)
memory = ConversationBufferWindowMemory(k=5)

# آخر 10 رسائل مع مفتاح مخصص
memory = ConversationBufferWindowMemory(
    k=10,
    return_messages=True,
    memory_key="chat_history"
)

# خطأ: k يجب أن يكون موجباً
try:
    bad = ConversationBufferWindowMemory(k=0)
except ValueError as e:
    print(e)  # "k يجب أن يكون موجباً"
```

---

### `get_memory_stats()`

**الوصف:** يُوسِّع إحصائيات الكلاس الأب `ConversationBufferMemory` بإضافة `window_size` و `is_full`.

**لا يأخذ معاملات.** | **Return:** `dict`

```python
memory = ConversationBufferWindowMemory(k=3)

for i in range(5):  # 5 رسائل → يحتفظ بآخر 3 فقط
    memory.save_context({"input": f"سؤال {i+1}"}, {"output": f"إجابة {i+1}"})

stats = memory.get_memory_stats()
print(stats)
# {
#   'type': 'ConversationBufferWindowMemory',
#   'message_count': 3,      ← يحتفظ بـ 3 فقط رغم إضافة 5
#   'window_size': 3,
#   'is_full': True,
#   'total_characters': ...,
#   'estimated_tokens': ...
# }
```

---

### `get_window_info()`

**الوصف:** يُعيد معلومات تفصيلية عن الحالة الحالية للنافذة: الحجم الحالي، الحد الأقصى، المقاعد المتاحة، وهل امتلأت.

**لا يأخذ معاملات.** | **Return:** `dict`

```python
info = memory.get_window_info()
print(info)
# {
#   'current_size': 3,
#   'max_size': 3,
#   'available_slots': 0,
#   'is_full': True
# }

# مثال على نافذة جزئياً مملوءة
new_mem = ConversationBufferWindowMemory(k=5)
new_mem.save_context({"input": "سؤال"}, {"output": "إجابة"})
print(new_mem.get_window_info())
# {'current_size': 1, 'max_size': 5, 'available_slots': 4, 'is_full': False}
```

---

## 12. `ConversationSummaryMemory` — ذاكرة التلخيص

>
> **الوصف:** ذاكرة ذكية تُلخِّص المحادثات القديمة **تلقائياً** عند تجاوز حد التوكنز. تحتفظ بالرسائل الحديثة كاملةً وبملخص تراكمي للقديمة. الملخص يتراكم ولا يُحذف، فيحتفظ بالمعلومات المهمة طوال الجلسة.
>
> ⚠️ **تتطلب نموذج لغوي** (`BaseLLMInterface`) للقيام بعملية التلخيص.

### `__init__()` — المعاملات

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `llm` | `BaseLLMInterface` | **مطلوب** | نموذج اللغة المستخدم للتلخيص |
| `max_token_limit` | `int` | `2000` | الحد الأقصى للتوكنز قبل تفعيل التلخيص تلقائياً |
| `memory_key` | `str` | `"history"` | مفتاح الذاكرة في القاموس المُرجَع |
| `input_key` | `str` | `"input"` | مفتاح رسالة المستخدم |
| `output_key` | `str` | `"output"` | مفتاح رد النظام |
| `summary_prompt_template` | `str \| None` | `None` → قالب افتراضي | قالب prompt مخصص للتلخيص. يجب أن يحتوي على `{previous_summary}` و `{new_conversation}` |

```python
from memory import ConversationSummaryMemory

llm = OpenAILLM(api_key="sk-...")

# استخدام افتراضي
memory = ConversationSummaryMemory(llm=llm, max_token_limit=1500)

# مع قالب تلخيص مخصص
custom_template = """لخّص المحادثة في 3 نقاط رئيسية:
الملخص السابق: {previous_summary}
المحادثة الجديدة: {new_conversation}
الملخص الجديد:"""

memory = ConversationSummaryMemory(
    llm=llm,
    max_token_limit=2000,
    summary_prompt_template=custom_template
)
```

---

### `save_context(inputs, outputs)`

**الوصف:** يحفظ رسالة جديدة في `chat_memory` ثم يتحقق فوراً من الحجم. إذا تجاوز مجموع التوكنز المقدَّر `max_token_limit`، يُطلق عملية التلخيص (`_summarize()`) تلقائياً ويُفرغ `chat_memory`.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `input_key` |
| `outputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `output_key` |

**Return:** `None`

```python
memory.save_context(
    {"input": "اشرح لي نظرية النسبية الخاصة"},
    {"output": "نظرية النسبية الخاصة لأينشتاين تقول إن سرعة الضوء ثابتة لجميع المراقبين..."}
)
# إذا تجاوز الحجم max_token_limit → يُلخَّص تلقائياً
```

---

### `load_memory_variables(inputs)`

**الوصف:** يُعيد الملخص التراكمي مدموجاً مع الرسائل الأخيرة غير الملخَّصة بعد، مفصولَيْن بفاصل نصي واضح. إذا كان هناك ملخص فقط أو رسائل حديثة فقط يُعيد ما هو متاح.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | المدخلات الحالية — غير مستخدمة في هذا النوع |

**Return:** `Dict[str, Any]`

```python
context = memory.load_memory_variables({})
print(context["history"])
# [ملخص المحادثات القديمة هنا]
#
# ---  the recent conversation---
# user: آخر سؤال من المستخدم
# assistant: آخر رد من النظام
```

---

### `get_summary()`

**الوصف:** يُعيد الملخص التراكمي الحالي كنص خام.

**لا يأخذ معاملات.** | **Return:** `str` — الملخص أو `""` إن لم يُولَّد بعد.

```python
summary = memory.get_summary()
print(summary)
# "ناقش المستخدم نظرية النسبية ثم سأل عن التعلم الآلي..."
# أو "" إذا لم يحدث تلخيص بعد
```

---

### `force_summarize()`

**الوصف:** يُجبر النظام على تلخيص المحادثة الحالية **فوراً** حتى لو لم يتجاوز `max_token_limit`. مفيد قبل انتهاء الجلسة أو عند رغبتك في تحرير الذاكرة يدوياً. لا يفعل شيئاً إذا كانت `chat_memory` فارغة.

**لا يأخذ معاملات.** | **Return:** `None`

```python
memory.save_context({"input": "سؤال أول"}, {"output": "إجابة أولى"})
memory.save_context({"input": "سؤال ثانٍ"}, {"output": "إجابة ثانية"})

print(f"قبل: {len(memory.chat_memory)} رسالة")   # 2
memory.force_summarize()
print(f"بعد: {len(memory.chat_memory)} رسالة")   # 0 (مُفرَّغت)
print(f"الملخص: {memory.get_summary()}")          # النص الملخَّص
```

---

### `clear()`

**الوصف:** يمسح الرسائل **والملخص** معاً بشكل كامل.

**لا يأخذ معاملات.** | **Return:** `None`

```python
memory.clear()
print(memory.get_summary())     # "" (فارغ)
print(len(memory.chat_memory))  # 0
```

---

### `get_memory_stats()`

**لا يأخذ معاملات.** | **Return:** `dict`

```python
stats = memory.get_memory_stats()
print(stats)
# {
#   'type': 'ConversationSummaryMemory',
#   'has_summary': True,
#   'summary_length': 250,         ← عدد أحرف الملخص
#   'recent_messages_count': 3,    ← رسائل لم تُلخَّص بعد
#   'estimated_tokens': 390,       ← تقدير إجمالي التوكنز
#   'token_limit': 2000            ← الحد المضبوط
# }
```

---

## 13. `ConversationEntityMemory` — ذاكرة الكيانات

>
> **الوصف:** ذاكرة متخصصة تتبع **الكيانات** (أشخاصاً، أماكن، منظمات، منتجات...) المذكورة في المحادثة. عند كل رسالة يستخرج النموذج الكيانات ويحفظ سياقاتها. عند التحميل يُعيد فقط السياقات الخاصة بالكيانات المذكورة في السؤال الحالي لا كل التاريخ.
>
> ⚠️ **تتطلب نموذج لغوي** (`BaseLLMInterface`) لاستخراج الكيانات في كل رسالة.
> ('Stanza')  او يمكنك استخدام 

### `__init__()` — المعاملات

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `llm` | `BaseLLMInterface` | **مطلوب** | نموذج اللغة المستخدم لاستخراج الكيانات |
| `memory_key` | `str` | `"entity_info"` | مفتاح معلومات الكيانات في القاموس المُرجَع |
| `input_key` | `str` | `"input"` | مفتاح رسالة المستخدم |
| `output_key` | `str` | `"output"` | مفتاح رد النظام |
| `entity_extraction_prompt` | `str \| None` | `None` → قالب افتراضي | قالب prompt مخصص لاستخراج الكيانات. يجب أن يحتوي على `{text}` |

```python
from memory import ConversationEntityMemory

llm = OpenAILLM(api_key="sk-...")

# استخدام افتراضي
memory = ConversationEntityMemory(llm=llm)

# مع قالب استخراج مخصص (فقط أسماء أشخاص وأماكن)
custom_prompt = """استخرج أسماء الأشخاص والأماكن فقط من النص التالي:
النص: {text}
القائمة (مفصولة بفاصلة، بدون شرح):"""

memory = ConversationEntityMemory(
    llm=llm,
    memory_key="entities",
    entity_extraction_prompt=custom_prompt
)
```

---

### `save_context(inputs, outputs)`

**الوصف:** يحفظ الرسالة **ويستخرج الكيانات** منها تلقائياً عبر نموذج اللغة. يُضيف كل كيان جديد إلى `entity_store`، ويُضيف السياق الكامل (input + output) لكيان موجود مسبقاً.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `input_key` |
| `outputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `output_key` |

**Return:** `None`

```python
memory.save_context(
    {"input": "أخبرني عن شركة أرامكو"},
    {"output": "أرامكو شركة نفطية سعودية تأسست عام 1933 في الظهران."}
)

print(memory.list_entities())
# ['أرامكو', 'الظهران']  ← مُستخرَجة تلقائياً من النص
```
### With Stanza
```python
from memory import ConversationEntityMemory
# مع قالب استخراج مخصص (فقط أسماء أشخاص وأماكن)
custom_prompt = """استخرج أسماء الأشخاص والأماكن فقط من النص التالي:
النص: {text}
القائمة (مفصولة بفاصلة، بدون شرح):"""

memory = ConversationEntityMemory(
    memory_key="entities",
    entity_extraction_prompt=custom_prompt,
    lang='ar'
)

```
---

### `load_memory_variables(inputs)`

**الوصف:** يستخرج الكيانات من **المدخل الحالي** ثم يُعيد السياقات السابقة لتلك الكيانات فقط. هذا يُزوِّد النموذج بسياق ذي صلة مباشرة بالسؤال بدلاً من كل تاريخ المحادثة.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `inputs` | `Dict[str, Any]` | يجب أن يحتوي على مفتاح `input_key` — يُستخدَم لاستخراج الكيانات |

**Return:** `Dict[str, Any]`

---

```python
# يستخرج "أرامكو" من السؤال ويُعيد سياقاتها السابقة فقط
context = memory.load_memory_variables({"input": "ما هو مقر أرامكو؟"})
print(context["entity_info"])
# معلومات سابقة عن أرامكو:
# أرامكو شركة نفطية سعودية تأسست عام 1933 في الظهران.

# إذا لم يُعثَر على كيانات مطابقة يُعيد نصاً فارغاً
context2 = memory.load_memory_variables({"input": "كيف حالك؟"})
print(context2["entity_info"])  # ""
```

---

### `get_entity_info(entity_name)`

**الوصف:** يُعيد معلومات تفصيلية عن كيان محدد بالاسم الدقيق. يُعيد `None` إذا لم يكن الكيان في المخزن.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `entity_name` | `str` | اسم الكيان الدقيق كما ظهر في `entity_store` |

**Return:** `dict | None`

```python
info = memory.get_entity_info("أرامكو")
print(info)
# {
#   'name': 'أرامكو',
#   'type': 'unknown',
#   'contexts_count': 1,
#   'first_seen': 1700000000.0,
#   'last_seen': 1700000010.0,
#   'recent_contexts': ['أرامكو شركة نفطية سعودية تأسست...']
# }

print(memory.get_entity_info("كيان غير موجود"))  # None
```

---

### `list_entities()`

**الوصف:** يُعيد قائمة بأسماء جميع الكيانات المُكتشَفة والمحفوظة في `entity_store` حتى الآن.

**لا يأخذ معاملات.** | **Return:** `List[str]`

```python
memory.save_context(
    {"input": "محمد يعمل في Microsoft بدبي"},
    {"output": "رائع! Microsoft شركة تقنية عالمية."}
)

entities = memory.list_entities()
print(entities)
# ['أرامكو', 'الظهران', 'محمد', 'Microsoft', 'دبي']
```

---

### `clear()`

**الوصف:** يمسح `entity_store` و `chat_memory` معاً بشكل كامل.

**لا يأخذ معاملات.** | **Return:** `None`

---

### `get_memory_stats()`

**لا يأخذ معاملات.** | **Return:** `dict`

```python
stats = memory.get_memory_stats()
print(stats)
# {
#   'type': 'ConversationEntityMemory',
#   'entity_count': 5,        ← عدد الكيانات المكتشفة
#   'message_count': 2,       ← عدد الرسائل المحفوظة
#   'total_contexts': 7       ← إجمالي السياقات عبر كل الكيانات
# }
```

---

## 💡 مثال شامل

```python
import asyncio
from memory import ConversationBufferMemory
from memory import ConversationBufferWindowMemory
from memory import ConversationSummaryMemory
from memory import ConversationEntityMemory
from  llm import MistralInterFace
llm=MistralInterFace(api_key="XXXXXXXX")


# ─── تطبيق نموذج اللغة ─────────────────────────────────────────



# ═══════════════════════════════════════════════════════════
#  1. BufferMemory — حفظ المحادثة الكاملة
# ═══════════════════════════════════════════════════════════
print("─" * 55)
print("1. ConversationBufferMemory — كل المحادثة")
print("─" * 55)

buffer = ConversationBufferMemory()

buffer.save_context(
    {"input": "مرحباً، اسمي سارة"},
    {"output": "أهلاً سارة! كيف يمكنني مساعدتك؟"}
)
buffer.save_context(
    {"input": "أريد تعلم Python"},
    {"output": "Python لغة رائعة للمبتدئين!"}
)
buffer.save_context(
    {"input": "من أين أبدأ؟"},
    {"output": "ابدئي بتعلم المتغيرات والحلقات أولاً."}
)

ctx = buffer.load_memory_variables({})
print(ctx["history"])

stats = buffer.get_memory_stats()
print(f"\nالإحصائيات: {stats['message_count']} رسائل، "
      f"~{stats['estimated_tokens']} توكن")

recent = buffer.get_messages(limit=1)
print(f"آخر سؤال: {recent[0]['input']}")


# ═══════════════════════════════════════════════════════════
#  2. WindowMemory — آخر K رسالة فقط
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("2. ConversationBufferWindowMemory — آخر 3 رسائل")
print("─" * 55)

window = ConversationBufferWindowMemory(k=3)

for i in range(1, 7):  # 6 رسائل → يحتفظ بآخر 3 فقط
    window.save_context(
        {"input": f"سؤال رقم {i}"},
        {"output": f"إجابة رقم {i}"}
    )

ctx = window.load_memory_variables({})
print(ctx["history"])  # يحتوي فقط على سؤال 4، 5، 6

info = window.get_window_info()
print(f"\nالنافذة: {info['current_size']}/{info['max_size']} — "
      f"مملوءة: {info['is_full']}")


# ═══════════════════════════════════════════════════════════
#  3. SummaryMemory — تلخيص تلقائي
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("3. ConversationSummaryMemory — تلخيص عند الحاجة")
print("─" * 55)

summ = ConversationSummaryMemory(llm=llm, max_token_limit=30)

summ.save_context(
    {"input": "ما هو التعلم الآلي؟"},
    {"output": "التعلم الآلي فرع من الذكاء الاصطناعي يستخدم البيانات لتدريب النماذج."}
)
summ.save_context(
    {"input": "ما الفرق بين supervised وunsupervised؟"},
    {"output": "Supervised يستخدم بيانات مُصنَّفة، وunsupervised يكتشف الأنماط تلقائياً."}
)

# إجبار التلخيص يدوياً
summ.force_summarize()
print(f"الملخص: {summ.get_summary()}")
print(f"رسائل بعد التلخيص: {len(summ.chat_memory)}")  # 0

# إضافة رسائل جديدة بعد التلخيص
summ.save_context(
    {"input": "وما هي الشبكات العصبية؟"},
    {"output": "الشبكات العصبية مستوحاة من الدماغ البشري وتُستخدم في التعرف على الصور."}
)

ctx = summ.load_memory_variables({})
print(f"\nالسياق الكامل:\n{ctx['history']}")

stats = summ.get_memory_stats()
print(f"\nيوجد ملخص: {stats['has_summary']} — "
      f"رسائل حديثة: {stats['recent_messages_count']}")


# ═══════════════════════════════════════════════════════════
#  4. EntityMemory — تتبع الكيانات
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("4. ConversationEntityMemory — تتبع الكيانات")
print("─" * 55)

entity_mem = ConversationEntityMemory(llm=llm)

entity_mem.save_context(
    {"input": "أخبرني عن Tesla"},
    {"output": "Tesla شركة سيارات كهربائية أمريكية أسسها Elon Musk عام 2003."}
)
entity_mem.save_context(
    {"input": "وأين تقع مقرات Tesla؟"},
    {"output": "مقرها الرئيسي في Austin, Texas."}
)

print(f"الكيانات المكتشفة: {entity_mem.list_entities()}")

info = entity_mem.get_entity_info("Tesla")
if info:
    print(f"سياقات Tesla: {info['contexts_count']}")
    print(f"آخر سياق: {info['recent_contexts'][-1][:60]}...")

ctx = entity_mem.load_memory_variables({"input": "هل Tesla شركة ناجحة؟"})
print(f"\nالسياق ذو الصلة:\n{ctx['entity_info']}")

stats = entity_mem.get_memory_stats()
print(f"\nالكيانات: {stats['entity_count']} — "
      f"الرسائل: {stats['message_count']} — "
      f"السياقات: {stats['total_contexts']}")


# ═══════════════════════════════════════════════════════════
#  5. Async — استخدام غير متزامن
# ═══════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("5. Async Context Manager")
print("─" * 55)

async def async_session():
    async with ConversationBufferMemory() as mem:
        await mem.asave_context(
            {"input": "هل أنت متاح؟"},
            {"output": "نعم، أنا هنا لمساعدتك!"}
        )
        ctx = await mem.aload_memory_variables({})
        print(ctx["history"])
    # ← يُنادى clear() تلقائياً هنا

asyncio.run(async_session())
```

---

### Example With Rag System

```python
from llm import MistralInterface
from embeddings import MistralEmbedder
from vector_database import FAISSVectorDatabase
from chunks import MultilanguageTextChunker
from context import ContextManager
from rag.core import RAGSystem
embedder=MistralEmbedder(api_key=api)
base_rag=RAGSystem(
        vector_db=FAISSVectorDatabase(embedder=embedder),
        llm=MistralInterface(api_key=api),
        chunker=MultilanguageTextChunker(),
        context_manager=ContextManager(),)

from memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationEntityMemory,
)
rag = base_rag
KNOWLEDGE_BASE = {
    "doc_rag": (
        "RAG يرمز إلى Retrieval-Augmented Generation. "
        "يعمل عن طريق استرجاع المستندات ذات الصلة أولاً ثم توليد الإجابة بناءً عليها. "
        "يُحسّن RAG دقة النماذج اللغوية الكبيرة ويُقلّل من الهلوسة. "
        "يُستخدم في قواعد المعرفة المؤسسية وأنظمة الإجابة على الأسئلة."
    ),
    "doc_ai": (
        "الذكاء الاصطناعي (Artificial Intelligence) هو محاكاة العقل البشري في الحواسيب. "
        "يشمل تعلم الآلة والشبكات العصبية ومعالجة اللغة الطبيعية. "
        "تأسس الذكاء الاصطناعي كمجال أكاديمي عام 1956 في مؤتمر دارتموث. "
        "تُطبّق تقنيات الذكاء الاصطناعي في الطب والتعليم والصناعة."
    ),
    "doc_ml": (
        "تعلم الآلة (Machine Learning) يُمكّن الأنظمة من التعلم من البيانات. "
        "أبرز أنواعه: التعلم المُشرف، غير المُشرف، والتعزيزي. "
        "الشبكات العصبية العميقة هي أساس تعلم العمق (Deep Learning). "
        "يُستخدم في التعرف على الصور والنصوص والتنبؤ بالأنماط."
    ),
    "doc_llm": (
        "النماذج اللغوية الكبيرة (LLM) تُدرَّب على كميات ضخمة من النصوص. "
        "أشهر النماذج: GPT-4 من OpenAI، وClaude من Anthropic، وGemini من Google. "
        "تعتمد على معمارية Transformer المُقدَّمة عام 2017. "
        "التضمينات (Embeddings) تُحوّل النصوص إلى متجهات رقمية لقياس التشابه."
    ),
}
base_rag.add_documents(KNOWLEDGE_BASE)
def conversational_rag_query(
    query: str,
    memory,
    memory_key: str = "history",
) -> str:
    """استعلام RAG يُدمج تاريخ المحادثة في السياق"""
    # تحميل تاريخ المحادثة
    mem_vars  = memory.load_memory_variables({"input": query})
    history   = mem_vars.get(memory_key, "")
    # استرجاع من قاعدة المعرفة
    retrieved = rag.retrieve(query, top_k=2)
    context   = rag.context_manager.build(query, retrieved)
    # بناء الـ prompt مع تاريخ المحادثة
    if history:
        full_prompt = (
            f"سياق المحادثة السابقة:\n{str(history)[:400]}\n\n"
            f"معلومات مسترجعة:\n{context}\n\n"
            f"السؤال الحالي: {query}\nالإجابة:"
        )
    else:
        full_prompt = f"معلومات مسترجعة:\n{context}\n\nالسؤال: {query}\nالإجابة:"
    answer = rag.llm.generate(full_prompt)
    # حفظ التبادل في الذاكرة
    memory.save_context({"input": query}, {"output": answer})
    return answer

# ── 5a: Buffer Memory — محادثة كاملة ─────────────────────── #
print("\n  [5a] ConversationBufferMemory — محادثة كاملة")
buffer_mem = ConversationBufferMemory(
    return_messages=False, input_key="input", output_key="output", memory_key="history"
)
conversation = [
    "ما هو الـ RAG؟",
    "ما هي مزاياه على النماذج اللغوية التقليدية؟",
    "هل يُستخدم RAG في قواعد المعرفة المؤسسية؟",
]
print("\n  💬 محادثة مع RAG (Buffer Memory):")
for turn, q in enumerate(conversation, 1):
    answer = conversational_rag_query(q, buffer_mem)
    print(f"  [{turn}] 👤 {q}")
    print(f"       🤖 {answer[:80]}...")
    print()
print(f"  📝 Buffer memory: {len(buffer_mem.chat_memory)} رسائل محفوظة")
# ── 5b: Window Memory — نافذة آخر K تبادلات ──────────────── #
print("\n  [5b] ConversationBufferWindowMemory — نافذة K=2")
window_mem = ConversationBufferWindowMemory(k=2)
long_conversation = [
    "ما هو الذكاء الاصطناعي؟",
    "ما هو تعلم الآلة؟",
    "ما هي الشبكات العصبية؟",   # هذه ستُزيح الأولى
    "ما هي التضمينات؟",          # هذه ستُزيح الثانية
]
for q in long_conversation:
    conversational_rag_query(q, window_mem)
print(f"  📝 Window memory (k=2): {len(window_mem.chat_memory)} رسائل محفوظة (آخر 2)")
if window_mem.chat_memory:
    print(f"  آخر سؤال: {window_mem.chat_memory[-1].get('input', '')}")
# ── 5c: Summary Memory ────────────────────────────────────── #
print("\n  [5c] ConversationSummaryMemory — ملخص تراكمي")
summary_mem = ConversationSummaryMemory(llm=base_rag.llm,max_token_limit=300)  # لو كانت المحادثه اقل من 300 مش هيلخص  
for q in conversation:
    conversational_rag_query(q, summary_mem)
print(f"  📝 Summary memory: {len(summary_mem.chat_memory)} رسائل → ملخص من {summary_mem.max_token_limit} رمز")
# ── 5d: Entity Memory ─────────────────────────────────────── #
print("\n  [5d] ConversationEntityMemory — تتبع الكيانات")
entity_mem = ConversationEntityMemory()
entity_queries = [
    "ما هو RAG؟",
    "كيف طوّرت OpenAI نموذج GPT-4؟",
    "هل Anthropic طوّرت Claude بناءً على RAG؟",
]
for q in entity_queries:
    conversational_rag_query(q, entity_mem, memory_key="history")
entities = entity_mem.entity_store
print(f"  📝 كيانات مُتتبَّعة: {list(entities.keys())}")
```

---

## 📊 مرجع سريع

### الدوال المشتركة — جميع أنواع الذاكرة

| الدالة | الوصف | يأخذ معاملات؟ | المُعيد |
|--------|-------|--------------|---------|
| `save_context(inputs, outputs)` | حفظ تبادل جديد | ✅ نعم | `None` |
| `load_memory_variables(inputs)` | تحميل السياق للنموذج | ✅ نعم | `Dict[str, Any]` |
| `clear()` | مسح الذاكرة كاملاً | ❌ لا | `None` |
| `get_memory_stats()` | إحصائيات الذاكرة | ❌ لا | `dict` |
| `asave_context(inputs, outputs)` | حفظ async | ✅ نعم | `None` |
| `aload_memory_variables(inputs)` | تحميل async | ✅ نعم | `Dict[str, Any]` |

### الدوال الإضافية — حسب نوع الذاكرة

| الدالة | النوع | الوصف | المُعيد |
|--------|-------|-------|---------|
| `get_messages(limit)` | `Buffer` | قائمة الرسائل المحفوظة | `List[Dict]` |
| `get_window_info()` | `Window` | معلومات حالة النافذة | `dict` |
| `get_summary()` | `Summary` | الملخص التراكمي الحالي | `str` |
| `force_summarize()` | `Summary` | إجبار التلخيص فوراً | `None` |
| `get_entity_info(name)` | `Entity` | معلومات كيان بالاسم | `dict \| None` |
| `list_entities()` | `Entity` | جميع الكيانات المكتشفة | `List[str]` |

### دليل اختيار نوع الذاكرة

```
هل المحادثة قصيرة (أقل من 20 رسالة)؟
    └── نعم ──► ConversationBufferMemory
                (أبسط وأسرع، لا يحتاج LLM)

هل تحتاج فقط للسياق الأخير؟
    └── نعم ──► ConversationBufferWindowMemory(k=10)
                (نافذة منزلقة، لا يحتاج LLM)

هل المحادثة طويلة جداً وتكلفة التوكنز مهمة؟
    └── نعم ──► ConversationSummaryMemory
                (تلخيص تلقائي، يحتاج LLM)

هل تتضمن أشخاصاً أو أماكن أو منظمات متعددة؟
    └── نعم ──► ConversationEntityMemory
                (سياق ذو صلة فقط، يحتاج LLM)
```

---

> **ملاحظة معمارية:** جميع الأنواع ترث من `BaseMemory` وتلتزم بنفس الواجهة.
> التبديل بين أي نوعين يتطلب تغيير **سطر واحد فقط** دون أي تعديل في باقي الكود.
