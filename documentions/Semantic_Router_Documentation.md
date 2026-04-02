
> نظام توجيه دلالي ذكي يستخدم **Sentence Transformers** لتوجيه الاستعلامات النصية تلقائيًا إلى أنسب معالج بناءً على المعنى — لا على الكلمات المطابقة.



## نظرة عامة

يعمل النظام على ثلاث خطوات رئيسية:

```
المستخدم يكتب استعلامًا
        │
        ▼
  تحويل الاستعلام إلى متجه (embedding)
        │
        ▼
  مقارنة المتجه بأمثلة كل مسار (cosine similarity)
        │
        ▼
  تنفيذ معالج المسار الأعلى تشابهًا
```

**مثال سريع:**

```python
from router import SemanticRouter
from router import Route

def handle_weather(query, **kw): return f"🌤 الطقس: {query}"
def handle_news(query, **kw):    return f"📰 الأخبار: {query}"

router = SemanticRouter()
router.add_route(Route("weather", "أسئلة عن الطقس", handle_weather,
    examples=["كيف الطقس؟", "هل ستمطر؟", "درجة الحرارة اليوم"]))
router.add_route(Route("news", "آخر الأخبار", handle_news,
    examples=["ما الأخبار؟", "ماذا يحدث في العالم؟"]))

print(router.route("هل ستمطر غدًا؟"))   # → 🌤 الطقس: هل ستمطر غدًا؟
print(router.route("أخبار اليوم"))        # → 📰 الأخبار: أخبار اليوم
```

---


### `RouterConfig`

**الوصف:** `dataclass` يحتوي على جميع إعدادات الموجه في مكان واحد. يمكن تمريره عند إنشاء `SemanticRouter` أو تعديله مباشرة بعد الإنشاء.

#### جدول الإعدادات

| الإعداد | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `model_name` | `str` | `"paraphrase-multilingual-mpnet-base-v2"` | نموذج Sentence Transformers المستخدم |
| `similarity_threshold` | `float` | `0.7` | الحد الأدنى للتشابه لقبول مسار (0.0–1.0) |
| `similarity_metric` | `str` | `"cosine"` | مقياس التشابه: `"cosine"` أو `"euclidean"` |
| `use_cache` | `bool` | `True` | تفعيل كاش نتائج التوجيه |
| `cache_ttl` | `int` | `300` | مدة صلاحية الكاش بالثواني |
| `cache_max_size` | `int` | `1000` | أقصى عدد عناصر في الكاش |
| `enable_logging` | `bool` | `True` | تفعيل السجلات |
| `log_level` | `str` | `"INFO"` | مستوى السجلات: `"DEBUG"` / `"INFO"` / `"WARNING"` |
| `auto_encode_examples` | `bool` | `True` | حساب التضمينات تلقائيًا عند إضافة مسار |
| `batch_encoding` | `bool` | `True` | ترميز الأمثلة دفعةً واحدة (أسرع) |
| `batch_size` | `int` | `32` | حجم الدفعة عند الترميز |
| `top_k_alternatives` | `int` | `3` | عدد البدائل المُعادة في نتيجة التوجيه |

```python
from router import RouterConfig

config = RouterConfig(
    similarity_threshold=0.75,
    similarity_metric="cosine",
    cache_ttl=600,
    top_k_alternatives=5
)
```

---


### `RouteMetrics`

**الوصف:** `dataclass` يُسجّل إحصائيات أداء كل مسار تلقائيًا عند كل استدعاء. كل كائن `Route` يحمل نسخته الخاصة منه.

#### الحقول

| الحقل | النوع | الوصف |
|---|---|---|
| `total_calls` | `int` | إجمالي عدد مرات استدعاء المسار |
| `successful_calls` | `int` | عدد الاستدعاءات الناجحة |
| `failed_calls` | `int` | عدد الاستدعاءات الفاشلة |
| `total_processing_time` | `float` | مجموع أوقات المعالجة بالثواني |
| `average_similarity` | `float` | متوسط درجة التشابه لجميع الاستدعاءات |
| `last_used` | `Optional[float]` | Unix timestamp لآخر استخدام |

