
---

# 🦙 OllamaEmbedder — نماذج Ollama المحلية

## نظرة عامة

`OllamaEmbedder` يُشغّل نماذج التضمين **محلياً بالكامل** عبر Ollama دون الحاجة لأي مفتاح API أو إنترنت. مثالي للخصوصية وتجنب التكاليف وبيئات العمل المعزولة.

---

## التثبيت

```bash
# 1. تثبيت Ollama
# من: https://ollama.ai

# 2. تحميل نموذج
ollama pull nomic-embed-text   # موصى به للعربية

# 3. مكتبة Python
pip install ollama
```

```python
from embeddings import OllamaEmbedder
```

---

## النماذج المتاحة

| النموذج | الأبعاد | الرموز | دعم العربية |
|---|---|---|---|
| `nomic-embed-text` | 768 | 8192 | جيد ← **موصى به** |
| `bge-m3` | 1024 | 8192 | ممتاز |
| `mxbai-embed-large` | 1024 | 512 | أساسي |
| `all-minilm` | 384 | 256 | أساسي |
| `snowflake-arctic-embed` | 1024 | 512 | أساسي |

---

## الدوال الرئيسية

### `__init__`

```python
OllamaEmbedder(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434",
    normalize_embeddings=True,
    batch_size=32,
    max_length=None,
    cache_embeddings=False,
    show_progress=False,
    timeout=60,
    max_retries=3,
    retry_delay=1.0,
    auto_start_server=False,
    server_start_wait=5
)
```

| المعامل | النوع | الوصف |
|---|---|---|
| `base_url` | `str` | عنوان خادم Ollama (افتراضي: `http://localhost:11434`) |
| `auto_start_server` | `bool` | محاولة تشغيل خادم Ollama تلقائياً |
| `server_start_wait` | `int` | ثواني الانتظار بعد تشغيل الخادم |

---

### `encode`

```python
encode(
    texts: Union[str, List[str]],
    show_progress_bar: bool = False,
    convert_to_numpy: bool = True
) -> np.ndarray
```

---

### `list_models`

```python
list_models() -> List[str]
```

**الوصف:** قائمة بجميع النماذج المُحمَّلة في Ollama.

---

### `is_model_available`

```python
is_model_available(model_name: str = None) -> bool
```

**الوصف:** التحقق من توفر نموذج معين.

---

### `pull_model`

```python
pull_model(model_name: str = None) -> bool
```

**الوصف:** تحميل نموذج من مستودع Ollama.

---

### `get_server_info`

```python
get_server_info() -> Dict[str, Any]
```

**الوصف:** معلومات خادم Ollama (الحالة، الإصدار، إلخ).

---

### `get_model_info`

```python
get_model_info() -> Dict[str, Any]
```

---

## مثال عملي

```python
from embeddings import OllamaEmbedder

# --- 1. التهيئة ---
embedder = OllamaEmbedder(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434",
    normalize_embeddings=True,
    batch_size=16,
    cache_embeddings=True,
)

# --- 2. فحص الخادم ---
server_info = embedder.get_server_info()
print(f"🖥️ خادم Ollama: {server_info}")

# --- 3. فحص النموذج ---
if not embedder.is_model_available():
    print("📥 تحميل النموذج...")
    success = embedder.pull_model()
    print(f"{'✅' if success else '❌'} التحميل")

# --- 4. قائمة النماذج المتاحة ---
available = embedder.list_models()
print(f"\n📦 النماذج المتاحة: {available}")

# --- 5. التحقق من الاتصال ---
status = embedder.validate_connection(detailed=True)
print(f"\n✅ الاتصال: {status['success']}")
print(f"   الأبعاد: {status['embedding_dim']}")
print(f"   الوقت: {status['encoding_time']}")

# --- 6. تحويل نصوص ---
texts = [
    "الذكاء الاصطناعي يُغيّر مستقبل البشرية.",
    "تعلم الآلة يستخدم البيانات لبناء نماذج ذكية.",
    "Artificial intelligence transforms industries.",
    "Machine learning builds intelligent models from data.",
]

embeddings = embedder.encode(texts, show_progress_bar=True)
print(f"\n📊 الشكل: {embeddings.shape}")

# --- 7. البحث ---
query = "ما هو تعلم الآلة؟"
results = embedder.batch_similarity(query, texts, top_k=2)
print(f"\n🔍 أقرب نصين لـ '{query}':")
for idx, score in results:
    print(f"  [{idx}] {score:.3f}: {texts[idx]}")

# --- 8. التشابه ---
ar_en_sim = embedder.similarity(texts[0], texts[2])
print(f"\n↔️ تشابه عربي-إنجليزي: {ar_en_sim:.3f}")

# --- 9. نموذج bge-m3 (أفضل للعربية) ---
bge_embedder = OllamaEmbedder(
    model_name="bge-m3",        # أفضل دعم للعربية
    normalize_embeddings=True,
)
if bge_embedder.is_model_available("bge-m3"):
    bge_emb = bge_embedder.encode("نص عربي للاختبار")
    print(f"\n🔥 bge-m3: {bge_emb.shape}")
else:
    print("\n💡 لتحميل bge-m3: ollama pull bge-m3")

# --- 10. معلومات النموذج ---
info = embedder.get_model_info()
print(f"\n📋 معلومات النموذج:")
print(f"  الاسم: {info['model_name']}")
print(f"  الأبعاد: {info['embedding_dim']}")
print(f"  عنوان الخادم: {info.get('base_url', 'N/A')}")

```
