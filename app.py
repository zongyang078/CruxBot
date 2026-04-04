from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.rag_pipeline import answer

app = FastAPI(title="CruxBot", description="Rock climbing RAG assistant")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)


class Source(BaseModel):
    url: str
    text_snippet: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[Source]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=QueryResponse)
def ask(req: QueryRequest):
    try:
        result = answer(req.query, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result
