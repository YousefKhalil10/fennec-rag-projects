
## 🌐 نظرة عامة

نظام **Persistence Manager** هو طبقة تخزين دائم متكاملة تتيح حفظ واسترجاع البيانات بصيغ متعددة مع دعم الضغط والتشفير والنسخ الاحتياطية. يُحل مشكلة أساسية في تطبيقات الذكاء الاصطناعي: **كيف تحفظ حالة التطبيق وبياناته بشكل موثوق وآمن بين الجلسات**.

### المميزات الرئيسية
- **صيغ تخزين متعددة:** JSON، Pickle، نص عادي، ومضغوطات Gzip
- **ضغط البيانات:** 4 مستويات من السرعة إلى أقصى ضغط
- **تشفير اختياري:** تشفير متماثل Fernet
- **نسخ احتياطية تلقائية:** مع الاحتفاظ بعدد محدد
- **ذاكرة مؤقتة LRU:** لتسريع القراءة المتكررة
- **تتبع البيانات الوصفية:** تواريخ الإنشاء والتعديل والأحجام
- **آمن للخيوط المتعددة:** Thread-safe عبر `RLock`
- **دعم المعاملات:** Rollback تلقائي عند الأخطاء

---


## 🏗 البنية المعمارية

```
┌──────────────────────────────────────────────────────────────┐
│                   PersistenceManager                         │
│              (الواجهة الرئيسية / Main Interface)             │
│                                                              │
│   save() │ load() │ delete() │ exists() │ transaction()      │
│   export_all() │ import_all() │ clear_all() │ get_stats()    │
└──────┬─────────┬──────────┬──────────┬──────────────────────┘
       │         │          │          │
  ┌────┴───┐ ┌───┴────┐ ┌───┴────┐ ┌───┴────────┐
  │  Data  │ │  LRU   │ │ Meta  │ │   Backup   │
  │Serial- │ │ Cache  │ │ data  │ │  Manager   │
  │ izer   │ │        │ │Manager│ │            │
  └────────┘ └────────┘ └───────┘ └────────────┘
       │
  ┌────┴──────────────────────────────────┐
  │           StorageFormat Enum          │
  │  JSON │ PICKLE │ COMPRESSED │ TEXT   │
  └───────────────────────────────────────┘
```

---


---

## 1. `StorageFormat` — صيغ التخزين

>
> **الوصف:** `Enum` يُعرِّف صيغ التخزين المدعومة. كل قيمة تُمثِّل امتداد الملف المستخدم على القرص. يُمرَّر لدوال `save()` و `load()` لتحديد كيفية تخزين البيانات.

### القيم | Values

| القيمة | الامتداد | الوصف |
|--------|---------|-------|
| `JSON` | `.json` | JSON قابل للقراءة البشرية |
| `PICKLE` | `.pickle` | ثنائي Python Pickle |
| `COMPRESSED_JSON` | `.json.gz` | JSON مضغوط بـ Gzip |
| `COMPRESSED_PICKLE` | `.pkl.gz` | Pickle مضغوط بـ Gzip |
| `TEXT` | `.txt` | نص عادي |

### الخصائص المحسوبة | Computed Properties

---

### `is_compressed` — Property

**الوصف:** يتحقق إذا كانت الصيغة مضغوطة (Gzip).

**Return:** `bool`

```python
from persistence import StorageFormat

print(StorageFormat.JSON.is_compressed)            # False
print(StorageFormat.COMPRESSED_JSON.is_compressed) # True
print(StorageFormat.PICKLE.is_compressed)          # False
print(StorageFormat.COMPRESSED_PICKLE.is_compressed) # True
```

---

### `is_binary` — Property

**الوصف:** يتحقق إذا كانت الصيغة ثنائية (Binary). صيغ Pickle وبياناتها لا يمكن فتحها كنص عادي.

**Return:** `bool`

```python
print(StorageFormat.PICKLE.is_binary)           # True
print(StorageFormat.COMPRESSED_PICKLE.is_binary)# True
print(StorageFormat.JSON.is_binary)             # False
print(StorageFormat.TEXT.is_binary)             # False
```

---

### `is_text_based` — Property

**الوصف:** يتحقق إذا كانت الصيغة مبنية على النصوص (JSON أو TEXT).

**Return:** `bool`

```python
print(StorageFormat.JSON.is_text_based)            # True
print(StorageFormat.TEXT.is_text_based)            # True
print(StorageFormat.COMPRESSED_JSON.is_text_based) # True
print(StorageFormat.PICKLE.is_text_based)          # False
```

---

## 2. `CompressionLevel` — مستويات الضغط

>
> **الوصف:** `Enum` يُعرِّف مستويات ضغط Gzip الأربعة. يُستخدم عند تهيئة `PersistenceManager` أو `DataSerializer` لضبط التوازن بين سرعة الضغط وحجم الملف الناتج.

### القيم | Values

| القيمة | الرقم | الوصف |
|--------|------|-------|
| `NONE` | `0` | بلا ضغط — أسرع، أكبر حجم |
| `FAST` | `1` | ضغط سريع — ملفات أكبر |
| `BALANCED` | `6` | توازن بين السرعة والحجم (افتراضي) |
| `BEST` | `9` | أقصى ضغط — أبطأ، أصغر حجم |

### `description` — Property

**الوصف:** يُعيد وصفاً نصياً لمستوى الضغط.

**Return:** `str`

```python
from persistence import CompressionLevel

print(CompressionLevel.NONE.description)      # "No compression"
print(CompressionLevel.FAST.description)      # "Fast compression, larger files"
print(CompressionLevel.BALANCED.description)  # "Balanced speed and size"
print(CompressionLevel.BEST.description)      # "Best compression, slower"

# استخدام عند إنشاء المدير
from persistence import PersistenceManager
manager = PersistenceManager(
    storage_path="./data",
    compression_level=CompressionLevel.BEST  # أقصى ضغط للبيانات الكبيرة
)
```

---

## 3. `LRUCache` — الذاكرة المؤقتة

