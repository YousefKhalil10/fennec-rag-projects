
> **نظرة عامة | Overview**  
> هذه المكتبة توفر واجهة موحدة للتعامل مع أشهر نماذج اللغة الكبيرة (LLMs) — OpenAI، Anthropic (Claude)، Google Gemini، Mistral، HuggingFace، وOllama — بنفس الـ API، مع دعم كامل للتوليد المتزامن، وغير المتزامن، والبث (Streaming).  
> This library provides a unified interface for all major LLM providers with identical API across sync, async, and streaming modes.

---


### `llm_config`

**الوصف:** `dataclass` يحتوي على جميع القيم الافتراضية المشتركة بين جميع الواجهات. يمكن تعديله مرة واحدة لتغيير سلوك المكتبة كلها.

**الحقول | Fields:**

| الحقل | القيمة الافتراضية | الوصف |
|-------|------------------|-------|
| `max_token` | `2048` | الحد الأقصى لعدد الـ tokens في كل استجابة |
| `temperature` | `0.3` | درجة العشوائية في التوليد (0 = حتمي، 1 = إبداعي) |
| `top_p` | `0.9` | Nucleus sampling — نسبة احتمالية الـ tokens المختارة |
| `top_k` | `50` | الحد الأقصى لعدد الـ tokens المرشحة في كل خطوة |
| `hugginface_model` | `"aubmindlab/bert-base-arabertv2"` | النموذج الافتراضي لـ HuggingFace |
| `gemini_model` | `"gemini-3-flash-preview"` | النموذج الافتراضي لـ Gemini |
| `mistral_model` | `"mistral-large-latest"` | النموذج الافتراضي لـ Mistral |
| `ollama_model` | `"llama2"` | النموذج الافتراضي لـ Ollama |
| `ollama_base_url` | `"http://127.0.0.1:11434"` | عنوان سيرفر Ollama المحلي |
| `time_out` | `60` | مهلة الطلب بالثواني لـ Ollama |

**مثال:**

```python
from llm import llm_config

config = llm_config()
print(config.max_token)     # 2048
print(config.temperature)   # 0.3

# تخصيص الإعدادات
config = llm_config(max_token=4096, temperature=0.7)
```

---


### `BaseLLMInterface` *(Abstract)*

**الوصف:** الفئة الأساسية المجردة التي ترث منها جميع الواجهات. تُعرّف العقد المشترك (generate، generate_async، astream) وتوفر أدوات مساعدة مشتركة كالتحقق من الاتصال والحماية من الهلوسة.

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الوصف |
|-----------|-------|-------|
| `model_name` | `str` | اسم النموذج المستخدم |
| `api_key` | `str` | مفتاح API للخدمة |
| `**kwargs` | — | إعدادات إضافية تُحفظ في `self.kwargs` |

---

#### `generate(prompt, max_tokens, temperature, **kwargs)` *(abstract)*

**الوصف:** توليد نص بشكل متزامن (sync). يجب تطبيقه في كل فئة فرعية.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `prompt` | `str` | — | النص المدخل للنموذج |
| `max_tokens` | `int` | `2048` | الحد الأقصى للـ tokens في الاستجابة |
| `temperature` | `float` | `0.3` | درجة العشوائية (0.0–1.0) |
| `**kwargs` | — | — | معاملات إضافية خاصة بكل مزود |

**Return:** `str`

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)` *(abstract)*

**الوصف:** نسخة غير متزامنة (async) من `generate`. تُستخدم في السياقات التي تتطلب `await`.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `prompt` | `str` | — | النص المدخل |
| `max_tokens` | `int` | `2048` | الحد الأقصى للـ tokens |
| `temperature` | `float` | `0.3` | درجة العشوائية |

**Return:** `Coroutine[str]`

**مثال:**

```python
import asyncio

async def main():
    response = await llm.generate_async("ما هو الذكاء الاصطناعي؟")
    print(response)

