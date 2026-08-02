import chromadb
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from src.config import settings

Settings.llm = OpenAI(model=settings.llm_model, api_key=settings.openai_api_key)
Settings.embed_model = OpenAIEmbedding(model=settings.embedding_model, api_key=settings.openai_api_key)

def run_ingestion():
    docs = SimpleDirectoryReader("data/documents").load_data()
    print(f"{len(docs)} documentos carregados")

    chroma_client = chromadb.PersistentClient(path="storage/chroma")
    collection = chroma_client.get_or_create_collection("docs")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
    print("índice criado/atualizado com sucesso")
    return index

if __name__ == "__main__":
    run_ingestion()