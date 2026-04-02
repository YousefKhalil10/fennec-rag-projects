
## نظرة عامة

مكتبة **Prompt Templates** هي أداة متكاملة لإنشاء وإدارة قوالب النصوص المستخدمة في تطبيقات الذكاء الاصطناعي. تدعم المكتبة:

- ✅ تنسيقات متعددة: `f-string` و `jinja2`
- ✅ استخراج المتغيرات تلقائياً
- ✅ التحقق من صحة القوالب
- ✅ قوالب جاهزة للمهام الشائعة
- ✅ دعم كامل للغة العربية

---

## الوحدات الأساسية (Core)

---

### 1. BaseTemplate


**الوصف:**
الكلاس الأساسي المجرد (Abstract Base Class) الذي ترث منه جميع أنواع القوالب الأخرى في المكتبة. يوفر الواجهة المشتركة والوظائف الأساسية.

---

#### `__init__(input_variables, partial_variables)`

**الوظيفة:** تهيئة القالب الأساسي وضبط المتغيرات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `input_variables` | `Optional[List[str]]` | قائمة المتغيرات المطلوبة في القالب |
| `partial_variables` | `Optional[Dict[str, Any]]` | متغيرات معبأة مسبقاً |

```python
template = MyTemplate(
    input_variables=["name", "age"],
    partial_variables={"language": "Python"}
)
```

---

#### `format(**kwargs)` *(abstract)*

**الوظيفة:** دالة مجردة يجب تنفيذها في كل كلاس فرعي لتنسيق القالب بالمتغيرات المعطاة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | المتغيرات المراد حقنها في القالب |

**Return:** `str` - النص المنسق

---

#### `_check_missing_variables(provided_vars)`

**الوظيفة:** فحص المتغيرات المفقودة بمقارنة المتغيرات المطلوبة بالمتغيرات المُقدَّمة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `provided_vars` | `Dict[str, Any]` | المتغيرات التي قدّمها المستخدم |

**Return:** `List[str]` - قائمة بأسماء المتغيرات الناقصة

```python
template = MyTemplate(input_variables=["name", "age"])
missing = template._check_missing_variables({"name": "Ahmad"})
# missing = ["age"]
```

---

#### `partial(**kwargs)`

**الوظيفة:** إنشاء نسخة جديدة من القالب مع تعبئة بعض المتغيرات مسبقاً.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | المتغيرات المراد تعبئتها مسبقاً |

**Return:** `BaseTemplate` - نسخة جديدة من القالب

```python
template = MyTemplate(input_variables=["name", "city"])
partial_template = template.partial(city="Cairo")
result = partial_template.format(name="Ahmad")
```

---

#### `get_info()`

**الوظيفة:** استرجاع معلومات وصفية عن القالب.

**Return:** `Dict[str, Any]` - قاموس يحتوي على معلومات القالب

```python
info = template.get_info()
# {
#   'class': 'PromptTemplate',
#   'input_variables': ['name'],
#   'partial_variables': ['language'],
#   'num_inputs': 1,
#   'num_partials': 1
# }
```

---

### 2. PromptTemplate


**الوصف:**
القالب الأساسي لإنشاء نصوص الـ prompts. يدعم تنسيقي `f-string` و `jinja2`، ويستخرج المتغيرات تلقائياً، ويمكن دمج قوالب متعددة معاً.

---

#### `__init__(template, input_variables, partial_variables, template_format, validate_template)`

**الوظيفة:** تهيئة قالب النص مع ضبط جميع الإعدادات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `input_variables` | `Optional[List[str]]` | المتغيرات المطلوبة (تُستخرج تلقائياً إذا لم تُحدَّد) |
| `partial_variables` | `Optional[Dict[str, Any]]` | متغيرات معبأة مسبقاً |
| `template_format` | `str` | نوع التنسيق: `'f-string'` أو `'jinja2'` |
| `validate_template` | `bool` | التحقق من صحة القالب عند التهيئة |

```python
from prompt import PromptTemplate

template = PromptTemplate(
    template="أهلاً {name}، عمرك {age} سنة",
    template_format="f-string"
)
```

---

#### `format(**kwargs)`

**الوظيفة:** تنسيق القالب بالمتغيرات المُعطاة ودمجها مع المتغيرات المعبأة مسبقاً.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | المتغيرات المطلوبة لتعبئة القالب |

