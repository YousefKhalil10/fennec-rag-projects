

## نظرة عامة

نظام إضافات (Plugin System) متكامل يتيح تحميل، تسجيل، وتشغيل وحدات برمجية مستقلة بشكل ديناميكي. يدعم النظام:

- ✅ إدارة دورة الحياة الكاملة (تسجيل، تفعيل، تعطيل، إلغاء)
- ✅ نظام Hooks للأحداث مع دعم الأولويات
- ✅ فحص تلقائي للتبعيات والأذونات والتوافق
- ✅ إعادة التحميل الساخن (Hot Reload) عند تعديل الملفات
- ✅ إحصائيات أداء تفصيلية لكل إضافة
- ✅ تنفيذ متوازي (Batch Execution)
- ✅ إعادة المحاولة التلقائية (Auto Retry) عند الفشل
- ✅ نظام أذونات دقيق لكل إضافة

---



---

## الأنواع الأساسية


---

### `PluginStatus`

**الوصف:** تعداد (Enum) يمثل الحالات الممكنة لأي إضافة طوال دورة حياتها.

| القيمة | النص | المعنى |
|--------|------|---------|
| `DISABLED` | `"disabled"` | الإضافة معطلة |
| `ENABLED` | `"enabled"` | الإضافة تعمل بشكل طبيعي |
| `LOADING` | `"loading"` | جارٍ تحميل الإضافة |
| `ERROR` | `"error"` | الإضافة في حالة خطأ |
| `UPDATING` | `"updating"` | جارٍ تحديث الإضافة |
| `DEPRECATED` | `"deprecated"` | الإضافة قديمة وغير مدعومة |
| `INITIALIZING` | `"initializing"` | جارٍ تهيئة الإضافة |

**مثال:**
```python
from plugins import PluginStatus

if plugin.status == PluginStatus.ERROR:
    print("الإضافة بها خطأ:", plugin.error_message)

if plugin.status == PluginStatus.ENABLED:
    print("الإضافة تعمل بشكل طبيعي")
```

---

### `PluginPriority`

**الوصف:** تعداد يحدد أولوية تنفيذ الإضافات في نظام Hooks. **كلما زادت القيمة، ارتفعت الأولوية.**

| القيمة | الرقم | الاستخدام المقترح |
|--------|-------|------------------|
| `CRITICAL` | `1000` | للعمليات الحرجة التي يجب تنفيذها أولاً |
| `HIGH` | `100` | للعمليات ذات الأهمية العالية |
| `NORMAL` | `50` | الاستخدام العام (القيمة الافتراضية) |
| `LOW` | `10` | للعمليات الثانوية |
| `BACKGROUND` | `1` | للمهام الخلفية التي تنفذ أخيراً |

**مثال:**
```python
from plugins import PluginPriority

# تسجيل hook بأولوية عالية (ينفذ قبل غيره)
manager.add_hook("data_processed", my_critical_handler, priority=PluginPriority.CRITICAL.value)

# hook خلفي (ينفذ أخيراً)
manager.add_hook("data_processed", my_log_handler, priority=PluginPriority.BACKGROUND.value)
```

---

### `PermissionType`

**الوصف:** تعداد يمثل أنواع الأذونات التي يمكن منحها أو سحبها من الإضافات.

| القيمة | النص | المعنى |
|--------|------|---------|
| `FILE_READ` | `"file_read"` | قراءة الملفات |
| `FILE_WRITE` | `"file_write"` | الكتابة على الملفات |
| `NETWORK_ACCESS` | `"network_access"` | الوصول للشبكة |
| `SYSTEM_CALL` | `"system_call"` | استدعاء أوامر النظام |
| `DATABASE_ACCESS` | `"database_access"` | الوصول لقاعدة البيانات |
| `USER_DATA_ACCESS` | `"user_data_access"` | الوصول لبيانات المستخدم |

**مثال:**
```python
from plugins import PermissionType

# منح أذونات محددة لإضافة
manager.grant_permission("my_plugin", PermissionType.FILE_READ.value)
manager.grant_permission("my_plugin", PermissionType.NETWORK_ACCESS.value)

# سحب إذن
manager.revoke_permission("my_plugin", PermissionType.NETWORK_ACCESS.value)
```

---

### `PluginMetadata`

**الوصف:** داتا كلاس (dataclass) يحتوي على جميع البيانات الوصفية للإضافة. يتحقق تلقائياً من صحة البيانات عند الإنشاء.

#### المعاملات

| المعامل | النوع | القيمة الافتراضية | الوصف | مطلوب |
|---------|-------|------------------|-------|--------|
| `name` | `str` | — | اسم الإضافة (فريد) | ✅ |
| `version` | `str` | — | الإصدار بصيغة `X.Y.Z` (semantic versioning) | ✅ |
| `author` | `str` | — | اسم المطور أو المؤسسة | ✅ |
| `description` | `str` | — | وصف وظيفة الإضافة | ✅ |
| `dependencies` | `List[str]` | `[]` | أسماء الإضافات التي تعتمد عليها | ❌ |
| `required_hooks` | `List[str]` | `[]` | أحداث Hooks المطلوبة | ❌ |
| `permissions` | `List[str]` | `[]` | الأذونات المطلوبة (من `PermissionType`) | ❌ |
| `min_system_version` | `str` | `"1.0.0"` | أدنى إصدار نظام متوافق معه | ❌ |
| `max_system_version` | `str` | `"999.0.0"` | أعلى إصدار نظام متوافق معه | ❌ |
| `tags` | `List[str]` | `[]` | وسوم تصنيفية | ❌ |
| `homepage` | `str` | `""` | رابط صفحة الإضافة | ❌ |
| `license` | `str` | `"MIT"` | نوع الرخصة | ❌ |
| `created_at` | `datetime \| None` | `datetime.now()` | تاريخ الإنشاء | ❌ |
| `updated_at` | `datetime \| None` | `datetime.now()` | تاريخ آخر تحديث | ❌ |

