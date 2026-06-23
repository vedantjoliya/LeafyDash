from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import datetime
import json
import os
import shutil
import uuid
from ..database import get_db
from ..models import User, ActiveModule, Product, Review, Sale, SaleItem, UserAnswers, Location, ContactMessage, AdminMessage, MarketingCampaign, CampaignCustomerTracking, Employee, OperationalExpense
from ..schemas import ProductCreate, ProductOut, ReviewCreate, ReviewOut, SaleCreate, SaleOut, ModuleStatus, LocationCreate, LocationOut, LocationUpdate, ProfileUpdate, ContactMessageCreate, AdminMessageOut, MarketingCampaignCreate, MarketingCampaignOut, CampaignCustomerTrackingOut, EmployeeCreate, EmployeeOut, OperationalExpenseCreate, OperationalExpenseOut
from ..auth import get_current_active_user, get_password_hash

router = APIRouter(tags=["Dashboard Operations"])

# --- Locations Endpoints ---

@router.get("/api/dashboard/locations", response_model=List[LocationOut])
def get_locations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Location).filter(Location.user_id == current_user.id).all()

@router.post("/api/dashboard/locations", response_model=LocationOut)
def add_location(
    location_data: LocationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_loc = Location(
        user_id=current_user.id,
        name=location_data.name,
        address=location_data.address or "",
        phone=location_data.phone or "",
        email=location_data.email or "",
        manager=location_data.manager or ""
    )
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc

@router.put("/api/dashboard/locations/{location_id}", response_model=LocationOut)
def update_location(
    location_id: int,
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    loc = db.query(Location).filter(
        Location.id == location_id,
        Location.user_id == current_user.id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if location_data.name is not None:
        loc.name = location_data.name
    if location_data.address is not None:
        loc.address = location_data.address
    if location_data.phone is not None:
        loc.phone = location_data.phone
    if location_data.email is not None:
        loc.email = location_data.email
    if location_data.manager is not None:
        loc.manager = location_data.manager
    
    db.commit()
    db.refresh(loc)
    return loc

@router.delete("/api/dashboard/locations/{location_id}")
def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    loc = db.query(Location).filter(
        Location.id == location_id,
        Location.user_id == current_user.id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(loc)
    db.commit()
    return {"detail": "Location deleted successfully"}

# --- Module Configuration Endpoint ---

@router.get("/api/dashboard/config", response_model=List[ModuleStatus])
def get_dashboard_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Retrieve active modules
    modules = db.query(ActiveModule).filter(ActiveModule.user_id == current_user.id).all()
    
    # If no configuration, provide a default layout
    if not modules:
        defaults = ["Overview", "Analytics", "Sales", "Inventory", "Reviews", "CRM", "Customers", "Inbox", "Operations", "Settings"]
        for mod in defaults:
            db.add(ActiveModule(user_id=current_user.id, module_name=mod, is_active=True))
        db.commit()
        modules = db.query(ActiveModule).filter(ActiveModule.user_id == current_user.id).all()
        
    # Ensure Inbox module exists for older registered shops
    has_inbox = any(m.module_name == "Inbox" for m in modules)
    if not has_inbox and modules:
        inbox_mod = ActiveModule(user_id=current_user.id, module_name="Inbox", is_active=True)
        db.add(inbox_mod)
        db.commit()
        modules.append(inbox_mod)

    # Ensure Operations module exists for older registered shops
    has_operations = any(m.module_name == "Operations" for m in modules)
    if not has_operations and modules:
        ops_mod = ActiveModule(user_id=current_user.id, module_name="Operations", is_active=True)
        db.add(ops_mod)
        db.commit()
        modules.append(ops_mod)
        
    return modules

@router.put("/api/dashboard/profile")
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if profile_data.business_name is not None:
        name = profile_data.business_name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Business name cannot be empty")
        current_user.business_name = name

    if profile_data.industry is not None:
        ind = profile_data.industry.strip()
        if not ind:
            raise HTTPException(status_code=400, detail="Industry cannot be empty")
        current_user.industry = ind

    if profile_data.email is not None:
        email = profile_data.email.strip().lower()
        if not email:
            raise HTTPException(status_code=400, detail="Email cannot be empty")
        exists = db.query(User).filter(User.email == email, User.id != current_user.id).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already taken")
        current_user.email = email

    if profile_data.password is not None and profile_data.password != "":
        passwd = profile_data.password
        if len(passwd) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        current_user.password_hash = get_password_hash(passwd)

    db.commit()
    db.refresh(current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "business_name": current_user.business_name,
        "industry": current_user.industry
    }

# --- 1. Overview Endpoints ---

@router.get("/api/dashboard/overview")
def get_overview_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Total metrics
    sales = db.query(Sale).filter(Sale.user_id == current_user.id).all()
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    reviews = db.query(Review).filter(Review.user_id == current_user.id).all()
    employees = db.query(Employee).filter(Employee.user_id == current_user.id).all()
    expenses = db.query(OperationalExpense).filter(OperationalExpense.user_id == current_user.id).all()
    
    total_revenue = sum(s.amount for s in sales)
    
    # Calculate actual spends
    payroll_sum = sum(e.salary for e in employees if e.status == "Active")
    total_expenses = sum(exp.amount for exp in expenses)
    total_spend = payroll_sum + total_expenses
    profit = total_revenue - total_spend
    
    avg_rating = 0.0
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
        
    # Chart data (last 6 days)
    chart_labels = []
    revenue_trend = []
    spend_trend = []
    
    today = datetime.date.today()
    for i in range(5, -1, -1):
        day = today - datetime.timedelta(days=i)
        chart_labels.append(day.strftime("%b %d"))
        
        # Calculate revenue for this day
        day_revenue = sum(
            s.amount for s in sales 
            if s.timestamp.date() == day
        )
        revenue_trend.append(round(day_revenue, 2))
        
        # Calculate actual expenses for this day
        day_expense = sum(
            exp.amount for exp in expenses
            if exp.date.date() == day
        )
        # Plus proportional daily payroll cost
        day_payroll = payroll_sum / 30.0
        spend_trend.append(round(day_expense + day_payroll, 2))
        
    # Location sales data
    loc_sales = {}
    for s in sales:
        loc_label = s.location or "Online"
        loc_sales[loc_label] = loc_sales.get(loc_label, 0.0) + s.amount
    
    location_sales = {
        "labels": list(loc_sales.keys()) if loc_sales else ["Online"],
        "data": [round(v, 2) for v in loc_sales.values()] if loc_sales else [0.0]
    }
    
    # Expense category breakdown
    categories_map = {}
    if payroll_sum > 0:
        categories_map["Payroll"] = payroll_sum
    for exp in expenses:
        categories_map[exp.category] = categories_map.get(exp.category, 0.0) + exp.amount
        
    expense_breakdown = {
        "labels": list(categories_map.keys()),
        "data": [round(v, 2) for v in categories_map.values()]
    }
        
    return {
        "user_id": current_user.id,
        "business_name": current_user.business_name,
        "industry": current_user.industry,
        "email": current_user.email,
        "metrics": {
            "revenue": round(total_revenue, 2),
            "spend": round(total_spend, 2),
            "profit": round(profit, 2),
            "stock_count": sum(p.stock for p in products),
            "reviews_count": len(reviews),
            "avg_rating": avg_rating,
        },
        "chart": {
            "labels": chart_labels,
            "revenue": revenue_trend,
            "spend": spend_trend
        },
        "location_sales": location_sales,
        "expense_breakdown": expense_breakdown
    }

# --- 2. Analytics Endpoints ---

@router.get("/api/dashboard/analytics")
def get_analytics_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sales = db.query(Sale).filter(Sale.user_id == current_user.id).all()
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    
    # Location breakdown
    loc_sales = {}
    for s in sales:
        loc_label = s.location or "Online"
        loc_sales[loc_label] = loc_sales.get(loc_label, 0.0) + s.amount
        
    location_labels = list(loc_sales.keys())
    location_data = [round(v, 2) for v in loc_sales.values()]
    
    # Product sales calculations
    product_performance = {
        p.id: {
            "name": p.name,
            "sku": p.sku or "N/A",
            "units_sold": 0,
            "revenue": 0.0,
            "stock": p.stock
        } for p in products
    }
    
    for s in sales:
        for item in s.items:
            if item.product_id in product_performance:
                product_performance[item.product_id]["units_sold"] += item.quantity
                product_performance[item.product_id]["revenue"] += item.amount
            else:
                product_performance[item.product_id] = {
                    "name": item.item_name,
                    "sku": "N/A",
                    "units_sold": item.quantity,
                    "revenue": item.amount,
                    "stock": 0
                }
                
    product_list = list(product_performance.values())
    product_list_sorted = sorted(product_list, key=lambda x: x["units_sold"], reverse=True)
    
    # Top 5 products for chart
    top_5 = product_list_sorted[:5]
    product_labels = [p["name"] for p in top_5]
    product_units = [p["units_sold"] for p in top_5]
    product_revenues = [round(p["revenue"], 2) for p in top_5]
    
    total_units_sold = sum(p["units_sold"] for p in product_list)
    
    # Top 5 customer spends
    customer_spends = {}
    for s in sales:
        email = s.customer_email or "walkin@example.com"
        name = s.customer_name or "Walk-in Customer"
        key = (email.strip().lower(), name)
        customer_spends[key] = customer_spends.get(key, 0.0) + s.amount
    
    sorted_customer_spends = sorted(customer_spends.items(), key=lambda x: x[1], reverse=True)[:5]
    customer_labels = [item[0][1] for item in sorted_customer_spends]
    customer_data = [round(item[1], 2) for item in sorted_customer_spends]
    
    # Product stock values
    product_stock_values = []
    for p in products:
        val = p.price * p.stock
        product_stock_values.append((p.name, val))
    sorted_stock_values = sorted(product_stock_values, key=lambda x: x[1], reverse=True)[:5]
    stock_labels = [item[0] for item in sorted_stock_values]
    stock_data = [round(item[1], 2) for item in sorted_stock_values]
    
    return {
        "locations": {
            "labels": location_labels if location_labels else ["Online"],
            "data": location_data if location_data else [0.0]
        },
        "products": {
            "labels": product_labels,
            "units": product_units,
            "revenues": product_revenues,
            "all_data": product_list_sorted
        },
        "total_products_sold": total_units_sold,
        "customers": {
            "labels": customer_labels if customer_labels else ["No Customers"],
            "data": customer_data if customer_data else [0.0]
        },
        "stock_values": {
            "labels": stock_labels if stock_labels else ["No Stock"],
            "data": stock_data if stock_data else [0.0]
        }
    }

# --- 3. Sales Endpoints ---

@router.get("/api/dashboard/sales", response_model=List[SaleOut])
def get_sales(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Sale).filter(Sale.user_id == current_user.id).order_by(Sale.timestamp.desc()).all()

@router.get("/api/dashboard/sales/validate-promo")
def validate_promo(
    code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(MarketingCampaign).filter(
        MarketingCampaign.user_id == current_user.id,
        MarketingCampaign.coupon_code == code.strip()
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return {
        "coupon_code": campaign.coupon_code,
        "discount_type": campaign.discount_type,
        "discount_value": campaign.discount_value
    }

@router.post("/api/dashboard/sales", response_model=SaleOut)
def add_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not sale_data.items:
        raise HTTPException(status_code=400, detail="A sale must contain at least one item.")
        
    # Verify promo code if provided
    campaign_found = None
    if sale_data.promo_code:
        campaign_found = db.query(MarketingCampaign).filter(
            MarketingCampaign.user_id == current_user.id,
            MarketingCampaign.coupon_code == sale_data.promo_code
        ).first()
        if not campaign_found:
            raise HTTPException(status_code=400, detail="Invalid promo code.")

    # Verify location exists
    loc = db.query(Location).filter(
        Location.id == sale_data.location_id,
        Location.user_id == current_user.id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Store location not found")
        
    loc_name = loc.name
    total_invoice_amount = 0.0
    sale_items = []
    
    # Process each item
    for item in sale_data.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.user_id == current_user.id
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
            
        if product.location_id != sale_data.location_id:
            raise HTTPException(status_code=400, detail=f"Product '{product.name}' does not belong to the selected storefront location")
            
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product '{product.name}'. Available: {product.stock}")
            
        item_amount = product.price * item.quantity
        total_invoice_amount += item_amount
        
        # Decrement product stock
        product.stock -= item.quantity
        
        # Create sale item DB object
        db_item = SaleItem(
            product_id=product.id,
            quantity=item.quantity,
            amount=item_amount,
            item_name=product.name
        )
        sale_items.append(db_item)
        
    # Apply discount if campaign has discount settings
    if campaign_found:
        if campaign_found.discount_type == "percentage" and campaign_found.discount_value is not None:
            total_invoice_amount = total_invoice_amount * (1.0 - (campaign_found.discount_value / 100.0))
        elif campaign_found.discount_type == "amount" and campaign_found.discount_value is not None:
            total_invoice_amount = max(0.0, total_invoice_amount - campaign_found.discount_value)
        total_invoice_amount = round(total_invoice_amount, 2)

    new_sale = Sale(
        user_id=current_user.id,
        location_id=sale_data.location_id,
        amount=total_invoice_amount,
        location=loc_name,
        customer_name=sale_data.customer_name or "Walk-in Customer",
        customer_email=sale_data.customer_email or "walkin@example.com",
        customer_phone=sale_data.customer_phone or "N/A",
        customer_address=sale_data.customer_address,
        promo_code=sale_data.promo_code,
        items=sale_items
    )
    
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    # Link tracking conversion if applicable
    if campaign_found and sale_data.customer_email:
        email_clean = sale_data.customer_email.strip().lower()
        tracking = db.query(CampaignCustomerTracking).filter(
            CampaignCustomerTracking.campaign_id == campaign_found.id,
            CampaignCustomerTracking.customer_email == email_clean
        ).first()
        if tracking:
            tracking.clicked = True
            if not tracking.clicked_at:
                tracking.clicked_at = datetime.datetime.utcnow()
            tracking.converted = True
            tracking.sale_id = new_sale.id
            db.commit()

    return new_sale

@router.put("/api/dashboard/sales/{sale_id}", response_model=SaleOut)
def update_sale(
    sale_id: int,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.user_id == current_user.id
    ).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
        
    cust_name = payload.get("customer_name")
    cust_email = payload.get("customer_email")
    cust_phone = payload.get("customer_phone")
    loc_id = payload.get("location_id")
    
    if loc_id is not None:
        loc = db.query(Location).filter(
            Location.id == loc_id,
            Location.user_id == current_user.id
        ).first()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")
        sale.location_id = loc_id
        sale.location = loc.name
        
    if cust_name is not None:
        sale.customer_name = cust_name
    if cust_email is not None:
        sale.customer_email = cust_email
    if cust_phone is not None:
        sale.customer_phone = cust_phone
        
    db.commit()
    db.refresh(sale)
    return sale

@router.delete("/api/dashboard/sales/{sale_id}")
def delete_sale(
    sale_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.user_id == current_user.id
    ).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
        
    # Restore product stocks
    for item in sale.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.user_id == current_user.id
        ).first()
        if product:
            product.stock += item.quantity
            
    db.delete(sale)
    db.commit()
    return {"message": "Sale deleted successfully"}

# --- 4. Inventory Endpoints ---

@router.get("/api/dashboard/inventory", response_model=List[ProductOut])
def get_inventory(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Product).filter(Product.user_id == current_user.id).all()

@router.post("/api/dashboard/inventory", response_model=ProductOut)
def add_product(
    name: str = Form(...),
    sku: str = Form(None),
    stock: int = Form(...),
    price: float = Form(...),
    buying_price: float = Form(...),
    location_id: int = Form(...),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    loc = db.query(Location).filter(
        Location.id == location_id,
        Location.user_id == current_user.id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Store location not found")

    image_path = None
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        upload_dir = "/tmp/uploads" if os.getenv("VERCEL") else "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = f"/uploads/{filename}"

    new_product = Product(
        user_id=current_user.id,
        location_id=location_id,
        name=name,
        sku=sku,
        stock=stock,
        price=price,
        buying_price=buying_price,
        image_path=image_path
    )
    db.add(new_product)
    db.commit()
    return new_product

@router.put("/api/dashboard/inventory/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    name: str = Form(...),
    sku: str = Form(None),
    stock: int = Form(...),
    price: float = Form(...),
    buying_price: float = Form(...),
    location_id: int = Form(...),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    loc = db.query(Location).filter(
        Location.id == location_id,
        Location.user_id == current_user.id
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Store location not found")

    product.name = name
    product.sku = sku
    product.stock = stock
    product.price = price
    product.buying_price = buying_price
    product.location_id = location_id

    if image and image.filename:
        # Delete old image if exists
        if product.image_path:
            try:
                old_path = product.image_path.lstrip('/')
                if os.getenv("VERCEL"):
                    old_path = old_path.replace("uploads", "/tmp/uploads", 1)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                print(f"Failed to delete old product image: {e}")
                
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        upload_dir = "/tmp/uploads" if os.getenv("VERCEL") else "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        product.image_path = f"/uploads/{filename}"

    db.commit()
    db.refresh(product)
    return product

@router.delete("/api/dashboard/inventory/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete image if exists
    if product.image_path:
        try:
            img_path = product.image_path.lstrip('/')
            if os.getenv("VERCEL"):
                img_path = img_path.replace("uploads", "/tmp/uploads", 1)
            if os.path.exists(img_path):
                os.remove(img_path)
        except Exception as e:
            print(f"Failed to delete product image: {e}")

    db.query(SaleItem).filter(SaleItem.product_id == product_id).delete()

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# --- 5. Reviews Endpoints ---

@router.get("/api/dashboard/reviews", response_model=List[ReviewOut])
def get_reviews(
    location_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Review).filter(Review.user_id == current_user.id)
    if location_id is not None:
        query = query.filter(Review.location_id == location_id)
    return query.order_by(Review.created_at.desc()).all()

@router.put("/api/dashboard/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == current_user.id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    name = payload.get("customer_name")
    rating = payload.get("rating")
    comment = payload.get("comment")
    status_val = payload.get("status")
    
    if name is not None:
        review.customer_name = name
    if rating is not None:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        review.rating = rating
    if comment is not None:
        review.comment = comment
    if status_val is not None:
        review.status = status_val
        
    db.commit()
    db.refresh(review)
    return review

@router.delete("/api/dashboard/reviews/{review_id}")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == current_user.id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    db.delete(review)
    db.commit()
    return {"message": "Review deleted successfully"}

# Public feedback API (No auth required, uses business ID/User ID)
@router.post("/api/public/review/{user_id}")
def post_public_review(
    user_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Business not found")
        
    customer_name = review_data.customer_name.strip()
    if not customer_name:
        raise HTTPException(status_code=400, detail="Customer name cannot be empty")
        
    from sqlalchemy import func
    # Verify the customer has actually bought a product from this business
    sale_exists = db.query(Sale).filter(
        Sale.user_id == user_id,
        Sale.customer_name.isnot(None),
        func.lower(func.trim(Sale.customer_name)) == func.lower(customer_name)
    ).first()
    
    if not sale_exists:
        raise HTTPException(
            status_code=403,
            detail="Reviews are only accepted from verified customers who have made a purchase."
        )
        
    # Check if a review already exists for this business from this customer
    existing_review = db.query(Review).filter(
        Review.user_id == user_id,
        func.lower(func.trim(Review.customer_name)) == func.lower(customer_name)
    ).first()
    
    # Resolve location context
    loc_id = review_data.location_id
    if not loc_id and sale_exists:
        loc_id = sale_exists.location_id

    if existing_review:
        existing_review.rating = review_data.rating
        existing_review.comment = review_data.comment
        existing_review.status = "New"
        existing_review.created_at = datetime.datetime.utcnow()
        if loc_id is not None:
            existing_review.location_id = loc_id
        db.commit()
        db.refresh(existing_review)
        return {"message": "Review updated successfully", "id": existing_review.id}
        
    new_review = Review(
        user_id=user_id,
        customer_name=customer_name,
        rating=review_data.rating,
        comment=review_data.comment,
        status="New",
        location_id=loc_id
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return {"message": "Review submitted successfully", "id": new_review.id}

# --- 6. CRM Endpoints ---

@router.get("/api/dashboard/crm")
def get_crm_leads(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # CRM tracks leads/reviews needing action (e.g. status='New')
    pending_tickets = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).all()
    
    return [
        {
            "id": t.id,
            "customer_name": t.customer_name,
            "rating": t.rating,
            "comment": t.comment,
            "status": t.status,
            "created_at": t.created_at
        } for t in pending_tickets
    ]

@router.put("/api/dashboard/crm/resolve/{review_id}")
def resolve_crm_ticket(
    review_id: int,
    status_update: Dict[str, str], # {"status": "Resolved"/"Replied"}
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Review).filter(
        Review.id == review_id,
        Review.user_id == current_user.id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Lead ticket not found")
        
    new_status = status_update.get("status", "Resolved")
    ticket.status = new_status
    db.commit()
    return {"message": f"Ticket status updated to {new_status}"}

@router.get("/api/dashboard/crm/marketing-analytics")
def get_marketing_analytics(
    location_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Fetch sales and products
    sales_query = db.query(Sale).filter(Sale.user_id == current_user.id)
    if location_id is not None:
        sales_query = sales_query.filter(Sale.location_id == location_id)
    sales = sales_query.all()
    products_db = db.query(Product).filter(Product.user_id == current_user.id).all()
    prod_map = {p.id: p for p in products_db}
    
    # 2. Aggregations
    total_customers = len(set(s.customer_email.lower().strip() for s in sales if s.customer_email))
    total_sales_count = len(sales)
    total_revenue = sum(s.amount for s in sales)
    avg_order_value = round(total_revenue / total_sales_count, 2) if total_sales_count > 0 else 0.0
    
    # Analyze leading products & profit
    product_stats = {} # product_id: {name, sku, units_sold, revenue, profit}
    customer_stats = {} # email: {name, phone, total_spend, total_qty, profit, last_purchased, purchases_count}
    
    total_profit = 0.0
    vip_count = 0
    
    for sale in sales:
        email_key = sale.customer_email.lower().strip() if sale.customer_email else f"guest-{sale.id}"
        
        if email_key not in customer_stats:
            customer_stats[email_key] = {
                "name": sale.customer_name or "Walk-in Customer",
                "email": sale.customer_email or "N/A",
                "phone": sale.customer_phone or "N/A",
                "total_spend": 0.0,
                "total_qty": 0,
                "total_profit": 0.0,
                "last_purchased": sale.timestamp,
                "purchases_count": 0
            }
        
        c = customer_stats[email_key]
        c["purchases_count"] += 1
        if sale.timestamp > c["last_purchased"]:
            c["last_purchased"] = sale.timestamp
        c["total_spend"] += sale.amount
        
        for item in sale.items:
            # Look up product info
            prod = prod_map.get(item.product_id)
            buying_price = prod.buying_price if prod else 0.0
            
            # calculate profit
            item_profit = item.amount - (buying_price * item.quantity)
            total_profit += item_profit
            
            c["total_qty"] += item.quantity
            c["total_profit"] += item_profit
            
            # Product aggregations
            p_id = item.product_id
            if p_id not in product_stats:
                product_stats[p_id] = {
                    "product_id": p_id,
                    "name": item.item_name,
                    "sku": prod.sku if prod else "N/A",
                    "units_sold": 0,
                    "revenue": 0.0,
                    "profit": 0.0
                }
            ps = product_stats[p_id]
            ps["units_sold"] += item.quantity
            ps["revenue"] += item.amount
            ps["profit"] += item_profit

    # Sort leading products by units sold descending
    leading_products = sorted(product_stats.values(), key=lambda x: x["units_sold"], reverse=True)[:10]
    # Sort top customers by spend descending
    top_customers = sorted(customer_stats.values(), key=lambda x: x["total_spend"], reverse=True)[:10]
    
    # Calculate VIP counts (repeat buyers with spend > $150 or count > 1)
    for c in customer_stats.values():
        if c["purchases_count"] > 1 or c["total_spend"] > 150.0:
            vip_count += 1
            
    # Form response timestamps nicely
    for c in top_customers:
        c["last_purchased"] = c["last_purchased"].strftime("%Y-%m-%d %H:%M:%S")
        c["total_spend"] = round(c["total_spend"], 2)
        c["total_profit"] = round(c["total_profit"], 2)
        
    for p in leading_products:
        p["revenue"] = round(p["revenue"], 2)
        p["profit"] = round(p["profit"], 2)
        
    return {
        "metrics": {
            "total_customers": total_customers,
            "avg_order_value": avg_order_value,
            "total_profit": round(total_profit, 2),
            "vip_count": vip_count
        },
        "leading_products": leading_products,
        "top_customers": top_customers
    }

@router.get("/api/dashboard/crm/marketing-segments")
def get_marketing_segments(
    segment: str = "all",
    product_id: Optional[int] = None,
    location_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Fetch user data
    sales_query = db.query(Sale).filter(Sale.user_id == current_user.id)
    if location_id is not None:
        sales_query = sales_query.filter(Sale.location_id == location_id)
    sales = sales_query.all()
    products_db = db.query(Product).filter(Product.user_id == current_user.id).all()
    prod_map = {p.id: p for p in products_db}
    
    # Aggregate customers
    customer_stats = {}
    for sale in sales:
        email_key = sale.customer_email.lower().strip() if sale.customer_email else f"guest-{sale.id}"
        
        if email_key not in customer_stats:
            customer_stats[email_key] = {
                "name": sale.customer_name or "Walk-in Customer",
                "email": sale.customer_email or "N/A",
                "phone": sale.customer_phone or "N/A",
                "total_spend": 0.0,
                "total_qty": 0,
                "total_profit": 0.0,
                "last_purchased": sale.timestamp,
                "purchases_count": 0,
                "bought_products": set()
            }
        
        c = customer_stats[email_key]
        c["purchases_count"] += 1
        if sale.timestamp > c["last_purchased"]:
            c["last_purchased"] = sale.timestamp
        c["total_spend"] += sale.amount
        
        for item in sale.items:
            c["total_qty"] += item.quantity
            c["bought_products"].add(item.product_id)
            
            prod = prod_map.get(item.product_id)
            buying_price = prod.buying_price if prod else 0.0
            item_profit = item.amount - (buying_price * item.quantity)
            c["total_profit"] += item_profit

    # Sort customers by spend descending
    customers = list(customer_stats.values())
    
    # Filter by segment
    filtered_customers = []
    
    if segment == "all":
        filtered_customers = customers
    elif segment == "vip":
        # Spenders with purchases > 1 or spend > 150
        filtered_customers = [c for c in customers if c["purchases_count"] > 1 or c["total_spend"] > 150.0]
    elif segment == "inactive":
        # Inactive segment: last purchased older than 5 days ago (or custom window)
        five_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=5)
        filtered_customers = [c for c in customers if c["last_purchased"] < five_days_ago]
    elif segment == "high_volume":
        # Total qty > 5
        filtered_customers = [c for c in customers if c["total_qty"] > 5]
    elif segment == "product_purchasers":
        if product_id is not None:
            filtered_customers = [c for c in customers if product_id in c["bought_products"]]
        else:
            filtered_customers = customers
            
    # Format and clean up sets
    resp = []
    for c in filtered_customers:
        # Get the name of the last product they bought
        last_product_name = "N/A"
        # Find the latest sale for this customer
        cust_sales = [s for s in sales if (s.customer_email and s.customer_email.lower().strip() == c["email"].lower()) or (not s.customer_email and f"guest-{s.id}" == c["email"])]
        if cust_sales:
            latest_s = max(cust_sales, key=lambda x: x.timestamp)
            if latest_s.items:
                last_product_name = latest_s.items[0].item_name
                
        resp.append({
            "name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "total_spend": round(c["total_spend"], 2),
            "total_profit": round(c["total_profit"], 2),
            "total_qty": c["total_qty"],
            "purchases_count": c["purchases_count"],
            "last_purchased": c["last_purchased"].strftime("%Y-%m-%d %H:%M:%S"),
            "last_product": last_product_name
        })
        
    return resp


@router.post("/api/dashboard/crm/campaigns", response_model=MarketingCampaignOut)
def create_marketing_campaign(
    campaign_data: MarketingCampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = MarketingCampaign(
        user_id=current_user.id,
        name=campaign_data.name,
        segment=campaign_data.segment,
        channel=campaign_data.channel,
        coupon_code=campaign_data.coupon_code,
        discount_type=campaign_data.discount_type,
        discount_value=campaign_data.discount_value,
        message_body=campaign_data.message_body,
        recipients_count=campaign_data.recipients_count
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    if campaign_data.target_emails:
        for email in campaign_data.target_emails:
            email_clean = email.strip().lower()
            if email_clean and email_clean != "n/a" and email_clean != "walkin@example.com":
                tracking = CampaignCustomerTracking(
                    campaign_id=campaign.id,
                    customer_email=email_clean,
                    clicked=False,
                    converted=False
                )
                db.add(tracking)
        db.commit()

    return campaign


@router.get("/api/dashboard/crm/campaigns", response_model=List[MarketingCampaignOut])
def get_marketing_campaigns(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaigns = db.query(MarketingCampaign).filter(
        MarketingCampaign.user_id == current_user.id
    ).order_by(MarketingCampaign.sent_at.desc()).all()
    return campaigns


@router.get("/api/dashboard/crm/campaigns/{campaign_id}/tracking", response_model=List[CampaignCustomerTrackingOut])
def get_campaign_tracking(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(MarketingCampaign).filter(
        MarketingCampaign.id == campaign_id,
        MarketingCampaign.user_id == current_user.id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    trackings = db.query(CampaignCustomerTracking).filter(
        CampaignCustomerTracking.campaign_id == campaign_id
    ).all()

    for t in trackings:
        t.customer_name = "N/A"
        t.sale_amount = 0.0
        t.items_purchased = "N/A"
        if t.sale_id:
            sale = db.query(Sale).filter(Sale.id == t.sale_id).first()
            if sale:
                t.customer_name = sale.customer_name or "Valued Customer"
                t.sale_amount = sale.amount
                if sale.items:
                    t.items_purchased = ", ".join(f"{item.item_name} (x{item.quantity})" for item in sale.items)

    return trackings


@router.get("/api/public/promo/info")
def get_public_promo_info(
    c: int,
    e: str,
    db: Session = Depends(get_db)
):
    email_clean = e.strip().lower()
    campaign = db.query(MarketingCampaign).filter(MarketingCampaign.id == c).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    tracking = db.query(CampaignCustomerTracking).filter(
        CampaignCustomerTracking.campaign_id == c,
        CampaignCustomerTracking.customer_email == email_clean
    ).first()
    
    if not tracking:
        raise HTTPException(status_code=403, detail="Access denied. This promotion page is private and only available to invited customers.")
        
    tracking.clicked = True
    if not tracking.clicked_at:
        tracking.clicked_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(tracking)
    
    owner = db.query(User).filter(User.id == campaign.user_id).first()
    products = db.query(Product).filter(Product.user_id == campaign.user_id).all()
    locations = db.query(Location).filter(Location.user_id == campaign.user_id).all()
    
    return {
        "business_name": owner.business_name,
        "campaign_name": campaign.name,
        "coupon_code": campaign.coupon_code,
        "discount_type": campaign.discount_type,
        "discount_value": campaign.discount_value,
        "customer_email": email_clean,
        "locations": [
            {"id": loc.id, "name": loc.name, "address": loc.address} for loc in locations
        ],
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "stock": p.stock,
                "price": p.price,
                "location_id": p.location_id,
                "image_path": p.image_path
            } for p in products if p.stock > 0
        ]
    }


@router.post("/api/public/promo/buy")
def public_promo_buy(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    campaign_id = payload.get("campaign_id")
    email = payload.get("email")
    location_id = payload.get("location_id")
    customer_name = payload.get("customer_name", "Valued Customer")
    customer_phone = payload.get("customer_phone", "N/A")
    customer_address = payload.get("customer_address")
    
    if not campaign_id or not email or not location_id:
        raise HTTPException(status_code=400, detail="Missing required checkout details")
        
    email_clean = email.strip().lower()
    campaign = db.query(MarketingCampaign).filter(MarketingCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    tracking = db.query(CampaignCustomerTracking).filter(
        CampaignCustomerTracking.campaign_id == campaign_id,
        CampaignCustomerTracking.customer_email == email_clean
    ).first()
    if not tracking:
        raise HTTPException(status_code=403, detail="Verification failed. Invalid promotion access.")
        
    # Standardize items selection
    items_to_process = []
    if "items" in payload:
        items_to_process = payload["items"]
    else:
        product_id = payload.get("product_id")
        quantity = payload.get("quantity", 1)
        if not product_id:
            raise HTTPException(status_code=400, detail="Missing product_id or items array")
        items_to_process = [{"product_id": product_id, "quantity": quantity}]
        
    if not items_to_process:
        raise HTTPException(status_code=400, detail="A sale must contain at least one item.")
        
    total_invoice_amount = 0.0
    sale_items = []
    
    for item_payload in items_to_process:
        pid = item_payload.get("product_id")
        qty = item_payload.get("quantity", 1)
        
        product = db.query(Product).filter(
            Product.id == pid,
            Product.user_id == campaign.user_id
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {pid} not found")
            
        if product.location_id != location_id:
            raise HTTPException(status_code=400, detail=f"Product '{product.name}' does not belong to the selected storefront location")
            
        if product.stock < qty:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product '{product.name}'. Only {product.stock} units available.")
            
        product.stock -= qty
        item_amount = product.price * qty
        total_invoice_amount += item_amount
        
        sale_item = SaleItem(
            product_id=product.id,
            quantity=qty,
            amount=item_amount,
            item_name=product.name
        )
        sale_items.append(sale_item)
        
    # Apply discount
    if campaign.discount_type == "percentage" and campaign.discount_value is not None:
        total_invoice_amount = total_invoice_amount * (1.0 - (campaign.discount_value / 100.0))
    elif campaign.discount_type == "amount" and campaign.discount_value is not None:
        total_invoice_amount = max(0.0, total_invoice_amount - campaign.discount_value)
    total_invoice_amount = round(total_invoice_amount, 2)
    
    loc = db.query(Location).filter(Location.id == location_id).first()
    loc_name = loc.name if loc else "Storefront"
    
    new_sale = Sale(
        user_id=campaign.user_id,
        location_id=location_id,
        amount=total_invoice_amount,
        location=loc_name,
        customer_name=customer_name,
        customer_email=email_clean,
        customer_phone=customer_phone,
        customer_address=customer_address,
        promo_code=campaign.coupon_code,
        items=sale_items
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    
    tracking.converted = True
    tracking.sale_id = new_sale.id
    db.commit()
    
    return {"message": "Purchase successful! Thank you for your order.", "sale_id": new_sale.id}


# --- 7. Customers Endpoints ---

@router.get("/api/dashboard/customers")
def get_customers(
    location_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Compile client patterns from sales
    sales_query = db.query(Sale).filter(Sale.user_id == current_user.id)
    if location_id is not None:
        sales_query = sales_query.filter(Sale.location_id == location_id)
    sales = sales_query.all()
    
    customers_map = {}
    
    for s in sales:
        name = s.customer_name or "Walk-in Customer"
        email = s.customer_email or "walkin@example.com"
        phone = s.customer_phone or "N/A"
        address = s.customer_address or ""
        key = email.strip().lower()
        
        last_item = "N/A"
        if s.items:
            last_item = s.items[-1].item_name
            
        purchases_count = len(s.items)
        
        if key not in customers_map:
            customers_map[key] = {
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "purchases_count": purchases_count,
                "total_spend": s.amount,
                "last_purchased": last_item,
                "promo_campaigns": []
            }
        else:
            customers_map[key]["purchases_count"] += purchases_count
            customers_map[key]["total_spend"] += s.amount
            customers_map[key]["last_purchased"] = last_item
            if address and not customers_map[key]["address"]:
                customers_map[key]["address"] = address

    # Add promo tracking info for each customer email
    for key, c_info in customers_map.items():
        trackings = db.query(CampaignCustomerTracking).filter(
            CampaignCustomerTracking.customer_email == key
        ).all()
        
        promo_campaigns = []
        for t in trackings:
            campaign = db.query(MarketingCampaign).filter(
                MarketingCampaign.id == t.campaign_id,
                MarketingCampaign.user_id == current_user.id
            ).first()
            if campaign:
                promo_campaigns.append({
                    "campaign_name": campaign.name,
                    "coupon_code": campaign.coupon_code,
                    "clicked": t.clicked,
                    "converted": t.converted
                })
        c_info["promo_campaigns"] = promo_campaigns
        
    return list(customers_map.values())

@router.put("/api/dashboard/customers/{old_email}")
def update_customer(
    old_email: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sales = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.customer_email.ilike(old_email.strip())
    ).all()
    
    if not sales:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    new_name = payload.get("name")
    new_email = payload.get("email")
    new_phone = payload.get("phone")
    new_address = payload.get("address")
    
    for s in sales:
        if new_name is not None:
            s.customer_name = new_name
        if new_email is not None:
            s.customer_email = new_email
        if new_phone is not None:
            s.customer_phone = new_phone
        if new_address is not None:
            s.customer_address = new_address
            
    db.commit()
    return {"message": "Customer updated successfully"}

@router.delete("/api/dashboard/customers/{email}")
def delete_customer(
    email: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sales = db.query(Sale).filter(
        Sale.user_id == current_user.id,
        Sale.customer_email.ilike(email.strip())
    ).all()
    
    if not sales:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    for s in sales:
        # Restore product stocks
        for item in s.items:
            product = db.query(Product).filter(
                Product.id == item.product_id,
                Product.user_id == current_user.id
            ).first()
            if product:
                product.stock += item.quantity
        db.delete(s)
        
    db.commit()
    return {"message": "Customer deleted successfully"}

# --- 9. Settings Configuration ---

@router.post("/api/dashboard/settings/toggle")
def toggle_module(
    payload: Dict[str, Any], # {"module_name": "Sales", "is_active": false}
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    mod_name = payload.get("module_name")
    is_active = payload.get("is_active", False)
    
    if mod_name in ["Overview", "Settings"]:
        raise HTTPException(status_code=400, detail="Cannot disable core modules.")
        
    db_mod = db.query(ActiveModule).filter(
        ActiveModule.user_id == current_user.id,
        ActiveModule.module_name == mod_name
    ).first()
    
    if not db_mod:
        db_mod = ActiveModule(user_id=current_user.id, module_name=mod_name, is_active=is_active)
        db.add(db_mod)
    else:
        db_mod.is_active = is_active
        
    db.commit()
    return {"message": f"Module {mod_name} set to active={is_active}"}


@router.post("/api/dashboard/settings/contact")
def create_contact_message(
    payload: ContactMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_msg = ContactMessage(
        user_id=current_user.id,
        category=payload.category,
        subject=payload.subject,
        message=payload.message
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return {"message": "Message sent to administrator successfully!", "message_id": db_msg.id}


@router.get("/api/dashboard/inbox", response_model=List[AdminMessageOut])
def get_inbox_messages(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(AdminMessage).filter(AdminMessage.user_id == current_user.id).order_by(AdminMessage.created_at.desc()).all()


@router.put("/api/dashboard/inbox/read/{message_id}")
def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    msg = db.query(AdminMessage).filter(AdminMessage.id == message_id, AdminMessage.user_id == current_user.id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_read = True
    db.commit()
    return {"message": "Message marked as read"}


@router.delete("/api/dashboard/inbox/{message_id}")
def delete_inbox_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    msg = db.query(AdminMessage).filter(AdminMessage.id == message_id, AdminMessage.user_id == current_user.id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
    return {"message": "Message deleted successfully"}


# --- 10. Operations (Employees, Expenses & Budget) Endpoints ---

@router.get("/api/dashboard/operations/employees", response_model=List[EmployeeOut])
def get_employees(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Employee).filter(Employee.user_id == current_user.id).all()


@router.post("/api/dashboard/operations/employees", response_model=EmployeeOut)
def add_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_emp = Employee(
        user_id=current_user.id,
        name=employee_data.name,
        role=employee_data.role,
        salary=employee_data.salary,
        email=employee_data.email,
        phone=employee_data.phone,
        status=employee_data.status or "Active"
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp


@router.put("/api/dashboard/operations/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: int,
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.user_id == current_user.id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    emp.name = employee_data.name
    emp.role = employee_data.role
    emp.salary = employee_data.salary
    emp.email = employee_data.email
    emp.phone = employee_data.phone
    if employee_data.status is not None:
        emp.status = employee_data.status
        
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/api/dashboard/operations/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.user_id == current_user.id
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(emp)
    db.commit()
    return {"detail": "Employee deleted successfully"}


@router.get("/api/dashboard/operations/expenses", response_model=List[OperationalExpenseOut])
def get_expenses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(OperationalExpense).filter(OperationalExpense.user_id == current_user.id).order_by(OperationalExpense.date.desc()).all()


@router.post("/api/dashboard/operations/expenses", response_model=OperationalExpenseOut)
def add_expense(
    expense_data: OperationalExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_exp = OperationalExpense(
        user_id=current_user.id,
        category=expense_data.category,
        amount=expense_data.amount,
        description=expense_data.description,
        date=datetime.datetime.utcnow()
    )
    db.add(new_exp)
    db.commit()
    db.refresh(new_exp)
    return new_exp


@router.put("/api/dashboard/operations/expenses/{expense_id}", response_model=OperationalExpenseOut)
def update_expense(
    expense_id: int,
    expense_data: OperationalExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    exp = db.query(OperationalExpense).filter(
        OperationalExpense.id == expense_id,
        OperationalExpense.user_id == current_user.id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    exp.category = expense_data.category
    exp.amount = expense_data.amount
    exp.description = expense_data.description
    
    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/api/dashboard/operations/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    exp = db.query(OperationalExpense).filter(
        OperationalExpense.id == expense_id,
        OperationalExpense.user_id == current_user.id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(exp)
    db.commit()
    return {"detail": "Expense deleted successfully"}


@router.get("/api/dashboard/operations/budget")
def get_budget_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sales = db.query(Sale).filter(Sale.user_id == current_user.id).all()
    employees = db.query(Employee).filter(Employee.user_id == current_user.id).all()
    expenses = db.query(OperationalExpense).filter(OperationalExpense.user_id == current_user.id).all()
    
    total_revenue = sum(s.amount for s in sales)
    total_payroll = sum(e.salary for e in employees if e.status == "Active")
    total_expenses = sum(exp.amount for exp in expenses)
    total_spend = total_payroll + total_expenses
    net_profit = total_revenue - total_spend
    
    # Group expenses by category
    expense_categories = {}
    if total_payroll > 0:
        expense_categories["Payroll"] = total_payroll
    for exp in expenses:
        expense_categories[exp.category] = expense_categories.get(exp.category, 0.0) + exp.amount
        
    return {
        "revenue": round(total_revenue, 2),
        "payroll_costs": round(total_payroll, 2),
        "operating_expenses": round(total_expenses, 2),
        "total_spend": round(total_spend, 2),
        "net_profit": round(net_profit, 2),
        "categories": {k: round(v, 2) for k, v in expense_categories.items()}
    }
