
> **نظرة عامة | Overview**  
> هذا النظام يوفر نظاماً متكاملاً وآمناً للخيوط (Thread-Safe) لجمع وتتبع مقاييس الأداء في وقت التشغيل. تدعم أربعة أنواع من المقاييس: العدادات (Counters)، المقاييس اللحظية (Gauges)، التوزيعات الإحصائية (Histograms)، وقياس وقت التنفيذ (Timers) — مع تصدير بصيغ Prometheus وJSON.  
> This library provides a thread-safe runtime metrics collection system supporting counters, gauges, histograms, and timers, with Prometheus and JSON export.


---



### `MetricPoint`

**الوصف:** يمثل نقطة قياس واحدة مسجّلة في لحظة زمنية محددة. هو الوحدة الأساسية التي يخزّنها نظام المقاييس لكل قيمة مُسجَّلة.

**الحقول | Fields:**

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `name` | `str` | اسم المقياس |
| `value` | `float` | القيمة المقاسة |
| `timestamp` | `float` | وقت التسجيل (Unix timestamp) |
| `tags` | `Dict[str, str]` | وسوم اختيارية للتصنيف والتصفية |

**مثال:**

```python
from monitor import MetricPoint
import time

point = MetricPoint(
    name="response_time",
    value=0.243,
    timestamp=time.time(),
    tags={"endpoint": "/api/users", "method": "GET"}
)
print(point)
# MetricPoint(name=response_time, value=0.243, tags={'endpoint': '/api/users', 'method': 'GET'})
```

---

#### `to_dict()`

**الوصف:** تحويل نقطة القياس إلى قاموس Python — مفيد للتسلسل (JSON، قواعد البيانات، السجلات). يضيف تلقائياً حقل `datetime` بصيغة ISO 8601 إلى جانب الـ `timestamp`.

**Return:** `Dict` يحتوي على: `name`, `value`, `timestamp`, `datetime`, `tags`

**مثال:**

```python
data = point.to_dict()
print(data)
# {
#   'name': 'response_time',
#   'value': 0.243,
#   'timestamp': 1718000000.0,
#   'datetime': '2024-06-10T12:00:00',
#   'tags': {'endpoint': '/api/users', 'method': 'GET'}
# }

import json
print(json.dumps(data, indent=2))
```

---

### `TimerContext`

**الوصف:** يوفر أداتين لقياس وقت تنفيذ الكود: Context Manager للاستخدام مع `with`، وDecorator للاستخدام مع `@`. يُسجّل القياسات مباشرةً في الـ `MetricsCollector` المرتبط به كـ histogram.

#### `__init__(collector)`

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `collector` | `MetricsCollector` | مثيل الـ collector المستخدم لتسجيل القياسات |

---

#### `timer(name, tags)` *(Context Manager)*

**الوصف:** Context Manager يقيس وقت تنفيذ الكود داخل كتلة `with` ويُسجّله تلقائياً في الـ histogram بالثواني. يضمن تسجيل القياس حتى لو حدث استثناء داخل الكتلة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم مقياس الوقت |
| `tags` | `Dict` | `None` | وسوم اختيارية للتصنيف |

**مثال:**

```python
from monitor import TimerContext
from monitor import MetricsCollector

collector = MetricsCollector()
tc = TimerContext(collector)

# قياس وقت تنفيذ عملية
with tc.timer("db_query", tags={"table": "users"}):
    # عملية قاعدة البيانات
    results = fetch_users_from_db()

# القياس يُسجّل تلقائياً في الـ histogram
stats = collector.get_summary()["histograms"]
print(stats["db_query{table=users}"])
# {'count': 1, 'min': 0.023, 'max': 0.023, 'mean': 0.023, ...}
```

---

#### `measure(name, tags)` *(Decorator)*

**الوصف:** Decorator يلف دالة بقياس وقت التنفيذ تلقائياً في كل استدعاء. يحافظ على اسم الدالة الأصلي وتوثيقها عبر `@wraps`.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم مقياس الوقت |
| `tags` | `Dict` | `None` | وسوم اختيارية للتصنيف |

**Return:** دالة مُزيَّنة (Decorated Function) تعمل بنفس طريقة الأصلية

