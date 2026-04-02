# Observability System — توثيق شامل

> **Metrics · Alerts · Tracing · Anomaly Detection · Export**



## 1. نظرة عامة على النظام

**Observability System** هو نظام مراقبة إنتاجي متكامل مكتوب بـ Python، يوفر رصداً شاملاً للتطبيقات عبر ثماني وحدات متكاملة:

## Config
يحتوي على `dataclasses` تُعرِّف كل إعدادات النظام. لا يحتوي على منطق تنفيذي — مجرد هياكل بيانات.

### 2.1 StorageConfig

يحدد backend التخزين المستخدم.

| البارامتر | النوع | الوصف |
|---|---|---|
| `backend` | `str` | `"memory"` \| `"sqlite"` \| `"redis"` — الافتراضي: `"memory"` |
| `sqlite_path` | `str` | مسار ملف SQLite — الافتراضي: `"obs.db"` |
| `redis_url` | `str` | رابط Redis — الافتراضي: `"redis://localhost:6379/0"` |
| `redis_key_prefix` | `str` | بادئة مفاتيح Redis — الافتراضي: `"obs:"` |
| `redis_ttl_seconds` | `int` | وقت انتهاء صلاحية البيانات في Redis (ثانية) — الافتراضي: `86400` |

### 2.2 RateLimitConfig

يضبط حدود معدل الكتابة لحماية النظام من الفيضان.

| البارامتر | النوع | الوصف |
|---|---|---|
| `enabled` | `bool` | تفعيل Rate Limiting — الافتراضي: `True` |
| `max_records_per_second` | `int` | الحد الأقصى الكلي في الثانية — الافتراضي: `10,000` |
| `burst_size` | `int` | السعة القصوى للـ burst — الافتراضي: `50,000` |
| `per_metric_limit` | `int` | الحد الأقصى لكل metric في الثانية — الافتراضي: `1,000` |

### 2.3 AnomalyConfig

يضبط كاشف الشذوذ.

| البارامتر | النوع | الوصف |
|---|---|---|
| `enabled` | `bool` | تفعيل الكشف — الافتراضي: `True` |
| `algorithm` | `str` | `"zscore"` \| `"iqr"` \| `"isolation_forest"` |
| `zscore_threshold` | `float` | حد Z-Score للحكم بالشذوذ — الافتراضي: `3.0` |
| `iqr_multiplier` | `float` | مضاعف IQR — الافتراضي: `1.5` |
| `min_samples` | `int` | أقل عدد قياسات للبدء — الافتراضي: `30` |
| `window_seconds` | `float` | حجم النافذة الزمنية بالثواني — الافتراضي: `300.0` |
| `retrain_interval_seconds` | `int` | فترة إعادة تدريب Isolation Forest — الافتراضي: `600` |

### 2.4 TracingConfig

يضبط نظام التتبع.

| البارامتر | النوع | الوصف |
|---|---|---|
| `sampling_rate` | `float` | نسبة الـ spans المُسجَّلة (0.0–1.0) — الافتراضي: `1.0` |
| `max_stored_traces` | `int` | أقصى عدد traces في الذاكرة — الافتراضي: `10,000` |
| `max_traces_age_seconds` | `float` | عمر الـ trace الأقصى قبل التنظيف — الافتراضي: `3600.0` |
| `opentelemetry_endpoint` | `Optional[str]` | رابط OTLP Collector مثل `http://jaeger:4317` — الافتراضي: `None` |
| `service_name` | `str` | اسم الخدمة — الافتراضي: `"my-service"` |
| `service_version` | `str` | إصدار الخدمة — الافتراضي: `"1.0.0"` |

### 2.5 ExporterConfig

يضبط خيارات التصدير لأنظمة المراقبة الخارجية.

| البارامتر | النوع | الوصف |
|---|---|---|
| `prometheus_enabled` | `bool` | تفعيل Prometheus HTTP Server — الافتراضي: `True` |
| `prometheus_port` | `int` | منفذ Prometheus — الافتراضي: `9090` |
| `grafana_url` | `Optional[str]` | رابط Grafana — الافتراضي: `None` |
| `grafana_api_key` | `Optional[str]` | مفتاح Grafana API — الافتراضي: `None` |
| `datadog_api_key` | `Optional[str]` | مفتاح Datadog API — الافتراضي: `None` |
| `datadog_site` | `str` | موقع Datadog — الافتراضي: `"datadoghq.com"` |
| `export_interval_seconds` | `int` | فترة التصدير بالثواني — الافتراضي: `15` |

### 2.6 ObservabilityConfig — الإعداد الرئيسي

يجمع كل الإعدادات الفرعية في كائن واحد يُمرَّر لـ `ObservabilitySystem`.

| البارامتر | النوع | الوصف |
|---|---|---|
| `service_name` | `str` | اسم الخدمة — الافتراضي: `"service"` |
| `environment` | `str` | `"production"` \| `"staging"` \| `"dev"` |
| `max_stored_metrics` | `int` | أقصى عدد قياسات محفوظة — الافتراضي: `100,000` |
| `max_stored_alerts` | `int` | أقصى عدد تنبيهات محفوظة — الافتراضي: `5,000` |
| `window_seconds` | `float` | النافذة الزمنية الافتراضية للاستعلام — الافتراضي: `60.0` |
| `alert_cooldown_seconds` | `int` | فترة الهدوء بين تنبيهين لنفس القاعدة — الافتراضي: `60` |
| `enable_auto_cleanup` | `bool` | تفعيل التنظيف التلقائي للبيانات القديمة — الافتراضي: `True` |
| `storage` | `StorageConfig` | إعدادات التخزين |
| `rate_limit` | `RateLimitConfig` | إعدادات Rate Limiting |
| `anomaly` | `AnomalyConfig` | إعدادات كشف الشذوذ |
| `tracing` | `TracingConfig` | إعدادات التتبع |
| `exporter` | `ExporterConfig` | إعدادات التصدير |

---

## 3. Storage

تُعرِّف واجهة مجردة `StorageBackend` وثلاثة تطبيقات: `MemoryBackend` و`SQLiteBackend` و`RedisBackend`. يتم اختيار الـ backend تلقائياً عبر دالة `create_storage()`.

### 3.1 الواجهة المجردة — StorageBackend

#### `save_observation(obs)`

يحفظ قياساً واحداً في الـ storage.

| البارامتر | النوع | الوصف |
|---|---|---|
| `obs` | `Observation` | كائن القياس المراد حفظه |

#### `save_observations_batch(observations)`

يحفظ قائمة قياسات دفعةً واحدة — أسرع من استدعاء `save_observation` مرات متعددة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `observations` | `List[Observation]` | قائمة القياسات المراد حفظها |

#### `query_observations(...)`

يستعلم عن القياسات المخزنة مع دعم التصفية.

