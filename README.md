# CompanySim. — Real-Time Multi-Player Corporate Simulation

Welcome to **CompanySim.**, a premium, real-time multi-player business simulation platform. Players take on corporate roles, complete task scenarios, upgrade their workspaces with widgets from the Gadget Shop, and compete to fulfill multi-metric victory conditions first. The entire application runs on real-time WebSockets and supports 11 global languages and 3 custom themes.

---

## 🚀 Key Features

### 1. Immersive Portals & Interactive Dashboards
*   **Access Terminal (Landing Page)**: Immersive split-screen layout. The left control center broadcasts live simulated server telemetry and system logs, while the right panel hosts the frosted-glass access controls. Sign-up fields dynamically toggle based on session status (new registration vs. password verification for returning player reconnection).
*   **Player Terminal**: Real-time business KPI bar displaying metrics (Revenue, Morale, Quality, Uptime, Customer Satisfaction, Market Share, Tech Debt, and Active Users) adorned with financial-style dynamic trend arrows (`▲` or `▼`) to track metric growth/drops in real time.
*   **Admin Control Room**: Comprehensive command dashboard. Admins can view aggregated global statistics, control the simulation clock (Launch, Pause, Resume, Kill), manage company nodes, and handle support requests.

### 2. Premium 3D Interactive Widgets
*   **Draggable News 3D Television**: A fully customized 3D TV cabinet with physical antennas, power switches, tuning dial knobs, and a CRT television screen that flickers with static noise on news updates. It physically wobbles in 3D space whenever new bulletins are received. Toggles Global vs. Team filtering channels.
*   **Diagnostics 3D Retro PC**: An interactive CRT monitor placed inside the player sidebar showing a diagnostics console. It synchronizes live revenue, uptime, morale, and goal targets in real-time. Can be grabbed and rotated in 3D space.
*   **Sidebar Goal Card**: A dedicated glassmorphic card placed directly below the 3D PC, displaying the victory target values cleanly.

### 3. Localization & Personalization
*   **11 Global Languages**: Full support for English, Spanish, Hindi, Gujarati, French, German, Chinese, Japanese, Arabic, Russian, and Portuguese, persistent across portal refreshes.
*   **3 Visual Themes**: Swap styles instantly:
    *   `Light Paper`: Standard clean business aesthetic.
    *   `Midnight Dev`: Dark workspace configuration with glowing icons.
    *   `Cyberpunk Neon`: Futuristic hot pink and purple styling.
*   **State Persistence**: Local coordinates, collapse states of the TV, selected languages, and active visual themes are persistently cached in `localStorage`.

---

## 🛠️ Technology Stack

*   **Backend**: Python, Flask, Flask-SQLAlchemy (ORM), Flask-SocketIO (Real-time Events).
*   **WSGI Server**: Eventlet, Gevent, Gunicorn (Production).
*   **Frontend**: HTML5, Vanilla CSS3 (Custom animations, 3D transforms, glassmorphic filters), Vanilla JavaScript, Lucide icons, Chart.js (Dynamic re-coloring).
*   **Database**: PostgreSQL (Production) / SQLite3 (Local fallback).

---

## 🗄️ Database Architecture

The application uses an ORM schema with cascade relationships:
*   **Session**: Holds corporate parameters (Join Code, Goal Targets, Active Status).
*   **Player**: Holds accounts, passwords (hashed via `werkzeug`), role tags, strikes, salaries, savings, and scores.
*   **Task**: Tracks active task configurations, questions, answers, and completion multipliers.
*   **ChatMessage**: Feeds global and company room communication channels.

---

## 💻 Local Installation

To run **CompanySim.** on your development machine:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/vedantjoliya/company-sim.git
    cd company-sim
    ```

2.  **Set Up Virtual Environment**:
    ```bash
    python -m venv venv
    # Activate on Windows:
    venv\Scripts\activate
    # Activate on macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Application Server**:
    ```bash
    python app.py
    ```
    *The app will automatically initialize SQLite databases and run on `http://127.0.0.1:5000`.*

5.  **Access Portals**:
    *   **Player Access Terminal**: `http://127.0.0.1:5000/`
    *   **Admin Control Room**: `http://127.0.0.1:5000/admin`

---

## ☁️ Render Cloud Deployment

Render is the recommended hosting service for the WSGI WebSocket servers.

### Setup Instructions
1.  Connect your GitHub repository to **Render**.
2.  Create a **Web Service** with the following options:
    *   **Runtime**: `Python`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn --worker-class eventlet -w 1 app:app`
3.  Choose database configuration:
    *   **SQLite Mode**: Deploy immediately. Standard databases will reset on service redeploys unless a persistent disk is attached under Render settings.
    *   **PostgreSQL Mode**: Add an environment variable under **Environment** tab:
        *   **Key**: `DATABASE_URL`
        *   **Value**: `postgresql://<your_database_connection_string>`
        *   *The schema will build automatically on the PostgreSQL DB on the first startup.*

---

## 👨‍💻 Developer Credits

**CompanySim.** is developed and maintained by **Vedant Joliya**.

*   **Portfolio**: [https://vedantjoliya.free.nf/](https://vedantjoliya.free.nf/)
*   **GitHub**: [@vedantjoliya](https://github.com/vedantjoliya)

---
*Created with ❤️ by Vedant Joliya. Feedback and pull requests are welcome!*
