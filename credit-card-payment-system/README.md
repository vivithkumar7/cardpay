# Credit Card Payment System

Full Stack Junior Application Task

## Stack

- Frontend: React + Tailwind CSS
- Authentication/Card/Transactions/Admin: Django + Django REST Framework
- Payment processing: FastAPI
- Database: MySQL
- Authentication: JWT
- API docs: FastAPI Swagger + DRF API endpoints
- Payment: simulated only; no real gateway

## Security

- Passwords use Django's PBKDF2 password hashing.
- JWT is required for API authentication.
- CVV is never stored.
- Full card numbers are never stored.
- Only masked card number and last 4 digits are persisted.
- ORM queries are used instead of raw SQL.
- Payment amount/card ownership are validated server-side.
- Payment service requires the same Django-signed JWT and receives only a card ID, not a full PAN/CVV.
- `DJANGO_INTERNAL_SECRET` must be a random value of at least 32 characters, shared only by Django and FastAPI. Internal transaction endpoints reject missing or shorter secrets.

## Important task interpretation

The provided task PDF requires Django + FastAPI + MySQL, JWT, masked cards, simulated payment states, transaction filtering/export, admin reporting, Docker, tests, Swagger, Postman, and README documentation.

The PDF says the strict time limit is 4 days. Follow the deadline stated by your assigned team if your email says otherwise.

## Project structure

```text
credit-card-payment-system/
├── backend/
│   ├── django_backend/
│   │   ├── manage.py
│   │   ├── config/
│   │   ├── accounts/
│   │   ├── cards/
│   │   ├── transactions/
│   │   ├── audit/
│   │   └── requirements.txt
│   └── fastapi_payment/
│       ├── app/
│       └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── postman/
│   └── Credit-Card-Payment-System.postman_collection.json
├── mysql/
│   └── init/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Local setup

Run the commands below from the repository root (`credit-card-payment-system/`). If your terminal is one directory above it, enter the project first:

```powershell
cd .\credit-card-payment-system
```

Create the local environment file from the sample:

```powershell
Copy-Item .env.example .env
```

Before running the services, replace `DJANGO_SECRET_KEY` and `DJANGO_INTERNAL_SECRET` in `.env` with independently generated random values of at least 32 characters. For example, run `python -c "import secrets; print(secrets.token_urlsafe(48))"` twice and use one value for each variable. Django and FastAPI refuse a signing key shorter than 32 characters. Do not use the sample placeholders outside local development.

### 1. MySQL

For Docker, `docker compose up --build` creates the database and `appuser` automatically. For a local MySQL installation, connect as a MySQL administrator:

```powershell
mysql -u root -p
```

If PowerShell says `mysql` is not recognized, use the installed client directly:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

Then create the database and application user to match `.env`:

At the `mysql>` prompt, enter only these SQL statements. Do not enter the PowerShell `mysql.exe` launch command here. If the prompt changes to `">`, type `\c` and press Enter to clear the unfinished input.

```sql
CREATE DATABASE IF NOT EXISTS credit_card_db CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'apppassword';
ALTER USER 'appuser'@'localhost' IDENTIFIED BY 'apppassword';
GRANT ALL PRIVILEGES ON credit_card_db.* TO 'appuser'@'localhost';
```

If Django reports `Access denied for user 'appuser'@'localhost'`, run the SQL above as a MySQL administrator and make sure `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_HOST`, and `MYSQL_PORT` in `.env` match the MySQL account. For the sample settings, the app password is `apppassword`.

Keep Django configured with `MYSQL_USER=appuser`; do not set it to `root`. Use the MySQL `root` account only to run the database and grant statements above. Set `MYSQL_PASSWORD` to the password assigned to `appuser`.

Alternatively, run this entire command in **PowerShell** (not at a `mysql>` prompt). It prompts for the MySQL root password and applies the sample `appuser` credentials:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "CREATE DATABASE IF NOT EXISTS credit_card_db CHARACTER SET utf8mb4; CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'apppassword'; ALTER USER 'appuser'@'localhost' IDENTIFIED BY 'apppassword'; GRANT ALL PRIVILEGES ON credit_card_db.* TO 'appuser'@'localhost'; FLUSH PRIVILEGES;"
```

For Docker, an existing `mysql_data` volume keeps the credentials from its first initialization. Reset the app account without deleting the database volume:

```powershell
docker compose exec mysql mysql -uroot -prootpassword -e "ALTER USER 'appuser'@'%' IDENTIFIED BY 'apppassword'; GRANT ALL PRIVILEGES ON credit_card_db.* TO 'appuser'@'%'; FLUSH PRIVILEGES;"
```

If you use a different `MYSQL_PASSWORD`, use that same password in the SQL command and `.env`.

### 2. Django

```bash
cd backend/django_backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Remove-Item Env:DJANGO_TEST_SQLITE -ErrorAction SilentlyContinue
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

Django API:

- API: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)
- Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### 3. FastAPI

