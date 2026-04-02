

## نظرة عامة

نظام **ذاكرة تخزين مؤقت متعدد المستويات** (Multi-Level Cache) هو نظام يحاكي طريقة عمل ذاكرة التخزين المؤقت في المعالجات الحديثة. يتكون من **3 مستويات** لتخزين البيانات بسرعات وأحجام مختلفة:

| المستوى | النوع | السرعة | الحجم |
|---------|-------|--------|-------|
| **L1** | ذاكرة RAM سريعة | أسرع (~100ns) | الأصغر (10MB افتراضي) |
| **L2** | ذاكرة RAM متوسطة | سريعة (~1000ns) | متوسط (100MB افتراضي) |
| **L3** | قرص صلب (Disk) | أبطأ (~10000ns) | الأكبر (1000MB افتراضي) |

### آلية العمل:
- عند البحث عن بيانات، يبحث النظام أولاً في L1، ثم L2، ثم L3.
- إذا وُجدت البيانات في L3، يتم **ترقيتها (Promotion)** تلقائياً إلى L2.
- إذا أصبحت البيانات في L2 "ساخنة" (كثيرة الطلب)، تُرقّى إلى L1.
- عند امتلاء أي مستوى، يتم **إخلاء (Eviction)** البيانات الأقل أهمية للمستوى الأدنى.

---



---

## التثبيت والاستخدام السريع

```python
from cache import MultiLevelCache
from cache import CacheStrategy
from cache import CacheConfig

# إنشاء كاش بسيط
cache = MultiLevelCache()

# تخزين قيمة
cache.set("user:123", {"name": "Ahmed", "age": 30})

# استرجاع قيمة
user = cache.get("user:123")
print(user)  # {"name": "Ahmed", "age": 30}

# حذف قيمة
cache.delete("user:123")
```

---

## توثيق الوحدات

---

## 1. `CacheConfig` — إعدادات الكاش

>
> **الوصف:** كلاس إعدادات يحتوي على جميع القيم القابلة للتخصيص في النظام. يُستخدم لتحديد الحدود القصوى للعناصر والأحجام والإعدادات العامة.

### الخصائص (Attributes)

| الخاصية | النوع | القيمة الافتراضية | الوصف |
|---------|------|------------------|-------|
| `l1_max_items` | `int` | `100` | الحد الأقصى لعدد العناصر في L1 |
| `l2_max_items` | `int` | `1000` | الحد الأقصى لعدد العناصر في L2 |
| `l3_max_items` | `int` | `10000` | الحد الأقصى لعدد العناصر في L3 |
| `l1_max_size_mb` | `float` | `10.0` | الحد الأقصى لحجم L1 بالميغابايت |
| `l2_max_size_mb` | `float` | `100.0` | الحد الأقصى لحجم L2 بالميغابايت |
| `l3_max_size_mb` | `float` | `1000.0` | الحد الأقصى لحجم L3 بالميغابايت |
| `default_ttl` | `float \| None` | `None` | مدة الصلاحية الافتراضية بالثواني (None = لا تنتهي) |
| `cache_dir` | `str` | `"./cache_storage"` | مجلد تخزين ملفات L3 |
| `enable_stats` | `bool` | `True` | تفعيل تتبع الإحصائيات |
| `auto_cleanup_interval` | `int` | `3600` | فترة التنظيف التلقائي بالثواني |
| `l2_to_l1_hits` | `int` | `10` | عدد الوصولات في L2 قبل الترقية إلى L1 |
| `size_bytes` | `int` | `1024` | الحجم الافتراضي للعنصر بالبايتات |

### الدوال

---

#### `__post_init__()`
**الوصف:** تُستدعى تلقائياً بعد إنشاء الكائن للتحقق من صحة الإعدادات.

```python
# لا تحتاج لاستدعائها يدوياً، تعمل تلقائياً عند الإنشاء
config = CacheConfig(l1_max_items=50)  # يتم التحقق تلقائياً
```

---

#### `from_env()` — Class Method
**الوصف:** إنشاء إعدادات من متغيرات البيئة (Environment Variables). مفيد في بيئات الإنتاج والـ Docker.

