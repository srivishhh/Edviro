from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_service import FacilityRagService

router = APIRouter()
rag_service = FacilityRagService()


class RagQueryRequest(BaseModel):
    query: str


@router.post("/rag/query")
def query_facility_rag(payload: RagQueryRequest):
    return rag_service.answer_query(payload.query)


@router.get("/rag/documents")
def list_rag_documents():
    return rag_service.documents
