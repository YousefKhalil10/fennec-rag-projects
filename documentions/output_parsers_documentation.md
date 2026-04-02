
> **نظرة عامة**
>
> مكتبة تُحوّل المخرجات النصية الخام من نماذج اللغة الكبيرة (LLMs)
> إلى بيانات Python منظّمة وجاهزة للاستخدام.
> تضم سبعة parsers متخصصة، مع أداتَين متقدمتَين للتصحيح التلقائي والتسلسل.

---

## 🗺️ خريطة الاختيار السريع

| إذا أردت... | استخدم |
|---|---|
| تحليل `{...}` أو `[...]` من نص | `JSONOutputParser` |
| تحليل JSON مع التحقق الكامل من النوع | `PydanticOutputParser` |
| تحليل `key: value` بصيغة YAML | `YAMLOutputParser` |
| تحليل جدول مبيانات CSV | `CSVOutputParser` |
| تحليل قوائم مرقّمة أو نقطية | `ListOutputParser` |
| استخراج حقول محددة بالاسم من نص حر | `StructuredOutputParser` |
| إعادة المحاولة التلقائية عند الفشل | `AutoFixingParser` |
| تجربة أكثر من parser بالترتيب | `ChainedParser` |

---

## 📦 متطلبات التثبيت

```bash
# أساسي — لا يحتاج مكتبات إضافية
# (JSON / CSV / List / Structured يعملون بمكتبات Python القياسية)

# لـ YAML parser
pip install pyyaml

# لـ Pydantic parser + التحقق في JSON/YAML
pip install pydantic

# كل الميزات معاً
pip install pyyaml pydantic
```

---
---


**الوصف:**
يحتوي على الكلاس المجرد الذي يرثه جميع الـ parsers،
فئة الاستثناءات `ParsingError`، وأداتَي
`AutoFixingParser` (التصحيح التلقائي) و`ChainedParser` (التسلسل).

---

## `BaseOutputParser` *(Abstract Class)*

**الوصف:**
الكلاس الجذر لكل الـ parsers في المكتبة.
يُعرّف دالتَين إلزاميتَين (`parse` و`get_format_instructions`)
ويُقدّم ثلاث دوال جاهزة مشتركة.

---

### الدوال الإلزامية

---

#### `parse(text)` *(abstract)*

**الوصف:**
تُحلّل نصاً خاماً وتُحوّله إلى بيانات منظّمة.
**يجب** تنفيذها في كل subclass.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام الوارد من الـ LLM |

**Return:** `Any` — البيانات المنظّمة

**Return:** `ParsingError` عند الفشل

---

#### `get_format_instructions()` *(abstract)*

**الوصف:**
تُرجع تعليمات نصية تُخبر الـ LLM بالصيغة المطلوبة في مخرجاته.
تُضاف عادةً لنهاية الـ prompt.
**يجب** تنفيذها في كل subclass.

**Return:** `str` — تعليمات التنسيق

---

### الدوال الجاهزة

---

#### `async_parse(text)`

**الوصف:**
نسخة async من `parse`. تُشغّل `parse` داخل Thread Pool
لعدم حجب Event Loop. تستخدم `asyncio.get_event_loop().run_in_executor`.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `Any` — نفس نتيجة `parse`

```python
import asyncio
from output_parser import JSONOutputParser

parser = JSONOutputParser()

async def main():
    result = await parser.async_parse('{"name": "Alice", "age": 30}')
    print(result)  # {'name': 'Alice', 'age': 30}

asyncio.run(main())
```

---

#### `parse_with_prompt(text)`

**الوصف:**
تُحلّل النص وتُرجع النتيجة مع تعليمات التنسيق معاً في tuple واحد.
مفيد عند الحاجة للنتيجة وتعليمات الـ prompt في خطوة واحدة.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `tuple[Any, str]` — `(parsed_result, format_instructions)`

```python
from output_parser import JSONOutputParser

parser = JSONOutputParser()
result, instructions = parser.parse_with_prompt('{"score": 9.5}')

print(result)        # {'score': 9.5}
print(instructions)  # "Return ONLY valid JSON..."
```

---

#### `parse_or_default(text, default=None)`

**الوصف:**
تُحلّل النص وتُرجع قيمة افتراضية إذا فشل التحليل.
**لا تُطلق استثناءً أبداً** — تعتمد على `logger.warning` لتسجيل الأخطاء.

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `text` | `str` | — | النص الخام |
| `default` | `Any` | `None` | القيمة عند الفشل |

**Return:** `Any` — النتيجة أو `default`

```python
from output_parser import JSONOutputParser

parser = JSONOutputParser()

# نجاح
result = parser.parse_or_default('{"value": 42}', default={})
print(result)  # {'value': 42}

# فشل — بدون استثناء
result = parser.parse_or_default("نص عشوائي", default={"error": True})
print(result)  # {'error': True}
```

---

## `ParsingError`

**الوصف:**
الاستثناء الموحَّد الذي تُطلقه جميع الـ parsers عند الفشل.
يحمل معلومات تشخيصية تفصيلية.

#### `__init__(message, original_text=None, cause=None)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `message` | `str` | — | وصف الخطأ |
| `original_text` | `str` | `None` | النص الفاشل (يعرض أول 200 حرف فقط) |
| `cause` | `Exception` | `None` | الاستثناء الأصلي المتسبب |

**`__str__()`:** يُرجع رسالة مُركَّبة تشمل `cause` و`original_text` إن وُجدا.

```python
from output_parser import ParsingError

try:
    parser.parse("نص غير صالح")
except ParsingError as e:
    print(str(e))           # رسالة كاملة
    print(e.original_text)  # النص الفاشل
    print(e.cause)          # JSONDecodeError مثلاً
```

