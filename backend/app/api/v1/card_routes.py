"""
PayPilot Global — Cards API Routes (Optional)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Card
from app.schemas import CardResponse, CardUpdateRequest, PaginatedResponse
from app.api.auth import get_employer_id
from app.services.flutterwave_client import flutterwave_client

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.get("", response_model=PaginatedResponse)
def list_cards(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """List cards with pagination."""
    query = db.query(Card).filter(Card.employer_id == employer_id)
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    items = query.order_by(Card.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return PaginatedResponse(
        items=[CardResponse.model_validate(c) for c in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )


@router.post("")
async def create_card(
    body: dict,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Create a new card using Flutterwave."""
    import random
    
    card = Card(
        employer_id=employer_id,
        employee_id=body.get("employee_id"),
        bmoni_card_id=f"bmoni_card_{random.randint(1000, 9999)}",  # Deprecated
        smart_wallet_id=f"sw_{random.randint(1000, 9999)}",
        card_name=body.get("card_name", "New Card"),
        card_color=body.get("card_color", "#1D4ED8"),
        currency=body.get("currency", "USD"),
        card_type=body.get("card_type", "virtual"),
        status="ACTIVE",
        spending_limit=body.get("spending_limit", 1000),
        spent_amount=0,
        is_frozen=False,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    # Create card in Flutterwave
    try:
        # Get customer_id from employee if employee_id is provided
        customer_id = None
        if card.employee_id:
            from app.models import Employee
            employee = db.query(Employee).filter(Employee.id == card.employee_id).first()
            if employee and employee.flutterwave_customer_id:
                customer_id = employee.flutterwave_customer_id

        if customer_id:
            card_response = await flutterwave_client.issue_card(
                customer_id=customer_id,
                card_type=card.card_type,
                currency=card.currency,
                amount=card.spending_limit,
                first_name=card.card_name.split()[0] if card.card_name else "User",
                last_name=" ".join(card.card_name.split()[1:]) if card.card_name and len(card.card_name.split()) > 1 else ""
            )
            
            if card_response.get("status") == "success":
                card_data = card_response.get("data", {})
                card.flutterwave_card_id = card_data.get("id")
                db.commit()
                db.refresh(card)
    except Exception as e:
        # Log error but don't fail the card creation
        # Card can be linked to Flutterwave later
        pass

    return {"card": CardResponse.model_validate(card), "status": "created"}


@router.put("/{card_id}/status")
async def update_card_status(
    card_id: str,
    body: CardUpdateRequest,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Freeze/unfreeze a card or update its status."""
    card = db.query(Card).filter(
        Card.id == card_id,
        Card.employer_id == employer_id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if body.is_frozen is not None:
        card.is_frozen = body.is_frozen
        card.status = "FROZEN" if body.is_frozen else "ACTIVE"

    if body.status is not None:
        card.status = body.status

    db.commit()
    db.refresh(card)

    # Update card status in Flutterwave
    try:
        if card.flutterwave_card_id and body.is_frozen is not None:
            await flutterwave_client.freeze_card(
                card_id=card.flutterwave_card_id,
                freeze=body.is_frozen
            )
    except Exception as e:
        # Log error but don't fail the local update
        pass

    return CardResponse.model_validate(card)


@router.put("/{card_id}/limit")
async def update_card_limit(
    card_id: str,
    body: CardUpdateRequest,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Update the spending limit on a card."""
    card = db.query(Card).filter(
        Card.id == card_id,
        Card.employer_id == employer_id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if body.spending_limit is not None:
        card.spending_limit = body.spending_limit

    db.commit()
    db.refresh(card)

    # Update card limit in Flutterwave
    try:
        if card.flutterwave_card_id and body.spending_limit is not None:
            await flutterwave_client.set_card_limit(
                card_id=card.flutterwave_card_id,
                amount=body.spending_limit
            )
    except Exception as e:
        # Log error but don't fail the local update
        pass

    return CardResponse.model_validate(card)
