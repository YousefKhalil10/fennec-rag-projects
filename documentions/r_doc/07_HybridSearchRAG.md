# 🔀 HybridSearchRAG — توثيق شامل

## نظرة عامة

`HybridSearchRAG` نظام بحث هجين يجمع بين **البحث الدلالي (Semantic Search)** القائم على التشابه المتجهي، و**البحث النصي (Keyword Search)** القائم على BM25 أو TF-IDF. يوفر نتائج أدق من كل طريقة منفردة عبر دمج ذكي للنتائج.

---

## المتطلبات والتثبيت

### المكتبات المطلوبة

```bash
pip install stanza numpy
```

### تحميل نموذج Stanza

Stanza هو المحلل اللغوي الأساسي المستخدم في التجذير والترميز. **يجب تحميل النموذج قبل الاستخدام:**

```python
import stanza

# للعربية
stanza.download('ar')

# للإنجليزية
stanza.download('en')
```

> **ملاحظة:** إذا لم يكن Stanza مثبتاً أو لم يُحمَّل النموذج، سيتراجع النظام تلقائياً إلى محلل نصي بسيط (`_simple_tokenize`) يعتمد على تقسيم المسافات وإزالة الرموز. الجودة ستكون أقل لكن النظام لن يتوقف.

---

## الاستيراد

```python
from rag.hybrid_search import HybridSearchRAG
from rag.hybrid_search.hybrid_search_config import SearchConfig
```

---

## الإعدادات — `SearchConfig`

```python
@dataclass
class SearchConfig:
    semantic_weight: float = 0.7
    keyword_weight: float  = 0.3
    min_score: float       = 0.0
    top_k: int             = 10
    enable_reranking: bool = True
    fusion_method: str     = 'weighted_sum'
```

| الحقل | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `semantic_weight` | `float` | `0.7` | وزن درجة البحث الدلالي في الدمج |
| `keyword_weight` | `float` | `0.3` | وزن درجة البحث النصي في الدمج |
| `min_score` | `float` | `0.0` | الحد الأدنى للدرجة — النتائج دونه تُحذف (يؤثر فقط على `weighted_sum`) |
| `top_k` | `int` | `10` | عدد النتائج المُرجعة افتراضياً |
| `enable_reranking` | `bool` | `True` | محجوز للاستخدام المستقبلي، لا يؤثر حالياً |
| `fusion_method` | `str` | `'weighted_sum'` | طريقة دمج النتائج: `'weighted_sum'`، `'rrf'`، أو `'max'` |

### طرق الدمج `fusion_method`

| الطريقة | الوصف | متى تستخدمها |
|---|---|---|
| `'weighted_sum'` | يطبّع الدرجات ثم يجمعها بالأوزان المحددة | الحالة الافتراضية، تحكم كامل بالأوزان |
| `'rrf'` | Reciprocal Rank Fusion — يعتمد على الترتيب لا الدرجات | عندما تكون مقاييس الدرجات غير متوافقة بين الطريقتين |
| `'max'` | يختار الدرجة الأعلى من الطريقتين لكل مستند | عندما تريد أفضل نتيجة من أي مصدر بدون مزج |

---

## الكلاس الرئيسي — `HybridSearchRAG`

### `__init__`

```python
HybridSearchRAG(
    rag_system,
    config: Optional[SearchConfig] = None,
    keyword_method: str = 'bm25',
    language: str = 'ar',
    use_lemmatization: bool = True
)
```

| المعامل | النوع | الافتراضي | الوصف |
|---|---|---|---|
| `rag_system` | Any | مطلوب | نظام RAG الأساسي. يجب أن يحتوي على `vector_db`، `llm`، و`context_manager` |
| `config` | `SearchConfig` | `None` | إعدادات البحث. إذا كانت `None` تُستخدم القيم الافتراضية |
| `keyword_method` | `str` | `'bm25'` | محرك البحث النصي: `'bm25'` أو `'tfidf'` |
| `language` | `str` | `'ar'` | لغة المحلل اللغوي Stanza |
| `use_lemmatization` | `bool` | `True` | تفعيل التجذير اللغوي لتحسين دقة المطابقة |