---

## `AutoFixingParser`

**الوصف:**
يُغلّف أي parser آخر بمنطق إعادة المحاولة.
عند فشل التحليل يُطبّق دالة `fixer` على النص ثم يعيد المحاولة
حتى `max_retries` مرة.

#### `__init__(parser, fixer=None, max_retries=2)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `parser` | `BaseOutputParser` | — | الـ parser الداخلي |
| `fixer` | `Callable[[str, str], str]` | `None` | دالة `(bad_text, instructions) → fixed_text` |
| `max_retries` | `int` | `2` | عدد محاولات الإعادة بعد الأولى |

---

#### `parse(text)`

**الوصف:**
يُحاوِل التحليل `max_retries + 1` مرة كحد أقصى.
بعد كل فشل يُطبّق `fixer` إذا تم تمريره ويعيد المحاولة.
إذا فشل الـ `fixer` نفسه يتوقف فوراً.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `Any`

**Return:** `ParsingError` إذا استُنفدت جميع المحاولات

```python
from output_parser import JSONOutputParser,AutoFixingParser
from output_parser import JSONOutputParser
import re

def my_fixer(bad_text: str, instructions: str) -> str:
    # محاولة استخراج JSON من نص مكسور
    match = re.search(r'\{.*\}', bad_text, re.DOTALL)
    return match.group(0) if match else bad_text

parser = AutoFixingParser(
    parser=JSONOutputParser(),
    fixer=my_fixer,
    max_retries=3,
)

result = parser.parse('Some noise {"name": "Alice"} more noise')
print(result)  # {'name': 'Alice'}
```

---

#### `get_format_instructions()`

**الوصف:** يُفوّض للـ parser الداخلي — يُرجع نفس تعليماته.

**Return:** `str`

---

## `ChainedParser`

**الوصف:**
يجرّب قائمة من الـ parsers بالترتيب ويُرجع أول نتيجة ناجحة.
مثالي عندما قد يُرجع الـ LLM الإجابة بإحدى صيغ متعددة.

#### `__init__(parsers)`

| Parameter | النوع | الوصف |
|---|---|---|
| `parsers` | `list[BaseOutputParser]` | قائمة الـ parsers بترتيب الأولوية |

**Return:** `ValueError` إذا كانت القائمة فارغة

---

#### `parse(text)`

**الوصف:**
يجرّب كل parser بالترتيب.
يُرجع أول نتيجة ناجحة.
إذا فشلت جميعها يُطلق `ParsingError` يحتوي على أخطاء كل parser.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `Any`

**Return:** `ParsingError` مع تفاصيل كل الأخطاء

```python
from output_parser import ChainedParser
from output_parser import JSONOutputParser
from output_parser import YAMLOutputParser
from output_parser import ListOutputParser

parser = ChainedParser([
    JSONOutputParser(),
    YAMLOutputParser(),
    ListOutputParser(),
])

r1 = parser.parse('{"items": [1, 2, 3]}')   # JSON → dict
r2 = parser.parse('items:\n  - 1\n  - 2')   # YAML → dict
r3 = parser.parse('1. Item A\n2. Item B')    # List → ['Item A', 'Item B']
```

---

#### `get_format_instructions()`

**الوصف:**
يدمج تعليمات جميع الـ parsers ويُرقّمها `[Option 1]`, `[Option 2]`...

**Return:** `str`

```python
print(parser.get_format_instructions())
# Accept any of the following formats:
#
# [Option 1] Return ONLY valid JSON...
# [Option 2] Return ONLY valid YAML...
# [Option 3] Return the result as a numbered list...
```

---
---


## `JSONOutputParser`

**الوصف:**
يستخرج JSON من نص خام باستخدام استراتيجيتَين متتاليتَين.
يدعم JSON في markdown code blocks والـ JSON المحاط بنص إضافي.
يدعم اختيارياً التحقق من نموذج Pydantic.

**استراتيجية الاستخراج (بالترتيب):**
1. يبحث عن ` ```json ... ``` ` أو ` ``` ... ``` ` في markdown
2. يستخدم `json.JSONDecoder.raw_decode` من أول `{` أو `[` يجدها

---

#### `__init__(pydantic_model=None)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `pydantic_model` | `Type[BaseModel]` | `None` | نموذج Pydantic للتحقق من البنية |

**Return:** `ImportError` إذا لم يكن Pydantic مثبتاً عند تمرير نموذج

**Return:** `ValueError` إذا لم يكن `pydantic_model` subclass من `BaseModel`

---

#### `parse(text)`

**الوصف:**
يستخرج أول JSON صالح من النص ويُحوّله لـ Python objects.
إذا تم تمرير `pydantic_model` يُرجع مثيلاً مُتحقَّقاً منه.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `dict | list | Any` أو مثيل Pydantic

**Return:** `ParsingError` في حالات:
- النص فارغ
- لا يوجد JSON صالح
- JSON غير صالح صياغةً
- البيانات لا تطابق نموذج Pydantic

