"""
PayPilot Global — Copilot API Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CopilotQueryRequest, CopilotQueryResponse
from app.api.auth import get_employer_id
from app.services.copilot import answer_copilot_question

router = APIRouter(prefix="/copilot", tags=["Copilot"])


@router.post("/query", response_model=CopilotQueryResponse)
def copilot_query(
    req: CopilotQueryRequest,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Ask the deterministic AI Payroll Copilot a question."""
    result = answer_copilot_question(db, employer_id, req.question)
    return CopilotQueryResponse(**result)
