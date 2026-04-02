<div align="center">

# 🦊 Fennec RAG Projects

**مجموعة مشاريع RAG مبنية على مكتبة `fennec-rag` مع Gemini AI**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_DB-FF6B35?style=flat-square)](https://faiss.ai)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-00C4B4?style=flat-square)](https://pinecone.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 📖 نظرة عامة

هذا الـ repository يضم **6 مشاريع تطبيقية** تُغطّي جوانب مختلفة من بناء أنظمة **Retrieval-Augmented Generation (RAG)** باستخدام Python، تتدرّج من الإعداد الأساسي إلى ميزات متقدمة مثل المراقبة، الذاكرة التحادثية، والتخزين المؤقت.

```
RAG Core ──► Monitoring ──► Observability ──► Memory ──► Cache ──► Plugin System ──► Evaluator
```

---

## 🗂️ المشاريع

### 1. 📡 `rag_monitor` — RAG مع مراقبة الأداء

نظام RAG يُضيف طبقة **Monitoring** كاملة تقيس كل خطوة من خطوات الاسترجاع والتوليد.

**الميزات:**
- قياس زمن الاستجابة (Latency) لكل مرحلة
- تتبّع عدد القطع المُسترجَعة ودرجات التشابه
- مقاييس `Counter`, `Timer`, `Gauge`, `Histogram`
- `HTMLStringLoader` لتحميل المستندات بصيغة HTML

```python
monitored_rag_query(query)
# ➜ يُنفّذ RAG ويسجّل المقاييس في MetricsCollector
```

---

### 2. 🔭 `rag_observability` — RAG مع لوحة مراقبة حية

نظام RAG متكامل مع **Observability** متقدمة وبث مباشر (Streaming) واكتشاف الشذوذات.

**الميزات:**
- `RAGObservabilityWrapper` يجمع RAG + Metrics + Chat Logger
- اكتشاف الشذوذات في الوقت الفعلي (Anomaly Detection)
- نظام تنبيهات (Alerts) قابل للتهيئة
- دعم `ConversationLogger` لتسجيل سجل المحادثة
- دعم Jupyter / بيئات تفاعلية

```python
wrapper = RAGObservabilityWrapper(rag, observability, logger)
wrapper.query("سؤالك هنا")
```

---

### 3. 🧠 `rag_memory` — RAG مع ذاكرة تحادثية

نظام RAG تحادثي يحتفظ بسياق المحادثة عبر الأسئلة المتعددة باستخدام **Pinecone**.

**الميزات:**
- دعم **3 أنواع من الذاكرة**: `BufferMemory`, `SummaryMemory`, `WindowMemory`
- قاعدة بيانات متجهية `PineconeVectorDatabase`
- استرجاع يأخذ سياق المحادثة السابقة في الاعتبار

```python
# اختر نوع الذاكرة
memory = BufferMemory()        # كل سجل المحادثة
memory = SummaryMemory(llm)    # ملخص ذكي
memory = WindowMemory(k=5)     # آخر 5 رسائل
```

| النوع | الوصف | الأنسب لـ |
|-------|-------|-----------|
| `BufferMemory` | يحتفظ بكل التاريخ | محادثات قصيرة |
| `SummaryMemory` | يُلخّص التاريخ بالـ LLM | محادثات طويلة |
| `WindowMemory(k)` | آخر k رسالة فقط | نوافذ ثابتة الحجم |

---

### 4. ⚡ `rag-cache` — RAG مع تخزين مؤقت متعدد المستويات

نظام RAG مُدعَّم بـ **MultiLevelCache** يتجنّب الطلبات المكررة إلى نموذج اللغة.

**الميزات:**
- كاش L1 (سريع) + L2 (أكبر)
- استراتيجية `LRU` للإزاحة
- TTL قابل للضبط
- إحصائيات Hit Rate في الوقت الفعلي

```python
cache_config = CacheConfig(l1_max_items=100, l2_max_items=500, default_ttl=600)
cache = MultiLevelCache(strategy=CacheStrategy.LRU, config=cache_config)

answer, from_cache = cached_rag_query("سؤالك")
# ⚡ Cache (0.2ms)  أو  🔄 RAG (1200ms)
```

---

### 5. 🔌 `rag_plugin` — RAG مع نظام إضافات

نظام **Plugin Pipeline** قابل للتوسعة يُمرّر الاستعلام عبر سلسلة إضافات متسلسلة.

**الميزات:**
- نمط معماري **Plugin Pipeline**
- `HTMLStringLoader` لتحميل المستندات
- 3 إضافات جاهزة: `QueryCleaner` → `RAGQuery` → `AnswerValidator`

```
الاستعلام الخام
     │
     ▼
QueryCleaner   ① تنظيف النص وتوحيد علامات الترقيم
     │
     ▼
RAGQuery       ② استرجاع المستندات + توليد الإجابة
     │
     ▼
AnswerValidator ③ التحقق من جودة الإجابة
     │
     ▼
الإجابة النهائية
```

---

### 6. 📊 `rag_evaluater` — RAG مع تقييم الجودة

نظام RAG كامل مع **تقييم آلي** لجودة الإجابات وتوليد لوحة تحكم تفاعلية.

**الميزات:**
- `RAGEvaluator` يقيّم الإجابات تلقائيًا
- `generate_dashboard` لتوليد تقرير HTML تفاعلي
- مقاييس: الدقة، الاسترجاع، F1-Score، التماسك

```python
evaluator = RAGEvaluator(llm=llm)
results = evaluator.evaluate(questions, answers, contexts)
generate_dashboard(results, output="dashboard.html")
```

---

## 🏗️ البنية العامة للمشاريع

```
fennec-rag-projects/
├── rag_monitor/
│   ├── main.py
│   ├── company_overview.txt
│   └── README.md
├── rag_observability/
│   ├── main.py
│   ├── company_overview.txt
│   └── README.md
├── rag_memory/
│   ├── main.py
│   ├── company_overview.txt
│   └── README.md
├── rag-cache/
│   ├── main.py
│   ├── company_overview.txt
│   └── README.md
├── rag_plugin/
│   ├── main.py
│   ├── company_overview.txt
│   └── README.md
├── rag_evaluater/
│   ├── main.py
│   ├── company_overview.txt
│   └── README.md
└── README.md  ← أنت هنا
```

---

## 🚀 البدء السريع

### المتطلبات

```bash
pip install fennec-rag faiss-cpu google-generativeai pinecone-client
```

### الإعداد

```python
# ضع مفتاح Gemini API
api = "YOUR_GEMINI_API_KEY"
```

### تشغيل أي مشروع

```bash
cd rag_monitor   # أو أي مشروع آخر
python main.py
```

---

## 🛠️ التقنيات المستخدمة

| التقنية | الاستخدام |
|---------|-----------|
| `fennec-rag` | المكتبة الأساسية لبناء أنظمة RAG |
| `Gemini AI` | نموذج اللغة الكبير (LLM) والتضمينات |
| `FAISS` | قاعدة البيانات المتجهية المحلية |
| `Pinecone` | قاعدة البيانات المتجهية السحابية |
| `Python 3.9+` | لغة البرمجة |

---

## 📄 الترخيص

هذا المشروع مرخّص تحت رخصة [MIT](LICENSE).

---

<div align="center">

**بُني بـ 🦊 fennec-rag **

</div>