> ⚠️ Return `ValueError` إذا كان الاسم أو الوصف أو المؤلف فارغاً، أو إذا كان الإصدار بصيغة غير صحيحة.

---

#### الدوال

##### `is_compatible_with(system_version)`

**الوصف:** يتحقق إذا كانت الإضافة متوافقة مع إصدار نظام معين.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `system_version` | `str` | إصدار النظام للفحص (مثال: `"2.1.0"`) |

** Return:** `bool`

---

##### `to_dict()`

**الوصف:** تحويل كائن `PluginMetadata` إلى قاموس Python قابل للتسلسل (serialization) للتخزين أو النقل.

**Return:** `Dict[str, Any]`

---

##### `from_dict(data)` *(class method)*

**الوصف:** إنشاء كائن `PluginMetadata` من قاموس (عكس `to_dict`). يحوّل حقول التواريخ من نص إلى `datetime` تلقائياً.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `data` | `Dict[str, Any]` | القاموس المحتوي على بيانات الإضافة |

**Return :** `PluginMetadata`

---

**مثال كامل:**
```python
from plugins import PluginMetadata, PermissionType

# إنشاء metadata
metadata = PluginMetadata(
    name="weather_plugin",
    version="1.2.0",
    author="Ahmed Ali",
    description="إضافة لجلب بيانات الطقس من API خارجي",
    dependencies=["http_client_plugin"],
    permissions=[PermissionType.NETWORK_ACCESS.value],
    min_system_version="1.5.0",
    tags=["weather", "api", "data"],
    homepage="https://github.com/example/weather-plugin",
    license="MIT"
)

# فحص التوافق
print(metadata.is_compatible_with("2.0.0"))  # True
print(metadata.is_compatible_with("1.0.0"))  # False (أقل من min_system_version)

# التحويل للقاموس والعودة
data = metadata.to_dict()
restored = PluginMetadata.from_dict(data)
print(restored.name)  # "weather_plugin"
```

---

### `PluginConfig`

**الوصف:** داتا كلاس يحتوي على إعدادات سلوك الإضافة القابلة للتخصيص.

#### المعاملات

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `enabled` | `bool` | `True` | هل الإضافة مفعلة عند التسجيل |
| `auto_update` | `bool` | `False` | التحديث التلقائي |
| `timeout` | `float` | `30.0` | مهلة التنفيذ بالثواني |
| `max_retries` | `int` | `3` | أقصى عدد لإعادة المحاولة عند الفشل |
| `custom_settings` | `Dict[str, Any]` | `{}` | إعدادات مخصصة إضافية |

#### `validate()`

**الوصف:** التحقق من صحة الإعدادات. يرفع `ValueError` إذا كانت `timeout` سالبة أو صفراً، أو إذا كانت `max_retries` سالبة.

**Return:** `bool` — دائماً `True` إذا نجح الفحص

**مثال:**
```python
from plugins import PluginConfig

config = PluginConfig(
    enabled=True,
    timeout=60.0,
    max_retries=5,
    custom_settings={"api_key": "xyz", "region": "eu"}
)

config.validate()  # لا يرفع استثناء
print(config.timeout)  # 60.0
```

---

## كلاس الإضافة


---

### الاستثناءات

#### `PluginError`

استثناء مخصص لأخطاء الإضافات العامة. يرث من `Exception`.

#### `PluginTimeoutError`

استثناء خاص بتجاوز مهلة التنفيذ. يرث من `PluginError`.

```python
from plugins import PluginError, PluginTimeoutError

try:
    await manager.execute_plugin("slow_plugin")
except PluginTimeoutError:
    print("انتهت مهلة التنفيذ!")
except PluginError as e:
    print("خطأ عام:", e)
```

---

### `Plugin`

**الوصف:** الكلاس المجرد (Abstract Base Class) الذي يجب أن ترث منه جميع الإضافات. يوفر آليات التنفيذ الآمن، الإحصائيات، وتتبع الأخطاء.

#### `__init__`

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `metadata` | `PluginMetadata` | البيانات الوصفية للإضافة (مطلوب) |
| `config` | `PluginConfig \| None` | إعدادات الإضافة (اختياري، يستخدم الافتراضي إذا لم يُحدد) |

> ⚠️ Return `TypeError` إذا لم يكن `metadata` من نوع `PluginMetadata`.

---

#### الدوال المجردة (يجب تطبيقها في الفئات الفرعية)

##### `initialize()` *(async, abstract)*

**الوصف:** تهيئة الإضافة وإعداد مواردها (اتصالات، ملفات، إلخ). يُستدعى تلقائياً عند التسجيل في `PluginManager`.

**Return:** `bool` — `True` إذا نجحت التهيئة

---

##### `execute(**kwargs)` *(async, abstract)*

**الوصف:** المنطق الرئيسي للإضافة. يُستدعى عند تشغيل الإضافة.

**المعاملات:** أي معاملات يحتاجها منطق الإضافة عبر `**kwargs`

**Return:** `Any`

---

##### `cleanup()` *(async, abstract)*

**الوصف:** تنظيف وتحرير الموارد (إغلاق الاتصالات، حذف الملفات المؤقتة). يُستدعى عند إلغاء تسجيل الإضافة.

---

#### الدوال الجاهزة (لا تحتاج لتطبيق)

##### `safe_execute(**kwargs)` *(async)*