| البارامتر | النوع | الوصف |
|---|---|---|
| `metric_name` | `Optional[str]` | اسم الـ metric — `None` لجميع المقاييس |
| `since` | `Optional[float]` | timestamp بداية الفترة (epoch) |
| `until` | `Optional[float]` | timestamp نهاية الفترة (epoch) |
| `tags_filter` | `Optional[Dict[str,str]]` | فلترة بالتاغات مثل `{"env": "prod"}` |
| `limit` | `int` | أقصى عدد نتائج — الافتراضي: `10,000` |

#### `save_alert(alert)`

يحفظ تنبيهاً في الـ storage.

| البارامتر | النوع | الوصف |
|---|---|---|
| `alert` | `Alert` | كائن التنبيه المراد حفظه |

#### `query_alerts(...)`

يستعلم عن التنبيهات المحفوظة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `since` | `Optional[float]` | timestamp بداية الفترة |
| `severity` | `Optional[str]` | `"info"` \| `"warning"` \| `"critical"` |
| `limit` | `int` | أقصى عدد نتائج — الافتراضي: `1,000` |

#### `purge_old_data(metrics_cutoff, alerts_cutoff)`

يحذف البيانات الأقدم من الـ cutoffs المحددة. يُستدعى تلقائياً بواسطة cleanup thread.

| البارامتر | النوع | الوصف |
|---|---|---|
| `metrics_cutoff` | `float` | timestamp — تُحذف القياسات الأقدم منه |
| `alerts_cutoff` | `float` | timestamp — تُحذف التنبيهات الأقدم منه |

### 3.2 MemoryBackend

تخزين في الذاكرة بـ `deque`. سريع جداً، لكن البيانات تُفقد عند إيقاف التطبيق.

> **ملاحظة:** استخدم هذا الـ backend للتطوير المحلي فقط. في الإنتاج استخدم SQLite أو Redis.

### 3.3 SQLiteBackend

تخزين دائم في ملف SQLite مع WAL mode للأداء والتزامن. مناسب لخادم واحد.

- يستخدم connection per thread عبر `threading.local()` لتجنب مشاكل التزامن
- يدعم WAL journal mode لأداء أفضل تحت الكتابة المتزامنة
- يحتفظ بـ indices على `(metric_name, timestamp)` و`(timestamp, severity)`
- يخزن `anomaly_score` مع كل تنبيه

### 3.4 RedisBackend

تخزين في Redis باستخدام Sorted Sets حيث `score = timestamp`. مناسب للنشر الموزع.

- يتطلب: `pip install redis`
- يستخدم pipeline لتقليل round-trips الشبكة
- يضبط TTL تلقائياً على كل البيانات
- يحافظ على حجم أقصى بحذف الأقدم تلقائياً

### 3.5 `create_storage(config)`

دالة factory تُنشئ الـ backend المناسب حسب `config.storage.backend`.

```python
storage = create_storage(config)  # يُعيد MemoryBackend أو SQLiteBackend أو RedisBackend
```

---

## 4. Anomaly

يحتوي على كاشف الشذوذ `AnomalyDetector` الذي يراقب القياسات ويكتشف القيم غير الطبيعية عبر ثلاث خوارزميات.

### 4.1 AnomalyResult — نتيجة الكشف

`dataclass` يُعيده `AnomalyDetector.detect()` لكل قياس.

| الحقل | النوع | الوصف |
|---|---|---|
| `metric_name` | `str` | اسم الـ metric الذي فُحص |
| `value` | `float` | القيمة التي فُحصت |
| `timestamp` | `float` | وقت القياس (epoch) |
| `is_anomaly` | `bool` | `True` إذا كانت القيمة شاذة |
| `score` | `float` | درجة الشذوذ — كلما زاد كلما كان الشذوذ أكبر |
| `algorithm` | `str` | الخوارزمية المستخدمة |
| `expected_range` | `Tuple[float,float]` | النطاق المتوقع الطبيعي `(min, max)` |
| `severity` | `str` | `"info"` \| `"warning"` (score≥2.0) \| `"critical"` (score≥5.0) |
| `tags` | `Dict[str,str]` | التاغات المرتبطة بالقياس |

### 4.2 AnomalyDetector

#### `__init__(...)`

ينشئ كاشف الشذوذ مع الخوارزمية والإعدادات المحددة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `algorithm` | `str` | `"zscore"` \| `"iqr"` \| `"isolation_forest"` |
| `zscore_threshold` | `float` | حد Z-Score — الافتراضي: `3.0` |
| `iqr_multiplier` | `float` | مضاعف IQR — الافتراضي: `1.5` |
| `min_samples` | `int` | أقل عدد قياسات للبدء — الافتراضي: `30` |
| `window_seconds` | `float` | حجم النافذة الزمنية — الافتراضي: `300.0` |
| `retrain_interval` | `int` | ثواني بين إعادات تدريب Isolation Forest — الافتراضي: `600` |

#### `update(metric_name, value, timestamp=None)`

يضيف قياساً للنافذة الزمنية دون إجراء فحص. مفيد للتغذية الأولية للنموذج.

| البارامتر | النوع | الوصف |
|---|---|---|
| `metric_name` | `str` | اسم الـ metric |
| `value` | `float` | القيمة |
| `timestamp` | `Optional[float]` | وقت القياس — `None` يستخدم `time.time()` |

#### `detect(metric_name, value, timestamp=None, tags=None)` → `AnomalyResult`

يُضيف القياس للنافذة ثم يفحصه ويُعيد `AnomalyResult`. **هذه هي الدالة الرئيسية.**

| البارامتر | النوع | الوصف |
|---|---|---|
| `metric_name` | `str` | اسم الـ metric |
| `value` | `float` | القيمة المراد فحصها |
| `timestamp` | `Optional[float]` | وقت القياس — `None` يستخدم `time.time()` |
| `tags` | `Optional[Dict[str,str]]` | تاغات إضافية تُضاف للنتيجة |

> إذا كانت العينات أقل من `min_samples`، يُعيد `is_anomaly=False` و`score=0.0`.

#### `get_stats(metric_name)` → `Dict`

يُعيد إحصائيات النافذة الحالية للـ metric المحدد.

**Return:** `dict` يحتوي على `samples`, `mean`, `std`, `min`, `max`, `p25`, `p75`

### 4.3 الخوارزميات

#### Z-Score

تقيس كم انحرافاً معيارياً تبعد القيمة عن المتوسط. سريعة وخفيفة، تعمل جيداً مع البيانات ذات التوزيع الطبيعي.

```
score      = |value - mean| / std
is_anomaly = score >= zscore_threshold  (الافتراضي: 3.0)
```

#### IQR (Interquartile Range)

تستخدم المدى بين الربيعين (Q1 وQ3) لتحديد الحدود. مقاومة للقيم الشاذة الشديدة، تعمل جيداً مع البيانات غير المتماثلة.

```
fence      = iqr_multiplier × (Q3 - Q1)
is_anomaly = value < (Q1 - fence)  OR  value > (Q3 + fence)
```

