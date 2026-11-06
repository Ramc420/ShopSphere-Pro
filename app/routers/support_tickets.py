import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from app.models.support_ticket import SupportTicket, TicketMessage
from app.schemas.support_ticket import (
    SupportTicketCreate, TicketMessageCreate, TicketAssignRequest,
    TicketStatusUpdate, SupportTicketResponse, TicketMessageResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/support-tickets", tags=["Module 40: Customer Support Tickets"])


@router.post("/", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: SupportTicketCreate,
    current_user: User = Depends(require_permissions(Permission.TICKETS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 40: Create support ticket associated with order or product.
    Initializes message thread.
    """
    if payload.order_id:
        order = db.query(Order).filter(Order.id == payload.order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced order not found")

    if payload.product_id:
        prod = db.query(Product).filter(Product.id == payload.product_id).first()
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced product not found")

    ticket_num = f"TCK-{uuid.uuid4().hex[:8].upper()}"
    ticket = SupportTicket(
        ticket_number=ticket_num,
        user_id=current_user.id,
        order_id=payload.order_id,
        product_id=payload.product_id,
        subject=payload.subject.strip(),
        category=payload.category.upper(),
        priority=payload.priority.upper(),
        status="OPEN"
    )
    db.add(ticket)
    db.flush()

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_user_id=current_user.id,
        message=payload.message.strip(),
        is_internal_note=False
    )
    db.add(msg)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/", response_model=List[SupportTicketResponse])
def list_support_tickets(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_permissions(Permission.TICKETS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    List support tickets (customers see own; staff see all).
    """
    query = db.query(SupportTicket)
    if current_user.role == "CUSTOMER":
        query = query.filter(SupportTicket.user_id == current_user.id)

    if status_filter:
        query = query.filter(SupportTicket.status == status_filter.upper())

    tickets = query.order_by(SupportTicket.created_at.desc()).all()
    return tickets


@router.get("/{ticket_id}", response_model=SupportTicketResponse)
def get_ticket_details(
    ticket_id: int,
    current_user: User = Depends(require_permissions(Permission.TICKETS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve full conversation and resolution history for a ticket.
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")

    if current_user.role == "CUSTOMER" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # If customer, hide internal staff notes
    if current_user.role == "CUSTOMER":
        ticket.messages = [m for m in ticket.messages if not m.is_internal_note]

    return ticket


@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse, status_code=status.HTTP_201_CREATED)
def reply_to_ticket(
    ticket_id: int,
    payload: TicketMessageCreate,
    current_user: User = Depends(require_permissions(Permission.TICKETS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Append response message or internal note to support ticket.
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")

    if current_user.role == "CUSTOMER" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    is_internal = payload.is_internal_note and current_user.role != "CUSTOMER"

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_user_id=current_user.id,
        message=payload.message.strip(),
        is_internal_note=is_internal
    )
    db.add(msg)

    # If customer replied, set to WAITING_FOR_AGENT / IN_PROGRESS; if agent replied, set WAITING_FOR_CUSTOMER
    if current_user.role == "CUSTOMER":
        ticket.status = "IN_PROGRESS"
    elif not is_internal:
        ticket.status = "WAITING_FOR_CUSTOMER"

    db.commit()
    db.refresh(msg)
    return msg


@router.patch("/{ticket_id}/status", response_model=SupportTicketResponse)
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    current_user: User = Depends(require_permissions(Permission.TICKETS_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Update ticket status (OPEN, IN_PROGRESS, RESOLVED, CLOSED).
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")

    valid_statuses = {"OPEN", "IN_PROGRESS", "WAITING_FOR_CUSTOMER", "RESOLVED", "CLOSED"}
    new_status = payload.status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {valid_statuses}")

    ticket.status = new_status
    db.commit()
    db.refresh(ticket)
    return ticket


@router.patch("/{ticket_id}/assign", response_model=SupportTicketResponse)
def assign_ticket_to_agent(
    ticket_id: int,
    payload: TicketAssignRequest,
    current_user: User = Depends(require_permissions(Permission.TICKETS_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Assign support ticket to a specific agent user.
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found")

    agent = db.query(User).filter(User.id == payload.assigned_to_user_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned agent user not found")

    ticket.assigned_to_user_id = agent.id
    ticket.status = "IN_PROGRESS"
    db.commit()
    db.refresh(ticket)
    return ticket