**يرمي:** `ValueError` إذا كانت `rag_system` هي `None`.

**الخصائص الداخلية بعد التهيئة:**

```python
hybrid.rag              # نظام RAG الأساسي
hybrid.config           # SearchConfig المُستخدم
hybrid.keyword_method   # 'bm25' أو 'tfidf'
hybrid.language         # اللغة المحددة
hybrid.use_lemmatization
hybrid.keyword_scorer   # BM25Scorer أو TFIDFScorer
hybrid._is_trained      # bool — هل تم تدريب الفهرس النصي
hybrid._document_texts  # List[str] — نصوص المستندات المفهرسة
hybrid.stats            # dict — إحصائيات عمليات البحث
```

---

## الدوال العامة (Public Methods)

### `train_keyword_index`

```python
train_keyword_index() -> None
```

يدرّب فهرس البحث النصي (BM25 أو TF-IDF) على المستندات الموجودة في `rag.vector_db.chunks`.

**سلوك مهم:**
- يُستدعى **تلقائياً** عند أول استدعاء لـ`keyword_search` أو `hybrid_search` إذا لم يُدعَ مسبقاً.
- إذا لم تكن هناك مستندات في `vector_db`، يُسجّل تحذيراً ويعود دون تدريب.
- يجب إعادة استدعاؤه يدوياً إذا أُضيفت مستندات جديدة بعد التهيئة.

```python
# الاستخدام الصحيح — استدعاء صريح بعد إضافة المستندات
base_rag.add_documents({...})
hybrid.train_keyword_index()

# يعمل أيضاً — يُستدعى تلقائياً عند الحاجة (لكن أبطأ)
results = hybrid.hybrid_search(query)  # يُدرّب تلقائياً إذا لزم
```

---

### `semantic_search`

```python
semantic_search(query: str, top_k: Optional[int] = None) -> List[Tuple[DocumentChunk, float]]
```

بحث دلالي فقط عبر نظام RAG الأساسي (`rag.retrieve`).

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | نص الاستعلام |
| `top_k` | `int` أو `None` | عدد النتائج. إذا كان `None` يُستخدم `config.top_k` |

**Return:** قائمة من `(DocumentChunk, score)` مرتبة تنازلياً حسب درجة التشابه.

**الإحصائيات:** يزيد `stats['semantic_searches']` بواحد عند كل استدعاء.

---

### `keyword_search`

```python
keyword_search(query: str, top_k: Optional[int] = None) -> List[Tuple[DocumentChunk, float]]
```

بحث نصي فقط باستخدام BM25 أو TF-IDF.

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | نص الاستعلام |
| `top_k` | `int` أو `None` | عدد النتائج. إذا كان `None` يُستخدم `config.top_k` |

**Return:** قائمة من `(DocumentChunk, score)` — **يُرجع فقط المستندات ذات الدرجة > 0**.

**سلوك مهم:** إذا لم يكن الفهرس مدرَّباً، يُدرِّبه أولاً تلقائياً ثم يبحث.

**الإحصائيات:** يزيد `stats['keyword_searches']` بواحد عند كل استدعاء.

---

### `hybrid_search`

```python
hybrid_search(
    query: str,
    top_k: Optional[int] = None,
    semantic_weight: Optional[float] = None,
    keyword_weight: Optional[float] = None
) -> List[Tuple[DocumentChunk, float]]
```

البحث الهجين — يجمع البحث الدلالي والنصي ثم يدمج النتائج.

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | نص الاستعلام |
| `top_k` | `int` أو `None` | عدد النتائج النهائية |
| `semantic_weight` | `float` أو `None` | يُتجاوز `config.semantic_weight` إذا حُدِّد (بما في ذلك القيمة `0.0`) |
| `keyword_weight` | `float` أو `None` | يُتجاوز `config.keyword_weight` إذا حُدِّد (بما في ذلك القيمة `0.0`) |

**آلية العمل الداخلية:**
1. يجلب `top_k * 2` نتيجة من كل طريقة (دلالي + نصي) لتوسيع مرشحي الدمج.
2. يدمج النتائج بالطريقة المحددة في `config.fusion_method`.
3. يُرجع أفضل `top_k` نتيجة مرتبة.