**Return:** `str` - النص المنسق

**استثناءات:** `ValueError` إذا كانت هناك متغيرات مفقودة

```python
template = PromptTemplate(template="مرحباً {name}!")
result = template.format(name="أحمد")
# "مرحباً أحمد!"
```

---

#### `partial(**kwargs)`

**الوظيفة:** إنشاء نسخة جديدة من القالب مع تعبئة بعض المتغيرات مسبقاً دون تنسيق القالب بالكامل.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | المتغيرات المراد تعبئتها مسبقاً |

**Return:** `PromptTemplate` - نسخة جديدة من القالب

```python
template = PromptTemplate(template="ترجم من {source} إلى {target}: {text}")
arabic_translator = template.partial(target="العربية")

result = arabic_translator.format(source="الإنجليزية", text="Hello World")
# "ترجم من الإنجليزية إلى العربية: Hello World"
```

---

#### `__add__(other)`

**الوظيفة:** دمج قالبين معاً باستخدام عملية الجمع `+`.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `other` | `PromptTemplate` أو `str` | القالب أو النص المراد دمجه |

**Return:** `PromptTemplate` - قالب مدمج جديد

```python
intro = PromptTemplate(template="أنت خبير في {domain}.")
task = PromptTemplate(template="أجب على: {question}")
combined = intro + task
result = combined.format(domain="الذكاء الاصطناعي", question="ما هو التعلم العميق؟")
```

---

#### `save(filepath)`

**الوظيفة:** حفظ القالب في ملف JSON.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `filepath` | `str` | مسار الملف المراد الحفظ إليه |

```python
template = PromptTemplate(template="ملخص: {text}")
template.save("templates/summarize.json")
```

---

#### `load(filepath)` *(classmethod)*

**الوظيفة:** تحميل قالب من ملف JSON محفوظ مسبقاً.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `filepath` | `str` | مسار ملف القالب |

**Return:** `PromptTemplate` - القالب المُحمَّل

```python
template = PromptTemplate.load("templates/summarize.json")
result = template.format(text="نص طويل...")
```

---

### 3. ChatPromptTemplate


**الوصف:**
قالب متخصص للمحادثات متعددة الأدوار. يدعم رسائل النظام (`system`) والمستخدم (`user`) والمساعد (`assistant`)، ويستخرج المتغيرات من جميع الرسائل تلقائياً.

---

#### `__init__(messages, input_variables, partial_variables, validate_messages)`

**الوظيفة:** تهيئة قالب المحادثة مع قائمة الرسائل.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `messages` | `List[Dict[str, str]]` | قائمة رسائل بصيغة `{"role": ..., "content": ...}` |
| `input_variables` | `Optional[List[str]]` | المتغيرات المطلوبة (تُستخرج تلقائياً) |
| `partial_variables` | `Optional[Dict[str, Any]]` | متغيرات معبأة مسبقاً |
| `validate_messages` | `bool` | التحقق من بنية الرسائل |

**الأدوار المدعومة:** `system`, `user`, `assistant`, `function`

```python
from prompt import ChatPromptTemplate

template = ChatPromptTemplate(messages=[
    {"role": "system", "content": "أنت مساعد متخصص في {domain}."},
    {"role": "user", "content": "{question}"}
])
```

---

#### `format(**kwargs)`

**الوظيفة:** تنسيق جميع رسائل القالب بالمتغيرات المُعطاة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | المتغيرات المطلوبة |

**Return:** `List[Dict[str, str]]` - قائمة الرسائل المنسقة

```python
messages = template.format(domain="الطب", question="ما أعراض الأنفلونزا؟")
# [
#   {"role": "system", "content": "أنت مساعد متخصص في الطب."},
#   {"role": "user", "content": "ما أعراض الأنفلونزا؟"}
# ]
```

---

#### `format_as_string(**kwargs)`

**الوظيفة:** تنسيق جميع الرسائل كنص واحد مدمج.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | المتغيرات المطلوبة |

**Return:** `str` - الرسائل كنص واحد

```python
text = template.format_as_string(domain="الطب", question="ما أعراض الأنفلونزا؟")
# "SYSTEM: أنت مساعد متخصص في الطب.
#
#  USER: ما أعراض الأنفلونزا؟"
```

