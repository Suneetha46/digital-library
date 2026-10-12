# Digital Library & E-Book Circulation Portal

A modern, full-stack **Digital Library & E-Book Circulation Portal** built with **Django 6**, **Python 3.12**, **HTML5**, **CSS3**, **JavaScript (ES6+)**, **Bootstrap 5**, **SQLite**, and **WhiteNoise**.

---

## 🌟 Key Highlights & Features

1. **Responsive Home Page & Digital Catalog**:
   - Modern glassmorphic hero banner with glowing effects and live library metrics.
   - Comprehensive book catalog displaying book cover images, titles, authors, ISBN numbers, genre tags, and inventory availability indicators.

2. **Instant Real-Time JavaScript Search & Multi-Filter**:
   - Zero-latency client-side search across book titles, authors, genres, and ISBNs as the user types.
   - Interactive genre filter pill tags and stock availability toggles (*All Volumes*, *Available Now*, *Currently Checked Out*).

3. **Robust Data Architecture (Django ORM & SQLite)**:
   - `Author`: Biographies, nationality, birth date, photo, and catalog relationships.
   - `Book`: Title, author foreign key, ISBN (unique), genre choices, description, covers, copies tracking (`total_copies`, `available_copies`), publication year, publisher, and digital e-book support.
   - `Member`: OneToOne linked `User`, unique formatted membership ID (`LIB-2026-XXXX`), contact information, and borrowing limits (quota: 5 books).
   - `CirculationRecord`: Tracks book loan lifecycle (`ISSUED`, `RETURNED`, `OVERDUE`), automatic 14-day due date calculation, return dates, overdue fines, and staff accountability records.

4. **Automated Circulation Workflows**:
   - **Issue Books**: Staff-only checkout workflow with atomic inventory transactions.
   - **Out-of-Stock Protection**: Strictly prevents issuing books when available copies are zero (`0`).
   - **Inventory Auto-Decrement**: Automatically decreases available copies by 1 when a book is issued.
   - **Automated Due Date**: Automatically sets loan return due date to **14 days** from the issue date.
   - **Return Books**: Staff-only check-in workflow that increments available copies by 1.
   - **Overdue Fine Calculation**: Automatically calculates late return fines at **$1.00 per day** overdue with fine payment settlement tracking.

5. **Member & Staff Dashboards**:
   - **Member Dashboard**: Features an interactive **Digital Library Card** with cardholder number, active loan tracking, countdown timers, animated pulsing overdue alerts, and lifetime borrowing history.
   - **Staff Circulation Desk**: Real-time overview of active checked-out books, overdue alert highlights, quick return modal, fine counters, and inventory restock status.

6. **Enterprise Security & Validation**:
   - Full server-side Django form validation with clean methods preventing double loans or quota exceedance.
   - CSRF protection across all forms and role-based view decorators (`@login_required`, `@user_passes_test`).
   - Django Admin integration with custom badges, search filters, and bulk return actions.

7. **Production & Cloud Ready**:
   - Configured with **WhiteNoise** for high-performance static asset compression and delivery.
   - Includes `render.yaml`, `build.sh`, `Procfile`, and `requirements.txt` for one-click deployment on Render or similar cloud platforms.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, Django 6.1.2, Django ORM
- **Database**: SQLite 3 (default Django configuration)
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Bootstrap 5.3, Bootstrap Icons
- **Static Assets & Server**: WhiteNoise 6.12, Gunicorn 23.0, Pillow 12.3

---

## 🚀 Quick Start Guide (Local Setup)

### 1. Prerequisites
Ensure Python 3.11+ is installed.

### 2. Navigate to Project Directory
```powershell
cd c:\Users\HOME\OneDrive\Desktop\digital-library
```

### 3. Activate Virtual Environment
The virtual environment `.venv` is configured in the project:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt (CMD)
.\.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

*(If you ever need to create a new virtual environment from scratch: `python -m venv .venv` followed by `pip install -r requirements.txt`)*

### 4. Apply Database Migrations
```powershell
python manage.py migrate
```

### 5. Seed Demo Data & Default Accounts
Run the custom seeding command to populate realistic authors, books, active and overdue circulation loans, and default test accounts:
```powershell
python manage.py seed_library
```

### 6. Collect Static Files (WhiteNoise)
```powershell
python manage.py collectstatic --no-input
```