**مثال:**

```python
collector = MetricsCollector()
tc = TimerContext(collector)

@tc.measure("process_image", tags={"pipeline": "resize"})
def resize_image(path: str, width: int, height: int):
    # معالجة الصورة
    return processed_image

# في كل استدعاء يُسجَّل وقت التنفيذ
resize_image("photo.jpg", 800, 600)
resize_image("photo2.jpg", 1920, 1080)

# إحصائيات لجميع الاستدعاءات
stats = collector.get_summary()["histograms"]["process_image{pipeline=resize}"]
print(f"عدد الاستدعاءات: {stats['count']}")
print(f"متوسط الوقت: {stats['mean']:.3f}s")
```

---


### `MetricsCollector`

**الوصف:** الكلاس الرئيسي في النظام. يجمع المقاييس بأمان من خيوط متعددة (Thread-Safe) عبر `threading.RLock`. يدير أربعة أنواع من المقاييس مع إدارة تلقائية للذاكرة وإمكانية التصدير.

**أنواع المقاييس:**

| النوع | الوصف | مثال الاستخدام |
|-------|-------|---------------|
| **Counter** | قيمة تتزايد فقط | عدد الطلبات، عدد الأخطاء |
| **Gauge** | قيمة تتغير صعوداً وهبوطاً | استخدام CPU، عدد الجلسات النشطة |
| **Histogram** | توزيع إحصائي لقيم متعددة | أوقات الاستجابة، أحجام الملفات |
| **Timer** | قياس وقت تنفيذ الكود | تُسجَّل كـ histogram بالثواني |

#### `__init__(max_metrics)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `max_metrics` | `int` | `10000` | الحد الأقصى لعدد نقاط القياس المحفوظة في الذاكرة. عند الوصول للحد تُحذف الأقدم. |

**مثال:**

```python
from monitor import MetricsCollector

collector = MetricsCollector(max_metrics=50000)
```

---

### 🔢 عمليات العداد | Counter Operations

#### `increment(name, value, tags)`

**الوصف:** زيادة قيمة عداد بمقدار محدد. مفيد لتتبع الأحداث التراكمية مثل عدد الطلبات والأخطاء والعمليات المكتملة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم العداد |
| `value` | `float` | `1` | مقدار الزيادة |
| `tags` | `Dict` | `None` | وسوم اختيارية للتصنيف |

**مثال:**

```python
collector = MetricsCollector()

# زيادة بمقدار 1 (الافتراضي)
collector.increment("http_requests")

# زيادة بمقدار محدد مع وسوم
collector.increment("http_requests", value=1, tags={"method": "POST", "status": "200"})
collector.increment("bytes_transferred", value=1024)

# قراءة القيمة
summary = collector.get_summary()
print(summary["counters"]["http_requests"])  # 2
print(summary["counters"]["http_requests{method=POST,status=200}"])  # 1
```

---

#### `decrement(name, value, tags)`

**الوصف:** تقليل قيمة عداد بمقدار محدد. داخلياً يستدعي `increment` بقيمة سالبة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم العداد |
| `value` | `float` | `1` | مقدار التقليل |
| `tags` | `Dict` | `None` | وسوم اختيارية |

**مثال:**

---
```python
# تتبع الجلسات النشطة
collector.increment("active_sessions")   # مستخدم جديد
collector.increment("active_sessions")   # مستخدم آخر
collector.decrement("active_sessions")   # مستخدم غادر

print(collector.get_summary()["counters"]["active_sessions"])  # 1
```

---

#### `reset_counter(name, tags)`

**الوصف:** إعادة تعيين عداد محدد إلى الصفر دون المساس بباقي العدادات.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم العداد |
| `tags` | `Dict` | `None` | وسوم لتحديد العداد المطلوب |

**مثال:**

```python
collector.increment("daily_signups", 45)
print(collector.get_summary()["counters"]["daily_signups"])  # 45

# إعادة تعيين مع بداية يوم جديد
collector.reset_counter("daily_signups")
print(collector.get_summary()["counters"]["daily_signups"])  # 0
```

---

### 🌡️ عمليات المقياس اللحظي | Gauge Operations

#### `gauge(name, value, tags)`