---

#### `add_message(role, content, name)`

**الوظيفة:** إضافة رسالة جديدة إلى القالب وإعادة نسخة جديدة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `role` | `str` | دور الرسالة (`system`, `user`, `assistant`) |
| `content` | `str` | محتوى الرسالة |
| `name` | `Optional[str]` | اسم المرسل (اختياري) |

**Return:** `ChatPromptTemplate` - قالب جديد يحتوي على الرسالة المضافة

```python
template = template.add_message("user", "سؤال متابعة: {follow_up}")
```

---

#### `add_system_message(content)` / `add_user_message(content)` / `add_assistant_message(content)`

**الوظيفة:** اختصارات لإضافة رسائل بأدوار محددة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `content` | `str` | محتوى الرسالة |

```python
template = (ChatPromptTemplate.from_messages([])
    .add_system_message("أنت مساعد ذكي.")
    .add_user_message("سؤالي هو: {question}"))
```

---

#### `from_messages(messages)` *(classmethod)*

**الوظيفة:** إنشاء قالب محادثة مباشرةً من قائمة رسائل.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `messages` | `List[Dict[str, str]]` | قائمة الرسائل |

```python
template = ChatPromptTemplate.from_messages([
    {"role": "system", "content": "أنت مساعد مفيد."},
    {"role": "user", "content": "{input}"}
])
```

---

#### `from_template(template, role)` *(classmethod)*

**الوظيفة:** إنشاء قالب محادثة من نص قالب بسيط.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `role` | `str` | دور الرسالة (افتراضي: `"user"`) |

```python
template = ChatPromptTemplate.from_template("أجب عن: {question}")
```

---

### 4. FewShotPromptTemplate


**الوصف:**
قالب متخصص لتعلم Few-Shot، حيث يُنشئ تلقائياً prompts تحتوي على أمثلة توضيحية قبل السؤال الحقيقي. مفيد جداً لتوجيه النموذج نحو نمط محدد من الإجابات.

---

#### `__init__(examples, example_prompt, prefix, suffix, input_variables, example_separator, max_examples, example_selector)`

**الوظيفة:** تهيئة قالب Few-Shot بالأمثلة والقوالب المطلوبة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `examples` | `List[Dict[str, Any]]` | قائمة الأمثلة التعليمية |
| `example_prompt` | `PromptTemplate` | قالب تنسيق كل مثال |
| `prefix` | `str` | نص يُضاف قبل الأمثلة |
| `suffix` | `str` | قالب يُضاف بعد الأمثلة (يحتوي على السؤال الحقيقي) |
| `input_variables` | `Optional[List[str]]` | المتغيرات في الـ suffix |
| `example_separator` | `str` | الفاصل بين الأمثلة (افتراضي: `"\n\n"`) |
| `max_examples` | `Optional[int]` | الحد الأقصى لعدد الأمثلة |
| `example_selector` | `Optional[Callable]` | دالة اختيار الأمثلة ديناميكياً |

```python
from prompt import FewShotPromptTemplate
from prompt import PromptTemplate

example_prompt = PromptTemplate(template="سؤال: {question}\nجواب: {answer}")

examples = [
    {"question": "ما عاصمة مصر؟", "answer": "القاهرة"},
    {"question": "ما عاصمة السعودية؟", "answer": "الرياض"},
]

template = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix="أجب على الأسئلة الجغرافية:",
    suffix="سؤال: {question}\nجواب:",
    max_examples=2
)
```

---

#### `format(**kwargs)`

**الوظيفة:** تجميع الـ prefix والأمثلة والـ suffix في prompt كامل.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `**kwargs` | `Any` | متغيرات الـ suffix (السؤال الحقيقي) |

**Return:** `str` - الـ prompt الكامل

```python
result = template.format(question="ما عاصمة الإمارات؟")
# "أجب على الأسئلة الجغرافية:
#
#  سؤال: ما عاصمة مصر؟
#  جواب: القاهرة
#
#  سؤال: ما عاصمة السعودية؟
#  جواب: الرياض
#
#  سؤال: ما عاصمة الإمارات؟
#  جواب:"
```

---

#### `add_example(example)`

