## نظرة عامة

نظام **Context Manager** هو أداة لبناء وإدارة السياق في تطبيقات **RAG** (Retrieval-Augmented Generation). يأخذ قطعاً نصية (chunks) مسترجعة من قاعدة بيانات متجهية ويحوّلها إلى سياق منسّق وجاهز للتمرير إلى نموذج اللغة (LLM).

### مهام النظام:
1. **التحقق من صحة البيانات** — التأكد من أن كل قطعة نصية تملك `doc_id` و `text`.
2. **إزالة التكرار (Deduplication)** — حذف القطع المتشابهة أو المكررة.
3. **الترتيب (Ranking)** — ترتيب القطع حسب درجة التشابه.
4. **التجميع (Assembly)** — بناء نص السياق النهائي ضمن حد طول محدد.
5. **الضغط (Compression)** — تقليص السياق إذا تجاوز الحد المسموح.
6. **توزيع الميزانية (Budget Allocation)** — توزيع الحد الأقصى عند استخدام استعلامات متعددة.

---



---

## البنية المعمارية

```
┌──────────────────────────────────────────────────────────┐
│                      ContextManager                      │
│                                                          │
│  Input: [(chunk, score), ...]   Query: str               │
│              │                                           │
│              ▼                                           │
│  ┌─────────────────────┐                                 │
│  │  validate_chunk()   │  ← التحقق من صحة البيانات       │
│  └──────────┬──────────┘                                 │
│             ▼                                            │
│  ┌─────────────────────┐                                 │
│  │ DeduplicationStrategy│ ← إزالة التكرار                │
│  │  Prefix / Hash      │                                 │
│  └──────────┬──────────┘                                 │
│             ▼                                            │
│  ┌─────────────────────┐                                 │
│  │   RankingStrategy   │ ← الترتيب حسب الدرجة            │
│  │   ScoreRanking      │                                 │
│  └──────────┬──────────┘                                 │
│             ▼                                            │
│  ┌─────────────────────┐                                 │
│  │  _assemble()        │ ← البناء ضمن الميزانية           │
│  └──────────┬──────────┘                                 │
│             ▼                                            │
│  ┌─────────────────────┐                                 │
│  │ CompressionStrategy │ ← الضغط عند الحاجة              │
│  │  GreedyCompression  │                                 │
│  └──────────┬──────────┘                                 │
│             ▼                                            │
│         Output: str (formatted context)                  │
└──────────────────────────────────────────────────────────┘
```

---

## استخدام سريع

```python
from dataclasses import dataclass
from typing import Optional
from context import ContextManager
from context import ContextConfig

# تعريف نموذج بسيط للقطعة النصية
@dataclass
class Chunk:
    doc_id: str
    text: str
    metadata: Optional[dict] = None

# إنشاء بيانات تجريبية
chunks = [
    (Chunk("doc_1", "Python هو لغة برمجة عالية المستوى."), 0.95),
    (Chunk("doc_2", "تُستخدم Python في تطوير الذكاء الاصطناعي."), 0.88),
    (Chunk("doc_3", "Django هو إطار عمل ويب مبني على Python."), 0.72),
]

# إنشاء الـ ContextManager وبناء السياق
manager = ContextManager()
context = manager.build(query="ما هي Python؟", chunks=chunks)
print(context)
```

---

## توثيق الوحدات

---

## 1. `ContextConfig` — إعدادات السياق

>
> **الوصف:** `dataclass` يحتوي على جميع الإعدادات القابلة للتخصيص في النظام. يُمرَّر إلى `ContextManager` للتحكم في سلوكه.

### الخصائص (Attributes)

| الخاصية | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `max_context_length` | `int` | `2000` | الحد الأقصى لطول السياق الناتج (بالحروف أو التوكنز) |
| `include_scores` | `bool` | `False` | إضافة درجة التشابه لكل قطعة في النص الناتج |
| `include_metadata` | `bool` | `False` | إضافة البيانات الوصفية (metadata) للقطع |
| `separator` | `str` | `"\n---\n"` | الفاصل النصي بين القطع في السياق الناتج |
| `template` | `str` | `"arabic"` | القالب المستخدم لتنسيق النص (`arabic`، `english`، `minimal`) |
| `prefix_length` | `int` | `100` | طول البادئة المستخدمة في `PrefixDeduplication` |
| `min_compression_char` | `int` | `50` | الحد الأدنى للمحتوى عند الضغط في `GreedyCompression` |

