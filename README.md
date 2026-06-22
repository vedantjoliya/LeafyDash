# 🍃 Leafy Dash

**Leafy Dash** is a secure, elegant, and modular business operations dashboard. Designed with soft, natural aesthetics, custom-tailored color palettes, and interactive user interfaces, it enables multi-location shop owners to manage sales, track inventory, capture QR-based customer feedback, log CRM campaigns, and handle support tickets directly from a single portal.

---

## 🚀 Features & Modules

### 1. 📊 Overview & Operational Analytics
* **Dynamic KPIs**: Real-time display of **Revenue**, **Spends**, **Net Profit**, and **Average Review Rating** with dynamic currency symbols and localized formats.
* **Profit Tracking Chart**: Dynamic Chart.js visualizations tracking sales revenue vs operating costs over time.
* **System Metrics Monitor**: Real-time server load, API latency trackers, and service health status bars.

### 2. 🏪 Storefront & Branch Locations Management
* Create and edit branch offices, storefronts, and warehouse locations.
* View directories detailing storefront Manager, Address, Email, and Phone contacts.
* Cascade deletes: Removing a storefront automatically purges associated inventory items, sales logs, and customer purchasing records.

### 3. 📦 Smart Inventory Catalog
* **Stock & SKU Tracking**: Track stock levels, buying prices, selling prices, and automatic low-stock triggers.
* **Location Contexts**: Switch storefront locations dynamically to view local inventory lists.
* **Product Management**: Upload product images, define names, input custom SKU numbers, and update details on-the-fly.

### 4. 🧾 Sales Transaction Log
* **POS Cart System**: Select storefront products, build a cart, adjust quantities, calculate totals, and log sales transactions instantly.
* **Transaction Invoices Table**: Fully searchable log of transactions detailing date, location, amount, and customer details.
* **Receipts & Shares**: Open details in an elegant receipt view, print directly, or generate WhatsApp/Email templates to share with clients.

### 5. ⭐ QR Reviews & Customer Feedback
* **Print-Ready QR Codes**: Automatically generates printable QR codes matching storefront links (`/review/{user_id}?location_id={loc_id}`).
* **Secure Review Logic**: Verifies customer purchase history prior to allowing 5-star reviews to prevent review bombing.
* **Negative Feedback Escalation**: Low-rating customer feedback (e.g. 1-2 stars) automatically generates a priority support ticket inside the CRM section to resolve customer issues.

### 6. ✉️ CRM & Marketing Broadcast Campaigns
* **Customer Directory**: Centralized table detailing customer lifetime value (LTV), transaction counts, last visit dates, and contacts.
* **Multi-Channel Campaigns**: Broadcast marketing messages via WhatsApp, Email, or Print flyer templates (*Seasonal Promo*, *Product Launch Alert*, and *Loyalty Reward*).
* **Flyer Generator**: Automatically formats printable promotional cards featuring personalized customer tags and storefront QR codes.
* **Sent Campaigns Log**: Persistent historical logs of all sent campaigns detailing coupon codes, segments, channels, and recipient counts.

### 7. 🛡️ System Administration Console (`/admin-portal`)
* **Pending Approvals**: Secure verification workflow. New shops start as `pending` and must be approved by the root admin.
* **Direct Broadcast Messages**: Send global notifications, server maintenance warnings, and administrative announcements directly to shop dashboards.
* **Shop Removal**: Root admin can delete shop accounts instantly, which cascades to delete all store data to satisfy compliance rules.

### 8. 💬 Integrated Support Settings & Inbox
* **Contact Admin Form**: Shops can submit questions, bug reports, and account queries to the root admin.
* **Integrated Inbox Card**: Submited support queries and admin announcements are housed directly within the Settings menu.
* **Unread Notifications Badge**: Visual badge counts unread announcements to keep shop owners updated.

---

## 🌍 Localizations & Internationalization (i18n)
* **Regional Currencies**: Instantly toggle between **USD ($)**, **GBP (£)**, and **EUR (€)**. Setting a currency applies it dynamically to all pricing, metrics, invoices, and cart systems.
* **Multi-Lingual Interface**: Dynamically toggle between **English (EN)**, **French (FR)**, and **German (DE)**. The sidebar navigation, titles, and support logs automatically translate.
* **Date & Metric Preferences**: Select preferred formatting options (`MM/DD/YYYY`, `DD/MM/YYYY`, or `YYYY-MM-DD`) and measurement systems (Metric/Imperial).

