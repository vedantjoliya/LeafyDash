import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserAnswers, ActiveModule
from ..schemas import OnboardingSubmit
from ..auth import get_current_active_user

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])

ONBOARDING_QUESTIONS = [
    {
        "key": "Analytics",
        "question": "Would you like to enable the Analytics Module to view graphical trends and performance metrics?",
        "options": [
            {"value": "yes", "label": "Yes, enable Analytics"},
            {"value": "no", "label": "No, skip Analytics"}
        ]
    },
    {
        "key": "Sales",
        "question": "Would you like to enable the Sales Module to log multi-location retail or online transactions?",
        "options": [
            {"value": "yes", "label": "Yes, enable Sales Log"},
            {"value": "no", "label": "No, skip Sales Log"}
        ]
    },
    {
        "key": "Inventory",
        "question": "Would you like to enable the Inventory Module to track product catalog items and stock levels?",
        "options": [
            {"value": "yes", "label": "Yes, enable Inventory"},
            {"value": "no", "label": "No, skip Inventory"}
        ]
    },
    {
        "key": "Reviews",
        "question": "Would you like to enable the Reviews Module to collect customer feedback via print-ready QR codes?",
        "options": [
            {"value": "yes", "label": "Yes, enable QR Reviews"},
            {"value": "no", "label": "No, skip QR Reviews"}
        ]
    },
    {
        "key": "CRM",
        "question": "Would you like to enable the CRM Module to follow up on client feedback and resolve complaints?",
        "options": [
            {"value": "yes", "label": "Yes, enable CRM Follow-ups"},
            {"value": "no", "label": "No, skip CRM Follow-ups"}
        ]
    },
    {
        "key": "Customers",
        "question": "Would you like to enable the Customers Module to build a client directory with billing summaries?",
        "options": [
            {"value": "yes", "label": "Yes, enable Customers Log"},
            {"value": "no", "label": "No, skip Customers Log"}
        ]
    }
]

@router.get("/questions")
def get_questions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return {"questions": ONBOARDING_QUESTIONS}

@router.post("/submit")
def submit_answers(
    payload: OnboardingSubmit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Clear existing configs if re-running
    db.query(UserAnswers).filter(UserAnswers.user_id == current_user.id).delete()
    db.query(ActiveModule).filter(ActiveModule.user_id == current_user.id).delete()
    
    # Save answers
    answers_str = json.dumps(payload.answers)
    user_answers = UserAnswers(user_id=current_user.id, answers_json=answers_str)
    db.add(user_answers)
    
    # Map questions directly to active states
    active_modules_dict = {
        "Overview": True,
        "Settings": True,
        "Analytics": payload.answers.get("Analytics") == "yes",
        "Sales": payload.answers.get("Sales") == "yes",
        "Inventory": payload.answers.get("Inventory") == "yes",
        "Reviews": payload.answers.get("Reviews") == "yes",
        "CRM": payload.answers.get("CRM") == "yes",
        "Customers": payload.answers.get("Customers") == "yes",
    }
    
    # Save active modules to DB
    for module_name, is_active in active_modules_dict.items():
        module_entry = ActiveModule(
            user_id=current_user.id,
            module_name=module_name,
            is_active=is_active
        )
        db.add(module_entry)
        
    # Mark user as onboarded
    current_user.status = "onboarded"
    db.commit()
    
    return {
        "message": "Onboarding completed successfully",
        "active_modules": [m for m, active in active_modules_dict.items() if active]
    }
