from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, ContactMessage, AdminMessage
from ..schemas import UserOut, AdminMessageCreate, AdminMessageOut
from ..auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

@router.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    # Retrieve all users
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@router.post("/approve/{user_id}")
def approve_user(user_id: int, db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User is already in status: {user.status}"
        )
        
    user.status = "approved"
    db.commit()
    return {"message": f"User {user.email} approved successfully"}

@router.post("/reject/{user_id}")
def reject_user(user_id: int, db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    db.delete(user)
    db.commit()
    return {"message": f"User reference deleted successfully"}

@router.delete("/shop/{user_id}")
def delete_shop(user_id: int, db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    db.delete(user)
    db.commit()
    return {"message": f"Shop {user.email} and all associated data deleted successfully"}

@router.post("/message/{user_id}")
def send_message_to_shop(user_id: int, payload: AdminMessageCreate, db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    msg = AdminMessage(user_id=user_id, subject=payload.subject, message=payload.message)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"message": "Message sent to shop successfully", "message_id": msg.id}

@router.get("/support-messages")
def get_support_messages(db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    msgs = db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()
    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "category": m.category,
            "subject": m.subject,
            "message": m.message,
            "status": m.status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "business_name": m.user.business_name if m.user else "Unknown Shop"
        })
    return result

@router.post("/support-messages/reply/{message_id}")
def reply_to_support_message(message_id: int, payload: AdminMessageCreate, db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support message not found"
        )
    
    reply_msg = AdminMessage(user_id=msg.user_id, subject=payload.subject, message=payload.message)
    db.add(reply_msg)
    
    msg.status = "Replied"
    db.commit()
    return {"message": "Reply sent successfully", "reply_id": reply_msg.id}