**الوظيفة:** إضافة مثال جديد وإعادة نسخة محدثة من القالب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `example` | `Dict[str, Any]` | المثال الجديد بنفس مفاتيح الأمثلة الأخرى |

```python
updated = template.add_example({"question": "ما عاصمة الأردن؟", "answer": "عمّان"})
```

---

#### `set_max_examples(max_examples)`

**الوظيفة:** تحديد الحد الأقصى لعدد الأمثلة المُستخدَمة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `max_examples` | `int` | العدد الأقصى للأمثلة |

```python
template = template.set_max_examples(3)
```

---

#### `from_examples(examples, example_template, suffix_template, prefix)` *(classmethod)*

**الوظيفة:** طريقة مختصرة لإنشاء قالب Few-Shot من نصوص القوالب مباشرةً.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `examples` | `List[Dict]` | قائمة الأمثلة |
| `example_template` | `str` | نص قالب المثال |
| `suffix_template` | `str` | نص قالب الـ suffix |
| `prefix` | `str` | النص التمهيدي |

```python
template = FewShotPromptTemplate.from_examples(
    examples=[{"word": "سعيد", "antonym": "حزين"}],
    example_template="الكلمة: {word}\nالمضاد: {antonym}",
    suffix_template="الكلمة: {word}\nالمضاد:",
    prefix="أعطِ مضاد كل كلمة:"
)
```

---

## الأدوات المساعدة (Utils)

---

### 5. TemplateFormatter


**الوصف:**
مجموعة أدوات لتنسيق ومعالجة النصوص والقوالب. توفر وظائف متعددة لتنظيف النصوص وتعديلها وعرضها.

---

#### `__init__(template_format)`