#### الخصائص (Properties)

---

##### `success_rate` → `float`

**الوصف:** يُحسب نسبة الاستدعاءات الناجحة كنسبة مئوية (0.0–100.0).

```python
metrics = route.metrics
print(f"معدل النجاح: {metrics.success_rate:.1f}%")  # → 95.0%
```

---

##### `average_processing_time` → `float`

**الوصف:** يُحسب متوسط وقت معالجة كل استدعاء بالثواني.

```python
print(f"متوسط الوقت: {metrics.average_processing_time * 1000:.2f}ms")
```

---

#### الدوال

---

##### `record_call(success, similarity, processing_time)` → `None`

**الوصف:** يُسجّل نتيجة استدعاء واحد ويُحدّث جميع الإحصائيات. يتم استدعاؤه تلقائيًا من داخل `Route.execute()`.

| Parameter | النوع | الوصف |
|---|---|---|
| `success` | `bool` | هل نجح الاستدعاء؟ |
| `similarity` | `float` | درجة التشابه التي أدت للتوجيه لهذا المسار |
| `processing_time` | `float` | وقت التنفيذ بالثواني |

```python
metrics.record_call(success=True, similarity=0.87, processing_time=0.032)
```

---

##### `reset()` → `None`

**الوصف:** يُعيد تعيين جميع المقاييس إلى الصفر.

```python
route.metrics.reset()
```

---

##### `to_dict()` → `Dict[str, Any]`

**الوصف:** يُحوّل المقاييس إلى قاموس قابل للتسلسل مع تحويل الوقت للميلي-ثانية.

```python
print(route.metrics.to_dict())
# {
#   'total_calls': 42,
#   'successful_calls': 40,
#   'failed_calls': 2,
#   'success_rate': 95.24,
#   'average_processing_time_ms': 31.5,
#   'average_similarity': 0.8341,
#   'last_used': '2024-01-15T10:30:45'
# }
```

---


### `Route`

**الوصف:** يُمثّل مسارًا واحدًا في النظام — وهو الوحدة الأساسية التي يتعامل معها الموجه. يربط بين وصف دلالي وأمثلة ومعالج قابل للتنفيذ.

---

#### `__init__`

**الوصف:** يُنشئ مسارًا جديدًا مع التحقق من صحة جميع المدخلات.

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `name` | `str` | اسم فريد للمسار (لا يجوز أن يكون فارغًا) | — |
| `description` | `str` | وصف يشرح وظيفة المسار | — |
| `handler` | `Callable` | دالة تُنفَّذ عند توجيه الاستعلام للمسار | — |
| `examples` | `Optional[List[str]]` | جمل مثال للمطابقة الدلالية | `None` |
| `metadata` | `Optional[Dict[str, Any]]` | بيانات وصفية إضافية حرة | `None` |
| `enabled` | `bool` | هل المسار مفعّل؟ | `True` |
| `priority` | `int` | أولوية المسار — أعلى قيمة = أعلى أولوية | `0` |

**يرفع:**
- `ValueError` إذا كان `name` أو `description` فارغًا
- `TypeError` إذا لم يكن `handler` قابلًا للاستدعاء

```python
from router import Route

def handle_support(query, **kw):
    return f"فريق الدعم سيرد على: {query}"

route = Route(
    name="customer_support",
    description="استفسارات خدمة العملاء والدعم الفني",
    handler=handle_support,
    examples=[
        "أريد التحدث مع الدعم",
        "عندي مشكلة في الحساب",
        "كيف أتواصل معكم؟"
    ],
    metadata={"department": "support", "sla_hours": 24},
    priority=10
)
```

---

#### إدارة الأمثلة

---

##### `add_example(example)` → `None`

**الوصف:** يُضيف مثالًا جديدًا للمسار ويُصفّر التضمينات لإعادة حسابها. يتجاهل الأمثلة المكررة تلقائيًا.

| Parameter | النوع | الوصف |
|---|---|---|
| `example` | `str` | نص المثال الجديد |

```python
route.add_example("كيف أتواصل مع فريق الدعم؟")
# ملاحظة: بعد الإضافة يجب إعادة الترميز عبر router.re_encode_route(route.name)
```

