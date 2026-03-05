"""
Vendor Exporter Module - Exports vendor data to Excel/PDF
"""

import os
from typing import List, Dict, Any
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class VendorExporter:
    """Exports vendor search results to various formats"""

    def __init__(self):
        self.temp_dir = "/tmp/unified_mvp"
        os.makedirs(self.temp_dir, exist_ok=True)

    def to_excel(self, vendors: List[Dict[str, Any]], keyword: str, country: str) -> str:
        """Export vendor list to Excel file per spec format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.temp_dir}/vendors_{keyword}_{country}_{timestamp}.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "Vendor Results"

        # Header style
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Headers per spec: Rank | Vendor | Country | Website | Email | Exhibition | Relevance Score
        headers = [
            "Rank", "Vendor", "Country", "Website", "Email",
            "Exhibition", "Relevance Score", "Products",
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Data rows
        for row, vendor in enumerate(vendors, 2):
            ws.cell(row=row, column=1, value=row - 1)
            ws.cell(row=row, column=2, value=vendor.get("name", ""))
            ws.cell(row=row, column=3, value=vendor.get("country", ""))
            ws.cell(row=row, column=4, value=vendor.get("website", ""))
            ws.cell(row=row, column=5, value=vendor.get("contact", ""))
            ws.cell(row=row, column=6, value=vendor.get("exhibition", ""))
            ws.cell(row=row, column=7, value=vendor.get("match_score", 0))
            ws.cell(row=row, column=8, value=vendor.get("products", ""))

        # Adjust column widths
        column_widths = [6, 30, 15, 35, 25, 20, 15, 30]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width

        wb.save(filename)
        return filename

    def to_pdf(self, vendors: List[Dict[str, Any]], keyword: str, country: str) -> str:
        """Export vendor list to PDF report per spec"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.temp_dir}/vendors_{keyword}_{country}_{timestamp}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1f4788"),
            spaceAfter=20,
        )

        # Title
        elements.append(Paragraph("<b>AI Global Vendor Scout Report</b>", title_style))

        # Search conditions
        info_style = ParagraphStyle(
            "Info", parent=styles["Normal"], fontSize=10, spaceAfter=6
        )
        elements.append(
            Paragraph(
                f"<b>Keyword:</b> {keyword} | "
                f"<b>Country:</b> {country or 'All'} | "
                f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}",
                info_style,
            )
        )

        # Exhibition coverage
        exhibitions = set(v.get("exhibition", "") for v in vendors if v.get("exhibition"))
        if exhibitions:
            elements.append(
                Paragraph(
                    f"<b>Exhibitions covered:</b> {', '.join(sorted(exhibitions))}",
                    info_style,
                )
            )

        elements.append(
            Paragraph(
                f"<b>Total vendors found:</b> {len(vendors)}",
                info_style,
            )
        )
        elements.append(Spacer(1, 0.2 * inch))

        # Top 20 vendor table
        top_vendors = vendors[:20]
        table_data = [
            ["Rank", "Vendor", "Country", "Exhibition", "Score", "Products"]
        ]
        for i, vendor in enumerate(top_vendors, 1):
            products = vendor.get("products", "")
            if len(products) > 35:
                products = products[:35] + "..."
            table_data.append([
                str(i),
                vendor.get("name", "")[:30],
                vendor.get("country", ""),
                vendor.get("exhibition", "")[:20],
                str(vendor.get("match_score", 0)),
                products,
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F2F2F2")),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("ALIGN", (5, 1), (5, -1), "LEFT"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))

        # Country distribution summary
        country_dist = {}
        for v in vendors:
            c = v.get("country", "Global")
            country_dist[c] = country_dist.get(c, 0) + 1
        sorted_countries = sorted(country_dist.items(), key=lambda x: x[1], reverse=True)

        if sorted_countries:
            elements.append(
                Paragraph("<b>Suggested priority countries:</b>", info_style)
            )
            for c, count in sorted_countries[:5]:
                elements.append(
                    Paragraph(f"  {c}: {count} vendors", info_style)
                )

        elements.append(Spacer(1, 0.3 * inch))
        elements.append(
            Paragraph(
                "<i>Generated by AI Global Vendor Scout</i>",
                styles["Italic"],
            )
        )

        doc.build(elements)
        return filename