```python
from output_parser import JSONOutputParser

parser = JSONOutputParser()

# JSON في منتصف نص
result = parser.parse('Here is the data: {"score": 9.5, "grade": "A"}')
print(result)  # {'score': 9.5, 'grade': 'A'}

# JSON في markdown code block
result = parser.parse('''
Sure! Here you go:
```json
{
  "products": ["apple", "banana"],
  "count": 2
}
''')
print(result)  # {'products': ['apple', 'banana'], 'count': 2}

# مع Pydantic model
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

parser_typed = JSONOutputParser(pydantic_model=User)
user = parser_typed.parse('{"name": "Bob", "age": 25}')
print(user)       # User(name='Bob', age=25)
print(user.name)  # 'Bob'
```

---

#### `get_format_instructions()`

**الوصف:**
بدون Pydantic:
 يُرجع تعليمات JSON عامة مع مثال.
مع Pydantic: يُرجع الـ JSON Schema كاملاً عبر `model_json_schema()`.

**Return:** `str`

```python
# بدون Pydantic
parser = JSONOutputParser()
print(parser.get_format_instructions())
# Return ONLY valid JSON with no surrounding text.
# Use double quotes for keys and string values.
# Example: {"key": "value", "number": 42}

# مع Pydantic
parser = JSONOutputParser(pydantic_model=User)
print(parser.get_format_instructions())
# Return ONLY valid JSON matching this schema (no extra text):
# ```json
# { "properties": {...}, "required": ["name", "age"] }
# ```
# Ensure all required fields are present and types are correct.
```

---

#### `_extract_json(text)` *(internal)*

**الوصف:**
يستخرج أول JSON صالح من النص عبر:
1. البحث عن markdown fences أولاً
2. `raw_decode` يبدأ من كل `{` أو `[` حتى يجد JSON صالحاً

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الكامل |

**Return:** `str` نص JSON، أو `None`

---

#### `_validate_pydantic_model(model)` *(internal)*

**الوصف:**
يتحقق أن `model` هو subclass فعلي من `pydantic.BaseModel`.

**Return:** `ValueError` أو `ImportError`

---
---


## `YAMLOutputParser`

**الوصف:**
يستخرج ويُحلّل YAML من نص خام باستخدام `yaml.safe_load`
(يمنع تنفيذ أي كود ضار). يدعم markdown code blocks وتحقق Pydantic.

**المتطلبات:** `pip install pyyaml`

---

#### `__init__(pydantic_model=None)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `pydantic_model` | `Type[BaseModel]` | `None` | نموذج Pydantic للتحقق |

**Return:** `ImportError` إذا لم يكن PyYAML مثبتاً (عند الإنشاء مباشرةً)
**Return:** `ValueError` إذا لم يكن `pydantic_model` من `BaseModel`

---

#### `parse(text)`

**الوصف:**
يستخرج YAML من النص ويُحلّله بأمان عبر `safe_load`.
يرفض صراحةً أي YAML يُحلَّل إلى `None`.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `dict | list | Any` أو مثيل Pydantic

**Return:** `ParsingError` في حالات:
- النص فارغ
- YAML غير صالح
- YAML يُحلَّل إلى `None`
- فشل التحقق من نموذج Pydantic

```python
from output_parser import YAMLOutputParser

parser = YAMLOutputParser()

# YAML في code block
result = parser.parse(
"""Here is the config:
yaml
host: localhost
port: 8080
debug: true
""")
print(result)  # {'host': 'localhost', 'port': 8080, 'debug': True}

# YAML عادي بدون code block
result = parser.parse('''
name: Alice
skills:
  - Python
  - Machine Learning''')

print(result)  # {'name': 'Alice', 'skills': ['Python', 'Machine Learning']}

# مع Pydantic model
from pydantic import BaseModel

class Config(BaseModel):
    host: str
    port: int

parser_typed = YAMLOutputParser(pydantic_model=Config)
config = parser_typed.parse('```yaml\nhost: prod\nport: 443\n```')
print(config)       # Config(host='prod', port=443)
print(config.port)  # 443  # 443
```

---

#### `get_format_instructions()`

**الوصف:**
بدون Pydantic: يُرجع تعليمات YAML عامة مع مثال ملفوف بـ ` ```yaml `.
مع Pydantic: يُرجع تعليمات مع أسماء الحقول وأنواعها وعلامات `# required/optional`.

**Return:** `str`

```python
# بدون Pydantic
print(YAMLOutputParser().get_format_instructions())
# Return ONLY valid YAML (no surrounding text).
# Wrap in a ```yaml code block.
# ...

# مع Pydantic
print(YAMLOutputParser(pydantic_model=Config).get_format_instructions())
# Return ONLY valid YAML matching the Config schema.
# ```yaml
# host: <string>  # required
# port: <integer>  # required
# ```
```

---

#### `_extract_yaml(text)` *(internal)*

**الوصف:**
يحذف ` ```yaml ` أو ` ```yml ` إذا وُجدا ويُرجع النص الداخلي.
إذا لم توجد code fences يُرجع النص كما هو بعد `strip()`.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الكامل |

**Return:** `str` — نص YAML النقي

---
---


## `CSVOutputParser`

**الوصف:**
يستخرج جدول CSV من نص خام ويُرجع `List[Dict]`
(كل سطر بيانات = قاموس، مفاتيحه من صف العنوان).
يكشف الفواصل تلقائياً ويتعامل مع markdown code blocks.

**الفواصل المدعومة للكشف التلقائي:** `,` | `;` | `\t` | `|`

---

#### `__init__(required_columns=None, column_types=None, delimiter=None)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `required_columns` | `List[str]` | `None` | أعمدة يجب وجودها في الجدول |
| `column_types` | `Dict[str, type]` | `None` | تحويل الأنواع مثل `{"age": int, "score": float}` |
| `delimiter` | `str` | `None` | فاصل محدد — `None` = كشف تلقائي |

**ملاحظة:** تُطبَّل الأسماء إلى lowercase داخلياً تلقائياً.

---

#### `parse(text)`

**الوصف:**
يستخرج CSV، يُطبّع مفاتيح الأعمدة (lowercase + strip)،
يتحقق من الأعمدة الإلزامية، ويُطبّق تحويلات الأنواع.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `List[Dict[str, Any]]`

**Return:** `ParsingError` في حالات:
- النص فارغ
- خطأ صياغة CSV
- لا توجد صفوف بيانات
- أعمدة مطلوبة غائبة
- فشل تحويل نوع

```python
from output_parser import CSVOutputParser

# بسيط بدون إعدادات
parser = CSVOutputParser()
result = parser.parse('''
name,age,city
Alice,30,Paris
Bob,25,London
''')
print(result)
# [{'name': 'Alice', 'age': '30', 'city': 'Paris'},
#  {'name': 'Bob',   'age': '25', 'city': 'London'}]

# مع التحقق وتحويل الأنواع
parser = CSVOutputParser(
    required_columns=["name", "age", "score"],
    column_types={"age": int, "score": float},
)
result = parser.parse('''
```csv
name,age,score
Alice,30,9.5
Bob,25,8.2
''')
print(result)
# [{'name': 'Alice', 'age': 30, 'score': 9.5},
#  {'name': 'Bob',   'age': 25, 'score': 8.2}]

# بفاصل semicolon محدد
parser = CSVOutputParser(delimiter=";")
result = parser.parse("name;country\nAlice;France\nBob;UK")
print(result[0])  # {'name': 'Alice', 'country': 'France'}
```