**الوصف:** تسجيل قيمة لحظية تمثل حالة شيء ما في وقت محدد. على عكس العداد، القيمة يمكن أن ترتفع وتنخفض بحرية وتُستبدَل بالقيمة الجديدة في كل مرة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم المقياس |
| `value` | `float` | — | القيمة الحالية |
| `tags` | `Dict` | `None` | وسوم اختيارية |

**مثال:**

```python
import psutil

# تسجيل موارد النظام
collector.gauge("cpu_usage_percent", psutil.cpu_percent())
collector.gauge("memory_usage_mb", psutil.virtual_memory().used / 1024 / 1024)
collector.gauge("disk_free_gb", psutil.disk_usage("/").free / 1024**3)

# تسجيل مقاييس التطبيق
collector.gauge("active_connections", 42, tags={"service": "api"})
collector.gauge("queue_size", 7, tags={"queue": "email_notifications"})

summary = collector.get_summary()
print(summary["gauges"]["cpu_usage_percent"])   # 73.2
print(summary["gauges"]["active_connections{service=api}"])  # 42
```

---

### 📊 عمليات التوزيع الإحصائي | Histogram Operations

#### `histogram(name, value, tags)`

**الوصف:** إضافة قيمة إلى مجموعة بيانات لحساب إحصائيات توزيعها. يجمع جميع القيم ويتيح حساب المتوسط والوسيط والانحراف المعياري والـ percentiles (p50, p90, p95, p99).

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم الـ histogram |
| `value` | `float` | — | القيمة المراد إضافتها |
| `tags` | `Dict` | `None` | وسوم اختيارية |

**مثال:**

```python
import random

# تسجيل أوقات استجابة الـ API
for _ in range(1000):
    response_time = random.gauss(0.2, 0.05)  # متوسط 200ms
    collector.histogram("api_response_time", response_time, tags={"endpoint": "/search"})

stats = collector.get_summary()["histograms"]["api_response_time{endpoint=/search}"]
print(f"الحد الأدنى:       {stats['min']:.3f}s")
print(f"المتوسط:           {stats['mean']:.3f}s")
print(f"الوسيط (p50):      {stats['p50']:.3f}s")
print(f"p90:               {stats['p90']:.3f}s")
print(f"p99:               {stats['p99']:.3f}s")
print(f"الحد الأقصى:       {stats['max']:.3f}s")
print(f"الانحراف المعياري: {stats['stdev']:.3f}s")
```

---

### ⏱️ عمليات قياس الوقت | Timer Operations

#### `timer(name, tags)`

**الوصف:** إرجاع Context Manager لقياس وقت تنفيذ كتلة كود. يُسجّل المدة الزمنية بالثواني كـ histogram عند انتهاء الكتلة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم مقياس الوقت |
| `tags` | `Dict` | `None` | وسوم اختيارية |

**Return:** Context Manager

**مثال:**

-

```python
collector = MetricsCollector()

# قياس وقت استعلام قاعدة البيانات
with collector.timer("db_query", tags={"operation": "SELECT"}):
    results = db.execute("SELECT * FROM users WHERE active = 1")

# قياس وقت معالجة ملف
with collector.timer("file_processing"):
    data = parse_large_csv("data.csv")

# القياسات محفوظة كـ histogram
stats = collector.get_summary()["histograms"]
print(f"وقت الاستعلام: {stats['db_query{operation=SELECT}']['mean']:.3f}s")
```

---

#### `measure(name, tags)`

**الوصف:** إرجاع Decorator لقياس وقت تنفيذ دالة في كل استدعاء لها. مثالي للدوال التي تُستدعى كثيراً وتحتاج مراقبة مستمرة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `name` | `str` | — | اسم مقياس الوقت |
| `tags` | `Dict` | `None` | وسوم اختيارية |

**Return:** Function Decorator

**مثال:**
-

