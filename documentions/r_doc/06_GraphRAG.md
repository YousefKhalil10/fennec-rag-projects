# 🕸️ GraphRAG — نظام RAG بالمخطط المعرفي

## نظرة عامة

`GraphRAG` يُضيف طبقة **مخطط معرفي (Knowledge Graph)** فوق قاعدة البيانات المتجهة. بدلاً من تخزين قطع نص مجردة، يُنشئ **عقداً (Nodes)** للكيانات و**حوافاً (Edges)** للعلاقات بينها. عند الاسترجاع، يوسّع السياق عبر **اجتياز الرسم البياني (Graph Traversal)** للوصول للمعلومات المرتبطة.

يتضمن أيضاً:
- `KnowledgeGraph` — إدارة العقد والحوافّ والاجتياز
- `GraphNode` / `GraphEdge` — وحدات البيانات الأساسية
- `ConfigGraphRAG` — إعدادات كاملة للنظام

---

## التثبيت والاستيراد

```python
from rag.graph_rag import GraphRAG
from rag.graph_rag import ConfigGraphRAG
from rag.graph_rag import KnowledgeGraph
from rag.graph_rag import GraphNode
from rag.graph_rag import GraphEdge
```

---

## المكونات الرئيسية

| المكوّن | النوع | الدور |
|---|---|---|
| `GraphRAG` | class | المنسّق الرئيسي — يجمع vector DB + graph + LLM |
| `KnowledgeGraph` | class | إدارة العقد والحوافّ والاجتياز |
| `GraphNode` | dataclass | تمثيل كيان في المخطط |
| `GraphEdge` | dataclass | تمثيل علاقة بين كيانين |
| `ConfigGraphRAG` | dataclass | إعدادات النظام الكاملة |

---

## `ConfigGraphRAG`

```python
@dataclass
class ConfigGraphRAG:
    # الاسترجاع
    k: int = 5                    # عدد نتائج الاسترجاع
    context_depth: int = 2        # عمق اجتياز الرسم البياني لتوسيع السياق
    max_depth: int = 2            # أقصى عمق عند استدعاء get_neighbors

    # الكاش
    l1_size: int = 50             # حجم الكاش L1
    l2_size: int = 50             # حجم الكاش L2
    l3_size: int = 50             # حجم الكاش L3
    cache_ttl: int = 300          # صلاحية الكاش بالثواني

    # التضمين (Embedding)
    embedder_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: Optional[int] = None   # يُكتشف تلقائياً إن لم يُحدَّد
    batch_size: int = 32
    normalize_embeddings: bool = True

    # FAISS
    use_gpu: bool = False
    faiss_nlist: Optional[int] = None    # عدد مجموعات IVF (يُحسب تلقائياً)
    faiss_nprobe: int = 10
    rebuild_threshold: int = 100         # إعادة بناء الفهرس بعد N إضافة

    # البحث
    enable_hybrid_search: bool = False
    hybrid_alpha: float = 0.5            # 0=keyword, 1=semantic

    # الأداء
    max_cache_embeddings: int = 1000
    parallel_processing: bool = True

    # اللوغ
    log_level: str = "INFO"
```

**مثال:**
```python
config = ConfigGraphRAG(
    k=5,
    context_depth=2,
    max_depth=3,
    embedder_name="paraphrase-multilingual-MiniLM-L12-v2",
    use_gpu=False,
    log_level="WARNING",
)

# أو من متغيرات البيئة
config = ConfigGraphRAG.from_env()
```

**`from_env()`** — يقرأ:
`GRAPHRAG_K`, `GRAPHRAG_CONTEXT_DEPTH`, `GRAPHRAG_MAX_DEPTH`, `GRAPHRAG_EMBEDDER`, `GRAPHRAG_BATCH_SIZE`, `GRAPHRAG_USE_GPU`, `GRAPHRAG_LOG_LEVEL`, `GRAPHRAG_HYBRID_SEARCH`

