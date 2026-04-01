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
        self.temp_dir = "/tmp/global_vendor_scout"
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

        headers = [
            "Rank", "Company", "Booth", "Exhibition", "Relevance Score",
            "Products", "Application Areas", "Website", "Email", "Phone", "Address",
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Data rows
        for row, vendor in enumerate(vendors, 2):
            products = ", ".join(vendor.get("products", []))
            areas = ", ".join(vendor.get("application_areas", []))
            ws.cell(row=row, column=1, value=row - 1)
            ws.cell(row=row, column=2, value=vendor.get("name", ""))
            ws.cell(row=row, column=3, value=vendor.get("booth", ""))
            ws.cell(row=row, column=4, value=vendor.get("exhibition", ""))
            ws.cell(row=row, column=5, value=vendor.get("match_score", 0))
            ws.cell(row=row, column=6, value=products)
            ws.cell(row=row, column=7, value=areas)
            ws.cell(row=row, column=8, value=vendor.get("website", ""))
            ws.cell(row=row, column=9, value=vendor.get("email", ""))
            ws.cell(row=row, column=10, value=vendor.get("phone", ""))
            ws.cell(row=row, column=11, value=vendor.get("address", ""))

        # Adjust column widths
        column_widths = [6, 30, 8, 18, 12, 35, 30, 30, 25, 18, 40]
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
        elements.append(Paragraph("<b>electronica 2024 — Exhibitor Report</b>", title_style))

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
            ["Rank", "Company", "Booth", "Score", "Products/Services", "Website"]
        ]
        for i, vendor in enumerate(top_vendors, 1):
            products = ", ".join(vendor.get("products", []))
            if len(products) > 40:
                products = products[:40] + "..."
            table_data.append([
                str(i),
                vendor.get("name", "")[:30],
                vendor.get("booth", ""),
                str(vendor.get("match_score", 0)),
                products,
                vendor.get("website", "")[:30],
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

        # Application area distribution
        area_dist: dict[str, int] = {}
        for v in vendors:
            for area in v.get("application_areas", []):
                area_dist[area] = area_dist.get(area, 0) + 1
        sorted_areas = sorted(area_dist.items(), key=lambda x: x[1], reverse=True)

        if sorted_areas:
            elements.append(
                Paragraph("<b>Top application areas:</b>", info_style)
            )
            for area, count in sorted_areas[:5]:
                elements.append(
                    Paragraph(f"  {area}: {count} companies", info_style)
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
