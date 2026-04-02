from fennec.llm import GeminiInterface
from fennec.embeddings import GeminiEmbedder
from fennec.vector_database import PineconeVectorDatabase
from fennec.chunks import MultilanguageTextChunker
from fennec.context import ContextManager
from fennec.rag.core import RAGSystem
from fennec.document_loaders import TextLoader

embedder=GeminiEmbedder(api_key=api)
base_rag=RAGSystem(
        vector_db=PineconeVectorDatabase(embedder=embedder,api_key=api_pinecone),
        llm=GeminiInterface(api_key=api),
        chunker=MultilanguageTextChunker(),
        context_manager=ContextManager(),)

from fennec.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationEntityMemory,
)

rag = base_rag
loader=TextLoader("company_overview.txt").load()
base_rag.add_documents(loader)
def conversational_rag_query(
    query: str,
    memory,
    memory_key: str = "history",
) -> str:
    """استعلام RAG يُدمج تاريخ المحادثة في السياق"""
    # تحميل تاريخ المحادثة
    mem_vars  = memory.load_memory_variables({"input": query})
    history   = mem_vars.get(memory_key, "")
    # استرجاع من قاعدة المعرفة
    retrieved = rag.retrieve(query, top_k=2)
    context   = rag.context_manager.build(query, retrieved)
    # بناء الـ prompt مع تاريخ المحادثة
    if history:
        full_prompt = (
            f"سياق المحادثة السابقة:\n{str(history)[:400]}\n\n"
            f"معلومات مسترجعة:\n{context}\n\n"
            f"السؤال الحالي: {query}\nالإجابة:"
        )
    else:
        full_prompt = f"معلومات مسترجعة:\n{context}\n\nالسؤال: {query}\nالإجابة:"
    answer = rag.llm.generate(full_prompt)
    # حفظ التبادل في الذاكرة
    memory.save_context({"input": query}, {"output": answer})
    return answer

# ── 5a: Buffer Memory — محادثة كاملة ─────────────────────── #
print("\n  [5a] ConversationBufferMemory — محادثة كاملة")
buffer_mem = ConversationBufferMemory(
    return_messages=False, input_key="input", output_key="output", memory_key="history"
)
conversation = [
    "ما هو الـ RAG؟",
    "ما هي مزاياه على النماذج اللغوية التقليدية؟",
    "هل يُستخدم RAG في قواعد المعرفة المؤسسية؟",
]
print("\n  💬 محادثة مع RAG (Buffer Memory):")
for turn, q in enumerate(conversation, 1):
    answer = conversational_rag_query(q, buffer_mem)
    print(f"  [{turn}] 👤 {q}")
    print(f"       🤖 {answer[:80]}...")
    print()
print(f"  📝 Buffer memory: {len(buffer_mem.chat_memory)} رسائل محفوظة")
# ── 5b: Window Memory — نافذة آخر K تبادلات ──────────────── #
print("\n  [5b] ConversationBufferWindowMemory — نافذة K=2")
window_mem = ConversationBufferWindowMemory(k=2)
long_conversation = [
    "ما هو الذكاء الاصطناعي؟",
    "ما هو تعلم الآلة؟",
    "ما هي الشبكات العصبية؟",   # هذه ستُزيح الأولى
    "ما هي التضمينات؟",          # هذه ستُزيح الثانية
]
for q in long_conversation:
    conversational_rag_query(q, window_mem)
print(f"  📝 Window memory (k=2): {len(window_mem.chat_memory)} رسائل محفوظة (آخر 2)")
if window_mem.chat_memory:
    print(f"  آخر سؤال: {window_mem.chat_memory[-1].get('input', '')}")
# ── 5c: Summary Memory ────────────────────────────────────── #
print("\n  [5c] ConversationSummaryMemory — ملخص تراكمي")
summary_mem = ConversationSummaryMemory(llm=base_rag.llm,max_token_limit=300)  # لو كانت المحادثه اقل من 300 مش هيلخص  
for q in conversation:
    conversational_rag_query(q, summary_mem)
print(f"  📝 Summary memory: {len(summary_mem.chat_memory)} رسائل → ملخص من {summary_mem.max_token_limit} رمز")
# ── 5d: Entity Memory ─────────────────────────────────────── #
print("\n  [5d] ConversationEntityMemory — تتبع الكيانات")
entity_mem = ConversationEntityMemory()
entity_queries = [
    "ما هو RAG؟",
    "كيف طوّرت OpenAI نموذج GPT-4؟",
    "هل Anthropic طوّرت Claude بناءً على RAG؟",
]
for q in entity_queries:
    conversational_rag_query(q, entity_mem, memory_key="history")
entities = entity_mem.entity_store
print(f"  📝 كيانات مُتتبَّعة: {list(entities.keys())}")