#### Isolation Forest

خوارزمية تعلم آلي تبني أشجاراً عشوائية وتعزل القيم الشاذة. الأقوى للأنماط المعقدة. تتطلب `scikit-learn` وتُعيد التدريب كل `retrain_interval` ثانية.

```bash
pip install scikit-learn
```

---

## 5. Observability

يحتوي على `ObservabilitySystem` وهو المكوّن المركزي للنظام. يدير تسجيل القياسات، التنبيهات، كشف الشذوذ، والإحصاءات.

### 5.1 MetricType

`Enum` يحدد نوع الـ metric:

| القيمة | الوصف |
|---|---|
| `COUNTER` | قيمة تتزايد فقط — عدد الطلبات، عدد الأخطاء |
| `GAUGE` | قيمة تتغير صعوداً وهبوطاً — استخدام CPU، حجم الذاكرة |
| `HISTOGRAM` | توزيع القيم — زمن الاستجابة |
| `TIMER` | قياس زمن تنفيذ عملية |

### 5.2 Observation — نموذج القياس

`dataclass` يمثل قياساً واحداً.

| الحقل | النوع | الوصف |
|---|---|---|
| `metric_name` | `str` | اسم الـ metric |
| `metric_type` | `MetricType` | نوع الـ metric |
| `value` | `float` | القيمة العددية |
| `timestamp` | `float` | وقت القياس (epoch) — الافتراضي: `time.time()` |
| `tags` | `Dict[str,str]` | تاغات للتصفية مثل `{"env": "prod", "region": "us-east"}` |

### 5.3 ObservabilitySystem

#### `__init__(config=None)`

ينشئ النظام الكامل: storage + rate limiter + write buffer + anomaly detector + cleanup thread.

| البارامتر | النوع | الوصف |
|---|---|---|
| `config` | `Optional[ObservabilityConfig]` | إعدادات النظام — `None` يستخدم الافتراضيات |

#### `record(metric_name, value, metric_type, tags)` → `bool`

يُسجِّل قياساً واحداً بشكل متزامن. يُعيد `True` عند القبول أو `False` عند الرفض بسبب Rate Limiting.

| البارامتر | النوع | الوصف |
|---|---|---|
| `metric_name` | `str` | اسم الـ metric |
| `value` | `float` | القيمة |
| `metric_type` | `MetricType` | النوع — الافتراضي: `MetricType.GAUGE` |
| `tags` | `Optional[Dict[str,str]]` | تاغات — الافتراضي: `{}` |

```python
accepted = obs.record("cpu.usage", 78.5, MetricType.GAUGE, {"host": "srv1"})
```

#### `record_batch(observations)` → `int`

يُسجِّل دفعة قياسات. يُعيد عدد القياسات المقبولة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `observations` | `List[Observation]` | قائمة القياسات |

```python
count = obs.record_batch([Observation(...), Observation(...)])
```

#### `arecord(metric_name, value, metric_type, tags)` → `Coroutine[bool]`

نسخة **async** من `record()` — تُنفَّذ في thread pool executor لعدم حجب event loop. مناسبة لـ FastAPI handlers.

```python
accepted = await obs.arecord("requests.count", 1, MetricType.COUNTER)
```

#### `arecord_batch(observations)` → `Coroutine[int]`

نسخة **async** من `record_batch()`.

```python
count = await obs.arecord_batch(observations)
```

#### `add_alert_rule(rule_id, metric_name, condition, message, ...)`

يُضيف قاعدة تنبيه تُفعَّل عند تحقق `condition` مع cooldown لتجنب التكرار.

| البارامتر | النوع | الوصف |
|---|---|---|
| `rule_id` | `str` | معرف فريد للقاعدة |
| `metric_name` | `str` | اسم الـ metric الذي تراقبه القاعدة |
| `condition` | `Callable[[float], bool]` | دالة تأخذ القيمة وتُعيد `True` إذا وجب التنبيه |
| `message` | `str` | نص رسالة التنبيه |
| `severity` | `str` | `"info"` \| `"warning"` \| `"critical"` — الافتراضي: `"warning"` |
| `cooldown_seconds` | `Optional[int]` | ثواني بين تنبيهين — `None` يستخدم config |
| `tags_filter` | `Optional[Dict]` | التنبيه يُفعَّل فقط إذا تطابقت التاغات |

```python
obs.add_alert_rule("high_cpu", "cpu.usage", lambda v: v > 90, "CPU عالٍ!", "critical")
```

#### `remove_alert_rule(rule_id)` → `bool`

يحذف قاعدة تنبيه. يُعيد `True` عند الحذف، `False` إذا لم توجد القاعدة.

#### `get_metrics_summary(metric_name, window_seconds, tags_filter)` → `Dict`

يُعيد إحصائيات شاملة لـ metric في نافذة زمنية محددة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `metric_name` | `str` | اسم الـ metric |
| `window_seconds` | `Optional[float]` | حجم النافذة بالثواني — `None` يستخدم config |
| `tags_filter` | `Optional[Dict]` | فلترة بالتاغات |

**Return:** `dict` يحتوي على `count`, `min`, `max`, `mean`, `median`, `std`, `p50`, `p90`, `p95`, `p99`, `sum`

#### `get_active_alerts(max_age_seconds, severity)` → `List[Alert]`

يُعيد التنبيهات النشطة مع إمكانية الفلترة بالخطورة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `max_age_seconds` | `Optional[float]` | عمر التنبيه الأقصى — `None` يستخدم config |
| `severity` | `Optional[str]` | `"info"` \| `"warning"` \| `"critical"` — `None` لجميع الخطورات |

#### `get_anomaly_stats(metric_name)` → `Optional[Dict]`

يُعيد إحصائيات كاشف الشذوذ للـ metric المحدد، أو `None` إذا كان الكاشف معطلاً.

#### `get_system_stats()` → `Dict`

يُعيد إحصائيات شاملة للنظام: `total_recorded`, `total_dropped`, `total_alerts`, `total_anomalies`, `unique_metrics`, `anomaly_enabled`, `storage_backend`.

#### `export_prometheus(window_seconds)` → `str`

يُصدِّر جميع المقاييس بصيغة Prometheus text format.

| البارامتر | النوع | الوصف |
|---|---|---|
| `window_seconds` | `float` | حجم النافذة الزمنية للتصدير — الافتراضي: `60.0` |

#### `export_dict()` → `Dict`

يُصدِّر snapshot شامل بصيغة JSON يحتوي على `service`, `environment`, `timestamp`, `stats`, `metrics`, `alerts`.

#### `stop()`

يوقف النظام بأمان: يُفرِّغ الـ write buffer، يوقف جميع threads، ويُغلق اتصال الـ storage.

```python
obs.stop()
# أو استخدم context manager:
with ObservabilitySystem(config) as obs:
    ...
```

### 5.4 TokenBucketRateLimiter