### نوع مخصص

```python
LengthCounter = Callable[[str], int]
```
نوع يمثل أي دالة تأخذ نصاً وتُعيد عدداً صحيحاً (عدد الحروف أو التوكنز).

### مثال

```python
from context import ContextConfig

# إعدادات مخصصة
config = ContextConfig(
    max_context_length=4000,      # سياق أطول
    include_scores=True,          # إظهار درجات التشابه
    include_metadata=True,        # إظهار الميتاداتا
    separator="\n===\n",          # فاصل مخصص
    template="english",           # قالب إنجليزي
)
```

---

## 2. `Strategy` — الكلاسات المجردة

>
> **الوصف:** يحتوي على أربعة كلاسات مجردة (Abstract Base Classes) تُعرِّف الواجهات التي يجب تطبيقها لكل نوع من استراتيجيات النظام. إذا أردت تخصيص سلوك أي جزء من النظام، فإنك تُنشئ كلاساً يرث من أحد هذه الكلاسات.

---

### `DeduplicationStrategy`

**الوصف:** واجهة لاستراتيجيات إزالة التكرار من قائمة القطع.

#### الدالة المجردة: `deduplicate(chunks)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `chunks` | `List[Tuple]` | قائمة من أزواج `(chunk, score)` |

**Return:** `List[Tuple]` — القائمة بعد حذف المكررات.

```python
from context.stratgey import DeduplicationStrategy
from typing import List, Tuple

# تطبيق مخصص: إزالة التكرار بناءً على الكلمة الأولى
class FirstWordDeduplication(DeduplicationStrategy):
    def deduplicate(self, chunks: List[Tuple]) -> List[Tuple]:
        seen = set()
        unique = []
        for chunk, score in chunks:
            first_word = chunk.text.split()[0].lower()
            if first_word not in seen:
                seen.add(first_word)
                unique.append((chunk, score))
        return unique
```

---

### `RankingStrategy`

**الوصف:** واجهة لاستراتيجيات ترتيب القطع.

#### الدالة المجردة: `rank(chunks, max_chunks)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `chunks` | `List[Tuple]` | قائمة أزواج `(chunk, score)` |
| `max_chunks` | `int \| None` | الحد الأقصى لعدد القطع المُعادة |

**Return:** `List[Tuple]` — القائمة بعد الترتيب والتقليص.

```python
from context.stratgey import RankingStrategy

# تطبيق مخصص: ترتيب عشوائي
import random

class RandomRanking(RankingStrategy):
    def rank(self, chunks, max_chunks=None):
        shuffled = chunks.copy()
        random.shuffle(shuffled)
        return shuffled[:max_chunks] if max_chunks else shuffled
```

---

### `CompressionStrategy`

**الوصف:** واجهة لاستراتيجيات ضغط السياق النصي.

#### الدالة المجردة: `compress(context, target, counter, separator)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `context` | `str` | النص الكامل المراد ضغطه |
| `target` | `int` | الحد الأقصى المستهدف للطول |
| `counter` | `LengthCounter` | دالة قياس الطول (حروف أو توكنز) |
| `separator` | `str` | الفاصل النصي المستخدم في السياق |

**Return:** `str` — النص المضغوط.

```python
from context.stratgey import CompressionStrategy

# تطبيق مخصص: قطع بسيط
class SimpleChopCompression(CompressionStrategy):
    def compress(self, context, target, counter, separator):
        if counter(context) <= target:
            return context
        return context[:target] + "..."
```

---

### `BudgetAllocationStrategy`

**الوصف:** واجهة لاستراتيجيات توزيع الميزانية (الحد الأقصى للطول) على استعلامات متعددة.

#### الدالة المجردة: `allocate(total_budget, n_queries)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `total_budget` | `int` | الميزانية الإجمالية (إجمالي الحروف أو التوكنز المتاحة) |
| `n_queries` | `int` | عدد الاستعلامات التي ستُوزَّع عليها الميزانية |

**Return:** `List[int]` — قائمة بالميزانية المخصصة لكل استعلام.