>
> **الوصف:** ذاكرة مؤقتة آمنة للخيوط المتعددة تعمل بخوارزمية **Least Recently Used**. عند امتلاء الكاش، تُحذف العناصر الأقل استخداماً تلقائياً. تستخدم `OrderedDict` لتتبع ترتيب الاستخدام و`RLock` لضمان الأمان في بيئات متعددة الخيوط.

### `__init__(max_size=128)`

**الوصف:** ينشئ كاش LRU بحجم أقصى محدد. يرفع `ValueError` إذا كان `max_size` ≤ 0.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `max_size` | `int` | `128` | الحد الأقصى لعدد العناصر. يجب أن يكون > 0 |

```python
from persistence import LRUCache

cache = LRUCache(max_size=256)

# خطأ: max_size يجب أن يكون موجباً
try:
    bad_cache = LRUCache(max_size=0)
except ValueError as e:
    print(e)  # "max_size must be a positive integer."
```

---

### `get(key)`

**الوصف:** يُعيد القيمة المخزَّنة للمفتاح المطلوب. كل وصول ناجح يُعيد ترتيب العنصر ليكون الأحدث استخداماً (يمنع حذفه لأطول وقت). يُعيد `None` إذا لم يُوجد المفتاح.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | المفتاح المراد البحث عنه |

**Return:** `Any | None`

```python
cache = LRUCache(max_size=10)
cache.set("user_profile", {"name": "أحمد", "age": 30})

profile = cache.get("user_profile")
print(profile)  # {'name': 'أحمد', 'age': 30}

missing = cache.get("غير موجود")
print(missing)  # None
```

---

### `set(key, value)`

**الوصف:** يُضيف عنصراً جديداً أو يُحدِّث عنصراً موجوداً في الكاش. إذا كان الكاش ممتلئاً، يُحذف العنصر الأقل استخداماً تلقائياً قبل الإضافة.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |
| `value` | `Any` | القيمة المراد تخزينها (أي نوع) |

**Return:** `None`

```python
cache = LRUCache(max_size=3)

cache.set("a", 1)
cache.set("b", 2)
cache.set("c", 3)
# الكاش ممتلئ: [a, b, c]

cache.set("d", 4)
# "a" حُذف لأنه الأقل استخداماً: [b, c, d]

print(cache.get("a"))  # None (حُذف)
print(cache.get("d"))  # 4
```

---

### `delete(key)`

**الوصف:** يحذف عنصراً محدداً من الكاش.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | المفتاح المراد حذفه |

**Return:** `bool` — `True` إذا وُجد وحُذف، `False` إذا لم يُوجد

```python
cache.set("temp_data", [1, 2, 3])

result = cache.delete("temp_data")
print(result)  # True

result2 = cache.delete("غير موجود")
print(result2)  # False
```

---

### `clear()`

**الوصف:** يمسح جميع العناصر من الكاش بشكل كامل.

**لا يأخذ معاملات.** | **Return:** `None`

```python
cache.set("x", 1)
cache.set("y", 2)
print(len(cache))  # 2

cache.clear()
print(len(cache))  # 0
```

---

### `stats()`

**الوصف:** يُعيد إحصائيات الكاش الحالية: الحجم، الحد الأقصى، ونسبة الاستخدام.

**لا يأخذ معاملات.** | **Return:** `dict`

```python
cache = LRUCache(max_size=100)
for i in range(40):
    cache.set(f"key_{i}", i)

print(cache.stats)
# {
#   'size': 40,
#   'max_size': 100,
#   'usage_pct': 40.0
# }
```

---

### `max_size` — Property

**الوصف:** يُعيد الحد الأقصى للكاش (للقراءة فقط).

**Return:** `int`

```python
cache = LRUCache(max_size=50)
print(cache.max_size)  # 50
```

---

### دعم `in` و `len`

```python
cache.set("session", {"user": "سارة"})

print("session" in cache)   # True
print("missing" in cache)   # False
print(len(cache))           # 1
```

---

## 4. `DataSerializer` — المُسَلسِل

>
> **الوصف:** يتولى تحويل البيانات إلى bytes وعكسها، مع دعم الضغط والتشفير. يُستخدم داخلياً بواسطة `PersistenceManager` وليس عادةً مباشرةً من المستخدم.

### `__init__(compression_level, enable_encryption, encryption_key)`

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `compression_level` | `int` | `6` | مستوى ضغط Gzip (0–9) |
| `enable_encryption` | `bool` | `False` | تفعيل التشفير |
| `encryption_key` | `bytes \| None` | `None` | مفتاح Fernet (مطلوب إذا التشفير مفعَّل) |

```python
from persistence import DataSerializer, generate_encryption_key
from persistence import StorageFormat

# بدون تشفير
serializer = DataSerializer(compression_level=6)

# مع تشفير
key = generate_encryption_key()
serializer_enc = DataSerializer(
    compression_level=6,
    enable_encryption=True,
    encryption_key=key
)
```

---

### `serialize(data, format, custom_serializer=None)`

**الوصف:** يُحوِّل البيانات إلى `bytes` حسب الصيغة المطلوبة، مع تطبيق الضغط والتشفير إذا كانا مفعَّلَيْن. يرفع `SerializationError` عند الفشل.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `data` | `Any` | البيانات المراد تسلسلها |
| `format` | `StorageFormat` | صيغة التخزين المستهدفة |
| `custom_serializer` | `Callable \| None` | دالة تسلسل مخصصة تأخذ `data` وتُعيد `bytes` أو `str` |

**Return:** `bytes`

**يرفع:** `SerializationError`

```python
from persistence import DataSerializer
from persistence import StorageFormat

serializer = DataSerializer()

data = {"users": ["أحمد", "سارة"], "count": 2}

# تسلسل JSON
json_bytes = serializer.serialize(data, StorageFormat.JSON)
print(type(json_bytes))   # <class 'bytes'>
print(len(json_bytes))    # عدد البايتات

# تسلسل مضغوط
gz_bytes = serializer.serialize(data, StorageFormat.COMPRESSED_JSON)
print(len(gz_bytes) < len(json_bytes))  # True (أصغر حجماً)

# تسلسل مخصص
import json
custom = lambda d: json.dumps(d, separators=(',', ':')).encode()
compact_bytes = serializer.serialize(data, StorageFormat.JSON, custom_serializer=custom)
```

