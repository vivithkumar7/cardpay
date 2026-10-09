from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "screenshots"
OUTPUT = Path(__file__).resolve().parent / "card-payment-system-project-report.pdf"

INK = colors.HexColor("#173b35")
GREEN = colors.HexColor("#1c5a4e")
MINT = colors.HexColor("#eaf3ed")
GOLD = colors.HexColor("#e2b94f")
SLATE = colors.HexColor("#62716c")
PALE = colors.HexColor("#f5f7f4")
WHITE = colors.white


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=29,
            leading=34,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            textColor=SLATE,
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=INK,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "SubHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=GREEN,
            spaceBefore=7,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            textColor=INK,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10,
            textColor=SLATE,
        ),
        "cell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=INK,
        ),
        "cell_white": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=WHITE,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=INK,
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=GREEN,
            spaceAfter=6,
        ),
    }


ST = styles()


def p(text, style="body"):
    return Paragraph(text, ST[style])


def bullet(text):
    return p(f'<font color="#1c5a4e"><b>•</b></font>&nbsp; {text}')


def table(rows, widths, header=True, padd=6):
    formatted = []
    for row_index, row in enumerate(rows):
        if header and row_index == 0:
            formatted.append(
                [
                    item if isinstance(item, Paragraph) else p(str(item), "cell_white")
                    for item in row
                ]
            )
        else:
            formatted.append(
                [
                    item if isinstance(item, Paragraph) else p(str(item), "cell")
                    for item in row
                ]
            )
    result = Table(formatted, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padd),
        ("RIGHTPADDING", (0, 0), (-1, -1), padd),
        ("TOPPADDING", (0, 0), (-1, -1), padd),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padd),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dbe3dd")),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
            ]
        )
    else:
        commands.append(("BACKGROUND", (0, 0), (-1, -1), MINT))
    result.setStyle(TableStyle(commands))
    return result


def image_crop(filename, box, crop=None):
    source = SCREENSHOTS / filename
    with PILImage.open(source) as opened:
        img = opened.convert("RGB")
        if crop is not None:
            img = img.crop(crop)
        img.thumbnail(box, PILImage.Resampling.LANCZOS)
        stream = BytesIO()
        img.save(stream, format="JPEG", quality=88, optimize=True)
        stream.seek(0)
        return Image(stream, width=img.width, height=img.height)


def framed_image(filename, width, height, crop=None, caption=None):
    visual = image_crop(filename, (width, height), crop)
    frame = Table([[visual]], colWidths=[width + 12])
    frame.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#dbe3dd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    contents = [frame]
    if caption:
        contents.extend([Spacer(1, 4), p(caption, "small")])
    return KeepTogether(contents)


def callout(text, width=510):
    box = Table([[p(text, "callout")]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), MINT),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#cbded1")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return box