**الوصف:** تنفيذ آمن يشمل فحص الحالة، تطبيق مهلة الـ timeout، ومنع التنفيذ المتزامن (باستخدام `asyncio.Lock`). يُحدّث الإحصائيات تلقائياً.

**يرفع:**
- `PluginError` — إذا كانت الإضافة معطلة أو في حالة خطأ
- `PluginTimeoutError` — عند تجاوز `config.timeout`
- `PluginError` — عند أي خطأ آخر أثناء التنفيذ

---

##### `retry_execute(**kwargs)` *(async)*

**الوصف:** تنفيذ مع إعادة المحاولة التلقائية عند الفشل باستخدام Exponential Backoff (انتظار متزايد بين المحاولات: 1s، 2s، 4s...).

عدد المحاولات محدد بـ `config.max_retries`.

**Return:** آخر `PluginError` إذا فشلت جميع المحاولات

---

##### `reset_stats()`

**الوصف:** إعادة تعيين جميع إحصائيات التنفيذ (العدادات، الأوقات، سجل الأخطاء) إلى قيمها الابتدائية.

---

##### `get_stats()`

**الوصف:** إرجاع قاموس شامل بإحصائيات الإضافة.

**Return:** `Dict[str, Any]` يحتوي على:

| المفتاح | الوصف |
|---------|-------|
| `name` | اسم الإضافة |
| `version` | الإصدار |
| `status` | الحالة الحالية |
| `enabled` | هل مفعلة |
| `execution_stats` | `{total_executions, successful, failed, success_rate}` |
| `timing_stats` | `{total_time, average_time, min_time, max_time, last_time}` |
| `timestamps` | `{initialized_at, last_executed_at, last_error_at}` |
| `current_error` | رسالة آخر خطأ |
| `recent_errors` | عدد الأخطاء الأخيرة في السجل |

---

##### `get_health_status()`

**الوصف:** تقييم صحة الإضافة بناءً على معدل نجاح التنفيذ.

**Return:** `Dict[str, Any]`:

| المفتاح | الوصف |
|---------|-------|
| `health` | `"excellent"` / `"good"` / `"medium"` / `"weak"` / `"not executed"` |
| `score` | درجة الصحة (0-100) |
| `status` | الحالة الحالية |
| `enabled` | هل مفعلة |
| `has_errors` | هل يوجد خطأ حالي |
| `error_count` | عدد الإخفاقات |

> معدل النجاح ≥ 95% → "excellent" | ≥ 80% → "good" | ≥ 60% → "medium" | أقل → "weak"

---

**مثال — إنشاء إضافة مخصصة:**
```python
import asyncio
from plugins import Plugin
from plugins import PluginMetadata, PluginConfig, PermissionType

class WeatherPlugin(Plugin):

    def __init__(self):
        metadata = PluginMetadata(
            name="weather_plugin",
            version="1.0.0",
            author="Ahmed",
            description="جلب بيانات الطقس",
            permissions=[PermissionType.NETWORK_ACCESS.value]
        )
        config = PluginConfig(timeout=15.0, max_retries=2)
        super().__init__(metadata, config)
        self.api_client = None

    async def initialize(self) -> bool:
        print("✅ تهيئة إضافة الطقس...")
        self.api_client = {}  # إنشاء اتصال
        return True

    async def execute(self, city: str = "Cairo") -> dict:
        print(f"🌤️ جلب طقس: {city}")
        return {"city": city, "temp": 28, "condition": "sunny"}

    async def cleanup(self):
        print("🧹 تنظيف موارد إضافة الطقس")
        self.api_client = None


# الاستخدام
async def main():
    plugin = WeatherPlugin()

    # تنفيذ آمن
    result = await plugin.safe_execute(city="Riyadh")
    print(result)  # {'city': 'Riyadh', 'temp': 28, 'condition': 'sunny'}

    # الإحصائيات
    stats = plugin.get_stats()
    print(stats["execution_stats"]["success_rate"])  # 100.00%

    # حالة الصحة
    health = plugin.get_health_status()
    print(health["health"])  # "excellent"

asyncio.run(main())
```

---

## مدير الإضافات


---

### `PluginManager`

**الوصف:** المركز الرئيسي لإدارة دورة حياة الإضافات بالكامل. يتضمن تسجيل الإضافات، تشغيل Hooks، إدارة التبعيات والأذونات، Hot Reload، والإحصائيات.

---

#### `__init__`

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `plugins_dir` | `str` | `"plugins"` | مسار المجلد الذي يحتوي على ملفات الإضافات |
| `safe_mode` | `bool` | `False` | وضع آمن يمنع تشغيل إضافات مشكوك فيها |
| `system_version` | `str` | `"1.0.0"` | إصدار النظام للتحقق من توافق الإضافات |
| `auto_discover` | `bool` | `True` | اكتشاف وتسجيل الإضافات تلقائياً من `plugins_dir` عند البدء |

> ⚠️ `auto_discover=True` يستدعي `discover_plugins()` كـ async task عند إنشاء المدير.

---

#### إدارة دورة الحياة

##### `register_plugin(plugin)` *(async)*

**الوصف:** تسجيل إضافة جديدة في المدير مع إجراء فحوصات شاملة تتضمن: التوافق مع إصدار النظام، التبعيات، الأذونات، ثم تهيئة الإضافة.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `plugin` | `Plugin` | كائن الإضافة المراد تسجيله |

**القيمة المُعادة:** `bool` — `True` إذا نجح التسجيل