---

##### `remove_example(example)` → `bool`

**الوصف:** يُزيل مثالًا من القائمة ويُعيد `True` إذا نجح، `False` إذا لم يُوجد المثال.

```python
removed = route.remove_example("نص قديم")
print(removed)  # → True أو False
```

---

##### `update_example(old_example, new_example)` → `bool`

**الوصف:** يُحدّث مثالًا موجودًا بنص جديد مع الحفاظ على الترتيب.

| Parameter | النوع | الوصف |
|---|---|---|
| `old_example` | `str` | نص المثال المراد تحديثه |
| `new_example` | `str` | النص الجديد البديل |

```python
success = route.update_example(
    "مشكلة في الحساب",
    "عندي مشكلة في تسجيل الدخول"
)
```

---

##### `get_examples(limit)` → `List[str]`

**الوصف:** يُعيد نسخة من قائمة الأمثلة مع دعم تحديد العدد.

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `limit` | `Optional[int]` | عدد الأمثلة المراد إرجاعها | `None` (الكل) |

```python
first_3 = route.get_examples(limit=3)
all_examples = route.get_examples()
```



---

#### إدارة البيانات الوصفية والتفعيل

---

##### `add_metadata(key, value)` → `None`

**الوصف:** يُضيف أو يُحدّث قيمة في قاموس البيانات الوصفية.

```python
route.add_metadata("owner", "team_alpha")
route.add_metadata("version", 2)
```

---

##### `remove_metadata(key)` → `bool`

**الوصف:** يُزيل مفتاحًا من البيانات الوصفية، يُعيد `True` عند النجاح.

```python
route.remove_metadata("owner")
```

---

##### `enable()` → `None`

**الوصف:** يُفعّل المسار ليصبح متاحًا للتوجيه.

```python
route.enable()
```

---

##### `disable()` → `None`

**الوصف:** يُعطّل المسار فلا يُوجَّه إليه أي استعلام حتى يُعاد تفعيله.

```python
route.disable()
# الموجه سيتجاهل هذا المسار تمامًا حتى يتم route.enable()
```

---

##### `clear_embeddings()` → `None`

**الوصف:** يُصفّر التضمينات المحسوبة لإجبار الموجه على إعادة حسابها عند الاستدعاء التالي.

```python
route.clear_embeddings()
```

---

#### التنفيذ

---

##### `execute(query, similarity, **kwargs)` → `Any`

**الوصف:** يُنفّذ معالج المسار ويُسجّل المقاييس تلقائيًا. يُستدعى من الموجه وليس مباشرة في الغالب.

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `query` | `str` | الاستعلام المُمرَّر للمعالج | — |
| `similarity` | `float` | درجة التشابه (تُسجَّل في المقاييس) | `0.0` |
| `**kwargs` | `Any` | معاملات إضافية تُمرَّر للمعالج | — |

**يرفع:** `RuntimeError` إذا كان المسار معطّلًا.

```python
result = route.execute(
    query="كيف أتواصل معكم؟",
    similarity=0.87,
    user_id="usr_123"
)
```

---

#### التسلسل

---

##### `get_info()` → `Dict[str, Any]`

**الوصف:** يُعيد قاموسًا شاملًا بجميع معلومات المسار بما فيها المقاييس والطوابع الزمنية.

```python
info = route.get_info()
print(info['embeddings_ready'])  # → True
print(info['metrics']['success_rate'])  # → 95.24
```

---

##### `to_dict()` → `Dict[str, Any]`

**الوصف:** يُسلسل المسار إلى قاموس للحفظ أو النقل — **يستثني** `handler` والتضمينات.

```python
import json
data = route.to_dict()
json.dump(data, open("route_backup.json", "w"), ensure_ascii=False)
```

---

##### `Route.from_dict(data, handler)` → `Route` *(Class Method)*

**الوصف:** يُنشئ مسارًا من قاموس محفوظ مع ربطه بالمعالج المناسب.

| Parameter | النوع | الوصف |
|---|---|---|
| `data` | `Dict[str, Any]` | القاموس المحفوظ |
| `handler` | `Callable` | المعالج المراد ربطه بالمسار |