```python
from context.stratgey import BudgetAllocationStrategy

# تطبيق مخصص: الاستعلام الأول يأخذ نصف الميزانية
class HeavyFirstAllocation(BudgetAllocationStrategy):
    def allocate(self, total_budget, n_queries):
        if n_queries == 0:
            return []
        first = total_budget // 2
        rest = (total_budget - first) // max(n_queries - 1, 1)
        return [first] + [rest] * (n_queries - 1)
```

---

## 3. `Allocations` — استراتيجيات توزيع الميزانية

>
> **الوصف:** يحتوي على تطبيقين جاهزين لـ `BudgetAllocationStrategy`.

---

### `EqualBudgetAllocation`

**الوصف:** توزيع الميزانية بالتساوي على جميع الاستعلامات. أي فائض من قسمة الميزانية يُضاف للاستعلام الأول.

**يرث من:** `BudgetAllocationStrategy`

#### `allocate(total_budget, n_queries)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `total_budget` | `int` | الميزانية الإجمالية |
| `n_queries` | `int` | عدد الاستعلامات |

**Return:** `List[int]`

```python
from context.allocations import EqualBudgetAllocation

allocator = EqualBudgetAllocation()

# توزيع 1000 حرف على 3 استعلامات
budgets = allocator.allocate(total_budget=1000, n_queries=3)
print(budgets)  # [334, 333, 333]  (الباقي يذهب للأول)

# حالة حافة: لا استعلامات
empty = allocator.allocate(total_budget=1000, n_queries=0)
print(empty)    # []
```

---

### `WeightedBudgetAllocation`

**الوصف:** توزيع الميزانية بشكل نسبي بناءً على أوزان مخصصة. مفيد عندما تكون بعض الاستعلامات أهم من غيرها.

**يرث من:** `BudgetAllocationStrategy`

#### `__init__(weights)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `weights` | `List[float]` | قائمة الأوزان — يجب أن يتساوى طولها مع عدد الاستعلامات |

#### `allocate(total_budget, n_queries)`

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `total_budget` | `int` | الميزانية الإجمالية |
| `n_queries` | `int` | عدد الاستعلامات (يجب مساواة طول `weights`) |

**Return:** `List[int]`

> **ملاحظة:** إذا كانت جميع الأوزان صفراً، يتراجع تلقائياً إلى `EqualBudgetAllocation`.

```python
from context.allocations import WeightedBudgetAllocation

# الاستعلام الأول أهم — يأخذ 50%، الثاني 30%، الثالث 20%
allocator = WeightedBudgetAllocation(weights=[0.5, 0.3, 0.2])
budgets = allocator.allocate(total_budget=1000, n_queries=3)
print(budgets)  # [500, 300, 200]

# حالة: أوزان كلها صفر → توزيع متساوٍ
allocator_zero = WeightedBudgetAllocation(weights=[0, 0, 0])
budgets_zero = allocator_zero.allocate(total_budget=900, n_queries=3)
print(budgets_zero)  # [300, 300, 300]
```

---

## 4. `ContextManager` — المنسق الرئيسي

>
> **الوصف:** الكلاس الرئيسي الذي ينسّق جميع الاستراتيجيات لبناء سياق RAG منسّق وجاهز. جميع سلوكياته قابلة للتخصيص عبر حقن الاستراتيجيات.

---

### دوال مساعدة عامة (Module-level)

---

#### `validate_chunk(chunk)`

**الوصف:** دالة مستقلة تتحقق من صحة أي كائن قطعة نصية. تُثير `TypeError` إذا كان الكائن لا يملك `doc_id` أو `text`، أو إذا لم يكونا من نوع `str`.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `chunk` | `object` | الكائن المراد التحقق منه |

**Return:** `None` — تُثير استثناءً في حالة الخطأ فقط.

```python
from context import validate_chunk
from dataclasses import dataclass

@dataclass
class GoodChunk:
    doc_id: str
    text: str

@dataclass
class BadChunk:
    content: str  # خطأ: ليس text

validate_chunk(GoodChunk("doc1", "نص سليم"))  # لا يحدث شيء ✓

try:
    validate_chunk(BadChunk("نص"))  # يُثير TypeError
except TypeError as e:
    print(e)  # Chunk is missing required attributes: ['doc_id', 'text']
```