**الخطوات الداخلية:**
1. التحقق من عدم التسجيل المسبق
2. فحص التوافق مع `system_version`
3. فحص التبعيات (مع محاولة التثبيت من Marketplace)
4. فحص الأذونات الممنوحة
5. استدعاء `plugin.initialize()`
6. تحديث رسم التبعيات وإطلاق hook `plugin_registered`

---

##### `unregister_plugin(name, force=False)` *(async)*

**الوصف:** إلغاء تسجيل إضافة مع تنظيف جميع مواردها.

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `name` | `str` | — | اسم الإضافة |
| `force` | `bool` | `False` | إجبار الإلغاء حتى لو كانت إضافات أخرى تعتمد عليها |

**Return:** `bool`

> بدون `force=True`، يرفض الإلغاء إذا وُجدت إضافات تعتمد على هذه الإضافة.

---

##### `enable_plugin(name)` *(async)*

**الوصف:** تفعيل إضافة معطلة. يتحقق أولاً من توفر تبعياتها.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `name` | `str` | اسم الإضافة |

**Return:** `bool`

---

##### `disable_plugin(name)` *(async)*

**الوصف:** تعطيل إضافة مفعلة دون إلغاء تسجيلها.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `name` | `str` | اسم الإضافة |

**Return:** `bool`

---

##### `shutdown()` *(async)*

**الوصف:** إيقاف المدير بشكل آمن: يعطّل Hot Reload ثم يلغي تسجيل جميع الإضافات بالترتيب.

> يجب استدعاؤها عند إنهاء التطبيق لضمان تنظيف جميع الموارد.

---

#### تنفيذ الإضافات

##### `execute_plugin(name, use_retry=False, **kwargs)` *(async)*

**الوصف:** تنفيذ إضافة محددة مع قياس الأداء وتسجيل النتيجة في Analytics.

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `name` | `str` | — | اسم الإضافة |
| `use_retry` | `bool` | `False` | استخدام `retry_execute` بدلاً من `safe_execute` |
| `**kwargs` | `Any` | — | المعاملات التي تمرر لدالة `execute` |

**Return:** نتيجة تنفيذ الإضافة، أو `None` إذا كانت معطلة

**Return:** `PluginManagerError` إذا لم تكن الإضافة مسجلة

---

##### `execute_batch(plugin_names, **kwargs)` *(async)*

**الوصف:** تنفيذ عدة إضافات بشكل متوازي (concurrent) في نفس الوقت.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `plugin_names` | `List[str]` | قائمة بأسماء الإضافات للتنفيذ |
| `**kwargs` | `Any` | معاملات مشتركة لجميع الإضافات |

**Return:** `Dict[str, Any]` — قاموس `{اسم_الإضافة: النتيجة}`. عند خطأ في إضافة معينة، يحتوي المدخل على `{'error': رسالة_الخطأ}`.

---

#### نظام Hooks

##### `add_hook(event, callback, priority=NORMAL)` *(sync)*

**الوصف:** تسجيل دالة استجابة (callback) لحدث معين. تُرتب الـ callbacks تلقائياً حسب الأولوية.

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `event` | `str` | — | اسم الحدث (مثال: `"plugin_registered"`) |
| `callback` | `Callable` | — | الدالة المراد تنفيذها (sync أو async) |
| `priority` | `int` | `PluginPriority.NORMAL.value` (50) | أولوية التنفيذ |

> ⚠️ Return `ValueError` إذا لم يكن `callback` قابلاً للاستدعاء.

---

##### `remove_hook(event, callback)` *(sync)*

**الوصف:** إزالة دالة استجابة من حدث معين.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `event` | `str` | اسم الحدث |
| `callback` | `Callable` | الدالة المراد إزالتها |

**Return:** `bool` — `True` إذا وُجدت وأُزيلت

---

##### `trigger_hook(event, **kwargs)` *(async)*

**الوصف:** إطلاق حدث وتنفيذ جميع الـ callbacks المسجلة له بترتيب الأولوية. يدعم الدوال العادية (sync) وغير المتزامنة (async). يسجل النتائج والأخطاء في Analytics.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `event` | `str` | اسم الحدث |
| `**kwargs` | `Any` | البيانات المرسلة للـ callbacks |

**Return:** `List[Any]` — نتائج جميع الـ callbacks

**الأحداث المدمجة (Built-in Events):**

| الحدث | متى يُطلق | البيانات المرسلة |
|-------|-----------|-----------------|
| `plugin_registered` | بعد تسجيل ناجح | `plugin=Plugin` |
| `plugin_unregistering` | قبل إلغاء التسجيل | `plugin=Plugin` |
| `plugin_unregistered` | بعد إلغاء التسجيل | `plugin_name=str` |
| `plugin_enabled` | عند تفعيل إضافة | `plugin=Plugin` |
| `plugin_disabled` | عند تعطيل إضافة | `plugin=Plugin` |
| `plugin_executed` | بعد تنفيذ ناجح | `plugin=Plugin, result=Any` |

---

#### الاكتشاف وإعادة التحميل

##### `discover_plugins()` *(async)*

**الوصف:** البحث تلقائياً في مجلد `plugins_dir` عن ملفات Python تحتوي على فئات ترث من `Plugin`، ثم إنشائها وتسجيلها. يتجاهل الملفات التي تبدأ بـ `_`.

**Return:** `List[str]` — أسماء الإضافات التي اكتُشفت وسُجِّلت بنجاح

---

##### `reload_plugin(name)` *(async)*

**الوصف:** إعادة تحميل إضافة من الملف مع الحفاظ على إعداداتها الحالية.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `name` | `str` | اسم الإضافة لإعادة تحميلها |

**Return:** `bool`

---

##### `enable_hot_reload(check_interval=5.0)` *(async)*