---

#### `get_format_instructions()`

**الوصف:**
إذا وُجدت `required_columns` يُظهرها في التعليمات مع مثال.
وإلا يُرجع تعليمات عامة.

**Return:** `str`

```python
parser = CSVOutputParser(required_columns=["name", "age", "city"])
print(parser.get_format_instructions())
# Return the result as a CSV table with a header row.
# The table must include these columns: name,age,city
#
# Example:
# name,age,city
# value_name,value_age,value_city
#
# You may wrap the CSV in a ```csv code block for clarity.
```

---

#### `_extract_csv(text)` *(internal)*

**الوصف:**
يحذف ` ```csv ` أو أي ` ``` ` عامة إذا وُجدت ويُرجع النص الداخلي.

**Return:** `str`

---

#### `_detect_delimiter(text)` *(internal)*

**الوصف:**
يُحدّد الفاصل بعدّ تكراراته في أول سطر من الـ CSV.
يُرجع الأكثر تكراراً من `[",", ";", "\t", "|"]`، أو `","` افتراضياً.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | نص CSV النقي |

**Return:** `str`

---

#### `_coerce_row(row)` *(internal)*

**الوصف:**
يُطبّق `column_types` على قاموس صف واحد.
يُطلق `ParsingError` إذا فشل التحويل مع رسالة تُحدّد العمود والقيمة.

| Parameter | النوع | الوصف |
|---|---|---|
| `row` | `Dict[str, str]` | صف البيانات كقيم نصية |

**Return:** `Dict[str, Any]`

---
---


## `ListOutputParser`

**الوصف:**
يستخرج قوائم من نص خام ويُرجع `List[str]` نظيفة.
يدعم صيغاً متعددة ويُطبّق fallback بالفاصلة إذا لم يجد علامات قائمة.

**الصيغ المدعومة:**

| الصيغة | أمثلة |
|---|---|
| مرقّمة | `1. item` أو `2) item` أو `(3) item` |
| بالحروف | `a. item` أو `b) item` |
| نقطية | `* item` أو `- item` أو `• item` أو `→ item` |
| فاصلة (fallback) | `item1, item2, item3` |

**الأنماط المُجمَّعة مسبقاً (class-level):**
- `_NUMBERED_RE` — يُطابق القوائم المرقّمة والحرفية
- `_BULLET_RE` — يُطابق القوائم النقطية
- `_SKIP_RE` — يتجاهل أسطر المقدمات مثل "Here are..."

---

#### `__init__(min_items=0, max_items=None, item_transform=None)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `min_items` | `int` | `0` | الحد الأدنى لعدد العناصر |
| `max_items` | `int` | `None` | الحد الأقصى (None = غير محدود) |
| `item_transform` | `Callable[[str], str]` | `None` | دالة تُطبَّق على كل عنصر بعد الاستخراج |

**يُطلق:** `ValueError` إذا `min_items < 0` أو `max_items < min_items`

---

#### `parse(text)`

**الوصف:**
يستخرج عناصر القائمة ثم يُطبّق `item_transform` إن وُجد،
ثم يتحقق من قيود العدد.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `List[str]`

**Return:** `ParsingError` في حالات:
- النص فارغ
- لم توجد عناصر
- عدد العناصر أقل من `min_items`
- عدد العناصر أكثر من `max_items`

```python
from output_parser import ListOutputParser

parser = ListOutputParser()
# قائمة مرقّمة
result = parser.parse('''
Here are the steps:
1. Install dependencies
2. Configure settings
3. Run the application
''')
print(result)
# ['Install dependencies', 'Configure settings', 'Run the application']

# قائمة نقطية بصيغ مختلطة
result = parser.parse('''
• High performance
* Low memory
- Multi-language support
→ Easy to use
''')
print(result)
# ['High performance', 'Low memory', 'Multi-language support', 'Easy to use']

# مع قيود وتحويل
parser = ListOutputParser(min_items=2, max_items=5, item_transform=str.upper)
result = parser.parse('1. Python\n2. JavaScript\n3. Rust')
print(result)  # ['PYTHON', 'JAVASCRIPT', 'RUST']

# fallback بالفاصلة
result = ListOutputParser().parse("Python, JavaScript, Rust, Go")
print(result)  # ['Python', 'JavaScript', 'Rust', 'Go']
```

---

#### `get_format_instructions()`

**الوصف:**
يُرجع تعليمات تطلب قائمة مرقّمة، مع إضافة قيود العدد إن وُجدت.

**Return:** `str`

```python
parser = ListOutputParser(min_items=3, max_items=5)
print(parser.get_format_instructions())
# Return the result as a numbered list, one item per line.
# Include at least 3 items.
# Include at most 5 items.
#
# Example format:
# 1. First item
# 2. Second item
# 3. Third item
```

