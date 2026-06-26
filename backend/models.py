from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    business_name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, approved, onboarded
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    answers = relationship("UserAnswers", back_populates="user", cascade="all, delete-orphan")
    active_modules = relationship("ActiveModule", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="user", cascade="all, delete-orphan")
    contact_messages = relationship("ContactMessage", back_populates="user", cascade="all, delete-orphan")
    admin_messages = relationship("AdminMessage", back_populates="user", cascade="all, delete-orphan")
    marketing_campaigns = relationship("MarketingCampaign", back_populates="user", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("OperationalExpense", back_populates="user", cascade="all, delete-orphan")


class UserAnswers(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers_json = Column(Text, nullable=False)  # JSON string of answers

    user = relationship("User", back_populates="answers")


class ActiveModule(Base):
    __tablename__ = "active_modules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module_name = Column(String, nullable=False)  # Overview, Analytics, Sales, etc.
    is_active = Column(Boolean, default=False)

    user = relationship("User", back_populates="active_modules")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True, default="")
    phone = Column(String, nullable=True, default="")
    email = Column(String, nullable=True, default="")
    manager = Column(String, nullable=True, default="")

    user = relationship("User", back_populates="locations")
    products = relationship("Product", back_populates="location", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="location_rel", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=True)
    stock = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    buying_price = Column(Float, default=0.0)
    image_path = Column(String, nullable=True)

    user = relationship("User", back_populates="products")
    location = relationship("Location", back_populates="products")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String, default="New")  # New, Replied, Resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    location = relationship("Location")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    amount = Column(Float, nullable=False)
    item_name = Column(String, nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    amount = Column(Float, nullable=False)
    location = Column(String, nullable=True)  # Legacy string label
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_address = Column(String, nullable=True)
    promo_code = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="sales")
    location_rel = relationship("Location", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="New")  # New, Replied, Resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="contact_messages")


class AdminMessage(Base):
    __tablename__ = "admin_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="admin_messages")


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    segment = Column(String, nullable=False)
    channel = Column(String, nullable=False)  # whatsapp, email, print
    coupon_code = Column(String, nullable=True)
    discount_type = Column(String, nullable=True)  # percentage or amount
    discount_value = Column(Float, nullable=True)
    message_body = Column(Text, nullable=False)
    recipients_count = Column(Integer, default=0)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # "active" or "stopped"

    user = relationship("User", back_populates="marketing_campaigns")
    tracking_records = relationship("CampaignCustomerTracking", back_populates="campaign", cascade="all, delete-orphan")


class CampaignCustomerTracking(Base):
    __tablename__ = "campaign_customer_tracking"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=False)
    customer_email = Column(String, index=True, nullable=False)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    converted = Column(Boolean, default=False)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)

    campaign = relationship("MarketingCampaign", back_populates="tracking_records")
    sale = relationship("Sale")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    salary = Column(Float, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="Active")  # Active, Suspended, Inactive
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="employees")


class OperationalExpense(Base):
    __tablename__ = "operational_expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)  # Rent, Utilities, Software, Marketing, etc.
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="expenses")