**الوصف:** تفعيل مراقبة الملفات وإعادة التحميل التلقائي عند تعديل ملف إضافة.

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `check_interval` | `float` | `5.0` | فترة الفحص بالثواني |

---

##### `disable_hot_reload()` *(async)*

**الوصف:** إيقاف مراقبة الملفات وإلغاء مهمة Hot Reload الخلفية.

---

#### نظام التبعيات

##### `get_dependency_tree(plugin_name, max_depth=10)`

**الوصف:** الحصول على شجرة التبعيات الكاملة لإضافة معينة بشكل هرمي. يكشف التبعيات الدائرية (circular dependencies).

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `plugin_name` | `str` | — | اسم الإضافة |
| `max_depth` | `int` | `10` | أقصى عمق للبحث |

**Return:** `Dict` هرمي يمثل الشجرة

---

##### `get_load_order()`

**الوصف:** حساب ترتيب تحميل الإضافات الصحيح باستخدام **Topological Sort** بحيث تُحمَّل التبعيات قبل الإضافات التي تعتمد عليها.

**Return:** `List[str]` — أسماء الإضافات بالترتيب الصحيح للتحميل

---

#### نظام الأذونات

##### `grant_permission(plugin_name, permission)`

**الوصف:** منح إذن محدد لإضافة.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `plugin_name` | `str` | اسم الإضافة |
| `permission` | `str` | الإذن (من `PermissionType.value`) |

---

##### `revoke_permission(plugin_name, permission)`

**الوصف:** سحب إذن من إضافة.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `plugin_name` | `str` | اسم الإضافة |
| `permission` | `str` | الإذن المراد سحبه |

---

##### `grant_all_permissions(plugin_name)`

**الوصف:** منح جميع الأذونات التي طلبتها الإضافة في `metadata.permissions` دفعة واحدة.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `plugin_name` | `str` | اسم الإضافة |

---

#### الإحصائيات والمعلومات

##### `list_plugins(status_filter=None, include_stats=False)`

**الوصف:** إرجاع قائمة بجميع الإضافات مع إمكانية التصفية حسب الحالة وإضافة الإحصائيات.

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `status_filter` | `PluginStatus \| None` | `None` | تصفية حسب الحالة |
| `include_stats` | `bool` | `False` | تضمين الإحصائيات التفصيلية |

**Return:** `List[Dict[str, Any]]`

---

##### `get_plugin_info(name)`

**الوصف:** معلومات تفصيلية شاملة عن إضافة واحدة تشمل البيانات الوصفية، الأذونات، التبعيات، الإحصائيات، وحالة الصحة.

| المعامل | النوع | الوصف |
|---------|-------|-------|
| `name` | `str` | اسم الإضافة |

**Return:** `Dict[str, Any]` أو `{}` إذا لم توجد الإضافة

---

##### `get_system_stats()`

**الوصف:** إحصائيات شاملة للنظام بأكمله.

**Return:** `Dict[str, Any]` يحتوي على:
- `total_plugins` — إجمالي الإضافات
- `enabled_plugins` — المفعّلة
- `disabled_plugins` — المعطلة
- `plugins_by_status` — تصنيف حسب الحالة
- `total_hooks` — إجمالي الـ hooks المسجلة
- `hot_reload_enabled` — هل Hot Reload مفعّل
- `safe_mode` — هل الوضع الآمن مفعّل
- `system_version` — إصدار النظام
- `analytics` — ملخص التحليلات

---

### `PluginAnalytics`

**الوصف:** نظام تحليلات لتتبع وتسجيل أحداث وأداء الإضافات والـ Hooks.

#### الدوال

| الدالة | الوصف |
|--------|-------|
| `record_plugin_registration(plugin_name)` | تسجيل تسجيل إضافة جديدة |
| `record_plugin_execution(plugin_name, execution_time, success, error=None)` | تسجيل تنفيذ إضافة مع نتيجته |
| `record_hook_execution(event, execution_time, results_count)` | تسجيل تنفيذ hook |
| `record_hook_error(event, error)` | تسجيل خطأ في hook |
| `get_summary()` | إرجاع ملخص إحصائي شامل |

**`get_summary()` Return:**
- `total_plugins_registered` — إجمالي الإضافات المسجلة
- `total_plugin_executions` — إجمالي عمليات التنفيذ
- `total_hook_executions` — إجمالي تنفيذات الـ Hooks
- `total_errors` — إجمالي الأخطاء
- `error_rate` — نسبة الأخطاء بالمئة

---

### `PluginMarketplace`

**الوصف:** واجهة لسوق الإضافات للبحث، التثبيت، والتحديث من مستودع خارجي.

> ⚠️ الدوال الثلاث حالياً هياكل جاهزة (TODO) وتحتاج لتطبيق فعلي.

#### `__init__`

| المعامل | النوع | القيمة الافتراضية | الوصف |
|---------|-------|------------------|-------|
| `registry_url` | `str` | `"https://plugins.example.com/registry"` | رابط مستودع الإضافات |

#### الدوال

| الدالة | المعاملات | الوصف |
|--------|-----------|-------|
| `search_plugins(query)` | `query: str` | البحث عن إضافات في السوق |
| `install_plugin(plugin_name, manager)` | `plugin_name: str, manager: PluginManager` | تثبيت إضافة من السوق |
| `update_plugin(plugin_name)` | `plugin_name: str` | تحديث إضافة مثبتة |

---

## امثله

### مثال 1 — إنشاء إضافة وتسجيلها

