import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from src.schemas import QueryResponse, SourceChunk
import src.ingestion 

def _load_index():
    chroma_client = chromadb.PersistentClient(path="storage/chroma")
    collection = chroma_client.get_or_create_collection("docs")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(vector_store)

_index = None

def answer_question(question: str, top_k: int = 3) -> QueryResponse:
    global _index
    if _index is None:
        _index = _load_index()

    engine = _index.as_query_engine(similarity_top_k=top_k)
    result = engine.query(question)

    sources = [
        SourceChunk(
            text=node.node.get_content()[:300],
            source_file=node.node.metadata.get("file_name", "desconhecido"),
            score=node.score or 0.0,
        )
        for node in result.source_nodes
    ]
    return QueryResponse(answer=str(result), sources=sources)