---

## `GraphNode`

يمثّل كياناً في المخطط المعرفي.

```python
@dataclass
class GraphNode:
    id: str                              # معرّف فريد (مطلوب)
    content: str                         # المحتوى النصي (مطلوب)
    node_type: str                       # نوع الكيان (مطلوب) مثل: 'entity', 'concept'
    metadata: Dict[str, Any] = {}        # بيانات وصفية حرة
    embedding: Optional[List[float]] = None   # متجه التضمين
```

### الخصائص والطرق

| الطريقة / الخاصية | الوصف |
|---|---|
| `has_embedding` | `True` إذا كان التضمين موجوداً وغير فارغ |
| `get_content_hash()` | MD5 للمحتوى — للكشف عن التغييرات |
| `to_dict(include_embedding=False)` | تحويل لقاموس |
| `from_dict(data)` | إنشاء من قاموس (classmethod) |
| `update_metadata(key, value)` | تحديث حقل واحد في الـ metadata |
| `merge_metadata(metadata)` | دمج قاموس metadata كامل |

```python
node = GraphNode(
    id="elon_musk",
    content="إيلون ماسك",
    node_type="person",
    metadata={"nationality": "US"},
)

print(node.has_embedding)        # False
print(node.get_content_hash())   # MD5 hash
node.update_metadata("age", 53)
d = node.to_dict()               # {'id': 'elon_musk', 'content': ..., ...}
node2 = GraphNode.from_dict(d)   # إعادة البناء من القاموس
```

---

## `GraphEdge`

يمثّل علاقة موجَّهة بين كيانين في المخطط.

```python
# (Paris) ---[capital_of]---> (France)

@dataclass
class GraphEdge:
    source: str                          # معرّف عقدة المصدر (مطلوب)
    target: str                          # معرّف عقدة الهدف (مطلوب)
    relation: str                        # نوع العلاقة (مطلوب)
    weight: float = 1.0                  # وزن الحافة (يجب أن يكون ≥ 0)
    metadata: Dict[str, Any] = {}
    bidirectional: bool = False          # True = علاقة في الاتجاهين
```

**القيود:** لا يُسمح بالحلقات الذاتية (`source == target`). الوزن لا يمكن أن يكون سالباً.

### الخصائص والطرق

| الطريقة / الخاصية | الوصف |
|---|---|
| `edge_id` | معرّف فريد: `"source-relation->target"` |
| `reverse()` | إنشاء حافة عكسية (`inverse_relation`) |
| `update_weight(new_weight)` | تحديث الوزن مع التحقق |
| `to_dict()` | تحويل لقاموس |
| `from_dict(data)` | إنشاء من قاموس (classmethod) |

```python
edge = GraphEdge(
    source="elon_musk",
    target="tesla",
    relation="founded",
    weight=1.0,
    bidirectional=False,
)

print(edge.edge_id)     # "elon_musk-founded->tesla"
rev = edge.reverse()    # GraphEdge(tesla, elon_musk, inverse_founded)
edge.update_weight(0.9)
```

---

## `KnowledgeGraph`

إدارة العقد والحوافّ مع دعم الاجتياز والتحليل.

```python
from rag.graph_rag import KnowledgeGraph

graph = KnowledgeGraph(config=config)   # config اختياري
```

### إدارة العقد والحوافّ

#### `add_node`
```python
add_node(node: GraphNode) -> bool
# True إذا أُضيفت عقدة جديدة، False إذا تم تحديث موجودة
```

#### `add_edge`
```python
add_edge(edge: GraphEdge) -> bool
# يتحقق أن المصدر والهدف موجودان قبل الإضافة
# يُحدِّث الوزن إن كانت الحافة موجودة مسبقاً
```

#### `remove_node`
```python
remove_node(node_id: str) -> bool
# يحذف العقدة وجميع حوافّها المتصلة
```

