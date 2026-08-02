from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str
    top_k: int = 3

class SourceChunk(BaseModel):
    text: str
    source_file: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = Field(default_factory=list)