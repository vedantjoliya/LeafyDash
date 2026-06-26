from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    business_name: str
    industry: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        special_chars = "@$!%*?&_#-"
        if not any(c in special_chars for c in value):
            raise ValueError(f"Password must contain at least one special character from: {special_chars}")
        return value

    @field_validator("business_name")
    @classmethod
    def validate_business_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Business name cannot be empty")
        return stripped

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Industry sector cannot be empty")
        return stripped

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str  # "user" or "admin"
    status: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    business_name: str
    industry: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class OnboardingSubmit(BaseModel):
    answers: Dict[str, str]  # Question key to selected option

class LocationCreate(BaseModel):
    name: str
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    manager: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Location name cannot be empty")
        return stripped

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("Location name cannot be empty")
        return stripped

class LocationOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    manager: Optional[str] = ""

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    stock: int
    price: float
    buying_price: float
    location_id: int
    image_path: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Product name cannot be empty")
        return stripped

    @field_validator("stock")
    @classmethod
    def validate_stock(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Stock count cannot be negative")
        return value

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value

    @field_validator("buying_price")
    @classmethod
    def validate_buying_price(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Buying price cannot be negative")
        return value

class ProductOut(BaseModel):
    id: int
    name: str
    sku: Optional[str] = None
    stock: int
    price: float
    buying_price: float
    location_id: Optional[int] = None
    image_path: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    customer_name: str
    rating: int
    comment: Optional[str] = None
    location_id: Optional[int] = None

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Customer name cannot be empty")
        return stripped

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if not (1 <= value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return value

class ReviewOut(BaseModel):
    id: int
    customer_name: str
    rating: int
    comment: Optional[str] = None
    status: str
    created_at: datetime
    location_id: Optional[int] = None

    class Config:
        from_attributes = True

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Quantity must be at least 1")
        return value

class SaleItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    amount: float
    item_name: str

    class Config:
        from_attributes = True

class SaleCreate(BaseModel):
    location_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    promo_code: Optional[str] = None
    items: List[SaleItemCreate]

class SaleOut(BaseModel):
    id: int
    location_id: Optional[int] = None
    amount: float
    location: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    promo_code: Optional[str] = None
    timestamp: datetime
    items: List[SaleItemOut]

    class Config:
        from_attributes = True

class ModuleStatus(BaseModel):
    module_name: str
    is_active: bool

    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        special_chars = "@$!%*?&_#-"
        if not any(c in special_chars for c in value):
            raise ValueError(f"Password must contain at least one special character from: {special_chars}")
        return value

    @field_validator("business_name")
    @classmethod
    def validate_business_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("Business name cannot be empty")
        return stripped

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("Industry cannot be empty")
        return stripped


class ContactMessageCreate(BaseModel):
    category: str
    subject: str
    message: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Category cannot be empty")
        return stripped

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Subject cannot be empty")
        return stripped

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message cannot be empty")
        return stripped


class ContactMessageOut(BaseModel):
    id: int
    user_id: int
    category: str
    subject: str
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MarketingCampaignCreate(BaseModel):
    name: str
    segment: str
    channel: str
    coupon_code: Optional[str] = None
    discount_type: Optional[str] = None  # "percentage" or "amount"
    discount_value: Optional[float] = None
    message_body: str
    recipients_count: int
    target_emails: Optional[List[str]] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Campaign name cannot be empty")
        return stripped

    @field_validator("message_body")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message body cannot be empty")
        return stripped


class MarketingCampaignOut(BaseModel):
    id: int
    user_id: int
    name: str
    segment: str
    channel: str
    coupon_code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    message_body: str
    recipients_count: int
    sent_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class CampaignCustomerTrackingOut(BaseModel):
    id: int
    campaign_id: int
    customer_email: str
    clicked: bool
    clicked_at: Optional[datetime] = None
    converted: bool
    sale_id: Optional[int] = None
    customer_name: Optional[str] = None
    sale_amount: Optional[float] = None
    items_purchased: Optional[str] = None
    is_new_customer: Optional[bool] = False

    class Config:
        from_attributes = True



class AdminMessageCreate(BaseModel):
    subject: str
    message: str

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Subject cannot be empty")
        return stripped

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message cannot be empty")
        return stripped


class AdminMessageOut(BaseModel):
    id: int
    user_id: int
    subject: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    name: str
    role: str
    salary: float
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "Active"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Employee name cannot be empty")
        return stripped

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Employee role cannot be empty")
        return stripped

    @field_validator("salary")
    @classmethod
    def validate_salary(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Salary cannot be negative")
        return value


class EmployeeOut(BaseModel):
    id: int
    user_id: int
    name: str
    role: str
    salary: float
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OperationalExpenseCreate(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Category cannot be empty")
        return stripped

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Amount cannot be negative")
        return value


class OperationalExpenseOut(BaseModel):
    id: int
    user_id: int
    category: str
    amount: float
    description: Optional[str] = None
    date: datetime

    class Config:
        from_attributes = True

