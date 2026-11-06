import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip
from app.core.permissions import UserRole, UserStatus
from app.core.security import hash_password, validate_password_strength
from app.database import get_db
from app.models.customer_profile import CustomerProfile
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.registration import (
    CustomerRegisterRequest,
    RegistrationResponse,
    ResendVerificationRequest,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/registration", tags=["Module 3: Customer Registration"])


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_customer(
    payload: CustomerRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new customer account.
    - Validates email address syntax and phone format.
    - Prevents duplicate registrations for existing emails or phone numbers.
    - Issues an email verification token with 24-hour validity.
    - Initializes customer profile.
    """
    email_clean = payload.email.strip().lower()

    # Check for duplicate email
    existing_email = db.query(User).filter(User.email == email_clean).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Registration failed: Email '{email_clean}' is already registered."
        )

    # Check for duplicate phone
    existing_phone = db.query(User).filter(User.phone == payload.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Registration failed: Phone number '{payload.phone}' is already registered."
        )

    # Validate password complexity
    if not validate_password_strength(payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and include an uppercase letter, lowercase letter, number, and special character."
        )

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    new_user = User(
        email=email_clean,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        role=UserRole.CUSTOMER.value,
        status=UserStatus.ACTIVE.value,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires_at=expires_at,
        registration_status="PENDING_VERIFICATION"
    )
    db.add(new_user)
    db.flush()

    # Initialize associated customer profile
    profile = CustomerProfile(
        user_id=new_user.id,
        marketing_opt_in=payload.marketing_opt_in
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)

    log_user_activity(
        db,
        action="CUSTOMER_REGISTERED",
        user_id=new_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"registration_status": "PENDING_VERIFICATION"}
    )

    base_url = str(request.base_url).rstrip("/")
    verification_link = f"{base_url}/api/v1/registration/verify-email?token={verification_token}"

    return RegistrationResponse(
        user_id=new_user.id,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        registration_status=new_user.registration_status,
        verification_token=verification_token,
        verification_link=verification_link,
        message="Registration successful! Please verify your email using the provided token or link."
    )


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(
    token: str = Query(..., description="Email verification token"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Verify customer email address using verification token.
    Updates registration status to VERIFIED and marks is_verified=True.
    """
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized verification token."
        )

    if user.is_verified:
        return MessageResponse(
            success=True,
            message="Email is already verified. You can log in.",
            data={"registration_status": user.registration_status}
        )

    # Check token expiration
    if user.verification_token_expires_at:
        now_utc = datetime.now(timezone.utc)
        token_exp = user.verification_token_expires_at
        if token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=timezone.utc)
            
        if now_utc > token_exp:
            user.registration_status = "EXPIRED"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired. Please request a new verification email."
            )

    user.is_verified = True
    user.registration_status = "VERIFIED"
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()

    log_user_activity(
        db,
        action="EMAIL_VERIFIED",
        user_id=user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"status": "VERIFIED"}
    )

    return MessageResponse(
        success=True,
        message="Email successfully verified! Your account is now fully active.",
        data={"user_id": user.id, "email": user.email, "registration_status": "VERIFIED"}
    )


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification_email(
    payload: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a new verification token for an unverified account.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account found with email '{email_clean}'"
        )

    if user.is_verified:
        return MessageResponse(
            success=True,
            message="This account is already verified. No action needed."
        )

    new_token = secrets.token_urlsafe(32)
    user.verification_token = new_token
    user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    user.registration_status = "PENDING_VERIFICATION"
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    verification_link = f"{base_url}/api/v1/registration/verify-email?token={new_token}"

    log_user_activity(
        db,
        action="VERIFICATION_RESENT",
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return MessageResponse(
        success=True,
        message="A new verification link has been generated.",
        data={
            "token": new_token,
            "verification_link": verification_link,
            "expires_in_hours": 24
        }
    )


@router.get("/status", response_model=MessageResponse)
def get_registration_status(
    email: str = Query(..., description="Customer email address"),
    db: Session = Depends(get_db)
):
    """
    Check customer registration and email verification status.
    """
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account found with email '{email_clean}'"
        )

    return MessageResponse(
        success=True,
        message="Registration status retrieved.",
        data={
            "email": user.email,
            "is_verified": user.is_verified,
            "registration_status": user.registration_status,
            "account_status": user.status
        }
    )