```python
import asyncio
from plugins import Plugin
from plugins import PluginMetadata, PluginConfig, PermissionType
from plugins import PluginManager

# 1. تعريف الإضافة
class DatabasePlugin(Plugin):

    def __init__(self):
        metadata = PluginMetadata(
            name="database_plugin",
            version="2.0.0",
            author="Dev Team",
            description="إضافة للتعامل مع قواعد البيانات",
            permissions=[
                PermissionType.DATABASE_ACCESS.value,
                PermissionType.FILE_READ.value
            ],
            tags=["database", "storage"]
        )
        config = PluginConfig(timeout=30.0, max_retries=3)
        super().__init__(metadata, config)
        self.connection = None

    async def initialize(self) -> bool:
        print("🔌 الاتصال بقاعدة البيانات...")
        self.connection = "db_connection"  # محاكاة
        return True

    async def execute(self, query: str = "") -> dict:
        return {"result": f"تنفيذ: {query}", "rows": 42}

    async def cleanup(self):
        self.connection = None
        print("🧹 قطع الاتصال بقاعدة البيانات")


async def main():
    # 2. إنشاء المدير
    manager = PluginManager(
        plugins_dir="my_plugins",
        system_version="2.0.0",
        auto_discover=False
    )

    # 3. منح الأذونات قبل التسجيل
    plugin = DatabasePlugin()
    manager.grant_permission("database_plugin", PermissionType.DATABASE_ACCESS.value)
    manager.grant_permission("database_plugin", PermissionType.FILE_READ.value)

    # 4. التسجيل
    success = await manager.register_plugin(plugin)
    print("تسجيل:", success)  # True

    # 5. التنفيذ
    result = await manager.execute_plugin("database_plugin", query="SELECT * FROM users")
    print(result)  # {'result': 'تنفيذ: SELECT * FROM users', 'rows': 42}

    # 6. الإحصائيات
    info = manager.get_plugin_info("database_plugin")
    print("الحالة:", info["status"])       # "enabled"
    print("الصحة:", info["health"]["health"])  # "excellent"

    # 7. إيقاف آمن
    await manager.shutdown()

asyncio.run(main())
```

---

### مثال 2 — نظام Hooks

```python
import asyncio
from plugins import PluginManager
from plugins import PluginPriority

async def main():
    manager = PluginManager(auto_discover=False)

    # hook عادي (sync)
    def on_plugin_registered(plugin):
        print(f"📢 تم تسجيل: {plugin.name}")

    # hook غير متزامن (async)
    async def on_plugin_executed(plugin, result):
        print(f"⚡ نُفِّذت {plugin.name} — النتيجة: {result}")

    # تسجيل الـ hooks
    manager.add_hook("plugin_registered", on_plugin_registered, priority=PluginPriority.HIGH.value)
    manager.add_hook("plugin_executed", on_plugin_executed, priority=PluginPriority.NORMAL.value)

    # إطلاق حدث يدوي
    await manager.trigger_hook("plugin_registered", plugin=my_plugin)

    # إزالة hook
    manager.remove_hook("plugin_registered", on_plugin_registered)

asyncio.run(main())
```

---

### مثال 3 — Hot Reload وإعادة التحميل

```python
import asyncio
from plugins import PluginManager

async def main():
    manager = PluginManager(
        plugins_dir="./plugins",
        auto_discover=True
    )

    # تفعيل Hot Reload (يفحص التغييرات كل 3 ثوانٍ)
    await manager.enable_hot_reload(check_interval=3.0)

    print("🔥 Hot Reload مفعّل — عدّل ملفات الإضافات وسترى التغييرات تلقائياً")

    # تشغيل التطبيق لمدة 30 ثانية
    await asyncio.sleep(30)

    # إيقاف Hot Reload يدوياً
    await manager.disable_hot_reload()

    # أو إعادة تحميل إضافة محددة
    await manager.reload_plugin("weather_plugin")

    await manager.shutdown()

asyncio.run(main())
```

---

### مثال 4 — تنفيذ متوازي (Batch)

```python
import asyncio
from plugins import PluginManager

async def main():
    manager = PluginManager(auto_discover=False)
    # (بعد تسجيل الإضافات...)

    # تنفيذ عدة إضافات في نفس الوقت
    results = await manager.execute_batch(
        plugin_names=["plugin_a", "plugin_b", "plugin_c"],
        input_data="بيانات مشتركة"
    )

    for name, result in results.items():
        if "error" in result:
            print(f"❌ {name}: {result['error']}")
        else:
            print(f"✅ {name}: {result}")

asyncio.run(main())
```

---

### مثال 5 — شجرة التبعيات وترتيب التحميل

```python
import asyncio
from plugins import PluginManager

async def main():
    manager = PluginManager(auto_discover=False)
    # (بعد تسجيل الإضافات...)

    # شجرة التبعيات لإضافة
    tree = manager.get_dependency_tree("advanced_plugin", max_depth=5)
    print(tree)
    # {
    #   'name': 'advanced_plugin',
    #   'dependencies': [
    #     {'name': 'base_plugin', 'dependencies': []},
    #     {'name': 'http_plugin', 'dependencies': [
    #       {'name': 'auth_plugin', 'dependencies': []}
    #     ]}
    #   ]
    # }

    # الترتيب الصحيح للتحميل
    order = manager.get_load_order()
    print("ترتيب التحميل:", order)
    # ['auth_plugin', 'base_plugin', 'http_plugin', 'advanced_plugin']

asyncio.run(main())
```

---

### مثال 6 — فحص الإحصائيات والصحة