def draw_page(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    if page > 1:
        canvas.setStrokeColor(colors.HexColor("#dbe3dd"))
        canvas.setLineWidth(0.6)
        canvas.line(50, 42, letter[0] - 50, 42)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(50, 28, "PAYSECURE  |  PROJECT IMPLEMENTATION REPORT")
        canvas.drawRightString(letter[0] - 50, 28, f"{page}  /  6")
    canvas.restoreState()


class ReportDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if getattr(getattr(flowable, "style", None), "name", "") == "SectionHeading":
            print(f"Section starts on page {self.page}: {flowable.getPlainText()}")


def build_story():
    W = letter[0] - 100
    story = []

    # Page 1 — cover and executive summary.
    story.extend(
        [
            Spacer(1, 15),
            p("PROJECT DELIVERY REPORT  •  09 OCTOBER 2026", "cover_label"),
            p("Secure Card Payment<br/>System", "title"),
            p(
                "RBAC, fraud detection, transaction analytics, monitoring, and operational reporting",
                "subtitle",
            ),
            callout(
                "A Django + FastAPI + React system for simulated card payments, "
                "with role-aware operations, reviewable fraud alerts, and auditable admin actions."
            ),
            Spacer(1, 13),
            p("Executive summary", "h2"),
            p(
                "The delivered application combines customer payment and card workflows "
                "with staff operations. Django owns identity, card and transaction data, "
                "permissions, fraud review, and audit records; FastAPI provides the "
                "payment-facing service; React presents customer and admin dashboards.",
            ),
            table(
                [
                    ["SECURITY", "FRAUD", "VISIBILITY", "OPERATIONS"],
                    [
                        "Three staff roles with scoped permissions",
                        "Rule checks, alerts, review states, and email",
                        "Analytics, search, charts, and exports",
                        "Health metrics, structured audit, Docker",
                    ],
                ],
                [W / 4] * 4,
                padd=7,
            ),
            Spacer(1, 14),
            framed_image(
                "live-test-admin-dashboard.png",
                W,
                205,
                crop=(0, 0, 788, 580),
                caption="Admin dashboard evidence: service health, export actions, payment metrics, and card operations.",
            ),
            Spacer(1, 6),
            p(
                "Scope note: payment processing is simulated; the application does not connect to a real payment gateway.",
                "small",
            ),
            PageBreak(),
        ]
    )

    # Page 2 — RBAC and audit.
    story.extend(
        [
            p("01  |  Security, roles & audit", "h1"),
            p(
                "Django group permissions enforce who may view or change cards, "
                "transactions, analytics, and fraud reviews. Customer APIs remain "
                "authenticated and scoped to the signed-in user's own records.",
            ),
            table(
                [
                    ["Role", "Allowed operations", "Explicit restrictions"],
                    [
                        "Admin",
                        "View all cards/transactions; block, unblock, remove cards; "
                        "change credit limits; analytics and exports; review fraud alerts.",
                        "Sensitive actions are recorded; no full PAN or CVV is stored.",
                    ],
                    [
                        "Support",
                        "View cards/transactions; block or unblock cards; analytics; "
                        "view and review fraud alerts.",
                        "Cannot change credit limits, remove cards, or initiate customer payments.",
                    ],
                    [
                        "Read-Only",
                        "View operations data, analytics, and fraud alerts.",
                        "No card changes, payment initiation, or fraud-alert review.",
                    ],
                ],
                [77, 225, W - 302],
            ),
            Spacer(1, 9),
            p("Audit design", "h2"),
            p(
                "The <b>admin_logs</b> table stores actor, action, target, timestamp, "
                "details, and structured before/after changes. Card block/unblock, "
                "credit-limit changes, transaction edits, and fraud-alert reviews "
                "create records. Admin users may also add immutable <b>manual_note</b> "
                "entries; these are clearly distinguished from system-generated events.",
            ),
            callout(
                "Privacy by design: card records retain a masked number and last four digits; "
                "audit details avoid card PAN and CVV."
            ),
            Spacer(1, 11),
            framed_image(
                "live-test-django-audit-logs.png",
                W,
                180,
                crop=(0, 0, 1109, 650),
                caption="Django Admin audit list showing card and transaction actions with actor and target.",
            ),
            PageBreak(),
        ]
    )

    # Page 3 — fraud.
    story.extend(
        [
            p("02  |  Fraud detection & alerting", "h1"),
            p(
                "The fraud evaluator runs as part of transaction creation. It checks "
                "a rolling 10-minute activity window and creates a linked review record "
                "when a rule is matched.",
            ),
            table(
                [
                    ["Rule", "Detection condition", "System response"],
                    [
                        "Repeated high value",
                        "Three or more transactions of at least ₹5,000 in ten minutes.",
                        "Flag transaction; create alert with rule code.",
                    ],
                    [
                        "Rapid location change",
                        "Source IP fingerprint differs from a recent attempt in the window.",
                        "Flag transaction; alert for review.",
                    ],
                    [
                        "Rapid device change",
                        "Device fingerprint differs from a recent attempt in the window.",
                        "Flag transaction; alert for review.",
                    ],
                ],
                [105, 213, W - 318],
            ),
            Spacer(1, 9),
            p("Detection and response flow", "h2"),
            table(
                [
                    [
                        p("<b>Payment attempt</b><br/>User, card, amount, device", "cell"),
                        p("<b>Evaluate</b><br/>Recent attempts + rule window", "cell"),
                        p("<b>Record</b><br/>Fraud status + alert", "cell"),
                        p("<b>Notify & review</b><br/>Email + staff decision", "cell"),
                    ]
                ],
                [W / 4] * 4,
                header=False,
                padd=9,
            ),
            Spacer(1, 9),
            bullet("Source IP and device identifiers are HMAC-fingerprinted before persistence."),
            bullet("Alerts retain rule codes, status, reviewer, detection time, and review time."),
            bullet("Email is queued after transaction commit for the account holder and active operations recipients."),
            bullet("A flagged payment is reviewable; detection does not automatically decline the simulated payment."),
            Spacer(1, 8),
            framed_image(
                "live-test-mailpit.png",
                W,
                155,
                crop=(0, 0, 1132, 470),
                caption="Mailpit evidence from the end-to-end run, including payment and card-operation notifications.",
            ),
            Spacer(1, 8),
            callout(
                "Location is inferred from source IP changes, not precise geolocation. "
                "Fingerprint comparison is a risk signal, not proof of fraud."
            ),
            PageBreak(),
        ]
    )

    # Page 4 — analytics and search.
    story.extend(
        [
            p("03  |  Analytics & transaction search", "h1"),
            p(
                "The analytics API summarizes successful spending and transaction "
                "activity for customer and staff dashboards. The frontend presents "
                "spending trends and category/status breakdowns, plus card utilization.",
            ),
            table(
                [
                    ["Analytics capability", "Definition / behavior"],
                    [
                        "Monthly spending",
                        "Six months of successful transaction totals, grouped by month.",
                    ],
                    [
                        "Category breakdown",
                        "Expense totals across categories such as travel, shopping, bills, and dining.",
                    ],
                    [
                        "Credit utilization",
                        "Successful credit-card spending compared with the configured credit limit.",
                    ],
                    [
                        "Activity context",
                        "Status totals and recent daily payment attempts support dashboard interpretation.",
                    ],
                ],
                [150, W - 150],
            ),
            Spacer(1, 8),
            p("Search, pagination & query efficiency", "h2"),
            bullet("Filter by date range, minimum/maximum amount, status, and masked card number or last four digits."),
            bullet("Sort by created date, amount, status, reference, or category; prefix with “-” for descending order."),
            bullet("Server pagination returns count/next/previous/results; default 20, maximum 100 rows per page."),
            bullet("Composite user/date/status and fraud/date indexes support common filters and review workflows."),
            Spacer(1, 10),
            framed_image(
                "live-test-admin-dashboard.png",
                W,
                190,
                crop=(0, 0, 788, 695),
                caption="Dashboard evidence for live monitoring and reporting; the dashboard also provides CSV/PDF exports.",
            ),
            Spacer(1, 7),
            p(
                "Data semantics: monthly analytics use successful payments; total-spend fields may include other statuses where the API definition says so.",
                "small",
            ),
            PageBreak(),
        ]
    )

    # Page 5 — monitoring, exports, API surfaces.
    story.extend(
        [
            p("04  |  Monitoring, exports & APIs", "h1"),
            p(
                "Request middleware in Django and FastAPI records method, path, status, "
                "and duration. Slow requests are flagged using a configurable threshold; "
                "failures and exceptions are logged for diagnosis.",
            ),
            table(
                [
                    ["Operations surface", "What it provides"],
                    [
                        "System health",
                        "Database connectivity, process-local request/failure/latency counters, uptime, and slow-request totals.",
                    ],
                    [
                        "Analytics exports",
                        "Role-authorized CSV and PDF summaries from the admin reporting endpoint.",
                    ],
                    [
                        "Django REST Swagger",
                        "Browsable API endpoints and generated OpenAPI schema for the Django service.",
                    ],
                    [
                        "FastAPI Swagger",
                        "Browsable payment-service API, schemas, and health/version endpoints.",
                    ],
                    [
                        "Mailpit",
                        "Local SMTP capture for payment and operational notification verification.",
                    ],
                ],
                [142, W - 142],
            ),
            Spacer(1, 9),
            p("Validated service surfaces", "h2"),
            table(
                [
                    ["Surface", "Observed result in live Docker verification"],
                    ["Frontend", "HTTP 200; sign-in, checkout, dashboard flows exercised."],
                    ["Django API docs / schema", "HTTP 200; endpoints and generated schema available."],
                    ["FastAPI docs / OpenAPI / health", "HTTP 200; payment and health surfaces available."],
                    ["Django Admin", "Sign-in and audit-history pages exercised."],
                    ["Mailpit", "HTTP 200; end-to-end messages received."],
                ],
                [150, W - 150],
            ),
            Spacer(1, 10),
            framed_image(
                "live-test-fastapi-swagger.png",
                W,
                170,
                crop=(0, 0, 1109, 610),
                caption="FastAPI Swagger UI with health, dashboard, and simulated payment operations.",
            ),
            Spacer(1, 6),
            p(
                "Monitoring counters are process-local and reset on restart; production multi-worker deployments should forward metrics and logs to centralized observability.",
                "small",
            ),
            PageBreak(),
        ]
    )

    # Page 6 — delivery and verification.
    story.extend(
        [
            p("05  |  Validation & delivery", "h1"),
            p(
                "Implementation is documented in the project README and Django "
                "migrations. The service stack runs with Docker Compose and retains "
                "MySQL data in a named volume.",
            ),
            table(
                [
                    ["Verification", "Result"],
                    ["Django automated tests", "46 tests passed in the latest run after Admin add-flow changes."],
                    ["FastAPI automated tests", "15 tests passed in the prior integration run."],
                    ["Frontend automated tests", "11 tests passed in the prior integration run."],
                    ["Docker end-to-end", "Compose services started; payment, card action, audit, email, docs, and health flows exercised."],
                    ["Whitespace / patch check", "git diff --check passed."],
                ],
                [160, W - 160],
            ),
            Spacer(1, 10),
            framed_image(
                "live-test-payment-success.png",
                W,
                170,
                crop=(0, 0, 1109, 590),
                caption="End-to-end checkout evidence. Card/payment values shown are synthetic and the charge is simulated.",
            ),
            Spacer(1, 9),
            callout(
                "Run locally: docker compose up --build. MySQL is published on host port 3307 "
                "by default to avoid a common Windows port-3306 conflict; containers use "
                "MySQL port 3306 internally. Create a Django superuser before signing in to Admin."
            ),
            Spacer(1, 8),
            p(
                "Limitations: no real payment gateway is connected; anomaly rules are deterministic starter rules; "
                "health counters are process-local; email delivery depends on configured SMTP (Mailpit in the demo).",
                "small",
            ),
        ]
    )
    return story


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = ReportDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=45,
        bottomMargin=55,
        title="Secure Card Payment System — Project Delivery Report",
        author="PaySecure Project Team",
        subject="RBAC, fraud detection, analytics, monitoring, exports, and validation",
    )
    doc.build(build_story(), onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