**ملاحظة مهمة حول الأوزان:** يستخدم `is not None` للتحقق من الأوزان المُمرَّرة، لذا تمرير `0.0` صريح **يعمل بشكل صحيح** ولا يُتجاهل. تمرير `None` (أو عدم التمرير) يُعيد استخدام القيمة من `config`.

**الإحصائيات:** يزيد `stats['total_searches']` و`stats['hybrid_searches']` بواحد عند كل استدعاء.

---

### `generate`

```python
generate(
    query: str,
    search_method: str = 'hybrid',
    include_sources: bool = False
) -> str
```

يبحث ثم يُولّد إجابة نصية باستخدام LLM.

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | السؤال المطلوب الإجابة عنه |
| `search_method` | `str` | طريقة البحث: `'semantic'`، `'keyword'`، أو `'hybrid'` |
| `include_sources` | `bool` | إذا `True`، يُضاف قسم المصادر في نهاية الإجابة |

**Return:**
- الإجابة النصية من LLM.
- `"I couldn't find relevant information for your question"` إذا لم توجد نتائج.
- `"Language model is not available"` إذا كان `rag.llm` هو `None`.

**تنسيق المصادر** (عند `include_sources=True`):
```
📚 Sources:
- doc_id_1 (similarity score: 0.85)
- doc_id_2 (similarity score: 0.72)
```
يُضاف حتى 3 مصادر فريدة فقط (مرتبة حسب ترتيب ظهورها في النتائج).

---

### `compare_methods`

```python
compare_methods(query: str, top_k: int = 5) -> Dict
```

يشغّل الطرق الثلاث على نفس الاستعلام ويُقارن النتائج.

**يُرجع dict بهذا الشكل:**

```python
{
    'query': str,                   # الاستعلام الأصلي
    'semantic': List[Tuple],        # نتائج البحث الدلالي
    'keyword': List[Tuple],         # نتائج البحث النصي
    'hybrid': List[Tuple],          # نتائج البحث الهجين
    'overlap': {
        'semantic_keyword': int,    # عدد النتائج المشتركة بين الدلالي والنصي
        'semantic_hybrid': int,     # عدد النتائج المشتركة بين الدلالي والهجين
        'keyword_hybrid': int       # عدد النتائج المشتركة بين النصي والهجين
    }
}
```

> **تحذير:** هذه الدالة تستدعي الطرق الثلاثة كاملة، مما يعني ضعف استهلاك الموارد مقارنة ببحث واحد. استخدمها للتشخيص والاختبار فقط.

---

### `get_stats`

```python
get_stats() -> dict
```

**يُرجع dict شامل بحالة النظام وإحصائياته:**

```python
{
    'total_searches': int,       # إجمالي عمليات البحث (يُحسب فقط في hybrid_search)
    'semantic_searches': int,    # عدد استدعاءات semantic_search
    'keyword_searches': int,     # عدد استدعاءات keyword_search
    'hybrid_searches': int,      # عدد استدعاءات hybrid_search
    'is_trained': bool,          # هل تم تدريب الفهرس النصي
    'indexed_documents': int,    # عدد المستندات المفهرسة
    'keyword_method': str,       # 'bm25' أو 'tfidf'
    'language': str,             # اللغة المُستخدمة
    'use_lemmatization': bool,
    'fusion_method': str,        # طريقة الدمج المُستخدمة
    'weights': {
        'semantic': float,       # الوزن الدلالي من config
        'keyword': float         # الوزن النصي من config
    }
}
```

> **ملاحظة:** `total_searches` يعكس فقط استدعاءات `hybrid_search`، ليس مجموع كل الطرق. لحساب الإجمالي الحقيقي: `stats['semantic_searches'] + stats['keyword_searches'] + stats['hybrid_searches']`.

---

## الواجهة غير المتزامنة (Async API)

يدعم النظام `async/await` الكامل عبر `asyncio.to_thread` للدوال المتزامنة، مع تحسين حقيقي بالتوازي في `ahybrid_search`.

### `asemantic_search`

```python
async asemantic_search(query: str, top_k=None) -> List[Tuple]
```