```python
import asyncio
from plugins import PluginManager
from plugins import PluginStatus

async def main():
    manager = PluginManager(auto_discover=False)

    # قائمة الإضافات المفعلة فقط مع إحصائياتها
    active_plugins = manager.list_plugins(
        status_filter=PluginStatus.ENABLED,
        include_stats=True
    )
    for p in active_plugins:
        print(f"📦 {p['name']} v{p['version']}")
        print(f"   معدل النجاح: {p['stats']['execution_stats']['success_rate']}")
        print(f"   الصحة: {p['health']['health']}")

    # إحصائيات النظام الكاملة
    sys_stats = manager.get_system_stats()
    print("\n📊 إحصائيات النظام:")
    print(f"  الإضافات: {sys_stats['total_plugins']}")
    print(f"  المفعلة: {sys_stats['enabled_plugins']}")
    print(f"  Hot Reload: {sys_stats['hot_reload_enabled']}")
    print(f"  معدل أخطاء Analytics: {sys_stats['analytics']['error_rate']:.2f}%")

asyncio.run(main())
```

```python
# مثال كامل: تبعيات الإضافات وتشغيل PluginManager
import asyncio
from plugins import PluginManager, Plugin, PluginMetadata, PluginConfig, PluginStatus

# ----------------------------
# تعريف الإضافات التجريبية
# ----------------------------

class BasePlugin(Plugin):
    def __init__(self):
        metadata = PluginMetadata(
            name="base_plugin",
            version="1.0.0",
            author="Dev Team",
            description="إضافة أساسية",
            dependencies=[],
            tags=["core"]
        )
        super().__init__(metadata, PluginConfig(timeout=5.0))
    
    async def initialize(self) -> bool:
        self.initialized_at = __import__("datetime").datetime.now()
        return True

    async def execute(self, **kwargs):
        return "BasePlugin executed"

    async def cleanup(self):
        pass

class AuthPlugin(Plugin):
    def __init__(self):
        metadata = PluginMetadata(
            name="auth_plugin",
            version="1.0.0",
            author="Dev Team",
            description="إضافة المصادقة",
            dependencies=[],
            tags=["auth"]
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        self.initialized_at = __import__("datetime").datetime.now()
        return True

    async def execute(self, **kwargs):
        return "AuthPlugin executed"

    async def cleanup(self):
        pass

class HttpPlugin(Plugin):
    def __init__(self):
        metadata = PluginMetadata(
            name="http_plugin",
            version="1.0.0",
            author="Dev Team",
            description="إضافة HTTP",
            dependencies=["auth_plugin"],  # تعتمد على AuthPlugin
            tags=["network"]
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        self.initialized_at = __import__("datetime").datetime.now()
        return True

    async def execute(self, **kwargs):
        return "HttpPlugin executed"

    async def cleanup(self):
        pass

class AdvancedPlugin(Plugin):
    def __init__(self):
        metadata = PluginMetadata(
            name="advanced_plugin",
            version="2.0.0",
            author="Dev Team",
            description="إضافة متقدمة",
            dependencies=["base_plugin", "http_plugin"],  # تعتمد على Base و HTTP
            tags=["advanced"]
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        self.initialized_at = __import__("datetime").datetime.now()
        return True

    async def execute(self, **kwargs):
        return "AdvancedPlugin executed"

    async def cleanup(self):
        pass

# ----------------------------
# مثال تشغيل PluginManager
# ----------------------------

async def main():
    manager = PluginManager(auto_discover=False)

    # تسجيل جميع الإضافات
    await manager.register_plugin(BasePlugin())
    await manager.register_plugin(AuthPlugin())
    await manager.register_plugin(HttpPlugin())
    await manager.register_plugin(AdvancedPlugin())

    # استعراض شجرة التبعيات للإضافة المتقدمة
    tree = manager.get_dependency_tree("advanced_plugin", max_depth=5)
    print("شجرة التبعيات للـ AdvancedPlugin:")
    print(tree)
    # متوقع:
    # {
    #   'name': 'advanced_plugin',
    #   'dependencies': [
    #       {'name': 'base_plugin', 'dependencies': []},
    #       {'name': 'http_plugin', 'dependencies': [
    #           {'name': 'auth_plugin', 'dependencies': []}
    #       ]}
    #   ]
    # }

    # ترتيب التحميل الصحيح للإضافات
    order = manager.get_load_order()
    print("ترتيب التحميل:", order)
    # متوقع:
    # ['auth_plugin', 'base_plugin', 'http_plugin', 'advanced_plugin']

asyncio.run(main())
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
from plugins import (
    Plugin, PluginManager, PluginConfig,
    PluginMetadata, PluginStatus, PluginPriority, PermissionType,
)
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

# تعريف نظام RAG أولاً
rag_system=base_rag
class QueryCleanerPlugin(Plugin):
    async def initialize(self) -> bool:
        self.status = PluginStatus.ENABLED          # ← ACTIVE → ENABLED
        self.initialized_at = __import__("datetime").datetime.now()
        return True
    async def execute(self, query: str = "") -> str:
        import re
        clean = re.sub(r"\s+", " ", query).strip()
        clean = re.sub(r"[؟?!]+$", "؟", clean)
        return clean
    async def cleanup(self):
        self.status = PluginStatus.DISABLED

class RAGQueryPlugin(Plugin):
    def __init__(self, metadata, config, rag_system):
        super().__init__(metadata, config)
        self._rag = rag_system
    async def initialize(self) -> bool:
        self.status = PluginStatus.ENABLED
        self.initialized_at = __import__("datetime").datetime.now()
        return True
    async def execute(self, query: str = "") -> dict:
        retrieved = self._rag.retrieve(query)
        answer = self._rag.generate(query)
        return {
            "query": query,
            "answer": answer,
            "num_sources": len(retrieved),
            "top_score": retrieved[0][1] if retrieved else 0.0,
        }
    async def cleanup(self):
        self.status = PluginStatus.DISABLED

class AnswerValidatorPlugin(Plugin):
    async def initialize(self) -> bool:
        self.status = PluginStatus.ENABLED
        self.initialized_at = __import__("datetime").datetime.now()
        return True
    async def execute(self, result: dict = None) -> dict:
        if result is None:
            return {"valid": False, "reason": "no result"}
        answer = result.get("answer", "")
        is_valid = len(answer) > 20 and result.get("num_sources", 0) > 0
        result["is_valid"]   = is_valid
        result["word_count"] = len(answer.split())
        result["confidence"] = min(result.get("top_score", 0) * 1.2, 1.0)
        return result
    async def cleanup(self):
        self.status = PluginStatus.DISABLED

# ── إنشاء الإضافات بالمعاملات الصحيحة ──────────────────────── #
cfg = PluginConfig(enabled=True, timeout=15.0, max_retries=1)

cleaner_plugin = QueryCleanerPlugin(
    PluginMetadata(
        name="query_cleaner", version="1.0.0",          # ← "1.0" → "1.0.0"
        author="fennec-rag", description="تنظيف الاستعلام",
        permissions=[PermissionType.FILE_READ.value]    # ← القيمة الصحيحة
    ), cfg)

rag_plugin = RAGQueryPlugin(
    PluginMetadata(
        name="rag_executor", version="1.0.0",
        author="fennec-rag", description="تنفيذ RAG",
        permissions=[PermissionType.FILE_READ.value, PermissionType.FILE_WRITE.value]
    ), cfg, base_rag)

validator_plugin = AnswerValidatorPlugin(
    PluginMetadata(
        name="answer_validator", version="1.0.0",
        author="fennec-rag", description="تدقيق الإجابة",
        permissions=[PermissionType.FILE_READ.value]
    ), cfg)

# ── تسجيل الإضافات (بدون initialize() مسبق — المدير يفعل ذلك) ─ #
manager = PluginManager(plugins_dir="./plugins_dir", safe_mode=False,
                        system_version="1.0.0", auto_discover=False)

for plugin in [cleaner_plugin, rag_plugin, validator_plugin]:
    manager.grant_all_permissions(plugin.name)      # ← يجب قبل register
    await manager.register_plugin(plugin)

# ── تشغيل الـ Pipeline ───────────────────────────────────────── #
raw_queries = [
    "  ما هو الـ RAG   ؟؟؟ ",
    "كيف يعمل تعلم الآلة !!! ",
    "ما هي النماذج اللغوية الكبيرة؟",
]

print(f"\n🔌 تشغيل RAG Pipeline عبر 3 إضافات:\n")
for raw_q in raw_queries:
    print(f"━━━ استعلام: '{raw_q.strip()}' ━━━")
    clean_q    = await cleaner_plugin.safe_execute(query=raw_q)
    rag_result = await rag_plugin.safe_execute(query=clean_q)
    validated  = await validator_plugin.safe_execute(result=rag_result)
    print(f"  [Cleaner]   : '{clean_q}'")
    print(f"  [RAG]       : sources={rag_result['num_sources']}, score={rag_result['top_score']:.3f}")
    print(f"  [Validator] : valid={validated['is_valid']}, words={validated['word_count']}, conf={validated['confidence']:.2f}")
    print()

for plugin in [cleaner_plugin, rag_plugin, validator_plugin]:
    s = plugin.get_stats()
    print(f"📊 {plugin.name}: executions={s['execution_stats']['total_executions']}, "
          f"success={s['execution_stats']['success_rate']}, avg={s['timing_stats']['average_time']}")

for p in [cleaner_plugin, rag_plugin, validator_plugin]:
    await p.cleanup()
```


