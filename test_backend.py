import os
import sys

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force clear DB if exists to start fresh
if os.path.exists("./database.db"):
    try:
        os.remove("./database.db")
    except Exception as e:
        print(f"Could not remove existing database.db: {e}")

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import engine, Base
from backend.models import User
from sqlalchemy.orm import Session

# Create tables
Base.metadata.create_all(bind=engine)

# Clean up test user if exists
db_sess = Session(bind=engine)
existing_user = db_sess.query(User).filter(User.email == "test@business.com").first()
if existing_user:
    db_sess.delete(existing_user)
    db_sess.commit()
db_sess.close()

client = TestClient(app)

def test_workflow():
    print("--- 1. Testing Registration Endpoint ---")
    reg_data = {
        "email": "test@business.com",
        "password": "Securepass123!",
        "business_name": "Test Boutique",
        "industry": "Retail & Boutique"
    }
    res = client.post("/api/auth/register", json=reg_data)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    user_info = res.json()
    assert user_info["email"] == "test@business.com"
    assert user_info["status"] == "pending"
    print("Registration OK! Status is 'pending'.")

    print("\n--- 2. Testing Login for Pending User ---")
    login_data = {
        "email": "test@business.com",
        "password": "Securepass123!"
    }
    res = client.post("/api/auth/login", json=login_data)
    assert res.status_code == 403, f"Expected 403 Forbidden for pending user, got {res.status_code}"
    print("Pending login block OK! Returned 403 Forbidden.")

    print("\n--- 3. Testing Admin Login ---")
    # Using defaults since we didn't override .env in the test environment
    admin_data = {
        "username": "admin",
        "password": "adminpass123"
    }
    res = client.post("/api/auth/admin-login", json=admin_data)
    assert res.status_code == 200, f"Admin Login failed: {res.text}"
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("Admin login OK!")

    print("\n--- 4. Testing Admin Listing Users ---")
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200, f"User list fetch failed: {res.text}"
    users = res.json()
    assert len(users) >= 1, "No users returned"
    target_user = [u for u in users if u["email"] == "test@business.com"][0]
    user_id = target_user["id"]
    print(f"User search OK! Found target user with ID {user_id}.")

    print("\n--- 5. Testing Admin Approving User ---")
    res = client.post(f"/api/admin/approve/{user_id}", headers=admin_headers)
    assert res.status_code == 200, f"User approval failed: {res.text}"
    print("User approved OK!")

    print("\n--- 6. Testing Login for Approved User ---")
    res = client.post("/api/auth/login", json=login_data)
    assert res.status_code == 200, f"Login failed for approved user: {res.text}"
    token_resp = res.json()
    user_token = token_resp["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    assert token_resp["status"] == "approved"
    print("Approved user login OK! Token generated.")

    print("\n--- 7. Testing Onboarding Questions Generation ---")
    res = client.get("/api/onboarding/questions", headers=user_headers)
    assert res.status_code == 200, f"Questions generation failed: {res.text}"
    questions_data = res.json()
    assert "questions" in questions_data
    assert len(questions_data["questions"]) == 6
    print("Onboarding Questions generation OK!")

    print("\n--- 8. Testing Onboarding Submission & Custom Module Selection ---")
    answers_payload = {
        "answers": {
            "Analytics": "yes",
            "Sales": "yes",
            "Inventory": "yes",
            "Reviews": "yes",
            "CRM": "yes",
            "Customers": "yes"
        }
    }
    res = client.post("/api/onboarding/submit", json=answers_payload, headers=user_headers)
    assert res.status_code == 200, f"Onboarding submit failed: {res.text}"
    submit_resp = res.json()
    assert "active_modules" in submit_resp
    # Verify customized module mapping works correctly
    assert "Sales" in submit_resp["active_modules"]
    assert "Inventory" in submit_resp["active_modules"]
    print("Onboarding submission OK! Active modules configured by user selections.")

    print("\n--- 9. Testing Dashboard Integration Endpoints ---")
    # Fetch overview data
    res = client.get("/api/dashboard/overview", headers=user_headers)
    assert res.status_code == 200, f"Overview retrieval failed: {res.text}"
    overview = res.json()
    assert overview["user_id"] == user_id
    assert overview["business_name"] == "Test Boutique"
    assert "metrics" in overview
    print("Overview metrics OK!")
    # Test adding location
    loc_data = {
        "name": "New York Store"
    }
    res = client.post("/api/dashboard/locations", json=loc_data, headers=user_headers)
    assert res.status_code == 200, f"Location creation failed: {res.text}"
    location = res.json()
    loc_id = location["id"]
    print("Store location creation OK!")
    # Test adding product (Inventory)
    prod_data = {
        "name": "Bluetooth Speaker",
        "sku": "BT-SPK-99",
        "buying_price": "25.00",
        "price": "49.99",
        "stock": "45",
        "location_id": str(loc_id)
    }
    res = client.post("/api/dashboard/inventory", data=prod_data, headers=user_headers)
    assert res.status_code == 200, f"Product insert failed: {res.text}"
    product = res.json()
    prod_id = product["id"]
    assert product["buying_price"] == 25.00
    print("Product inventory addition OK!")
    # Test adding sale (Sales)
    sale_data = {
        "location_id": loc_id,
        "customer_name": "Bob Vance",
        "customer_email": "bob@vancerefrigeration.com",
        "customer_phone": "+1 555-0199",
        "items": [
            {
                "product_id": prod_id,
                "quantity": 1
            }
        ]
    }
    res = client.post("/api/dashboard/sales", json=sale_data, headers=user_headers)
    assert res.status_code == 200, f"Sale insert failed: {res.text}"
    sale_info = res.json()
    assert sale_info["customer_phone"] == "+1 555-0199"
    print("Sales log insertion OK!")
    # Test product stock decrement
    res = client.get("/api/dashboard/inventory", headers=user_headers)
    assert res.status_code == 200
    products = res.json()
    db_product = [p for p in products if p["id"] == prod_id][0]
    assert db_product["stock"] == 44, f"Expected stock to decrement to 44, got {db_product['stock']}"
    print("Product stock decrement check OK!")

    # Test Customer phone number listing in Customer Directories
    res = client.get("/api/dashboard/customers", headers=user_headers)
    assert res.status_code == 200, f"Customers fetch failed: {res.text}"
    customers = res.json()
    matching_cust = [c for c in customers if c["email"] == "bob@vancerefrigeration.com"][0]
    assert matching_cust["phone"] == "+1 555-0199", f"Expected bob's phone to be '+1 555-0199', got {matching_cust['phone']}"
    print("Customer phone directory storage OK!")
    # Test customer review feedback - Reject non-purchaser
    non_buyer_feedback = {
        "customer_name": "Stranger Danger",
        "rating": 1,
        "comment": "Nice place?"
    }
    res = client.post(f"/api/public/review/{user_id}", json=non_buyer_feedback)
    assert res.status_code == 403, f"Expected 403 for non-buyer review, got {res.status_code}"
    print("Non-purchaser review rejection OK!")

    # Test customer review feedback (Public submission) - Accept valid purchaser
    feedback_data = {
        "customer_name": "Bob Vance",
        "rating": 5,
        "comment": "Best boutique around!"
    }
    res = client.post(f"/api/public/review/{user_id}", json=feedback_data)
    assert res.status_code == 200, f"Public review failed: {res.text}"
    print("Public customer feedback submission OK!")

    # Verify review syncs with reviews listing
    res = client.get("/api/dashboard/reviews", headers=user_headers)
    assert res.status_code == 200, f"Reviews list fetch failed: {res.text}"
    reviews = res.json()
    assert len(reviews) == 1, f"Expected 1 review, got {len(reviews)}"
    latest_review = reviews[0]
    assert latest_review["customer_name"] == "Bob Vance"
    assert latest_review["rating"] == 5
    assert latest_review["comment"] == "Best boutique around!"
    print("Review synchronization OK!")

    # Test customer review feedback - Update duplicate review instead of inserting new
    duplicate_feedback = {
        "customer_name": "  Bob Vance  ",  # with trailing spaces to test trimming
        "rating": 4,
        "comment": "Actually, 4 stars only."
    }
    res = client.post(f"/api/public/review/{user_id}", json=duplicate_feedback)
    assert res.status_code == 200, f"Public duplicate review failed: {res.text}"
    print("Public customer duplicate review update OK!")

    # Verify review was updated, and no new review was added
    res = client.get("/api/dashboard/reviews", headers=user_headers)
    assert res.status_code == 200
    reviews = res.json()
    assert len(reviews) == 1, f"Expected exactly 1 review after duplicate post, got {len(reviews)}"
    updated_review = reviews[0]
    assert updated_review["customer_name"] == "Bob Vance"
    assert updated_review["rating"] == 4
    assert updated_review["comment"] == "Actually, 4 stars only."
    print("Duplicate review update verification OK!")

    # Test CRM listing contains the new review
    res = client.get("/api/dashboard/crm", headers=user_headers)
    assert res.status_code == 200, f"CRM tickets fetch failed: {res.text}"
    tickets = res.json()
    matching_ticket = [t for t in tickets if t["customer_name"] == "Bob Vance"][0]
    ticket_id = matching_ticket["id"]
    assert matching_ticket["status"] == "New"
    print("CRM Ticket creation from review OK!")

    # Resolve CRM ticket
    res = client.put(f"/api/dashboard/crm/resolve/{ticket_id}", json={"status": "Resolved"}, headers=user_headers)
    assert res.status_code == 200, f"CRM resolve ticket failed: {res.text}"
    print("CRM Ticket resolution OK!")

    print("\n--- 10. Testing Settings Contact Support Endpoint ---")
    contact_data = {
        "category": "Billing Query",
        "subject": "Invoice missing for last month",
        "message": "Hi Admin, we didn't receive our invoice for June 2026. Please check."
    }
    res = client.post("/api/dashboard/settings/contact", json=contact_data, headers=user_headers)
    assert res.status_code == 200, f"Contact submission failed: {res.text}"
    contact_resp = res.json()
    assert "message_id" in contact_resp
    print("Contact support message submission OK!")
    print("\n--- 11. Testing Admin Retrieving Support Messages ---")
    res = client.get("/api/admin/support-messages", headers=admin_headers)
    assert res.status_code == 200, f"Support message retrieval failed: {res.text}"
    support_messages = res.json()
    assert len(support_messages) >= 1, "No support messages returned"
    target_msg = [m for m in support_messages if m["subject"] == "Invoice missing for last month"][0]
    msg_id = target_msg["id"]
    assert target_msg["status"] == "New"
    assert target_msg["business_name"] == "Test Boutique"
    print("Admin Support Messages Retrieval OK!")

    print("\n--- 12. Testing Admin Replying to Support Message ---")
    reply_payload = {
        "subject": "Re: Invoice missing for last month",
        "message": "Hi, we have sent the invoice to test@business.com. Please check your spam folder."
    }
    res = client.post(f"/api/admin/support-messages/reply/{msg_id}", json=reply_payload, headers=admin_headers)
    assert res.status_code == 200, f"Support reply failed: {res.text}"
    reply_resp = res.json()
    assert "reply_id" in reply_resp
    print("Admin Support Reply OK!")

    # Verify status changed to Replied
    res = client.get("/api/admin/support-messages", headers=admin_headers)
    support_messages = res.json()
    target_msg = [m for m in support_messages if m["id"] == msg_id][0]
    assert target_msg["status"] == "Replied"
    print("Support Message Status Updated to 'Replied' OK!")

    print("\n--- 13. Testing Shop Retrieving Admin Reply from Inbox ---")
    res = client.get("/api/dashboard/inbox", headers=user_headers)
    assert res.status_code == 200, f"Inbox fetch failed: {res.text}"
    inbox_messages = res.json()
    assert len(inbox_messages) == 1
    reply_inbox_msg = inbox_messages[0]
    assert reply_inbox_msg["subject"] == "Re: Invoice missing for last month"
    assert reply_inbox_msg["is_read"] is False
    admin_msg_id = reply_inbox_msg["id"]
    print("Shop Inbox Retrieve OK!")

    print("\n--- 14. Testing Shop Marking Inbox Message as Read ---")
    res = client.put(f"/api/dashboard/inbox/read/{admin_msg_id}", headers=user_headers)
    assert res.status_code == 200
    res = client.get("/api/dashboard/inbox", headers=user_headers)
    inbox_messages = res.json()
    assert inbox_messages[0]["is_read"] is True
    print("Shop Mark Message Read OK!")

    print("\n--- 15. Testing Shop Deleting Inbox Message ---")
    res = client.delete(f"/api/dashboard/inbox/{admin_msg_id}", headers=user_headers)
    assert res.status_code == 200
    res = client.get("/api/dashboard/inbox", headers=user_headers)
    assert len(res.json()) == 0
    print("Shop Delete Message OK!")

    print("\n--- 16. Testing Admin Sending Direct Message to Shop ---")
    dm_payload = {
        "subject": "Urgent Maintenance Notice",
        "message": "We will have server maintenance tonight."
    }
    res = client.post(f"/api/admin/message/{user_id}", json=dm_payload, headers=admin_headers)
    assert res.status_code == 200, f"Direct message dispatch failed: {res.text}"
    print("Admin Direct Message Dispatch OK!")

    print("\n--- 17. Testing CRM Creating Marketing Campaign Log ---")
    campaign_payload = {
        "name": "Summer Special Offer",
        "segment": "VIP Spenders",
        "channel": "email",
        "coupon_code": "SUMMER15",
        "message_body": "Hi {name}, enjoy 15% off!",
        "recipients_count": 3
    }
    res = client.post("/api/dashboard/crm/campaigns", json=campaign_payload, headers=user_headers)
    assert res.status_code == 200, f"Campaign creation failed: {res.text}"
    campaign_data = res.json()
    assert campaign_data["name"] == "Summer Special Offer"
    assert campaign_data["coupon_code"] == "SUMMER15"
    campaign_id = campaign_data["id"]
    print("CRM Campaign Creation OK!")

    print("\n--- 18. Testing CRM Fetching Marketing Campaigns History ---")
    res = client.get("/api/dashboard/crm/campaigns", headers=user_headers)
    assert res.status_code == 200
    campaigns_history = res.json()
    assert len(campaigns_history) >= 1
    assert campaigns_history[0]["id"] == campaign_id
    print("CRM Campaign History Retrieval OK!")

    print("\n--- 19. Testing Admin Deleting Shop (Cascade Delete) ---")
    res = client.delete(f"/api/admin/shop/{user_id}", headers=admin_headers)
    assert res.status_code == 200, f"Shop deletion failed: {res.text}"
    print("Admin Shop Deletion OK!")

    print("\n--- 20. Verifying Cascade Deletion & Auth Block ---")
    # Login should now fail since shop doesn't exist
    res = client.post("/api/auth/login", json=login_data)
    assert res.status_code == 401, f"Expected unauthorized, got {res.status_code}"
    
    # Verify in DB that campaigns were cascade deleted
    from backend.models import MarketingCampaign
    db_sess = Session(bind=engine)
    campaign_exists = db_sess.query(MarketingCampaign).filter(MarketingCampaign.user_id == user_id).first()
    assert campaign_exists is None, "Campaign record was not cascade deleted"
    db_sess.close()
    print("Cascade Deletion Verification OK!")


    print("\n==========================================")
    print("ALL API WORKFLOW TESTS COMPLETED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_workflow()