#### `get_node` / `get_edge`
```python
get_node(node_id: str) -> Optional[GraphNode]
get_edge(source: str, target: str, relation: str) -> Optional[GraphEdge]
```

---

### الاجتياز والمسارات

#### `get_neighbors`
```python
get_neighbors(
    node_id: str,
    max_depth: int = None,          # افتراضي: config.max_depth
    include_incoming: bool = True,  # تتبع الحوافّ الواردة أيضاً
) -> Set[str]
```
يُرجع معرّفات العقد المجاورة (باستثناء العقدة نفسها) باستخدام BFS.

#### `find_path`
```python
find_path(start: str, end: str, max_length: Optional[int] = None) -> Optional[List[str]]
# أقصر مسار بين عقدتين — BFS
# يُرجع None إن لم يوجد مسار
```

#### `find_all_paths`
```python
find_all_paths(start: str, end: str, max_length: int = 5) -> List[List[str]]
# جميع المسارات حتى max_length — DFS
```

#### `get_subgraph`
```python
get_subgraph(node_ids: Set[str]) -> KnowledgeGraph
# استخراج مخطط فرعي يحتوي على العقد المحدَّدة وحوافّها
```

---

### التحليل والإحصاء

#### `get_node_degree`
```python
get_node_degree(node_id: str) -> Dict[str, int]
# يُرجع: {'in_degree': N, 'out_degree': N, 'total_degree': N}
# O(1) — يستخدم عداد داخلي مُحدَّث تدريجياً
```

#### `get_connected_components`
```python
get_connected_components() -> List[Set[str]]
# قائمة المكوّنات المترابطة (كل مكوّن = مجموعة معرّفات)
```

#### `get_stats`
```python
get_stats() -> Dict[str, Any]
# يُرجع:
{
    "num_nodes": 10,
    "num_edges": 15,
    "avg_degree": 3.0,
    "max_degree": 6,
    "min_degree": 1,
    "num_components": 2,
    "density": 0.17,
}
```

#### `validate_integrity`
```python
validate_integrity() -> Dict[str, List[str]]
# يُرجع:
{
    "orphan_edges": [...],    # حوافّ تشير لعقد غير موجودة
    "duplicate_edges": [...], # حوافّ مكرّرة
    "self_loops": [...],      # حلقات ذاتية
}
```

**مثال كامل:**
```python

graph = KnowledgeGraph(config=ConfigGraphRAG(max_depth=3))
# إضافة عقد
graph.add_node(GraphNode("paris",  "باريس",  "city"))
graph.add_node(GraphNode("france", "فرنسا",  "country"))
graph.add_node(GraphNode("europe", "أوروبا", "continent"))

# إضافة حوافّ
graph.add_edge(GraphEdge("paris",  "france", "capital_of"))
graph.add_edge(GraphEdge("france", "europe", "part_of"))

# اجتياز
neighbors = graph.get_neighbors("paris", max_depth=2)
# {"france", "europe"}

path = graph.find_path("paris", "europe")
# ["paris", "france", "europe"]

degree = graph.get_node_degree("france")
# {"in_degree": 1, "out_degree": 1, "total_degree": 2}

stats = graph.get_stats()
issues = graph.validate_integrity()

# مخطط فرعي
sub = graph.get_subgraph({"paris", "france"})
```

---

## `GraphRAG`

### `__init__`

```python
GraphRAG(
    vector_db,                          # قاعدة البيانات المتجهة (مطلوبة)
    llm: Optional[Any] = None,          # نموذج اللغة (اختياري)
    config: Optional[ConfigGraphRAG] = None,
)
```

| المعامل | الوصف |
|---|---|
| `vector_db` | أي كائن يملك `add`, `search`, `save`, `load` |
| `llm` | أي كائن يملك `.generate(prompt)` — إن غاب يُرجع السياق خاماً |
| `config` | إعدادات النظام — يُنشئ `ConfigGraphRAG()` افتراضياً |