---

#### `char_counter(text)`

**الوصف:** دالة العدّ الافتراضية — تُعيد عدد الحروف في النص. تُستخدم تلقائياً في `ContextManager` ما لم يُحدَّد عداد آخر.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `text` | `str` | النص المراد قياسه |

**Return:** `int`

```python
from context import char_counter

print(char_counter("مرحباً بالعالم"))  # 14
print(char_counter("Hello World"))     # 11
```

---

#### `make_token_counter(tokenizer)`

**الوصف:** دالة مصنع (factory) تُحوّل أي tokenizer بأسلوب HuggingFace أو tiktoken إلى `LengthCounter`. مفيد للتحكم الدقيق في الطول عند العمل مع نماذج اللغة.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `tokenizer` | أي كائن يملك دالة `encode()` | الـ tokenizer المراد تغليفه |

**Return:** `LengthCounter` — دالة من نوع `Callable[[str], int]`.

```python
from context import make_token_counter, ContextManager

# مثال مع tiktoken
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")
token_counter = make_token_counter(enc)

# الآن الـ manager يحسب التوكنز بدلاً من الحروف
manager = ContextManager(length_counter=token_counter)

# مثال مع HuggingFace
from transformers import AutoTokenizer
hf_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
hf_counter = make_token_counter(hf_tokenizer)
manager_hf = ContextManager(length_counter=hf_counter)
```

---

### `__init__()` — إنشاء الـ ContextManager

**الوصف:** تهيئة المنسق مع جميع الاستراتيجيات المطلوبة. جميع المعاملات اختيارية — إذا لم تُحدَّد، تُستخدم القيم الافتراضية.

**المعاملات:**
| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `config` | `ContextConfig \| None` | `None` → `ContextConfig()` | كائن الإعدادات |
| `length_counter` | `LengthCounter \| None` | `None` → `char_counter` | دالة قياس الطول |
| `dedup_strategy` | `DeduplicationStrategy \| None` | `None` → `HashDeduplication()` | استراتيجية إزالة التكرار |
| `ranking_strategy` | `RankingStrategy \| None` | `None` → `ScoreRanking()` | استراتيجية الترتيب |
| `compression_strategy` | `CompressionStrategy \| None` | `None` → `GreedyCompression()` | استراتيجية الضغط |
| `budget_strategy` | `BudgetAllocationStrategy \| None` | `None` → `EqualBudgetAllocation()` | استراتيجية توزيع الميزانية |

```python
from context import ContextManager, PrefixDeduplication
from context import ContextConfig
from context.allocations import WeightedBudgetAllocation

config = ContextConfig(
    max_context_length=3000,
    include_scores=True,
    template="english"
)

manager = ContextManager(
    config=config,
    dedup_strategy=PrefixDeduplication(prefix_length=80),
    budget_strategy=WeightedBudgetAllocation(weights=[0.6, 0.4])
)
```

---

### العمليات الأساسية | Core Operations

---

#### `build(query, chunks, max_chunks=None, *, max_length=None)`

**الوصف:** الدالة الرئيسية — تبني سياقاً نصياً منسّقاً من قائمة قطع مسترجعة. تمر بمراحل: التحقق → إزالة التكرار → الترتيب → التجميع (مع ضغط عند الحاجة).

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `query` | `str` | نص الاستعلام (يُستخدم للتسجيل والـ logging فقط) |
| `chunks` | `List[Tuple]` | قائمة أزواج `(chunk, score)` حيث `chunk` يملك `doc_id` و `text` |
| `max_chunks` | `int \| None` | الحد الأقصى لعدد القطع المُدرَجة في السياق |
| `max_length` | `int \| None` | تجاوز `max_context_length` من الإعدادات لهذه العملية فقط |

**Return:** `str` — السياق المنسّق والجاهز.

> **ملاحظة:** في حالة قائمة فارغة أو خطأ في التحقق، تُعيد الدالة سياقاً فارغاً منسّقاً بدلاً من إثارة استثناء.