يطبق خوارزمية Token Bucket لحماية النظام من الفيضان. آمن للـ threads.

- يملأ الـ bucket بمعدل `rate` token في الثانية حتى حد `burst`
- كل طلب يستهلك token واحداً — إذا لم يتوفر token يُرفض الطلب
- يدعم حداً منفصلاً لكل metric عبر `per_metric_rate`

---

## 6. Tracer

يوفر تتبع الطلبات عبر الخدمات مع دعم معيار W3C Trace Context وإرسال البيانات لـ OpenTelemetry Collector.

### 6.1 TraceContext

يمثل سياق الـ trace الذي يُمرَّر بين الخدمات عبر HTTP headers.

| الحقل | النوع | الوصف |
|---|---|---|
| `trace_id` | `str` | معرف الـ trace الفريد (UUID hex) |
| `span_id` | `str` | معرف الـ span الحالي (16 حرفاً) |
| `sampled` | `bool` | هل يجب تخزين هذا الـ trace؟ |

#### `TraceContext.from_header(traceparent)` → `TraceContext`

يستخرج الـ context من W3C traceparent header بصيغة: `00-{trace_id}-{span_id}-{flags}`

```python
ctx = TraceContext.from_header("00-4bf92f3577b34da6-00f067aa0073662e-01")
```

#### `to_header()` → `str`

يحوّل الـ context لـ traceparent header لإرساله للخدمة التالية.

```python
header_value = ctx.to_header()  # "00-trace_id-span_id-01"
```

### 6.2 TraceEvent

`dataclass` يمثل span واحداً (حدثاً في الـ trace).

| الحقل | النوع | الوصف |
|---|---|---|
| `event_id` | `str` | معرف الـ span الفريد |
| `trace_id` | `str` | معرف الـ trace الذي ينتمي إليه |
| `event_type` | `str` | نوع العملية مثل `http.request`, `db.query` |
| `service_name` | `str` | اسم الخدمة |
| `timestamp` | `float` | وقت بداية الـ span (epoch) |
| `duration` | `Optional[float]` | مدة التنفيذ بالثواني (`None` إذا لم ينته بعد) |
| `status` | `str` | `"success"` \| `"error"` \| `"timeout"` |
| `error` | `Optional[str]` | رسالة الخطأ إذا فشل الـ span |
| `parent_id` | `Optional[str]` | معرف الـ span الأب (للـ nested spans) |
| `tags` | `Dict[str,str]` | تاغات إضافية |
| `metadata` | `Dict[str,Any]` | بيانات إضافية (kwargs من `start_span`) |

### 6.3 Tracer

#### `start_span(event_type, parent_id, trace_context, tags, **metadata)` → `str`

يبدأ span جديداً ويُعيد `span_id`. يُعيد سلسلة فارغة عند التخطي بسبب sampling.

| البارامتر | النوع | الوصف |
|---|---|---|
| `event_type` | `str` | نوع العملية المُتتبَّعة |
| `parent_id` | `Optional[str]` | `span_id` الأب للـ nested spans |
| `trace_context` | `Optional[TraceContext]` | الـ context القادم من خدمة أخرى |
| `tags` | `Optional[Dict[str,str]]` | تاغات الـ span |
| `**metadata` | `Any` | بيانات إضافية تُرفق بالـ span |

```python
span_id = tracer.start_span("db.query", table="users", query="SELECT *")
```

#### `end_span(span_id, status, error, extra_tags)` → `Optional[TraceEvent]`

يُنهي الـ span ويحسب مدته ويحفظه. يُعيد `None` إذا كان `span_id` فارغاً.

| البارامتر | النوع | الوصف |
|---|---|---|
| `span_id` | `str` | معرف الـ span المراد إنهاؤه |
| `status` | `str` | `"success"` \| `"error"` \| `"timeout"` — الافتراضي: `"success"` |
| `error` | `Optional[str]` | رسالة الخطأ إن وجد |
| `extra_tags` | `Optional[Dict]` | تاغات إضافية تُضاف عند الإنهاء |

#### `trace(event_type, ...)` — Context Manager (sync)

يبدأ span تلقائياً ويُنهيه عند الخروج، مع التقاط الأخطاء تلقائياً.

```python
with tracer.trace("http.request", method="GET", path="/api/users") as span_id:
    result = db.query(...)
```

#### `atrace(event_type, ...)` — Async Context Manager

نسخة async من `trace()` للاستخدام مع `async/await`.

```python
async with tracer.atrace("db.query", table="orders") as span_id:
    await db.fetch_all(query)
```

#### `inject_context(span_id, headers)` → `Dict`

يحقن trace context في HTTP headers لإرسالها للخدمة التالية.

| البارامتر | النوع | الوصف |
|---|---|---|
| `span_id` | `str` | span_id النشط الحالي |
| `headers` | `Dict[str,str]` | قاموس الـ headers المراد الحقن فيه |

```python
headers = tracer.inject_context(span_id, {"Content-Type": "application/json"})
```

#### `extract_context(headers)` → `Optional[TraceContext]`

يستخرج trace context من HTTP headers الواردة من خدمة أخرى.

#### `get_events(...)` → `List[TraceEvent]`

يستعلم عن الأحداث المحفوظة مع دعم فلترة متعددة.

| البارامتر | النوع | الوصف |
|---|---|---|
| `event_type` | `Optional[str]` | فلترة بنوع الحدث |
| `since` | `Optional[float]` | فلترة بالوقت (epoch) |
| `status` | `Optional[str]` | `"success"` \| `"error"` \| `"timeout"` |
| `parent_id` | `Optional[str]` | فلترة بالـ span الأب |
| `trace_id` | `Optional[str]` | فلترة بـ trace_id للحصول على spans trace كامل |

#### `get_trace(trace_id)` → `List[TraceEvent]`

يُعيد جميع spans في trace واحد مرتبةً زمنياً.

#### `get_trace_tree(root_span_id)` → `Dict`

يُعيد شجرة الـ trace كاملة `(span + children)` ابتداءً من الـ root span المحدد.

#### `get_stats()` → `Dict`

يُعيد إحصائيات شاملة: `total_spans`, `completed_spans`, `failed_spans`, `active_spans`, `error_rate`, `duration_stats` (mean/p95/max بالمللي ثانية لكل نوع).

### 6.4 OTLPExporter

يُرسل traces لـ OpenTelemetry Collector (Jaeger / Grafana Tempo) عبر HTTP/JSON بصيغة OTLP.

| البارامتر | النوع | الوصف |
|---|---|---|
| `endpoint` | `str` | رابط الـ collector مثل `http://jaeger:4317` |
| `service_name` | `str` | اسم الخدمة |
| `service_version` | `str` | إصدار الخدمة |

---

## 7. Export

يُدير تصدير البيانات لأنظمة المراقبة الخارجية عبر `ExporterManager`.

### 7.1 PrometheusExporter