```python
data = json.load(open("route_backup.json"))
restored_route = Route.from_dict(data, handler=handle_support)
```

---


### `SimpleCache`

**الوصف:** كاش في الذاكرة بنظام TTL (Time-To-Live) وحد أقصى للحجم. يُستخدم داخليًا من `SemanticRouter` لتخزين نتائج التوجيه السابقة.

---

#### `__init__`

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `ttl` | `int` | مدة صلاحية العنصر بالثواني | `300` |
| `max_size` | `int` | الحد الأقصى لعدد العناصر | `1000` |

```python
from router import SimpleCache
cache = SimpleCache(ttl=600, max_size=500)
```

---

#### الدوال

---

##### `get(key)` → `Optional[Any]`

**الوصف:** يُعيد قيمة المفتاح إذا كانت موجودة وصالحة، أو `None` إذا انتهت صلاحيتها أو لم تُوجد.

```python
value = cache.get("route:abc123")
if value:
    print(f"Cache hit: {value}")
```

---

##### `set(key, value)` → `None`

**الوصف:** يُخزّن قيمة مع الطابع الزمني. إذا امتلأ الكاش يُطبّق سياسة الإخلاء تلقائيًا.

```python
cache.set("route:abc123", "weather_route")
```

---

##### `clear()` → `None`

**الوصف:** يُفرّغ الكاش بالكامل ويُصفّر عدادات الإصابات والإخفاقات.

```python
cache.clear()
```

---

##### `hit_rate` → `float` *(Property)*

**الوصف:** يُعيد نسبة إصابات الكاش (Cache Hits) كنسبة مئوية (0.0–100.0).

```python
print(f"Cache hit rate: {cache.hit_rate:.1f}%")
```

---

##### `_evict()` → `None` *(Private)*

**الوصف:** يُطبّق سياسة الإخلاء: يُزيل أولًا العناصر المنتهية الصلاحية، ثم أقدم 25% إذا لا يزال الكاش ممتلئًا.

---


### `RouteCollection`

**الوصف:** حاوية مُدارة للمسارات تدعم الإضافة والحذف والتحديث والترتيب حسب الأولوية. يحملها `SemanticRouter` داخليًا ويُديرها نيابةً عنك.

---

#### `add(route)` → `None`

**الوصف:** يُضيف مسارًا جديدًا. يرفض الإضافة إذا كان الاسم موجودًا مسبقًا.

| Parameter | النوع | الوصف |
|---|---|---|
| `route` | `Route` | المسار المراد إضافته |

**Return:** `ValueError` إذا كان الاسم موجودًا. استخدم `update()` للاستبدال.

```python
collection = RouteCollection()
collection.add(route)
```

---

#### `update(route)` → `None`

**الوصف:** يُضيف مسارًا أو يستبدله إذا كان موجودًا — لا يرفع استثناءات.

```python
collection.update(updated_route)  # آمن حتى لو الاسم موجود
```

---

#### `remove(name)` → `bool`

**الوصف:** يُزيل مسارًا بالاسم. يُعيد `True` إذا نجح، `False` إذا لم يُوجد.

```python
removed = collection.remove("old_route")
```

---

#### `get(name)` → `Optional[Route]`

**الوصف:** يُعيد المسار بالاسم أو `None`.

```python
route = collection.get("weather")
if route:
    print(route.description)
```

---

#### `get_enabled()` → `List[Route]`

**الوصف:** يُعيد قائمة بالمسارات المفعّلة فقط — هذه القائمة هي ما يبحث فيها الموجه.

```python
active = collection.get_enabled()
print(f"عدد المسارات النشطة: {len(active)}")
```

---

#### `get_by_priority(descending)` → `List[Route]`

**الوصف:** يُعيد جميع المسارات مرتبة حسب الأولوية.

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `descending` | `bool` | ترتيب تنازلي (أعلى أولوية أولًا) | `True` |

```python
ordered = collection.get_by_priority()
for r in ordered:
    print(f"{r.priority}: {r.name}")
```

---

#### `enable_all()` / `disable_all()` → `None`