```python
collector = MetricsCollector()

@collector.measure("embed_text", tags={"model": "bert"})
def embed_text(text: str) -> list:
    return model.encode(text)

@collector.measure("classify_document")
def classify_document(doc: dict) -> str:
    return classifier.predict(doc)

# استدعاء عادي — القياس يحدث تلقائياً
embed_text("مرحباً بالعالم")
embed_text("الذكاء الاصطناعي")
classify_document({"content": "..."})

# إحصائيات التنفيذ
stats = collector.get_summary()["histograms"]
print(f"عدد استدعاءات embed_text: {stats['embed_text{model=bert}']['count']}")
print(f"متوسط وقت التصنيف: {stats['classify_document']['mean']:.3f}s")
```

---

### 🔍 عمليات الاستعلام | Query Operations

#### `get_metrics_by_name(name)`

**الوصف:** استرجاع جميع نقاط القياس التي تحمل اسماً محدداً، مرتبةً زمنياً بحسب وقت تسجيلها.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `name` | `str` | اسم المقياس المطلوب |

**Return:** `List[MetricPoint]`

**مثال:**

```python
# استرجاع سجل قياسات CPU كاملاً
cpu_metrics = collector.get_metrics_by_name("cpu_usage")
for m in cpu_metrics[-5:]:  # آخر 5 قياسات
    print(f"{m.metadata['datetime']}: {m.value:.1f}%")

# التحقق من حدوث قياسات
if not collector.get_metrics_by_name("payment_processed"):
    print("⚠️ لم تُسجَّل أي معاملات دفع بعد")
```

---

#### `get_metrics_by_tag(tag_key, tag_value)`

**الوصف:** استرجاع جميع نقاط القياس التي تحتوي على وسم محدد بقيمة محددة، بصرف النظر عن اسم المقياس.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `tag_key` | `str` | مفتاح الوسم المطلوب البحث به |
| `tag_value` | `str` | القيمة المطلوب مطابقتها |

**Return:** `List[MetricPoint]`

**مثال:**

--
```python
# جميع مقاييس endpoint معين (بأنواعها المختلفة)
api_metrics = collector.get_metrics_by_tag("endpoint", "/api/checkout")
print(f"عدد القياسات لـ /api/checkout: {len(api_metrics)}")

# تحليل مقاييس خدمة محددة
prod_metrics = collector.get_metrics_by_tag("environment", "production")
errors = [m for m in prod_metrics if m.name == "errors"]
print(f"عدد الأخطاء في الـ production: {len(errors)}")
```

---

#### `get_summary()`

**الوصف:** إرجاع ملخص شامل لجميع المقاييس المحفوظة. للـ histograms يحسب تلقائياً إحصائيات كاملة تشمل الـ percentiles.

**Return:** `Dict` يحتوي على:
- `counters` — قيمة كل عداد
- `gauges` — آخر قيمة لكل gauge
- `histograms` — إحصائيات كاملة لكل histogram (count, min, max, mean, median, stdev, sum, p50, p90, p95, p99)
- `total_metrics` — العدد الإجمالي لنقاط القياس المخزّنة

**مثال:**

```python
summary = collector.get_summary()

print(f"إجمالي نقاط القياس: {summary['total_metrics']}")
print(f"\nالعدادات:")
for name, value in summary["counters"].items():
    print(f"  {name}: {value}")

print(f"\nالمقاييس اللحظية:")
for name, value in summary["gauges"].items():
    print(f"  {name}: {value}")

print(f"\nالتوزيعات الإحصائية:")
for name, stats in summary["histograms"].items():
    print(f"  {name}:")
    print(f"    عدد القياسات: {stats['count']}")
    print(f"    متوسط:        {stats['mean']:.3f}")
    print(f"    p99:          {stats['p99']:.3f}")
```

---

### 📤 عمليات التصدير | Export Operations

#### `export_prometheus()`

**الوصف:** تصدير جميع المقاييس بصيغة Prometheus النصية القياسية. يُنظّف أسماء المقاييس تلقائياً لتكون متوافقة مع متطلبات Prometheus (يستبدل الأحرف الخاصة بـ `_`).

**Return:** `str` — نص بصيغة Prometheus

**مثال:**

```python
prometheus_text = collector.export_prometheus()
print(prometheus_text)
# # TYPE http_requests counter
# http_requests 142
# # TYPE http_requests_method_POST_status_200_ counter
# http_requests_method_POST_status_200_ 87
# # TYPE cpu_usage_percent gauge
# cpu_usage_percent 73.2
# # TYPE api_response_time histogram
# api_response_time_count 1000
# api_response_time_sum 201.4
# api_response_time_avg 0.2014

# حفظ في ملف أو إرسال لـ Pushgateway
with open("metrics.txt", "w") as f:
    f.write(prometheus_text)
```