يُشغِّل HTTP server على المنفذ المحدد. Prometheus يسحب البيانات من `/metrics` endpoint بشكل دوري.

| البارامتر | النوع | الوصف |
|---|---|---|
| `obs` | `ObservabilitySystem` | مرجع للنظام |
| `port` | `int` | المنفذ — الافتراضي: `9090` |

المسارات المخدومة:
- `GET /metrics` — بيانات Prometheus text format
- `GET /health` — فحص الصحة

```yaml
# Prometheus config:
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['localhost:9090']
```

### 7.2 GrafanaExporter

يُرسل annotations لـ Grafana كلما حدث تنبيه جديد.

| البارامتر | النوع | الوصف |
|---|---|---|
| `obs` | `ObservabilitySystem` | مرجع للنظام |
| `grafana_url` | `str` | رابط Grafana مثل `http://grafana:3000` |
| `api_key` | `str` | Grafana API Key بصلاحية Editor أو أعلى |
| `export_interval` | `int` | ثواني بين عمليات التصدير — الافتراضي: `15` |
| `dashboard_id` | `Optional[int]` | معرف الـ dashboard لربط الـ annotations به |

### 7.3 DatadogExporter

يُرسل metrics وevents لـ Datadog عبر API v2.

| البارامتر | النوع | الوصف |
|---|---|---|
| `obs` | `ObservabilitySystem` | مرجع للنظام |
| `api_key` | `str` | Datadog API Key |
| `site` | `str` | موقع Datadog — الافتراضي: `"datadoghq.com"` |
| `export_interval` | `int` | ثواني بين عمليات التصدير — الافتراضي: `15` |

- يُرسل `mean`, `max`, `p95` لكل metric
- يُرسل التنبيهات كـ Datadog Events مع mapping الخطورة

### 7.4 ExporterManager

يُدير جميع الـ exporters المُفعَّلة في config. يُنشئها تلقائياً ويُشغِّلها ويُوقفها.

| الدالة | الوصف |
|---|---|
| `start_all()` | يبدأ جميع الـ exporters في threads خلفية |
| `stop_all()` | يوقف جميع الـ exporters بأمان |
| `export_all()` → `Dict[str, bool]` | يُشغِّل التصدير يدوياً لجميع الـ exporters |

---

## 8. Api — REST API

يُعرِّف FastAPI application مع endpoints لجميع وظائف النظام.

### 8.1 جميع الـ Endpoints

| الـ Endpoint | Method | الوصف |
|---|---|---|
| `/health` | `GET` | فحص صحة النظام — يُعيد `{status: ok, timestamp}` |
| `/stats` | `GET` | إحصائيات النظام الشاملة |
| `/metrics/record` | `POST` | تسجيل قياس واحد |
| `/metrics/batch` | `POST` | تسجيل دفعة قياسات (حتى 1000) |
| `/metrics/{name}` | `GET` | ملخص إحصائي لـ metric مع فلترة |
| `/metrics` | `GET` | قائمة أسماء جميع المقاييس |
| `/metrics/{name}/anomaly` | `GET` | إحصائيات كشف الشذوذ لـ metric |
| `/alerts` | `GET` | التنبيهات مع فلترة بالعمر والخطورة |
| `/alerts/rules` | `POST` | إضافة قاعدة تنبيه |
| `/alerts/rules/{id}` | `DELETE` | حذف قاعدة تنبيه |
| `/traces` | `GET` | الأحداث المُتتبَّعة مع فلترة |
| `/traces/{trace_id}` | `GET` | جميع spans في trace واحد |
| `/traces/stats/summary` | `GET` | إحصائيات التتبع |
| `/export/prometheus` | `GET` | تصدير Prometheus text format |
| `/export/json` | `GET` | تصدير JSON شامل |

### 8.2 W3C Trace Context عبر API

جميع endpoints تقبل query parameter اختياري `traceparent` لربط الطلبات بـ distributed trace:

```
POST /metrics/record?traceparent=00-4bf92f3577b34da6-00f067aa0073662e-01
```

---

## 9. Dashboard

يُشغِّل HTTP server بسيط يُقدِّم لوحة تحكم ويب تتحدث تلقائياً عبر Server-Sent Events (SSE).

### المسارات

| المسار | الوصف |
|---|---|
| `/` | لوحة التحكم الكاملة (HTML) |
| `/stream` | SSE — تتحدث كل `refresh_seconds` |
| `/data` | JSON snapshot فوري |

### المحتوى المعروض

- **KPI cards:** المقاييس، إجمالي القياسات، التنبيهات، الشذوذات، الـ Rate Limiter tokens، نوع الـ Storage
- **جدول المقاييس:** count, mean, min, max, p90, p99, std لكل metric
- **التنبيهات النشطة:** مصنفةً بالألوان حسب الخطورة (info / warning / critical)
- **إحصائيات كشف الشذوذ:** samples, mean, std, p25, p75 لكل metric

### `DashboardExporter`

| البارامتر | النوع | الوصف |
|---|---|---|
| `obs` | `ObservabilitySystem` | مرجع للنظام |
| `port` | `int` | المنفذ — الافتراضي: `8888` |
| `refresh_seconds` | `int` | فترة تحديث SSE — الافتراضي: `3` |
| `host` | `str` | عنوان الاستماع — الافتراضي: `"0.0.0.0"` |

```python
from observability.dashboard import DashboardExporter

dash = DashboardExporter(obs, port=8080)
dash.start()
print(dash.url)   # http://0.0.0.0:8080
```

---

