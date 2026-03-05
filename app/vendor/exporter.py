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
        """Export vendor list to Excel file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.temp_dir}/vendors_{keyword}_{country}_{timestamp}.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Vendor Results"
        
        # Header style
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Headers
        headers = ["Name", "Country", "Category", "Rating", "Match Score", "Products", "Contact", "Established"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Data rows
        for row, vendor in enumerate(vendors, 2):
            ws.cell(row=row, column=1, value=vendor.get("name", ""))
            ws.cell(row=row, column=2, value=vendor.get("country", ""))
            ws.cell(row=row, column=3, value=vendor.get("category", ""))
            ws.cell(row=row, column=4, value=vendor.get("rating", 0))
            ws.cell(row=row, column=5, value=f"{vendor.get('match_score', 0)}%")
            ws.cell(row=row, column=6, value=vendor.get("products", ""))
            ws.cell(row=row, column=7, value=vendor.get("contact", ""))
            ws.cell(row=row, column=8, value=vendor.get("established", ""))
        
        # Adjust column widths
        column_widths = [25, 15, 15, 10, 12, 30, 35, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        wb.save(filename)
        return filename
    
    def to_pdf(self, vendors: List[Dict[str, Any]], keyword: str, country: str) -> str:
        """Export vendor list to PDF file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.temp_dir}/vendors_{keyword}_{country}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=20
        )
        
        # Title
        title = Paragraph(f"<b>Vendor Search Results</b>", title_style)
        elements.append(title)
        
        # Subtitle
        subtitle = Paragraph(f"<b>Keyword:</b> {keyword} | <b>Country:</b> {country or 'All'} | <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        table_data = [["Name", "Country", "Category", "Rating", "Score", "Products", "Contact"]]
        
        for vendor in vendors:
            table_data.append([
                vendor.get("name", ""),
                vendor.get("country", ""),
                vendor.get("category", ""),
                str(vendor.get("rating", 0)),
                f"{vendor.get('match_score', 0)}%",
                vendor.get("products", "")[:30] + "..." if len(vendor.get("products", "")) > 30 else vendor.get("products", ""),
                vendor.get("contact", "")
            ])
        
        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F2F2F2')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer = Paragraph(f"<i>Generated by Unified MVP - Vendor Scout</i>", styles['Italic'])
        elements.append(footer)
        
        doc.build(elements)
        return filename