**يقرأ متغيرات البيئة:**
- `CACHE_L1_MAX_ITEMS`
- `CACHE_L2_MAX_ITEMS`
- `CACHE_L3_MAX_ITEMS`
- `CACHE_DIR`
- `CACHE_DEFAULT_TTL`

**Return (Returns):** `CacheConfig`

```python
import os

# تعيين متغيرات البيئة
os.environ['CACHE_L1_MAX_ITEMS'] = '200'
os.environ['CACHE_DIR'] = '/tmp/my_cache'

# إنشاء الإعدادات من البيئة
config = CacheConfig.from_env()
print(config.l1_max_items)  # 200
print(config.cache_dir)     # /tmp/my_cache
```

---

#### `to_dict()`
**الوصف:** تحويل الإعدادات إلى قاموس (dictionary). مفيد لحفظ الإعدادات أو طباعتها.

**(Returns):** `dict`

```python
config = CacheConfig()
settings = config.to_dict()
print(settings)
# {
#   'l1_max_items': 100,
#   'l2_max_items': 1000,
#   'l3_max_items': 10000,
#   'l1_max_size_mb': 10.0,
#   ...
# }
```

---

### مثال كامل على CacheConfig

```python
from cache import CacheConfig

# إنشاء إعدادات مخصصة
config = CacheConfig(
    l1_max_items=200,          # L1 يتسع لـ 200 عنصر
    l2_max_items=2000,         # L2 يتسع لـ 2000 عنصر
    l3_max_items=20000,        # L3 يتسع لـ 20000 عنصر
    l1_max_size_mb=20.0,       # حجم L1 لا يتجاوز 20MB
    default_ttl=3600.0,        # العناصر تنتهي صلاحيتها بعد ساعة
    cache_dir="/var/cache/app",
    auto_cleanup_interval=1800 # تنظيف كل 30 دقيقة
)
```

---

## 2. `CacheStrategy` — استراتيجيات الإخلاء


>
> **الوصف:** `Enum` يحدد استراتيجية اختيار العنصر المراد إزالته عند امتلاء الكاش.

### القيم المتاحة

| القيمة | الاسم | الوصف |
|--------|-------|-------|
| `CacheStrategy.LRU` | Least Recently Used | يُزيل العنصر الأقل استخداماً حديثاً |
| `CacheStrategy.LFU` | Least Frequently Used | يُزيل العنصر الأقل استخداماً كلياً |
| `CacheStrategy.FIFO` | First In First Out | يُزيل العنصر الأقدم دخولاً |
| `CacheStrategy.TTL` | Time To Live | يُزيل العناصر منتهية الصلاحية أولاً |
| `CacheStrategy.ADAPTIVE` | Adaptive | يحسب نقاط لكل عنصر ويُزيل الأقل قيمة |

```python
from cache import CacheStrategy

# الاستخدام عند إنشاء الكاش
cache = MultiLevelCache(strategy=CacheStrategy.LFU)
```

---

## 3. `CacheEntry` — عنصر الكاش


>
> **الوصف:** كلاس يمثل عنصراً واحداً مخزناً في الكاش مع جميع بياناته الوصفية (metadata) كوقت الإنشاء وعدد الوصولات والحجم.

### الخصائص (Attributes)

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | المفتاح الفريد للعنصر |
| `value` | `Any` | القيمة المخزنة |
| `created_at` | `float` | وقت الإنشاء (Unix timestamp) |
| `last_access` | `float` | وقت آخر وصول |
| `hits` | `int` | عدد مرات الوصول |
| `ttl` | `float \| None` | مدة الصلاحية بالثواني |
| `size_bytes` | `int` | الحجم التقريبي بالبايتات |

### الدوال

---

#### `increment_hits()`
**الوصف:** تزيد عداد الوصول بمقدار 1 وتُحدِّث وقت آخر وصول. تُستدعى تلقائياً في كل مرة يتم الوصول للعنصر.

```python
entry = CacheEntry(key="user:1", value={"name": "Sara"})
print(entry.hits)       # 0
entry.increment_hits()
print(entry.hits)       # 1
```

---

#### `is_expired()`
**الوصف:** يتحقق إذا كان العنصر قد انتهت صلاحيته بناءً على `ttl`. إذا لم يكن هناك `ttl`، يُعيد دائماً `False`.

**(Returns):** `bool`

