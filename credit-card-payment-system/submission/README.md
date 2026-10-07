# Submission Review Package

[Open the team review and demo guide](Credit-Card-Payment-System-Review.pdf). It explains the architecture, payment flow, security choices, demo sequence, test results, caveats, and captured UI/API screens. This is a project review guide, not the original assignment brief.

## Screenshots

- [Sign in](screenshots/login.png)
- [Customer overview](screenshots/dashboard.png)
- [Dashboard summary and recent transactions](screenshots/dashboard-summary.png)
- [Cards](screenshots/cards.png)
- [Simulated payment success](screenshots/payment-success.png)
- [Simulated payment failure](screenshots/payment-failure.png)
- [Transaction history](screenshots/transactions.png)
- [Admin reporting](screenshots/admin-dashboard.png)
- [Django administration](screenshots/django-admin.png)
- [Django API documentation](screenshots/django-api-docs.png)
- [FastAPI Swagger](screenshots/fastapi-swagger.png)

## MySQL Demo Dump

- [MySQL schema and synthetic demo data](credit-card-payment-demo.sql)

The dump uses schema-only DDL from the configured local MySQL database and synthetic rows from the isolated showcase SQLite database. It does not include existing MySQL user data, sessions, refresh tokens, CVVs, or full card numbers. It creates the separate `credit_card_submission_demo` database and contains no `DROP TABLE` statements.

Restore it with MySQL Workbench or the MySQL command-line client using a database administrator account. The local application account cannot create a database. The dump creates a separate demo schema and does not alter `credit_card_db`.

Screenshots were captured from the running application using synthetic records in a separate SQLite showcase database. Existing MySQL records were neither modified nor exported. The SQL dump includes schema-only DDL and synthetic showcase rows; the SQLite file itself is ignored by Git and is not the MySQL dump.

Regenerate the MySQL dump from the project root with `python submission/build_mysql_dump.py` when the local MySQL schema and isolated showcase database are available. Regenerate the PDF with `python submission/build_report.py` after installing ReportLab and Pillow.
