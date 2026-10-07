from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
OUTPUT = ROOT / "Credit-Card-Payment-System-Review.pdf"
GREEN = colors.HexColor("#174b40")
INK = colors.HexColor("#18332d")
MUTED = colors.HexColor("#718078")
GOLD = colors.HexColor("#eabf56")

CAPTURES = [
    ("Sign in", "login.png", "JWT sign-in screen for the local demo account."),
    ("Customer overview", "dashboard.png", "Payment totals, recent activity, and masked saved-card summary."),
    ("Dashboard API contract", "fastapi-dashboard-summary.png", "FastAPI Swagger documents the dashboard summary route and its response models."),
    ("Cards", "cards.png", "Card entry and saved-card views; only the masked number is persisted."),
    ("Simulated payment success", "payment-success.png", "End-to-end success response from the simulated payment service."),
    ("Simulated payment failure", "payment-failure.png", "Deterministic failure response from the simulated payment service."),
    ("Transaction history", "transactions.png", "Filterable history showing success, failure, and pending states."),
    ("Admin reporting", "admin-dashboard.png", "Staff-only transaction totals and daily reporting."),
    ("Django administration", "django-admin.png", "Authenticated Django administration site."),
    ("Django API documentation", "django-api-docs.png", "OpenAPI documentation for the Django REST API."),
    ("FastAPI Swagger", "fastapi-swagger.png", "Payment-service Swagger UI, including the typed dashboard summary response."),
]


def draw_footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#e3e9e2"))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "Credit Card Payment System | Local showcase")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, str(document.page))
    canvas.restoreState()