### 7. Run the Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Pre-Configured Test Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Staff / Librarian (Superuser)** | `librarian` | `admin1234` | Has access to Circulation Desk, Book/Author creation, Admin |
| **Library Member 1** | `alex_reader` | `member1234` | Has 1 active loan and 1 overdue loan (fine: $6.00) |
| **Library Member 2** | `sophia_books` | `member1234` | Has 2 returned loans in borrowing history |

*(Tip: On the Sign In page, you can click the **"Use"** button next to any test account to auto-fill the credentials!)*

---

## 🧪 Step-by-Step Verification & Testing Guide

### 1. Test Instant Search & Filters (Public)
1. Open `http://127.0.0.1:8000/`.
2. Type `Clean` into the search box: observe that only *Clean Code* remains visible instantly.
3. Click the genre pill `Fantasy & Sci-Fi`: observe that *Dune* appears immediately.
4. Select `Currently Checked Out` in the filter dropdown: observe that *Sapiens* (0 copies available) appears.
5. Click **Clear / All Genres** to restore the catalog.

### 2. Test Staff Circulation Desk & Overdue Alerts
1. Navigate to `http://127.0.0.1:8000/login/`.
2. Click **Use** for `librarian` / `admin1234` and submit.
3. You will be redirected to `http://127.0.0.1:8000/staff/circulation/`.
4. Observe the four metric summary cards:
   - Active Checked Out
   - Overdue Loans (highlighted with pulsing red badge)
   - Returned Volumes
   - Total Fines Assessed
5. Look at the record for *Refactoring* borrowed by `alex_reader`: note the red **OVERDUE** badge and calculated fine.

### 3. Test Issuing a Book & 14-Day Due Date Calculation
1. Click **Issue New Book** (or visit `/staff/issue/`).
2. Select member `Sophia Chen` and book `Dune`.
3. Notice the **Calculated Due Date Preview**: it automatically calculates exactly 14 days from today.
4. Click **Confirm & Issue Book**:
   - The book is issued.
   - Available copies for *Dune* decreases by 1 automatically.
   - A success message confirms the 14-day due date.

### 4. Test Zero Copies Prevention (Out-of-Stock Validation)
1. Visit `/staff/issue/`.
2. Notice that *Sapiens: A Brief History of Humankind* (which has 0 copies available) is **excluded** from the book dropdown list.
3. If an invalid or zero-copy book ID is manually submitted, server-side validation rejects the request and protects inventory integrity.

### 5. Test Returning a Book & Fine Calculation
1. Go to the Circulation Desk (`/staff/circulation/`).
2. Locate the overdue record for *Refactoring* (`alex_reader`).
3. Click **Return** (`/staff/return/<id>/`).
4. On the confirmation page, review the loan breakdown:
   - Issue date, due date, and today's date.
   - Days overdue calculated.
   - Fine calculation: `Days Overdue x $1.00/day`.
   - Toggle switch to record fine payment.
5. Click **Process Return & Restock Copy**:
   - The book is marked as `RETURNED`.
   - The book's `available_copies` increases by 1 automatically.

### 6. Test Member Dashboard & Borrowing History
1. Log out (`/logout/`) or open an incognito window.
2. Sign in as `alex_reader` (password `member1234`).
3. You are redirected to `/dashboard/`.
4. View the **Digital Membership Card** displaying membership ID `LIB-2026-ALEX01`.
5. Check the **Active Borrowed Books** table with remaining days and overdue alerts.
6. Check the **Borrowing History** table with completed loans and settled fine records.

### 7. Test Django Admin
1. Sign in as `librarian`.
2. Visit `http://127.0.0.1:8000/admin/`.
3. Manage **Authors**, **Books**, **Members**, and **Circulation Records** with search fields, list filters, availability badges, and admin actions.

### 8. Run Automated Test Suite
To run the automated tests verifying all requirements:
```powershell
python manage.py test circulation
```
Output:
```text
Ran 7 tests in 18.548s

OK
```

---

## ☁️ Deployment on Render

This project is fully configured for zero-configuration deployment to Render:

1. **`render.yaml`**: Contains the complete service specification.
2. **`build.sh`**: Installs requirements, runs WhiteNoise `collectstatic`, and applies database migrations automatically.
3. **`requirements.txt`**: Specifies all required dependencies (Django 6, WhiteNoise, Gunicorn, Pillow).
4. **`Procfile`**: Specifies the production WSGI command: `gunicorn library_portal.wsgi:application --bind 0.0.0.0:$PORT`.

To deploy:
1. Push this repository to GitHub or GitLab.
2. Log into [Render.com](https://render.com) and click **New > Blueprint**.
3. Select your repository — Render will automatically read `render.yaml` and configure the web service.