```python
from dataclasses import dataclass
from typing import Optional
from context import ContextManager

@dataclass
class Chunk:
    doc_id: str
    text: str
    metadata: Optional[dict] = None

manager = ContextManager()

chunks = [
    (Chunk("wiki_1", "الذكاء الاصطناعي هو محاكاة الذكاء البشري."), 0.95),
    (Chunk("wiki_2", "يشمل الذكاء الاصطناعي التعلم الآلي والشبكات العصبية."), 0.87),
    (Chunk("wiki_3", "GPT هو نموذج لغوي من OpenAI."), 0.65),
]

# بناء سياق كامل
context = manager.build(query="ما هو الذكاء الاصطناعي؟", chunks=chunks)
print(context)

# تحديد الحد الأقصى للقطع
context_limited = manager.build(
    query="ما هو الذكاء الاصطناعي؟",
    chunks=chunks,
    max_chunks=2           # أقصى قطعتين
)

# تجاوز الحد الأقصى للطول مؤقتاً
context_short = manager.build(
    query="ملخص قصير",
    chunks=chunks,
    max_length=300         # 300 حرف فقط
)
```

---

#### `build_multi_query_context(queries, all_chunks, *, global_budget=None)`

**الوصف:** بناء سياق موحّد لاستعلامات متعددة (Multi-hop RAG). يُنشئ سياقاً مستقلاً لكل استعلام ثم يدمجها في نص واحد. إذا حُدِّد `global_budget`، تُوزَّع الميزانية بين الاستعلامات باستخدام استراتيجية التوزيع المُحقَنة.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `queries` | `List[str]` | قائمة نصوص الاستعلامات |
| `all_chunks` | `List[List[Tuple]]` | قائمة مقابِلة من قوائم القطع لكل استعلام |
| `global_budget` | `int \| None` | الحد الأقصى الإجمالي للسياق الموحّد |

**Return:** `str` — السياق الموحّد لجميع الاستعلامات.

> **تنبيه:** يجب أن يكون طول `queries` مساوياً لطول `all_chunks` وإلا تُثار `ValueError`.

```python
manager = ContextManager()

queries = ["ما هو Python؟", "ما هو Django؟"]

chunks_q1 = [
    (Chunk("doc1", "Python هي لغة برمجة مفسّرة عالية المستوى."), 0.92),
    (Chunk("doc2", "صمّمها غيدو فان روسوم عام 1991."), 0.80),
]

chunks_q2 = [
    (Chunk("doc3", "Django هو إطار ويب مبني على Python."), 0.91),
    (Chunk("doc4", "يتبع Django مبدأ DRY: Don't Repeat Yourself."), 0.75),
]

# بدون ميزانية: كل استعلام يحصل على كامل max_context_length
combined = manager.build_multi_query_context(
    queries=queries,
    all_chunks=[chunks_q1, chunks_q2]
)

# مع ميزانية: 2000 حرف إجمالاً موزّعة بالتساوي
combined_budgeted = manager.build_multi_query_context(
    queries=queries,
    all_chunks=[chunks_q1, chunks_q2],
    global_budget=2000
)
```

---

#### `compress_context(context, target_length)`

**الوصف:** ضغط سياق نصي موجود ليُلائم حداً أقصى محدداً. يُفوَّض للاستراتيجية المُحقَنة (`GreedyCompression` افتراضياً). يتضمن ضماناً نهائياً: إذا أعادت الاستراتيجية نصاً أطول من المستهدف، يتم القطع القسري.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `context` | `str` | النص الكامل المراد ضغطه |
| `target_length` | `int` | الحد الأقصى المستهدف للطول |

**Return:** `str` — النص المضغوط. يُعيد نصاً فارغاً إذا كان `target_length <= 0`.

```python
manager = ContextManager()

long_context = """المعلومات المسترجعة:
---
[مصدر: doc1] Python هي لغة برمجة عالية المستوى شائعة الاستخدام في تطوير الويب.
---
[مصدر: doc2] Django هو إطار عمل Python الأكثر استخداماً لتطوير تطبيقات الويب.
---
[مصدر: doc3] Flask هو إطار عمل Python خفيف الوزن مناسب للتطبيقات الصغيرة.
---"""

# ضغط لـ 200 حرف
compressed = manager.compress_context(long_context, target_length=200)
print(f"الطول قبل: {len(long_context)}")
print(f"الطول بعد: {len(compressed)}")
```

---

#### `get_context_stats(context)`