def build_report():
    missing = [filename for _, filename, _ in CAPTURES if not (SCREENSHOTS / filename).is_file()]
    if missing:
        raise FileNotFoundError("Missing screenshots: " + ", ".join(missing))

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=27, leading=32, textColor=GREEN, alignment=TA_CENTER, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", parent=styles["Normal"], fontSize=12,
        leading=18, textColor=MUTED, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=19, leading=24, textColor=GREEN, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="CaptureHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=15, leading=19, textColor=GREEN, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="BodyCopy", parent=styles["BodyText"], fontSize=10,
        leading=15, textColor=INK, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Caption", parent=styles["BodyText"], fontSize=9,
        leading=13, textColor=MUTED, spaceAfter=9,
    ))

    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=22 * mm,
        title="Credit Card Payment System - Team Review and Demo Guide",
        author="PaySecure Project Team",
    )
    story = [Spacer(1, 22 * mm)]
    story.append(Paragraph("Credit Card Payment System", styles["ReportTitle"]))
    story.append(Paragraph("Team review and demo guide", styles["ReportSubtitle"]))
    story.append(Spacer(1, 12 * mm))

    summary = [
        ["Frontend", "React, Vite, Tailwind CSS"],
        ["Backend", "Django REST Framework and FastAPI"],
        ["Database", "MySQL demo dump included; screenshots use isolated SQLite"],
        ["Payment mode", "Simulated only; no real gateway is connected"],
        ["Captured", date.today().isoformat()],
    ]
    table = Table(summary, colWidths=[34 * mm, 118 * mm], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff3ee")),
        ("TEXTCOLOR", (0, 0), (0, -1), GREEN),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#e3e9e2")),
    ]))
    story.extend([table, Spacer(1, 12 * mm)])
    story.append(Paragraph(
        "This review documents the running application using synthetic showcase records. "
        "The screenshots do not use the local MySQL records or real payment-card data.",
        styles["BodyCopy"],
    ))
    story.append(Paragraph(
        "Local showcase accounts: <b>demo-user</b> and <b>demo-admin</b>. "
        "Their passwords are intentionally omitted from this report; they are seeded only "
        "in the ignored local SQLite showcase database.",
        styles["BodyCopy"],
    ))
    story.append(PageBreak())

    story.append(Paragraph("Architecture at a glance", styles["SectionHeading"]))
    story.append(Paragraph(
        "The application separates the customer experience, core account and ledger APIs, and "
        "payment simulation. Django is the source of truth for users, card records, and transactions. "
        "FastAPI coordinates a simulated payment and calls Django's protected internal endpoints.",
        styles["BodyCopy"],
    ))

    architecture = [
        ["Caller", "Protocol", "Service / responsibility"],
        ["React + Tailwind", "JWT", "Django REST: auth, cards, history, admin reporting"],
        ["React + Tailwind", "JWT", "FastAPI: validate request and simulate payment"],
        ["FastAPI", "Internal secret", "Django internal API: ownership check and transaction state"],
        ["Django ORM", "Database", "MySQL in normal configuration; SQLite for screenshots"],
    ]
    architecture_table = Table(architecture, colWidths=[38 * mm, 32 * mm, 82 * mm], repeatRows=1)
    architecture_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f8f4")),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dce5dc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([architecture_table, Spacer(1, 5 * mm)])
    story.append(Paragraph("What happens during a payment", styles["CaptureHeading"]))
    story.append(Paragraph(
        "1. The signed-in React client sends the user ID, saved card ID, amount, and JWT to FastAPI. "
        "2. FastAPI verifies the JWT and user identity. 3. Django verifies card ownership and creates "
        "a PENDING transaction. 4. FastAPI simulates the outcome and asks Django to finalize it. "
        "Django permits only a one-way PENDING-to-final transition.",
        styles["BodyCopy"],
    ))
    story.append(Paragraph("Security and data handling", styles["CaptureHeading"]))
    story.append(Paragraph(
        "Django hashes passwords. Protected APIs require JWT authentication. Card entry validates "
        "the number but stores only a masked value and last four digits; CVV is write-only and "
        "discarded. FastAPI receives a saved-card ID, never the PAN or CVV. No payment gateway is used.",
        styles["BodyCopy"],
    ))
    story.append(PageBreak())

    story.append(Paragraph("Review meeting walkthrough", styles["SectionHeading"]))
    story.append(Paragraph(
        "Suggested opening: <i>This project demonstrates a full-stack payment workflow without "
        "moving real money. React handles the customer and admin screens, Django owns authenticated "
        "records, and FastAPI simulates payment outcomes.</i>",
        styles["BodyCopy"],
    ))
    story.append(Paragraph("Demo sequence", styles["CaptureHeading"]))
    demo_steps = [
        ["1", "Sign in as demo-user and point out the overview metrics and recent activity."],
        ["2", "Open Cards and show the masked saved card ending in 4242."],
        ["3", "Submit INR 825.00 for a simulated SUCCESS response."],
        ["4", "Submit INR 100.13 for the deterministic simulated FAILED response."],
        ["5", "Open Activity to show both new ledger entries, then review Admin reporting and API docs."],
    ]
    steps_table = Table(demo_steps, colWidths=[12 * mm, 140 * mm])
    steps_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (0, -1), GREEN),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e3e9e2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([steps_table, Spacer(1, 5 * mm)])
    story.append(Paragraph("Verification", styles["CaptureHeading"]))
    test_summary = [
        ["Django", "12 tests passed"],
        ["FastAPI", "11 tests passed"],
        ["Frontend", "6 tests passed; production build succeeded"],
        ["Docker", "Not verified in this environment; Docker CLI unavailable"],
    ]
    test_table = Table(test_summary, colWidths=[36 * mm, 116 * mm])
    test_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff3ee")),
        ("TEXTCOLOR", (0, 0), (0, -1), GREEN),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dce5dc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([test_table, Spacer(1, 5 * mm)])
    story.append(Paragraph("Scope and caveats", styles["CaptureHeading"]))
    story.append(Paragraph(
        "Payment outcomes are deterministic demo behavior, not a production processor. The included "
        "MySQL dump uses schema-only DDL plus synthetic showcase rows and creates a separate "
        "credit_card_submission_demo database; existing MySQL rows were not exported or modified. "
        "Screenshots use isolated SQLite. Import requires a MySQL administrator because the app "
        "account cannot create databases. This guide is not the original assignment PDF.",
        styles["BodyCopy"],
    ))
    story.append(Paragraph(
        "Complete PNG captures are included in the screenshots folder. The PDF uses a preview crop "
        "for layout; open the PNG for the full-page image.",
        styles["Caption"],
    ))
    story.append(PageBreak())

    max_width = document.width
    for index, (title, filename, caption) in enumerate(CAPTURES):
        image_path = SCREENSHOTS / filename
        with PILImage.open(image_path) as source:
            width, height = source.size
            crop_height = min(height, 1150)
            preview = source.crop((0, 0, width, crop_height))
            image_data = BytesIO()
            preview.save(image_data, format="PNG")
        image_data.seek(0)
        image_height = max_width * crop_height / width
        image = Image(image_data, width=max_width, height=image_height)
        story.append(KeepTogether([
            Paragraph(title, styles["CaptureHeading"]),
            Spacer(1, 3 * mm),
            image,
            Spacer(1, 3 * mm),
            Paragraph(caption, styles["Caption"]),
        ]))
        if index < len(CAPTURES) - 1:
            story.append(PageBreak())

    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build_report()