**الوصف:** يُفعّل أو يُعطّل جميع المسارات دفعةً واحدة.

```python
collection.disable_all()   # إيقاف النظام مؤقتًا
# ... صيانة ...
collection.enable_all()    # إعادة التشغيل
```

---

#### `get_statistics()` → `Dict[str, Any]`

**الوصف:** يُعيد إحصائيات مجمّعة للمجموعة.

```python
stats = collection.get_statistics()
# {
#   'total_routes': 5,
#   'enabled_routes': 4,
#   'total_calls': 1250,
#   'total_examples': 47,
#   'average_examples_per_route': 9.4
# }
```

---


### `RoutingResult`

**الوصف:** `dataclass` يُغلّف نتيجة عملية التوجيه الكاملة. يُعاد عند استدعاء `router.route(query, return_result=True)` أو `router.test_route(query)`.

#### الحقول

| الحقل | النوع | الوصف |
|---|---|---|
| `route` | `Optional[Route]` | المسار المختار أو `None` |
| `similarity_score` | `float` | أعلى درجة تشابه وُجدت |
| `query` | `str` | الاستعلام الأصلي |
| `processing_time` | `float` | وقت التوجيه بالثواني |
| `from_cache` | `bool` | هل جاءت النتيجة من الكاش؟ |
| `alternatives` | `List[Tuple[str, float]]` | قائمة بأسماء المسارات البديلة ودرجاتها |

---

##### `matched` → `bool` *(Property)*

**الوصف:** يُعيد `True` إذا وُجد مسار مناسب (أي أن `route` ليس `None`).

```python
result = router.test_route("كيف الطقس؟")
if result.matched:
    print(f"✅ وُجّه إلى: {result.route.name}")
else:
    print(f"❌ لم يُوجد مسار. أعلى تشابه: {result.similarity_score:.3f}")
```

---

##### `to_dict()` → `Dict[str, Any]`

**الوصف:** يُحوّل النتيجة إلى قاموس مناسب للتسجيل أو إعادة الإرسال عبر API.

```python
result_dict = result.to_dict()
# {
#   'matched': True,
#   'route_name': 'weather',
#   'similarity_score': 0.8734,
#   'query': 'كيف الطقس؟',
#   'processing_time_ms': 12.4,
#   'from_cache': False,
#   'alternatives': [{'route': 'news', 'score': 0.4123}, ...]
# }
```

---


### دوال مساعدة (Module Level)

---

#### `cosine_similarity(a, b)` → `float`

**الوصف:** يحسب تشابه الكوساين بين متجهَيْن. القيم تتراوح بين `0.0` (لا تشابه) و`1.0` (تطابق تام). يتجنب القسمة على صفر تلقائيًا.

| Parameter | النوع | الوصف |
|---|---|---|
| `a` | `List[float]` | المتجه الأول |
| `b` | `List[float]` | المتجه الثاني |

```python
from router import cosine_similarity

sim = cosine_similarity([1.0, 0.5, 0.3], [0.9, 0.6, 0.2])
print(f"التشابه: {sim:.4f}")  # → 0.9987
```

---

#### `euclidean_distance(a, b)` → `float`

**الوصف:** يحسب المسافة الإقليدية بين متجهَيْن — قيم أصغر تعني تشابهًا أكبر (عكس التشابه).

```python
from router import euclidean_distance

dist = euclidean_distance([1.0, 0.0], [0.0, 1.0])
print(f"المسافة: {dist:.4f}")  # → 1.4142
```

---

### `SemanticRouter`

**الوصف:** الكلاس الرئيسي للنظام — الواجهة الوحيدة التي يحتاجها المطور. يُحمّل نموذج التضمينات، ويُدير المسارات، ويُوجّه الاستعلامات.

يدعم الاستخدام كـ **context manager** واستخدامه كـ **callable** مباشرة.

---

#### `__init__`

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `config` | `Optional[RouterConfig]` | كائن إعدادات كامل | `RouterConfig()` |
| `model_name` | `Optional[str]` | اسم النموذج (يُلغي إعداد config) | `None` |
| `similarity_threshold` | `Optional[float]` | الحد الأدنى للتشابه (يُلغي إعداد config) | `None` |

