# 🏥 MedNova ERP System

A full-featured Enterprise Resource Planning (ERP) system built with **FastAPI** (Python) backend and vanilla HTML/CSS/JS frontend. Designed for healthcare and corporate organizations.

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Modules](#modules)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [Default Login](#default-login)
- [API Documentation](#api-documentation)
- [Environment Variables](#environment-variables)
- [Document Storage](#document-storage)

---

## 🧠 System Overview

MedNova ERP standardizes and automates administrative and financial processes across departments including HR, Finance, Procurement, Inventory, and Asset Management. It supports multi-role access, approval workflows, real-time dashboards, and bilingual (English/Arabic) interface.

---

## 📦 Modules

| Module | Features |
|--------|----------|
| **Auth** | Login, Register, JWT Token, Role-based redirect |
| **Admin** | User management, create/edit/delete users, role assignment, audit logs, CSV import/export |
| **HR** | Employee profiles, Leave requests, Attendance tracking, Payroll processing, Contracts, Performance reviews, Document upload |
| **Finance** | Expense management, Budget tracking, General Ledger, Journal Entries, Chart of Accounts, Accounts Payable, P&L Report, Cash Flow, Balance Sheet |
| **Procurement** | Purchase Requests (PR), Purchase Orders (PO), Vendor management, Approval workflow |
| **Inventory** | Item master, Stock movements (IN/OUT), Low stock alerts, Category management |
| **Asset Management** | Asset registration, Status tracking, Maintenance scheduling, Depreciation, QR code generation |
| **Dashboard** | Real-time KPIs, Charts, Stats per role |
| **Navigation** | Global search (Ctrl+K), Breadcrumb, Favorites, Mobile responsive sidebar |
| **i18n** | English / Arabic (RTL) language toggle |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy ORM |
| Database | MySQL (via PyMySQL) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Charts | Chart.js |
| Export | ReportLab (PDF), openpyxl (Excel) |
| Server | Uvicorn (ASGI) |

---

## 📁 Project Structure

```
final_erp/
├── app/
│   ├── api/
│   │   └── v1/               # All route handlers
│   │       ├── auth.py
│   │       ├── admin.py
│   │       ├── admin_extra.py
│   │       ├── hr.py
│   │       ├── finance.py
│   │       ├── employee.py
│   │       ├── procurement.py
│   │       ├── inventory.py
│   │       ├── asset.py
│   │       ├── dashboard.py
│   │       ├── workflow.py
│   │       └── workflow_config.py
│   ├── core/
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   ├── dependencies.py   # Auth guards (get_admin, get_hr, etc.)
│   │   └── security.py       # JWT + bcrypt
│   ├── models/               # SQLAlchemy DB models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic
│   ├── static/               # Frontend (HTML, CSS, JS)
│   │   ├── index.html        # Login page
│   │   ├── admin.html        # Admin dashboard
│   │   ├── hr.html           # HR dashboard
│   │   ├── finance.html      # Finance dashboard
│   │   ├── employee.html     # Employee portal
│   │   ├── procurement.html  # Procurement
│   │   ├── inventory.html    # Inventory
│   │   ├── asset.html        # Asset management
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── api.js        # Global fetch wrapper + auth
│   │       ├── navigation.js # Search, breadcrumb, favorites, mobile menu
│   │       ├── i18n.js       # Language switcher
│   │       └── content-enhancer.js
│   └── main.py               # FastAPI app entry point
├── uploads/
│   └── documents/            # HR uploaded documents (local storage)
├── .env                      # Environment configuration
├── requirements.txt
└── run.py                    # Start server
```

---

## ⚙️ Requirements

- Python 3.10 or higher
- MySQL 8.0 or higher
- pip

---

## 🚀 Setup & Installation

### 1. Clone / Download the project

```bash
cd final_erp
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

Activate it:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup MySQL Database

Open MySQL and run:

```sql
CREATE DATABASE erp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Configure `.env`

Open the `.env` file and set:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/erp_db
SECRET_KEY=your-strong-secret-key-minimum-32-characters
```

> ⚠️ Change `YOUR_MYSQL_PASSWORD` to your actual MySQL root password.

### 6. Create database tables

Tables are created **automatically** when the server starts (via SQLAlchemy `create_all`). No migrations needed.

---

## ▶️ Running the App

```bash
python run.py
```

Server will start at: **http://127.0.0.1:8000**

Or with uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔐 Default Login

After first run, create an admin user via the register page, then update the role in MySQL:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

### User Roles

| Role | Access |
|------|--------|
| `admin` | Full access — all modules |
| `hr_manager` | HR dashboard, employees, leave, payroll |
| `finance` | Finance dashboard, expenses, budgets, GL |
| `employee` | Own profile, leaves, payslips, expenses |

---

## 📖 API Documentation

Once server is running, visit:

```
http://127.0.0.1:8000/api/docs
```

Interactive Swagger UI with all endpoints listed.

### Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/register` | Register |
| GET | `/api/v1/admin/users` | List all users (admin only) |
| GET | `/api/v1/employee/` | List all employees |
| GET | `/api/v1/hr/leave` | List leave requests |
| POST | `/api/v1/hr/attendance` | Mark attendance |
| GET | `/api/v1/finance/expense` | List expenses |
| GET | `/api/v1/finance/budget` | List budgets |
| GET | `/api/v1/dashboard/` | Dashboard stats |
| GET | `/api/v1/procurement/pr` | Purchase requests |
| GET | `/api/v1/inventory/items` | Inventory items |
| GET | `/api/v1/asset/` | Assets list |

---

## 🌐 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://root:2002@localhost:3306/erp_db` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | `my-secret-key-change-this-now` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `60` |

---

## 📂 Document Storage

HR-uploaded documents are stored **locally** on the server:

```
uploads/documents/{employee_id}_{doc_type}_{filename}
```

- File metadata (name, size, path, uploader) → saved in MySQL
- File download available via: `GET /api/v1/hr/document/download/{doc_id}`
- Cloud storage (S3/MinIO) support is available in `app/services/document_archive.py` (configure in `.env`)

---

## ✅ What's Complete (MVP)

- [x] Multi-role authentication (JWT)
- [x] Admin user & role management
- [x] HR module (employees, leave, attendance, payroll, contracts, performance, documents)
- [x] Finance module (expenses, budgets, GL, journal, COA, AP, reports)
- [x] Procurement module (PR, PO, vendors, approval flow)
- [x] Inventory module (items, stock movements, low stock alerts)
- [x] Asset management (assets, maintenance, depreciation)
- [x] Real-time dashboards with charts
- [x] Global search, breadcrumb, favorites, mobile sidebar
- [x] English / Arabic (RTL) language support
- [x] PDF & Excel export (payroll, employees, expenses)
- [x] MySQL database
- [x] Audit logging

---

## 🔮 Planned (Future)

- [ ] Email notifications (SMTP configured, not wired)
- [ ] MFA enforcement
- [ ] Cloud document storage (S3/MinIO)
- [ ] Biometric attendance integration
- [ ] Power BI integration
- [ ] Mobile app

---

*Built with ❤️ — MedNova ERP v1.0 MVP*