```python
print(repr(graph_rag))
# GraphRAG(nodes=9, edges=5, llm=MistralInterface)
```

---

### إضافة البيانات

#### `add_document_with_relations`

```python
add_document_with_relations(
    content:   str,
    entities:  List[Dict],
    relations: List[Dict],
    doc_id:    str,
    metadata:  Optional[Dict] = None,
) -> Dict[str, Any]
```

**تنسيق الكيانات** — أي من هذه الحقول يُقبل كنص للكيان (بالأولوية):
```python
{"id": "elon", "text": "إيلون ماسك",  "type": "person"}   # text
{"id": "elon", "name": "إيلون ماسك",  "type": "person"}   # name
{"id": "elon", "content": "إيلون ماسك", "type": "person"} # content
{"id": "elon", "type": "person"}                           # يستخدم id كنص
```

**تنسيق العلاقات:**
```python
{
    "source": "elon_musk",
    "target": "tesla",
    "type": "founded",          # نوع العلاقة (افتراضي: "related")
    "weight": 1.0,              # اختياري (افتراضي: 1.0)
    "bidirectional": False,     # اختياري (افتراضي: False)
}
```

**Return:**
```python
{"nodes_added": 6, "edges_added": 5, "chunks_created": 6}
```

> كل الكيانات تُضاف لقاعدة البيانات في **استدعاء batch واحد** للأداء.

---

### الاستعلام

#### `query`

```python
query(
    query: str,
    k: int = None,                  # عدد النتائج (افتراضي: config.k)
    language: str = "ar",           # 'ar' أو 'en'
    include_sources: bool = False,  # إضافة قائمة المصادر للإجابة
    **llm_kwargs,                   # معاملات إضافية لنموذج اللغة
) -> str
```

الواجهة الرئيسية: استرجاع → بناء prompt → توليد إجابة.

```python
answer = graph_rag.query("من أسّس تيسلا؟", k=5, language="ar")
answer = graph_rag.query("Who founded Tesla?", language="en", include_sources=True)
```

#### `generate`

```python
generate(query: str, k: int = None, **kwargs) -> str
```

اسم بديل لـ `query()` للتوافق مع باقي أنواع RAG في الـ federation.

---

### Return

#### `retrieve_with_context`

```python
retrieve_with_context(
    query: str,
    k: int = None,
    context_depth: int = None,      # عمق توسيع المخطط (افتراضي: config.context_depth)
    min_similarity: float = 0.0,
    combine_scores: bool = True,    # دمج درجات vector + graph
) -> List[Dict[str, Any]]
```

**Return:**
```python
[{
    "id":             "elon_musk",
    "content":        "إيلون ماسك",
    "type":           "person",
    "score":          0.92,
    "metadata":       {"doc_id": "tech_doc", ...},
    "related_chunks": [{"text": "...", "metadata": {...}}],
    "neighbors": [
        {"id": "tesla", "content": "شركة تيسلا", "type": "company"},
        {"id": "spacex", "content": "سبيس إكس",  "type": "company"},
    ],
}]
```

#### `semantic_search`

```python
semantic_search(
    query: str,
    top_k: int = 5,
    include_graph_info: bool = True,
) -> List[Dict[str, Any]]
```

بحث دلالي نقي بدون توسيع مخطط. يُضيف `graph_node` لكل نتيجة إن كانت `include_graph_info=True`:
```python
{
    "text":  "نص القطعة",
    "score": 0.88,
    "metadata": {...},
    "graph_node": {           # إن كانت include_graph_info=True
        "id":              "elon_musk",
        "type":            "person",
        "neighbors_count": 3,
    },
}
```

---

### سياق العقد

#### `get_node_context`

```python
get_node_context(
    node_id: str,
    max_depth: int = 2,
    include_chunks: bool = True,
) -> Dict[str, Any]
```