**يرفع:** `ImportError` إذا لم تكن مكتبة `sentence-transformers` مثبّتة.

```python
from router import SemanticRouter
from router import RouterConfig

# الطريقة 1: إعدادات افتراضية
router = SemanticRouter()

# الطريقة 2: تعديل سريع
router = SemanticRouter(similarity_threshold=0.8)

# الطريقة 3: إعدادات كاملة
config = RouterConfig(similarity_metric="cosine", cache_ttl=600)
router = SemanticRouter(config=config)

# الطريقة 4: context manager
with SemanticRouter() as router:
    router.add_route(my_route)
    result = router.route("استفسار")
```

---

#### إدارة المسارات

---

##### `add_route(route)` → `None`

**الوصف:** يُضيف مسارًا للموجه ويحسب تضمينات أمثلته تلقائيًا (إذا كان `auto_encode_examples=True`). يُسجّل تحذيرًا إذا أُضيف مسار بدون أمثلة.

```python
router.add_route(Route(
    name="billing",
    description="استفسارات الفواتير والمدفوعات",
    handler=handle_billing,
    examples=["كيف أدفع؟", "فاتورتي غلط", "طرق الدفع المتاحة"]
))
```

---

##### `remove_route(name)` → `bool`

**الوصف:** يُزيل مسارًا من الموجه ويمسح الكاش. يُعيد `True` عند النجاح.

```python
router.remove_route("old_route")
```

---

##### `re_encode_route(name)` → `bool`

**الوصف:** يُعيد حساب تضمينات مسار بعد تحديث أمثلته ويمسح الكاش. ضروري بعد `route.add_example()` أو `route.remove_example()`.

```python
# تحديث مثال
router.get_route("weather").add_example("هل ستمطر هذا الأسبوع؟")

# إعادة الترميز ضروري
router.re_encode_route("weather")
```

---

##### `set_fallback(handler)` → `None`

**الوصف:** يُعيّن معالجًا احتياطيًا يُستدعى عندما لا يُوجد مسار بتشابه كافٍ. بدونه يُعيد الموجه قاموس خطأ.

| Parameter | النوع | الوصف |
|---|---|---|
| `handler` | `Callable` | دالة تقبل `query: str` وتُعيد ردًّا |

**يرفع:** `TypeError` إذا لم يكن `handler` قابلًا للاستدعاء.

-
```python
def fallback(query: str):
    return f"عذرًا، لم أفهم طلبك: '{query}'. كيف يمكنني مساعدتك؟"

router.set_fallback(fallback)
```

---

##### `get_route(name)` → `Optional[Route]`

**الوصف:** يُعيد مسارًا بالاسم أو `None`.

```python
weather_route = router.get_route("weather")
```

---

##### `list_routes()` → `List[str]`

**الوصف:** يُعيد قائمة بأسماء جميع المسارات المسجّلة.

```python
print(router.list_routes())  # → ['weather', 'news', 'billing']
```

---

#### التوجيه

---

##### `route(query, return_result, **handler_kwargs)` → `Any`

**الوصف:** الدالة الرئيسية — توجّه استعلامًا للمسار الأنسب وتُنفّذ معالجه. تمر بالخطوات: فحص الكاش ← حساب التضمين ← إيجاد المسار ← التنفيذ ← المعالج الاحتياطي.

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `query` | `str` | نص الاستعلام (لا يجوز أن يكون فارغًا) | — |
| `return_result` | `bool` | إذا `True` يُعيد `RoutingResult` بدل ناتج المعالج | `False` |
| `**handler_kwargs` | `Any` | معاملات إضافية تُمرَّر للمعالج | — |

**Return:** `ValueError` إذا كان الاستعلام فارغًا.

--
```python
# تنفيذ عادي — يُعيد ناتج handler
response = router.route("ما توقع الطقس؟")

# مع معاملات إضافية للمعالج
response = router.route("استفسار", user_id="usr_42", lang="ar")

# إعادة RoutingResult بدلًا من تنفيذ المعالج
result = router.route("استفسار", return_result=True)
print(f"المسار: {result.route.name}, التشابه: {result.similarity_score:.3f}")

# استخدام مختصر عبر __call__
response = router("ما توقع الطقس؟")
```