---

### `deserialize(data, format, custom_deserializer=None)`

**الوصف:** يُعيد تحويل `bytes` إلى البيانات الأصلية، مع فك الضغط وفك التشفير إذا كانا مطبَّقَيْن. يرفع `DeserializationError` عند الفشل.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `data` | `bytes` | البيانات المُسَلسَلة |
| `format` | `StorageFormat` | صيغة التخزين المستخدمة عند الحفظ |
| `custom_deserializer` | `Callable \| None` | دالة فك تسلسل مخصصة تأخذ `bytes` وتُعيد البيانات |

**Return:** `Any`

**Return:** `DeserializationError`

```python
serializer = DataSerializer()
data = {"key": "value", "num": 42}

# تسلسل ثم فك تسلسل
bytes_data = serializer.serialize(data, StorageFormat.JSON)
restored = serializer.deserialize(bytes_data, StorageFormat.JSON)

print(restored)              # {'key': 'value', 'num': 42}
print(restored == data)      # True
```

---

### `generate_encryption_key()` — دالة مساعدة

**الوصف:** تولِّد مفتاح Fernet جديداً عشوائياً للتشفير. **احفظ هذا المفتاح — بدونه لا يمكن استعادة البيانات المشفَّرة!**

**لا تأخذ معاملات.** | **Return:** `bytes`

**تتطلب:** `pip install cryptography`

```python
from persistence import generate_encryption_key

key = generate_encryption_key()
print(type(key))   # <class 'bytes'>
print(len(key))    # 44 (مفتاح Fernet base64)

# استخدام مع PersistenceManager
from persistence import PersistenceManager
manager = PersistenceManager(
    storage_path="./secure_data",
    enable_encryption=True,
    encryption_key=key
)
```

---

## 5. `MetadataManager` — مدير البيانات الوصفية

>
> **الوصف:** يتتبع معلومات عن كل ملف محفوظ: الصيغة، الحجم، تواريخ الإنشاء والتعديل. يحفظ هذه المعلومات في ملف `.metadata.json` داخل مجلد التخزين ويُحمِّلها تلقائياً عند التشغيل. يُستخدم داخلياً بواسطة `PersistenceManager`.

### `__init__(storage_path, logger=None)`

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `storage_path` | `Path` | مسار مجلد التخزين |
| `logger` | `Logger \| None` | كائن logger اختياري |

---

### `update(key, format, size, **custom_fields)`

**الوصف:** يُنشئ أو يُحدِّث سجل البيانات الوصفية لمفتاح. عند الإنشاء يحفظ `created`، وعند التحديث يحدِّث فقط `modified`.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |
| `format` | `str` | اسم الصيغة (مثل `"json"`) |
| `size` | `int` | حجم الملف بالبايت |
| `**custom_fields` | — | حقول إضافية مخصصة |

**Return:** `None`

```python
from pathlib import Path
from persistence import MetadataManager

meta = MetadataManager(Path("./storage"))

meta.update("users", "json", 1024)
meta.update("config", "json.gz", 256, version="1.2", author="نظام")

info = meta.get("users")
print(info)
# {
#   'format': 'json',
#   'size': 1024,
#   'created': '2024-01-15T10:30:00',
#   'modified': '2024-01-15T10:30:00'
# }
```

---

### `get(key)`

**الوصف:** يُعيد البيانات الوصفية لمفتاح محدد.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |

**Return:** `Dict | None`

```python
info = meta.get("users")
if info:
    print(f"الصيغة: {info['format']}")
    print(f"الحجم: {info['size']} بايت")
    print(f"أُنشئ: {info['created']}")
    print(f"عُدِّل: {info['modified']}")

print(meta.get("غير موجود"))  # None
```

---

### `get_all()`

**الوصف:** يُعيد نسخة من قاموس جميع البيانات الوصفية المحفوظة.

**لا يأخذ معاملات.** | **Return:** `Dict[str, Dict]`

```python
all_meta = meta.get_all()
for key, info in all_meta.items():
    print(f"{key}: {info['size']} bytes — {info['format']}")
```

---

### `remove(key)`

**الوصف:** يحذف سجل البيانات الوصفية لمفتاح محدد ويحفظ التغيير فوراً.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |

**Return:** `bool` — `True` إذا وُجد وحُذف، `False` إذا لم يُوجد

```python
result = meta.remove("users")
print(result)  # True

result2 = meta.remove("غير موجود")
print(result2)  # False
```

---

### `clear()`

**الوصف:** يمسح جميع البيانات الوصفية ويُحدِّث الملف على القرص.

**لا يأخذ معاملات.** | **Return:** `None`

---

### دعم `in` و `len`

```python
print("users" in meta)  # True / False
print(len(meta))        # عدد المفاتيح المُسجَّلة
```

---

## 6. `BackupManager` — مدير النسخ الاحتياطية

>
> **الوصف:** يُنشئ نسخاً احتياطية للملفات قبل الكتابة عليها. يسمي النسخ بطابع زمني ويحذف القديمة تلقائياً عند تجاوز الحد المضبوط. يُفعَّل اختيارياً عبر `auto_backup=True` في `PersistenceManager`.

### `__init__(backup_path, backup_count=3, logger=None)`

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `backup_path` | `Path` | مطلوب | مسار مجلد تخزين النسخ الاحتياطية |
| `backup_count` | `int` | `3` | عدد النسخ المحتفظ بها لكل مفتاح |
| `logger` | `Logger \| None` | `None` | كائن logger اختياري |

---

### `create_backup(source_file, key)`

**الوصف:** يُنشئ نسخة احتياطية من ملف موجود بإضافة طابع زمني بصيغة `YYYYMMDD_HHMMSS` للاسم. يُنظِّف النسخ القديمة تلقائياً بعد الإنشاء.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `source_file` | `Path` | مسار الملف المراد نسخه احتياطياً |
| `key` | `str` | مفتاح التخزين (يُستخدم لتسمية النسخة) |