```python
import time
entry = CacheEntry(key="token", value="abc123", ttl=5.0)  # تنتهي بعد 5 ثواني

print(entry.is_expired())  # False
time.sleep(6)
print(entry.is_expired())  # True
```

---

#### `age()`
**الوصف:** يُعيد عمر العنصر بالثواني منذ إنشائه.

**(Returns):** `float`

```python
entry = CacheEntry(key="x", value=42)
time.sleep(2)
print(entry.age())  # ~2.0
```

---

#### `idle_time()`
**الوصف:** يُعيد الوقت منذ آخر وصول للعنصر بالثواني. مفيد في استراتيجية LRU.

**(Returns):** `float`

```python
entry = CacheEntry(key="y", value="data")
time.sleep(3)
print(entry.idle_time())   # ~3.0

entry.increment_hits()     # تحديث وقت الوصول
print(entry.idle_time())   # ~0.0
```

---

#### `get_stats()`
**الوصف:** يُعيد قاموساً بجميع إحصائيات العنصر.

**(Returns):** `dict`

```python
entry = CacheEntry(key="session:99", value={"token": "xyz"}, ttl=300.0)
stats = entry.get_stats()
print(stats)
# {
#   'key': 'session:99',
#   'hits': 0,
#   'age_seconds': 0.001,
#   'idle_seconds': 0.001,
#   'size_bytes': 48,
#   'is_expired': False,
#   'ttl': 300.0
# }
```

---

#### `_calculate_size()`
**الوصف:** دالة داخلية تحسب الحجم الفعلي للقيمة المخزنة باستخدام `pickle`. تُستدعى تلقائياً عند الإنشاء.

> **ملاحظة:** هذه دالة داخلية (private)، لا تحتاج لاستدعائها مباشرة.

---

## 4. `CacheMetrics` — مقاييس الأداء

>
> **الوصف:** كلاس لتتبع وقياس أداء الكاش. يحتفظ بعدادات للإصابات (hits) والإخفاقات (misses) والعمليات المختلفة في كل مستوى.

### الخصائص (Attributes)

| الخاصية | النوع | الوصف |
|---------|------|-------|
| `l1_hits` | `int` | عدد الإصابات في L1 |
| `l2_hits` | `int` | عدد الإصابات في L2 |
| `l3_hits` | `int` | عدد الإصابات في L3 |
| `l1_misses` | `int` | عدد الإخفاقات في L1 |
| `l2_misses` | `int` | عدد الإخفاقات في L2 |
| `l3_misses` | `int` | عدد الإخفاقات في L3 |
| `sets` | `int` | إجمالي عمليات التخزين |
| `evictions` | `int` | إجمالي عمليات الإخلاء |
| `promotions` | `int` | إجمالي عمليات الترقية |
| `expirations` | `int` | إجمالي العناصر منتهية الصلاحية |

### الدوال

---

#### `record_get(level, hit)`
**الوصف:** تسجيل عملية قراءة (get). تُستدعى تلقائياً من `MultiLevelCache` في كل عملية بحث.

**المعاملات (Parameters):**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `level` | `int` | مستوى الكاش (1، 2، أو 3) |
| `hit` | `bool` | هل وُجدت البيانات؟ (`True` = إصابة، `False` = إخفاق) |

```python
metrics = CacheMetrics()
metrics.record_get(level=1, hit=True)   # إصابة في L1
metrics.record_get(level=2, hit=False)  # إخفاق في L2
print(metrics.l1_hits)    # 1
print(metrics.l2_misses)  # 1
```

---

#### `record_set()`
**الوصف:** تسجيل عملية تخزين (set). تُستدعى تلقائياً عند كل استدعاء لـ `cache.set()`.

```python
metrics = CacheMetrics()
metrics.record_set()
metrics.record_set()
print(metrics.sets)  # 2
```

---

#### `record_eviction()`
**الوصف:** تسجيل عملية إخلاء عند امتلاء الكاش وإزالة عنصر منه.

```python
metrics = CacheMetrics()
metrics.record_eviction()
print(metrics.evictions)  # 1
```

---

#### `record_promotion()`
**الوصف:** تسجيل عملية ترقية عنصر من مستوى أدنى إلى مستوى أعلى (مثلاً من L2 إلى L1).