**الوصف:** إرجاع إحصائيات تفصيلية عن سياق نصي. يستثني ترويسة (header) وذيل (footer) القالب من حسابات القطع للحصول على أرقام دقيقة.

**المعاملات:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| `context` | `str` | السياق النصي المراد تحليله |

**Return:** `dict`

```python
manager = ContextManager()
chunks = [
    (Chunk("d1", "نص أول للاختبار وهو نص متوسط الطول."), 0.9),
    (Chunk("d2", "نص ثانٍ."), 0.7),
    (Chunk("d3", "نص ثالث مطوّل يحتوي على معلومات إضافية مفصّلة."), 0.5),
]
context = manager.build("استعلام", chunks)

stats = manager.get_context_stats(context)
print(stats)
# {
#   'total_length': 180,       # الطول الكلي
#   'word_count': 28,          # عدد الكلمات
#   'chunk_count': 3,          # عدد القطع
#   'template': 'arabic',      # القالب المستخدم
#   'avg_chunk_length': 42,    # متوسط طول القطعة
#   'min_chunk_length': 10,    # أقصر قطعة
#   'max_chunk_length': 68,    # أطول قطعة
#   'length_unit': 'chars'     # وحدة القياس
# }
```

---

## الاستراتيجيات التفصيلية

### استراتيجيات إزالة التكرار | Deduplication Strategies

---

#### `PrefixDeduplication`

**الوصف:** إزالة التكرار بناءً على مقارنة بادئة النص. سريعة لكن أقل دقةً — قد تفوّت تكرارات تختلف في بدايتها فقط.

**يرث من:** `DeduplicationStrategy`

**المعاملات في `__init__`:**
| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| `prefix_length` | `int` | `config.prefix_length` (100) | عدد الحروف من بداية النص للمقارنة |

```python
from context import PrefixDeduplication

dedup = PrefixDeduplication(prefix_length=50)
chunks = [
    (Chunk("d1", "Python هي لغة برمجة عالية المستوى تُستخدم في كثير من المجالات."), 0.9),
    (Chunk("d2", "Python هي لغة برمجة عالية المستوى وتتميز بسهولة القراءة."), 0.8),  # مكرر (نفس البادئة)
    (Chunk("d3", "Django هو إطار عمل مبني على Python."), 0.7),
]

unique = dedup.deduplicate(chunks)
print(len(unique))  # 2 (حُذف d2 لأن بادئته تشبه d1)
```

---

#### `HashDeduplication`

**الوصف:** إزالة التكرار باستخدام تجزئة SHA-256 للنص الكامل بعد تطبيع الأحرف والمسافات. أكثر دقةً من `PrefixDeduplication` وتكتشف النسخ المتطابقة تقريباً (الاختلاف في المسافات فقط).

**يرث من:** `DeduplicationStrategy`

> هذه هي الاستراتيجية **الافتراضية** في `ContextManager`.

```python
from context import HashDeduplication

dedup = HashDeduplication()
chunks = [
    (Chunk("d1", "Python هي لغة برمجة."), 0.9),
    (Chunk("d2", "python   هي   لغة   برمجة."), 0.8),  # مكرر (نفس النص بعد التطبيع)
    (Chunk("d3", "Django إطار عمل."), 0.7),
]

unique = dedup.deduplicate(chunks)
print(len(unique))  # 2 (حُذف d2 لأنه مطابق لـ d1 بعد التطبيع)
```

---

### استراتيجيات الترتيب | Ranking Strategies

---

#### `ScoreRanking`

**الوصف:** ترتيب القطع تنازلياً بناءً على درجة التشابه (أعلى درجة أولاً). مع تطبيق الحد الأقصى للعدد إذا حُدِّد.

**يرث من:** `RankingStrategy`

> هذه هي الاستراتيجية **الافتراضية** في `ContextManager`.

```python
from context import ScoreRanking

ranker = ScoreRanking()
chunks = [
    (Chunk("d1", "نص أول"), 0.65),
    (Chunk("d2", "نص ثانٍ"), 0.92),
    (Chunk("d3", "نص ثالث"), 0.78),
]

# ترتيب بدون حد
ranked = ranker.rank(chunks, max_chunks=None)
print([score for _, score in ranked])  # [0.92, 0.78, 0.65]

# ترتيب مع حد
top2 = ranker.rank(chunks, max_chunks=2)
print([score for _, score in top2])    # [0.92, 0.78]
```