**Return:** `Path | None` — مسار النسخة الاحتياطية أو `None` إذا فشلت العملية أو الملف غير موجود

```python
from pathlib import Path
from persistence import BackupManager

# 📁 تحديد المسار الأساسي (مكان الملف الحالي)
#BASE_DIR = Path(__file__).parent # on python file

BASE_DIR = Path.cwd()            # on jupyter  

# 📁 مسار الملف الأصلي
source = BASE_DIR / "storage" / "users.json"

# 📁 إنشاء الملف لو مش موجود (للتجربة)
source.parent.mkdir(parents=True, exist_ok=True)
if not source.exists():
    source.write_text('{"name": "yousef", "age": 25}')

# 🗂️ إنشاء BackupManager
backup_mgr = BackupManager(
    backup_path=BASE_DIR / "backups",
    backup_count=5
)

# 🔄 إنشاء نسخة احتياطية
backup_path = backup_mgr.create_backup(source, "users")

# 🖨️ طباعة النتيجة
if backup_path:
    print(f"✅ تم الحفظ في: {backup_path}")
else:
    print("❌ فشل إنشاء النسخة الاحتياطية")
```

---

### `list_backups(key)`

**الوصف:** يُعيد قائمة بمسارات جميع النسخ الاحتياطية لمفتاح محدد مرتبةً زمنياً (الأقدم أولاً).

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |

**Return:** `list[Path]`

```python
backups = backup_mgr.list_backups("users")
for b in backups:
    print(b.name)
# users_20240113_090000.json
# users_20240114_120000.json
# users_20240115_103045.json
```

---

### `restore_backup(backup_file, destination)`

**الوصف:** يستعيد ملفاً من نسخة احتياطية بنسخه إلى المسار المطلوب.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `backup_file` | `Path` | مسار ملف النسخة الاحتياطية |
| `destination` | `Path` | المسار الوجهة للاستعادة |

**Return:** `bool` — `True` عند النجاح، `False` عند الفشل

```python
backups = backup_mgr.list_backups("users")
latest = backups[-1]

success = backup_mgr.restore_backup(
    backup_file=latest,
    destination=Path("./storage/users.json")
)
print(f"الاستعادة: {'نجحت' if success else 'فشلت'}")
```

---

### `get_latest_backup(key)`

**الوصف:** يُعيد أحدث نسخة احتياطية لمفتاح محدد مباشرةً دون الحاجة للمرور بـ `list_backups`.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |

**Return:** `Path | None`

```python
latest = backup_mgr.get_latest_backup("users")
if latest:
    print(f"آخر نسخة: {latest.name}")
else:
    print("لا توجد نسخ احتياطية")
```

---

### `clear_backups(key=None)`

**الوصف:** يحذف النسخ الاحتياطية. إذا مُرِّر `key` يحذف نسخ ذلك المفتاح فقط، وإذا تُرك `None` يحذف جميع النسخ.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `key` | `str \| None` | `None` | المفتاح المحدد أو `None` لحذف الكل |

**Return:** `None`

```python
# حذف نسخ مفتاح محدد
backup_mgr.clear_backups("users")

# حذف جميع النسخ الاحتياطية
backup_mgr.clear_backups()
```

---

## 7. `PersistenceManager` — المدير الرئيسي

>
> **الوصف:** الواجهة الرئيسية للنظام. يجمع جميع المكونات (التسلسل، الكاش، البيانات الوصفية، النسخ الاحتياطية) في واجهة برمجية موحَّدة وسهلة الاستخدام. جميع عملياته آمنة للخيوط المتعددة عبر `threading.RLock`.

### `__init__()` — المعاملات

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `storage_path` | `str` | `"./storage"` | مسار مجلد التخزين (يُنشَأ تلقائياً إذا لم يكن موجوداً) |
| `enable_logging` | `bool` | `True` | تفعيل رسائل السجل (logging) |
| `auto_backup` | `bool` | `False` | إنشاء نسخة احتياطية تلقائياً قبل كل كتابة |
| `backup_count` | `int` | `3` | عدد النسخ الاحتياطية المحتفظ بها لكل مفتاح |
| `compression_level` | `CompressionLevel` | `BALANCED` | مستوى الضغط الافتراضي |
| `enable_encryption` | `bool` | `False` | تفعيل التشفير لجميع البيانات |
| `encryption_key` | `str \| bytes \| None` | `None` | مفتاح Fernet (مطلوب إذا التشفير مفعَّل) |

```python
from persistence import PersistenceManager
from persistence import CompressionLevel
from persistence import generate_encryption_key

# ─── إعداد أساسي ───────────────────────────────────────────
manager = PersistenceManager(storage_path="./data")

# ─── مع نسخ احتياطية تلقائية ────────────────────────────
manager = PersistenceManager(
    storage_path="./data",
    auto_backup=True,
    backup_count=5
)

# ─── مع ضغط وتشفير ──────────────────────────────────────
key = generate_encryption_key()
manager = PersistenceManager(
    storage_path="./secure_data",
    auto_backup=True,
    compression_level=CompressionLevel.BEST,
    enable_encryption=True,
    encryption_key=key
)
```

---

## قسم: إدارة الكاش | Cache Management

---

### `enable_cache(max_size=100)`

**الوصف:** يُفعِّل الذاكرة المؤقتة LRU. بعد التفعيل كل `load()` يحفظ النتيجة في الكاش وكل `save()` يُحدِّثه، مما يجعل القراءات المتكررة فورية.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `max_size` | `int` | `100` | الحد الأقصى لعدد العناصر في الكاش |

**Return:** `None`

```python
manager = PersistenceManager(storage_path="./data")

manager.enable_cache(max_size=200)
# الآن القراءات المتكررة لنفس المفتاح تأتي من الذاكرة مباشرة
```

---

### `disable_cache()`