```python
metrics = CacheMetrics()
metrics.record_promotion()
print(metrics.promotions)  # 1
```

---

#### `record_expiration()`
**الوصف:** تسجيل انتهاء صلاحية عنصر وإزالته من الكاش.

```python
metrics = CacheMetrics()
metrics.record_expiration()
print(metrics.expirations)  # 1
```

---

#### `get_hit_rate(level=None)`
**الوصف:** حساب معدل الإصابة (Hit Rate). يُعيد نسبة مئوية تُعبّر عن كفاءة الكاش.

**المعاملات (Parameters):**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `level` | `int \| None` | المستوى (1، 2، 3) أو `None` للمعدل الإجمالي |

**(Returns):** `float` — قيمة بين 0.0 و 1.0

```python
metrics = CacheMetrics()
metrics.record_get(1, hit=True)
metrics.record_get(1, hit=True)
metrics.record_get(1, hit=False)

print(metrics.get_hit_rate(level=1))  # 0.6667 (~66.7%)
print(metrics.get_hit_rate())          # معدل إجمالي
```

---

#### `get_stats()`
**الوصف:** يُعيد قاموساً شاملاً بجميع مقاييس الأداء.

**(Returns):** `dict`

```python
metrics = CacheMetrics()
# ... بعض العمليات ...
stats = metrics.get_stats()
print(stats)
# {
#   'l1_hits': 10, 'l2_hits': 3, 'l3_hits': 1,
#   'total_hits': 14,
#   'l1_misses': 2, 'l2_misses': 2, 'l3_misses': 2,
#   'total_misses': 6,
#   'l1_hit_rate': 0.833,
#   'overall_hit_rate': 0.7,
#   'sets': 20, 'evictions': 2, 'promotions': 5, 'expirations': 1
# }
```

---

#### `reset()`
**الوصف:** إعادة تعيين جميع العدادات إلى الصفر.

```python
metrics = CacheMetrics()
metrics.record_set()
metrics.record_get(1, True)
print(metrics.sets)   # 1

metrics.reset()
print(metrics.sets)   # 0
```

---

## 5. `MultiLevelCache` — الكاش الرئيسي


>
> **الوصف:** الكلاس الرئيسي الذي يدير نظام الكاش بالكامل. يجمع بين جميع المكونات الأخرى ويوفر واجهة برمجية (API) نظيفة وسهلة الاستخدام.

### `__init__()` — إنشاء الكاش

**الوصف:** تهيئة نظام الكاش متعدد المستويات.

**المعاملات (Parameters):**
| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `l1_max_items` | `int \| None` | `None` | الحد الأقصى لعدد عناصر L1 (يتجاوز الإعدادات) |
| `l2_max_items` | `int \| None` | `None` | الحد الأقصى لعدد عناصر L2 (يتجاوز الإعدادات) |
| `l3_max_items` | `int \| None` | `None` | الحد الأقصى لعدد عناصر L3 (يتجاوز الإعدادات) |
| `strategy` | `CacheStrategy` | `CacheStrategy.LRU` | استراتيجية الإخلاء |
| `config` | `CacheConfig \| None` | `None` | كائن الإعدادات (إذا لم يُحدَّد يُستخدم الافتراضي) |

```python
from cache import MultiLevelCache
from cache import CacheStrategy
from cache import CacheConfig

# الطريقة 1: إنشاء بسيط بالإعدادات الافتراضية
cache = MultiLevelCache()

# الطريقة 2: تحديد الحدود مباشرة
cache = MultiLevelCache(l1_max_items=50, l2_max_items=500)

# الطريقة 3: استخدام إعدادات مخصصة
config = CacheConfig(default_ttl=600, cache_dir="/tmp/cache")
cache = MultiLevelCache(strategy=CacheStrategy.LFU, config=config)
```

---

### العمليات الأساسية | Core Operations

---

#### `get(key)`
**الوصف:** استرجاع قيمة من الكاش. يبحث في L1 أولاً، ثم L2، ثم L3. إذا وُجد في L2 أو L3، يتم ترقيته تلقائياً.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح البيانات |

**Return:** `Any | None` — القيمة المخزنة، أو `None` إذا لم تُوجد أو انتهت صلاحيتها.