**الوظيفة:** تهيئة المنسق بنوع التنسيق المطلوب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template_format` | `str` | نوع التنسيق: `'f-string'` أو `'jinja2'` |

---

#### `format(template, variables)`

**الوظيفة:** تنسيق قالب بقاموس من المتغيرات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `variables` | `Dict[str, Any]` | قاموس المتغيرات |

```python
formatter = TemplateFormatter()
result = formatter.format("مرحباً {name}", {"name": "أحمد"})
# "مرحباً أحمد"
```

---

#### `escape_special_chars(text, format_type)` *(static)*

**الوظيفة:** تحويل الأقواس المعقوصة إلى صيغة مُهرَّبة لتجنب تفسيرها كمتغيرات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد معالجته |
| `format_type` | `str` | نوع التنسيق |

```python
TemplateFormatter.escape_special_chars("استخدم {الأقواس}")
# "استخدم {{الأقواس}}"
```

---

#### `strip_whitespace(text, mode)` *(static)*

**الوظيفة:** إزالة المسافات الزائدة من بداية أو نهاية أو كلا الطرفين.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد معالجته |
| `mode` | `str` | `'left'` أو `'right'` أو `'both'` (افتراضي) |

```python
TemplateFormatter.strip_whitespace("  مرحبا  ", "both")
# "مرحبا"
```

---

#### `normalize_whitespace(text)` *(static)*

**الوظيفة:** تحويل المسافات المتعددة المتتالية إلى مسافة واحدة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد تطبيعه |

```python
TemplateFormatter.normalize_whitespace("مرحبا    أحمد")
# "مرحبا أحمد"
```

---

#### `remove_empty_lines(text)` *(static)*

**الوظيفة:** حذف الأسطر الفارغة من النص.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد معالجته |

```python
text = "سطر أول\n\n\nسطر ثالث"
TemplateFormatter.remove_empty_lines(text)
# "سطر أول\nسطر ثالث"
```

---

#### `truncate_text(text, max_length, suffix)` *(static)*

**الوظيفة:** اقتطاع النص إذا تجاوز الحد الأقصى من الأحرف مع إضافة لاحقة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد اقتطاعه |
| `max_length` | `int` | الحد الأقصى للأحرف |
| `suffix` | `str` | اللاحقة عند الاقتطاع (افتراضي: `"..."`) |

```python
TemplateFormatter.truncate_text("نص طويل جداً", 8)
# "نص طو..."
```

---

#### `indent_text(text, spaces)` *(static)*

**الوظيفة:** إضافة مسافات بادئة لكل سطر في النص.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد إضافة المسافة البادئة له |
| `spaces` | `int` | عدد المسافات (افتراضي: `4`) |

```python
TemplateFormatter.indent_text("سطر أول\nسطر ثاني", 2)
# "  سطر أول\n  سطر ثاني"
```

---

#### `add_prefix(text, prefix, skip_empty)` *(static)*

**الوظيفة:** إضافة بادئة محددة لكل سطر في النص.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `text` | `str` | النص المراد معالجته |
| `prefix` | `str` | البادئة المراد إضافتها |
| `skip_empty` | `bool` | تخطي الأسطر الفارغة (افتراضي: `True`) |

```python
TemplateFormatter.add_prefix("سطر أول\nسطر ثاني", "> ")
# "> سطر أول\n> سطر ثاني"
```

---

#### `highlight_variables(template, style)` *(static)*

**الوظيفة:** إبراز المتغيرات في القالب بأسلوب تنسيق معين (مفيد للعرض).

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `style` | `str` | أسلوب الإبراز (افتراضي: `"**"` للخط العريض) |

```python
TemplateFormatter.highlight_variables("مرحباً {name}")
# "مرحباً **{name}**"
```

---

#### `replace_variables(template, replacements)` *(static)*

**الوظيفة:** إعادة تسمية المتغيرات داخل القالب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `replacements` | `Dict[str, str]` | قاموس يربط الأسماء القديمة بالجديدة |

```python
TemplateFormatter.replace_variables("مرحباً {name}", {"name": "username"})
# "مرحباً {username}"
```

---

### 6. TemplateValidator


**الوصف:**
أداة للتحقق من صحة بنية القوالب والمتغيرات. تكشف الأخطاء قبل محاولة تنسيق القالب وتوفر تحذيرات مفيدة.

---

#### `validate_template(template, expected_variables, template_format)`

**الوظيفة:** التحقق الشامل من صحة القالب: الأقواس، والصياغة، والمتغيرات المطلوبة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `expected_variables` | `Optional[List[str]]` | المتغيرات المتوقعة للتحقق منها |
| `template_format` | `str` | نوع التنسيق |

**Return:** `True` إذا كان القالب صحيحاً

```python
validator = TemplateValidator()
validator.validate_template("مرحباً {name}", expected_variables=["name"])
# True
```

---

#### `validate_format_string(template)`

**الوظيفة:** التحقق من أن القالب صيغة format string صحيحة في Python.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

```python
validator.validate_format_string("نص صحيح {var}")  # True
validator.validate_format_string("نص {غير مكتمل")  # ValueError
```

---

#### `validate_variable_names(variables)`

**الوظيفة:** التحقق من أن أسماء المتغيرات تتبع قواعد تسمية Python.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `variables` | `List[str]` | قائمة أسماء المتغيرات |

```python
validator.validate_variable_names(["name", "user_age"])  # True
validator.validate_variable_names(["1invalid"])  # ValueError
```

---

#### `check_balanced_braces(template)`

**الوظيفة:** التحقق من أن الأقواس المعقوصة `{}` متوازنة ومتطابقة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

```python
validator.check_balanced_braces("مرحباً {name}")    # True
validator.check_balanced_braces("مرحباً {name")     # ValueError: Unmatched opening brace
```

---

#### `check_security(template)`

**الوظيفة:** فحص القالب بحثاً عن أنماط قد تُشكّل ثغرات أمنية.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `Dict` يحتوي على `is_safe` و `issues`

```python
result = validator.check_security("نص آمن {var}")
# {"is_safe": True, "issues": []}

result = validator.check_security("استدعاء eval({code})")
# {"is_safe": False, "issues": ["Potential security issue: eval( found"]}
```

---

#### `suggest_variable_name(name)` *(static)*

**الوظيفة:** اقتراح اسم متغير صحيح بناءً على نص غير صالح.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `name` | `str` | الاسم الأصلي غير الصالح |

```python
TemplateValidator.suggest_variable_name("user name")   # "user_name"
TemplateValidator.suggest_variable_name("1st-item")    # "_1st_item"
```

---

### 7. VariableExtractor


**الوصف:**
أداة لاستخراج وتحليل المتغيرات من القوالب. تدعم تنسيقَي f-string و jinja2، وتوفر معلومات تفصيلية عن كل متغير.

---

#### `__init__(template_format)`

**الوظيفة:** تهيئة مستخرج المتغيرات بنوع التنسيق المستخدم.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template_format` | `str` | نوع التنسيق: `'f-string'` أو `'jinja2'` |