**الوصف:** يُعطِّل الكاش ويمسح جميع محتوياته. البيانات تُقرأ من القرص مباشرةً بعد التعطيل.

**لا يأخذ معاملات.** | **Return:** `None`

```python
manager.disable_cache()
```

---

## قسم: العمليات الأساسية | Core Operations

---

### `save(key, data, format, compress, custom_serializer)`

**الوصف:** يحفظ البيانات في ملف على القرص. يُنشئ نسخة احتياطية تلقائياً إذا كان `auto_backup=True` والملف موجود مسبقاً. يُحدِّث الكاش والبيانات الوصفية تلقائياً عند النجاح.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `key` | `str` | مطلوب | اسم المفتاح (يُصبح اسم الملف بدون امتداد) |
| `data` | `Any` | مطلوب | البيانات المراد حفظها |
| `format` | `StorageFormat \| str` | `StorageFormat.JSON` | صيغة التخزين. يقبل `"json"` أو `StorageFormat.JSON` |
| `compress` | `bool` | `False` | تفعيل الضغط — يُحوِّل JSON إلى COMPRESSED_JSON تلقائياً |
| `custom_serializer` | `Callable \| None` | `None` | دالة مخصصة تأخذ البيانات وتُعيد `bytes` أو `str` |

**Return:** `bool` — `True` عند النجاح، `False` عند الفشل

```python
manager = PersistenceManager(storage_path="./data")
manager.enable_cache(max_size=50)

# ─── حفظ بصيغة JSON (افتراضي) ──────────────────────────
users = {"alice": {"age": 28, "city": "الرياض"}, "bob": {"age": 35}}
ok = manager.save("users", users)
print(ok)  # True → يُنشئ ./data/users.json

# ─── حفظ مضغوط ──────────────────────────────────────────
big_data = list(range(100_000))
ok = manager.save("numbers", big_data, compress=True)
# يُنشئ ./data/numbers.json.gz

# ─── حفظ بـ Pickle ──────────────────────────────────────
from persistence import StorageFormat
import numpy as np

array = np.random.rand(1000, 1000)
ok = manager.save("matrix", array, format=StorageFormat.PICKLE)
# يُنشئ ./data/matrix.pickle

# ─── محسِّل مخصص ────────────────────────────────────────
import csv, io

def csv_serializer(data):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(data)
    return buf.getvalue().encode('utf-8')

rows = [["الاسم", "العمر"], ["أحمد", 30], ["سارة", 25]]
ok = manager.save("report", rows, custom_serializer=csv_serializer)
```

---

### `load(key, format, decompress, custom_deserializer, default)`

**الوصف:** يُحمِّل البيانات من القرص. يبحث في الكاش أولاً ويُعيد منه مباشرةً إذا وُجد. إذا لم يُوجد الملف يُعيد قيمة `default`.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `key` | `str` | مطلوب | مفتاح التخزين |
| `format` | `StorageFormat \| str` | `StorageFormat.JSON` | الصيغة المستخدمة عند الحفظ |
| `decompress` | `bool` | `False` | إجبار فك الضغط (يُستخدم مع الصيغ المضغوطة) |
| `custom_deserializer` | `Callable \| None` | `None` | دالة مخصصة تأخذ `bytes` وتُعيد البيانات |
| `default` | `Any` | `None` | القيمة المُعادة إذا لم يُوجد المفتاح |

**Return:** `Any`

---
```python
# ─── تحميل بصيغة JSON (افتراضي) ─────────────────────────
users = manager.load("users")
print(users)  # {'alice': {'age': 28, ...}, 'bob': {...}}

# ─── تحميل مضغوط ─────────────────────────────────────────
numbers = manager.load("numbers", format=StorageFormat.COMPRESSED_JSON)

# ─── قيمة افتراضية إذا لم يُوجد المفتاح ─────────────────
config = manager.load("config", default={"theme": "light", "lang": "ar"})
print(config)  # {'theme': 'light', 'lang': 'ar'} إذا لم يُوجد config.json

# ─── محسِّل فك مخصص ──────────────────────────────────────
import csv, io

def csv_deserializer(data: bytes):
    buf = io.StringIO(data.decode('utf-8'))
    return list(csv.reader(buf))

rows = manager.load("report", custom_deserializer=csv_deserializer)
print(rows)  # [['الاسم', 'العمر'], ['أحمد', '30'], ...]
```

---

### `exists(key, format)`

**الوصف:** يتحقق من وجود ملف بالمفتاح والصيغة المحددة على القرص.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `key` | `str` | مطلوب | مفتاح التخزين |
| `format` | `StorageFormat \| str` | `StorageFormat.JSON` | الصيغة المستخدمة |

**Return:** `bool`

```python
# التحقق من وجود users.json
print(manager.exists("users"))                              # True
print(manager.exists("users", StorageFormat.JSON))         # True
print(manager.exists("users", StorageFormat.PICKLE))       # False
print(manager.exists("missing_key"))                       # False

# مثال شائع: تحميل أو إنشاء
if not manager.exists("settings"):
    manager.save("settings", {"lang": "ar", "theme": "dark"})

settings = manager.load("settings")
```

---

### `delete(key, format)`

**الوصف:** يحذف ملف من القرص ويزيله من الكاش والبيانات الوصفية.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `key` | `str` | مطلوب | مفتاح التخزين |
| `format` | `StorageFormat \| str` | `StorageFormat.JSON` | صيغة الملف المراد حذفه |

**Return:** `bool` — `True` إذا وُجد وحُذف، `False` إذا لم يُوجد

```python
result = manager.delete("users")
print(result)   # True

result2 = manager.delete("غير موجود")
print(result2)  # False

# حذف ملف Pickle
result3 = manager.delete("matrix", StorageFormat.PICKLE)
```

---

## قسم: عمليات الاستعلام | Query Operations

---

### `list_keys(pattern="*")`

**الوصف:** يُعيد قائمة مرتبة بجميع المفاتيح (أسماء الملفات بدون امتداد) في مجلد التخزين. يدعم أنماط Glob للتصفية.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `pattern` | `str` | `"*"` | نمط Glob للتصفية |