```python
cache = MultiLevelCache()
cache.set("product:42", {"name": "Laptop", "price": 999})

# استرجاع القيمة
product = cache.get("product:42")
print(product)  # {"name": "Laptop", "price": 999}

# مفتاح غير موجود
result = cache.get("product:99")
print(result)   # None
```

---

#### `set(key, value, ttl=None)`
**الوصف:** تخزين قيمة في الكاش. يضيف العنصر دائماً في L1 أولاً. إذا وُجد المفتاح مسبقاً، يتم تحديثه في جميع المستويات.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح فريد للبيانات |
| `value` | `Any` | البيانات المراد تخزينها (أي نوع قابل للـ pickle) |
| `ttl` | `float \| None` | مدة الصلاحية بالثواني. `None` يعني استخدام الافتراضي من الإعدادات |

**Return:** `bool` — `True` إذا نجحت العملية، `False` إذا فشلت.

```python
cache = MultiLevelCache()

# تخزين بدون انتهاء صلاحية
cache.set("config", {"theme": "dark"})

# تخزين ينتهي بعد 60 ثانية
cache.set("session:abc", {"user_id": 1}, ttl=60.0)

# تخزين قيم متنوعة
cache.set("count", 42)
cache.set("items", [1, 2, 3])
cache.set("flag", True)
```

---

#### `delete(key)`
**الوصف:** حذف عنصر من جميع مستويات الكاش في آنٍ واحد.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح العنصر المراد حذفه |

**Return:** `bool` — `True` إذا وُجد العنصر وتم حذفه، `False` إذا لم يُوجد.

```python
cache = MultiLevelCache()
cache.set("temp_data", "hello")

deleted = cache.delete("temp_data")
print(deleted)  # True

deleted = cache.delete("non_existent")
print(deleted)  # False
```

---

#### `exists(key)`
**الوصف:** التحقق من وجود مفتاح في الكاش (في أي مستوى) وعدم انتهاء صلاحيته.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | المفتاح المراد البحث عنه |

**Return:** `bool`

```python
cache = MultiLevelCache()
cache.set("active_user", 123)

print(cache.exists("active_user"))  # True
print(cache.exists("ghost_key"))    # False

# يدعم أيضاً عامل `in`
print("active_user" in cache)       # True
```

---

#### `clear(level=None)`
**الوصف:** مسح الكاش بالكامل أو مستوى محدد فقط. عند مسح الكل، تُعاد الإحصائيات أيضاً.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `level` | `int \| None` | رقم المستوى (1، 2، أو 3)، أو `None` لمسح الكل |

```python
cache = MultiLevelCache()
cache.set("a", 1)
cache.set("b", 2)

cache.clear(level=1)   # مسح L1 فقط
cache.clear(level=2)   # مسح L2 فقط
cache.clear()          # مسح كل شيء
```

---

#### `cleanup_expired()`
**الوصف:** فحص جميع المستويات وحذف العناصر منتهية الصلاحية. يُستدعى تلقائياً كل `auto_cleanup_interval` ثانية، لكن يمكن استدعاؤه يدوياً.

**Return:** `int` — عدد العناصر التي تم حذفها.

```python
cache = MultiLevelCache()
cache.set("short_lived", "data", ttl=0.1)  # تنتهي بعد 0.1 ثانية

import time
time.sleep(0.2)

removed = cache.cleanup_expired()
print(f"تم حذف {removed} عنصر")  # تم حذف 1 عنصر
```

---

### عمليات الإحصاء والمعلومات

---

#### `get_stats()`
**الوصف:** الحصول على تقرير شامل لأداء الكاش يشمل الإصابات والإخفاقات ومعدل الاستخدام لكل مستوى.

**Return:** `dict`

```python
cache = MultiLevelCache()
# ... عمليات متعددة ...

stats = cache.get_stats()
print(stats)
# {
#   'l1_items': 15,       # عدد العناصر في L1
#   'l1_size_mb': 0.02,   # الحجم الحالي بـ MB
#   'l1_utilization': 15.0, # نسبة الاستخدام %
#   'l1_hit_rate': 0.85,  # معدل الإصابة
#   'total_items': 120,
#   'overall_hit_rate': 0.78,
#   'evictions': 5,
#   'promotions': 3,
#   ...
# }
```

