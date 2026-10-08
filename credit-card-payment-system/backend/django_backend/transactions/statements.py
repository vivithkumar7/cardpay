import calendar
import re
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Transaction


def _masked_card_details(card):
    last4 = re.sub(r"\D", "", card.last4)[-4:]
    safe_last4 = last4.rjust(4, "*")
    return (
        f"{escape(card.card_type)}<br/>"
        f"<font color='#718078'>**** **** **** {safe_last4}</font>"
    )


class MonthlyStatementPdfView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        month_value = request.query_params.get("month", "")
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month_value):
            return Response(
                {"detail": "Month must use the YYYY-MM format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        year, month = (int(part) for part in month_value.split("-"))
        today = timezone.localdate()
        if year == 0 or (year, month) > (today.year, today.month):
            return Response(
                {"detail": "A statement cannot be generated for a future month."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start = timezone.make_aware(
            datetime(year, month, 1), timezone.get_current_timezone()
        )
        if month == 12:
            end = timezone.make_aware(
                datetime(year + 1, 1, 1), timezone.get_current_timezone()
            )
        else:
            end = timezone.make_aware(
                datetime(year, month + 1, 1), timezone.get_current_timezone()
            )

        transactions = list(
            Transaction.objects.filter(
                user=request.user, created_at__gte=start, created_at__lt=end
            )
            .select_related("card")
            .order_by("created_at", "pk")
        )
        successful = [
            transaction
            for transaction in transactions
            if transaction.status == Transaction.Status.SUCCESS
        ]
        total_spent = sum(
            (transaction.amount for transaction in successful), Decimal("0.00")
        )
        pdf = self._render_statement(
            request.user.get_username(), month_value, transactions, total_spent
        )
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="paysecure-statement-{month_value}.pdf"'
        )
        return response

    @staticmethod
    def _render_statement(username, month, transactions, total_spent):
        buffer = BytesIO()
        content_width = A4[0] - 36 * mm
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=31 * mm,
            bottomMargin=24 * mm,
            title=f"PaySecure statement {month}",
            author="PaySecure",
        )
        styles = getSampleStyleSheet()
        heading = ParagraphStyle(
            "StatementHeading",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#123b33"),
            spaceAfter=4 * mm,
        )
        body = ParagraphStyle(
            "StatementBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#52655b"),
        )
        small = ParagraphStyle(
            "StatementSmall",
            parent=body,
            fontSize=7.5,
            leading=10,
            wordWrap="CJK",
        )
        table_header = ParagraphStyle(
            "StatementTableHeader",
            parent=small,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
        right = ParagraphStyle(
            "RightAligned",
            parent=small,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#263a31"),
        )
        month_date = date(int(month[:4]), int(month[5:]), 1)
        month_end_date = date(
            month_date.year,
            month_date.month,
            calendar.monthrange(month_date.year, month_date.month)[1],
        )
        month_label = month_date.strftime("%B %Y")
        status_counts = {
            status: sum(1 for transaction in transactions if transaction.status == status)
            for status, _ in Transaction.Status.choices
        }
        unique_cards = {
            transaction.card_id: transaction.card for transaction in transactions
        }

        def draw_page(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#123b33"))
            canvas.rect(0, A4[1] - 19 * mm, A4[0], 19 * mm, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 11)
            canvas.drawString(18 * mm, A4[1] - 12 * mm, "PAYSECURE")
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(
                A4[0] - 18 * mm, A4[1] - 12 * mm, "MONTHLY ACCOUNT STATEMENT"
            )
            canvas.setStrokeColor(colors.HexColor("#dce5df"))
            canvas.line(18 * mm, 18 * mm, A4[0] - 18 * mm, 18 * mm)
            canvas.setFillColor(colors.HexColor("#718078"))
            canvas.setFont("Helvetica", 7)
            canvas.drawString(18 * mm, 12 * mm, "Private financial statement")
            canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
            canvas.restoreState()

        story = [
            Paragraph(f"Statement for {escape(month_label)}", heading),
            Paragraph(f"Account holder: {escape(username)}", body),
            Paragraph(
                f"Period: {month_date.strftime('%d %b %Y')} – "
                f"{month_end_date.strftime('%d %b %Y')}",
                body,
            ),
            Paragraph(
                f"Generated: {timezone.localtime().strftime('%d %b %Y, %H:%M %Z')}",
                small,
            ),
            Spacer(1, 6 * mm),
        ]
        summary_values = [
            ("SUCCESSFUL SPEND", f"INR {total_spent:,.2f}"),
            ("TRANSACTIONS", str(len(transactions))),
            ("SUCCESSFUL", str(status_counts[Transaction.Status.SUCCESS])),
            ("FAILED", str(status_counts[Transaction.Status.FAILED])),
            ("PENDING", str(status_counts[Transaction.Status.PENDING])),
        ]
        summary_rows = [
            [
                Paragraph(f"<b>{label}</b><br/><font size='11'>{value}</font>", body)
                for label, value in summary_values[:3]
            ],
            [
                Paragraph(f"<b>{label}</b><br/><font size='11'>{value}</font>", body)
                for label, value in summary_values[3:]
            ]
            + [
                Paragraph(
                    f"<b>PAYMENT METHODS</b><br/><font size='11'>{len(unique_cards)}</font>",
                    body,
                )
            ],
        ]
        summary_table = Table(
            summary_rows,
            colWidths=[content_width / 3] * 3,
            hAlign="LEFT",
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f6f3")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce5df")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce5df")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.extend(
            [
                summary_table,
                Spacer(1, 7 * mm),
                Paragraph("Transaction activity", styles["Heading2"]),
                Spacer(1, 2 * mm),
            ]
        )
        rows = [[
            Paragraph("DATE", table_header),
            Paragraph("REFERENCE", table_header),
            Paragraph("PAYMENT METHOD", table_header),
            Paragraph("STATUS", table_header),
            Paragraph("AMOUNT", table_header),
        ]]
        for transaction in transactions:
            local_created_at = timezone.localtime(transaction.created_at)
            rows.append(
                [
                    Paragraph(local_created_at.strftime("%d %b %Y<br/>%H:%M"), small),
                    Paragraph(escape(transaction.reference), small),
                    Paragraph(_masked_card_details(transaction.card), small),
                    Paragraph(escape(transaction.get_status_display()), small),
                    Paragraph(
                        f"{escape(transaction.currency)} {transaction.amount:,.2f}",
                        right,
                    ),
                ]
            )
        table = Table(
            rows,
            colWidths=[
                25 * mm,
                38 * mm,
                42 * mm,
                25 * mm,
                content_width - 130 * mm,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123b33")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce5df")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8f6")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.extend(
            [
                table,
                Spacer(1, 4 * mm),
                Paragraph(
                    "Successful spend includes only settled successful transactions. "
                    "Card numbers are masked; no full card number or security code "
                    "is included in this statement.",
                    small,
                ),
            ]
        )
        document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
        return buffer.getvalue()