---

### استراتيجيات الضغط | Compression Strategies

---

#### `GreedyCompression`

**الوصف:** ضغط ذكي يحافظ على الترويسة (header) والذيل (footer) ويملأ المحتوى الأوسط بشكل جشع (greedy). يعالج الحالات الحافة: الميزانية الصغيرة جداً، النص القصير، والمسافة السالبة.

**يرث من:** `CompressionStrategy`

> هذه هي الاستراتيجية **الافتراضية** في `ContextManager`.

**ثابت مهم:**
- `MIN_CONTENT_LENGTH = 50` — الحد الأدنى للمحتوى المقبول بعد الضغط.

```python
from context import GreedyCompression, char_counter

compressor = GreedyCompression()

context = """المعلومات المسترجعة:
---
[مصدر: d1] نص أول طويل نسبياً يحتوي على معلومات مفصلة عن الموضوع المطلوب.
---
[مصدر: d2] نص ثانٍ يضيف معلومات تكميلية وداعمة للموضوع الرئيسي في البحث.
---
[مصدر: d3] نص ثالث يشمل تفاصيل إضافية ونقاط توضيحية متعددة.
---"""

compressed = compressor.compress(
    context=context,
    target=100,
    counter=char_counter,
    separator="\n---\n"
)
print(f"الطول بعد: {len(compressed)}")  # ≤ 100
```

---

## القوالب

يدعم `ContextManager` ثلاثة قوالب جاهزة لتنسيق السياق:

### `arabic` (الافتراضي)

```
المعلومات المسترجعة:
---
[مصدر: doc_1] نص القطعة الأولى.
---
[مصدر: doc_2 | تشابه: 0.88] نص بالدرجة (عند تفعيل include_scores)
---
```

### `english`

```
Retrieved Information:
---
[Source: doc_1] First chunk text.
---
[Source: doc_2 | Similarity: 0.88] Text with score (when include_scores=True)
---
```

### `minimal`

```
نص القطعة الأولى.
---
نص القطعة الثانية.
```

```python
from context import ContextConfig
from context import ContextManager

# تغيير القالب
config = ContextConfig(template="english", include_scores=True)
manager = ContextManager(config=config)
```

---

## مرجع سريع

### جدول الدوال العامة

| الدالة | الوصف | المُعيد |
|--------|-------|---------|
| `validate_chunk(chunk)` | التحقق من صحة القطعة | `None` أو `TypeError` |
| `char_counter(text)` | عدّ الحروف | `int` |
| `make_token_counter(tokenizer)` | إنشاء عداد توكنز | `LengthCounter` |
| `manager.build(query, chunks, ...)` | بناء سياق من قطع | `str` |
| `manager.build_multi_query_context(...)` | سياق موحّد لاستعلامات متعددة | `str` |
| `manager.compress_context(context, target)` | ضغط سياق موجود | `str` |
| `manager.get_context_stats(context)` | إحصائيات السياق | `dict` |

### جدول الاستراتيجيات الجاهزة

| الكلاس | النوع | الاستخدام |
|--------|------|-----------|
| `HashDeduplication` | إزالة تكرار | الافتراضي — دقيق، يستخدم SHA-256 |
| `PrefixDeduplication` | إزالة تكرار | سريع، يقارن بادئة النص فقط |
| `ScoreRanking` | ترتيب | الافتراضي — تنازلي حسب درجة التشابه |
| `GreedyCompression` | ضغط | الافتراضي — يحافظ على header وfooter |
| `EqualBudgetAllocation` | توزيع ميزانية | الافتراضي — توزيع متساوٍ |
| `WeightedBudgetAllocation` | توزيع ميزانية | توزيع نسبي بأوزان مخصصة |

---

### مثال شامل متكامل