---

#### `export_json()`

**الوصف:** تصدير المقاييس بصيغة JSON تشمل الملخص الكامل وآخر 100 نقطة قياس مسجّلة.

**Return:** `Dict` يحتوي على: `summary` و`recent_metrics`

**مثال:**

```python
import json

data = collector.export_json()

# حفظ في ملف
with open("metrics_snapshot.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# إرسال عبر API
import requests
requests.post("https://monitoring.example.com/metrics", json=data)

# الوصول للبيانات
print(f"عدد الطلبات المسجّلة: {data['summary']['counters'].get('http_requests', 0)}")
print(f"آخر قياس: {data['recent_metrics'][-1]}")
```

---

### 🗑️ إدارة البيانات | Management Operations

#### `clear()`

**الوصف:** مسح جميع البيانات المحفوظة وإعادة تعيين جميع العدادات والـ gauges والـ histograms إلى الحالة الابتدائية.

**مثال:**

```python
print(f"قبل المسح: {len(collector.metrics)} نقطة قياس")
collector.clear()
print(f"بعد المسح: {len(collector.metrics)} نقطة قياس")  # 0

# مفيد في الاختبارات لعزل كل اختبار
def setUp(self):
    self.collector = MetricsCollector()
    self.collector.clear()
```

---

### 🌐 الـ Collector العالمي | Global Collector

#### `get_collector()`

**الوصف:** إرجاع مثيل واحد مشترك من `MetricsCollector` على مستوى التطبيق كله (Singleton). مفيد للمشاريع التي تحتاج collector موحّد بدون تمرير المثيل يدوياً.

**Return:** `MetricsCollector`

**مثال:**

```python
from monitor import get_collector

# في أي مكان بالتطبيق — نفس المثيل دائماً
collector = get_collector()
collector.increment("app_started")
```

---

### 🛠️ دوال الاختصار العالمية | Global Convenience Functions

**الوصف:** دوال مباشرة تعمل على الـ collector العالمي دون الحاجة لإنشاء مثيل. مثالية للاستخدام السريع في التطبيقات الصغيرة.

```python
from monitor import increment, gauge, histogram, timer, measure

# استخدام مباشر بدون إنشاء collector
increment("page_views")
increment("page_views", tags={"page": "/home"})

gauge("memory_mb", 512.4)

histogram("file_size_kb", 128.5)

with timer("render_template"):
    html = render("index.html", context)

@measure("send_email")
def send_welcome_email(user_email: str):
    # إرسال البريد الإلكتروني
    pass
```

---

### 🔧 الدوال الداخلية المساعدة | Internal Helper Methods

#### `_make_key(name, tags)`

**الوصف:** إنشاء مفتاح فريد من اسم المقياس ووسومه بصيغة `name{tag1=val1,tag2=val2}` (مرتّبة أبجدياً لضمان التوافق). تُستخدم داخلياً لتنظيم مخازن العدادات والـ gauges والـ histograms.

**مثال:**

```python
key = collector._make_key("requests", {"method": "POST", "status": "200"})
print(key)  # requests{method=POST,status=200}

key_no_tags = collector._make_key("requests")
print(key_no_tags)  # requests
```

---

#### `_calculate_stats(values)`

**الوصف:** حساب إحصائيات شاملة لقائمة قيم. تُستخدم داخلياً لحساب إحصائيات الـ histograms.

**Return:** `Dict` يحتوي على: `count`, `min`, `max`, `mean`, `median`, `stdev`, `sum`, `p50`, `p90`, `p95`, `p99`

**مثال:**

```python
values = [0.1, 0.2, 0.15, 0.3, 0.25, 0.5, 0.18]
stats = collector._calculate_stats(values)

print(f"العدد:   {stats['count']}")     # 7
print(f"المتوسط: {stats['mean']:.3f}")  # 0.241
print(f"p95:     {stats['p95']:.3f}")   # 0.470
```