---

##### `test_route(query)` → `RoutingResult`

**الوصف:** يختبر التوجيه بدون تنفيذ المعالج — مفيد أثناء التطوير والتشخيص.

```python
result = router.test_route("هل ستمطر؟")
print(result)
# RoutingResult(route='weather', score=0.872, time=15.3ms, cache=False)

if not result.matched:
    print(f"لم يُوجد مسار. الأقرب: {result.similarity_score:.3f}")
    print(f"البدائل: {result.alternatives}")
```

---

##### `batch_route(queries, return_results, **handler_kwargs)` → `List[Any]`

**الوصف:** يوجّه قائمة استعلامات تباعًا ويُعيد قائمة نتائج.

| Parameter | النوع | الوصف | الافتراضي |
|---|---|---|---|
| `queries` | `List[str]` | قائمة الاستعلامات | — |
| `return_results` | `bool` | إعادة `List[RoutingResult]` بدل النتائج | `False` |

```python
queries = ["كيف الطقس؟", "آخر الأخبار", "أريد الدعم"]
responses = router.batch_route(queries)

# مع تفاصيل التوجيه
results = router.batch_route(queries, return_results=True)
for r in results:
    print(f"'{r.query}' → '{r.route.name if r.matched else 'NO MATCH'}'")
```

---

#### الإحصائيات

---

##### `get_route_stats()` → `Dict[str, Any]`

**الوصف:** يُعيد تقريرًا شاملًا بإحصائيات الموجه وجميع مساراته.

```python
stats = router.get_route_stats()
print(f"إجمالي الاستعلامات: {stats['total_queries']}")
print(f"معدل النجاح: {stats['success_rate']}%")
print(f"متوسط الوقت: {stats['average_processing_time_ms']}ms")
print(f"Cache hit rate: {stats['cache']['hit_rate']}%")
```
--
```python
# هيكل القاموس المُعاد
{
    'total_queries': 500,
    'successful_routes': 470,
    'failed_routes': 30,
    'success_rate': 94.0,
    'average_processing_time_ms': 18.5,
    'routes': {
        'total_routes': 4,
        'enabled_routes': 4,
        'total_calls': 470,
        'total_examples': 38,
        'average_examples_per_route': 9.5
    },
    'config': {
        'model': 'paraphrase-multilingual-mpnet-base-v2',
        'similarity_threshold': 0.7,
        'similarity_metric': 'cosine'
    },
    'cache': {
        'hit_rate': 62.4,
        'size': 87,
        'ttl_seconds': 300
    }
}
```

---

##### `reset_statistics()` → `None`

**الوصف:** يُعيد تعيين جميع إحصائيات الموجه ويمسح الكاش.

```python
router.reset_statistics()
```

---

## أمثلة متكاملة

### مثال 1: بوت دعم متعدد الأقسام

