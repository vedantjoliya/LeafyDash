import datetime
from fastapi.testclient import TestClient
import os
import sys

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.database import SessionLocal, get_db
from backend.models import User, MarketingCampaign, Sale, Location, Product, CampaignCustomerTracking

client = TestClient(app)

def setup_test_data():
    db = SessionLocal()
    # Find or create a test user
    user = db.query(User).filter(User.email == "contactsvedant@gmail.com").first()
    if not user:
        user = User(
            email="contactsvedant@gmail.com",
            password_hash="fakehash",
            business_name="Test Garden Shop",
            industry="Gardening",
            status="onboarded"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Find or create storefront location
    loc = db.query(Location).filter(Location.user_id == user.id).first()
    if not loc:
        loc = Location(
            user_id=user.id,
            name="Green Oasis",
            address="123 Plant Road"
        )
        db.add(loc)
        db.commit()
        db.refresh(loc)

    # Find or create product
    prod = db.query(Product).filter(Product.user_id == user.id).first()
    if not prod:
        prod = Product(
            user_id=user.id,
            location_id=loc.id,
            name="Fern",
            price=20.0,
            stock=100
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)

    db.close()
    return user.id, loc.id, prod.id

def test_campaign_validation():
    user_id, loc_id, prod_id = setup_test_data()
    print("[Test] Setting up mock campaigns for testing...")

    # Clean up previous runs to avoid test-pollution on customer spend counts
    db = SessionLocal()
    test_emails = ["bruce@wayne.com", "clark@kent.com", "diana@prince.com", "peter@parker.com"]
    for email in test_emails:
        sales_to_delete = db.query(Sale).filter(Sale.customer_email == email).all()
        for s in sales_to_delete:
            db.delete(s)
        trackings_to_delete = db.query(CampaignCustomerTracking).filter(CampaignCustomerTracking.customer_email == email).all()
        for t in trackings_to_delete:
            db.delete(t)
    db.commit()
    db.close()

    # Log in to get token
    login_res = client.post("/api/auth/login", json={
        "email": "contactsvedant@gmail.com",
        "password": "Joliya@283"
    })
    
    if login_res.status_code != 200:
        print("[Error] Login failed for contactsvedant@gmail.com. Please make sure the user exists and has this password.")
        return False

    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a stopped/inactive campaign
    print("\n--- 1. Testing Stopped Campaign Validation ---")
    c1_payload = {
        "name": "Stopped Promo Campaign",
        "segment": "All Customers",
        "channel": "email",
        "coupon_code": "STOPPED10",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "message_body": "This is stopped {tracking_link}",
        "recipients_count": 1,
        "target_emails": ["bruce@wayne.com"]
    }
    res = client.post("/api/dashboard/crm/campaigns", json=c1_payload, headers=headers)
    assert res.status_code == 200, res.text
    campaign1 = res.json()
    c1_id = campaign1["id"]

    # Stop the campaign
    res = client.post(f"/api/dashboard/crm/campaigns/{c1_id}/stop", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "stopped"
    print("Campaign successfully toggled to 'stopped' status.")

    # Try validating/applying the coupon code - should fail with 400
    res = client.get("/api/dashboard/sales/validate-promo?code=STOPPED10", headers=headers)
    print(f"Check coupon response for stopped campaign: Code={res.status_code}, Body={res.json()}")
    assert res.status_code == 400
    assert "stopped" in res.json()["detail"]

    # Try checking out using the promo storefront route - should fail with 400
    checkout_payload = {
        "campaign_id": c1_id,
        "email": "bruce@wayne.com",
        "location_id": loc_id,
        "customer_name": "Bruce Wayne",
        "customer_phone": "123-456",
        "customer_address": "Wayne Manor, Gotham",
        "product_id": prod_id,
        "quantity": 1
    }
    res = client.post("/api/public/promo/buy", json=checkout_payload)
    print(f"Public checkout response for stopped campaign: Code={res.status_code}, Body={res.json()}")
    assert res.status_code == 400
    assert "stopped" in res.json()["detail"]

    # 2. Create a future start campaign
    print("\n--- 2. Testing Future Start Campaign Validation ---")
    future_start = (datetime.datetime.utcnow() + datetime.timedelta(days=2)).isoformat()
    future_end = (datetime.datetime.utcnow() + datetime.timedelta(days=5)).isoformat()
    c2_payload = {
        "name": "Future Promo Campaign",
        "segment": "All Customers",
        "channel": "email",
        "coupon_code": "FUTURE20",
        "discount_type": "percentage",
        "discount_value": 20.0,
        "message_body": "This starts in the future {tracking_link}",
        "recipients_count": 1,
        "target_emails": ["clark@kent.com"],
        "start_date": future_start,
        "end_date": future_end
    }
    res = client.post("/api/dashboard/crm/campaigns", json=c2_payload, headers=headers)
    assert res.status_code == 200, res.text
    campaign2 = res.json()
    c2_id = campaign2["id"]

    # Try validating/applying the coupon code - should fail with 400
    res = client.get("/api/dashboard/sales/validate-promo?code=FUTURE20", headers=headers)
    print(f"Check coupon response for future start campaign: Code={res.status_code}, Body={res.json()}")
    assert res.status_code == 400
    assert "not started yet" in res.json()["detail"]

    # 3. Create a past end campaign
    print("\n--- 3. Testing Past End Campaign Validation ---")
    past_start = (datetime.datetime.utcnow() - datetime.timedelta(days=5)).isoformat()
    past_end = (datetime.datetime.utcnow() - datetime.timedelta(days=2)).isoformat()
    c3_payload = {
        "name": "Expired Promo Campaign",
        "segment": "All Customers",
        "channel": "email",
        "coupon_code": "EXPIRED30",
        "discount_type": "percentage",
        "discount_value": 30.0,
        "message_body": "This has expired {tracking_link}",
        "recipients_count": 1,
        "target_emails": ["diana@prince.com"],
        "start_date": past_start,
        "end_date": past_end
    }
    res = client.post("/api/dashboard/crm/campaigns", json=c3_payload, headers=headers)
    assert res.status_code == 200, res.text
    campaign3 = res.json()
    c3_id = campaign3["id"]

    # Try validating/applying the coupon code - should fail with 400
    res = client.get("/api/dashboard/sales/validate-promo?code=EXPIRED30", headers=headers)
    print(f"Check coupon response for expired campaign: Code={res.status_code}, Body={res.json()}")
    assert res.status_code == 400
    assert "expired" in res.json()["detail"]

    # 4. Create an active campaign and test New vs Returning Customer Tracking
    print("\n--- 4. Testing Active Campaign & Customer Cohorts (New vs Returning) ---")
    active_start = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat()
    active_end = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
    c4_payload = {
        "name": "Active Promo Campaign",
        "segment": "All Customers",
        "channel": "email",
        "coupon_code": "ACTIVE40",
        "discount_type": "percentage",
        "discount_value": 40.0,
        "message_body": "Active offer {tracking_link}",
        "recipients_count": 1,
        "target_emails": ["peter@parker.com"],
        "start_date": active_start,
        "end_date": active_end
    }
    res = client.post("/api/dashboard/crm/campaigns", json=c4_payload, headers=headers)
    assert res.status_code == 200, res.text
    campaign4 = res.json()
    c4_id = campaign4["id"]

    # Try validating/applying the coupon code - should succeed!
    res = client.get("/api/dashboard/sales/validate-promo?code=ACTIVE40", headers=headers)
    print(f"Check coupon response for active campaign: Code={res.status_code}, Body={res.json()}")
    assert res.status_code == 200
    assert res.json()["coupon_code"] == "ACTIVE40"

    # Make first purchase using the promo storefront route
    checkout_payload = {
        "campaign_id": c4_id,
        "email": "peter@parker.com",
        "location_id": loc_id,
        "customer_name": "Peter Parker",
        "customer_phone": "555-SPIDY",
        "customer_address": "Queens, New York",
        "product_id": prod_id,
        "quantity": 1
    }
    res = client.post("/api/public/promo/buy", json=checkout_payload)
    print(f"First purchase (New Customer) response: Code={res.status_code}, Body={res.json()}")
    assert res.status_code == 200
    
    # Retrieve logs and confirm they flag Peter Parker as a NEW customer
    res = client.get(f"/api/dashboard/crm/campaigns/{c4_id}/tracking", headers=headers)
    tracking_logs = res.json()
    peter_log = [l for l in tracking_logs if l["customer_email"] == "peter@parker.com"][0]
    print(f"Peter Parker tracking log: name={peter_log['customer_name']}, converted={peter_log['converted']}, is_new_customer={peter_log['is_new_customer']}")
    assert peter_log["converted"] is True
    assert peter_log["is_new_customer"] is True

    # Make second purchase (simulate returning customer with another manual sale or purchase)
    # Log a manual sale for Peter Parker
    manual_sale_payload = {
        "location_id": loc_id,
        "customer_name": "Peter Parker",
        "customer_email": "peter@parker.com",
        "customer_phone": "555-SPIDY",
        "customer_address": "Queens, New York",
        "items": [{"product_id": prod_id, "quantity": 1}]
    }
    res = client.post("/api/dashboard/sales", json=manual_sale_payload, headers=headers)
    assert res.status_code == 200

    # Retrieve tracking logs again. Now sales count for Peter Parker is 2, so is_new_customer should become False
    res = client.get(f"/api/dashboard/crm/campaigns/{c4_id}/tracking", headers=headers)
    tracking_logs = res.json()
    peter_log = [l for l in tracking_logs if l["customer_email"] == "peter@parker.com"][0]
    print(f"Peter Parker tracking log (after 2nd purchase): is_new_customer={peter_log['is_new_customer']}")
    assert peter_log["is_new_customer"] is False

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    test_campaign_validation()