---

#### `get_keys(level=None)`
**الوصف:** الحصول على قائمة جميع المفاتيح (المُشفَّرة بـ SHA-256) في الكاش أو في مستوى محدد.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `level` | `int \| None` | المستوى (1، 2، 3) أو `None` للكل |

**Return:** `List[str]`

```python
cache = MultiLevelCache()
cache.set("user:1", "Alice")
cache.set("user:2", "Bob")

all_keys = cache.get_keys()
l1_keys = cache.get_keys(level=1)
print(len(all_keys))   # 2
```

---

#### `get_entry_info(key)`
**الوصف:** الحصول على معلومات تفصيلية عن عنصر معين مثل موقعه (L1/L2/L3) وعدد الوصولات وحجمه وهل انتهت صلاحيته.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `key` | `str` | مفتاح العنصر |

**Return:** `dict | None`

```python
cache = MultiLevelCache()
cache.set("report:2024", {"data": [1, 2, 3]}, ttl=3600.0)

info = cache.get_entry_info("report:2024")
print(info)
# {
#   'level': 1,
#   'hits': 0,
#   'age': 0.002,
#   'idle_time': 0.002,
#   'size_bytes': 64,
#   'ttl': 3600.0,
#   'expired': False
# }
```

---

### العمليات الجماعية | Batch Operations

---

#### `get_many(keys)`
**الوصف:** استرجاع قيم متعددة دفعةً واحدة. أسرع من استدعاء `get()` لكل مفتاح على حدة في حالة البيانات الكثيرة.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `keys` | `List[str]` | قائمة المفاتيح المراد استرجاعها |

**Return:** `Dict[str, Any]` — قاموس يحتوي على المفاتيح الموجودة فقط.

```python
cache = MultiLevelCache()
cache.set("a", 1)
cache.set("b", 2)
cache.set("c", 3)

result = cache.get_many(["a", "b", "z"])
print(result)  # {"a": 1, "b": 2}  (z غير موجود)
```

---

#### `set_many(items, ttl=None)`
**الوصف:** تخزين قيم متعددة دفعةً واحدة.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `items` | `Dict[str, Any]` | قاموس أزواج (مفتاح: قيمة) |
| `ttl` | `float \| None` | مدة الصلاحية المشتركة لجميع العناصر |

**Return:** `int` — عدد العناصر التي تم تخزينها بنجاح.

```python
cache = MultiLevelCache()

users = {
    "user:1": {"name": "Ahmed"},
    "user:2": {"name": "Sara"},
    "user:3": {"name": "Omar"},
}

count = cache.set_many(users, ttl=300.0)
print(f"تم تخزين {count} مستخدم")  # تم تخزين 3 مستخدم
```

---

#### `delete_many(keys)`
**الوصف:** حذف مفاتيح متعددة دفعةً واحدة.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `keys` | `List[str]` | قائمة المفاتيح المراد حذفها |

**Return:** `int` — عدد المفاتيح التي تم حذفها فعلاً.

```python
cache = MultiLevelCache()
cache.set_many({"x": 1, "y": 2, "z": 3})

deleted = cache.delete_many(["x", "y", "ghost"])
print(deleted)  # 2 (x و y فقط)
```

---

### الواجهة غير المتزامنة | Async API

---

#### `aget(key)`
**الوصف:** نسخة غير متزامنة (async) من `get()`. مناسبة لاستخدامها داخل `async/await`.

```python
import asyncio
from cache import MultiLevelCache

async def main():
    cache = MultiLevelCache()
    cache.set("async_key", "hello")
    
    value = await cache.aget("async_key")
    print(value)  # hello

asyncio.run(main())
```

---

#### `aset(key, value, ttl=None)`
**الوصف:** نسخة غير متزامنة من `set()`.

```python
async def store_data(cache, key, data):
    success = await cache.aset(key, data, ttl=120.0)
    return success
```

---

#### `adelete(key)`
**الوصف:** نسخة غير متزامنة من `delete()`.

```python
async def remove_session(cache, session_id):
    removed = await cache.adelete(f"session:{session_id}")
    return removed
```

---

### Context Manager (with statement)

**الوصف:** يدعم الكاش استخدام `with` statement لضمان تنظيف الموارد تلقائياً عند الانتهاء.