---

## 🛡️ Security Enhancements
* **Strict Form Validation**: Client-side validation checks input integrity. Text inputs cannot consist of only blank whitespace, and email forms require RFC 5322 pattern matches.
* **Strong Password Validation**: Enforces minimum 8 characters containing at least one uppercase letter, one lowercase letter, one digit, and one special symbol (`@$!%*?&_#-`).
* **Backend Database Schemas**: Enforces data constraints on model schemas using Pydantic validators (preventing negative prices, empty fields, and unauthorized ratings).

---

## 📐 Architecture & Data Flow

Leafy Dash is structured as a decoupled architecture where the FastAPI backend serves static frontend files and interacts via a REST API:

```mermaid
graph TD
    User([Browser Client]) -->|HTTP GET /| FastAPI[FastAPI Backend]
    User -->|AJAX API Request| FastAPI
    FastAPI -->|ORM queries| SQLAlchemy[SQLAlchemy ORM]
    SQLAlchemy -->|Read/Write| DB[(SQLite / PostgreSQL)]
    FastAPI -->|Serve static HTML/CSS/JS| Static[Static Filesystem]
```

### Flow of Core Interactions:
1. **Onboarding & Configuration**:
   During registration, users are routed to `/onboarding`. Their modular selections (Overview, Inventory, Analytics, etc.) customize the database settings and shape the workspace sidebar tabs dynamically.
2. **Review to CRM Loop**:
   * A customer scans a QR code at `/review/{user_id}`.
   * If the rating is 1 or 2 stars, the backend automatically flags it and creates a ticket in the `CRMLead` table.
   * The business owner sees the alert in their **CRM & Campaigns** dashboard, allowing them to contact the customer and resolve the ticket.
3. **Admin Announcement Routing**:
   * Admin posts a message from the `/admin-portal`.
   * The message is stored in the `AdminMessage` table.
   * Dashboard clients query `/api/dashboard/inbox` and show a real-time badge count next to the **Settings** menu.

---

## 🛠️ Local Development Setup

### Prerequisites
* Python 3.8 or higher installed on your system.

### Installation Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/vedantjoliya/LeafyDash.git
   cd LeafyDash
   ```

2. **Set Up Python Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory (optional, defaults to local SQLite):
   ```env
   DATABASE_URL=sqlite:///./database.db
   SECRET_KEY=YOUR_SUPER_SECRET_JWT_KEY
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. **Run Development Server**:
   ```bash
   uvicorn backend.main:app --reload
   ```
   Open your browser to `http://127.0.0.1:8000` to view the application.

---

## ☁️ Deployment from GitHub to Vercel

Leafy Dash is optimized for seamless deployment to Vercel using serverless functions.

### How it Works:
* Vercel reads `vercel.json` and routes all frontend/backend traffic to `api/index.py`.
* `api/index.py` boots the FastAPI app from `backend/main.py`.
* FastAPI mounts static folder paths (`/css`, `/js`, `/images`) and handles user/admin rendering natively.

### ⚠️ Critical Note on Databases in Serverless Environments:
Vercel Serverless Functions are **stateless and ephemeral**. The default local SQLite database (`database.db`) will be reset every time a function goes idle (cold start). 

To persist your database records in staging or production:
1. Provision a managed PostgreSQL instance (e.g. Supabase, Neon.tech, or CockroachDB).
2. Grab your connection URI (e.g. `postgresql://user:pass@host:5432/dbname`).
3. Add it as an Environment Variable inside your Vercel Project Settings named **`DATABASE_URL`**.
4. The system automatically converts `postgres://` to `postgresql://` and sets up the schemas on build.

### Deployment Instructions:
1. Push your latest code changes to GitHub:
   ```bash
   git add .
   git commit -m "Configure Vercel Serverless Deployment"
   git push origin main
   ```
2. Log into the [Vercel Dashboard](https://vercel.com).
3. Click **Add New** > **Project** and import your `LeafyDash` repository.
4. Expand **Environment Variables** and add:
   * `DATABASE_URL`: Your production PostgreSQL connection string.
   * `SECRET_KEY`: A secure random hash string for authentication tokens.
5. Click **Deploy**. Vercel will build the dependencies and provide you with a live URL.
