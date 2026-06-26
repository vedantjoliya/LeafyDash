import os
import sys
import httpx
from fastapi.testclient import TestClient

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Define a hybrid API Client that supports running against a live uvicorn server 
# OR falling back to fastapi.testclient.TestClient in-process.
class APIClient:
    def __init__(self, base_url=None, app=None):
        self.base_url = base_url
        self.app = app
        if base_url:
            self.client = httpx.Client(base_url=base_url)
            self.mode = "LIVE (HTTP)"
        else:
            self.client = TestClient(app)
            self.mode = "TEST_CLIENT (Local DB)"

    def post(self, url, json=None, data=None, headers=None):
        # Handle form data / multipart for product image uploading
        return self.client.post(url, json=json, data=data, headers=headers)

    def get(self, url, headers=None):
        return self.client.get(url, headers=headers)

    def delete(self, url, headers=None):
        return self.client.delete(url, headers=headers)

def run_automation():
    print("==================================================")
    print("      Leafy Dash Database Automation Script       ")
    print("==================================================")

    # 1. Detect environment / connect client
    base_url = "http://127.0.0.1:8000"
    client = None

    try:
        # Check if live server is reachable
        resp = httpx.get(f"{base_url}/")
        print(f"[Mode] Connected to running uvicorn server at {base_url}!")
        client = APIClient(base_url=base_url)
    except Exception:
        print("[Mode] Live server not reachable. Running locally in-process against database.db...")
        # Import app here so we don't trigger DB locks unless needed
        from backend.main import app
        client = APIClient(app=app)

    # User details
    email = "contactsvedant@gmail.com"
    password = "Joliya@283"

    # Try Logging in
    print(f"\n1. Authenticating as user '{email}'...")
    login_payload = {"email": email, "password": password}
    login_res = client.post("/api/auth/login", json=login_payload)

    user_token = None
    user_status = None

    if login_res.status_code == 200:
        login_data = login_res.json()
        user_token = login_data["access_token"]
        user_status = login_data["status"]
        print(f"Logged in successfully! (Account status: {user_status})")
    elif login_res.status_code in (401, 404, 403):
        # Register user if not exists or approved
        if login_res.status_code in (401, 404):
            print(f"User not found. Registering '{email}'...")
            reg_payload = {
                "email": email,
                "password": password,
                "business_name": "LeafyDash Garden Co",
                "industry": "E-Commerce & Online Sales"
            }
            reg_res = client.post("/api/auth/register", json=reg_payload)
            if reg_res.status_code != 200:
                print(f"Registration failed: {reg_res.text}")
                return

        # Login as Admin to Approve
        print("Logging in as Administrator to approve the account...")
        admin_login = client.post("/api/auth/admin-login", json={"username": "admin", "password": "adminpass123"})
        if admin_login.status_code != 200:
            print(f"Admin login failed: {admin_login.text}")
            return
        
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Find target user ID
        users_res = client.get("/api/admin/users", headers=admin_headers)
        if users_res.status_code != 200:
            print(f"Failed to list users: {users_res.text}")
            return
        
        user_id = None
        for u in users_res.json():
            if u["email"] == email:
                user_id = u["id"]
                break
        
        if not user_id:
            print(f"Could not find user with email '{email}' in admin dashboard.")
            return

        # Approve user
        print(f"Approving user ID {user_id}...")
        approve_res = client.post(f"/api/admin/approve/{user_id}", headers=admin_headers)
        if approve_res.status_code != 200:
            print(f"Approval failed: {approve_res.text}")
            return
        print("Account approved by administrator!")

        # Log in again
        login_res = client.post("/api/auth/login", json=login_payload)
        login_data = login_res.json()
        user_token = login_data["access_token"]
        user_status = login_data["status"]

    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Onboarding check
    if user_status == "approved":
        print("\nCompleting onboarding module setup...")
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
        onboard_res = client.post("/api/onboarding/submit", json=answers_payload, headers=user_headers)
        if onboard_res.status_code != 200:
            print(f"Onboarding failed: {onboard_res.text}")
            return
        print("Onboarding completed successfully!")

    # 2. Get User ID
    overview_res = client.get("/api/dashboard/overview", headers=user_headers)
    if overview_res.status_code != 200:
        print(f"Overview retrieval failed: {overview_res.text}")
        return
    user_id = overview_res.json()["user_id"]

    # 3. Create Store Location
    print("\n2. Creating new storefront location...")
    loc_payload = {
        "name": "Emerald Oasis Greenhouse",
        "address": "456 Oak Lane, Pineville",
        "phone": "+1 555-0202",
        "email": "greenhouse@leafydash.com",
        "manager": "Dr. Pamela Isley"
    }
    loc_res = client.post("/api/dashboard/locations", json=loc_payload, headers=user_headers)
    if loc_res.status_code != 200:
        print(f"Location creation failed: {loc_res.text}")
        return
    loc_data = loc_res.json()
    loc_id = loc_data["id"]
    print(f"Location '{loc_data['name']}' created successfully (ID: {loc_id})")

    # 4. Create Catalog Products
    print("\n3. Adding products to storefront inventory...")
    prod1_payload = {
        "name": "Emerald Bonsai Tree",
        "sku": "EM-BON-88",
        "stock": "15",
        "price": "95.00",
        "buying_price": "45.00",
        "location_id": str(loc_id)
    }
    prod1_res = client.post("/api/dashboard/inventory", data=prod1_payload, headers=user_headers)
    if prod1_res.status_code != 200:
        print(f"Product 1 insert failed: {prod1_res.text}")
        return
    prod1_data = prod1_res.json()
    prod1_id = prod1_data["id"]
    print(f"Added product: '{prod1_data['name']}' (ID: {prod1_id}, Stock: {prod1_data['stock']})")

    prod2_payload = {
        "name": "Desert Rose Cactus",
        "sku": "DES-ROSE-22",
        "stock": "30",
        "price": "25.00",
        "buying_price": "10.00",
        "location_id": str(loc_id)
    }
    prod2_res = client.post("/api/dashboard/inventory", data=prod2_payload, headers=user_headers)
    if prod2_res.status_code != 200:
        print(f"Product 2 insert failed: {prod2_res.text}")
        return
    prod2_data = prod2_res.json()
    prod2_id = prod2_data["id"]
    print(f"Added product: '{prod2_data['name']}' (ID: {prod2_id}, Stock: {prod2_data['stock']})")

    # 5. Log Customer Sale
    print("\n4. Logging a verified customer transaction...")
    sale_payload = {
        "location_id": loc_id,
        "customer_name": "Tony Stark",
        "customer_email": "tony@starkindustries.com",
        "customer_phone": "+1 555-3000",
        "customer_address": "10880 Malibu Point, Malibu, CA",
        "items": [
            {"product_id": prod1_id, "quantity": 1},
            {"product_id": prod2_id, "quantity": 2}
        ]
    }
    sale_res = client.post("/api/dashboard/sales", json=sale_payload, headers=user_headers)
    if sale_res.status_code != 200:
        print(f"Sales logging failed: {sale_res.text}")
        return
    sale_data = sale_res.json()
    print(f"Sale logged successfully! Total Invoice Amount: {sale_data['amount']} (Decremented product stocks)")

    # 6. Submit Verified Customer Review
    print("\n5. Posting customer review...")
    review_payload = {
        "customer_name": "Tony Stark",
        "rating": 5,
        "comment": "Absolutely love the Bonsai tree and Desert Rose cacti! They bring life to my Malibu mansion. Excellent customer service!",
        "location_id": loc_id
    }
    review_res = client.post(f"/api/public/review/{user_id}", json=review_payload)
    if review_res.status_code != 200:
        print(f"Review posting failed: {review_res.text}")
        return
    print(f"Review posted successfully: {review_res.json()['message']}")

    # 7. Fetch All Reviews
    print("\n6. Retrieving all customer reviews...")
    reviews_res = client.get("/api/dashboard/reviews", headers=user_headers)
    if reviews_res.status_code != 200:
        print(f"Review list fetch failed: {reviews_res.text}")
        return
    
    reviews = reviews_res.json()
    print("\n================ Store reviews list ================")
    for r in reviews:
        print(f"- {r['customer_name']}: {r['rating']} Stars - \"{r['comment']}\" (Status: {r['status']})")
    print("====================================================\n")
    print("SUCCESS: Store, products, sale logs, and customer reviews added successfully!")

if __name__ == "__main__":
    run_automation()