**Return:**
```python
{
    "node": {"id": "elon_musk", "content": "...", "type": "person", "metadata": {...}},
    "neighbors_by_depth": {
        1: [{"id": "tesla",  "content": "شركة تيسلا", "type": "company"}],
        2: [{"id": "ev",     "content": "السيارات الكهربائية", "type": "product"}],
    },
    "related_chunks": [{"text": "...", "metadata": {...}}],  # إن include_chunks=True
}
```

---

### الإحصائيات والحفظ

#### `get_statistics`

```python
get_statistics() -> Dict[str, Any]
# يُرجع:
{
    "graph": {
        "num_nodes": 9, "num_edges": 7,
        "avg_degree": 1.5, "num_components": 1, "density": 0.09,
    },
    "vector_db": {...},
    "mappings": {
        "chunks_to_nodes": 9,
        "nodes_with_chunks": 9,
    },
}
```

#### `save` / `load`

```python
save(path: str) -> None
load(path: str) -> None
```

يحفظ: قاعدة البيانات المتجهة + المخطط (`graph.json`) + التعيينات (`mappings.json`) + محتويات المستندات.

> بعد `load()` يُحدَّث `self.embedder` تلقائياً من قاعدة البيانات الجديدة.

---

### Context Manager

```python
async with GraphRAG(vector_db=vdb, llm=llm) as gr:
    gr.add_document_with_relations(...)
    answer = await gr.aquery("سؤال؟")
```

---

### الواجهة غير المتزامنة

| الدالة | الوصف |
|---|---|
| `await aquery(query, k=None, **kwargs)` | نسخة async من `query()` |
| `await agenerate(query, k=None, **kwargs)` | نسخة async من `generate()` |
| `await aretrieve(query, top_k=None, k=None, **kwargs)` | نسخة async من `retrieve_with_context()` — تقبل `top_k` للتوافق مع federat |

---

### Dunder Methods

| | |
|---|---|
| `repr(graph_rag)` | `GraphRAG(nodes=9, edges=7, llm=MistralInterface)` |

---

## مثال عملي كامل