asyncio.run(main())
```

---

#### `astream(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** بث الاستجابة token بـ token كـ AsyncGenerator. الإعداد الافتراضي يُولّد الاستجابة الكاملة ثم يُعيدها كلمةً كلمة. الواجهات التي تدعم البث الأصلي (OpenAI، Anthropic، Mistral) تتجاوز هذا السلوك لبث حقيقي.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `prompt` | `str` | — | النص المدخل |
| `max_tokens` | `int` | `2048` | الحد الأقصى للـ tokens |
| `temperature` | `float` | `0.3` | درجة العشوائية |

**Return:** `AsyncIterator[str]`

**مثال:**

```python
async def stream_response():
    async for token in llm.astream("اكتب قصة قصيرة"):
        print(token, end="", flush=True)

asyncio.run(stream_response())
```

---

#### `validate_connection(test_prompt, max_tokens, temperature, async_mode)`

**الوصف:** اختبار الاتصال بالنموذج والتحقق من أن الـ API Key صحيح وأن الخدمة تعمل. مفيد جداً في التشخيص والإعداد الأولي.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `test_prompt` | `str` | `"test"` | نص الاختبار |
| `max_tokens` | `int` | `10` | عدد tokens محدود للاختبار السريع |
| `temperature` | `float` | `0.7` | درجة العشوائية |
| `async_mode` | `bool` | `False` | استخدام الوضع غير المتزامن للاختبار |

**Return:** `dict` — `{"success": bool, "reason": str, "response": str}`

**مثال:**

```python
from llm import OpenAIInterface

llm = OpenAIInterface(model_name="gpt-4", api_key="sk-...")
result = llm.validate_connection()

if result["success"]:
    print("✓ الاتصال يعمل بنجاح!")
    print(f"الاستجابة: {result['response']}")
else:
    print(f"✗ فشل الاتصال: {result['reason']}")
```

---

#### `with_hallucination_guard(...)`

**الوصف:** تُلفّ الواجهة الحالية بطبقة حماية من الهلوسة (Hallucination Guard). تُرجع `ProtectedLLMInterface` تعمل بنفس واجهة `BaseLLMInterface` مع فحوصات إضافية على الاستجابات.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `auto_retry` | `bool` | `True` | إعادة المحاولة تلقائياً عند اكتشاف هلوسة |
| `max_retries` | `int` | `3` | أقصى عدد للمحاولات |
| `strict_mode` | `bool` | `False` | الوضع الصارم — رفض أي إجابة مشبوهة |
| `verbose` | `bool` | `True` | طباعة تفاصيل الفحوصات |
| `threshold` | `float` | `0.7` | حد الثقة المطلوب (0.0–1.0) |
| `require_sources` | `bool` | `True` | اشتراط المصادر في الاستجابة |
| `domain` | `str` | `None` | مجال متخصص: `"medical"`, `"legal"`, `"financial"`, `"educational"`, `"customer_service"`, `"creative_writing"` |

**Return:** `ProtectedLLMInterface`

**مثال:**

```python
llm = OpenAIInterface(model_name="gpt-4", api_key="sk-...")

# حماية عامة
protected = llm.with_hallucination_guard(strict_mode=True, threshold=0.8)
result = protected.generate("ما هي أعراض مرض السكري؟")
print(result["response"])

# حماية متخصصة للمجال الطبي
medical_llm = llm.with_hallucination_guard(domain="medical")
result = medical_llm.generate("ما الجرعة الآمنة من الأسبرين؟")
```

---

#### `__aenter__` / `__aexit__` / `acleanup()`

**الوصف:** دعم نمط Context Manager غير المتزامن (`async with`). يستدعي `acleanup()` تلقائياً عند الخروج لتحرير الموارد (جلسات HTTP، اتصالات مفتوحة).

**مثال:**

```python
async def main():
    async with OpenAIInterface(model_name="gpt-4", api_key="sk-...") as llm:
        response = await llm.generate_async("مرحباً!")
        print(response)
    # acleanup() يُستدعى تلقائياً هنا
```

---


### `OpenAIInterface`

**الوصف:** واجهة OpenAI GPT مع دعم كامل للتوليد المتزامن، وغير المتزامن، والبث الأصلي (native streaming). تستخدم مكتبة `openai` الرسمية.

> ⚠️ يتطلب: `pip install openai`

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `"gpt-4"` | اسم النموذج: `"gpt-4"`, `"gpt-4o"`, `"gpt-3.5-turbo"`, ... |
| `api_key` | `str` | `None` | مفتاح OpenAI API |

**مثال:**

```python
from llm import OpenAIInterface

llm = OpenAIInterface(model_name="gpt-4o", api_key="sk-...")
```

---

#### `generate(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد نص بشكل متزامن عبر OpenAI Chat Completions API.

```python
response = llm.generate(
    "اشرح مفهوم الـ RAG في جملتين.",
    max_tokens=200,
    temperature=0.5
)
print(response)
```

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** نسخة async من `generate` تستخدم `AsyncOpenAI`.

```python
async def main():
    response = await llm.generate_async("ما الفرق بين GPT-3 وGPT-4؟")
    print(response)
```

---

#### `astream(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** بث أصلي من OpenAI — يُرجع كل token فور وصوله عبر Server-Sent Events.

```python
async def stream():
    async for token in llm.astream("اكتب قصيدة عن البحر"):
        print(token, end="", flush=True)
```

---


### `AnthropicInterface`

**الوصف:** واجهة Anthropic Claude مع دعم التوليد المتزامن، وغير المتزامن، والبث الأصلي عبر `anthropic.messages.stream`. تستخدم مكتبة `anthropic` الرسمية.

> ⚠️ يتطلب: `pip install anthropic`

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `"claude-3-5-sonnet-20241022"` | اسم نموذج Claude |
| `api_key` | `str` | `None` | مفتاح Anthropic API |

**نماذج Claude المتاحة:**
- `claude-3-5-sonnet-20241022` — الأكثر توازناً ✅ موصى به
- `claude-3-5-haiku-20241022` — الأسرع والأوفر
- `claude-3-opus-20240229` — الأقوى والأكثر تفصيلاً

**مثال:**

```python
from llm import AnthropicInterface

llm = AnthropicInterface(
    model_name="claude-3-5-sonnet-20241022",
    api_key="sk-ant-..."
)
```

---

#### `generate(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد متزامن عبر Anthropic Messages API.

```python
response = llm.generate("لخّص هذا النص في نقطتين: ...")
print(response)
```

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد غير متزامن باستخدام `AsyncAnthropic`.

```python
async def main():
    response = await llm.generate_async("حلل هذه البيانات...")
    print(response)
```

---

#### `astream(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** بث أصلي من Claude عبر `messages.stream` — يُرجع كل token فور توليده.

```python
async def stream():
    async with AnthropicInterface(api_key="sk-ant-...") as llm:
        async for token in llm.astream("اشرح الشبكات العصبية بالتفصيل"):
            print(token, end="", flush=True)
```

---

#### `acleanup()`

**الوصف:** يُغلق اتصال `AsyncAnthropic` وتحرير الموارد. يُستدعى تلقائياً عند استخدام `async with`.

---


### `GeminiInterface`

**الوصف:** واجهة Google Gemini محسّنة مع دعم للإجابات الطويلة والنصوص العربية. تتضمن منطق إعادة المحاولة التلقائية (retry) مع انتظار تدريجي لمعالجة أخطاء 503/429.

> ⚠️ يتطلب: `pip install google-genai`

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `"gemini-3-flash-preview"` | اسم نموذج Gemini |
| `api_key` | `str` | `None` | مفتاح Google AI API |

**مثال:**

```python
from llm import GeminiInterface

llm = GeminiInterface(
    model_name="gemini-2.0-flash-exp",
    api_key="AIza..."
)
```

---

#### `generate(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد متزامن مع إعادة المحاولة التلقائية (حتى 5 مرات) عند أخطاء 503/UNAVAILABLE/429. يقبل `top_p` و`top_k` كـ kwargs.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `prompt` | `str` | — | النص المدخل |
| `max_tokens` | `int` | `None` | `None` يستخدم القيمة الافتراضية الكبيرة من `default_config` |
| `temperature` | `float` | `None` | `None` يستخدم الإعداد الافتراضي |
| `top_p` | `float` | `0.9` | (عبر kwargs) |
| `top_k` | `int` | `50` | (عبر kwargs) |

```python
response = llm.generate(
    "اكتب تقريراً عن أحدث تطورات الذكاء الاصطناعي",
    max_tokens=3000,
    temperature=0.4
)
print(response)
```

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد غير متزامن باستخدام `generate_content_async`.

```python
async def main():
    response = await llm.generate_async("ترجم هذا النص للعربية: ...")
    print(response)
```

---

#### `astream(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** بث كلمة بكلمة (fallback) — Gemini لا يدعم البث الأصلي حالياً، لذا يُولَّد الرد كاملاً ثم يُبث كلمةً كلمة.

```python
async def stream():
    async for word in llm.astream("اشرح مفهوم التعلم الآلي"):
        print(word, end="", flush=True)
```

---


### `MistralInterface`

**الوصف:** واجهة Mistral AI مع دعم كامل للتوليد المتزامن، وغير المتزامن، والبث الأصلي عبر `stream_async`. تدعم جميع نماذج Mistral بما فيها نماذج المصدر المفتوح.

> ⚠️ يتطلب: `pip install mistralai`

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `"mistral-large-latest"` | اسم النموذج |
| `api_key` | `str` | `None` | مفتاح Mistral API |

**النماذج المتاحة:**

| النموذج | الوصف |
|---------|-------|
| `mistral-small-latest` | سريع وموفر التكلفة |
| `mistral-medium-latest` | متوازن |
| `mistral-large-latest` | الأقوى ✅ الافتراضي |
| `open-mistral-7b` | مفتوح المصدر |
| `open-mixtral-8x7b` | Mixture of Experts |
| `open-mixtral-8x22b` | MoE الأكبر |
| `codestral-latest` | متخصص في كتابة الكود |

**مثال:**

```python
from llm import MistralInterface

llm = MistralInterface(
    model_name="mistral-large-latest",
    api_key="..."
)
```

---

#### `generate(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد متزامن عبر Mistral Chat API.

```python
response = llm.generate("اشرح الفرق بين RAG و Fine-tuning")
print(response)
```

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد غير متزامن باستخدام `complete_async`.

```python
async def main():
    result = await llm.generate_async("ما هو Mixture of Experts؟")
    print(result)
```

---

#### `astream(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** بث أصلي حقيقي من Mistral عبر `stream_async` — يُرجع كل delta token فور وصوله.

```python
async def stream():
    async for token in llm.astream("اكتب قصيدة عن الذكاء الاصطناعي"):
        print(token, end="", flush=True)
```

---

#### `acleanup()`

**الوصف:** إغلاق اتصال Mistral client وتحرير الموارد.

---

### `HuggingFaceInterface`

**الوصف:** واجهة HuggingFace المتقدمة تدعم  نوعين من النماذج المحلية تلقائياً: **Causal LM** (GPT، LLaMA)، **Seq2Seq** (T5، BART)منهجية التوليد المناسبة.

> ⚠️ يتطلب: `pip install transformers torch`

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `"aubmindlab/bert-base-arabertv2"` | اسم النموذج من Hugging Face Hub |


**أنواع النماذج المدعومة:**

| النوع | أمثلة النماذج | الاستخدام |
|-------|--------------|-----------|
| `causal_lm` | GPT-2, LLaMA, Mistral, Falcon, Bloom | توليد نص حر |
| `seq2seq` | T5, BART, mBART, FLAN-T5 | ترجمة، تلخيص |

**مثال:**

```python
from llm import HuggingFaceInterface

# نموذج توليد نص
llm = HuggingFaceInterface("gpt2")

# نموذج ترجمة Seq2Seq
llm = HuggingFaceInterface("Helsinki-NLP/opus-mt-ar-en")
```

---

#### `generate(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد نص يختار تلقائياً المنهجية الصحيحة بناءً على نوع النموذج المكتشف.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `prompt` | `str` | — | النص المدخل |
| `max_tokens` | `int` | `2048` | الحد الأقصى للـ tokens الجديدة |
| `temperature` | `float` | `0.3` | درجة العشوائية |
| `top_p` | `float` | `0.9` | (عبر kwargs) Nucleus sampling |
| `top_k` | `int` | `50` | (عبر kwargs) Top-K sampling |
| `repetition_penalty` | `float` | `1.0` | (عبر kwargs) عقوبة التكرار |
| `num_beams` | `int` | `1` | (عبر kwargs) Beam search — للـ seq2seq فقط |
| `max_input_tokens` | `int` | `512` | (عبر kwargs) الحد الأقصى لطول المدخل |

```python
# Causal LM — توليد نص حر
llm = HuggingFaceInterface("gpt2")
response = llm.generate("الذكاء الاصطناعي هو", max_tokens=100)
print(response)
```

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** تشغيل `generate` في Thread منفصل باستخدام `asyncio.to_thread` لعدم تعطيل حلقة الأحداث.

```python
async def main():
    response = await llm.generate_async("ما هو BERT؟", max_tokens=200)
    print(response)
```

---

#### `get_model_info()`

**الوصف:** إرجاع معلومات تشخيصية عن النموذج المحمّل.

**Return:** `dict` يحتوي على:
- `model_name`: اسم النموذج
- `model_type`: النوع (`causal_lm` / `seq2seq` )
- `device`: الجهاز المستخدم (`cpu` / `cuda`)
- `has_cuda`: هل GPU متاح؟
- `tokenizer_vocab_size`: حجم مفردات الـ tokenizer

**مثال:**

```python
info = llm.get_model_info()
print(f"النموذج: {info['model_name']}")
print(f"النوع: {info['model_type']}")
print(f"الجهاز: {info['device']}")
print(f"حجم المفردات: {info['tokenizer_vocab_size']:,}")
```

---


### `OllamaInterface`

**الوصف:** واجهة النماذج المحلية عبر Ollama. تُدير دورة حياة السيرفر تلقائياً (تشغيل، إيقاف)، وتدعم التوليد المتزامن، وغير المتزامن، والبث الحقيقي عبر NDJSON. مثالية للاستخدام دون الحاجة لـ API Keys أو إرسال بيانات لسحابة خارجية.

> ⚠️ يتطلب: تثبيت [Ollama](https://ollama.ai) + `pip install aiohttp` للـ async

#### `__init__(model_name, api_key, **kwargs)`

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `"llama2"` | اسم النموذج في مكتبة Ollama |
| `api_key` | `str` | `None` | غير مستخدم لـ Ollama |
| `base_url` | `str` | `"http://127.0.0.1:11434"` | (عبر kwargs) عنوان السيرفر |
| `auto_start` | `bool` | `True` | (عبر kwargs) تشغيل السيرفر تلقائياً |

**مثال:**

```python
from llm import OllamaInterface

# سيتصل بالسيرفر تلقائياً أو يشغّله
llm = OllamaInterface(model_name="llama3")

# سيرفر بعيد
llm = OllamaInterface(
    model_name="mistral",
    base_url="http://192.168.1.10:11434",
    auto_start=False
)
```

---

#### `generate(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد متزامن عبر Ollama REST API. يُرجع رسائل خطأ واضحة عند فشل الاتصال أو انتهاء المهلة.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `prompt` | `str` | — | النص المدخل |
| `max_tokens` | `int` | `2048` | عدد الـ tokens المولدة (`num_predict`) |
| `temperature` | `float` | `0.3` | درجة العشوائية |
| `top_p` | `float` | `0.9` | (عبر kwargs) |
| `top_k` | `int` | `40` | (عبر kwargs) |
| `repeat_penalty` | `float` | `1.1` | (عبر kwargs) عقوبة التكرار |

```python
response = llm.generate("ما هو الفرق بين Docker وVirtual Machine؟")
print(response)
```

---

#### `generate_async(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** توليد غير متزامن باستخدام `aiohttp`. إذا لم تكن `aiohttp` مثبتة يُعيد التراجع لـ `asyncio.to_thread`.

```python
async def main():
    response = await llm.generate_async("اشرح مفهوم Kubernetes")
    print(response)
```

---

#### `astream(prompt, max_tokens, temperature, **kwargs)`

**الوصف:** بث أصلي حقيقي من Ollama عبر NDJSON stream — يُرجع كل token فور توليده من النموذج المحلي.

```python
async def stream():
    async for token in llm.astream("اكتب كود Python لفرز قائمة"):
        print(token, end="", flush=True)
```

---

#### `list_models()`

**الوصف:** إرجاع قائمة بجميع النماذج المحمّلة على سيرفر Ollama.

**Return:** `List[str]`

```python
models = llm.list_models()
print("النماذج المتاحة:", models)
# ['llama3:latest', 'mistral:latest', 'codellama:latest']
```

---

#### `pull_model(model_name)`

**الوصف:** تحميل نموذج جديد من مكتبة Ollama مباشرةً من الكود.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `model_name` | `str` | `None` | اسم النموذج (None = يستخدم `self.model_name`) |

**Return:** `bool` — `True` إذا نجح التحميل

```python
success = llm.pull_model("llama3:8b")
if success:
    print("✓ تم تحميل النموذج بنجاح")
```

---

#### `_check_server_status()`

**الوصف:** فحص ما إذا كان سيرفر Ollama يعمل حالياً. يستخدم داخلياً عند التهيئة وعند إعادة المحاولة.

**Return:** `bool`

```python
if llm._check_server_status():
    print("✓ السيرفر يعمل")
```

---

#### `_start_server(max_wait)`

**الوصف:** تشغيل سيرفر Ollama كعملية خلفية (subprocess) والانتظار حتى يكون جاهزاً.

| Parameter | النوع | الافتراضي | الوصف |
|-----------|-------|-----------|-------|
| `max_wait` | `int` | `10` | أقصى عدد ثواني للانتظار |

**Return:** `bool`

---

#### `stop_server()`

**الوصف:** إيقاف سيرفر Ollama إذا كان قد بدأ بواسطة هذه الواجهة. يُستدعى تلقائياً عند حذف الكائن (`__del__`).

```python
llm.stop_server()
```

---

## 🚀 أمثلة متكاملة

### مثال 1: تبديل المزودين بسهولة
---
```python
# جميع الواجهات تتشارك نفس الـ API — التبديل لا يتطلب تغيير باقي الكود

def ask_llm(llm, question: str) -> str:
    return llm.generate(question, max_tokens=500, temperature=0.5)

# اختر أي واجهة
from llm    import OpenAIInterface
from llm import AnthropicInterface
from llm    import GeminiInterface
from llm    import OllamaInterface

llm_openai    = OpenAIInterface(model_name="gpt-4",                     api_key="sk-...")
llm_claude    = AnthropicInterface(model_name="claude-3-5-sonnet-20241022", api_key="sk-ant-...")
llm_gemini    = GeminiInterface(model_name="gemini-2.0-flash-exp",       api_key="AIza...")
llm_local     = OllamaInterface(model_name="llama3")

question = "ما هو الفرق بين RAG و Fine-tuning؟"

for llm in [llm_openai, llm_claude, llm_gemini, llm_local]:
    print(f"\n[{llm.__class__.__name__}]")
    print(ask_llm(llm, question))
```

---

### مثال 2: توليد async متوازٍ من عدة نماذج

```python
import asyncio
from llm    import OpenAIInterface
from llm import AnthropicInterface
from llm   import MistralInterface

async def compare_models(question: str):
    llms = [
        OpenAIInterface(model_name="gpt-4", api_key="sk-..."),
        AnthropicInterface(model_name="claude-3-5-sonnet-20241022", api_key="sk-ant-..."),
        MistralInterface(model_name="mistral-large-latest", api_key="..."),
    ]

    # توليد متوازٍ من الثلاثة في نفس الوقت
    tasks = [llm.generate_async(question) for llm in llms]
    results = await asyncio.gather(*tasks)

    for llm, result in zip(llms, results):
        print(f"\n{'='*40}")
        print(f"[{llm.__class__.__name__} / {llm.model_name}]")
        print(result)

asyncio.run(compare_models("ما هو أفضل نموذج لغوي حالياً؟"))
```

---

### مثال 3: بث مع معالجة الأحداث

```python
import asyncio
from llm import OpenAIInterface

async def stream_with_callback(prompt: str, on_token=None):
    llm = OpenAIInterface(model_name="gpt-4", api_key="sk-...")
    full_response = []

    async for token in llm.astream(prompt):
        full_response.append(token)
        if on_token:
            on_token(token)

    return "".join(full_response)

def print_token(token):
    print(token, end="", flush=True)

response = asyncio.run(
    stream_with_callback("اكتب نبذة عن تاريخ الذكاء الاصطناعي", on_token=print_token)
)
print(f"\n\n[طول الاستجابة: {len(response)} حرف]")
```

---

### مثال 4: التحقق من الاتصال والتشخيص

```python
from llm    import OpenAIInterface
from llm import AnthropicInterface
from llm    import OllamaInterface

interfaces = [
    OpenAIInterface(model_name="gpt-4",     api_key="sk-..."),
    AnthropicInterface(model_name="claude-3-5-sonnet-20241022", api_key="sk-ant-..."),
    OllamaInterface(model_name="llama3"),
]

for llm in interfaces:
    result = llm.validate_connection()
    status = "✓" if result["success"] else "✗"
    print(f"{status} {llm.__class__.__name__}: {result['reason']}")
    if result["success"]:
        print(f"  الاستجابة: {result['response'][:50]}...")
```

---

### مثال 5: استخدام الحماية من الهلوسة

```python
from llm import OpenAIInterface

llm = OpenAIInterface(model_name="gpt-4", api_key="sk-...")

# للمجال الطبي مع أعلى درجات الحماية
medical_llm = llm.with_hallucination_guard(
    strict_mode=True,
    threshold=0.9,
    require_sources=True
)

result = medical_llm.generate("ما هي الجرعة الآمنة من الأسبرين للبالغين؟")
print(result["response"])

# حماية عامة مع إعادة المحاولة
protected = llm.with_hallucination_guard(
    auto_retry=True,
    max_retries=3,
    verbose=True
)
result = protected.generate("من اخترع الهاتف؟")
```

---

### مثال 6: HuggingFace مع نموذج عربي

```python
from llm import HuggingFaceInterface

# نموذج ArabERT للإكمال
llm = HuggingFaceInterface("aubmindlab/bert-base-arabertv2")
info = llm.get_model_info()
print(f"نوع النموذج: {info['model_type']}")  # masked_lm

# إكمال النص
response = llm.generate("الذكاء الاصطناعي [MASK] العلوم التقنية")
print(response)

# نموذج توليد نص
llm_gen = HuggingFaceInterface("gpt2")
response = llm_gen.generate(
    "Artificial intelligence is",
    max_tokens=100,
    temperature=0.8,
    top_p=0.95,
    repetition_penalty=1.2
)
print(response)
```

---

## ⚠️ متطلبات التثبيت

```bash
# OpenAI
pip install openai

# Anthropic (Claude)
pip install anthropic

# Google Gemini
pip install google-genai

# Mistral
pip install mistralai

# HuggingFace
pip install transformers torch

# Ollama (async)
pip install aiohttp
# تثبيت Ollama نفسه: https://ollama.ai
```

---

## 🔑 ملخص مقارنة الواجهات

| الواجهة | المزود | Sync | Async | Streaming | محلي | API Key |
|---------|--------|------|-------|-----------|------|---------|
| `OpenAIInterface` | OpenAI | ✅ | ✅ | ✅ أصلي | ❌ | ✅ مطلوب |
| `AnthropicInterface` | Anthropic | ✅ | ✅ | ✅ أصلي | ❌ | ✅ مطلوب |
| `GeminiInterface` | Google | ✅ | ✅ | ⚡ fallback | ❌ | ✅ مطلوب |
| `MistralInterface` | Mistral AI | ✅ | ✅ | ✅ أصلي | ❌ | ✅ مطلوب |
| `HuggingFaceInterface` | HuggingFace | ✅ | ⚡ thread | ⚡ fallback | ✅ | ❌ اختياري |
| `OllamaInterface` | Ollama | ✅ | ✅ | ✅ أصلي | ✅ | ❌ غير مطلوب |

> ✅ أصلي = بث حقيقي token بـ token من المزود  
> ⚡ fallback = يُولّد الرد كاملاً ثم يُبثّ كلمةً كلمة