```python
from dataclasses import dataclass
from typing import Optional
from context.context_manager import (
    ContextManager, HashDeduplication,
    ScoreRanking, GreedyCompression, make_token_counter
)
from context import ContextConfig
from context.allocations import WeightedBudgetAllocation
#_____________
# يمكنك استخدام 
# from chunks import DocumentChunks
# ─── 1. تعريف نموذج القطعة ───
@dataclass
class Chunk:
    doc_id: str
    text: str
    metadata: Optional[dict] = None

# ─── 2. الإعدادات ───
config = ContextConfig(
    max_context_length=2000,
    include_scores=True,
    include_metadata=True,
    template="arabic",
)

# ─── 3. إنشاء المنسق ───
manager = ContextManager(
    config=config,
    dedup_strategy=HashDeduplication(),
    ranking_strategy=ScoreRanking(),
    compression_strategy=GreedyCompression(),
    budget_strategy=WeightedBudgetAllocation(weights=[0.6, 0.4]),
)

# ─── 4. بيانات تجريبية ───
chunks_q1 = [
    (Chunk("wiki_py", "Python هي لغة برمجة عالية المستوى.",
           {"source": "Wikipedia", "year": 2024}), 0.95),
    (Chunk("docs_py", "Python تدعم البرمجة الكائنية والوظيفية.", None), 0.82),
    (Chunk("wiki_py_dup", "Python هي لغة برمجة عالية المستوى.", None), 0.70),  # مكرر
]
chunks_q2 = [
    (Chunk("wiki_dj", "Django هو إطار عمل ويب Python.", None), 0.90),
    (Chunk("docs_dj", "يتبع Django مبدأ DRY ويوفر ORM قوياً.", None), 0.78),
]

# ─── 5. سياق استعلام مفرد ───
context = manager.build(
    query="ما هي Python؟",
    chunks=chunks_q1,
    max_chunks=5,
)
print("=== سياق مفرد ===")
print(context)

# ─── 6. سياق متعدد الاستعلامات ───
multi_context = manager.build_multi_query_context(
    queries=["ما هي Python؟", "ما هو Django؟"],
    all_chunks=[chunks_q1, chunks_q2],
    global_budget=1500,
)
print("\n=== سياق متعدد ===")
print(multi_context)

# ─── 7. الإحصائيات ───
stats = manager.get_context_stats(context)
print("\n=== إحصائيات ===")
for key, value in stats.items():
    print(f"  {key}: {value}")

# ─── 8. ضغط يدوي ───
compressed = manager.compress_context(context, target_length=300)
print(f"\n=== بعد الضغط (300 حرف) ===")
print(f"الطول: {len(compressed)}")
print(compressed)
```

---

### Example With Rag System

```python
from context import (
    ContextManager, ContextConfig,
    HashDeduplication, GreedyCompression, ScoreRanking,
    char_counter
)
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
ctx_config = ContextConfig(
    max_context_length=1500,
    include_scores=True,
    separator="\n---\n",
    template="arabic",
)

advanced_ctx_manager = ContextManager(
    config=ctx_config,
    length_counter=char_counter,
    dedup_strategy=HashDeduplication(),
    compression_strategy=GreedyCompression(),
    ranking_strategy=ScoreRanking(),
)

class AdvancedContextAdapter:
    def __init__(self, ctx_manager):
        self._ctx = ctx_manager

    def build(self, query: str, retrieved: list) -> str:
        # retrieved = List[(chunk, score)]
        ctx = self._ctx.build(
            query=query,
            chunks=retrieved,
            max_length=1500,
        )
        return ctx if ctx else "لا يوجد سياق."

rag = base_rag

def run_query(query: str):
    print(f"\n🔍 السؤال: {query}")

    # 1. استرجاع
    retrieved = rag.retrieve(query, top_k=3)

    # 2. بناء Context متقدم
    context = rag.context_manager.build(query, retrieved)

    print("\n🧠 Context:")
    print(context)

    # 3. توليد الإجابة
    answer = rag.llm.generate(context, query)

    print("\n🤖 Answer:")
    print(answer)

    # 4. إحصائيات
    stats = advanced_ctx_manager.get_context_stats(context)
    print("\n📊 Stats:")
    print(stats)

if __name__ == "__main__":
    run_query("ما هو الذكاء الاصطناعي؟")
    run_query("ما هو RAG؟")
```


---

> **ملاحظة معمارية:** `ContextManager` مبني على مبدأ **Dependency Injection** — كل سلوك يمكن تخصيصه عبر حقن استراتيجية بديلة دون تعديل الكود الأصلي. هذا يجعله مرناً للتوسعة وسهل الاختبار.
