# ⚙️ EmbedderConfig — ملف الإعدادات المشتركة

## نظرة عامة

`EmbedderConfig` هو dataclass مركزي يحتوي على جميع الإعدادات الافتراضية المشتركة بين كل الـ Embedders. يمكنك إنشاء كائن منه وتمريره للمحوّل، أو الاعتماد على القيم الافتراضية مباشرة.

---

## التثبيت والاستيراد

```python
from embeddings import EmbedderConfig
```

---

## جميع المعاملات

```python
@dataclass
class EmbedderConfig:
    # إعدادات النموذج
    model_name: str = "multilingual"
    device: Optional[str] = None
    cache_dir: Optional[str] = None

    # إعدادات التضمين
    batch_size: int = 32
    normalize_embeddings: bool = True
    max_seq_length: int = 512

    # إعدادات المعالجة
    enable_preprocessing: bool = True
    enable_arabic_normalization: bool = True

    # إعدادات الكاش
    enable_cache: bool = False
    cache_size: int = 10000

    # إعدادات الأداء
    show_progress_bar: bool = False
    convert_to_numpy: bool = True
    skip_preprocessing: bool = False
    return_valid_indices: bool = False

    # إعدادات إضافية
    extra_config: Dict[str, Any] = field(default_factory=dict)
    track_processing_stats: bool = True
    auto_download: bool = True
    trust_remote_code: bool = False

    # إعدادات Ollama
    base_url: str = "http://127.0.0.1:11434"
    host: str = "localhost"
    port: int = 11434
    embedding_model: str = "nomic-embed-text"
```

---

## شرح المعاملات

### إعدادات النموذج

| المعامل | القيمة الافتراضية | الوصف |
|---|---|---|
| `model_name` | `"multilingual"` | اسم النموذج الافتراضي |
| `device` | `None` | الجهاز — `None` يعني كشف تلقائي (GPU > MPS > CPU) |
| `cache_dir` | `None` | مجلد حفظ النماذج المُحمَّلة (يستخدم مجلد HuggingFace الافتراضي) |

### إعدادات التضمين

| المعامل | القيمة الافتراضية | الوصف |
|---|---|---|
| `batch_size` | `32` | عدد النصوص في الدفعة الواحدة |
| `normalize_embeddings` | `True` | تطبيع المتجهات لوحدة القياس (مطلوب لحساب cosine similarity) |
| `max_seq_length` | `512` | أقصى عدد رموز للنص (النصوص الأطول تُقطع) |

### إعدادات المعالجة

| المعامل | القيمة الافتراضية | الوصف |
|---|---|---|
| `enable_preprocessing` | `True` | تفعيل المعالجة المسبقة للنصوص |
| `enable_arabic_normalization` | `True` | تطبيع النصوص العربية (مستخدم في `ArabicEmbedder`) |

### إعدادات الكاش

| المعامل | القيمة الافتراضية | الوصف |
|---|---|---|
| `enable_cache` | `False` | تفعيل الكاش (يتطلب ذاكرة إضافية) |
| `cache_size` | `10000` | أقصى عدد متجهات في الكاش |

### إعدادات الأداء

| المعامل | القيمة الافتراضية | الوصف |
|---|---|---|
| `show_progress_bar` | `False` | شريط التقدم (يتطلب `tqdm`) |
| `convert_to_numpy` | `True` | تحويل المتجهات إلى numpy array |
| `skip_preprocessing` | `False` | تخطي المعالجة المسبقة |
| `return_valid_indices` | `False` | إرجاع فهارس النصوص الصالحة |
| `track_processing_stats` | `True` | تتبع إحصائيات المعالجة |
| `auto_download` | `True` | تحميل النماذج تلقائياً |
| `trust_remote_code` | `False` | السماح بتنفيذ كود النموذج |

### إعدادات Ollama

| المعامل | القيمة الافتراضية | الوصف |
|---|---|---|
| `base_url` | `"http://127.0.0.1:11434"` | عنوان خادم Ollama |
| `host` | `"localhost"` | اسم المضيف |
| `port` | `11434` | المنفذ |
| `embedding_model` | `"nomic-embed-text"` | النموذج الافتراضي لـ Ollama |

---

## أنماط الاستخدام