---

#### `_percentile(sorted_values, p)`

**الوصف:** حساب الـ percentile باستخدام Linear Interpolation للحصول على دقة أعلى مقارنة بطريقة التقريب البسيطة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `sorted_values` | `List[float]` | قائمة قيم مرتّبة تصاعدياً |
| `p` | `float` | الـ percentile المطلوب (0-100) |

**Return:** `float`

---

## 🚀 أمثلة متكاملة

### مثال 1: مراقبة تطبيق ويب

```python
from monitor import MetricsCollector
import time, random

collector = MetricsCollector()

def handle_request(endpoint: str, method: str):
    """معالجة طلب HTTP مع تسجيل المقاييس"""
    collector.increment("http_requests", tags={"endpoint": endpoint, "method": method})

    with collector.timer("response_time", tags={"endpoint": endpoint}):
        # محاكاة معالجة الطلب
        time.sleep(random.uniform(0.05, 0.3))
        status = random.choice([200, 200, 200, 404, 500])

    collector.increment(f"http_status_{status}")
    return status

# محاكاة 200 طلب
for _ in range(200):
    handle_request("/api/products", "GET")
    handle_request("/api/checkout", "POST")

# مراقبة الموارد
collector.gauge("active_connections", random.randint(10, 50))
collector.gauge("memory_usage_mb", 245.7)

# تقرير الأداء
summary = collector.get_summary()
rt_stats = summary["histograms"].get("response_time{endpoint=/api/products}", {})

print("📊 تقرير أداء التطبيق")
print(f"  إجمالي الطلبات:   {summary['counters'].get('http_requests', 0):.0f}")
print(f"  متوسط وقت الاستجابة: {rt_stats.get('mean', 0)*1000:.1f}ms")
print(f"  p99 وقت الاستجابة:   {rt_stats.get('p99', 0)*1000:.1f}ms")
print(f"  أخطاء 500:        {summary['counters'].get('http_status_500', 0):.0f}")
```

---

### مثال 2: قياس أداء نموذج ML

```python
from monitor import MetricsCollector

collector = MetricsCollector()

@collector.measure("model_inference", tags={"model": "bert-arabic"})
def run_inference(text: str) -> dict:
    # استدعاء النموذج
    return model.predict(text)

@collector.measure("preprocess_text")
def preprocess(text: str) -> str:
    return text.strip().lower()

# تشغيل على مجموعة بيانات
texts = ["نص تجريبي " * i for i in range(1, 101)]
for text in texts:
    clean = preprocess(text)
    result = run_inference(clean)

    # تسجيل مقاييس إضافية
    collector.histogram("input_length", len(text))
    collector.histogram("confidence_score", result.get("confidence", 0))

summary = collector.get_summary()

print("🤖 إحصائيات أداء النموذج")
inf_stats = summary["histograms"]["model_inference{model=bert-arabic}"]
print(f"  عدد الاستدعاءات: {inf_stats['count']}")
print(f"  متوسط وقت الاستنتاج: {inf_stats['mean']*1000:.1f}ms")
print(f"  p95: {inf_stats['p95']*1000:.1f}ms")
print(f"  p99: {inf_stats['p99']*1000:.1f}ms")
```

---

### مثال 3: مراقبة متعدد الخيوط

```python
from monitor import MetricsCollector
import threading
import time
import random

collector = MetricsCollector()

def worker_task(worker_id: int, n_tasks: int):
    """مهمة عامل في خيط منفصل"""
    for i in range(n_tasks):
        with collector.timer("task_duration", tags={"worker": str(worker_id)}):
            time.sleep(random.uniform(0.01, 0.1))

        collector.increment("tasks_completed", tags={"worker": str(worker_id)})
        collector.gauge("worker_progress",
                        (i + 1) / n_tasks * 100,
                        tags={"worker": str(worker_id)})

# تشغيل 5 خيوط متوازية
threads = [threading.Thread(target=worker_task, args=(i, 20)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# النتائج بعد انتهاء جميع الخيوط
summary = collector.get_summary()
total = sum(v for k, v in summary["counters"].items() if "tasks_completed" in k)
print(f"✓ إجمالي المهام المكتملة: {total:.0f}")
print(f"  إجمالي نقاط القياس: {summary['total_metrics']}")
```