---
```python
# الاستخدام المتزامن
with MultiLevelCache() as cache:
    cache.set("temp", "value")
    result = cache.get("temp")
# يتم تنظيف الكاش تلقائياً هنا

# الاستخدام غير المتزامن
async with MultiLevelCache() as cache:
    await cache.aset("temp", "value")
    result = await cache.aget("temp")
```

---

### Dunder Methods (دوال خاصة)

| الدالة | الوصف | مثال |
|--------|-------|------|
| `__len__()` | عدد العناصر في جميع المستويات | `len(cache)` |
| `__contains__()` | التحقق من وجود مفتاح | `"key" in cache` |
| `__repr__()` | تمثيل نصي للكاش | `print(cache)` |

```python
cache = MultiLevelCache()
cache.set("a", 1)
cache.set("b", 2)

print(len(cache))      # 2
print("a" in cache)    # True
print(cache)
# MultiLevelCache(L1=2/100, L2=0/1000, L3=0/10000, strategy=lru, hit_rate=0.00%)
```

---

## استراتيجيات الإخلاء

عند امتلاء أي مستوى، يجب إخلاء (إزالة) عنصر لإفساح المجال لعنصر جديد. النظام يدعم 5 استراتيجيات:

### LRU — Least Recently Used (الافتراضي)
يُزيل العنصر الذي لم يُستخدم لأطول فترة زمنية.

**مناسب لـ:** معظم التطبيقات العامة، البيانات التي تُطلب بشكل دوري.

```python
cache = MultiLevelCache(strategy=CacheStrategy.LRU)
```

---

### LFU — Least Frequently Used
يُزيل العنصر الأقل استخداماً من حيث عدد المرات الإجمالية.

**مناسب لـ:** البيانات التي لها نمط استخدام واضح (بعض العناصر تُطلب كثيراً وبعضها نادراً).

```python
cache = MultiLevelCache(strategy=CacheStrategy.LFU)
```

---

### FIFO — First In First Out
يُزيل أقدم عنصر تم إضافته بغض النظر عن الاستخدام.

**مناسب لـ:** بيانات لها عمر محدود بطبيعتها.

```python
cache = MultiLevelCache(strategy=CacheStrategy.FIFO)
```

---

### TTL — Time To Live
يبحث أولاً عن العناصر منتهية الصلاحية ويحذفها. إذا لم يجد، يتراجع لـ LRU.

**مناسب لـ:** البيانات التي لها صلاحية زمنية (sessions، tokens).

```python
cache = MultiLevelCache(strategy=CacheStrategy.TTL)
```

---

### ADAPTIVE — Adaptive Strategy
يحسب "درجة" لكل عنصر: `score = hits / (idle_time + 1)`. العنصر ذو الدرجة الأقل هو المُزال. يوازن بين عدد الاستخدامات وحداثة الوصول.

**مناسب لـ:** أحمال العمل المتغيرة وغير المتوقعة.

```python
cache = MultiLevelCache(strategy=CacheStrategy.ADAPTIVE)
```

---

## مرجع سريع

### جدول الدوال العامة

| الدالة | الوصف | المُعيد |
|--------|-------|---------|
| `cache.get(key)` | استرجاع قيمة | `Any \| None` |
| `cache.set(key, value, ttl)` | تخزين قيمة | `bool` |
| `cache.delete(key)` | حذف عنصر | `bool` |
| `cache.exists(key)` | التحقق من الوجود | `bool` |
| `cache.clear(level)` | مسح الكاش | `None` |
| `cache.cleanup_expired()` | حذف المنتهية صلاحيتها | `int` |
| `cache.get_stats()` | إحصائيات شاملة | `dict` |
| `cache.get_keys(level)` | جميع المفاتيح | `List[str]` |
| `cache.get_entry_info(key)` | تفاصيل عنصر | `dict \| None` |
| `cache.get_many(keys)` | استرجاع متعدد | `Dict[str, Any]` |
| `cache.set_many(items, ttl)` | تخزين متعدد | `int` |
| `cache.delete_many(keys)` | حذف متعدد | `int` |
| `cache.aget(key)` | استرجاع async | `Any \| None` |
| `cache.aset(key, value, ttl)` | تخزين async | `bool` |
| `cache.adelete(key)` | حذف async | `bool` |