---

#### `_extract_list_items(text)` *(internal)*

**الوصف:**
يستخرج العناصر عبر مسارَين:
1. **الأساسي:** يفحص كل سطر بـ `_match_list_item`
2. **الاحتياط:** يقسّم أول سطر غير مقدّمة بفاصلة إذا لم يجد شيئاً

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الكامل |

**Return:** `List[str]`

---

#### `_match_list_item(line)` *(internal)*

**الوصف:**
يُطابق سطراً واحداً ضد `_NUMBERED_RE` ثم `_BULLET_RE`.
يُرجع محتوى العنصر أو `None`.

| Parameter | النوع | الوصف |
|---|---|---|
| `line` | `str` | سطر واحد مُجرَّد من المسافات |

**Return:** `str | None`

---
---


## `ResponseSchema`

**الوصف:**
يُعرّف حقلاً واحداً يُراد استخراجه في `StructuredOutputParser`.

**الأنواع المدعومة:** `"str"` | `"int"` | `"float"` | `"bool"` | `"list"`

---

#### `__init__(name, description, type="str", required=True, aliases=None)`

| Parameter | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `name` | `str` | — | الاسم الرئيسي للحقل |
| `description` | `str` | — | وصف يظهر في تعليمات التنسيق |
| `type` | `str` | `"str"` | نوع القيمة |
| `required` | `bool` | `True` | هل الحقل إلزامي؟ |
| `aliases` | `List[str]` | `None` | أسماء بديلة قد يستخدمها الـ LLM |

**Return:** `ValueError` إذا كان `type` غير مدعوم

```python
from output_parser import ResponseSchema

answer = ResponseSchema("answer", "الإجابة الكاملة", type="str")

confidence = ResponseSchema(
    name="confidence",
    description="درجة الثقة من 0 إلى 1",
    type="float",
    aliases=["score", "certainty"],
)

sources = ResponseSchema("sources", "قائمة المصادر", type="list", required=False)

print(confidence.all_names)  # ['confidence', 'score', 'certainty']
print(sources.to_dict())
# {'name': 'sources', 'description': '...', 'type': 'list', 'required': False, 'aliases': []}
```

---

#### `all_names` *(property)*

**الوصف:** Return `[name] + aliases` — كل الأسماء التي تُطابق هذا الحقل.

**Return:** `List[str]`

---

#### `to_dict()`

**الوصف:** يُحوّل تعريف الحقل إلى قاموس Python.

**Return:** `Dict[str, Any]`

---

## `StructuredOutputParser`

**الوصف:**
يستخرج حقولاً محددة من نص حر باستخدام أربعة أنماط regex بالترتيب:
XML → markdown bold → colon → equals.

**الصيغ المدعومة:**

| الصيغة | مثال |
|---|---|
| XML | `<field>value</field>` |
| Markdown bold | `**field**: value` |
| Colon | `field: value` |
| Equals | `field = value` |

---

#### `__init__(response_schemas)`

| Parameter | النوع | الوصف |
|---|---|---|
| `response_schemas` | `List[ResponseSchema]` | تعريفات الحقول المراد استخراجها |

**يُطلق:** `ValueError` إذا كانت القائمة فارغة أو توجد أسماء/aliases مكرّرة

---

#### `parse(text)`

**الوصف:**
يستخرج كل الحقول المُعرَّفة من النص ويُحوّل أنواعها.
يتحقق من وجود الحقول الإلزامية.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `Dict[str, Any]`

**Return:** `ParsingError` إذا كان حقل إلزامي غائباً أو فشل تحويل النوع

```python
from output_parser import ResponseSchema, StructuredOutputParser

schemas = [
    ResponseSchema("answer",     "الإجابة",                type="str"),
    ResponseSchema("confidence", "درجة الثقة 0-1",        type="float"),
    ResponseSchema("sources",    "قائمة المصادر",         type="list",  required=False),
    ResponseSchema("verified",   "هل تم التحقق؟",         type="bool",  required=False),
]
parser = StructuredOutputParser(response_schemas=schemas)

# صيغة colon
result = parser.parse('''
answer: عاصمة فرنسا هي باريس
confidence: 0.98
sources: Wikipedia, Britannica
verified: true
''')
print(result)
# {'answer': 'عاصمة فرنسا هي باريس', 'confidence': 0.98,
#  'sources': ['Wikipedia', 'Britannica'], 'verified': True}

# صيغة XML
result = parser.parse('''
<answer>Tokyo is Japan's capital</answer>
<confidence>0.99</confidence>
''')
print(result)  # {'answer': "Tokyo is Japan's capital", 'confidence': 0.99}

# صيغة markdown bold
result = parser.parse('''
**answer**: The sun is a star
**confidence**: 0.95
''')
print(result)  # {'answer': 'The sun is a star', 'confidence': 0.95}
```

---

#### `get_format_instructions()`

**الوصف:**
يُرجع قائمة بكل الحقول مع أوصافها وإلزاميتها ومثال حي.

**Return:** `str`

```python
print(parser.get_format_instructions())
# Return the result using the following key: value format:
#
# answer: الإجابة (required)
# confidence: درجة الثقة 0-1 (required)
# sources: قائمة المصادر (optional)
# verified: هل تم التحقق؟ (optional)
#
# Example:
# answer: example text
# confidence: 0.95
# sources: item1, item2, item3
# verified: true
```

---

#### `_extract_field(text, schema)` *(internal)*

**الوصف:**
يبحث عن قيمة حقل في النص بتجربة كل `all_names` مع كل الأنماط الأربعة.
يُبسّط قيم متعددة الأسطر بـ `re.sub(r"\s+", " ", value)`.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الكامل |
| `schema` | `ResponseSchema` | تعريف الحقل |