```python
import asyncio
from rag.graph_rag import GraphRAG
from rag.graph_rag import ConfigGraphRAG
from rag.graph_rag import KnowledgeGraph
from rag.graph_rag import GraphNode
from rag.graph_rag import GraphEdge
from vector_database import FAISSVectorDatabase
from embeddings import MistralEmbedder
from llm import MistralInterface

# --- 1. إعداد المكونات ---
embedder  = MistralEmbedder(api_key="...")
vector_db = FAISSVectorDatabase(embedder=embedder)
llm       = MistralInterface(api_key="...")

config = ConfigGraphRAG(
    k=5,
    context_depth=2,
    max_depth=3,
    log_level="WARNING",
)

graph_rag = GraphRAG(vector_db=vector_db, llm=llm, config=config)
print(repr(graph_rag))
# GraphRAG(nodes=0, edges=0, llm=MistralInterface)

# --- 2. إضافة مستند ---
results = graph_rag.add_document_with_relations(
    content="""
        أسّس إيلون ماسك شركة تيسلا عام 2003.
        تيسلا متخصصة في السيارات الكهربائية والطاقة الشمسية.
    """,
    entities=[
        {"id": "elon_musk", "text": "إيلون ماسك",          "type": "person"},
        {"id": "tesla",     "text": "شركة تيسلا",           "type": "company"},
        {"id": "ev",        "text": "السيارات الكهربائية",  "type": "product"},
        {"id": "solar",     "text": "الطاقة الشمسية",       "type": "energy"},
    ],
    relations=[
        {"source": "elon_musk", "target": "tesla", "type": "founded",      "weight": 1.0},
        {"source": "tesla",     "target": "ev",    "type": "produces",     "weight": 1.0},
        {"source": "tesla",     "target": "solar", "type": "partners_with","weight": 0.8},
    ],
    doc_id="tesla_doc",
    metadata={"year": 2024, "source": "wikipedia"},
)
print(f"تمت الإضافة: {results}")
# {'nodes_added': 4, 'edges_added': 3, 'chunks_created': 4}

# --- 3. الاستعلام ---
answer = graph_rag.query("ما هي منتجات تيسلا؟", k=3, language="ar")
print(answer)

answer_en = graph_rag.query("What does Tesla produce?", language="en", include_sources=True)
print(answer_en)

# generate() — نفس query() للتوافق مع federat
answer2 = graph_rag.generate("من أسّس تيسلا؟", k=5)

# --- 4. الاسترجاع المباشر ---
results = graph_rag.retrieve_with_context(
    query="شركات الطاقة",
    k=3,
    context_depth=2,
    min_similarity=0.3,
)
for r in results:
    print(f"[{r['type']}] {r['content']} | score={r['score']:.2f}")
    print(f"  جيران: {[n['content'] for n in r['neighbors']]}")

# --- 5. البحث الدلالي ---
sem = graph_rag.semantic_search("سيارات كهربائية", top_k=3)
for r in sem:
    print(f"{r['text']} | graph_node={r.get('graph_node', {}).get('id')}")

# --- 6. سياق عقدة ---
ctx = graph_rag.get_node_context("tesla", max_depth=2)
print(ctx["node"]["content"])
for depth, neighbors in ctx["neighbors_by_depth"].items():
    print(f"  عمق {depth}: {[n['content'] for n in neighbors]}")

# --- 7. KnowledgeGraph مباشرة ---
graph = graph_rag.graph

# إضافة يدوية
graph.add_node(GraphNode("spacex", "سبيس إكس", "company"))
graph.add_edge(GraphEdge("elon_musk", "spacex", "founded"))

# اجتياز
neighbors = graph.get_neighbors("elon_musk", max_depth=1)
print(f"جيران ماسك: {neighbors}")   # {"tesla", "spacex"}

path = graph.find_path("elon_musk", "ev")
print(f"المسار: {path}")            # ["elon_musk", "tesla", "ev"]

all_paths = graph.find_all_paths("elon_musk", "ev", max_length=3)

degree = graph.get_node_degree("tesla")
print(degree)   # {"in_degree": 1, "out_degree": 2, "total_degree": 3}

sub = graph.get_subgraph({"elon_musk", "tesla", "ev"})
print(repr(sub))   # KnowledgeGraph(nodes=3, edges=2)

components = graph.get_connected_components()
stats  = graph.get_stats()
issues = graph.validate_integrity()

# --- 8. الإحصائيات ---
sys_stats = graph_rag.get_statistics()
print(f"العقد: {sys_stats['graph']['num_nodes']}")
print(f"الحوافّ: {sys_stats['graph']['num_edges']}")

# --- 9. الحفظ والتحميل ---
graph_rag.save("./graph_data")

new_rag = GraphRAG(vector_db=FAISSVectorDatabase(embedder=embedder), llm=llm)
new_rag.load("./graph_data")   # self.embedder يُحدَّث تلقائياً

# --- 10. الاستخدام غير المتزامن ---
async def run():
    # Context manager
    async with GraphRAG(vector_db=vector_db, llm=llm) as gr:
        gr.add_document_with_relations(
            content="محتوى المستند",
            entities=[{"id": "x", "text": "كيان", "type": "entity"}],
            relations=[],
            doc_id="d1",
        )
        answer = await gr.aquery("سؤال؟", k=3, language="ar")
        print(answer)

    # aretrieve — يقبل top_k للتوافق مع federat
    results = await graph_rag.aretrieve("سؤال؟", top_k=5)
    results = await graph_rag.aretrieve("سؤال؟", k=5)    # كلاهما يعمل

    # agenerate — alias لـ aquery
    answer = await graph_rag.agenerate("سؤال؟", k=3)

asyncio.run(run())

```