نسخة غير متزامنة من `semantic_search`. تُشغّل الدالة المتزامنة في thread منفصل.

---

### `akeyword_search`

```python
async akeyword_search(query: str, top_k=None) -> List[Tuple]
```

نسخة غير متزامنة من `keyword_search`. تُشغّل الدالة المتزامنة في thread منفصل.

---

### `ahybrid_search`

```python
async ahybrid_search(
    query: str,
    top_k=None,
    semantic_weight=None,
    keyword_weight=None
) -> List[Tuple]
```

نسخة غير متزامنة مُحسَّنة من `hybrid_search`. **تُشغّل البحث الدلالي والنصي بالتوازي** باستخدام `asyncio.gather`، مما يُقلل وقت الاستجابة عند استخدام embeddings أو BM25 بطيئة.

---

### `agenerate`

```python
async agenerate(
    query: str,
    search_method: str = "hybrid",
    include_sources: bool = False
) -> str
```

نسخة غير متزامنة من `generate`. إذا كان LLM يدعم `generate_async`، يستخدمه مباشرة؛ وإلا يُشغّل `generate` في thread منفصل.

---

### `astream`

```python
async astream(query: str, search_method: str = "hybrid") -> AsyncGenerator[str, None]
```

مولّد غير متزامن يُعيد الإجابة كلمة بكلمة (streaming).

| المعامل | النوع | الوصف |
|---|---|---|
| `query` | `str` | الاستعلام |
| `search_method` | `str` | طريقة البحث: `'semantic'`، `'keyword'`، أو `'hybrid'` |

**سلوك مهم:**
- يستخدم دائماً `ahybrid_search` داخلياً بغض النظر عن `search_method` (الـ parameter محجوز للمستقبل).
- يبني prompt يتضمن السياق المسترجع كاملاً للغتين العربية والإنجليزية.
- إذا كان LLM يدعم `astream`، يستخدمه للـ streaming الحقيقي token-by-token.
- إذا لم يدعمه، يُولّد الإجابة كاملة ثم يُرسلها كلمة بكلمة.
- يُعيد `"No info found"` إذا لم توجد نتائج.

```python
async for token in hybrid.astream("ما هو التعلم الآلي؟"):
    print(token, end="", flush=True)
```

---

### Context Manager غير المتزامن

```python
async with HybridSearchRAG(...) as hybrid:
    results = await hybrid.ahybrid_search(query)
```

`__aenter__` يُرجع `self`، و`__aexit__` يُرجع `False` (لا يكتم الاستثناءات).

---

## المحركات الداخلية

### `BM25Scorer`

محرك البحث النصي المُوصى به. يُستخدم عند `keyword_method='bm25'`.

**المعاملات:**
```python
BM25Scorer(k1=1.5, b=0.75, language='ar', use_lemmatization=True)
```

| المعامل | الوصف |
|---|---|
| `k1` | معامل تشبع تكرار الكلمة (1.2–2.0). أعلى = أبطأ تشبعاً |
| `b` | معامل تطبيع طول المستند (0–1). `0` = بلا تطبيع، `1` = تطبيع كامل |

**الصيغة المُستخدمة:**

```
score = Σ IDF(t) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × (dl / avgdl)))
```

```
IDF(t) = log((N - df + 0.5) / (df + 0.5) + 1)
```

حيث `dl` = طول المستند، `avgdl` = متوسط أطوال المستندات، `N` = عدد المستندات.

---

### `TFIDFScorer`

بديل أبسط لـ BM25. يُستخدم عند `keyword_method='tfidf'`.

**الدوال المتاحة:**

| الدالة | الوصف |
|---|---|
| `fit(documents)` | تدريب النموذج على قائمة المستندات، يحسب IDF لكل كلمة |
| `score(query, document)` | يحسب درجة TF-IDF لمستند واحد مقابل استعلام |
| `batch_score(query, documents)` | يحسب الدرجات لمجموعة مستندات دفعةً واحدة — **مطلوب داخلياً بواسطة `keyword_search`** |

**الصيغة المُستخدمة:**