---

#### `extract(template)`

**الوظيفة:** استخراج قائمة بأسماء جميع المتغيرات الموجودة في القالب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `List[str]` - قائمة أسماء المتغيرات

```python
extractor = VariableExtractor()
vars = extractor.extract("مرحباً {name}، عمرك {age} سنة")
# ["name", "age"]
```

---

#### `extract_with_positions(template)`

**الوظيفة:** استخراج المتغيرات مع مواضعها الدقيقة في النص.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `List[Dict]` - قائمة تحتوي على اسم كل متغير وموضعه

```python
extractor.extract_with_positions("مرحباً {name}")
# [{"name": "name", "start": 7, "end": 13, "full_match": "{name}"}]
```

---

#### `get_variable_details(template)`

**الوظيفة:** الحصول على معلومات تفصيلية عن كل متغير في القالب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `List[Dict]` - قائمة تفاصيل المتغيرات

```python
extractor.get_variable_details("مرحباً {name}")
# [{"name": "name", "required": True, "type": "any", "description": "Variable: name"}]
```

---

#### `count_variables(template)`

**الوظيفة:** حساب عدد المتغيرات الفريدة في القالب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `int`

```python
extractor.count_variables("{a} و {b} و {a}")
# 2  (a تُحسب مرة واحدة)
```

---

#### `has_variables(template)`

**الوظيفة:** التحقق السريع مما إذا كان القالب يحتوي على أي متغيرات.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `bool`

```python
extractor.has_variables("نص ثابت")        # False
extractor.has_variables("مرحباً {name}")  # True
```

---

#### `get_variable_types(template)`

**الوظيفة:** تخمين أنواع البيانات للمتغيرات بناءً على أسمائها.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |

**Return:** `Dict[str, str]` - قاموس يربط اسم المتغير بنوعه المُقدَّر

```python
extractor.get_variable_types("{name} لديه {count} رسالة وسعر {price}")
# {"name": "str", "count": "int", "price": "float"}
```

---

#### `find_missing_variables(template, provided_vars, template_format)` *(static)*

**الوظيفة:** إيجاد المتغيرات المطلوبة في القالب ولكن غير المُقدَّمة.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `provided_vars` | `Dict[str, Any]` | المتغيرات المُقدَّمة |
| `template_format` | `str` | نوع التنسيق |

```python
VariableExtractor.find_missing_variables(
    "مرحباً {name} في {city}",
    {"name": "أحمد"}
)
# ["city"]
```

---

#### `find_unused_variables(template, provided_vars, template_format)` *(static)*

**الوظيفة:** إيجاد المتغيرات المُقدَّمة ولكن غير المستخدمة في القالب.

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `template` | `str` | نص القالب |
| `provided_vars` | `Dict[str, Any]` | المتغيرات المُقدَّمة |
| `template_format` | `str` | نوع التنسيق |

```python
VariableExtractor.find_unused_variables(
    "مرحباً {name}",
    {"name": "أحمد", "city": "القاهرة", "age": 30}
)
# ["city", "age"]
```

---

## القوالب الجاهزة (Prebuilt)

---

### 8. SystemPrompts

**الوصف:**
مجموعة من قوالب System Prompts الجاهزة للاستخدام الفوري في تطبيقات الذكاء الاصطناعي. كل دالة تُعيد `ChatPromptTemplate` جاهزاً.

---

| الدالة | الوصف | مثال الاستخدام |
|--------|-------|----------------|
| `assistant()` | مساعد عام مفيد | روبوتات المحادثة العامة |
| `code_assistant()` | مساعد برمجة متخصص | أدوات المساعدة في الكتابة البرمجية |
| `translator()` | مترجم احترافي | تطبيقات الترجمة |
| `teacher()` | معلم صبور ومتخصص | منصات التعليم الإلكتروني |
| `creative_writer()` | كاتب إبداعي | أدوات الكتابة الإبداعية |
| `data_analyst()` | محلل بيانات | تطبيقات تحليل البيانات |
| `technical_writer()` | كاتب توثيق تقني | أدوات التوثيق |
| `customer_support()` | وكيل دعم عملاء | روبوتات خدمة العملاء |
| `research_assistant()` | مساعد بحثي | أدوات البحث والتلخيص |
| `business_analyst()` | محلل أعمال | تطبيقات الأعمال |
| `custom(system_message)` | قالب نظام مخصص | أي استخدام مخصص |