---

### مثال 4: تصدير للمراقبة

```python
from monitor import MetricsCollector
import json

collector = MetricsCollector()

# ... (تشغيل التطبيق وجمع المقاييس) ...

# تصدير بصيغة Prometheus
prom_output = collector.export_prometheus()
with open("metrics.prom", "w") as f:
    f.write(prom_output)
print("✓ تم تصدير مقاييس Prometheus")

# تصدير بصيغة JSON للرسوم البيانية
json_output = collector.export_json()
with open("metrics_dashboard.json", "w", encoding="utf-8") as f:
    json.dump(json_output, f, indent=2, ensure_ascii=False, default=str)
print(f"✓ تم تصدير {len(json_output['recent_metrics'])} نقطة قياس بصيغة JSON")

# طباعة ملخص للـ console
summary = json_output["summary"]
print(f"\n📊 ملخص المقاييس:")
print(f"  إجمالي نقاط القياس: {summary['total_metrics']}")
print(f"  عدد العدادات: {len(summary['counters'])}")
print(f"  عدد الـ gauges: {len(summary['gauges'])}")
print(f"  عدد الـ histograms: {len(summary['histograms'])}")
```
---

### EXample With Rag System:

```python
from monitor import MetricsCollector
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
collector = MetricsCollector(max_metrics=10_000)
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
def monitored_rag_query(query: str) -> str:
    """تنفيذ استعلام RAG مع تسجيل كل المقاييس"""
    # ── قياس خطوة الاسترجاع ──────────────────────────────── #
    with collector.timer("rag.retrieval.latency"):
        retrieved = base_rag.retrieve(query)
    collector.increment("rag.queries.total")
    collector.gauge("rag.docs.retrieved", len(retrieved))
    if not retrieved:
        collector.increment("rag.retrieval.failures")
        return "❌ لم يتم العثور على معلومات."
    top_score = retrieved[0][1] if retrieved else 0
    collector.histogram("rag.retrieval.top_score", top_score)
    collector.increment("rag.retrieval.success")
    # ── قياس خطوة بناء السياق ────────────────────────────── #
    with collector.timer("rag.context.build_time"):
        context = base_rag.context_manager.build(query, retrieved)
    collector.gauge("rag.context.length_chars", len(context))
    # ── قياس خطوة التوليد ────────────────────────────────── #
    with collector.timer("rag.generation.latency"):
        answer = base_rag.llm.generate(
            base_rag._build_prompt(query, context, language_pr="ar")
        )
        collector.gauge("rag.answer.length_chars", len(answer))
        collector.histogram("rag.answer.length_hist", len(answer))
        collector.increment("rag.queries.successful")
        return answer

    # ── تشغيل استعلامات متعددة ────────────────────────────────── #
test_queries = [
    "ما هو الـ RAG؟",
    "كيف يعمل تعلم الآلة؟",
    "ما هي النماذج اللغوية الكبيرة؟",
    "ما هو الذكاء الاصطناعي؟",
    "ما هي التضمينات (Embeddings)؟",
]
print(f"\n  🚀 تشغيل {len(test_queries)} استعلام مع المراقبة:\n")
for q in test_queries:
    answer = monitored_rag_query(q)
    print(f"  Q: {q}")
    print(f"  A: {answer[:70]}...\n")

print(collector.get_summary())
```

## 🔑 ملخص أنواع المقاييس

| النوع | الدالة | متى تستخدمه | مثال |
|-------|--------|------------|------|
| **Counter** | `increment()` / `decrement()` | أحداث تراكمية تزيد مع الوقت | عدد الطلبات، الأخطاء، المستخدمين الجدد |
| **Gauge** | `gauge()` | قيم تتغير صعوداً وهبوطاً | استخدام CPU، الذاكرة، الجلسات النشطة |
| **Histogram** | `histogram()` | توزيع قيم لحساب إحصائياتها | أوقات الاستجابة، أحجام الملفات، درجات الثقة |
| **Timer** | `timer()` / `measure()` | قياس وقت تنفيذ كود | استعلامات DB، استدعاءات API، معالجة البيانات |
