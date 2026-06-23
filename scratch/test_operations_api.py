import sys
import os
import json
from fastapi.testclient import TestClient

# Ensure python can find backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database import SessionLocal, engine, Base
from backend.models import User, ActiveModule, Location, Product, Sale, SaleItem, Employee, OperationalExpense

client = TestClient(app)

def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(SaleItem).delete()
    db.query(Sale).delete()
    db.query(Product).delete()
    db.query(Location).delete()
    db.query(Employee).delete()
    db.query(OperationalExpense).delete()
    db.query(ActiveModule).delete()
    db.query(User).delete()
    db.commit()
    db.close()

def test_operations_and_promo_flow():
    setup_db()
    
    # 1. Register a test user
    reg_payload = {
        "email": "owner@leafydash.com",
        "password": "Password123!",
        "business_name": "Leafy Dash Inc",
        "industry": "Retail"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200, res.text
    
    # Approve user via admin simulation
    db = SessionLocal()
    user = db.query(User).filter(User.email == "owner@leafydash.com").first()
    user.status = "approved"
    db.commit()
    db.close()
    
    # Login to get token
    login_payload = {
        "email": "owner@leafydash.com",
        "password": "Password123!"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Add Employee
    emp_payload = {
        "name": "Jane Miller",
        "role": "Operations Lead",
        "salary": 4500.00,
        "email": "jane@leafydash.com",
        "phone": "+1 555-1234",
        "status": "Active"
    }
    res = client.post("/api/dashboard/operations/employees", json=emp_payload, headers=headers)
    assert res.status_code == 200, res.text
    emp_id = res.json()["id"]
    assert res.json()["name"] == "Jane Miller"
    assert res.json()["salary"] == 4500.00
    
    # List Employees
    res = client.get("/api/dashboard/operations/employees", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    
    # Update Employee
    emp_payload["salary"] = 4800.00
    res = client.put(f"/api/dashboard/operations/employees/{emp_id}", json=emp_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["salary"] == 4800.00
    
    # 3. Add Expense
    exp_payload = {
        "category": "Rent",
        "amount": 1200.00,
        "description": "Office rent June"
    }
    res = client.post("/api/dashboard/operations/expenses", json=exp_payload, headers=headers)
    assert res.status_code == 200, res.text
    exp_id = res.json()["id"]
    assert res.json()["category"] == "Rent"
    assert res.json()["amount"] == 1200.00
    
    # List Expenses
    res = client.get("/api/dashboard/operations/expenses", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    
    # Update Expense
    exp_payload["amount"] = 1250.00
    res = client.put(f"/api/dashboard/operations/expenses/{exp_id}", json=exp_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["amount"] == 1250.00
    
    # 4. Check Budget Endpoint
    res = client.get("/api/dashboard/operations/budget", headers=headers)
    assert res.status_code == 200, res.text
    budget = res.json()
    assert budget["payroll_costs"] == 4800.00
    assert budget["operating_expenses"] == 1250.00
    assert budget["total_spend"] == 6050.00
    assert budget["net_profit"] == -6050.00 # No revenue yet
    
    # 5. Set up location and products for Promo Storefront purchase
    loc_res = client.post("/api/dashboard/locations", json={"name": "West Side Branch", "address": "456 West Blvd"}, headers=headers)
    loc_id = loc_res.json()["id"]
    
    prod_payload_1 = {
        "name": "Organic Fertilizer",
        "sku": "FERT-ORG-01",
        "stock": 50,
        "price": 25.00,
        "buying_price": 10.00,
        "location_id": loc_id
    }
    p1_res = client.post("/api/dashboard/inventory", data=prod_payload_1, headers=headers)
    p1_id = p1_res.json()["id"]
    
    prod_payload_2 = {
        "name": "Pruning Shears",
        "sku": "SHEAR-PRN-02",
        "stock": 30,
        "price": 40.00,
        "buying_price": 18.00,
        "location_id": loc_id
    }
    p2_res = client.post("/api/dashboard/inventory", data=prod_payload_2, headers=headers)
    p2_id = p2_res.json()["id"]
    
    # 6. Create Marketing Campaign to get tracking context
    camp_payload = {
        "name": "Summer Greenery Promo",
        "segment": "all",
        "channel": "email",
        "coupon_code": "SUMMER10",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "message_body": "Buy multiple garden products with 10% off!",
        "recipients_count": 1,
        "target_emails": ["customer@example.com"]
    }
    res = client.post("/api/dashboard/crm/campaigns", json=camp_payload, headers=headers)
    assert res.status_code == 200, res.text
    camp_id = res.json()["id"]
    
    # Verify tracking clicks (simulated public info route)
    res = client.get(f"/api/public/promo/info?c={camp_id}&e=customer@example.com")
    assert res.status_code == 200, res.text
    
    # 7. Test Multi-item buy storefront checkout
    buy_payload = {
        "campaign_id": camp_id,
        "email": "customer@example.com",
        "location_id": loc_id,
        "customer_name": "Bob Green",
        "customer_phone": "+1 555-9876",
        "customer_address": "789 Pine Rd, Seattle WA",
        "items": [
            {"product_id": p1_id, "quantity": 2}, # 2 x 25 = 50
            {"product_id": p2_id, "quantity": 1}  # 1 x 40 = 40. Total = 90. Discount 10% = 81.
        ]
    }
    res = client.post("/api/public/promo/buy", json=buy_payload)
    assert res.status_code == 200, res.text
    
    # Verify products stock decremented
    res = client.get("/api/dashboard/inventory", headers=headers)
    products = res.json()
    p1 = next(p for p in products if p["id"] == p1_id)
    p2 = next(p for p in products if p["id"] == p2_id)
    assert p1["stock"] == 48
    assert p2["stock"] == 29
    
    # Verify sale amount and customer address logged
    res = client.get("/api/dashboard/sales", headers=headers)
    sales = res.json()
    assert len(sales) == 1
    assert sales[0]["amount"] == 81.00
    assert sales[0]["customer_address"] == "789 Pine Rd, Seattle WA"
    
    # Verify customer list aggregates address
    res = client.get("/api/dashboard/customers", headers=headers)
    customers = res.json()
    assert len(customers) == 1
    assert customers[0]["address"] == "789 Pine Rd, Seattle WA"
    
    # 8. Update Customer Address & Details
    update_cust_payload = {
        "name": "Robert Green",
        "email": "customer@example.com",
        "phone": "+1 555-9876",
        "address": "999 Oak St, Portland OR"
    }
    res = client.put("/api/dashboard/customers/customer@example.com", json=update_cust_payload, headers=headers)
    assert res.status_code == 200, res.text
    
    # Verify address updated on sales log & customer aggregate
    res = client.get("/api/dashboard/sales", headers=headers)
    assert res.json()[0]["customer_address"] == "999 Oak St, Portland OR"
    assert res.json()[0]["customer_name"] == "Robert Green"
    
    res = client.get("/api/dashboard/customers", headers=headers)
    assert res.json()[0]["address"] == "999 Oak St, Portland OR"
    assert res.json()[0]["name"] == "Robert Green"
    
    # 9. Verify budget updated with revenue
    res = client.get("/api/dashboard/operations/budget", headers=headers)
    budget = res.json()
    assert budget["revenue"] == 81.00
    assert budget["net_profit"] == round(81.00 - 6050.00, 2)
    
    # 10. Delete Employee and verify budget recalculates
    client.delete(f"/api/dashboard/operations/employees/{emp_id}", headers=headers)
    res = client.get("/api/dashboard/operations/budget", headers=headers)
    budget = res.json()
    assert budget["payroll_costs"] == 0.0
    assert budget["total_spend"] == 1250.00
    assert budget["net_profit"] == round(81.00 - 1250.00, 2)

    print("\nALL INTEGRATION AND CRITICAL FLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_operations_and_promo_flow()