**Return:** `str | None`

---

#### `_convert_type(value, target_type)` *(internal)*

**الوصف:**
يُحوّل قيمة نصية للنوع المطلوب.

| النوع | السلوك |
|---|---|
| `"str"` | يُرجع القيمة كما هي بعد `strip()` |
| `"int"` | يستخرج أول رقم صحيح بـ `re.search(r"-?\d+", ...)` |
| `"float"` | يستخرج أول رقم عشري بـ regex يدعم scientific notation |
| `"bool"` | `true/yes/1/correct/y/on` → `True` ؛ `false/no/0/incorrect/n/off` → `False` |
| `"list"` | يقسّم بـ `,` أو `;` أو `\|` أو `\n`، يحذف الاقتباسات المحيطة |

**Return:** `ValueError` إذا تعذّر التحويل

---

#### `_get_example_value(type_name)` *(static internal)*

**الوصف:**
Return قيمة مثال نصية لكل نوع — تُستخدم في `get_format_instructions`.

| النوع | المثال |
|---|---|
| `"str"` | `"example text"` |
| `"int"` | `"42"` |
| `"float"` | `"0.95"` |
| `"bool"` | `"true"` |
| `"list"` | `"item1, item2, item3"` |

---
---


## `PydanticOutputParser`

**الوصف:**
يُحلّل مخرج الـ LLM مباشرةً في مثيل Pydantic مُتحقَّق منه.
يُفوّض استخراج JSON لـ `JSONOutputParser` داخلياً
ثم يُطبّق كل قواعد Pydantic: أنواع، قيود، validators، قيم افتراضية.

**المتطلبات:** `pip install pydantic`

---

#### `__init__(pydantic_object)`

| Parameter | النوع | الوصف |
|---|---|---|
| `pydantic_object` | `Type[T]` | كلاس يرث من `pydantic.BaseModel` |

**Return:** `ImportError` إذا لم يكن Pydantic مثبتاً
**Return:** `TypeError` إذا لم يكن `pydantic_object` من `BaseModel`

---

#### `parse(text)`

**الوصف:**
يستدعي `JSONOutputParser(pydantic_model=...).parse(text)` داخلياً.
يُطبّق كل قواعد التحقق في نموذج Pydantic.

| Parameter | النوع | الوصف |
|---|---|---|
| `text` | `str` | النص الخام |

**Return:** `T` — مثيل من `pydantic_object`

**Return:** `ParsingError` إذا فشل استخراج JSON أو التحقق