## 10. مثال عملي شامل
```python
"""
RAG + Observability + Live Chat Dashboard — Demo
=================================================
افتح المتصفح على http://localhost:8888 بعد التشغيل
"""
from __future__ import annotations

import logging
import random
import time
from typing import Dict, List, Optional, Tuple

# ── مكوّنات المكتبة ──────────────────────────────────────────────────────
from llm import MistralInterface
from embeddings import MistralEmbedder
from chunks import MultilanguageTextChunker
from vector_database import FAISSVectorDatabase
from context import ContextManager
from rag.core import RAGSystem, RAGConfig
from rag.streaming_rag import StreamingRAG, StreamConfig, EventType
from observability import (
    ObservabilityConfig,
    ObservabilitySystem,
    AnomalyConfig,
    MetricType,
    DashboardExporter,
)
from observability.dashboard import ConversationLogger   # ← Live Chat

# ── إعداد الـ logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)-7s | %(name)s — %(message)s",
)

# ════════════════════════════════════════════════════════════════════════════
# ① الاعتمادات
# ════════════════════════════════════════════════════════════════════════════

API_KEY = "Vq1tR9u65wBFEyPelrjqcpFv99AGwmRG"

llm      = MistralInterface(api_key=API_KEY)
embedder = MistralEmbedder(api_key=API_KEY)
chunker  = MultilanguageTextChunker(chunk_size=200, overlap=50)
vd       = FAISSVectorDatabase(embedder=embedder)
context  = ContextManager()

# ════════════════════════════════════════════════════════════════════════════
# ② بيانات الـ Demo
# ════════════════════════════════════════════════════════════════════════════

DEMO_DOCUMENTS: Dict[str, str] = {
    "ml_intro": """
    التعلم الآلي (Machine Learning) هو فرع من فروع الذكاء الاصطناعي يُمكّن الأنظمة من التعلم
    تلقائياً وتحسين أدائها من خلال التجربة دون الحاجة إلى برمجة صريحة. يعتمد التعلم الآلي
    على بناء نماذج رياضية من بيانات "تدريب" لاتخاذ تنبؤات أو قرارات دون أن تكون مبرمجة
    صراحةً للقيام بذلك. أبرز أنواعه: التعلم الخاضع للإشراف، وغير الخاضع، والمعزَّز.
    """,
    "deep_learning": """
    التعلم العميق (Deep Learning) هو نوع متقدم من التعلم الآلي يستخدم شبكات عصبية اصطناعية
    بطبقات متعددة لتعلم تمثيلات البيانات. تُعدّ هذه التقنية أساس معظم التطبيقات الحديثة
    كالتعرف على الكلام والصور وترجمة النصوص. نماذج مثل GPT وBERT مبنية على معمارية
    المحوّلات (Transformers) التي ثورت مجال معالجة اللغات الطبيعية.
    """,
    "rag_concept": """
    RAG (Retrieval-Augmented Generation) هو نهج يُدمج نظام استرجاع المعلومات مع نماذج
    اللغة التوليدية. يعمل على مرحلتين: أولاً استرجاع المستندات ذات الصلة من قاعدة معرفية،
    ثم استخدام هذه المستندات كسياق لتوليد إجابة دقيقة. يُقلّل هذا من الهلوسة ويُحسّن
    دقة الإجابات بشكل كبير مقارنةً بالنماذج التوليدية البحتة.
    """,
    "vector_databases": """
    قواعد البيانات المتجهية (Vector Databases) تُخزّن البيانات كمتجهات رياضية عالية الأبعاد
    وتُتيح البحث بالتشابه الدلالي بدلاً من التطابق الحرفي. أشهر الأمثلة: FAISS من Meta،
    وChroma، وPinecone، وMilvus. تُستخدم على نطاق واسع في تطبيقات RAG والتوصيات
    والبحث الدلالي. تعتمد على خوارزميات Approximate Nearest Neighbor للبحث الفعّال.
    """,
    "embeddings": """
    التضمينات (Embeddings) هي تمثيلات رياضية للنصوص في فضاء متجهي عالي الأبعاد،
    حيث تكون النصوص المتشابهة دلالياً قريبة من بعضها. تُنتَج باستخدام نماذج مثل
    text-embedding-ada-002 من OpenAI، أو sentence-transformers من HuggingFace.
    جودة التضمينات تؤثر مباشرةً على دقة الاسترجاع في أنظمة RAG.
    """,
    "observability": """
    المراقبة والرصد (Observability) في أنظمة AI تعني القدرة على قياس وتتبع أداء النظام
    في الوقت الفعلي. تشمل: زمن الاستجابة، ومعدل الأخطاء، وجودة الاسترجاع، وتكاليف
    الاستدلال. أدوات مثل Prometheus وGrafana وLangSmith تُستخدم لمراقبة أنظمة RAG.
    الشذوذات في الأداء يمكن اكتشافها تلقائياً عبر خوارزميات Z-Score أو IQR.
    """,
}

DEMO_QUERIES = [
    "ما هو التعلم الآلي؟",
    "كيف يعمل التعلم العميق؟",
    "ما هو RAG وكيف يعمل؟",
    "ما الفرق بين قواعد البيانات المتجهية والعادية؟",
    "ما هي التضمينات وكيف تؤثر على RAG؟",
    "كيف يتم رصد أداء أنظمة الذكاء الاصطناعي؟",
]

# ════════════════════════════════════════════════════════════════════════════
# ③ RAGObservabilityWrapper — يجمع RAG + Observability + Live Chat
# ════════════════════════════════════════════════════════════════════════════

class RAGObservabilityWrapper:
    """
    يلتف حول RAGSystem ويُضيف:
    - Observability كاملة (latency, docs, errors…)
    - تسجيل تلقائي في ConversationLogger لعرضه في Live Chat
    """

    def __init__(
        self,
        rag: RAGSystem,
        obs: ObservabilitySystem,
        conv_logger: ConversationLogger,
    ):
        self.rag         = rag
        self.obs         = obs
        self.conv_logger = conv_logger

    # ── مساعد تسجيل المقاييس ─────────────────────────────────────────
    def _rec(
        self,
        name: str,
        value: float,
        mtype: MetricType = MetricType.GAUGE,
        tags: Optional[Dict] = None,
    ) -> None:
        self.obs.record(name, value, mtype, tags or {})

    # ── فهرسة المستندات ──────────────────────────────────────────────
    def add_documents(self, docs: Dict[str, str]) -> Dict[str, int]:
        t0     = time.perf_counter()
        result = self.rag.add_documents(docs)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self._rec("rag.indexing_latency_ms",  elapsed_ms,          MetricType.TIMER)
        self._rec("rag.indexed_chunks_count", sum(result.values()), MetricType.COUNTER)
        return result

    # ── الاسترجاع ────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple]:
        t0      = time.perf_counter()
        results = self.rag.retrieve(query, top_k=top_k)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self._rec("rag.retrieval_latency_ms", elapsed_ms,   MetricType.TIMER)
        self._rec("rag.retrieved_docs_count", len(results))
        if results:
            avg_score = sum(s for _, s in results) / len(results)
            self._rec("rag.avg_similarity_score", avg_score)
        return results

    # ── الاستعلام الكامل (Query + Live Chat log) ──────────────────────
    def query(
        self,
        query: str,
        session_id: str = "default",
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        t_total = time.perf_counter()
        _tags   = tags or {}

        self._rec("rag.query_count", 1, MetricType.COUNTER, _tags)

        try:
            # مرحلة الاسترجاع
            t0 = time.perf_counter()
            retrieved = self.rag.retrieve(query)
            retrieval_ms = (time.perf_counter() - t0) * 1000
            self._rec("rag.retrieval_latency_ms", retrieval_ms, MetricType.TIMER, _tags)
            self._rec("rag.retrieved_docs_count", len(retrieved), tags=_tags)
            if retrieved:
                avg_score = sum(s for _, s in retrieved) / len(retrieved)
                self._rec("rag.avg_similarity_score", avg_score, tags=_tags)

            # مرحلة التوليد
            t0 = time.perf_counter()
            answer = self.rag.generate(query)
            generation_ms = (time.perf_counter() - t0) * 1000
            self._rec("rag.generation_latency_ms", generation_ms, MetricType.TIMER, _tags)
            self._rec("rag.answer_length_chars",   len(answer),   tags=_tags)

            total_ms = (time.perf_counter() - t_total) * 1000
            self._rec("rag.total_latency_ms", total_ms, MetricType.TIMER, _tags)

            # ✅ تسجيل المحادثة في Live Chat
            self.conv_logger.log(
                session_id    = session_id,
                query         = query,
                answer        = answer,
                latency_ms    = total_ms,
                sources_count = len(retrieved),
            )

            return answer

        except Exception as exc:
            self._rec("rag.error_count", 1, MetricType.COUNTER, _tags)
            raise

    # ── البث مع Observability + Live Chat ────────────────────────────
    def stream_query(
        self,
        streaming_rag: StreamingRAG,
        query: str,
        session_id: str = "default",
        print_tokens: bool = True,
    ) -> str:
        tokens: List[str] = []
        t_start            = time.perf_counter()
        retrieval_ms       = 0.0
        num_docs           = 0
        t_retrieval_start  = None

        for event in streaming_rag.stream_events(query):

            if event.type == EventType.RETRIEVAL_START:
                t_retrieval_start = time.perf_counter()

            elif event.type == EventType.RETRIEVAL_DONE:
                retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000
                num_docs     = event.data.get("num_docs", 0)
                self._rec("rag.retrieval_latency_ms", retrieval_ms, MetricType.TIMER)
                self._rec("rag.retrieved_docs_count", num_docs)
                if print_tokens:
                    print(f"\n  📂 استُرجع {num_docs} مستندات ({retrieval_ms:.0f}ms)")

            elif event.type == EventType.CHUNK:
                tokens.append(event.data)
                if print_tokens:
                    print(event.data, end="", flush=True)

            elif event.type == EventType.GENERATION_DONE:
                generation_ms = event.data.get("total_latency", 0) * 1000
                self._rec("rag.generation_latency_ms", generation_ms, MetricType.TIMER)

            elif event.type == EventType.ERROR:
                self._rec("rag.error_count", 1, MetricType.COUNTER)
                if print_tokens:
                    print(f"\n  ❌ خطأ: {event.data.get('msg')}")

        total_ms    = (time.perf_counter() - t_start) * 1000
        full_answer = "".join(tokens)

        self._rec("rag.total_latency_ms",    total_ms,          MetricType.TIMER)
        self._rec("rag.answer_length_chars", len(full_answer))
        self._rec("rag.query_count",         1,                 MetricType.COUNTER)

        # ✅ تسجيل المحادثة في Live Chat
        self.conv_logger.log(
            session_id    = session_id,
            query         = query,
            answer        = full_answer,
            latency_ms    = total_ms,
            sources_count = num_docs,
        )

        if print_tokens:
            print(f"\n  ⏱ الزمن الكلي: {total_ms:.0f}ms")

        return full_answer


# ════════════════════════════════════════════════════════════════════════════
# ④ بناء المكوّنات
# ════════════════════════════════════════════════════════════════════════════

def build_rag() -> RAGSystem:
    return RAGSystem(
        vector_db       = vd,
        llm             = llm,
        chunker         = chunker,
        context_manager = context,
        config          = RAGConfig(
            top_k                  = 3,
            min_score              = 0.0,
            enable_reranking       = False,
            enable_prompt_routing  = False,
        ),
    )


def build_observability() -> ObservabilitySystem:
    obs = ObservabilitySystem(
        config=ObservabilityConfig(
            environment           = "development",
            window_seconds        = 120.0,
            alert_cooldown_seconds= 15,
            anomaly               = AnomalyConfig(
                enabled           = True,
                algorithm         = "zscore",
                zscore_threshold  = 2.5,
                min_samples       = 5,
                window_seconds    = 120.0,
            ),
        )
    )

    obs.add_alert_rule(
        rule_id     = "slow_retrieval",
        metric_name = "rag.retrieval_latency_ms",
        condition   = lambda v: v > 500,
        message     = "زمن الاسترجاع تجاوز 500ms",
        severity    = "warning",
    )
    obs.add_alert_rule(
        rule_id     = "very_slow_total",
        metric_name = "rag.total_latency_ms",
        condition   = lambda v: v > 3000,
        message     = "الزمن الكلي تجاوز 3 ثوانٍ",
        severity    = "critical",
    )
    obs.add_alert_rule(
        rule_id     = "no_docs_retrieved",
        metric_name = "rag.retrieved_docs_count",
        condition   = lambda v: v < 1,
        message     = "لم يُسترجَع أي مستند",
        severity    = "critical",
    )
    obs.add_alert_rule(
        rule_id     = "low_similarity",
        metric_name = "rag.avg_similarity_score",
        condition   = lambda v: v < 0.3,
        message     = "درجة التشابه منخفضة جداً",
        severity    = "warning",
    )
    return obs


# ════════════════════════════════════════════════════════════════════════════
# ⑤ حلقة الطلبات
# ════════════════════════════════════════════════════════════════════════════

# أسماء جلسات وهمية لمحاكاة عدة مستخدمين
_SESSIONS = ["user-alpha", "user-beta", "user-gamma", "user-delta"]


def run_query_loop(
    wrapper:       RAGObservabilityWrapper,
    streaming_rag: StreamingRAG,
    iterations:    int = 20,
    delay_range:   Tuple[float, float] = (0.5, 2.0),
) -> None:
    print("\n" + "═" * 60)
    print(f"🚀 إرسال {iterations} طلب للـ RAG system...")
    print("📊 افتح المتصفح على http://localhost:8888 → تبويب 💬 Live Chat")
    print("═" * 60 + "\n")

    for i in range(iterations):
        query      = random.choice(DEMO_QUERIES)
        session_id = random.choice(_SESSIONS)
        streaming  = (i % 3 == 0)

        print(f"\n[{i+1}/{iterations}] {'🌊 Stream' if streaming else '📝 Query'}"
              f" | {session_id} | {query}")

        try:
            if streaming:
                print("  الإجابة: ", end="")
                wrapper.stream_query(streaming_rag, query,
                                     session_id=session_id, print_tokens=True)
            else:
                answer  = wrapper.query(query, session_id=session_id)
                preview = answer[:80] + "…" if len(answer) > 80 else answer
                print(f"  الإجابة: {preview}")

        except Exception as exc:
            print(f"  ❌ خطأ: {exc}")

        time.sleep(random.uniform(*delay_range))

    print("\n\n" + "═" * 60)
    print("✅ انتهت جميع الطلبات!")


# ════════════════════════════════════════════════════════════════════════════
# ⑥ إحصائيات نهائية
# ════════════════════════════════════════════════════════════════════════════

def print_final_stats(
    obs:         ObservabilitySystem,
    conv_logger: ConversationLogger,
) -> None:
    print("\n📊 ملخص الإحصائيات النهائية:")
    print("─" * 50)

    s = obs.get_system_stats()
    print(f"  إجمالي القياسات  : {s['total_recorded']}")
    print(f"  إجمالي التنبيهات : {s['total_alerts']}")
    print(f"  الشذوذات المكتشفة: {s['total_anomalies']}")
    print(f"  المقاييس الفريدة : {s['unique_metrics']}")

    chat_stats = conv_logger.get_stats()
    print(f"\n💬 إحصائيات Live Chat:")
    print(f"  إجمالي المحادثات : {chat_stats['total_logged']}")
    print(f"  جلسات مختلفة    : {chat_stats['unique_sessions']}")
    print(f"  متوسط الاستجابة  : {chat_stats['avg_latency_ms']} ms")

    print("\n📈 تفاصيل الزمن الكلي (rag.total_latency_ms):")
    summary = obs.get_metrics_summary("rag.total_latency_ms")
    if summary.get("count", 0) > 0:
        print(f"  عدد القياسات : {summary['count']}")
        print(f"  المتوسط      : {summary['mean']:.1f}ms")
        print(f"  الحد الأدنى  : {summary['min']:.1f}ms")
        print(f"  الحد الأقصى  : {summary['max']:.1f}ms")
        print(f"  p90          : {summary['p90']:.1f}ms")
        print(f"  p99          : {summary['p99']:.1f}ms")

    print("\n🔔 التنبيهات النشطة:")
    alerts = obs.get_active_alerts()
    if alerts:
        for a in alerts[-5:]:
            print(f"  [{a.severity.upper()}] {a.metric_name} — {a.message}")
    else:
        print("  ✅ لا توجد تنبيهات")


# ════════════════════════════════════════════════════════════════════════════
# ⑦ main
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   RAG + Observability + Live Chat Dashboard Demo     ║")
    print("╚═══════════════════════════════════════════════════════╝\n")

    # ── بناء المكوّنات ───────────────────────────────────────────────
    print("⚙️  بناء RAG system...")
    rag = build_rag()

    print("⚙️  بناء Observability system...")
    obs = build_observability()

    # ── ConversationLogger للـ Live Chat ─────────────────────────────
    conv_logger = ConversationLogger(max_turns=200)

    # ── Wrapper يجمع الثلاثة ─────────────────────────────────────────
    wrapper = RAGObservabilityWrapper(rag=rag, obs=obs, conv_logger=conv_logger)

    # ── Dashboard مع Live Chat ────────────────────────────────────────
    dashboard = DashboardExporter(
        obs,
        port                = 8888,
        refresh_seconds     = 2,
        conversation_logger = conv_logger,   # ← يفعّل تبويب Live Chat
    )
    dashboard.start()

    # ── فهرسة المستندات ──────────────────────────────────────────────
    print("\n📄 فهرسة المستندات...")
    result = wrapper.add_documents(DEMO_DOCUMENTS)
    for doc_id, n_chunks in result.items():
        print(f"  ✅ {doc_id}: {n_chunks} chunks")

    # ── StreamingRAG ─────────────────────────────────────────────────
    streaming_rag = StreamingRAG(
        rag_system = rag,
        llm        = rag.llm,
        config     = StreamConfig(
            chunk_size    = 4,
            sim_delay     = 0.015,
            max_context_docs = 3,
            max_doc_chars    = 400,
        ),
    )

    # ── حلقة الطلبات ─────────────────────────────────────────────────
    try:
        run_query_loop(
            wrapper       = wrapper,
            streaming_rag = streaming_rag,
            iterations    = 25,
            delay_range   = (0.3, 1.2),
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  توقف المستخدم")

    # ── الإحصائيات النهائية ──────────────────────────────────────────
    print_final_stats(obs, conv_logger)

    # ── إبقاء الـ Dashboard شغّال ────────────────────────────────────
    print(f"\n🌐 الـ Dashboard لا يزال يعمل على http://localhost:8888")
    print("   اضغط Ctrl+C للخروج\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 إيقاف النظام...")
    finally:
        obs.stop()
        dashboard.stop()
        print("✅ تم الإيقاف بشكل نظيف")


# ════════════════════════════════════════════════════════════════════════════
# دعم Jupyter Notebook
# ════════════════════════════════════════════════════════════════════════════

def jupyter_demo(iterations: int = 10, port: int = 8888):
    """
    من داخل Jupyter:
        from rag_demo import jupyter_demo
        wrapper, obs, conv_logger = jupyter_demo(iterations=10)
    """
    import nest_asyncio
    nest_asyncio.apply()

    rag         = build_rag()
    obs         = build_observability()
    conv_logger = ConversationLogger(max_turns=200)
    wrapper     = RAGObservabilityWrapper(rag=rag, obs=obs, conv_logger=conv_logger)

    DashboardExporter(obs, port=port, refresh_seconds=2,
                      conversation_logger=conv_logger).start()

    wrapper.add_documents(DEMO_DOCUMENTS)

    streaming_rag = StreamingRAG(
        rag_system=rag, llm=rag.llm,
        config=StreamConfig(chunk_size=4, sim_delay=0.01, max_context_docs=3),
    )

    run_query_loop(wrapper, streaming_rag,
                   iterations=iterations, delay_range=(0.2, 0.8))
    print_final_stats(obs, conv_logger)

    return wrapper, obs, conv_logger


if __name__ == "__main__":
    main()
```