---

### مثال شامل

```python
from cache import MultiLevelCache
from cache import CacheStrategy
from cache import CacheConfig

# إعداد الكاش
config = CacheConfig(
    l1_max_items=100,
    l2_max_items=1000,
    default_ttl=300.0,       # 5 دقائق
    cache_dir="/tmp/app_cache"
)

cache = MultiLevelCache(
    strategy=CacheStrategy.ADAPTIVE,
    config=config
)

# تخزين بيانات
cache.set("user:1", {"name": "Ahmed", "role": "admin"})
cache.set("user:2", {"name": "Sara", "role": "user"})
cache.set("config:app", {"debug": False}, ttl=3600.0)

# تخزين جماعي
products = {f"product:{i}": {"id": i, "price": i * 10} for i in range(10)}
cache.set_many(products, ttl=600.0)

# استرجاع
user = cache.get("user:1")
print(user["name"])   # Ahmed

# استرجاع جماعي
result = cache.get_many(["user:1", "user:2", "user:99"])
print(len(result))    # 2

# معلومات عنصر
info = cache.get_entry_info("user:1")
print(f"موجود في المستوى: {info['level']}")

# إحصائيات
stats = cache.get_stats()
print(f"معدل الإصابة: {stats['overall_hit_rate']:.1%}")
print(f"إجمالي العناصر: {stats['total_items']}")

# التنظيف والحذف
cache.delete("user:2")
cache.cleanup_expired()

print(len(cache))     # عدد العناصر المتبقية
```

---

### EXample With Rag System

---
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
from cache import MultiLevelCache, CacheConfig, CacheStrategy
from typing import Tuple
import time
cache_config = CacheConfig(
    l1_max_items=100,
    l2_max_items=500,
    default_ttl=600,          # نتيجة صالحة لـ 10 دقائق
    enable_stats=True,
)
cache = MultiLevelCache(strategy=CacheStrategy.LRU, config=cache_config)

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
def cached_rag_query(query: str) -> Tuple[str, bool]:
    """استعلام RAG مع Cache — يُرجع (answer, from_cache)"""
    cache_key = f"rag:query:{query.strip().lower()}"
    # 1) تحقق من الـ Cache أولاً
    cached = cache.get(cache_key)
    if cached:
        return cached, True
    # 2) تنفيذ الـ RAG الحقيقي
    answer = base_rag.generate(query)
    # 3) حفظ النتيجة في الـ Cache
    cache.set(cache_key, answer)
    return answer, False
    # ── اختبار الـ Cache ──────────────────────────────────────── #
queries = [
    "ما هو الـ RAG وكيف يعمل؟",
    "ما هو الذكاء الاصطناعي؟",
    "ما هو الـ RAG وكيف يعمل؟",    # ← سيُجاب من الـ Cache
    "ما هو الذكاء الاصطناعي؟",     # ← سيُجاب من الـ Cache
    "كيف تعمل النماذج اللغوية الكبيرة؟",
]
print(f"\n  🔍 تشغيل {len(queries)} استعلام على الـ RAG:\n")
for q in queries:
    t0 = time.perf_counter()
    answer, from_cache = cached_rag_query(q)
    elapsed = (time.perf_counter() - t0) * 1000
    source = "⚡ Cache" if from_cache else "🔄 RAG"
    print(f"  {source} ({elapsed:.1f}ms)")
    print(f"  Q: {q}")
    print(f"  A: {answer[:80]}...")
    print()
# ── إحصائيات الـ Cache ────────────────────────────────────── #
stats = cache.get_stats()
print(f"  📊 Cache Stats:")
print(f"     L1 items : {stats.get('l1_items', 0)}")
print(f"     hits     : {stats.get('hits', 0)}")
print(f"     misses   : {stats.get('misses', 0)}")
hit_rate = stats.get("hits", 0) / max(stats.get("hits", 0) + stats.get("misses", 0), 1)
print(f"     hit rate : {hit_rate:.0%}")


```

> **ملاحظة:** جميع العمليات في `MultiLevelCache` آمنة للاستخدام مع الـ threads (Thread-Safe) بفضل استخدام `threading.RLock` داخلياً.