```bash
cd backend/fastapi_payment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Swagger: [FastAPI Swagger UI](http://127.0.0.1:8001/docs)

### 4. React

```bash
cd frontend
npm install
npm run dev
```

Frontend: [http://localhost:5173](http://localhost:5173)

## Docker

```bash
docker compose up --build
```

Services:

- Frontend: [http://localhost:5173](http://localhost:5173)
- Django: [http://localhost:8000](http://localhost:8000)
- FastAPI: [http://localhost:8001/docs](http://localhost:8001/docs)
- MySQL: `localhost:3306`

## Demo payment simulation

The frontend sends a card ID and amount to FastAPI. FastAPI creates a PENDING transaction through the Django internal API, then simulates success/failure and updates the transaction.

For deterministic testing:

- Amount ending in `.13` => FAILED
- Other valid amounts => SUCCESS

Example: `100.13` produces FAILED.

This is only a simulation and does not contact a payment gateway.

## API summary

Django:

- POST `/api/auth/register/`
- POST `/api/auth/login/`
- POST `/api/auth/refresh/`
- POST `/api/auth/logout/`
- GET `/api/auth/me/`
- POST `/api/cards/`
- GET `/api/cards/`
- DELETE `/api/cards/<id>/`
- GET `/api/transactions/`
- GET `/api/admin/export/` (staff/admin only)
- GET `/api/admin/summary/`

FastAPI verifies the JWT and forwards only the authenticated user ID to Django's
internal summary endpoint using the shared internal secret. Django queries
transactions and related cards; the recent-transactions query selects related card
data and is limited to five results. `total_amount_spent` and
`current_month_spending` include successful transactions only.
`available_credit_limit` is the account's configured limit minus successful
credit-card transactions, floored at zero. Configure limits in Django Admin under
**User credit profiles**; new profiles default to `0.00`.

The dashboard also lists recent successful transactions as payment receipts.
Users can view receipt details or download a self-contained HTML receipt; receipts
are for simulated payments and are not tax invoices.

FastAPI:

- GET `/dashboard/summary` (JWT required; successful transactions count toward spending)
- POST `/payments/`
- GET `/health`
- GET `/version`
- Swagger `/docs`

## Database schema

| Table | Important fields | Sensitive data policy |
| --- | --- | --- |
| Django users | `id`, `username`, `email`, `password`, `is_staff` | `password` contains a Django password hash, never the plaintext password. |
| Cards | `id`, `user_id`, `card_type`, `masked_card_number`, `last4`, `card_holder_name`, `expiry_month`, `expiry_year` | No full card number or CVV columns are stored. |
| Transactions | `id`, `user_id`, `card_id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, timestamps | References the saved card; payment is simulated and has no gateway credentials. |
| Admin logs | `id`, `admin_user_id`, `action`, `details`, `created_at` | Administrative audit records; no card PAN or CVV fields. |

The Django migrations define the authoritative schema. MySQL is used for normal runs; `DJANGO_TEST_SQLITE=1` is available for isolated tests and local live demos.

## Admin

Create a Django superuser:

```bash
python manage.py createsuperuser
```

Use those credentials for `/admin/`.

## Postman

Import:
`postman/Credit-Card-Payment-System.postman_collection.json`

Set:

- `django_url = http://localhost:8000`
- `fastapi_url = http://localhost:8001`
- `token` after login
- `refresh` after login (the Login request saves both JWTs automatically)
- `card_id` after adding a card

Use the **Dashboard Summary** request to call FastAPI `GET /dashboard/summary`;
the request asserts the response fields and that the recent transaction list is
limited to five entries.

## Screenshots

The dashboard summary UI screenshot is available at
[submission/screenshots/dashboard-summary.png](./submission/screenshots/dashboard-summary.png).
The screenshot uses mocked API data and contains no real account information.
Other submission screenshots are in `submission/screenshots/`.

## Database dump

After testing with MySQL:

```bash
mysqldump -u root -p credit_card_db > credit_card_db.sql
```

Do not commit real passwords, secrets, CVVs, or production data.

## Tests

Each test watcher runs independently and reruns its suite when relevant files change. Open three terminals from the repository root (`credit-card-payment-system/`):

### Terminal 1: Django

```powershell
cd backend/django_backend
python -m pip install -r requirements.txt
$env:DJANGO_TEST_SQLITE = "1"
python -m pytest_watch --runner "python manage.py test"
```

### Terminal 2: FastAPI

```powershell
cd backend/fastapi_payment
python -m pip install -r requirements.txt
python -m pytest_watch
```

### Terminal 3: Frontend

```powershell
cd frontend
npm install
npm test
```

`Ctrl+C` stops each watcher. Django's `$env:DJANGO_TEST_SQLITE` setting remains in that terminal after the watcher stops. Before normal Django commands such as migrations or creating a superuser, clear it and migrate the configured database:

```powershell
Remove-Item Env:DJANGO_TEST_SQLITE -ErrorAction SilentlyContinue
python manage.py migrate
python manage.py createsuperuser
```

For a single non-watch test run, use `python manage.py test` in `backend/django_backend` (set `$env:DJANGO_TEST_SQLITE = "1"` first), `pytest` in `backend/fastapi_payment`, or `npm run test:run` in `frontend`.

Target at least 50% coverage for the assignment.
