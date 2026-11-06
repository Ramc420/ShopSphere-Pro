import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user
from app.core.permissions import UserRole
from app.database import get_db
from app.models.address import Address
from app.models.order import Order
from app.models.user import User
from app.schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    MockOrderResponse,
    OrderAddressAssociationRequest,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/customer/addresses", tags=["Module 5: Address Management"])


def unset_existing_defaults(db: Session, user_id: int, is_shipping: bool, is_billing: bool, exclude_id: Optional[int] = None):
    stmt = db.query(Address).filter(Address.user_id == user_id, Address.is_active == True)
    if exclude_id:
        stmt = stmt.filter(Address.id != exclude_id)
        
    for addr in stmt.all():
        if is_shipping and addr.is_default:
            addr.is_default = False
        if is_billing and addr.is_default_billing:
            addr.is_default_billing = False


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new shipping or billing address for the customer.
    Validates all required fields and updates default address state.
    """
    # If this is the user's first address, make it default automatically
    existing_count = db.query(Address).filter(Address.user_id == current_user.id, Address.is_active == True).count()
    is_default = payload.is_default or (existing_count == 0 and payload.address_type in ["SHIPPING", "BOTH"])
    is_default_billing = payload.is_default_billing or (existing_count == 0 and payload.address_type in ["BILLING", "BOTH"])

    if is_default or is_default_billing:
        unset_existing_defaults(db, current_user.id, is_shipping=is_default, is_billing=is_default_billing)

    new_address = Address(
        user_id=current_user.id,
        full_name=payload.full_name.strip(),
        phone_number=payload.phone_number.strip(),
        address_type=payload.address_type,
        street_line1=payload.street_line1.strip(),
        street_line2=payload.street_line2.strip() if payload.street_line2 else None,
        city=payload.city.strip(),
        state_province=payload.state_province.strip(),
        postal_code=payload.postal_code.strip(),
        country=payload.country.strip(),
        is_default=is_default,
        is_default_billing=is_default_billing,
        is_active=True
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    log_user_activity(
        db,
        action="ADDRESS_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"address_id": new_address.id, "type": new_address.address_type}
    )

    return new_address


@router.get("", response_model=List[AddressResponse])
def get_my_addresses(
    address_type: Optional[str] = Query(None, description="Filter by SHIPPING, BILLING, or BOTH"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of active addresses for the authenticated customer.
    """
    stmt = db.query(Address).filter(Address.user_id == current_user.id, Address.is_active == True)
    if address_type:
        stmt = stmt.filter(Address.address_type.in_([address_type.upper(), "BOTH"]))
    return stmt.order_by(Address.is_default.desc(), Address.id.desc()).all()


@router.get("/{address_id}", response_model=AddressResponse)
def get_address_by_id(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific address by ID.
    """
    addr = db.query(Address).filter(Address.id == address_id, Address.is_active == True).first()
    if not addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
        
    if addr.user_id != current_user.id and current_user.role not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this address")
        
    return addr


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing address.
    """
    addr = db.query(Address).filter(Address.id == address_id, Address.is_active == True).first()
    if not addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
        
    if addr.user_id != current_user.id and current_user.role not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if payload.is_default is True or payload.is_default_billing is True:
        unset_existing_defaults(
            db, addr.user_id,
            is_shipping=(payload.is_default is True),
            is_billing=(payload.is_default_billing is True),
            exclude_id=addr.id
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            if isinstance(value, str):
                setattr(addr, field, value.strip())
            else:
                setattr(addr, field, value)

    db.commit()
    db.refresh(addr)

    log_user_activity(
        db,
        action="ADDRESS_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"address_id": addr.id}
    )

    return addr


@router.patch("/{address_id}/set-default", response_model=AddressResponse)
def set_default_address(
    address_id: int,
    default_type: str = Query("shipping", description="'shipping' or 'billing'"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set an address as default shipping or default billing address.
    """
    addr = db.query(Address).filter(Address.id == address_id, Address.is_active == True).first()
    if not addr or addr.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    dt_lower = default_type.lower()
    if dt_lower == "shipping":
        unset_existing_defaults(db, current_user.id, is_shipping=True, is_billing=False, exclude_id=addr.id)
        addr.is_default = True
    elif dt_lower == "billing":
        unset_existing_defaults(db, current_user.id, is_shipping=False, is_billing=True, exclude_id=addr.id)
        addr.is_default_billing = True
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="default_type must be 'shipping' or 'billing'")

    db.commit()
    db.refresh(addr)

    log_user_activity(
        db,
        action=f"DEFAULT_{default_type.upper()}_ADDRESS_SET",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"address_id": addr.id}
    )

    return addr


@router.delete("/{address_id}", response_model=MessageResponse)
def delete_address(
    address_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an address. If associated with historical orders, performs a soft-deactivate
    to preserve order integrity while removing it from customer view.
    """
    addr = db.query(Address).filter(Address.id == address_id, Address.is_active == True).first()
    if not addr or addr.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    # Check if linked with orders
    linked_orders = db.query(Order).filter(
        (Order.shipping_address_id == addr.id) | (Order.billing_address_id == addr.id)
    ).count()

    if linked_orders > 0:
        # Soft delete to preserve historical order records
        addr.is_active = False
        addr.is_default = False
        addr.is_default_billing = False
        db.commit()
        msg = f"Address has been removed from your active addresses (preserved in {linked_orders} order records)."
    else:
        db.delete(addr)
        db.commit()
        msg = "Address successfully deleted."

    log_user_activity(
        db,
        action="ADDRESS_DELETED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"address_id": address_id}
    )

    return MessageResponse(success=True, message=msg)


@router.post("/associate-order", response_model=MockOrderResponse, status_code=status.HTTP_201_CREATED)
def associate_address_with_order(
    payload: OrderAddressAssociationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Associate customer shipping and billing addresses with an order (Module 5).
    Takes a snapshot of both addresses to maintain an immutable record.
    """
    ship_addr = db.query(Address).filter(Address.id == payload.shipping_address_id, Address.user_id == current_user.id).first()
    if not ship_addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping address not found")

    bill_addr = db.query(Address).filter(Address.id == payload.billing_address_id, Address.user_id == current_user.id).first()
    if not bill_addr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing address not found")

    order_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    ship_snapshot = f"{ship_addr.full_name}, {ship_addr.street_line1}, {ship_addr.city}, {ship_addr.state_province} {ship_addr.postal_code}, {ship_addr.country} (Tel: {ship_addr.phone_number})"
    bill_snapshot = f"{bill_addr.full_name}, {bill_addr.street_line1}, {bill_addr.city}, {bill_addr.state_province} {bill_addr.postal_code}, {bill_addr.country} (Tel: {bill_addr.phone_number})"

    order = Order(
        order_number=order_num,
        user_id=current_user.id,
        shipping_address_id=ship_addr.id,
        billing_address_id=bill_addr.id,
        shipping_address_snapshot=ship_snapshot,
        billing_address_snapshot=bill_snapshot,
        status="CONFIRMED",
        total_amount=payload.total_amount
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@router.get("/orders/all", response_model=List[MockOrderResponse])
def get_user_orders_with_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all orders placed by the current user with associated addresses.
    """
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.id.desc()).all()