---

## 11. مرجع سريع — أهم الدوال

| الدالة | الاستخدام |
|---|---|
| `obs.record(name, val)` | تسجيل قياس واحد — sync |
| `obs.record_batch(list)` | تسجيل دفعة — sync |
| `await obs.arecord(name, val)` | تسجيل قياس — async (FastAPI) |
| `await obs.arecord_batch(list)` | تسجيل دفعة — async |
| `obs.add_alert_rule(...)` | إضافة قاعدة تنبيه |
| `obs.remove_alert_rule(rule_id)` | حذف قاعدة تنبيه |
| `obs.get_metrics_summary(name)` | إحصائيات metric |
| `obs.get_active_alerts()` | التنبيهات النشطة |
| `obs.get_anomaly_stats(name)` | إحصائيات كشف الشذوذ |
| `obs.get_system_stats()` | إحصائيات النظام |
| `obs.export_prometheus()` | Prometheus text format |
| `obs.export_dict()` | JSON snapshot شامل |
| `obs.stop()` | إيقاف آمن |
| `tracer.trace(type)` | context manager للتتبع — sync |
| `tracer.atrace(type)` | context manager للتتبع — async |
| `tracer.start_span(type)` | بدء span يدوياً |
| `tracer.end_span(span_id)` | إنهاء span يدوياً |
| `tracer.inject_context(span, hdrs)` | حقن trace في HTTP headers |
| `tracer.extract_context(headers)` | استخراج trace من HTTP headers |
| `tracer.get_trace(trace_id)` | جميع spans في trace |
| `tracer.get_stats()` | إحصائيات التتبع |
| `exp_mgr.start_all()` | بدء جميع الـ exporters |
| `exp_mgr.stop_all()` | إيقاف جميع الـ exporters |

---