```
TF(t, d)  = count(t in d) / len(d)
IDF(t)    = log((N + 1) / (df + 1)) + 1     ← smoothed لتجنب قيم Inf عند df = N، وتجنب الصفر عند df = 0
score     = Σ TF(t, d) × IDF(t)
```

> **ملاحظة حول IDF:** الصيغة المُطبَّقة هي النسخة المُخففة (smoothed) التي تضيف `+1` للبسط والمقام، مما يضمن قيماً مستقرة في جميع الحالات بما فيها الكلمات التي تظهر في كل المستندات.

> **متى تختار BM25 vs TF-IDF؟**
> BM25 أفضل للنصوص القصيرة والمتوسطة لأنه يُعالج ظاهرة تشبع التكرار ويأخذ طول المستند بعين الاعتبار. TF-IDF أبسط وأسرع قليلاً لكنه أقل دقة للنصوص غير المتساوية الطول.

---

### `StanzaTokenizer`

المحلل اللغوي المُستخدم داخلياً في BM25 وTF-IDF.

**الميزات:**
- يدعم التجذير اللغوي (lemmatization) عبر Stanza.
- يتراجع تلقائياً إلى `_simple_tokenize` إذا لم يكن Stanza متاحاً.
- يُصفّي الكلمات أحادية الحرف والرموز والأرقام.

**`_simple_tokenize` (الوضع الاحتياطي):**
- يُزيل الرموز والأرقام بـ regex.
- يُقسّم على المسافات.
- يُصفّي الكلمات بطول حرف واحد.

---

## طرق الدمج الداخلية

### `_weighted_sum_fusion`

```
final_score = normalize(sem_score) × sem_weight + normalize(key_score) × key_weight
```

- تطبيع Min-Max لكل مجموعة نتائج على حدة قبل الدمج.
- المستندات التي تظهر في طريقة واحدة فقط تحصل على `0.0` للطريقة الأخرى.
- النتائج ذات `final_score < config.min_score` تُحذف.

### `_reciprocal_rank_fusion` (RRF)

```
score = Σ 1 / (k + rank)      حيث k = 60 (ثابت)
```

- لا يحتاج تطبيع الدرجات — يعتمد فقط على ترتيب النتائج.
- الثابت `k=60` مُضمَّن في الكود ولا يمكن تغييره من `SearchConfig` حالياً.

### `_max_fusion`

```
final_score = max(normalize(sem_score), normalize(key_score))
```

- يُطبّع الدرجتين ثم يختار الأعلى لكل مستند.

### `_normalize_scores`

يُطبّع قائمة درجات إلى نطاق `[0, 1]` بـ Min-Max:

```
normalized = (score - min) / (max - min)
```

**حالات خاصة:**
- قائمة فارغة → قائمة فارغة.
- جميع الدرجات صفر → قائمة من الأصفار (لا يُعطي وزناً زائفاً للمستندات غير ذات الصلة).
- جميع الدرجات متساوية وغير صفر → قائمة من الواحدات (جميع المستندات بنفس الأهمية النسبية).

---

## مثال عملي شامل