```python
from prompt import SystemPrompts

# استخدام مساعد برمجة جاهز
template = SystemPrompts.code_assistant()
messages = template.add_user_message("{code_question}").format(
    code_question="كيف أكتب دالة تعكس قائمة في Python؟"
)

# إنشاء قالب نظام مخصص
custom = SystemPrompts.custom("أنت خبير في تحليل العقود القانونية.")
```

---

### 9. TaskPrompts


**الوصف:**
مجموعة قوالب `PromptTemplate` جاهزة لمهام NLP الشائعة. كل دالة تُعيد قالباً جاهزاً للاستخدام الفوري.

---

| الدالة | المتغيرات | الوصف |
|--------|-----------|-------|
| `question_answering()` | `context`, `question` | إجابة الأسئلة بناءً على سياق |
| `summarization()` | `text`, `num_sentences` | تلخيص النصوص |
| `translation()` | `text`, `source_lang`, `target_lang` | ترجمة النصوص |
| `classification()` | `text`, `categories` | تصنيف النصوص |
| `sentiment_analysis()` | `text` | تحليل المشاعر |
| `entity_extraction()` | `text`, `entity_type` | استخراج الكيانات |
| `code_generation()` | `task`, `requirements`, `language` | توليد الكود البرمجي |
| `code_review()` | `code`, `language` | مراجعة الكود البرمجي |
| `code_explanation()` | `code`, `language` | شرح الكود البرمجي |
| `brainstorming()` | `topic`, `context`, `num_ideas` | العصف الذهني |
| `comparison()` | `item1`, `item2` | المقارنة بين شيئين |
| `explanation()` | `concept`, `audience` | شرح المفاهيم |
| `pros_cons()` | `topic` | تحليل الإيجابيات والسلبيات |
| `step_by_step()` | `task`, `goal` | تعليمات خطوة بخطوة |
| `email_writing()` | `topic`, `recipient`, `subject`, `tone` | كتابة البريد الإلكتروني |
| `product_description()` | `product_name`, `category`, `features`, `audience` | وصف المنتج |
| `blog_post()` | `topic`, `title`, `audience`, `word_count`, `tone` | مقالة مدونة |
| `social_media_post()` | `platform`, `topic`, `tone`, `elements` | منشور وسائل التواصل |
| `meeting_notes()` | `discussion` | تنظيم ملاحظات الاجتماع |

```python
from prompt import TaskPrompts

# تلخيص نص
summarize = TaskPrompts.summarization()
prompt = summarize.format(
    text="نص طويل يحتاج إلى تلخيص...",
    num_sentences="3"
)

# توليد كود
code_gen = TaskPrompts.code_generation()
prompt = code_gen.format(
    language="Python",
    task="دالة لترتيب قائمة",
    requirements="- يجب أن تعمل مع الأعداد والنصوص\n- تدعم الترتيب التصاعدي والتنازلي"
)
```

---

### 10. ArabicPrompts


**الوصف:**
مجموعة قوالب متخصصة للمحتوى العربي والإسلامي. توفر قوالب جاهزة للمساعدين العرب والمهام اللغوية والدينية.

---

#### قوالب المساعدين (تُعيد `ChatPromptTemplate`)

| الدالة | الوصف |
|--------|-------|
| `arabic_assistant()` | مساعد عربي عام |
| `arabic_teacher()` | معلم لغة عربية |
| `quran_explainer()` | متخصص في شرح القرآن الكريم |
| `islamic_scholar()` | عالم إسلامي |
| `arabic_poet()` | شاعر عربي |
| `arabic_news_writer()` | كاتب أخبار عربي |

---

#### قوالب المهام العربية  `PromptTemplate`

