from fastapi import FastAPI, HTTPException
from src.schemas import QueryRequest, QueryResponse
from src.query_engine import answer_question
from src.ingestion import run_ingestion

app = FastAPI(title="junior-rag-fastapi")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        return answer_question(request.question, request.top_k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/ingest")
def ingest():
    try:
        run_ingestion()
        return {"status": "ingestão concluída"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))