**Return:** `List[str]`

```python
manager.save("users", {})
manager.save("config", {})
manager.save("cache_users", {})

# كل المفاتيح
print(manager.list_keys())
# ['cache_users', 'config', 'users']

# المفاتيح التي تبدأ بـ "cache"
print(manager.list_keys("cache_*"))
# ['cache_users']

# عدد الملفات
print(f"إجمالي الملفات: {len(manager)}")  # 3
```

---

### `get_metadata(key)`

**الوصف:** يُعيد البيانات الوصفية لمفتاح محدد: الصيغة، الحجم، تاريخ الإنشاء، تاريخ آخر تعديل.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح التخزين |

**Return:** `Dict | None`

```python
meta = manager.get_metadata("users")
if meta:
    print(f"الصيغة:    {meta['format']}")     # json
    print(f"الحجم:     {meta['size']} بايت")
    print(f"أُنشئ:     {meta['created']}")
    print(f"عُدِّل:     {meta['modified']}")
```

---

### `get_all_metadata()`

**الوصف:** يُعيد قاموساً بالبيانات الوصفية لجميع المفاتيح المحفوظة.

**لا يأخذ معاملات.** | **Return:** `Dict[str, Dict]`

```python
all_meta = manager.get_all_metadata()
for key, info in all_meta.items():
    print(f"{key}: {info['size']} bytes، آخر تعديل: {info['modified']}")
```

---

## قسم: معلومات الحجم | Size Information

---

### `get_size(key, format)`

**الوصف:** يُعيد حجم ملف محدد بالبايت.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `key` | `str` | مطلوب | مفتاح التخزين |
| `format` | `StorageFormat \| str` | `StorageFormat.JSON` | صيغة الملف |

**Return:** `int` — الحجم بالبايت، أو `0` إذا لم يُوجد الملف

```python
size = manager.get_size("users")
print(f"الحجم: {size} بايت")         # مثال: 245 بايت

size_gz = manager.get_size("numbers", StorageFormat.COMPRESSED_JSON)
print(f"مضغوط: {size_gz} بايت")

# ملف غير موجود
print(manager.get_size("missing"))    # 0
```

---

### `get_total_size()`

**الوصف:** يُعيد الحجم الكلي لجميع الملفات في مجلد التخزين بالبايت.

**لا يأخذ معاملات.** | **Return:** `int`

```python
total = manager.get_total_size()
print(f"إجمالي التخزين: {total} بايت")
print(f"بالكيلوبايت: {total / 1024:.2f} KB")
print(f"بالميغابايت: {total / (1024**2):.2f} MB")
```

---

## قسم: العمليات الجماعية | Bulk Operations

---

### `clear_all(confirm=False)`

**الوصف:** يحذف جميع الملفات في مجلد التخزين ويمسح الكاش والبيانات الوصفية. **تطلب `confirm=True` صريحة للحماية من الحذف العرضي**.

**المعاملات:**

| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `confirm` | `bool` | `False` | يجب تمرير `True` لتأكيد الحذف. أي قيمة أخرى تُلغي العملية |

**Return:** `None`

---
```python
# بدون تأكيد — لا يفعل شيئاً (يسجل تحذيراً)
manager.clear_all()

# مع تأكيد — يحذف كل شيء
manager.clear_all(confirm=True)
print(len(manager))  # 0
```

---

### `export_all(export_path)`

**الوصف:** يصدِّر جميع البيانات المحفوظة إلى ملف JSON واحد. يُجرِّب جميع الصيغ لكل مفتاح ويأخذ أول صيغة ناجحة. مفيد للنسخ الاحتياطية الشاملة أو نقل البيانات.

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `export_path` | `str` | مسار ملف التصدير المنشود |

**Return:** `bool` — `True` عند النجاح، `False` عند الفشل

```python
ok = manager.export_all("./backup_2024.json")
print(ok)  # True

# محتوى الملف المُصدَّر:
# {
#   "users": {"alice": {...}, "bob": {...}},
#   "config": {"theme": "dark"},
#   "settings": {...}
# }
```

---

### `import_all(import_path)`

**الوصف:** يستورد بيانات من ملف JSON تم إنشاؤه بـ `export_all()`. يحفظ كل عنصر بصيغة JSON الافتراضية. يُدمَج مع البيانات الموجودة (لا يمسحها).

**المعاملات:**

| المعامل | النوع | الوصف |
|---------|------|-------|
| `import_path` | `str` | مسار ملف JSON المراد استيراده |

**المُعيدات:** `bool` — `True` عند النجاح، `False` عند الفشل

```python
ok = manager.import_all("./backup_2024.json")
print(ok)  # True

# التحقق بعد الاستيراد
print(manager.list_keys())  # جميع المفاتيح المستوردة
```

---

## قسم: الإحصائيات | Statistics

---

### `get_stats()`

**الوصف:** يُعيد قاموساً شاملاً بإحصائيات الاستخدام: عمليات الحفظ، التحميل، الحذف، الأخطاء، وإحصائيات الكاش.

**لا يأخذ معاملات.** | **المُعيدات:** `dict`

```python
stats = manager.get_stats()
print(stats)
# {
#   'saves': 15,              ← عمليات حفظ ناجحة
#   'loads': 42,              ← عمليات تحميل ناجحة
#   'deletes': 3,             ← عمليات حذف ناجحة
#   'errors': 1,              ← إجمالي الأخطاء
#   'total_files': 12,        ← عدد الملفات الحالي
#   'total_size_bytes': 8192, ← الحجم الكلي
#   'cache': {
#       'size': 8,
#       'max_size': 100,
#       'usage_pct': 8.0
#   }
# }
```

---

## قسم: دعم المعاملات | Transaction Support

---

### `transaction()` — Context Manager

**الوصف:** مدير سياق يُلف عمليات الحفظ في معاملة واحدة. **إذا حدث أي خطأ داخل الـ `with` block يُعيد النظام جميع الملفات إلى حالتها قبل المعاملة** (Rollback تلقائي). يُعيد رفع الاستثناء الأصلي بعد الـ Rollback.