```python

from router import SemanticRouter, Route, RouterConfig
# إعداد
config = RouterConfig(
    similarity_threshold=0.6,   # خففناه شوية علشان النتائج تظهر
    cache_ttl=600,
    top_k_alternatives=2
)

router = SemanticRouter(config=config)

# =========================
# Handlers
# =========================

def billing_handler(query, **kw):
    return {"dept": "billing", "message": f"تم تحويلك لقسم الفواتير: {query}"}

def technical_handler(query, **kw):
    return {"dept": "tech", "message": f"الدعم التقني يعالج: {query}"}

def general_handler(query, **kw):
    return {"dept": "general", "message": f"خدمة العملاء تستلم: {query}"}

def weather_handler(query, **kw):
    return {"dept": "weather", "message": f"🌤️ حالة الطقس: {query}"}

# =========================
# Routes
# =========================

router.add_route(Route(
    "billing",
    "الفواتير والمدفوعات",
    billing_handler,
    examples=[
        "فاتورتي غلط",
        "كيف أدفع؟",
        "أريد استرداد المبلغ",
        "مشكلة في الدفع"
    ],
    priority=5
))

router.add_route(Route(
    "technical",
    "الدعم التقني",
    technical_handler,
    examples=[
        "الموقع لا يعمل",
        "خطأ في التطبيق",
        "لا أستطيع تسجيل الدخول"
    ],
    priority=5
))

router.add_route(Route(
    "general",
    "الاستفسارات العامة",
    general_handler,
    examples=[
        "أريد معلومات",
        "كيف أتواصل معكم؟",
        "ما أوقات العمل؟"
    ],
    priority=5
))

# 🔥 ده المهم (حل المشكلة)
router.add_route(Route(
    "weather",
    "الطقس والتوقعات الجوية",
    weather_handler,
    examples=[
        "هل ستمطر اليوم",
        "هل ستمطر هذا الأسبوع",
        "حالة الطقس",
        "درجة الحرارة كام",
        "weather today",
        "will it rain",
        "forecast this week"
    ],
    priority=5
))

# fallback
router.set_fallback(lambda q: {"dept": "fallback", "message": "❌ لم يتم فهم الطلب"})

# =========================
# TEST
# =========================

queries = [
    "فاتورتي بها مبلغ خاطئ",
    "التطبيق يتوقف عن العمل",
    "ما ساعات عملكم؟",
    "هل ستمطر هذا الأسبوع؟",
    "what's the weather like?",
    "شيء غير مفهوم"
]

for q in queries:
    result = router.route(q, return_result=True)

    if result.matched:
        print(f"✅ [{result.route.name}] ({result.similarity_score:.3f}) → {result.response}")
    else:
        print(f"❌ fallback ({result.similarity_score:.3f}) → {result.response}")
```

---

## مرجع سريع

### جدول الدوال الأكثر استخدامًا

| الدالة | المكان | الاستخدام |
|---|---|---|
| `SemanticRouter(config)` | `semantic_router.py` | إنشاء الموجه |
| `router.add_route(route)` | `semantic_router.py` | إضافة مسار |
| `router.route(query)` | `semantic_router.py` | **التوجيه الرئيسي** |
| `router.test_route(query)` | `semantic_router.py` | اختبار بدون تنفيذ |
| `router.batch_route(queries)` | `semantic_router.py` | توجيه دفعة |
| `router.set_fallback(fn)` | `semantic_router.py` | معالج احتياطي |
| `router.re_encode_route(name)` | `semantic_router.py` | إعادة ترميز بعد تحديث |
| `router.get_route_stats()` | `semantic_router.py` | إحصائيات شاملة |
| `Route(name, desc, handler, examples)` | `route.py` | إنشاء مسار |
| `route.add_example(text)` | `route.py` | إضافة مثال |
| `route.enable()` / `route.disable()` | `route.py` | تفعيل/تعطيل |
| `route.to_dict()` / `Route.from_dict()` | `route.py` | حفظ واستعادة |

### مقارنة `route()` مقابل `test_route()`

| | `route(query)` | `test_route(query)` |
|---|---|---|
| **يُنفّذ المعالج** | ✅ | ❌ |
| **يُعيد** | ناتج `handler` | `RoutingResult` |
| **يُسجّل في الإحصائيات** | ✅ | ✅ |
| **يستخدم الكاش** | ✅ | ✅ |
| **مناسب لـ** | الإنتاج | التطوير والتشخيص |

### حالات الخطأ الشائعة

| الخطأ | السبب | الحل |
|---|---|---|
| `ImportError: sentence-transformers` | المكتبة غير مثبّتة | `pip install sentence-transformers` |
| `ValueError: Router Name Is Empty` | اسم مسار فارغ | تحقق من `name` في `Route()` |
| `TypeError: Must be callable` | handler ليس دالة | مرر دالة صالحة لـ `handler` |
| `ValueError: route already exists` | اسم مسار مكرر | استخدم `collection.update()` بدلًا من `add()` |
| `RuntimeError: route is disabled` | استدعاء مسار معطّل مباشرة | استخدم `route.enable()` أولًا |
| `ValueError: query is empty` | استعلام فارغ | تحقق من المدخل قبل الاستدعاء |

---