### 1. استخدام القيم الافتراضية مباشرة (الأبسط)

```python
from embeddings.arabic_embedder import ArabicEmbedder

# يستخدم EmbedderConfig افتراضياً داخلياً
embedder = ArabicEmbedder(model_name="multilingual")
```

---

### 2. تخصيص الإعدادات

```python
from embeddings import EmbedderConfig
from embeddings import ArabicEmbedder

config = EmbedderConfig(
    batch_size=64,
    normalize_embeddings=True,
    enable_cache=True,
    cache_size=5000,
    show_progress_bar=True,
    track_processing_stats=True,
)

embedder = ArabicEmbedder(
    model_name="multilingual",
    batch_size=config.batch_size,
    normalize_embeddings=config.normalize_embeddings,
    cache_embeddings=config.enable_cache,
)
```

---

### 3. إعدادات للإنتاج (Production)

```python
from embeddings import EmbedderConfig

production_config = EmbedderConfig(
    batch_size=128,               # دفعات أكبر للسرعة
    normalize_embeddings=True,
    enable_cache=True,
    cache_size=50000,             # كاش أكبر
    show_progress_bar=False,      # إيقاف التقدم للإنتاج
    track_processing_stats=True,
    auto_download=True,
    device=None,                  # كشف GPU تلقائياً
)
```

---

### 4. إعدادات للتطوير (Development)

```python
dev_config = EmbedderConfig(
    batch_size=8,                 # دفعات صغيرة لتجنب overflow الذاكرة
    enable_cache=False,           # لا كاش عند الاختبار
    show_progress_bar=True,       # عرض التقدم
    track_processing_stats=True,
)
```

---

### 5. إعدادات Ollama

```python
from embeddings import EmbedderConfig
from embeddings import OllamaEmbedder

ollama_config = EmbedderConfig(
    embedding_model="bge-m3",
    base_url="http://localhost:11434",
    batch_size=16,
    normalize_embeddings=True,
    enable_cache=True,
)

embedder = OllamaEmbedder(
    model_name=ollama_config.embedding_model,
    base_url=ollama_config.base_url,
    batch_size=ollama_config.batch_size,
    cache_embeddings=ollama_config.enable_cache,
)
```

---

## مثال عملي كامل

```python
from embeddings.config_embedder import EmbedderConfig
from embeddings.arabic_embedder import ArabicEmbedder
from embeddings.ollama_embedder import OllamaEmbedder
from embeddings.openai_embedder import OpenAIEmbedder
import os

# --- إعدادات مختلفة لسيناريوهات مختلفة ---

# 1. للاختبار السريع
test_config = EmbedderConfig(
    batch_size=8,
    show_progress_bar=True,
    enable_cache=False,
)

# 2. للإنتاج عالي الأداء
prod_config = EmbedderConfig(
    batch_size=256,
    enable_cache=True,
    cache_size=100000,
    show_progress_bar=False,
    normalize_embeddings=True,
)

# 3. للعربية فقط
arabic_config = EmbedderConfig(
    model_name="arabert",
    enable_preprocessing=True,
    enable_arabic_normalization=True,
    batch_size=32,
    max_seq_length=256,
)

# 4. لـ Ollama المحلي
ollama_config = EmbedderConfig(
    embedding_model="bge-m3",
    base_url="http://localhost:11434",
    enable_cache=True,
    batch_size=16,
)

# --- تطبيق الإعدادات ---
print("📋 إعدادات الاختبار:")
print(f"  batch_size: {test_config.batch_size}")
print(f"  cache: {test_config.enable_cache}")

print("\n📋 إعدادات الإنتاج:")
print(f"  batch_size: {prod_config.batch_size}")
print(f"  cache_size: {prod_config.cache_size}")

# إنشاء محوّل باستخدام الإعدادات
arabic_emb = ArabicEmbedder(
    model_name=arabic_config.model_name,
    batch_size=arabic_config.batch_size,
    enable_preprocessing=arabic_config.enable_preprocessing,
    normalize_embeddings=arabic_config.normalize_embeddings,
    max_seq_length=arabic_config.max_seq_length,
)

result = arabic_emb.encode("مرحباً بكم في عالم الذكاء الاصطناعي")
print(f"\n✅ التضمين: {result.shape}")
```