| الدالة | المتغيرات | الوصف |
|--------|-----------|-------|
| `question_answering_arabic()` | `سياق`, `سؤال` | سؤال وجواب بالعربية |
| `summarization_arabic()` | `نص`, `عدد_الجمل` | تلخيص بالعربية |
| `translation_to_arabic()` | `نص`, `اللغة_المصدر` | الترجمة إلى العربية |
| `grammar_check_arabic()` | `نص` | التدقيق النحوي والإملائي |
| `formal_letter_arabic()` | `موضوع`, `المستلم`, `الغرض` | رسالة رسمية |
| `essay_arabic()` | `موضوع`, `عنوان`, `عدد_الكلمات`, `أسلوب` | مقال عربي |
| `story_arabic()` | `نوع_القصة`, `موضوع`, `شخصيات`, `مكان`, `طول` | قصة عربية |
| `social_media_arabic()` | `منصة`, `موضوع`, `أسلوب`, `عناصر` | منشور عربي |
| `proverb_explanation()` | `مثل` | شرح مثل عربي |
| `poetry_analysis()` | `شاعر`, `عصر`, `قصيدة` | تحليل قصيدة |
| `quran_tafseer()` | `آية`, `سورة` | تفسير آية قرآنية |
| `hadith_explanation()` | `حديث`, `راوي` | شرح حديث نبوي |

```python
from prompt import ArabicPrompts

# قالب التدقيق النحوي
grammar = ArabicPrompts.grammar_check_arabic()
prompt = grammar.format(نص="هذا الكتاب مفيدة جداً")

# تحليل قصيدة
analysis = ArabicPrompts.poetry_analysis()
prompt = analysis.format(
    شاعر="المتنبي",
    عصر="العصر العباسي",
    قصيدة="على قدر أهل العزم تأتي العزائم..."
)

# مساعد عربي في المحادثة
assistant = ArabicPrompts.arabic_assistant()
messages = assistant.add_user_message("{سؤال}").format(سؤال="ما هي قواعد الإعراب؟")
```

---

## 💡 أمثلة متكاملة

### مثال 1: بناء chatbot لخدمة العملاء

```python
from prompt import ChatPromptTemplate
from prompt  import SystemPrompts

# استخدام قالب دعم العملاء الجاهز
template = (SystemPrompts.customer_support()
    .add_user_message("المشكلة: {problem}\nاسم العميل: {customer_name}"))

messages = template.format(
    problem="لا أستطيع تسجيل الدخول إلى حسابي",
    customer_name="أحمد محمد"
)
```

---

### مثال 2: Few-Shot لتصنيف المشاعر

```python
from prompt import FewShotPromptTemplate

template = FewShotPromptTemplate.from_examples(
    examples=[
        {"text": "المنتج رائع جداً!", "sentiment": "إيجابي"},
        {"text": "جودة سيئة للغاية", "sentiment": "سلبي"},
    ],
    example_template="النص: {text}\nالمشاعر: {sentiment}",
    suffix_template="النص: {text}\nالمشاعر:",
    prefix="صنّف مشاعر النصوص التالية:",
    max_examples=2
)

result = template.format(text="التوصيل كان سريعاً جداً")
```

---

### مثال 3: التحقق من قالب قبل استخدامه

```python
from prompt import TemplateValidator
from prompt import VariableExtractor

template = "ترجم {نص} من {لغة_المصدر} إلى {لغة_الهدف}"

# استخراج المتغيرات
extractor = VariableExtractor()
variables = extractor.extract(template)
print(f"المتغيرات: {variables}")

# التحقق من القالب
validator = TemplateValidator()
validator.validate_template(template, expected_variables=variables)

# فحص الأمان
security = validator.check_security(template)
print(f"آمن: {security['is_safe']}")
```

---

## ⚠️ الاستثناءات الشائعة

| الاستثناء | السبب | الحل |
|-----------|-------|------|
| `ValueError: Missing variables` | متغيرات مطلوبة غير مُقدَّمة | تحقق من أسماء المتغيرات وتأكد من تمريرها |
| `ValueError: Unmatched braces` | أقواس معقوصة غير متوازنة | راجع القالب وتأكد من إغلاق كل قوس |
| `ValueError: Invalid variable name` | اسم متغير غير صالح | يجب أن يبدأ بحرف أو `_`، وليس رقماً |
| `ImportError: jinja2` | مكتبة jinja2 غير مثبتة | نفّذ `pip install jinja2` |

---

