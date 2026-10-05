import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pymysql
from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
SQLITE_FILE = PROJECT_ROOT / ".demo-showcase.sqlite3"
OUTPUT_FILE = Path(__file__).resolve().parent / "credit-card-payment-demo.sql"
TARGET_DATABASE = "credit_card_submission_demo"
EXCLUDED_TABLES = {
    "django_session",
    "token_blacklist_blacklistedtoken",
    "token_blacklist_outstandingtoken",
}


def sql_identifier(value):
    return "`" + value.replace("`", "``") + "`"


def sql_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    encoded = str(value).encode("utf-8").hex()
    return "CONVERT(X'" + encoded + "' USING utf8mb4)"


def get_mysql_settings():
    if not ENV_FILE.is_file():
        raise FileNotFoundError("Project .env is required to read the local MySQL schema.")
    settings = dotenv_values(ENV_FILE)
    required = ("MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    if any(not settings.get(key) for key in required):
        raise RuntimeError("The local .env is missing required MySQL settings.")
    if settings["MYSQL_HOST"] not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Refusing to export a schema from a non-local MySQL host.")
    return settings


def get_dump_utility():
    utility = shutil.which("mysqldump")
    if utility:
        return utility
    windows_path = Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe")
    if windows_path.is_file():
        return str(windows_path)
    raise FileNotFoundError("mysqldump was not found. Install MySQL client tools first.")


def ensure_target_database_is_new(settings):
    connection = pymysql.connect(
        host=settings["MYSQL_HOST"],
        port=int(settings.get("MYSQL_PORT") or 3306),
        user=settings["MYSQL_USER"],
        password=settings["MYSQL_PASSWORD"],
        database=settings["MYSQL_DATABASE"],
        connect_timeout=5,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (TARGET_DATABASE,))
            if cursor.fetchone():
                raise RuntimeError(
                    f"Refusing to create a dump because {TARGET_DATABASE} already exists."
                )
    finally:
        connection.close()


def load_demo_rows():
    if not SQLITE_FILE.is_file():
        raise FileNotFoundError("The isolated .demo-showcase.sqlite3 database is missing.")

    connection = sqlite3.connect(SQLITE_FILE)
    connection.row_factory = sqlite3.Row
    try:
        users = [row[0] for row in connection.execute("SELECT username FROM auth_user")]
        if sorted(users) != ["demo-admin", "demo-user"]:
            raise RuntimeError("The showcase database contains unexpected user accounts.")

        columns = [row[1] for row in connection.execute('PRAGMA table_info("cards_card")')]
        if any("cvv" in column.lower() for column in columns):
            raise RuntimeError("Refusing to export a card table containing a CVV column.")
        if not {"masked_card_number", "last4"}.issubset(columns):
            raise RuntimeError("The card table does not match the masked-card schema.")
        for masked, last4 in connection.execute(
            "SELECT masked_card_number, last4 FROM cards_card"
        ):
            if not masked.endswith(last4) or set(masked[:-4]) != {"*"}:
                raise RuntimeError("Refusing to export an unmasked card number.")

        table_names = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if row[0] not in EXCLUDED_TABLES
        ]
        data = []
        for table_name in table_names:
            table_columns = [
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(" + sql_identifier(table_name) + ")"
                )
            ]
            rows = connection.execute(
                "SELECT * FROM " + sql_identifier(table_name)
            ).fetchall()
            if rows:
                data.append((table_name, table_columns, rows))
        return data
    finally:
        connection.close()


def build_dump():
    settings = get_mysql_settings()
    ensure_target_database_is_new(settings)
    rows_by_table = load_demo_rows()
    utility = get_dump_utility()

    environment = os.environ.copy()
    environment["MYSQL_PWD"] = settings["MYSQL_PASSWORD"]
    command = [
        utility,
        "--no-data",
        "--skip-lock-tables",
        "--skip-add-locks",
        "--skip-add-drop-table",
        "--skip-comments",
        "--no-tablespaces",
        "--default-character-set=utf8mb4",
        "--host",
        settings["MYSQL_HOST"],
        "--port",
        str(settings.get("MYSQL_PORT") or 3306),
        "--user",
        settings["MYSQL_USER"],
        settings["MYSQL_DATABASE"],
    ]
    result = subprocess.run(command, env=environment, capture_output=True, text=True, check=False)
    environment.pop("MYSQL_PWD", None)
    if result.returncode:
        raise RuntimeError(
            "mysqldump could not read the local database schema: " + result.stderr.strip()
        )

    schema = result.stdout.strip()

    statements = [
        "-- MySQL schema-only export plus synthetic rows from the isolated showcase database.",
        "-- No rows from the existing local MySQL database are included.",
        "CREATE DATABASE IF NOT EXISTS " + sql_identifier(TARGET_DATABASE)
        + " CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "USE " + sql_identifier(TARGET_DATABASE) + ";",
        schema.rstrip(),
        "SET FOREIGN_KEY_CHECKS=0;",
        "START TRANSACTION;",
    ]
    for table_name, columns, rows in rows_by_table:
        column_sql = ", ".join(sql_identifier(column) for column in columns)
        table_sql = sql_identifier(table_name)
        for row in rows:
            values_sql = ", ".join(sql_value(value) for value in row)
            statements.append(
                "INSERT INTO " + table_sql + " (" + column_sql + ") VALUES ("
                + values_sql + ");"
            )
    statements.extend([
        "COMMIT;",
        "SET FOREIGN_KEY_CHECKS=1;",
        "",
    ])
    OUTPUT_FILE.write_text("\n".join(statements), encoding="utf-8")
    print({
        "dump": str(OUTPUT_FILE),
        "bytes": OUTPUT_FILE.stat().st_size,
        "tables_with_demo_rows": len(rows_by_table),
        "target_database": TARGET_DATABASE,
    })


if __name__ == "__main__":
    build_dump()