**لا يأخذ معاملات.**

**Return:** `PersistenceManager` (نفس الكائن داخل الـ `with`)

```python
manager = PersistenceManager(storage_path="./data")

# ─── مثال: معاملة ناجحة ──────────────────────────────────
with manager.transaction():
    manager.save("orders", {"order_1": 100, "order_2": 200})
    manager.save("inventory", {"item_a": 50, "item_b": 30})
# كلا الحفظين اكتملا بنجاح

# ─── مثال: معاملة مع خطأ → Rollback ─────────────────────
manager.save("balance", {"amount": 1000})

try:
    with manager.transaction():
        manager.save("balance", {"amount": 500})  # تعديل الرصيد
        manager.save("log", {"action": "deduct"}) # تسجيل العملية
        raise ValueError("خطأ في المعالجة!")      # خطأ مفتعل
except ValueError:
    pass

# بعد الخطأ: balance عاد إلى 1000 تلقائياً
balance = manager.load("balance")
print(balance["amount"])  # 1000 ← لم يتغير!
```

---

## قسم: الدوال الخاصة | Special Methods

---

### `__len__()`

**الوصف:** يُعيد عدد الملفات المحفوظة حالياً في مجلد التخزين.

```python
print(len(manager))  # مثال: 5
```

---

### `__repr__()`

**الوصف:** يُعيد تمثيلاً نصياً للكائن يشمل المسار وعدد الملفات وإجمالي الحجم.

```python
print(repr(manager))
# PersistenceManager(path='data', files=5, size=8192 bytes)
```

---

## 💡 مثال شامل

--
```python

from persistence import PersistenceManager
from persistence import StorageFormat, CompressionLevel
from persistence import generate_encryption_key


# ══════════════════════════════════════════════════════════════
#  1. إعداد المدير مع جميع المميزات
# ══════════════════════════════════════════════════════════════
print("─" * 55)
print("1. إعداد المدير | Setup")
print("─" * 55)

enc_key = generate_encryption_key()

manager = PersistenceManager(
    storage_path="./app_data",
    enable_logging=True,
    auto_backup=True,
    backup_count=3,
    compression_level=CompressionLevel.BALANCED,
    enable_encryption=False   # True لتشفير البيانات
)

manager.enable_cache(max_size=100)
print(repr(manager))


# ══════════════════════════════════════════════════════════════
#  2. الحفظ والتحميل الأساسي
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("2. الحفظ والتحميل | Save & Load")
print("─" * 55)

# حفظ بيانات المستخدمين (JSON)
users = {
    "u001": {"name": "أحمد", "age": 30, "city": "الرياض"},
    "u002": {"name": "سارة", "age": 25, "city": "جدة"},
    "u003": {"name": "محمد", "age": 35, "city": "الدمام"},
}
ok = manager.save("users", users)
print(f"حفظ المستخدمين: {'✅' if ok else '❌'}")

# حفظ الإعدادات (JSON)
config = {"theme": "dark", "lang": "ar", "notifications": True}
manager.save("config", config)

# حفظ قائمة أرقام كبيرة (مضغوط)
big_list = list(range(50_000))
ok = manager.save("numbers", big_list, compress=True)
print(f"حفظ مضغوط: {'✅' if ok else '❌'}")

# تحميل البيانات
loaded_users = manager.load("users")
print(f"عدد المستخدمين: {len(loaded_users)}")  # 3

# تحميل الأرقام المضغوطة
loaded_numbers = manager.load("numbers", format=StorageFormat.COMPRESSED_JSON)
print(f"عدد الأرقام: {len(loaded_numbers)}")   # 50000

# قيمة افتراضية
profile = manager.load("profile_missing", default={"guest": True})
print(f"مستخدم افتراضي: {profile}")  # {'guest': True}


# ══════════════════════════════════════════════════════════════
#  3. التحقق والحذف
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("3. التحقق والحذف | Exists & Delete")
print("─" * 55)

print(f"users موجود:   {manager.exists('users')}")     # True
print(f"missing موجود: {manager.exists('missing')}")   # False

manager.save("temp_data", {"x": 1})
result = manager.delete("temp_data")
print(f"حذف temp_data: {'✅' if result else '❌'}")     # True
print(f"بعد الحذف:     {manager.exists('temp_data')}") # False


# ══════════════════════════════════════════════════════════════
#  4. الاستعلام والبيانات الوصفية
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("4. الاستعلام | Query & Metadata")
print("─" * 55)

keys = manager.list_keys()
print(f"جميع المفاتيح: {keys}")

meta = manager.get_metadata("users")
if meta:
    print(f"users.json — الحجم: {meta['size']} بايت")
    print(f"             أُنشئ: {meta['created']}")

size = manager.get_size("users")
total = manager.get_total_size()
print(f"حجم users: {size} بايت")
print(f"الحجم الكلي: {total} بايت ({total/1024:.1f} KB)")


# ══════════════════════════════════════════════════════════════
#  5. المعاملات (Transactions)
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("5. المعاملات | Transactions")
print("─" * 55)

# معاملة ناجحة
manager.save("balance", {"amount": 1000, "currency": "SAR"})

with manager.transaction():
    manager.save("balance", {"amount": 800, "currency": "SAR"})
    manager.save("tx_log", [{"type": "debit", "amount": 200}])

print(f"رصيد بعد المعاملة: {manager.load('balance')['amount']}")  # 800

# معاملة مع rollback
try:
    with manager.transaction():
        manager.save("balance", {"amount": 500, "currency": "SAR"})
        raise RuntimeError("فشل في المعالجة!")
except RuntimeError:
    pass

print(f"رصيد بعد الفشل: {manager.load('balance')['amount']}")  # 800 ← لم يتغير!


# ══════════════════════════════════════════════════════════════
#  6. التصدير والاستيراد
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("6. التصدير والاستيراد | Export & Import")
print("─" * 55)

ok = manager.export_all("./full_backup.json")
print(f"تصدير: {'✅' if ok else '❌'}")

# محاكاة الاستيراد في مدير جديد
new_manager = PersistenceManager("./restored_data")
ok = new_manager.import_all("./full_backup.json")
print(f"استيراد: {'✅' if ok else '❌'}")
print(f"مفاتيح مستوردة: {new_manager.list_keys()}")


# ══════════════════════════════════════════════════════════════
#  7. الإحصائيات
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("7. الإحصائيات | Statistics")
print("─" * 55)

stats = manager.get_stats()
print(f"عمليات الحفظ:   {stats['saves']}")
print(f"عمليات التحميل: {stats['loads']}")
print(f"عمليات الحذف:   {stats['deletes']}")
print(f"الأخطاء:        {stats['errors']}")
print(f"إجمالي الملفات: {stats['total_files']}")
print(f"الحجم الكلي:    {stats['total_size_bytes']} بايت")
print(f"الكاش: {stats['cache']['size']}/{stats['cache']['max_size']} "
      f"({stats['cache']['usage_pct']}%)")


# ══════════════════════════════════════════════════════════════
#  8. مع تشفير (Encryption)
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("8. مع تشفير | With Encryption")
print("─" * 55)

enc_key = generate_encryption_key()
print(f"مفتاح التشفير: {enc_key[:20]}...  (احفظه بأمان!)")

secure_manager = PersistenceManager(
    storage_path="./secure_data",
    enable_encryption=True,
    encryption_key=enc_key
)

secure_manager.save("secrets", {
    "api_key": "sk-xxxxxxxxxxxxx",
    "db_password": "p@ssw0rd!123"
})

# لن يُمكن قراءة الملف بدون المفتاح
secrets = secure_manager.load("secrets")
print(f"السر المُسترجَع: {secrets['api_key'][:6]}...")  # sk-xxx...


# ══════════════════════════════════════════════════════════════
#  9. Pickle لأنواع Python المعقدة
# ══════════════════════════════════════════════════════════════
print("\n" + "─" * 55)
print("9. Pickle للأنواع المعقدة | Complex Python Types")
print("─" * 55)

from datetime import datetime
from collections import Counter

complex_data = {
    "timestamp": datetime.now(),
    "word_count": Counter(["python", "ai", "python", "data", "ai", "python"]),
    "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    "mixed": (1, "two", 3.0, None, True)
}

manager.save("complex", complex_data, format=StorageFormat.PICKLE)
restored = manager.load("complex", format=StorageFormat.PICKLE)

print(f"Timestamp: {restored['timestamp']}")
print(f"Word count: {dict(restored['word_count'])}")
# {'python': 3, 'ai': 2, 'data': 1}

```