```python
import asyncio
from rag.hybrid_search import HybridSearchRAG
from rag.hybrid_search import SearchConfig
from chunks import MultilanguageTextChunker
from vector_database import FAISSVectorDatabase
from context import ContextManager
from rag.core import RAGSystem
    # chunk_size=300 يستوعب الجمل العربية الطويلة (max = 300 × 1.05 = 315 حرف)
chunker     = MultilanguageTextChunker(chunk_size=300, overlap=50)
ctx_manager = ContextManager()
vector_db = FAISSVectorDatabase(embedder=embedder)
from rag.core import RAGSystem


# --- 1. إعداد النظام الأساسي ---
base_rag = RAGSystem(
    vector_db=vector_db,
    llm=llm,
    chunker=chunker,
    context_manager=ctx_manager,
)

base_rag.add_documents({
    "nlp": (
        "معالجة اللغة الطبيعية (NLP) هي فرع من فروع الذكاء الاصطناعي يُعنى بتمكين الحواسيب من فهم اللغة البشرية وتحليلها وتوليدها. "
        "تشمل تطبيقاتها: الترجمة الآلية بين اللغات، تحليل المشاعر في النصوص، استخراج المعلومات من المستندات، "
        "التلخيص الآلي، الإجابة على الأسئلة، وتصنيف النصوص. "
        "من أبرز تقنياتها: نماذج المحولات (Transformers) مثل BERT وGPT، "
        "ونماذج التضمين (Word Embeddings) مثل Word2Vec وGloVe التي تُحوّل الكلمات إلى متجهات رقمية."
    ),

    "dl": (
        "التعلم العميق (Deep Learning) هو فرع من تعلم الآلة يعتمد على شبكات عصبية اصطناعية متعددة الطبقات مستوحاة من الدماغ البشري. "
        "تُستخدم الشبكات العصبية الالتفافية (CNN) في معالجة الصور والتعرف على الوجوه، "
        "بينما تُستخدم الشبكات العصبية المتكررة (RNN/LSTM) في معالجة البيانات المتسلسلة كالنصوص والصوت. "
        "يحتاج التعلم العميق إلى كميات كبيرة من البيانات وقوة حوسبة عالية (GPU)، "
        "وقد حقق نتائج متميزة في مجالات التعرف على الصور والكلام وترجمة اللغات."
    ),

    "rl": (
        "التعلم المعزز (Reinforcement Learning) هو أسلوب في تعلم الآلة يُدرّب الوكلاء (Agents) على اتخاذ قرارات متسلسلة "
        "عبر التفاعل المستمر مع بيئة ديناميكية. يتلقى الوكيل مكافأة عند اتخاذ قرار صحيح وعقوبة عند الخطأ، "
        "بهدف تعظيم المكافأة الإجمالية على المدى البعيد. "
        "من أشهر خوارزمياته: Q-Learning وDeep Q-Networks (DQN) وPPO. "
        "يُطبَّق في الألعاب الإلكترونية (مثل AlphaGo)، الروبوتات، السيارات ذاتية القيادة، وإدارة الموارد."
    ),

    "supervised": (
        "التعلم الخاضع للإشراف (Supervised Learning) هو أكثر أنواع تعلم الآلة شيوعاً، "
        "ويعتمد على تدريب النموذج باستخدام بيانات موسومة (labeled data) تحتوي على المدخلات والمخرجات الصحيحة. "
        "ينقسم إلى نوعين رئيسيين: التصنيف (Classification) للتنبؤ بفئات محددة كتشخيص الأمراض، "
        "والانحدار (Regression) للتنبؤ بقيم مستمرة كأسعار المنازل. "
        "أبرز خوارزمياته: الانحدار الخطي، شجرة القرار، الغابات العشوائية (Random Forest)، "
        "وآلات المتجهات الداعمة (SVM)."
    ),

    "unsupervised": (
        "التعلم غير الخاضع للإشراف (Unsupervised Learning) يتعامل مع بيانات غير موسومة بهدف اكتشاف الأنماط والهياكل الخفية. "
        "يشمل خوارزميات التجميع (Clustering) مثل K-Means والتجميع الهرمي لتقسيم البيانات إلى مجموعات متشابهة، "
        "وخوارزميات تقليل الأبعاد مثل PCA وt-SNE لتبسيط البيانات عالية الأبعاد. "
        "يُستخدم في تقسيم العملاء، اكتشاف الشذوذ (Anomaly Detection)، وضغط البيانات."
    ),

    "transformers": (
        "نماذج المحولات (Transformers) هي معمارية شبكات عصبية ثورية ظهرت عام 2017 في ورقة 'Attention is All You Need'. "
        "تعتمد على آلية الانتباه (Attention Mechanism) التي تُمكّن النموذج من ربط كل كلمة بالكلمات الأخرى في الجملة بغض النظر عن مسافتها. "
        "تُشكّل الأساس لنماذج اللغة الكبيرة مثل GPT وBERT وT5. "
        "تتفوق على RNN في معالجة النصوص الطويلة وتدعم المعالجة المتوازية مما يُسرّع التدريب بشكل كبير."
    ),
})

# --- 2. تهيئة نظام البحث الهجين ---
config = SearchConfig(
    top_k=5,
    semantic_weight=0.6,
    keyword_weight=0.4,
    fusion_method='rrf',
    min_score=0.0,
)

hybrid = HybridSearchRAG(
    rag_system=base_rag,
    config=config,
    keyword_method='bm25',
    language='ar',
    use_lemmatization=True,
)

# --- 3. تدريب الفهرس النصي (مرة واحدة بعد إضافة المستندات) ---
hybrid.train_keyword_index()

query = "ما هي تقنيات تعلم الآلة؟"

# --- 4. الطرق المتزامنة ---

# بحث دلالي فقط
sem_results = hybrid.semantic_search(query, top_k=3)
print(f"دلالي: {len(sem_results)} نتيجة")

# بحث نصي فقط
kw_results = hybrid.keyword_search(query, top_k=3)
print(f"نصي: {len(kw_results)} نتيجة")

# بحث هجين مع تجاوز الأوزان
hyb_results = hybrid.hybrid_search(
    query,
    top_k=5,
    semantic_weight=0.8,
    keyword_weight=0.2,
)
print(f"هجين: {len(hyb_results)} نتيجة")

# توليد إجابة مع المصادر
answer = hybrid.generate(query, search_method='hybrid', include_sources=True)
print(answer)

# مقارنة الطرق (للتشخيص فقط)
comparison = hybrid.compare_methods(query, top_k=3)
print(f"تداخل دلالي-نصي: {comparison['overlap']['semantic_keyword']}")

# إحصائيات النظام
stats = hybrid.get_stats()
print(f"مستندات مفهرسة: {stats['indexed_documents']}")
print(f"عمليات هجينة: {stats['hybrid_searches']}")

# --- 5. الطرق غير المتزامنة ---

async def run_async():
    # بحث دلالي غير متزامن
    sem = await hybrid.asemantic_search(query, top_k=3)

    # بحث نصي غير متزامن
    kw = await hybrid.akeyword_search(query, top_k=3)

    # بحث هجين غير متزامن (دلالي + نصي بالتوازي)
    hyb = await hybrid.ahybrid_search(
        query,
        top_k=5,
        semantic_weight=0.7,
        keyword_weight=0.3,
    )
    print(f"[Async] هجين: {len(hyb)} نتيجة")

    # توليد غير متزامن
    answer = await hybrid.agenerate(
        query,
        search_method="hybrid",
        include_sources=True,
    )
    print(f"[Async] إجابة: {answer[:100]}...")

    # streaming — token بـ token
    print("[Stream] ", end="")
    async for token in hybrid.astream(query):
        print(token, end="", flush=True)
    print()

asyncio.run(run_async())

# --- 6. كـ Context Manager ---
async def run_with_context_manager():
    async with HybridSearchRAG(base_rag, config=config) as h:
        h.train_keyword_index()
        results = await h.ahybrid_search(query)
        print(f"نتائج: {len(results)}")

asyncio.run(run_with_context_manager())
```

---

## أسئلة شائعة

**هل يجب استدعاء `train_keyword_index` يدوياً؟**
لا، يُستدعى تلقائياً عند الحاجة. لكن يُنصح باستدعائه صراحةً بعد إضافة المستندات لتجنب التأخير في أول استعلام.

**ماذا يحدث إذا أضفت مستندات جديدة بعد التدريب؟**
الفهرس النصي لن يتحدث تلقائياً. يجب استدعاء `train_keyword_index()` من جديد.

**هل يمكن تمرير `semantic_weight=0.0` أو `keyword_weight=0.0`؟**
نعم، يعمل بشكل صحيح في `hybrid_search` و`ahybrid_search`. كلاهما يستخدم `is not None` للتحقق من القيمة، لذا `0.0` يُعامَل كقيمة صريحة ولا يُتجاهل لصالح قيمة `config`. هذا يسمح مثلاً بتعطيل البحث النصي كلياً بتمرير `keyword_weight=0.0`.

**ما الفرق بين `total_searches` وباقي الإحصائيات؟**
`total_searches` يُحسب فقط داخل `hybrid_search`. للحصول على إجمالي حقيقي، اجمع: `semantic_searches + keyword_searches + hybrid_searches`.