---

## مخطط دورة حياة الإضافة

```
     إنشاء Plugin
          │
          ▼
  grant_permission()      ← منح الأذونات (قبل التسجيل)
          │
          ▼
  register_plugin()
          │
    ┌─────┴──────┐
    │   فحوصات  │
    │ ─────────  │
    │ التوافق   │
    │ التبعيات  │
    │ الأذونات  │
    └─────┬──────┘
          │ ✅ نجح
          ▼
   initialize()           → INITIALIZING
          │
       ✅ True
          │
          ▼
      ENABLED              ← جاهز للتنفيذ
          │
    ┌─────┴──────┐
    │            │
    ▼            ▼
execute()    disable_plugin()
    │               │
    │           DISABLED
    │               │
    │          enable_plugin()
    │               │
    └───────────────┘
          │
          ▼
   (10+ أخطاء)
          │
          ▼
       ERROR
          │
          ▼
  unregister_plugin()
          │
       cleanup()
          │
          ▼
      [محذوف]
```

---

## ⚠️ ملاحظات مهمة

- **التهيئة الأولى:** تأكد من منح الأذونات **قبل** استدعاء `register_plugin()`.
- **Auto Discover:** عند `auto_discover=True`، يجب أن يكون المدير داخل event loop نشط لأن الاكتشاف يعمل كـ async task.
- **التبعيات الدائرية:** `get_dependency_tree()` يكتشفها ويضع `{'circular': True}` في الشجرة بدلاً من التكرار اللانهائي.
- **إعادة المحاولة:** `retry_execute` يستخدم Exponential Backoff — الانتظار بين المحاولات: 1s، 2s، 4s...
- **حد الأخطاء:** إضافة تتجاوز 10 إخفاقات تنتقل تلقائياً إلى حالة `ERROR` وتتوقف عن القبول.
- **إيقاف التطبيق:** دائماً استدعِ `await manager.shutdown()` عند إنهاء التطبيق لضمان تنظيف كامل للموارد.