---

## 📊 مرجع سريع

### جدول الدوال الرئيسية — `PersistenceManager`

| الدالة | الوصف | المُعيد |
|--------|-------|---------|
| `save(key, data, format, compress)` | حفظ بيانات | `bool` |
| `load(key, format, default)` | تحميل بيانات | `Any` |
| `exists(key, format)` | التحقق من الوجود | `bool` |
| `delete(key, format)` | حذف ملف | `bool` |
| `list_keys(pattern)` | قائمة المفاتيح | `List[str]` |
| `get_metadata(key)` | بيانات وصفية لمفتاح | `Dict \| None` |
| `get_all_metadata()` | جميع البيانات الوصفية | `Dict` |
| `get_size(key, format)` | حجم ملف بالبايت | `int` |
| `get_total_size()` | الحجم الكلي | `int` |
| `get_stats()` | إحصائيات الاستخدام | `dict` |
| `clear_all(confirm)` | حذف كل الملفات | `None` |
| `export_all(path)` | تصدير كل البيانات لـ JSON | `bool` |
| `import_all(path)` | استيراد من ملف JSON | `bool` |
| `enable_cache(max_size)` | تفعيل الكاش | `None` |
| `disable_cache()` | تعطيل الكاش | `None` |
| `transaction()` | معاملة مع Rollback | Context Manager |
| `__len__()` | عدد الملفات | `int` |

### جدول الصيغ وحالات الاستخدام

| الصيغة | متى تستخدمها؟ | ملاحظة |
|--------|-------------|--------|
| `JSON` | بيانات بسيطة، قراءة بشرية مطلوبة | الافتراضي |
| `COMPRESSED_JSON` | JSON بيانات كبيرة (> 10KB) | يوفر 60–80% حجماً |
| `PICKLE` | كائنات Python معقدة (datetime, numpy...) | ثنائي، أسرع |
| `COMPRESSED_PICKLE` | كائنات Python معقدة وكبيرة | أفضل توفير |
| `TEXT` | نصوص خام، CSV، HTML... | نص عادي فقط |

### متى تستخدم كل مستوى ضغط؟

```
البيانات صغيرة (< 1KB)    → NONE     (الضغط لا يستحق)
سرعة التخزين أهم          → FAST     (ضغط سريع)
توازن (الاستخدام العام)   → BALANCED (الافتراضي)
المساحة المهمة             → BEST     (أقصى ضغط)
```

### دليل اختيار الصيغة

```
هل البيانات كائنات Python معقدة (datetime, set, class...)؟
    └── نعم ──► StorageFormat.PICKLE

هل حجم البيانات > 10KB؟
    └── نعم ──► compress=True  (يُحوِّل تلقائياً للمضغوط)

هل تحتاج قراءة الملف بمحرر نصوص؟
    └── نعم ──► StorageFormat.JSON  أو  StorageFormat.TEXT

الحالة العامة (قاموس، قائمة، أرقام)؟
    └── ──────► StorageFormat.JSON  (الافتراضي)
```

---

> **ملاحظة الأمان:** عند استخدام التشفير احفظ `encryption_key` في مكان آمن منفصل عن البيانات. فقدان المفتاح يعني فقدان البيانات بشكل نهائي.
>
> **ملاحظة الأداء:** فعِّل الكاش `enable_cache()` دائماً في التطبيقات التي تقرأ نفس البيانات بتكرار لتجنب I/O غير ضروري على القرص.