```python
from pydantic import BaseModel, Field, field_validator
from output_parser import PydanticOutputParser

class Product(BaseModel):
    name: str = Field(..., min_length=1, description="اسم المنتج")
    price: float = Field(..., ge=0, description="السعر")
    in_stock: bool = Field(default=True)
    tags: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

parser = PydanticOutputParser(pydantic_object=Product)
# JSON في code block
product = parser.parse("""
```json
{"name": "A", "price": 10}""")
```

```python
print(product)           # Product(name='Widget Pro', price=29.99, in_stock=True, tags=['sale'])
print(product.price)     # 29.99
# قيد مُنتهَك — يُطلق ParsingError
try:
    parser.parse('{"name": "Bad", "price": -10}')
except Exception as e:
    print(f"خطأ: {e}")
```

---

#### `get_format_instructions()`

**الوصف:**
يُنشئ تعليمات تفصيلية تشمل: اسم كل حقل، نوعه، إلزاميته، وصفه،
ومثال JSON مُنشَأ تلقائياً من `_generate_example()`.

**Return:** `str`

```python
print(parser.get_format_instructions())
# Return ONLY valid JSON that matches the Product schema.
#
# Fields:
#   • name (string, required): اسم المنتج
#   • price (number, required): السعر
#   • in_stock (boolean, optional): —
#   • tags (array, optional): —
#
# Example:
# {
#   "name": "example",
#   "price": 1.0,
#   "in_stock": true,
#   "tags": []
# }
```

---

#### `get_schema()`

**الوصف:**
يُرجع JSON Schema الخام للنموذج عبر `model_json_schema()`.
مفيد للتوثيق أو الفحص البرمجي.

**Return:** `Dict[str, Any]`

```python
schema = parser.get_schema()
print(schema["properties"])
# {'name': {'type': 'string', ...}, 'price': {'type': 'number', ...}, ...}

print(schema.get("required", []))  # ['name', 'price']
```

---

#### `validate(data)`

**الوصف:**
يتحقق من قاموس Python مباشرةً بدون تحليل نص.
يستدعي `pydantic_object(**data)`.

| Parameter | النوع | الوصف |
|---|---|---|
| `data` | `Dict[str, Any]` | القاموس المراد التحقق منه |

**Return:** `T`

**Return:** `ParsingError` إذا فشل التحقق

```python
product = parser.validate({"name": "Test", "price": 19.99})
print(product)  # Product(name='Test', price=19.99, in_stock=True, tags=[])

try:
    parser.validate({"name": "", "price": -5})
except Exception as e:
    print(f"فشل: {e}")
```

---

#### `_resolve_type(field_info)` *(static internal)*

**الوصف:**
يُرجع اسم نوع مقروء من حقل JSON Schema.
يدعم `"type"` مباشر، `"anyOf"` (يُدمج الأنواع غير null)، و`"$ref"` (يُرجع آخر جزء من المسار).

| Parameter | النوع | الوصف |
|---|---|---|
| `field_info` | `Dict[str, Any]` | حقل من `properties` في JSON Schema |

**Return:** `str` مثل `"string"`, `"number"`, `"boolean"`, `"array"`

---

#### `_generate_example()` *(internal)*

**الوصف:**
يُنشئ مثال JSON من النموذج بتعيين قيمة افتراضية لكل نوع:
`string→"example"`, `integer→1`, `number→1.0`, `boolean→true`, `array→[]`, `object→{}`.

**Return:** `str` — JSON مُنسَّق بـ `indent=2`

---
---

# 🚀 أمثلة متكاملة

---

### مثال 1: Pipeline مع Pydantic

```python
from pydantic import BaseModel, Field
from output_parser import PydanticOutputParser

class MovieReview(BaseModel):
    title: str = Field(..., description="عنوان الفيلم")
    rating: float = Field(..., ge=0, le=10)
    summary: str
    recommended: bool
    pros: list[str] = Field(default_factory=list)

parser = PydanticOutputParser(pydantic_object=MovieReview)

# الـ prompt
prompt = f"راجع فيلم Inception.\n\n{parser.get_format_instructions()}"

# محاكاة مخرج الـ LLM
llm_output = '''
```json
{
  "title": "Inception",
  "rating": 9.2,
  "summary": "تحفة فنية عن عالم الأحلام",
  "recommended": true,
  "pros": ["تأثيرات مذهلة", "قصة عميقة"]
}
```
```python
review = parser.parse(llm_output)
print(f"🎬 {review.title} — {review.rating}/10")
print(f"✅ يُنصح به: {'نعم' if review.recommended else 'لا'}")
for pro in review.pros:
    print(f"  + {pro}")
```
'''

---

---

### مثال 2: استخراج جدول مبيعات

```python
from output_parser import CSVOutputParser

parser = CSVOutputParser(
    required_columns=["product", "units", "revenue"],
    column_types={"units": int, "revenue": float},
)

llm_output = """
ملخص المبيعات:
```csv
product,units,revenue
Widget A,150,4500.00
Widget B,89,3560.00
Premium Kit,45,9000.00```
"""
```
--
```python
rows = parser.parse(llm_output)
total = sum(r["revenue"] for r in rows)
print(f"{'المنتج':<15} {'الوحدات':>8} {'الإيراد':>10}")
print("-" * 35)
for r in rows:
    print(f"{r['product']:<15} {r['units']:>8,} ${r['revenue']:>8,.2f}")
print(f"\nالإجمالي: ${total:,.2f}")

```
---

### مثال 3: استخراج بيانات منظّمة

```python
from output_parser import ResponseSchema, StructuredOutputParser

parser = StructuredOutputParser([
    ResponseSchema("diagnosis",  "التشخيص الرئيسي"),
    ResponseSchema("confidence", "درجة اليقين 0-1",          type="float"),
    ResponseSchema("symptoms",   "الأعراض الملاحظة",          type="list"),
    ResponseSchema("urgent",     "يحتاج تدخلاً عاجلاً؟",     type="bool"),
    ResponseSchema("notes",      "ملاحظات إضافية",            type="str",  required=False),
])

result = parser.parse('''
diagnosis: التهاب في الجهاز التنفسي العلوي
confidence: 0.87
symptoms: سعال, حرارة, ألم في الحلق
urgent: false
notes: راحة وسوائل لمدة 3-5 أيام
''')

print(f"🩺 {result['diagnosis']}")
print(f"📊 اليقين: {result['confidence']*100:.0f}%")
print(f"🤒 الأعراض: {', '.join(result['symptoms'])}")
print(f"🚨 عاجل: {'نعم' if result['urgent'] else 'لا'}")
```

---

### مثال 4: ChainedParser + AutoFixingParser

```python
from output_parser import AutoFixingParser, ChainedParser
from output_parser import JSONOutputParser
from output_parser import YAMLOutputParser
from output_parser import ListOutputParser
import re

def quick_fixer(bad_text: str, instructions: str) -> str:
    match = re.search(r'\{.*\}', bad_text, re.DOTALL)
    return match.group(0) if match else bad_text

# يقبل أي من الصيغ الثلاث
flexible = ChainedParser([
    JSONOutputParser(),
    YAMLOutputParser(),
    ListOutputParser(),
])

# مع التصحيح التلقائي
robust = AutoFixingParser(parser=flexible, fixer=quick_fixer, max_retries=2)

print(robust.parse('{"lang": "Python"}'))           # dict
print(robust.parse('lang: Python\nver: 3.12'))       # dict
print(robust.parse('1. Python\n2. JavaScript'))      # list

# بدون استثناء عند الفشل الكامل
print(robust.parse_or_default("نص فاشل", default=[]))  # []
```

---

### مثال 5: معالجة متوازية async

```python
import asyncio
from pydantic import BaseModel
from output_parser import PydanticOutputParser

class Summary(BaseModel):
    title: str
    word_count: int
    sentiment: str

parser = PydanticOutputParser(pydantic_object=Summary)

outputs = [
    '{"title": "AI News",     "word_count": 800,  "sentiment": "positive"}',
    '{"title": "Tech Report", "word_count": 1200, "sentiment": "neutral"}',
    '{"title": "Economy",     "word_count": 950,  "sentiment": "negative"}',
]

async def process_all(texts):
    results = await asyncio.gather(
        *[parser.async_parse(t) for t in texts],
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            print(f"[خطأ]: {r}")
        else:
            print(f"📰 {r.title:<15} | {r.word_count:>5} كلمة | {r.sentiment}")

asyncio.run(process_all(outputs))
```
---

### Example With Rag System

```python
from output_parser import (
        JSONOutputParser, StructuredOutputParser, ResponseSchema,
        PydanticOutputParser, ListOutputParser,
    )

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
import json

    # ── تهيئة الـ RAG ─────────────────────────────────────────── #
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

print("\n[4a] JSON — RAG يُرجع إجابة منظمة كـ JSON")

json_parser = JSONOutputParser()

def rag_query_json(query: str) -> dict:
    retrieved = rag.retrieve(query)
    mock_llm_output = (
        f'هنا إجابتي: {{"answer": "RAG يجمع الاسترجاع مع التوليد لتحسين الدقة.", '
        f'"confidence": {round(retrieved[0][1], 2)}, '
        f'"keywords": ["RAG", "retrieval", "generation"]}}'
    )
    return json_parser.parse(mock_llm_output)

result = rag_query_json("ما هو الـ RAG؟")
print(f"  ✅ JSON result: {result}")

# ── 4b: Structured Parser ─────────────────────────────────────── #
print("\n[4b] Structured — schema محدد لإجابات الـ RAG")

schemas = [
    ResponseSchema(name="answer",    description="الإجابة الرئيسية بالعربية"),
    ResponseSchema(name="sources",   description="المصادر المستخدمة مفصولة بفاصلة"),
    ResponseSchema(name="follow_up", description="سؤال متابعة مقترح"),
]
struct_parser = StructuredOutputParser(response_schemas=schemas)

mock_structured_output = (
    "answer: النماذج اللغوية الكبيرة مثل GPT-4 وClaude تعتمد على Transformer.\n"
    "sources: doc_llm, doc_ai\n"
    "follow_up: ما الفرق بين GPT-4 وClaude؟"
)

parsed = struct_parser.parse(mock_structured_output)
print(f"  ✅ answer   : {parsed.get('answer')}")
print(f"  ✅ sources  : {parsed.get('sources')}")
print(f"  ✅ follow_up: {parsed.get('follow_up')}")

# ── 4c: Pydantic Parser ───────────────────────────────────────── #
print("\n[4c] Pydantic — التحقق الصارم من مخرجات الـ RAG")

try:
    from pydantic import BaseModel, Field
    from typing import List as TList

    class RAGAnswer(BaseModel):
        answer:     str        = Field(description="الإجابة الكاملة")
        confidence: float      = Field(ge=0.0, le=1.0, description="درجة الثقة")
        sources:    TList[str] = Field(description="معرفات المستندات المستخدمة")
        language:   str        = Field(default="ar", description="لغة الإجابة")

    pydantic_parser = PydanticOutputParser(pydantic_object=RAGAnswer)

    retrieved = rag.retrieve("ما هو تعلم الآلة؟")
    mock_rag_pydantic_out = json.dumps({
        "answer": "تعلم الآلة فرع من الذكاء الاصطناعي يتعلم من البيانات.",
        "confidence": round(retrieved[0][1], 2),
        "sources": [doc.doc_id for doc, _ in retrieved[:2]],
        "language": "ar",
    }, ensure_ascii=False)

    rag_answer = pydantic_parser.parse(mock_rag_pydantic_out)
    print(f"  ✅ answer    : {rag_answer.answer}")
    print(f"  ✅ confidence: {rag_answer.confidence}")
    print(f"  ✅ sources   : {rag_answer.sources}")
    print(f"  ✅ language  : {rag_answer.language}")

except ImportError:
    print("  ⚠️  pydantic not installed — skipping")

# ── 4d: List Parser ───────────────────────────────────────────── #
print("\n[4d] List — RAG يُرجع قائمة نقاط رئيسية")

list_parser = ListOutputParser()

mock_list_output = (
    "1. الاسترجاع الدلالي\n"
    "2. التوليد المُعزَّز\n"
    "3. النماذج اللغوية\n"
    "4. قواعد البيانات المتجهية"
)

key_points = list_parser.parse(mock_list_output)
print(f"  ✅ Key points from RAG: {key_points}")
```

---

## 📊 ملخص مقارنة الـ Parsers

| Parser | المدخل | المخرج | يحتاج مكتبة خارجية |
|---|---|---|---|
| `JSONOutputParser` | نص يحتوي `{...}` أو `[...]` | `dict / list` أو Pydantic | اختياري (pydantic) |
| `YAMLOutputParser` | نص يحتوي YAML | `dict / list / Any` أو Pydantic | pyyaml + pydantic اختياري |
| `CSVOutputParser` | نص يحتوي CSV | `List[Dict]` | — |
| `ListOutputParser` | قوائم مرقّمة/نقطية | `List[str]` | — |
| `StructuredOutputParser` | نص بـ `field: value` | `Dict[str, Any]` | — |
| `PydanticOutputParser` | نص يحتوي JSON | مثيل Pydantic | pydantic |
| `AutoFixingParser` | أي نص | نتيجة الـ parser الداخلي | — |
| `ChainedParser` | أي نص | نتيجة أول parser ناجح | — |

---

## 🔑 نقاط جوهرية

- **جميع الـ parsers** ترث من `BaseOutputParser` وتحصل مجاناً على `async_parse`, `parse_or_default`, `parse_with_prompt`
- **`ParsingError`** هو الاستثناء الموحَّد — دائماً يحمل `original_text` و`cause`
- **`AutoFixingParser`** إذا فشل الـ `fixer` نفسه يتوقف فوراً ولا يُكمل المحاولات
- **`ChainedParser`** عند الفشل الكامل يُطلق خطأ يحتوي على أخطاء **كل** الـ parsers
- **`JSONOutputParser`** يستخدم `raw_decode` — يستطيع استخراج JSON من وسط نص طويل
- **`CSVOutputParser`** يُطبّل الأعمدة إلى lowercase تلقائياً — لا حاجة لمطابقة الحالة
- **`ListOutputParser`** يُطبّق `_SKIP_RE` لتجاهل أسطر المقدمات قبل بدء القائمة
- **`PydanticOutputParser`** يُفوّض لـ `JSONOutputParser` داخلياً — أي تحسين في JSON ينعكس عليه
